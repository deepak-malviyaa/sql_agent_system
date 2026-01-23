# DEPLOYMENT.md

# 🚀 Production Deployment Guide

## Overview
This guide covers deploying the SQL Agent System to production environments with enterprise-grade reliability, security, and monitoring.

---

## Pre-Deployment Checklist

### 1. Environment Variables
Create a `.env` file with all required credentials:

```bash
# LLM API Keys
GOOGLE_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# Database Connection
DATABASE_URL=postgresql://username:password@host:port/database

# Optional: Monitoring
LANGSMITH_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=sql-agent-prod

# Optional: Model Selection
MODEL_REASONING=gemini  # or groq
MODEL_FAST=groq         # or gemini
```

### 2. Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Setup
```bash
python db_setup.py
```

Verify connection:
```python
from tools.db_connector import DatabaseConnector
assert DatabaseConnector.test_connection()
```

---

## Deployment Architectures

### Option 1: Container Deployment (Recommended)

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from tools.db_connector import DatabaseConnector; DatabaseConnector.test_connection()" || exit 1

# Run application
CMD ["python", "main.py"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  sql-agent:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./logs:/app/logs
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

**Deploy:**
```bash
docker-compose up -d
docker-compose logs -f sql-agent
```

---

### Option 2: Kubernetes Deployment

#### k8s/deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sql-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sql-agent
  template:
    metadata:
      labels:
        app: sql-agent
    spec:
      containers:
      - name: sql-agent
        image: your-registry/sql-agent:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: sql-agent-secrets
              key: database-url
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: sql-agent-secrets
              key: google-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "from tools.db_connector import DatabaseConnector; DatabaseConnector.test_connection()"
          initialDelaySeconds: 30
          periodSeconds: 60
```

**Deploy:**
```bash
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl get pods -l app=sql-agent
```

---

### Option 3: Serverless (AWS Lambda)

#### lambda_handler.py
```python
import json
from graph import app

def lambda_handler(event, context):
    """
    AWS Lambda handler for SQL Agent
    """
    question = event.get('question', '')
    
    if not question:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing question parameter'})
        }
    
    try:
        inputs = {"question": question, "retry_count": 0, "error": None}
        
        final_state = None
        for output in app.stream(inputs):
            for agent_name, agent_state in output.items():
                final_state = agent_state
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'answer': final_state.get('final_answer', 'No answer generated'),
                'sql': final_state.get('generated_sql', ''),
                'success': bool(final_state.get('final_answer'))
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

**Deploy with SAM:**
```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  SQLAgentFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_handler.lambda_handler
      Runtime: python3.11
      Timeout: 30
      MemorySize: 1024
      Environment:
        Variables:
          DATABASE_URL: !Ref DatabaseURL
          GOOGLE_API_KEY: !Ref GoogleAPIKey
```

---

## Security Hardening

### 1. Database Security
```python
# config/security.py
import os

class SecurityConfig:
    # Read-only database user
    DB_USER_READ_ONLY = os.getenv("DB_READ_ONLY_USER")
    
    # Connection encryption
    DB_SSL_MODE = "require"
    
    # Query timeout (prevent long-running queries)
    MAX_QUERY_TIMEOUT = 30  # seconds
    
    # Row limit to prevent data exfiltration
    MAX_ROWS_RETURNED = 10000
```

### 2. API Key Rotation
```bash
# Rotate keys monthly
# Use AWS Secrets Manager or HashiCorp Vault
aws secretsmanager rotate-secret --secret-id sql-agent/google-api-key
```

### 3. Rate Limiting
```python
# middleware/rate_limiter.py
from functools import wraps
import time

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = {}
    
    def check(self, user_id):
        now = time.time()
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Remove old requests
        self.requests[user_id] = [
            req for req in self.requests[user_id]
            if now - req < self.window
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True
```

---

## Monitoring & Observability

### 1. LangSmith Integration
```python
# config.py - Already configured
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "sql-agent-prod"
```

### 2. Custom Metrics Dashboard
```python
# monitoring/dashboard.py
from utils.metrics import get_metrics_collector
import json

def export_prometheus_metrics():
    """Export metrics in Prometheus format"""
    collector = get_metrics_collector()
    summary = collector.get_session_summary()
    
    return f"""
# HELP sql_agent_queries_total Total number of queries
# TYPE sql_agent_queries_total counter
sql_agent_queries_total {summary['total_queries']}

# HELP sql_agent_success_rate Success rate percentage
# TYPE sql_agent_success_rate gauge
sql_agent_success_rate {summary['success_rate']}

# HELP sql_agent_avg_execution_time_ms Average execution time
# TYPE sql_agent_avg_execution_time_ms gauge
sql_agent_avg_execution_time_ms {summary['avg_execution_time_ms']}
"""
```

### 3. Alerting Rules
```yaml
# prometheus/alerts.yml
groups:
  - name: sql_agent
    rules:
      - alert: LowSuccessRate
        expr: sql_agent_success_rate < 80
        for: 5m
        annotations:
          summary: "SQL Agent success rate below 80%"
      
      - alert: HighErrorRate
        expr: rate(sql_agent_errors_total[5m]) > 5
        for: 5m
        annotations:
          summary: "High error rate detected"
```

---

## Performance Optimization

### 1. Connection Pooling
Already implemented in [db_connector.py](d:\\T2S\\sql-agent-system\\tools\\db_connector.py):
- Pool size: 5
- Max overflow: 10
- Connection recycling: 3600s

### 2. Caching Layer
```python
# tools/query_cache.py
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_sql_execution(sql_hash: str, sql: str):
    """Cache frequent queries"""
    from tools.db_connector import DatabaseConnector
    return DatabaseConnector.execute_query(sql)

def execute_with_cache(sql: str):
    sql_hash = hashlib.sha256(sql.encode()).hexdigest()
    return cached_sql_execution(sql_hash, sql)
```

### 3. Async Processing
```python
# async_handler.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=5)

async def process_query_async(question: str):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        run_query_sync,
        question
    )
    return result
```

---

## Disaster Recovery

### 1. Backup Strategy
```bash
# Automated daily backups
0 2 * * * pg_dump $DATABASE_URL > backups/sql_agent_$(date +\%Y\%m\%d).sql
```

### 2. Graceful Degradation
```python
# config/fallback.py
class FallbackStrategy:
    @staticmethod
    def handle_llm_failure():
        """Use simpler model if primary fails"""
        return "gemini-flash"  # Faster, cheaper fallback
    
    @staticmethod
    def handle_db_failure():
        """Return cached results if DB unavailable"""
        return {"error": "Database temporarily unavailable"}
```

---

## Cost Optimization

### 1. Model Selection
```python
# Use cheaper models for simple queries
if query_complexity < 0.5:
    model = "groq"  # Free tier available
else:
    model = "gemini"  # More capable
```

### 2. Request Batching
```python
# Batch multiple queries in one session
# to amortize LLM initialization cost
```

### 3. Smart Retries
```python
# Exponential backoff to reduce retry costs
import time

def retry_with_backoff(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)  # 1s, 2s, 4s
```

---

## Compliance & Audit

### 1. Query Logging
All queries are logged in `logs/metrics.jsonl`:
```json
{"question": "...", "sql": "...", "timestamp": "...", "user_id": "..."}
```

### 2. PII Detection (Future)
```python
# security/pii_scanner.py
import re

def contains_pii(text):
    patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'  # Credit Card
    ]
    return any(re.search(p, text) for p in patterns)
```

---

## Rollback Plan

If deployment fails:
1. **Revert to previous version:**
   ```bash
   docker-compose down
   git checkout <previous-tag>
   docker-compose up -d
   ```

2. **Check logs:**
   ```bash
   tail -f logs/sql_agent_*.log
   ```

3. **Verify database:**
   ```bash
   python -c "from tools.db_connector import DatabaseConnector; print(DatabaseConnector.test_connection())"
   ```

---

## Production Checklist

- [ ] Environment variables configured
- [ ] Database connection tested
- [ ] SSL/TLS enabled for database
- [ ] API keys rotated and secured
- [ ] Logging configured and tested
- [ ] Monitoring dashboards set up
- [ ] Rate limiting implemented
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Documentation updated

---

## Support & Troubleshooting

### Common Issues

**Issue: "Connection timeout"**
- Check DATABASE_URL
- Verify network connectivity
- Increase pool_timeout in db_connector.py

**Issue: "API rate limit exceeded"**
- Implement caching
- Use fallback models
- Add rate limiting per user

**Issue: "High error rate"**
- Check logs: `tail -f logs/sql_agent_*.log`
- Review metrics: `python -c "from utils.metrics import get_metrics_collector; get_metrics_collector().print_session_summary()"`

---

## Next Steps
- [ ] Implement user authentication
- [ ] Add multi-tenant support
- [ ] Create REST API endpoint
- [ ] Build web UI dashboard
- [ ] Add support for more databases (MySQL, Snowflake)
