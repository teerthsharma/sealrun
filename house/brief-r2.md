# sealrun — house brief, round 2 (Need N2.G0, real Minecraft 1.16.1)

## The owner's two goals (his words, 2026-11-01)
1. "someone found a way to transmutate a block in vanilla minecraft i want same but to transmutate
   next gonna be rendered chunk our way": find a move the player makes BEFORE a chunk generates
   that changes what that chunk contains (his sketch: "moves done before rendering chunk give chunk
   more diamond"), measured on the real game, not guessed.
2. "then the second goal is to achieve fastest run": plan the fastest route on real 1.16.1 terrain
   and beat a plain baseline.
His sketch also names: world generation as fractal topology, a manifold of player moves, imaginary
numbers, and Godel's incompleteness as the base of the study.

## What is measured already (House, 2026-11-01)
- Server: C:/Users/seal/Desktop/sanitised mineraft/server-1.16.1 (outside the repo; Minecraft files
  never enter the repo). server.jar sha1 a412fd69db1f81db3f511c1463fd304675244077, 37968964 bytes.
  Java 8u51: C:/Users/seal/Desktop/sanitised mineraft/.minecraft/runtime/jre-legacy/windows/jre-legacy/bin/java.exe
- server.properties: server-ip=127.0.0.1, online-mode=false, view-distance=4, level-seed=7.
- One headless boot (-Xmx1G nogui): log "Done (9.966s)!", 19.5 s wall clock to the Done line (5 s
  poll), one working-set sample 717 MB (peak not measured), clean `stop`, world folder 3.8 MB.
- Machine: 16 GB RAM, about 5 GB free; 69 GB disk free. So at most 3 servers at once at 1 GB heap;
  RAM, not CPU, is the limit. Builds and servers share it.
- Round 1 (need G0) code to reuse: crates/world (rng hash, Grid with to_bytes/from_bytes,
  Tile::is_open), crates/topo (UnionFind), crates/route (Dijkstra, tech tree order). In progress:
  noise, flood, euler, reach, tick metric (crates/route/src/metric.rs, Minecraft's dig rule).

## Rule for facts about Minecraft
Facts come from experiments on this local server, not from memory or the web. A claim from memory
is a hypothesis until a RED-first test on the server shows it.

## Hypotheses to chart (House's reading, all unverified)
- H1 Terrain and ores of a chunk are computed from the world seed and the chunk's coordinates
  (that is how seed tools predict diamonds). If true, the player cannot change a chunk's own
  generation, and the only levers on a not-yet-generated chunk are:
  - L1 generation ORDER: features that cross a chunk border overlap with features of the
    neighbour; which chunk generates first may decide which feature wins the overlap;
  - L2 blocks the player placed or broke in a loaded neighbour that a later feature meets;
  - (not chunk blocks: the shared random stream behind drops and bartering, which player actions
    do advance.)
- The deciding experiment for goal 1: the same seed generated in two or more orders (for example
  /forceload in different sequences over RCON, no client), then every block in a fixed area
  compared. Zero differing blocks kills L1 with a route; differing blocks are the lever, and a
  search over orders can then aim it at diamonds in a chosen next chunk.
- Godel, honestly placed: redstone makes Minecraft able to compute anything, so no solver answers
  every question about it (Godel/Turing). A bounded question (a route within N ticks inside a
  finite area) is a finite search and is answerable. Every solver question in this round carries
  its bound.

## Tools that need no game client (to be confirmed by tests)
- RCON (enable-rcon, rcon.port, rcon.password in server.properties) sends commands from a script.
- /forceload add makes chunks generate with no player; /setblock places a known block.
- Region files world/region/r.X.Z.mca are Anvil: zlib-compressed NBT. Python's stdlib (zlib,
  struct, socket) covers RCON and the reader, so the lab needs no new dependency. A reader is
  trusted only after it reads back a block placed with /setblock.
- Reset = stop, delete world/, start (about 20 s). A lab run must clean up its server process.

## Chart format (validated by `house_chart`, need "N2.G0")
Same rules as round 1 (house/brief.md in the scratch root; summary): ids carry the N2 prefix
(N2.G1, N2.G1.1); depth <= 6, fan-out <= 7, a non-leaf needs >= 2 children; every leaf has `test`
{name unique, cmd scoped to one test, class}, `tier` ("sonnet" = resident who writes code, "haiku" =
read-only nurse), `est` {ram_mb, secs, tokens}; absolute paths that exist or are in `creates`;
two leaves writing one file are ordered by `needs`. Chase ids end in C-suffixes with `guards`,
Cameron's in A-suffixes with `alt_of`. `text` is one plain sentence a 12-year-old understands.
A test that boots the server estimates ram_mb 1500 and secs >= 60.
House fixes the top-level branches (Foreman writes them, parent "N2.G0"):
- N2.G1 the lab: start, drive (RCON), reset and stop the headless server from a script, timed.
- N2.G2 the chunk reader: region files to blocks, proven against /setblock.
- N2.G3 goal 1, the next-chunk lever: the order experiment, then aiming it if it exists.
- N2.G4 goal 2, the fastest run: plan on real seed-7 terrain read by N2.G2 (wood, crafting table,
  wooden pickaxe, stone, stone pickaxe, iron) with the round 1 metric; beat a BFS baseline in ticks.
  Playing the route with a bot in the real game is a later round; say so in the chart.
- N2.G5 the website shows round 2 goals and the experiment's numbers.
Lab code lives in C:/Users/seal/Documents/GitHub/sealrun/lab (Python, stdlib only, tests in
lab/tests run as `python lab/tests/test_<x>.py`); solver code stays in the Rust crates.

## Site copy
Write C:/Users/seal/Documents/GitHub/sealrun/site/charts/r2/<your name lowercase>.json, same shape
as round 1: [{"id","title","plain","why","done_when"}], one entry per goal you charted.
