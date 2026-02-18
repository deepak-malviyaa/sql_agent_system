from graph import app
from logging_config import setup_logging
from utils.metrics import get_metrics_collector, QueryMetrics
from tools.query_history import get_query_history
import logging
import time
import uuid

# Initialize production-grade logging
setup_logging(logging.INFO)
logger = logging.getLogger(__name__)

# Initialize metrics collector and query history
metrics = get_metrics_collector()
query_history = get_query_history()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 SQL AGENT SYSTEM - PRODUCTION MODE")
    print("   Architecture: Multi-Agent LangGraph")
    print("   Models: Gemini (Reasoning) + Groq (Speed)")
    print("   Database: PostgreSQL with connection pooling")
    print("   Features: RAG Schema, Self-healing, 🧠 Learning")
    print("   Type 'exit', 'quit', 'stats', or 'learning' for options")
    print("="*50 + "\n")
    
    logger.info("System started in interactive mode")
    session_id = str(uuid.uuid4())

    while True:
        try:
            # FEATURE: Interactive Input
            user_q = input("👉 Ask a question: ").strip()
            
            # FEATURE: Special Commands
            if user_q.lower() in ["exit", "quit", "q"]:
                metrics.print_session_summary()
                print("\n🧠 Learning Summary:")
                stats = query_history.get_statistics()
                print(f"   📚 Total queries learned: {stats['total_queries']}")
                print(f"   💯 Success rate: {stats['success_rate']:.1f}%")
                print("👋 Exiting. Goodbye!")
                logger.info("System shutdown by user")
                break
            
            if user_q.lower() == "stats":
                metrics.print_session_summary()
                continue
            
            if user_q.lower() == "learning":
                stats = query_history.get_statistics()
                print("\n" + "="*50)
                print("🧠 LEARNING SYSTEM STATISTICS")
                print("="*50)
                print(f"📊 Total Queries: {stats['total_queries']}")
                print(f"✅ Successful: {stats['successful']}")
                print(f"❌ Failed: {stats['failed']}")
                print(f"💯 Success Rate: {stats['success_rate']:.1f}%")
                print(f"👍 Positive Feedback: {stats['thumbs_up']}")
                print(f"👎 Negative Feedback: {stats['thumbs_down']}")
                print(f"✏️ User Corrections: {stats['corrections']}")
                if stats['avg_rating']:
                    print(f"⭐ Avg Rating: {stats['avg_rating']:.1f}/5.0")
                print("="*50 + "\n")
                continue
            
            if not user_q:
                continue

            # Start timing
            start_time = time.time()
            
            # Prepare Initial State
            inputs = {
                "question": user_q,
                "retry_count": 0,
                "error": None,
                "session_id": session_id
            }

            logger.info(f"Processing query: {user_q}")
            print(f"\n🔄 Processing: '{user_q}'...\n")
            
            # FEATURE: Real-time Streaming
            final_response = None
            generated_sql = None
            sql_result = None
            final_error = None
            retry_count = 0
            
            # Stream the steps to see agents working
            for output in app.stream(inputs, {"recursion_limit": 50}):
                for agent_name, agent_state in output.items():
                    print(f"   🔹 Finished: {agent_name}")
                    
                    # Capture metrics
                    if "final_answer" in agent_state:
                        final_response = agent_state["final_answer"]
                    
                    if "generated_sql" in agent_state:
                        generated_sql = agent_state["generated_sql"]
                        print(f"      [SQL]: {agent_state['generated_sql'][:100]}...")
                    
                    if "sql_result" in agent_state:
                        sql_result = agent_state["sql_result"]
                    
                    if "error" in agent_state and agent_state["error"]:
                        final_error = agent_state["error"]
                        print(f"      [Guardrail]: ⚠️ {agent_state['error'][:80]}...")
                    
                    if "retry_count" in agent_state:
                        retry_count = agent_state["retry_count"]

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Print Final Result cleanly
            print("\n" + "-"*40)
            if final_response:
                print(f"🤖 ANSWER:\n{final_response}")
                success = True
            else:
                print("⚠️ No answer generated.")
                success = False
            print("-"*40 + "\n")
            
            # Log metrics
            row_count = None
            if sql_result and isinstance(sql_result, dict):
                row_count = sql_result.get("row_count")
            
            query_metrics = QueryMetrics(
                question=user_q,
                sql_generated=generated_sql or "N/A",
                success=success,
                retry_count=retry_count,
                execution_time_ms=execution_time_ms,
                row_count=row_count,
                error_type=final_error[:50] if final_error else None
            )
            metrics.log_query(query_metrics)
            
            # 🧠 LEARNING: Save to query history
            try:
                query_id = query_history.save_query(
                    question=user_q,
                    generated_sql=generated_sql,
                    success=success,
                    error_message=final_error,
                    execution_time_ms=execution_time_ms,
                    row_count=row_count,
                    retry_count=retry_count,
                    session_id=session_id
                )
                logger.info(f"Query saved to learning system (ID: {query_id})")
            except Exception as e:
                logger.warning(f"Failed to save to learning system: {e}")
            
            logger.info(f"Query completed: success={success}, time={execution_time_ms:.0f}ms, retries={retry_count}")

        except KeyboardInterrupt:
            print("\n👋 Force Quit.")
            logger.info("System interrupted by user (Ctrl+C)")
            metrics.print_session_summary()
            break
        except Exception as e:
            print(f"\n❌ SYSTEM ERROR: {str(e)}\n")
            logger.error(f"Unhandled exception: {e}", exc_info=True)