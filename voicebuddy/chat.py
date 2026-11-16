"""Chat: answer sentences that are not a command with a language model (optional)."""

import os
import sys

import anthropic
from dotenv import load_dotenv

# Read the .env file, so the key in it becomes an environment variable.
load_dotenv()

MODEL = "claude-haiku-5-5"  # the fast and cheap Claude model: good for spoken answers
MAX_HISTORY = 10  # remember this many messages (5 questions and their answers)
SYSTEM_PROMPT = (
    "Sen VoiceBuddy adlı sesli bir asistansın. Cevabın sesli okunacak. "
    "Türkçe, konuşma diliyle ve en fazla iki cümleyle cevap ver. "
    "Liste, başlık, emoji ya da özel işaret kullanma."
)

# The conversation so far: {"role": "user" or "assistant", "content": text}.
history = []


def ask_llm(text):
    """Send the sentence to the language model and return its answer as text."""
    # Without a key the feature is off and the assistant answers as before.
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return "Bunu anlamadım."

    history.append({"role": "user", "content": text})
    # timeout: give up after 20 seconds instead of freezing the assistant.
    client = anthropic.Anthropic(timeout=20.0)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            # A spoken answer must come fast, so the model does not think first.
            thinking={"type": "disabled"},
            output_config={"effort": "low"},
            # The whole history is sent each time: the model itself remembers nothing.
            messages=history,
        )
    except anthropic.APIConnectionError:
        # No internet. Forget the question, so the history stays question-answer pairs.
        history.pop()
        return "İnternete ulaşamadım."
    except anthropic.APIStatusError as error:
        # The server said no, for example the key is wrong (401) or the limit is reached (429).
        history.pop()
        print(f"Chat error: {error.status_code}")
        return "Şu an cevap veremiyorum."

    # The answer arrives as a list of blocks; the text blocks hold the words.
    answer = ""
    for block in response.content:
        if block.type == "text":
            answer += block.text
    answer = answer.strip()

    if answer == "":
        # The model declined to answer, so there is no text.
        history.pop()
        return "Buna cevap veremiyorum."

    history.append({"role": "assistant", "content": answer})
    # Keep only the newest messages. The number is even, so the first is always a question.
    del history[:-MAX_HISTORY]
    return answer


if __name__ == "__main__":
    # Manual test: python -m voicebuddy.chat "Türkiye'nin başkenti neresi?"
    print(ask_llm(sys.argv[1]))
