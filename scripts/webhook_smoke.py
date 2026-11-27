"""Real dual-Uvicorn-process signed webhook integration smoke test.
No paid API or external n8n is contacted. This tests a genuine HTTP integration.
"""
import os, sys, json, time, tempfile, subprocess, socket, secrets, sqlite3, hmac, hashlib
from pathlib import Path
from datetime import datetime, timezone
import requests
ROOT=Path(__file__).resolve().parents[1]

def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

def start(module,port,env):
    return subprocess.Popen([sys.executable,'-m','uvicorn',module,'--host','127.0.0.1','--port',str(port)],
        cwd=str(ROOT),env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)

def wait_health(url):
    for _ in range(60):
        try:
            if requests.get(url,timeout=1).status_code==200:return
        except requests.RequestException:pass
        time.sleep(.1)
    raise RuntimeError('Health endpoint unavailable: '+url)

with tempfile.TemporaryDirectory(prefix='aihas-webhook-') as tmp:
    token=secrets.token_hex(30)
    main_port,hook_port=free_port(),free_port()
    receiver_db=str(Path(tmp)/'receiver.db')
    common={**os.environ,'AIHAS_ENV':'demo','WEBHOOK_TOKEN':token}
    receiver_env={**common,'WEBHOOK_DEMO_DB':receiver_db}
    main_env={**common,'AIHAS_DB':str(Path(tmp)/'app.db'),'SESSION_SECRET':secrets.token_hex(40),
        'N8N_WEBHOOK_URL':f'http://127.0.0.1:{hook_port}/webhook/ticket',
        'ALLOW_HTTP_WEBHOOK':'1','OPENAI_API_KEY':'','ENABLE_TOOL_CALLING':'0'}
    receiver=start('integrations.sandbox_webhook:app',hook_port,receiver_env)
    main=None
    try:
        wait_health(f'http://127.0.0.1:{hook_port}/health')
        main=start('app.main:app',main_port,main_env)
        wait_health(f'http://127.0.0.1:{main_port}/api/health')
        user=requests.Session()
        assert user.post(f'http://127.0.0.1:{main_port}/api/login',json={'username':'employee','password':'Demo1234!'},timeout=4).status_code==200
        payload={'category':'VPN','description':'Test user cannot connect with sandbox VPN'}
        headers={'Idempotency-Key':'independent-real-webhook-001'}
        r=user.post(f'http://127.0.0.1:{main_port}/api/tickets',json=payload,headers=headers,timeout=8)
        assert r.status_code==201 and r.json()['webhook_status']=='sent',r.text
        ticket=r.json()['id']
        again=user.post(f'http://127.0.0.1:{main_port}/api/tickets',json=payload,headers=headers,timeout=8)
        assert again.json()['id']==ticket and again.json()['created'] is False
        with sqlite3.connect(receiver_db) as db:
            rows=db.execute('SELECT event_type,ticket_id,category FROM notifications').fetchall()
            assert rows==[('ticket_created',ticket,'VPN')], rows
        fake=requests.post(f'http://127.0.0.1:{hook_port}/webhook/ticket',
            json={'event':'ticket_created','ticket_id':9999,'category':'Other'},timeout=4)
        assert fake.status_code==401
        # Also verify the real receiver rejects a signed but stale event.
        stale_stamp=str(int(time.time())-900)
        body=b'{"event":"ticket_created","ticket_id":9999,"category":"Other"}'
        sig='sha256='+hmac.new(token.encode(),stale_stamp.encode()+b'.'+body,hashlib.sha256).hexdigest()
        stale=requests.post(f'http://127.0.0.1:{hook_port}/webhook/ticket',data=body,
            headers={'X-AIHAS-Timestamp':stale_stamp,'X-AIHAS-Signature':sig,'Content-Type':'application/json'},timeout=4)
        assert stale.status_code==401
        report={'executed_at_utc':datetime.now(timezone.utc).isoformat(),
            'integration':'Two independent local HTTP services (AI-HAS and independent sandbox webhook receiver)',
            'checks':{'real_http_delivery':True,'signature_verified':True,'notification_persisted':True,
                      'idempotent_retry_no_duplicate':True,'unsigned_request_rejected':True,'expired_request_rejected':True},
            'result':'PASS','n8n_verified':False,'jira_verified':False,'production_verified':False}
        (ROOT/'docs/evidence/webhook_integration_v3.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))
    finally:
        for proc in [main,receiver]:
            if proc and proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill()
