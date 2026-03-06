# Workshop 2: Nevermined + Stripe + x402 — Fiat vs Crypto Payments

**Duration:** 1 hour
**Goal:** Participants understand how the x402 payment protocol works under the hood, and how Nevermined supports both crypto (on-chain) and fiat (Stripe card) payments through the same middleware.

---

## Format Recommendation

| Element | Recommendation |
|---------|----------------|
| **Slides/Diagrams** | More than Workshop 1 — flow diagrams are essential |
| **Live demo** | Two live demos: crypto flow + fiat flow |
| **Docs site** | `docs.nevermined.app` for protocol reference |
| **Browser** | nevermined.app dashboard to show plans, balances, transactions |
| **Terminal** | For running the demo agents |

**Why more visual:** The x402 protocol and payment flows have multiple steps and actors. Diagrams make it click. But still keep slides minimal — the demos are the star.

---

## Pre-Workshop Checklist

### Your machine (presenter)

- [ ] Two Nevermined accounts ready:
  - **Seller account**: has a registered agent with TWO plans (one crypto, one fiat)
  - **Buyer account**: has credits on the crypto plan + a Stripe test card enrolled for the fiat plan
- [ ] `workshops/x402/demo/` installed and tested (`poetry install` done)
- [ ] Client script ready for both crypto and fiat flows (`workshops/x402/demo/src/client.py`)
- [ ] Stripe dashboard access (to show PaymentIntents for fiat demo)
- [ ] Browser tabs ready: nevermined.app (seller view), nevermined.app (buyer view), Stripe dashboard
- [ ] `.env` configured with all keys

### For the fiat demo

- [ ] A fiat-priced plan created in nevermined.app (price in USD, not crypto)
- [ ] Buyer has enrolled a Stripe test card via nevermined.app
- [ ] Verify the fiat flow works end-to-end before the workshop

---

## Agenda

| Time | Section | Format |
|------|---------|--------|
| 0:00 - 0:05 | The problem: How do AI agents pay each other? | Slides |
| 0:05 - 0:15 | x402 Protocol Deep Dive | Slides + diagrams |
| 0:15 - 0:25 | Demo 1: Crypto payment flow (live) | Terminal + browser |
| 0:25 - 0:30 | Crypto vs Fiat: Same protocol, different rails | Slides |
| 0:30 - 0:40 | Demo 2: Fiat/Stripe payment flow (live) | Terminal + browser + Stripe |
| 0:40 - 0:50 | Building for both: Code walkthrough | Code + slides |
| 0:50 - 0:55 | When to use crypto vs fiat | Discussion |
| 0:55 - 1:00 | Q&A + Resources | Open |

---

## Detailed Script

### Section 1: The Problem (5 min)

**[SLIDE 1: Title]**
- Workshop title, your name, logos

**[SLIDE 2: The Agent Economy Problem]**

> "We're entering a world where AI agents do work autonomously. An agent searches the web, another analyzes data, another generates reports. But how does Agent A pay Agent B for its work?"

**Key points:**
- Agents can't swipe credit cards
- Traditional payment APIs (Stripe, PayPal) are designed for human checkout flows
- We need machine-to-machine payments that work over HTTP
- Payments should be per-request, not subscriptions (though subscriptions are supported too)

> "What if we could make payments as simple as HTTP headers? That's what x402 does."

**[SLIDE 3: The x402 Idea]**

> "HTTP has status codes everyone knows: 200 OK, 401 Unauthorized, 404 Not Found. There's also 402 — Payment Required. It was reserved in 1997 for 'future use.' The future is now."

Show the one-liner:
```
402 Payment Required  →  "Pay me, then I'll serve you"
```

---

### Section 2: x402 Protocol Deep Dive (10 min)

**[SLIDE 4: x402 Flow Diagram]**

Draw or show this sequence diagram:

```
 Buyer Agent                    Seller Agent                 Nevermined
     |                               |                          |
     |  1. POST /ask                 |                          |
     |  (no payment header)          |                          |
     |------------------------------>|                          |
     |                               |                          |
     |  2. 402 Payment Required      |                          |
     |  Header: payment-required     |                          |
     |  (base64 JSON: planId,        |                          |
     |   scheme, network, credits)   |                          |
     |<------------------------------|                          |
     |                               |                          |
     |  3. Generate x402 token       |                          |
     |------------------------------------------------------>  |
     |                               |                          |
     |  4. Access token              |                          |
     |<------------------------------------------------------  |
     |                               |                          |
     |  5. POST /ask                 |                          |
     |  Header: payment-signature    |                          |
     |------------------------------>|                          |
     |                               |  6. Verify token         |
     |                               |------------------------->|
     |                               |  7. Valid ✓              |
     |                               |<-------------------------|
     |                               |                          |
     |                               |  [execute business logic] |
     |                               |                          |
     |                               |  8. Settle (burn credits)|
     |                               |------------------------->|
     |                               |  9. Receipt              |
     |                               |<-------------------------|
     |                               |                          |
     |  10. 200 OK                   |                          |
     |  Header: payment-response     |                          |
     |  (base64 JSON: credits burned,|                          |
     |   txHash, remaining balance)  |                          |
     |<------------------------------|                          |
```

> "The beauty of x402 is that it uses standard HTTP. No WebSockets, no special protocols. Any HTTP client can participate."

**[SLIDE 5: The Three Headers]**

| Header | Direction | When | Contains |
|--------|-----------|------|----------|
| `payment-required` | Server → Client | 402 response | What to pay: plan ID, scheme, credits needed |
| `payment-signature` | Client → Server | Retry request | x402 access token (proof of payment authorization) |
| `payment-response` | Server → Client | 200 response | Receipt: credits burned, tx hash, remaining balance |

**Walk through each header with a real decoded example:**

```json
// payment-required (decoded from base64)
{
  "x402Version": 2,
  "resource": { "url": "POST /ask" },
  "accepts": [{
    "scheme": "nvm:erc4337",
    "network": "eip155:84532",
    "planId": "plan_abc123",
    "extra": { "agentId": "agent_xyz" }
  }],
  "extensions": {}
}
```

> "The server tells the client exactly what it accepts. The client picks a scheme, gets a token, and retries."

**[SLIDE 6: Verify & Settle — The Two-Step]**

> "The seller doesn't handle money directly. The middleware calls Nevermined to verify the token (is this valid? does the buyer have credits?) and then settle (burn the credits, record the transaction). This is atomic — if settlement fails, the response still goes through but credits aren't charged."

Emphasize:
- **Verify** = read-only check (no credits burned)
- **Settle** = write operation (credits burned on-chain, or Stripe card charged for fiat)
- Seller never touches the buyer's wallet or card directly

---

### Section 3: Demo 1 — Crypto Payment Flow (10 min)

**[SWITCH TO TERMINAL]**

> "Let's see the crypto flow in action. I have an agent running that's protected with x402 middleware."

**Setup: Start the seller agent**

```bash
# Terminal 1 — start the demo agent
cd workshops/x402/demo
poetry run python -m src.agent
# Running on http://localhost:3000
```

**Step 1: Call without payment**

```bash
curl -X POST http://localhost:3000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is quantum computing?"}' \
  -v 2>&1 | head -30
```

> "We get a 402. Look at the `payment-required` header."

**Step 2: Decode the payment-required header**

```bash
# Copy the base64 value and decode it
echo "<base64-value>" | base64 -d | python -m json.tool
```

> "It tells us: plan ID, scheme `nvm:erc4337`, network `eip155:84532` (Base Sepolia). This is the crypto scheme."

**Step 3: Run the client script (full flow)**

```bash
# Terminal 2 — run client
poetry run python -m src.client
```

Walk through the output:
1. "Request WITHOUT payment token... 402 Payment Required"
2. "Resolved scheme: nvm:erc4337"
3. "Token obtained"
4. "Retry WITH payment token... 200 OK"
5. "Settlement Receipt: creditsRedeemed: 1"

**Step 4: Show it on nevermined.app**

Switch to browser and show:
- The buyer's credit balance decreased
- The transaction appears in the agent's analytics
- The on-chain transaction (link to Base Sepolia block explorer)

> "That credit burn happened on-chain. It's an ERC-1155 token burn on Base Sepolia. Fully transparent, fully auditable."

---

### Section 4: Crypto vs Fiat — Same Protocol, Different Rails (5 min)

**[SLIDE 7: Two Schemes, One Protocol]**

```
                    x402 Protocol
                   ┌─────────────┐
                   │  Same HTTP   │
                   │  Same headers│
                   │  Same SDK    │
                   │  Same code   │
                   └──────┬──────┘
                          │
              ┌───────────┴───────────┐
              │                       │
    ┌─────────▼─────────┐  ┌─────────▼─────────┐
    │   nvm:erc4337      │  │ nvm:card-delegation│
    │                    │  │                    │
    │  On-chain credits  │  │  Stripe card       │
    │  ERC-1155 on Base  │  │  Auto-recharge     │
    │  Crypto wallets    │  │  USD via credit card│
    │  Instant settlement│  │  Familiar payment  │
    └────────────────────┘  └────────────────────┘
```

> "Here's the key insight: **the seller's code doesn't change**. The middleware is identical. The difference is in how the buyer gets their token and how settlement happens behind the scenes."

**[SLIDE 8: Side-by-Side Comparison]**

| Aspect | Crypto (`nvm:erc4337`) | Fiat (`nvm:card-delegation`) |
|--------|----------------------|------------------------------|
| **Plan type** | FIXED_PRICE | FIXED_FIAT_PRICE |
| **Plan `isCrypto`** | `true` | `false` |
| **How buyer pays** | USDC on Base chain | Credit card via Stripe |
| **Credit storage** | ERC-1155 on-chain | ERC-1155 on-chain (auto-minted) |
| **Settlement** | Burn on-chain | Charge card → mint credits → burn |
| **Network in token** | `eip155:84532` | `stripe` |
| **Buyer needs** | Crypto wallet + USDC | Stripe card enrolled in nevermined.app |
| **Seller code** | `PaymentMiddleware(...)` | `PaymentMiddleware(...)` (same!) |
| **Latency** | ~2-3 seconds | ~3-5 seconds |

> "For the seller, it's literally zero code change. The middleware auto-detects the scheme from the plan metadata. For the buyer, the SDK handles the scheme differences — you just call `get_x402_access_token()` with optional token options."

**[SLIDE 9: The Fiat Magic — Card Delegation]**

> "The fiat flow is clever. When a buyer enrolls a credit card, they create a 'delegation' — permission for Nevermined to charge the card up to a spending limit. It's like a pre-authorized tab at a bar."

```
Card Delegation Flow:
1. Buyer enrolls card at nevermined.app → Stripe pm_xxx stored
2. Buyer requests token with CardDelegationConfig:
   - providerPaymentMethodId: "pm_xxx"
   - spendingLimitCents: 10000 ($100)
   - durationSecs: 604800 (7 days)
3. Nevermined validates card ownership via Stripe API
4. Creates delegation entity + signs JWT
5. On settlement: if credits insufficient:
   a. Charge card (Stripe PaymentIntent, off-session)
   b. Mint credits on-chain
   c. Burn credits (same as crypto)
```

> "The buyer's card is charged automatically when they run out of credits. It's like auto-recharge on a prepaid account. And because credits are still on-chain, the seller's settlement code is identical."

---

### Section 5: Demo 2 — Fiat/Stripe Payment Flow (10 min)

**[SWITCH TO TERMINAL + BROWSER]**

> "Now let's see the fiat flow. Same agent, same code, different plan."

**NOTE TO PRESENTER:** For this demo, you need:
- A fiat-priced plan (created in nevermined.app with USD pricing)
- A buyer account with an enrolled Stripe test card
- The Stripe dashboard open to show PaymentIntents

**Step 1: Show the fiat plan in nevermined.app**

> "I've created a second plan on this agent — same agent, but priced in USD instead of crypto credits. Notice in the plan metadata: `isCrypto: false`. That's what triggers the fiat flow."

**Step 2: Show enrolled payment method**

> "My buyer account has a Stripe card enrolled. In the Nevermined app, under payment methods, you can see the card — Visa ending in 4242 (our test card)."

**Step 3: Run the fiat client**

```bash
# Terminal 2 — run client with fiat plan (same agent, just swap the plan ID)
cd workshops/x402/demo
NVM_PLAN_ID=plan_fiat_xxx poetry run python -m src.client
```

The client auto-detects the scheme via `resolve_scheme()` and builds the `CardDelegationConfig` automatically.

Walk through the output:
1. "Detected scheme: `nvm:card-delegation`"
2. "Card: visa ending in 4242"
3. "Generated delegation token..."
4. "Calling /ask with payment-signature header..."
5. "Got 200! Answer: [AI response]"
6. "Credits used: 1, Network: stripe"

**Step 4: Show Stripe dashboard**

Switch to Stripe dashboard and show:
- The PaymentIntent that was created
- Amount charged in USD
- Metadata: `source: nvm-card-delegation`, `delegationId`, `userId`

> "There it is in Stripe. A real card charge, triggered by an AI agent making an HTTP request. The seller's code didn't change at all — the middleware handled everything."

**Step 5: Show the on-chain side**

> "Even with fiat, credits still exist on-chain. The card charge minted credits, then the settlement burned them. So you get the audit trail of on-chain settlement with the convenience of card payments."

---

### Section 6: Building for Both — Code Walkthrough (10 min)

**[SLIDE 10: Seller Code — Zero Changes Needed]**

> "Let me show you the seller's perspective. This is all the code you need."

**Show the middleware (Python):**

```python
from payments_py import Payments, PaymentOptions
from payments_py.x402.fastapi import PaymentMiddleware

payments = Payments.get_instance(PaymentOptions(
    nvm_api_key=os.getenv("NVM_API_KEY"),
    environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
))

# This handles BOTH crypto and fiat automatically
app.add_middleware(
    PaymentMiddleware,
    payments=payments,
    routes={
        "POST /ask": {"plan_id": os.getenv("NVM_PLAN_ID"), "credits": 1},
    },
)
```

> "That's it. The middleware calls `resolveScheme()` internally, which fetches the plan metadata and determines if it's crypto or fiat. Then it builds the correct `payment-required` response for 402s and handles verify/settle appropriately."

**Show the middleware (TypeScript):**

```typescript
import { paymentMiddleware } from "@nevermined-io/payments/express";

app.use(paymentMiddleware(payments, {
  "POST /ask": { planId: PLAN_ID, credits: 1 },
}));
```

> "TypeScript is the same — one line of middleware. Works for both schemes."

**[CODE WALKTHROUGH: Buyer adaptation]**

> "The buyer needs slightly more code for fiat, because they need to specify the card delegation config. But the SDK makes it easy."

```python
from payments_py.x402.token_api import X402TokenOptions, CardDelegationConfig
from payments_py.x402.resolve_scheme import resolve_scheme

# Auto-detect scheme from plan metadata
scheme = resolve_scheme(payments, plan_id)

if scheme == "nvm:card-delegation":
    # Fiat plan — need delegation config
    methods = payments.delegation.list_payment_methods()
    token_options = X402TokenOptions(
        scheme=scheme,
        delegation_config=CardDelegationConfig(
            provider_payment_method_id=methods[0].id,
            spending_limit_cents=10_000,
            duration_secs=604_800,
            currency="usd",
        ),
    )
else:
    # Crypto plan — no extra config needed
    token_options = X402TokenOptions(scheme=scheme)

# Same call for both schemes
token = payments.x402.get_x402_access_token(plan_id, token_options=token_options)
```

> "Notice the function `resolve_scheme()` does the heavy lifting. It reads the plan's `isCrypto` field and returns the right scheme. The buyer code just branches on the scheme to add delegation config if needed."

**[SLIDE 11: Architecture — How It All Connects]**

```
┌──────────────────────────────────────────────────────────┐
│                     Nevermined Platform                    │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐ │
│  │  Plans API   │  │ Permissions │  │   Delegation     │ │
│  │             │  │   (x402)    │  │    Service       │ │
│  │ - create    │  │             │  │                  │ │
│  │ - subscribe │  │ - generate  │  │ - create         │ │
│  │ - balance   │  │ - verify    │  │ - validate card  │ │
│  │             │  │ - settle    │  │ - charge (Stripe)│ │
│  └─────────────┘  └─────────────┘  └──────────────────┘ │
│         │                │                │               │
│  ┌──────▼────────────────▼────────────────▼──────────┐   │
│  │              Smart Contracts (Base)                │   │
│  │  ERC-1155 Credits: mint / burn / transfer         │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
   ┌─────┴─────┐       ┌─────┴─────┐       ┌─────┴─────┐
   │  Seller    │       │   Buyer    │       │  Stripe   │
   │  Agent     │       │   Agent    │       │  (fiat)   │
   │            │       │            │       │           │
   │ middleware │       │ SDK calls  │       │ pm_xxx    │
   │ verify()   │       │ get_token()│       │ charge()  │
   │ settle()   │       │            │       │ mint()    │
   └────────────┘       └────────────┘       └───────────┘
```

---

### Section 7: When to Use Crypto vs Fiat (5 min)

**[SLIDE 12: Decision Guide]**

> "So when should you use each scheme? Here's a practical guide."

| Use Case | Recommended Scheme | Why |
|----------|-------------------|-----|
| **Agent-to-agent payments** | Crypto | Agents don't have credit cards |
| **Human users buying from agents** | Fiat | Familiar payment experience |
| **Hackathon prototyping** | Crypto (sandbox) | Faster setup, no card enrollment needed |
| **Production with enterprise customers** | Fiat | Enterprises prefer invoices and cards |
| **Micropayments (< $0.01)** | Crypto | Card processing fees make micro-fiat impractical |
| **Global users without crypto** | Fiat | Lower barrier to entry |
| **Both agent and human buyers** | Both (two plans) | Same agent, two plans on same endpoint |

> "The good news: you don't have to choose upfront. You can create two plans on the same agent — one crypto, one fiat — and the middleware handles both automatically. Your business logic doesn't change."

**Discussion prompt:**

> "For your hackathon project, which scheme makes more sense? Think about who your buyer is — another agent, or a human?"

---

### Section 8: Q&A + Resources (5 min)

**[SLIDE 13: Key Takeaways]**

1. **x402 = HTTP payments via headers** — 402 response, `payment-signature` header, settlement receipt
2. **Two schemes, one protocol** — crypto (ERC-4337) and fiat (Stripe card delegation)
3. **Seller code is scheme-agnostic** — the middleware handles both
4. **Buyer adapts slightly** — fiat needs `CardDelegationConfig`, crypto is zero-config
5. **Credits are always on-chain** — even fiat mints credits before burning them

**[SLIDE 14: Resources]**

| Resource | URL |
|----------|-----|
| Nevermined Docs | https://docs.nevermined.app |
| x402 Protocol Spec | https://github.com/coinbase/x402 |
| Payments Python SDK | https://github.com/nevermined-io/payments-py |
| Payments TypeScript SDK | https://github.com/nevermined-io/payments |
| Stripe Test Cards | https://docs.stripe.com/testing#cards |
| Nevermined App (enroll cards) | https://nevermined.app |
| Hackathon Starter Kits | This repo (`starter-kits/`) |

---

## Troubleshooting Notes (for presenter)

| Issue | Fix |
|-------|-----|
| Fiat plan not detected as fiat | Check plan metadata — `isCrypto` must be `false` |
| Card delegation fails | Verify card is enrolled in nevermined.app for the buyer account |
| Stripe PaymentIntent fails | Check Stripe dashboard for error; common: `pm_xxx` not attached to customer |
| `resolve_scheme()` returns wrong scheme | Cache may be stale (5-min TTL); restart agent |
| Settlement succeeds but no Stripe charge | Buyer still had on-chain credits; card is only charged when credits run out |
| "No payment methods found" | Buyer needs to enroll a card at nevermined.app first |

## Backup Plan

If fiat demo fails (Stripe sandbox issues, card enrollment problems):
1. **Focus on the crypto demo** — it's more reliable on sandbox
2. **Show the code diff** — walk through the client's `resolve_scheme` + `CardDelegationConfig` from `workshops/x402/demo/src/client.py`
3. **Show Stripe dashboard screenshots** — pre-captured PaymentIntent screenshots
4. **Architecture slides** — spend more time on the diagrams and protocol explanation
