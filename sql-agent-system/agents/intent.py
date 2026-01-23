from typing import List, Optional
from pydantic import BaseModel, Field
from config import LLMFactory

# --- IMPROVED SCHEMA ---
class UserIntent(BaseModel):
    filters: List[str] = Field(
        default_factory=list,
        description="A LIST of SQL WHERE conditions. Example: ['country=\\'Germany\\'', 'date > \\'2023-01-01\\'']. Return an empty list [] if no filters are needed."
    )
    metrics: List[str] = Field(
        default_factory=list,
        description="A LIST of columns or aggregates to select. Example: ['SUM(total_revenue)', 'product_name']. Default to ['*'] if unsure."
    )

def intent_agent(state):
    print(f"🧠 [Intent Agent] Analyzing: {state['question']}")
    
    try:
        llm = LLMFactory.get_llm("reasoning")
        
        # We bind the schema to the model
        structured_llm = llm.with_structured_output(UserIntent)
        
        # Invoke
        res = structured_llm.invoke(state["question"])
        
        # Convert Pydantic object to standard Dict for the state
        intent_data = res.dict()
        
    except Exception as e:
        print(f"⚠️ Intent Parsing Failed: {e}. Using fallback.")
        # Fallback if the strict JSON parsing fails
        intent_data = {"filters": [], "metrics": ["*"]}

    return {
        "user_intent": intent_data, 
        "retry_count": 0, 
        "error": None
    }