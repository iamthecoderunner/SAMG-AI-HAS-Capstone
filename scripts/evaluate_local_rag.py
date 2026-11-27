"""Real local Ollama/Chroma mini-benchmark; no paid API or real employee records.

This evaluates: retrieval-hit and citation *format/source ID*, not human-judged
factual faithfulness. Runs on a disposable DB and Chroma path, out of process
so Windows can release Chroma SQLite before cleanup. Exit 0=all cases pass,
1=some cases fail, 2=prerequisites blocked.

COPY-PASTE TO TERMINAL (from AI-HAS):
 .\\.venv\\Scripts\\python.exe scripts\\evaluate_local_rag.py --quick
 .\\.venv\\Scripts\\python.exe scripts\\evaluate_local_rag.py --full
"""
from __future__ import annotations
import argparse,json,os,secrets,subprocess,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
CASE_FILE=ROOT/'tests'/'retrieval_cases.json'
OUTPUT=ROOT/'docs'/'evidence'/'live_rag_evaluation.json'

def grade_case(case,response):
    """Deterministic checks; never call this score hallucination rate."""
    if not isinstance(response,dict):
        return {'pass':False,'reason':'invalid_response'}
    expected=case.get('expected_title')
    refs=response.get('sources') or []
    ids=[str(d.get('id')) for d in refs]
    answer=str(response.get('answer') or '')
    mode=str(response.get('mode') or '')
    source_hit=any(d.get('title')==expected for d in refs) if expected else False
    cited=bool(refs) and all('['+id+']' in answer for id in ids)
    unexpected=bool(set(__import__('re').findall(r'\[(\d+)\]',answer))-set(ids))
    live_cited=mode=='semantic+ollama' and cited and not unexpected and response.get('outcome')=='answered'
    abstains=(response.get('outcome') in ('escalation_recommended','out_of_scope') and not refs)
    if expected:
        return {'pass':bool(source_hit and live_cited),'supported':True,
                'source_hit':source_hit,'valid_citation_ids':cited and not unexpected,
                'live_model_cited':live_cited,'abstained':False}
    return {'pass':bool(abstains),'supported':False,'source_hit':None,
            'valid_citation_ids':None,'live_model_cited':None,'abstained':bool(abstains)}

def aggregate(results):
    supported=[r for r in results if r['grade']['supported']]
    unsupported=[r for r in results if not r['grade']['supported']]
    frac=lambda num,den: round(num/den,4) if den else None
    return {'cases':len(results),'passed':sum(r['grade']['pass'] for r in results),
        'failed':sum(not r['grade']['pass'] for r in results),
        'supported_cases':len(supported),'unsupported_cases':len(unsupported),
        'observed_source_hit_rate':frac(sum(bool(r['grade']['source_hit']) for r in supported),len(supported)),
        'live_cited_answer_rate':frac(sum(bool(r['grade']['live_model_cited']) for r in supported),len(supported)),
        'unsupported_abstention_rate':frac(sum(bool(r['grade']['abstained']) for r in unsupported),len(unsupported)),
        'human_reviewed_faithfulness':'NOT YET MEASURED',
        'real_enterprise_mttr_improvement':'NOT YET MEASURED'}

def worker(path, output, full):
    from fastapi.testclient import TestClient
    temp=Path(path)
    os.environ.update({'AIHAS_DB':str(temp/'evaluation.sqlite3'),'CHROMA_PATH':str(temp/'chroma'),
        'AI_PROVIDER':'ollama','RAG_MODE':'semantic','REQUIRE_SEMANTIC_RAG':'1',
        'ENABLE_TOOL_CALLING':'0','AIHAS_ENV':'demo','OPENAI_API_KEY':'',
        'N8N_WEBHOOK_URL':'','SESSION_SECRET':secrets.token_urlsafe(48),
        'DEMO_EMPLOYEE_PASSWORD':secrets.token_urlsafe(20),
        'DEMO_AGENT_PASSWORD':secrets.token_urlsafe(20),
        'DEMO_ADMIN_PASSWORD':secrets.token_urlsafe(20)})
    from app.main import app
    cases=json.loads(CASE_FILE.read_text(encoding='utf-8'))
    if not full: cases=[cases[i] for i in [0,3,6,12,18,20]]
    result=[]
    try:
        with TestClient(app) as client:
            assert client.post('/api/login',json={'username':'employee','password':os.environ['DEMO_EMPLOYEE_PASSWORD']}).status_code==200
            for n,case in enumerate(cases,1):
                r=client.post('/api/chat',json={'message':case['query']},timeout=120)
                response=r.json() if r.status_code==200 else {}
                grade=grade_case(case,response)
                result.append({'case_id':f'RG-{n:02d}','question':case['query'],
                    'expected_sop':case['expected_title'],'http_status':r.status_code,
                    'observed_mode':response.get('mode'),'outcome':response.get('outcome'),
                    'source_titles':[s.get('title') for s in response.get('sources',[])],
                    'answer':response.get('answer'),'latency_ms':response.get('latency_ms'),'grade':grade})
                print(f"{n}/{len(cases)} {'PASS' if grade['pass'] else 'FAIL'} {case['query'][:52]}",flush=True)
    except Exception as e:
        result.append({'case_id':'SYSTEM','question':'','expected_sop':None,'http_status':0,
                       'grade':{'pass':False,'supported':False,'reason':type(e).__name__}})
    report={'executed_utc':datetime.now(timezone.utc).isoformat(),
        'environment':'Student computer, real Ollama + Chroma, isolated synthetic dataset',
        'evaluation_limits':'Corpus-specific and model/version-specific. Citation validity is not semantic faithfulness. Unsupported answers require manual review. No production claims.',
        'model':os.environ.get('OLLAMA_CHAT_MODEL','qwen3:4b'),
        'embed_model':os.environ.get('OLLAMA_EMBED_MODEL','nomic-embed-text'),
        'metrics':aggregate(result),'results':result}
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('REPORT:',output,flush=True)
    return 0 if report['metrics']['failed']==0 else 1

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--full',action='store_true',help='22 questions; takes longer')
    parser.add_argument('--quick',action='store_true',help='6 representative questions (default)')
    parser.add_argument('--worker-temp',help=argparse.SUPPRESS)
    parser.add_argument('--output',default=str(OUTPUT))
    args=parser.parse_args()
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT/'.env',override=False)
    except ImportError:pass
    if args.worker_temp:
        return worker(args.worker_temp,args.output,args.full)
    from scripts.verify_local_ai import preflight
    issues=preflight()
    if issues:
        print('BLOCKED: '+ '; '.join(issues));return 2
    try:
        with tempfile.TemporaryDirectory(prefix='aihas-rag-eval-',ignore_cleanup_errors=True) as temp:
            cmd=[sys.executable,str(Path(__file__).resolve()),'--worker-temp',temp,'--output',str(Path(args.output).resolve())]
            if args.full:cmd.append('--full')
            outcome=subprocess.run(cmd,check=False,timeout=1200)
            return outcome.returncode if outcome.returncode in (0,1,2) else 1
    except subprocess.TimeoutExpired:
        print('FAIL: evaluation timed out');return 1
if __name__=='__main__':raise SystemExit(main())
