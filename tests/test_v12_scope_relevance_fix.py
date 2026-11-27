"""Realistic irrelevant Chroma hits must never become spurious cited answers.

Local-unit checks mock Ollama; live qwen3/Chroma benchmarking must still be run
on the user's configured Windows machine after applying this patch.
"""
import json
from unittest.mock import patch

from app.main import (
    connection, generate, is_model_scope_refusal, relevant_sop_sources,
    validated_ollama_answer,
)
from tests.test_app import as_user


def test_relevance_gate_on_22_existing_case_questions():
    with connection() as db:
        all_docs=[dict(row) for row in db.execute('SELECT * FROM documents')]
    cases=json.loads((__import__('pathlib').Path(__file__).parent/'retrieval_cases.json').read_text(encoding='utf8'))
    assert len(cases)==22
    for case in cases:
        docs=relevant_sop_sources(case['query'],all_docs)
        if case['expected_title'] is None:
            assert not docs, (case['query'],docs)
        else:
            assert any(d['title']==case['expected_title'] for d in docs),case['query']


def test_unsupported_questions_fail_closed_even_when_chroma_gives_irrelevant_hits(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER','ollama')
    monkeypatch.setenv('RAG_MODE','semantic')
    monkeypatch.setenv('REQUIRE_SEMANTIC_RAG','1')
    with connection() as db:
        bogus=[{'id':d['id'],'title':d['title'],'body':d['body'],'score':0.51}
               for d in db.execute('SELECT * FROM documents')]
    with patch('app.main.semantic_retrieve',return_value=bogus),patch('app.local_ai.ollama_chat') as model:
        employee=as_user('employee')
        for question in ['How do I breed rainbow axolotls?',
                         'How to pilot a spacecraft through a wormhole?',
                         'Quantum gravity starship fuel optimization',
                         'Estimate cryptocurrency prices tomorrow']:
            response=employee.post('/api/chat',json={'message':question})
            assert response.status_code==200
            payload=response.json()
            assert payload['outcome']=='escalation_recommended', payload
            assert payload['sources']==[],payload
            assert '[1]' not in payload['answer'],payload
            assert payload['mode']=='semantic+no_relevant_context',payload
    model.assert_not_called()


def test_model_out_of_scope_refusal_is_not_validated_as_a_cited_answer(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER','ollama')
    doc={'id':4,'title':'Email troubleshooting','body':'Restart the mail application if company email fails to sync.'}
    message={'content':json.dumps({'answer':'This question is outside the scope of our IT services.',
                                   'citation_ids':[4]})}
    assert validated_ollama_answer(message,[doc]) is None
    assert is_model_scope_refusal('We do not support or provide guidance on pet breeding.')
    with patch('app.local_ai.ollama_chat',return_value=message):
        result,mode=generate('Can company email be used for personal messages?', [doc])
    assert result is None and mode=='llm_citation_invalid'


def test_valid_negative_password_policy_answer_remains_supported(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER','ollama')
    doc={'id':2,'title':'Password reset policy','body':'A human agent must approve password reset after identity verification.'}
    message={'content':json.dumps({'answer':'No, you cannot reset your password through this chatbot. A human agent must approve it.',
                                   'citation_ids':[2]})}
    assert not is_model_scope_refusal('No, you cannot reset your password through this chatbot.')
    with patch('app.local_ai.ollama_chat',return_value=message):
        answer,mode=generate('Can I reset my password through this chatbot?', [doc])
    assert mode=='ollama' and answer.endswith('[2]')
