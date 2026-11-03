"""Publish and receive one diagnostic MQTT message; never forge device telemetry."""
import argparse
import os
import secrets
import sys
import time

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=1883)
    args=parser.parse_args()
    try:import paho.mqtt.client as mqtt
    except ImportError:
        print('[FAIL] paho-mqtt missing: run START_DEMO_WINDOWS.bat once first.')
        return 1
    nonce=secrets.token_hex(10)
    topic='coldchain/diagnostics/'+nonce
    ok={'message':False,'connected':False}
    client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='coldchain_diagnostic_'+nonce)
    def on_connect(cl,userdata,flags,reason_code,properties):
        if reason_code==0:
            ok['connected']=True
            cl.subscribe(topic,qos=1)
        else:print('[FAIL] Broker rejected connection:', reason_code)
    def on_subscribe(cl,userdata,mid,reason_codes,properties):
        cl.publish(topic,nonce,qos=1)
    def on_message(cl,userdata,message):
        if message.topic==topic and message.payload.decode(errors='replace')==nonce:
            ok['message']=True
    client.on_connect=on_connect;client.on_message=on_message;client.on_subscribe=on_subscribe
    try:
        client.connect(args.host,args.port,keepalive=10)
        client.loop_start()
        deadline=time.monotonic()+7
        while not ok['message'] and time.monotonic()<deadline:
            time.sleep(0.15)
    except Exception as e:
        print('[FAIL] MQTT broker diagnostic connection error:',str(e));return 1
    finally:
        try:client.loop_stop();client.disconnect()
        except Exception:pass
    if not ok['message']:
        print('[FAIL] TCP/MQTT may be connected but test subscribe/publish echo did not return.')
        return 1
    print('[PASS] MQTT local broker subscribe/publish diagnostic succeeded.')
    print('This is NOT real ESP32 telemetry validation. Use CHECK_LIVE_TELEMETRY after flashing.')
    return 0
if __name__=='__main__':raise SystemExit(main())
