"""
Investor Relations Operations Module for Finance Accountant Agent

This module handles operations related to investor relations, including
shareholder inquiries, dividend information, earnings reports,
investor presentations, and stock performance analysis.

Features:
- Shareholder information retrieval
- Dividend history and forecasts
- Earnings report generation
- Investor presentation preparation
- Stock performance analytics

Dependencies:
- llm_module: For generating reports and insights
- rag_module: For retrieving relevant financial documents
- bank_adapters: For financial data access
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


async def handle_shareholder_inquiry(entities: Dict) -> Dict:
    shareholder_id = entities.get("shareholder_id")
    inquiry_type = entities.get("inquiry_type", "general")

    query = f"shareholder inquiry about {inquiry_type}"
    if shareholder_id:
        query += f" for shareholder {shareholder_id}"

    context = await rag_module.generate_context(query, filter_criteria={"category": "investor_relations"})

    system_prompt = """
    You are a financial assistant specializing in investor relations.
    Provide accurate and helpful information to shareholder inquiries based on the context provided.
    Be professional, courteous, and informative in your responses.
    """

    response = await generate_text(
        prompt=query,
        system_prompt=system_prompt if context else f"{system_prompt}\n\nNote: I don't have specific information about this inquiry in my records."
    )

    return {
        "formatted_response": response,
        "inquiry_type": inquiry_type,
        "context_used": bool(context),
    }


async def handle_dividend_info(entities: Dict) -> Dict:
    year = entities.get("year", datetime.datetime.now().year)
    quarter = entities.get("quarter")

    dividend_data = {
        "2023": {
            "1": {"date": "2023-03-15", "amount": 0.25, "currency": "USD"},
            "2": {"date": "2023-06-15", "amount": 0.25, "currency": "USD"},
            "3": {"date": "2023-09-15", "amount": 0.28, "currency": "USD"},
            "4": {"date": "2023-12-15", "amount": 0.28, "currency": "USD"},
        },
        "2024": {
            "1": {"date": "2024-03-15", "amount": 0.30, "currency": "USD"},
            "2": {"date": "2024-06-15", "amount": 0.30, "currency": "USD"},
            "3": {"date": "2024-09-15", "amount": 0.32, "currency": "USD"},
            "4": {"date": "2024-12-15", "amount": 0.32, "currency": "USD"},
        },
        "2025": {
            "1": {"date": "2025-03-15", "amount": 0.35, "currency": "USD"},
        }
    }

    if quarter and str(year) in dividend_data and str(quarter) in dividend_data[str(year)]:
        quarter_data = dividend_data[str(year)][str(quarter)]
        return {
            "year": year,
            "quarter": quarter,
            "dividend": quarter_data,
            "message": f"The dividend for Q{quarter} {year} was {quarter_data['amount']} {quarter_data['currency']}, paid on {quarter_data['date']}."
        }
    elif str(year) in dividend_data:
        year_data = dividend_data[str(year)]
        total_amount = sum(q["amount"] for q in year_data.values())
        quarters_info = [f"Q{q}: {data['amount']} {data['currency']} (paid on {data['date']})" for q, data in year_data.items()]
        return {
            "year": year,
            "quarterly_dividends": year_data,
            "total_annual_dividend": total_amount,
            "currency": "USD",
            "message": f"Dividend information for {year}:\n" + "\n".join(quarters_info) + f"\nTotal annual dividend: {total_amount} USD"
        }
    else:
        return {
            "error": f"No dividend information available for {year}",
            "available_years": list(dividend_data.keys())
        }


async def handle_earnings_report(entities: Dict) -> Dict:
    year = entities.get("year", datetime.datetime.now().year)
    quarter = entities.get("quarter")
    report_type = entities.get("report_type", "summary")

    filter_criteria = {
        "category": "financial_reports",
        "type": "earnings",
    }

    if year:
        filter_criteria["year"] = str(year)
    if quarter:
        filter_criteria["quarter"] = str(quarter)

    query = f"earnings report {year}"
    if quarter:
        query += f" Q{quarter}"
    if report_type:
        query += f" {report_type}"

    context = await rag_module.generate_context(query, filter_criteria=filter_criteria)

    system_prompt = """
    You are a financial reporting specialist. Generate an earnings report based on the provided context.
    Include key performance metrics, revenue, profit, expenses, and notable changes from previous periods.
    Format the report professionally and highlight key insights for investors.
    """

    if not context:
        system_prompt += "\n\nNote: You don't have specific earnings data for the requested period. Generate a response explaining this limitation."

    response = await generate_text(
        prompt=query,
        system_prompt=system_prompt,
        max_new_tokens=1024,
    )

    return {
        "formatted_response": response,
        "year": year,
        "quarter": quarter if quarter else "full_year",
        "report_type": report_type,
        "context_used": bool(context),
    }


async def handle_investor_presentation(entities: Dict) -> Dict:
    topic = entities.get("topic", "company overview")
    audience = entities.get("audience", "investors")
    format_type = entities.get("format", "outline")

    system_prompt = f"""
    You are an investor relations specialist creating a presentation for {audience} about {topic}.

    Create a {format_type} that:
    1. Is professionally formatted and structured
    2. Covers key financial information relevant to the topic
    3. Presents data in a clear, actionable manner
    4. Includes appropriate sections for the topic

    Focus on content that would be useful for financial decision-making.
    """

    response = await generate_text(
        prompt=f"Create an investor presentation {format_type} on {topic} for {audience}",
        system_prompt=system_prompt,
        max_new_tokens=1024,
    )

    return {
        "formatted_response": response,
        "topic": topic,
        "audience": audience,
        "format": format_type
    }


async def handle_stock_performance(entities: Dict) -> Dict:
    time_period = entities.get("time_period", "1y")
    comparison = entities.get("comparison", "index")
    metrics = entities.get("metrics", ["price", "volume"])
    if isinstance(metrics, str):
        metrics = [metrics]

    stock_data = {
        "current_price": 157.82,
        "change_percent": 2.3,
        "52w_high": 183.45,
        "52w_low": 121.70,
        "average_volume": 35000000,
        "market_cap": "2.53T",
        "pe_ratio": 26.4,
        "dividend_yield": 0.5,
        "performance": {
            "1m": 3.2,
            "3m": -1.5,
            "6m": 8.7,
            "1y": 15.2,
            "3y": 42.8,
            "5y": 138.5,
        },
        "vs_index": {
            "1m": 1.8,
            "3m": -0.9,
            "6m": 3.2,
            "1y": 7.5,
            "3y": 12.6,
            "5y": 65.3,
        }
    }

    response_data = {
        "current_data": {
            "price": stock_data["current_price"],
            "change_percent": stock_data["change_percent"],
        }
    }

    if time_period in stock_data["performance"]:
        response_data["period_performance"] = {
            "time_period": time_period,
            "performance_percent": stock_data["performance"][time_period]
        }

    if comparison == "index" and time_period in stock_data["vs_index"]:
        response_data["comparison"] = {
            "vs_index_percent": stock_data["vs_index"][time_period],
            "outperformance": stock_data["vs_index"][time_period] > 0
        }

    for metric in metrics:
        if metric in stock_data:
            response_data[metric] = stock_data[metric]

    message = f"Current stock price is ${stock_data['current_price']} ({stock_data['change_percent']}% today). "
    if time_period in stock_data["performance"]:
        perf = stock_data["performance"][time_period]
        message += f"{time_period.upper()} performance is {perf}%. "
    if comparison == "index" and time_period in stock_data["vs_index"]:
        vs_idx = stock_data["vs_index"][time_period]
        message += f"This is {abs(vs_idx)}% {'better' if vs_idx > 0 else 'worse'} than the market index. "

    response_data["message"] = message.strip()

    return response_data
