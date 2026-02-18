"""
Query History & Learning System

This module enables the agent to learn from past queries by:
1. Storing all queries with success/failure status
2. Collecting user feedback (thumbs up/down, corrections)
3. Finding similar past queries for context
4. Providing learning examples to improve SQL generation

Architecture:
- SQLite database for history storage
- Vector embeddings for similarity search
- Feedback loop integration
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class QueryHistory:
    """
    Manages query history with learning capabilities.
    
    Features:
    - Stores all queries with metadata
    - Tracks success/failure patterns
    - Collects user feedback
    - Finds similar past queries
    - Provides learning examples
    """
    
    def __init__(self, db_path: str = "data/query_history.db"):
        self.db_path = db_path
        self._ensure_db_exists()
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        logger.info(f"Query history initialized: {db_path}")
    
    def _ensure_db_exists(self):
        """Create database and tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main query history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    generated_sql TEXT,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    execution_time_ms REAL,
                    row_count INTEGER,
                    retry_count INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT
                )
            """)
            
            # User feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER NOT NULL,
                    feedback_type TEXT CHECK(feedback_type IN ('thumbs_up', 'thumbs_down', 'correction')),
                    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                    corrected_sql TEXT,
                    comment TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (query_id) REFERENCES query_history(id)
                )
            """)
            
            # Query embeddings table (for similarity search)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER NOT NULL,
                    embedding BLOB NOT NULL,
                    FOREIGN KEY (query_id) REFERENCES query_history(id)
                )
            """)
            
            # Learning patterns table (aggregated insights)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    question_pattern TEXT,
                    sql_template TEXT,
                    success_rate REAL,
                    usage_count INTEGER DEFAULT 1,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("Query history database initialized")
    
    def save_query(
        self,
        question: str,
        generated_sql: Optional[str],
        success: bool,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        row_count: Optional[int] = None,
        retry_count: int = 0,
        session_id: Optional[str] = None
    ) -> int:
        """
        Save a query execution to history.
        
        Returns:
            query_id: ID of the saved query
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO query_history 
                (question, generated_sql, success, error_message, execution_time_ms, 
                 row_count, retry_count, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (question, generated_sql, success, error_message, execution_time_ms,
                  row_count, retry_count, session_id))
            
            query_id = cursor.lastrowid
            
            # Generate and store embedding for similarity search
            try:
                embedding = self.embeddings.embed_query(question)
                embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
                cursor.execute("""
                    INSERT INTO query_embeddings (query_id, embedding)
                    VALUES (?, ?)
                """, (query_id, embedding_bytes))
            except Exception as e:
                logger.warning(f"Failed to generate embedding: {e}")
            
            conn.commit()
            logger.info(f"Saved query {query_id}: success={success}, retries={retry_count}")
            return query_id
    
    def add_feedback(
        self,
        query_id: int,
        feedback_type: str,
        rating: Optional[int] = None,
        corrected_sql: Optional[str] = None,
        comment: Optional[str] = None
    ):
        """
        Add user feedback for a query.
        
        Args:
            query_id: ID of the query
            feedback_type: 'thumbs_up', 'thumbs_down', or 'correction'
            rating: 1-5 star rating
            corrected_sql: User's corrected SQL (for learning)
            comment: Additional feedback text
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO query_feedback 
                (query_id, feedback_type, rating, corrected_sql, comment)
                VALUES (?, ?, ?, ?, ?)
            """, (query_id, feedback_type, rating, corrected_sql, comment))
            conn.commit()
            
            logger.info(f"Added feedback for query {query_id}: {feedback_type}")
    
    def find_similar_queries(
        self,
        question: str,
        limit: int = 5,
        success_only: bool = True
    ) -> List[Dict]:
        """
        Find similar past queries using embedding similarity.
        
        Args:
            question: Current question
            limit: Max number of results
            success_only: Only return successful queries
            
        Returns:
            List of similar queries with metadata
        """
        try:
            # Generate embedding for current question
            query_embedding = np.array(
                self.embeddings.embed_query(question),
                dtype=np.float32
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all embeddings with their queries
                success_filter = "AND h.success = 1" if success_only else ""
                cursor.execute(f"""
                    SELECT 
                        h.id, h.question, h.generated_sql, h.success,
                        h.execution_time_ms, h.row_count, h.retry_count,
                        e.embedding
                    FROM query_history h
                    JOIN query_embeddings e ON h.id = e.query_id
                    WHERE h.generated_sql IS NOT NULL {success_filter}
                    ORDER BY h.timestamp DESC
                    LIMIT 100
                """)
                
                results = []
                for row in cursor.fetchall():
                    # Calculate cosine similarity
                    stored_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                    similarity = np.dot(query_embedding, stored_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                    )
                    
                    results.append({
                        'id': row['id'],
                        'question': row['question'],
                        'generated_sql': row['generated_sql'],
                        'success': row['success'],
                        'execution_time_ms': row['execution_time_ms'],
                        'row_count': row['row_count'],
                        'retry_count': row['retry_count'],
                        'similarity': float(similarity)
                    })
                
                # Sort by similarity and return top results
                results.sort(key=lambda x: x['similarity'], reverse=True)
                return results[:limit]
                
        except Exception as e:
            logger.error(f"Error finding similar queries: {e}")
            return []
    
    def get_learning_examples(self, question: str, limit: int = 3) -> str:
        """
        Get formatted learning examples for prompt injection.
        
        This provides the SQL generator with successful past queries
        that are similar to the current question.
        
        Returns:
            Formatted string of examples
        """
        similar = self.find_similar_queries(question, limit=limit)
        
        if not similar:
            return ""
        
        examples = []
        for i, query in enumerate(similar, 1):
            examples.append(f"""
Example {i} (similarity: {query['similarity']:.2f}):
Question: {query['question']}
SQL: {query['generated_sql']}
""")
        
        return "\n".join(examples)
    
    def get_statistics(self) -> Dict:
        """Get overall learning statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Overall stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_queries,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                    AVG(execution_time_ms) as avg_execution_time,
                    AVG(retry_count) as avg_retries
                FROM query_history
            """)
            stats = dict(cursor.fetchone())
            
            # Feedback stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_feedback,
                    SUM(CASE WHEN feedback_type = 'thumbs_up' THEN 1 ELSE 0 END) as thumbs_up,
                    SUM(CASE WHEN feedback_type = 'thumbs_down' THEN 1 ELSE 0 END) as thumbs_down,
                    SUM(CASE WHEN feedback_type = 'correction' THEN 1 ELSE 0 END) as corrections,
                    AVG(rating) as avg_rating
                FROM query_feedback
            """)
            feedback_stats = dict(cursor.fetchone())
            
            stats.update(feedback_stats)
            
            # Calculate success rate
            if stats['total_queries'] > 0:
                stats['success_rate'] = (stats['successful'] / stats['total_queries']) * 100
            else:
                stats['success_rate'] = 0.0
            
            return stats
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict]:
        """Get recent queries for display"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id, question, generated_sql, success, error_message,
                    execution_time_ms, row_count, retry_count, timestamp
                FROM query_history
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_corrected_queries(self) -> List[Dict]:
        """
        Get queries where users provided corrections.
        These are valuable for improving the system.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    h.question,
                    h.generated_sql as original_sql,
                    f.corrected_sql,
                    f.comment,
                    f.timestamp
                FROM query_history h
                JOIN query_feedback f ON h.id = f.query_id
                WHERE f.feedback_type = 'correction'
                  AND f.corrected_sql IS NOT NULL
                ORDER BY f.timestamp DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def export_learning_data(self, output_file: str = "data/learning_export.json"):
        """
        Export all learning data for analysis or model fine-tuning.
        
        This creates a dataset of question -> SQL pairs with feedback
        that can be used to fine-tune the model.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    h.question,
                    h.generated_sql,
                    h.success,
                    f.feedback_type,
                    f.rating,
                    f.corrected_sql,
                    f.comment
                FROM query_history h
                LEFT JOIN query_feedback f ON h.id = f.query_id
                WHERE h.success = 1 OR f.corrected_sql IS NOT NULL
                ORDER BY h.timestamp
            """)
            
            data = [dict(row) for row in cursor.fetchall()]
            
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Exported {len(data)} queries to {output_file}")
            return output_file


# Singleton instance
_query_history_instance = None

def get_query_history() -> QueryHistory:
    """Get or create global query history instance"""
    global _query_history_instance
    if _query_history_instance is None:
        _query_history_instance = QueryHistory()
    return _query_history_instance
