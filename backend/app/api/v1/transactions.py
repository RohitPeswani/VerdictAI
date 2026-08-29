"""
VerdictAI Transaction Lookup Endpoints
Author: Darshan Prajapati (Backend Engineer - Reasoning & APIs)
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.app.core.db import db_manager

router = APIRouter(prefix="/transactions", tags=["Transactions"])


class TransactionDTO(BaseModel):
    id: str
    user_id: str
    merchant_id: str
    merchant_name: str
    amount: float
    currency: str = "USD"
    cardholder_name: str
    payment_method: str
    transaction_timestamp: datetime
    is_disputed: bool = False


# Initial mock dataset of cardholder transactions for seamless mobile/web integration
SEED_TRANSACTIONS = [
    {
        "id": "txn_apple_1099",
        "user_id": "usr_alice_01",
        "merchant_id": "m_apple_001",
        "merchant_name": "Apple Store Online",
        "amount": 1299.00,
        "currency": "USD",
        "cardholder_name": "Alice Smith",
        "payment_method": "VISA_CREDIT_8841",
        "transaction_timestamp": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
        "is_disputed": False
    },
    {
        "id": "txn_starbucks_15",
        "user_id": "usr_alice_01",
        "merchant_id": "m_starbucks_002",
        "merchant_name": "Starbucks Coffee",
        "amount": 15.75,
        "currency": "USD",
        "cardholder_name": "Alice Smith",
        "payment_method": "VISA_CREDIT_8841",
        "transaction_timestamp": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "is_disputed": False
    },
    {
        "id": "txn_uber_42",
        "user_id": "usr_alice_01",
        "merchant_id": "m_uber_003",
        "merchant_name": "Uber Technologies",
        "amount": 42.20,
        "currency": "USD",
        "cardholder_name": "Alice Smith",
        "payment_method": "VISA_CREDIT_8841",
        "transaction_timestamp": (datetime.now(timezone.utc) - timedelta(days=8)).isoformat(),
        "is_disputed": False
    },
    {
        "id": "txn_amazon_124",
        "user_id": "usr_bob_02",
        "merchant_id": "m_amazon_004",
        "merchant_name": "Amazon.com",
        "amount": 124.50,
        "currency": "USD",
        "cardholder_name": "Bob Jones",
        "payment_method": "MASTERCARD_5512",
        "transaction_timestamp": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
        "is_disputed": False
    }
]

def ensure_seed_transactions():
    """Ensure mock transactions exist in in-memory storage."""
    for txn in SEED_TRANSACTIONS:
        if not db_manager.get_pg_record("transactions", txn["id"]):
            db_manager.insert_pg_record("transactions", txn["id"], txn.copy())


# Initial population
ensure_seed_transactions()


@router.get("/cardholder/{cardholder_id}", response_model=List[TransactionDTO])
async def get_cardholder_transactions(cardholder_id: str):
    """
    Fetch all cardholder transactions eligible for dispute challenge (SRS FR-06).
    """
    ensure_seed_transactions()
    matching_txns = []
    for txn_id, txn in db_manager.pg_tables.get("transactions", {}).items():
        if txn.get("user_id") == cardholder_id:
            matching_txns.append(TransactionDTO(**txn))
    return matching_txns


@router.get("/{transaction_id}", response_model=TransactionDTO)
async def get_transaction_by_id(transaction_id: str):
    """
    Fetch a single transaction record by its unique ID.
    """
    ensure_seed_transactions()
    txn = db_manager.get_pg_record("transactions", transaction_id)
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found."
        )
    return TransactionDTO(**txn)
