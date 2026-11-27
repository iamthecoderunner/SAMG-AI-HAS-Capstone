"""Completion measures require an actual user confirmation, not AI answer count."""
import os, tempfile, pathlib
from fastapi.testclient import TestClient


def test_resolution_feedback_lifecycle(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv('AIHAS_DB', str(pathlib.Path(tmp)/'feedback.sqlite3'))
        monkeypatch.setenv('AI_PROVIDER','offline')
        monkeypatch.setenv('RAG_MODE','lexical')
        monkeypatch.setenv('N8N_WEBHOOK_URL','')
        import app.main as m
        monkeypatch.setattr(m,'DB_PATH',pathlib.Path(tmp)/'feedback.sqlite3')
        with TestClient(m.app) as employee:
            assert employee.post('/api/login',json={'username':'employee','password':'Demo1234!'}).status_code==200
            answer=employee.post('/api/chat',json={'message':'How can I troubleshoot VPN issues?'}).json()
            assert answer['outcome']=='answered'
            cid=answer['conversation_id']
            assert isinstance(cid,int) and cid>0
            assert employee.post(f'/api/conversations/{cid}/feedback',json={'resolved':True}).status_code==201
            assert employee.post(f'/api/conversations/{cid}/feedback',json={'resolved':False}).status_code==409
            other=employee.post('/api/chat',json={'message':'quantum wormhole propulsion'}).json()
            assert other['outcome']=='escalation_recommended'
            assert employee.post(f'/api/conversations/{other["conversation_id"]}/feedback',json={'resolved':True}).status_code==409
            assert employee.post('/api/conversations/99999/feedback',json={'resolved':True}).status_code==404
            assert employee.get('/api/metrics').status_code==403
        with TestClient(m.app) as agent:
            assert agent.post('/api/login',json={'username':'agent','password':'Demo1234!'}).status_code==200
            assert agent.post(f'/api/conversations/{cid}/feedback',json={'resolved':False}).status_code==403
            metrics=agent.get('/api/metrics').json()
            assert metrics['feedback_responses']==1
            assert metrics['confirmed_resolved']==1
            assert metrics['feedback_resolution_rate_pct']==100
            assert metrics['observed_resolved_ticket_minutes'] is None
            assert metrics['answer_rate_pct']<=100
