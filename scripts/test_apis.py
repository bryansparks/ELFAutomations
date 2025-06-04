#!/usr/bin/env python3
"""
API Connectivity Test Script

Tests connectivity to external APIs with configured keys.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import structlog
from dotenv import load_dotenv

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def test_anthropic_api():
    """Test Anthropic API connectivity."""
    try:
        from langchain_anthropic import ChatAnthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set - skipping test")
            return False
        
        logger.info("Testing Anthropic API connectivity...")
        
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            temperature=0.1,
            anthropic_api_key=api_key
        )
        
        # Simple test message
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content="Hello! Please respond with 'API test successful'")])
        
        logger.info("Anthropic API test successful", response=response.content)
        return True
        
    except Exception as e:
        logger.error("Anthropic API test failed", error=str(e))
        return False


async def test_openai_api():
    """Test OpenAI API connectivity."""
    try:
        from langchain_openai import ChatOpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set - skipping test")
            return False
        
        logger.info("Testing OpenAI API connectivity...")
        
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            max_tokens=100,
            temperature=0.1,
            openai_api_key=api_key
        )
        
        # Simple test message
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content="Hello! Please respond with 'API test successful'")])
        
        logger.info("OpenAI API test successful", response=response.content)
        return True
        
    except Exception as e:
        logger.error("OpenAI API test failed", error=str(e))
        return False


async def test_database_connectivity():
    """Test database connectivity."""
    try:
        import asyncpg
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.warning("DATABASE_URL not set - skipping test")
            return False
        
        logger.info("Testing database connectivity...")
        
        conn = await asyncpg.connect(db_url)
        result = await conn.fetchval("SELECT version()")
        await conn.close()
        
        logger.info("Database connectivity test successful", version=result)
        return True
        
    except Exception as e:
        logger.error("Database connectivity test failed", error=str(e))
        return False


async def test_redis_connectivity():
    """Test Redis connectivity."""
    try:
        import redis.asyncio as redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        logger.info("Testing Redis connectivity...")
        
        r = redis.from_url(redis_url)
        await r.ping()
        await r.close()
        
        logger.info("Redis connectivity test successful")
        return True
        
    except Exception as e:
        logger.error("Redis connectivity test failed", error=str(e))
        return False


async def main():
    """Main test function."""
    logger.info("🧪 Starting API Connectivity Tests")
    logger.info("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    results = {}
    
    # Test LLM APIs
    logger.info("\n🤖 Testing LLM APIs")
    logger.info("-" * 30)
    results['anthropic'] = await test_anthropic_api()
    results['openai'] = await test_openai_api()
    
    # Test databases
    logger.info("\n🗄️ Testing Database Connectivity")
    logger.info("-" * 30)
    results['database'] = await test_database_connectivity()
    results['redis'] = await test_redis_connectivity()
    
    # Summary
    logger.info("\n📊 Test Results Summary")
    logger.info("=" * 30)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for service, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{service.upper()}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if results.get('anthropic') or results.get('openai'):
        logger.info("\n🚀 Ready for LLM-powered demos!")
        logger.info("   Run: python scripts/demo.py")
    else:
        logger.info("\n⚠️  No LLM APIs available - demos will use mock responses")
    
    return 0 if passed > 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
