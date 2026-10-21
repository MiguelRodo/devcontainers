# devcontainers

Semantically versioned, pre-built [dev containers](https://containers.dev/) intended to be used as the base for other project devcontainers.

## Available containers

| Branch | Description | Image |
|--------|-------------|-------|
| `main` | Default R-focused container (BioConductor base, Quarto, renv) | `ghcr.io/miguelrodo/devcontainers:<tag>` |
| `<name>` | Branch name describes the container (e.g. `python`) | `ghcr.io/miguelrodo/devcontainers-<name>:<tag>` |

## How to use

Add a `.devcontainer/devcontainer.json` to your project referencing the desired image. For example:

```json
{
  "image": "ghcr.io/miguelrodo/devcontainers-main:v1.3.0",
  "customizations": {
    "vscode": {
      "extensions": [
        "quarto.quarto",
        "mathematic.vscode-pdf"
      ]
    }
  }
}
```

This works with both VS Code and [Positron](https://github.com/posit-dev/positron).

## Adding or updating a container

Images are built and stored in this repository's GitHub Container Registry using the [`MiguelRodo/actions/prebuild-devcontainer`](https://github.com/MiguelRodo/actions) GitHub Action. A new image is built and published whenever a tag is pushed.

- **Default (`main`) container:** push a tag matching `v*` (e.g. `v1.0.1`). Always increment the version.
- **New container:** create a branch whose name reflects the container's purpose (e.g. `python`), then push a tag matching `<branch>-v*` (e.g. `python-v1.0.0`).

## License

[MIT](LICENSE) © Miguel Julio Rodo
## projcli development and diagnostic variant

The long-lived `projcli` branch defines this variant. It reuses main's
`bioconductor/bioconductor_docker:RELEASE_3_23` base, non-root `rstudio` user,
common-utils/build-info and Rocker apt/Quarto features. It adds stable Rust via
checksum-verified rustup, C/C++ build tools, Python 3/venv, knitr/rmarkdown and
Poppler/qpdf. Quarto 1.10.19 matches projcli's existing renderer diagnostics;
its bundled Pandoc and TinyTeX supply HTML/PDF rendering without full TeX Live.
Rocker's r-packages feature installs the two explicit R packages without a
project/cache restoration framework. No CMDStan, full OS upgrade or unrelated
repository/bootstrap tools are added. This is a large existing R base, not a
new claim of a minimal image. Only Linux x86-64 is exercised in CI.

The standard Rust feature requests ptrace and unconfined seccomp. The small
Dockerfile installs the official toolchain instead, without extra container
capabilities, security overrides, host mounts, Docker socket or credentials.
The context is `.devcontainer`; it contains no source/home/authentication COPY.
Codex is not installed or authenticated. Users handle that later themselves.

### Remote validation

The `projcli image smoke` PR workflow uses the same pinned `devcontainers/ci`
action as the publication action, with `push: never` and read-only permissions.
It runs `python3 tests/smoke.py` inside the resulting container as `rstudio`.
All Docker builds, Rust compilation and R/Quarto/PDF renders must stay on CI
while the operator's local machine is memory constrained.

The smoke reads sibling CSV input with Rust, Python and R in a path containing
spaces. It renders R Markdown and Quarto to embedded HTML and PDF with both
literal Markdown and knitr images. After relocating the output and hiding the
entire source tree, it verifies exact embedded PNG bytes in HTML, actual RGB
image pixels extracted from PDF, PDF structure and rendered CSV-derived text.
`smoke-evidence` retains named tool/package versions, commands and output files;
it never dumps environment values or process arguments. These are environment
checks, not projcli path-policy changes or proof of R/IDE/projr parity. No projr
source is installed or modified. See projcli diagnostic commit
`488adaf727668bdd6c3f46c544e3801ce92de24b` for the separate unmerged investigation.

### Publication and updates

Independent review and green exact-head smoke CI precede merge/publication.
Use the existing **Pre-build Dev Container** workflow, selecting workflow ref
`projcli`, `target_branch=projcli`, and initial `version=v1.0.0`. Future builds
use its existing version/bump inputs, never reuse a published version. The
established action publishes `ghcr.io/miguelrodo/devcontainers-projcli:v1.0.0`
and its usual aliases, using only the existing `GITHUB_TOKEN` secret reference.
Do not use an unqualified tag push: the existing workflow's tag fallback names
the main image; explicit branch dispatch removes that ambiguity.

Dependabot must run from default-branch configuration with a `target-branch:
projcli` entry for this variant. Its monthly update PRs target the long-lived
branch and run the same smoke checks; approved updates receive a new image
version through the existing prebuild action. Rust `stable` and TinyTeX resolve
at build time. Quarto's explicit version is an intentional compatibility pin;
review it alongside renderer diagnostics rather than assuming Dependabot
updates feature options. Version evidence plus the final image digest identify
the actual environment; rebuilding a source commit alone is not byte reproducibility.

After publication, obtain the registry digest from the remote build, verify the
published image with this smoke, and pin `image:tag@sha256:...` in projcli's
`.devcontainer/devcontainer.json`. A review-only candidate reference is not yet
a published image or a locally verified devcontainer. No local Docker startup,
Codex authentication, image visibility or repository setting changes are implied.

Ponytail full-mode review: reused the existing base, features, publication action
and Dependabot. Rejected the standard Rust feature's extra permissions; kept
one stdlib smoke instead of importing the broad unmerged path diagnostic.
Payload checks prevent render exit codes or PDF headers from masking missing
images. No production source, path contract or existing R package changes.

The smoke's `workflow_dispatch` is also registered on the default branch by
PR12. It checks out the reviewed long-lived `projcli` branch; supplying its
optional `image` input requires the exact package, SemVer tag and SHA256 digest.
It then consumes that prebuilt image without adding features or publishing.
Use this remote verification after normal publication and before finalizing the
consumer digest. Rendering smokes disable automatic TeX package installation,
so success must come from the image's installed toolchain.

Initial remote build/smoke passed at source head
`653add136713f01f35235e03bd588e98372058e9` in
[Actions run39558670289](https://github.com/MiguelRodo/devcontainers/actions/runs/39558670289).
Recorded versions included Rust/Cargo 1.99.1 stable, Python 3.12.3, R 4.6.1,
knitr 1.52, rmarkdown 2.32, Quarto 1.10.19, Pandoc 3.10 and TinyTeX v2026.10.
Later exact-head checks are required for subsequent changes. This was a
nonpublishing runner build; it supplies no registry digest or local editor claim.
