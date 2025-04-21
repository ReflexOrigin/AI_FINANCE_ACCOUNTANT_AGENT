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
import re
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

IMPORTANT: Respond with a VALID JSON object only. Do not include any markdown formatting, 
explanations, or code blocks. Just return the raw JSON.

Your JSON response must include these exact keys:
1. "intent": The primary intent category
2. "subintent": The specific subintent
3. "entities": Key-value pairs of extracted entities
4. "confidence": Your confidence score (0.0-1.0)

Use the following finance intent taxonomy:
{intent_taxonomy}

Example:
User: "What's our current cash position as of today?"
Your response should be exactly:
{{
  "intent": "cash_management",
  "subintent": "cash_position",
  "entities": {{
    "date": "today",
    "type": "current"
  }},
  "confidence": 0.95
}}
"""


def extract_json_from_text(text: str) -> str:
    """
    Extract JSON from text, handling markdown code blocks and other formatting.
    
    Args:
        text: The text containing JSON
        
    Returns:
        Extracted JSON string
    """
    logger.debug(f"Attempting to extract JSON from: {text}")
    
    # First, try to find JSON in markdown code blocks
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    code_blocks = re.findall(code_block_pattern, text)
    
    if code_blocks:
        return code_blocks[0].strip()
    
    # If no code blocks, try to find JSON between curly braces
    # This regex finds the outermost JSON object
    json_pattern = r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}"
    json_matches = re.findall(json_pattern, text)
    
    if json_matches:
        return json_matches[0].strip()
    
    # If all else fails, return the original text
    return text.strip()


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
            max_new_tokens=1024, # Ensure we get a complete response
        )

        logger.debug(f"Raw LLM response: {response}")
        
        # Extract JSON from response
        json_str = extract_json_from_text(response)
        logger.debug(f"Extracted JSON string: {json_str}")
        
        # Parse the JSON response
        try:
            intent_data = json.loads(json_str)
            
            # Validate and ensure required fields
            for field in ("intent", "subintent", "entities", "confidence"):
                if field not in intent_data:
                    if field == "entities":
                        intent_data[field] = {}
                    elif field == "confidence":
                        intent_data[field] = 0.5
                    else:
                        intent_data[field] = "unknown"

            logger.info(
                f"Recognized intent: {intent_data['intent']}/{intent_data['subintent']} "
                f"(confidence: {intent_data['confidence']:.2f})"
            )
            return intent_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent JSON: {e}, extracted JSON: {json_str}")
            return {
                "intent": "unknown",
                "subintent": "general_query",
                "entities": {"error_message": f"JSON parse error: {str(e)}"},
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