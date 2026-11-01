# Field map: the mathematics of Minecraft world generation (Foreman, N2 round 2)

Status key: source states = a page says it, nobody here measured it. checked by Foreman = Foreman fetched the page.
measured by the lab = run on the local 1.16.1 server. contradicted = two sources or an arithmetic check disagree.
Goal 1 = change what a not-yet-generated chunk holds by a move made before it generates. Goal 2 = fastest run.

## Verdict first
The field says the RANDOM STREAMS of a chunk are fixed by world seed plus chunk coordinates. The field does not say the
FINISHED BLOCKS are fixed: several Mojang tracker entries (snippets only) and three modder write-ups say blocks written
across a chunk border depend on which neighbour generated first. Goal 1 therefore lives only in that border band,
and nobody has measured its size on 1.16.1. Nothing here supports changing a chunk's own terrain or ore count.

## A. Seed, RNG, noise
- A1. Java Random is a 48-bit linear congruential generator; only 48 of the 64 seed bits reach it.
  https://Gist.github.com/hube12/368e7331e497b17e092e8ca4ba206b3c . source states (community gist). Goal 1: the seed is a
  constant of the world, not a player move. Goal 2: seed 7 is fixed, so seed hunting (FSG) is off the table for us.
- A2. Yarn ChunkRandom: setSeed keeps the low 48 bits for the population seed.
  https://maven.fabricmc.net/docs/yarn-21w06a+build.5/net/minecraft/world/gen/ChunkRandom.html . source states (21w06a docs,
  not 1.16.1). Goal 1: same as A1.
- A3. Seed methods are pure functions of seed and position: setPopulationSeed(worldSeed, blockX, blockZ),
  setDecoratorSeed(populationSeed, index, step), setCarverSeed(worldSeed, chunkX, chunkZ), setRegionSeed(worldSeed,
  regionX, regionZ, salt) for structure starts.
  https://maven.fabricmc.net/docs/yarn-1.18.2+build.1/net/minecraft/world/gen/random/ChunkRandom.html . checked by Foreman
  via nurse quote, 1.18.2 signatures, not 1.16.1. Goal 1: no player input exists in these formulas, so structure and
  feature seeds are not a lever. (The 1.16.1 formula itself: no source found, gap.)
- A4. 1.18 experimental snapshot 1 set a 48-bit seed limit, 21w41a reverted to 64 bits.
  https://minecraft.wiki/w/Seed_(level_generation) . source states. Not 1.16.1; no use for either goal.
- A5. Biomes: cubiomes layer stack covers up to 1.17; from 1.15 biome generation stops at 1:4 OceanMix, voronoi seeded with
  the first 8 bytes of SHA-256 of the world seed.
  https://docs.rs/crate/cubiomes-sys/latest/source/cubiomes/layers.h . source states. Goal 1: biome is a function of seed
  and position alone, so a chunk's biome cannot be moved. Goal 2: a reusable oracle for biome and structure placement.
- A6. The gist says biomes use an internal LCG, and also that Alpha/Beta biomes used Java Random: the two lines are for
  different versions, not a conflict for 1.16.1. source states.
- A7. 1.16.4 terrain uses OctavePerlinNoiseSampler (density), optional SimplexNoiseSampler (island), plain NoiseSampler
  (surface depth). https://maven.fabricmc.net/docs/yarn-1.16.4+build.1/net/minecraft/world/gen/chunk/NoiseChunkGenerator.html
  . source states (field names only, no algorithm). Goal 1: smooth noise of position, fixed by seed.
- A8. Ore-vein float error: Mojang MC-185925 says lode placement uses 32-bit floats that distort veins at huge
  distances (1.16 pre-releases). https://bugs-legacy.mojang.com/browse/MC-185925 . source states (search snippet).
  Goal 1: a function of coordinates, not of a move.
- A9. Seed crackers (SeedCrackerX by CB30, KaptainWutax SeedCracker, FeatureUtils, SeedUtils) recover the seed from
  structures, pillars and ore positions. https://github.com/CB30/SeedcrackerX , https://github.com/kaptainwutax .
  source states. Goal 1: their existence is the field's strongest evidence that chunk content is a function of seed.

## B. Chunk pipeline and neighbours
- B1. Java steps in order: empty, structure_starts, structure_references, biomes, terrain (carvers), features,
  initialize_light, light, spawn, full. https://minecraft.wiki/w/World_generation . checked by Foreman (first 100,000 of
  139,674 characters; no neighbour counts on that part). Goal 1: "features" is the step where blocks cross chunk borders.
- B2. ChunkStatus has a per-stage task margin (getTaskMargin) but no values found.
  https://maven.fabricmc.net/docs/yarn-1.16.4+build.1/net/minecraft/world/chunk/ChunkStatus.html . source states (names
  only). Open: how many neighbours FEATURES needs and at what status on 1.16.1. Measured by lab: not yet.
- B3. Decoration waits for the south and east neighbours; vanilla ores offset +8,+8; big structures defer further.
  https://forums.minecraftforge.net/topic/58520-1112-looking-for-structure-generation-advice/ . source states (1.11.2
  community analysis). Goal 1: if the 1.16.1 rule is similar, features of chunk C can write into a neighbour N.
  Not applicable to 1.16 without a test (1.13 to 1.16 rewrote the pipeline).
- B4. Sponge docs: population runs once the three chunks adjacent in +x and +z are loaded.
  https://docs.spongepowered.org/5.1.0/nl/plugin/wgen/index.html . source states (version not stated, likely 1.12.2).
- B5. Lab measured: headless 1.16.1 boots seed 7 in about 20 s; region r.0.0.mca holds 460 chunks, r.-1.0 holds 69, four
  region files are 0 bytes; 7,360 real sections decode with the padded 1.16 layout (4 and 5 bits seen). measured by the
  lab. Goal 1 and 2: the reader works on real chunks; it does not yet tell which stage each chunk was at.

## C. Order dependence (the heart of goal 1)
- C1. MC-55596: chunks from one seed differ by load or generation order. https://bugs.mojang.com/browse/MC-55596 . source
  states (title and snippet only; status conflicts, Unresolved vs Confirmed). Goal 1: direct claim of the lever.
- C2. MC-224494: dirt near pools depends on chunk load order, Confirmed.
  https://bugs-legacy.mojang.com/browse/MC-224494 . source states (snippet). Goal 1: supports L1; reporter suggests
  avoiding teleports, meaning travel pattern changes the result.
- C3. MC-272481: stronghold chest loot differs for one seed, blamed on generation order with a cave in the chunk, Won't Fix.
  https://bugs-legacy.mojang.com/browse/MC-272481 . source states (snippet). Goal 1: loot rolls move with order.
- C4. MC-188086 and MC-125007: trees, mushrooms, decorations cut at chunk borders on 1.16.x; one linked entry says tree
  generation is not seed dependent. https://bugs.mojang.com/browse/MC-188086 , https://bugs.mojang.com/browse/MC-125007
  . source states (snippets). 1.16.x is named, so this is the closest to our version. Contradicts "fully determined".
- C5. MC-185253: border decorations ignore saved biome data of half-generated chunks, open.
  https://bugs-legacy.mojang.com/browse/MC-185253 . source states (snippet).
- C6. Forge thread: order changes values drawn from shared world random, but terrain itself comes from a deterministic
  function. https://forums.minecraftforge.net/topic/27256-worldgen-and-worldrand . source states (pre-1.16, extraction
  not checked against raw HTML). This is the one source that says "deterministic": it limits order effects to shared state.
- C7. Searches for any source stating generation is fully order independent returned none (nurse f3, plus one Foreman
  search). That is absence of evidence, not a proof of order dependence. checked by Foreman.
- C8. Mojang tracker pages themselves could not be fetched (title only or refused), so every C-item is a snippet. A real
  1.16.1 order effect is unmeasured; the lab experiment below decides it.

## D. Speedrun and "transmutation"
- D1. "Block transmutation": nine pre-1.13 methods that set a block's data value (random Indev values, preserved
  value, liquid, moving piston, tripwire hook, door, arrow, falling block...). Last working method ended at 17w46a; 17w47a
  removed block metadata. Only method 1 (Indev 0.31) touched world generation.
  https://mcdf.wiki.gg/wiki/Java_Edition:Block_Transmutation . checked by Foreman (fetched, summarised). Goal 1: gives the
  owner's word, not a 1.16.1 method; none of the nine works on 1.16.1.
- D2. Searched for a new vanilla transmutation trick (2026): none found, only mods and a 24w38a recipe bug.
  checked by Foreman (one search; absence is weak).
- D3. 1.16.1 speedrun RNG: piglin pearl barter about 4.73% for 4 to 8 pearls, reduced to about 2.18% for 2 to 4 pearls in
  1.16.2. https://www.speedrun.com/posts/tdf9x (HTTP 403; snippet) and https://minecraft.wiki/w/Bartering (1.16.2 tweak
  note only). source states. One mod site says 8.5%: contradicted by the 4.73 and 2.18 figures. Goal 2: barter and blaze
  rolls come from the shared random stream, which player actions advance. Not chunk content.
- D4. Dream report (Scribd): 42% pearl trades and 69% rods, but the quoted counts are 42 of 262 (16.0%) and 211 of 305
  (69.2%). https://www.scribd.com/document/490823478/dream . contradicted (Foreman arithmetic: 42/262 = 0.160; rods match).
  Treat the 42% as a misprint; the report's own conclusion was not retrieved.
- D5. Tools: Atum (reset hotkey), FSG mod (uses a filtered-seed database), Julti (multi-instance). Julti README fetched.
  https://github.com/DuncanRuns/Julti . source states / checked by Foreman for Julti only. Goal 2: all three change which
  world is played, not what a generated chunk holds; our seed is fixed at 7.

## Ranked levers on a not-yet-generated chunk
Rank 0 is not a lever but the control: if the same order run twice differs, nothing below can be read.
0. CONTROL same order twice. Cheapest: 2 boots of one 2x2 square at chunk (64,64), forceload one chunk at a time, wait for
   full, then diff the 4 chunks plus their readable ring. Kill: nonzero diff means threading noise; fix by serial loads first.
1. L1 generation order. Support: C1, C2, C4, B3. Cheapest: same square, forward vs reverse order (2 boots, extend to 24
   orders by orders.py). Kill: zero differing blocks over all orders and 3 squares (about 20 s boot + loads each). If
   alive: count diamonds in the diff, then search orders. Likely effect is a thin border band only.
2. L2 blocks placed in a loaded neighbour. Support: mechanism only (veins and trees test the target block). Cheapest: make N
   full, /fill a border band of N with a non-stone block, then generate C; diff against a control without the fill.
   Kill: C and N identical to control outside the filled cells. Cannot touch C itself: /setblock needs a loaded chunk.
3. Generation-time state (tick count, difficulty, gamerules, player nearby). No source supports it. Cheapest: boot, idle
   120 s, generate the square, diff against an immediate generation. Kill: zero diff.
4. Seed or feature seed formulas (A1 to A3). Ruled out by the field: pure functions of seed and position.
5. Shared random stream (barter, drops, loot rolls): real and movable by the player, but it is not chunk blocks. D3.
   Possible partial exception: chest loot seeds (C3). Check with the loot of a structure chest under two orders.

## Where the field says "determined" and where it does not
Determined: seed expansion, biome layers, density noise, carver and population random streams (A1 to A7, C6, seed
crackers A9). Not shown determined: finished blocks within one chunk of a border (C1 to C5), structure chest loot
(C3), shared-world-random draws (C6). Unknown on 1.16.1: the neighbour radius per stage (B2).

## What "transmutate a block in vanilla" most likely means
Probable: the "block transmutation" family of D1, a trick that turns one block into another by corrupting its data value;
the owner wants the generation-time analogue ("transmutate next gonna be rendered chunk"). No 1.16.1 method exists (D1
dead from 17w47a, D2 empty). Whether he saw a specific video or post is unknown. Implication for goal 2: the route
planner must read terrain generated in the order the player will produce, else border blocks differ (C-items).
