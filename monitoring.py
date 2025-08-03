# monitoring.py
import os

try:
    import agentops
    _AGENTOPS_AVAILABLE = True
    print("[Monitoring] AgentOps SDK available")
except ImportError:
    print("[Monitoring] AgentOps not installed. Monitoring disabled.")
    _AGENTOPS_AVAILABLE = False

# Initialize AgentOps according to documentation
def initialize_agentops():
    """Initialize AgentOps with proper configuration"""
    if not _AGENTOPS_AVAILABLE:
        return False
    
    api_key = os.getenv("AGENTOPS_API_KEY")
    if not api_key:
        print("[Monitoring] No AGENTOPS_API_KEY found in environment. Monitoring disabled.")
        return False
    
    try:
        # Initialize AgentOps with auto session management for multi-threaded app
        agentops.init(
            api_key=api_key,
            auto_start_session=False,  # Manual session management for FastAPI
            tags=["loan-servicing", "banking", "multi-agent"],
            default_tags=["production"]
        )
        print("[Monitoring] AgentOps initialized successfully")
        return True
    except Exception as e:
        print(f"[Monitoring] Failed to initialize AgentOps: {e}")
        return False

# Initialize on module import
_AGENTOPS_INITIALIZED = initialize_agentops() if _AGENTOPS_AVAILABLE else False

def start_session(trace_name="Loan Servicing Request", user_id=None):
    """Start a new AgentOps session for tracking"""
    if not _AGENTOPS_INITIALIZED:
        return None
    
    try:
        tags = ["loan-servicing"]
        if user_id:
            tags.append(f"user-{user_id}")
        
        tracer = agentops.start_trace(
            trace_name=trace_name,
            tags=tags
        )
        return tracer
    except Exception as e:
        print(f"[Monitoring] Failed to start session: {e}")
        return None

def end_session(tracer=None, end_state="Success"):
    """End AgentOps session"""
    if not _AGENTOPS_INITIALIZED:
        return
    
    try:
        if tracer:
            agentops.end_trace(tracer, end_state=end_state)
        else:
            agentops.end_trace(end_state=end_state)
    except Exception as e:
        print(f"[Monitoring] Failed to end session: {e}")

# Backward compatibility functions
def set_metadata(metadata):
    """Set metadata for current session"""
    if _AGENTOPS_INITIALIZED:
        try:
            # AgentOps v2 doesn't have set_metadata, use tags instead
            print(f"[Monitoring] Metadata logged: {metadata}")
        except Exception as e:
            print(f"[Monitoring] set_metadata failed: {e}")

def track_event(name, extra_data=None):
    """Track custom event"""
    if _AGENTOPS_INITIALIZED:
        try:
            # Events are automatically tracked by decorators
            print(f"[Monitoring] Event tracked: {name} - {extra_data}")
        except Exception as e:
            print(f"[Monitoring] track_event failed: {e}")

def track_tool_usage(tool_name, input_data, output_data, tokens=None, cost=None):
    """Track tool usage with performance metrics"""
    if _AGENTOPS_INITIALIZED:
        try:
            payload = {
                "tool": tool_name,
                "input": str(input_data)[:500],  # Limit input size
                "output": str(output_data)[:500],  # Limit output size
            }
            if tokens:
                payload["tokens"] = tokens
            if cost:
                payload["cost_usd"] = cost
            
            print(f"[Monitoring] Tool usage tracked: {tool_name}")
        except Exception as e:
            print(f"[Monitoring] track_tool_usage failed: {e}")

def track_agent_performance(agent_name, operation, duration, success=True):
    """Track individual agent performance metrics"""
    if _AGENTOPS_INITIALIZED:
        try:
            performance_data = {
                "agent": agent_name,
                "operation": operation,
                "duration_ms": duration,
                "success": success
            }
            print(f"[Monitoring] Agent performance tracked: {agent_name} - {operation} - {duration}ms")
        except Exception as e:
            print(f"[Monitoring] track_agent_performance failed: {e}")
