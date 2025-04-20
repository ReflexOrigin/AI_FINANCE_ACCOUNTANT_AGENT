"""
Cash Management Operations Module for Finance Accountant Agent

This module handles operations related to cash management, including
cash position reporting, cash flow forecasting, liquidity analysis,
working capital optimization, and cash pooling.

Features:
- Current cash position reporting
- Short and long-term cash flow forecasting
- Liquidity analysis and metrics
- Working capital optimization recommendations
- Cash pooling and concentration strategies

Dependencies:
- bank_adapters: For banking data access
- rag_module: For retrieving relevant cash documents
- llm_module: For analysis and recommendations
"""

import asyncio
import datetime
import logging
from typing import Dict, List, Optional

from modules.bank_adapters import get_banking_adapter
from modules.llm_module import generate_text
from modules.rag_module import rag_module

from config.settings import settings


logger = logging.getLogger(__name__)


async def handle_cash_position(entities: Dict) -> Dict:
    """
    Get current cash position across accounts.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with cash position information
    """
    # Extract relevant entities
    currency = entities.get("currency", "USD")
    as_of_date = entities.get("date", "today")
    account_id = entities.get("account_id")

    # Convert "today" to actual date
    if as_of_date == "today":
        as_of_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Get banking adapter
    banking_adapter = get_banking_adapter()

    try:
        accounts_data: List[Dict] = []
        total_balance: float = 0.0

        # If specific account requested
        if account_id:
            account_data = await banking_adapter.get_account_balance(account_id)
            accounts_data.append(account_data)

            # Convert if different currency
            if account_data["currency"] != currency:
                fx_rates = await banking_adapter.get_fx_rates(
                    account_data["currency"], [currency]
                )
                rate = fx_rates["rates"][currency]
                converted_balance = account_data["balance"] * rate
                account_data["converted_balance"] = converted_balance
                account_data["converted_currency"] = currency
                total_balance += converted_balance
            else:
                total_balance += account_data["balance"]
        else:
            # Get all accounts (using sample account IDs from bank_adapters)
            for acct_id in ["1001", "1002", "1003", "1004"]:
                account_data = await banking_adapter.get_account_balance(acct_id)
                accounts_data.append(account_data)

                # Convert if different currency
                if account_data["currency"] != currency:
                    fx_rates = await banking_adapter.get_fx_rates(
                        account_data["currency"], [currency]
                    )
                    rate = fx_rates["rates"][currency]
                    converted_balance = account_data["balance"] * rate
                    account_data["converted_balance"] = converted_balance
                    account_data["converted_currency"] = currency
                    total_balance += converted_balance
                else:
                    total_balance += account_data["balance"]

        # Format response
        message = (
            f"Total cash position as of {as_of_date}: "
            f"{total_balance:,.2f} {currency}"
        )

        return {
            "total_balance": total_balance,
            "currency": currency,
            "as_of_date": as_of_date,
            "accounts": accounts_data,
            "message": message,
        }

    except Exception as e:
        logger.error(f"Error in cash position: {e}")
        return {"error": f"Failed to retrieve cash position: {e}"}


async def handle_cash_flow_forecast(entities: Dict) -> Dict:
    """
    Generate cash flow forecast for specified period.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with cash flow forecast data
    """
    # Extract relevant entities
    period = entities.get("period", "month")
    num_periods = int(entities.get("num_periods", 3))
    currency = entities.get("currency", "USD")

    # Get RAG context for cash flow assumptions
    query = f"cash flow forecast {period} {num_periods} periods"
    context = await rag_module.generate_context(
        query, filter_criteria={"category": "cash_management"}
    )

    system_prompt = (
        "You are a financial analyst specializing in cash flow forecasting.\n"
        "Generate a cash flow forecast based on available information.\n"
        "Include inflows, outflows, net cash flow, and ending cash position for each period.\n"
        "Provide realistic projections based on historical data and business trends."
    )

    if context:
        system_prompt += f"\n\nUse this context for your forecast:\n{context}"

    # If no context, generate sample data
    if not context:
        start_date = datetime.datetime.now()
        forecast_data: List[Dict] = []
        current_balance = 1_500_000  # Starting balance

        for i in range(num_periods):
            # Calculate period end date and name
            if period == "day":
                period_end = start_date + datetime.timedelta(days=i + 1)
                period_name = period_end.strftime("%Y-%m-%d")
            elif period == "week":
                period_end = start_date + datetime.timedelta(weeks=i + 1)
                period_name = f"Week {i + 1} ({period_end.strftime('%m/%d')})"
            elif period == "month":
                month = start_date.month + i
                year = start_date.year + (month - 1) // 12
                month = (month - 1) % 12 + 1
                period_end = start_date.replace(year=year, month=month)
                period_name = period_end.strftime("%b %Y")
            else:  # quarter
                extra_quarters = i + (start_date.month - 1) // 3
                extra_years = extra_quarters // 4
                quarter_month = (extra_quarters % 4) * 3 + 1
                period_end = start_date.replace(
                    year=start_date.year + extra_years, month=quarter_month
                )
                quarter_num = (quarter_month - 1) // 3 + 1
                period_name = f"Q{quarter_num} {period_end.year}"

            # Sample data with variability
            inflows = 800_000 + (i * 50_000)
            outflows = 700_000 + (i * 30_000)
            net_flow = inflows - outflows
            ending_balance = current_balance + net_flow

            forecast_data.append({
                "period": period_name,
                "inflows": inflows,
                "outflows": outflows,
                "net_flow": net_flow,
                "beginning_balance": current_balance,
                "ending_balance": ending_balance,
            })

            current_balance = ending_balance

        periods_text = (
            "days" if period == "day" else
            "weeks" if period == "week" else
            "months" if period == "month" else
            "quarters"
        )
        start_balance = forecast_data[0]["beginning_balance"]
        end_balance = forecast_data[-1]["ending_balance"]
        net_change = end_balance - start_balance

        message = (
            f"Cash flow forecast for the next {num_periods} {periods_text}:\n"
            f"Starting balance: {start_balance:,.2f} {currency}\n"
            f"Ending balance: {end_balance:,.2f} {currency}\n"
            f"Net change: {net_change:,.2f} {currency} "
            f"({(net_change / start_balance * 100):.1f}%)"
        )

        return {
            "period_type": period,
            "num_periods": num_periods,
            "currency": currency,
            "forecast_data": forecast_data,
            "message": message,
        }

    # Generate forecast via LLM
    formatted_response = await generate_text(
        prompt=f"Generate a cash flow forecast for {
            num_periods} {period}s in {currency}",
        system_prompt=system_prompt,
    )

    return {"formatted_response": formatted_response}


async def handle_liquidity_analysis(entities: Dict) -> Dict:
    """
    Perform liquidity analysis with key metrics.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with liquidity analysis results
    """
    time_period = entities.get("time_period", "current")
    metrics = entities.get("metrics", ["current_ratio", "quick_ratio", "cash_ratio"])

    if isinstance(metrics, str):
        metrics = [metrics]

    liquidity_data = {
        "current": {
            "current_assets": 2_500_000,
            "cash_equivalents": 1_200_000,
            "accounts_receivable": 800_000,
            "inventory": 500_000,
            "current_liabilities": 1_800_000,
            "accounts_payable": 750_000,
            "short_term_debt": 650_000,
            "accrued_expenses": 400_000,
        },
        "previous_quarter": {
            "current_assets": 2_300_000,
            "cash_equivalents": 1_000_000,
            "accounts_receivable": 850_000,
            "inventory": 450_000,
            "current_liabilities": 1_700_000,
            "accounts_payable": 720_000,
            "short_term_debt": 650_000,
            "accrued_expenses": 330_000,
        },
        "previous_year": {
            "current_assets": 2_100_000,
            "cash_equivalents": 850_000,
            "accounts_receivable": 780_000,
            "inventory": 470_000,
            "current_liabilities": 1_550_000,
            "accounts_payable": 680_000,
            "short_term_debt": 600_000,
            "accrued_expenses": 270_000,
        },
    }

    if time_period not in liquidity_data:
        return {
            "error": f"Data not available for time period: {time_period}",
            "available_periods": list(liquidity_data.keys()),
        }

    period_data = liquidity_data[time_period]
    ratios: Dict[str, float] = {}

    if "current_ratio" in metrics:
        ratios["current_ratio"] = (
            period_data["current_assets"] / period_data["current_liabilities"]
        )
    if "quick_ratio" in metrics:
        ratios["quick_ratio"] = (
            (period_data["current_assets"] - period_data["inventory"])
            / period_data["current_liabilities"]
        )
    if "cash_ratio" in metrics:
        ratios["cash_ratio"] = (
            period_data["cash_equivalents"] / period_data["current_liabilities"]
        )
    if "working_capital" in metrics:
        ratios["working_capital"] = (
            period_data["current_assets"] - period_data["current_liabilities"]
        )
    if "dso" in metrics:
        daily_revenue = 3_000_000 / 90
        ratios["dso"] = period_data["accounts_receivable"] / daily_revenue
    if "dpo" in metrics:
        daily_cogs = 2_000_000 / 90
        ratios["dpo"] = period_data["accounts_payable"] / daily_cogs

    # Generate analysis message
    analysis_lines: List[str] = [f"Liquidity Analysis ({time_period}):"]

    if "current_ratio" in ratios:
        cr = ratios["current_ratio"]
        status = "strong" if cr > 2 else "adequate" if cr > 1.5 else "concerning"
        analysis_lines.append(f"Current Ratio: {cr:.2f} ({status})")
    if "quick_ratio" in ratios:
        qr = ratios["quick_ratio"]
        status = "strong" if qr > 1.5 else "adequate" if qr > 1 else "concerning"
        analysis_lines.append(f"Quick Ratio: {qr:.2f} ({status})")
    if "cash_ratio" in ratios:
        cashr = ratios["cash_ratio"]
        status = "strong" if cashr > 0.8 else "adequate" if cashr > 0.5 else "concerning"
        analysis_lines.append(f"Cash Ratio: {cashr:.2f} ({status})")
    if "working_capital" in ratios:
        wc = ratios["working_capital"]
        analysis_lines.append(f"Working Capital: ${wc:,.2f}")
    if "dso" in metrics and "dpo" in metrics:
        ccc = ratios.get("dso", 0) - ratios.get("dpo", 0)
        analysis_lines.append(f"Cash Conversion Cycle: {ccc:.1f} days")

    return {
        "time_period": time_period,
        "metrics": metrics,
        "ratios": ratios,
        "raw_data": period_data,
        "message": "\n".join(analysis_lines),
    }


async def handle_working_capital(entities: Dict) -> Dict:
    """
    Analyze working capital and provide optimization recommendations.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with working capital analysis and recommendations
    """
    analysis_type = entities.get("analysis_type", "overview")
    focus_area = entities.get("focus_area")  # ar, ap, inventory, etc.

    query = f"working capital {analysis_type}"
    if focus_area:
        query += f" {focus_area}"

    context = await rag_module.generate_context(
        query, filter_criteria={"category": "cash_management"}
    )

    system_prompt = (
        "You are a working capital optimization specialist. Provide analysis and recommendations "
        "based on the company's current working capital situation.\n\n"
        "Include specific, actionable recommendations for improving working capital efficiency.\n"
        "Focus on practical steps that can be implemented to optimize cash flow.\n\n"
        "If focusing on a specific area:\n"
        "- Accounts Receivable: Discuss collection strategies, credit policies, and invoice processes\n"
        "- Accounts Payable: Discuss payment timing, vendor negotiations, and early payment discounts\n"
        "- Inventory: Discuss inventory management, JIT approaches, and forecasting improvements"
    )

    if context:
        system_prompt += f"\n\nUse this context for your analysis:\n{context}"

    prompt = f"Analyze working capital {analysis_type}"
    if focus_area:
        prompt += f" focusing on {focus_area}"

    response = await generate_text(
        prompt=prompt,
        system_prompt=system_prompt,
        max_new_tokens=1024,
    )

    return {
        "formatted_response": response,
        "analysis_type": analysis_type,
        "focus_area": focus_area or "overall",
        "context_used": bool(context),
    }


async def handle_cash_pooling(entities: Dict) -> Dict:
    """
    Provide cash pooling analysis and recommendations.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with cash pooling analysis
    """
    pooling_type = entities.get("pooling_type", "physical")
    currency = entities.get("currency")
    region = entities.get("region")

    banking_adapter = get_banking_adapter()
    accounts_data: List[Dict] = []

    for acct_id in ["1001", "1002", "1003", "1004"]:
        try:
            account_data = await banking_adapter.get_account_balance(acct_id)
            accounts_data.append(account_data)
        except Exception as e:
            logger.error(f"Error fetching account {acct_id}: {e}")

    query = f"cash pooling {pooling_type}"
    if currency:
        query += f" {currency}"
    if region:
        query += f" {region}"

    context = await rag_module.generate_context(
        query, filter_criteria={"category": "cash_management"}
    )

    system_prompt = (
        "You are a cash management specialist focusing on cash pooling strategies. "
        "Provide analysis and recommendations for implementing or optimizing cash pooling.\n\n"
        "Address these key aspects:\n"
        "1. Structure (physical vs. notional pooling)\n"
        "2. Benefits (interest optimization, reduced overdrafts, etc.)\n"
        "3. Operational considerations\n"
        "4. Regulatory and tax implications\n"
        "5. Banking partner requirements\n"
        "Provide specific, actionable recommendations tailored to the company's situation."  
    )

    if accounts_data:
        acct_context = "Current account balances:\n"
        for account in accounts_data:
            acct_context += f"- Account {account['account_id']}: {account['balance']} {account['currency']}\n"
        system_prompt += f"\n\n{acct_context}"

    if context:
        system_prompt += f"\n\nAdditional context:\n{context}"

    prompt = f"Analyze cash pooling options using {pooling_type} pooling"
    if currency:
        prompt += f" for {currency}"
    if region:
        prompt += f" in {region}"

    response = await generate_text(
        prompt=prompt,
        system_prompt=system_prompt,
        max_new_tokens=1024,
    )

    return {
        "formatted_response": response,
        "pooling_type": pooling_type,
        "currency": currency,
        "region": region,
        "accounts_analyzed": len(accounts_data),
        "context_used": bool(context),
    }
