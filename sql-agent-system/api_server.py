# api_server.py
"""
FastAPI REST API Server for SQL Agent System
Provides HTTP endpoints for integration with other systems
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from graph import app
from utils.metrics import get_metrics_collector, QueryMetrics
import time

logger = logging.getLogger(__name__)

# Initialize FastAPI app
api = FastAPI(
    title="SQL Agent System API",
    description="Natural language to SQL query API with multi-agent orchestration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question about the database")
    max_retries: int = Field(3, description="Maximum retry attempts", ge=0, le=10)
    timeout: int = Field(30, description="Query timeout in seconds", ge=5, le=300)
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the total revenue from Germany?",
                "max_retries": 3,
                "timeout": 30
            }
        }

class QueryResponse(BaseModel):
    success: bool
    answer: str
    sql: Optional[str] = None
    execution_time_ms: float
    retry_count: int
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    agents_available: List[str]

class MetricsResponse(BaseModel):
    total_queries: int
    success_rate: float
    avg_execution_time_ms: float
    avg_retries: float

# Initialize metrics collector
metrics = get_metrics_collector()

@api.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "SQL Agent System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "query": "POST /query"
    }

@api.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        from tools.db_connector import DatabaseConnector
        db_connected = DatabaseConnector.test_connection()
        
        return HealthResponse(
            status="healthy" if db_connected else "degraded",
            version="1.0.0",
            agents_available=["intent", "sql_generator", "validator", "executor", "responder", "retry_decision"]
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            agents_available=[]
        )

@api.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Execute a natural language query against the database.
    
    The system uses multiple AI agents to:
    1. Parse user intent
    2. Generate SQL with schema context
    3. Validate for security and syntax
    4. Execute against database
    5. Return natural language answer
    
    Retry logic is agent-based using LLM reasoning.
    """
    start_time = time.time()
    
    try:
        # Validate input
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Prepare state
        inputs = {
            "question": request.question,
            "retry_count": 0,
            "error": None
        }
        
        # Execute workflow
        final_state = None
        retry_count = 0
        generated_sql = ""
        
        for output in app.stream(inputs):
            for agent_name, agent_state in output.items():
                final_state = agent_state
                
                if "generated_sql" in agent_state:
                    generated_sql = agent_state["generated_sql"]
                
                if "retry_count" in agent_state:
                    retry_count = agent_state["retry_count"]
                
                # Stop if max retries exceeded
                if retry_count >= request.max_retries:
                    break
        
        execution_time = (time.time() - start_time) * 1000
        
        # Build response
        if final_state:
            answer = final_state.get("final_answer", "No answer generated")
            error = final_state.get("error")
            
            success = bool(answer and answer != "No answer generated" and not error)
            
            # Extract metadata
            metadata = {}
            if "sql_result" in final_state and isinstance(final_state["sql_result"], dict):
                metadata["row_count"] = final_state["sql_result"].get("row_count")
                metadata["columns"] = final_state["sql_result"].get("columns")
            
            # Log metrics in background
            query_metrics = QueryMetrics(
                question=request.question,
                sql_generated=generated_sql or "N/A",
                success=success,
                retry_count=retry_count,
                execution_time_ms=execution_time,
                row_count=metadata.get("row_count")
            )
            background_tasks.add_task(metrics.log_query, query_metrics)
            
            return QueryResponse(
                success=success,
                answer=answer,
                sql=generated_sql,
                execution_time_ms=execution_time,
                retry_count=retry_count,
                error=error,
                metadata=metadata
            )
        else:
            raise HTTPException(status_code=500, detail="Workflow failed to return state")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        execution_time = (time.time() - start_time) * 1000
        
        return QueryResponse(
            success=False,
            answer="",
            execution_time_ms=execution_time,
            retry_count=0,
            error=str(e)
        )

@api.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get session metrics"""
    summary = metrics.get_session_summary()
    
    return MetricsResponse(
        total_queries=summary["total_queries"],
        success_rate=summary["success_rate"],
        avg_execution_time_ms=summary["avg_execution_time_ms"],
        avg_retries=summary["avg_retries"]
    )

@api.get("/schema")
async def get_schema(table_name: Optional[str] = None):
    """Get database schema information"""
    try:
        from tools.schema_rag import get_relevant_schema
        
        query = f"schema for {table_name}" if table_name else "database schema"
        schema = get_relevant_schema(query)
        
        return {
            "success": True,
            "schema": schema,
            "table": table_name
        }
    except Exception as e:
        logger.error(f"Schema retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)
