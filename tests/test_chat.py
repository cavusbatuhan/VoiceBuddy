"""Tests for the chat. No request leaves the computer: the Anthropic client is replaced by a fake."""

import anthropic
import httpx2
import pytest

from voicebuddy import chat


class FakeBlock:
    """One piece of a fake model answer."""

    def __init__(self, block_type, text):
        self.type = block_type
        self.text = text


class FakeResponse:
    """A fake model answer made of blocks."""

    def __init__(self, blocks):
        self.content = blocks


class FakeClient:
    """Stands in for anthropic.Anthropic and remembers what it was asked."""

    answer = "Ankara."
    requests = []

    def __init__(self, timeout):
        # The real client is used as client.messages.create(...).
        self.messages = self

    def create(self, **request):
        # Copy the messages: the real list keeps changing after the call.
        FakeClient.requests.append(list(request["messages"]))
        return FakeResponse([FakeBlock("text", FakeClient.answer)])


@pytest.fixture(autouse=True)
def fresh_chat(monkeypatch):
    # Every test starts with a key, an empty history and the fake client.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(anthropic, "Anthropic", FakeClient)
    chat.history.clear()
    FakeClient.answer = "Ankara."
    FakeClient.requests = []


def test_without_a_key_the_chat_is_off(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert chat.ask_llm("Türkiye'nin başkenti neresi?") == "Bunu anlamadım."
    assert FakeClient.requests == []


def test_answer_is_returned_and_remembered():
    assert chat.ask_llm("Türkiye'nin başkenti neresi?") == "Ankara."
    assert chat.history == [
        {"role": "user", "content": "Türkiye'nin başkenti neresi?"},
        {"role": "assistant", "content": "Ankara."},
    ]


def test_second_question_is_sent_with_the_first():
    chat.ask_llm("Türkiye'nin başkenti neresi?")
    chat.ask_llm("Nüfusu kaç?")
    # The second request holds the first question, its answer and the new question.
    assert len(FakeClient.requests[1]) == 3
    assert FakeClient.requests[1][0]["content"] == "Türkiye'nin başkenti neresi?"


def test_history_keeps_only_the_newest_messages():
    for number in range(8):
        chat.ask_llm(f"Soru {number}")
    assert len(chat.history) == chat.MAX_HISTORY
    assert chat.history[0] == {"role": "user", "content": "Soru 3"}


def test_no_internet_gives_a_clear_answer(monkeypatch):
    def fail(self, **request):
        raise anthropic.APIConnectionError(request=httpx2.Request("POST", "https://example.invalid"))

    monkeypatch.setattr(FakeClient, "create", fail)
    assert chat.ask_llm("Merhaba") == "İnternete ulaşamadım."
    # The failed question is forgotten.
    assert chat.history == []


def test_empty_answer_is_not_remembered():
    FakeClient.answer = ""
    assert chat.ask_llm("Merhaba") == "Buna cevap veremiyorum."
    assert chat.history == []
