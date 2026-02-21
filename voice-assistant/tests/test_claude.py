"""
Test Claude agent integration with a simple exchange.
"""
import sys
sys.path.insert(0, "/home/respeaker/voice-assistant")

from agent.claude_agent import ClaudeAgent

def test_single_turn():
    agent = ClaudeAgent()
    response = agent.chat("What is the capital of France?")
    assert "Paris" in response, f"Expected Paris in response, got: {response}"
    print(f"Response: {response}")
    print("Claude single-turn test PASSED")

def test_multi_turn_memory():
    agent = ClaudeAgent()
    agent.chat("My name is Alex.")
    response = agent.chat("What is my name?")
    assert "Alex" in response, f"Expected Alex in response, got: {response}"
    print(f"Memory test response: {response}")
    print("Claude multi-turn memory test PASSED")

if __name__ == "__main__":
    test_single_turn()
    test_multi_turn_memory()
