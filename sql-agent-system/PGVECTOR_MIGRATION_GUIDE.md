# Implementation Guide: Migrating from FAISS to pgvector

## 🎯 Overview

This guide walks you through replacing FAISS (in-memory) with PostgreSQL pgvector (external database) for RAG in your SQL Agent system.

---

## 📋 What You Get

### Created Files:
1. **`tools/schema_rag_pgvector.py`** - New RAG implementation using pgvector
2. **`RAG_ARCHITECTURE_GUIDE.md`** - Complete explanation of how RAG works
3. **`RAG_VISUAL_GUIDE.md`** - Visual diagrams and comparisons
4. **`setup_pgvector_rag.py`** - Automated setup script
5. **`compare_rag_systems.py`** - Benchmark comparison tool

### Existing Files (Unchanged):
- **`tools/schema_rag.py`** - Original FAISS implementation (still works)

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install pgvector Extension

#### Docker (RECOMMENDED for containerized PostgreSQL) 🐳

**Option 1: Use Official pgvector Image (Easiest)**
```bash
# Stop your current PostgreSQL container
docker stop postgres_container
docker rm postgres_container

# Run PostgreSQL with pgvector pre-installed
docker run -d \
  --name postgres_container \
  -e POSTGRES_USER=user1 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=entegris_db \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  pgvector/pgvector:pg15

# pgvector is already installed! Just enable it (see Step 2)
```

**Option 2: Add pgvector to Existing Container**
```bash
# Enter your existing container
docker exec -it your_postgres_container bash

# Inside container - Install dependencies
apt-get update
apt-get install -y postgresql-server-dev-15 git build-essential

# Clone and build pgvector
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
make install

# Exit container
exit

# Restart container
docker restart your_postgres_container
```

**Option 3: Create Custom Dockerfile**
```dockerfile
# Dockerfile
FROM postgres:15

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    postgresql-server-dev-15 && \
    rm -rf /var/lib/apt/lists/*

# Install pgvector
RUN cd /tmp && \
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/pgvector

# Create initialization script
RUN echo "CREATE EXTENSION IF NOT EXISTS vector;" > /docker-entrypoint-initdb.d/init-pgvector.sql
```

Build and run:
```bash
docker build -t postgres-pgvector:15 .
docker run -d \
  --name postgres_container \
  -e POSTGRES_USER=user1 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=entegris_db \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres-pgvector:15
```

**Option 4: Docker Compose (Recommended for Development)**
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    container_name: postgres_pgvector
    environment:
      POSTGRES_USER: user1
      POSTGRES_PASSWORD: password
      POSTGRES_DB: entegris_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-pgvector.sql:/docker-entrypoint-initdb.d/init-pgvector.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user1"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

Create `init-pgvector.sql`:
```sql
-- init-pgvector.sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Start:
```bash
docker-compose up -d
```

**Verify Installation:**
```bash
# Connect to database
docker exec -it postgres_container psql -U user1 -d entegris_db

# Check if pgvector is available
SELECT * FROM pg_available_extensions WHERE name = 'vector';

# Enable extension (if not auto-enabled)
CREATE EXTENSION vector;

# Verify
\dx vector
```

---

#### Ubuntu/Debian (Native Installation):
```bash
sudo apt-get update
sudo apt-get install postgresql-15-pgvector
```

#### macOS (Native Installation):
```bash
brew install pgvector
```

#### Windows (Native Installation):
1. Download from: https://github.com/pgvector/pgvector/releases
2. Extract to PostgreSQL extensions directory
3. Enable in database (see Step 2)

### Step 2: Run Setup Script

```bash
# Edit DB connection in setup_pgvector_rag.py first!
python setup_pgvector_rag.py
```

This script will:
- ✅ Check if pgvector is installed
- ✅ Enable pgvector extension
- ✅ Create `schema_embeddings` table
- ✅ Create vector similarity indexes
- ✅ Seed initial schema documentation
- ✅ Test the RAG system

### Step 3: Update Your Code

#### Option A: Switch to pgvector (Recommended for Production)

```python
# In config.py or main.py, replace:
# from tools.schema_rag import get_relevant_schema

# With:
from tools.schema_rag_pgvector import initialize_rag, get_relevant_schema

# Initialize at startup
initialize_rag("postgresql://user1:password@localhost:5432/entegris_db")
```

#### Option B: Keep Both (Development)

```python
# Use FAISS for development, pgvector for production
import os

if os.getenv("ENVIRONMENT") == "production":
    from tools.schema_rag_pgvector import initialize_rag, get_relevant_schema
    initialize_rag(os.getenv("DB_CONNECTION"))
else:
    from tools.schema_rag import get_relevant_schema
```

---

## 📊 Detailed Comparison

### FAISS (Current - In-Memory)

```python
# How it works:
embeddings = HuggingFaceEmbeddings(...)
vector_store = FAISS.from_documents(schema_docs, embeddings)
results = vector_store.similarity_search(query, k=3)

# Storage:
- RAM only
- Lost on restart
- Rebuilt on every startup
```

**Pros:**
- ✅ Fastest queries (~1-5ms)
- ✅ No database dependency
- ✅ Simple setup
- ✅ Good for development

**Cons:**
- ❌ Not persistent (data lost on restart)
- ❌ Must rebuild on every startup (~5-10 seconds)
- ❌ Single process only
- ❌ No concurrent access
- ❌ No incremental updates

### pgvector (New - External Database)

```python
# How it works:
embeddings = HuggingFaceEmbeddings(...)
conn = psycopg2.connect(db_url)
# Store vectors in PostgreSQL table
cur.execute("""
    INSERT INTO schema_embeddings (content, embedding)
    VALUES (%s, %s)
""", (text, vector))

# Query with SQL
cur.execute("""
    SELECT content FROM schema_embeddings
    ORDER BY embedding <=> %s::vector
    LIMIT 3
""", (query_vector,))
```

**Pros:**
- ✅ Persistent storage (survives restarts)
- ✅ No rebuild needed (instant startup)
- ✅ Concurrent access (multiple users/agents)
- ✅ ACID transactions (data integrity)
- ✅ Incremental updates (add schemas anytime)
- ✅ Scales to millions of vectors
- ✅ SQL interface (familiar queries)
- ✅ Production-ready

**Cons:**
- ⚠️ Slightly slower (~10-30ms vs 1-5ms for small datasets)
- ⚠️ Requires PostgreSQL extension installation
- ⚠️ More complex setup

---

## 🏗️ Database Schema

### Table: `schema_embeddings`

```sql
CREATE TABLE schema_embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,                    -- Schema documentation text
    embedding vector(384),                     -- 384-dim vector from embeddings model
    table_name VARCHAR(100),                   -- Table name for filtering
    column_name VARCHAR(100),                  -- Column name (if applicable)
    doc_type VARCHAR(50),                      -- 'full_schema', 'enum_values', etc.
    priority INTEGER DEFAULT 1,                -- Search priority (1=highest)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector similarity index (IVFFlat)
CREATE INDEX schema_embeddings_vector_idx 
ON schema_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 10);

-- Regular indexes for filtering
CREATE INDEX schema_embeddings_table_idx ON schema_embeddings(table_name);
CREATE INDEX schema_embeddings_priority_idx ON schema_embeddings(priority);
```

### Example Data:

```sql
INSERT INTO schema_embeddings (content, embedding, table_name, doc_type, priority)
VALUES (
    'Table: sales_data
    Columns: id, transaction_date, product_category, total_revenue, country
    Purpose: E-commerce transaction tracking',
    '[0.23, -0.45, 0.67, ..., -0.89]',  -- 384 dimensions
    'sales_data',
    'full_schema',
    1
);
```

---

## 🔍 How Vector Search Works

### Query Process:

```python
# 1. User asks: "Show revenue from Germany"
query = "Show revenue from Germany"

# 2. Convert query to vector
query_vector = embeddings.embed_query(query)
# Result: [0.21, -0.43, 0.69, ..., -0.87] (384 dimensions)

# 3. Find similar vectors in database
cur.execute("""
    SELECT content, table_name, (embedding <=> %s::vector) as distance
    FROM schema_embeddings
    ORDER BY distance ASC
    LIMIT 3;
""", (f"[{','.join(map(str, query_vector))}]",))

# 4. Results (sorted by similarity):
# Row 1: "Table: sales_data, Column: total_revenue..." (distance: 0.08)
# Row 2: "Country values: USA, Germany, France..." (distance: 0.12)
# Row 3: "Revenue calculations: SUM(total_revenue)" (distance: 0.15)
```

### Cosine Distance:
- **0.0** = Identical vectors (same meaning)
- **0.5** = Somewhat similar
- **1.0** = Orthogonal (unrelated)
- **2.0** = Opposite direction (opposite meaning)

Lower distance = More relevant! ✅

---

## 🛠️ Advanced Usage

### Adding New Schema Documentation

```python
from tools.schema_rag_pgvector import add_schema_document

# Add documentation for new table
add_schema_document(
    content="""Table: customers
    Columns: customer_id, first_name, last_name, email, country, city
    Purpose: Customer information and demographics
    
    Business Terms: clients, users, buyers
    Sample values:
    - country: USA, Germany, France, UK, Canada, India
    - Total rows: ~50
    
    Common queries:
    - Customer by country: WHERE country = 'USA'
    - Customer search: WHERE email LIKE '%@domain.com'""",
    table_name="customers",
    doc_type="full_schema",
    priority=1
)

# Add enum values
add_schema_document(
    content="""Customer countries: USA, Germany, France, UK, Canada, India
    Use for geographic analysis and customer segmentation.""",
    table_name="customers",
    column_name="country",
    doc_type="enum_values",
    priority=2
)
```

### Auto-Discovery from information_schema

```python
def auto_generate_schema_docs(db_connection):
    """Generate schema docs from database metadata"""
    conn = psycopg2.connect(db_connection)
    cur = conn.cursor()
    
    # Get all tables
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public';
    """)
    tables = cur.fetchall()
    
    for (table_name,) in tables:
        # Get columns
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s;
        """, (table_name,))
        columns = cur.fetchall()
        
        # Generate documentation
        doc = f"Table: {table_name}\nColumns:\n"
        for col_name, data_type, nullable in columns:
            doc += f"- {col_name} ({data_type})"
            if nullable == 'NO':
                doc += " NOT NULL"
            doc += "\n"
        
        # Add to RAG
        add_schema_document(doc, table_name, doc_type="full_schema")
```

### Monitoring & Performance

```sql
-- Check number of embeddings
SELECT COUNT(*) FROM schema_embeddings;

-- Check storage size
SELECT pg_size_pretty(pg_total_relation_size('schema_embeddings'));

-- Check average embedding size
SELECT AVG(pg_column_size(embedding)) as avg_bytes 
FROM schema_embeddings;

-- Most queried tables (add query logging first)
SELECT table_name, COUNT(*) 
FROM schema_query_logs 
GROUP BY table_name 
ORDER BY COUNT(*) DESC;

-- Test similarity search performance
EXPLAIN ANALYZE
SELECT content FROM schema_embeddings
ORDER BY embedding <=> '[0.21,-0.43,0.69,...]'::vector
LIMIT 3;
```

### Rebuild Index for Better Performance

```sql
-- Drop old index
DROP INDEX schema_embeddings_vector_idx;

-- Recreate with more lists (for larger datasets)
CREATE INDEX schema_embeddings_vector_idx 
ON schema_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- Adjust based on dataset size

-- Rule of thumb: lists = sqrt(rows) for good balance
-- More lists = better recall, slower insert
-- Fewer lists = faster queries, worse recall
```

---

## 🧪 Testing

### Run Comparison Benchmark:
```bash
python compare_rag_systems.py
```

### Manual Testing:
```python
from tools.schema_rag_pgvector import get_relevant_schema

# Test queries
queries = [
    "Show me revenue from Germany",
    "What product categories exist?",
    "Get total sales by country"
]

for query in queries:
    print(f"\nQuery: {query}")
    schema = get_relevant_schema(query)
    print(f"Retrieved schema:\n{schema}\n")
```

---

## 🔧 Troubleshooting

### Docker-Specific Issues:

#### Error: "permission denied for extension vector"
```bash
# Connect as superuser
docker exec -it postgres_container psql -U postgres -d entegris_db
CREATE EXTENSION vector;
\q
```

#### Container can't find pgvector after installation
```bash
# Restart container
docker restart postgres_container

# Check PostgreSQL logs
docker logs postgres_container

# Verify installation inside container
docker exec -it postgres_container ls /usr/share/postgresql/15/extension/ | grep vector
# Should show: vector--0.5.1.sql, vector.control
```

#### Connection refused from Python
```python
# If using Docker, update connection string:
# Use 'localhost' if connecting from host machine
DB_CONNECTION = "postgresql://user1:password@localhost:5432/entegris_db"

# Use service name if connecting from another Docker container
DB_CONNECTION = "postgresql://user1:password@postgres:5432/entegris_db"
```

#### Volume persistence issues
```bash
# List Docker volumes
docker volume ls

# Inspect volume
docker volume inspect postgres_data

# Backup volume
docker run --rm -v postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_backup.tar.gz /data

# Restore volume
docker run --rm -v postgres_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/postgres_backup.tar.gz -C /
```

---

### General Issues:

### Error: "extension vector does not exist"
```bash
# Docker: Enter container and check
docker exec -it postgres_container psql -U user1 -d entegris_db
SELECT * FROM pg_available_extensions WHERE name = 'vector';

# If not available, reinstall (see Step 1 Docker options)

# Native: Install pgvector extension first
sudo apt-get install postgresql-15-pgvector

# Then enable in database
psql -d your_database -c "CREATE EXTENSION vector;"
```

### Error: "column embedding does not exist"
```bash
# Table not created - run setup script
python setup_pgvector_rag.py
```

### Slow queries (>100ms)
```sql
-- Rebuild index with more lists
DROP INDEX schema_embeddings_vector_idx;
CREATE INDEX schema_embeddings_vector_idx 
ON schema_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);  -- Increase from default 10

-- Run ANALYZE
ANALYZE schema_embeddings;
```

### Out of memory errors
```python
# Use smaller batch sizes for embedding
docs_batch = schema_docs[:10]  # Process 10 at a time
embeddings.embed_documents(docs_batch)
```

---

## 📚 Additional Resources

- **pgvector GitHub**: https://github.com/pgvector/pgvector
- **pgvector Documentation**: https://github.com/pgvector/pgvector#installation
- **LangChain pgvector**: https://python.langchain.com/docs/integrations/vectorstores/pgvector
- **Sentence Transformers**: https://www.sbert.net/
- **Vector Search Theory**: https://www.pinecone.io/learn/vector-similarity/

---

## ✅ Migration Checklist

- [ ] Install pgvector extension
- [ ] Run `setup_pgvector_rag.py`
- [ ] Verify schema_embeddings table exists
- [ ] Update imports in your code
- [ ] Test with sample queries
- [ ] Monitor performance
- [ ] Add all table schemas
- [ ] Set up auto-refresh for schema changes
- [ ] Configure backup for schema_embeddings table
- [ ] Document for your team

---

## 🎉 You're Done!

Your RAG system is now using persistent, scalable PostgreSQL storage instead of volatile FAISS memory!

**Benefits achieved:**
- ✅ No data loss on restart
- ✅ Instant startup (no rebuild)
- ✅ Multi-user support
- ✅ Production-ready
- ✅ Incremental updates

**Next steps:**
1. Add more schema documentation for your tables
2. Monitor query performance
3. Set up auto-discovery from information_schema
4. Configure regular backups

Questions? Check the RAG_ARCHITECTURE_GUIDE.md and RAG_VISUAL_GUIDE.md! 🚀
