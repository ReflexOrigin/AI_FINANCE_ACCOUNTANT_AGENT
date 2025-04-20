"""
Intent Recognition Module for Finance Accountant Agent

This module processes user input text (from voice transcription or direct text input)
and identifies the user's intent along with relevant entities. It determines which
financial operation the user is trying to perform and extracts key parameters.

Features:
- Intent classification using LLM
- Entity extraction for financial data
- Context-aware understanding
- Finance-specific intent taxonomy
- Confidence scoring

Dependencies:
- llm_module: For LLM-based intent recognition
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Union

from modules.llm_module import generate_text
from config.settings import settings

logger = logging.getLogger(__name__)

# Finance-specific intent taxonomy
FINANCE_INTENTS = {
    "investor_relations": [
        "shareholder_inquiry",
        "dividend_info",
        "earnings_report",
        "investor_presentation",
        "stock_performance",
    ],
    "cash_management": [
        "cash_position",
        "cash_flow_forecast",
        "liquidity_analysis",
        "working_capital",
        "cash_pooling",
    ],
    "risk_management": [
        "fx_risk",
        "interest_rate_risk",
        "commodity_risk",
        "credit_risk",
        "liquidity_risk",
    ],
    "investment_management": [
        "investment_performance",
        "portfolio_allocation",
        "investment_strategy",
        "new_investment",
        "divest",
    ],
    "fin_inst_relations": [
        "bank_relations",
        "line_of_credit",
        "account_services",
        "fee_negotiation",
        "bank_covenant",
    ],
    "external_financing": [
        "debt_issuance",
        "loan_terms",
        "refinancing",
        "debt_maturity",
        "interest_payment",
    ],
    "accounting": [
        "general_ledger",
        "journal_entry",
        "account_reconciliation",
        "financial_statement",
        "accounting_policy",
    ],
    "mis": [
        "management_report",
        "variance_analysis",
        "kpi_dashboard",
        "business_metrics",
        "executive_summary",
    ],
    "ar_aging": [
        "customer_balance",
        "overdue_accounts",
        "collection_strategy",
        "credit_limit",
        "bad_debt",
    ],
    "ap_aging": [
        "vendor_payment",
        "payment_schedule",
        "early_payment_discount",
        "payment_terms_negotiation",
        "vendor_balance",
    ],
    "tax_reporting": [
        "tax_provision",
        "tax_filing",
        "tax_planning",
        "tax_jurisdiction",
        "tax_credit",
    ],
    "financial_planning": [
        "budget_preparation",
        "forecast_update",
        "scenario_analysis",
        "capital_planning",
        "financial_target",
    ],
}

# System prompt for intent recognition
INTENT_RECOGNITION_PROMPT = """
You are a financial intent recognition system. Your task is to analyze user queries
and determine the specific finance-related intent and extract relevant entities.

Respond with a JSON object that includes:
1. "intent": The primary intent category
2. "subintent": The specific subintent
3. "entities": Key-value pairs of extracted entities
4. "confidence": Your confidence score (0.0-1.0)

Use the following finance intent taxonomy:
{intent_taxonomy}

Example:
User: "What's our current cash position as of today?"
Response:
{
  "intent": "cash_management",
  "subintent": "cash_position",
  "entities": {
    "date": "today",
    "type": "current"
  },
  "confidence": 0.95
}
"""


async def recognize_intent(
    text: str, context: Optional[Dict] = None
) -> Dict:
    """
    Recognize financial intent from user text input.

    Args:
        text: User input text
        context: Optional context information for better understanding

    Returns:
        Dictionary containing intent, subintent, entities, and confidence
    """
    try:
        # Format the system prompt with intent taxonomy
        formatted_taxonomy = json.dumps(FINANCE_INTENTS, indent=2)
        system_prompt = INTENT_RECOGNITION_PROMPT.format(
            intent_taxonomy=formatted_taxonomy
        )

        # Include context if provided
        user_prompt = text
        if context:
            context_str = json.dumps(context)
            user_prompt = f"{text}\n\nContext: {context_str}"

        # Generate intent recognition using LLM
        response = await generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.1,  # Low temperature for consistency
        )

        # Parse the JSON response
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                intent_data = json.loads(json_str)
            else:
                intent_data = json.loads(response)

            # Ensure required fields
            for field in ("intent", "subintent", "entities", "confidence"):
                if field not in intent_data:
                    intent_data.setdefault("entities", {})
                    intent_data.setdefault("confidence", 0.5)
                    intent_data.setdefault("intent", "unknown")
                    intent_data.setdefault("subintent", "unknown")

            logger.info(
                f"Recognized intent: {intent_data['intent']}/{intent_data['subintent']} "
                f"(confidence: {intent_data['confidence']:.2f})"
            )
            return intent_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent JSON: {e}, response: {response}")
            return {
                "intent": "unknown",
                "subintent": "general_query",
                "entities": {},
                "confidence": 0.1,
                "raw_response": response,
            }

    except Exception as e:
        logger.error(f"Error in intent recognition: {e}")
        return {
            "intent": "error",
            "subintent": "recognition_failed",
            "entities": {"error_message": str(e)},
            "confidence": 0.0,
        }
