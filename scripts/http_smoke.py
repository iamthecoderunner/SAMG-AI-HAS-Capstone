"""Live HTTP/SQLite smoke test with a disposable local Uvicorn server.
Never contacts external model/webhook services. Saves a sanitized evidence report.
"""
import os, sys, json, time, tempfile, subprocess, socket, secrets
from datetime import datetime, timezone
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='aihas-http-') as temp:
    db=str(Path(temp)/'http_test.db')
    env={**os.environ,'AIHAS_DB':db,'AIHAS_ENV':'demo','RAG_MODE':'lexical',
         'REQUIRE_SEMANTIC_RAG':'0','SESSION_SECRET':secrets.token_hex(40),
         'N8N_WEBHOOK_URL':'','OPENAI_API_KEY':'','ENABLE_TOOL_CALLING':'0'}
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port=sock.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    checks=[]
    def server():
        return subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port)],
            cwd=str(ROOT), env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    def ready():
        for _ in range(50):
            try:
                if requests.get(base+'/api/health',timeout=1).status_code==200:return
            except requests.RequestException:pass
            time.sleep(.1)
        raise RuntimeError('HTTP server could not start')
    proc=server()
    try:
        ready()
        session=requests.Session()
        def call(method,path,**kwargs):
            return session.request(method,base+path,timeout=3,**kwargs)
        h=call('GET','/api/health').json()
        assert h['status']=='ok' and h['db']=='ok'
        checks.append('HTTP health endpoint + real SQLite connection')
        assert call('GET','/api/tickets').status_code==401
        checks.append('Unauthorized ticket list is denied')
        r=call('POST','/api/login',json={'username':'employee','password':'Demo1234!'})
        assert r.status_code==200
        checks.append('Cookie-based employee login via real HTTP')
        chat=call('POST','/api/chat',json={'message':'How to troubleshoot VPN connection failures?'}).json()
        assert chat['sources'] and chat['outcome']=='answered' and isinstance(chat['conversation_id'],int)
        checks.append('Offline grounded SOP response + source IDs via HTTP')
        feedback_id=chat['conversation_id']
        feedback=call('POST',f'/api/conversations/{feedback_id}/feedback',json={'resolved':True})
        assert feedback.status_code==201 and feedback.json()['resolved'] is True
        assert call('POST',f'/api/conversations/{feedback_id}/feedback',json={'resolved':False}).status_code==409
        checks.append('Real HTTP answer-resolution feedback + duplicate prevention')
        issue={'category':'VPN','description':'Helpdesk VPN fails to connect in the test environment'}
        r=call('POST','/api/tickets',json=issue,headers={'Idempotency-Key':'http-smoke-retry-2026'})
        assert r.status_code==201
        ticket_id=r.json()['id']
        r2=call('POST','/api/tickets',json=issue,headers={'Idempotency-Key':'http-smoke-retry-2026'})
        assert r2.json()['id']==ticket_id and r2.json()['created'] is False
        checks.append('Real HTTP ticket create + idempotent retry')
        assert call('PATCH',f'/api/tickets/{ticket_id}',json={'status':'resolved'}).status_code==403
        checks.append('RBAC blocks employee ticket mutation')
        approval=call('POST','/api/approvals',json={'request_type':'software_access','details':'Need a trial design application for mock employee'}).json()
        assert approval['status']=='pending'
        approval_id=approval['id']
        checks.append('Approval request persists via HTTP')
        session=requests.Session()
        assert call('POST','/api/login',json={'username':'agent','password':'Demo1234!'}).status_code==200
        assert call('PATCH',f'/api/tickets/{ticket_id}',json={'status':'escalated'}).json()['status']=='escalated'
        assert call('POST',f'/api/approvals/{approval_id}/decision',json={'decision':'approved'}).json()['execution']=='simulated_only'
        dashboard=call('GET','/api/metrics')
        assert dashboard.status_code==200
        assert dashboard.json()['confirmed_resolved']==1 and dashboard.json()['feedback_responses']==1
        checks.append('Agent state transition + simulated approval + live KPI aggregation')
        proc.terminate();proc.wait(timeout=6)
        proc=server();ready()
        session=requests.Session()
        assert call('POST','/api/login',json={'username':'employee','password':'Demo1234!'}).status_code==200
        tickets=call('GET','/api/tickets').json()
        assert any(t['id']==ticket_id and t['status']=='escalated' for t in tickets)
        approvals=call('GET','/api/approvals').json()
        assert any(a['id']==approval_id and a['status']=='approved' for a in approvals)
        checks.append('Ticket and approval persist across complete server restart')
        session=requests.Session()
        assert call('POST','/api/login',json={'username':'agent','password':'Demo1234!'}).status_code==200
        assert call('GET','/api/metrics').json()['confirmed_resolved']==1
        checks.append('Self-reported resolution counter persists after server restart')
        session=requests.Session()
        assert call('POST','/api/login',json={'username':'admin','password':'Demo1234!'}).status_code==200
        assert any(r['resource_id']==ticket_id for r in call('GET','/api/outbox').json())
        checks.append('Admin outbox reflects persisted webhook event')
        report={'executed_utc':datetime.now(timezone.utc).isoformat(),'test':'Real local Uvicorn HTTP, browser cookie-compatible requests, SQLite; no external API',
               'all_passed':True,'checks':checks,'count':len(checks),'external_llm_verified':False,'external_webhook_verified':False}
        evidence=ROOT/'docs/evidence/http_smoke_v3.json'
        evidence.write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill()
