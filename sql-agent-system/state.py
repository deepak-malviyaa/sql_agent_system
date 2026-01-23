# state.py
from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    question: str
    user_intent: dict          # Structured goal, filters
    relevant_schema: str       # RAG output
    generated_sql: str         # The SQL Code
    sql_result: str            # Raw rows from DB
    error: Optional[str]       # Error message if validation fails
    retry_count: int           # To prevent infinite loops
    retry_guidance: Optional[str]  # Agentic guidance for next retry
    retry_strategy: Optional[str]  # Strategy: retry_with_schema, retry_simpler, etc.
    final_answer: str          # Natural language response