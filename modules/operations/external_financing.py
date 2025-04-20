"""
External Financing Operations Module for Finance Accountant Agent

This module handles operations related to external financing, including debt
issuance, loan terms analysis, refinancing, debt maturity management, and interest
payment tracking.

Features:
- Debt issuance analysis and recommendations
- Loan terms evaluation and comparison
- Refinancing opportunity assessment
- Debt maturity schedule management
- Interest payment tracking and forecasting

Dependencies:
- bank_adapters: For financial data access
- rag_module: For retrieving relevant financing documents
- llm_module: For analysis and recommendations
"""

import asyncio
import datetime
import logging
import random
from typing import Dict, List, Optional

from modules.bank_adapters import get_banking_adapter
from modules.llm_module import generate_text
from modules.rag_module import rag_module

from config.settings import settings

logger = logging.getLogger(__name__)


async def handle_debt_issuance(entities: Dict) -> Dict:
    """
    Analyze debt issuance options and provide recommendations.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with debt issuance analysis
    """
    # Extract relevant entities
    amount = entities.get("amount", 10000000)
    currency = entities.get("currency", "USD")
    term = entities.get("term", "5y")
    purpose = entities.get("purpose", "general")

    # Get RAG context for debt issuance
    query = f"debt issuance {currency} {term} {purpose}"
    context = await rag_module.generate_context(
        query, filter_criteria={"category": "external_financing"}
    )

    # Sample market data (would come from financial data provider in real implementation)
    market_rates = {
        "USD": {
            "risk_free": {
                "1y": 3.85,
                "2y": 4.10,
                "3y": 4.20,
                "5y": 4.25,
                "7y": 4.30,
                "10y": 4.35,
                "30y": 4.45,
            },
            "corporate": {
                "AA": {
                    "1y": 4.10,
                    "2y": 4.40,
                    "3y": 4.55,
                    "5y": 4.70,
                    "7y": 4.80,
                    "10y": 4.90,
                    "30y": 5.10,
                },
                "A": {
                    "1y": 4.35,
                    "2y": 4.70,
                    "3y": 4.90,
                    "5y": 5.10,
                    "7y": 5.25,
                    "10y": 5.40,
                    "30y": 5.65,
                },
                "BBB": {
                    "1y": 4.85,
                    "2y": 5.20,
                    "3y": 5.40,
                    "5y": 5.65,
                    "7y": 5.85,
                    "10y": 6.05,
                    "30y": 6.45,
                },
            }
        },
        "EUR": {
            "risk_free": {
                "1y": 2.95,
                "2y": 3.05,
                "3y": 3.10,
                "5y": 3.15,
                "7y": 3.20,
                "10y": 3.30,
                "30y": 3.45,
            },
            "corporate": {
                "AA": {
                    "1y": 3.25,
                    "2y": 3.40,
                    "3y": 3.50,
                    "5y": 3.60,
                    "7y": 3.70,
                    "10y": 3.85,
                    "30y": 4.10,
                },
                "A": {
                    "1y": 3.50,
                    "2y": 3.70,
                    "3y": 3.85,
                    "5y": 4.00,
                    "7y": 4.15,
                    "10y": 4.35,
                    "30y": 4.70,
                },
                "BBB": {
                    "1y": 4.00,
                    "2y": 4.25,
                    "3y": 4.45,
                    "5y": 4.70,
                    "7y": 4.90,
                    "10y": 5.15,
                    "30y": 5.60,
                },
            }
        }
    }

    # Company credit profile (would come from financial system in real implementation)
    company_credit = {
        "rating": "BBB+",
        "rating_outlook": "stable",
        "debt_to_ebitda": 2.8,
        "interest_coverage": 4.2,
        "existing_debt": 85000000,
        "existing_debt_currency": "USD",
    }

    # Map term to years for lookup
    term_mapping = {
        "1y": "1y", "2y": "2y", "3y": "3y", "5y": "5y",
        "7y": "7y", "10y": "10y", "30y": "30y",
        "short": "3y", "medium": "5y", "long": "10y"
    }

    mapped_term = term_mapping.get(term, "5y")

    # Determine credit rating band (simplified)
    if company_credit["rating"] in ["AAA", "AA+", "AA", "AA-"]:
        rating_band = "AA"
    elif company_credit["rating"] in ["A+", "A", "A-"]:
        rating_band = "A"
    else:
        rating_band = "BBB"

    # Check if we have market data for the requested currency
    if currency not in market_rates:
        return {
            "error": f"Market data not available for {currency}",
            "available_currencies": list(market_rates.keys())
        }

    # Get applicable rates
    try:
        risk_free_rate = market_rates[currency]["risk_free"][mapped_term]
        corporate_rate = market_rates[currency]["corporate"][rating_band][mapped_term]
        spread = corporate_rate - risk_free_rate
    except KeyError:
        return {
            "error": f"Rate data not available for {term} term",
            "available_terms": list(term_mapping.keys())
        }

    # Calculate estimated all-in rate
    all_in_rate = corporate_rate + 0.25  # Adding 25bps for new issuance premium

    # Calculate annual interest expense
    annual_interest = amount * (all_in_rate / 100)

    # Generate debt issuance strategy using LLM
    system_prompt = f"""
    You are a debt capital markets advisor. Provide a debt issuance strategy for a {currency} {amount:,} financing with these parameters:

    Term: {term}
    Purpose: {purpose}

    Current Market Conditions:
    - Risk-Free Rate ({mapped_term}): {risk_free_rate:.2f}%
    - Corporate {rating_band} Rate ({mapped_term}): {corporate_rate:.2f}%
    - Credit Spread: {spread:.2f}%
    - Estimated All-in Rate: {all_in_rate:.2f}%

    Company Credit Profile:
    - Credit Rating: {company_credit['rating']} ({company_credit['rating_outlook']})
    - Debt/EBITDA: {company_credit['debt_to_ebitda']}x
    - Interest Coverage: {company_credit['interest_coverage']}x
    - Existing Debt: {company_credit['existing_debt_currency']} {company_credit['existing_debt']:,}

    Provide a comprehensive debt issuance strategy including:
    1. Recommended debt structure (public bonds vs. private placement vs. bank loan)
    2. Pricing expectations and timing considerations
    3. Key terms to negotiate
    4. Risk factors to consider
    5. Process timeline and key milestones

    Be specific and actionable in your recommendations, considering the company's credit profile and current market conditions.
    """

    if context:
        system_prompt += f"\n\nAdditional context for your analysis:\n{context}"

    issuance_strategy = await generate_text(
        prompt=f"Develop debt issuance strategy for {currency} {amount:,} {term} {purpose}",
        system_prompt=system_prompt,
        max_new_tokens=1024,
    )

    # Return results
    return {
        "amount": amount,
        "currency": currency,
        "term": term,
        "purpose": purpose,
        "market_conditions": {
            "risk_free_rate": risk_free_rate,
            "corporate_rate": corporate_rate,
            "credit_spread": spread,
            "estimated_all_in_rate": all_in_rate,
        },
        "company_credit": company_credit,
        "financing_impact": {
            "annual_interest": annual_interest,
            "new_total_debt": company_credit["existing_debt"] + amount if company_credit["existing_debt_currency"] == currency else None,
        },
        "formatted_response": issuance_strategy,
    }


async def handle_loan_terms(entities: Dict) -> Dict:
    """
    Analyze and compare loan terms.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with loan terms analysis
    """
    # Extract relevant entities
    loan_id = entities.get("loan_id")
    compare = entities.get("compare", False)

    # Sample loan data (would come from debt management system in real implementation)
    loans = {
        "L001": {
            "name": "Term Loan A",
            "type": "term_loan",
            "lender": "Global Trust Bank",
            "bank_id": "BNK001",
            "original_amount": 25000000,
            "outstanding_amount": 20000000,
            "currency": "USD",
            "start_date": "2022-06-15",
            "maturity_date": "2027-06-15",
            "term": "5 years",
            "interest_rate_type": "floating",
            "benchmark": "SOFR",
            "spread": 175,  # basis points
            "current_rate": 5.5,  # percent
            "payment_frequency": "quarterly",
            "principal_payment": "amortizing",
            "amortization_schedule": "5 years",
            "prepayment_penalty": "1% in year 1, 0.5% in year 2, none thereafter",
            "financial_covenants": ["Debt/EBITDA <= 3.5x", "Interest Coverage >= 3.0x"],
            "security": "unsecured",
            "key_terms": [
                "Change of control provision",
                "Material adverse change clause",
                "Cross-default provision",
                "Restriction on additional debt"
            ],
            "fees": {
                "upfront_fee": 0.75,  # percent
                "commitment_fee": 0.375,  # percent
                "agency_fee": 25000,  # USD per year
            },
        },
        "L002": {
            "name": "Revolving Credit Facility",
            "type": "revolver",
            "lender": "Global Trust Bank",
            "bank_id": "BNK001",
            "original_amount": 15000000,
            "outstanding_amount": 8000000,
            "currency": "USD",
            "start_date": "2022-06-15",
            "maturity_date": "2027-06-15",
            "term": "5 years",
            "interest_rate_type": "floating",
            "benchmark": "SOFR",
            "spread": 150,  # basis points
            "current_rate": 5.25,  # percent
            "payment_frequency": "quarterly",
            "principal_payment": "bullet",
            "prepayment_penalty": "none",
            "financial_covenants": ["Debt/EBITDA <= 3.5x", "Interest Coverage >= 3.0x"],
            "security": "unsecured",
            "key_terms": [
                "Change of control provision",
                "Material adverse change clause",
                "Cross-default provision",
                "Restriction on additional debt"
            ],
            "fees": {
                "upfront_fee": 0.5,  # percent
                "commitment_fee": 0.375,  # percent
                "agency_fee": 25000,  # USD per year
            },
        },
        "L003": {
            "name": "Term Loan B",
            "type": "term_loan",
            "lender": "Continental Financial",
            "bank_id": "BNK002",
            "original_amount": 50000000,
            "outstanding_amount": 48750000,
            "currency": "USD",
            "start_date": "2023-03-10",
            "maturity_date": "2030-03-10",
            "term": "7 years",
            "interest_rate_type": "floating",
            "benchmark": "SOFR",
            "spread": 225,  # basis points
            "current_rate": 6.0,  # percent
            "payment_frequency": "quarterly",
            "principal_payment": "1% annual amortization, remainder bullet",
            "amortization_schedule": "1% per year, 94% bullet",
            "prepayment_penalty": "2% in year 1, 1% in year 2, none thereafter",
            "financial_covenants": ["Debt/EBITDA <= 4.0x"],
            "security": "secured",
            "collateral": "All assets",
            "key_terms": [
                "Change of control provision",
                "Material adverse change clause",
                "Cross-default provision",
                "Restriction on additional debt",
                "Excess cash flow sweep"
            ],
            "fees": {
                "upfront_fee": 1.5,  # percent
                "agency_fee": 35000,  # USD per year
            },
        },
        "L004": {
            "name": "Euro Term Loan",
            "type": "term_loan",
            "lender": "European Credit Bank",
            "bank_id": "BNK003",
            "original_amount": 20000000,
            "outstanding_amount": 20000000,
            "currency": "EUR",
            "start_date": "2023-09-15",
            "maturity_date": "2028-09-15",
            "term": "5 years",
            "interest_rate_type": "floating",
            "benchmark": "EURIBOR",
            "spread": 200,  # basis points
            "current_rate": 4.5,  # percent
            "payment_frequency": "quarterly",
            "principal_payment": "bullet",
            "prepayment_penalty": "1% in year 1, none thereafter",
            "financial_covenants": ["Debt/EBITDA <= 3.75x", "Interest Coverage >= 3.0x"],
            "security": "unsecured",
            "key_terms": [
                "Change of control provision",
                "Material adverse change clause",
                "Cross-default provision"
            ],
            "fees": {
                "upfront_fee": 0.75,  # percent
                "commitment_fee": 0.35,  # percent
                "agency_fee": 25000,  # EUR per year
            },
        },
    }

    # If specific loan requested
    if loan_id:
        if loan_id not in loans:
            return {
                "error": f"Loan {loan_id} not found",
                "available_loans": list(loans.keys())
            }

        loan = loans[loan_id]

        # Compare with other loans if requested
        if compare:
            # Find similar loans for comparison
            same_type_loans = [l for l_id, l in loans.items() if l["type"] == loan["type"] and l_id != loan_id]
            same_currency_loans = [l for l_id, l in loans.items() if l["currency"] == loan["currency"] and l_id != loan_id]

            # Pick the most relevant loan for comparison
            comparison_loan = None
            comparison_loan_id = None

            # Prefer same type and currency
            for l_id, l in loans.items():
                if l_id != loan_id and l["type"] == loan["type"] and l["currency"] == loan["currency"]:
                    comparison_loan = l
                    comparison_loan_id = l_id
                    break

            # If no exact match, prefer same type
            if comparison_loan is None and same_type_loans:
                comparison_loan = same_type_loans[0]
                comparison_loan_id = next(l_id for l_id, l in loans.items() if l is comparison_loan)

            # If still no match, prefer same currency
            if comparison_loan is None and same_currency_loans:
                comparison_loan = same_currency_loans[0]
                comparison_loan_id = next(l_id for l_id, l in loans.items() if l is comparison_loan)

            if comparison_loan:
                # Prepare comparison analysis
                comparison = {
                    "loan_id": loan_id,
                    "comparison_loan_id": comparison_loan_id,
                    "interest_rate": {
                        "primary": loan["current_rate"],
                        "comparison": comparison_loan["current_rate"],
                        "difference": loan["current_rate"] - comparison_loan["current_rate"],
                    },
                    "spread": {
                        "primary": loan["spread"],
                        "comparison": comparison_loan["spread"],
                        "difference": loan["spread"] - comparison_loan["spread"],
                    },
                    "term": {
                        "primary": loan["term"],
                        "comparison": comparison_loan["term"],
                    },
                    "amortization": {
                        "primary": loan.get("principal_payment", "N/A"),
                        "comparison": comparison_loan.get("principal_payment", "N/A"),
                    },
                    "prepayment_penalty": {
                        "primary": loan.get("prepayment_penalty", "None"),
                        "comparison": comparison_loan.get("prepayment_penalty", "None"),
                    },
                    "covenants": {
                        "primary": loan.get("financial_covenants", []),
                        "comparison": comparison_loan.get("financial_covenants", []),
                    },
                }

                # Get RAG context for loan terms benchmarking
                query = f"loan terms benchmark {loan['type']} {loan['currency']}"
                context = await rag_module.generate_context(
                    query, filter_criteria={"category": "external_financing"}
                )

                # Generate loan terms comparison analysis using LLM
                system_prompt = f"""
                You are a debt financing analyst. Provide a comparison analysis between these two loans:

                Loan 1: {loan['name']} ({loan_id})
                - Type: {loan['type']}
                - Amount: {loan['currency']} {loan['original_amount']:,}
                - Term: {loan['term']}
                - Rate: {loan['current_rate']}% ({loan['benchmark']} + {loan['spread']} bps)
                - Amortization: {loan.get('principal_payment', 'N/A')}
                - Prepayment: {loan.get('prepayment_penalty', 'None')}
                - Security: {loan['security']}
                - Covenants: {', '.join(loan.get('financial_covenants', ['None']))}
                - Upfront Fee: {loan['fees'].get('upfront_fee', 0)}%

                Loan 2: {comparison_loan['name']} ({comparison_loan_id})
                - Type: {comparison_loan['type']}
                - Amount: {comparison_loan['currency']} {comparison_loan['original_amount']:,}
                - Term: {comparison_loan['term']}
                - Rate: {comparison_loan['current_rate']}% ({comparison_loan['benchmark']} + {comparison_loan['spread']} bps)
                - Amortization: {comparison_loan.get('principal_payment', 'N/A')}
                - Prepayment: {comparison_loan.get('prepayment_penalty', 'None')}
                - Security: {comparison_loan['security']}
                - Covenants: {', '.join(comparison_loan.get('financial_covenants', ['None']))}
                - Upfront Fee: {comparison_loan['fees'].get('upfront_fee', 0)}%

                Provide a detailed comparison that includes:
                1. Key differences in pricing and terms
                2. Relative advantages and disadvantages of each loan
                3. Recommendations for potential refinancing or renegotiation
                4. Market context for the terms of each loan

                Focus on practical insights that could help optimize the debt structure.
                """

                if context:
                    system_prompt += f"\n\nAdditional market context for your analysis:\n{context}"

                comparison_analysis = await generate_text(
                    prompt=f"Compare loan terms between {loan['name']} and {comparison_loan['name']}",
                    system_prompt=system_prompt,
                )

                return {
                    "loan_id": loan_id,
                    "loan_details": loan,
                    "comparison_loan_id": comparison_loan_id,
                    "comparison_loan_details": comparison_loan,
                    "comparison": comparison,
                    "formatted_response": comparison_analysis,
                }

        # Return single loan details
        return {
            "loan_id": loan_id,
            "name": loan["name"],
            "type": loan["type"],
            "lender": loan["lender"],
            "bank_id": loan["bank_id"],
            "original_amount": loan["original_amount"],
            "outstanding_amount": loan["outstanding_amount"],
            "currency": loan["currency"],
            "start_date": loan["start_date"],
            "maturity_date": loan["maturity_date"],
            "term": loan["term"],
            "interest_rate": {
                "type": loan["interest_rate_type"],
                "benchmark": loan["benchmark"],
                "spread": loan["spread"],
                "current_rate": loan["current_rate"],
            },
            "payment_terms": {
                "frequency": loan["payment_frequency"],
                "principal_payment": loan["principal_payment"],
                "amortization_schedule": loan.get("amortization_schedule"),
                "prepayment_penalty": loan.get("prepayment_penalty"),
            },
            "covenants": loan.get("financial_covenants", []),
            "security": loan["security"],
            "collateral": loan.get("collateral"),
            "key_terms": loan.get("key_terms", []),
            "fees": loan["fees"],
            "message": (
                f"Loan Terms: {loan['name']} ({loan_id})\n"
                f"Type: {loan['type']}\n"
                f"Lender: {loan['lender']} ({loan['bank_id']})\n"
                f"Amount: {loan['currency']} {loan['original_amount']:,} (Outstanding: {loan['currency']} {loan['outstanding_amount']:,})\n"
                f"Term: {loan['term']} ({loan['start_date']} to {loan['maturity_date']})\n"
                f"Interest: {loan['current_rate']}% ({loan['interest_rate_type']}: {loan['benchmark']} + {loan['spread']} bps)\n"
                f"Payment: {loan['payment_frequency']} ({loan['principal_payment']})\n"
                f"Security: {loan['security']}\n"
                f"Covenants: {', '.join(loan.get('financial_covenants', ['None']))}"
            ),
        }

    # Return summary of all loans
    else:
        total_debt = {}

        for loan in loans.values():
            currency = loan["currency"]
            if currency not in total_debt:
                total_debt[currency] = 0
            total_debt[currency] += loan["outstanding_amount"]

        weighted_rate = 0
        total_usd_equivalent = 0

        # Sample exchange rates (would come from banking API in real implementation)
        fx_rates = {"USD": 1.0, "EUR": 1.09}  # USD per unit of currency

        for loan in loans.values():
            currency = loan["currency"]
            usd_amount = loan["outstanding_amount"] * fx_rates[currency]
            weighted_rate += loan["current_rate"] * (usd_amount / (total_debt["USD"] + total_debt.get("EUR", 0) * fx_rates["EUR"]))
            total_usd_equivalent += usd_amount

        return {
            "total_loans": len(loans),
            "total_debt": total_debt,
            "total_usd_equivalent": total_usd_equivalent,
            "weighted_average_rate": weighted_rate,
            "loans_summary": [
                {
                    "loan_id": loan_id,
                    "name": loan["name"],
                    "type": loan["type"],
                    "lender": loan["lender"],
                    "currency": loan["currency"],
                    "outstanding_amount": loan["outstanding_amount"],
                    "maturity_date": loan["maturity_date"],
                    "current_rate": loan["current_rate"],
                } for loan_id, loan in loans.items()
            ],
            "message": (
                f"Loan Summary:\n"
                f"Total Loans: {len(loans)}\n"
                f"Total Debt: " + ", ".join([f"{currency} {amount:,}" for currency, amount in total_debt.items()]) + "\n"
                f"USD Equivalent: ${total_usd_equivalent:,.2f}\n"
                f"Weighted Average Rate: {weighted_rate:.2f}%\n\n"
                "Loans:\n" +
                "\n".join([
                    f"- {loan['name']} ({loan_id}): {loan['currency']} {loan['outstanding_amount']:,}, "
                    f"{loan['current_rate']}%, matures {loan['maturity_date']}"
                    for loan_id, loan in loans.items()
                ])
            ),
        }


async def handle_refinancing(entities: Dict) -> Dict:
    """
    Analyze refinancing opportunities and provide recommendations.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with refinancing analysis
    """
    # Extract relevant entities
    loan_id = entities.get("loan_id")
    target_rate = entities.get("target_rate")

    # Sample loan data (would come from debt management system in real implementation)
    loans = {
        "L001": {
            "name": "Term Loan A",
            "type": "term_loan",
            "lender": "Global Trust Bank",
            "bank_id": "BNK001",
            "original_amount": 25000000,
            "outstanding_amount": 20000000,
            "currency": "USD",
            "start_date": "2022-06-15",
            "maturity_date": "2027-06-15",
            "term": "5 years",
            "interest_rate_type": "floating",
            "benchmark": "SOFR",
            "spread": 175,  # basis points
            "current_rate": 5.5,  # percent
            "payment_frequency": "quarterly",
            "principal_payment": "amortizing",
            "amortization_schedule": "5 years",
            "prepayment_penalty": "1% in year 1, 0.5% in year 2, none thereafter",
            "financial_covenants": ["Debt/EBITDA <= 3.5x", "Interest Coverage >= 3.0x"],
            "security": "unsecured",
            "refinancing_costs": {
                "prepayment_fee": 0,  # beyond penalty period
                "upfront_fee_estimate": 0.75,  # percent
                "legal_fees_estimate": 150000,  # USD
            },
        },
        "L002": {
            "name": "Revolving Credit Facility",
            "type": "revolver",
            "lender": "Global Trust Bank",
            "bank_id": "BNK001",
            "original_amount": 15000000,
            "outstanding_amount": 8000000,
            "currency": "USD",
            "start_date": "2022-06-15",
            "maturity_date": "2027-06-15",
            "term": "5 years",
            "interest_rate_type": "floating",
            "benchmark": "SOFR",
            "spread": 150,  # basis points
            "current_rate": 5.25,  # percent
            "payment_frequency": "quarterly",
            "principal_payment": "bullet",
            "prepayment_penalty": "none",
            "financial_covenants": ["Debt/EBITDA <= 3.5x", "Interest Coverage >= 3.0x"],
            "security": "unsecured",
            "refinancing_costs": {
                "prepayment_fee": 0,  # no penalty
                "upfront_fee_estimate": 0.5,  # percent
                "legal_fees_estimate": 100000,  # USD
            },
        },
        "L003": {
            "name": "Term Loan B",
            "type": "term_loan",
            "lender": "Continental Financial",
            "bank_id": "BNK002",
            "original_amount": 50000000,
            "outstanding_amount": 48750000,
            "currency": "USD",
            "start_date": "2023-03-10",
            "maturity_date": "2030-03-10",
            "term": "7 years",
            "interest_rate_type": "floating",
            "benchmark": "SOFR",
            "spread": 225,  # basis points
            "current_rate": 6.0,  # percent
            "payment_frequency": "quarterly",
            "principal_payment": "1% annual amortization, remainder bullet",
            "amortization_schedule": "1% per year, 94% bullet",
            "prepayment_penalty": "2% in year 1, 1% in year 2, none thereafter",
            "financial_covenants": ["Debt/EBITDA <= 4.0x"],
            "security": "secured",
            "collateral": "All assets",
            "refinancing_costs": {
                "prepayment_fee": 0.01 * 48750000,  # 1% penalty still applies
                "upfront_fee_estimate": 1.5,  # percent
                "legal_fees_estimate": 250000,  # USD
            },
        },
        "L004": {
            "name": "Euro Term Loan",
            "type": "term_loan",
            "lender": "European Credit Bank",
            "bank_id": "BNK003",
            "original_amount": 20000000,
            "outstanding_amount": 20000000,
            "currency": "EUR",
            "start_date": "2023-09-15",
            "maturity_date": "2028-09-15",
            "term": "5 years",
            "interest_rate_type": "floating",
            "benchmark": "EURIBOR",
            "spread": 200,  # basis points
            "current_rate": 4.5,  # percent
            "payment_frequency": "quarterly",
            "principal_payment": "bullet",
            "prepayment_penalty": "1% in year 1, none thereafter",
            "financial_covenants": ["Debt/EBITDA <= 3.75x", "Interest Coverage >= 3.0x"],
            "security": "unsecured",
            "refinancing_costs": {
                "prepayment_fee": 0.01 * 20000000,  # 1% penalty still applies
                "upfront_fee_estimate": 0.75,  # percent
                "legal_fees_estimate": 150000,  # EUR
            },
        },
    }

    # Sample market data (would come from financial data provider in real implementation)
    market_rates = {
        "USD": {
            "risk_free": {
                "1y": 3.85,
                "2y": 4.10,
                "3y": 4.20,
                "5y": 4.25,
                "7y": 4.30,
                "10y": 4.35,
            },
            "term_loan": {
                "AA": {"spread": 125},
                "A": {"spread": 150},
                "BBB": {"spread": 200},
            },
            "revolver": {
                "AA": {"spread": 100},
                "A": {"spread": 125},
                "BBB": {"spread": 175},
            },
        },
        "EUR": {
            "risk_free": {
                "1y": 2.95,
                "2y": 3.05,
                "3y": 3.10,
                "5y": 3.15,
                "7y": 3.20,
                "10y": 3.30,
            },
            "term_loan": {
                "AA": {"spread": 150},
                "A": {"spread": 175},
                "BBB": {"spread": 225},
            },
            "revolver": {
                "AA": {"spread": 125},
                "A": {"spread": 150},
                "BBB": {"spread": 200},
            },
        },
    }

    # Company credit profile
    company_credit = {
        "rating": "BBB+",
        "rating_outlook": "stable",
    }

    # Determine credit rating band (simplified)
    if company_credit["rating"] in ["AAA", "AA+", "AA", "AA-"]:
        rating_band = "AA"
    elif company_credit["rating"] in ["A+", "A", "A-"]:
        rating_band = "A"
    else:
        rating_band = "BBB"

    # If specific loan requested
    if loan_id:
        if loan_id not in loans:
            return {
                "error": f"Loan {loan_id} not found",
                "available_loans": list(loans.keys())
            }

        loan = loans[loan_id]
        currency = loan["currency"]
        loan_type = "term_loan" if loan["type"] in ["term_loan", "term"] else "revolver"

        # Check if market data is available
        if currency not in market_rates:
            return {
                "error": f"Market data not available for {currency}",
                "available_currencies": list(market_rates.keys())
            }

        # Determine loan term for rate lookup
        if "term" in loan:
            if "7 year" in loan["term"] or "7-year" in loan["term"]:
                term_key = "7y"
            elif "10 year" in loan["term"] or "10-year" in loan["term"]:
                term_key = "10y"
            elif "5 year" in loan["term"] or "5-year" in loan["term"]:
                term_key = "5y"
            elif "3 year" in loan["term"] or "3-year" in loan["term"]:
                term_key = "3y"
            elif "2 year" in loan["term"] or "2-year" in loan["term"]:
                term_key = "2y"
            elif "1 year" in loan["term"] or "1-year" in loan["term"]:
                term_key = "1y"
            else:
                term_key = "5y"  # Default to 5 years
        else:
            term_key = "5y"  # Default to 5 years

        # Calculate estimated new rate
        risk_free_rate = market_rates[currency]["risk_free"][term_key]
        spread = market_rates[currency][loan_type][rating_band]["spread"]
        estimated_new_rate = risk_free_rate + (spread / 100)

        # If target rate is provided, use that instead
        if target_rate is not None:
            estimated_new_rate = float(target_rate)

        # Calculate potential savings
        rate_reduction = loan["current_rate"] - estimated_new_rate
        annual_interest_current = loan["outstanding_amount"] * (loan["current_rate"] / 100)
        annual_interest_new = loan["outstanding_amount"] * (estimated_new_rate / 100)
        annual_savings = annual_interest_current - annual_interest_new

        # Calculate refinancing costs
        upfront_fee = loan["outstanding_amount"] * (loan["refinancing_costs"]["upfront_fee_estimate"] / 100)
        total_refinancing_cost = loan["refinancing_costs"]["prepayment_fee"] + upfront_fee + loan["refinancing_costs"]["legal_fees_estimate"]

        # Calculate breakeven
        if annual_savings > 0:
            breakeven_years = total_refinancing_cost / annual_savings
        else:
            breakeven_years = float('inf')

        # Get RAG context for refinancing
        query = f"refinancing {loan['type']} {currency} {company_credit['rating']}"
        context = await rag_module.generate_context(
            query, filter_criteria={"category": "external_financing"}
        )

        # Generate refinancing analysis using LLM
        system_prompt = f"""
        You are a debt refinancing advisor. Analyze the refinancing opportunity for this debt:

        Loan: {loan['name']} ({loan_id})
        Type: {loan['type']}
        Outstanding Amount: {currency} {loan['outstanding_amount']:,}
        Current Rate: {loan['current_rate']}% ({loan['benchmark']} + {loan['spread']} bps)
        Maturity: {loan['maturity_date']}
        Prepayment Penalty: {loan.get('prepayment_penalty', 'None')}

        Market Conditions:
        - Current {currency} {term_key} Risk-Free Rate: {risk_free_rate}%
        - Credit Spread for {rating_band}-rated {loan_type}: {spread} bps
        - Estimated New Rate: {estimated_new_rate:.2f}%
        - Rate Reduction: {rate_reduction:.2f}%

        Financial Impact:
        - Annual Interest (Current): {currency} {annual_interest_current:,.2f}
        - Annual Interest (New): {currency} {annual_interest_new:,.2f}
        - Annual Savings: {currency} {annual_savings:,.2f}

        Refinancing Costs:
        - Prepayment Fee: {currency} {loan['refinancing_costs']['prepayment_fee']:,.2f}
        - Estimated Upfront Fee: {currency} {upfront_fee:,.2f}
        - Legal and Other Fees: {currency} {loan['refinancing_costs']['legal_fees_estimate']:,.2f}
        - Total Refinancing Cost: {currency} {total_refinancing_cost:,.2f}

        Breakeven Period: {breakeven_years:.2f} years

        Provide a comprehensive refinancing recommendation that addresses:
        1. Whether refinancing is financially advantageous
        2. Optimal timing for refinancing
        3. Recommended structure for the new financing
        4. Key terms to negotiate
        5. Potential risks or considerations

        Be specific and actionable in your recommendations, considering the financial impact and market conditions.
        """

        if context:
            system_prompt += f"\n\nAdditional market context for your analysis:\n{context}"

        refinancing_analysis = await generate_text(
            prompt=f"Analyze refinancing opportunity for {loan['name']}",
            system_prompt=system_prompt,
        )

        return {
            "loan_id": loan_id,
            "loan_details": {
                "name": loan["name"],
                "type": loan["type"],
                "outstanding_amount": loan["outstanding_amount"],
                "currency": currency,
                "current_rate": loan["current_rate"],
                "maturity_date": loan["maturity_date"],
            },
            "market_conditions": {
                "risk_free_rate": risk_free_rate,
                "credit_spread": spread,
                "estimated_new_rate": estimated_new_rate,
                "rate_reduction": rate_reduction,
            },
            "financial_impact": {
                "annual_interest_current": annual_interest_current,
                "annual_interest_new": annual_interest_new,
                "annual_savings": annual_savings,
            },
            "refinancing_costs": {
                "prepayment_fee": loan["refinancing_costs"]["prepayment_fee"],
                "upfront_fee": upfront_fee,
                "legal_fees": loan["refinancing_costs"]["legal_fees_estimate"],
                "total_cost": total_refinancing_cost,
            },
            "breakeven_years": breakeven_years,
            "formatted_response": refinancing_analysis,
        }

    # Portfolio-level refinancing analysis
    else:
        # Analyze all loans for refinancing opportunities
        refinancing_opportunities = []

        for loan_id, loan in loans.items():
            currency = loan["currency"]
            loan_type = "term_loan" if loan["type"] in ["term_loan", "term"] else "revolver"

            # Skip if market data not available
            if currency not in market_rates:
                continue

            # Determine loan term for rate lookup
            if "term" in loan:
                if "7 year" in loan["term"] or "7-year" in loan["term"]:
                    term_key = "7y"
                elif "10 year" in loan["term"] or "10-year" in loan["term"]:
                    term_key = "10y"
                elif "5 year" in loan["term"] or "5-year" in loan["term"]:
                    term_key = "5y"
                elif "3 year" in loan["term"] or "3-year" in loan["term"]:
                    term_key = "3y"
                elif "2 year" in loan["term"] or "2-year" in loan["term"]:
                    term_key = "2y"
                elif "1 year" in loan["term"] or "1-year" in loan["term"]:
                    term_key = "1y"
                else:
                    term_key = "5y"  # Default to 5 years
            else:
                term_key = "5y"  # Default to 5 years

            # Check if term_key exists in market_rates
            if term_key not in market_rates[currency]["risk_free"]:
                continue

            # Calculate estimated new rate
            risk_free_rate = market_rates[currency]["risk_free"][term_key]
            spread = market_rates[currency][loan_type][rating_band]["spread"]
            estimated_new_rate = risk_free_rate + (spread / 100)

            # Calculate potential savings
            rate_reduction = loan["current_rate"] - estimated_new_rate
            annual_interest_current = loan["outstanding_amount"] * (loan["current_rate"] / 100)
            annual_interest_new = loan["outstanding_amount"] * (estimated_new_rate / 100)
            annual_savings = annual_interest_current - annual_interest_new

            # Calculate refinancing costs
            upfront_fee = loan["outstanding_amount"] * (loan["refinancing_costs"]["upfront_fee_estimate"] / 100)
            total_refinancing_cost = loan["refinancing_costs"]["prepayment_fee"] + upfront_fee + loan["refinancing_costs"]["legal_fees_estimate"]

            # Calculate breakeven
            if annual_savings > 0:
                breakeven_years = total_refinancing_cost / annual_savings
            else:
                breakeven_years = float('inf')

            # Add to opportunities if there are savings
            if rate_reduction > 0:
                refinancing_opportunities.append({
                    "loan_id": loan_id,
                    "name": loan["name"],
                    "currency": currency,
                    "outstanding_amount": loan["outstanding_amount"],
                    "current_rate": loan["current_rate"],
                    "estimated_new_rate": estimated_new_rate,
                    "rate_reduction": rate_reduction,
                    "annual_savings": annual_savings,
                    "refinancing_cost": total_refinancing_cost,
                    "breakeven_years": breakeven_years,
                    "prepayment_penalty": loan.get("prepayment_penalty", "None"),
                })

        # Sort opportunities by breakeven period
        refinancing_opportunities.sort(key=lambda x: x["breakeven_years"])

        # Get RAG context for portfolio refinancing
        query = f"debt portfolio refinancing strategy {company_credit['rating']}"
        context = await rag_module.generate_context(
            query, filter_criteria={"category": "external_financing"}
        )

        # Generate portfolio refinancing strategy using LLM
        system_prompt = """
        You are a debt portfolio manager. Develop a comprehensive refinancing strategy for this loan portfolio:

        Refinancing Opportunities:
        """

        for opp in refinancing_opportunities:
            system_prompt += f"""

            {opp['name']} ({opp['loan_id']}):
            - Outstanding: {opp['currency']} {opp['outstanding_amount']:,}
            - Current Rate: {opp['current_rate']}%
            - Potential New Rate: {opp['estimated_new_rate']:.2f}%
            - Rate Reduction: {opp['rate_reduction']:.2f}%
            - Annual Savings: {opp['currency']} {opp['annual_savings']:,.2f}
            - Refinancing Cost: {opp['currency']} {opp['refinancing_cost']:,.2f}
            - Breakeven: {opp['breakeven_years']:.2f} years
            - Prepayment Penalty: {opp['prepayment_penalty']}
            """

        system_prompt += """

        Provide a strategic refinancing approach for the overall debt portfolio, including:
        1. Prioritization of which loans to refinance first
        2. Potential for combining multiple refinancings
        3. Optimal timing considerations
        4. Impact on overall debt portfolio structure
        5. Market and execution risks to consider

        Be specific and actionable in your recommendations, focusing on maximizing financial benefits while managing execution risks.
        """

        if context:
            system_prompt += f"\n\nAdditional market context for your strategy:\n{context}"

        portfolio_strategy = await generate_text(
            prompt="Develop debt portfolio refinancing strategy",
            system_prompt=system_prompt,
            max_new_tokens=1024,
        )

        # Calculate total potential savings
        total_annual_savings = sum(opp["annual_savings"] for opp in refinancing_opportunities)
        total_refinancing_cost = sum(opp["refinancing_cost"] for opp in refinancing_opportunities)

        return {
            "refinancing_opportunities": refinancing_opportunities,
            "opportunity_count": len(refinancing_opportunities),
            "total_potential_savings": {
                "annual": total_annual_savings,
                "costs": total_refinancing_cost,
                "average_breakeven": sum(opp["breakeven_years"] for opp in refinancing_opportunities) / len(refinancing_opportunities) if refinancing_opportunities else 0,
            },
            "formatted_response": portfolio_strategy,
        }


async def handle_debt_maturity(entities: Dict) -> Dict:
    """
    Analyze debt maturity schedule and provide recommendations.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with debt maturity analysis
    """
    # Extract relevant entities
    time_horizon = entities.get("time_horizon", "5y")
    currency = entities.get("currency")

    # Sample debt data (would come from debt management system in real implementation)
    debts = {
        "L001": {
            "name": "Term Loan A",
            "type": "term_loan",
            "outstanding_amount": 20000000,
            "currency": "USD",
            "maturity_date": "2027-06-15",
            "interest_rate": 5.5,
        },
        "L002": {
            "name": "Revolving Credit Facility",
            "type": "revolver",
            "outstanding_amount": 8000000,
            "currency": "USD",
            "maturity_date": "2027-06-15",
            "interest_rate": 5.25,
        },
        "L003": {
            "name": "Term Loan B",
            "type": "term_loan",
            "outstanding_amount": 48750000,
            "currency": "USD",
            "maturity_date": "2030-03-10",
            "interest_rate": 6.0,
        },
        "L004": {
            "name": "Euro Term Loan",
            "type": "term_loan",
            "outstanding_amount": 20000000,
            "currency": "EUR",
            "maturity_date": "2028-09-15",
            "interest_rate": 4.5,
        },
        "B001": {
            "name": "Senior Notes Series A",
            "type": "bond",
            "outstanding_amount": 75000000,
            "currency": "USD",
            "maturity_date": "2029-12-15",
            "interest_rate": 5.75,
        },
        "B002": {
            "name": "Senior Notes Series B",
            "type": "bond",
            "outstanding_amount": 50000000,
            "currency": "USD",
            "maturity_date": "2031-06-30",
            "interest_rate": 6.25,
        },
        "CP001": {
            "name": "Commercial Paper Program",
            "type": "commercial_paper",
            "outstanding_amount": 25000000,
            "currency": "USD",
            "maturity_date": "2025-12-31",
            "interest_rate": 4.25,
        },
    }

    # Filter by currency if specified
    if currency:
        debts = {id: debt for id, debt in debts.items() if debt["currency"] == currency}

    # Parse time horizon
    years = 5
    if time_horizon.endswith("y"):
        try:
            years = int(time_horizon[:-1])
        except ValueError:
            years = 5

    horizon_date = datetime.datetime.now() + datetime.timedelta(days=365 * years)
    horizon_date_str = horizon_date.strftime("%Y-%m-%d")

    # Group by year
    maturities_by_year = {}
    for debt_id, debt in debts.items():
        year = debt["maturity_date"][:4]  # Extract year from date

        if year not in maturities_by_year:
            maturities_by_year[year] = {
                "count": 0,
                "total_amount": 0,
                "by_currency": {},
                "debts": [],
            }

        maturities_by_year[year]["count"] += 1
        maturities_by_year[year]["total_amount"] += debt["outstanding_amount"]

        if debt["currency"] not in maturities_by_year[year]["by_currency"]:
            maturities_by_year[year]["by_currency"][debt["currency"]] = 0

        maturities_by_year[year]["by_currency"][debt["currency"]] += debt["outstanding_amount"]
        maturities_by_year[year]["debts"].append({
            "debt_id": debt_id,
            "name": debt["name"],
            "type": debt["type"],
            "amount": debt["outstanding_amount"],
            "currency": debt["currency"],
            "rate": debt["interest_rate"],
        })

    # Sort years
    sorted_years = sorted(maturities_by_year.keys())

    # Calculate major maturity years (>20% of total debt)
    total_debt = sum(debt["outstanding_amount"] for debt in debts.values())
    major_maturity_years = [
        year for year, data in maturities_by_year.items()
        if data["total_amount"] / total_debt > 0.2
    ]

    # Get RAG context for debt maturity management
    query = f"debt maturity management {time_horizon}"
    context = await rag_module.generate_context(
        query, filter_criteria={"category": "external_financing"}
    )

    # Generate debt maturity analysis using LLM
    system_prompt = f"""
    You are a debt portfolio manager specializing in maturity management. Analyze this debt maturity profile:

    Total Debt: {sum(debt['outstanding_amount'] for debt in debts.values()):,.0f} mixed currencies
    Time Horizon: {time_horizon} (until {horizon_date_str})
    """

    for year in sorted_years:
        system_prompt += f"""

        {year} Maturities:
        - Total: {maturities_by_year[year]['total_amount']:,.0f} ({', '.join([f'{curr} {amt:,.0f}' for curr, amt in maturities_by_year[year]['by_currency'].items()])})
        - Count: {maturities_by_year[year]['count']} debt instruments
        - Instruments: {', '.join([f"{debt['name']} ({debt['currency']} {debt['amount']:,.0f})" for debt in maturities_by_year[year]['debts']])}
        """

    system_prompt += f"""

    Major Maturity Years (>20% of total debt): {', '.join(major_maturity_years)}

    Provide a comprehensive debt maturity analysis that includes:
    1. Assessment of the current maturity profile and concentration risks
    2. Recommendations for addressing maturity concentrations
    3. Proactive refinancing strategy to smooth the maturity profile
    4. Optimal debt structure recommendations
    5. Market timing considerations for addressing near-term maturities

    Focus on practical strategies to manage refinancing risk while optimizing the cost of debt.
    """

    if context:
        system_prompt += f"\n\nAdditional context for your analysis:\n{context}"

    maturity_analysis = await generate_text(
        prompt=f"Analyze debt maturity profile over {time_horizon}",
        system_prompt=system_prompt,
        max_new_tokens=1024,
    )

    return {
        "time_horizon": time_horizon,
        "horizon_date": horizon_date_str,
        "total_debt": sum(debt["outstanding_amount"] for debt in debts.values()),
        "currency_filter": currency,
        "maturity_profile": {
            year: {
                "total": maturities_by_year[year]["total_amount"],
                "count": maturities_by_year[year]["count"],
                "by_currency": maturities_by_year[year]["by_currency"],
                "percent_of_total": maturities_by_year[year]["total_amount"] / total_debt * 100,
                "debts": maturities_by_year[year]["debts"],
            } for year in sorted_years
        },
        "major_maturity_years": major_maturity_years,
        "formatted_response": maturity_analysis,
    }


async def handle_interest_payment(entities: Dict) -> Dict:
    """
    Track and forecast interest payments.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with interest payment information
    """
    # Extract relevant entities
    time_period = entities.get("time_period", "1y")
    debt_id = entities.get("debt_id")

    # Sample debt data (would come from debt management system in real implementation)
    debts = {
        "L001": {
            "name": "Term Loan A",
            "type": "term_loan",
            "outstanding_amount": 20000000,
            "currency": "USD",
            "maturity_date": "2027-06-15",
            "interest_rate_type": "floating",
            "current_rate": 5.5,
            "payment_frequency": "quarterly",
            "next_payment_date": "2025-06-15",
            "annual_interest": 1100000,  # 5.5% of 20M
        },
        "L002": {
            "name": "Revolving Credit Facility",
            "type": "revolver",
            "outstanding_amount": 8000000,
            "currency": "USD",
            "maturity_date": "2027-06-15",
            "interest_rate_type": "floating",
            "current_rate": 5.25,
            "payment_frequency": "quarterly",
            "next_payment_date": "2025-06-15",
            "annual_interest": 420000,  # 5.25% of 8M
        },
        "L003": {
            "name": "Term Loan B",
            "type": "term_loan",
            "outstanding_amount": 48750000,
            "currency": "USD",
            "maturity_date": "2030-03-10",
            "interest_rate_type": "floating",
            "current_rate": 6.0,
            "payment_frequency": "quarterly",
            "next_payment_date": "2025-06-10",
            "annual_interest": 2925000,  # 6.0% of 48.75M
        },
        "L004": {
            "name": "Euro Term Loan",
            "type": "term_loan",
            "outstanding_amount": 20000000,
            "currency": "EUR",
            "maturity_date": "2028-09-15",
            "interest_rate_type": "floating",
            "current_rate": 4.5,
            "payment_frequency": "quarterly",
            "next_payment_date": "2025-06-15",
            "annual_interest": 900000,  # 4.5% of 20M
        },
        "B001": {
            "name": "Senior Notes Series A",
            "type": "bond",
            "outstanding_amount": 75000000,
            "currency": "USD",
            "maturity_date": "2029-12-15",
            "interest_rate_type": "fixed",
            "current_rate": 5.75,
            "payment_frequency": "semi-annual",
            "next_payment_date": "2025-06-15",
            "annual_interest": 4312500,  # 5.75% of 75M
        },
        "B002": {
            "name": "Senior Notes Series B",
            "type": "bond",
            "outstanding_amount": 50000000,
            "currency": "USD",
            "maturity_date": "2031-06-30",
            "interest_rate_type": "fixed",
            "current_rate": 6.25,
            "payment_frequency": "semi-annual",
            "next_payment_date": "2025-06-30",
            "annual_interest": 3125000,  # 6.25% of 50M
        },
        "CP001": {
            "name": "Commercial Paper Program",
            "type": "commercial_paper",
            "outstanding_amount": 25000000,
            "currency": "USD",
            "maturity_date": "2025-12-31",
            "interest_rate_type": "fixed",
            "current_rate": 4.25,
            "payment_frequency": "at maturity",
            "next_payment_date": "2025-12-31",
            "annual_interest": 1062500,  # 4.25% of 25M
        },
    }

    # If specific debt requested
    if debt_id:
        if debt_id not in debts:
            return {
                "error": f"Debt {debt_id} not found",
                "available_debts": list(debts.keys())
            }

        debt = debts[debt_id]

        # Generate payment schedule
        payment_schedule = []

        # Parse time period
        years = 1
        if time_period.endswith("y"):
            try:
                years = int(time_period[:-1])
            except ValueError:
                years = 1

        # Determine number of payments based on frequency
        payments_per_year = {
            "monthly": 12,
            "quarterly": 4,
            "semi-annual": 2,
            "annual": 1,
            "at maturity": 1,
        }

        frequency = debt["payment_frequency"]
        total_payments = payments_per_year.get(frequency, 4) * years

        # Calculate payment amount
        annual_interest = debt["annual_interest"]
        payment_amount = annual_interest / payments_per_year.get(frequency, 4)

        # Generate schedule
        current_date = datetime.datetime.strptime(debt["next_payment_date"], "%Y-%m-%d")

        for i in range(total_payments):
            payment_schedule.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "amount": payment_amount,
                "currency": debt["currency"],
                "payment_type": "Interest",
            })

            # Advance to next payment date
            if frequency == "monthly":
                current_date = current_date.replace(month=current_date.month % 12 + 1)
                if current_date.month == 1:
                    current_date = current_date.replace(year=current_date.year + 1)
            elif frequency == "quarterly":
                new_month = ((current_date.month - 1 + 3) % 12) + 1
                new_year = current_date.year + ((current_date.month - 1 + 3) // 12)
                current_date = current_date.replace(year=new_year, month=new_month)
            elif frequency == "semi-annual":
                new_month = ((current_date.month - 1 + 6) % 12) + 1
                new_year = current_date.year + ((current_date.month - 1 + 6) // 12)
                current_date = current_date.replace(year=new_year, month=new_month)
            elif frequency == "annual":
                current_date = current_date.replace(year=current_date.year + 1)
            elif frequency == "at maturity":
                break  # Only one payment at maturity

        # Add maturity payment if within time period
        maturity_date = datetime.datetime.strptime(debt["maturity_date"], "%Y-%m-%d")
        end_date = datetime.datetime.now() + datetime.timedelta(days=365 * years)

        if maturity_date <= end_date:
            payment_schedule.append({
                "date": debt["maturity_date"],
                "amount": debt["outstanding_amount"],
                "currency": debt["currency"],
                "payment_type": "Principal",
            })

        # Sort by date
        payment_schedule.sort(key=lambda x: x["date"])

        # Calculate total interest over period
        total_interest = sum(p["amount"] for p in payment_schedule if p["payment_type"] == "Interest")

        return {
            "debt_id": debt_id,
            "name": debt["name"],
            "type": debt["type"],
            "currency": debt["currency"],
            "outstanding_amount": debt["outstanding_amount"],
            "interest_rate": debt["current_rate"],
            "payment_frequency": debt["payment_frequency"],
            "next_payment_date": debt["next_payment_date"],
            "time_period": time_period,
            "payment_schedule": payment_schedule,
            "total_interest": total_interest,
            "total_principal": sum(p["amount"] for p in payment_schedule if p["payment_type"] == "Principal"),
            "message": (
                f"Interest Payment Schedule for {debt['name']} ({debt_id}):\n"
                f"Amount: {debt['currency']} {debt['outstanding_amount']:,.0f}\n"
                f"Rate: {debt['current_rate']}% ({debt['interest_rate_type']})\n"
                f"Frequency: {debt['payment_frequency']}\n"
                f"Annual Interest: {debt['currency']} {debt['annual_interest']:,.0f}\n\n"
                f"Payments over {time_period}:\n" +
                "\n".join([
                    f"- {p['date']}: {debt['currency']} {p['amount']:,.2f} ({p['payment_type']})"
                    for p in payment_schedule
                ]) +
                f"\n\nTotal Interest: {debt['currency']} {total_interest:,.2f}"
            ),
        }

    # Portfolio-level interest payments
    else:
        # Parse time period
        years = 1
        if time_period.endswith("y"):
            try:
                years = int(time_period[:-1])
            except ValueError:
                years = 1

        end_date = datetime.datetime.now() + datetime.timedelta(days=365 * years)
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Group debts by currency
        by_currency = {}
        for debt_id, debt in debts.items():
            currency = debt["currency"]

            if currency not in by_currency:
                by_currency[currency] = {
                    "count": 0,
                    "total_outstanding": 0,
                    "annual_interest": 0,
                }

            by_currency[currency]["count"] += 1
            by_currency[currency]["total_outstanding"] += debt["outstanding_amount"]
            by_currency[currency]["annual_interest"] += debt["annual_interest"]

        # Calculate total interest over period
        total_interest_by_currency = {}
        for currency, data in by_currency.items():
            total_interest_by_currency[currency] = data["annual_interest"] * years

        # Generate quarterly forecast
        quarterly_forecast = []
        current_quarter_start = datetime.datetime.now().replace(day=1)
        # Adjust to start of quarter
        month = current_quarter_start.month
        quarter_month = ((month - 1) // 3) * 3 + 1
        current_quarter_start = current_quarter_start.replace(month=quarter_month)

        for i in range(years * 4):
            quarter_end_month = ((current_quarter_start.month - 1 + 3) % 12) + 1
            quarter_end_year = current_quarter_start.year + ((current_quarter_start.month - 1 + 3) // 12)
            quarter_end = current_quarter_start.replace(year=quarter_end_year, month=quarter_end_month) - datetime.timedelta(days=1)

            quarter_name = f"Q{((current_quarter_start.month - 1) // 3) + 1} {current_quarter_start.year}"
            interest_by_currency = {}

            for currency, data in by_currency.items():
                interest_by_currency[currency] = data["annual_interest"] / 4

            quarterly_forecast.append({
                "quarter": quarter_name,
                "start_date": current_quarter_start.strftime("%Y-%m-%d"),
                "end_date": quarter_end.strftime("%Y-%m-%d"),
                "interest_by_currency": interest_by_currency,
                "total_interest": sum(interest_by_currency.values()),
            })

            # Move to next quarter
            current_quarter_start = current_quarter_start.replace(
                month=((current_quarter_start.month - 1 + 3) % 12) + 1,
                year=current_quarter_start.year + ((current_quarter_start.month - 1 + 3) // 12)
            )

        # Get RAG context for interest payment management
        query = f"interest payment management {time_period}"
        context = await rag_module.generate_context(
            query, filter_criteria={"category": "external_financing"}
        )

        # Generate interest payment analysis using LLM
        system_prompt = f"""
        You are a financial analyst specializing in debt management. Analyze this debt interest payment forecast:

        Time Period: {time_period} (until {end_date_str})

        Debt Portfolio Summary:
        """

        for currency, data in by_currency.items():
            system_prompt += f"""

            {currency} Debt:
            - Outstanding Amount: {currency} {data['total_outstanding']:,.0f}
            - Annual Interest: {currency} {data['annual_interest']:,.0f}
            - Projected Interest ({time_period}): {currency} {total_interest_by_currency[currency]:,.0f}
            """

        system_prompt += """

        Quarterly Interest Forecast:
        """

        for quarter in quarterly_forecast:
            system_prompt += f"""

            {quarter['quarter']} ({quarter['start_date']} to {quarter['end_date']}):
            """
            for currency, amount in quarter["interest_by_currency"].items():
                system_prompt += f"- {currency}: {amount:,.0f}\n"

        system_prompt += """

        Provide a comprehensive interest payment analysis including:
        1. Assessment of the current interest burden and its impact on cash flow
        2. Identification of high-interest debt that might be refinancing candidates
        3. Strategies for managing interest rate risk in the portfolio
        4. Cash flow planning recommendations for meeting interest obligations
        5. Opportunities for optimizing the overall cost of debt

        Focus on practical insights and actionable recommendations for managing interest payments efficiently.
        """

        if context:
            system_prompt += f"\n\nAdditional context for your analysis:\n{context}"

        interest_analysis = await generate_text(
            prompt=f"Analyze debt interest payments over {time_period}",
            system_prompt=system_prompt,
        )

        return {
            "time_period": time_period,
            "end_date": end_date_str,
            "debt_summary": {
                "total_count": len(debts),
                "by_currency": by_currency,
            },
            "interest_summary": {
                "annual_by_currency": {currency: data["annual_interest"] for currency, data in by_currency.items()},
                "total_by_currency": total_interest_by_currency,
                "total_usd_equivalent": total_interest_by_currency.get("USD", 0) + total_interest_by_currency.get("EUR", 0) * 1.09,  # Simplified conversion
            },
            "quarterly_forecast": quarterly_forecast,
            "formatted_response": interest_analysis,
        }