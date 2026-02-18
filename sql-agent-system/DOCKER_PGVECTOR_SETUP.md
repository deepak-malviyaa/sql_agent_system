# Docker Setup Guide for PostgreSQL + pgvector

## 🐳 Complete Docker Setup for RAG System

This guide shows how to set up PostgreSQL with pgvector extension using Docker for your SQL Agent RAG system.

---

## 🚀 Quick Start (Recommended)

### Option 1: Using Docker Compose (Easiest)

```bash
# 1. Files are already created in your project:
#    - docker-compose-pgvector.yml
#    - init-pgvector.sql

# 2. Start PostgreSQL with pgvector
docker-compose -f docker-compose-pgvector.yml up -d

# 3. Verify it's running
docker-compose -f docker-compose-pgvector.yml ps

# 4. Check logs
docker-compose -f docker-compose-pgvector.yml logs postgres

# 5. Connect and verify pgvector
docker exec -it postgres_pgvector psql -U user1 -d entegris_db

# In PostgreSQL:
\dx vector              -- Should show vector extension
SELECT version();       -- PostgreSQL version
\q                      -- Exit

# 6. Run your setup script
python setup_pgvector_rag.py

# 7. Test your SQL agent
python main.py
```

**Done! Your Docker PostgreSQL with pgvector is ready.** ✅

---

## 📋 Detailed Options

### Option 1: Official pgvector/pgvector Image (Pre-built)

**Easiest method - pgvector already installed!**

```bash
# Stop existing PostgreSQL container (if any)
docker stop postgres_container 2>/dev/null || true
docker rm postgres_container 2>/dev/null || true

# Run PostgreSQL with pgvector
docker run -d \
  --name postgres_pgvector \
  -e POSTGRES_USER=user1 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=entegris_db \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  -v "$(pwd)/init-pgvector.sql:/docker-entrypoint-initdb.d/init-pgvector.sql" \
  pgvector/pgvector:pg15

# Wait for startup (check logs)
docker logs -f postgres_pgvector
# Press Ctrl+C when you see "database system is ready to accept connections"

# Verify
docker exec -it postgres_pgvector psql -U user1 -d entegris_db -c "\dx vector"
```

---

### Option 2: Add pgvector to Existing Container

**If you already have a PostgreSQL Docker container:**

```bash
# 1. Enter your container
docker exec -it your_postgres_container bash

# 2. Install build dependencies
apt-get update
apt-get install -y build-essential git postgresql-server-dev-15

# 3. Download and install pgvector
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make clean
make
make install

# 4. Exit container
exit

# 5. Restart container
docker restart your_postgres_container

# 6. Enable extension
  docker exec -it your_postgres_container psql -U user1 -d entegris_db -c "CREATE EXTENSION vector;"

  # 7. Verify
  docker exec -it your_postgres_container psql -U user1 -d entegris_db -c "\dx vector"
```

---

### Option 3: Custom Dockerfile

**Build your own image with pgvector:**

Create `Dockerfile.pgvector`:

```dockerfile
FROM postgres:15

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    postgresql-server-dev-15 && \
    rm -rf /var/lib/apt/lists/*

# Install pgvector (specific version for stability)
RUN cd /tmp && \
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make clean && \
    make OPTFLAGS="" && \
    make install && \
    cd / && \
    rm -rf /tmp/pgvector

# Add initialization script
COPY init-pgvector.sql /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432

# Use official entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["postgres"]
```

Build and run:

```bash
# Build image
docker build -f Dockerfile.pgvector -t postgres-pgvector:15-custom .

# Run container
docker run -d \
  --name postgres_pgvector \
  -e POSTGRES_USER=user1 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=entegris_db \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres-pgvector:15-custom

# Verify
docker logs postgres_pgvector | grep vector
docker exec -it postgres_pgvector psql -U user1 -d entegris_db -c "\dx vector"
```

---

## 🔧 Configuration

### Update Connection String in Python

```python
# If running Docker on same machine:
DB_CONNECTION = "postgresql://user1:password@localhost:5432/entegris_db"

# If Python is also in Docker (use service name):
DB_CONNECTION = "postgresql://user1:password@postgres_pgvector:5432/entegris_db"

# If Docker on remote server:
DB_CONNECTION = "postgresql://user1:password@server_ip:5432/entegris_db"
```

### Environment Variables (Recommended)

Create `.env` file:
```bash
# .env
POSTGRES_USER=user1
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=entegris_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Load in Python:
```python
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONNECTION = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}"
    f"/{os.getenv('POSTGRES_DB')}"
)
```

---

## 🛠️ Common Docker Commands

### Container Management

```bash
# Start container
docker start postgres_pgvector

# Stop container
docker stop postgres_pgvector

# Restart container
docker restart postgres_pgvector

# Remove container (⚠️ keeps data in volume)
docker rm postgres_pgvector

# View logs
docker logs postgres_pgvector
docker logs -f postgres_pgvector  # Follow mode

# Check container status
docker ps | grep postgres

# Container resource usage
docker stats postgres_pgvector
```

### Database Operations

```bash
# Connect to database
docker exec -it postgres_pgvector psql -U user1 -d entegris_db

# Run SQL command
docker exec -it postgres_pgvector psql -U user1 -d entegris_db -c "SELECT COUNT(*) FROM schema_embeddings;"

# Run SQL file
docker exec -i postgres_pgvector psql -U user1 -d entegris_db < query.sql

# Create database backup
docker exec postgres_pgvector pg_dump -U user1 entegris_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
docker exec -i postgres_pgvector psql -U user1 entegris_db < backup_20260127_120000.sql

# Copy file into container
docker cp my_data.sql postgres_pgvector:/tmp/

# Copy file from container
docker cp postgres_pgvector:/tmp/output.txt ./
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect postgres_data

# Backup volume to tar file
docker run --rm \
  -v postgres_data:/data \
  -v "$(pwd):/backup" \
  ubuntu \
  tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /data

# Restore volume from tar file
docker run --rm \
  -v postgres_data:/data \
  -v "$(pwd):/backup" \
  ubuntu \
  bash -c "cd / && tar xzf /backup/postgres_backup_20260127.tar.gz"

# Remove volume (⚠️ DELETES ALL DATA)
docker volume rm postgres_data
```

---

## 🔍 Verification & Testing

### Verify pgvector Installation

```bash
# Check extension availability
docker exec -it postgres_pgvector psql -U user1 -d entegris_db -c \
  "SELECT * FROM pg_available_extensions WHERE name = 'vector';"

# Check if extension is enabled
docker exec -it postgres_pgvector psql -U user1 -d entegris_db -c "\dx vector"

# Test vector operations
docker exec -it postgres_pgvector psql -U user1 -d entegris_db -c \
  "SELECT '[1,2,3]'::vector <=> '[4,5,6]'::vector AS cosine_distance;"
```

### Test Python Connection

```python
# test_connection.py
import psycopg2

try:
    conn = psycopg2.connect(
        "postgresql://user1:password@localhost:5432/entegris_db"
    )
    cur = conn.cursor()
    
    # Test pgvector
    cur.execute("SELECT '[1,2,3]'::vector <=> '[4,5,6]'::vector;")
    result = cur.fetchone()[0]
    print(f"✅ Connection successful! Cosine distance: {result}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

Run test:
```bash
python test_connection.py
```

---

## 🐛 Troubleshooting

### Container won't start

```bash
# Check logs for errors
docker logs postgres_pgvector

# Common issues:
# 1. Port 5432 already in use
docker ps | grep 5432  # Find conflicting container
docker stop <conflicting_container>

# 2. Permission issues with volume
docker volume rm postgres_data
docker volume create postgres_data

# 3. Out of memory
docker system prune -a  # Clean up Docker resources
```

### Can't connect from Python

```bash
# Check if container is running
docker ps | grep postgres

# Check if PostgreSQL is accepting connections
docker exec postgres_pgvector pg_isready -U user1

# Test connection from container
docker exec -it postgres_pgvector psql -U user1 -d entegris_db -c "SELECT 1;"

# Check PostgreSQL configuration
docker exec postgres_pgvector cat /var/lib/postgresql/data/postgresql.conf | grep listen_addresses
# Should be: listen_addresses = '*'

# Check firewall (Windows)
netsh advfirewall firewall add rule name="PostgreSQL" dir=in action=allow protocol=TCP localport=5432
```

### pgvector not working

```bash
# Check if extension exists
docker exec -it postgres_pgvector \
  ls /usr/share/postgresql/15/extension/ | grep vector

# Should show:
# vector--0.5.1.sql
# vector.control

# If missing, reinstall (see Option 2 above)

# Force enable extension
docker exec -it postgres_pgvector psql -U postgres -d entegris_db
# In PostgreSQL:
DROP EXTENSION IF EXISTS vector CASCADE;
CREATE EXTENSION vector;
\dx vector
\q
```

### Data not persisting

```bash
# Check if volume is properly mounted
docker inspect postgres_pgvector | grep -A 10 Mounts

# Recreate with explicit volume
docker stop postgres_pgvector
docker rm postgres_pgvector
docker run -d \
  --name postgres_pgvector \
  -e POSTGRES_USER=user1 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=entegris_db \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  pgvector/pgvector:pg15
```

---

## 🔐 Security Best Practices

### 1. Use Strong Passwords

```bash
# Generate random password
openssl rand -base64 32

# Use in Docker Compose or .env file
POSTGRES_PASSWORD=<generated_password>
```

### 2. Don't Expose Port Publicly

```yaml
# docker-compose.yml
ports:
  - "127.0.0.1:5432:5432"  # Only localhost can connect
```

### 3. Use Docker Secrets (Production)

```yaml
# docker-compose.yml
services:
  postgres:
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password

secrets:
  postgres_password:
    file: ./postgres_password.txt
```

### 4. Regular Backups

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

docker exec postgres_pgvector \
  pg_dump -U user1 entegris_db | \
  gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

---

## 📊 Performance Tuning

### Optimize PostgreSQL Config for Vectors

```sql
-- Inside PostgreSQL
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET work_mem = '64MB';
ALTER SYSTEM SET max_parallel_workers_per_gather = '4';

-- Restart container
-- docker restart postgres_pgvector
```

### Monitor Performance

```bash
# Container resource usage
docker stats postgres_pgvector

# Database size
docker exec postgres_pgvector psql -U user1 -d entegris_db -c \
  "SELECT pg_size_pretty(pg_database_size('entegris_db'));"

# Table size
docker exec postgres_pgvector psql -U user1 -d entegris_db -c \
  "SELECT pg_size_pretty(pg_total_relation_size('schema_embeddings'));"

# Active connections
docker exec postgres_pgvector psql -U user1 -d entegris_db -c \
  "SELECT count(*) FROM pg_stat_activity;"
```

---

## ✅ Complete Setup Checklist

- [ ] Choose Docker option (Compose recommended)
- [ ] Start PostgreSQL container with pgvector
- [ ] Verify container is running (`docker ps`)
- [ ] Verify pgvector extension (`\dx vector`)
- [ ] Update connection string in Python code
- [ ] Run `python setup_pgvector_rag.py`
- [ ] Verify schema_embeddings table exists
- [ ] Test with sample query
- [ ] Set up automated backups
- [ ] Configure resource limits
- [ ] Document setup for team

---

## 🎉 You're All Set!

Your Docker PostgreSQL with pgvector is ready for production use!

**Next Steps:**
1. Run your SQL Agent: `python main.py`
2. Monitor performance: `docker stats postgres_pgvector`
3. Set up backups: See security section above
4. Scale as needed: Adjust resource limits in docker-compose.yml

**Questions?** Check the main PGVECTOR_MIGRATION_GUIDE.md for more details!
