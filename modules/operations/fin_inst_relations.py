"""
Financial Institution Relations Operations Module for Finance Accountant Agent

This module handles operations related to financial institution relationships,
including bank relationship management, credit line monitoring, account services,
fee negotiation, and bank covenant tracking.

Features:
- Bank relationship management and contacts
- Credit/line of credit monitoring and reporting
- Banking account services management
- Fee structure analysis and negotiation
- Bank covenant compliance tracking

Dependencies:
- bank_adapters: For banking data access
- rag_module: For retrieving relevant documents
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


async def handle_bank_relations(entities: Dict) -> Dict:
    """
    Manage bank relationships and contact information.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with bank relationship information
    """
    # Extract relevant entities
    bank_id = entities.get("bank_id")
    relation_type = entities.get("relation_type", "summary")

    # Sample bank relationship data (would come from a CRM system in real implementation)
    banks = {
        "BNK001": {
            "name": "Global Trust Bank",
            "relationship_level": "Primary",
            "relationship_manager": "Sarah Johnson",
            "rm_contact": "sjohnson@gtbank.com | (555) 123-4567",
            "services": ["Credit Facilities", "Cash Management", "Treasury", "FX", "Trade Finance"],
            "annual_fees": 120000,
            "active_since": "2015-03-10",
            "last_review": "2024-11-15",
            "notes": "Strategic partner for international operations. Considering expanded credit facilities.",
            "contacts": [
                {"name": "Sarah Johnson", "title": "Relationship Manager", "email": "sjohnson@gtbank.com", "phone": "(555) 123-4567"},
                {"name": "Michael Chen", "title": "Treasury Solutions", "email": "mchen@gtbank.com", "phone": "(555) 123-4589"},
                {"name": "David Wilson", "title": "Credit Officer", "email": "dwilson@gtbank.com", "phone": "(555) 123-4522"},
            ]
        },
        "BNK002": {
            "name": "Continental Financial",
            "relationship_level": "Secondary",
            "relationship_manager": "Robert Martinez",
            "rm_contact": "rmartinez@contfin.com | (555) 987-6543",
            "services": ["Credit Facilities", "Cash Management", "Trade Finance"],
            "annual_fees": 85000,
            "active_since": "2018-07-22",
            "last_review": "2024-09-30",
            "notes": "Regional bank with competitive trade finance rates. Good backup facility provider.",
            "contacts": [
                {"name": "Robert Martinez", "title": "Relationship Manager", "email": "rmartinez@contfin.com", "phone": "(555) 987-6543"},
                {"name": "Jennifer Adams", "title": "Trade Finance Specialist", "email": "jadams@contfin.com", "phone": "(555) 987-6555"},
            ]
        },
        "BNK003": {
            "name": "First National Bank",
            "relationship_level": "Tertiary",
            "relationship_manager": "Amanda Lee",
            "rm_contact": "alee@fnbank.com | (555) 456-7890",
            "services": ["Credit Facilities", "Depository Services"],
            "annual_fees": 35000,
            "active_since": "2020-02-15",
            "last_review": "2024-08-12",
            "notes": "Smaller regional bank with competitive rates for smaller facilities. Considering expansion of services.",
            "contacts": [
                {"name": "Amanda Lee", "title": "Relationship Manager", "email": "alee@fnbank.com", "phone": "(555) 456-7890"},
                {"name": "Thomas Reilly", "title": "Branch Manager", "email": "treilly@fnbank.com", "phone": "(555) 456-7899"},
            ]
        }
    }

    # If specific bank requested
    if bank_id:
        if bank_id not in banks:
            return {
                "error": f"Bank relationship {bank_id} not found",
                "available_banks": list(banks.keys())
            }

        bank = banks[bank_id]

        if relation_type == "contacts":
            # Return just contacts information
            return {
                "bank_id": bank_id,
                "bank_name": bank["name"],
                "contacts": bank["contacts"],
                "message": (
                    f"Contacts for {bank['name']} ({bank_id}):\n\n" +
                    "\n".join([f"{c['name']} - {c['title']}\n{c['email']} | {c['phone']}" for c in bank["contacts"]])
                )
            }
        else:
            # Return full bank relationship data
            return {
                "bank_id": bank_id,
                "bank_name": bank["name"],
                "relationship_level": bank["relationship_level"],
                "relationship_manager": bank["relationship_manager"],
                "rm_contact": bank["rm_contact"],
                "services": bank["services"],
                "annual_fees": bank["annual_fees"],
                "active_since": bank["active_since"],
                "last_review": bank["last_review"],
                "notes": bank["notes"],
                "contacts": bank["contacts"],
                "message": (
                    f"Bank Relationship: {bank['name']} ({bank_id})\n"
                    f"Relationship Level: {bank['relationship_level']}\n"
                    f"Relationship Manager: {bank['relationship_manager']}\n"
                    f"Contact: {bank['rm_contact']}\n"
                    f"Services: {', '.join(bank['services'])}\n"
                    f"Annual Fees: ${bank['annual_fees']:,}\n"
                    f"Active Since: {bank['active_since']}\n"
                    f"Last Review: {bank['last_review']}\n"
                    f"Notes: {bank['notes']}"
                )
            }

    else:
        # Return summary of all bank relationships
        total_fees = sum(bank["annual_fees"] for bank in banks.values())

        bank_summary = []
        for bank_id, bank in banks.items():
            bank_summary.append({
                "bank_id": bank_id,
                "name": bank["name"],
                "relationship_level": bank["relationship_level"],
                "services": bank["services"],
                "annual_fees": bank["annual_fees"],
            })

        return {
            "total_banks": len(banks),
            "total_annual_fees": total_fees,
            "banks": bank_summary,
            "message": (
                f"Bank Relationship Summary:\n"
                f"Total Banking Partners: {len(banks)}\n"
                f"Total Annual Fees: ${total_fees:,}\n\n"
                "Key Relationships:\n" +
                "\n".join([f"- {b['name']} ({b['relationship_level']}): ${b['annual_fees']:,}" for b in bank_summary])
            )
        }


async def handle_line_of_credit(entities: Dict) -> Dict:
    """
    Monitor and report on credit lines and facilities.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with credit line information
    """
    # Extract relevant entities
    facility_id = entities.get("facility_id")
    bank_id = entities.get("bank_id")

    # Get banking adapter to retrieve credit facilities
    banking_adapter = get_banking_adapter()

    try:
        # Get credit facilities data
        facilities = await banking_adapter.get_credit_facilities()

        # If specific facility requested
        if facility_id:
            # Find the requested facility
            facility = next((f for f in facilities if f.get("id") == facility_id), None)

            if not facility:
                return {
                    "error": f"Credit facility {facility_id} not found",
                    "available_facilities": [f.get("id") for f in facilities if "id" in f]
                }

            # Calculate utilization
            if "limit" in facility and facility["limit"] > 0:
                utilization = facility.get("used", 0) / facility["limit"] * 100
            else:
                utilization = 0

            return {
                "facility_id": facility_id,
                "facility_type": facility.get("type", "Unknown"),
                "limit": facility.get("limit", 0),
                "used": facility.get("used", 0),
                "available": facility.get("available", 0),
                "currency": facility.get("currency", "USD"),
                "utilization_percent": utilization,
                "expiry_date": facility.get("expiry_date"),
                "interest_rate": facility.get("interest_rate"),
                "message": (
                    f"Credit Facility: {facility_id}\n"
                    f"Type: {facility.get('type', 'Unknown')}\n"
                    f"Limit: {facility.get('currency', 'USD')} {facility.get('limit', 0):,.0f}\n"
                    f"Used: {facility.get('currency', 'USD')} {facility.get('used', 0):,.0f}\n"
                    f"Available: {facility.get('currency', 'USD')} {facility.get('available', 0):,.0f}\n"
                    f"Utilization: {utilization:.1f}%\n"
                    f"Expiry Date: {facility.get('expiry_date', 'Unknown')}\n"
                    f"Interest Rate: {facility.get('interest_rate', 'Unknown')}"
                )
            }

        # If specific bank requested
        elif bank_id:
            # Sample mapping of facilities to banks (would come from a database in real implementation)
            facility_bank_mapping = {
                "CF001": "BNK001",
                "CF002": "BNK001",
                "LOC001": "BNK002",
                "TL001": "BNK003"
            }

            # Filter facilities by bank
            bank_facilities = [
                f for f in facilities
                if f.get("id") in facility_bank_mapping and facility_bank_mapping[f.get("id")] == bank_id
            ]

            if not bank_facilities:
                return {
                    "error": f"No credit facilities found for bank {bank_id}",
                    "available_banks": list(set(facility_bank_mapping.values()))
                }

            # Calculate total values
            total_limit = sum(f.get("limit", 0) for f in bank_facilities)
            total_used = sum(f.get("used", 0) for f in bank_facilities)
            total_available = sum(f.get("available", 0) for f in bank_facilities)
            overall_utilization = total_used / total_limit * 100 if total_limit > 0 else 0

            # Simple formatting of the facilities
            facility_details = []
            for f in bank_facilities:
                utilization = f.get("used", 0) / f.get("limit", 0) * 100 if f.get("limit", 0) > 0 else 0
                facility_details.append({
                    "facility_id": f.get("id"),
                    "type": f.get("type", "Unknown"),
                    "limit": f.get("limit", 0),
                    "used": f.get("used", 0),
                    "available": f.get("available", 0),
                    "utilization_percent": utilization,
                    "expiry_date": f.get("expiry_date"),
                })

            return {
                "bank_id": bank_id,
                "total_facilities": len(bank_facilities),
                "total_limit": total_limit,
                "total_used": total_used,
                "total_available": total_available,
                "overall_utilization_percent": overall_utilization,
                "currency": "USD",  # Assuming all in same currency for simplicity
                "facilities": facility_details,
                "message": (
                    f"Credit Facilities for Bank {bank_id}:\n"
                    f"Total Facilities: {len(bank_facilities)}\n"
                    f"Total Limit: USD {total_limit:,.0f}\n"
                    f"Total Used: USD {total_used:,.0f}\n"
                    f"Total Available: USD {total_available:,.0f}\n"
                    f"Overall Utilization: {overall_utilization:.1f}%\n\n"
                    "Individual Facilities:\n" +
                    "\n".join([
                        f"- {f.get('id')}: USD {f.get('limit', 0):,.0f} limit, "
                        f"{f.get('used', 0) / f.get('limit', 0) * 100:.1f}% utilized, "
                        f"expires {f.get('expiry_date', 'Unknown')}"
                        for f in bank_facilities
                    ])
                )
            }

        # Return summary of all facilities
        else:
            # Calculate total values
            total_limit = sum(f.get("limit", 0) for f in facilities)
            total_used = sum(f.get("used", 0) for f in facilities)
            total_available = sum(f.get("available", 0) for f in facilities)
            overall_utilization = total_used / total_limit * 100 if total_limit > 0 else 0

            # Categorize facilities by type
            facility_by_type = {}
            for f in facilities:
                f_type = f.get("type", "Unknown")
                if f_type not in facility_by_type:
                    facility_by_type[f_type] = {
                        "count": 0,
                        "limit": 0,
                        "used": 0,
                        "available": 0
                    }

                facility_by_type[f_type]["count"] += 1
                facility_by_type[f_type]["limit"] += f.get("limit", 0)
                facility_by_type[f_type]["used"] += f.get("used", 0)
                facility_by_type[f_type]["available"] += f.get("available", 0)

            return {
                "total_facilities": len(facilities),
                "total_limit": total_limit,
                "total_used": total_used,
                "total_available": total_available,
                "overall_utilization_percent": overall_utilization,
                "currency": "USD",  # Assuming all in same currency for simplicity
                "facilities_by_type": facility_by_type,
                "individual_facilities": [
                    {
                        "id": f.get("id"),
                        "type": f.get("type", "Unknown"),
                        "limit": f.get("limit", 0),
                        "used": f.get("used", 0),
                        "available": f.get("available", 0),
                    } for f in facilities
                ],
                "message": (
                    f"Credit Facilities Summary:\n"
                    f"Total Facilities: {len(facilities)}\n"
                    f"Total Limit: USD {total_limit:,.0f}\n"
                    f"Total Used: USD {total_used:,.0f}\n"
                    f"Total Available: USD {total_available:,.0f}\n"
                    f"Overall Utilization: {overall_utilization:.1f}%\n\n"
                    "By Facility Type:\n" +
                    "\n".join([
                        f"- {f_type}: {data['count']} facilities, "
                        f"USD {data['limit']:,.0f} total limit, "
                        f"{data['used'] / data['limit'] * 100:.1f}% utilized"
                        for f_type, data in facility_by_type.items()
                    ])
                )
            }

    except Exception as e:
        logger.error(f"Error retrieving credit facilities: {str(e)}")
        return {"error": f"Failed to retrieve credit facilities: {str(e)}"}


async def handle_account_services(entities: Dict) -> Dict:
    """
    Manage banking account services and features.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with account services information
    """
    # Extract relevant entities
    account_id = entities.get("account_id")
    service_type = entities.get("service_type")
    bank_id = entities.get("bank_id")

    # Sample account services data (would come from banking systems in real implementation)
    accounts = {
        "1001": {
            "name": "Operating Account",
            "bank_id": "BNK001",
            "type": "checking",
            "currency": "USD",
            "services": [
                {"name": "ACH Payments", "status": "active", "fee": 0.25, "fee_type": "per transaction"},
                {"name": "Wire Transfers", "status": "active", "fee": 15.00, "fee_type": "per transaction"},
                {"name": "Positive Pay", "status": "active", "fee": 75.00, "fee_type": "monthly"},
                {"name": "Check Images", "status": "active", "fee": 0.10, "fee_type": "per item"},
                {"name": "Online Banking", "status": "active", "fee": 0.00, "fee_type": "included"},
            ],
            "monthly_fee": 50.00,
            "fee_waiver_threshold": 250000.00,
            "earnings_credit_rate": 0.0075,  # 0.75%
            "last_review_date": "2024-10-15",
        },
        "1002": {
            "name": "Payroll Account",
            "bank_id": "BNK001",
            "type": "checking",
            "currency": "USD",
            "services": [
                {"name": "ACH Payments", "status": "active", "fee": 0.25, "fee_type": "per transaction"},
                {"name": "Positive Pay", "status": "active", "fee": 50.00, "fee_type": "monthly"},
                {"name": "Online Banking", "status": "active", "fee": 0.00, "fee_type": "included"},
            ],
            "monthly_fee": 25.00,
            "fee_waiver_threshold": 100000.00,
            "earnings_credit_rate": 0.0075,  # 0.75%
            "last_review_date": "2024-10-15",
        },
        "1003": {
            "name": "Tax Reserve",
            "bank_id": "BNK002",
            "type": "savings",
            "currency": "USD",
            "services": [
                {"name": "Online Banking", "status": "active", "fee": 0.00, "fee_type": "included"},
                {"name": "Wire Transfers", "status": "active", "fee": 20.00, "fee_type": "per transaction"},
            ],
            "monthly_fee": 15.00,
            "fee_waiver_threshold": 100000.00,
            "interest_rate": 0.015,  # 1.5%
            "last_review_date": "2024-09-22",
        },
        "1004": {
            "name": "Euro Operations",
            "bank_id": "BNK003",
            "type": "checking",
            "currency": "EUR",
            "services": [
                {"name": "SEPA Transfers", "status": "active", "fee": 0.15, "fee_type": "per transaction"},
                {"name": "International Wires", "status": "active", "fee": 10.00, "fee_type": "per transaction"},
                {"name": "Online Banking", "status": "active", "fee": 10.00, "fee_type": "monthly"},
            ],
            "monthly_fee": 30.00,
            "fee_waiver_threshold": 100000.00,
            "earnings_credit_rate": 0.0050,  # 0.50%
            "last_review_date": "2024-08-10",
        },
    }

    # If specific account requested
    if account_id:
        if account_id not in accounts:
            return {
                "error": f"Account {account_id} not found",
                "available_accounts": list(accounts.keys())
            }

        account = accounts[account_id]

        # If specific service type requested
        if service_type:
            matching_services = [s for s in account["services"] if s["name"].lower() == service_type.lower()]

            if not matching_services:
                return {
                    "error": f"Service {service_type} not found for account {account_id}",
                    "available_services": [s["name"] for s in account["services"]]
                }

            service = matching_services[0]

            return {
                "account_id": account_id,
                "account_name": account["name"],
                "bank_id": account["bank_id"],
                "service_name": service["name"],
                "status": service["status"],
                "fee": service["fee"],
                "fee_type": service["fee_type"],
                "message": (
                    f"Service Details - {service['name']} for {account['name']} ({account_id}):\n"
                    f"Status: {service['status']}\n"
                    f"Fee: {account['currency']} {service['fee']} ({service['fee_type']})"
                )
            }

        # Return all account services
        total_monthly_fixed_fees = account["monthly_fee"] + sum(
            s["fee"] for s in account["services"] if s["fee_type"] == "monthly"
        )

        return {
            "account_id": account_id,
            "account_name": account["name"],
            "bank_id": account["bank_id"],
            "account_type": account["type"],
            "currency": account["currency"],
            "monthly_fee": account["monthly_fee"],
            "fee_waiver_threshold": account["fee_waiver_threshold"],
            "rate": account.get("interest_rate") or account.get("earnings_credit_rate"),
            "rate_type": "interest_rate" if "interest_rate" in account else "earnings_credit_rate",
            "last_review_date": account["last_review_date"],
            "services": account["services"],
            "total_monthly_fixed_fees": total_monthly_fixed_fees,
            "message": (
                f"Account Services for {account['name']} ({account_id}):\n"
                f"Bank: {account['bank_id']}\n"
                f"Account Type: {account['type']}\n"
                f"Currency: {account['currency']}\n"
                f"Monthly Fee: {account['currency']} {account['monthly_fee']:.2f}\n"
                f"Fee Waiver Threshold: {account['currency']} {account['fee_waiver_threshold']:,.2f}\n"
                f"{'Interest Rate' if 'interest_rate' in account else 'Earnings Credit Rate'}: "
                f"{(account.get('interest_rate', 0) or account.get('earnings_credit_rate', 0)) * 100:.3f}%\n"
                f"Total Monthly Fixed Fees: {account['currency']} {total_monthly_fixed_fees:.2f}\n\n"
                "Services:\n" +
                "\n".join([
                    f"- {s['name']}: {s['status']}, {account['currency']} {s['fee']} ({s['fee_type']})"
                    for s in account["services"]
                ])
            )
        }

    # If specific bank requested
    elif bank_id:
        bank_accounts = [a for a_id, a in accounts.items() if a["bank_id"] == bank_id]

        if not bank_accounts:
            return {
                "error": f"No accounts found for bank {bank_id}",
                "available_banks": list(set(a["bank_id"] for a in accounts.values()))
            }

        # Count services by type
        service_counts = {}

        for account in bank_accounts:
            for service in account["services"]:
                if service["name"] not in service_counts:
                    service_counts[service["name"]] = 0
                service_counts[service["name"]] += 1

        return {
            "bank_id": bank_id,
            "account_count": len(bank_accounts),
            "accounts": [
                {
                    "account_id": a_id,
                    "name": accounts[a_id]["name"],
                    "type": accounts[a_id]["type"],
                    "currency": accounts[a_id]["currency"],
                    "service_count": len(accounts[a_id]["services"]),
                } for a_id in accounts if accounts[a_id]["bank_id"] == bank_id
            ],
            "service_counts": service_counts,
            "message": (
                f"Account Services for Bank {bank_id}:\n"
                f"Total Accounts: {len(bank_accounts)}\n\n"
                "Accounts:\n" +
                "\n".join([
                    f"- {a['name']} ({a_id}): {a['type']}, {a['currency']}, {len(a['services'])} services"
                    for a_id, a in accounts.items() if a["bank_id"] == bank_id
                ]) +
                "\n\nServices Used:\n" +
                "\n".join([
                    f"- {service}: {count} accounts"
                    for service, count in service_counts.items()
                ])
            )
        }

    # Return summary of all account services
    else:
        # Summarize services across all accounts
        all_services = set()
        service_usage = {}

        for account in accounts.values():
            for service in account["services"]:
                all_services.add(service["name"])

                if service["name"] not in service_usage:
                    service_usage[service["name"]] = {
                        "count": 0,
                        "banks": set(),
                        "currencies": set(),
                    }

                service_usage[service["name"]]["count"] += 1
                service_usage[service["name"]]["banks"].add(account["bank_id"])
                service_usage[service["name"]]["currencies"].add(account["currency"])

        # Convert sets to lists for JSON serialization
        for service in service_usage:
            service_usage[service]["banks"] = list(service_usage[service]["banks"])
            service_usage[service]["currencies"] = list(service_usage[service]["currencies"])

        # Group accounts by bank
        accounts_by_bank = {}

        for a_id, account in accounts.items():
            bank_id = account["bank_id"]

            if bank_id not in accounts_by_bank:
                accounts_by_bank[bank_id] = {
                    "count": 0,
                    "currencies": set(),
                }

            accounts_by_bank[bank_id]["count"] += 1
            accounts_by_bank[bank_id]["currencies"].add(account["currency"])

        # Convert sets to lists for JSON serialization
        for bank in accounts_by_bank:
            accounts_by_bank[bank]["currencies"] = list(accounts_by_bank[bank]["currencies"])

        return {
            "total_accounts": len(accounts),
            "total_services": len(all_services),
            "service_usage": service_usage,
            "accounts_by_bank": accounts_by_bank,
            "message": (
                f"Account Services Summary:\n"
                f"Total Accounts: {len(accounts)}\n"
                f"Total Unique Services: {len(all_services)}\n\n"
                "Services by Usage:\n" +
                "\n".join([
                    f"- {service}: {data['count']} accounts, "
                    f"{len(data['banks'])} bank(s), "
                    f"{', '.join(data['currencies'])} currencies"
                    for service, data in service_usage.items()
                ]) +
                "\n\nAccounts by Bank:\n" +
                "\n".join([
                    f"- {bank_id}: {data['count']} accounts, "
                    f"{', '.join(data['currencies'])} currencies"
                    for bank_id, data in accounts_by_bank.items()
                ])
            )
        }


async def handle_fee_negotiation(entities: Dict) -> Dict:
    """
    Analyze and provide recommendations for fee negotiations with banks.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with fee analysis and negotiation recommendations
    """
    # Extract relevant entities
    bank_id = entities.get("bank_id")
    fee_type = entities.get("fee_type")

    # Get RAG context for fee benchmarks
    query = f"bank fee benchmarks {fee_type if fee_type else 'all'}"
    context = await rag_module.generate_context(
        query, filter_criteria={"category": "financial_institutions"}
    )

    # Sample banking fee structure data (would come from banking systems in real implementation)
    banks = {
        "BNK001": {
            "name": "Global Trust Bank",
            "annual_fees": 120000,
            "accounts": ["1001", "1002"],
            "service_fees": {
                "account_maintenance": {"fee": 50.00, "basis": "per account monthly", "benchmark": 45.00},
                "ach_payments": {"fee": 0.25, "basis": "per transaction", "benchmark": 0.20},
                "wire_transfers_domestic": {"fee": 15.00, "basis": "per transaction", "benchmark": 12.00},
                "wire_transfers_international": {"fee": 35.00, "basis": "per transaction", "benchmark": 30.00},
                "positive_pay": {"fee": 75.00, "basis": "monthly", "benchmark": 65.00},
                "check_processing": {"fee": 0.10, "basis": "per item", "benchmark": 0.08},
                "online_banking": {"fee": 0.00, "basis": "included", "benchmark": 0.00},
            },
            "volume": {
                "ach_payments": 1200,  # monthly volume
                "wire_transfers_domestic": 45,
                "wire_transfers_international": 15,
                "check_processing": 350,
            },
            "earnings_credit_rate": 0.0075,  # 0.75%
            "average_balances": 3500000,
            "last_negotiation": "2023-11-10",
        },
        "BNK002": {
            "name": "Continental Financial",
            "annual_fees": 85000,
            "accounts": ["1003"],
            "service_fees": {
                "account_maintenance": {"fee": 35.00, "basis": "per account monthly", "benchmark": 40.00},
                "wire_transfers_domestic": {"fee": 20.00, "basis": "per transaction", "benchmark": 12.00},
                "wire_transfers_international": {"fee": 40.00, "basis": "per transaction", "benchmark": 30.00},
                "online_banking": {"fee": 0.00, "basis": "included", "benchmark": 0.00},
            },
            "volume": {
                "wire_transfers_domestic": 20,
                "wire_transfers_international": 8,
            },
            "interest_rate": 0.015,  # 1.5%
            "average_balances": 1200000,
            "last_negotiation": "2024-02-15",
        },
        "BNK003": {
            "name": "First National Bank",
            "annual_fees": 35000,
            "accounts": ["1004"],
            "service_fees": {
                "account_maintenance": {"fee": 30.00, "basis": "per account monthly", "benchmark": 35.00},
                "sepa_transfers": {"fee": 0.15, "basis": "per transaction", "benchmark": 0.18},
                "international_wires": {"fee": 10.00, "basis": "per transaction", "benchmark": 15.00},
                "online_banking": {"fee": 10.00, "basis": "monthly", "benchmark": 12.00},
            },
            "volume": {
                "sepa_transfers": 150,
                "international_wires": 25,
            },
            "earnings_credit_rate": 0.005,  # 0.5%
            "average_balances": 800000,
            "last_negotiation": "2024-05-20",
        }
    }

    # If specific bank requested
    if bank_id:
        if bank_id not in banks:
            return {
                "error": f"Bank {bank_id} not found",
                "available_banks": list(banks.keys())
            }

        bank = banks[bank_id]

        # If specific fee type requested
        if fee_type and fee_type in bank["service_fees"]:
            fee = bank["service_fees"][fee_type]
            volume = bank["volume"].get(fee_type, 0)

            # Calculate annual cost
            annual_cost = 0
            if fee["basis"] == "per transaction":
                annual_cost = fee["fee"] * volume * 12
            elif fee["basis"] == "monthly":
                annual_cost = fee["fee"] * 12
            elif fee["basis"] == "per account monthly":
                annual_cost = fee["fee"] * len(bank["accounts"]) * 12

            # Benchmark comparison
            benchmark_cost = 0
            if fee["basis"] == "per transaction":
                benchmark_cost = fee["benchmark"] * volume * 12
            elif fee["basis"] == "monthly":
                benchmark_cost = fee["benchmark"] * 12
            elif fee["basis"] == "per account monthly":
                benchmark_cost = fee["benchmark"] * len(bank["accounts"]) * 12

            saving_potential = annual_cost - benchmark_cost

            # Get negotiation recommendations
            system_prompt = f"""
You are a bank fee negotiation specialist. Provide recommendations for negotiating the {fee_type} fee with {bank['name']} based on this information:

Current Fee: ${fee['fee']} ({fee['basis']})
Industry Benchmark: ${fee['benchmark']} ({fee['basis']})
Monthly Volume: {volume if volume else 'N/A'}
Annual Cost: ${annual_cost:,.2f}
Benchmark Annual Cost: ${benchmark_cost:,.2f}
Potential Annual Savings: ${saving_potential:,.2f}
Average Balances: ${bank['average_balances']:,.2f}
Last Negotiation: {bank['last_negotiation']}

Provide specific tactics for negotiating this fee, including:
1. Target rate to aim for
2. Key arguments to use
3. Potential trade-offs or concessions
4. Timing considerations
"""

            if context:
                system_prompt += f"\n\nUse this benchmark data in your recommendations:\n{context}"

            negotiation_advice = await generate_text(
                prompt=f"Provide negotiation advice for {fee_type} fee with {bank['name']}",
                system_prompt=system_prompt,
            )

            return {
                "bank_id": bank_id,
                "bank_name": bank["name"],
                "fee_type": fee_type,
                "current_fee": fee["fee"],
                "fee_basis": fee["basis"],
                "benchmark_fee": fee["benchmark"],
                "monthly_volume": volume,
                "annual_cost": annual_cost,
                "benchmark_annual_cost": benchmark_cost,
                "saving_potential": saving_potential,
                "formatted_response": negotiation_advice,
            }

        # Analyze all fees for the bank
        else:
            # Calculate annual costs and saving potential
            annual_costs = {}
            total_annual_cost = 0
            total_benchmark_cost = 0

            for fee_name, fee in bank["service_fees"].items():
                volume = bank["volume"].get(fee_name, 0)

                # Calculate annual cost
                annual_cost = 0
                if fee["basis"] == "per transaction":
                    annual_cost = fee["fee"] * volume * 12
                elif fee["basis"] == "monthly":
                    annual_cost = fee["fee"] * 12
                elif fee["basis"] == "per account monthly":
                    annual_cost = fee["fee"] * len(bank["accounts"]) * 12

                # Benchmark comparison
                benchmark_cost = 0
                if fee["basis"] == "per transaction":
                    benchmark_cost = fee["benchmark"] * volume * 12
                elif fee["basis"] == "monthly":
                    benchmark_cost = fee["benchmark"] * 12
                elif fee["basis"] == "per account monthly":
                    benchmark_cost = fee["benchmark"] * len(bank["accounts"]) * 12

                saving_potential = annual_cost - benchmark_cost

                annual_costs[fee_name] = {
                    "fee": fee["fee"],
                    "basis": fee["basis"],
                    "benchmark": fee["benchmark"],
                    "volume": volume,
                    "annual_cost": annual_cost,
                    "benchmark_cost": benchmark_cost,
                    "saving_potential": saving_potential,
                }

                total_annual_cost += annual_cost
                total_benchmark_cost += benchmark_cost

            total_saving_potential = total_annual_cost - total_benchmark_cost

            # Get comprehensive negotiation recommendations
            system_prompt = f"""
You are a bank fee negotiation specialist. Provide a comprehensive strategy for negotiating fees with {bank['name']} based on this information:

Total Annual Fees: ${total_annual_cost:,.2f}
Benchmark Annual Fees: ${total_benchmark_cost:,.2f}
Total Potential Annual Savings: ${total_saving_potential:,.2f}
Average Balances: ${bank['average_balances']:,.2f}
{'Earnings Credit Rate' if 'earnings_credit_rate' in bank else 'Interest Rate'}: {(bank.get('earnings_credit_rate', 0) or bank.get('interest_rate', 0)) * 100:.2f}%
Last Negotiation: {bank['last_negotiation']}

Fee Details:
"""

            for fee_name, fee_data in annual_costs.items():
                system_prompt += f"""
{fee_name}: ${fee_data['fee']} ({fee_data['basis']})
- Benchmark: ${fee_data['benchmark']}
- Annual Cost: ${fee_data['annual_cost']:,.2f}
- Potential Savings: ${fee_data['saving_potential']:,.2f}
"""

            system_prompt += """

Provide a comprehensive negotiation strategy, including:
1. Overall approach and timing
2. Priority fees to focus on (highest saving potential)
3. Specific tactics for key fee categories
4. Potential package deal considerations
5. Balance and relationship considerations
6. Fallback positions
"""

            if context:
                system_prompt += f"\n\nUse this benchmark data in your strategy:\n{context}"

            negotiation_strategy = await generate_text(
                prompt=f"Provide comprehensive fee negotiation strategy for {bank['name']}",
                system_prompt=system_prompt,
                max_new_tokens=1024,
            )

            return {
                "bank_id": bank_id,
                "bank_name": bank["name"],
                "total_annual_cost": total_annual_cost,
                "total_benchmark_cost": total_benchmark_cost,
                "total_saving_potential": total_saving_potential,
                "fee_details": annual_costs,
                "average_balances": bank["average_balances"],
                "rate": bank.get("earnings_credit_rate") or bank.get("interest_rate"),
                "rate_type": "earnings_credit_rate" if "earnings_credit_rate" in bank else "interest_rate",
                "last_negotiation": bank["last_negotiation"],
                "formatted_response": negotiation_strategy,
            }

    # Compare fees across all banks
    else:
        # Get all fee types across all banks
        all_fee_types = set()
        for bank in banks.values():
            all_fee_types.update(bank["service_fees"].keys())

        # Compare fees across banks
        fee_comparison = {}
        for fee_type in all_fee_types:
            fee_comparison[fee_type] = {}

        for bank_id, bank in banks.items():
            if fee_type in bank["service_fees"]:
                fee_comparison[fee_type][bank_id] = {
                    "fee": bank["service_fees"][fee_type]["fee"],
                    "basis": bank["service_fees"][fee_type]["basis"],
                    "benchmark": bank["service_fees"][fee_type]["benchmark"],
                }

        # Calculate total annual fees for each bank
        bank_annual_fees = {}

        for bank_id, bank in banks.items():
            total_annual_cost = 0
            total_benchmark_cost = 0

            for fee_name, fee in bank["service_fees"].items():
                volume = bank["volume"].get(fee_name, 0)

                # Calculate annual cost
                annual_cost = 0
                if fee["basis"] == "per transaction":
                    annual_cost = fee["fee"] * volume * 12
                elif fee["basis"] == "monthly":
                    annual_cost = fee["fee"] * 12
                elif fee["basis"] == "per account monthly":
                    annual_cost = fee["fee"] * len(bank["accounts"]) * 12

                # Benchmark comparison
                benchmark_cost = 0
                if fee["basis"] == "per transaction":
                    benchmark_cost = fee["benchmark"] * volume * 12
                elif fee["basis"] == "monthly":
                    benchmark_cost = fee["benchmark"] * 12
                elif fee["basis"] == "per account monthly":
                    benchmark_cost = fee["benchmark"] * len(bank["accounts"]) * 12

                total_annual_cost += annual_cost
                total_benchmark_cost += benchmark_cost

            bank_annual_fees[bank_id] = {
                "bank_name": bank["name"],
                "total_annual_cost": total_annual_cost,
                "total_benchmark_cost": total_benchmark_cost,
                "total_saving_potential": total_annual_cost - total_benchmark_cost,
                "last_negotiation": bank["last_negotiation"],
            }

        # Get cross-bank negotiation strategy
        system_prompt = """
You are a bank fee negotiation specialist. Provide a strategic approach for optimizing banking fees across multiple banking relationships based on this comparative data:
"""

        for bank_id, fee_data in bank_annual_fees.items():
            system_prompt += f"""

{banks[bank_id]['name']} ({bank_id}):
- Annual Fees: ${fee_data['total_annual_cost']:,.2f}
- Potential Savings: ${fee_data['total_saving_potential']:,.2f}
- Last Negotiation: {fee_data['last_negotiation']}
"""

        system_prompt += """

Select fee categories for comparison:
"""

        for fee_type in fee_comparison:
            system_prompt += f"\n\n{fee_type}:"
            for bank_id, bank_fee in fee_comparison[fee_type].items():
                system_prompt += f"\n- {banks[bank_id]['name']}: ${bank_fee['fee']} ({bank_fee['basis']}), Benchmark: ${bank_fee['benchmark']}"

        system_prompt += """

Provide a comprehensive strategy for optimizing fees across all banking relationships, including:
1. Which banks to prioritize for negotiation
2. Potential for leveraging competing offers
3. Fee categories with highest optimization potential
4. Relationship considerations and trade-offs
5. Timing strategy for negotiations
"""

        if context:
            system_prompt += f"\n\nUse this benchmark data in your strategy:\n{context}"

        negotiation_strategy = await generate_text(
            prompt="Provide cross-bank fee optimization strategy",
            system_prompt=system_prompt,
            max_new_tokens=1024,
        )

        return {
            "bank_annual_fees": bank_annual_fees,
            "fee_comparison": fee_comparison,
            "formatted_response": negotiation_strategy,
        }


async def handle_bank_covenant(entities: Dict) -> Dict:
    """
    Track and analyze bank covenants compliance.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with covenant compliance information
    """
    # Extract relevant entities
    covenant_id = entities.get("covenant_id")
    bank_id = entities.get("bank_id")
    facility_id = entities.get("facility_id")

    # Sample covenant data (would come from debt management system in real implementation)
    covenants = {
        "COV001": {
            "name": "Debt-to-EBITDA",
            "type": "financial",
            "bank_id": "BNK001",
            "facility_id": "CF001",
            "threshold": 3.5,
            "comparison": "less_than",
            "current_value": 2.8,
            "calculation": "Total Debt / EBITDA (trailing 12 months)",
            "reporting_frequency": "quarterly",
            "last_reported": "2024-09-30",
            "next_due": "2024-12-31",
            "status": "compliant",
            "trending": "stable",
            "historical": [
                {"date": "2023-12-31", "value": 3.1, "status": "compliant"},
                {"date": "2024-03-31", "value": 3.0, "status": "compliant"},
                {"date": "2024-06-30", "value": 2.9, "status": "compliant"},
                {"date": "2024-09-30", "value": 2.8, "status": "compliant"},
            ],
            "cushion": 0.7,  # Difference from threshold
            "cushion_percent": 20.0,  # Percentage of threshold
        },
        "COV002": {
            "name": "Interest Coverage Ratio",
            "type": "financial",
            "bank_id": "BNK001",
            "facility_id": "CF001",
            "threshold": 3.0,
            "comparison": "greater_than",
            "current_value": 4.2,
            "calculation": "EBITDA / Interest Expense (trailing 12 months)",
            "reporting_frequency": "quarterly",
            "last_reported": "2024-09-30",
            "next_due": "2024-12-31",
            "status": "compliant",
            "trending": "improving",
            "historical": [
                {"date": "2023-12-31", "value": 3.5, "status": "compliant"},
                {"date": "2024-03-31", "value": 3.7, "status": "compliant"},
                {"date": "2024-06-30", "value": 4.0, "status": "compliant"},
                {"date": "2024-09-30", "value": 4.2, "status": "compliant"},
            ],
            "cushion": 1.2,
            "cushion_percent": 40.0,
        },
        "COV003": {
            "name": "Fixed Charge Coverage Ratio",
            "type": "financial",
            "bank_id": "BNK002",
            "facility_id": "LOC001",
            "threshold": 1.25,
            "comparison": "greater_than",
            "current_value": 1.3,
            "calculation": "(EBITDA - CapEx) / (Interest + Principal Payments)",
            "reporting_frequency": "quarterly",
            "last_reported": "2024-09-30",
            "next_due": "2024-12-31",
            "status": "compliant",
            "trending": "declining",
            "historical": [
                {"date": "2023-12-31", "value": 1.5, "status": "compliant"},
                {"date": "2024-03-31", "value": 1.45, "status": "compliant"},
                {"date": "2024-06-30", "value": 1.35, "status": "compliant"},
                {"date": "2024-09-30", "value": 1.3, "status": "compliant"},
            ],
            "cushion": 0.05,
            "cushion_percent": 4.0,
        },
        "COV004": {
            "name": "Current Ratio",
            "type": "financial",
            "bank_id": "BNK003",
            "facility_id": "TL001",
            "threshold": 1.2,
            "comparison": "greater_than",
            "current_value": 1.45,
            "calculation": "Current Assets / Current Liabilities",
            "reporting_frequency": "quarterly",
            "last_reported": "2024-09-30",
            "next_due": "2024-12-31",
            "status": "compliant",
            "trending": "stable",
            "historical": [
                {"date": "2023-12-31", "value": 1.42, "status": "compliant"},
                {"date": "2024-03-31", "value": 1.44, "status": "compliant"},
                {"date": "2024-06-30", "value": 1.45, "status": "compliant"},
                {"date": "2024-09-30", "value": 1.45, "status": "compliant"},
            ],
            "cushion": 0.25,
            "cushion_percent": 20.8,
        },
    }

    # If specific covenant requested
    if covenant_id:
        if covenant_id not in covenants:
            return {
                "error": f"Covenant {covenant_id} not found",
                "available_covenants": list(covenants.keys())
            }

        covenant = covenants[covenant_id]

        # Format comparison for readability
        comparison_text = "≤" if covenant["comparison"] == "less_than" else "≥"

        # Format the trend indicator
        trend_indicators = {
            "improving": "↑ Improving",
            "stable": "→ Stable",
            "declining": "↓ Declining"
        }
        trend = trend_indicators.get(covenant["trending"], covenant["trending"])

        # Check if covenant is at risk
        at_risk = False
        if covenant["cushion_percent"] < 10.0:
            at_risk = True

        # Calculate forecast based on trend (simplified)
        forecast = None
        if covenant["trending"] == "improving" or covenant["trending"] == "declining":
            # Calculate average change per period
            historical = covenant["historical"]
            if len(historical) >= 2:
                total_change = historical[-1]["value"] - historical[0]["value"]
                periods = len(historical) - 1
                avg_change_per_period = total_change / periods

                # Project next value
                forecast = covenant["current_value"] + avg_change_per_period

                # Check if forecast would breach covenant
                if covenant["comparison"] == "less_than":
                    forecast_status = "compliant" if forecast < covenant["threshold"] else "breach"
                else:  # greater_than
                    forecast_status = "compliant" if forecast > covenant["threshold"] else "breach"

                # Calculate quarters until breach (simplified)
                quarters_to_breach = None
                if covenant["comparison"] == "less_than" and avg_change_per_period < 0:
                    cushion = covenant["threshold"] - covenant["current_value"]
                    quarters_to_breach = abs(cushion / avg_change_per_period) if avg_change_per_period != 0 else None
                elif covenant["comparison"] == "greater_than" and avg_change_per_period < 0:
                    cushion = covenant["current_value"] - covenant["threshold"]
                    quarters_to_breach = abs(cushion / avg_change_per_period) if avg_change_per_period != 0 else None

        return {
            "covenant_id": covenant_id,
            "name": covenant["name"],
            "type": covenant["type"],
            "bank_id": covenant["bank_id"],
            "facility_id": covenant["facility_id"],
            "threshold": covenant["threshold"],
            "comparison": covenant["comparison"],
            "comparison_text": comparison_text,
            "current_value": covenant["current_value"],
            "calculation": covenant["calculation"],
            "status": covenant["status"],
            "trending": covenant["trending"],
            "trend_indicator": trend,
            "cushion": covenant["cushion"],
            "cushion_percent": covenant["cushion_percent"],
            "last_reported": covenant["last_reported"],
            "next_due": covenant["next_due"],
            "historical": covenant["historical"],
            "at_risk": at_risk,
            "forecast": forecast,
            "forecast_status": forecast_status if forecast is not None else None,
            "quarters_to_breach": quarters_to_breach,
            "message": (
                f"Covenant: {covenant['name']} ({covenant_id})\n"
                f"Requirement: {comparison_text} {covenant['threshold']}\n"
                f"Current Value: {covenant['current_value']}\n"
                f"Status: {covenant['status'].title()} ({trend})\n"
                f"Cushion: {covenant['cushion']} ({covenant['cushion_percent']:.1f}%)\n"
                f"Last Reported: {covenant['last_reported']}\n"
                f"Next Due: {covenant['next_due']}"
            ),
        }

    # If specific bank requested
    elif bank_id:
        bank_covenants = [cov for cov_id, cov in covenants.items() if cov["bank_id"] == bank_id]

        if not bank_covenants:
            return {
                "error": f"No covenants found for bank {bank_id}",
                "available_banks": list(set(cov["bank_id"] for cov in covenants.values()))
            }

        # Analyze covenant status
        at_risk_covenants = [cov for cov in bank_covenants if cov["cushion_percent"] < 10.0]
        compliant_covenants = [cov for cov in bank_covenants if cov["status"] == "compliant"]
        non_compliant_covenants = [cov for cov in bank_covenants if cov["status"] != "compliant"]

        # Get RAG context for covenant management
        query = f"bank covenant management {bank_id}"
        context = await rag_module.generate_context(
            query, filter_criteria={"category": "financial_institutions"}
        )

        # Generate covenant management recommendations
        system_prompt = f"""
You are a financial analyst specializing in bank covenant management. Provide an analysis of covenant compliance for {bank_id} based on this information:

Total Covenants: {len(bank_covenants)}
Compliant: {len(compliant_covenants)}
Non-Compliant: {len(non_compliant_covenants)}
At Risk (<10% cushion): {len(at_risk_covenants)}

Covenant Details:
"""

        for cov in bank_covenants:
            comparison_text = "≤" if cov["comparison"] == "less_than" else "≥"
            system_prompt += f"""

{cov['name']}:
- Requirement: {comparison_text} {cov['threshold']}
- Current Value: {cov['current_value']}
- Status: {cov['status'].title()} ({cov['trending']})
- Cushion: {cov['cushion']} ({cov['cushion_percent']:.1f}%)
- Next Due: {cov['next_due']}
"""

        system_prompt += """

Provide a comprehensive covenant compliance analysis that includes:
1. Overall compliance status and risk assessment
2. Specific recommendations for at-risk covenants
3. Monitoring strategy for upcoming reporting periods
4. Suggested proactive measures to maintain compliance
5. Communication strategy with the bank
"""

        if context:
            system_prompt += f"\n\nUse this context in your analysis:\n{context}"

        covenant_analysis = await generate_text(
            prompt=f"Analyze covenant compliance for bank {bank_id}",
            system_prompt=system_prompt,
        )

        return {
            "bank_id": bank_id,
            "total_covenants": len(bank_covenants),
            "compliant_count": len(compliant_covenants),
            "non_compliant_count": len(non_compliant_covenants),
            "at_risk_count": len(at_risk_covenants),
            "covenants": [
                {
                    "covenant_id": cov_id,
                    "name": covenants[cov_id]["name"],
                    "threshold": covenants[cov_id]["threshold"],
                    "comparison": covenants[cov_id]["comparison"],
                    "current_value": covenants[cov_id]["current_value"],
                    "status": covenants[cov_id]["status"],
                    "trending": covenants[cov_id]["trending"],
                    "cushion_percent": covenants[cov_id]["cushion_percent"],
                    "next_due": covenants[cov_id]["next_due"],
                } for cov_id, cov in covenants.items() if cov["bank_id"] == bank_id
            ],
            "formatted_response": covenant_analysis,
        }

    # If specific facility requested
    elif facility_id:
        facility_covenants = [cov for cov_id, cov in covenants.items() if cov["facility_id"] == facility_id]

        if not facility_covenants:
            return {
                "error": f"No covenants found for facility {facility_id}",
                "available_facilities": list(set(cov["facility_id"] for cov in covenants.values()))
            }

        # Analyze covenant status
        at_risk_covenants = [cov for cov in facility_covenants if cov["cushion_percent"] < 10.0]

        return {
            "facility_id": facility_id,
            "total_covenants": len(facility_covenants),
            "at_risk_count": len(at_risk_covenants),
            "covenants": [
                {
                    "covenant_id": cov_id,
                    "name": covenants[cov_id]["name"],
                    "threshold": covenants[cov_id]["threshold"],
                    "comparison": covenants[cov_id]["comparison"],
                    "current_value": covenants[cov_id]["current_value"],
                    "status": covenants[cov_id]["status"],
                    "trending": covenants[cov_id]["trending"],
                    "cushion_percent": covenants[cov_id]["cushion_percent"],
                } for cov_id, cov in covenants.items() if cov["facility_id"] == facility_id
            ],
            "message": (
                f"Covenant Summary for Facility {facility_id}:\n"
                f"Total Covenants: {len(facility_covenants)}\n"
                f"At Risk Covenants: {len(at_risk_covenants)}\n\n"
                "Covenant Details:\n" +
                "\n".join([
                    f"- {cov['name']}: {'≤' if cov['comparison'] == 'less_than' else '≥'} {cov['threshold']}, "
                    f"Current: {cov['current_value']} ({cov['status']}), "
                    f"Cushion: {cov['cushion_percent']:.1f}%"
                    for cov in facility_covenants
                ])
            ),
        }

    # Return summary of all covenants
    else:
        # Analyze overall covenant status
        at_risk_covenants = [cov_id for cov_id, cov in covenants.items() if cov["cushion_percent"] < 10.0]
        non_compliant_covenants = [cov_id for cov_id, cov in covenants.items() if cov["status"] != "compliant"]

        # Group by bank and facility
        by_bank = {}
        by_facility = {}

        for cov_id, cov in covenants.items():
            bank_id = cov["bank_id"]
            facility_id = cov["facility_id"]

            if bank_id not in by_bank:
                by_bank[bank_id] = []
            by_bank[bank_id].append(cov_id)

            if facility_id not in by_facility:
                by_facility[facility_id] = []
            by_facility[facility_id].append(cov_id)

        return {
            "total_covenants": len(covenants),
            "compliant_count": len(covenants) - len(non_compliant_covenants),
            "non_compliant_count": len(non_compliant_covenants),
            "at_risk_count": len(at_risk_covenants),
            "by_bank": by_bank,
            "by_facility": by_facility,
            "at_risk_covenants": at_risk_covenants,
            "non_compliant_covenants": non_compliant_covenants,
            "covenants_summary": [
                {
                    "covenant_id": cov_id,
                    "name": cov["name"],
                    "bank_id": cov["bank_id"],
                    "facility_id": cov["facility_id"],
                    "status": cov["status"],
                    "trending": cov["trending"],
                    "cushion_percent": cov["cushion_percent"],
                    "next_due": cov["next_due"],
                } for cov_id, cov in covenants.items()
            ],
            "message": (
                f"Covenant Compliance Summary:\n"
                f"Total Covenants: {len(covenants)}\n"
                f"Compliant: {len(covenants) - len(non_compliant_covenants)}\n"
                f"Non-Compliant: {len(non_compliant_covenants)}\n"
                f"At Risk (<10% cushion): {len(at_risk_covenants)}\n\n"
                "Covenants by Bank:\n" +
                "\n".join([f"- {bank}: {len(covs)} covenants" for bank, covs in by_bank.items()]) +
                "\n\nAt Risk Covenants:\n" +
                "\n".join([
                    f"- {covenants[cov_id]['name']} ({cov_id}): {covenants[cov_id]['current_value']} vs. "
                    f"{'≤' if covenants[cov_id]['comparison'] == 'less_than' else '≥'} {covenants[cov_id]['threshold']}, "
                    f"Cushion: {covenants[cov_id]['cushion_percent']:.1f}%"
                    for cov_id in at_risk_covenants
                ]) if at_risk_covenants else "None"
            ),
        }