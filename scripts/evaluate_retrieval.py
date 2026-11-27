"""Reproducible corpus-specific lexical retrieval measurement, not LLM accuracy."""
import os, tempfile, json, sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory(prefix='aihas-eval-') as tmp:
    os.environ['AIHAS_DB']=str(Path(tmp)/'evaluation.db')
    os.environ.pop('OPENAI_API_KEY',None)
    from app.main import init_db, connection, retrieve
    init_db()
    with connection() as db:
        docs=[dict(r) for r in db.execute('SELECT * FROM documents')]
    cases=json.loads((Path(__file__).resolve().parents[1]/'tests/retrieval_cases.json').read_text())
    results=[]
    for i,case in enumerate(cases,1):
        matches=retrieve(case['query'],docs,k=3)
        titles=[m['title'] for m in matches]
        expected=case['expected_title']
        correct=expected in titles if expected else not bool(matches)
        results.append({'case_id':f'LR-{i:02d}','query':case['query'],'expected':expected,'retrieved':titles,'pass':correct})
    positive=[r for r in results if r['expected']]
    negative=[r for r in results if not r['expected']]
    report={'evaluated_at_utc':datetime.now(timezone.utc).isoformat(),
        'retrieval_type':'local TF-IDF lexical (NOT semantic RAG, NOT an LLM evaluation)',
        'corpus':'6 synthetic seeded SOPs','cases':len(results),
        'positive_cases':len(positive),'negative_cases':len(negative),
        'recall_at_3':round(sum(r['pass'] for r in positive)/len(positive),4),
        'unsupported_abstention_rate':round(sum(r['pass'] for r in negative)/len(negative),4),
        'cases_passed':sum(r['pass'] for r in results),'details':results}
    folder=Path(__file__).resolve().parents[1]/'docs/evidence'
    folder.mkdir(parents=True,exist_ok=True)
    output=folder/'retrieval_eval_lexical.json'
    output.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='details'},indent=2))
    if any(not r['pass'] for r in results):
        print('FAILURES:',[(r['case_id'],r['expected'],r['retrieved']) for r in results if not r['pass']])
