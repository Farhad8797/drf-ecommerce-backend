import stripe
import sys, os
from pathlib import Path

import os
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent  
src_dir = current_dir.parent                  
project_root = src_dir.parent                 

sys.path.append(str(project_root))
sys.path.append(str(src_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from utils.stripeConfig import stripe_client

def simulate_merchant_update(account_id: str):
    try:
        updated_account = stripe_client.v2.core.accounts.update(
            account_id, 
            {
            "configuration":{
                "merchant": {
                    "capabilities": {
                        "card_payments": {
                            "requested": True
                        }
                    }
                }
            },
            "include":["configuration.merchant", "requirements"]
            }, 
        )

        # Convert to a clean dictionary for inspection
        account_dict = updated_account.to_dict()
        print("Successfully updated dummy account:", account_dict)
        return account_dict

    except stripe.error.StripeError as e:
        print(f"Failed to update account: {e}")
        return None

simulate_merchant_update(account_id='acct_1UF3PIIvl9a7wu2r')