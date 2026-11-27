"""Optional automatic signed-webhook outbox worker.

Run beside the helpdesk API with the same AIHAS_DB and .env. Intended for a
single, small demo instance. Does not access model APIs or privileged systems.
Retries are bounded (5 attempts), idempotent at the sandbox receiver and
backed off. Production requires a managed queue and monitoring.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env',override=False)
except ImportError:
    pass
from app.main import init_db,drain_pending_outbox


def main():
    parser=argparse.ArgumentParser(description='Automatic bounded webhook retry worker')
    parser.add_argument('--once',action='store_true',help='One batch; no persistent process')
    parser.add_argument('--interval',type=int,default=10,help='Seconds between sweeps (minimum 2)')
    args=parser.parse_args()
    init_db()
    while True:
        result=drain_pending_outbox()
        print(json.dumps(result),flush=True)
        if args.once:return
        time.sleep(max(2,args.interval))

if __name__=='__main__':main()
