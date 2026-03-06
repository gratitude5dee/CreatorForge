"""
x402 Client - Tests the full payment flow against the tech trends agent.

Steps:
1. Request without token -> 402 Payment Required
2. Decode payment requirements from header
3. Resolve scheme & generate x402 access token
4. Retry with token -> 200 OK
5. Show response and credits used from settlement
"""

import base64
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

import httpx

from payments_py import Payments, PaymentOptions
from payments_py.x402.fastapi import X402_HEADERS
from payments_py.x402.resolve_scheme import resolve_scheme
from payments_py.x402.types import CardDelegationConfig, X402TokenOptions

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:3000")
NVM_API_KEY = os.getenv("NVM_API_KEY", "")
NVM_ENVIRONMENT = os.getenv("NVM_ENVIRONMENT", "sandbox")
NVM_PLAN_ID = os.getenv("NVM_PLAN_ID", "")

if not NVM_API_KEY or not NVM_PLAN_ID:
    print("Error: NVM_API_KEY and NVM_PLAN_ID environment variables are required.")
    sys.exit(1)

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key=NVM_API_KEY, environment=NVM_ENVIRONMENT)
)


def decode_header(b64: str) -> dict:
    return json.loads(base64.b64decode(b64).decode())


def pp(obj: dict) -> str:
    return json.dumps(obj, indent=2)


def main():
    print("=" * 60)
    print("Tech Trends Agent - x402 Payment Flow Test")
    print("=" * 60)
    print(f"Server:  {SERVER_URL}")
    print(f"Plan ID: {NVM_PLAN_ID}")

    query = "What are the top AI trends for 2026?"

    with httpx.Client(timeout=60.0) as client:
        # Step 1: Request without token -> 402
        print(f"\n{'=' * 60}")
        print("STEP 1: Request WITHOUT payment token")
        print("=" * 60)

        resp1 = client.post(
            f"{SERVER_URL}/ask",
            json={"query": query},
        )
        print(f"Status: {resp1.status_code}")

        if resp1.status_code != 402:
            print(f"Expected 402, got {resp1.status_code}. Is the server running?")
            sys.exit(1)

        print("Got 402 Payment Required (expected)")

        # Step 2: Parse payment requirements
        print(f"\n{'=' * 60}")
        print("STEP 2: Parse payment requirements from 402 response")
        print("=" * 60)

        pr_header = resp1.headers.get(X402_HEADERS["PAYMENT_REQUIRED"])
        if not pr_header:
            print(f"Missing '{X402_HEADERS['PAYMENT_REQUIRED']}' header")
            sys.exit(1)

        payment_required = decode_header(pr_header)
        print(f"\nPayment Requirements:\n{pp(payment_required)}")

        # Step 3: Get x402 access token
        print(f"\n{'=' * 60}")
        print("STEP 3: Get x402 access token")
        print("=" * 60)

        scheme = resolve_scheme(payments, NVM_PLAN_ID)
        print(f"Resolved scheme: {scheme}")

        token_options = X402TokenOptions(scheme=scheme)

        if scheme == "nvm:card-delegation":
            print("Fiat plan detected - configuring card delegation...")
            methods = payments.delegation.list_payment_methods()
            if not methods:
                print("No payment methods found. Add a card in the Nevermined dashboard.")
                sys.exit(1)
            pm = methods[0]
            print(f"Using card: {pm.brand} *{pm.last4}")
            token_options = X402TokenOptions(
                scheme=scheme,
                delegation_config=CardDelegationConfig(
                    provider_payment_method_id=pm.id,
                    spending_limit_cents=10000,
                    duration_secs=604800,
                    currency="usd",
                ),
            )
        else:
            print("Crypto plan detected (ERC-4337)")

        token_result = payments.x402.get_x402_access_token(
            NVM_PLAN_ID, token_options=token_options
        )
        access_token = token_result["accessToken"]
        print(f"Token obtained ({len(access_token)} chars)")

        # Step 4: Retry with token -> 200
        print(f"\n{'=' * 60}")
        print("STEP 4: Retry WITH payment token")
        print("=" * 60)

        resp2 = client.post(
            f"{SERVER_URL}/ask",
            headers={X402_HEADERS["PAYMENT_SIGNATURE"]: access_token},
            json={"query": query},
        )
        print(f"Status: {resp2.status_code}")

        if resp2.status_code != 200:
            print(f"Expected 200, got {resp2.status_code}")
            print(f"Body: {resp2.text}")
            sys.exit(1)

        body = resp2.json()
        print(f"\nAgent Response:\n{body.get('response', body)}")

        # Step 5: Show credits used from settlement
        print(f"\n{'=' * 60}")
        print("STEP 5: Settlement & credits used")
        print("=" * 60)

        pr_header = resp2.headers.get(X402_HEADERS["PAYMENT_RESPONSE"])
        if pr_header:
            settlement = decode_header(pr_header)
            print(f"\nSettlement Receipt:\n{pp(settlement)}")
            if "creditsRedeemed" in settlement:
                print(f"\nCredits used: {settlement['creditsRedeemed']}")
        else:
            print("No settlement header (credits settled asynchronously)")

        # Summary
        print(f"\n{'=' * 60}")
        print("FLOW COMPLETE")
        print("=" * 60)
        print(f"  1. No token      -> 402 Payment Required")
        print(f"  2. Requirements   -> plan_id, scheme, network")
        print(f"  3. Token obtained -> scheme: {scheme}")
        print(f"  4. With token     -> 200 OK")
        print(f"  5. Settlement     -> credits burned")


if __name__ == "__main__":
    main()
