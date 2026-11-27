"""Focused regression checks for source privacy, request visibility, and readiness status."""
import importlib.util
import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import Mock

from app.main import minimize_pii, generate, llm_ticket_tool_request
from scripts.release_readiness import measure


def test_pii_is_masked_without_destroying_issue_topic():
    sample='My email is maria@example.org, phone +639171234567. VPN keeps failing.'
    result=minimize_pii(sample)
    assert 'maria@example.org' not in result
    assert '+639171234567' not in result
    assert 'VPN keeps failing' in result
    assert '[REDACTED EMAIL]' in result
    assert '[REDACTED PHONE]' in result


def test_ready_report_does_not_expose_secret(monkeypatch):
    fake='sk-fake-private-sample-not-real-0000000000'
    monkeypatch.setenv('OPENAI_API_KEY',fake)
    result=measure()
    assert fake not in json.dumps(result)
    assert result['api_key']=='configured_privately'
    assert result['live_ai_verification'] in ('BLOCKED','READY_TO_TEST_NOT_VERIFIED')
    assert result['public_deployment']=='NOT_VERIFIED'


def test_ready_to_test_never_claims_pass(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-key')
    monkeypatch.setenv('RAG_MODE','semantic')
    monkeypatch.setenv('REQUIRE_SEMANTIC_RAG','1')
    monkeypatch.setenv('ENABLE_TOOL_CALLING','1')
    monkeypatch.setattr(importlib.util,'find_spec',lambda name: object())
    result=measure()
    assert result['live_ai_verification']=='READY_TO_TEST_NOT_VERIFIED'
    assert 'PASS' not in json.dumps(result)


def test_model_generation_receives_minimized_prompt(monkeypatch):
    captured={}
    class Chat:
        def create(self,**kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='Use approved VPN SOP [1].'))])
    class Client:
        def __init__(self,**kwargs):
            self.chat=types.SimpleNamespace(completions=Chat())
    monkeypatch.setitem(sys.modules,'openai',types.SimpleNamespace(OpenAI=Client))
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-only')
    answer,mode=generate('Contact test.user@example.com or +639171234567 for VPN',
        [{'id':1,'title':'VPN SOP','body':'For VPN issues write to contact@example.com or +639178887777.'}])
    assert mode=='openai' and '[1]' in answer
    all_messages=' '.join(str(m['content']) for m in captured['messages'])
    assert 'test.user@example.com' not in all_messages
    assert 'contact@example.com' not in all_messages
    assert '+639171234567' not in all_messages
    assert '+639178887777' not in all_messages


def test_model_tool_call_receives_minimized_prompt(monkeypatch):
    captured={}
    class Chat:
        def create(self,**kwargs):
            captured.update(kwargs)
            call=types.SimpleNamespace(function=types.SimpleNamespace(name='create_support_ticket',arguments=json.dumps({'category':'VPN','description':'VPN client disconnects after startup'})))
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(tool_calls=[call]))])
    class Client:
        def __init__(self,**kwargs):self.chat=types.SimpleNamespace(completions=Chat())
    monkeypatch.setitem(sys.modules,'openai',types.SimpleNamespace(OpenAI=Client))
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-only')
    monkeypatch.setenv('ENABLE_TOOL_CALLING','1')
    payload=llm_ticket_tool_request('Please create a support ticket for VPN issue; contact employee@example.com')
    assert payload.category=='VPN'
    assert 'employee@example.com' not in captured['messages'][-1]['content']



def test_chat_history_does_not_store_detectable_email_or_phone():
    from tests.test_app import as_user
    from app.main import connection
    c=as_user('employee')
    result=c.post('/api/chat',json={'message':'VPN disconnects for test.user@example.com and +639171234567 on office WiFi'})
    assert result.status_code==200
    with connection() as db:
        row=db.execute('SELECT question,response FROM conversations ORDER BY id DESC LIMIT 1').fetchone()
    assert 'test.user@example.com' not in row['question']
    assert '+639171234567' not in row['question']
    assert '[REDACTED EMAIL]' in row['question']
    assert '[REDACTED PHONE]' in row['question']


def test_semantic_index_contract_with_test_doubles(monkeypatch,tmp_path):
    """Verifies vector ingestion/changes against in-memory doubles, NOT actual Chroma/OpenAI."""
    from app.main import semantic_retrieve
    collection={}
    class FakeCollection:
        def get(self,**kwargs): return {'ids':list(collection)}
        def delete(self,ids):
            for key in ids: collection.pop(key,None)
        def upsert(self,ids,documents,metadatas,embeddings):
            for key,document,metadata,vector in zip(ids,documents,metadatas,embeddings):
                collection[key]=(document,metadata,vector)
        def query(self,query_embeddings,n_results):
            # Transparent deterministic test double for a vector match.
            ranks=sorted(collection,key=lambda k:sum((x-y)**2 for x,y in zip(query_embeddings[0],collection[k][2])))
            ranks=ranks[:n_results]
            dists=[sum((x-y)**2 for x,y in zip(query_embeddings[0],collection[k][2])) for k in ranks]
            return {'ids':[ranks],'distances':[dists]}
    fake_col=FakeCollection()
    class FakeClient:
        def get_or_create_collection(self,*args,**kwargs): return fake_col
    def embedding(s):
        s=s.lower().replace('[redacted email]','').replace('[redacted phone]','')
        return [float('vpn' in s),float('email' in s),float('mfa' in s)]
    class Embeddings:
        def create(self,model,input):
            items=input if isinstance(input,list) else [input]
            assert all('tester@example.com' not in item for item in items)
            return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=embedding(item)) for item in items])
    class Client:
        def __init__(self,*args,**kwargs):self.embeddings=Embeddings()
    monkeypatch.setitem(sys.modules,'chromadb',types.SimpleNamespace(PersistentClient=lambda **kwargs:FakeClient()))
    monkeypatch.setitem(sys.modules,'openai',types.SimpleNamespace(OpenAI=Client))
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-only')
    monkeypatch.setenv('RAG_MODE','semantic')
    monkeypatch.setenv('CHROMA_PATH',str(tmp_path/'chroma'))
    docs=[{'id':1,'title':'VPN procedures','body':'Use approved VPN access. Contact tester@example.com for help.','version':1},
          {'id':2,'title':'Email issues','body':'Restart the email client and verify network service health.','version':1}]
    results=semantic_retrieve('VPN connection failure',docs)
    assert results and results[0]['id']==1
    assert len(collection)==2
    assert all('tester@example.com' not in item[0] for item in collection.values())
    docs[0]['body']='VPN setup requests must be reviewed by the approved IT administrator.'
    docs[0]['version']=2
    results=semantic_retrieve('VPN setup',docs)
    assert len(collection)==2 and results[0]['id']==1
    assert any(item[1]['version']==2 for item in collection.values())
