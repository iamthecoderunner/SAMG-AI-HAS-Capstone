"""Safely switch a local demo .env to the free Ollama provider.

Preserves existing demo credentials, DB path, and secrets; never prints secrets.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / '.env'
if not path.is_file():
    raise SystemExit('BLOCKED: .env is absent; run scripts/bootstrap_demo.py first.')
updates = {
    'AI_PROVIDER': 'ollama',
    'OLLAMA_BASE_URL': 'http://127.0.0.1:11434',
    'OLLAMA_CHAT_MODEL': 'qwen3:4b',
    'OLLAMA_EMBED_MODEL': 'nomic-embed-text',
    'RAG_MODE': 'semantic',
    'REQUIRE_SEMANTIC_RAG': '1',
    'ENABLE_TOOL_CALLING': '1',
    'AIHAS_ENV': 'demo',
}
original = path.read_text(encoding='utf-8').splitlines()
seen = set()
result = []
for line in original:
    key = line.split('=', 1)[0].strip() if '=' in line else None
    if key in updates:
        if key not in seen:
            result.append(f'{key}={updates[key]}')
            seen.add(key)
    else:
        result.append(line)
for key, value in updates.items():
    if key not in seen:
        result.append(f'{key}={value}')
path.write_text('\n'.join(result) + '\n', encoding='utf-8')
print('CONFIGURED: Free local Ollama provider, semantic RAG and tool calling enabled.')
print('Existing credentials and other settings were preserved. No API key required.')
