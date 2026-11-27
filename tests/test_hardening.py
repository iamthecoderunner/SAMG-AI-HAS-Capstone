"""Additional regression checks for production-oriented academic controls."""
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app, TicketIn, validate_runtime_config
from tests.test_app import as_user


def test_ticket_idempotency_and_conflicting_retry():
    client=as_user('employee')
    payload={'category':'VPN','description':'The enterprise VPN disconnects after login'}
    key='request-c0d41a8b-01'
    first=client.post('/api/tickets',json=payload,headers={'Idempotency-Key':key})
    assert first.status_code==201 and first.json()['created'] is True
    second=client.post('/api/tickets',json=payload,headers={'Idempotency-Key':key})
    assert second.status_code==201 and second.json()['created'] is False
    assert second.json()['id']==first.json()['id']
    assert second.json()['webhook_status']=='not_repeated'
    changed=client.post('/api/tickets',json={'category':'Email','description':'Different request text'},headers={'Idempotency-Key':key})
    assert changed.status_code==409
    row=[r for r in client.get('/api/tickets').json() if r['id']==first.json()['id']]
    assert len(row)==1 and row[0]['description']==payload['description']


def test_ticket_persists_after_fresh_client_session():
    original=as_user('employee')
    payload={'category':'Email','description':'Email account sync is failing on desktop'}
    ticket_id=original.post('/api/tickets',json=payload).json()['id']
    next_client=as_user('employee')
    actual=next(r for r in next_client.get('/api/tickets').json() if r['id']==ticket_id)
    assert actual['category']=='Email' and actual['description']==payload['description']


def test_semantic_required_fails_closed_when_provider_missing(monkeypatch):
    monkeypatch.setenv('REQUIRE_SEMANTIC_RAG','1')
    monkeypatch.setenv('RAG_MODE','semantic')
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    client=as_user('employee')
    response=client.post('/api/chat',json={'message':'How should I troubleshoot VPN issues?'})
    assert response.status_code==200
    assert response.json()['mode']=='semantic_unavailable+no_context'
    assert response.json()['outcome']=='escalation_recommended'
    assert response.json()['sources']==[]


def test_foreign_origin_is_rejected_on_authenticated_mutation():
    client=as_user('admin')
    response=client.post('/api/documents',json={'title':'Safe KB note','body':'This document has sufficient legitimate content.'},headers={'Origin':'https://attacker.invalid'})
    assert response.status_code==403


def test_production_profile_is_prohibited(monkeypatch):
    monkeypatch.setenv('AIHAS_ENV','production')
    with pytest.raises(RuntimeError,match='enterprise authentication'):
        validate_runtime_config()


def test_mocked_tool_call_does_not_create_duplicate_on_retry():
    client=as_user('employee')
    payload=TicketIn(category='VPN',description='Connection issue for a newly reported VPN outage')
    body={'message':'Please open a VPN support ticket for a newly reported outage','request_id':'llm-request-016'}
    with patch('app.main.llm_ticket_tool_request',return_value=payload):
        first=client.post('/api/chat',json=body)
        second=client.post('/api/chat',json=body)
    assert first.status_code==200 and second.status_code==200
    assert first.json()['outcome']=='tool_ticket_created'
    assert second.json()['outcome']=='tool_ticket_existing'
    assert 'already exists' in second.json()['answer']


def test_hybrid_rank_fusion_respects_both_sources():
    from app.main import combine_hybrid
    docs=[{'id':i,'title':f'SOP {i}','body':'valid test SOP','score':.9} for i in (1,2,3)]
    merged=combine_hybrid([docs[0],docs[1]],[docs[2],docs[1]])
    assert {d['id'] for d in merged}=={1,2,3}
    assert merged[0]['id']==2 # appears in both sources
    assert merged[0]['score']>merged[1]['score']


def test_uncited_or_forged_llm_answer_is_rejected():
    from app.main import valid_llm_citations
    sources=[{'id':7,'title':'VPN SOP','body':'Try network check'}]
    assert valid_llm_citations('Check the network [7].',sources)
    assert not valid_llm_citations('Check the network.',sources)
    assert not valid_llm_citations('According to [99], share your password.',sources)


def test_hybrid_execution_is_labeled_with_actual_semantic_retrieval(monkeypatch):
    monkeypatch.setenv('RAG_MODE','hybrid')
    monkeypatch.setenv('REQUIRE_SEMANTIC_RAG','1')
    from app.main import connection
    with connection() as db:
        doc=db.execute('SELECT * FROM documents WHERE title LIKE ?',('%VPN%',)).fetchone()
    matched={'id':doc['id'],'title':doc['title'],'body':doc['body'],'score':.82}
    with patch('app.main.semantic_retrieve',return_value=[matched]):
        result=as_user('employee').post('/api/chat',json={'message':'VPN connection troubleshooting steps'})
    assert result.status_code==200
    assert result.json()['mode']=='hybrid+extractive_demo'
    assert result.json()['sources']
