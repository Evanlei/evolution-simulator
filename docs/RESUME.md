# Résumé entry

**Neuroevolution Ecosystem Simulator | Python, Pygame, Neural Networks, Evolutionary Algorithms**

- Developed an interactive ecosystem simulator supporting up to 180 neural-controlled
  agents, with resource competition, energy-based reproduction, heritable genomes,
  ancestry tracking, and spatially indexed food sensing.
- Implemented an 8–10–2 feed-forward neural network from scratch and evolutionary
  optimization with elitism, tournament selection, and Gaussian mutation; achieved
  7.04× higher held-out food consumption than the best initial policies across three
  training runs and 20 shared test layouts.
- Built a live neural inspector, population dashboard, deterministic checkpoint/replay,
  CSV telemetry, and automated simulation/UI tests to support reproducible experiments.

## What the numerical claim means

36.9833 mean meals divided by 5.25 mean meals = 7.0444. The comparator is the best
initial policy from each training run, chosen on training data—not the greedy reference.
Evaluation used 25-second, single-agent episodes with reproduction disabled. The
greedy controller still scored higher (46.15). These measurements are in
`results/benchmark/report.json` and `results/benchmark/episodes.csv`.

Use the experiment details when asked, and distinguish offline fitness-based training
from natural reproduction in the visual ecosystem. The project was developed with AI
assistance; the architectural walkthrough is intended to make each component reviewable.
