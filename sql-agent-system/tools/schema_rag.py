from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)

class SchemaRAG:
    """Semantic schema retrieval using vector embeddings"""
    
    def __init__(self):
        try:
            # Use HuggingFace embeddings (free, runs locally)
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            self.vector_store = None
            self._initialize_schema()
            logger.info("Schema RAG initialized successfully with HuggingFace embeddings")
        except Exception as e:
            logger.warning(f"Failed to initialize embeddings: {e}. Using fallback.")
            self.embeddings = None
            self.vector_store = None
    
    def _initialize_schema(self):
        """
        Initialize vector store with schema documentation.
        In production, this should:
        1. Auto-discover database schema from information_schema
        2. Include sample values and statistics
        3. Add business glossary mappings
        4. Support multiple tables with relationships
        """
        if self.embeddings is None:
            return
            
        schema_docs = [
            Document(
                page_content="""Table: sales_data
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
                metadata={"table": "sales_data", "type": "full_schema", "priority": 1}
            ),
            Document(
                page_content="""Country dimension in sales_data:
Possible values: USA, Germany, France, India, UK, Canada
Use for geographic analysis and revenue breakdown by region.
Example: WHERE country = 'Germany' or WHERE country IN ('USA', 'UK')""",
                metadata={"table": "sales_data", "column": "country", "type": "enum_values"}
            ),
            Document(
                page_content="""Product categories in sales_data:
Possible values: Electronics, Clothing, Home
Use for product mix analysis and category performance.
Example: WHERE product_category = 'Electronics' or GROUP BY product_category""",
                metadata={"table": "sales_data", "column": "product_category", "type": "enum_values"}
            ),
            Document(
                page_content="""Revenue calculations in sales_data:
total_revenue = units_sold * unit_price (pre-computed)
For revenue queries: SELECT SUM(total_revenue) for totals
For average order value: SELECT AVG(total_revenue)
For units analysis: SELECT SUM(units_sold)""",
                metadata={"table": "sales_data", "type": "business_logic"}
            ),
            Document(
                page_content="""Date filtering in sales_data:
transaction_date is DATE type
Examples:
- Specific date: WHERE transaction_date = '2023-12-25'
- Date range: WHERE transaction_date BETWEEN '2023-01-01' AND '2023-12-31'
- Recent data: WHERE transaction_date >= CURRENT_DATE - INTERVAL '30 days'
- Year filter: WHERE EXTRACT(YEAR FROM transaction_date) = 2023""",
                metadata={"table": "sales_data", "column": "transaction_date", "type": "usage_examples"}
            )
        ]
        
        try:
            self.vector_store = FAISS.from_documents(schema_docs, self.embeddings)
            logger.info(f"Vector store created with {len(schema_docs)} schema documents")
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            self.vector_store = None
    
    def get_relevant_schema(self, query: str, k: int = 3) -> str:
        """
        Retrieve schema context based on semantic similarity to the query.
        
        Args:
            query: The user's natural language question
            k: Number of relevant documents to retrieve
            
        Returns:
            Concatenated schema documentation
        """
        if self.vector_store is None:
            logger.warning("Vector store not available, using fallback schema")
            return self._fallback_schema()
        
        try:
            # Retrieve semantically similar schema docs
            docs = self.vector_store.similarity_search(query, k=k)
            schema_text = "\n\n---\n\n".join([doc.page_content for doc in docs])
            logger.info(f"Retrieved {len(docs)} relevant schema documents for query")
            return schema_text
        except Exception as e:
            logger.error(f"Schema retrieval failed: {e}. Using fallback.")
            return self._fallback_schema()
    
    def _fallback_schema(self) -> str:
        """Minimal schema for when RAG is unavailable"""
        return """Table: sales_data
Columns: id, transaction_date, product_category, product_name, units_sold, unit_price, total_revenue, country, payment_method
Key columns for queries:
- total_revenue: For revenue calculations
- country: For geographic analysis ('USA', 'Germany', 'France', 'India', 'UK', 'Canada')
- product_category: For product analysis ('Electronics', 'Clothing', 'Home')
- transaction_date: For time-based analysis"""

# Singleton instance
_schema_rag = SchemaRAG()

def get_relevant_schema(query: str) -> str:
    """Public API for schema retrieval"""
    return _schema_rag.get_relevant_schema(query)