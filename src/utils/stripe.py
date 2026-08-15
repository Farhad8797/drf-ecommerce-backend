import logging
import stripe
from django.conf import settings 

logger = logging.getLogger(__name__)
stripe_client = stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)

def create_payment_intent(amount_in_cents: int, metadata: dict, currency: str = 'usd') -> stripe.PaymentIntent:
    try:
        payment_intent = stripe_client.v1.payment_intents.create(
            params={
                'amount': amount_in_cents,
                'automatic_payment_methods': {'enabled': True},
                'metadata': metadata or {},
                'currency': currency
            }
        )
        return payment_intent
    except stripe.StripeError as e:
        logger.error(f'Stripe payment intent creation error: {e.user_message} or {str(e)}')
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
    except ValueError as e:
        logger.error("Invalid Stripe webhook payload received.")
        raise e
    except stripe.SignatureVerificationError as e:
        logger.error("Stripe webhook signature verification failed.")
        raise e