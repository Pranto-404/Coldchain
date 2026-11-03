/* ColdChain ESP32 reference node; flash separately as FRIDGE_A and FRIDGE_B.
 * Libraries: DallasTemperature, OneWire, ArduinoJson 7, PubSubClient,
 * Adafruit GFX, Adafruit SSD1306; built-in WiFi, LittleFS, Preferences, mbedTLS.
 * Demonstration hardware ONLY: compressor requires a certified low-voltage
 * control interface and electrical safety engineering. Never wire mains directly.
 */
#include <WiFi.h>
#include <time.h>
#include <LittleFS.h>
#include <Preferences.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "mbedtls/md.h"
#include "secrets.h"
#include "hardware_pins.h"

constexpr uint32_t SAMPLE_MS=5000, COMPRESSOR_MIN_OFF_MS=60000;
constexpr int MAX_FLASH_SAMPLES=900; // 75 minutes at 5s; supports 30-minute outage even with events
const char* QUEUE_FILE="/queue.jsonl";
const char* TMP_FILE="/queue.new";

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
OneWire oneWire(PIN_TEMP);
DallasTemperature probe(&oneWire);
Adafruit_SSD1306 oled(128,64,&Wire,-1);
Preferences settings;
bool compressor=false,doorOpen=false,priorDoor=false,powerOK=true,discardLatch=false,sensorOK=false,awaitingAck=false,queueFault=false,oledReady=false;
float tempC=NAN;
uint32_t lastSample=0,lastWiFi=0,lastMqtt=0,lastDisplay=0,lastRelayOff=0,doorSince=0,pendingSent=0,seqNext=0,pendingSeq=0;
// Offline queue: acknowledged lines are skipped by a read offset instead of rewriting the whole
// file per ACK (which was O(n^2) flash writes when syncing a 30-minute backlog). The offset is not
// persisted: after a reset the backend dedups re-sent samples and still ACKs them.
uint32_t queueOffset=0;int queuedCount=0;
uint64_t prevCommandNonce=0;
String topicData,topicAck,topicCmd;

String hmac256(const String &plain){
  uint8_t digest[32];char out[65];
  mbedtls_md_context_t ctx;mbedtls_md_init(&ctx);
  const mbedtls_md_info_t* md=mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
  mbedtls_md_setup(&ctx,md,1);
  mbedtls_md_hmac_starts(&ctx,(const unsigned char*)DEVICE_SECRET,strlen(DEVICE_SECRET));
  mbedtls_md_hmac_update(&ctx,(const unsigned char*)plain.c_str(),plain.length());
  mbedtls_md_hmac_finish(&ctx,digest);mbedtls_md_free(&ctx);
  for(int i=0;i<32;i++)sprintf(out+i*2,"%02x",digest[i]);out[64]=0;
  return String(out);
}

String deviceCanonical(JsonDocument &d){
  String s=String((const char*)d["device_id"]);s+='|'+String((uint32_t)d["seq"]);
  s+='|'+String((uint32_t)d["observed_at"]);
  s+='|'+String((int)d["temp_c_100"]);
  s+='|'+String(d["door_open"].as<bool>()?1:0);
  s+='|'+String(d["mains_ok"].as<bool>()?1:0);
  s+='|'+String(d["compressor_on"].as<bool>()?1:0);
  s+='|'+String((int)d["battery_pct"]);
  s+='|'+String((uint32_t)d["sent_at"]);
  s+='|'+String((const char*)d["nonce"]);
  return s;
}

void relaySet(bool turnOn){
  if(turnOn==compressor)return;
  compressor=turnOn;
  if(!compressor)lastRelayOff=millis();
  digitalWrite(PIN_RELAY,RELAY_ACTIVE_LOW?!turnOn:turnOn);
}
void regulate(){
  if(!sensorOK||!powerOK){relaySet(false);return;}
  if(tempC<=3.0f)relaySet(false);
  else if(tempC>=7.0f&&!compressor&&(uint32_t)(millis()-lastRelayOff)>=COMPRESSOR_MIN_OFF_MS)relaySet(true);
}
uint32_t allocatedSeq(){
  if(seqNext%1000==0){
    // Reserve a 1000-sequence block in NVS: no sequence reuse after sudden resets.
    uint32_t top=settings.getUInt("top",1000);
    if(top<=seqNext)top=seqNext+1000;
    settings.putUInt("top",top+1000);
    seqNext=top;
  }
  return seqNext++;
}
int batteryPercent(){
  // Demo rough ADC representation. Calibrate divider/reference before field use.
  if(powerOK)return 100;
  int raw=analogRead(PIN_BATTERY);
  return constrain(map(raw,1950,3000,0,100),0,100);
}
int queueCount(){return queuedCount;}
int countQueueFile(){
  File f=LittleFS.open(QUEUE_FILE,"r");if(!f)return 0;int count=0;
  while(f.available()){if(f.readStringUntil('\n').length())count++;}
  f.close();return count;
}
void compactQueue(){
  // Rarely needed: drop the acknowledged prefix once it is large, so the file cannot grow forever
  // when the link never fully drains.
  File old=LittleFS.open(QUEUE_FILE,"r");if(!old)return;
  old.seek(queueOffset);
  File fresh=LittleFS.open(TMP_FILE,"w");if(!fresh){old.close();queueFault=true;return;}
  while(old.available()){
    String line=old.readStringUntil('\n');if(line.length()){fresh.print(line);fresh.print('\n');}
  }
  old.close();fresh.close();
  LittleFS.remove(QUEUE_FILE);
  if(!LittleFS.rename(TMP_FILE,QUEUE_FILE))queueFault=true;
  queueOffset=0;
}
void appendSample(){
  if(!sensorOK||time(nullptr)<1700000000){queueFault=true;return;}
  JsonDocument d;
  d["device_id"]=DEVICE_ID;d["seq"]=allocatedSeq();d["observed_at"]=(uint32_t)time(nullptr);
  d["temp_c_100"]=(int)roundf(tempC*100.0f);
  d["door_open"]=doorOpen;d["mains_ok"]=powerOK;d["compressor_on"]=compressor;
  d["battery_pct"]=batteryPercent();
  if(queueCount()>=MAX_FLASH_SAMPLES){queueFault=true;return;} // NEVER silently overwrite unacknowledged readings
  File f=LittleFS.open(QUEUE_FILE,"a");if(!f){queueFault=true;return;}
  serializeJson(d,f);f.print('\n');f.close();
  queuedCount++;
}
String headLine(){
  File f=LittleFS.open(QUEUE_FILE,"r");if(!f)return "";
  f.seek(queueOffset);
  String line=f.readStringUntil('\n');f.close();line.trim();return line;
}
void dropHead(){
  File f=LittleFS.open(QUEUE_FILE,"r");if(!f)return;
  f.seek(queueOffset);
  f.readStringUntil('\n');
  queueOffset=f.position();
  bool drained=!f.available();
  f.close();
  if(queuedCount>0)queuedCount--;
  if(drained){LittleFS.remove(QUEUE_FILE);queueOffset=0;queuedCount=0;}
  else if(queueOffset>32768)compactQueue();
}
void transmitHead(){
  if(!mqtt.connected()||awaitingAck)return;
  String raw=headLine();if(!raw.length())return;
  JsonDocument d;if(deserializeJson(d,raw))return;
  if(time(nullptr)<1700000000)return;
  d["sent_at"]=(uint32_t)time(nullptr);
  uint64_t nonce=((uint64_t)esp_random()<<32)|esp_random();
  char noncebuf[24];snprintf(noncebuf,sizeof(noncebuf),"%08lx%08lx",(unsigned long)(nonce>>32),(unsigned long)nonce);
  d["nonce"]=noncebuf;
  d["signature"]=hmac256(deviceCanonical(d));
  String payload;serializeJson(d,payload);
  pendingSeq=d["seq"].as<uint32_t>();
  if(mqtt.publish(topicData.c_str(),payload.c_str())){
    awaitingAck=true;pendingSent=millis();
  }
}
void mqttCallback(char* topic,byte* payload,unsigned int len){
  String raw;for(unsigned i=0;i<len;i++)raw+=(char)payload[i];
  JsonDocument d;if(deserializeJson(d,raw))return;
  uint32_t sent=d["sent_at"]|0;
  if(abs((long)time(nullptr)-(long)sent)>120)return;
  if(String(topic)==topicAck){
    if(!awaitingAck||!d["seq"].is<uint32_t>()||d["seq"].as<uint32_t>()!=pendingSeq)return;
    String nonce=String((const char*)(d["nonce"]|""));
    String plain=String(DEVICE_ID)+"|"+String(pendingSeq)+"|"+String(sent)+"|"+nonce;
    if(hmac256(plain)!=String((const char*)(d["signature"]|"")))return;
    dropHead();awaitingAck=false;
    return;
  }
  if(String(topic)==topicCmd){
    if(!d["discard_latch"].is<bool>())return;
    String nonce=String((const char*)(d["nonce"]|""));
    String plain=String(DEVICE_ID)+"|"+String(d["discard_latch"].as<bool>()?1:0)+"|"+String(sent)+"|"+nonce;
    if(hmac256(plain)!=String((const char*)(d["signature"]|"")))return;
    discardLatch=d["discard_latch"].as<bool>();
    settings.putBool("redLatch",discardLatch); // Retained power-cycle behavior
  }
}
void networkTick(){
  if(WiFi.status()!=WL_CONNECTED&&millis()-lastWiFi>7000){
    lastWiFi=millis();WiFi.begin(WIFI_SSID,WIFI_PASSWORD);return;
  }
  if(WiFi.status()==WL_CONNECTED&&!mqtt.connected()&&millis()-lastMqtt>5000){
    lastMqtt=millis();
    String clientId=String("coldchain-")+DEVICE_ID+"-"+String(esp_random(),HEX);
    if(mqtt.connect(clientId.c_str())){mqtt.subscribe(topicAck.c_str(),1);mqtt.subscribe(topicCmd.c_str(),1);awaitingAck=false;}
  }
  if(mqtt.connected())mqtt.loop();
  if(awaitingAck&&millis()-pendingSent>5500)awaitingAck=false; // re-sign, retry identical seq, backend idempotent
  transmitHead();
}
void displayTick(){
  if(!oledReady)return;
  if(millis()-lastDisplay<800)return;lastDisplay=millis();
  oled.clearDisplay();oled.setTextColor(SSD1306_WHITE);oled.setTextSize(1);
  oled.setCursor(0,0);oled.print("COLDCHAIN ");oled.println(DEVICE_ID);
  oled.setTextSize(2);oled.setCursor(0,17);
  if(sensorOK){oled.print(tempC,1);oled.print(" C");}else oled.print("SENSOR!");
  oled.setTextSize(1);oled.setCursor(0,42);
  if(discardLatch||!sensorOK||tempC<2||tempC>8)oled.print("BREACH");
  else if(tempC>=7||doorOpen||!powerOK)oled.print("WARNING");
  else oled.print("SAFE");
  oled.setCursor(75,42);oled.print(mqtt.connected()?"MQTT":"OFFLINE");
  oled.setCursor(0,55);oled.print(powerOK?"MAINS ":"BATTERY ");
  oled.print("Q:");oled.print(queueCount());
  oled.display();
}
void serialDiagnostics(){
  static uint32_t lastPrint=0;
  if(millis()-lastPrint<5000)return;
  lastPrint=millis();
  Serial.printf("NODE=%s TEMP=%.2f SENSOR=%d DOOR=%d POWER=%d COMP=%d BAT=%d REDLATCH=%d QUEUEFAULT=%d QUEUE=%d WIFI=%d MQTT=%d MQTT_STATE=%d\n",
      DEVICE_ID,tempC,int(sensorOK),int(doorOpen),int(powerOK),int(compressor),
      batteryPercent(),int(discardLatch),int(queueFault),queueCount(),int(WiFi.status()),
      int(mqtt.connected()),mqtt.state());
  if(WiFi.status()==WL_CONNECTED){
    Serial.print("Node IPv4: ");Serial.println(WiFi.localIP());
  } else {
    Serial.println("Wi-Fi not connected. Check hotspot and secrets.h network settings.");
  }
  if(time(nullptr)<1700000000)Serial.println("Clock not synchronized: NTP/Internet or compatible RTC needed before signed samples.");
}
bool powerButtonPressed(){return digitalRead(PIN_POWER_BUTTON)==(POWER_OK_WHEN_HIGH?LOW:HIGH);}
void readPower(){
  if(!POWER_BUTTON_TOGGLES){powerOK=!powerButtonPressed();return;}
  // Momentary push button: each debounced press toggles the simulated mains failure.
  static bool lastPressed=false;static uint32_t lastEdge=0;
  bool pressed=powerButtonPressed();
  if(pressed!=lastPressed&&millis()-lastEdge>40){
    lastEdge=millis();lastPressed=pressed;
    if(pressed)powerOK=!powerOK;
  }
}
void setup(){
  Serial.begin(115200);
  Serial.printf("ColdChain firmware starting: %s\n",DEVICE_ID);
  pinMode(PIN_DOOR,INPUT_PULLUP);pinMode(PIN_POWER_BUTTON,INPUT_PULLUP);
  pinMode(PIN_RELAY,OUTPUT);pinMode(PIN_RED,OUTPUT);pinMode(PIN_GREEN,OUTPUT);pinMode(PIN_BUZZER,OUTPUT);
  digitalWrite(PIN_RELAY,RELAY_ACTIVE_LOW?HIGH:LOW);digitalWrite(PIN_BUZZER,LOW);
  lastRelayOff=millis()-COMPRESSOR_MIN_OFF_MS; // compressor initially off; safe allowed on at 7 C
  probe.begin();Wire.begin(PIN_OLED_SDA,PIN_OLED_SCL);
  oledReady=oled.begin(SSD1306_SWITCHCAPVCC,OLED_I2C_ADDRESS);
  if(!oledReady)Serial.println("WARN: OLED init failed; check I2C wiring/address.");
  if(!LittleFS.begin(true)){queueFault=true;}
  queuedCount=countQueueFile();
  settings.begin("coldchain",false);
  // Allocate new sequence block on every boot. Large monotonic gaps are intentional.
  seqNext=settings.getUInt("top",1000);settings.putUInt("top",seqNext+1000);
  discardLatch=settings.getBool("redLatch",false);
  topicData=String("coldchain/telemetry/")+DEVICE_ID;
  topicAck=String("coldchain/ack/")+DEVICE_ID;
  topicCmd=String("coldchain/cmd/")+DEVICE_ID;
  mqtt.setServer(MQTT_BROKER_IP,MQTT_BROKER_PORT);mqtt.setCallback(mqttCallback);mqtt.setBufferSize(768);
  WiFi.mode(WIFI_STA);WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  configTime(0,0,"pool.ntp.org","time.cloudflare.com");
  probe.requestTemperatures();tempC=probe.getTempCByIndex(0);
  sensorOK=(tempC>-50&&tempC<65);
  doorOpen=(digitalRead(PIN_DOOR)==(DOOR_OPEN_WHEN_LOW?LOW:HIGH));doorSince=millis();priorDoor=doorOpen;
}
void loop(){
  doorOpen=(digitalRead(PIN_DOOR)==(DOOR_OPEN_WHEN_LOW?LOW:HIGH));
  static bool priorPower=true;
  readPower();
  if(doorOpen&&!priorDoor)doorSince=millis();
  // Door and power changes are reported immediately, not at the next 5-second tick.
  bool changed=(doorOpen!=priorDoor)||(powerOK!=priorPower);
  priorDoor=doorOpen;priorPower=powerOK;
  if(changed||millis()-lastSample>=SAMPLE_MS){
    lastSample=millis();probe.requestTemperatures();float t=probe.getTempCByIndex(0);
    sensorOK=t>-50&&t<65;
    if(sensorOK)tempC=t;
    regulate();appendSample();
  }
  regulate();
  bool doorAlarm=doorOpen&&(uint32_t)(millis()-doorSince)>60000;
  digitalWrite(PIN_BUZZER,doorAlarm||!sensorOK||queueFault?HIGH:LOW);
  bool bad=discardLatch||!sensorOK||queueFault||tempC<2||tempC>8||!powerOK;
  digitalWrite(PIN_RED,bad?HIGH:LOW);
  digitalWrite(PIN_GREEN,!bad&&tempC<7?HIGH:LOW);
  networkTick();displayTick();serialDiagnostics();delay(25);
}
