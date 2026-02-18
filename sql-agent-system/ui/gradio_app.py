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
from tools.query_history import get_query_history
import time
import logging
import uuid

logger = logging.getLogger(__name__)

# Initialize metrics and query history
metrics = get_metrics_collector()
query_history = get_query_history()

def process_query(question: str, show_sql: bool = True, show_metrics: bool = True, session_id: str = None):
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
        return "Please enter a question.", "", "", "", "", gr.update(visible=False)
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    start_time = time.time()
    query_id = None
    
    try:
        inputs = {
            "question": question,
            "retry_count": 0,
            "error": None,
            "session_id": session_id
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
        
        # 🧠 LEARNING: Save to query history
        try:
            query_id = query_history.save_query(
                question=question,
                generated_sql=generated_sql,
                success=bool(answer and answer != "No answer generated"),
                error_message=final_state.get("error") if final_state else None,
                execution_time_ms=execution_time,
                row_count=row_count,
                retry_count=retry_count,
                session_id=session_id
            )
            logger.info(f"Saved query to history: ID {query_id}")
        except Exception as e:
            logger.warning(f"Failed to save query history: {e}")
        
        # Return with feedback component visible
        feedback_visible = gr.update(visible=True)
        return answer, sql_display, metrics_info, error_info, query_id, feedback_visible
        
    except Exception as e:
        logger.error(f"UI query processing failed: {e}", exc_info=True)
        return f"❌ Error: {str(e)}", "", "", str(e), None, gr.update(visible=False)

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

def get_learning_stats():
    """Get learning system statistics"""
    try:
        stats = query_history.get_statistics()
        
        learning_text = f"""
## 🧠 Learning Statistics

### Query History
- **Total Queries:** {stats.get('total_queries', 0)}
- **Successful:** {stats.get('successful', 0)}
- **Failed:** {stats.get('failed', 0)}
- **Success Rate:** {stats.get('success_rate', 0):.1f}%

### User Feedback
- **Total Feedback:** {stats.get('total_feedback', 0)}
- **👍 Thumbs Up:** {stats.get('thumbs_up', 0)}
- **👎 Thumbs Down:** {stats.get('thumbs_down', 0)}
- **✏️ Corrections:** {stats.get('corrections', 0)}
- **Avg Rating:** {stats.get('avg_rating', 0) or 0:.1f}/5.0

The system learns from past queries to improve future responses!
"""
        return learning_text
    except Exception as e:
        return f"Learning stats unavailable: {e}"

def submit_feedback(query_id: int, feedback_type: str, rating: int = None, 
                   corrected_sql: str = None, comment: str = None):
    """Submit user feedback for a query"""
    if not query_id:
        return "⚠️ No query to provide feedback for. Please run a query first."
    
    try:
        query_history.add_feedback(
            query_id=query_id,
            feedback_type=feedback_type,
            rating=rating,
            corrected_sql=corrected_sql if corrected_sql and corrected_sql.strip() else None,
            comment=comment if comment and comment.strip() else None
        )
        
        feedback_msg = {
            "thumbs_up": "✅ Thanks! Your positive feedback helps improve the system.",
            "thumbs_down": "📝 Feedback recorded. We'll work on improving this.",
            "correction": "🎓 SQL correction saved! The system will learn from this."
        }
        
        return feedback_msg.get(feedback_type, "✅ Feedback submitted!")
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        return f"❌ Failed to submit feedback: {e}"

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
                gr.Markdown("### 📊 Session Stats")
                stats_display = gr.Markdown("No queries yet")
                refresh_stats_btn = gr.Button("🔄 Refresh Stats")
                
                gr.Markdown("---")
                
                # Learning stats panel
                gr.Markdown("### 🧠 Learning Stats")
                learning_stats_display = gr.Markdown("No learning data yet")
                refresh_learning_btn = gr.Button("🔄 Refresh Learning")
        
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
        
        # 🧠 LEARNING: Feedback Section
        with gr.Row(visible=False) as feedback_row:
            with gr.Column():
                gr.Markdown("### 💬 Rate This Response")
                gr.Markdown("Help the system learn by providing feedback!")
                
                with gr.Row():
                    thumbs_up_btn = gr.Button("👍 Good Answer", variant="primary")
                    thumbs_down_btn = gr.Button("👎 Needs Improvement")
                
                with gr.Accordion("📝 Provide More Details (Optional)", open=False):
                    rating_slider = gr.Slider(
                        minimum=1, maximum=5, step=1, value=3,
                        label="Rating (1-5 stars)"
                    )
                    corrected_sql_input = gr.Textbox(
                        label="Corrected SQL (if you know the right query)",
                        placeholder="Paste corrected SQL here...",
                        lines=3
                    )
                    comment_input = gr.Textbox(
                        label="Additional Comments",
                        placeholder="What could be improved?",
                        lines=2
                    )
                    submit_correction_btn = gr.Button("📤 Submit Detailed Feedback")
                
                feedback_output = gr.Markdown()
        
        # Hidden state to track current query ID
        current_query_id = gr.State(None)
        current_session_id = gr.State(str(uuid.uuid4()))
        
        # Event handlers
        submit_btn.click(
            fn=process_query,
            inputs=[question_input, show_sql, show_metrics, current_session_id],
            outputs=[answer_output, sql_output, metrics_output, error_output, 
                    current_query_id, feedback_row]
        )
        
        refresh_stats_btn.click(
            fn=get_session_stats,
            outputs=stats_display
        )
        
        refresh_learning_btn.click(
            fn=get_learning_stats,
            outputs=learning_stats_display
        )
        
        # Feedback handlers
        thumbs_up_btn.click(
            fn=lambda qid: submit_feedback(qid, "thumbs_up"),
            inputs=[current_query_id],
            outputs=feedback_output
        )
        
        thumbs_down_btn.click(
            fn=lambda qid: submit_feedback(qid, "thumbs_down"),
            inputs=[current_query_id],
            outputs=feedback_output
        )
        
        submit_correction_btn.click(
            fn=lambda qid, rating, sql, comment: submit_feedback(
                qid, "correction", rating, sql, comment
            ),
            inputs=[current_query_id, rating_slider, corrected_sql_input, comment_input],
            outputs=feedback_output
        )
        
        clear_btn.click(
            fn=lambda: ("", "", "", "", None, gr.update(visible=False), ""),
            outputs=[answer_output, sql_output, metrics_output, error_output,
                    current_query_id, feedback_row, feedback_output]
        )
        
        # Footer
        gr.Markdown("""
        ---
        **Powered by:** LangGraph Multi-Agent System | Gemini + Groq | PostgreSQL
        
        **Features:** Semantic RAG • Self-Healing Retry • Security Validation • 🧠 Learning from Feedback
        
        💡 **New:** The system learns from your feedback to improve future responses!
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
