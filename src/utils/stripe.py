import logging
import stripe
from django.conf import settings 

logger = logging.getLogger(__name__)
stripe_client = stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)

def create_express_account(email: str) -> stripe.Account:
    try:
        return stripe_client.v1.accounts.create(
            params={
                "type": "express",
                "email": email,
                "capabilities": {
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                }
            }
        )
    except stripe.StripeError as e:
        logger.error(f"Stripe Express account creation error: {e.user_message or str(e)}")
        raise e
    
def create_account_onboarding_link(stripe_account_id: str, return_url: str, refresh_url: str) -> stripe.AccountLink:
    try:
        return stripe_client.v1.account_links.create(
            params={
                "account": stripe_account_id,
                "refresh_url": refresh_url,
                "return_url": return_url,
                "type": "account_onboarding",
            }
        )
    except stripe.StripeError as e:
        logger.error(f"Error creating onboarding link for {stripe_account_id}: {e.user_message or str(e)}")
        raise e

def is_merchant_account_ready(stripe_id: str) -> bool:
    try:
        account = stripe_client.v1.accounts.retrieve(stripe_id)
        return bool(account.get('payouts_enabled') and account.get('charges_enabled'))
    except stripe.StripeError as e:
        logger.error(f"Error retrieving Stripe account {stripe_id}: {str(e)}")
        return False

def create_payment_intent(
    amount_in_cents: int,
    metadata: dict,
    currency: str = 'usd',
    merchant_stripe_account_id: str = None,
    application_fee_in_cents: int = 0
) -> stripe.PaymentIntent:
    try:
        params = {
            'amount': amount_in_cents,
            'automatic_payment_methods': {'enabled': True},
            'metadata': metadata or {},
            'currency': currency
        }

        if merchant_stripe_account_id:
            params['transfer_data'] = {'destination': merchant_stripe_account_id}
            if application_fee_in_cents > 0:
                params['application_fee_amount'] = application_fee_in_cents

        payment_intent = stripe_client.v1.payment_intents.create(params=params)
        return payment_intent

    except stripe.StripeError as e:
        logger.error(f'Stripe payment intent creation error: {e.user_message or str(e)}')
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during Stripe PaymentIntent creation: {str(e)}")
        raise e
    
def verify_webhook_signature(payload: bytes, sig_header: str) -> stripe.Event:
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError as e:
        logger.error("Invalid Stripe webhook payload received.")
        raise e
    except stripe.SignatureVerificationError as e:
        logger.error("Stripe webhook signature verification failed.")
        raise e
    
def refund_payment(
    payment_intent_id: str,
    amount_in_cents: int = None,
    refund_application_fee: bool = True,
    reverse_transfer: bool = True
) -> stripe.Refund:
    
    try:
        params = {
            'payment_intent': payment_intent_id,
            'refund_application_fee': refund_application_fee,
            'reverse_transfer': reverse_transfer,
        }
        
        if amount_in_cents:
            params['amount'] = amount_in_cents

        refund = stripe_client.v1.refunds.create(params=params)
        return refund

    except stripe.StripeError as e:
        logger.error(f"Stripe refund creation error: {e.user_message or str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during Stripe refund creation: {str(e)}")
        raise e