"""Production MQTT ingestion: broker service should have ACLs, TLS, and broker auth."""
import json,os,time,secrets,hmac,hashlib
from .core import secret_for
from .core import ingest
class MQTTBridge:
    def __init__(self):self.client=None
    def start(self):
        try:import paho.mqtt.client as mqtt
        except ImportError as e:raise RuntimeError('pip install paho-mqtt to enable MQTT') from e
        client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='coldchain_backend',clean_session=True)
        if os.getenv('MQTT_USERNAME'):client.username_pw_set(os.getenv('MQTT_USERNAME'),os.getenv('MQTT_PASSWORD'))
        if os.getenv('MQTT_TLS','0')=='1':client.tls_set()
        def on_connect(c,userdata,flags,reason_code,properties):
            if reason_code==0:c.subscribe('coldchain/telemetry/+',qos=1)
        def on_message(c,userdata,msg):
            try:
                payload=json.loads(msg.payload)
                fid=msg.topic.rsplit('/',1)[-1]
                if payload.get('device_id')!=fid:return
                result=ingest(payload,'device')
                if result.get('accepted'):
                    sent=int(time.time());nonce=secrets.token_hex(8)
                    plain=f'{fid}|{result["seq"]}|{sent}|{nonce}'
                    sig=hmac.new(secret_for(fid).encode(),plain.encode(),hashlib.sha256).hexdigest()
                    c.publish('coldchain/ack/'+fid,json.dumps({'seq':result['seq'],'sent_at':sent,'nonce':nonce,'signature':sig}),qos=1)
                    from .app import publish_latch
                    publish_latch(fid)
            except Exception:
                # ingest() already logs invalid or duplicate signatures; never ACK rejected packets
                pass
        client.on_connect=on_connect;client.on_message=on_message
        client.connect_async(os.getenv('MQTT_HOST','localhost'),int(os.getenv('MQTT_PORT','1883')),keepalive=60)
        client.loop_start();self.client=client
    def publish_latch(self,fid,red):
        if self.client:
            sent=int(time.time());nonce=secrets.token_hex(8)
            plain=f'{fid}|{int(bool(red))}|{sent}|{nonce}'
            sig=hmac.new(secret_for(fid).encode(),plain.encode(),hashlib.sha256).hexdigest()
            self.client.publish('coldchain/cmd/'+fid,json.dumps({'discard_latch':bool(red),'sent_at':sent,'nonce':nonce,'signature':sig}),qos=1,retain=True)
    def stop(self):
        if self.client:self.client.loop_stop();self.client.disconnect()
