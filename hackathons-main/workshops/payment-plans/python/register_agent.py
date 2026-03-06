"""
Nevermined Lab: Payment Plans — Register Agent + Plan

Complete registration: create an agent and attach a payment plan
in a single call.
"""

import os
import urllib3
from payments_py import Payments, PaymentOptions
from payments_py.plans import get_erc20_price_config, get_fixed_credits_config
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

# USDC on Base Sepolia (sandbox)
USDC_ADDRESS = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

payments = Payments.get_instance(
    PaymentOptions(
        nvm_api_key=os.getenv("NVM_API_KEY", ""),
        environment=os.getenv("NVM_ENVIRONMENT", "sandbox"),
    )
)

builder_address = payments.account_address

result = payments.agents.register_agent_and_plan(
    agent_metadata={
        "name": "My AI Agent",
        "description": "AI analysis service",
        "tags": ["ai", "analysis"],
    },
    agent_api={
        "endpoints": [{"POST": "https://your-server.com/ask"}],
        "agentDefinitionUrl": "https://your-server.com/openapi.json",
    },
    plan_metadata={
        "name": "Pro Plan",
        "description": "100 credits for 10 USDC",
    },
    price_config=get_erc20_price_config(
        10_000_000,  # 10 USDC (6 decimals)
        USDC_ADDRESS,
        builder_address,
    ),
    credits_config=get_fixed_credits_config(100, 1),
    access_limit="credits",
)

print(f"Agent ID: {result['agentId']}")
print(f"Plan ID:  {result['planId']}")
