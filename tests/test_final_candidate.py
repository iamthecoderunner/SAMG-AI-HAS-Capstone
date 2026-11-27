"""Release-candidate guards for misleading retrieval and true agent escalation."""
from unittest.mock import patch
from tests.test_app import as_user
from app.main import chunk_document, connection, scope_guard


def test_scope_guard_rejects_unsupported_free_vpn_question():
    client=as_user('employee')
    result=client.post('/api/chat',json={'message':'How do I get free vpn'})
    assert result.status_code==200
    output=result.json()
    assert output['outcome']=='out_of_scope'
    assert output['mode']=='scope_guard'
    assert output['sources']==[]
    assert 'free VPN' in output['answer']


def test_scope_guard_does_not_block_valid_vpn_troubleshooting():
    assert scope_guard('How do I troubleshoot VPN connection failures?') is None
    result=as_user('employee').post('/api/chat',json={'message':'How do I troubleshoot VPN connection failures?'})
    assert result.json()['outcome']=='answered'
    assert result.json()['sources']


def test_scope_guard_detects_unsupported_vpn_installation():
    result=as_user('employee').post('/api/chat',json={'message':'Can I download and install VPN software on my phone?'})
    assert result.json()['outcome']=='out_of_scope'
    assert result.json()['sources']==[]


def test_explicit_human_escalation_is_persistent_and_in_queue():
    employee=as_user('employee');agent=as_user('agent')
    key='user-escalation-check-2026'
    payload={'message':'Unknown VPN error 407 after router replacement','category':'VPN'}
    result=employee.post('/api/escalations',json=payload,headers={'Idempotency-Key':key})
    assert result.status_code==201
    assert result.json()['created'] is True
    assert result.json()['status']=='escalated'
    tid=result.json()['id']
    assert employee.get('/api/tickets').status_code==200
    assert any(t['id']==tid and t['status']=='escalated' for t in agent.get('/api/tickets').json())
    history=agent.get(f'/api/tickets/{tid}/history').json()
    assert len(history)==1 and history[0]['new_status']=='escalated'
    with connection() as db:
        assert db.execute('SELECT COUNT(*) AS count FROM audit WHERE action=? AND target=?',
                          ('human_escalation_requested',str(tid))).fetchone()['count']==1
    again=employee.post('/api/escalations',json=payload,headers={'Idempotency-Key':key})
    assert again.status_code==201
    assert again.json()['id']==tid and again.json()['created'] is False
    changed=employee.post('/api/escalations',json={'message':'New VPN error 444', 'category':'VPN'},headers={'Idempotency-Key':key})
    assert changed.status_code==409


def test_escalation_protects_against_secret_leaks():
    client=as_user('employee')
    bad=client.post('/api/escalations',json={'message':'My password is SeCrEt_123123','category':'VPN'})
    assert bad.status_code==422
    bad_category=client.post('/api/escalations',json={'message':'Unsupported operation','category':'RootAccess'})
    assert bad_category.status_code==422


def test_semantic_chunks_keep_bounded_length_and_overlap():
    original=('Approved troubleshooting: Check link connectivity. Restart VPN client safely. '*70).strip()
    segments=chunk_document(original,max_chars=400,overlap=60)
    assert len(segments)>3
    assert all(0<len(c)<=400 for c in segments)
    assert segments[0].startswith('Approved troubleshooting')
    assert 'Restart VPN client' in segments[-1]
    assert chunk_document('')==[]


def test_frontend_offers_real_human_escalation_action():
    page=as_user('employee').get('/').text
    assert 'Create agent escalation ticket' in page
    assert "api('escalations','POST'" in page


def test_no_llm_tool_invoked_for_out_of_scope_vpn():
    with patch('app.main.llm_ticket_tool_request') as tool:
        response=as_user('employee').post('/api/chat',json={'message':'where can I buy free VPN for gaming?'})
    assert response.json()['outcome']=='out_of_scope'
    tool.assert_not_called()


def test_semantic_vector_contract_is_chunked_cited_and_stale_safe(monkeypatch, tmp_path):
    """Mock only the external vector/embedding SDKs; verify application glue."""
    import sys, types
    from app.main import semantic_retrieve
    monkeypatch.setenv('OPENAI_API_KEY','synthetic_test_key')
    monkeypatch.setenv('RAG_MODE','semantic')
    monkeypatch.setenv('CHROMA_PATH',str(tmp_path/'chroma'))

    class Collection:
        def __init__(self):self.records={};self.deleted=[]
        def get(self,include):return {'ids':list(self.records)}
        def delete(self,ids):
            self.deleted+=ids
            for i in ids:self.records.pop(i,None)
        def upsert(self,ids,documents,metadatas,embeddings):
            assert len(ids)==len(documents)==len(metadatas)==len(embeddings)
            self.records.update({i:(text,metadata) for i,text,metadata in zip(ids,documents,metadatas)})
        def query(self,query_embeddings,n_results):
            keys=list(self.records)[:n_results]
            return {'ids':[keys],'distances':[[0.1 for _ in keys]]}
    collection=Collection()
    fake_chroma=types.SimpleNamespace(PersistentClient=lambda path:types.SimpleNamespace(
        get_or_create_collection=lambda name,metadata:collection))
    class Client:
        def __init__(self,**kw):
            self.embeddings=types.SimpleNamespace(create=lambda model,input:types.SimpleNamespace(
                data=[types.SimpleNamespace(embedding=[0.1,0.2]) for _ in ([input] if isinstance(input,str) else input)]))
    monkeypatch.setitem(sys.modules,'chromadb',fake_chroma)
    monkeypatch.setitem(sys.modules,'openai',types.SimpleNamespace(OpenAI=Client))
    docs=[{'id':941,'title':'Network VPN SOP','body':'Reconnect VPN client after an error. '*85,'version':1}]
    results=semantic_retrieve('VPN connection error',docs)
    assert len(collection.records)>=2
    assert len(results)==1 and results[0]['id']==941
    assert results[0]['chunk_id'] in collection.records
    assert results[0]['score']==0.9
    before=set(collection.records)
    docs[0]['body']='New approved guidance. '*85
    docs[0]['version']=2
    rerun=semantic_retrieve('VPN connection error',docs)
    assert rerun and before.issubset(set(collection.deleted))
    assert before.isdisjoint(set(collection.records))
