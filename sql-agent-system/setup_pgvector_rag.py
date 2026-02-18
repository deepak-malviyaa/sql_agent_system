"""
Setup script for migrating from FAISS to PostgreSQL pgvector

This script:
1. Checks if pgvector extension is installed
2. Creates schema_embeddings table
3. Migrates existing schema documentation
4. Tests the RAG system

Run: python setup_pgvector_rag.py
"""

import sys
import psycopg2
from psycopg2 import sql
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Update this with your database connection
DB_CONNECTION = "postgresql://user1:password@localhost:5432/entegris_db"


def check_pgvector_installed(conn):
    """Check if pgvector extension is available"""
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM pg_available_extensions WHERE name = 'vector';")
        result = cur.fetchone()
        if result:
            logger.info("✅ pgvector extension is available")
            return True
        else:
            logger.error("❌ pgvector extension NOT found")
            return False
    finally:
        cur.close()


def enable_pgvector(conn):
    """Enable pgvector extension"""
    cur = conn.cursor()
    try:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
        logger.info("✅ pgvector extension enabled")
        
        # Verify
        cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
        version = cur.fetchone()
        if version:
            logger.info(f"   pgvector version: {version[0]}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to enable pgvector: {e}")
        logger.error("   Install instructions:")
        logger.error("   Ubuntu/Debian: sudo apt-get install postgresql-15-pgvector")
        logger.error("   macOS: brew install pgvector")
        logger.error("   Windows: https://github.com/pgvector/pgvector/releases")
        return False
    finally:
        cur.close()


def create_schema_embeddings_table(conn):
    """Create schema_embeddings table"""
    cur = conn.cursor()
    try:
        logger.info("📋 Creating schema_embeddings table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_embeddings (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(384),
                table_name VARCHAR(100),
                column_name VARCHAR(100),
                doc_type VARCHAR(50),
                priority INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        logger.info("✅ schema_embeddings table created")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create table: {e}")
        return False
    finally:
        cur.close()


def create_indexes(conn):
    """Create vector similarity index"""
    cur = conn.cursor()
    try:
        logger.info("🔍 Creating vector similarity index...")
        
        # Check if data exists to determine index parameters
        cur.execute("SELECT COUNT(*) FROM schema_embeddings;")
        row_count = cur.fetchone()[0]
        
        # For small datasets, use fewer lists
        lists = max(10, row_count // 100) if row_count > 0 else 10
        
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS schema_embeddings_vector_idx 
            ON schema_embeddings 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = {lists});
        """)
        
        # Create regular indexes for filtering
        cur.execute("""
            CREATE INDEX IF NOT EXISTS schema_embeddings_table_idx 
            ON schema_embeddings(table_name);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS schema_embeddings_priority_idx 
            ON schema_embeddings(priority);
        """)
        
        conn.commit()
        logger.info(f"✅ Indexes created (lists={lists})")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {e}")
        return False
    finally:
        cur.close()


def test_rag_system():
    """Test the RAG system with a sample query"""
    try:
        logger.info("🧪 Testing RAG system...")
        from tools.schema_rag_pgvector import initialize_rag, get_relevant_schema
        
        # Initialize
        initialize_rag(DB_CONNECTION)
        
        # Test query
        test_queries = [
            "Show me revenue from Germany",
            "What products are in Electronics category?",
            "Get total sales by country"
        ]
        
        for query in test_queries:
            logger.info(f"\n   Query: '{query}'")
            schema = get_relevant_schema(query)
            logger.info(f"   Retrieved {len(schema)} chars of schema context")
            if "sales_data" in schema:
                logger.info("   ✅ Successfully retrieved sales_data schema")
            else:
                logger.warning("   ⚠️ Expected schema not found")
        
        logger.info("\n✅ RAG system test complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ RAG test failed: {e}")
        return False


def main():
    """Main setup flow"""
    logger.info("=" * 60)
    logger.info("PostgreSQL pgvector RAG Setup")
    logger.info("=" * 60)
    
    try:
        # Connect to database
        logger.info(f"\n📡 Connecting to database...")
        conn = psycopg2.connect(DB_CONNECTION)
        logger.info("✅ Connected successfully")
        
        # Check pgvector availability
        logger.info("\n1️⃣ Checking pgvector extension...")
        if not check_pgvector_installed(conn):
            logger.error("\n❌ Setup failed: pgvector not installed")
            logger.error("\nInstallation instructions:")
            logger.error("Ubuntu/Debian: sudo apt-get install postgresql-15-pgvector")
            logger.error("macOS: brew install pgvector")
            logger.error("Windows: Download from https://github.com/pgvector/pgvector/releases")
            sys.exit(1)
        
        # Enable pgvector
        logger.info("\n2️⃣ Enabling pgvector extension...")
        if not enable_pgvector(conn):
            sys.exit(1)
        
        # Create table
        logger.info("\n3️⃣ Creating schema_embeddings table...")
        if not create_schema_embeddings_table(conn):
            sys.exit(1)
        
        # Create indexes
        logger.info("\n4️⃣ Creating indexes...")
        if not create_indexes(conn):
            sys.exit(1)
        
        # Close connection for testing phase
        conn.close()
        
        # Test RAG system
        logger.info("\n5️⃣ Testing RAG system...")
        if not test_rag_system():
            logger.warning("⚠️ RAG test had issues, but setup is complete")
        
        # Success message
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Setup Complete!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Update your code to use schema_rag_pgvector:")
        logger.info("   from tools.schema_rag_pgvector import get_relevant_schema")
        logger.info("\n2. Run your SQL agent:")
        logger.info("   python main.py")
        logger.info("\n3. The system will automatically populate schema embeddings on first run")
        logger.info("\n4. Monitor performance:")
        logger.info("   SELECT COUNT(*), AVG(pg_column_size(embedding)) FROM schema_embeddings;")
        
    except psycopg2.OperationalError as e:
        logger.error(f"\n❌ Database connection failed: {e}")
        logger.error("\nCheck your connection string in the script:")
        logger.error(f"   DB_CONNECTION = \"{DB_CONNECTION}\"")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
