"""Measured SMALL-LOAD HTTP check; no external API or production claims.

Spawns disposable local Uvicorn + SQLite and measures 60 concurrent-ish
low-risk helpdesk requests (6 workers, 10 questions each). It is explicitly
NOT an enterprise load / penetration test.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
import json,os,requests,secrets,socket,subprocess,sys,tempfile,time,statistics

ROOT=Path(__file__).resolve().parents[1]

def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]

def main():
    with tempfile.TemporaryDirectory(prefix='aihas-load-') as tmp:
        p=port();base=f'http://127.0.0.1:{p}'
        env={**os.environ,'AIHAS_DB':str(Path(tmp)/'load.db'),'SESSION_SECRET':secrets.token_hex(32),
            'AIHAS_ENV':'demo','RAG_MODE':'lexical','OPENAI_API_KEY':'','ENABLE_TOOL_CALLING':'0',
            'N8N_WEBHOOK_URL':''}
        proc=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(p)],
            cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            for _ in range(100):
                try:
                    if requests.get(base+'/api/health',timeout=1).status_code==200:break
                except requests.RequestException:pass
                time.sleep(.1)
            else:raise RuntimeError('Local benchmark server not ready')
            queries=['How do I troubleshoot VPN connection failures?',
                     'What should I do when email synchronization fails?',
                     'How to report an MFA lockout?','How can I access the office printer?',
                     'quantum entanglement starship propulsion']
            def worker(worker_id):
                session=requests.Session()
                login=session.post(base+'/api/login',json={'username':'employee','password':'Demo1234!'},timeout=8)
                if login.status_code!=200:return [{'ok':False,'elapsed_ms':0,'status':login.status_code,'login_failed':True}]
                values=[]
                for i in range(10):
                    begin=time.perf_counter()
                    try:
                        r=session.post(base+'/api/chat',json={'message':queries[(i+worker_id)%len(queries)]},timeout=12)
                        value=r.json()
                        values.append({'ok':r.status_code==200 and value.get('outcome') in ('answered','escalation_recommended'),
                                       'elapsed_ms':round((time.perf_counter()-begin)*1000,1),'status':r.status_code})
                    except requests.RequestException:
                        values.append({'ok':False,'elapsed_ms':round((time.perf_counter()-begin)*1000,1),'status':0})
                return values
            began=time.perf_counter()
            results=[]
            with ThreadPoolExecutor(max_workers=6) as pool:
                for fut in as_completed([pool.submit(worker,i) for i in range(6)]):
                    results.extend(fut.result())
            times=sorted(r['elapsed_ms'] for r in results)
            percentile=lambda x: times[min(len(times)-1,int(len(times)*x))] if times else 0
            report={'tested_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'scope':'SMALL-LOAD real local Uvicorn+SQLite; offline TF-IDF, synthetic users/docs, not production',
                'workers':6,'requests':len(results),'passed':sum(r['ok'] for r in results),
                'failed':sum(not r['ok'] for r in results),'p50_ms':round(statistics.median(times),1) if times else 0,
                'p95_ms':percentile(.95),'max_ms':max(times) if times else 0,
                'wall_time_seconds':round(time.perf_counter()-began,2),'passed_check':bool(results) and all(r['ok'] for r in results),
                'external_llm_verified':False,'enterprise_load_test':False}
            out=ROOT/'docs/evidence/load_smoke_v6.json';out.parent.mkdir(exist_ok=True,parents=True)
            out.write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps(report,indent=2))
            return 0 if report['passed_check'] else 1
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill()

if __name__=='__main__':raise SystemExit(main())
