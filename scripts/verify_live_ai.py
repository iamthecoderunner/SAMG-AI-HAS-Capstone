"""Independently verify *real* external LLM, embeddings and function calling.

Runs in a temporary SQLite + Chroma directory. Never touches the user's demo DB.
Requires OPENAI_API_KEY set privately. Exit 0=PASS, 1=FAIL, 2=BLOCKED.
No sensitive key, raw API errors, or user chat content is written to evidence.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def preflight() -> tuple[bool, list[str]]:
    issues=[]
    if not os.getenv('OPENAI_API_KEY', '').strip():
        issues.append('OPENAI_API_KEY is absent; set it privately in .env or process environment.')
    try:
        import openai
        if not callable(getattr(openai, 'OpenAI', None)):
            raise ImportError('OpenAI SDK incomplete')
    except ImportError:
        issues.append('OpenAI SDK missing: pip install -r requirements.txt')
    try:
        import chromadb  # noqa: F401
    except ImportError:
        issues.append('ChromaDB missing: pip install -r requirements-semantic.txt')
    return not issues, issues


def persist(data: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n', encoding='utf-8')


def main() -> int:
    parser=argparse.ArgumentParser(description='Prove real API, semantic RAG and tool-calling end-to-end.')
    parser.add_argument('--preflight',action='store_true',help='Only check configuration and installed dependencies.')
    parser.add_argument('--output',default=str(ROOT/'docs'/'evidence'/'live_ai_verification.json'),help='Safe JSON evidence destination')
    args=parser.parse_args()
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT/'.env',override=False)
    except ImportError:
        pass
    ready, issues=preflight()
    if not ready:
        print('BLOCKED: external provider prerequisites are missing.')
        for issue in issues: print(' -',issue)
        print('No live LLM, embedding, or Chroma verification was performed.')
        return 2
    if args.preflight:
        print('READY: SDK, ChromaDB and private key configuration detected. No live API call performed.')
        return 0

    result={'started_at':utc(),'source':'real OpenAI API + real local ChromaDB via application endpoints',
            'status':'FAIL','model':os.getenv('OPENAI_MODEL','gpt-4o-mini'),
            'embedding_model':os.getenv('EMBEDDING_MODEL','text-embedding-3-small'),
            'checks':{}}
    with tempfile.TemporaryDirectory(prefix='aihas-live-verify-') as temp:
        # Prevent overwriting a user's local SQLite database, document collection, or demo log.
        os.environ.update({
            'AIHAS_DB':str(Path(temp)/'live_verification.db'),
            'CHROMA_PATH':str(Path(temp)/'chroma'),
            'AIHAS_ENV':'demo','RAG_MODE':'semantic','REQUIRE_SEMANTIC_RAG':'1',
            'ENABLE_TOOL_CALLING':'1', 'SESSION_SECRET':secrets.token_hex(32),
            'DEMO_EMPLOYEE_PASSWORD':secrets.token_urlsafe(20),
            'DEMO_AGENT_PASSWORD':secrets.token_urlsafe(20),
            'DEMO_ADMIN_PASSWORD':secrets.token_urlsafe(20),
            'N8N_WEBHOOK_URL':'',
        })
        try:
            from fastapi.testclient import TestClient
            from app.main import app, connection
            with TestClient(app) as c:
                login=c.post('/api/login',json={
                    'username':'employee','password':os.environ['DEMO_EMPLOYEE_PASSWORD']})
                assert login.status_code==200, 'login_failed'
                result['checks']['login']='PASS'
                ask=c.post('/api/chat',json={'message':'How do I troubleshoot a VPN connection failure?'},timeout=90)
                assert ask.status_code==200, 'rag_request_failed'
                rag=ask.json()
                sources=rag.get('sources',[])
                assert rag.get('mode')=='semantic+openai', f"rag_mode_not_live: {rag.get('mode')}"
                assert rag.get('outcome')=='answered', f"rag_outcome: {rag.get('outcome')}"
                assert sources and any('VPN' in x['title'] for x in sources),'vpn_sop_not_retrieved'
                assert any(f"[{x['id']}]" in rag['answer'] for x in sources),'citation_missing'
                result['checks']['semantic_rag']='PASS'
                result['rag']={'mode':rag['mode'],'outcome':rag['outcome'],
                               'sources':[{'id':x['id'],'title':x['title']} for x in sources],
                               'latency_ms':rag.get('latency_ms')}
                # Prove actual Chroma persistence, independent of model-returned labels.
                import chromadb
                chroma=chromadb.PersistentClient(path=os.environ['CHROMA_PATH'])
                count=chroma.get_collection('sops').count()
                assert count>=6, f'expected_at_least_six_indexed_sops_found_{count}'
                result['checks']['chroma_persistence']='PASS'
                result['indexed_sop_count']=count

                request=c.post('/api/chat',json={
                    'message':'Please create a support ticket for a VPN failure: VPN disconnects after an approved network change.',
                    'request_id':'independent-live-test-2026'},timeout=90)
                assert request.status_code==200, 'ticket_tool_request_failed'
                tool=request.json()
                assert tool.get('mode')=='openai_function_call', f"tool_mode: {tool.get('mode')}"
                assert tool.get('outcome')=='tool_ticket_created', f"tool_outcome: {tool.get('outcome')}"
                records=c.get('/api/tickets').json()
                assert len(records)==1 and records[0]['category']=='VPN','tool_ticket_not_persisted'
                result['checks']['live_function_call']='PASS'
                result['checks']['ticket_db_persistence']='PASS'
                result['tool']={'mode':tool['mode'],'outcome':tool['outcome'],
                                'ticket_id':records[0]['id'],'ticket_category':records[0]['category']}
                # Idempotency on replay is a backend control independent of the model.
                duplicate=c.post('/api/chat',json={
                    'message':'Please create a support ticket for a VPN failure: VPN disconnects after an approved network change.',
                    'request_id':'independent-live-test-2026'},timeout=90)
                assert duplicate.status_code==200, 'replay_failed'
                assert duplicate.json().get('outcome')=='tool_ticket_existing','replay_created_second_ticket'
                assert len(c.get('/api/tickets').json())==1,'duplicate_ticket_written'
                result['checks']['idempotent_tool_replay']='PASS'
                with connection() as db:
                    audit_events=db.execute("SELECT COUNT(*) FROM audit WHERE action='llm_tool_ticket_returned'").fetchone()[0]
                assert audit_events>=2,'tool_event_not_audited'
                result['checks']['audit']='PASS'
            result['status']='PASS'
        except Exception as exc:
            # Only error *type* and a restricted local assertion label; never raw exception
            # (provider errors may contain request data, endpoint info, or secrets).
            result['status']='FAIL'
            result['failure_type']=type(exc).__name__
            if isinstance(exc,AssertionError):
                label=str(exc)
                result['failure_label']=label[:150].split('\n')[0]
            print('FAIL:',result['failure_type'],result.get('failure_label','external integration error'))
    result['finished_at']=utc()
    persist(result, Path(args.output))
    print(f"{result['status']}: evidence written to {args.output}")
    if result['status']=='PASS':
        print('Live semantic RAG, cited model answer, native function call, Chroma indexing and durable ticket were verified.')
        return 0
    print('Do not claim live semantic RAG or tool calling passed. The evidence file records the failure.')
    return 1


if __name__=='__main__':
    raise SystemExit(main())
