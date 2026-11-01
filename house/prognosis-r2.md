# Round 2 prognosis (House, 2026-11-01, shell 07:34-13:34 IST)

## Prognosis
Goal 1 (change the next chunk before it is built) is alive and measured. The first forceload ticket of a 2x2 square
picks the world: with first chunk (64,65) instead of (64,64), chunk (64,64) holds iron 149 and gold 14 instead of
147 and 16, and 43 blocks of the square differ. Resident run and House re-run agree exactly, and the same order repeated
gives 0 (n2-F6, n2-F8). The lever moves iron and gold, not diamonds (1 in every class), so "more diamonds" is not yet
shown. Goal 2 (fastest run) is not met on real terrain. On the hand trap the planner beats BFS, 485 ticks against 573
(main e5cae64, real_trap.rs). On the real 64x64 seed 7 spawn grid neither solver finds any route to iron from any of
1,417 air starts: water and stone are permanent walls in the round 1 model, so the terrain is islands (n2-T5, a House
probe, unbound). Next: a model where stone is dug through at its dig cost and water is swum at a price, then the race.

## Chart
- **Foreman (neurology):** the round 2 tree (lab tools G1, order experiment G3, route G4) - kept; G1 resolved whole.
- **Chase (surgery):** chunks as non-commuting operators; H1 "a chunk is a pure function of seed and position" -
  refuted by measurement (AB vs BA 18 blocks, n2-F3; first-chunk classes 30/43/41, n2-F8). His bound "order changes
  ores only by a few blocks, never above a vein" - kept (diamonds 0, iron and gold 2). Locality n2-T3 (a House lead)
  - dead, rerouted to N2.G3.6 (aim the edit lever, map its reach).
- **Cameron (immunology):** 4 first-chunk worlds instead of 24 orders (N2.G3.4.A3) - kept, it produced n2-F8; the
  one-boot spawn window (N2.G4.1.A1) won over G4.1.4 - kept.
- **Wilson (oncology, verification):** plans r2-batch2..16. Batch 15: a start-key-only and an iron-key-only mutant
  (the resident's tie mutant moved both), `gridfile.write` untested. Batch 16: the S-W kill closes that gap; edges
  listed under Open. The tool-trap contract fix came from a resident's measurement (the stone pick costs 3 stone, so
  `stone >= 11` gives plan = BFS = 473); House re-specified the trap as furnace + stone pick.
- **Residents (haiku):** batch 15, 5 leaves + 2 rebuilds; batch 16, 5 leaves; three verification lanes. Mutants:
  batch 15 lanes 6 of 8 killed + SM-1; batch 16 all 5 predictions killed.
- **Inspector (House, tools):** 8 findings audited, 0 struck. Re-runs on main: F1/F2 red as recorded (neighbour
  full), F3 18 (12 + 6), F4/F5 42 (34 + 8) and 6, F6 one fingerprint for 3 worlds, F8 identical; F7 bound but
  unreplicated. Caustic `research_orbit_audit` on order -> fingerprint (N2.G3.C6): violation of the premise "every
  order gives a distinct world" (3 orders, 1 orbit), consistent with n2-F6.
- **Dr House:** n2-L1 (observing is a move; one ticket makes a 5x5 full) - bound to
  `neighbour_of_full_chunk_is_not_yet_full`; it killed n2-T1, rerouted to N2.G3.2.

## Gates
Run n2, 12:34: gates 1-7 return 0 rows. Gate 2 returned F4, F5, F6 first: their Test nodes had no `first_status`;
set from the TestRun table (first run red) before the pass.

## Open
- Five batch 16 leaves are GREEN on main e5cae64 but quarantined by the flake guard, because House recorded GREEN
  from int/r2-b16 before the merge: N2.G3.4.A3, N2.G4.1.3, N2.G4.1.6, N2.G4.C2, N2.G4.C3. Route: the fellows
  re-chart them under new test names (renamed Rust test targets, so RED is a real "no test target"). N2.G3.6.2 and
  everything after it in the goal 1 aim chain wait on N2.G3.4.A3.
- N2.G4.2.3 (the real race) blocked: it needs the committed seed 7 grid of N2.G4.1.5; the chart has no NEEDS edge.
- n2-T5 (islands) has no RED test yet; the probe grid is in the session scratchpad, not the repo.
- n2-F7: the spawn window differs between two boots (stone 2223 vs 2231, water 3724 vs 3717, air 3323 vs 3322).
  A third boot is needed; fluid ticks before the save are a lead.
- n2-F4 "noise" repeats exactly (42 = 34 + 8), so it is probably deterministic, not noise.
- `lab/flatten.py` maps surface lava to air (walkable); the 64x64x256 spawn box holds 2966 lava blocks (surface share
  unmeasured).
- Test gaps: walk cost (guard_real_rules C2 survives: no asserted route walks); `to_bytes([[]])` accepted;
  start_finish neighbour order and centre rounding; spawn_area sent commands; seed7 x/z transpose; grid reader
  trailing bytes; crop-edge Mine bounds; first-chunk row fields. T3/T3b (removed asserts) survive by construction.
- Earlier survivors: BD, BL, BE (bench); WF, WG, WM, WN (choice); PH (pool); GA-GG (collapse).
- Carried: only the centre is saved after remove-then-stop (TF); the collapse guard is blind to tickets 2-4; b7 D,
  anvil C, S-H1, S-L, F-D, F-E, R-I, R-K, R-L2; round 1 G2.1 and G1.7.C1 quarantined; N2.G3.C5 blocked;
  test_neighbour_partial red by design; ResourceWarning; departments.json lacks G6 and G7; edits.py treats an unknown
  op as place; the mlm MCP may be dead; the Fabric download waits on the owner (ledger row 15); chart cmds for
  N2.G4.C1-C4 name `-p route` (the package is sealrun-route).
