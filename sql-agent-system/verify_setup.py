# verify_setup.py
"""
Verification script to test all components are working
Run this after installation to verify everything is set up correctly
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    tests = [
        ("logging_config", "Logging configuration"),
        ("graph", "LangGraph workflow"),
        ("state", "State definitions"),
        ("config", "LLM configuration"),
        ("agents.intent", "Intent agent"),
        ("agents.sql_generator", "SQL generator agent"),
        ("agents.validator", "Validator agent"),
        ("agents.responder", "Responder agent"),
        ("agents.retry_agent", "Retry agent (agentic)"),
        ("tools.db_connector", "Database connector"),
        ("tools.schema_rag", "Schema RAG"),
        ("utils.metrics", "Metrics collector"),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"  ✅ {description}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {description}: {str(e)}")
            failed += 1
    
    print(f"\n✅ Passed: {passed}/{len(tests)}")
    if failed > 0:
        print(f"❌ Failed: {failed}/{len(tests)}")
        return False
    return True

def test_interfaces():
    """Test that interface files exist"""
    print("\n🖥️ Testing interfaces...")
    
    interfaces = [
        ("main.py", "CLI interface"),
        ("launcher.py", "Unified launcher"),
        ("ui/gradio_app.py", "Gradio web UI"),
        ("api_server.py", "FastAPI REST API"),
        ("mcp_server.py", "MCP server"),
    ]
    
    passed = 0
    failed = 0
    
    for filepath, description in interfaces:
        if os.path.exists(filepath):
            print(f"  ✅ {description}")
            passed += 1
        else:
            print(f"  ❌ {description}: File not found")
            failed += 1
    
    print(f"\n✅ Available: {passed}/{len(interfaces)}")
    return failed == 0

def test_dependencies():
    """Test critical dependencies"""
    print("\n📦 Testing dependencies...")
    
    deps = [
        ("langchain", "LangChain"),
        ("langgraph", "LangGraph"),
        ("langchain_groq", "Groq"),
        ("langchain_google_genai", "Gemini"),
        ("langchain_huggingface", "HuggingFace embeddings"),
        ("faiss", "FAISS vector store"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pydantic", "Pydantic"),
        ("gradio", "Gradio UI"),
        ("fastapi", "FastAPI"),
        ("mcp", "MCP protocol"),
    ]
    
    passed = 0
    failed = 0
    
    for module, name in deps:
        try:
            __import__(module)
            print(f"  ✅ {name}")
            passed += 1
        except ImportError:
            print(f"  ❌ {name}: Not installed")
            failed += 1
    
    print(f"\n✅ Installed: {passed}/{len(deps)}")
    if failed > 0:
        print(f"\n💡 Install missing packages:")
        print(f"   pip install -r requirements.txt")
    return failed == 0

def test_env_config():
    """Test environment configuration"""
    print("\n⚙️ Testing environment configuration...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        ("GOOGLE_API_KEY", "Gemini API key"),
        ("GROQ_API_KEY", "Groq API key"),
        ("DATABASE_URL", "Database connection"),
    ]
    
    passed = 0
    warned = 0
    
    for var, description in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked = value[:10] + "..." if len(value) > 10 else "***"
            print(f"  ✅ {description}: {masked}")
            passed += 1
        else:
            print(f"  ⚠️ {description}: Not set")
            warned += 1
    
    if warned > 0:
        print(f"\n💡 Create .env file with required variables")
        print(f"   See QUICKSTART.md for instructions")
    
    return warned == 0

def test_database():
    """Test database connectivity"""
    print("\n💾 Testing database connection...")
    
    try:
        from tools.db_connector import DatabaseConnector
        
        if DatabaseConnector.test_connection():
            print("  ✅ Database connection successful")
            return True
        else:
            print("  ❌ Database connection failed")
            print("  💡 Run: python db_setup.py")
            return False
    except Exception as e:
        print(f"  ❌ Database test failed: {str(e)}")
        return False

def test_agentic_features():
    """Test agentic components"""
    print("\n🤖 Testing agentic features...")
    
    features = []
    
    # Test retry agent
    try:
        from agents.retry_agent import get_retry_decision
        state = {
            "question": "test",
            "error": "test error",
            "retry_count": 0,
            "generated_sql": "SELECT 1"
        }
        decision = get_retry_decision(state)
        if "should_retry" in decision:
            print("  ✅ Agentic retry agent")
            features.append(True)
        else:
            print("  ⚠️ Retry agent returned unexpected format")
            features.append(False)
    except Exception as e:
        print(f"  ❌ Retry agent: {str(e)}")
        features.append(False)
    
    # Test MCP server
    try:
        from mcp_server import SQLAgentMCPServer
        print("  ✅ MCP server available")
        features.append(True)
    except Exception as e:
        print(f"  ❌ MCP server: {str(e)}")
        features.append(False)
    
    return all(features)

def main():
    """Run all verification tests"""
    print("="*60)
    print("🔍 SQL AGENT SYSTEM - VERIFICATION SCRIPT")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("Imports", test_imports()))
    results.append(("Interfaces", test_interfaces()))
    results.append(("Dependencies", test_dependencies()))
    results.append(("Environment", test_env_config()))
    results.append(("Database", test_database()))
    results.append(("Agentic Features", test_agentic_features()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for category, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {category}")
    
    print(f"\n✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\n🚀 Quick Start:")
        print("   python launcher.py ui      # Launch web UI")
        print("   python launcher.py cli     # Launch CLI")
        print("   python launcher.py api     # Launch REST API")
        print("   python launcher.py mcp     # Launch MCP server")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please fix the issues above.")
        print("\n📚 Documentation:")
        print("   QUICKSTART.md - Setup instructions")
        print("   FIXES_APPLIED.md - Recent fixes")
        print("   AGENTIC_FEATURES.md - Feature guide")
        return 1

if __name__ == "__main__":
    sys.exit(main())
