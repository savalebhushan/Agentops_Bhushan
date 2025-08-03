import os
import json
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from langchain_core.tools import tool
from schemas import UserIDInput, RefinanceInput
import agentops
from agentops.sdk.decorators import agent, operation, tool as agentops_tool

# Database connection
DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL) if DB_URL else None

@agent(name="LoanServicingAgent")
class LoanServicingAgent:
    """Agent responsible for basic loan servicing operations like balance checks and payments"""
    
    def __init__(self):
        self.agent_id = "loan_servicing_agent"
    
    @operation
    def get_account_details(self, user_id: str) -> Dict[str, Any]:
        """Get user account details from database"""
        if not engine:
            return {"error": "Database not configured"}
        
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM user_accounts WHERE user_id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
                
                if result:
                    return dict(result._mapping)
                return {"error": "User not found"}
        except Exception as e:
            return {"error": f"Database error: {str(e)}"}
    
    @operation
    def get_loan_details(self, user_id: str) -> Dict[str, Any]:
        """Get detailed loan information for user"""
        if not engine:
            return {"error": "Database not configured"}
        
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM user_loans WHERE user_id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
                
                if result:
                    return dict(result._mapping)
                return {"error": "Loan not found"}
        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

@agent(name="LoanAdvisorAgent")
class LoanAdvisorAgent:
    """Agent specialized in providing loan advice and optimization strategies"""
    
    def __init__(self):
        self.agent_id = "loan_advisor_agent"
    
    @operation
    def analyze_loan_optimization(self, user_id: str, financial_data: Dict[str, Any]) -> str:
        """Analyze loan and provide optimization recommendations"""
        try:
            # Get current loan details
            loan_data = LoanServicingAgent().get_loan_details(user_id)
            if "error" in loan_data:
                return f"Cannot analyze loan: {loan_data['error']}"
            
            current_balance = loan_data.get('outstanding_balance', 0)
            monthly_payment = loan_data.get('monthly_payment', 0)
            interest_rate = loan_data.get('interest_rate', 0)
            
            # Generate advice based on loan data
            advice = f"""
            **Loan Optimization Analysis for User {user_id}:**
            
            Current Loan Status:
            - Outstanding Balance: ${current_balance:,.2f}
            - Monthly Payment: ${monthly_payment:,.2f}
            - Interest Rate: {interest_rate}%
            
            Recommendations:
            1. Consider making extra principal payments to reduce total interest
            2. If credit score improved, explore refinancing options
            3. Set up automatic payments for potential rate discounts
            """
            
            return advice
        except Exception as e:
            return f"Error analyzing loan: {str(e)}"

@agent(name="RefinanceAgent")
class RefinanceAgent:
    """Agent specialized in refinancing analysis and recommendations"""
    
    def __init__(self):
        self.agent_id = "refinance_agent"
    
    @operation
    def analyze_refinance_options(self, user_id: str, new_rate: Optional[float] = None, 
                                new_credit_score: Optional[int] = None, 
                                new_income: Optional[float] = None) -> str:
        """Analyze refinancing options with potential new terms"""
        try:
            # Get current loan and financial info
            loan_data = LoanServicingAgent().get_loan_details(user_id)
            financial_data = LoanServicingAgent().get_account_details(user_id)
            
            if "error" in loan_data or "error" in financial_data:
                return "Cannot analyze refinance: Missing loan or financial data"
            
            current_rate = loan_data.get('interest_rate', 0)
            current_balance = loan_data.get('outstanding_balance', 0)
            current_payment = loan_data.get('monthly_payment', 0)
            
            # Use provided overrides or current values
            proposed_rate = new_rate if new_rate else current_rate * 0.95  # Assume 5% reduction
            credit_score = new_credit_score if new_credit_score else financial_data.get('credit_score', 700)
            income = new_income if new_income else financial_data.get('annual_income', 50000)
            
            # Calculate potential savings
            rate_difference = current_rate - proposed_rate
            monthly_savings = current_balance * (rate_difference / 100) / 12
            annual_savings = monthly_savings * 12
            
            analysis = f"""
            **Refinance Analysis for User {user_id}:**
            
            Current Loan:
            - Rate: {current_rate}%
            - Balance: ${current_balance:,.2f}
            - Monthly Payment: ${current_payment:,.2f}
            
            Proposed Terms:
            - New Rate: {proposed_rate}%
            - Credit Score: {credit_score}
            - Annual Income: ${income:,.2f}
            
            Potential Savings:
            - Monthly Savings: ${monthly_savings:,.2f}
            - Annual Savings: ${annual_savings:,.2f}
            - Rate Improvement: {rate_difference:.2f} percentage points
            
            Recommendation: {'Proceed with refinance' if rate_difference > 0.5 else 'Current terms are competitive'}
            """
            
            return analysis
        except Exception as e:
            return f"Error analyzing refinance: {str(e)}"

# Initialize agent instances
loan_servicing_agent = LoanServicingAgent()
loan_advisor_agent_instance = LoanAdvisorAgent()
refinance_agent_instance = RefinanceAgent()

# Tool functions that integrate with the agents
@tool
@agentops_tool(name="UserFinancialInfo", cost=0.01)
def get_user_financial_info(user_id: str) -> str:
    """Get user's financial information including income, credit score, and debt details"""
    result = loan_servicing_agent.get_account_details(user_id)
    
    if "error" in result:
        return f"Error retrieving financial info: {result['error']}"
    
    return f"""
    Financial Information for User {user_id}:
    - Annual Income: ${result.get('annual_income', 'N/A'):,}
    - Credit Score: {result.get('credit_score', 'N/A')}
    - Debt-to-Income Ratio: {result.get('debt_to_income_ratio', 'N/A')}%
    - Account Status: {result.get('account_status', 'Active')}
    """

@tool
@agentops_tool(name="CurrentMortgageRate", cost=0.005)
def get_current_mortgage_rate() -> str:
    """Get current market mortgage rates"""
    # Simulate getting current market rates
    return """
    Current Market Mortgage Rates:
    - 30-year Fixed: 6.875%
    - 15-year Fixed: 6.125%
    - 5/1 ARM: 5.750%
    
    Rates updated daily and subject to credit approval.
    """

@tool
@agentops_tool(name="LoanAdvisorTool", cost=0.02)
def loan_advisor_agent(user_id: str) -> str:
    """Get personalized loan advice and optimization strategies from the Loan Advisor Agent"""
    financial_data = loan_servicing_agent.get_account_details(user_id)
    return loan_advisor_agent_instance.analyze_loan_optimization(user_id, financial_data)

@tool
@agentops_tool(name="UserAccountDetail", cost=0.01)
def get_user_account_detail(user_id: str) -> str:
    """Get detailed user account information"""
    result = loan_servicing_agent.get_account_details(user_id)
    
    if "error" in result:
        return f"Error retrieving account details: {result['error']}"
    
    return f"""
    Account Details for User {user_id}:
    - Account Number: {result.get('account_number', 'N/A')}
    - Account Type: {result.get('account_type', 'N/A')}
    - Account Status: {result.get('account_status', 'N/A')}
    - Last Updated: {result.get('last_updated', 'N/A')}
    - Contact Email: {result.get('email', 'N/A')}
    """

@tool
@agentops_tool(name="UserLoanDetail", cost=0.01)
def get_user_loan_detail(user_id: str) -> str:
    """Get comprehensive loan details including payment history and terms"""
    result = loan_servicing_agent.get_loan_details(user_id)
    
    if "error" in result:
        return f"Error retrieving loan details: {result['error']}"
    
    return f"""
    Loan Details for User {user_id}:
    - Loan Number: {result.get('loan_number', 'N/A')}
    - Loan Type: {result.get('loan_type', 'N/A')}
    - Original Amount: ${result.get('original_amount', 0):,.2f}
    - Outstanding Balance: ${result.get('outstanding_balance', 0):,.2f}
    - Interest Rate: {result.get('interest_rate', 0)}%
    - Monthly Payment: ${result.get('monthly_payment', 0):,.2f}
    - Next Payment Due: {result.get('next_payment_date', 'N/A')}
    - Loan Term: {result.get('loan_term_months', 'N/A')} months
    - Payments Made: {result.get('payments_made', 'N/A')}
    """

@tool
@agentops_tool(name="SmartRefinanceAgent", cost=0.03)
def smart_refinance_agent(refinance_input: str) -> str:
    """Advanced refinance analysis using the Smart Refinance Agent"""
    try:
        # Parse input - expect JSON string or user_id
        if refinance_input.startswith('{'):
            import json
            data = json.loads(refinance_input)
            user_id = data.get('user_id')
            new_rate = data.get('new_interest_rate')
            new_credit_score = data.get('new_credit_score')
            new_income = data.get('new_income')
        else:
            user_id = refinance_input
            new_rate = None
            new_credit_score = None
            new_income = None
        
        return refinance_agent_instance.analyze_refinance_options(
            user_id, new_rate, new_credit_score, new_income
        )
    except Exception as e:
        return f"Error in refinance analysis: {str(e)}"