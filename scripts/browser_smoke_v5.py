"""Optional headless browser/JS verification using FastAPI TestClient bridge.

Browser routes are intentionally intercepted because the build environment
blocks real localhost browser navigation. This checks UI event code + backend,
NOT a normal browser-over-network HTTP deployment. For that, see http_smoke.py.
"""
from pathlib import Path
import json, os, secrets, tempfile, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'docs'/'evidence'

def main():
    from playwright.sync_api import sync_playwright
    from fastapi.testclient import TestClient
    from urllib.parse import urlparse
    OUT.mkdir(exist_ok=True,parents=True)
    with tempfile.TemporaryDirectory(prefix='aihas-browser-bridge-') as tmp:
        os.environ.update({'AIHAS_DB':str(Path(tmp)/'ui.db'),'AIHAS_ENV':'demo',
            'SESSION_SECRET':secrets.token_hex(32),
            'DEMO_EMPLOYEE_PASSWORD':'synthetic-browser-only-pass',
            'DEMO_AGENT_PASSWORD':'synthetic-agent-browser-pass',
            'DEMO_ADMIN_PASSWORD':'synthetic-admin-browser-pass',
            'OPENAI_API_KEY':'','RAG_MODE':'lexical','REQUIRE_SEMANTIC_RAG':'0',
            'ENABLE_TOOL_CALLING':'0','N8N_WEBHOOK_URL':''})
        from app.main import app
        with TestClient(app) as client, sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True,
                executable_path=os.getenv('AIHAS_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            context=browser.new_context(viewport={'width':1280,'height':900})
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            def bridge(url, options):
                parsed=urlparse(url)
                headers={'Host':'demo.example'}
                method=options.get('method','GET')
                body=options.get('body')
                if body is not None:headers['Content-Type']='application/json'
                response=client.request(method,parsed.path or '/api/me',
                    content=body,headers=headers)
                return {'ok':response.is_success,'status':response.status_code,
                        'data':response.json() if response.content else {}}
            page.expose_function('bridgeToBackend',bridge)
            page.set_content((ROOT/'app/static/index.html').read_text(encoding='utf8'))
            page.evaluate('''window.fetch = async function(url, options) {
                if (!url) return {ok: false, status: 400, json: async () => ({detail: 'Missing URL'})};
                const r = await window.bridgeToBackend(url, options || {});
                return {ok: r.ok, status: r.status, json: async () => r.data};
            };''')
            page.select_option('#username','employee')
            page.fill('#password',os.environ['DEMO_EMPLOYEE_PASSWORD'])
            page.click('#loginForm button[type=submit]')
            page.locator('#tab-chat:not(.hidden)').wait_for(timeout=10000)
            page.fill('#chatInput','How do I get free vpn')
            page.click('#send')
            page.get_by_text('Create agent escalation ticket',exact=True).wait_for(timeout=10000)
            reply=page.locator('#chatbox .bubble').last.inner_text()
            assert 'out_of_scope' in reply
            assert 'VPN troubleshooting SOP' not in reply
            page.screenshot(path=str(OUT/'v5-free-vpn-scope-guard.png'),full_page=True)
            page.get_by_text('Create agent escalation ticket',exact=True).click()
            page.get_by_text('Escalated to human agent',exact=False).wait_for(timeout=10000)
            page.screenshot(path=str(OUT/'v5-human-escalation-created.png'),full_page=True)
            page.click('#logout')
            page.wait_for_timeout(150)
            page.set_content((ROOT/'app/static/index.html').read_text(encoding='utf8'))
            page.evaluate('''window.fetch = async function(url, options) {
                if (!url) return {ok: false, status: 400, json: async () => ({detail: 'Missing URL'})};
                const r = await window.bridgeToBackend(url, options || {});
                return {ok: r.ok, status: r.status, json: async () => r.data};
            };''')
            page.select_option('#username','agent')
            page.fill('#password',os.environ['DEMO_AGENT_PASSWORD'])
            page.click('#loginForm button[type=submit]')
            page.locator('#tab-chat:not(.hidden)').wait_for(timeout=10000)
            page.locator('button[data-tab="tickets"]').click()
            page.get_by_text('How do I get free vpn',exact=False).wait_for(timeout=10000)
            assert 'escalated' in page.locator('#ticketsList').inner_text()
            page.screenshot(path=str(OUT/'v5-agent-queue-escalation.png'),full_page=True)
            assert not errors,errors
            browser.close()
            evidence={'status':'PASS','scope':'Chromium JavaScript + intercepted FastAPI TestClient + disposable SQLite',
                      'normal_network_browser_verified':False,
                      'checks':['employee login','out-of-scope no wrong SOP','escalation button','persisted ticket','agent queue'],
                      'external_ai_verified':False,
                      'screenshots':['v5-free-vpn-scope-guard.png','v5-human-escalation-created.png','v5-agent-queue-escalation.png']}
            (OUT/'browser_smoke_v5.json').write_text(json.dumps(evidence,indent=2)+'\n')
            print(json.dumps(evidence,indent=2))

if __name__=='__main__':main()
