use std::path::Path;
use std::process::Command;

const DATA: &str = r#"{"need":"GR","departments":[],"theory":[],"facts":[],"alternatives":[],"goals":[
{"id":"GR","parent":null,"title":"Root","status":"active","fellow":"Foreman","department":null},
{"id":"GA","parent":"GR","title":"Goal A","status":"blocked","fellow":"Foreman","department":null},
{"id":"GB","parent":"GR","title":"Goal B","status":"reached","fellow":"Foreman","department":null},
{"id":"GC","parent":"GR","title":"Goal C","fellow":"Foreman","department":null}
]}"#;

fn render_source(html: &str) -> &str {
    let start = html.find("function renderPage(").expect("index.html has no renderPage");
    let end = html[start..].find("\n}").expect("renderPage has no closing brace") + start + 2;
    &html[start..end]
}

fn card<'a>(page: &'a str, id: &str) -> &'a str {
    let at = page.find(&format!("data-goal=\"{id}\"")).unwrap_or_else(|| panic!("no card for {id}"));
    let end = page[at..].find("</article>").expect("card is not closed") + at;
    &page[at..end]
}

#[test]
fn site_status_red_when_test_red() {
    let index = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../site/index.html");
    let html = std::fs::read_to_string(&index).expect("read site/index.html");
    let script = format!("{}\nprocess.stdout.write(renderPage({DATA}));\n", render_source(&html));
    let js = std::env::temp_dir().join(format!("guard_status_{}.js", std::process::id()));
    std::fs::write(&js, script).expect("write temp js");
    let out = Command::new("node")
        .arg(&js)
        .output()
        .expect("node must be on PATH; this test never skips");
    let _ = std::fs::remove_file(&js);
    assert!(out.status.success(), "node failed: {}", String::from_utf8_lossy(&out.stderr));
    let page = String::from_utf8(out.stdout).expect("render output is utf-8");

    let a = card(&page, "GA");
    assert!(a.contains(">failing<"), "blocked goal GA must show failing: {a}");
    let b = card(&page, "GB");
    assert!(b.contains(">passing<"), "reached goal GB must show passing: {b}");
    let c = card(&page, "GC");
    assert!(c.contains(">not started<"), "goal GC without status must show not started: {c}");
    assert!(!c.contains("passing"), "goal GC without status must not show passing: {c}");
}
