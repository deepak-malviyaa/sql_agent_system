# agents/retry_agent.py
"""
Agentic Retry Mechanism
Uses LLM to analyze failures and decide retry strategy
"""

from typing import Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from config import LLMFactory
import logging

logger = logging.getLogger(__name__)

class RetryDecisionAgent:
    """
    Intelligent agent that decides whether and how to retry failed queries.
    Uses LLM reasoning instead of simple rule-based logic.
    """
    
    def __init__(self):
        self.llm = LLMFactory.get_llm("reasoning")
        self.retry_history = []
    
    def should_retry(self, state: Dict) -> Dict[str, any]:
        """
        Agent-based decision on whether to retry.
        
        Instead of simple retry_count > 3, we use LLM to analyze:
        - Nature of the error
        - Previous retry attempts
        - Likelihood of success with retry
        - Alternative approaches
        """
        error = state.get("error")
        retry_count = state.get("retry_count", 0)
        question = state.get("question", "")
        generated_sql = state.get("generated_sql", "")
        
        # Store in history
        self.retry_history.append({
            "error": error,
            "sql": generated_sql,
            "retry_count": retry_count
        })
        
        # If no error, proceed
        if not error:
            return {"should_retry": False, "strategy": "none"}
        
        # Use LLM to analyze the situation
        prompt = ChatPromptTemplate.from_template("""
You are a retry strategy expert for a SQL generation system.

Context:
- User Question: {question}
- Current Retry Count: {retry_count}
- Failed SQL: {sql}
- Error Message: {error}
- Previous Retry History: {history}

Your Task:
Analyze whether we should retry and what strategy to use.

Decision Criteria:
1. If retry_count >= 3, generally should NOT retry (unless fixable)
2. Syntax errors are usually fixable - retry with corrections
3. Security violations (DROP, DELETE) should NEVER retry - abort immediately
4. Column not found errors - retry with schema clarification
5. Timeout errors - retry with simpler query
6. Same error repeating - abort (we're stuck)

Respond in JSON format:
{{
  "should_retry": true/false,
  "confidence": 0.0-1.0,
  "strategy": "abort" | "retry_with_schema" | "retry_simpler" | "retry_corrected",
  "reasoning": "Brief explanation",
  "suggested_fix": "Specific instruction for next attempt"
}}
        """)
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({
                "question": question,
                "retry_count": retry_count,
                "sql": generated_sql,
                "error": error,
                "history": self._format_history()
            })
            
            # Parse LLM response (assuming JSON output)
            import json
            import re
            
            # Extract JSON from response
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                decision = json.loads(json_match.group())
                logger.info(f"Retry decision: {decision['strategy']} (confidence: {decision['confidence']})")
                return decision
            else:
                # Fallback to simple logic
                logger.warning("LLM response parsing failed, using fallback logic")
                return self._fallback_decision(retry_count, error)
                
        except Exception as e:
            logger.error(f"Retry agent failed: {e}")
            return self._fallback_decision(retry_count, error)
    
    def _fallback_decision(self, retry_count: int, error: str) -> Dict:
        """Simple rule-based fallback if LLM fails"""
        # Hard limit on retries
        if retry_count >= 2:  # Changed from 3 to 2 for faster abort
            return {
                "should_retry": False,
                "strategy": "abort",
                "reasoning": "Maximum retries exceeded",
                "confidence": 1.0
            }
        
        # Never retry security violations
        if "Security" in error or "DROP" in error or "DELETE" in error:
            return {
                "should_retry": False,
                "strategy": "abort",
                "reasoning": "Security violation - cannot retry",
                "confidence": 1.0
            }
        
        # Check if same error repeating (stuck in loop)
        if len(self.retry_history) >= 2:
            recent_errors = [h['error'][:50] for h in self.retry_history[-2:]]
            if len(set(recent_errors)) == 1:  # Same error twice
                logger.warning("Same error repeating - aborting")
                return {
                    "should_retry": False,
                    "strategy": "abort",
                    "reasoning": "Same error repeating - unable to fix",
                    "confidence": 0.9
                }
        
        return {
            "should_retry": True,
            "strategy": "retry_corrected",
            "reasoning": "Fixable error, retrying",
            "confidence": 0.7
        }
    
    def _format_history(self) -> str:
        """Format retry history for LLM context"""
        if not self.retry_history:
            return "No previous retries"
        
        return "\n".join([
            f"Attempt {i+1}: {h['error'][:50]}..." 
            for i, h in enumerate(self.retry_history[-3:])  # Last 3 attempts
        ])
    
    def get_retry_guidance(self, state: Dict, decision: Dict) -> str:
        """
        Generate specific guidance for the next retry attempt.
        This is sent to the SQL generator agent.
        """
        strategy = decision.get("strategy", "retry_corrected")
        error = state.get("error", "")
        suggested_fix = decision.get("suggested_fix", "")
        
        if strategy == "abort":
            return "ABORT: " + decision.get("reasoning", "Cannot proceed")
        
        elif strategy == "retry_with_schema":
            return f"""
RETRY STRATEGY: Schema Clarification

Previous Error: {error}

Action Required:
1. Carefully review the schema provided
2. Verify exact column names (case-sensitive)
3. Ensure table name is correct
4. Use only columns that exist in the schema

Suggested Fix: {suggested_fix}
"""
        
        elif strategy == "retry_simpler":
            return f"""
RETRY STRATEGY: Simplify Query

Previous Error: {error}

Action Required:
1. Remove complex joins or subqueries
2. Use simpler aggregations
3. Add LIMIT clause if missing
4. Break down complex logic into steps

Suggested Fix: {suggested_fix}
"""
        
        else:  # retry_corrected
            return f"""
RETRY STRATEGY: Corrected Approach

Previous Error: {error}

Action Required:
1. Fix the specific error identified
2. Double-check syntax
3. Verify data types match

Suggested Fix: {suggested_fix}
"""

# Singleton instance
_retry_agent = RetryDecisionAgent()

def get_retry_decision(state: Dict) -> Dict:
    """Public API for retry decisions"""
    return _retry_agent.should_retry(state)

def get_retry_guidance(state: Dict, decision: Dict) -> str:
    """Public API for retry guidance"""
    return _retry_agent.get_retry_guidance(state, decision)
