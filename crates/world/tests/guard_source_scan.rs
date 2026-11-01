use std::fs;
use std::path::Path;

fn is_ident(b: u8) -> bool {
    b.is_ascii_alphanumeric() || b == b'_'
}

fn has_word(line: &str, word: &str) -> bool {
    let bytes = line.as_bytes();
    let mut from = 0;
    while let Some(pos) = line[from..].find(word) {
        let start = from + pos;
        let end = start + word.len();
        let before_ok = start == 0 || !is_ident(bytes[start - 1]);
        let after_ok = end == bytes.len() || !is_ident(bytes[end]);
        if before_ok && after_ok {
            return true;
        }
        from = end;
    }
    false
}

#[test]
fn worldgen_source_has_no_hashmap_or_float() {
    let dir = Path::new(concat!(env!("CARGO_MANIFEST_DIR"), "/src"));
    let mut files: Vec<_> = fs::read_dir(dir)
        .expect("read worldgen src dir")
        .map(|e| e.expect("dir entry").path())
        .filter(|p| p.extension().is_some_and(|x| x == "rs"))
        .collect();
    files.sort();
    assert!(
        files.len() >= 3,
        "scanned {} .rs files in {}, expected at least 3",
        files.len(),
        dir.display()
    );

    let mut hits = Vec::new();
    for path in &files {
        let text = fs::read_to_string(path).expect("read worldgen source file");
        for (i, line) in text.lines().enumerate() {
            for word in ["HashMap", "HashSet", "f32", "f64"] {
                if has_word(line, word) {
                    hits.push(format!("{}:{}: {}", path.display(), i + 1, word));
                }
            }
        }
    }
    assert!(
        hits.is_empty(),
        "unordered map or float in worldgen source (nondeterministic across machines):\n{}",
        hits.join("\n")
    );
}
