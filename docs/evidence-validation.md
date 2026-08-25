# The evidence rule

The model never produces an accepted fact directly. For every populated scalar,
contact, or facility proposal, Python applies this sequence:

1. Require one or more non-empty evidence quotes.
2. Find each quote exactly in the normalized source text.
3. Compute `start` and `end` in Python; model-provided offsets are not accepted.
4. Require the proposed name, value, or contact detail to occur inside the cited
   evidence, ignoring letter case only.
5. Apply a narrow relationship check for `self`, family relationships, and
   referring-attorney contacts.
6. Replace unsupported scalar values with `NOT FOUND`; discard unsupported
   collection items; record a validation issue.
7. Walk the complete validated result again and verify
   `source_text[start:end] == quote` for every evidence object.

This proves that accepted values are attached to exact source text. It does not
prove legal meaning, negligence, credibility, or ultimate semantic entailment.
Those decisions remain with a human reviewer.
