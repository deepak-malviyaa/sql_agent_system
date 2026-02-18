"""
Setup Script for Learning System

This script initializes the learning database and tests the learning features.
Run this once to set up the query history and learning capabilities.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.query_history import QueryHistory
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def setup_learning_system():
    """Initialize and test the learning system"""
    
    print("="*60)
    print("🧠 SQL AGENT LEARNING SYSTEM SETUP")
    print("="*60)
    print()
    
    # Step 1: Create data directory
    print("📁 Step 1: Creating data directory...")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    print(f"   ✅ Data directory: {data_dir.absolute()}")
    print()
    
    # Step 2: Initialize query history database
    print("💾 Step 2: Initializing query history database...")
    try:
        query_history = QueryHistory()
        print("   ✅ Database initialized successfully")
        print(f"   📊 Database location: {query_history.db_path}")
    except Exception as e:
        print(f"   ❌ Failed to initialize database: {e}")
        return False
    print()
    
    # Step 3: Test embedding generation
    print("🔢 Step 3: Testing embedding generation...")
    try:
        test_question = "What is the total revenue?"
        embedding = query_history.embeddings.embed_query(test_question)
        print(f"   ✅ Embedding generated successfully")
        print(f"   📏 Embedding dimensions: {len(embedding)}")
    except Exception as e:
        print(f"   ❌ Failed to generate embedding: {e}")
        return False
    print()
    
    # Step 4: Test query saving
    print("💾 Step 4: Testing query save functionality...")
    try:
        query_id = query_history.save_query(
            question="What is the total revenue from Germany?",
            generated_sql="SELECT SUM(amount) FROM sales WHERE country = 'Germany';",
            success=True,
            execution_time_ms=45.2,
            row_count=1,
            retry_count=0,
            session_id="test_session_1"
        )
        print(f"   ✅ Query saved successfully (ID: {query_id})")
    except Exception as e:
        print(f"   ❌ Failed to save query: {e}")
        return False
    print()
    
    # Step 5: Test feedback saving
    print("💬 Step 5: Testing feedback functionality...")
    try:
        query_history.add_feedback(
            query_id=query_id,
            feedback_type="thumbs_up",
            rating=5,
            comment="Perfect answer!"
        )
        print(f"   ✅ Feedback saved successfully")
    except Exception as e:
        print(f"   ❌ Failed to save feedback: {e}")
        return False
    print()
    
    # Step 6: Test similarity search
    print("🔍 Step 6: Testing similarity search...")
    try:
        similar = query_history.find_similar_queries(
            "Show me revenue from France",
            limit=3
        )
        print(f"   ✅ Similarity search working")
        print(f"   📊 Found {len(similar)} similar queries")
        if similar:
            print(f"   🎯 Most similar: '{similar[0]['question']}' (similarity: {similar[0]['similarity']:.2f})")
    except Exception as e:
        print(f"   ❌ Failed similarity search: {e}")
        return False
    print()
    
    # Step 7: Add more sample data
    print("📚 Step 7: Adding sample learning data...")
    sample_queries = [
        {
            "question": "Show me sales by product category",
            "sql": "SELECT category, SUM(amount) as total FROM sales JOIN products ON sales.product_id = products.id GROUP BY category;",
            "success": True,
            "time": 67.3,
            "rows": 5
        },
        {
            "question": "Top 10 customers by purchase volume",
            "sql": "SELECT customer_name, COUNT(*) as orders FROM sales GROUP BY customer_name ORDER BY orders DESC LIMIT 10;",
            "success": True,
            "time": 52.1,
            "rows": 10
        },
        {
            "question": "Revenue by payment method",
            "sql": "SELECT payment_method, SUM(amount) FROM sales GROUP BY payment_method;",
            "success": True,
            "time": 41.5,
            "rows": 3
        },
        {
            "question": "Average order value by country",
            "sql": "SELECT country, AVG(amount) as avg_order FROM sales GROUP BY country;",
            "success": True,
            "time": 58.9,
            "rows": 8
        },
        {
            "question": "Monthly revenue trend",
            "sql": "SELECT DATE_TRUNC('month', order_date) as month, SUM(amount) FROM sales GROUP BY month ORDER BY month;",
            "success": True,
            "time": 72.4,
            "rows": 12
        }
    ]
    
    added_count = 0
    for sample in sample_queries:
        try:
            qid = query_history.save_query(
                question=sample["question"],
                generated_sql=sample["sql"],
                success=sample["success"],
                execution_time_ms=sample["time"],
                row_count=sample["rows"],
                retry_count=0,
                session_id="setup_samples"
            )
            # Add positive feedback to some
            if added_count % 2 == 0:
                query_history.add_feedback(qid, "thumbs_up", rating=4)
            added_count += 1
        except Exception as e:
            print(f"   ⚠️ Warning: Failed to add sample query: {e}")
    
    print(f"   ✅ Added {added_count} sample queries")
    print()
    
    # Step 8: Display statistics
    print("📊 Step 8: Learning system statistics...")
    try:
        stats = query_history.get_statistics()
        print(f"   📈 Total queries in history: {stats['total_queries']}")
        print(f"   ✅ Successful queries: {stats['successful']}")
        print(f"   ❌ Failed queries: {stats['failed']}")
        print(f"   💯 Success rate: {stats['success_rate']:.1f}%")
        print(f"   👍 Thumbs up: {stats['thumbs_up']}")
        print(f"   ⭐ Average rating: {stats['avg_rating'] or 0:.1f}/5.0")
    except Exception as e:
        print(f"   ⚠️ Could not retrieve statistics: {e}")
    print()
    
    # Final summary
    print("="*60)
    print("✅ LEARNING SYSTEM SETUP COMPLETE!")
    print("="*60)
    print()
    print("🎉 Your SQL agent can now learn from past queries!")
    print()
    print("📝 Next steps:")
    print("   1. Run your SQL agent: python main.py")
    print("   2. Or launch Web UI: python launcher.py ui")
    print("   3. The system will automatically:")
    print("      • Store all queries in history")
    print("      • Learn from similar past queries")
    print("      • Improve based on user feedback")
    print()
    print("💡 Features enabled:")
    print("   ✓ Query history with embeddings")
    print("   ✓ Similarity-based learning")
    print("   ✓ User feedback collection")
    print("   ✓ SQL correction learning")
    print("   ✓ Performance analytics")
    print()
    
    return True

if __name__ == "__main__":
    success = setup_learning_system()
    sys.exit(0 if success else 1)
