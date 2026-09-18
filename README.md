# DRF + Stripe ecommerce backend

A secure backend service built with **Django** and the modern **Stripe Python SDK (API v2)**. This project handles real-time merchant onboarding synchronization, HMAC-SHA256 webhook signature verification, and automated database updates based on live merchant capabilities and verification states.

---

## Key Features

- **Stripe v2 Core Accounts Integration**: Leverages `stripe_client.v2.core.accounts` to retrieve and manage nested account capabilities (`card_payments`, `stripe_balance.payouts`).
- **Payload-Reduction Handling**: Utilizes explicit parameter expansion (`include=["configuration.merchant", "requirements"]`) to bypass Stripe v2's default payload reduction and retrieve deep capability statuses.
- **Secure Webhook Verification**: Implements robust HMAC-SHA256 signature validation on raw request bytes to ensure payload authenticity before processing.
- **Automated Status Synchronization**: Maps restricted, pending, or active capability states directly to local user/merchant records (`VERIFIED` vs `UNVERIFIED`).
- **Standalone Utility Scripts**: Includes robust setup blocks for executing isolated administrative and testing scripts outside the normal WSGI/ASGI server lifecycle.

---

## Tech Stack

- **Backend Framework**: Django, Django REST Framework (DRF)
- **Payment Gateway**: Stripe API v2 Core Services
- **Language**: Python 3.10+
- **Environment Management**: `uv` package manager / python-dotenv
- **Database**: [Supabase](https://supabase.com/)
- **Media storage**: [Imagekit](https://imagekit.io/)
- **Api endpoint testing**: VScode restclient

---

## configuration

- Clone the repo:

```bash
git clone https://github.com/Farhad8797/drf-ecommerce-backend.git
```

- Create virtual environment:

```bash
uv venv
```

- Activate (via git bash):

```bash
source .venv/Scripts/activate
```

- Install necessary modules:

```bash
uv sync
```

- Create a .env file and save your api keys with appropriate name

```code
SECRET_KEY=
STRIPE_SANDBOX_TEST_PRIVATE_KEY=
STRIPE_WEBHOOK_SECRET=
SUPABASE_CONNECTION_URI=
IMAGEKIT_PRIVATE_KEY=
IMAGEKIT_PUBLIC_KEY=
IMAGEKIT_URL_ENDPOINT=
STRIPE_SANDBOX_TEST_PUBLIC_KEY=
```

- Run server:

```bash
uv run py manage.py runserver
```

---

**N.B.**: I created a field for paypal id in accounts/models.py. But I didn't include any functionality for Paypal since it is a hobby project.

## Important:

Make sure you have uv installed in your system. To install uv, run the following command:

```bash
pip install uv
```
