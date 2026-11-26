import os

from dotenv import load_dotenv
from openai import OpenAI

# Loads variables from .env into the environment (must run before the client is created)
load_dotenv()

MODEL = "gpt-6-luna"  # every generation call: chat, tools, agents, guardrail checks, the judge, images
EMBED_MODEL = "text-embedding-3-small"  # turns text into vectors for retrieval
MODERATION_MODEL = "omni-moderation-latest"  # flags harmful text; free
TTS_MODEL = "gpt-4o-mini-tts"  # text to speech
STT_MODEL = "gpt-transcribe"  # speech to text
VOICE = "sage"  # one of the built-in text-to-speech voices

# Always set the reasoning effort: the model's default ("medium") is slow for simple tasks.
FAST_REASONING = {"effort": "none"}

client = OpenAI(
    timeout=60.0,
    max_retries=2,  # retries 429s, 5xx errors, and timeouts
    default_headers={"Accept-Encoding": "identity"},  # workaround: skip the broken decompressor
)  # reads OPENAI_API_KEY from the environment

voice_client = client.with_options(timeout=18.0, max_retries=1)  # a stalled request gives up after about 40 s