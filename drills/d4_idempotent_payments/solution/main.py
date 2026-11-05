import asyncio
from collections import defaultdict
from typing import Annotated, Literal

from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI(title="D4 · Idempotent payments")

PAYMENTS: dict[int, dict] = {}
GATEWAY_CALLS: list[dict] = []  # every real charge/refund sent to the "card network"
IDEMPOTENCY: dict[str, dict] = {}  # key -> {"fingerprint", "status", "body"}
LOCKS: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)  # prod: Redis lock or a DB unique row


class PaymentIn(BaseModel):
    amount_cents: int = Field(gt=0)
    currency: Literal["USD", "EUR"]
    customer_id: str = Field(min_length=1)


class RefundIn(BaseModel):
    amount_cents: int = Field(gt=0)


async def gateway(kind: str, **details) -> None:
    await asyncio.sleep(0.05)  # slow network call: the window where concurrent duplicates sneak in
    GATEWAY_CALLS.append({"kind": kind, **details})


def status_of(payment: dict) -> str:
    if payment["refunded_cents"] == 0:
        return "succeeded"
    return "refunded" if payment["refunded_cents"] == payment["amount_cents"] else "partially_refunded"


async def idempotent(key: str | None, scope: str, fingerprint: str, response: Response, work):
    """Run `work()` once per (scope, key). Replays the stored result for retries, even concurrent ones."""
    if not key:
        raise HTTPException(400, "Idempotency-Key header required")
    full_key = f"{scope}:{key}"
    async with LOCKS[full_key]:  # concurrent duplicates wait here, then see the stored result
        stored = IDEMPOTENCY.get(full_key)
        if stored:
            if stored["fingerprint"] != fingerprint:
                raise HTTPException(409, "Idempotency-Key was used with a different request")
            response.status_code = stored["status"]
            response.headers["Idempotent-Replayed"] = "true"
            return stored["body"]
        body = await work()  # errors aren't stored, so the client may retry them
        IDEMPOTENCY[full_key] = {"fingerprint": fingerprint, "status": 201, "body": body}
        return body


@app.post("/payments", status_code=201)
async def create_payment(data: PaymentIn, response: Response, idempotency_key: Annotated[str | None, Header()] = None):
    async def work():
        await gateway("charge", amount_cents=data.amount_cents, customer_id=data.customer_id)
        payment_id = len(PAYMENTS) + 1
        PAYMENTS[payment_id] = {"id": payment_id, **data.model_dump(), "refunded_cents": 0, "status": "succeeded"}
        return PAYMENTS[payment_id]

    return await idempotent(idempotency_key, "payments", data.model_dump_json(), response, work)


@app.post("/payments/{payment_id}/refunds", status_code=201)
async def refund(payment_id: int, data: RefundIn, response: Response, idempotency_key: Annotated[str | None, Header()] = None):
    async def work():
        async with LOCKS[f"payment:{payment_id}"]:  # serialise refunds per payment (no over-refund race)
            payment = PAYMENTS.get(payment_id)
            if payment is None:
                raise HTTPException(404, "Payment not found")
            remaining = payment["amount_cents"] - payment["refunded_cents"]
            if data.amount_cents > remaining:
                raise HTTPException(422, f"Refund exceeds remaining amount ({remaining})")
            await gateway("refund", payment_id=payment_id, amount_cents=data.amount_cents)
            payment["refunded_cents"] += data.amount_cents
            payment["status"] = status_of(payment)
            return {"payment_id": payment_id, "amount_cents": data.amount_cents, "payment_status": payment["status"]}

    return await idempotent(idempotency_key, f"refunds:{payment_id}", data.model_dump_json(), response, work)


@app.get("/payments/{payment_id}")
async def get_payment(payment_id: int):
    if payment_id not in PAYMENTS:
        raise HTTPException(404, "Payment not found")
    return PAYMENTS[payment_id]
