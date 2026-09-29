# How the simulator works

## One physics step

`World.step()` shuffles the living creatures in seeded order. Each creature senses the
nearest food within 250 pixels, runs its brain, moves, and pays its energy cost. Dead
creatures are removed before feeding. A living creature may consume one nearby food,
which respawns immediately. Eligible creatures split energy with a mutated offspring.
Newborns enter the population only after the current update completes.

The physics timestep is fixed at 1/30 second. The dashboard accumulates elapsed time
and runs whole physics steps. Speed controls change the number of steps per wall-clock
second, not the physics equations. Under heavy load playback slows rather than taking
larger, unstable steps.

## Files and responsibilities

| File | Responsibility |
| --- | --- |
| `brain.py` | Parameter initialization, feed-forward inference, independent mutation |
| `creature.py` | Sensing, neural decisions, movement, energy, offspring construction |
| `spatial.py` | Uniform-grid index for finite-range nearest-food queries |
| `simulation.py` | Update order, seeded randomness, population lifecycle, metrics, checkpoints |
| `config.py` | Validated, immutable simulation settings |
| `dashboard.py` | Rendering, controls, selection, live network inspection |
| `experiments.py` | Generational optimization, baselines, held-out evaluation, reports |
| `main.py` | Command-line entry point for interactive and headless operation |

The simulation modules do not import Pygame. Only the dashboard requires a display
library; tests and evolutionary experiments can run without a window.

## Brain: 8 → 10 → 2

Inputs, in order:

1. Horizontal component of the direction to the nearest visible food.
2. Vertical component of that direction.
3. Food-presence flag, distinguishing no food from a food centered on the creature.
4. Energy divided by maximum energy.
5. Previous horizontal commanded velocity divided by maximum speed.
6. Previous vertical commanded velocity divided by maximum speed.
7. Horizontal world position scaled to −1…1.
8. Vertical world position scaled to −1…1.

Food direction is normalized to unit length. This avoids shrinking the signal as the
creature approaches food. There is no direct distance input in this version. Food is
invisible outside the sensor range. A zero-length displacement produces zero direction.

For each layer, the computation is `tanh(Wx + b)`. Eight inputs feed ten hidden neurons;
ten hidden activations feed two outputs. There are `8×10 + 10 + 10×2 + 2 = 112`
parameters. All arithmetic is implemented with Python lists and `math`; no neural
network framework is used.

The two outputs become x/y velocity commands. The vector is limited to unit length
before multiplying by maximum speed, so diagonal movement has no speed advantage.
This is a feed-forward network with previous velocity included as an input, not an RNN.

## Energy and inheritance

Default energy cost per second is `2.5 + 0.018 × commanded_speed`. A food restores
38 energy, capped at 240. Motion against a wall still costs energy. Boundary clamping
keeps the whole circle in the world; it does not tell the brain how to escape a wall.

Reproduction requires at least 170 energy, age 5 seconds, an expired 5-second cooldown,
and room below the 180-creature cap. Energy is split equally between parent and child.
The child inherits a *copy* of the brain, never a shared object. Each parameter has a
12% chance of independent Gaussian mutation (standard deviation 0.22), clipped to
−5…5. The child retains its founder lineage, records its parent ID, and increments
its generation. It spawns just outside the parent's center, clamped to the world.

Founder lineage is not a species classification. Multiple lineages can behave similarly,
and members of a lineage can diverge. The generation counter measures ancestry depth,
not synchronized population-wide generations.

## Two different selection mechanisms

**Interactive ecosystem:** survival, resource competition, and reproduction determine
which genomes persist. There is no explicit fitness ranking or backpropagation.

**Experiment runner:** independent agents are evaluated on common training layouts.
Elites survive, tournament selection chooses parents, and mutations create the next
population. Its explicit fitness includes meals, signed progress toward sensed food,
and survival time. This engineered training process is not the same as emergent
selection in the ecosystem. The dashboard's Evolved demo deliberately imports a policy
from this second process, and labels those founders accordingly.

## Reproducibility and performance

Separate seeded random streams control environment layout, evolutionary events, and
baseline movement. A checkpoint stores all three RNG states, the complete population,
food, counters, history, founder policy, and champion. Loading resumes the random
sequence instead of merely restarting from the original seed. Exact continuation is
tested in the same Python environment; bit-for-bit results across Python versions
and machines are not promised.

Food is stored in uniform-grid buckets. Each query searches intersecting cells and
returns the exact nearest food within the requested radius, with stable index-based
tie-breaking. Typical local work is much smaller than a full-food scan, but the worst
case remains linear when food is clustered or the search covers the whole world.

## Limits worth understanding

- No obstacles, predators, sexual reproduction, crossover, or evolving topology.
- Food respawns immediately, so this is a simplified resource model, not a calibrated
  biological ecosystem. The population cap is an explicit computational constraint.
- Selection order is randomized each step; feeding remains sequential.
- A small neural network can still get stuck at walls or drive extinction. Extinction
  is displayed explicitly and never silently replaced with a new population.
- Collision detection is discrete at a fixed timestep; extreme custom speeds can
  require a smaller timestep or swept collision detection.
- A strong single-agent foraging score does not establish stable multi-agent ecology.

## Code navigation

- Start with `World.step()` in `simulation.py` to follow one complete physics step.
- `Creature.sense()` and `Creature.update()` connect observations to neural decisions
  and movement. `Creature.reproduce()` handles energy splitting and ancestry.
- `Brain.forward()` performs inference; `Brain.mutated_copy()` creates an independent
  offspring genome.
- `World.save()` and `World.load()` serialize and restore simulation and RNG state.
- `experiments.train()` implements generational selection; `experiments.benchmark()`
  evaluates the resulting policies on held-out environments.
- `Dashboard.draw()` renders the world and inspection panels, while
  `Dashboard.handle_event()` routes mouse and keyboard input.
