from unittest.mock import patch
from tests.test_app import as_user
from app.main import TicketIn

def test_native_tool_execution_path_is_backend_validated():
    client=as_user('employee')
    payload=TicketIn(category='VPN',description='Connection issue for a support ticket')
    with patch('app.main.llm_ticket_tool_request',return_value=payload):
        r=client.post('/api/chat',json={'message':'Please create a support ticket for a VPN connection issue'})
    assert r.status_code==200
    assert r.json()['mode']=='openai_function_call'
    assert r.json()['outcome']=='tool_ticket_created'
    assert 'Support ticket #' in r.json()['answer']
