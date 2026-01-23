# utils/metrics.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json
import os

@dataclass
class QueryMetrics:
    """Track metrics for each query execution"""
    question: str
    sql_generated: str
    success: bool
    retry_count: int
    execution_time_ms: float
    row_count: Optional[int] = None
    error_type: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        return {
            "question": self.question,
            "sql": self.sql_generated,
            "success": self.success,
            "retry_count": self.retry_count,
            "execution_time_ms": self.execution_time_ms,
            "row_count": self.row_count,
            "error_type": self.error_type,
            "timestamp": self.timestamp.isoformat()
        }

class MetricsCollector:
    """
    Collect and persist system metrics for monitoring and improvement.
    Use this data to:
    - Identify common failure patterns
    - Measure success rates
    - Track performance trends
    - Train on successful queries
    """
    
    def __init__(self, metrics_file: str = "logs/metrics.jsonl"):
        self.metrics_file = metrics_file
        self.session_metrics: List[QueryMetrics] = []
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
    
    def log_query(self, metrics: QueryMetrics):
        """Log a single query's metrics"""
        self.session_metrics.append(metrics)
        
        # Append to persistent log file (JSONL format)
        with open(self.metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metrics.to_dict()) + '\n')
    
    def get_session_summary(self) -> dict:
        """Get summary statistics for current session"""
        if not self.session_metrics:
            return {
                "total_queries": 0,
                "success_rate": 0.0,
                "avg_retries": 0.0,
                "avg_execution_time_ms": 0.0
            }
        
        total = len(self.session_metrics)
        successful = sum(1 for m in self.session_metrics if m.success)
        total_retries = sum(m.retry_count for m in self.session_metrics)
        total_time = sum(m.execution_time_ms for m in self.session_metrics)
        
        return {
            "total_queries": total,
            "success_rate": (successful / total) * 100,
            "avg_retries": total_retries / total,
            "avg_execution_time_ms": total_time / total,
            "most_common_errors": self._get_common_errors()
        }
    
    def _get_common_errors(self) -> List[tuple]:
        """Get top 3 most common error types"""
        from collections import Counter
        
        errors = [m.error_type for m in self.session_metrics if m.error_type]
        if not errors:
            return []
        
        return Counter(errors).most_common(3)
    
    def print_session_summary(self):
        """Print human-readable session summary"""
        summary = self.get_session_summary()
        
        print("\n" + "="*60)
        print("📊 SESSION METRICS SUMMARY")
        print("="*60)
        print(f"Total Queries: {summary['total_queries']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Avg Retries: {summary['avg_retries']:.2f}")
        print(f"Avg Execution Time: {summary['avg_execution_time_ms']:.0f}ms")
        
        if summary['most_common_errors']:
            print("\nTop Errors:")
            for error, count in summary['most_common_errors']:
                print(f"  • {error}: {count} occurrences")
        
        print("="*60 + "\n")

# Global instance
_metrics_collector = MetricsCollector()

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    return _metrics_collector
