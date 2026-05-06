import pytest
import pytest_asyncio
from jegal.research_agents import GenericResearchAgent
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_research_agent_ollama_initialization():
    """Verifies that the agent initializes correctly with the Ollama provider."""
    agent = GenericResearchAgent(provider="ollama", model="llama3")
    assert agent.provider == "ollama"
    assert agent.model == "llama3"

@pytest.mark.asyncio
async def test_research_agent_config_loading():
    """Verifies that the agent loads default stocks from config.json."""
    agent = GenericResearchAgent(provider="ollama", model="llama3")
    # config.json contains ["BTC-USD", "AAPL", "TSLA"]
    assert "AAPL" in agent.stocks
    assert "BTC-USD" in agent.stocks

@pytest.mark.asyncio
async def test_research_agent_ollama_execute():
    """Tests the Ollama execution flow with multiple symbols."""
    # Mock the ollama.chat method
    with patch("ollama.chat") as mock_chat:
        mock_chat.return_value = type('obj', (object,), {'message': type('obj', (object,), {'content': 'BUY'})})
        
        agent = GenericResearchAgent(provider="ollama", model="llama3")
        # Test defaulting to config symbols
        result = await agent.execute_task("System", "User")
        
        assert result['action'] == 'BUY'
        assert result['symbols'] == agent.stocks
        mock_chat.assert_called_once()
