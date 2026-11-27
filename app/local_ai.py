"""Minimal, restricted Ollama HTTP adapter for a local-only academic AI-HAS.

No external API account and no Python Ollama SDK required. Model inference is
performed by a running, local Ollama service, not by this adapter.
"""
import json
import os
import re
import urllib.request
from urllib.parse import urlsplit


class LocalAIError(RuntimeError):
    pass


def base_url() -> str:
    url = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
    parsed = urlsplit(url)
    # Protect the local prototype from arbitrary SSRF and credential-bearing URLs.
    if (parsed.scheme != 'http' or parsed.hostname not in {'localhost', '127.0.0.1', '::1'}
            or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment
            or not (1 <= (parsed.port or 11434) <= 65535)):
        raise LocalAIError('OLLAMA_BASE_URL must be an HTTP loopback URL with no path or credentials')
    return url


def local_request(path: str, payload: dict | None = None, *, timeout: int = 90) -> dict:
    if path not in {'/api/chat', '/api/embed', '/api/tags'}:
        raise LocalAIError('Unsupported local AI API operation')
    url = base_url() + path
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {'Content-Type': 'application/json'} if data is not None else {}
    try:
        request = urllib.request.Request(url, data=data, headers=headers,
                                         method='POST' if data is not None else 'GET')
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise LocalAIError('Local model service returned an unsuccessful HTTP status')
            return json.loads(response.read(12_000_000).decode('utf-8'))
    except LocalAIError:
        raise
    except Exception as exc:
        # Do not leak user input, host details, or model content through raw errors.
        raise LocalAIError(f'Local model request failed ({type(exc).__name__})') from None


def ollama_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = local_request('/api/embed', {
        'model': os.getenv('OLLAMA_EMBED_MODEL', 'nomic-embed-text'),
        'input': texts, 'truncate': True,
    }, timeout=120)
    embeddings = response.get('embeddings')
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise LocalAIError('Local embeddings returned invalid batch size')
    if any(not isinstance(e, list) or not e or any(not isinstance(x, (float, int)) for x in e) for e in embeddings):
        raise LocalAIError('Local embeddings have invalid values')
    return embeddings


def ollama_chat(messages: list[dict], tools: list[dict] | None = None, *, timeout: int = 120,
                format_schema: dict | None = None) -> dict:
    payload = {
        'model': os.getenv('OLLAMA_CHAT_MODEL', 'qwen3:4b'),
        'messages': messages, 'stream': False, 'think': False,
        'options': {'temperature': 0, 'num_ctx': 4096, 'num_predict': 512},
    }
    if tools is not None:
        payload['tools'] = tools
    if format_schema is not None:
        # Ollama native /api/chat supports JSON-schema-constrained responses.
        # Never set this for function-calling requests.
        if tools is not None:
            raise LocalAIError('Structured answer mode cannot be combined with tool calls')
        payload['format'] = format_schema
    response = local_request('/api/chat', payload, timeout=timeout)
    message = response.get('message')
    if not isinstance(message, dict):
        raise LocalAIError('Local chat did not return a message')
    return message


def final_answer_only(raw: str) -> str:
    """Exclude exposed model reasoning before sending, storing, or parsing replies.

    Some Ollama/model combinations include thinking text in message.content even
    when think=false. Ambiguous unclosed thinking blocks fail closed.
    """
    if not isinstance(raw, str):
        return ''
    value=raw.strip()
    if re.search(r'</think\s*>', value, flags=re.I):
        value=re.split(r'</think\s*>', value, flags=re.I)[-1].strip()
    if re.search(r'<\s*/?think\b', value, flags=re.I):
        return ''
    if re.match(r'(?is)^(?:we are given|we have the following|the employee is asking|the user (?:is asking|asks)|let.s write the response|analysis:|reasoning:)', value):
        return ''
    if not value or len(value)>2500:
        return ''
    return value
