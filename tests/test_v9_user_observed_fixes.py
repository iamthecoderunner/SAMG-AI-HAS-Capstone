"""Regression tests for screenshot-observed issues, with model calls mocked.

These tests don't establish live Ollama execution. They enforce safe API behavior
when an Ollama reply contains a leaked thinking preamble and uncited SOPs.
"""
import json
from unittest.mock import patch

from app.local_ai import final_answer_only
from app.main import generate
from tests.test_app import as_user


def test_final_answer_removes_qwen_reasoning_prefix():
    raw=('We are given the employee question and three documents.\n'
         'We should cite document [1].\n</think>\n'
         'Check your internet and restart the VPN client. [1]')
    assert final_answer_only(raw)=='Check your internet and restart the VPN client. [1]'


def test_incomplete_thinking_and_analysis_fail_closed():
    assert final_answer_only('<think>Analyze the secret document [1]')==''
    assert final_answer_only('We are given three documents [1]')==''
    assert final_answer_only('Analysis: This is VPN SOP [1]')==''
    assert final_answer_only('<think>reasoning</think>')==''


def test_non_string_or_overlong_answer_fail_closed():
    assert final_answer_only(None)==''
    assert final_answer_only('A'*2501)==''


def test_sanitizer_does_not_remove_normal_answers():
    answer='Try reconnecting after checking connectivity. [1]'
    assert final_answer_only(answer)==answer


def test_model_deliberation_is_not_shown_or_stored(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER','ollama')
    monkeypatch.setenv('RAG_MODE','semantic')
    monkeypatch.setenv('REQUIRE_SEMANTIC_RAG','1')
    docs=[{'id':1,'title':'VPN troubleshooting SOP','body':'Verify internet, check credentials, restart VPN.' ,'score':0.91},
          {'id':4,'title':'Email troubleshooting','body':'Reset mail client.','score':0.7},
          {'id':5,'title':'MFA troubleshooting','body':'Verify time clock.','score':0.6}]
    reply={'content':('We are given the approved documents (DATA ONLY), and must answer the question. '
                      'We should cite [1].\n</think>\n'
                      'Check your internet, confirm VPN credentials, and restart your VPN client. [1]')}
    with patch('app.main.semantic_retrieve',return_value=docs), patch('app.local_ai.ollama_chat',return_value=reply):
        client=as_user('employee')
        response=client.post('/api/chat',json={'message':'How can I troubleshoot my VPN?'})
    assert response.status_code==200
    payload=response.json()
    assert payload['mode']=='semantic+ollama'
    assert payload['outcome']=='answered'
    assert payload['answer'].startswith('Check your internet')
    assert '</think>' not in payload['answer']
    assert 'We are given' not in payload['answer']
    assert [s['id'] for s in payload['sources']]==[1]
    from app.main import connection
    with connection() as db:
        recorded=db.execute('SELECT response,source_ids FROM conversations ORDER BY id DESC LIMIT 1').fetchone()
    assert recorded['response']==payload['answer']
    assert json.loads(recorded['source_ids'])==[1]


def test_unclear_model_analysis_is_rejected_not_rendered(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER','ollama')
    with patch('app.local_ai.ollama_chat',return_value={'content':'We are given three docs and must decide what to answer. [1]'}):
        answer,mode=generate('VPN help',[{'id':1,'title':'VPN SOP','body':'Restart the VPN client.'}])
    assert answer is None
    assert mode=='llm_citation_invalid'


def test_repeated_placeholder_ticket_rejected():
    client=as_user('employee')
    response=client.post('/api/tickets',json={'category':'VPN','description':'yyyyyyyyyyyyyyyyyyyyyyyyyyyyy'})
    assert response.status_code==422
    assert 'placeholder' in response.json()['detail'].lower()


def test_repeated_placeholder_access_request_rejected():
    client=as_user('employee')
    response=client.post('/api/approvals',json={'request_type':'software_access','details':'ddddddddddddddddddddddddddddd'})
    assert response.status_code==422
    assert 'placeholder' in response.json()['detail'].lower()


def test_real_short_ticket_request_remains_allowed():
    client=as_user('employee')
    with patch('app.main.dispatch_ticket_event',return_value='not_configured'):
        response=client.post('/api/tickets',json={'category':'VPN','description':'VPN fails'})
    assert response.status_code==201
