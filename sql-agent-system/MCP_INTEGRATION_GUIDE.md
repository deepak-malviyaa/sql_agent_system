# 🔗 MCP Integration Guide
## Connecting SQL Agent to Other Tools & Agents

**Date:** January 23, 2026  
**MCP Version:** 0.9.0+

---

## Table of Contents

1. [What is MCP?](#what-is-mcp)
2. [Quick Start](#quick-start)
3. [Integration Examples](#integration-examples)
4. [Claude Desktop Integration](#claude-desktop-integration)
5. [Custom Agent Integration](#custom-agent-integration)
6. [Langfuse Monitoring](#langfuse-monitoring)
7. [Troubleshooting](#troubleshooting)

---

## What is MCP?

**Model Context Protocol (MCP)** is a standard for AI agents to expose and use tools. Your SQL Agent becomes a tool that other agents can discover and call.

### Why MCP?
- ✅ **Standardized:** Works with any MCP-compatible client (Claude Desktop, custom agents, etc.)
- ✅ **Discoverable:** Other agents automatically see your SQL Agent's capabilities
- ✅ **Composable:** Build multi-agent systems where agents call each other
- ✅ **Secure:** Each tool defines its own permissions and validation

### Your SQL Agent Exposes 3 MCP Tools:

| Tool | Purpose | Example Use |
|------|---------|-------------|
| `execute_sql_query` | Natural language → SQL → Answer | "What's our revenue?" |
| `get_schema_info` | Retrieve database schema | Get table/column info |
| `validate_sql` | Check SQL for security/syntax | Pre-validate queries |

---

## Quick Start

### 1. Start Your MCP Server

```bash
# Terminal 1: Start the SQL Agent MCP Server
python launcher.py mcp

# OR directly:
python mcp_server.py
```

**Output:**
```
🚀 SQL AGENT SYSTEM - MCP SERVER MODE
==================================================
Starting SQL Agent MCP Server...
Server ready on stdio transport
Waiting for connections...
```

### 2. Test with MCP Inspector

```bash
# Install MCP inspector (if not already installed)
npm install -g @modelcontextprotocol/inspector

# Connect to your server
mcp-inspector python mcp_server.py
```

**You'll see:**
- ✅ Available tools: `execute_sql_query`, `get_schema_info`, `validate_sql`
- ✅ Tool schemas with parameters
- ✅ Test UI for calling tools

---

## Integration Examples

### Example 1: Claude Desktop Integration

**Add your SQL Agent as a Claude Desktop tool:**

#### Step 1: Find Claude Config File

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Mac:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

#### Step 2: Add MCP Server Config

```json
{
  "mcpServers": {
    "sql-agent": {
      "command": "python",
      "args": [
        "d:/T2S/sql-agent-system/mcp_server.py"
      ],
      "env": {
        "GOOGLE_API_KEY": "your_gemini_key",
        "GROQ_API_KEY": "your_groq_key",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/db"
      }
    }
  }
}
```

#### Step 3: Restart Claude Desktop

#### Step 4: Use in Claude

**You can now ask Claude:**
```
"Use the sql-agent tool to find out what our total revenue is from Germany"
```

**Claude will:**
1. Discover your `execute_sql_query` tool
2. Call it with: `question="What's the total revenue from Germany?"`
3. Receive: `answer="The total revenue from Germany is $45,230.00"`
4. Format response for you

---

### Example 2: Python Client Integration

**Call your SQL Agent from another Python script:**

```python
# other_agent.py
import asyncio
from mcp.client import MCPClient
from mcp.transports.stdio import StdioServerParameters, stdio_client

async def query_sql_agent():
    """Use SQL Agent as a tool"""
    
    # Configure connection to your SQL Agent MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["d:/T2S/sql-agent-system/mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with MCPClient(read, write) as client:
            # Initialize session
            await client.initialize()
            
            # List available tools
            tools = await client.list_tools()
            print(f"📋 Available tools: {[t.name for t in tools]}")
            
            # Call the SQL query tool
            result = await client.call_tool(
                "execute_sql_query",
                arguments={
                    "question": "What's our total revenue?",
                    "max_retries": 3
                }
            )
            
            print(f"✅ Answer: {result.content}")
            return result

# Run it
asyncio.run(query_sql_agent())
```

**Output:**
```
📋 Available tools: ['execute_sql_query', 'get_schema_info', 'validate_sql']
✅ Answer: The total revenue is $125,450.00
```

---

### Example 3: Multi-Agent Research System

**Build a research agent that uses SQL Agent for data:**

```python
# research_agent.py
import asyncio
from mcp.client import MCPClient
from mcp.transports.stdio import StdioServerParameters, stdio_client
from langchain_google_genai import ChatGoogleGenerativeAI

async def research_with_sql_agent(research_question: str):
    """
    Research agent that:
    1. Breaks down research question
    2. Uses SQL Agent to get data
    3. Analyzes and synthesizes findings
    """
    
    # Initialize LLM for research analysis
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    
    # Connect to SQL Agent
    server_params = StdioServerParameters(
        command="python",
        args=["d:/T2S/sql-agent-system/mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with MCPClient(read, write) as client:
            await client.initialize()
            
            # Step 1: Decompose research question into data queries
            print(f"🔍 Researching: {research_question}")
            
            decomposition = llm.invoke(f"""
            Break this research question into 3-5 specific data queries:
            "{research_question}"
            
            Return as JSON array of questions.
            """)
            
            queries = eval(decomposition.content)  # Parse JSON
            
            # Step 2: Gather data from SQL Agent
            findings = []
            for query in queries:
                print(f"  📊 Querying: {query}")
                
                result = await client.call_tool(
                    "execute_sql_query",
                    arguments={"question": query}
                )
                
                findings.append({
                    "query": query,
                    "answer": result.content
                })
            
            # Step 3: Synthesize findings
            synthesis_prompt = f"""
            Research Question: {research_question}
            
            Findings:
            {chr(10).join([f"- {f['query']}: {f['answer']}" for f in findings])}
            
            Provide a comprehensive answer with insights.
            """
            
            final_answer = llm.invoke(synthesis_prompt)
            
            print(f"\n✅ Research Complete:")
            print(final_answer.content)
            
            return final_answer.content

# Example usage
asyncio.run(research_with_sql_agent(
    "What are the top performing product categories and their revenue trends?"
))
```

**Output:**
```
🔍 Researching: What are the top performing product categories...
  📊 Querying: What are the top 5 product categories by revenue?
  📊 Querying: What's the revenue trend for Electronics over time?
  📊 Querying: What's the average order value per category?

✅ Research Complete:
Based on the data analysis:

1. Top Categories: Electronics ($245K), Clothing ($189K), Home Goods ($156K)
2. Electronics shows 15% QoQ growth - strongest performer
3. Average order values: Electronics ($89), Clothing ($45), Home Goods ($67)

Key Insight: Electronics dominates both in volume and value, with 
consistent growth trajectory suggesting continued investment opportunity.
```

---

### Example 4: Slack Bot Integration

**Create a Slack bot that uses your SQL Agent:**

```python
# slack_bot.py
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import asyncio
from mcp.client import MCPClient
from mcp.transports.stdio import StdioServerParameters, stdio_client

app = App(token="your-bot-token")

async def query_sql_agent(question):
    """Query the SQL Agent MCP server"""
    server_params = StdioServerParameters(
        command="python",
        args=["d:/T2S/sql-agent-system/mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with MCPClient(read, write) as client:
            await client.initialize()
            
            result = await client.call_tool(
                "execute_sql_query",
                arguments={"question": question}
            )
            
            return result.content

@app.command("/query")
def handle_query_command(ack, command, respond):
    """Handle /query command in Slack"""
    ack()  # Acknowledge command
    
    question = command['text']
    
    # Run async query
    answer = asyncio.run(query_sql_agent(question))
    
    respond(f"📊 *SQL Agent Results:*\n\n{answer}")

# Start bot
if __name__ == "__main__":
    handler = SocketModeHandler(app, "your-app-token")
    handler.start()
```

**Usage in Slack:**
```
/query What's our revenue this month?

📊 SQL Agent Results:
This month's revenue is $342,150.00, representing a 12% 
increase compared to last month.
```

---

### Example 5: VS Code Extension Integration

**Add SQL Agent to a VS Code extension:**

```typescript
// extension.ts
import * as vscode from 'vscode';
import { spawn } from 'child_process';

class SQLAgentMCPClient {
  private process: any;
  
  async query(question: string): Promise<string> {
    return new Promise((resolve, reject) => {
      // Start MCP server process
      this.process = spawn('python', [
        'd:/T2S/sql-agent-system/mcp_server.py'
      ]);
      
      // Send MCP request
      const request = {
        jsonrpc: '2.0',
        method: 'tools/call',
        params: {
          name: 'execute_sql_query',
          arguments: { question }
        },
        id: 1
      };
      
      this.process.stdin.write(JSON.stringify(request) + '\n');
      
      // Handle response
      this.process.stdout.on('data', (data: Buffer) => {
        const response = JSON.parse(data.toString());
        resolve(response.result.content);
      });
    });
  }
}

export function activate(context: vscode.ExtensionContext) {
  const client = new SQLAgentMCPClient();
  
  // Register command
  let disposable = vscode.commands.registerCommand(
    'extension.querySQLAgent',
    async () => {
      const question = await vscode.window.showInputBox({
        prompt: 'Ask a data question'
      });
      
      if (question) {
        const answer = await client.query(question);
        vscode.window.showInformationMessage(answer);
      }
    }
  );
  
  context.subscriptions.push(disposable);
}
```

---

## Langfuse Monitoring with MCP

### Why Add Langfuse to MCP?

When other agents call your SQL Agent via MCP, you want to track:
- 📊 **Usage metrics:** Which agents call you most?
- 💰 **Cost attribution:** How much does each caller cost?
- 🐛 **Debug failures:** What queries fail from external agents?
- ⚡ **Performance:** Latency per caller

### Step 1: Enable Langfuse in config.py

```python
# config.py
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv(override=True)

class LLMFactory:
    @staticmethod
    def get_llm(model_type="reasoning"):
        # ENABLE LANGFUSE
        callbacks = []
        try:
            from langfuse.callback import CallbackHandler
            
            # Optional: Tag by caller (MCP vs UI vs API)
            metadata = {
                "interface": os.getenv("INTERFACE_TYPE", "unknown"),
                "session_id": os.getenv("SESSION_ID", "")
            }
            
            langfuse_handler = CallbackHandler(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
                metadata=metadata
            )
            callbacks.append(langfuse_handler)
        except ImportError:
            print("⚠️ Langfuse not available - install: pip install langfuse")
        
        provider = os.getenv("MODEL_REASONING") if model_type == "reasoning" else os.getenv("MODEL_FAST")
        if not provider:
            provider = "gemini" if model_type == "reasoning" else "groq"
        
        if provider == "gemini":
            return ChatGoogleGenerativeAI(
                model="gemini-pro", 
                temperature=0,
                callbacks=callbacks
            )
        elif provider == "groq":
            return ChatGroq(
                model_name="llama-3.1-8b-instant", 
                temperature=0,
                callbacks=callbacks
            )
```

### Step 2: Add Environment Variables

```bash
# .env
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com

# Optional: Tag by interface
INTERFACE_TYPE=mcp
```

### Step 3: Enhanced MCP Server with Langfuse

```python
# mcp_server.py (enhanced version)
import os
from mcp.server import Server
from graph import app
import logging

# Set interface type for Langfuse tagging
os.environ["INTERFACE_TYPE"] = "mcp"

logger = logging.getLogger(__name__)

class SQLAgentMCPServer:
    def __init__(self):
        self.server = Server("sql-agent-server")
        self.setup_tools()
    
    def setup_tools(self):
        @self.server.tool()
        async def execute_sql_query(
            question: str,
            max_retries: int = 3,
            caller_id: str = "unknown"  # NEW: Track caller
        ) -> Dict[str, Any]:
            """Execute SQL query with Langfuse tracking"""
            
            # Set caller metadata for Langfuse
            os.environ["SESSION_ID"] = f"mcp-{caller_id}"
            
            logger.info(f"MCP query from {caller_id}: {question}")
            
            try:
                inputs = {
                    "question": question,
                    "retry_count": 0,
                    "error": None
                }
                
                final_state = None
                for output in app.stream(inputs, {"recursion_limit": 50}):
                    for agent_name, agent_state in output.items():
                        final_state = agent_state
                
                if final_state:
                    return {
                        "success": bool(final_state.get("final_answer")),
                        "answer": final_state.get("final_answer", ""),
                        "sql": final_state.get("generated_sql", ""),
                        "retry_count": final_state.get("retry_count", 0),
                        "caller_id": caller_id  # Track in response
                    }
            except Exception as e:
                logger.error(f"MCP query failed: {e}")
                return {"success": False, "error": str(e)}
```

### Step 4: View Traces in Langfuse

**Sign up:** https://cloud.langfuse.com

**Dashboard shows:**
```
MCP Calls (Last 24h):
┌──────────────────┬──────────┬──────────┬──────────┐
│ Caller           │ Queries  │ Avg Time │ Cost     │
├──────────────────┼──────────┼──────────┼──────────┤
│ Claude Desktop   │ 45       │ 2.1s     │ $0.14    │
│ research-agent   │ 23       │ 3.2s     │ $0.09    │
│ slack-bot        │ 12       │ 1.8s     │ $0.04    │
└──────────────────┴──────────┴──────────┴──────────┘
```

**Click any query to see:**
- Full conversation trace
- LLM prompts sent (intent, SQL generation, response)
- Token usage per step
- Errors and retries
- SQL generated
- Database execution time

---

## Advanced Integration: Agent Marketplace

### Build an Agent that Discovers & Uses Your SQL Agent

```python
# autonomous_agent.py
import asyncio
from mcp.client import MCPClient
from mcp.transports.stdio import StdioServerParameters, stdio_client

async def discover_and_use_tools():
    """Agent discovers SQL tool and uses it autonomously"""
    
    # Connect to MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["d:/T2S/sql-agent-system/mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with MCPClient(read, write) as client:
            await client.initialize()
            
            # Discover available tools
            tools = await client.list_tools()
            
            print("🔍 Discovered tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Agent decides which tool to use based on task
            task = "I need to know revenue metrics"
            
            # Simple reasoning: if task mentions "revenue" or "data", use SQL tool
            if any(word in task.lower() for word in ["revenue", "data", "sales", "customers"]):
                print(f"\n✅ Task requires data - using 'execute_sql_query' tool")
                
                result = await client.call_tool(
                    "execute_sql_query",
                    arguments={"question": "What's the total revenue?"}
                )
                
                print(f"📊 Result: {result.content}")
            else:
                print("ℹ️ Task doesn't require SQL tool")

asyncio.run(discover_and_use_tools())
```

---

## Troubleshooting

### Issue 1: "Connection refused" or "Server not responding"

**Solution:**
```bash
# Check if server is running
netstat -ano | findstr :3000  # Windows
lsof -i :3000  # Mac/Linux

# Restart server
python launcher.py mcp
```

### Issue 2: "Tool not found"

**Solution:**
```python
# List available tools to verify name
tools = await client.list_tools()
print([t.name for t in tools])

# Use exact name from list
await client.call_tool("execute_sql_query", {...})
```

### Issue 3: Langfuse "Authentication failed"

**Solution:**
```bash
# Check keys in .env
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY

# Verify at https://cloud.langfuse.com/settings
# Keys should start with pk-lf- and sk-lf-
```

### Issue 4: High latency on MCP calls

**Solution:**
```python
# Add timeout to prevent hanging
result = await asyncio.wait_for(
    client.call_tool("execute_sql_query", {...}),
    timeout=30.0  # 30 seconds max
)

# Or increase recursion limit
for output in app.stream(inputs, {"recursion_limit": 100}):
    ...
```

---

## MCP Client Examples Repository

**More examples at:**
- https://github.com/modelcontextprotocol/examples
- https://github.com/anthropics/mcp-examples

**Community servers:**
- File system access
- Web search
- Code execution
- Image generation
- PDF processing

**Your SQL Agent can:**
- Call these servers as tools
- Be called by agents using these servers
- Create multi-agent workflows

---

## Next Steps

1. ✅ **Test MCP server** with inspector
2. ✅ **Add to Claude Desktop** for quick testing
3. ✅ **Enable Langfuse** for monitoring
4. ✅ **Build custom agent** that uses your SQL tool
5. ✅ **Share server** with team (publish to registry)

**Documentation:**
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Claude Desktop MCP](https://docs.anthropic.com/claude/docs/mcp)
- [Langfuse Tracing](https://langfuse.com/docs/tracing)

---

**Document Version:** 1.0  
**Last Updated:** January 23, 2026  
**Status:** Production Ready
