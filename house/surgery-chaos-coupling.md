# Surgery (Chase), round 2: chaos and coupling on the chunk graph
Verdict: the abstraction survives only as one object, an operator algebra. Generating chunk c is an
operator G_c on the block state. "Neighbours couple" means the G_c do not commute, and that is
measurable as block differences between build orders. Chaos, imaginary numbers and the quadratic game
do not map to anything the server computes; they are kept out of the goals (section 7).
Status: H1 (a chunk is a pure function of seed and coordinates) is UNTESTED; nothing below is a result.
Sources: [checked] = Chase fetched it; [nurse] = nurse quote, not re-read.
## 1. The abstraction in four lines
- Nodes: chunks c in Z^2; state s_c = its 65536 blocks (lab/anvil.py reads them).
- Operator G_c: "generate c". H1 says G_c(s) depends on (seed, c) only; then all G_c commute and every
  build order gives the same world. Coupling = the failure of that.
- Edge weight W_ij = blocks of chunk i that change when j is built before i instead of after.
  Everything below is a statistic of the table {order -> blocks}.

## 2. Coupled map lattice (state per chunk, coupling across borders)
- Maths: Kaneko CML u_s(t+1) = (1-e) f(u_s) + (e/2)[f(u_s+1) + f(u_s-1)], e in [0,1]
  [checked: en.wikipedia.org/wiki/Coupled_map_lattice]. e = 0 is uncoupled maps.
- Mismatch to state first: Kaneko updates all sites at once (synchronous). The generator updates one
  chunk at a time in some order (asynchronous, Gauss-Seidel style), and f is not a smooth map but a
  seeded feature placement. So the CML is a template, not a theorem: the maths gives the vocabulary
  (coupling e, spatial range, degrees of freedom growing with size [nurse]), not a prediction.
- Measurable: e_hat = (blocks of chunk i that depend on build order) / 65536, averaged over the 24
  orders of a 2x2 square at the 3 far squares (orders.py). Also e_hat per direction (north, east,
  south, west, diagonal).
- H1 predicts e_hat = 0 for every i. Coupled predicts e_hat > 0 only for neighbours (distance 1,
  diagonals included), with a direction bias: community posts say decoration waits on the south and
  east neighbours and ores use a +8,+8 offset [nurse, 1.11.2 posts, version mismatch, a lead].
- Killed by: 72/72 (24 orders x 3 squares) with 0 differing blocks AND the section 8 control
  reproducing. Then e = 0, the abstraction retires, and goal 1 falls back to lever L2.

## 3. Damage spreading (Lyapunov-style measure)
- Maths: Bagnoli, Rechtman, Ruffo define damage spreading through the Boolean derivative and a maximal
  Lyapunov exponent for cellular automata, with a directed-percolation-type transition for chaotic
  rules [nurse: arxiv.org/pdf/cond-mat/9811159, appeared in Phys. Lett. A 172 (1992), not Physica D].
- Fit: one-shot generation has no time axis, so a Lyapunov exponent is not defined. What is defined is the Boolean-derivative matrix J_ij = P(a block of chunk i changes | the input in
  chunk j is flipped), and its spectral radius rho(J). rho(J) > 1 would be the supercritical (damage
  percolates) case, rho(J) < 1 means damage dies out. That is the honest replacement for lambda.
- Measurable, perturbation 1 (order): swap two adjacent builds; D = count of differing blocks,
  profile D(r) by chunk distance r from the swap, reach R = max r with D(r) > 0.
- Measurable, perturbation 2 (one block): /setblock a changed block in a generated chunk A, then build
  neighbour B; count and reach of differing blocks in B and beyond.
- Strip experiment (2 boots): chunks (0..5, 0) built left to right, versus the first two swapped;
  D(r), r = 0..5, reads whether damage cascades.
- H1 predicts D = 0 everywhere. Coupled with local overlap predicts R <= 1 chunk and D(r) falling
  geometrically, rho(J) well below 1 (veins overlap rarely). Unverified: that decoration reads only
  the 3x3 ring (memory; wiki gives no neighbour count [nurse, f3 gap]).
- Killed by: D(r) > 0 for r >= 3 on the strip (long range, rho possibly > 1: kills the local-overlap
  model); or D = 0 for both perturbations.

## 4. Field curvature with a coupling constant = holonomy (the part with exact content)
- Maths: in Yang-Mills the curvature F is the commutator of covariant derivatives, g multiplies the
  field term, and lattice gauge theory writes the action with Wilson loops (loop products of link
  variables) [nurse: wikipedia Yang-Mills, Lattice gauge theory].
- Exact content that transfers: a flat connection means transport around a loop returns the start.
  Here the link "build j after i" acts on states; the loop defect of the plaquette (i, j) is
  d(G_j G_i s, G_i G_j s) in blocks. Curvature 0 on every plaquette is exactly "order independent".
- The 24 orders of 2x2 are the vertices of the permutohedron of S4 (24 vertices, 36 adjacent-swap
  edges). Order -> world is a function on it; an edge difference is a plaquette defect; flat = constant.
- Coupling constant g := sum of edge defects / sum of single-chunk block counts changed per build, one
  number per square. Metaphor warning: the Yang-Mills Lie-algebra structure is not used; only the
  commutator is. Do not claim a gauge theory.
- H1 predicts every defect 0 and g = 0. Coupled predicts defects on edges whose swapped pair are
  adjacent chunks and 0 on edges swapping far chunks inside the square (diagonal pairs a weaker case).
- Killed by: all 36 edge defects 0 on all 3 squares (flat).

## 5. Curvature of the chunk graph weighted by measured coupling
- Maths: Ollivier curvature kappa(x,y) = 1 - W1(m_x, m_y)/d(x,y) for random walks on a metric space
  [checked: arxiv.org/abs/math/0701886, "local contraction coefficient"; the discrete cube is positively
  curved]. Forman curvature is the cheap combinatorial cousin [nurse]; Tee and Trugenberger give
  conditions where the two agree [nurse, arxiv 2102.12329].
- Hand values for the RED test (computed by Chase, alpha = walk idleness): 4-cycle edge: kappa = 0 at
  alpha = 0, 0.5 at alpha = 0.5; the Z^2 grid is flat (kappa = 0 on every edge at alpha = 0).
- Consequence, found by working it out: the unweighted chunk graph is the plain grid, so its curvature
  is a constant 0 and carries no information. Curvature can only say something if the weights W_ij
  are non-uniform or directional. And W is directed (south/east bias), Ollivier needs a symmetric
  walk, so W must be symmetrised first, losing the bias.
- No source found links Ricci or Forman curvature to synchronisation or damage spreading (five
  searches, nurse finding 11, absence only). Any claim "negative curvature lets damage escape" is a
  conjecture. Test it, do not assume it: compare kappa(edge) with the measured J_ij on the strip.
- Kill: kappa on the weighted graph has rank correlation with J_ij below 0.5 over >= 20 edges, or W
  is uniform within noise. Then curvature is a plot, not a mechanism; retire it from the goals.

## 6. Player versus generator
- The generator is deterministic given its inputs (H1 or the ordered version), so there is no
  adversary and no hidden information. The "game" is one-player optimisation: choose moves before
  generation, maximise payoff (diamond ore blocks in a target chunk). Calling it a two-player game
  would be wrong unless the shared random stream (drops, bartering) enters, and it does not touch
  chunk blocks (brief-r2).
- Moves available: M1 the order of requested builds; M2 placed or broken blocks in a loaded neighbour.
  Search size: k chunks give k! orders (4 -> 24 boots, 9 -> 362,880 boots at ~20 s each, impossible).
- Quadratic content that is real: if payoff = sum_i a_i + sum_{i<j} b_ij x_ij with x_ij = +-1 the
  order of pair (i, j), this is an Ising or quadratic pseudo-boolean model, and choosing the best
  consistent order is the linear ordering problem. That is the "quadratic game", with integer
  payoffs, no complex numbers.
- Payoff bound (from how ores are placed, unverified): a later vein only fills stone, so order
  changes the diamond count only where two veins overlap or a structure cuts one. Prediction under
  coupling: |delta diamonds| per square is small (a few blocks, never above the vein size of 8).
  If the measured delta is 0 over all orders, goal 1 via order is dead even if blocks differ.
- Measurable: leave-out test. Fit b_ij on 18 of the 24 orders, predict diamonds (and all ores) on the
  held-out 6. Pair-sum holds if error is 0 on every held-out order.
- Killed by: any held-out error > 0 (triples interact; fall back to exhaustive for k = 4 only), or
  max-min diamond spread over orders = 0.

## 7. Where the complex quadratic map and imaginary numbers fit: they do not
- Maths exists: z -> z^2 + c, escape once |z| > 2, Julia set = boundary of the filled Julia set
  [checked via nurse quotes: wikipedia Mandelbrot_set, Julia_set].
- Fit checks against the lab: (1) generation is not an iteration of one map, it is a fixed
  pipeline of octave noises and placements; (2) every quantity (blocks, counts) is a real integer;
  (3) the only iterated quadratic in this study would be best-response dynamics in a quadratic game,
  and none runs in the server; (4) the section 6 payoff is quadratic in real pair variables and
  needs no i; (5) chunk coordinates as Gaussian integers gain nothing; (6) no measurement was
  identified that z^2 + c could predict.
- Verdict: metaphor, out of the goals. An iterated quadratic could be earned later only as a model of
  a player adapting a plan to generated terrain; that needs a bot, a later round.
- Fractal terrain is a smaller true claim. Octave noise sums the fBm form with frequency doubled and
  amplitude halved per octave [nurse: Perlin noise, Book of Shaders]; fBm has H in (0,1) and variance
  |t|^(2H) [nurse; variance is derived from the covariance]. Measurable: slope of log structure
  function of the seed-7 heightmap versus log lag over 2..64 blocks. A straight line means a scaling
  range, not "fractal" in general: octave noise is self-similar only inside a finite band.
  Kill: R^2 of the log-log line < 0.95, then the word fractal is dropped for this server.

## 8. Controls every claim needs
- Determinism control: the same build order run twice must give 0 differing blocks, else every
  difference is noise (threaded worldgen) and sections 2 to 6 have no signal.
- Order realised vs requested: /forceload requests an order, but the pipeline pulls neighbours in at
  lower stages itself (wiki stage list only [nurse]; neighbour counts not found). A null result
  kills the request-order lever only; the unseen internal order is not a player move.
- Prior art leads (snippets only): MC-55596 (same seed differs by load order), MC-224494, MC-188086,
  MC-125007 (features cut at chunk borders, 1.16.x). They raise the prior that D > 0; no measurement.

## 9. Godel, honestly placed
- Redstone makes the game Turing complete, so no solver decides every question about all worlds
  (Godel, Turing). That does not touch the questions here, because each carries a bound:
  - Decidable (finite): are any two builds of this finite square different (compare 4 x 65536 blocks)?
    What are W, J, kappa on a k-chunk region? Best of k! orders for k <= 4? Fastest route within N
    ticks in a fixed box.
  - Not claimed: any whole-world property for every order of every region, or of unbounded player
    behaviour. Those are not asked, and no general solver is promised.

## 10. Survived or metaphor
- Measurable: e_hat (section 2), D(r), R, rho(J) (3), plaquette defects and g (4), kappa vs J (5),
  pair-sum held-out error and diamond spread (6), structure-function slope (7).
- Metaphor, out of goals: z^2 + c, imaginary numbers, chaos as exponential divergence, gauge
  group structure, a two-player game.
- Limits: the 3x3 ring, vein overlap and +8 offset are memory or other-version posts; the first server
  run replaces them. Six sub-goals: proposals/surgery.json (reuse blockdiff, ores, orders, squares_plan).
- First experiment: the determinism control plus the 24-order run on the 3 far squares (72 builds,
  squares_plan gives one boot per order), then the strip. Default if the control fails: stop and fix
  the lab before any order claim.
