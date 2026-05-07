import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from jegal.research_agents import GenericResearchAgent

@pytest.fixture
def mock_anthropic():
    with patch('jegal.research_agents.Anthropic') as mock:
        yield mock

@pytest.fixture
def mock_openai():
    with patch('jegal.research_agents.OpenAI') as mock:
        yield mock

@pytest.mark.asyncio
async def test_bullish_scenario(mock_anthropic):
    """
    Simulates a bullish earnings review and asserts a 'BUY' decision.
    """
    # Setup mock response
    mock_client = mock_anthropic.return_value
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="The earnings report was outstanding. Revenue grew 50% YoY. BUY.")]
    mock_client.messages.create.return_value = mock_response

    agent = GenericResearchAgent(provider="anthropic", model="claude-3-opus-20240229")
    result = await agent.execute_task(
        system_prompt="Analyze earnings", 
        user_prompt="Review transcript for AAPL", 
        symbols=["AAPL"]
    )

    assert result["action"] == "BUY"
    assert "AAPL" in result["symbols"]
    assert "outstanding" in result["research_summary"]

@pytest.mark.asyncio
async def test_bearish_scenario(mock_openai):
    """
    Simulates a bearish market news report and asserts a 'SELL' decision.
    """
    # Setup mock response
    mock_client = mock_openai.return_value
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Market conditions are deteriorating. SELL all positions."))]
    mock_client.chat.completions.create.return_value = mock_response

    agent = GenericResearchAgent(provider="openai", model="gpt-4")
    result = await agent.execute_task(
        system_prompt="Analyze news", 
        user_prompt="Review market news", 
        symbols=["BTC-USD"]
    )

    assert result["action"] == "SELL"
    assert "BTC-USD" in result["symbols"]
    assert "deteriorating" in result["research_summary"]

def test_result_to_dataframe_conversion():
    """
    Verifies that agent results can be correctly formatted into a signal DataFrame.
    """
    results = [
        {"action": "BUY", "symbols": ["AAPL"], "research_summary": "Good stuff"},
        {"action": "SELL", "symbols": ["TSLA"], "research_summary": "Bad stuff"},
        {"action": "HOLD", "symbols": ["MSFT"], "research_summary": "Neutral stuff"}
    ]
    
    # Simulating the logic in jegal/engine_bridge.py
    df = pd.DataFrame(results)
    signal_map = {"BUY": 1.0, "SELL": -1.0, "HOLD": 0.0}
    df['signal'] = df['action'].map(signal_map).fillna(0.0)
    
    assert df.iloc[0]['signal'] == 1.0
    assert df.iloc[1]['signal'] == -1.0
    assert df.iloc[2]['signal'] == 0.0
    assert df.iloc[0]['symbols'] == ["AAPL"]
