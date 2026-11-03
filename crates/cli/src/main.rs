fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match sealrun_cli::run(&args) {
        Ok(out) => println!("{out}"),
        Err(e) => {
            eprintln!("sealrun: {e}");
            std::process::exit(2);
        }
    }
}
