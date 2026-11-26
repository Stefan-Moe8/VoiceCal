import pandas as pd
from config import MODEL, EMBED_MODEL, MODERATION_MODEL, TTS_MODEL, STT_MODEL

# USD per 1M tokens: (input, cached input, output), standard tier. Update these if you change a model above.
# Prices change, so check https://developers.openai.com/api/docs/pricing
PRICES = {
    MODEL: (0.10, 0.01, 0.50),
    EMBED_MODEL: (0.02, 0.02, 0.0),
    MODERATION_MODEL: (0.0, 0.0, 0.0),  # free
}
# USD per minute of audio. Speech to text is billed per minute. Text to speech is billed per token
# ($0.60 per 1M text tokens in, $12 per 1M audio tokens out), which comes to about $0.015 per minute of speech.
AUDIO_PRICES = {TTS_MODEL: 0.015, STT_MODEL: 0.0045}
USAGE_LOG = []  # one row per model call

def log_usage(label, model, seconds, input_tokens=0, output_tokens=0, cached_tokens=0, reasoning_tokens=0, audio_seconds=0.0):
    """Add one model call to USAGE_LOG (tokens, audio, latency, estimated cost) and return the row."""
    known = [*PRICES, *AUDIO_PRICES]
    # Match the longest known name, so dated snapshots work and one name can't shadow another that starts with it.
    matches = [p for p in known if model == p or model.startswith(p + "-")]
    name = max(matches, key=len) if matches else model
    if name not in known:
        print(f"Note: no price for {model!r}; add it to PRICES. Counting it as $0 for now.")
        PRICES[name] = (0.0, 0.0, 0.0)
    p_in, p_cached, p_out = PRICES.get(name, (0.0, 0.0, 0.0))
    cost = ((input_tokens - cached_tokens) * p_in + cached_tokens * p_cached + output_tokens * p_out) / 1e6
    cost += audio_seconds / 60 * AUDIO_PRICES.get(name, 0.0)
    row = {
        "label": label,
        "model": name,
        "input": input_tokens,
        "cached": cached_tokens,
        "output": output_tokens,
        "reasoning": reasoning_tokens,
        "audio_s": round(audio_seconds, 1),
        "seconds": round(seconds, 2),
        "cost_usd": cost,
    }
    USAGE_LOG.append(row)
    return row


def log_response(label, response, seconds):
    """Log a Responses API result: its usage has input, cached, output, and reasoning token counts."""
    u = response.usage
    cached = getattr(u.input_tokens_details, "cached_tokens", 0) or 0
    reasoning = getattr(u.output_tokens_details, "reasoning_tokens", 0) or 0
    return log_usage(label, response.model, seconds, u.input_tokens, u.output_tokens, cached, reasoning)


def usage_summary(rows=None):
    """Calls, tokens, audio seconds, summed latency, and cost per model, plus a total row."""
    df = pd.DataFrame(USAGE_LOG if rows is None else rows)
    if df.empty:
        return df
    summary = df.groupby("model").agg(
        calls=("label", "size"),
        input=("input", "sum"),
        cached=("cached", "sum"),
        output=("output", "sum"),
        reasoning=("reasoning", "sum"),
        audio_s=("audio_s", "sum"),
        seconds=("seconds", "sum"),
        cost_usd=("cost_usd", "sum"),
    )
    summary.loc["total"] = summary.sum()
    counts = ["calls", "input", "cached", "output", "reasoning"]
    return summary.astype({c: int for c in counts}).round({"audio_s": 1, "seconds": 1, "cost_usd": 5})
