# marimo-quarto

  > Dependencies: All you need is Nix (Look at the relevant hashbangs)
  > Without Nix, problably `quarto`, `flask`, `marimo`

```mermaid
graph TD
    A[run.sh] --Spawns (server.py)--> B[Flask server]
    A --> C[Runs Quarto (_extension/marimo/quarto)]
    C --> F1[Filter 1: marimo-register]
    subgraph F1
        D[`marimo-register:CodeBlock`]
        E[`marimo-register:Pandoc`]
    end
    D --sends cells to build--> B[Builds all the cells]
    D --replaces: `{marimo}` code blocks with {marimo-id} stubs--> E
    E --Signals server to run on cell objects--> B
    F1 --> F2[Filter 2: marimo-execute]
    subgraph F2
        G[`marimo-execute:CodeBlock`]
        H[`marimo-execute:Pandoc`]
    end
    B --Sends code outputs--> G
    G --Replaces stubs with outputs--> H
    H -->Provides relevant HTML headers to make things work--> I[Out]
```

Run `run.sh`. This spawns the Flask server in `server.py` and runs a quarto action.
Documents that specify the `marimo/quarto` extension e.g.

```yml
---
title: Marimo Tutorial
format: html
filters:
  - marimo/quarto
---
```

call the relevant extension in `_extension/marimo/quarto`. Here there are 2
filters `marimo-register` and `marimo-execute`. `marimo-register:CodeBlock`
sends cells to the Flask server to be built and replaces `{marimo}` code blocks
with `{marimo-id}` stubs, and after all cells have been run
`marimo-register:Pandoc` signals the server to run on cell objects.
`marimo-execute:CodeBlock` receives the code outputs from the server and
replaces the stubs with these outputs, and `marimo-execute:Pandoc` provides the
relevant HTML headers to make everything work correctly.

## Other
see `convert.py` that naively changes a marimo python file to a quarto file.

---
adapted from https://github.com/awesome-panel/holoviz-quarto
