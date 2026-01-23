# agents/validator.py
import re
import logging

logger = logging.getLogger(__name__)

def validator_agent(state):
    """
    Multi-layer SQL validation:
    1. Security guardrails (forbidden operations)
    2. Basic syntax checks
    3. PostgreSQL EXPLAIN validation
    4. Semantic column/table existence checks
    """
    print("🛡️ [Validator] Running security & syntax checks...")
    sql = state["generated_sql"]
    sql_upper = sql.upper()
    
    # --- Layer 1: Security Guardrails ---
    # Prevent destructive operations
    forbidden = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", 
                 "GRANT", "REVOKE", "CREATE", "EXEC", "EXECUTE"]
    
    for word in forbidden:
        # Use word boundary to avoid false positives (e.g., "DROP" in "BACKDROP")
        if re.search(rf"\b{word}\b", sql_upper):
            logger.warning(f"Security violation: '{word}' operation detected")
            return {
                "error": f"🚫 Security Risk: '{word}' operation not allowed. Only SELECT queries permitted.",
                "retry_count": state["retry_count"] + 1
            }
    
    # --- Layer 2: Basic Syntax Validation ---
    if "SELECT" not in sql_upper:
        logger.warning("Invalid query: Missing SELECT statement")
        return {
            "error": "❌ Invalid Syntax: Must be a SELECT statement.",
            "retry_count": state["retry_count"] + 1
        }
    
    # Check for suspicious patterns
    suspicious_patterns = [
        (r"--;.*DROP", "SQL injection attempt detected"),
        (r"'\s*OR\s*'1'\s*=\s*'1", "SQL injection pattern detected"),
        (r"UNION.*SELECT", "UNION-based injection attempt detected")
    ]
    
    for pattern, error_msg in suspicious_patterns:
        if re.search(pattern, sql_upper):
            logger.warning(f"Security threat: {error_msg}")
            return {
                "error": f"🚫 {error_msg}",
                "retry_count": state["retry_count"] + 1
            }
    
    # --- Layer 3: PostgreSQL EXPLAIN Validation ---
    # This actually tests the SQL against the database without executing it
    try:
        from tools.db_connector import DatabaseConnector
        
        explain_sql = f"EXPLAIN {sql}"
        result = DatabaseConnector.execute_query(explain_sql, timeout_seconds=5)
        
        if not result["success"]:
            error_msg = result.get("error", "Unknown syntax error")
            logger.warning(f"EXPLAIN failed: {error_msg}")
            
            # Parse common errors and provide helpful messages
            if "column" in error_msg.lower() and "does not exist" in error_msg.lower():
                return {
                    "error": f"❌ Column Error: {error_msg}\n💡 Hint: Check the schema for correct column names.",
                    "retry_count": state["retry_count"] + 1
                }
            elif "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
                return {
                    "error": f"❌ Table Error: {error_msg}\n💡 Hint: Verify the table name is 'sales_data'.",
                    "retry_count": state["retry_count"] + 1
                }
            else:
                return {
                    "error": f"❌ Syntax Error: {error_msg}",
                    "retry_count": state["retry_count"] + 1
                }
        else:
            # EXPLAIN passed - SQL is valid!
            logger.info("SQL validation passed all checks (EXPLAIN successful)")
            return {"error": None}  # All checks passed!
            
    except ImportError:
        logger.warning("DatabaseConnector not available, skipping EXPLAIN validation")
    except Exception as e:
        logger.error(f"EXPLAIN validation error: {e}")
        return {
            "error": f"⚠️ Validation failed: {str(e)}",
            "retry_count": state["retry_count"] + 1
        }
    
    # If we reach here (no EXPLAIN or it was skipped), assume valid
    logger.info("SQL validation passed (no EXPLAIN available)")
    return {"error": None}