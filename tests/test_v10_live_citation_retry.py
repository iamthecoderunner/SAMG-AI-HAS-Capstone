"""Small-model citation-retry regressions. Mocked responses, NOT live Ollama proof."""
from unittest.mock import patch
from app.main import generate

VPN = {'id': 1, 'title': 'VPN troubleshooting SOP',
       'body': 'Verify internet connectivity, check VPN credentials, restart VPN client. Never share passwords.',
       'score': 0.9}
EMAIL = {'id': 4, 'title': 'Email troubleshooting', 'body': 'Restart your email client.', 'score': 0.4}


def test_ollama_one_retry_recovers_real_model_citation(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'ollama')
    with patch('app.local_ai.ollama_chat', side_effect=[
        {'content': 'Try reconnecting.'},
        {'content': 'Verify internet connectivity and restart the VPN client. [1]'},
    ]) as request:
        answer, mode = generate('How can I troubleshoot VPN connection failures?', [VPN, EMAIL])
        assert mode == 'ollama'
        assert answer.endswith('[1]')
        assert request.call_count == 2
        retry_text = str(request.call_args.args[0])
        assert 'VPN troubleshooting SOP' in retry_text
        assert 'Email troubleshooting' not in retry_text


def test_ollama_retry_does_not_turn_uncited_text_into_verified_answer(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'ollama')
    with patch('app.local_ai.ollama_chat', side_effect=[
        {'content': 'Invent a VPN command.'}, {'content': 'Restart the router.'},
    ]) as request:
        answer, mode = generate('How can I troubleshoot VPN connection failures?', [VPN])
        assert request.call_count == 2
        assert mode == 'sop_extract_fallback'
        assert 'Invent' not in answer and 'Restart the router' not in answer
        assert '[1]' in answer


def test_ollama_retry_rejects_citation_for_unrelated_document(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'ollama')
    with patch('app.local_ai.ollama_chat', side_effect=[
        {'content': 'Check VPN [4]'}, {'content': 'Check VPN [4]'},
    ]):
        answer, mode = generate('How can I troubleshoot VPN connection failures?', [VPN, EMAIL])
        assert mode == 'sop_extract_fallback' and '[1]' in answer
        assert '[4]' not in answer


def test_ollama_valid_first_response_never_retries(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'ollama')
    with patch('app.local_ai.ollama_chat', return_value={'content': 'Restart the client. [1]'}) as request:
        answer, mode = generate('How can I troubleshoot VPN connection failures?', [VPN])
        assert mode == 'ollama' and answer.endswith('[1]')
        assert request.call_count == 1
