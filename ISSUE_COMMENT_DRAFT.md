# Comment for issue #4509 — SENT on 2026-11-21

Posted at https://github.com/EleutherAI/lm-evaluation-harness/issues/4509#issuecomment-7067386356. The text below is the draft; the posted version adds a table.

---

I counted real exposure on `cais/mmlu` at d6de8164 (census only, no model runs).

- `mmlu_flan_n_shot_generative` (test, 14,042 questions): 82 questions have choices that collide after normalisation; in 51 the gold answer is inside the colliding group (26 where a correct literal answer is scored wrong, 25 where a wrong literal answer is scored right).
- `mmlu_flan_cot_zeroshot` (validation, 1,531): 8 colliding, 7 with gold inside.
- Upper bound on aggregate accuracy: 0.36 points (test). Per subject it exceeds 1 point in 11 of 57 subjects, highest in `high_school_mathematics` (10 of 270, 3.7 %).
- 26 of the 51 are numbers that differ only by a minus sign or a decimal point.
- These are ceilings: they are reached only when the model answers with the choice text instead of the letter. I have not measured how often that happens.

Two side observations from the negative control, not checked against existing issues:

- choices that normalise to an empty string (`/`, `//`) are never matched;
- choices whose normalised text has leading or trailing whitespace (`. . . asthma.`) are matched and then lost by the `.strip()` before the dictionary lookup.

The list of affected (subject, split, row) with choices and gold is in `results/affected_questions.csv` in this repository, usable as regression cases.
