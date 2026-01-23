# 🚀 Quick Start Guide

## Get Your Production-Ready SQL Agent Running in 5 Minutes

---

## Step 1: Install Dependencies (1 min)

```bash
# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install all requirements
pip install -r requirements.txt
```

---

## Step 2: Configure Environment (1 min)

Create a `.env` file in the project root:

```bash
# LLM API Keys (get free keys)
GOOGLE_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Database Connection
DATABASE_URL=postgresql://user1:password@localhost:5432/entegris_db

# Optional: Monitoring
# LANGSMITH_API_KEY=your_langsmith_key
# LANGCHAIN_PROJECT=sql-agent-prod
```

**Where to get API keys:**
- Gemini: https://ai.google.dev/
- Groq: https://console.groq.com/ (free tier available)

---

## Step 3: Setup Database (2 min)

```bash
# Initialize PostgreSQL with sample data
python db_setup.py
```

**Expected output:**
```
🛠️  Resetting Database...
📝 Creating Table 'sales_data'...
🌱 Seeding 50 rows of data...
✅ Setup Complete! Table 'sales_data' ready.
```

**Don't have PostgreSQL?** Install it:
- Windows: https://www.postgresql.org/download/windows/
- Mac: `brew install postgresql`
- Linux: `sudo apt-get install postgresql`

---

## Step 4: Run the System (1 min)

```bash
python main.py
```

**You should see:**
```
==================================================
🚀 SQL AGENT SYSTEM - PRODUCTION MODE
   Architecture: Multi-Agent LangGraph
   Models: Gemini (Reasoning) + Groq (Speed)
   Database: PostgreSQL with connection pooling
   Features: RAG Schema, Self-healing, Monitoring
   Type 'exit', 'quit', or 'stats' for options
==================================================

👉 Ask a question:
```

---

## Step 5: Try Sample Queries

### Simple Query
```
👉 Ask a question: What is the total revenue?

🔄 Processing: 'What is the total revenue?'...

   🔹 Finished: intent
   🔹 Finished: generate_sql
      [SQL]: SELECT SUM(total_revenue) FROM sales_data...
   🔹 Finished: validate
   🔹 Finished: execute_db
   🔹 Finished: interpret

----------------------------------------
🤖 ANSWER:
The total revenue is $125,450.00
----------------------------------------
```

### Complex Query
```
👉 Ask a question: Show me revenue by country for Electronics in 2023

🤖 ANSWER:
Based on the sales data, here's the revenue breakdown for Electronics by country in 2023:

• USA: $45,230.50 (highest)
• Germany: $32,100.00
• UK: $28,450.75
• France: $19,320.00

The USA accounts for 36% of total Electronics revenue, making it the strongest market.
```

### See Statistics
```
👉 Ask a question: stats

============================================================
📊 SESSION METRICS SUMMARY
============================================================
Total Queries: 5
Success Rate: 100.0%
Avg Retries: 0.20
Avg Execution Time: 1850ms
============================================================
```

---

## Common Commands

- **Exit:** Type `exit`, `quit`, or `q`
- **Stats:** Type `stats` to see session metrics
- **Logs:** Check `logs/sql_agent_*.log` for detailed logs
- **Metrics:** View `logs/metrics.jsonl` for query history

---

## Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution:** Install missing package
```bash
pip install <package-name>
```

### Issue: "Connection refused" (Database)
**Solution:** Ensure PostgreSQL is running
```bash
# Windows
services.msc  # Start PostgreSQL service

# Mac/Linux
sudo service postgresql start
```

### Issue: "Invalid API key"
**Solution:** Verify your .env file
```bash
# Test API keys
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Gemini:', bool(os.getenv('GOOGLE_API_KEY')))"
```

### Issue: "Schema not found"
**Solution:** Re-run database setup
```bash
python db_setup.py
```

---

## Testing the System

Run the test suite to verify everything works:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_system.py::TestValidator -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

**Expected:** 80-90% of tests should pass (some require database connection)

---

## File Structure Overview

```
sql-agent-system/
├── agents/               # Agent logic
│   ├── intent.py        # Parse user intent
│   ├── sql_generator.py # Generate SQL
│   ├── validator.py     # Validate SQL
│   ├── responder.py     # Generate answers
│   └── error_analyzer.py # Classify errors
├── tools/               # Utilities
│   ├── db_connector.py  # Database execution
│   └── schema_rag.py    # Schema retrieval
├── config/              # Configuration
│   └── logging_config.py # Logging setup
├── utils/               # Helper functions
│   └── metrics.py       # Metrics tracking
├── tests/               # Test suite
│   └── test_system.py   # Integration tests
├── logs/                # Auto-generated logs
├── graph.py             # LangGraph workflow
├── state.py             # State definition
├── main.py              # Entry point
├── config.py            # LLM factory
├── db_setup.py          # Database initialization
└── requirements.txt     # Dependencies
```

---

## Next Steps

### Immediate
1. ✅ Try the sample queries above
2. ✅ Experiment with your own questions
3. ✅ Check the logs to understand what's happening
4. ✅ Review metrics to see performance

### Short-Term (This Week)
1. Read [COMPREHENSIVE_ANALYSIS.md](COMPREHENSIVE_ANALYSIS.md) - Full system overview
2. Review [PRODUCTION_ROADMAP.md](PRODUCTION_ROADMAP.md) - Market trends & features
3. Read [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment options
4. Customize schema in [tools/schema_rag.py](tools/schema_rag.py)

### Medium-Term (This Month)
1. Add your own database tables
2. Customize the agents for your use case
3. Build a REST API wrapper (see DEPLOYMENT.md)
4. Deploy to production (Docker/Kubernetes)

---

## Getting Help

### Documentation
- **COMPREHENSIVE_ANALYSIS.md** - Complete system analysis
- **PRODUCTION_ROADMAP.md** - Market trends & implementation plan
- **DEPLOYMENT.md** - Production deployment guide

### Logs & Debugging
- Check `logs/sql_agent_*.log` for detailed logs
- View `logs/metrics.jsonl` for query metrics
- Use `stats` command for session summary

### Community
- Open issues on GitHub
- Join LangChain Discord
- Ask on Stack Overflow with tag: `text-to-sql`

---

## Example Queries to Try

### Revenue Analysis
- "What's the total revenue?"
- "Revenue by country"
- "Top 5 products by revenue"
- "Average order value"

### Time-Based
- "Sales in December 2023"
- "Revenue last 30 days"
- "Month-over-month growth"

### Product Analysis
- "Most popular product"
- "Electronics vs Clothing revenue"
- "Products sold in Germany"

### Geographic
- "Revenue from USA"
- "Countries with revenue > $10,000"
- "Sales by region"

---

## Success! 🎉

If you've made it here, you now have a **production-ready text-to-SQL agent** that:
- ✅ Executes real database queries
- ✅ Uses semantic schema retrieval
- ✅ Generates natural language responses
- ✅ Has multi-layer security validation
- ✅ Tracks metrics and performance
- ✅ Logs everything for debugging

**Your system is ready for real-world use!**

---

## Pro Tips

1. **Use specific questions:** "Revenue from Germany" > "Tell me about sales"
2. **Check stats regularly:** Type `stats` to monitor performance
3. **Review failed queries:** Check logs to improve prompts
4. **Start simple:** Test basic queries before complex ones
5. **Monitor costs:** Track API usage in Gemini/Groq dashboards

---

**Happy querying! 🚀**

For detailed analysis and next steps, see [COMPREHENSIVE_ANALYSIS.md](COMPREHENSIVE_ANALYSIS.md).

