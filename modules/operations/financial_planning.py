"""
Financial Planning & Analysis Operations Module for Finance Accountant Agent

This module handles budgeting, forecasting, scenario analysis, and financial target setting.

Features:
- Prepare and manage annual budgets
- Update financial forecasts with actual data
- Perform scenario and what-if analyses
- Plan for capital expenditures and investments
- Set and track financial targets and KPIs
"""

import asyncio
import datetime
import logging
from typing import Dict, Any, List, Optional

from modules.bank_adapters import get_banking_adapter
from modules.llm_module import generate_text
from modules.rag_module import rag_module
from config.settings import settings

logger = logging.getLogger(__name__)

async def handle_budget_preparation(entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare and manage annual or periodic budgets.
    
    Args:
        entities: Dictionary containing:
            - period: Budget period (annual, quarterly, monthly)
            - year: The budget year
            - department: Optional specific department to budget for
            - approach: Budgeting approach (zero_based, incremental, etc.)
    
    Returns:
        Dict with:
            - formatted_response: The budget preparation analysis
            - budget_data: Structured budget data
            - _metadata: Metadata about the operation
    """
    try:
        period = entities.get("period", "annual")
        year = entities.get("year", datetime.datetime.now().year)
        department = entities.get("department")
        approach = entities.get("approach", "incremental")
            
        # TODO: Implement budget preparation logic
        
        # Use RAG+LLM for narrative generation
        query = f"Prepare {period} budget for {year}"
        if department:
            query += f" for {department} department"
        query += f" using {approach} approach"
            
        context = await rag_module.generate_context(query, filter_criteria={"category": "budgeting"})
        system_prompt = "You are a financial assistant specializing in budget preparation and analysis..."
        response = await generate_text(
            prompt=query,
            system_prompt=(system_prompt if context else system_prompt + "\n\nNote: no docs found."),
            context=context
        )
        
        result = {"formatted_response": response, "context_used": bool(context)}
        result["_metadata"] = {"operation": "financial_planning/budget_preparation", "success": True}
        return result
    except Exception as e:
        logger.error(f"Error in budget_preparation: {e}")
        return {"error": str(e), "_metadata": {"operation": "financial_planning/budget_preparation", "success": False}}

async def handle_forecast_update(entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update financial forecasts with actual results and new assumptions.
    
    Args:
        entities: Dictionary containing:
            - forecast_period: Period to forecast (quarter, year, multi-year)
            - as_of_date: Date of forecast update (default: today)
            - department: Optional specific department to forecast
            - metrics: Optional specific metrics to focus on
    
    Returns:
        Dict with:
            - formatted_response: The forecast update analysis
            - forecast_data: Structured forecast data
            - _metadata: Metadata about the operation
    """
    try:
        # Normalize date
        date_str = entities.get("as_of_date", "today")
        if date_str in ("today", None):
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            
        forecast_period = entities.get("forecast_period", "year")
        department = entities.get("department")
        metrics = entities.get("metrics", [])
            
        # TODO: Implement forecast update logic
        
        # Use RAG+LLM for narrative generation
        query = f"Update {forecast_period} financial forecast as of {date_str}"
        if department:
            query += f" for {department} department"
        if metrics:
            metrics_str = ", ".join(metrics)
            query += f" focusing on {metrics_str}"
            
        context = await rag_module.generate_context(query, filter_criteria={"category": "forecasting"})
        system_prompt = "You are a financial assistant specializing in financial forecasting and projection..."
        response = await generate_text(
            prompt=query,
            system_prompt=(system_prompt if context else system_prompt + "\n\nNote: no docs found."),
            context=context
        )
        
        result = {"formatted_response": response, "context_used": bool(context)}
        result["_metadata"] = {"operation": "financial_planning/forecast_update", "success": True}
        return result
    except Exception as e:
        logger.error(f"Error in forecast_update: {e}")
        return {"error": str(e), "_metadata": {"operation": "financial_planning/forecast_update", "success": False}}

async def handle_scenario_analysis(entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform scenario analysis and what-if modeling.
    
    Args:
        entities: Dictionary containing:
            - scenario_type: Type of scenario (best_case, worst_case, most_likely, custom)
            - variables: Variables to adjust in the scenario
            - time_horizon: Time period for the analysis
            - metrics: Metrics to evaluate in the scenario
    
    Returns:
        Dict with:
            - formatted_response: The scenario analysis
            - scenario_data: Structured scenario data
            - _metadata: Metadata about the operation
    """
    try:
        scenario_type = entities.get("scenario_type", "most_likely")
        variables = entities.get("variables", {})
        time_horizon = entities.get("time_horizon", "1 year")
        metrics = entities.get("metrics", ["revenue", "profit", "cash_flow"])
            
        # TODO: Implement scenario analysis logic
        
        # Use RAG+LLM for narrative generation
        query = f"Perform {scenario_type} scenario analysis over {time_horizon} time horizon"
        variables_str = ", ".join([f"{k}: {v}" for k, v in variables.items()])
        if variables:
            query += f" adjusting {variables_str}"
        metrics_str = ", ".join(metrics)
        query += f" analyzing impact on {metrics_str}"
            
        context = await rag_module.generate_context(query, filter_criteria={"category": "scenario_analysis"})
        system_prompt = "You are a financial assistant specializing in financial scenario modeling and analysis..."
        response = await generate_text(
            prompt=query,
            system_prompt=(system_prompt if context else system_prompt + "\n\nNote: no docs found."),
            context=context
        )
        
        result = {"formatted_response": response, "context_used": bool(context)}
        result["_metadata"] = {"operation": "financial_planning/scenario_analysis", "success": True}
        return result
    except Exception as e:
        logger.error(f"Error in scenario_analysis: {e}")
        return {"error": str(e), "_metadata": {"operation": "financial_planning/scenario_analysis", "success": False}}

async def handle_capital_planning(entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plan and analyze capital expenditures and investments.
    
    Args:
        entities: Dictionary containing:
            - timeframe: Planning timeframe (1_year, 3_year, 5_year)
            - budget_amount: Total capital budget
            - categories: Optional categories of capital expenditure
            - prioritization: How to prioritize projects (ROI, strategic, maintenance)
    
    Returns:
        Dict with:
            - formatted_response: The capital planning analysis
            - capital_plan_data: Structured capital plan data
            - _metadata: Metadata about the operation
    """
    try:
        timeframe = entities.get("timeframe", "1_year")
        budget_amount = entities.get("budget_amount")
        categories = entities.get("categories", [])
        prioritization = entities.get("prioritization", "ROI")
            
        # TODO: Implement capital planning logic
        
        # Use RAG+LLM for narrative generation
        query = f"Develop {timeframe} capital expenditure plan"
        if budget_amount:
            query += f" with budget of {budget_amount}"
        if categories:
            categories_str = ", ".join(categories)
            query += f" for {categories_str}"
        query += f" prioritized by {prioritization}"
            
        context = await rag_module.generate_context(query, filter_criteria={"category": "capital_planning"})
        system_prompt = "You are a financial assistant specializing in capital expenditure planning and analysis..."
        response = await generate_text(
            prompt=query,
            system_prompt=(system_prompt if context else system_prompt + "\n\nNote: no docs found."),
            context=context
        )
        
        result = {"formatted_response": response, "context_used": bool(context)}
        result["_metadata"] = {"operation": "financial_planning/capital_planning", "success": True}
        return result
    except Exception as e:
        logger.error(f"Error in capital_planning: {e}")
        return {"error": str(e), "_metadata": {"operation": "financial_planning/capital_planning", "success": False}}

async def handle_financial_target(entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set and track financial targets and KPIs.
    
    Args:
        entities: Dictionary containing:
            - timeframe: Target timeframe (quarter, year, long_term)
            - target_type: Type of target (growth, profitability, efficiency, liquidity)
            - current_value: Current metric value
            - target_value: Target metric value
    
    Returns:
        Dict with:
            - formatted_response: The financial target analysis
            - target_data: Structured target data
            - _metadata: Metadata about the operation
    """
    try:
        timeframe = entities.get("timeframe", "year")
        target_type = entities.get("target_type", "growth")
        current_value = entities.get("current_value")
        target_value = entities.get("target_value")
            
        # TODO: Implement financial target setting logic
        
        # Use RAG+LLM for narrative generation
        query = f"Set {target_type} financial targets for {timeframe} timeframe"
        if current_value is not None and target_value is not None:
            query += f" moving from {current_value} to {target_value}"
            
        context = await rag_module.generate_context(query, filter_criteria={"category": "financial_targets"})
        system_prompt = "You are a financial assistant specializing in setting and tracking financial targets and KPIs..."
        response = await generate_text(
            prompt=query,
            system_prompt=(system_prompt if context else system_prompt + "\n\nNote: no docs found."),
            context=context
        )
        
        result = {"formatted_response": response, "context_used": bool(context)}
        result["_metadata"] = {"operation": "financial_planning/financial_target", "success": True}
        return result
    except Exception as e:
        logger.error(f"Error in financial_target: {e}")
        return {"error": str(e), "_metadata": {"operation": "financial_planning/financial_target", "success": False}}


# New handler for variance analysis
async def handle_variance_analysis(entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare actual vs. budget figures and compute variance analysis.

    Expected entities:
      - metric: e.g. "Operating Expenses"
      - period_actual: e.g. "Q1 2025"
      - period_budget: e.g. "FY 2025 Budget"
    """
    metric = entities.get("metric", "total expenses")
    period_actual = entities.get("period_actual", "current period")
    period_budget = entities.get("period_budget", "budget period")

    query = f"{metric} actuals for {period_actual} vs budget for {period_budget}"
    system_prompt = (
        f"You are a financial analyst. Compute the absolute and percentage variance "
        f"for {metric} comparing {period_actual} against {period_budget}, "
        "and provide commentary on key drivers."
    )
    augmented_prompt = await rag_module.augment_prompt(query, system_prompt)

    analysis = await generate_text(
        prompt=query,
        system_prompt=augmented_prompt,
        temperature=0.2
    )

    import json, re
    m = re.search(r'\{.*\}', analysis, re.DOTALL)
    if m:
        try:
            result = json.loads(m.group(0))
        except json.JSONDecodeError:
            result = {"commentary": analysis.strip()}
    else:
        result = {"commentary": analysis.strip()}

    return {
        "metric": metric,
        "period_actual": period_actual,
        "period_budget": period_budget,
        **result,
        "_metadata": {
            "operation": "financial_planning/variance_analysis",
            "success": not bool(result.get("error"))
        }
    }

__all__ = [
    "handle_budget_preparation",
    "handle_forecast_update",
    "handle_scenario_analysis",
    "handle_capital_planning",
    "handle_financial_target",
    "handle_variance_analysis"
]