#[test]
fn skeleton_links_all_crates() {
    assert_eq!(sealrun_world::NAME, "sealrun-world");
    assert_eq!(sealrun_topo::NAME, "sealrun-topo");
    assert_eq!(sealrun_route::NAME, "sealrun-route");
}
