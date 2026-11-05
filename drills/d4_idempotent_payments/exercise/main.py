"""⏱ 30 minutes. Make this payments API safe to retry.

POST /payments                       {amount_cents > 0, currency "USD"|"EUR", customer_id}
POST /payments/{id}/refunds          {amount_cents > 0}
GET  /payments/{id}

Requirements (see test_d4.py):
  1. Both POSTs require an Idempotency-Key header (400 without it).
  2. Same key + same body  -> replay the original response (same status & body), header Idempotent-Replayed: true,
                              and NO second gateway call.
  3. Same key + different body -> 409.
  4. CONCURRENT duplicates (5 identical requests at once) -> exactly ONE gateway charge.
  5. Refunds: the total refunded can't exceed the amount (422); payment status becomes
     "partially_refunded" / "refunded". Concurrent refunds must not over-refund.
  6. Keys are scoped per endpoint: the same key on /payments and /refunds doesn't collide.
"""
import asyncio
from collections import defaultdict  # noqa: F401
from typing import Annotated, Literal  # noqa: F401

from fastapi import FastAPI, Header, HTTPException, Response  # noqa: F401
from pydantic import BaseModel, Field

app = FastAPI(title="D4 · Idempotent payments")

PAYMENTS: dict[int, dict] = {}
GATEWAY_CALLS: list[dict] = []
IDEMPOTENCY: dict[str, dict] = {}
LOCKS: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


class PaymentIn(BaseModel):
    amount_cents: int = Field(gt=0)
    currency: Literal["USD", "EUR"]
    customer_id: str = Field(min_length=1)


class RefundIn(BaseModel):
    amount_cents: int = Field(gt=0)


async def gateway(kind: str, **details) -> None:
    await asyncio.sleep(0.05)
    GATEWAY_CALLS.append({"kind": kind, **details})


@app.post("/payments", status_code=201)
async def create_payment(data: PaymentIn):
    await gateway("charge", amount_cents=data.amount_cents, customer_id=data.customer_id)
    payment_id = len(PAYMENTS) + 1
    PAYMENTS[payment_id] = {"id": payment_id, **data.model_dump(), "refunded_cents": 0, "status": "succeeded"}
    return PAYMENTS[payment_id]


@app.post("/payments/{payment_id}/refunds", status_code=201)
async def refund(payment_id: int, data: RefundIn):
    payment = PAYMENTS.get(payment_id)
    if payment is None:
        raise HTTPException(404, "Payment not found")
    await gateway("refund", payment_id=payment_id, amount_cents=data.amount_cents)
    payment["refunded_cents"] += data.amount_cents
    return {"payment_id": payment_id, "amount_cents": data.amount_cents, "payment_status": payment["status"]}


@app.get("/payments/{payment_id}")
async def get_payment(payment_id: int):
    if payment_id not in PAYMENTS:
        raise HTTPException(404, "Payment not found")
    return PAYMENTS[payment_id]
