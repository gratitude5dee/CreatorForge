"""
LangGraph agent definition with Nevermined x402 payment-protected tools.

LangGraph counterpart of strands_agent.py. Both agent.py (FastAPI) and
agent_agentcore.py can import from here. The tools use plain functions from
tools/ modules, wrapped with @tool + @requires_payment decorators.

Usage:
    from src.langgraph_agent import payments, create_agent, NVM_PLAN_ID
"""

import os

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from payments_py import Payments, PaymentOptions
from payments_py.x402.langchain import requires_payment

from .tools.market_research import research_market_impl
from .tools.summarize import summarize_content_impl
from .tools.web_search import search_web

load_dotenv()

NVM_API_KEY = os.environ["NVM_API_KEY"]
NVM_ENVIRONMENT = os.getenv("NVM_ENVIRONMENT", "sandbox")
NVM_PLAN_ID = os.environ["NVM_PLAN_ID"]
NVM_AGENT_ID = os.getenv("NVM_AGENT_ID")

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key=NVM_API_KEY, environment=NVM_ENVIRONMENT)
)


# ---------------------------------------------------------------------------
# Payment-protected LangGraph tools
# ---------------------------------------------------------------------------


@tool
@requires_payment(
    payments=payments,
    plan_id=NVM_PLAN_ID,
    credits=1,
    agent_id=NVM_AGENT_ID,
)
def search_data(query: str, max_results: int = 5, config: RunnableConfig = None) -> str:
    """Search the web for data. Costs 1 credit per request.

    Args:
        query: The search query to run.
        max_results: Maximum number of results to return.
    """
    result = search_web(query, max_results)
    return result["content"][0]["text"]


@tool
@requires_payment(
    payments=payments,
    plan_id=NVM_PLAN_ID,
    credits=5,
    agent_id=NVM_AGENT_ID,
)
def summarize_data(content: str, focus: str = "key_findings", config: RunnableConfig = None) -> str:
    """Summarize content with LLM-powered analysis. Costs 5 credits per request.

    Args:
        content: The text content to summarize.
        focus: Focus area - 'key_findings', 'action_items', 'trends', or 'risks'.
    """
    result = summarize_content_impl(content, focus)
    return result["content"][0]["text"]


@tool
@requires_payment(
    payments=payments,
    plan_id=NVM_PLAN_ID,
    credits=10,
    agent_id=NVM_AGENT_ID,
)
def research_data(query: str, depth: str = "standard", config: RunnableConfig = None) -> str:
    """Conduct full market research with a multi-source report. Costs 10 credits per request.

    Args:
        query: The research topic or question.
        depth: Research depth - 'standard' or 'deep'.
    """
    result = research_market_impl(query, depth)
    return result["content"][0]["text"]


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a data selling agent. You provide data services at three pricing tiers:

1. **search_data** (1 credit) - Basic web search. Use this for quick lookups.
2. **summarize_data** (5 credits) - LLM-powered content summarization. Use this \
when the user wants analysis of specific content.
3. **research_data** (10 credits) - Full market research report. Use this for \
comprehensive research questions.

Choose the appropriate tool based on the user's request complexity. If the user \
asks for a simple search, use search_data. If they want analysis or summary, use \
summarize_data. For in-depth research, use research_data.

Always be helpful and explain what data you found."""

TOOLS = [search_data, summarize_data, research_data]


def create_agent(model=None):
    """Create a LangGraph ReAct agent.

    Args:
        model: A LangChain-compatible chat model. If None, uses ChatOpenAI
               with MODEL_ID from env (default gpt-4o-mini).

    Returns:
        Compiled LangGraph graph with payment-protected tools.
    """
    if model is None:
        model = ChatOpenAI(
            model=os.getenv("MODEL_ID", "gpt-4o-mini"),
            temperature=0,
        )
    return create_react_agent(model, TOOLS, prompt=SYSTEM_PROMPT)


def run_agent(graph, query: str, payment_token: str) -> str:
    """Run the LangGraph agent with a payment token.

    Args:
        graph: Compiled LangGraph graph from create_agent().
        query: User query.
        payment_token: x402 access token from the buyer.

    Returns:
        The agent's final text response.
    """
    result = graph.invoke(
        {"messages": [("human", query)]},
        config={"configurable": {"payment_token": payment_token}},
    )
    messages = result.get("messages", [])
    if messages:
        final = messages[-1]
        return final.content if hasattr(final, "content") else str(final)
    return "No response generated."
