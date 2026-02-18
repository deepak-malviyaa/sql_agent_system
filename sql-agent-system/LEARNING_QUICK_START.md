# 🧠 Learning System - Quick Reference

## Setup (One Time)

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize learning system
python setup_learning_system.py
```

## Usage

### CLI Mode
```bash
python main.py

# Commands:
> learning          # View learning statistics
> stats            # View session statistics  
> exit             # Exit with summary
```

### Web UI Mode
```bash
python launcher.py ui

# Features:
- Rate responses with 👍/👎
- Provide SQL corrections
- View learning statistics
- Track improvement over time
```

## How It Works

### 1. Automatic Learning
Every query you run is:
- ✅ Saved to history database
- ✅ Converted to embedding vector
- ✅ Available for similarity search
- ✅ Used to improve future queries

### 2. Smart SQL Generation
When generating SQL, the system:
1. Searches for similar past queries
2. Finds successful examples
3. Uses them as learning context
4. Generates better SQL

### 3. Feedback Loop
Provide feedback to improve:
- 👍 **Thumbs Up** → Reinforces good patterns
- 👎 **Thumbs Down** → Flags for improvement
- ✏️ **SQL Correction** → Direct learning from experts
- ⭐ **Rating** → Quantifies quality

## Example Flow

```
User: "What is total revenue from Germany?"
  ↓
System searches history...
  ↓
Found similar: "Show me sales from France" ✅
  ↓
Learns from past pattern
  ↓
Generates accurate SQL: SELECT SUM(amount) FROM sales WHERE country = 'Germany';
  ↓
Executes successfully ✅
  ↓
Saves to history for future learning
  ↓
User rates 👍 (reinforces pattern)
```

## Key Statistics

Check improvement with:
```bash
> learning
```

Monitor:
- **Success Rate** - Should increase over time
- **Avg Retries** - Should decrease over time
- **Positive Feedback** - Indicates quality
- **Total Queries** - More data = better learning

## Files & Locations

```
data/
  └── query_history.db      # Learning database (SQLite)
  
logs/
  └── metrics.jsonl         # Performance metrics
  
tools/
  └── query_history.py      # Learning system code
```

## Troubleshooting

**No learning happening?**
```bash
# Verify database exists
ls data/query_history.db

# Re-run setup
python setup_learning_system.py
```

**Low similarity scores?**
- Need more queries in history (minimum 10-20)
- Try asking similar questions
- Provide more specific queries

**Database errors?**
```bash
# Reset if needed
rm data/query_history.db
python setup_learning_system.py
```

## API Quick Reference

```python
from tools.query_history import get_query_history

qh = get_query_history()

# Save query
qh.save_query(question="...", generated_sql="...", success=True)

# Find similar
similar = qh.find_similar_queries("revenue by country", limit=5)

# Add feedback
qh.add_feedback(query_id=1, feedback_type="thumbs_up", rating=5)

# Get stats
stats = qh.get_statistics()
```

## Performance

- **Query Overhead:** +50-100ms
- **Storage:** ~2KB per query
- **Memory:** Minimal impact
- **Benefit:** Significantly improved accuracy

## Best Practices

✅ **DO:**
- Provide feedback regularly
- Correct wrong SQL
- Ask diverse questions
- Monitor statistics

❌ **DON'T:**
- Ignore failed queries
- Skip feedback
- Delete history database
- Use inconsistent terminology

---

**📖 Full Documentation:** [LEARNING_SYSTEM_GUIDE.md](LEARNING_SYSTEM_GUIDE.md)
