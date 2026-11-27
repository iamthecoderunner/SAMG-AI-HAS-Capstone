"""v4 contract tests; do NOT claim these are live provider tests."""
from pathlib import Path
import os
import subprocess
import sys
from unittest.mock import patch
import pytest
from tests.test_app import as_user
from app.main import connection


def test_database_transaction_rolls_back_on_exception():
    with pytest.raises(RuntimeError,match='forced'):
        with connection() as db:
            db.execute('INSERT INTO audit(actor,action,target,details,created_at) VALUES(?,?,?,?,?)',
                       ('rollback_test_actor','should_rollback','0','{}','2026-11-25T00:00:00+00:00'))
            raise RuntimeError('forced')
    with connection() as db:
        assert not db.execute("SELECT 1 FROM audit WHERE actor='rollback_test_actor'").fetchone()


def test_failed_live_ticket_tool_does_not_fallback_to_kb_answer(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','nonfunctional-demo-key')
    monkeypatch.setenv('ENABLE_TOOL_CALLING','1')
    with patch('app.main.llm_ticket_tool_request',return_value=None):
        res=as_user('employee').post('/api/chat',json={
            'message':'Please create a support ticket for a VPN error'})
    assert res.status_code==200
    assert res.json()['outcome']=='tool_not_executed'
    assert res.json()['sources']==[]
    assert 'no ticket was created' in res.json()['answer'].lower()
    assert 'openai_tool_unverified'==res.json()['mode']


def test_provider_tool_schema_is_strict_and_required(monkeypatch):
    import types, json
    from app.main import llm_ticket_tool_request
    monkeypatch.setenv('OPENAI_API_KEY','nonfunctional-demo-key')
    monkeypatch.setenv('ENABLE_TOOL_CALLING','1')
    captured=[]
    def generate(**kwargs):
        captured.append(kwargs)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(
            tool_calls=[types.SimpleNamespace(function=types.SimpleNamespace(
                name='create_support_ticket',arguments=json.dumps({'category':'VPN','description':'VPN stops working after restart'})))])
        )])
    import sys
    class FakeSDK:
        def __init__(self, **kwargs):
            self.chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=generate))
    monkeypatch.setitem(sys.modules, 'openai', types.SimpleNamespace(OpenAI=FakeSDK))
    data=llm_ticket_tool_request('Please create a support ticket for VPN connection issues')
    assert data is not None
    assert captured[0]['tool_choice']=='required'
    assert captured[0]['parallel_tool_calls'] is False
    assert captured[0]['tools'][0]['function']['strict'] is True


def test_live_verifier_preflight_exits_blocked_without_key(tmp_path):
    env=os.environ.copy();env.pop('OPENAI_API_KEY',None)
    r=subprocess.run([sys.executable,'scripts/verify_live_ai.py',
                     '--output',str(tmp_path/'should_not_exist.json')],env=env,
                     cwd=Path(__file__).resolve().parents[1],
                     capture_output=True,text=True,timeout=30)
    assert r.returncode==2
    assert 'BLOCKED' in r.stdout
    assert not (tmp_path/'should_not_exist.json').exists()
