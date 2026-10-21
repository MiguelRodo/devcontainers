"""Remote-only toolchain smoke; no projcli/projr behavior or parity assertions."""
import base64
import binascii
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zlib

EVIDENCE = Path("smoke-evidence").resolve()
EVIDENCE.mkdir(exist_ok=True)


def run(*args, cwd=None):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    with (EVIDENCE / "commands.log").open("a") as log:
        log.write("+ " + " ".join(map(str, args)) + "\n" + result.stdout + "\n")
    print(result.stdout, end="", flush=True)
    result.check_returncode()
    return result.stdout


class Images(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.payloads = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            src = dict(attrs).get("src", "")
            if src.startswith("data:image/png;base64,"):
                self.payloads.append(base64.b64decode(src.split(",", 1)[1]))


# Capture only named tool/package metadata, never environment or process dumps.
run("git", "rev-parse", "HEAD")
for command in [("container-info",), ("rustc", "-Vv"), ("cargo", "-V"),
                ("rustup", "show", "active-toolchain"), ("cc", "--version"),
                ("make", "--version"), ("pkg-config", "--modversion", "openssl"),
                ("python3", "--version"), ("quarto", "--version"),
                ("quarto", "pandoc", "--version"), ("qpdf", "--version"),
                ("pdfimages", "-v"), ("pdftotext", "-v")]:
    run(*command)
run("Rscript", "-e", 'cat(R.version.string, "\\n"); '
    'for (p in c("knitr", "rmarkdown")) cat(p, as.character(packageVersion(p)), "\\n"); '
    'stopifnot(rmarkdown::pandoc_available()); print(rmarkdown::pandoc_version())')
# Quarto's TinyTeX may live outside PATH. This also proves Quarto can discover it.
run("quarto", "list", "tools")

with tempfile.TemporaryDirectory(prefix="projcli image smoke ") as temporary:
    root = Path(temporary) / "project with spaces"
    analysis = root / "analysis"
    inputs = root / "input"
    analysis.mkdir(parents=True)
    inputs.mkdir()
    (inputs / "data.csv").write_text("value\n17\n")
    # Lossless RGB sentinel: PDF verification compares decoded pixels, not headers.
    rgb = bytes((37, 149, 211)) * (32 * 24)

    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", binascii.crc32(kind + payload) & 0xffffffff))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", 32, 24, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(b"".join(
               b"\0" + rgb[y * 96:(y + 1) * 96] for y in range(24))))
           + chunk(b"IEND", b""))
    (inputs / "sentinel.png").write_bytes(png)
    (analysis / "read.py").write_text(
        'from pathlib import Path\nassert Path("../input/data.csv").read_text() == "value\\n17\\n"\n')
    run("python3", str(analysis / "read.py"), cwd=analysis)
    (analysis / "main.rs").write_text(
        'fn main() { assert_eq!(std::fs::read_to_string("../input/data.csv").unwrap(), '
        '"value\\n17\\n"); println!("rust sibling data: 17"); }\n')
    run("rustc", str(analysis / "main.rs"), "-o", str(analysis / "rust-smoke"))
    run(str(analysis / "rust-smoke"), cwd=analysis)
    # Native document-relative resources and explicit code cwd; no new path policy.
    body = '''
![literal sentinel](../input/sentinel.png)

```{r}
x <- read.csv("../input/data.csv")
stopifnot(identical(x$value[[1]], 17L))
cat("SIBLING-DATA-17")
knitr::include_graphics("../input/sentinel.png")
```
'''
    outputs = root / "rendered"
    outputs.mkdir()
    for renderer in ("rmarkdown", "quarto"):
        extension = "Rmd" if renderer == "rmarkdown" else "qmd"
        source = analysis / f"report.{extension}"
        for fmt in ("html", "pdf"):
            output = outputs / f"{renderer}.{fmt}"
            if renderer == "rmarkdown":
                source.write_text('---\ntitle: "Image smoke"\n---\n' + body)
                # R Markdown uses Quarto's bundled Pandoc, as it does in this base.
                run("Rscript", "-e", '''args <- commandArgs(TRUE)
options(tinytex.install_packages=FALSE)
format <- if (args[3] == "html") rmarkdown::html_document(self_contained=TRUE) else rmarkdown::pdf_document()
rmarkdown::render(args[1], output_format=format, output_file=basename(args[2]),
  output_dir=dirname(args[2]), knit_root_dir=dirname(args[1]), quiet=FALSE)
''', str(source), str(output), fmt, cwd=analysis)
            else:
                source.write_text('---\ntitle: "Image smoke"\nformat:\n'
                                  '  html:\n    embed-resources: true\n'
                                  '  pdf:\n    latex-auto-install: false\n---\n' + body)
                run("quarto", "render", str(source), "--to", fmt,
                    "--execute-dir", str(analysis), "--output", f"quarto.{fmt}", cwd=analysis)
                shutil.copy2(analysis / f"quarto.{fmt}", output)

    # Inspect relocated artifacts with the entire source/input tree unavailable.
    portable = Path(temporary) / "portable"
    shutil.copytree(outputs, portable)
    hidden = root.with_name("source-unavailable")
    root.rename(hidden)
    for renderer in ("rmarkdown", "quarto"):
        html = (portable / f"{renderer}.html").read_text()
        assert "SIBLING-DATA-17" in html, renderer
        assert Images(html).payloads.count(png) >= 2, f"{renderer}: missing actual embedded PNG bytes"
        pdf = portable / f"{renderer}.pdf"
        run("qpdf", "--check", str(pdf))
        assert "SIBLING-DATA-17" in run("pdftotext", str(pdf), "-"), renderer
        prefix = portable / f"{renderer}-image"
        run("pdfimages", str(pdf), str(prefix))
        images = list(portable.glob(f"{renderer}-image-*.ppm"))
        matches = 0
        for image in images:
            data = image.read_bytes()
            header = re.match(rb"P6\s+(?:#[^\n]*\n\s*)*32\s+24\s+255\s", data)
            if header and data[header.end():] == rgb:
                matches += 1
        assert matches >= 2, f"{renderer}: missing literal/knitr RGB sentinel in PDF ({matches})"
    shutil.copytree(portable, EVIDENCE / "rendered", dirs_exist_ok=True)
print("PASS: Rust/Python sibling data; R Markdown and Quarto HTML/PDF data and image payloads")
(EVIDENCE / "PASS.txt").write_text("All toolchain smokes passed; no projcli/projr parity claim.\n")
