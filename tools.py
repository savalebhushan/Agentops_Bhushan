import os
import time
from sqlalchemy import create_engine, text
from langchain_core.tools import tool
from schemas import UserIDInput, RefinanceInput
import agentops
from agentops.sdk.decorators import agent, operation, tool as agentops_tool
import monitoring

DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL) if DB_URL else None

@agentops_tool(name="UserFinancialInfoTool", cost=0.01)
@tool
def get_user_financial_info(user_id: str) -> str:
    """Get user's financial information including income, credit score, and debt."""
    if not engine:
        return "Database connection not available"
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT income, credit_score, debt FROM users WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return f"Income: ${result[0]:,.2f}, Credit Score: {result[1]}, Total Debt: ${result[2]:,.2f}"
            else:
                return f"No financial information found for user {user_id}"
    except Exception as e:
        return f"Error retrieving financial info: {str(e)}"

@agentops_tool(name="MortgageRateTool", cost=0.005)
@tool
def get_current_mortgage_rate() -> str:
    """Get current market mortgage rates."""
    return "Current 30-year fixed mortgage rate: 7.25%, 15-year fixed: 6.75%"

@agentops_tool(name="UserAccountTool", cost=0.01)
@tool
def get_user_account_detail(user_id: str) -> str:
    """Get user's account details including balance and payment status."""
    if not engine:
        return "Database connection not available"
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT account_balance, payment_status, last_payment_date FROM accounts WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return f"Account Balance: ${result[0]:,.2f}, Payment Status: {result[1]}, Last Payment: {result[2]}"
            else:
                return f"No account found for user {user_id}"
    except Exception as e:
        return f"Error retrieving account details: {str(e)}"

@agentops_tool(name="UserLoanTool", cost=0.01)
@tool
def get_user_loan_detail(user_id: str) -> str:
    """Get detailed loan information including principal, interest rate, and term."""
    if not engine:
        return "Database connection not available"
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT loan_amount, interest_rate, loan_term, remaining_balance FROM loans WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return f"Loan Amount: ${result[0]:,.2f}, Interest Rate: {result[1]:.2f}%, Term: {result[2]} years, Remaining Balance: ${result[3]:,.2f}"
            else:
                return f"No loan found for user {user_id}"
    except Exception as e:
        return f"Error retrieving loan details: {str(e)}"

@agent(name="LoanAdvisorAgent")
class LoanAdvisorAgent:
    """Agent for providing personalized loan advice and optimization strategies."""
    
    @operation
    def analyze_prepayment_strategy(self, user_id: str, extra_payment: float = 0) -> str:
        """Analyze the impact of extra payments on loan payoff."""
        loan_info = get_user_loan_detail(user_id)
        financial_info = get_user_financial_info(user_id)
        
        if "Error" in loan_info or "No loan found" in loan_info:
            return loan_info
        
        return f"""
        Loan Advisor Analysis for User {user_id}:
        
        Current Loan Status: {loan_info}
        Financial Profile: {financial_info}
        
        Prepayment Strategy Recommendation:
        - With extra payment of ${extra_payment:,.2f}/month, you could save significant interest
        - Consider your emergency fund and other investments before increasing payments
        - Current market rates suggest holding existing low-rate loans may be beneficial
        
        Recommendation: Contact our loan specialists for detailed amortization analysis.
        """

@agentops_tool(name="LoanAdvisorTool", cost=0.05)
@tool
def loan_advisor_agent(user_id: str, query: str = "") -> str:
    """Loan advisor agent for optimization and prepayment strategies."""
    start_time = time.time()
    
    try:
        advisor = LoanAdvisorAgent()
        
        if "prepay" in query.lower() or "extra payment" in query.lower():
            result = advisor.analyze_prepayment_strategy(user_id)
        else:
            loan_info = get_user_loan_detail(user_id)
            financial_info = get_user_financial_info(user_id)
            
            result = f"""
            Loan Advisor Consultation for User {user_id}:
            
            Current Situation: {loan_info}
            Financial Profile: {financial_info}
            
            General Recommendations:
            - Review your payment schedule quarterly
            - Consider refinancing if rates drop significantly
            - Maintain 3-6 months emergency fund before extra payments
            - Evaluate tax implications of mortgage interest deduction
            """
        
        # Track performance metrics
        execution_time = (time.time() - start_time) * 1000
        monitoring.track_agent_performance("LoanAdvisorAgent", execution_time, tokens_used=150, cost=0.05, success=True)
        monitoring.track_cost_and_tokens("loan_advisor_consultation", tokens_input=50, tokens_output=100, cost_usd=0.05)
        
        return result
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        monitoring.track_agent_performance("LoanAdvisorAgent", execution_time, success=False)
        return f"Error in loan advisor analysis: {str(e)}"

@agent(name="SmartRefinanceAgent")
class SmartRefinanceAgent:
    """Agent for analyzing refinancing opportunities and benefits."""
    
    @operation
    def calculate_refinance_savings(self, user_id: str, new_rate: float, new_income: float = None, new_credit_score: int = None) -> str:
        """Calculate potential savings from refinancing."""
        loan_info = get_user_loan_detail(user_id)
        account_info = get_user_account_detail(user_id)
        
        if "Error" in loan_info or "No loan found" in loan_info:
            return loan_info
        
        return f"""
        Refinance Analysis for User {user_id}:
        
        Current Loan: {loan_info}
        Account Status: {account_info}
        
        Proposed Terms:
        - New Interest Rate: {new_rate:.2f}%
        - Updated Income: ${new_income:,.2f}" if new_income else "Using existing income"
        - Updated Credit Score: {new_credit_score}" if new_credit_score else "Using existing score"
        
        Estimated Impact:
        - Monthly payment change: Calculate based on new rate
        - Total interest savings over loan term: Significant if rate reduction > 0.5%
        - Break-even point: Typically 2-3 years with closing costs
        
        Recommendation: Refinancing appears {"favorable" if new_rate < 7.0 else "neutral"} based on current market conditions.
        """

@agentops_tool(name="SmartRefinanceTool", cost=0.08)
@tool
def smart_refinance_agent(user_id: str, new_interest_rate: float = None,
                         new_income: float = None, new_credit_score: int = None,
                         query: str = "") -> str:
    """Smart refinance agent for analyzing refinancing opportunities."""
    start_time = time.time()
    
    try:
        refinance_agent = SmartRefinanceAgent()
        current_rate = 7.25  # Default current market rate
        proposed_rate = new_interest_rate or current_rate
        
        if new_interest_rate:
            result = refinance_agent.calculate_refinance_savings(user_id, proposed_rate, new_income, new_credit_score)
        else:
            loan_info = get_user_loan_detail(user_id)
            market_rates = get_current_mortgage_rate()
            
            result = f"""
            Smart Refinance Analysis for User {user_id}:
            
            Current Loan Status: {loan_info}
            Market Conditions: {market_rates}
            
            Refinancing Opportunities:
            - Current market rates may offer savings opportunity
            - Your creditworthiness will impact qualification
            - Consider cash-out refinancing for home improvements
            - Evaluate ARM vs Fixed rate options based on your timeline
            
            Next Steps:
            - Get updated credit report
            - Calculate closing costs vs monthly savings
            - Consider timing with market rate trends
            
            Use specific rate parameters for detailed savings analysis.
            """
        
        # Track performance metrics
        execution_time = (time.time() - start_time) * 1000
        monitoring.track_agent_performance("SmartRefinanceAgent", execution_time, tokens_used=200, cost=0.08, success=True)
        monitoring.track_cost_and_tokens("refinance_analysis", tokens_input=75, tokens_output=125, cost_usd=0.08)
        
        return result
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        monitoring.track_agent_performance("SmartRefinanceAgent", execution_time, success=False)
        return f"Error in refinance analysis: {str(e)}"