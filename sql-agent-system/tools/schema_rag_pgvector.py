"""
Schema RAG with PostgreSQL pgvector (External Database Storage)

Instead of FAISS (in-memory vector store), this uses PostgreSQL with pgvector extension
for persistent, scalable vector similarity search.

HOW RAG WORKS IN THIS SYSTEM:
=============================

1. EMBEDDING GENERATION (Vectorization):
   - User asks: "Show me revenue from Germany"
   - Text → Vector: [0.23, -0.45, 0.67, ...] (384 dimensions)
   - Schema docs also embedded: Each table/column description → Vector
   
2. SIMILARITY SEARCH (Retrieval):
   - Compare query vector with schema vectors using cosine similarity
   - PostgreSQL pgvector: SELECT * FROM schema_embeddings ORDER BY embedding <=> query_vector LIMIT 3
   - Returns top 3 most relevant schema docs
   
3. CONTEXT AUGMENTATION (Augmented Generation):
   - LLM receives: User query + Retrieved schema docs
   - LLM generates SQL with accurate table/column names
   
ADVANTAGES OF PGVECTOR OVER FAISS:
===================================
✅ Persistent storage (survives restarts)
✅ Concurrent access (multiple agents)
✅ Incremental updates (add new schemas without rebuild)
✅ ACID transactions (data integrity)
✅ Scales to millions of vectors
✅ Same database as your data (no separate service)
✅ SQL interface (familiar query language)

DISADVANTAGES:
==============
❌ Requires PostgreSQL extension installation
❌ Slightly slower than FAISS for small datasets (<10k vectors)
❌ Needs database schema changes
"""

import logging
from typing import List, Optional
import psycopg2
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class SchemaRAGPgVector:
    """
    RAG system using PostgreSQL pgvector for external vector storage.
    
    Architecture:
    1. Embeddings: sentence-transformers/all-MiniLM-L6-v2 (384 dims, local)
    2. Vector Store: PostgreSQL with pgvector extension
    3. Similarity: Cosine distance (<=> operator)
    """
    
    def __init__(self, db_connection: str):
        """
        Initialize RAG with PostgreSQL connection.
        
        Args:
            db_connection: PostgreSQL connection string 
                          "postgresql://user:password@localhost:5432/db_name"
        """
        self.db_connection = db_connection
        
        # Initialize embeddings model (runs locally, no API calls)
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}  # For cosine similarity
            )
            logger.info("✅ HuggingFace embeddings initialized (384 dimensions)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
            self.embeddings = None
            return
        
        # Setup database
        self._setup_database()
        self._initialize_schema_embeddings()
    
    def _setup_database(self):
        """Create pgvector extension and schema_embeddings table"""
        try:
            conn = psycopg2.connect(self.db_connection)
            cur = conn.cursor()
            
            # Enable pgvector extension
            logger.info("📦 Enabling pgvector extension...")
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create embeddings table
            logger.info("📋 Creating schema_embeddings table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_embeddings (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding vector(384),  -- 384 dims for all-MiniLM-L6-v2
                    table_name VARCHAR(100),
                    column_name VARCHAR(100),
                    doc_type VARCHAR(50),  -- 'full_schema', 'enum_values', 'business_logic', etc.
                    priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create index for fast similarity search
            logger.info("🔍 Creating vector similarity index...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS schema_embeddings_idx 
                ON schema_embeddings 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 10);
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info("✅ Database setup complete!")
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise
    
    def _initialize_schema_embeddings(self):
        """
        Initialize vector store with schema documentation.
        
        This should be expanded to:
        1. Auto-discover all tables from information_schema
        2. Include foreign key relationships
        3. Add business glossary terms
        4. Store sample values and statistics
        """
        if self.embeddings is None:
            return
        
        # Check if already populated
        conn = psycopg2.connect(self.db_connection)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM schema_embeddings;")
        count = cur.fetchone()[0]
        
        if count > 0:
            logger.info(f"📚 Schema embeddings already exist ({count} documents). Skipping initialization.")
            cur.close()
            conn.close()
            return
        
        logger.info("🌱 Seeding schema embeddings...")
        
        # Define schema documentation (same as FAISS version but stored in PostgreSQL)
        schema_docs = [
            {
                "content": """Table: sales_data
Purpose: E-commerce transaction tracking for revenue analytics
Business Terms: revenue, transactions, orders, sales, purchases
Row Count: ~50-100 records (sample dataset)

Columns:
- id (INTEGER, PRIMARY KEY): Unique transaction identifier, auto-incrementing
- transaction_date (DATE, indexed): Purchase timestamp, format YYYY-MM-DD
- product_category (VARCHAR): Product classification - Valid values: 'Electronics', 'Clothing', 'Home'
- product_name (VARCHAR): Specific product SKU/name
- units_sold (INTEGER): Quantity purchased in this transaction, always positive
- unit_price (DECIMAL(10,2)): Per-unit cost in USD, positive values
- total_revenue (DECIMAL(10,2)): Computed as units_sold * unit_price
- country (VARCHAR, indexed): Customer location - Valid values: 'USA', 'Germany', 'France', 'India', 'UK', 'Canada'
- payment_method (VARCHAR): Payment type - Valid values: 'Credit Card', 'PayPal', 'Bank Transfer'

Common Query Patterns:
- Revenue aggregation: SELECT SUM(total_revenue) FROM sales_data WHERE ...
- Top products: SELECT product_name, SUM(total_revenue) FROM sales_data GROUP BY product_name ORDER BY SUM(total_revenue) DESC
- Time-based analysis: WHERE transaction_date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
- Geographic breakdown: GROUP BY country""",
                "table_name": "sales_data",
                "column_name": None,
                "doc_type": "full_schema",
                "priority": 1
            },
            {
                "content": """Country dimension in sales_data:
Possible values: USA, Germany, France, India, UK, Canada
Use for geographic analysis and revenue breakdown by region.
Example: WHERE country = 'Germany' or WHERE country IN ('USA', 'UK')""",
                "table_name": "sales_data",
                "column_name": "country",
                "doc_type": "enum_values",
                "priority": 2
            },
            {
                "content": """Product categories in sales_data:
Possible values: Electronics, Clothing, Home
Use for product mix analysis and category performance.
Example: WHERE product_category = 'Electronics' or GROUP BY product_category""",
                "table_name": "sales_data",
                "column_name": "product_category",
                "doc_type": "enum_values",
                "priority": 2
            },
            {
                "content": """Revenue calculations in sales_data:
total_revenue = units_sold * unit_price (pre-computed)
For revenue queries: SELECT SUM(total_revenue) for totals
For average order value: SELECT AVG(total_revenue)
For units analysis: SELECT SUM(units_sold)""",
                "table_name": "sales_data",
                "column_name": None,
                "doc_type": "business_logic",
                "priority": 2
            },
            {
                "content": """Date filtering in sales_data:
transaction_date is DATE type
Examples:
- Specific date: WHERE transaction_date = '2023-12-25'
- Date range: WHERE transaction_date BETWEEN '2023-01-01' AND '2023-12-31'
- Recent data: WHERE transaction_date >= CURRENT_DATE - INTERVAL '30 days'
- Year filter: WHERE EXTRACT(YEAR FROM transaction_date) = 2023""",
                "table_name": "sales_data",
                "column_name": "transaction_date",
                "doc_type": "usage_examples",
                "priority": 2
            }
        ]
        
        # Generate embeddings and insert
        for doc in schema_docs:
            embedding = self.embeddings.embed_query(doc["content"])
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            
            cur.execute("""
                INSERT INTO schema_embeddings (content, embedding, table_name, column_name, doc_type, priority)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                doc["content"],
                embedding_str,
                doc["table_name"],
                doc["column_name"],
                doc["doc_type"],
                doc["priority"]
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ Initialized {len(schema_docs)} schema embeddings in PostgreSQL")
    
    def get_relevant_schema(self, query: str, k: int = 3) -> str:
        """
        Retrieve schema context using semantic similarity search.
        
        Process:
        1. Convert user query to embedding vector
        2. Search PostgreSQL for similar schema docs using cosine distance
        3. Return top-k most relevant documents
        
        Args:
            query: User's natural language question
            k: Number of relevant documents to retrieve
            
        Returns:
            Concatenated schema documentation
        """
        if self.embeddings is None:
            logger.warning("⚠️ Embeddings not available, using fallback")
            return self._fallback_schema()
        
        try:
            # Step 1: Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            query_vector = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Step 2: Semantic search using pgvector cosine distance
            conn = psycopg2.connect(self.db_connection)
            cur = conn.cursor()
            
            # <=> is cosine distance operator (0 = identical, 2 = opposite)
            cur.execute("""
                SELECT content, table_name, doc_type, (embedding <=> %s::vector) as distance
                FROM schema_embeddings
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """, (query_vector, query_vector, k))
            
            results = cur.fetchall()
            cur.close()
            conn.close()
            
            if not results:
                logger.warning("⚠️ No schema documents found, using fallback")
                return self._fallback_schema()
            
            # Step 3: Format results
            schema_text = "\n\n---\n\n".join([
                f"{row[0]}\n(Table: {row[1]}, Type: {row[2]}, Distance: {row[3]:.3f})"
                for row in results
            ])
            
            logger.info(f"✅ Retrieved {len(results)} relevant schema docs (distances: {[f'{r[3]:.3f}' for r in results]})")
            return schema_text
            
        except Exception as e:
            logger.error(f"❌ Schema retrieval failed: {e}")
            return self._fallback_schema()
    
    def add_schema_document(self, content: str, table_name: str, 
                           column_name: Optional[str] = None,
                           doc_type: str = "custom", priority: int = 2):
        """
        Add new schema documentation dynamically.
        
        Use this to:
        - Add new table schemas as they're created
        - Update business logic documentation
        - Add domain-specific glossary terms
        
        Args:
            content: Schema documentation text
            table_name: Name of the table
            column_name: Optional column name
            doc_type: Type of document (full_schema, enum_values, etc.)
            priority: Search priority (1=highest)
        """
        if self.embeddings is None:
            logger.error("❌ Cannot add document: embeddings not initialized")
            return
        
        try:
            embedding = self.embeddings.embed_query(content)
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            
            conn = psycopg2.connect(self.db_connection)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO schema_embeddings (content, embedding, table_name, column_name, doc_type, priority)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (content, embedding_str, table_name, column_name, doc_type, priority))
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"✅ Added schema document for {table_name}.{column_name or '*'}")
            
        except Exception as e:
            logger.error(f"❌ Failed to add schema document: {e}")
    
    def _fallback_schema(self) -> str:
        """Minimal schema when RAG is unavailable"""
        return """Table: sales_data
Columns: id, transaction_date, product_category, product_name, units_sold, unit_price, total_revenue, country, payment_method
Key columns:
- total_revenue: Revenue calculations
- country: Geographic analysis ('USA', 'Germany', 'France', 'India', 'UK', 'Canada')
- product_category: Product analysis ('Electronics', 'Clothing', 'Home')
- transaction_date: Time-based analysis"""


# Singleton instance (initialized in config)
_schema_rag: Optional[SchemaRAGPgVector] = None


def initialize_rag(db_connection: str):
    """Initialize the RAG system with database connection"""
    global _schema_rag
    _schema_rag = SchemaRAGPgVector(db_connection)


def get_relevant_schema(query: str) -> str:
    """Public API for schema retrieval"""
    if _schema_rag is None:
        logger.error("❌ RAG not initialized. Call initialize_rag() first.")
        return "Error: RAG system not initialized"
    return _schema_rag.get_relevant_schema(query)


def add_schema_document(content: str, table_name: str, **kwargs):
    """Public API for adding schema documents"""
    if _schema_rag is None:
        logger.error("❌ RAG not initialized")
        return
    _schema_rag.add_schema_document(content, table_name, **kwargs)
