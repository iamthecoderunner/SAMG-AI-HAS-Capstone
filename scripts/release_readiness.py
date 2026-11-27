"""Read-only AI-HAS external integration/deployment readiness summary.

Does not send requests, access provider APIs, print secrets, or imply a service passed.
Run from project root: python scripts/release_readiness.py
"""
from __future__ import annotations
import importlib.util
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load_local_configuration():
    """Load local .env only when explicitly running this report.

    Importing `measure` from automated tests must never modify the
    process environment or switch tests to a running Ollama provider.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT/'.env',override=False)
    except ImportError:
        pass

def measure() -> dict:
    sdk=importlib.util.find_spec('openai') is not None
    vector=importlib.util.find_spec('chromadb') is not None
    has_key=bool(os.environ.get('OPENAI_API_KEY','').strip())
    mode=os.environ.get('RAG_MODE','lexical').strip().lower()
    strict=os.environ.get('REQUIRE_SEMANTIC_RAG','0')=='1'
    tools=os.environ.get('ENABLE_TOOL_CALLING','0')=='1'
    demo=os.environ.get('AIHAS_ENV','demo').strip().lower()=='demo'
    local_deps=['fastapi','uvicorn','pydantic','httpx']
    local_ready=all(importlib.util.find_spec(dep) is not None for dep in local_deps)
    ready_to_attempt=has_key and sdk and vector and mode in {'semantic','hybrid'} and strict and tools
    return {
        'checked_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'read_only':True,
        'application_dependencies':'present' if local_ready else 'missing',
        'local_demo_config':'demo_only' if demo else 'unsupported_non_demo',
        'openai_sdk':'installed' if sdk else 'missing',
        'chroma_sdk':'installed' if vector else 'missing',
        'api_key':'configured_privately' if has_key else 'not_configured',
        'rag_mode':mode,
        'require_semantic_rag':strict,
        'enable_tool_calling':tools,
        'live_ai_verification':'READY_TO_TEST_NOT_VERIFIED' if ready_to_attempt else 'BLOCKED',
        'docker_executable':'available_not_tested' if shutil.which('docker') else 'not_available',
        'public_deployment':'NOT_VERIFIED',
        'security_certification':'NOT_PERFORMED',
        'instructions':'Run scripts/verify_live_ai.py for actual integration evidence once readiness is READY_TO_TEST_NOT_VERIFIED.'
    }

if __name__=='__main__':
    load_local_configuration()
    result=measure()
    print(json.dumps(result,indent=2))
    sys.exit(0)  # Status is an observation, not a test pass/fail.
