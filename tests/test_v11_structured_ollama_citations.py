"""Structured Ollama citations: mocked regression tests, NOT a live Ollama pass."""
import json
from unittest.mock import patch

import pytest

from app.main import generate, validated_ollama_answer, ollama_citation_schema
from app.local_ai import LocalAIError, ollama_chat

VPN = {'id': 1, 'title': 'VPN troubleshooting SOP',
       'body': 'Verify internet connectivity, check VPN credentials, restart the VPN client, then try again. If the error continues, create a support ticket. Never disclose passwords.',
       'score': .91}
EMAIL = {'id': 4, 'title': 'Email troubleshooting SOP',
         'body': 'Restart your email client.', 'score': .33}


def response(answer, citations):
    return {'content': json.dumps({'answer': answer, 'citation_ids': citations})}


def test_structured_response_is_genuinely_model_cited(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'ollama')
    with patch('app.local_ai.ollama_chat', return_value=response(
            'Verify internet connectivity, check VPN credentials and restart the VPN client.', [1])) as mock:
        answer, mode = generate('How can I troubleshoot VPN issues?', [VPN, EMAIL])
    assert mode == 'ollama'
    assert answer == 'Verify internet connectivity, check VPN credentials and restart the VPN client. [1]'
    assert mock.call_count == 1
    schema = mock.call_args.kwargs['format_schema']
    assert schema['properties']['citation_ids']['items']['enum'] == [1]


def test_model_must_select_real_citation_not_guess(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'ollama')
    with patch('app.local_ai.ollama_chat', return_value=response(
            'Verify internet connectivity and restart the VPN client.', [4])) as mock:
        answer, mode = generate('How can I troubleshoot VPN issues?', [VPN, EMAIL])
    assert mode == 'sop_extract_fallback'
    assert 'VPN troubleshooting SOP [1]' in answer
    assert mock.call_count == 2


def test_plain_uncited_model_answer_is_not_auto_cited():
    assert validated_ollama_answer({'content':'Restart the router.'}, [VPN]) is None
    assert validated_ollama_answer({'content':'[1]'}, [VPN]) is None


def test_mismatched_prose_citation_is_rejected():
    assert validated_ollama_answer(response('Restart the VPN client. [4]', [1]), [VPN]) is None
    assert validated_ollama_answer(response('Restart the VPN client.', []), [VPN]) is None
    assert validated_ollama_answer(response('Restart the VPN client.', [99]), [VPN]) is None
    assert validated_ollama_answer(response('Restart the VPN client.', [True]), [VPN]) is None


def test_multiple_model_selected_citations_are_rendered():
    assert validated_ollama_answer(response('Review both SOPs.', [1,4]), [VPN, EMAIL]) == 'Review both SOPs. [1] [4]'


def test_structured_retry_can_recover(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'ollama')
    with patch('app.local_ai.ollama_chat', side_effect=[
        {'content': 'Try reconnecting.'},
        response('Verify internet connectivity and restart the VPN client.', [1])
    ]) as mock:
        answer, mode = generate('VPN troubleshooting', [VPN])
    assert mode == 'ollama'
    assert '[1]' in answer
    assert mock.call_count == 2


def test_ollama_api_payload_passes_schema_to_native_chat():
    with patch('app.local_ai.local_request', return_value={'message': response('A', [1])}) as request:
        schema = ollama_citation_schema([VPN])
        out=ollama_chat([{'role':'user','content':'hello'}],format_schema=schema)
        assert out['content']
    payload=request.call_args.args[1]
    assert payload['format'] == schema
    assert payload['think'] is False
    assert 'tools' not in payload
    with pytest.raises(LocalAIError):
        ollama_chat([{'role':'user','content':'hello'}], tools=[], format_schema=schema)


def test_tool_path_does_not_change_to_structured_mode():
    with patch('app.local_ai.local_request', return_value={'message':{'tool_calls':[]}}) as request:
        ollama_chat([{'role':'user','content':'hello'}],tools=[])
    payload=request.call_args.args[1]
    assert 'format' not in payload
