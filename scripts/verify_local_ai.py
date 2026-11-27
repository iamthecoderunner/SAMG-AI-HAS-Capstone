"""Verify actual Ollama + Chroma AI-HAS on an isolated database.

Exit 0=PASS; 1=FAIL; 2=BLOCKED. The verifier process is isolated from
its parent so Windows releases ChromaDB/SQLite handles before cleanup.
No API keys are required and the existing AI-HAS database is not modified.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import secrets
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def preflight():
    missing = []
    if importlib.util.find_spec('chromadb') is None:
        missing.append('ChromaDB is not installed (pip install -r requirements-semantic.txt).')
    try:
        from app.local_ai import local_request
        response = local_request('/api/tags', timeout=5)
        names = {v.get('name', '') for v in response.get('models', [])}
        for model in [os.getenv('OLLAMA_CHAT_MODEL', 'qwen3:4b'),
                      os.getenv('OLLAMA_EMBED_MODEL', 'nomic-embed-text')]:
            if model not in names and model + ':latest' not in names:
                missing.append('Local Ollama model is not downloaded: ' + model)
    except Exception:
        missing.append('Ollama localhost service is unavailable. Open the Ollama application.')
    return missing


def verify_in_worker(temp, output):
    """Run independent live checks in an isolated process to release SQLite locks."""
    temp = Path(temp)
    record = {
        'checked_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'provider': 'ollama', 'status': 'FAIL', 'checks': {}, 'failures': [],
        'chat_model': os.getenv('OLLAMA_CHAT_MODEL', 'qwen3:4b'),
        'embed_model': os.getenv('OLLAMA_EMBED_MODEL', 'nomic-embed-text'),
    }
    os.environ.update({
        'AIHAS_DB': str(temp / 'verification.db'),
        'CHROMA_PATH': str(temp / 'chroma'),
        'AI_PROVIDER': 'ollama', 'RAG_MODE': 'semantic', 'REQUIRE_SEMANTIC_RAG': '1',
        'ENABLE_TOOL_CALLING': '1', 'AIHAS_ENV': 'demo', 'N8N_WEBHOOK_URL': '',
        'SESSION_SECRET': secrets.token_urlsafe(48),
        'DEMO_EMPLOYEE_PASSWORD': secrets.token_urlsafe(18),
        'DEMO_AGENT_PASSWORD': secrets.token_urlsafe(18),
        'DEMO_ADMIN_PASSWORD': secrets.token_urlsafe(18),
    })

    def check(name, condition, reason):
        record['checks'][name] = 'PASS' if condition else 'FAIL'
        if not condition:
            record['failures'].append(reason)
        return bool(condition)

    try:
        from fastapi.testclient import TestClient
        from app.main import app, connection, vector_collection_name
        with TestClient(app) as client:
            resp = client.post('/api/login', json={
                'username': 'employee', 'password': os.environ['DEMO_EMPLOYEE_PASSWORD']})
            if not check('login', resp.status_code == 200, 'login_failed'):
                raise RuntimeError('login_failed')

            # Check live retrieval and LLM output independently. A safe SOP
            # fallback means semantic lookup worked, but does NOT pass the
            # live LLM citation test.
            rag = client.post('/api/chat', json={
                'message': 'How do I troubleshoot VPN connection failures?'})
            if check('rag_http', rag.status_code == 200, 'rag_http_failed'):
                data = rag.json()
                mode = str(data.get('mode', ''))
                answer = str(data.get('answer', ''))
                sources = data.get('sources') or []
                record['rag'] = {
                    'observed_mode': mode, 'outcome': data.get('outcome'),
                    'source_titles': [x.get('title') for x in sources],
                    'latency_ms': data.get('latency_ms'),
                }
                retrieval_ok = (mode.startswith('semantic+') and
                                any('VPN' in x.get('title', '') for x in sources))
                check('semantic_retrieval', retrieval_ok, 'semantic_retrieval_failed')
                llm_ok = (mode == 'semantic+ollama' and data.get('outcome') == 'answered'
                          and '<think' not in answer.lower()
                          and '</think' not in answer.lower()
                          and not answer.lower().startswith('we are given')
                          and bool(sources)
                          and all('[' + str(x['id']) + ']' in answer for x in sources))
                check('ollama_cited_generation', llm_ok,
                      'live_model_did_not_generate_valid_cited_answer: ' + mode)

            # Independent real ChromaDB check: a model citation failure must
            # not conceal that embeddings and vector storage work.
            try:
                import chromadb
                chroma = chromadb.PersistentClient(path=os.environ['CHROMA_PATH'])
                count = chroma.get_collection(vector_collection_name()).count()
                record['indexed_chunk_count'] = count
                check('real_chroma_index', count >= 6, 'vector_chunks_missing')
            except Exception:
                check('real_chroma_index', False, 'vector_store_unavailable')

            # Independently check genuine local LLM tool calling, then DB
            # persistence and idempotency, even when RAG citation fails.
            tool_body = {
                'message': 'Please create a support ticket for my VPN connection failing repeatedly after startup.',
                'request_id': 'ollama-verified-ticket-0001',
            }
            req = client.post('/api/chat', json=tool_body)
            tool_ok = req.status_code == 200
            result = req.json() if tool_ok else {}
            record['tool'] = {'observed_mode': result.get('mode'),
                              'outcome': result.get('outcome')}
            tool_ok = (tool_ok and result.get('mode') == 'ollama_function_call'
                       and result.get('outcome') == 'tool_ticket_created')
            check('ollama_function_call', tool_ok, 'live_model_did_not_invoke_ticket_tool')
            if tool_ok:
                rows = client.get('/api/tickets').json()
                check('ticket_persistence', len(rows) == 1 and rows[0]['category'] == 'VPN',
                      'ticket_persistence_failed')
                replay = client.post('/api/chat', json=tool_body)
                is_replay = (replay.status_code == 200
                             and replay.json().get('outcome') == 'tool_ticket_existing'
                             and len(client.get('/api/tickets').json()) == 1)
                check('idempotency', is_replay, 'idempotency_failed')
                with connection() as db:
                    n = db.execute("SELECT COUNT(*) FROM audit WHERE action='llm_tool_ticket_returned'").fetchone()[0]
                check('audit', n >= 2, 'audit_missing')
    except Exception as e:
        record['failure_type'] = type(e).__name__
        if isinstance(e, AssertionError):
            record['failures'].append('assertion_failed')
        elif not record['failures']:
            record['failures'].append('unexpected_check_exception')

    record['status'] = 'PASS' if record['checks'] and all(
        v == 'PASS' for v in record['checks'].values()) and not record['failures'] else 'FAIL'
    dest = Path(output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    if record['status'] == 'PASS':
        print('PASS: ' + ', '.join(record['checks']), flush=True)
    else:
        print('FAIL: ' + ', '.join(record['failures']) +
              ' (details in docs/evidence/local_ai_verification.json)', flush=True)
    return 0 if record['status'] == 'PASS' else 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--output', default=str(ROOT / 'docs/evidence/local_ai_verification.json'))
    parser.add_argument('--worker-temp', help=argparse.SUPPRESS)
    options = parser.parse_args()
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / '.env', override=False)
    except ImportError:
        pass
    if options.worker_temp:
        return verify_in_worker(options.worker_temp, options.output)
    issues = preflight()
    if issues:
        print('BLOCKED: Local AI prerequisites not ready:')
        for issue in issues:
            print(' - ' + issue)
        return 2
    if options.preflight:
        print('READY TO TEST: local Ollama models and ChromaDB detected (not a test PASS).')
        return 0

    # Keep Chroma's SQLite handles in a separate interpreter. When that
    # interpreter exits, Windows releases them BEFORE TemporaryDirectory cleanup.
    try:
        with tempfile.TemporaryDirectory(prefix='aihas-local-verify-',
                                         ignore_cleanup_errors=True) as temp:
            worker = subprocess.run([
                sys.executable, str(Path(__file__).resolve()), '--worker-temp', temp,
                '--output', str(Path(options.output).resolve()),
            ], check=False, timeout=900)
            return worker.returncode if worker.returncode in (0, 1, 2) else 1
    except subprocess.TimeoutExpired:
        print('FAIL: Local verification timed out (no successful live AI claim).')
        return 1
    except OSError as exc:
        print('FAIL: Could not launch isolated verifier: ' + type(exc).__name__)
        return 1


if __name__ == '__main__':
    sys.exit(main())
