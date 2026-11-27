"""Create a unique local demo .env; never overwrites an existing configuration.

Run: python scripts/bootstrap_demo.py
Keep printed passwords privately; they are never added to the repository.
"""
from pathlib import Path
import secrets

root=Path(__file__).resolve().parents[1]
source=root/'.env.example'
target=root/'.env'
if target.exists():
    raise SystemExit('Existing .env preserved. No secrets overwritten.')
values={
    'SESSION_SECRET':secrets.token_urlsafe(48),
    'DEMO_EMPLOYEE_PASSWORD':secrets.token_urlsafe(16),
    'DEMO_AGENT_PASSWORD':secrets.token_urlsafe(16),
    'DEMO_ADMIN_PASSWORD':secrets.token_urlsafe(16),
    'WEBHOOK_TOKEN':secrets.token_urlsafe(40),
}
lines=[]
for line in source.read_text().splitlines():
    k=line.split('=',1)[0]
    lines.append(k+'='+values[k] if k in values else line)
target.write_text('\n'.join(lines)+'\n')
try:target.chmod(0o600)
except OSError:pass
print('Local .env created. These demonstration-only credentials are not stored in a public file:')
for user,env in [('employee','DEMO_EMPLOYEE_PASSWORD'),('agent','DEMO_AGENT_PASSWORD'),('admin','DEMO_ADMIN_PASSWORD')]:
    print(f'  {user}: {values[env]}')
print('Use ONLY with local demo. Keep secrets private and do not commit .env.')
