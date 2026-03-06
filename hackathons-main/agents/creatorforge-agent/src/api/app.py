"""CreatorForge FastAPI application."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from ..agents.ad_revenue_agent import AdRevenueAgent
from ..agents.brand_strategist import BrandStrategistAgent
from ..agents.copywriter import CopywriterAgent
from ..agents.designer import DesignerAgent
from ..agents.market_scout import MarketScoutAgent
from ..agents.quality_auditor import QualityAuditorAgent
from ..config import Settings, load_settings
from ..integrations.nevermined_client import NeverminedClient
from ..integrations.openai_clients import OpenAIClients
from ..integrations.zeroclick_client import ZeroClickClient
from ..orchestration.ceo_orchestrator import CEOOrchestrator
from ..orchestration.creative_director import CreativeDirector
from ..orchestration.mindra_client import MindraClient
from ..orchestration.procurement_director import ProcurementDirector
from ..payments.http_x402 import X402HttpService
from ..pricing.policy import PricingPolicy
from ..procurement.budget_engine import BudgetEngine
from ..procurement.vendor_selector import VendorSelector
from ..storage.db import Database
from ..storage.repository import Repository
from .routes_approvals import router as approvals_router
from .routes_procurement import router as procurement_router
from .routes_seller import router as seller_router


@dataclass
class Container:
    settings: Settings
    repo: Repository
    pricing: PricingPolicy
    ceo: CEOOrchestrator
    x402: X402HttpService
    zeroclick: ZeroClickClient


def create_app() -> FastAPI:
    load_dotenv()
    settings = load_settings()

    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    db = Database(settings.db_path)
    db.initialize()
    repo = Repository(db)

    openai_clients = OpenAIClients(
        api_key=settings.openai_api_key,
        text_model=settings.openai_text_model,
        image_model=settings.openai_image_model,
    )
    nevermined = NeverminedClient(
        api_key=settings.nvm_api_key,
        environment=settings.nvm_environment,
        plan_id=settings.nvm_plan_id,
        agent_id=settings.nvm_agent_id,
        base_url=settings.nvm_base_url,
    )
    zeroclick = ZeroClickClient(
        base_url=settings.zeroclick_api_url,
        api_key=settings.zeroclick_api_key,
        timeout_seconds=settings.zeroclick_timeout_seconds,
    )
    mindra = MindraClient(
        api_url=settings.mindra_api_url,
        api_key=settings.mindra_api_key,
        timeout_seconds=settings.mindra_timeout_seconds,
    )

    copywriter = CopywriterAgent(openai_clients)
    designer = DesignerAgent(openai_clients)
    strategist = BrandStrategistAgent(openai_clients)
    auditor = QualityAuditorAgent()
    ad_agent = AdRevenueAgent(zeroclick)

    creative_director = CreativeDirector(
        copywriter=copywriter,
        designer=designer,
        strategist=strategist,
        auditor=auditor,
        ad_agent=ad_agent,
    )
    procurement_director = ProcurementDirector(
        market_scout=MarketScoutAgent(nevermined),
        budget_engine=BudgetEngine(
            daily_cap=settings.budget_daily_cap,
            vendor_cap=settings.budget_vendor_cap,
            approval_threshold=settings.approval_threshold,
        ),
        selector=VendorSelector(),
        repo=repo,
    )
    ceo = CEOOrchestrator(
        creative_director=creative_director,
        procurement_director=procurement_director,
        mindra_client=mindra,
    )

    app = FastAPI(
        title="CreatorForge Agent",
        description="Autonomous creative asset economy with x402 payments",
    )
    app.state.container = Container(
        settings=settings,
        repo=repo,
        pricing=PricingPolicy(),
        ceo=ceo,
        x402=X402HttpService(nevermined),
        zeroclick=zeroclick,
    )

    app.include_router(seller_router)
    app.include_router(procurement_router)
    app.include_router(approvals_router)

    return app


def main() -> None:
    app = create_app()
    settings: Settings = app.state.container.settings
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
