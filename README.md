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

1. **Submit.** The client sends `POST /submit` with a JSON object containing `text` and `creator_id`.

2. **Validate (`app.py::submit`).** The body must be a JSON object. The `text` must be a nonblank string of at most 20,000 characters. Invalid requests get a 4xx JSON error and a `rejected` audit entry. The model only runs on valid input.

3. **Model score (`detector.py::model_signal`).** Local GPT-2 checks the first 400 tokens for predictability. More predictable text gets a higher AI score, from 0 to 1.

4. **Style score (`stylometry.py::style_signal`).** Sentence lengths, vocabulary variety, and punctuation produce another score from 0 to 1. Higher means more AI-like. This check does not consider meaning.

5. **Combine (`scoring.py::combine_signals`).** The two scores become one score: 0 means human-like and 1 means AI-like. Strong disagreement moves the score toward 0.5.

6. **Label (`scoring.py::score_to_label`).** The final score becomes one of three labels: `human`, `unsure`, or `AI`.

7. **Save and respond.** The system creates a `content_id` and saves both scores, the final score, the label, and status `decided` in `logs/audit.jsonl`. It returns the label. Writers can send `POST /appeal` with their `content_id` and reasoning to record an appeal and change the status to `under_review`.

## Example: a wrong AI label

A student submits their own writing using short, simple sentences. The model gives it 0.68, and the style check gives it 0.79. The combined score is 0.73, so it receives a high-confidence AI label.

*The label explains that the result may be wrong and offers an appeal. The student appeals, their reasoning is saved, and the status changes to `under_review` for a person to review.
---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — model score

**What it measures:** GPT-2 checks how predictable the text is using perplexity. Lower perplexity gives a higher AI-like score from 0 to 1. The midpoint perplexity is 45.

**Where:** `detector.py::model_signal`

**Why it may help:** AI often chooses likely words, making its writing predictable. Human writing can have unexpected words and changes.

**Limits:** Predictability cannot prove authorship. Simple human writing can also score as AI-like. My plain-writing samples scored 0.68–0.91. The model checks only the first 400 tokens.

### Signal two — style score

**What it measures:** Three features produce a score from 0 to 1. Higher means more AI-like.

| Feature | What it checks | Weight |
|---|---|---|
| `sentence_length_spread` | Sentence-length variation: standard deviation divided by average length | 0.45 |
| `type_token_ratio` | Unique words divided by total words, using up to the first 100 words | 0.25 |
| `punctuation_density` | Weighted punctuation per word; some marks count more than commas, and periods are ignored | 0.30 |

**Where:** `stylometry.py::style_signal`

**Why it may help:** AI writing may have more even sentence lengths and less varied punctuation. In my samples, sentence-length spread was 0.09–0.19 for AI and 0.51–0.81 for casual human writing.

**Limits:** It cannot understand meaning or prove authorship. Changing sentence breaks or punctuation can change the score without changing the message. One lightly edited AI paragraph scored 0.23, making it look human-like.

### The combining rule

**Rule:** Combine both scores, giving the model more weight because style is easier to manipulate. If the scores differ by more than 0.35, move the result halfway toward 0.5 to show uncertainty. Keep the final score between 0 and 1.

**Calculation:**

    combined = 0.6 * model_score + 0.4 * style_score

    if abs(model_score - style_score) > 0.35:
        combined = 0.5 + (combined - 0.5) * 0.5

**Where:** `scoring.py::combine_signals`

**Settings:** `config.py` contains `WEIGHT_MODEL_SIGNAL`, `WEIGHT_STYLE_SIGNAL`, `DISAGREEMENT_GAP`, and `DISAGREEMENT_SHRINK`.

**Example:** A formal human passage scored 0.49 for the model and 0.00 for style. The gap was 0.49, so the rule moved the combined score from 0.292 to 0.396. This produced `unsure`.

**Tradeoff:** Disagreement shows uncertainty, but some human writers receive `unsure` instead of `human`.

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**When the signals disagree:** A formal human passage scored 0.49 from the model and 0.00 from the style check. The gap of 0.49 triggered the rule, moving the combined score from 0.292 toward 0.5, resulting in 0.396 and the label `unsure`.

*This shows uncertainty when the signals disagree, but it can leave real human writers labeled `unsure`.
---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | What the reader sees |
|---|---|---|
| high-confidence human | 0.00–0.35 | This was probably written by a person, but no check is perfect. |
| unsure | Above 0.35 and below 0.65 | We can't tell whether a person or AI wrote this. Many people write this way. You don't need to do anything, but you can ask for a review anytime. |
| high-confidence AI | 0.65–1.00 | This may be AI-written. We can be wrong, especially with simple writing. If you wrote it yourself, please appeal for a human review. |

Every score maps to exactly one label, checked in steps of 0.01. A score of 0.51 gets `unsure`, and 0.95 gets `high-confidence AI`. Real test submissions produced all three labels.

**Why the `unsure` message uses this wording:** It makes clear that the tool is uncertain. It reassures writers without accusing them or requiring action.

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

*The original decision line stays as it was and the appeal is appended after it; the log is append-only.

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
