# graph.py
from langgraph.graph import StateGraph, END
from state import AgentState
from agents.intent import intent_agent
from agents.sql_generator import sql_generator_agent
from agents.validator import validator_agent
from agents.responder import responder_agent
from agents.retry_agent import get_retry_decision, get_retry_guidance
from tools.db_connector import DatabaseConnector
import logging

logger = logging.getLogger(__name__)

def execute_db_agent(state):
    """Execute SQL query against real database"""
    print("⚡ [Executor] Running query against database...")
    sql = state["generated_sql"]
    result = DatabaseConnector.execute_query(sql, timeout_seconds=30)
    return {"sql_result": result}

def retry_decision_agent(state):
    """
    Agentic retry decision node - uses LLM to decide if/how to retry.
    This replaces simple rule-based retry logic.
    """
    print("🤔 [Retry Agent] Analyzing failure and deciding strategy...")
    
    # Get intelligent decision from retry agent
    decision = get_retry_decision(state)
    
    should_retry = decision.get("should_retry", False)
    strategy = decision.get("strategy", "abort")
    confidence = decision.get("confidence", 0.0)
    
    logger.info(f"Retry decision: {strategy} (confidence: {confidence:.2f})")
    
    if should_retry and strategy != "abort":
        # Get guidance for next attempt
        guidance = get_retry_guidance(state, decision)
        
        # Inject guidance into state for SQL generator
        return {
            "retry_guidance": guidance,
            "retry_strategy": strategy,
            "retry_count": state["retry_count"] + 1
        }
    else:
        # Abort - pass through to responder with error
        return {
            "retry_count": state["retry_count"],
            "final_answer": f"❌ Unable to process query: {decision.get('reasoning', 'Unknown error')}"
        }

def route_validation(state):
    """
    Conditional routing after validation.
    If error exists, route to retry decision agent (not directly to regenerate).
    """
    # Check if max retries exceeded
    if state.get("retry_count", 0) >= 3:
        logger.warning("Max retries (3) exceeded, aborting")
        return "abort_to_interpret"
    
    if state.get("error"):
        return "retry_decision"  # Let agent decide
    return "execute"

def route_retry_decision(state):
    """
    Route based on retry agent's decision.
    """
    # Check max retries as safety net
    if state.get("retry_count", 0) >= 3:
        logger.warning("Max retries reached in retry_decision")
        return "interpret"
    
    # If we have a final_answer set by retry agent, we're aborting
    if state.get("final_answer"):
        return "interpret"  # Go straight to responder with error message
    
    # Otherwise, retry
    return "regenerate"

def abort_handler(state):
    """Handle max retries exceeded"""
    error = state.get("error", "Unknown error")
    return {
        "final_answer": f"❌ Maximum retry attempts (3) exceeded. Last error: {error}"
    }

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("intent", intent_agent)
workflow.add_node("generate_sql", sql_generator_agent)
workflow.add_node("validate", validator_agent)
workflow.add_node("retry_decision", retry_decision_agent)  # NEW: Agentic retry
workflow.add_node("execute_db", execute_db_agent)
workflow.add_node("interpret", responder_agent)
workflow.add_node("abort_handler", abort_handler)  # Handle max retries

# Define Flow
workflow.set_entry_point("intent")
workflow.add_edge("intent", "generate_sql")
workflow.add_edge("generate_sql", "validate")

# Conditional routing after validation
workflow.add_conditional_edges(
    "validate",
    route_validation,
    {
        "retry_decision": "retry_decision",  # NEW: Route to agent decision
        "execute": "execute_db",
        "abort_to_interpret": "abort_handler"  # Max retries exceeded
    }
)

# Conditional routing after retry decision
workflow.add_conditional_edges(
    "retry_decision",
    route_retry_decision,
    {
        "regenerate": "generate_sql",  # Try again
        "interpret": "interpret"  # Abort with error message
    }
)

workflow.add_edge("execute_db", "interpret")
workflow.add_edge("abort_handler", "interpret")
workflow.add_edge("interpret", END)

# Compile with recursion limit to prevent infinite loops
app = workflow.compile(
    debug=False,
    checkpointer=None,
    interrupt_before=None,
    interrupt_after=None,
)