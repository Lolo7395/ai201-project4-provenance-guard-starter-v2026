# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick targets you can explain

Choose at least **three of the five areas** below.

- Wrongly accusing a human writer is more harmful than missing AI text.
- Each target must pass in **all three trials**. For example, a limit of 1 mistake fails if the results are 2, 1, and 2.

## 1. False positives

**Target:** Test 10 simple paragraphs I wrote myself, each 60–120 words long. In each trial, no more than 1 paragraph should be labeled high-confidence AI (combined score above 0.65).

**Why:** Human writers should rarely receive a wrong accusation. Simple writing is especially important to test because predictable wording may trigger the detector.

## 2. Score spread

**Target:** Test 5 clearly-AI paragraphs and 5 clearly-human paragraphs.

- The average AI score must be at least 0.30 higher than the average human score.
- The lowest AI score must be higher than the highest human score.

**Why:** The scores should clearly separate these examples. Checking both averages and individual scores prevents averages from hiding overlap.

## 3. Label coverage

**Target:** Test `score_to_label` from 0.00 to 1.00 in steps of 0.01.

- All 101 scores must return one of exactly three labels.
- Every label must appear at least once.
- Scores of 0.51 and 0.95 must return different labels.
- Actual test submissions must also produce all three labels.

**Why:** Every label should be reachable, and the labels should reflect different confidence levels.

## 4. Appeal path

**Target:** Submit 5 appeals using valid `content_id`s.

- All 5 return HTTP 200 with status `under_review`.
- All 5 add an `appeal` entry containing the reasoning to `logs/audit.jsonl`.
- Original decision entries stay unchanged.
- An unknown `content_id` returns 404 and adds no log entry.
- Empty reasoning returns 400.

**Why:** Writers need a reliable way to challenge a decision. Failed appeals must return clear errors.

## 5. Bad input

**Target:** Test these 6 invalid submissions:

1. Missing `text`.
2. Empty `text`.
3. Whitespace-only `text`.
4. `text` that is not a string.
5. `text` longer than 20,000 characters.
6. A request body that is not JSON.

Every submission must return a 4xx JSON error with a clear message and be logged as a rejection. None may return a 500 error.

**Why:** Invalid input should be caught before the model runs. Logging rejections helps identify problems and possible attacks.
---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
