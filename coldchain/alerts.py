"""Real alert delivery only if configured; failures recorded and never reported as success."""
import os,smtplib,ssl,urllib.request,urllib.parse,json
from email.message import EmailMessage
from .db import now

def send_alert(con,fridge_id,message):
    token=os.getenv('TELEGRAM_BOT_TOKEN',''); chat=os.getenv('TELEGRAM_CHAT_ID','')
    host=os.getenv('SMTP_HOST',''); recipient=os.getenv('ALERT_EMAIL_TO','')
    status='not_configured'; channel='none'; detail=message
    try:
        if token and chat:
            channel='telegram'
            q=urllib.parse.urlencode({'chat_id':chat,'text':message}).encode()
            req=urllib.request.Request(f'https://api.telegram.org/bot{token}/sendMessage',data=q)
            with urllib.request.urlopen(req,timeout=8) as r:
                response=json.loads(r.read())
                if not response.get('ok'):raise RuntimeError('Telegram API rejected message')
            status='delivered'
        elif host and recipient:
            channel='email'; email=EmailMessage(); email['From']=os.getenv('SMTP_USERNAME','alerts@coldchain.local'); email['To']=recipient
            email['Subject']='ColdChain urgent door alert'; email.set_content(message)
            with smtplib.SMTP(host,int(os.getenv('SMTP_PORT','587')),timeout=8) as s:
                s.starttls(context=ssl.create_default_context())
                if os.getenv('SMTP_USERNAME'):s.login(os.getenv('SMTP_USERNAME'),os.getenv('SMTP_PASSWORD',''))
                s.send_message(email)
            status='delivered'
    except Exception as ex:
        status='failed'; detail=type(ex).__name__+': '+str(ex)[:180]
    con.execute('INSERT INTO alert_outbox(at,fridge_id,channel,status,detail) VALUES(?,?,?,?,?)',(now(),fridge_id,channel,status,detail))
    return status
