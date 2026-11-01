# sealrun — house brief (run tag `sr1`, round 1 = chart)

## The Need (G0, already stored in uriel-house)
sealrun: a deterministic Rust solver that reads a game's seed, maps the shape of
the world with topology (connected regions, loops, enclosed caves), and plans the
fastest route to the win condition, starting with a Minecraft-like seeded world.
The owner's aim: a way to speedrun any game, starting from Minecraft, with a Rust
topological solver that reaches best times. Simple to an onlooker, important to him.

Acceptance (verbatim from house_need):
1. Every reached leaf has a RED-first bound test; crate tests run with `cargo test -p <crate>` inside the repo.
2. Determinism: the same seed gives a byte-identical world and an identical route.
3. Topology is correct: Betti numbers of the walkable terrain (b0 regions, b1 loops) match a brute-force flood fill / Euler characteristic on a fixed set of 100 seeds.
4. Surgery is correct: mining or placing one block updates the Betti numbers incrementally to the same value as a full recompute.
5. Routing: the geodesic route cost on the rules metric equals Dijkstra ground truth, and the toy any% run finishes in fewer in-game ticks than a baseline planner (BFS or MCTS) at the same wall-clock budget, on a fixed seed set.
6. A website on http://localhost:7740 shows every goal in plain English with its live status.

## The owner's theory ("TTS: Transdimensional Topological Solver"), condensed claims
- C1 Treat the procedural seed space (Perlin/Simplex/Voronoi noise) as a continuous manifold M instead of brute-force tree search (MCTS, RL rollouts).
- C2 Persistent homology computed "analytically from the seed, in constant time": b0 = resource clusters/islands, b1 = tunnels/bridges/cycles, b2 = enclosed caves.
- C3 "Surgery": walls/locks raise local Betti numbers; agent actions (mining, opening) act as boundary operators that cut the mesh and drop b1/b0, carving wormholes between regions.
- C4 Game rules (stamina, speed caps, friction, gravity) define a metric tensor g_ij; optimal motion = geodesic equation d2x/dt2 + Gamma dx dx = 0.
- C5 Multi-agent strategy as fiber bundles; fixed-point theorems find Nash equilibria without game-tree search.
- C6 Conformal maps flatten distorted dungeon geometry; analytic continuation predicts unrendered seed regions.
- C7 FTLE / Lyapunov exponents and Lagrangian coherent structures find stable routes through chaotic combat/physics.
- C8 Complex/quaternion embedding of noise: the imaginary part as a phase that "rotates through fractal iterations instantly".
- C9 Fractal (Hausdorff) dimension per Betti slice gives "infinite world complexity in constant-time invariants".
- C10 Benchmarks: seed-to-geodesic routing vs baseline MCTS on procedural survival (Crafter / custom deterministic seed grids).
(The pasted text also sketches an economics monitor; it is out of scope for sealrun.)

## Existing material
- monodromy (the owner's repo, Python, NOT Rust): C:/Users/seal/Documents/GitHub/monodromy
  Modules: phdim.py (PH fractal dimension via MST, total_persistence), dynamics.py (Lyapunov by QR
  cocycle, Henon/Lorenz), equilibrium.py (minimax game value, equalizer gap), schedule.py
  (Budget, successive_halving, coarse_to_fine), injectivity.py (two-point collision), properness.py,
  so3.py, blind.py, discover.py. Docs: docs/mathematics.md (section 9 "What has no theorem behind it").
  It is indexed in uriel-house: `mcp__uriel-house__rag_search` finds it. sealrun is a separate Rust
  repo; monodromy is the mathematical reference to port from, not a dependency.
- sealrun repo: C:/Users/seal/Documents/GitHub/sealrun — empty, one commit (.gitignore). Branch main.
- Machine: Windows 11, Rust/cargo 1.97, 16 GB RAM with about 3.3 GB free. Every build shares ONE
  target dir: CARGO_TARGET_DIR=C:/Users/seal/Documents/GitHub/sealrun/target (cargo's lock then
  serialises builds so RAM stays safe). Be lazy: fewest crates and files that work, std first,
  no dependency for what 20 lines do.

## Chart format (validated by `mcp__uriel-house__house_chart`, need "G0")
`{"need":"G0","fellow":"<you>","goals":[{id, parent, text, leaf, tier, class, needs, writes, reads,
creates, test:{name,cmd,class}, est:{ram_mb,secs,tokens}, guards, alt_of}]}`
- House fixes the top-level branches so the three charts line up (Foreman writes these nodes,
  parent "G0"; Chase and Cameron reference them):
  G1 seeded world · G2 topology (Betti numbers) · G3 surgery (mine/place updates) ·
  G4 routing and the any% run · G5 the plain-English website.
  Foreman may add G6+ (e.g. workspace skeleton) if the tree needs it.
- Ids: dotted under their parent (G2.1, G2.1.3). Chase ids end in a C-suffix (G2.C1), Cameron's in
  an A-suffix (G4.A1). Depth <= 6, fan-out <= 7, a non-leaf needs >= 2 children.
- Every leaf: `test` {name unique across the chart, cmd scoped like
  `cargo test -p sealrun-world same_seed_same_world` — never a whole-workspace run, class one of
  test_unit|build|bench|read|grep|collect|run_test|format|llm}, `tier`, `est`.
  tier "sonnet" = a resident who writes code (the harness maps it to the residents model);
  tier "haiku" = a nurse: read-only, class read|grep|run_test|collect|format, writes nothing.
- Paths are ABSOLUTE (C:/Users/seal/Documents/GitHub/sealrun/...). A path in reads/writes must exist
  or appear in `creates` of the goal itself or of a goal in its `needs`. Two leaves writing one
  file must be ordered by `needs`.
- Chase nodes carry `guards: "<goal id>"`; Cameron nodes carry `alt_of: "<goal id>"`.
- `text` is PLAIN ENGLISH: one sentence a 12-year-old understands. Jargon gets explained in the
  same sentence ("b0, the number of separate islands"). This text goes on the owner's website.

## Site copy (the website the owner asked for)
Also write C:/Users/seal/Documents/GitHub/sealrun/site/charts/<your name lowercase>.json:
`[{"id":"G2.1","title":"3-6 word title","plain":"1-2 plain sentences","why":"why this matters for a
faster speedrun, 1 sentence","done_when":"the test, in plain words"}]` — one entry per goal you charted.

## Departments and skills (owner order, 2026-11-01: "100% of every skill")
Every resident and nurse belongs to a department. Cameron owns the department map: he sees all
residents and nurses and gives each department its tailored skills. Residents and nurses invoke
their department's skills with the Skill tool before they write a line. The skill list (invoke by
exact name): ponytail:ponytail, coding-guidelines, superpowers:test-driven-development,
superpowers:verification-before-completion, superpowers:systematic-debugging, tdd-fix,
anthropic-skills:tda-tdd, discover-topology, discover-math, discover-rust-game-design,
discover-systems-theory, discover-testing, discover-research, extract-repo-math, rust-router,
rust-patterns, rust-learner, rust-daily, rust-code-navigator, rust-call-graph, rust-symbol-analyzer,
rust-trait-explorer, rust-refactor-helper, rust-deps-visualizer, unsafe-checker, m01-ownership,
m02-resource, m03-mutability, m04-zero-cost, m05-type-driven, m06-error-handling, m07-concurrency,
m09-domain, m10-performance, m11-ecosystem, m12-lifecycle, m13-domain-error, m14-mental-model,
m15-anti-pattern, typed-holes-refactor, domain-cli, domain-web, frontend-design:frontend-design,
site-revamp, visual-companion, dataviz, anti-slop, super-investigator, anthropic-skills:verify-claims,
investigator, meta-cognition-parallel, super-genius-rick, research-verdict, ship-like-teerth,
anthropic-skills:research-readme, writing-pr-messages, github-master, basic-toolkit, discover-engineering,
discover-debugging, discover-wasm, discover-ml, domain-ml.
