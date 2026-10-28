# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

1. **Arrival.** A client sends `POST /submit` with JSON `{"text", "creator_id"}`.
2. **Validation (`app.py::submit`).** The body must be a JSON object, and `text` must be present, a string, not blank, and at most 20,000 characters. Anything else gets a 4xx JSON error and a `rejected` line in the audit log. The model never runs on bad input.
3. **Signal one (`detector.py::model_signal`).** GPT-2 runs locally on the first 400 tokens and measures how predictable the text is. Predictable text gets a high (AI-ish) score from 0 to 1.
4. **Signal two (`stylometry.py::style_signal`).** My own measures of sentence-length spread, vocabulary variety and punctuation give a second 0–1 score, same direction (higher = more AI-ish). It never looks at meaning.
5. **Combining (`scoring.py::combine_signals`).** The two scores become one confidence from 0 (human) to 1 (AI). If the signals disagree sharply, the score is pulled toward 0.5.
6. **Label (`scoring.py::score_to_label`).** The confidence maps to one of three plain-English labels: human, unsure, or AI.
7. **Log and answer.** A new `content_id` is created, the full decision (both signals, combined score, label, status `decided`) is appended to `logs/audit.jsonl`, and the response carries the label. If the writer disagrees, `POST /appeal` with that `content_id` and their reasoning records the appeal and moves the item to `under_review`.

**The false-positive path.** A student who writes in short, simple sentences (for example because English is their second language) submits an honest paragraph. GPT-2 finds it predictable (0.68) and my style signal finds even sentence lengths and little punctuation (0.79), so the combined score is 0.73 and they see the high-confidence AI label. That label tells them it can be wrong and to appeal; the appeal records their reasoning, sets the item to `under_review`, and a person looks. The sample run below is exactly this case.

---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** Perplexity under GPT-2: how surprised a language model is by the text, squashed to 0–1 (`detector.py::model_signal`, midpoint perplexity 45). Low perplexity means high score.

**Why that might differ between human and AI writing:** A model writes by picking likely next words, so its output is easy for another model to predict. Human writing has odd word choices and abrupt turns.

**What it can't see:** Authorship. It rewards common words in short, ordinary sentences, so plain human writers (second-language writers, younger writers) score as machine-like. My plain-writing samples scored 0.68–0.91. It also reads only the first 400 tokens.

### Signal two — the style signal

**What it measures:** Three things, in `stylometry.py`, scaled and weighted into one 0–1 score (`style_signal`, higher = more AI-ish):
- `sentence_length_spread` (weight 0.45): standard deviation of sentence length divided by the mean.
- `type_token_ratio` (weight 0.25): unique words over words, on the first 100 words only so length doesn't move it.
- `punctuation_density` (weight 0.30): weighted punctuation per word, with semicolons, dashes, colons, brackets, `!` and `?` counting more than commas. Full stops are ignored.

**Why that might differ between human and AI writing:** AI prose tends toward even, mid-length sentences and flat punctuation. Human prose is lumpier. On my samples, AI spread was 0.09–0.19 and casual human spread was 0.51–0.81.

**What it can't see:** Meaning. It can't tell that a short-sentence paragraph is honest, and it is easy to move on purpose: breaking up sentences, adding dashes or exclamation marks, or pasting a quotation shifts the shape without changing the substance. A lightly edited AI paragraph in my tests scored 0.23, which reads as human.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** A weighted average, leaning on the model signal because the style signal is easier to fool. If the two signals differ by more than 0.35, the result is pulled halfway back toward 0.5, so a real split reads as "unsure" and not as whichever signal carried the bigger weight. The result is clamped to 0–1.

**The numbers:** `combined = 0.6 * model_score + 0.4 * style_score`. If `abs(model_score - style_score) > 0.35` then `combined = 0.5 + (combined - 0.5) * 0.5`. All values live in `config.py` (`WEIGHT_MODEL_SIGNAL`, `WEIGHT_STYLE_SIGNAL`, `DISAGREEMENT_GAP`, `DISAGREEMENT_SHRINK`).

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:** An ornate human passage (semicolons, an em dash, rare words) scored model 0.49 but style 0.00: GPT-2 was unsure while the style signal said "very human". The gap is 0.49, so the rule fires: the weighted average 0.292 is pulled halfway toward 0.5, giving 0.396, which lands in "unsure" and not in "human". Two methods disagreeing is uncertainty, so I let the label say so. The cost is that confident-human formal writers get "unsure" and not a clean pass.

---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.35 (score at or below 0.35) | We think this was probably written by a person. Nothing about it looks like machine writing, though no check is perfect. |
| unsure | above 0.35 and below 0.65 | We can't tell whether this was written by a person or by an AI tool. Plenty of people write this way, so this is not a judgment about you or your work. If you wrote it yourself, you don't need to do anything, and you can ask for a review at any time. |
| high-confidence AI | 0.65 – 1.00 (score at or above 0.65) | This looks like it may have been written by an AI tool. We can be wrong, especially with plain or simple writing. If you wrote it yourself, please appeal and a person will take a look. |

Every score from 0.00 to 1.00 maps to exactly one label (checked in 0.01 steps). 0.51 gets "unsure" and 0.95 gets "AI", and all three labels were produced by real submissions in my test set.

**Why I worded the "unsure" one this way:**
It says "we can't tell" instead of "maybe AI", says outright that plenty of people write this way, and tells the reader they don't have to do anything. A writer who wrote every word themselves should read it as "the tool is unsure", not "you are suspected".

---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "I think the school should start later in the morning. Many students are tired when they get to class and cannot pay attention. If school started at nine, students could sleep more and get better grades. Some people say it would be hard for parents who work. But I think the school should still try it for one year.", "creator_id": "writer_042"}'
```

```json
{
    "confidence": 0.7272,
    "content_id": "fb1b058828e3",
    "guess": "ai",
    "label": "This looks like it may have been written by an AI tool. We can be wrong, especially with plain or simple writing. If you wrote it yourself, please appeal and a person will take a look.",
    "model_score": 0.6824,
    "status": "decided",
    "style_score": 0.7945
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "fb1b058828e3", "reasoning": "I wrote this myself for my school newspaper. I use short, simple sentences because English is my second language."}'
```

```json
{
  "content_id": "fb1b058828e3",
  "message": "Thanks. Your appeal is recorded and this piece is now under review by a person. Until then, please treat the original label as unconfirmed.",
  "status": "under_review"
}
```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=2"
```

```json
[
  {
    "timestamp": "2026-10-28T21:48:02+00:00",
    "content_id": "fb1b058828e3",
    "creator_id": "writer_042",
    "guess": "ai",
    "model_score": 0.6824,
    "style_score": 0.7945,
    "combined_score": 0.7272,
    "label": "This looks like it may have been written by an AI tool. We can be wrong, especially with plain or simple writing. If you wrote it yourself, please appeal and a person will take a look.",
    "status": "decided",
    "text_length": 314
  },
  {
    "timestamp": "2026-10-28T21:48:02+00:00",
    "content_id": "fb1b058828e3",
    "creator_id": "writer_042",
    "event": "appeal",
    "status": "under_review",
    "reasoning": "I wrote this myself for my school newspaper. I use short, simple sentences because English is my second language."
  }
]
```

The original decision line stays as it was and the appeal is appended after it; the log is append-only.

---

## How I Used AI

**Moment 1 — the style signal**

- *What I asked for:* Build `stylometry.py`: sentence-length spread, type-token ratio and punctuation density, all combined into one 0–1 score where higher means more AI.
- *What came back:* Three measures with each scaled onto 0–1 and flipped to point the same way as signal one. The first draft used raw type-token ratio over the whole text.
- *What I changed:* Raw TTR falls as text gets longer, so I capped it to the first 100 words. I also kept the weights (0.45 / 0.25 / 0.30) tied to ranges I observed on my calibration texts, and I put the blind spots (typos, broken sentences, quotations) in the README instead of claiming the signal was robust.

**Moment 2 — the combining rule and the failed criterion**

- *What I asked for:* A combining rule in `scoring.py::combine_signals` that does something sensible when the signals disagree, and three labels written for someone who has never heard of a threshold.
- *What came back:* A weighted average plus a "pull toward 0.5 when the signals split" rule, and three labels. My calibration run showed plain human paragraphs scoring 0.73–0.88, in the AI band.
- *What I changed:* I changed the weights to 0.6 / 0.4 because the style signal is easier to fool, and I reworded the AI label to say it can be wrong on plain writing and point to the appeal. I did not loosen criterion 1 to make it pass. It fails on my plain samples (4 of 4 flagged), as a known miss, and fixing it is the next unit's job.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

## My Test Results Against criteria.md

Run against the live service on 2026-10-28, one trial (the three-trial runs belong to the next unit).

| # | Target | Result |
|---|---|---|
| 1 | At most 1 of 10 plain human paragraphs flagged AI | **Missed.** 4 of 4 plain paragraphs were labelled high-confidence AI (0.74–0.88). I only tested 4, not 10, and they were written for the test, not by me. |
| 2 | AI mean at least 0.30 above human mean, no overlap | **Met.** AI 0.78–0.86, human 0.09–0.39. |
| 3 | 101 sweep values, 0 gaps, 0.51 ≠ 0.95, all labels reached live | **Met.** |
| 4 | 5/5 appeals recorded, unknown id 404, empty reasoning 400 | **Met.** |
| 5 | 6 bad inputs, 0 server errors, all logged | **Met.** Statuses 400, 400, 400, 400, 413, 400. |

Also noted: a lightly edited AI paragraph scored 0.24 and got the "human" label, so the style signal is easy to fool.
