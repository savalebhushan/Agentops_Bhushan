from fastapi import FastAPI, Form, HTTPException
from sqlalchemy import create_engine, text
from langchain_core.messages import HumanMessage
from graph import graph
import os
from dotenv import load_dotenv
import uvicorn
import asyncio
import monitoring  # Initialize AgentOps monitoring

# ----------------- Load environment variables -----------------
print("[DEBUG] Loading environment variables...")
load_dotenv()

# Explicitly set API key for OpenAI
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    print("[ERROR] DB_URL missing in .env!")
else:
    print(f"[DEBUG] DB_URL loaded: {DB_URL}")

# Test DB connection at startup
try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("[DEBUG] Database connection successful.")
except Exception as e:
    print(f"[ERROR] DB connection failed: {e}")

# ----------------- Initialize FastAPI -----------------
app = FastAPI()

@app.post("/ask")
async def ask_question(
    query: str = Form(...),
    user_id: str = Form(...),
    new_interest_rate: float = Form(None),
    new_credit_score: int = Form(None),
    new_income: float = Form(None)
):
    """
    Unified endpoint: Routes query to correct agent (Servicing, Advisor, Refinance)
    Supports refinance overrides via extra form fields.
    """
    
    # Start AgentOps session for this request
    tracer = monitoring.start_session(
        trace_name=f"Loan Servicing Request - {query[:50]}...", 
        user_id=user_id
    )

    print("\n========== NEW REQUEST ==========")
    print(f"[DEBUG] Input - query: {query}, user_id: {user_id}, "
          f"new_interest_rate={new_interest_rate}, new_credit_score={new_credit_score}, new_income={new_income}")

    if not user_id:
        print("[ERROR] Missing user_id in request")
        if tracer:
            monitoring.end_session(tracer, end_state="Fail")
        raise HTTPException(status_code=400, detail="user_id required")

    # If refinance/restructure keywords present, append overrides info
    full_query = query
    if "refinance" in query.lower() or "restructure" in query.lower():
        full_query += (
            "\nPerform refinance analysis using DB values, but override with "
            f"user-provided values: rate={new_interest_rate}, score={new_credit_score}, income={new_income}. "
            "Use new offer column if present for better recommendation."
        )

    print(f"[DEBUG] Full query passed to graph: {full_query}")

    # Ensure API key is present
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found!")
        if tracer:
            monitoring.end_session(tracer, end_state="Fail")
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    # Invoke graph with timeout
    try:
        message = HumanMessage(content=full_query)
        print("[DEBUG] Calling graph.invoke()...")

        result = await asyncio.wait_for(
            asyncio.to_thread(
                graph.invoke,
                {"messages": [message]},
                {"configurable": {"thread_id": user_id}}
            ),
            timeout=20  # 20-second timeout
        )

        print("[DEBUG] graph.invoke() completed.")

    except asyncio.TimeoutError:
        print("[ERROR] graph.invoke() timed out.")
        if tracer:
            monitoring.end_session(tracer, end_state="Fail")
        raise HTTPException(status_code=504, detail="Request timed out (check DB/LLM).")

    except Exception as e:
        print(f"[ERROR] Exception in graph.invoke: {e}")
        if tracer:
            monitoring.end_session(tracer, end_state="Fail")
        raise HTTPException(status_code=500, detail=str(e))

    response_content = result["messages"][-1].content if result and "messages" in result else "No response generated."
    print(f"[DEBUG] Final response: {response_content}")

    # Track the overall request
    monitoring.track_tool_usage("ask_endpoint", {"query": query, "user_id": user_id}, response_content)
    
    # End AgentOps session successfully
    if tracer:
        monitoring.end_session(tracer, end_state="Success")

    return {"response": response_content}


if __name__ == "__main__":
    print("[DEBUG] Starting server on 0.0.0.0:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
