"""
Anthropic Claude agent with persistent conversation history.

Maintains a rolling window of conversation turns so Claude has
context across multiple exchanges in the same session.

The messages list format expected by Claude:
  [
    {"role": "user",      "content": "..."},
    {"role": "assistant", "content": "..."},
    {"role": "user",      "content": "..."},
    ...
  ]
Messages MUST alternate user/assistant. The list MUST start with a user turn.
"""
import anthropic
from config.settings import settings


class ClaudeAgent:
    def __init__(self):
        cfg = settings.agent
        self.client = anthropic.Anthropic(api_key=cfg.ANTHROPIC_API_KEY)
        self.model = cfg.MODEL
        self.max_tokens = cfg.MAX_TOKENS
        self.system_prompt = cfg.SYSTEM_PROMPT
        self.max_history_turns = cfg.MAX_HISTORY_TURNS

        # Conversation history: list of {"role": ..., "content": ...}
        self._history: list[dict] = []

    def chat(self, user_text: str) -> str:
        """
        Send a user message to Claude, get a response, and update history.

        Args:
            user_text: The transcribed user speech

        Returns:
            Claude's text response (plain text, suitable for TTS)
        """
        self._history.append({"role": "user", "content": user_text})

        # Trim history to stay within max turns (each turn = 1 user + 1 assistant)
        # Keep at most max_history_turns*2 messages
        max_messages = self.max_history_turns * 2
        if len(self._history) > max_messages:
            # Always keep from index 0 as a user turn (API requirement)
            self._history = self._history[-max_messages:]

        print(f"[Agent] Sending to Claude ({self.model}), "
              f"history={len(self._history)} messages...")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=self._history,
        )

        # Extract text from the response
        response_text = message.content[0].text
        print(f"[Agent] Response: {response_text[:80]}{'...' if len(response_text) > 80 else ''}")

        # Add Claude's response to history so next turn has context
        self._history.append({"role": "assistant", "content": response_text})

        return response_text

    def reset_history(self) -> None:
        """Clear conversation history to start a fresh session."""
        self._history = []
        print("[Agent] Conversation history cleared.")

    @property
    def turn_count(self) -> int:
        """Returns the number of complete user/assistant turn pairs."""
        return len(self._history) // 2
