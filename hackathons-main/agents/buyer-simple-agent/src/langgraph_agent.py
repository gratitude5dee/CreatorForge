"""
LangGraph agent definition with buyer tools for x402 data purchasing.

LangGraph counterpart of strands_agent.py. The tools are plain @tool —
NOT @requires_payment — because the buyer generates tokens, not receives them.
The x402 flow (token generation + HTTP call) happens inside the tools.

Usage:
    from src.langgraph_agent import payments, create_agent, NVM_PLAN_ID
"""

import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from payments_py import Payments, PaymentOptions

from .budget import Budget
from .log import get_logger, log
from .tools.balance import check_balance_impl
from .tools.discover import discover_pricing_impl
from .tools.purchase import purchase_data_impl

load_dotenv()

NVM_API_KEY = os.environ["NVM_API_KEY"]
NVM_ENVIRONMENT = os.getenv("NVM_ENVIRONMENT", "sandbox")
NVM_PLAN_ID = os.environ["NVM_PLAN_ID"]
NVM_AGENT_ID = os.getenv("NVM_AGENT_ID")
SELLER_URL = os.getenv("SELLER_URL", "http://localhost:3000")

MAX_DAILY_SPEND = int(os.getenv("MAX_DAILY_SPEND", "0"))
MAX_PER_REQUEST = int(os.getenv("MAX_PER_REQUEST", "0"))

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key=NVM_API_KEY, environment=NVM_ENVIRONMENT)
)

budget = Budget(max_daily=MAX_DAILY_SPEND, max_per_request=MAX_PER_REQUEST)

_logger = get_logger("buyer.langgraph")


# ---------------------------------------------------------------------------
# Buyer tools (plain @tool — no @requires_payment)
# ---------------------------------------------------------------------------


@tool
def discover_pricing(seller_url: str = "") -> str:
    """Discover a seller's available data services and pricing tiers.

    Call this first to understand what data is available and how much it costs.

    Args:
        seller_url: Base URL of the seller (defaults to SELLER_URL env var).
    """
    url = seller_url or SELLER_URL
    result = discover_pricing_impl(url)
    return result["content"][0]["text"]


@tool
def check_balance() -> str:
    """Check your Nevermined credit balance and daily budget status.

    Returns your remaining credits on the seller's plan and your
    local spending budget status.
    """
    log(_logger, "TOOLS", "BALANCE", f"plan={NVM_PLAN_ID[:12]}")
    result = check_balance_impl(payments, NVM_PLAN_ID)
    budget_status = budget.get_status()

    text = result["content"][0]["text"]
    text += (
        f"\n\nLocal budget:"
        f"\n  Daily limit: {budget_status['daily_limit']}"
        f"\n  Daily spent: {budget_status['daily_spent']}"
        f"\n  Daily remaining: {budget_status['daily_remaining']}"
        f"\n  Total spent (session): {budget_status['total_spent']}"
    )
    return text


@tool
def purchase_data(query: str, seller_url: str = "") -> str:
    """Purchase data from a seller using x402 payment.

    Generates an x402 access token and sends the query to the seller.
    Budget limits are checked before purchasing.

    Args:
        query: The data query to send to the seller.
        seller_url: Base URL of the seller (defaults to SELLER_URL env var).
    """
    url = seller_url or SELLER_URL

    # Pre-check with minimum 1 credit
    allowed, reason = budget.can_spend(1)
    if not allowed:
        return f"Budget check failed: {reason}"

    result = purchase_data_impl(
        payments=payments,
        plan_id=NVM_PLAN_ID,
        seller_url=url,
        query=query,
        agent_id=NVM_AGENT_ID,
    )

    credits_used = result.get("credits_used", 0)
    if result.get("status") == "success" and credits_used > 0:
        budget.record_purchase(credits_used, url, query)

    return result["content"][0]["text"]


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a data buying agent. You help users discover and purchase data from \
sellers using the x402 HTTP payment protocol.

Your workflow:
1. **discover_pricing** — Call this first to see what the seller offers.
2. **check_balance** — Check your credit balance and budget before purchasing.
3. **purchase_data** — Buy data by sending an x402-protected HTTP request.

Important guidelines:
- Always discover the seller first so you can inform the user about costs.
- Check the balance before making a purchase to show the user their credit status.
- Even if the balance shows "not subscribed", you CAN still purchase. The x402
  payment flow handles subscription automatically during the verify/settle step.
- Tell the user the expected cost BEFORE purchasing and confirm they want to proceed.
- After a purchase, report what was received and the credits spent.
- If budget limits are exceeded, explain the situation and suggest alternatives.
- You can purchase from different sellers by providing their URL."""

TOOLS = [discover_pricing, check_balance, purchase_data]


def create_agent(model=None):
    """Create a LangGraph ReAct agent with buyer tools.

    Args:
        model: A LangChain-compatible chat model. If None, uses ChatOpenAI
               with MODEL_ID from env (default gpt-4o-mini).

    Returns:
        Compiled LangGraph graph with buyer tools.
    """
    if model is None:
        model = ChatOpenAI(
            model=os.getenv("MODEL_ID", "gpt-4o-mini"),
            temperature=0,
        )
    return create_react_agent(model, TOOLS, prompt=SYSTEM_PROMPT)
