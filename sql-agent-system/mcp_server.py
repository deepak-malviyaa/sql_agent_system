# mcp_server.py
"""
Model Context Protocol (MCP) Server for SQL Agent System
Provides agent-to-agent communication and tool exposure
"""

import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
import json
from graph import app
from typing import Optional, Dict, Any, Sequence
import logging

logger = logging.getLogger(__name__)

class SQLAgentMCPServer:
    """MCP Server exposing SQL Agent capabilities to other agents"""
    
    def __init__(self):
        self.server = Server("sql-agent-server")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Register agent tools for MCP exposure"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="execute_sql_query",
                    description="Execute a natural language question as SQL query. Returns answer, SQL, and metadata.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Natural language question about the data"
                            },
                            "max_retries": {
                                "type": "integer",
                                "description": "Maximum retry attempts",
                                "default": 3
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Query timeout in seconds",
                                "default": 30
                            }
                        },
                        "required": ["question"]
                    }
                ),
                Tool(
                    name="get_schema_info",
                    description="Get database schema information for a specific table or entire database.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Optional specific table name"
                            }
                        }
                    }
                ),
                Tool(
                    name="validate_sql",
                    description="Validate SQL query for security and syntax issues.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL query to validate"
                            }
                        },
                        "required": ["sql"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
            """Handle tool calls"""
            
            if name == "execute_sql_query":
                result = await self.execute_sql_query(
                    arguments.get("question"),
                    arguments.get("max_retries", 3),
                    arguments.get("timeout", 30)
                )
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "get_schema_info":
                result = await self.get_schema_info(
                    arguments.get("table_name")
                )
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            elif name == "validate_sql":
                result = await self.validate_sql(
                    arguments.get("sql")
                )
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def execute_sql_query(
        self,
        question: str,
        max_retries: int = 3,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a natural language question as SQL query.
        
        This tool allows other agents to query databases using natural language.
        The agent will:
        1. Parse the intent
        2. Generate SQL from schema
        3. Validate for security
        4. Execute against database
        5. Return natural language answer
        
        Args:
            question: Natural language question about the data
            max_retries: Maximum retry attempts (default: 3)
            timeout: Query timeout in seconds (default: 30)
            
        Returns:
            Dict with answer, sql, success status, and metadata
        """
        logger.info(f"MCP Server received query: {question}")
        
        try:
            inputs = {
                "question": question,
                "retry_count": 0,
                "error": None
            }
            
            final_state = None
            for output in app.stream(inputs):
                for agent_name, agent_state in output.items():
                    final_state = agent_state
                    
                    # Stop if we've exceeded retries
                    if agent_state.get("retry_count", 0) >= max_retries:
                        break
            
            if final_state:
                return {
                    "success": bool(final_state.get("final_answer")),
                    "answer": final_state.get("final_answer", "No answer generated"),
                    "sql": final_state.get("generated_sql", ""),
                    "retry_count": final_state.get("retry_count", 0),
                    "error": final_state.get("error")
                }
            else:
                return {
                    "success": False,
                    "answer": "Query processing failed",
                    "error": "No state returned from workflow"
                }
                
        except Exception as e:
            logger.error(f"MCP query execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_schema_info(
        self,
        table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get database schema information.
        
        Args:
            table_name: Optional specific table name
            
        Returns:
            Schema information as dict
        """
        from tools.schema_rag import get_relevant_schema
        
        try:
            query = f"schema for {table_name}" if table_name else "database schema"
            schema = get_relevant_schema(query)
            
            return {
                "success": True,
                "schema": schema,
                "table": table_name
            }
        except Exception as e:
            logger.error(f"Schema retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_sql(
        self,
        sql: str
    ) -> Dict[str, Any]:
        """
        Validate SQL query for security and syntax.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Validation results with any errors
        """
        from agents.validator import validator_agent
        
        try:
            state = {
                "generated_sql": sql,
                "retry_count": 0
            }
            
            result = validator_agent(state)
            
            return {
                "success": result["error"] is None,
                "error": result["error"],
                "sql": sql
            }
        except Exception as e:
            logger.error(f"SQL validation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run(self, transport="stdio"):
        """Run the MCP server"""
        logger.info("Starting SQL Agent MCP Server...")
        
        if transport == "stdio":
            from mcp.server.stdio import stdio_server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        else:
            raise ValueError(f"Unsupported transport: {transport}")

def start_mcp_server():
    """Start the MCP server (entry point)"""
    server = SQLAgentMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    start_mcp_server()
