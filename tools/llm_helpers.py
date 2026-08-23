"""Shared helpers for talking to the LLM and reliably getting JSON back.

gpt-oss-120b on Groq is a reasoning model. Even with reasoning suppressed via
model_kwargs, Groq's own community forum documents cases where reasoning text
or stray preamble still leaks into the response content (see
community.groq.com/t/bug-gpt-oss-120b-reasoning-tokens...). So we do two
things: (1) ask the API to hide/minimize reasoning, and (2) never trust the
raw response to be pure JSON — always extract the outermost [...] or {...}
block before parsing, and never let a parse failure silently produce a blank
result the person can't diagnose.
"""
import os
import json
import re
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()


def make_llm(temperature: float = 0.2) -> ChatGroq:
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=temperature,
        model_kwargs={"reasoning_effort": "low", "include_reasoning": False},
    )


def extract_json(raw: str):
    """Pull the first well-formed JSON array or object out of a string that
    may have extra text, markdown fences, or leaked reasoning around it.
    Returns the parsed Python object, or None if nothing parseable is found.
    """
    if not raw:
        return None

    text = raw.strip()

    # strip markdown fences if present
    if text.startswith("```"):
        text = text.strip("`")
        text = text[4:] if text.lower().startswith("json") else text

    # fast path — the whole thing is already valid JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # slow path — find the first balanced [...] or {...} substring
    for open_ch, close_ch in (("[", "]"), ("{", "}")):
        start = text.find(open_ch)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == open_ch:
                depth += 1
            elif text[i] == close_ch:
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break  # try the other bracket type
    return None


def ask_llm_json(llm: ChatGroq, prompt: str, fallback=None):
    """Invoke the LLM and robustly parse JSON from its response.
    Returns `fallback` (default: None) if the response truly can't be parsed,
    instead of raising or silently producing a blank/malformed structure."""
    response = llm.invoke(prompt)
    result = extract_json(response.content)
    return result if result is not None else fallback
