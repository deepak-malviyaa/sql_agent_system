from langchain_core.prompts import ChatPromptTemplate
from config import LLMFactory
import json
import logging

logger = logging.getLogger(__name__)

def responder_agent(state):
    """
    Convert raw SQL results into business-friendly natural language narrative.
    
    This agent:
    1. Checks execution status
    2. Handles empty results gracefully
    3. Uses LLM to generate insights
    4. Formats numerical values appropriately
    """
    print("💬 [Responder] Crafting natural language answer...")
    
    # Extract result from state
    sql_result = state.get("sql_result", {})
    
    # Handle old mock format for backward compatibility
    if isinstance(sql_result, str):
        logger.warning("Received string result (mock format)")
        return {"final_answer": sql_result}
    
    # Check if execution failed
    if not sql_result.get("success"):
        error = sql_result.get("error", "Unknown error occurred")
        error_type = sql_result.get("error_type", "Error")
        logger.error(f"Query execution failed: {error_type} - {error}")
        return {
            "final_answer": f"❌ I couldn't execute the query due to a {error_type}: {error}"
        }
    
    # Extract data
    data = sql_result.get("data", [])
    row_count = sql_result.get("row_count", 0)
    columns = sql_result.get("columns", [])
    
    # Handle empty results
    if row_count == 0:
        logger.info("Query returned no results")
        return {
            "final_answer": "No data found matching your criteria. This could mean:\n"
                          "• The filters are too restrictive\n"
                          "• The time period has no transactions\n"
                          "• The database is empty for this query"
        }
    
    # For very large result sets, inform the user
    if row_count > 100:
        logger.info(f"Large result set: {row_count} rows")
        data_preview = data[:10]
        size_note = f"\n\n📊 Note: Showing insights from {row_count} total rows."
    else:
        data_preview = data[:20]  # Show more for smaller sets
        size_note = ""
    
    # Use LLM to generate natural language narrative
    try:
        llm = LLMFactory.get_llm("fast")  # Use fast model for response generation
        
        prompt = ChatPromptTemplate.from_template("""
You are a professional data analyst presenting query results to a business stakeholder.

Original Question: {question}

SQL Query Used:
{sql}

Result Data (showing first {preview_count} of {total_count} rows):
{data}

Your Task:
1. Answer the question DIRECTLY with the key metric/insight (e.g., "The total revenue from Germany is $45,230.50")
2. If there are multiple rows, summarize the top findings or trends
3. Add ONE brief business insight if applicable (e.g., "This represents the highest sales region")
4. Use clear formatting with numbers formatted properly (e.g., $1,234.56 for currency)
5. Keep it concise (under 150 words)

DO NOT:
- Repeat the question
- Explain what the SQL does
- Apologize or use disclaimers
- List raw data rows unless specifically asked

Response:
""")
        
        chain = prompt | llm
        response = chain.invoke({
            "question": state["question"],
            "sql": state["generated_sql"],
            "data": json.dumps(data_preview, indent=2, default=str),
            "preview_count": len(data_preview),
            "total_count": row_count
        })
        
        final_answer = response.content + size_note
        logger.info("Natural language response generated successfully")
        return {"final_answer": final_answer}
        
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        # Fallback to simple data presentation
        if row_count == 1 and len(columns) == 1:
            # Single value result
            value = data[0][columns[0]]
            return {"final_answer": f"The result is: {value}"}
        else:
            # Multi-row/column result
            summary = f"Query returned {row_count} rows with columns: {', '.join(columns)}\n\n"
            summary += "Sample data:\n"
            for i, row in enumerate(data[:5], 1):
                summary += f"{i}. {json.dumps(row, default=str)}\n"
            return {"final_answer": summary}
