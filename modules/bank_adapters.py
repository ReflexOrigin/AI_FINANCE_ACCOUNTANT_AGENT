"""
Banking Adapters Module for Finance Accountant Agent

This module provides interfaces to banking APIs for real-time financial data.
It includes both real banking API adapters and a dummy implementation for
development and testing.

Features:
- Abstract Banking API interface
- Real banking API implementation (with OAuth)
- Dummy banking API for testing
- Async operations for all banking functions
- Rate limiting and caching
- Error handling with graceful fallbacks

Dependencies:
- aiohttp: For async HTTP requests
- config.settings: For API credentials and configuration
"""

import asyncio
import datetime
import json
import logging
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

import aiohttp

from config.settings import settings

logger = logging.getLogger(__name__)


class BankingAdapter(ABC):
    """Abstract base class for banking API adapters."""

    @abstractmethod
    async def get_account_balance(self, account_id: str) -> Dict:
        """Get the current balance for an account."""
        pass

    @abstractmethod
    async def get_transaction_history(
        self, account_id: str, start_date: str, end_date: Optional[str] = None
    ) -> List[Dict]:
        """Get transaction history for an account within date range."""
        pass

    @abstractmethod
    async def initiate_payment(
        self, from_account: str, to_account: str, amount: float, currency: str, description: str
    ) -> Dict:
        """Initiate a payment from one account to another."""
        pass

    @abstractmethod
    async def get_fx_rates(self, base_currency: str, target_currencies: List[str]) -> Dict:
        """Get foreign exchange rates."""
        pass

    @abstractmethod
    async def get_credit_facilities(self) -> List[Dict]:
        """Get information about available credit facilities."""
        pass


class RealBankingAdapter(BankingAdapter):
    """
    Real banking API adapter implementation.
    Connects to actual banking APIs using OAuth authentication.
    """

    def __init__(self):
        self.api_url = settings.BANKING_API_URL
        self.api_key = settings.BANKING_API_KEY
        self.api_secret = settings.BANKING_API_SECRET
        self.token = None
        self.token_expiry = None

    async def _get_auth_token(self) -> str:
        """Get or refresh the authentication token."""
        if self.token and self.token_expiry and self.token_expiry > datetime.datetime.now():
            return self.token

        async with aiohttp.ClientSession() as session:
            auth_url = f"{self.api_url}/auth/token"
            payload = {
                "client_id": self.api_key,
                "client_secret": self.api_secret,
                "grant_type": "client_credentials",
            }
            async with session.post(auth_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.token = data["access_token"]
                    expires_in = data.get("expires_in", 3600)
                    self.token_expiry = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
                    return self.token
                else:
                    error_text = await resp.text()
                    logger.error(f"Authentication failed: {resp.status} - {error_text}")
                    raise Exception(f"Banking API authentication failed: {resp.status}")

    async def _make_api_request(self, method: str, endpoint: str, **kwargs) -> Union[Dict, List]:
        """Make an authenticated request to the banking API."""
        token = await self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = f"{self.api_url}{endpoint}"

        async with aiohttp.ClientSession() as session:
            if method.lower() == "get":
                async with session.get(url, headers=headers, **kwargs) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    text = await resp.text()
                    logger.error(f"GET {endpoint} failed: {resp.status} - {text}")
                    raise Exception(f"Banking API GET failed: {resp.status}")
            elif method.lower() == "post":
                async with session.post(url, headers=headers, **kwargs) as resp:
                    if resp.status in (200, 201):
                        return await resp.json()
                    text = await resp.text()
                    logger.error(f"POST {endpoint} failed: {resp.status} - {text}")
                    raise Exception(f"Banking API POST failed: {resp.status}")
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

    async def get_account_balance(self, account_id: str) -> Dict:
        endpoint = f"/accounts/{account_id}/balance"
        return await self._make_api_request("get", endpoint)

    async def get_transaction_history(
        self, account_id: str, start_date: str, end_date: Optional[str] = None
    ) -> List[Dict]:
        endpoint = f"/accounts/{account_id}/transactions"
        params = {"startDate": start_date}
        if end_date:
            params["endDate"] = end_date
        return await self._make_api_request("get", endpoint, params=params)

    async def initiate_payment(
        self, from_account: str, to_account: str, amount: float, currency: str, description: str
    ) -> Dict:
        endpoint = "/payments"
        payload = {
            "fromAccount": from_account,
            "toAccount": to_account,
            "amount": amount,
            "currency": currency,
            "description": description,
        }
        return await self._make_api_request("post", endpoint, json=payload)

    async def get_fx_rates(self, base_currency: str, target_currencies: List[str]) -> Dict:
        endpoint = "/fx/rates"
        params = {"baseCurrency": base_currency, "targetCurrencies": ",".join(target_currencies)}
        return await self._make_api_request("get", endpoint, params=params)

    async def get_credit_facilities(self) -> List[Dict]:
        endpoint = "/credit/facilities"
        return await self._make_api_request("get", endpoint)


class DummyBankingAdapter(BankingAdapter):
    """
    Dummy banking API adapter for development and testing.
    Provides simulated responses for all banking operations.
    """

    def __init__(self):
        # Simulated account data
        self.accounts = {
            "1001": {"name": "Operating Account", "balance": 1250000.00, "currency": "USD", "type": "checking"},
            "1002": {"name": "Payroll Account",   "balance": 350000.00,  "currency": "USD", "type": "checking"},
            "1003": {"name": "Tax Reserve",       "balance": 420000.00,  "currency": "USD", "type": "savings"},
            "1004": {"name": "Euro Operations",   "balance": 275000.00,  "currency": "EUR", "type": "checking"},
        }
        # Simulated FX rates (against USD)
        self.fx_rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.78, "JPY": 150.25, "CAD": 1.36, "AUD": 1.52}
        # Simulated credit facilities
        self.credit_facilities = [
            {
                "id": "CF001",
                "type": "revolving",
                "limit": 5000000.00,
                "currency": "USD",
                "used": 1200000.00,
                "available": 3800000.00,
                "expiry_date": "2026-12-31",
                "interest_rate": "SOFR + 1.5%",
            },
            {
                "id": "CF002",
                "type": "term_loan",
                "original_amount": 2500000.00,
                "currency": "USD",
                "outstanding": 1800000.00,
                "maturity_date": "2028-06-30",
                "interest_rate": "4.25% fixed",
            },
        ]

    async def get_account_balance(self, account_id: str) -> Dict:
        await asyncio.sleep(0.5)  # simulate delay
        if account_id not in self.accounts:
            raise Exception(f"Account {account_id} not found")
        acc = self.accounts[account_id]
        return {
            "account_id": account_id,
            "balance": acc["balance"],
            "currency": acc["currency"],
            "available_balance": acc["balance"] - random.uniform(0, 10000),
            "as_of": datetime.datetime.now().isoformat(),
        }

    async def get_transaction_history(
        self, account_id: str, start_date: str, end_date: Optional[str] = None
    ) -> List[Dict]:
        await asyncio.sleep(1.0)
        if account_id not in self.accounts:
            raise Exception(f"Account {account_id} not found")
        start = datetime.datetime.fromisoformat(start_date)
        end = datetime.datetime.now() if not end_date else datetime.datetime.fromisoformat(end_date)
        transactions = []
        for _ in range(random.randint(5, 20)):
            days = random.randint(0, (end - start).days if (end - start).days > 0 else 1)
            tx_date = start + datetime.timedelta(days=days)
            amount = random.uniform(-50000, 50000)
            tx_type = "credit" if amount > 0 else "debit"
            descs = (["Customer Payment","Interest Income","Rebate","Refund","Investment Return","Asset Sale"]
                     if tx_type=="credit"
                     else ["Supplier Payment","Payroll","Rent","Utilities","Software Subscription","Insurance Premium","Tax Payment"])
            transactions.append({
                "id": f"TX{random.randint(10000,99999)}",
                "date": tx_date.isoformat(),
                "amount": abs(amount),
                "type": tx_type,
                "description": random.choice(descs),
                "currency": self.accounts[account_id]["currency"],
                "balance_after": random.uniform(100000, 2000000),
            })
        transactions.sort(key=lambda x: x["date"])
        return transactions

    async def initiate_payment(
        self, from_account: str, to_account: str, amount: float, currency: str, description: str
    ) -> Dict:
        await asyncio.sleep(1.5)
        if from_account not in self.accounts:
            raise Exception(f"Source account {from_account} not found")
        if self.accounts[from_account]["balance"] < amount:
            raise Exception(f"Insufficient funds in account {from_account}")
        payment_id = f"PAY{random.randint(100000,999999)}"
        return {
            "payment_id": payment_id,
            "status": "processed",
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "currency": currency,
            "description": description,
            "timestamp": datetime.datetime.now().isoformat(),
            "reference": f"REF{random.randint(10000,99999)}",
        }

    async def get_fx_rates(self, base_currency: str, target_currencies: List[str]) -> Dict:
        await asyncio.sleep(0.7)
        if base_currency not in self.fx_rates:
            raise Exception(f"Currency {base_currency} not supported")
        base = self.fx_rates[base_currency]
        rates = {
            cur: (self.fx_rates[cur] / base) * random.uniform(0.99,1.01)
            if cur in self.fx_rates else None
            for cur in target_currencies
        }
        return {"base_currency": base_currency, "timestamp": datetime.datetime.now().isoformat(), "rates": rates}

    async def get_credit_facilities(self) -> List[Dict]:
        await asyncio.sleep(0.8)
        return list(self.credit_facilities)


def get_banking_adapter() -> BankingAdapter:
    """
    Factory to select real or dummy banking adapter based on config.
    """
    if settings.BANKING_API_ENABLED and not settings.USE_DUMMY_BANKING_API:
        logger.info("Using real banking API adapter")
        return RealBankingAdapter()
    else:
        logger.info("Using dummy banking API adapter")
        return DummyBankingAdapter()
