"""
Accounting Operations Module for Finance Accountant Agent

This module handles operations related to accounting, including general ledger
queries, journal entry generation, account reconciliation, financial statement
analysis, and accounting policy information.

Features:
- General ledger account queries and analysis
- Journal entry creation and validation
- Account reconciliation assistance
- Financial statement generation and analysis
- Accounting policy and procedure information

Dependencies:
- rag_module: For retrieving relevant accounting documents
- llm_module: For analysis and recommendations
"""

import asyncio
import datetime
import logging
import random
from typing import Dict, List, Optional

from modules.llm_module import generate_text
from modules.rag_module import rag_module

from config.settings import settings

logger = logging.getLogger(__name__)


async def handle_general_ledger(entities: Dict) -> Dict:
    """
    Query general ledger accounts and provide analysis.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with general ledger information
    """
    # Extract relevant entities
    account_number = entities.get("account_number")
    account_name = entities.get("account_name")
    date_range = entities.get("date_range", "current_month")
    analysis_type = entities.get("analysis_type", "balance")

    # Parse date range
    today = datetime.datetime.now()
    if date_range == "current_month":
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
    elif date_range == "previous_month":
        if today.month == 1:
            start_date = today.replace(year=today.year-1, month=12, day=1).strftime("%Y-%m-%d")
            end_date = today.replace(year=today.year-1, month=12, day=31).strftime("%Y-%m-%d")
        else:
            start_date = today.replace(month=today.month-1, day=1).strftime("%Y-%m-%d")
            last_day = (today.replace(day=1) - datetime.timedelta(days=1)).day
            end_date = today.replace(month=today.month-1, day=last_day).strftime("%Y-%m-%d")
    elif date_range == "ytd":
        start_date = today.replace(month=1, day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
    elif date_range == "quarter":
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_month, day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
    else:
        # Try to parse custom date range in format "yyyy-mm-dd:yyyy-mm-dd"
        try:
            start_date, end_date = date_range.split(":")
        except:
            # Default to current month
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")

    # Sample GL account data (would come from accounting system in real implementation)
    gl_accounts = {
        "1000": {"name": "Cash", "type": "asset", "category": "current_asset", "balance": 1250000, "normal_balance": "debit"},
        "1010": {"name": "Accounts Receivable", "type": "asset", "category": "current_asset", "balance": 850000, "normal_balance": "debit"},
        "1020": {"name": "Inventory", "type": "asset", "category": "current_asset", "balance": 750000, "normal_balance": "debit"},
        "1500": {"name": "Property, Plant and Equipment", "type": "asset", "category": "non_current_asset", "balance": 3500000, "normal_balance": "debit"},
        "1510": {"name": "Accumulated Depreciation", "type": "asset", "category": "non_current_asset", "balance": -850000, "normal_balance": "credit"},
        "2000": {"name": "Accounts Payable", "type": "liability", "category": "current_liability", "balance": 650000, "normal_balance": "credit"},
        "2010": {"name": "Accrued Expenses", "type": "liability", "category": "current_liability", "balance": 225000, "normal_balance": "credit"},
        "2500": {"name": "Long-term Debt", "type": "liability", "category": "non_current_liability", "balance": 2500000, "normal_balance": "credit"},
        "3000": {"name": "Common Stock", "type": "equity", "category": "equity", "balance": 1000000, "normal_balance": "credit"},
        "3010": {"name": "Retained Earnings", "type": "equity", "category": "equity", "balance": 1875000, "normal_balance": "credit"},
        "4000": {"name": "Revenue", "type": "revenue", "category": "income", "balance": 3500000, "normal_balance": "credit"},
        "5000": {"name": "Cost of Goods Sold", "type": "expense", "category": "expense", "balance": 2100000, "normal_balance": "debit"},
        "6000": {"name": "Operating Expenses", "type": "expense", "category": "expense", "balance": 950000, "normal_balance": "debit"},
        "6010": {"name": "Salaries and Wages", "type": "expense", "category": "expense", "balance": 750000, "normal_balance": "debit"},
        "7000": {"name": "Interest Expense", "type": "expense", "category": "expense", "balance": 125000, "normal_balance": "debit"},
        "8000": {"name": "Tax Expense", "type": "expense", "category": "expense", "balance": 150000, "normal_balance": "debit"},
    }

    # Generate sample transactions for the specified account
    def generate_sample_transactions(account, start_date_str, end_date_str, count=10):
        transactions = []
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        days_range = (end_date - start_date).days + 1

        for i in range(count):
            # Random date within range
            random_days = random.randint(0, days_range - 1)
            tx_date = (start_date + datetime.timedelta(days=random_days)).strftime("%Y-%m-%d")

            # Random amount (scaled based on account balance)
            scale_factor = abs(account["balance"]) * 0.05
            amount = random.uniform(scale_factor * 0.2, scale_factor * 1.5)

            # Determine debit/credit based on normal balance
            if random.random() < 0.7:  # 70% chance of normal balance type
                if account["normal_balance"] == "debit":
                    debit_amount = amount
                    credit_amount = 0
                else:
                    debit_amount = 0
                    credit_amount = amount
            else:
                if account["normal_balance"] == "debit":
                    debit_amount = 0
                    credit_amount = amount
                else:
                    debit_amount = amount
                    credit_amount = 0

            # Generate description
            descriptions = {
                "1000": ["Deposit", "Transfer", "Payment", "Withdrawal", "Bank Fee"],
                "1010": ["Customer Payment", "Invoice", "Credit Memo", "Write-off"],
                "1020": ["Inventory Purchase", "Inventory Adjustment", "Cost Adjustment"],
                "1500": ["Asset Purchase", "Asset Improvement", "Asset Disposal"],
                "1510": ["Monthly Depreciation", "Asset Retirement", "Depreciation Adjustment"],
                "2000": ["Vendor Payment", "Invoice", "Credit from Vendor"],
                "2010": ["Accrual Entry", "Accrual Reversal", "Monthly Accrual"],
                "2500": ["Loan Payment", "Interest Accrual", "Debt Issuance"],
                "3000": ["Stock Issuance", "Capital Contribution"],
                "3010": ["Net Income Allocation", "Dividend Payment", "Prior Year Adjustment"],
                "4000": ["Sales", "Service Revenue", "Product Revenue", "Discount"],
                "5000": ["Inventory Cost", "Direct Labor", "Purchase"],
                "6000": ["Rent", "Utilities", "Insurance", "Miscellaneous"],
                "6010": ["Payroll", "Bonus", "Commission", "Benefits"],
                "7000": ["Interest Payment", "Interest Accrual"],
                "8000": ["Tax Payment", "Tax Accrual", "Tax Adjustment"],
            }

            description = random.choice(descriptions.get(account_number, ["Transaction"]))

            # Generate reference and journal entry number
            je_number = f"JE-{random.randint(10000, 99999)}"
            reference = f"REF-{random.randint(1000, 9999)}"

            transactions.append({
                "date": tx_date,
                "je_number": je_number,
                "reference": reference,
                "description": description,
                "debit": debit_amount,
                "credit": credit_amount,
                "running_balance": 0,  # Will be calculated later
            })

        # Sort by date
        transactions.sort(key=lambda x: x["date"])

        # Calculate running balance
        running_balance = account["balance"] - sum(tx["debit"] for tx in transactions) + sum(tx["credit"] for tx in transactions)

        for tx in reversed(transactions):
            tx["running_balance"] = running_balance
            if account["normal_balance"] == "debit":
                running_balance = running_balance - tx["debit"] + tx["credit"]
            else:
                running_balance = running_balance + tx["debit"] - tx["credit"]

        return transactions

    # If specific account requested by number
    if account_number:
        if account_number not in gl_accounts:
            return {
                "error": f"Account {account_number} not found",
                "available_accounts": [f"{num}: {account['name']}" for num, account in gl_accounts.items()]
            }

        account = gl_accounts[account_number]

        # Generate sample transactions
        transactions = generate_sample_transactions(account, start_date, end_date)

        # Calculate period activity
        period_debits = sum(tx["debit"] for tx in transactions)
        period_credits = sum(tx["credit"] for tx in transactions)
        period_net = period_debits - period_credits if account["normal_balance"] == "debit" else period_credits - period_debits

        # Get context from RAG for analysis
        if analysis_type != "balance":
            query = f"general ledger {account['name']} {analysis_type} analysis"
            context = await rag_module.generate_context(
                query, filter_criteria={"category": "accounting"}
            )

            # Generate account analysis using LLM
            system_prompt = f"""
            You are a financial accountant analyzing a general ledger account. Provide a {analysis_type} analysis for this account:

            Account: {account_number} - {account['name']}
            Type: {account['type'].title()}
            Category: {account['category'].replace('_', ' ').title()}
            Normal Balance: {account['normal_balance'].title()}

            Period: {start_date} to {end_date}
            Beginning Balance: ${account['balance'] - period_net:,.2f}
            Ending Balance: ${account['balance']:,.2f}
            Period Activity: ${period_net:,.2f} ({period_debits:,.2f} debits, {period_credits:,.2f} credits)

            Notable Transactions:
            """

            # Add largest transactions
            top_transactions = sorted(transactions, key=lambda x: max(x["debit"], x["credit"]), reverse=True)[:3]
            for tx in top_transactions:
                amount = tx["debit"] if tx["debit"] > 0 else tx["credit"]
                system_prompt += f"- {tx['date']}: {tx['description']} for ${amount:,.2f}\n"

            system_prompt += f"""

            Provide a detailed {analysis_type} analysis of this account, including:
            1. Key trends and patterns in the account activity
            2. Potential issues or anomalies to investigate
            3. Recommendations for further analysis or actions
            4. Context within overall financial statements

            Focus on actionable insights that would be valuable for financial reporting and decision-making.
            """

            if context:
                system_prompt += f"\n\nAdditional relevant context:\n{context}"

            analysis = await generate_text(
                prompt=f"Provide {analysis_type} analysis for {account['name']} (Account {account_number})",
                system_prompt=system_prompt,
            )

            return {
                "account_number": account_number,
                "account_name": account["name"],
                "account_type": account["type"],
                "account_category": account["category"],
                "normal_balance": account["normal_balance"],
                "balance": account["balance"],
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date,
                },
                "period_activity": {
                    "debits": period_debits,
                    "credits": period_credits,
                    "net": period_net,
                },
                "transactions": transactions,
                "analysis_type": analysis_type,
                "analysis": analysis,
            }

        # Return account details and transactions
        return {
            "account_number": account_number,
            "account_name": account["name"],
            "account_type": account["type"],
            "account_category": account["category"],
            "normal_balance": account["normal_balance"],
            "balance": account["balance"],
            "date_range": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "period_activity": {
                "debits": period_debits,
                "credits": period_credits,
                "net": period_net,
            },
            "transactions": transactions,
            "message": (
                f"General Ledger Account: {account_number} - {account['name']}\n"
                f"Type: {account['type'].title()}, Category: {account['category'].replace('_', ' ').title()}\n"
                f"Normal Balance: {account['normal_balance'].title()}\n\n"
                f"Date Range: {start_date} to {end_date}\n"
                f"Beginning Balance: ${account['balance'] - period_net:,.2f}\n"
                f"Period Activity: ${period_net:,.2f} ({period_debits:,.2f} debits, {period_credits:,.2f} credits)\n"
                f"Ending Balance: ${account['balance']:,.2f}\n\n"
                "Recent Transactions:\n" +
                "\n".join([
                    f"- {tx['date']}: {tx['description']}, "
                    f"{'Debit' if tx['debit'] > 0 else 'Credit'} ${max(tx['debit'], tx['credit']):,.2f}, "
                    f"Balance: ${tx['running_balance']:,.2f}"
                    for tx in transactions[:5]
                ])
            ),
        }

    # If specific account requested by name
    elif account_name:
        matching_accounts = {num: acct for num, acct in gl_accounts.items() if account_name.lower() in acct["name"].lower()}

        if not matching_accounts:
            return {
                "error": f"No accounts found matching '{account_name}'",
                "available_accounts": [f"{num}: {account['name']}" for num, account in gl_accounts.items()]
            }

        if len(matching_accounts) == 1:
            # Exactly one match, get the account number
            account_number = next(iter(matching_accounts.keys()))
            # Recursively call with the account number
            return await handle_general_ledger({
                "account_number": account_number,
                "date_range": date_range,
                "analysis_type": analysis_type,
            })

        # Multiple matches, return list of matching accounts
        return {
            "matching_accounts": [
                {
                    "account_number": num,
                    "account_name": acct["name"],
                    "account_type": acct["type"],
                    "balance": acct["balance"],
                } for num, acct in matching_accounts.items()
            ],
            "message": (
                f"Multiple accounts found matching '{account_name}':\n" +
                "\n".join([
                    f"- {num}: {acct['name']} (${acct['balance']:,.2f})"
                    for num, acct in matching_accounts.items()
                ])
            ),
        }

    # Return summary of all accounts
    else:
        # Group accounts by type
        accounts_by_type = {}
        for num, acct in gl_accounts.items():
            acct_type = acct["type"]
            if acct_type not in accounts_by_type:
                accounts_by_type[acct_type] = []

            accounts_by_type[acct_type].append({
                "account_number": num,
                "name": acct["name"],
                "balance": acct["balance"],
            })

        # Calculate totals by type
        totals_by_type = {
            acct_type: sum(acct["balance"] for acct in accts)
            for acct_type, accts in accounts_by_type.items()
        }

        # Calculate overall totals
        total_assets = sum(acct["balance"] for acct in gl_accounts.values() if acct["type"] == "asset")
        total_liabilities = sum(acct["balance"] for acct in gl_accounts.values() if acct["type"] == "liability")
        total_equity = sum(acct["balance"] for acct in gl_accounts.values() if acct["type"] == "equity")
        total_revenue = sum(acct["balance"] for acct in gl_accounts.values() if acct["type"] == "revenue")
        total_expenses = sum(acct["balance"] for acct in gl_accounts.values() if acct["type"] == "expense")
        net_income = total_revenue - total_expenses

        return {
            "date_range": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "accounts_by_type": accounts_by_type,
            "totals_by_type": totals_by_type,
            "summary": {
                "total_assets": total_assets,
                "total_liabilities": total_liabilities,
                "total_equity": total_equity,
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_income": net_income,
            },
            "message": (
                f"General Ledger Summary as of {end_date}:\n\n"
                f"Assets: ${total_assets:,.2f}\n"
                f"Liabilities: ${total_liabilities:,.2f}\n"
                f"Equity: ${total_equity:,.2f}\n"
                f"Revenue: ${total_revenue:,.2f}\n"
                f"Expenses: ${total_expenses:,.2f}\n"
                f"Net Income: ${net_income:,.2f}\n\n"
                "Top Accounts by Type:\n" +
                "\n".join([
                    f"{acct_type.title()}: ${totals_by_type[acct_type]:,.2f}"
                    for acct_type in sorted(totals_by_type.keys())
                ])
            ),
        }


async def handle_journal_entry(entities: Dict) -> Dict:
    """
    Create or analyze journal entries.

    Args:
        entities: Dictionary of entities extracted from user intent

    Returns:
        Dictionary with journal entry information
    """
    # Extract relevant entities
    je_number = entities.get("je_number")
    entry_type = entities.get("entry_type")
    amount = entities.get("amount")
    description = entities.get("description", "")

    # Sample GL account data for validation
    gl_accounts = {
        "1000": {"name": "Cash", "type": "asset", "normal_balance": "debit"},
        "1010": {"name": "Accounts Receivable", "type": "asset", "normal_balance": "debit"},
        "1020": {"name": "Inventory", "type": "asset", "normal_balance": "debit"},
        "1500": {"name": "Property, Plant and Equipment", "type": "asset", "normal_balance": "debit"},
        "1510": {"name": "Accumulated Depreciation", "type": "asset", "normal_balance": "credit"},
        "2000": {"name": "Accounts Payable", "type": "liability", "normal_balance": "credit"},
        "2010": {"name": "Accrued Expenses", "type": "liability", "normal_balance": "credit"},
        "2500": {"name": "Long-term Debt", "type": "liability", "normal_balance": "credit"},
        "3000": {"name": "Common Stock", "type": "equity", "normal_balance": "credit"},
        "3010": {"name": "Retained Earnings", "type": "equity", "normal_balance": "credit"},
        "4000": {"name": "Revenue", "type": "revenue", "normal_balance": "credit"},
        "5000": {"name": "Cost of Goods Sold", "type": "expense", "normal_balance": "debit"},
        "6000": {"name": "Operating Expenses", "type": "expense", "normal_balance": "debit"},
        "6010": {"name": "Salaries and Wages", "type": "expense", "normal_balance": "debit"},
        "7000": {"name": "Interest Expense", "type": "expense", "normal_balance": "debit"},
        "8000": {"name": "Tax Expense", "type": "expense", "normal_balance": "debit"},
    }

    # Sample journal entries
    journal_entries = {
        "JE-20250415-001": {
            "date": "2025-04-15",
            "description": "Monthly depreciation entry",
            "status": "posted",
            "lines": [
                {"account": "6000", "description": "Depreciation expense", "debit": 15000, "credit": 0},
                {"account": "1510", "description": "Accumulated depreciation", "debit": 0, "credit": 15000},
            ],
            "created_by": "System",
            "approved_by": "John Doe",
            "created_at": "2025-04-15T08:00:00",
        },
        "JE-20250414-001": {
            "date": "2025-04-14",
            "description": "Cash receipt from customer",
            "status": "posted",
            "lines": [
                {"account": "1000", "description": "Cash deposit", "debit": 50000, "credit": 0},
                {"account": "1010", "description": "Customer payment", "debit": 0, "credit": 50000},
            ],
            "created_by": "Jane Smith",
            "approved_by": "John Doe",
            "created_at": "2025-04-14T10:15:00",
        },
        "JE-20250413-001": {
            "date": "2025-04-13",
            "description": "Vendor payment",
            "status": "posted",
            "lines": [
                {"account": "2000", "description": "Accounts payable", "debit": 35000, "credit": 0},
                {"account": "1000", "description": "Cash payment", "debit": 0, "credit": 35000},
            ],
            "created_by": "Jane Smith",
            "approved_by": "John Doe",
            "created_at": "2025-04-13T14:30:00",
        },
    }

    # If specific journal entry requested
    if je_number:
        if je_number not in journal_entries:
            return {
                "error": f"Journal entry {je_number} not found",
                "available_entries": list(journal_entries.keys())
            }

        je = journal_entries[je_number]

        # Calculate totals
        total_debits = sum(line["debit"] for line in je["lines"])
        total_credits = sum(line["credit"] for line in je["lines"])

        return {
            "je_number": je_number,
            "date": je["date"],
            "description": je["description"],
            "status": je["status"],
            "lines": [
                {
                    "account_number": line["account"],
                    "account_name": gl_accounts[line["account"]]["name"],
                    "description": line["description"],
                    "debit": line["debit"],
                    "credit": line["credit"],
                } for line in je["lines"]
            ],
            "total_debits": total_debits,
            "total_credits": total_credits,
            "balanced": total_debits == total_credits,
            "metadata": {
                "created_by": je["created_by"],
                "approved_by": je["approved_by"],
                "created_at": je["created_at"],
            },
            "message": (
                f"Journal Entry: {je_number}\n"
                f"Date: {je['date']}\n"
                f"Description: {je['description']}\n"
                f"Status: {je['status'].title()}\n\n"
                "Lines:\n" +
                "\n".join([
                    f"- {line['account']} ({gl_accounts[line['account']]['name']}): "
                    f"{'Debit' if line['debit'] > 0 else 'Credit'} ${max(line['debit'], line['credit']):,.2f}"
                    for line in je["lines"]
                ]) +
                f"\n\nTotal Debits: ${total_debits:,.2f}\n"
                f"Total Credits: ${total_credits:,.2f}\n"
                f"Balanced: {'Yes' if total_debits == total_credits else 'No'}"
            ),
        }

    # Create a new journal entry based on entry type
    elif entry_type:
        # Get RAG context for journal entry
        query = f"journal entry template {entry_type}"
        context = await rag_module.generate_context(
            query, filter_criteria={"category": "accounting"}
        )

        # Generate journal entry using LLM
        system_prompt = f"""
        You are an accounting expert creating a journal entry. Provide a properly formatted journal entry for a {entry_type} transaction.

        Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}

        Available accounts:
        """

        for acct_num, acct in gl_accounts.items():
            system_prompt += f"- {acct_num}: {acct['name']} ({acct['type'].title()}, Normal Balance: {acct['normal_balance'].title()})\n"

        if amount:
            system_prompt += f"\nAmount: ${amount:,.2f}"

        if description:
            system_prompt += f"\nDescription: {description}"

        system_prompt += """

        Provide a complete journal entry template including:
        1. Journal entry description
        2. Debit and credit lines with appropriate accounts
        3. Line descriptions
        4. Brief explanation of the accounting treatment

        Format your response like this:

        Description: [Brief description of the entry]

        Account entries:
        - Debit: [Account Number] ([Account Name]) $[Amount]
          Description: [Line description]
        - Credit: [Account Number] ([Account Name]) $[Amount]
          Description: [Line description]
        [Additional lines as needed]

        Explanation:
        [Brief explanation of the accounting treatment]
        """

        if context:
            system_prompt += f"\n\nAdditional relevant accounting context:\n{context}"

        je_template = await generate_text(
            prompt=f"Create journal entry template for {entry_type} transaction",
            system_prompt=system_prompt,
        )

        # Create a placeholder JE number
        new_je_number = f"JE-{datetime.datetime.now().strftime('%Y%m%d')}-NEW"

        return {
            "entry_type": entry_type,
            "template_je_number": new_je_number,
            "template": je_template,
        }

    # Return recent journal entries
    else:
        # Sort entries by date (descending)
        sorted_entries = sorted(
            journal_entries.items(),
            key=lambda x: x[1]["date"],
            reverse=True
        )

        entries_summary = []
        for je_number, je in sorted_entries:
            total_debits = sum(line["debit"] for line in je["lines"])

            entries_summary.append({
                "je_number": je_number,
                "date": je["date"],
                "description": je["description"],
                "amount": total_debits,  # Using debits as the amount
                "status": je["status"],
                "line_count": len(je["lines"]),
            })

        return {
            "recent_entries": entries_summary,
            "message": (
                "Recent Journal Entries:\n\n" +
                "\n".join([
                    f"{entry['date']} - {entry['je_number']}: {entry['description']} (${entry['amount']:,.2f})"
                    for entry in entries_summary
                ])
            ),
        }


async def handle_account_reconciliation(entities: Dict) -> Dict:
    """
    Assist with account reconciliation processes.

    Args:
    entities: Dictionary of entities extracted from user intent

    Returns:
    Dictionary with reconciliation information
    """
    # Extract relevant entities
    account_number = entities.get("account_number")
    account_name = entities.get("account_name")
    reconciliation_date = entities.get("date", datetime.datetime.now().strftime("%Y-%m-%d"))
    reconciliation_type = entities.get("reconciliation_type", "bank")

    # Sample reconciliation data (would come from accounting system in real implementation)
    reconciliations = {
        "1000": {  # Cash
            "account_name": "Cash",
            "type": "bank",
            "as_of_date": "2025-03-31",
            "gl_balance": 1250000,
            "bank_balance": 1275000,
            "reconciled_balance": 1250000,
            "unreconciled_items": [
                {"date": "2025-03-30", "description": "Check #12345", "amount": -15000, "status": "outstanding"},
                {"date": "2025-03-31", "description": "Deposit in transit", "amount": 40000, "status": "in_transit"},
                {"date": "2025-03-29", "description": "Bank fee", "amount": -50, "status": "unrecorded"},
            ],
            "status": "in_progress",
            "last_reconciled": "2025-02-28",
        },
        "1010": {  # Accounts Receivable
            "account_name": "Accounts Receivable",
            "type": "subledger",
            "as_of_date": "2025-03-31",
            "gl_balance": 850000,
            "subledger_balance": 852500,
            "reconciled_balance": 850000,
            "unreconciled_items": [
                {"date": "2025-03-31", "description": "Customer payment not posted", "amount": -2500, "status": "timing"},
            ],
            "status": "complete",
            "last_reconciled": "2025-02-28",
        },
        "1020": {  # Inventory
            "account_name": "Inventory",
            "type": "physical",
            "as_of_date": "2025-03-31",
            "gl_balance": 750000,
            "physical_count": 758000,
            "reconciled_balance": 750000,
            "unreconciled_items": [
                {"date": "2025-03-31", "description": "Goods in transit", "amount": -5000, "status": "timing"},
                {"date": "2025-03-30", "description": "Count discrepancy", "amount": 3000, "status": "unexplained"},
            ],
            "status": "in_progress",
            "last_reconciled": "2025-02-28",
        },
        "2000": {  # Accounts Payable
            "account_name": "Accounts Payable",
            "type": "subledger",
            "as_of_date": "2025-03-31",
            "gl_balance": 650000,
            "subledger_balance": 647500,
            "reconciled_balance": 650000,
            "unreconciled_items": [
                {"date": "2025-03-31", "description": "Vendor invoice not entered", "amount": 2500, "status": "timing"},
            ],
            "status": "complete",
            "last_reconciled": "2025-02-28",
        },
    }

    # If specific account requested by number
    if account_number:
        if account_number not in reconciliations:
            return {
                "error": f"Reconciliation for account {account_number} not found",
                "available_accounts": list(reconciliations.keys())
            }

        reconciliation = reconciliations[account_number]

        # Calculate statistics
        total_unreconciled = sum(item["amount"] for item in reconciliation["unreconciled_items"])
        abs_diff = abs(reconciliation["gl_balance"] - reconciliation[f"{reconciliation['type']}_balance"])

        # Get context from RAG for reconciliation guidance
        query = f"{reconciliation['type']} reconciliation {reconciliation['account_name']}"
        context = await rag_module.generate_context(
            query, filter_criteria={"category": "accounting"}
        )

        # Generate reconciliation guidance using LLM
        system_prompt = f"""
        You are an accounting reconciliation specialist. Provide guidance for reconciling this account:

        Account: {account_number} - {reconciliation['account_name']}
        Reconciliation Type: {reconciliation['type'].replace('_', ' ').title()}
        As of Date: {reconciliation['as_of_date']}

        GL Balance: ${reconciliation['gl_balance']:,.2f}
        {reconciliation['type'].title()} Balance: ${reconciliation[f"{reconciliation['type']}_balance"]:,.2f}
        Difference: ${reconciliation['gl_balance'] - reconciliation[f"{reconciliation['type']}_balance"]:,.2f}

        Unreconciled Items:
        """

        for item in reconciliation["unreconciled_items"]:
            system_prompt += f"- {item['date']}: {item['description']}, ${item['amount']:,.2f} ({item['status']})\n"

        system_prompt += f"""

        Current Status: {reconciliation['status'].replace('_', ' ').title()}
        Last Reconciled: {reconciliation['last_reconciled']}

        Provide detailed guidance for completing this reconciliation, including:
        1. Assessment of current reconciliation status
        2. Recommendations for addressing unreconciled items
        3. Step-by-step process to complete the reconciliation
        4. Best practices for this type of reconciliation
        5. Any potential red flags or issues to investigate

        Focus on practical, actionable advice that would help an accountant complete this reconciliation accurately and efficiently.
        """

        if context:
            system_prompt += f"\n\nAdditional relevant context:\n{context}"

        guidance = await generate_text(
            prompt=f"Provide guidance for reconciling {reconciliation['account_name']} account",
            system_prompt=system_prompt,
        )

        return {
            "account_number": account_number,
            "account_name": reconciliation["account_name"],
            "reconciliation_type": reconciliation["type"],
            "as_of_date": reconciliation["as_of_date"],
            "gl_balance": reconciliation["gl_balance"],
            "comparison_balance": reconciliation[f"{reconciliation['type']}_balance"],
            "difference": reconciliation["gl_balance"] - reconciliation[f"{reconciliation['type']}_balance"],
            "reconciled_balance": reconciliation["reconciled_balance"],
            "unreconciled_items": reconciliation["unreconciled_items"],
            "total_unreconciled": total_unreconciled,
            "status": reconciliation["status"],
            "last_reconciled": reconciliation["last_reconciled"],
            "guidance": guidance,
        }

    # If specific account requested by name
    elif account_name:
        matching_accounts = {num: recon for num, recon in reconciliations.items() if account_name.lower() in recon["account_name"].lower()}

        if not matching_accounts:
            return {
                "error": f"No reconciliations found matching '{account_name}'",
                "available_accounts": [f"{num}: {recon['account_name']}" for num, recon in reconciliations.items()]
            }

        if len(matching_accounts) == 1:
            # Exactly one match, get the account number
            account_number = next(iter(matching_accounts.keys()))
            # Recursively call with the account number
            return await handle_account_reconciliation({
                "account_number": account_number,
                "date": reconciliation_date,
                "reconciliation_type": reconciliation_type,
            })

        # Multiple matches, return list of matching accounts
        return {
            "matching_accounts": [
                {
                    "account_number": num,
                    "account_name": recon["account_name"],
                    "reconciliation_type": recon["type"],
                    "status": recon["status"],
                } for num, recon in matching_accounts.items()
            ],
            "message": (
                f"Multiple reconciliations found matching '{account_name}':\n" +
                "\n".join([
                    f"- {num}: {recon['account_name']} ({recon['type']} reconciliation, {recon['status']})"
                    for num, recon in matching_accounts.items()
                ])
            ),
        }

    # Return summary of all reconciliations
    else:
        # Filter by reconciliation type if specified
        filtered_reconciliations = reconciliations
        if reconciliation_type != "all":
            filtered_reconciliations = {
                num: recon for num, recon in reconciliations.items()
                if recon["type"] == reconciliation_type
            }

        # Calculate statistics
        complete_count = sum(1 for recon in filtered_reconciliations.values() if recon["status"] == "complete")
        in_progress_count = sum(1 for recon in filtered_reconciliations.values() if recon["status"] == "in_progress")
        not_started_count = sum(1 for recon in filtered_reconciliations.values() if recon["status"] == "not_started")

        return {
            "reconciliation_type": reconciliation_type,
            "as_of_date": reconciliation_date,
            "statistics": {
                "total": len(filtered_reconciliations),
                "complete": complete_count,
                "in_progress": in_progress_count,
                "not_started": not_started_count,
                "completion_percentage": complete_count / len(filtered_reconciliations) * 100 if filtered_reconciliations else 0,
            },
            "reconciliations": [
                {
                    "account_number": num,
                    "account_name": recon["account_name"],
                    "type": recon["type"],
                    "status": recon["status"],
                    "gl_balance": recon["gl_balance"],
                    "comparison_balance": recon[f"{recon['type']}_balance"],
                    "difference": recon["gl_balance"] - recon[f"{recon['type']}_balance"],
                    "unreconciled_count": len(recon["unreconciled_items"]),
                } for num, recon in filtered_reconciliations.items()
            ],
            "message": (
                f"Reconciliation Summary as of {reconciliation_date}:\n"
                f"Total Reconciliations: {len(filtered_reconciliations)}\n"
                f"Complete: {complete_count}\n"
                f"In Progress: {in_progress_count}\n"
                f"Not Started: {not_started_count}\n"
                f"Completion Percentage: {complete_count / len(filtered_reconciliations) * 100 if filtered_reconciliations else 0:.1f}%\n\n"
                "Reconciliations:\n" +
                "\n".join([
                    f"- {num}: {recon['account_name']} ({recon['status'].replace('_', ' ').title()}), "
                    f"Diff: ${recon['gl_balance'] - recon[f'{recon['type']}_balance']:,.2f}"
                    for num, recon in filtered_reconciliations.items()
                ])
            ),
        }


async def handle_financial_statement(entities: Dict) -> Dict:
    """
    Generate or analyze financial statements.

    Args:
    entities: Dictionary of entities extracted from user intent

    Returns:
    Dictionary with financial statement information
    """
    # Extract relevant entities
    statement_type = entities.get("statement_type", "balance_sheet")
    time_period = entities.get("time_period", "current")
    comparison = entities.get("comparison", False)
    analysis_type = entities.get("analysis_type", "overview")

    # Sample financial statement data (would come from accounting system in real implementation)
    financial_data = {
        "balance_sheet": {
            "current": {
                "date": "2025-03-31",
                "assets": {
                    "current_assets": {
                        "cash": 1250000,
                        "accounts_receivable": 850000,
                        "inventory": 750000,
                        "prepaid_expenses": 125000,
                        "total_current_assets": 2975000,
                    },
                    "non_current_assets": {
                        "property_plant_equipment": 3500000,
                        "accumulated_depreciation": -850000,
                        "intangible_assets": 750000,
                        "investments": 1200000,
                        "total_non_current_assets": 4600000,
                    },
                    "total_assets": 7575000,
                },
                "liabilities_equity": {
                    "current_liabilities": {
                        "accounts_payable": 650000,
                        "accrued_expenses": 225000,
                        "short_term_debt": 300000,
                        "current_portion_long_term_debt": 250000,
                        "total_current_liabilities": 1425000,
                    },
                    "non_current_liabilities": {
                        "long_term_debt": 2250000,
                        "deferred_tax_liabilities": 150000,
                        "total_non_current_liabilities": 2400000,
                    },
                    "equity": {
                        "common_stock": 1000000,
                        "retained_earnings": 2750000,
                        "total_equity": 3750000,
                    },
                    "total_liabilities_equity": 7575000,
                },
            },
            "previous": {
                "date": "2024-12-31",
                "assets": {
                    "current_assets": {
                        "cash": 1175000,
                        "accounts_receivable": 825000,
                        "inventory": 725000,
                        "prepaid_expenses": 110000,
                        "total_current_assets": 2835000,
                    },
                    "non_current_assets": {
                        "property_plant_equipment": 3450000,
                        "accumulated_depreciation": -800000,
                        "intangible_assets": 775000,
                        "investments": 1150000,
                        "total_non_current_assets": 4575000,
                    },
                    "total_assets": 7410000,
                },
                "liabilities_equity": {
                    "current_liabilities": {
                        "accounts_payable": 675000,
                        "accrued_expenses": 200000,
                        "short_term_debt": 350000,
                        "current_portion_long_term_debt": 250000,
                        "total_current_liabilities": 1475000,
                    },
                    "non_current_liabilities": {
                        "long_term_debt": 2350000,
                        "deferred_tax_liabilities": 135000,
                        "total_non_current_liabilities": 2485000,
                    },
                    "equity": {
                        "common_stock": 1000000,
                        "retained_earnings": 2450000,
                        "total_equity": 3450000,
                    },
                    "total_liabilities_equity": 7410000,
                },
            },
        },
        "income_statement": {
            "current": {
                "period": "Q1 2025",
                "revenue": {
                    "product_revenue": 2200000,
                    "service_revenue": 1300000,
                    "total_revenue": 3500000,
                },
                "cost_of_sales": {
                    "product_costs": 1350000,
                    "service_costs": 750000,
                    "total_cost_of_sales": 2100000,
                },
                "gross_profit": 1400000,
                "operating_expenses": {
                    "salaries_wages": 750000,
                    "rent": 95000,
                    "utilities": 45000,
                    "depreciation": 50000,
                    "other_expenses": 60000,
                    "total_operating_expenses": 950000,
                },
                "operating_income": 450000,
                "other_income_expense": {
                    "interest_expense": 125000,
                    "interest_income": 35000,
                    "total_other_income_expense": -90000,
                },
                "income_before_tax": 360000,
                "tax_expense": 90000,
                "net_income": 270000,
            },
            "previous": {
                "period": "Q1 2024",
                "revenue": {
                    "product_revenue": 2050000,
                    "service_revenue": 1150000,
                    "total_revenue": 3200000,
                },
                "cost_of_sales": {
                    "product_costs": 1280000,
                    "service_costs": 670000,
                    "total_cost_of_sales": 1950000,
                },
                "gross_profit": 1250000,
                "operating_expenses": {
                    "salaries_wages": 690000,
                    "rent": 90000,
                    "utilities": 40000,
                    "depreciation": 45000,
                    "other_expenses": 55000,
                    "total_operating_expenses": 880000,
                },
                "operating_income": 370000,
                "other_income_expense": {
                    "interest_expense": 130000,
                    "interest_income": 25000,
                    "total_other_income_expense": -105000,
                },
                "income_before_tax": 265000,
                "tax_expense": 66250,
                "net_income": 198750,
            },
        },
        "cash_flow_statement": {
            "current": {
                "period": "Q1 2025",
                "operating_activities": {
                    "net_income": 270000,
                    "adjustments": {
                        "depreciation": 50000,
                        "changes_in_working_capital": {
                            "accounts_receivable": -25000,
                            "inventory": -25000,
                            "prepaid_expenses": -15000,
                            "accounts_payable": -25000,
                            "accrued_expenses": 25000,
                        },
                        "total_adjustments": 10000,
                    },
                    "net_cash_from_operating": 280000,
                },
                "investing_activities": {
                    "capital_expenditures": -100000,
                    "investments": -50000,
                    "net_cash_from_investing": -150000,
                },
                "financing_activities": {
                    "debt_repayments": -100000,
                    "dividends_paid": 0,
                    "net_cash_from_financing": -100000,
                },
                "net_change_in_cash": 30000,
                "beginning_cash": 1220000,
                "ending_cash": 1250000,
            },
            "previous": {
                "period": "Q1 2024",
                "operating_activities": {
                    "net_income": 198750,
                    "adjustments": {
                        "depreciation": 45000,
                        "changes_in_working_capital": {
                            "accounts_receivable": -30000,
                            "inventory": -20000,
                            "prepaid_expenses": -5000,
                            "accounts_payable": 15000,
                            "accrued_expenses": 10000,
                        },
                        "total_adjustments": 15000,
                    },
                    "net_cash_from_operating": 213750,
                },
                "investing_activities": {
                    "capital_expenditures": -85000,
                    "investments": -25000,
                    "net_cash_from_investing": -110000,
                },
                "financing_activities": {
                    "debt_repayments": -75000,
                    "dividends_paid": 0,
                    "net_cash_from_financing": -75000,
                },
                "net_change_in_cash": 28750,
                "beginning_cash": 1110000,
                "ending_cash": 1138750,
            },
        },
    }

    # Get statement data for requested period
    if statement_type not in financial_data:
        return {
            "error": f"Statement type '{statement_type}' not found",
            "available_statements": list(financial_data.keys())
        }

    statement_data = financial_data[statement_type]

    if time_period not in statement_data:
        return {
            "error": f"Time period '{time_period}' not found",
            "available_periods": list(statement_data.keys())
        }

    current_data = statement_data[time_period]

    # If analysis requested, provide detailed analysis
    if analysis_type != "overview":
        # Get RAG context for financial analysis
        query = f"financial statement analysis {statement_type} {analysis_type}"
        context = await rag_module.generate_context(
            query, filter_criteria={"category": "accounting"}
        )

        # Prepare comparison data if requested
        comparison_data = None
        if comparison and "previous" in statement_data:
            comparison_data = statement_data["previous"]

        # Generate financial statement analysis using LLM
        system_prompt = f"""
        You are a financial analyst reviewing financial statements. Provide a {analysis_type} analysis of this {statement_type.replace('_', ' ')}:
        """

        # Format the statement data as readable text
        if statement_type == "balance_sheet":
            period_text = f"As of {current_data['date']}"

            system_prompt += f"""

            {statement_type.replace('_', ' ').title()} {period_text}

            Assets:
            """

            for category, accounts in current_data['assets'].items():
                if category == "total_assets":
                    system_prompt += f"Total Assets: ${accounts:,.0f}\n"
                    continue

                system_prompt += f"\n{category.replace('_', ' ').title()}:\n"
                for account, amount in accounts.items():
                    system_prompt += f"- {account.replace('_', ' ').title()}: ${amount:,.0f}\n"

            system_prompt += "\nLiabilities & Equity:\n"

            for category, accounts in current_data['liabilities_equity'].items():
                if category == "total_liabilities_equity":
                    system_prompt += f"Total Liabilities & Equity: ${accounts:,.0f}\n"
                    continue

                system_prompt += f"\n{category.replace('_', ' ').title()}:\n"
                for account, amount in accounts.items():
                    system_prompt += f"- {account.replace('_', ' ').title()}: ${amount:,.0f}\n"

        elif statement_type == "income_statement":
            period_text = f"For {current_data['period']}"

            system_prompt += f"""

            {statement_type.replace('_', ' ').title()} {period_text}

            Revenue:
            """

            for account, amount in current_data['revenue'].items():
                system_prompt += f"- {account.replace('_', ' ').title()}: ${amount:,.0f}\n"

            system_prompt += "\nCost of Sales:\n"
            for account, amount in current_data['cost_of_sales'].items():
                system_prompt += f"- {account.replace('_', ' ').title()}: ${amount:,.0f}\n"

            system_prompt += f"\nGross Profit: ${current_data['gross_profit']:,.0f}\n"

            system_prompt += "\nOperating Expenses:\n"
            for account, amount in current_data['operating_expenses'].items():
                system_prompt += f"- {account.replace('_', ' ').title()}: ${amount:,.0f}\n"

            system_prompt += f"\nOperating Income: ${current_data['operating_income']:,.0f}\n"

            system_prompt += "\nOther Income/Expense:\n"
            for account, amount in current_data['other_income_expense'].items():
                system_prompt += f"- {account.replace('_', ' ').title()}: ${amount:,.0f}\n"

            system_prompt += f"""
            Income Before Tax: ${current_data['income_before_tax']:,.0f}
            Tax Expense: ${current_data['tax_expense']:,.0f}
            Net Income: ${current_data['net_income']:,.0f}
            """

        elif statement_type == "cash_flow_statement":
            period_text = f"For {current_data['period']}"

            system_prompt += f"""

            {statement_type.replace('_', ' ').title()} {period_text}

            Operating Activities:
            - Net Income: ${current_data['operating_activities']['net_income']:,.0f}

            Adjustments:
            - Depreciation: ${current_data['operating_activities']['adjustments']['depreciation']:,.0f}

            Changes in Working Capital:
            """

            for account, amount in current_data['operating_activities']['adjustments']['changes_in_working_capital'].items():
                system_prompt += f"- {account.replace('_', ' ').title()}: ${amount:,.0f}\n"

            system_prompt += f"""
            Net Cash from Operating Activities: ${current_data['operating_activities']['net_cash_from_operating']:,.0f}

            Investing Activities:
            """

            for account, amount in current_data['investing_activities'].items():
                if account != "net_cash_from_investing":
                    system_prompt += f"- {account.replace('_', ' ').title()}: ${amount:,.0f}\n"

            system_prompt += f"""
            Net Cash from Investing Activities: ${current_data['investing_activities']['net_cash_from_investing']:,.0f}

            Financing Activities:
            """

            for account, amount in current_data['financing_activities'].items():
                if account != "net_cash_from_financing":
                    system_prompt += f"- {account.replace('_', ' ').title()}: ${amount:,.0f}\n"

            system_prompt += f"""
            Net Cash from Financing Activities: ${current_data['financing_activities']['net_cash_from_financing']:,.0f}

            Net Change in Cash: ${current_data['net_change_in_cash']:,.0f}
            Beginning Cash: ${current_data['beginning_cash']:,.0f}
            Ending Cash: ${current_data['ending_cash']:,.0f}
            """

        # Add comparison data if available
        if comparison_data:
            system_prompt += f"""

            Comparison to {comparison_data.get('period', comparison_data.get('date', 'previous period'))}:
            """

            if statement_type == "balance_sheet":
                # Calculate key changes
                current_assets_current = current_data['assets']['current_assets']['total_current_assets']
                current_assets_prev = comparison_data['assets']['current_assets']['total_current_assets']
                current_assets_change = current_assets_current - current_assets_prev
                current_assets_pct_change = (current_assets_change / current_assets_prev) * 100

                total_assets_current = current_data['assets']['total_assets']
                total_assets_prev = comparison_data['assets']['total_assets']
                total_assets_change = total_assets_current - total_assets_prev
                total_assets_pct_change = (total_assets_change / total_assets_prev) * 100

                total_liabilities_current = (current_data['liabilities_equity']['current_liabilities']['total_current_liabilities'] +
                                            current_data['liabilities_equity']['non_current_liabilities']['total_non_current_liabilities'])
                total_liabilities_prev = (comparison_data['liabilities_equity']['current_liabilities']['total_current_liabilities'] +
                                        comparison_data['liabilities_equity']['non_current_liabilities']['total_non_current_liabilities'])
                total_liabilities_change = total_liabilities_current - total_liabilities_prev
                total_liabilities_pct_change = (total_liabilities_change / total_liabilities_prev) * 100

                equity_current = current_data['liabilities_equity']['equity']['total_equity']
                equity_prev = comparison_data['liabilities_equity']['equity']['total_equity']
                equity_change = equity_current - equity_prev
                equity_pct_change = (equity_change / equity_prev) * 100

                system_prompt += f"""
                - Current Assets: ${current_assets_change:,.0f} ({current_assets_pct_change:.1f}%)
                - Total Assets: ${total_assets_change:,.0f} ({total_assets_pct_change:.1f}%)
                - Total Liabilities: ${total_liabilities_change:,.0f} ({total_liabilities_pct_change:.1f}%)
                - Total Equity: ${equity_change:,.0f} ({equity_pct_change:.1f}%)
                """

            elif statement_type == "income_statement":
                # Calculate key changes
                revenue_current = current_data['revenue']['total_revenue']
                revenue_prev = comparison_data['revenue']['total_revenue']
                revenue_change = revenue_current - revenue_prev
                revenue_pct_change = (revenue_change / revenue_prev) * 100

                gross_profit_current = current_data['gross_profit']
                gross_profit_prev = comparison_data['gross_profit']
                gross_profit_change = gross_profit_current - gross_profit_prev
                gross_profit_pct_change = (gross_profit_change / gross_profit_prev) * 100

                operating_income_current = current_data['operating_income']
                operating_income_prev = comparison_data['operating_income']
                operating_income_change = operating_income_current - operating_income_prev
                operating_income_pct_change = (operating_income_change / operating_income_prev) * 100

                net_income_current = current_data['net_income']
                net_income_prev = comparison_data['net_income']
                net_income_change = net_income_current - net_income_prev
                net_income_pct_change = (net_income_change / net_income_prev) * 100

                system_prompt += f"""
                - Revenue: ${revenue_change:,.0f} ({revenue_pct_change:.1f}%)
                - Gross Profit: ${gross_profit_change:,.0f} ({gross_profit_pct_change:.1f}%)
                - Operating Income: ${operating_income_change:,.0f} ({operating_income_pct_change:.1f}%)
                - Net Income: ${net_income_change:,.0f} ({net_income_pct_change:.1f}%)
                """

            elif statement_type == "cash_flow_statement":
                # Calculate key changes
                operating_current = current_data['operating_activities']['net_cash_from_operating']
                operating_prev = comparison_data['operating_activities']['net_cash_from_operating']
                operating_change = operating_current - operating_prev
                operating_pct_change = (operating_change / operating_prev) * 100 if operating_prev != 0 else float('inf')

                investing_current = current_data['investing_activities']['net_cash_from_investing']
                investing_prev = comparison_data['investing_activities']['net_cash_from_investing']
                investing_change = investing_current - investing_prev

                financing_current = current_data['financing_activities']['net_cash_from_financing']
                financing_prev = comparison_data['financing_activities']['net_cash_from_financing']
                financing_change = financing_current - financing_prev

                net_change_current = current_data['net_change_in_cash']
                net_change_prev = comparison_data['net_change_in_cash']
                net_change_change = net_change_current - net_change_prev
                net_change_pct_change = (net_change_change / net_change_prev) * 100 if net_change_prev != 0 else float('inf')

                system_prompt += f"""
                - Operating Cash Flow: ${operating_change:,.0f} ({operating_pct_change:.1f}%)
                - Investing Cash Flow: ${investing_change:,.0f}
                - Financing Cash Flow: ${financing_change:,.0f}
                - Net Change in Cash: ${net_change_change:,.0f} ({net_change_pct_change:.1f}%)
                """

        # Add ratio calculations for ratio analysis
        if analysis_type == "ratio":
            system_prompt += "\nKey Financial Ratios:\n"

            if statement_type == "balance_sheet":
                # Liquidity ratios
                current_assets = current_data['assets']['current_assets']['total_current_assets']
                current_liabilities = current_data['liabilities_equity']['current_liabilities']['total_current_liabilities']
                current_ratio = current_assets / current_liabilities if current_liabilities != 0 else float('inf')

                quick_assets = current_assets - current_data['assets']['current_assets']['inventory']
                quick_ratio = quick_assets / current_liabilities if current_liabilities != 0 else float('inf')

                # Leverage ratios
                total_assets = current_data['assets']['total_assets']
                total_liabilities = (current_data['liabilities_equity']['current_liabilities']['total_current_liabilities'] +
                                    current_data['liabilities_equity']['non_current_liabilities']['total_non_current_liabilities'])
                debt_to_assets = total_liabilities / total_assets if total_assets != 0 else float('inf')

                total_equity = current_data['liabilities_equity']['equity']['total_equity']
                debt_to_equity = total_liabilities / total_equity if total_equity != 0 else float('inf')

                system_prompt += f"""
                Liquidity Ratios:
                - Current Ratio: {current_ratio:.2f}
                - Quick Ratio: {quick_ratio:.2f}

                Leverage Ratios:
                - Debt to Assets: {debt_to_assets:.2f}
                - Debt to Equity: {debt_to_equity:.2f}
                """

            elif statement_type == "income_statement":
                # Assume we have balance sheet data available for some ratios
                if "balance_sheet" in financial_data and time_period in financial_data["balance_sheet"]:
                    balance_sheet = financial_data["balance_sheet"][time_period]

                    # Profitability ratios
                    revenue = current_data['revenue']['total_revenue']
                    gross_profit = current_data['gross_profit']
                    operating_income = current_data['operating_income']
                    net_income = current_data['net_income']

                    gross_margin = gross_profit / revenue if revenue != 0 else 0
                    operating_margin = operating_income / revenue if revenue != 0 else 0
                    net_margin = net_income / revenue if revenue != 0 else 0

                    # Efficiency ratios
                    total_assets = balance_sheet['assets']['total_assets']
                    return_on_assets = net_income / total_assets if total_assets != 0 else 0

                    total_equity = balance_sheet['liabilities_equity']['equity']['total_equity']
                    return_on_equity = net_income / total_equity if total_equity != 0 else 0

                    system_prompt += f"""
                    Profitability Ratios:
                    - Gross Margin: {gross_margin:.2f} ({gross_margin*100:.1f}%)
                    - Operating Margin: {operating_margin:.2f} ({operating_margin*100:.1f}%)
                    - Net Profit Margin: {net_margin:.2f} ({net_margin*100:.1f}%)

                    Return Ratios:
                    - Return on Assets (ROA): {return_on_assets:.2f} ({return_on_assets*100:.1f}%)
                    - Return on Equity (ROE): {return_on_equity:.2f} ({return_on_equity*100:.1f}%)
                    """
                else:
                    # Limited ratios without balance sheet
                    revenue = current_data['revenue']['total_revenue']
                    gross_profit = current_data['gross_profit']
                    operating_income = current_data['operating_income']
                    net_income = current_data['net_income']

                    gross_margin = gross_profit / revenue if revenue != 0 else 0
                    operating_margin = operating_income / revenue if revenue != 0 else 0
                    net_margin = net_income / revenue if revenue != 0 else 0

                    system_prompt += f"""
                    Profitability Ratios:
                    - Gross Margin: {gross_margin:.2f} ({gross_margin*100:.1f}%)
                    - Operating Margin: {operating_margin:.2f} ({operating_margin*100:.1f}%)
                    - Net Profit Margin: {net_margin:.2f} ({net_margin*100:.1f}%)
                    """

            elif statement_type == "cash_flow_statement":
                # Cash flow ratios
                if "income_statement" in financial_data and time_period in financial_data["income_statement"]:
                    income_statement = financial_data["income_statement"][time_period]
                    net_income = income_statement['net_income']

                    operating_cash_flow = current_data['operating_activities']['net_cash_from_operating']
                    operating_cash_flow_ratio = operating_cash_flow / net_income if net_income != 0 else float('inf')

                    if "balance_sheet" in financial_data and time_period in financial_data["balance_sheet"]:
                        balance_sheet = financial_data["balance_sheet"][time_period]
                        total_liabilities = (balance_sheet['liabilities_equity']['current_liabilities']['total_current_liabilities'] +
                                            balance_sheet['liabilities_equity']['non_current_liabilities']['total_non_current_liabilities'])

                        cash_flow_to_debt = operating_cash_flow / total_liabilities if total_liabilities != 0 else float('inf')

                        system_prompt += f"""
                        Cash Flow Ratios:
                        - Operating Cash Flow to Net Income: {operating_cash_flow_ratio:.2f}
                        - Cash Flow to Debt: {cash_flow_to_debt:.2f}
                        - Free Cash Flow: ${operating_cash_flow + current_data['investing_activities']['capital_expenditures']:,.0f}
                        """
                    else:
                        system_prompt += f"""
                        Cash Flow Ratios:
                        - Operating Cash Flow to Net Income: {operating_cash_flow_ratio:.2f}
                        - Free Cash Flow: ${operating_cash_flow + current_data['investing_activities']['capital_expenditures']:,.0f}
                        """
                else:
                    system_prompt += f"""
                    Cash Flow Metrics:
                    - Operating Cash Flow: ${current_data['operating_activities']['net_cash_from_operating']:,.0f}
                    - Free Cash Flow: ${current_data['operating_activities']['net_cash_from_operating'] + current_data['investing_activities']['capital_expenditures']:,.0f}
                    - Cash Flow from Operations to Capital Expenditures: {current_data['operating_activities']['net_cash_from_operating'] / abs(current_data['investing_activities']['capital_expenditures']):,.2f}
                    """

        system_prompt += f"""

        Based on the {statement_type.replace('_', ' ')} and the information provided, perform a detailed {analysis_type} analysis, including:

        1. Key insights and trends
        2. Strengths and areas of concern
        3. Notable changes and their implications
        4. Recommendations for management

        Focus on the most important aspects that would be relevant to financial decision-makers.
        """

        if context:
            system_prompt += f"\n\nAdditional relevant context for analysis:\n{context}"

        analysis = await generate_text(
            prompt=f"Perform {analysis_type} analysis on the {statement_type.replace('_', ' ')}",
            system_prompt=system_prompt,
            max_new_tokens=1024,
        )

        # Prepare response data
        statement_data = {
            "statement_type": statement_type,
            "time_period": time_period,
            "data": current_data,
            "comparison_data": comparison_data if comparison else None,
            "analysis_type": analysis_type,
            "analysis": analysis,
        }

        return statement_data

    # Return raw statement data
    elif statement_type == "balance_sheet":
        # Format date for display
        period_text = f"As of {current_data['date']}"

        # Calculate comparison data if requested
        comparison_data = None
        if comparison and "previous" in statement_data:
            comparison_data = statement_data["previous"]

        # Calculate changes
        comparison_changes = {
            "assets": {},
            "liabilities_equity": {},
        }

        # Process assets
        for category in current_data["assets"]:
            if category not in comparison_data["assets"]:
                continue

            if isinstance(current_data["assets"][category], dict):
                comparison_changes["assets"][category] = {}
                for account in current_data["assets"][category]:
                    if account in comparison_data["assets"][category]:
                        current_value = current_data["assets"][category][account]
                        previous_value = comparison_data["assets"][category][account]
                        change = current_value - previous_value
                        pct_change = (change / previous_value) * 100 if previous_value != 0 else 0

                        comparison_changes["assets"][category][account] = {
                            "change": change,
                            "pct_change": pct_change,
                        }
            else:
                current_value = current_data["assets"][category]
                previous_value = comparison_data["assets"][category]
                change = current_value - previous_value
                pct_change = (change / previous_value) * 100 if previous_value != 0 else 0

                comparison_changes["assets"][category] = {
                    "change": change,
                    "pct_change": pct_change,
                }

        # Process liabilities & equity
        for category in current_data["liabilities_equity"]:
            if category not in comparison_data["liabilities_equity"]:
                continue

            if isinstance(current_data["liabilities_equity"][category], dict):
                comparison_changes["liabilities_equity"][category] = {}
                for account in current_data["liabilities_equity"][category]:
                    if account in comparison_data["liabilities_equity"][category]:
                        current_value = current_data["liabilities_equity"][category][account]
                        previous_value = comparison_data["liabilities_equity"][category][account]
                        change = current_value - previous_value
                        pct_change = (change / previous_value) * 100 if previous_value != 0 else 0

                        comparison_changes["liabilities_equity"][category][account] = {
                            "change": change,
                            "pct_change": pct_change,
                        }
            else:
                current_value = current_data["liabilities_equity"][category]
                previous_value = comparison_data["liabilities_equity"][category]
                change = current_value - previous_value
                pct_change = (change / previous_value) * 100 if previous_value != 0 else 0

                comparison_changes["liabilities_equity"][category] = {
                    "change": change,
                    "pct_change": pct_change,
                }

        return {
            "statement_type": statement_type,
            "period": period_text,
            "data": current_data,
            "comparison_data": comparison_data if comparison else None,
            "comparison_changes": comparison_changes if comparison and comparison_data else None,
            "message": (
                f"Balance Sheet as of {current_data['date']}\n\n"
                "ASSETS\n"
                f"Current Assets: ${current_data['assets']['current_assets']['total_current_assets']:,.0f}\n"
                f"Non-Current Assets: ${current_data['assets']['non_current_assets']['total_non_current_assets']:,.0f}\n"
                f"Total Assets: ${current_data['assets']['total_assets']:,.0f}\n\n"
                "LIABILITIES & EQUITY\n"
                f"Current Liabilities: ${current_data['liabilities_equity']['current_liabilities']['total_current_liabilities']:,.0f}\n"
                f"Non-Current Liabilities: ${current_data['liabilities_equity']['non_current_liabilities']['total_non_current_liabilities']:,.0f}\n"
                f"Total Equity: ${current_data['liabilities_equity']['equity']['total_equity']:,.0f}\n"
                f"Total Liabilities & Equity: ${current_data['liabilities_equity']['total_liabilities_equity']:,.0f}"
            ),
        }

    elif statement_type == "income_statement":
        # Format period for display
        period_text = f"For {current_data['period']}"

        # Calculate comparison data if requested
        comparison_data = None
        comparison_changes = None
        if comparison and "previous" in statement_data:
            comparison_data = statement_data["previous"]

            # Calculate key changes
            revenue_current = current_data['revenue']['total_revenue']
            revenue_prev = comparison_data['revenue']['total_revenue']
            revenue_change = revenue_current - revenue_prev
            revenue_pct_change = (revenue_change / revenue_prev) * 100 if revenue_prev != 0 else 0

            gross_profit_current = current_data['gross_profit']
            gross_profit_prev = comparison_data['gross_profit']
            gross_profit_change = gross_profit_current - gross_profit_prev
            gross_profit_pct_change = (gross_profit_change / gross_profit_prev) * 100 if gross_profit_prev != 0 else 0

            operating_income_current = current_data['operating_income']
            operating_income_prev = comparison_data['operating_income']
            operating_income_change = operating_income_current - operating_income_prev
            operating_income_pct_change = (operating_income_change / operating_income_prev) * 100 if operating_income_prev != 0 else 0

            net_income_current = current_data['net_income']
            net_income_prev = comparison_data['net_income']
            net_income_change = net_income_current - net_income_prev
            net_income_pct_change = (net_income_change / net_income_prev) * 100 if net_income_prev != 0 else 0

            comparison_changes = {
                "revenue": {
                    "change": revenue_change,
                    "pct_change": revenue_pct_change,
                },
                "gross_profit": {
                    "change": gross_profit_change,
                    "pct_change": gross_profit_pct_change,
                },
                "operating_income": {
                    "change": operating_income_change,
                    "pct_change": operating_income_pct_change,
                },
                "net_income": {
                    "change": net_income_change,
                    "pct_change": net_income_pct_change,
                },
            }

        return {
            "statement_type": statement_type,
            "period": period_text,
            "data": current_data,
            "comparison_data": comparison_data if comparison else None,
            "comparison_changes": comparison_changes,
            "message": (
                f"Income Statement for {current_data['period']}\n\n"
                f"Revenue: ${current_data['revenue']['total_revenue']:,.0f}\n"
                f"Cost of Sales: ${current_data['cost_of_sales']['total_cost_of_sales']:,.0f}\n"
                f"Gross Profit: ${current_data['gross_profit']:,.0f}\n"
                f"Operating Expenses: ${current_data['operating_expenses']['total_operating_expenses']:,.0f}\n"
                f"Operating Income: ${current_data['operating_income']:,.0f}\n"
                f"Income Before Tax: ${current_data['income_before_tax']:,.0f}\n"
                f"Net Income: ${current_data['net_income']:,.0f}\n"
                f"Gross Margin: {(current_data['gross_profit'] / current_data['revenue']['total_revenue']) * 100:.1f}%\n"
                f"Net Margin: {(current_data['net_income'] / current_data['revenue']['total_revenue']) * 100:.1f}%"
            ),
        }

    elif statement_type == "cash_flow_statement":
        # Format period for display
        period_text = f"For {current_data['period']}"

        # Calculate comparison data if requested
        comparison_data = None
        comparison_changes = None
        if comparison and "previous" in statement_data:
            comparison_data = statement_data["previous"]

            # Calculate key changes
            operating_current = current_data['operating_activities']['net_cash_from_operating']
            operating_prev = comparison_data['operating_activities']['net_cash_from_operating']
            operating_change = operating_current - operating_prev
            operating_pct_change = (operating_change / operating_prev) * 100 if operating_prev != 0 else 0

            investing_current = current_data['investing_activities']['net_cash_from_investing']
            investing_prev = comparison_data['investing_activities']['net_cash_from_investing']
            investing_change = investing_current - investing_prev
            investing_pct_change = (investing_change / investing_prev) * 100 if investing_prev != 0 else 0

            financing_current = current_data['financing_activities']['net_cash_from_financing']
            financing_prev = comparison_data['financing_activities']['net_cash_from_financing']
            financing_change = financing_current - financing_prev
            financing_pct_change = (financing_change / financing_prev) * 100 if financing_prev != 0 else 0

            net_change_current = current_data['net_change_in_cash']
            net_change_prev = comparison_data['net_change_in_cash']
            net_change_change = net_change_current - net_change_prev
            net_change_pct_change = (net_change_change / net_change_prev) * 100 if net_change_prev != 0 else 0

            comparison_changes = {
                "operating_activities": {
                    "change": operating_change,
                    "pct_change": operating_pct_change,
                },
                "investing_activities": {
                    "change": investing_change,
                    "pct_change": investing_pct_change,
                },
                "financing_activities": {
                    "change": financing_change,
                    "pct_change": financing_pct_change,
                },
                "net_change_in_cash": {
                    "change": net_change_change,
                    "pct_change": net_change_pct_change,
                },
            }

        return {
            "statement_type": statement_type,
            "period": period_text,
            "data": current_data,
            "comparison_data": comparison_data if comparison else None,
            "comparison_changes": comparison_changes,
            "message": (
                f"Cash Flow Statement for {current_data['period']}\n\n"
                f"Net Income: ${current_data['operating_activities']['net_income']:,.0f}\n"
                f"Net Cash from Operating: ${current_data['operating_activities']['net_cash_from_operating']:,.0f}\n"
                f"Net Cash from Investing: ${current_data['investing_activities']['net_cash_from_investing']:,.0f}\n"
                f"Net Cash from Financing: ${current_data['financing_activities']['net_cash_from_financing']:,.0f}\n"
                f"Net Change in Cash: ${current_data['net_change_in_cash']:,.0f}\n"
                f"Beginning Cash: ${current_data['beginning_cash']:,.0f}\n"
                f"Ending Cash: ${current_data['ending_cash']:,.0f}"
            ),
        }


async def handle_accounting_policy(entities: Dict) -> Dict:
    """
    Provide information about accounting policies and procedures.

    Args:
    entities: Dictionary of entities extracted from user intent

    Returns:
    Dictionary with accounting policy information
    """
    # Extract relevant entities
    policy_name = entities.get("policy_name")
    policy_category = entities.get("policy_category")

    # Get context from RAG for accounting policies
    query = f"accounting policy {policy_name if policy_name else policy_category if policy_category else 'overview'}"
    context = await rag_module.generate_context(
        query, filter_criteria={"category": "accounting"}
    )

    # Generate accounting policy information using LLM
    system_prompt = """
    You are an accounting policy specialist. Provide information about accounting policies and procedures.
    """

    if policy_name:
        system_prompt += f"\n\nThe user is asking about the '{policy_name}' accounting policy."
    elif policy_category:
        system_prompt += f"\n\nThe user is asking about policies in the '{policy_category}' category."
    else:
        system_prompt += "\n\nThe user is asking for an overview of accounting policies."

    if context:
        system_prompt += f"\n\nUse this relevant context for your response:\n{context}"
    else:
        system_prompt += """

        Without specific context about the company's policies, provide general information about standard accounting policies and procedures following GAAP or IFRS as appropriate. Include:

        1. Definition and purpose of the policy or policy area
        2. Key principles and requirements
        3. Implementation considerations
        4. Common practices and industry standards
        5. Relevant accounting standards (GAAP/IFRS references)

        Tailor the response to be informative and educational while noting that specific company policies may vary.
        """

    policy_info = await generate_text(
        prompt=f"Provide information about {policy_name if policy_name else policy_category if policy_category else 'accounting policies overview'}",
        system_prompt=system_prompt,
        max_new_tokens=1024,
    )

    return {
        "policy_name": policy_name,
        "policy_category": policy_category,
        "context_available": bool(context),
        "formatted_response": policy_info,
    }