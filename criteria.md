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

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. False positives: plain human writing is rarely called AI

Of 10 plain, ordinary paragraphs that I wrote myself (about 60–120 words each, no
fancy vocabulary), at most 1 is labelled high-confidence AI (combined score above
0.65). The target must hold in each of three repeated runs.

**Why this target:** On a writing site a wrong accusation costs the writer far
more than a missed AI text costs the site, and plain writers are exactly who a
predictability-based detector is most likely to accuse. 1 in 10 is the most I
will tolerate, and I am deliberately testing plain prose rather than easy ornate prose.

---

## 2. Score spread: clearly-AI and clearly-human text separate

Over 5 clearly-AI paragraphs and 5 clearly-human paragraphs (casual, lumpy,
specific), the mean combined score of the AI set is at least 0.30 higher than the
mean of the human set, and the lowest AI score is still above the highest human score.

**Why this target:** If the two groups sit within 0.30 of each other, the score is
not telling me anything and the labels are noise. Requiring no overlap on the
extreme examples keeps me from hiding behind averages.

---

## 3. Label coverage: all three labels reachable, no gaps, confidence matters

Sweeping the combined score from 0.00 to 1.00 in steps of 0.01, `score_to_label`
returns one of exactly three labels for all 101 values (0 gaps), and each label is
produced at least once. Scores 0.51 and 0.95 return different labels. Also, real
submissions across my test set produce all three labels at least once.

**Why this target:** A label that no score can produce is dead text, and a flip at
exactly 0.5 would call 0.51 and 0.95 the same kind of certain. Real submissions
have to reach each label, not just the sweep, since the style signal can limit the
reachable range of the combined score.

---

## 4. Appeal path: every appeal changes status and is recorded

For 5 appeals on valid `content_id`s, 5 of 5 return HTTP 200 with status
`under_review`, and 5 of 5 add an `appeal` entry (with the reasoning text) to
`logs/audit.jsonl` while the original decision entry stays untouched. An appeal for
an unknown `content_id` returns 404 and writes nothing, and an appeal with empty
reasoning returns 400.

**Why this target:** The appeal is the only thing between a wrong accusation and
nothing at all, so it must work every time, not most of the time. Failures have to
be loud (404/400) so a typo does not silently look like a recorded appeal.

---

## 5. Bad input: malformed requests never crash the service

Six bad submissions (missing `text`, empty `text`, whitespace-only `text`, `text`
that is not a string, `text` over 20,000 characters, and a body that is not JSON)
each get a 4xx JSON error with a plain message, 0 of 6 return a 500, and each is
recorded in the audit log as a rejection.

**Why this target:** A crash on malformed input is one of the most common real
failures, and a rejection with no log entry is an attack I would never see.
Zero 500s is the only defensible number here because every one of these cases can
be checked before the model runs.

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
