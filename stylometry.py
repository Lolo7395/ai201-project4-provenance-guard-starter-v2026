"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies. Higher means more human.

    Returns the coefficient of variation of sentence length in words: standard
    deviation divided by the mean, so a long text and a short one compare. Even,
    mid-length sentences give roughly 0.1–0.3; lumpy human prose gives 0.6+.

    One sentence has no spread to measure, so it returns 0.0 — "no evidence of
    variety", which style_signal then treats as a weak machine-ish vote.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    return round(statistics.stdev(lengths) / mean, 4)


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words, 0–1. Higher means more varied vocabulary.

    Measured over the first 100 words only. Raw TTR falls as text gets longer,
    so without the cap a long human text would look repetitive next to a short
    one and length alone would move the score.
    """
    ws = words(text)[:100]
    if not ws:
        return 0.0
    return round(len(set(ws)) / len(ws), 4)


# Marks weighted by how much writers differ in using them. Full stops are
# left out: nearly everyone uses them at the rate their sentences dictate.
_PUNCT_WEIGHTS = {
    ",": 1.0, ";": 3.0, ":": 2.0, "—": 3.0, "–": 2.0, "-": 0.5,
    "(": 2.0, ")": 0.0, "!": 2.0, "?": 2.0, '"': 0.5, "…": 2.0,
}


def punctuation_density(text: str) -> float:
    """
    Weighted punctuation marks per word. Higher means more human.

    Commas count 1, semicolons and dashes more, because they vary more between
    writers than commas do. A typical value is 0.05–0.15 for flat prose and
    0.2+ for chatty or heavily punctuated writing.
    """
    n_words = len(words(text))
    if n_words == 0:
        return 0.0
    total = sum(_PUNCT_WEIGHTS.get(ch, 0.0) for ch in text)
    return round(total / n_words, 4)


# ── Combining them ───────────────────────────────────────────────────────────

def _scale(value: float, low: float, high: float) -> float:
    """Map value onto 0–1, clamped: `low` -> 0.0, `high` -> 1.0."""
    return min(max((value - low) / (high - low), 0.0), 1.0)


def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.**

    All three raw measures run "higher = more human", so each is scaled to 0–1
    over the range I saw on my calibration texts and then flipped (1 - x):

        spread      0.15 (even, AI-ish) .. 0.70 (lumpy, human)   weight 0.45
        TTR         0.55 (repetitive)   .. 0.85 (varied)         weight 0.25
        punctuation 0.05 (flat)         .. 0.25 (varied)         weight 0.30

    Spread gets the most weight because it is the property the brief calls out
    and the least affected by text length. TTR gets the least because it is the
    easiest to move with typos or a pasted quotation.
    """
    human = (
        0.45 * _scale(sentence_length_spread(text), 0.15, 0.70)
        + 0.25 * _scale(type_token_ratio(text), 0.55, 0.85)
        + 0.30 * _scale(punctuation_density(text), 0.05, 0.25)
    )
    return round(1.0 - human, 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
