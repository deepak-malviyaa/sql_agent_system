import sqlalchemy
from sqlalchemy import text, create_engine
from sqlalchemy.pool import QueuePool
import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class DatabaseConnector:
    """Production-ready database connector with connection pooling"""
    _engine = None
    
    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            connection_string = os.getenv(
                "DATABASE_URL", 
                "postgresql://user1:password@localhost:5432/entegris_db"
            )
            cls._engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Health check before each connection
                pool_recycle=3600    # Recycle connections every hour
            )
            logger.info("Database connection pool initialized")
        return cls._engine
    
    @classmethod
    def execute_query(cls, sql: str, timeout_seconds: int = 30) -> Dict[str, Any]:
        """
        Execute SELECT queries safely with timeout and error handling
        
        Args:
            sql: The SQL query to execute
            timeout_seconds: Query timeout in seconds
            
        Returns:
            Dict with success status, data, metadata, or error details
        """
        try:
            engine = cls.get_engine()
            with engine.connect() as conn:
                # Set statement timeout to prevent long-running queries
                conn.execute(text(f"SET statement_timeout = {timeout_seconds * 1000}"))
                
                # Execute the query
                result = conn.execute(text(sql))
                rows = result.fetchall()
                columns = result.keys()
                
                # Convert to list of dicts for JSON serialization
                data = [dict(zip(columns, row)) for row in rows]
                
                logger.info(f"Query executed successfully: {len(data)} rows returned")
                
                return {
                    "success": True,
                    "data": data,
                    "row_count": len(data),
                    "columns": list(columns),
                    "sql": sql
                }
                
        except sqlalchemy.exc.OperationalError as e:
            logger.error(f"Database connection error: {e}")
            return {
                "success": False,
                "error": f"Database connection failed: {str(e)}",
                "error_type": "OperationalError"
            }
        except sqlalchemy.exc.ProgrammingError as e:
            logger.error(f"SQL syntax error: {e}")
            return {
                "success": False,
                "error": f"SQL syntax error: {str(e)}",
                "error_type": "ProgrammingError"
            }
        except sqlalchemy.exc.TimeoutError as e:
            logger.error(f"Query timeout: {e}")
            return {
                "success": False,
                "error": f"Query exceeded {timeout_seconds}s timeout",
                "error_type": "TimeoutError"
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    @classmethod
    def test_connection(cls) -> bool:
        """Test database connectivity"""
        try:
            engine = cls.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test: SUCCESS")
            return True
        except Exception as e:
            logger.error(f"Database connection test: FAILED - {e}")
            return False
