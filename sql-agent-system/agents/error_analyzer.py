# agents/error_analyzer.py
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ErrorAnalyzer:
    """
    Intelligent error classification and recovery suggestions.
    Analyzes SQL execution errors and provides actionable fixes.
    """
    
    # Error pattern matching with recovery suggestions
    ERROR_PATTERNS = {
        "column_not_found": {
            "pattern": r"column \"(\w+)\" does not exist",
            "category": "semantic",
            "severity": "high",
            "suggestion": "Verify column name against schema. Common mistake: confusing 'total_revenue' with 'revenue'."
        },
        "table_not_found": {
            "pattern": r"relation \"(\w+)\" does not exist",
            "category": "semantic",
            "severity": "critical",
            "suggestion": "Ensure table name is correct. For this database, use 'sales_data'."
        },
        "syntax_error": {
            "pattern": r"syntax error at or near \"(\w+)\"",
            "category": "syntax",
            "severity": "high",
            "suggestion": "Check SQL syntax. Look for missing commas, parentheses, or keywords."
        },
        "type_mismatch": {
            "pattern": r"operator does not exist|cannot cast|invalid input syntax",
            "category": "type",
            "severity": "medium",
            "suggestion": "Type mismatch detected. Ensure date formats use 'YYYY-MM-DD' and numbers aren't quoted."
        },
        "aggregate_misuse": {
            "pattern": r"must appear in the GROUP BY clause",
            "category": "logic",
            "severity": "medium",
            "suggestion": "Add missing columns to GROUP BY clause or wrap them in aggregate functions."
        },
        "division_by_zero": {
            "pattern": r"division by zero",
            "category": "runtime",
            "severity": "medium",
            "suggestion": "Add WHERE clause to filter out zero values before division."
        }
    }
    
    @classmethod
    def analyze(cls, error_msg: str) -> Dict[str, any]:
        """
        Analyze error message and classify error type.
        
        Args:
            error_msg: Raw error message from database
            
        Returns:
            Dict with error_type, category, severity, and suggestion
        """
        if not error_msg:
            return {
                "error_type": "unknown",
                "category": "unknown",
                "severity": "low",
                "suggestion": "No specific error information available."
            }
        
        # Try to match against known patterns
        for error_type, config in cls.ERROR_PATTERNS.items():
            if re.search(config["pattern"], error_msg, re.IGNORECASE):
                # Extract specific entity (column/table name) if available
                match = re.search(config["pattern"], error_msg, re.IGNORECASE)
                entity = match.group(1) if match and match.groups() else None
                
                logger.info(f"Error classified as: {error_type} (severity: {config['severity']})")
                
                return {
                    "error_type": error_type,
                    "category": config["category"],
                    "severity": config["severity"],
                    "suggestion": config["suggestion"],
                    "entity": entity,
                    "original_message": error_msg
                }
        
        # Fallback for unrecognized errors
        logger.warning(f"Unrecognized error pattern: {error_msg[:100]}")
        return {
            "error_type": "unknown",
            "category": "unknown",
            "severity": "medium",
            "suggestion": "Review the SQL query for common mistakes: typos, missing quotes, or incorrect syntax.",
            "original_message": error_msg
        }
    
    @classmethod
    def get_recovery_prompt(cls, error_analysis: Dict, original_sql: str) -> str:
        """
        Generate a recovery prompt for the SQL regeneration agent.
        
        Args:
            error_analysis: Output from analyze()
            original_sql: The SQL that failed
            
        Returns:
            Detailed prompt for fixing the error
        """
        error_type = error_analysis["error_type"]
        category = error_analysis["category"]
        suggestion = error_analysis["suggestion"]
        entity = error_analysis.get("entity")
        
        prompt = f"""
PREVIOUS SQL FAILED: {error_type} ({category})

Failed SQL:
{original_sql}

Error Details:
{error_analysis['original_message']}

Recovery Guidance:
{suggestion}
"""
        
        # Add specific instructions based on error type
        if error_type == "column_not_found" and entity:
            prompt += f\"\"\"

CRITICAL: The column '{entity}' does not exist in the database.
Valid columns are: id, transaction_date, product_category, product_name, 
units_sold, unit_price, total_revenue, country, payment_method

Action Required: Replace '{entity}' with the correct column name.
\"\"\"
        
        elif error_type == "table_not_found" and entity:
            prompt += f\"\"\"

CRITICAL: The table '{entity}' does not exist.
The only available table is: sales_data

Action Required: Use 'sales_data' as the table name.
\"\"\"
        
        elif error_type == "aggregate_misuse":
            prompt += \"\"\"

Action Required: 
1. Add all non-aggregated SELECT columns to GROUP BY
2. OR wrap them in aggregate functions (SUM, AVG, COUNT, etc.)
\"\"\"
        
        return prompt


class ErrorRecoveryTracker:
    """
    Track error patterns across retries to prevent infinite loops.
    """
    
    def __init__(self):
        self.error_history: List[Dict] = []
    
    def add_error(self, error_analysis: Dict, sql: str):
        \"\"\"Record an error occurrence\"\"\"
        self.error_history.append({
            "error_type": error_analysis["error_type"],
            "sql_hash": hash(sql.strip().lower()),
            "timestamp": None  # Add timestamp if needed
        })
    
    def is_repeating_error(self) -> bool:
        \"\"\"
        Detect if the same error type is repeating.
        Returns True if last 2 errors are the same.
        \"\"\"
        if len(self.error_history) < 2:
            return False
        
        recent_errors = [e["error_type"] for e in self.error_history[-2:]]
        return len(set(recent_errors)) == 1
    
    def is_sql_unchanged(self) -> bool:
        \"\"\"
        Detect if SQL hasn't changed between retries.
        Returns True if last 2 SQL hashes are identical.
        \"\"\"
        if len(self.error_history) < 2:
            return False
        
        recent_hashes = [e["sql_hash"] for e in self.error_history[-2:]]
        return recent_hashes[0] == recent_hashes[1]
    
    def should_abort(self) -> bool:
        \"\"\"
        Decide if we should stop retrying.
        Abort if same error repeats or SQL doesn't change.
        \"\"\"
        return self.is_repeating_error() or self.is_sql_unchanged()
