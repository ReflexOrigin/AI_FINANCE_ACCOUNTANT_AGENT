"""
Investment Management Operations Module for Finance Accountant Agent

This module handles operations related to investment management, including
investment performance analysis, portfolio allocation, investment strategy
development, new investment evaluation, and divestment analysis.

Features:
- Investment performance tracking and analysis
- Portfolio allocation and rebalancing recommendations
- Investment strategy development and evaluation
- New investment opportunity analysis
- Divestment/exit strategy analysis

Dependencies:
- bank_adapters: For financial data access
- rag_module: For retrieving relevant investment documents
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


async def handle_investment_performance(entities: Dict) -> Dict:
    """
    Analyze performance of investment portfolio or specific investments.

    Args:
    entities: Dictionary of entities extracted from user intent

    Returns:
    Dictionary with investment performance analysis
    """
    # Extract relevant entities
    investment_id = entities.get("investment_id")
    time_period = entities.get("time_period", "ytd")
    metrics = entities.get("metrics", ["return", "risk", "sharpe"])

    if isinstance(metrics, str):
        metrics = [metrics]

    # Sample investment portfolio data (would come from investment system in real implementation)
    investments = {
        "INV001": {
            "name": "US Treasury Bonds",
            "type": "fixed_income",
            "initial_investment": 5000000,
            "current_value": 5175000,
            "inception_date": "2022-06-15",
            "currency": "USD",
            "performance": {
                "ytd": 2.5,
                "1y": 3.5,
                "3y": 9.2,
                "5y": 15.8,
            },
            "risk_metrics": {
                "volatility": 3.2,
                "sharpe_ratio": 0.85,
                "max_drawdown": -2.1,
            },
            "benchmarks": {
                "Bloomberg US Agg": {
                    "ytd": 1.8,
                    "1y": 2.9,
                    "3y": 8.1,
                    "5y": 14.2,
                }
            }
        },
        "INV002": {
            "name": "US Equity Fund",
            "type": "equity",
            "initial_investment": 8000000,
            "current_value": 9120000,
            "inception_date": "2021-03-10",
            "currency": "USD",
            "performance": {
                "ytd": 5.8,
                "1y": 14.0,
                "3y": 32.5,
                "5y": None, # Not available
            },
            "risk_metrics": {
                "volatility": 15.8,
                "sharpe_ratio": 0.72,
                "max_drawdown": -12.5,
            },
            "benchmarks": {
                "S&P 500": {
                    "ytd": 6.2,
                    "1y": 12.5,
                    "3y": 35.8,
                    "5y": 65.3,
                }
            }
        },
        "INV003": {
            "name": "Corporate Bond Portfolio",
            "type": "fixed_income",
            "initial_investment": 6500000,
            "current_value": 6825000,
            "inception_date": "2022-09-20",
            "currency": "USD",
            "performance": {
                "ytd": 3.2,
                "1y": 5.0,
                "3y": None, # Not available
                "5y": None, # Not available
            },
            "risk_metrics": {
                "volatility": 5.5,
                "sharpe_ratio": 0.78,
                "max_drawdown": -3.8,
            },
            "benchmarks": {
                "Bloomberg US Corp": {
                    "ytd": 2.9,
                    "1y": 4.2,
                    "3y": None,
                    "5y": None,
                }
            }
        },
        "INV004": {
            "name": "European Equity Fund",
            "type": "equity",
            "initial_investment": 3500000,
            "current_value": 3745000,
            "inception_date": "2023-01-15",
            "currency": "EUR",
            "performance": {
                "ytd": 7.0,
                "1y": None, # Not available yet
                "3y": None,
                "5y": None,
            },
            "risk_metrics": {
                "volatility": 14.2,
                "sharpe_ratio": 0.65,
                "max_drawdown": -8.5,
            },
            "benchmarks": {
                "STOXX Europe 600": {
                    "ytd": 6.5,
                    "1y": None,
                    "3y": None,
                    "5y": None,
                }
            }
        },
    }

    # If specific investment requested
    if investment_id:
        if investment_id not in investments:
            return {
                "error": f"Investment {investment_id} not found",
                "available_investments": list(investments.keys())
            }

        investment = investments[investment_id]

        # Check if data is available for requested time period
        if time_period not in investment["performance"] or investment["performance"][time_period] is None:
            available_periods = [p for p, v in investment["performance"].items() if v is not None]
            return {
                "error": f"Performance data for {time_period} not available for {investment_id}",
                "available_periods": available_periods
            }

        # Calculate absolute return
        initial_value = investment["initial_investment"]
        current_value = investment["current_value"]
        absolute_return = current_value - initial_value
        percent_return = absolute_return / initial_value * 100

        # Get benchmark comparison
        benchmark_name = next(iter(investment["benchmarks"]))
        benchmark_data = investment["benchmarks"][benchmark_name]

        if time_period in benchmark_data and benchmark_data[time_period] is not None:
            benchmark_return = benchmark_data[time_period]
            relative_performance = investment["performance"][time_period] - benchmark_return
        else:
            benchmark_return = None
            relative_performance = None

        # Format response
        result = {
            "investment_id": investment_id,
            "name": investment["name"],
            "type": investment["type"],
            "currency": investment["currency"],
            "initial_investment": initial_value,
            "current_value": current_value,
            "absolute_return": absolute_return,
            "percent_return": percent_return,
            "time_period": time_period,
            "performance": {
                "return": investment["performance"][time_period],
                "benchmark": benchmark_return,
                "relative_performance": relative_performance,
            },
        }

        # Add requested risk metrics
        if "risk" in metrics or "volatility" in metrics:
            result["risk_metrics"] = {"volatility": investment["risk_metrics"]["volatility"]}

        if "sharpe" in metrics:
            result["risk_metrics"] = result.get("risk_metrics", {})
            result["risk_metrics"]["sharpe_ratio"] = investment["risk_metrics"]["sharpe_ratio"]

        if "drawdown" in metrics:
            result["risk_metrics"] = result.get("risk_metrics", {})
            result["risk_metrics"]["max_drawdown"] = investment["risk_metrics"]["max_drawdown"]

        # Generate message
        message = (
            f"Performance Analysis for {investment['name']} ({investment_id}):\n"
            f"Initial Investment: {investment['currency']} {initial_value:,.0f}\n"
            f"Current Value: {investment['currency']} {current_value:,.0f}\n"
            f"Absolute Return: {investment['currency']} {absolute_return:,.0f} ({percent_return:.2f}%)\n"
            f"{time_period.upper()} Return: {investment['performance'][time_period]:.2f}%"
        )

        if benchmark_return is not None:
            message += f"\nBenchmark ({benchmark_name}): {benchmark_return:.2f}%"
            message += f"\nRelative Performance: {relative_performance:+.2f}%"

        if "risk_metrics" in result:
            message += "\n\nRisk Metrics:"
            if "volatility" in result["risk_metrics"]:
                message += f"\nVolatility: {investment['risk_metrics']['volatility']:.2f}%"
            if "sharpe_ratio" in result["risk_metrics"]:
                message += f"\nSharpe Ratio: {investment['risk_metrics']['sharpe_ratio']:.2f}"
            if "max_drawdown" in result["risk_metrics"]:
                message += f"\nMaximum Drawdown: {investment['risk_metrics']['max_drawdown']:.2f}%"

        result["message"] = message
        return result

    else:
        # Portfolio-level analysis
        portfolio_value = sum(inv["current_value"] for inv in investments.values())
        initial_investment = sum(inv["initial_investment"] for inv in investments.values())
        absolute_return = portfolio_value - initial_investment
        percent_return = absolute_return / initial_investment * 100 if initial_investment > 0 else 0

        # Calculate weighted performance for requested time period
        weighted_performance = 0
        total_weight = 0

        for inv in investments.values():
            if time_period in inv["performance"] and inv["performance"][time_period] is not None:
                weight = inv["current_value"] / portfolio_value if portfolio_value > 0 else 0
                weighted_performance += inv["performance"][time_period] * weight
                total_weight += weight

        if total_weight > 0:
            portfolio_performance = weighted_performance / total_weight
        else:
            portfolio_performance = None

        # Format response
        result = {
            "portfolio_summary": {
                "total_value": portfolio_value,
                "initial_investment": initial_investment,
                "absolute_return": absolute_return,
                "percent_return": percent_return,
                "time_period": time_period,
                "performance": portfolio_performance,
            },
            "investments": {},
        }

        for inv_id, inv in investments.items():
            result["investments"][inv_id] = {
                "name": inv["name"],
                "type": inv["type"],
                "current_value": inv["current_value"],
                "allocation": inv["current_value"] / portfolio_value * 100 if portfolio_value > 0 else 0,
            }

            if time_period in inv["performance"] and inv["performance"][time_period] is not None:
                result["investments"][inv_id]["performance"] = inv["performance"][time_period]

        # Generate message
        message = (
            f"Portfolio Performance Summary ({time_period.upper()}):\n"
            f"Total Portfolio Value: ${portfolio_value:,.0f}\n"
            f"Initial Investment: ${initial_investment:,.0f}\n"
            f"Absolute Return: ${absolute_return:,.0f} ({percent_return:.2f}%)\n"
        )

        if portfolio_performance is not None:
            message += f"{time_period.upper()} Return: {portfolio_performance:.2f}%\n"

        message += "\nAllocation:"
        for inv_id, inv_data in result["investments"].items():
            message += f"\n- {inv_data['name']}: ${inv_data['current_value']:,.0f} ({inv_data['allocation']:.1f}%)"
            if "performance" in inv_data:
                message += f", {time_period.upper()}: {inv_data['performance']:.2f}%"

        result["message"] = message
        return result


async def handle_portfolio_allocation(entities: Dict) -> Dict:
    """
    Analyze portfolio allocation and provide rebalancing recommendations.

    Args:
    entities: Dictionary of entities extracted from user intent

    Returns:
    Dictionary with portfolio allocation analysis and recommendations
    """
    # Extract relevant entities
    allocation_type = entities.get("allocation_type", "current")
    risk_profile = entities.get("risk_profile")

    # Sample current portfolio allocation
    current_allocation = {
        "equity": {
            "value": 11500000,
            "percent": 55.0,
            "components": {
                "us_large_cap": {"value": 4800000, "percent": 23.0},
                "us_small_cap": {"value": 2100000, "percent": 10.0},
                "international_developed": {"value": 3200000, "percent": 15.3},
                "emerging_markets": {"value": 1400000, "percent": 6.7},
            }
        },
        "fixed_income": {
            "value": 7500000,
            "percent": 35.9,
            "components": {
                "government": {"value": 3200000, "percent": 15.3},
                "corporate": {"value": 2800000, "percent": 13.4},
                "high_yield": {"value": 1500000, "percent": 7.2},
            }
        },
        "alternatives": {
            "value": 1200000,
            "percent": 5.7,
            "components": {
                "real_estate": {"value": 800000, "percent": 3.8},
                "commodities": {"value": 400000, "percent": 1.9},
            }
        },
        "cash": {
            "value": 700000,
            "percent": 3.4,
            "components": {
                "money_market": {"value": 500000, "percent": 2.4},
                "bank_deposits": {"value": 200000, "percent": 1.0},
            }
        }
    }

    # Sample target allocations based on risk profile
    target_allocations = {
        "conservative": {
            "equity": 30.0,
            "fixed_income": 60.0,
            "alternatives": 5.0,
            "cash": 5.0,
        },
        "moderate": {
            "equity": 50.0,
            "fixed_income": 40.0,
            "alternatives": 7.0,
            "cash": 3.0,
        },
        "aggressive": {
            "equity": 70.0,
            "fixed_income": 20.0,
            "alternatives": 8.0,
            "cash": 2.0,
        },
        "custom": {
            "equity": 55.0,
            "fixed_income": 35.0,
            "alternatives": 7.0,
            "cash": 3.0,
        }
    }

    # Calculate total portfolio value
    total_value = sum(asset_class["value"] for asset_class in current_allocation.values())

    if allocation_type == "current":
        # Return current allocation
        return {
            "total_value": total_value,
            "allocation_type": "current",
            "allocation": current_allocation,
            "message": (
                f"Current Portfolio Allocation:\n"
                f"Total Value: ${total_value:,.0f}\n\n"
                f"Equity: ${current_allocation['equity']['value']:,.0f} ({current_allocation['equity']['percent']:.1f}%)\n"
                f"Fixed Income: ${current_allocation['fixed_income']['value']:,.0f} ({current_allocation['fixed_income']['percent']:.1f}%)\n"
                f"Alternatives: ${current_allocation['alternatives']['value']:,.0f} ({current_allocation['alternatives']['percent']:.1f}%)\n"
                f"Cash: ${current_allocation['cash']['value']:,.0f} ({current_allocation['cash']['percent']:.1f}%)"
            ),
        }

    elif allocation_type == "target":
        # Return target allocation based on risk profile
        if not risk_profile or risk_profile not in target_allocations:
            risk_profile = "moderate" # Default to moderate if not specified or invalid

        target = target_allocations[risk_profile]

        return {
            "total_value": total_value,
            "allocation_type": "target",
            "risk_profile": risk_profile,
            "current_allocation": {
                "equity": current_allocation["equity"]["percent"],
                "fixed_income": current_allocation["fixed_income"]["percent"],
                "alternatives": current_allocation["alternatives"]["percent"],
                "cash": current_allocation["cash"]["percent"],
            },
            "target_allocation": target,
            "message": (
                f"Target Portfolio Allocation ({risk_profile.title()}):\n"
                f"Equity: {target['equity']:.1f}%\n"
                f"Fixed Income: {target['fixed_income']:.1f}%\n"
                f"Alternatives: {target['alternatives']:.1f}%\n"
                f"Cash: {target['cash']:.1f}%"
            ),
        }

    elif allocation_type == "rebalance":
        # Calculate rebalancing recommendations
        if not risk_profile or risk_profile not in target_allocations:
            risk_profile = "moderate" # Default to moderate if not specified or invalid

        target = target_allocations[risk_profile]
        rebalance_actions = []

        for asset_class, target_pct in target.items():
            current_pct = current_allocation[asset_class]["percent"]
            deviation = current_pct - target_pct

            if abs(deviation) >= 1.0: # Only rebalance if deviation is significant
                current_value = current_allocation[asset_class]["value"]
                target_value = (target_pct / 100) * total_value
                adjustment = target_value - current_value

                action = "buy" if adjustment > 0 else "sell"
                rebalance_actions.append({
                    "asset_class": asset_class,
                    "action": action,
                    "amount": abs(adjustment),
                    "current_percent": current_pct,
                    "target_percent": target_pct,
                    "deviation": deviation,
                })

        # Get RAG context for rebalancing strategy
        query = f"portfolio rebalancing {risk_profile} risk profile"
        context = await rag_module.generate_context(
            query, filter_criteria={"category": "investment_management"}
        )

        # Generate rebalancing recommendations using LLM
        system_prompt = f"""
        You are an investment portfolio manager. Provide rebalancing recommendations for a portfolio with the following characteristics:

        Current Allocation:
        - Equity: {current_allocation['equity']['percent']:.1f}% (${current_allocation['equity']['value']:,.0f})
        - Fixed Income: {current_allocation['fixed_income']['percent']:.1f}% (${current_allocation['fixed_income']['value']:,.0f})
        - Alternatives: {current_allocation['alternatives']['percent']:.1f}% (${current_allocation['alternatives']['value']:,.0f})
        - Cash: {current_allocation['cash']['percent']:.1f}% (${current_allocation['cash']['value']:,.0f})

        Target Allocation ({risk_profile.title()} risk profile):
        - Equity: {target['equity']:.1f}%
        - Fixed Income: {target['fixed_income']:.1f}%
        - Alternatives: {target['alternatives']:.1f}%
        - Cash: {target['cash']:.1f}%

        Total Portfolio Value: ${total_value:,.0f}

        Provide specific, actionable rebalancing recommendations including:
        1. Which asset classes to buy or sell
        2. Approximate amounts for each adjustment
        3. Suggested implementation approach (e.g., gradual vs. immediate)
        4. Tax considerations (if applicable)
        5. Market timing considerations

        Aim for practical advice that balances the need to align with target allocation against transaction costs and market impact.
        """

        if context:
            system_prompt += f"\n\nAdditional context for your recommendations:\n{context}"

        rebalancing_advice = await generate_text(
            prompt=f"Provide rebalancing recommendations for a {risk_profile} risk profile portfolio",
            system_prompt=system_prompt,
        )

        return {
            "total_value": total_value,
            "allocation_type": "rebalance",
            "risk_profile": risk_profile,
            "current_allocation": {
                "equity": current_allocation["equity"]["percent"],
                "fixed_income": current_allocation["fixed_income"]["percent"],
                "alternatives": current_allocation["alternatives"]["percent"],
                "cash": current_allocation["cash"]["percent"],
            },
            "target_allocation": target,
            "rebalance_actions": rebalance_actions,
            "formatted_response": rebalancing_advice,
        }

    else:
        return {
            "error": f"Unsupported allocation type: {allocation_type}",
            "supported_types": ["current", "target", "rebalance"]
        }


async def handle_investment_strategy(entities: Dict) -> Dict:
    """
    Develop or analyze investment strategy.

    Args:
    entities: Dictionary of entities extracted from user intent

    Returns:
    Dictionary with investment strategy information
    """
    # Extract relevant entities
    strategy_type = entities.get("strategy_type", "develop")
    time_horizon = entities.get("time_horizon", "medium")
    objectives = entities.get("objectives", "growth")

    if isinstance(objectives, str):
        objectives = [objectives]

    # Get RAG context for investment strategy
    query = f"investment strategy {objectives} {time_horizon} term"
    context = await rag_module.generate_context(
        query, filter_criteria={"category": "investment_management"}
    )

    # Map time horizon to years
    horizon_mapping = {
        "short": "1-3 years",
        "medium": "3-7 years",
        "long": "7+ years",
    }

    time_horizon_years = horizon_mapping.get(time_horizon, "3-7 years")

    # Generate investment strategy using LLM
    system_prompt = f"""
    You are an investment strategy advisor. Provide a {strategy_type} investment strategy with these parameters:

    Time Horizon: {time_horizon_years}
    Primary Objectives: {', '.join(objectives)}

    Your response should include:
    1. Overall strategy summary
    2. Recommended asset allocation
    3. Key investment themes and sectors
    4. Risk management considerations
    5. Implementation guidelines

    Structure your advice in a clear, actionable manner that balances the stated objectives with appropriate risk management.
    """

    if context:
        system_prompt += f"\n\nUse this context in developing your strategy:\n{context}"

    strategy = await generate_text(
        prompt=f"{strategy_type} investment strategy for {time_horizon} term with {', '.join(objectives)} objectives",
        system_prompt=system_prompt,
        max_new_tokens=1024,
    )

    return {
        "formatted_response": strategy,
        "strategy_type": strategy_type,
        "time_horizon": time_horizon,
        "objectives": objectives,
        "context_used": bool(context),
    }


async def handle_new_investment(entities: Dict) -> Dict:
    """
    Evaluate potential new investment opportunities.

    Args:
    entities: Dictionary of entities extracted from user intent

    Returns:
    Dictionary with investment evaluation
    """
    # Extract relevant entities
    investment_type = entities.get("investment_type", "equity")
    amount = entities.get("amount", 1000000)
    criteria = entities.get("criteria", ["return", "risk", "liquidity"])

    if isinstance(criteria, str):
        criteria = [criteria]

    # Get RAG context for investment opportunities
    query = f"new {investment_type} investment opportunities {' '.join(criteria)}"
    context = await rag_module.generate_context(
        query, filter_criteria={"category": "investment_management"}
    )

    # Generate investment opportunities analysis using LLM
    system_prompt = f"""
    You are an investment advisor evaluating new investment opportunities. Provide an analysis of potential {investment_type} investments with these parameters:

    Investment Amount: ${amount:,.0f}
    Key Criteria: {', '.join(criteria)}

    Your analysis should include:
    1. Overview of current market conditions for {investment_type}
    2. 3-5 specific investment options that meet the criteria
    3. Pros and cons of each option
    4. Expected returns and risks
    5. Implementation recommendations

    For each investment option, provide specific details on expected returns, risks, liquidity, and other relevant factors based on the criteria.
    """

    if context:
        system_prompt += f"\n\nUse this context in your analysis:\n{context}"

    analysis = await generate_text(
        prompt=f"Evaluate {investment_type} investment opportunities for ${amount:,.0f} based on {', '.join(criteria)}",
        system_prompt=system_prompt,
        max_new_tokens=1024,
    )

    return {
        "formatted_response": analysis,
        "investment_type": investment_type,
        "amount": amount,
        "criteria": criteria,
        "context_used": bool(context),
    }


async def handle_divest(entities: Dict) -> Dict:
    """
    Analyze divestment options and exit strategies.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with divestment analysis
    """
    # Extract relevant entities
    investment_id = entities.get("investment_id")
    reason = entities.get("reason", "reallocation")
    timeline = entities.get("timeline", "gradual")

    # Sample investment data (would come from investment system in real implementation)
    investments = {
        "INV001": {
            "name": "US Treasury Bonds",
            "type": "fixed_income",
            "current_value": 5175000,
            "unrealized_gain": 175000,
            "cost_basis": 5000000,
            "liquidity": "high",
            "holding_period": "3 years",
            "currency": "USD",
        },
        "INV002": {
            "name": "US Equity Fund",
            "type": "equity",
            "current_value": 9120000,
            "unrealized_gain": 1120000,
            "cost_basis": 8000000,
            "liquidity": "high",
            "holding_period": "4 years",
            "currency": "USD",
        },
        "INV003": {
            "name": "Corporate Bond Portfolio",
            "type": "fixed_income",
            "current_value": 6825000,
            "unrealized_gain": 325000,
            "cost_basis": 6500000,
            "liquidity": "medium",
            "holding_period": "2.5 years",
            "currency": "USD",
        },
        "INV004": {
            "name": "European Equity Fund",
            "type": "equity",
            "current_value": 3745000,
            "unrealized_gain": 245000,
            "cost_basis": 3500000,
            "liquidity": "high",
            "holding_period": "1.3 years",
            "currency": "EUR",
        },
    }

    if investment_id:
        # Check if investment exists
        if investment_id not in investments:
            return {
                "error": f"Investment {investment_id} not found",
                "available_investments": list(investments.keys())
            }

        investment = investments[investment_id]

        # Get RAG context for divestment strategy
        query = f"divest {investment['type']} investment {reason} {timeline}"
        context = await rag_module.generate_context(
            query, filter_criteria={"category": "investment_management"}
        )

        # Generate divestment analysis using LLM
        system_prompt = f"""
        You are an investment advisor analyzing divestment options. Provide a divestment strategy for the following investment:

        Investment: {investment['name']} ({investment_id})
        Type: {investment['type']}
        Current Value: {investment['currency']} {investment['current_value']:,.0f}
        Cost Basis: {investment['currency']} {investment['cost_basis']:,.0f}
        Unrealized Gain/Loss: {investment['currency']} {investment['unrealized_gain']:,.0f}
        Holding Period: {investment['holding_period']}
        Liquidity: {investment['liquidity']}

        Divestment Reason: {reason}
        Preferred Timeline: {timeline}

        Your analysis should include:
        1. Overall divestment recommendation
        2. Optimal timing and execution strategy
        3. Tax implications
        4. Market considerations
        5. Alternative approaches to consider

        Provide specific, actionable advice that balances the need to divest with maximizing returns and minimizing costs.
        """

        if context:
            system_prompt += f"\n\nUse this context in your analysis:\n{context}"

        divestment_analysis = await generate_text(
            prompt=f"Analyze divestment options for {investment['name']} due to {reason} with {timeline} timeline",
            system_prompt=system_prompt,
        )

        return {
            "formatted_response": divestment_analysis,
            "investment_id": investment_id,
            "investment_name": investment["name"],
            "investment_type": investment["type"],
            "current_value": investment["current_value"],
            "unrealized_gain": investment["unrealized_gain"],
            "reason": reason,
            "timeline": timeline,
            "context_used": bool(context),
        }

    else:
        # Portfolio-level divestment strategy
        # Get RAG context for portfolio divestment strategy
        query = f"portfolio divestment strategy {reason} {timeline}"
        context = await rag_module.generate_context(
            query, filter_criteria={"category": "investment_management"}
        )

        # Calculate total portfolio value and gains
        total_value = sum(inv["current_value"] for inv in investments.values())
        total_cost_basis = sum(inv["cost_basis"] for inv in investments.values())
        total_unrealized_gain = sum(inv["unrealized_gain"] for inv in investments.values())

        # Generate portfolio divestment analysis using LLM
        system_prompt = f"""
        You are an investment advisor analyzing portfolio divestment options. Provide a divestment strategy for the following portfolio:

        Total Portfolio Value: ${total_value:,.0f}
        Total Cost Basis: ${total_cost_basis:,.0f}
        Total Unrealized Gain/Loss: ${total_unrealized_gain:,.0f}

        Portfolio Composition:
        """

        for inv_id, inv in investments.items():
            system_prompt += f"- {inv['name']} ({inv_id}): {inv['currency']} {inv['current_value']:,.0f}, {inv['liquidity']} liquidity\n"

        system_prompt += f"""

        Divestment Reason: {reason}
        Preferred Timeline: {timeline}

        Your analysis should include:
        1. Overall divestment approach
        2. Prioritization of assets to divest
        3. Execution strategy and timeline
        4. Tax optimization considerations
        5. Market impact management

        Provide specific, actionable advice that balances the need to divest with maximizing returns and minimizing costs.
        """

        if context:
            system_prompt += f"\n\nUse this context in your analysis:\n{context}"

        portfolio_divestment_analysis = await generate_text(
            prompt=f"Analyze portfolio divestment options due to {reason} with {timeline} timeline",
            system_prompt=system_prompt,
            max_new_tokens=1024,
        )

        return {
            "formatted_response": portfolio_divestment_analysis,
            "total_value": total_value,
            "total_cost_basis": total_cost_basis,
            "total_unrealized_gain": total_unrealized_gain,
            "reason": reason,
            "timeline": timeline,
            "investments": {inv_id: {"name": inv["name"], "value": inv["current_value"], "type": inv["type"]} for inv_id, inv in investments.items()},
            "context_used": bool(context),
        }