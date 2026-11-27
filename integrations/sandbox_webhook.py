"""Independent signed webhook receiver for AI-HAS academic sandbox.

Real HTTP -> signature verification -> persisted notification queue.
It is NOT n8n, Jira, ServiceNow, or a production identity integration.
"""
import os
import json
import hmac
import hashlib
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from contextlib import contextmanager

app=FastAPI(title='AI-HAS Independent Sandbox Webhook',version='1.0')

def db_path():return Path(os.getenv('WEBHOOK_DEMO_DB','sandbox_webhook.db'))

@contextmanager
def db_conn():
    dest=db_path();dest.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(str(dest),timeout=10)
    con.row_factory=sqlite3.Row
    try:
        con.execute('''CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY, event_type TEXT NOT NULL, ticket_id INTEGER NOT NULL,
            category TEXT NOT NULL, created_at TEXT NOT NULL,
            UNIQUE(event_type,ticket_id))''')
        yield con
        con.commit()
    finally:con.close()

def authenticate(request,body):
    secret=os.getenv('WEBHOOK_TOKEN','')
    if len(secret)<16:raise HTTPException(503,'Webhook secret not configured')
    stamp=request.headers.get('X-AIHAS-Timestamp','')
    signature=request.headers.get('X-AIHAS-Signature','')
    if not stamp.isdecimal():raise HTTPException(401,'Missing signed timestamp')
    if abs(int(time.time())-int(stamp))>300:raise HTTPException(401,'Timestamp outside replay window')
    correct='sha256='+hmac.new(secret.encode(),stamp.encode()+b'.'+body,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature,correct):raise HTTPException(401,'Invalid webhook signature')

@app.get('/health')
def health():
    with db_conn() as con:con.execute('SELECT 1')
    return {'ok':True,'kind':'academic-sandbox-receiver'}

@app.post('/webhook/ticket')
async def receive(request:Request):
    body=await request.body()
    if len(body)>4096:raise HTTPException(413,'Webhook payload too large')
    authenticate(request,body)
    try:
        event=json.loads(body)
        if set(event)!={'event','ticket_id','category'}:raise ValueError('Unexpected payload fields')
        if event['event']!='ticket_created':raise ValueError('Unsupported event type')
        if type(event['ticket_id']) is not int or event['ticket_id']<1:raise ValueError('Invalid ticket ID')
        if not isinstance(event['category'],str) or not 2<=len(event['category'])<=80:raise ValueError('Invalid category')
    except (ValueError,TypeError):raise HTTPException(422,'Invalid event payload')
    with db_conn() as con:
        cur=con.execute('INSERT OR IGNORE INTO notifications(event_type,ticket_id,category,created_at) VALUES(?,?,?,?)',
            (event['event'],event['ticket_id'],event['category'],datetime.now(timezone.utc).isoformat()))
        return {'accepted':True,'created':cur.rowcount==1,'ticket_id':event['ticket_id'], 'action':'queued_agent_notification'}
