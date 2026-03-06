import os

from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from openai import OpenAI
from payments_py import Payments, PaymentOptions
from payments_py.x402.fastapi import PaymentMiddleware
from pydantic import BaseModel

NVM_API_KEY = os.environ["NVM_API_KEY"]
NVM_ENVIRONMENT = os.environ.get("NVM_ENVIRONMENT", "sandbox")
NVM_PLAN_ID = os.environ["NVM_PLAN_ID"]
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

payments = Payments.get_instance(
    PaymentOptions(nvm_api_key=NVM_API_KEY, environment=NVM_ENVIRONMENT)
)

SYSTEM_PROMPT = """You are a technology trends analyst. You provide concise, insightful answers
about current and emerging technology trends including AI, cloud computing, cybersecurity,
blockchain, quantum computing, and software development practices.
Keep answers focused and under 300 words."""

app = FastAPI(title="x402 Workshop Demo")

app.add_middleware(
    PaymentMiddleware,
    payments=payments,
    routes={
        "POST /ask": {"plan_id": NVM_PLAN_ID, "credits": 1},
    },
)


class AskRequest(BaseModel):
    query: str


@app.post("/ask")
async def ask(body: AskRequest) -> JSONResponse:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": body.query},
        ],
        max_tokens=500,
    )
    answer = completion.choices[0].message.content

    return JSONResponse(content={"response": answer})


@app.get("/health")
async def health():
    return {"status": "ok"}


def main():
    port = int(os.environ.get("PORT", 3000))
    print(f"x402 Workshop Demo running on http://localhost:{port}")
    print(f"Plan ID: {NVM_PLAN_ID}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
