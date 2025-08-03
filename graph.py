from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.chat_models import init_chat_model

from tools import (
    get_user_financial_info,
    get_current_mortgage_rate,
    loan_advisor_agent,
    get_user_account_detail,
    get_user_loan_detail,
    smart_refinance_agent
)

# Define graph state
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Bind tools
tools = [
    get_user_financial_info,
    get_current_mortgage_rate,
    loan_advisor_agent,
    get_user_account_detail,
    get_user_loan_detail,
    smart_refinance_agent
]

llm = init_chat_model("gpt-4o")
agented_llm = llm.bind_tools(tools)

# Core chatbot node with enhanced routing
def chatbot(state: State, config=None) -> State:
    print("Received config in chatbot:", config)
    user_id = config.get("configurable", {}).get("thread_id") if config else None
    print("user_id in chatbot:", user_id)

    system_msg = SystemMessage(
        content=f"""
You are a multi-agent banking assistant helping user ID {user_id}.

ROUTING RULES:
- If query is about **current balance, outstanding amount, payment, mortgage rate, loan summary** → use Loan Servicing tools.
- If query is about **loan details (full breakdown)** → use get_user_loan_detail tool.
- If query is about **closing loan early, prepaying, reducing loan payment, optimizing repayment strategy** → use Personalized Loan Advisor tool.
- If query is about **refinancing, comparing current loan with new offer, refinance savings, benefit/loss analysis** → ALWAYS use Smart Refinance Agent tool.

Be concise, financial but user-friendly.
"""
    )

    response = agented_llm.invoke([system_msg] + state["messages"], config=config)
    return {"messages": [response]}

# Build graph
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")
builder.set_finish_point("chatbot")

# Compile final graph
graph = builder.compile()
