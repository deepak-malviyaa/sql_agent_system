# ui/gradio_app.py
"""
Gradio Web UI for SQL Agent System
Provides interactive interface for natural language database queries
"""

import gradio as gr
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import app
from utils.metrics import get_metrics_collector, QueryMetrics
import time
import logging

logger = logging.getLogger(__name__)

# Initialize metrics
metrics = get_metrics_collector()

def process_query(question: str, show_sql: bool = True, show_metrics: bool = True):
    """
    Process a natural language query through the agent system.
    
    Args:
        question: User's natural language question
        show_sql: Whether to display generated SQL
        show_metrics: Whether to display execution metrics
        
    Returns:
        Tuple of (answer, sql, metrics_info, error_info)
    """
    if not question or not question.strip():
        return "Please enter a question.", "", "", ""
    
    start_time = time.time()
    
    try:
        inputs = {
            "question": question,
            "retry_count": 0,
            "error": None
        }
        
        # Track execution stages
        stages_info = []
        final_state = None
        generated_sql = ""
        retry_count = 0
        
        # Stream through agents with recursion limit
        for output in app.stream(inputs, {"recursion_limit": 50}):
            for agent_name, agent_state in output.items():
                stages_info.append(f"✅ {agent_name}")
                final_state = agent_state
                
                if "generated_sql" in agent_state:
                    generated_sql = agent_state["generated_sql"]
                
                if "retry_count" in agent_state:
                    retry_count = agent_state["retry_count"]
        
        execution_time = (time.time() - start_time) * 1000
        
        # Build response
        answer = final_state.get("final_answer", "No answer generated") if final_state else "Processing failed"
        
        # SQL display
        sql_display = f"```sql\n{generated_sql}\n```" if show_sql and generated_sql else ""
        
        # Metrics display
        metrics_info = ""
        if show_metrics:
            metrics_info = f"""
### Execution Metrics
- **Time:** {execution_time:.0f}ms
- **Retries:** {retry_count}
- **Stages:** {' → '.join(stages_info)}
"""
        
        # Error info
        error_info = ""
        if final_state and final_state.get("error"):
            error_info = f"⚠️ **Warning:** {final_state['error']}"
        
        # Log metrics
        row_count = None
        if final_state and "sql_result" in final_state:
            sql_result = final_state["sql_result"]
            if isinstance(sql_result, dict):
                row_count = sql_result.get("row_count")
        
        query_metrics = QueryMetrics(
            question=question,
            sql_generated=generated_sql or "N/A",
            success=bool(answer and answer != "No answer generated"),
            retry_count=retry_count,
            execution_time_ms=execution_time,
            row_count=row_count
        )
        metrics.log_query(query_metrics)
        
        return answer, sql_display, metrics_info, error_info
        
    except Exception as e:
        logger.error(f"UI query processing failed: {e}", exc_info=True)
        return f"❌ Error: {str(e)}", "", "", str(e)

def get_session_stats():
    """Get current session statistics"""
    summary = metrics.get_session_summary()
    
    stats_text = f"""
## Session Statistics

- **Total Queries:** {summary['total_queries']}
- **Success Rate:** {summary['success_rate']:.1f}%
- **Avg Retries:** {summary['avg_retries']:.2f}
- **Avg Execution Time:** {summary['avg_execution_time_ms']:.0f}ms
"""
    
    if summary.get('most_common_errors'):
        stats_text += "\n### Top Errors:\n"
        for error, count in summary['most_common_errors']:
            stats_text += f"- {error}: {count} occurrences\n"
    
    return stats_text

def create_ui():
    """Create and configure Gradio interface"""
    
    # Custom CSS for better styling
    custom_css = """
    .gradio-container {
        font-family: 'Arial', sans-serif;
    }
    .output-markdown {
        min-height: 100px;
    }
    """
    
    with gr.Blocks(css=custom_css, title="SQL Agent System", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🤖 SQL Agent System - Natural Language Database Interface
        
        Ask questions about your data in plain English. The AI agents will:
        1. 🧠 Parse your intent
        2. 🔍 Retrieve relevant schema
        3. ⚡ Generate SQL query
        4. 🛡️ Validate for security
        5. 💬 Return human-friendly answer
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                # Input section
                question_input = gr.Textbox(
                    label="Your Question",
                    placeholder="e.g., What's the total revenue from Germany?",
                    lines=2
                )
                
                with gr.Row():
                    show_sql = gr.Checkbox(label="Show SQL", value=True)
                    show_metrics = gr.Checkbox(label="Show Metrics", value=True)
                
                with gr.Row():
                    submit_btn = gr.Button("🚀 Execute Query", variant="primary", size="lg")
                    clear_btn = gr.Button("🗑️ Clear", size="lg")
                
                # Example queries
                gr.Examples(
                    examples=[
                        "What is the total revenue?",
                        "Show me revenue by country",
                        "Top 5 products by sales",
                        "Revenue from Electronics in USA",
                        "Average order value by payment method"
                    ],
                    inputs=question_input,
                    label="Example Queries"
                )
            
            with gr.Column(scale=1):
                # Stats panel
                stats_display = gr.Markdown("### Session Stats\nNo queries yet")
                refresh_stats_btn = gr.Button("🔄 Refresh Stats")
        
        # Output section
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🤖 Answer")
                answer_output = gr.Markdown()
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📊 SQL Query")
                sql_output = gr.Markdown()
            
            with gr.Column():
                gr.Markdown("### 📈 Metrics")
                metrics_output = gr.Markdown()
        
        with gr.Row():
            with gr.Column():
                error_output = gr.Markdown()
        
        # Event handlers
        submit_btn.click(
            fn=process_query,
            inputs=[question_input, show_sql, show_metrics],
            outputs=[answer_output, sql_output, metrics_output, error_output]
        )
        
        refresh_stats_btn.click(
            fn=get_session_stats,
            outputs=stats_display
        )
        
        clear_btn.click(
            fn=lambda: ("", "", "", ""),
            outputs=[answer_output, sql_output, metrics_output, error_output]
        )
        
        # Footer
        gr.Markdown("""
        ---
        **Powered by:** LangGraph Multi-Agent System | Gemini + Groq | PostgreSQL
        
        **Features:** Semantic RAG • Self-Healing Retry • Security Validation • Natural Language Output
        """)
    
    return demo

def launch_ui(share=False, server_port=7860):
    """Launch the Gradio interface"""
    # Setup logging
    from logging_config import setup_logging
    setup_logging(logging.INFO)
    
    logger.info("Launching Gradio UI...")
    
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=server_port,
        share=share,
        show_error=True
    )

if __name__ == "__main__":
    launch_ui(share=False)
