import hmac
import hashlib
import json
from django.conf import settings
import os
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()


def generate_stripe_signature(payload, secret):
    # timestamp = str(int(time.time()))
    timestamp = 1789492668
    
    if isinstance(payload, dict):
        payload_string = json.dumps(payload, separators=(',', ':'))
    else:
        payload_string = payload

    signed_payload = f"{timestamp}.{payload_string}"
    
    signature = hmac.new(
        secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    print(f"t={timestamp},v1={signature}", payload_string)
    return f"t={timestamp},v1={signature}", payload_string

payload = '''{"id":"evt_2N00002eZvKYlo2Cxxxxxx","object":"event","api_version":"v2","created":1789492668,"type":"account.updated","related_object":{"id":"acct_1UF3PIIvl9a7wu2r","type":"account","url":"/v2/core/accounts/acct_1UF3PIIvl9a7wu2r"}}'''

secret = settings.STRIPE_WEBHOOK_SECRET

generate_stripe_signature(payload=payload,secret=secret)
