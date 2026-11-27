"""Local Ollama integration contract tests. The Ollama responder is a test double;
these tests do NOT establish a genuine local model is installed or inference passed.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
import pytest

from app.local_ai import base_url, local_request, ollama_embeddings, ollama_chat, LocalAIError
from app.main import generate, llm_ticket_tool_request, ai_provider
project_root = Path(__file__).resolve().parents[1]


class LocalFake(BaseHTTPRequestHandler):
    calls=[]
    def log_message(self, *args):pass
    def do_GET(self):
        if self.path!='/api/tags':return self.send_error(404)
        self.respond({'models':[{'name':'qwen3:4b'},{'name':'nomic-embed-text:latest'}]})
    def do_POST(self):
        size=int(self.headers.get('Content-Length','0'))
        payload=json.loads(self.rfile.read(size))
        type(self).calls.append((self.path,payload))
        if self.path=='/api/embed':
            value=payload['input']
            self.respond({'embeddings':[[float('vpn' in x.lower()),float('email' in x.lower())] for x in value]})
        elif self.path=='/api/chat':
            if payload.get('tools'):
                self.respond({'message':{'role':'assistant','content':'','tool_calls':[{'function':{'name':'create_support_ticket','arguments':{'category':'VPN','description':'VPN fails every morning at login'}}}]}})
            else:
                self.respond({'message':{'role':'assistant','content':'Restart the VPN client as in SOP [1].'}})
        else:self.send_error(404)
    def respond(self,data):
        content=json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(content)))
        self.end_headers()
        self.wfile.write(content)


@pytest.fixture
def fake_local_service(monkeypatch):
    LocalFake.calls.clear()
    server=ThreadingHTTPServer(('127.0.0.1',0),LocalFake)
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    monkeypatch.setenv('AI_PROVIDER','ollama')
    monkeypatch.setenv('OLLAMA_BASE_URL',f'http://127.0.0.1:{server.server_address[1]}')
    try:yield LocalFake
    finally:server.shutdown();server.server_close();t.join(timeout=2)


def test_local_ollama_http_contract_and_token_safe_prompts(fake_local_service,monkeypatch):
    monkeypatch.setenv('ENABLE_TOOL_CALLING','1')
    assert ai_provider()=='ollama'
    assert local_request('/api/tags')['models'][0]['name']=='qwen3:4b'
    assert len(ollama_embeddings(['a vpn error','email issue']))==2
    answer,mode=generate('VPN broken for analyst@example.org', [{'id':1,'title':'VPN SOP','body':'Restart client. Email helpdesk@example.org'}])
    assert mode=='ollama' and '[1]' in answer
    payload=llm_ticket_tool_request('Please create a support ticket for VPN issues for analyst@example.org')
    assert payload.category=='VPN'
    assert any('/api/embed'==path for path,_ in fake_local_service.calls)
    assert sum(path=='/api/chat' for path,_ in fake_local_service.calls)==2
    all_calls=json.dumps(fake_local_service.calls)
    assert 'analyst@example.org' not in all_calls
    assert 'helpdesk@example.org' not in all_calls
    assert 'tools' in fake_local_service.calls[-1][1]
    assert fake_local_service.calls[-1][1]['model']=='qwen3:4b'


def test_local_tool_without_valid_model_proposal_fails_closed(fake_local_service,monkeypatch):
    monkeypatch.setenv('ENABLE_TOOL_CALLING','1')
    with patch('app.local_ai.ollama_chat',return_value={'content':'no tool calls'}):
        assert llm_ticket_tool_request('Please create a support ticket for VPN issues') is None
    with patch('app.local_ai.ollama_chat',return_value={'tool_calls':[{'function':{'name':'erase_database','arguments':{}}}]}):
        assert llm_ticket_tool_request('Please create a support ticket for VPN issues') is None
    with patch('app.local_ai.ollama_chat',return_value={'tool_calls':[{'function':{'name':'create_support_ticket','arguments':{'category':'VPN','description':'My password: secret98765'}}}]}):
        assert llm_ticket_tool_request('Please create a support ticket for VPN issues') is None


def test_ollama_restricts_remote_endpoint_and_api_calls(monkeypatch):
    for bad in ('http://example.com:11434','https://127.0.0.1:11434','http://user:pass@localhost:11434','http://localhost:11434/private','http://169.254.169.254'):
        monkeypatch.setenv('OLLAMA_BASE_URL',bad)
        with pytest.raises(LocalAIError):base_url()
    monkeypatch.setenv('OLLAMA_BASE_URL','http://127.0.0.1:11434')
    with pytest.raises(LocalAIError):local_request('/api/delete',{})


def test_missing_local_provider_does_not_pretend_an_answer(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER','ollama')
    monkeypatch.setenv('OLLAMA_BASE_URL','http://127.0.0.1:11434')
    with patch('app.local_ai.local_request',side_effect=LocalAIError('not running')):
        answer,mode=generate('VPN help',[{'id':1,'title':'VPN SOP','body':'Restart VPN'}])
    assert answer is None and mode=='llm_error'


def test_v8_local_config_preserves_existing_secret(monkeypatch,tmp_path):
    """Actual config logic is exercised in subprocess to protect test state."""
    import subprocess,sys
    newproj=tmp_path/'testproject';(newproj/'scripts').mkdir(parents=True)
    original=project_root/'scripts/configure_free_ai.py'
    (newproj/'scripts/configure_free_ai.py').write_text(original.read_text())
    envfile=newproj/'.env'
    envfile.write_text('SESSION_SECRET=private-long-secret\nDEMO_EMPLOYEE_PASSWORD=do-not-override\nAI_PROVIDER=offline\nRAG_MODE=lexical\n')
    r=subprocess.run([sys.executable,str(newproj/'scripts/configure_free_ai.py')],capture_output=True,text=True)
    assert r.returncode==0
    config=envfile.read_text()
    assert 'SESSION_SECRET=private-long-secret' in config
    assert 'DEMO_EMPLOYEE_PASSWORD=do-not-override' in config
    assert 'AI_PROVIDER=ollama' in config
    assert 'RAG_MODE=semantic' in config
    assert 'ENABLE_TOOL_CALLING=1' in config
    assert 'private-long-secret' not in r.stdout


def test_full_browser_api_path_with_mock_ollama_and_mock_vector(fake_local_service,monkeypatch):
    """Request->local HTTP simulator->vector double->real API/SQLite.

    This does not prove Ollama model inference or real Chroma execution.
    """
    import sys,types
    from tests.test_app import as_user
    class FakeCollection:
        def __init__(self):self.store={}
        def get(self,**kwargs):return {'ids':list(self.store)}
        def delete(self,ids):
            for key in ids:self.store.pop(key,None)
        def upsert(self,ids,documents,metadatas,embeddings):
            for key,text,metadata,vector in zip(ids,documents,metadatas,embeddings):
                self.store[key]=(text,metadata,vector)
        def query(self,query_embeddings,n_results):
            q=query_embeddings[0]
            pairs=sorted([(sum((a-b)**2 for a,b in zip(q,v)),key) for key,(_,_,v) in self.store.items()])[:n_results]
            return {'ids':[[key for _,key in pairs]],'distances':[[dist for dist,_ in pairs]]}
    c=FakeCollection()
    class FakeClient:
        def __init__(self,**kwargs):pass
        def get_or_create_collection(self,*args,**kwargs):return c
    monkeypatch.setitem(sys.modules,'chromadb',types.SimpleNamespace(PersistentClient=FakeClient))
    monkeypatch.setenv('RAG_MODE','semantic')
    monkeypatch.setenv('REQUIRE_SEMANTIC_RAG','1')
    monkeypatch.setenv('ENABLE_TOOL_CALLING','1')
    client=as_user('employee')
    rag=client.post('/api/chat',json={'message':'How do I troubleshoot VPN connection failures?'})
    assert rag.status_code==200
    assert rag.json()['mode']=='semantic+ollama',rag.json()
    assert rag.json()['sources']
    with patch('app.main.dispatch_ticket_event',return_value='not_configured'):
        ticket=client.post('/api/chat',json={'message':'Please create a support ticket for VPN failing repeatedly today',
                                             'request_id':'v8-local-mock-end-to-end-01'})
    assert ticket.status_code==200 and ticket.json()['mode']=='ollama_function_call',ticket.json()
    tid=int(ticket.json()['answer'].split('#')[1].split()[0])
    assert any(x['id']==tid for x in client.get('/api/tickets').json())
