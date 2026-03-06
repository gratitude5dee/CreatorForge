"""
Interactive CLI for the LangGraph data buying agent.

LangGraph counterpart of agent.py. Read-eval-print loop: user types queries,
the LangGraph ReAct agent orchestrates buyer tools (discover, check balance,
purchase) autonomously.

Usage:
    poetry run python -m src.server_langgraph
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from .langgraph_agent import NVM_PLAN_ID, SELLER_URL, create_agent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    print("OPENAI_API_KEY is required. Set it in .env file.")
    sys.exit(1)


def main():
    """Run the interactive buyer agent CLI."""
    graph = create_agent()

    print("=" * 60)
    print("Data Buying Agent (LangGraph) — Interactive CLI")
    print("=" * 60)
    print(f"Mode: http (x402)")
    print(f"Plan ID: {NVM_PLAN_ID}")
    print(f"Seller: {SELLER_URL}")
    print("\nType your queries (or 'quit' to exit):")
    print("Examples:")
    print('  "How many credits do I have?"')
    print('  "Search for the latest AI agent trends"')
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        try:
            result = graph.invoke({"messages": [("human", user_input)]})
            messages = result.get("messages", [])
            if messages:
                final = messages[-1]
                answer = final.content if hasattr(final, "content") else str(final)
            else:
                answer = "No response generated."
            print(f"\nAgent: {answer}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
