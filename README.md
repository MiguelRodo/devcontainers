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
  "image": "ghcr.io/miguelrodo/devcontainers:v1.0.0",
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