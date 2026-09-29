# Archived pilot experiment

This experiment used food offsets divided by sensor range, rather than unit food
directions. It trained 28 policies for 20 generations on three layouts per run, using
training seeds 11, 22 and 33 and 12 test layouts beginning at 900000.

Evolved policies improved over initial neural policies, but underperformed the random
walk and greedy references. This exposed weak near-food signals and motivated the
direction encoding used in the final benchmark. The final experiment also doubled
the number of training layouts, so this is **not a controlled single-variable ablation**.
Final evaluation used a fresh test set beginning at 1900000.

The pilot files remain as a development record. To reproduce the original semantics,
use the code at commit `7c39728` in a separate checkout. Do not load these pilot brains
into the current application and expect the original scores: their sensor encoding differs.
