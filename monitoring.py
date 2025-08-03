# monitoring.py
import os

try:
    import agentops
    _AGENTOPS_AVAILABLE = True
except ImportError:
    print("[Monitoring] AgentOps not installed. Monitoring disabled.")
    _AGENTOPS_AVAILABLE = False

client = None
if _AGENTOPS_AVAILABLE:
    api_key = os.getenv("AGENTOPS_API_KEY")
    if api_key:
        try:
            client = agentops.Client(api_key=api_key)
        except Exception as e:
            print(f"[Monitoring] Failed to initialize AgentOps: {e}")
            client = None
    else:
        print("[Monitoring] No API key found for AgentOps. Monitoring disabled.")

# Safe no-op functions if monitoring disabled
def set_metadata(metadata):
    if client:
        try:
            client.set_metadata(metadata)
        except Exception as e:
            print(f"[Monitoring] set_metadata failed: {e}")

def track_event(name, extra_data=None):
    if client:
        try:
            client.track_event(name, extra_data or {})
        except Exception as e:
            print(f"[Monitoring] track_event failed: {e}")

def track_tool_usage(tool_name, input_data, output_data, tokens=None, cost=None):
    if client:
        try:
            payload = {"input": str(input_data), "output": str(output_data)[:200]}
            if tokens: payload["tokens"] = tokens
            if cost: payload["cost_usd"] = cost
            client.track_event(f"Tool Used: {tool_name}", payload)
        except Exception as e:
            print(f"[Monitoring] track_tool_usage failed: {e}")
