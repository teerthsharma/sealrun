#[path = "common/n3_priced.rs"]
mod n3_priced;

use n3_priced::cheapest;

const HAND: [&str; 5] = ["...#...", "...~...", "S..#..G", "...#...", "......."];
const SEALED: [&str; 2] = ["S.#", "##G"];

#[test]
fn dig_and_swim_cost_hand_grid() {
    assert_eq!(
        cheapest(&HAND, 5, 1),
        Some(6),
        "dig=1 swim=5: straight 5 air + dig 1 = 6; water 7 + swim 5 = 12; detour 10"
    );
    assert_eq!(
        cheapest(&HAND, 1, 9),
        Some(8),
        "dig=9 swim=1: water 7 + swim 1 = 8; straight 5 + dig 9 = 14; detour 10"
    );
    assert_eq!(
        cheapest(&HAND, 9, 9),
        Some(10),
        "dig=9 swim=9: detour 10; straight 5 + dig 9 = 14; water 7 + swim 9 = 16"
    );
    assert_eq!(
        cheapest(&SEALED, 1, 4),
        Some(6),
        "sealed goal, dig=4: air 1 + dig 4 + air 1 = 6"
    );
    assert_eq!(
        cheapest(&SEALED, 1, 7),
        Some(9),
        "sealed goal, dig=7: air 1 + dig 7 + air 1 = 9"
    );
}
