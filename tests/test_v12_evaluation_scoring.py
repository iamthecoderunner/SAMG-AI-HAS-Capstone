from scripts.evaluate_local_rag import grade_case,aggregate

def test_valid_grounded_model_answer():
    case={'expected_title':'VPN troubleshooting SOP'}
    resp={'outcome':'answered','mode':'semantic+ollama','sources':[{'id':1,'title':'VPN troubleshooting SOP'}], 'answer':'Restart VPN client [1]'}
    assert grade_case(case,resp)['pass']
    resp['mode']='semantic+sop_extract_fallback'
    assert not grade_case(case,resp)['pass']

def test_unrelated_citation_and_false_success_rejected():
    case={'expected_title':'VPN troubleshooting SOP'}
    data={'outcome':'answered','mode':'semantic+ollama','sources':[{'id':4,'title':'Email troubleshooting'}],'answer':'Restart client [4]'}
    assert not grade_case(case,data)['pass']
    data['sources']=[{'id':1,'title':'VPN troubleshooting SOP'}]
    assert not grade_case(case,data)['pass']
    data['answer']='Restart client [1]'
    assert grade_case(case,data)['pass']

def test_unsupported_must_abstain():
    case={'expected_title':None}
    assert grade_case(case,{'outcome':'escalation_recommended','sources':[]})['pass']
    assert not grade_case(case,{'outcome':'answered','sources':[{'id':1}],'answer':'anything'})['pass']

def test_aggregation_is_honest_about_faithfulness():
    a={'grade':{'pass':True,'supported':True,'source_hit':True,'live_model_cited':True}}
    b={'grade':{'pass':False,'supported':False,'abstained':False}}
    result=aggregate([a,b])
    assert result['passed']==1 and result['failed']==1
    assert result['human_reviewed_faithfulness']=='NOT YET MEASURED'
