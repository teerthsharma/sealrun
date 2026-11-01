<h1 align="center">sealrun</h1>

<p align="center"><b>Plan the fastest Minecraft run before the timer starts. Then find out if the world remembers how you built it.</b></p>

<p align="center">
  <img alt="Rust" src="https://img.shields.io/badge/solver-Rust-b7410e?style=flat-square">
  <img alt="Minecraft" src="https://img.shields.io/badge/tested%20on-Minecraft%201.16.1%20seed%207-2d6a4f?style=flat-square">
  <img alt="Tests" src="https://img.shields.io/badge/every%20finding-red%20test%20first-1f2933?style=flat-square">
</p>

<p align="center"><b>Invented by <a href="https://teerthsharma.vercel.app/">Teerth Sharma</a></b> · <a href="mailto:teerths57@gmail.com">teerths57@gmail.com</a></p>

---

## What this is

Every Minecraft world comes from one number: the **seed**. Same seed, same hills, same rivers, same iron. That is why set-seed speedruns exist.

sealrun looks at the map before the run. It finds which parts of the land connect, where the islands are, and where water or stone cuts you off. Then it plans the fastest route. Same seed, same plan, every time.

It also asks a weird question. Minecraft builds the world in square pieces called **chunks**, and which chunks get built first depends on where you go. So: if you go north first or east first, do you end up in the same world?

## What we achieved

Every line below was measured on a real Minecraft 1.16.1 server on seed 7.

- **One `/forceload` builds 25 chunks, not 1.** A 5 by 5 block around it. The wiki predicted it. The server gave 25 of 25.
- **Build order really changes the world.** Four chunks in a square, built in 4 different orders (not all 24), gave 4 different worlds.
- **But only a little, and only for common ore.** In chunk (64,64), iron plus gold is 163 in every world. One order swaps 2 iron for 2 gold. **Diamonds never moved.**
- **The world can forget how it was built.** Two different build orders of the square gave the exact same world, block for block. So the world alone cannot always tell you how it was built.
- **We killed our own first idea.** We guessed a rule, wrote it down before testing, then ran it. On a five-chunk ring it said 5 worlds and the server gave 6. A bolder version of the rule lost on the same test too.
- **The wider rule mostly lost too.** We let each chunk remember the order of the tickets within 4 chunks. It explains only 19 of the 102 chunks that change with build order. Where it did fit, all 19 fits sit exactly on the 4-chunk reach, and luck would give about 6. So it is a clue, not an answer.
- **A spacing test said no as well.** The rule predicted 1 world when tickets sit 5 or 7 chunks apart. The server gave 6 different worlds from 6 orders, on the chunks where repeats agreed.
- **The old planner could not leave spawn.** From none of the 1,417 open tiles at spawn did the round 1 planner find a route, because no walkable area there touches a tree, so it could never get wood. The dig-and-swim planner routes from spawn in 538 ticks.
- **The spawn area is islands.** On the seed 7 spawn map there are 158 separate walkable regions. Pay 10 to swim and they merge to 77. Pay 23 to dig and they merge to 1.
- **A planner that can dig and swim routes every start point.** 179 of 179 at a million steps, same as plain search. At 10,000 steps plain search is ahead (67 against 13). Where both find a route, the planner's route is never slower in game ticks.
- **We found nobody who has written this down.** We searched 53 sources (the Minecraft wiki, bug trackers, math papers) and found no one who states how build order shapes a Minecraft world.
- **The Blood Lab works.** 15 of 16 rebuilt so far. Small AI agents rebuilt published maths from scratch, and each one had to print the same number as its source: 104 of 256 simple rules that ignore update order, 24, 14 and 20 corners for three classic shapes, 200 random maps where two island-counting methods agree, and the "elder rule" for which island lives on when two islands merge.
- **Our first-ticket count is a known shape.** Counted over every run of neighbouring tickets, the first-ticket rule splits the 24 build orders of 4 tickets into 14 groups. Those are exactly the 14 groups that binary search trees give, a grouping mathematicians already study.

## See it: one ticket, 25 chunks

<p align="center"><img src="docs/ticket-tile.svg" alt="A 5 by 5 block of chunks around one ticket, shaded by ticket level" width="640"></p>

A ticket starts at level 31. Each chunk away adds 1. A chunk is finished up to level 33. That is two chunks out in every direction, so 5 by 5. The picture is the real server's answer.

This matters for one reason. If a second ticket lands inside a block that is already built, there is nothing left for it to build. That was our first guess: the first ticket in a neighbourhood does the deciding. The server said no (see below).

## How it was built, round by round

**Round 1, the solver.** Three small Rust crates. `world` makes a map from a seed, byte for byte the same every time. `topo` counts separate regions and loops, and updates the count when you mine one block. `route` finds the cheapest route. On a hand-made trap map, where only a stone pickaxe gets you past the wall, the planner finishes in 485 ticks and plain search needs 573.

**Round 2, a real server.** A set of Python scripts starts a real Minecraft server, builds chunks with `/forceload`, saves, stops, and reads the save files from disk. One fresh world takes about 20 seconds and under 1 GB. This is where the 25-chunk block and the first sign of build order came from.

**Round 3, the rule.** Before running anything new, we wrote down a rule and committed it: each chunk keeps only the first ticket that reaches it. Then we tested it. It lost. A wider version lost on most chunks too.

**The Blood Lab.** 15 of 16 papers, bug reports and algorithms rebuilt so far, in code under `lab/blood/`. Each one must reproduce a number printed in its source or it does not go in.

**The bug hunt.** We search our own code for real bugs in six areas. Each area announces up front how many probes it runs and how many real bugs end the hunt. A bug only counts with a test that fails on today's code and prints the wrong answer it saw.

## The maths, as pictures

**Two orders, one world.** Chunks A and B touch. Build A first and a granite blob across their border lands one way. Build B first and the same blob can turn out andesite. So a world carries a faint trace of what was built first.

**Counting worlds.** Four chunks can be built in 4 × 3 × 2 × 1 = 24 orders. Many orders end in the same world. Put orders that give the same world in one group. The number of groups is the number of different worlds. Our first model said 4 worlds from 24 orders, 6 orders per group. That was a prediction, never run over all 24 orders.

**Bits lost.** If the model were right, picking one order out of 6 would take about 2.58 yes-or-no questions, and that is how much the finished world would no longer tell you. In plain words: the world holds true facts about how you built it that it cannot show you any more.

**Do the groups make sense?** Picture every build order as a dot, with dots close together when the orders are almost the same. Orders that give one world should sit in one solid clump. We checked the groups that hold more than one order: 3 of 3 came out in two separate pieces, not one clump. One more sign the first rule was too simple.

**Islands and prices.** Treat water and stone as "you can cross, for a price" instead of "wall". At price 0 the spawn map is 158 islands. As the price rises, islands merge.

<p align="center"><img src="docs/islands-join.svg" alt="Regions of the seed 7 spawn map at three prices" width="640"></p>

The first tree is reachable at exactly the cheaper of the two prices, in all 961 price pairs we tried.

## The rule against the real server

<p align="center"><img src="docs/worlds-predicted-measured.svg" alt="Predicted and measured number of different worlds for five ticket layouts" width="640"></p>

Grey is what the first rule said, written down before the runs. Orange is what the server gave. One layout matched. The rest did not, and the rule lost.

There is a second problem we found on the way. **Building the same order twice does not always give the same world.** Repeats differ by 122 to 3,396 blocks, mostly in the ring 2 to 3 chunks from the tickets, where chunks are only half loaded. Across 11 worlds, each odd chunk came out in one of just 2 or 3 versions, so it is not random noise. 59 to 63% of the differing blocks sit in the outermost row of a chunk (23% if spread evenly), mostly granite, andesite and diorite blobs.

Were other programs on the machine causing it? We booted the same order 6 more times with only one Minecraft server running and nothing else. 15 of 25 chunks still came out differently, each in 2 to 4 versions. So the cause is inside the server itself.

Our best guess: a blob that crosses a chunk border is placed by whichever neighbour decorates first, so the server's own thread timing acts like a hidden second build order. That is the explanation we are testing, not a proven one.

## Routes on real terrain

| Step budget | Priced planner routes | Plain search routes |
|---|---|---|
| 10,000 | 13 of 179 | 67 of 179 |
| 100,000 | 178 of 179 | 177 of 179 |
| 1,000,000 | 179 of 179 | 179 of 179 |

Both got the same step budget on the 179 start points of the spawn map. Plain search wins on a tiny budget. Where both found a route, the planner's was never slower in game ticks.

## Run it

You need Rust (stable) and Python 3.11. The real-server experiments also need a Minecraft 1.16.1 server jar, which is not in this repo.

```bash
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings

python lab/tests/test_n3_bits_hand.py Lab.bits_lost_square_is_log2_six
python lab/tests/test_ores.py Lab.ore_tally_counts_per_chunk

python site/serve.py     # the goal page, http://localhost:7740
```

To use a real server:

```bash
export SEALRUN_SERVER="/path/to/server-1.16.1"   # read only, never written
export SEALRUN_JAVA="/path/to/java"
python lab/tests/test_forceload_tile.py Lab.forceload_tile_full_at_0_to_2_and_not_saved_at_3
```

Each world lives in a scratch folder outside the repo and is deleted afterwards. No Minecraft file is ever committed.

## Where things live

```
crates/world   seed to map, same seed same bytes
crates/topo    regions, loops, live updates when a block changes
crates/route   the planner, plain search, priced dig and swim
lab/           scripts that drive the real server and read its saves
lab/research/  the order rule, the clump check, the price curve
lab/blood/     the Blood Lab re-builds
site/          the goal page and its cards
docs/          the figures above
```
