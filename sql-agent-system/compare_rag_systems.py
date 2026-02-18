"""
Comparison Demo: FAISS vs PostgreSQL pgvector for RAG

This script demonstrates the differences between FAISS and pgvector
for semantic search in the SQL Agent RAG system.

Run: python compare_rag_systems.py
"""

import time
from tools.schema_rag import get_relevant_schema as get_schema_faiss

# Uncomment after pgvector setup:
# from tools.schema_rag_pgvector import initialize_rag, get_relevant_schema as get_schema_pgvector
# initialize_rag("postgresql://user1:password@localhost:5432/entegris_db")


def benchmark_query(query: str, use_pgvector: bool = False):
    """Benchmark a single query"""
    start = time.time()
    
    if use_pgvector:
        # Uncomment after pgvector setup:
        # schema = get_schema_pgvector(query)
        schema = "PGVector not initialized"
    else:
        schema = get_schema_faiss(query)
    
    end = time.time()
    duration = (end - start) * 1000  # Convert to milliseconds
    
    return schema, duration


def main():
    print("=" * 80)
    print("RAG System Comparison: FAISS vs PostgreSQL pgvector")
    print("=" * 80)
    
    # Test queries
    test_queries = [
        "Show me revenue from Germany",
        "What are the product categories?",
        "Get total sales by country",
        "Which payment methods are available?",
        "Show Electronics products with revenue"
    ]
    
    print("\n📊 Testing FAISS (In-Memory Vector Store):")
    print("-" * 80)
    
    faiss_times = []
    for i, query in enumerate(test_queries, 1):
        schema, duration = benchmark_query(query, use_pgvector=False)
        faiss_times.append(duration)
        
        print(f"\n{i}. Query: '{query}'")
        print(f"   Time: {duration:.2f}ms")
        print(f"   Schema preview: {schema[:100]}...")
    
    print(f"\n   Average FAISS time: {sum(faiss_times)/len(faiss_times):.2f}ms")
    
    print("\n" + "=" * 80)
    print("\n📊 Testing pgvector (PostgreSQL External Database):")
    print("-" * 80)
    print("\n⚠️  Note: Run setup_pgvector_rag.py first to enable pgvector testing")
    print("     Then uncomment pgvector imports in this script")
    
    # Uncomment after pgvector setup:
    # pgvector_times = []
    # for i, query in enumerate(test_queries, 1):
    #     schema, duration = benchmark_query(query, use_pgvector=True)
    #     pgvector_times.append(duration)
    #     
    #     print(f"\n{i}. Query: '{query}'")
    #     print(f"   Time: {duration:.2f}ms")
    #     print(f"   Schema preview: {schema[:100]}...")
    # 
    # print(f"\n   Average pgvector time: {sum(pgvector_times)/len(pgvector_times):.2f}ms")
    
    # Comparison
    print("\n" + "=" * 80)
    print("📈 Comparison Summary:")
    print("-" * 80)
    
    print("""
FAISS (In-Memory):
  ✅ Fastest queries (<5ms typically)
  ✅ No database dependency
  ✅ Simple setup
  ❌ Data lost on restart
  ❌ Not persistent
  ❌ Single process only
  ❌ No concurrent access
  
  Best for: Development, prototyping, single-user systems
  
PostgreSQL pgvector (External DB):
  ✅ Persistent storage (survives restarts)
  ✅ Concurrent access (multiple users/agents)
  ✅ ACID transactions
  ✅ Incremental updates (add schemas without rebuild)
  ✅ Scales to millions of vectors
  ✅ SQL interface for queries
  ⚠️  Slightly slower (~10-30ms vs <5ms for small datasets)
  ⚠️  Requires PostgreSQL extension installation
  
  Best for: Production, multi-user, large-scale systems
  
Recommended: Start with FAISS, migrate to pgvector for production
""")
    
    print("\n" + "=" * 80)
    print("🚀 Next Steps:")
    print("-" * 80)
    print("""
1. Install pgvector extension:
   Ubuntu/Debian: sudo apt-get install postgresql-15-pgvector
   macOS: brew install pgvector
   Windows: Download from https://github.com/pgvector/pgvector/releases

2. Run setup script:
   python setup_pgvector_rag.py

3. Update your code:
   # config.py or main.py
   from tools.schema_rag_pgvector import initialize_rag, get_relevant_schema
   initialize_rag("postgresql://user:pass@localhost:5432/db_name")

4. The system will automatically create schema_embeddings table and
   populate it with your schema documentation on first run.

5. Monitor performance:
   SELECT COUNT(*), AVG(pg_column_size(embedding)) 
   FROM schema_embeddings;
""")


if __name__ == "__main__":
    main()
