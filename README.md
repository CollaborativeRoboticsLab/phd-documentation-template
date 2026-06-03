# VSCode LaTeX Template

[![License](https://img.shields.io/badge/License-BSD-yellow)](./LICENSE)
[![Template Repository](https://img.shields.io/badge/Use-Template-purple)](https://github.com/mik-p/vscode-latex-template)

A lightweight LaTeX Publication repository template with VS Code support and a dev container for building PDFs consistently.

## 🚀 Getting started

1. Install Visual Studio Code.
2. Install the `Remote - Containers` extension.
3. Open this repository in VS Code.
4. Open the Command Palette and choose `Dev Containers: Reopen in Container`.

## ⚙️ VS Code LaTeX editor setup

Recommended extension:

- `LaTeX Workshop` (`james-yu.latex-workshop`)

Recommended workflow:

- Open `main.tex`.
- Use the LaTeX Workshop build commands from the editor.
- The default PDF output directory is `build/`.

### ⚡ Recommended settings

These settings are configured automatically when you open the dev container:

- `latex-workshop.latex.autoBuild.run`: `onFileSave`
- `latex-workshop.latex.outDir`: `build`

## 🐳 Dev container support

This repository includes a `.devcontainer/` configuration that installs a complete LaTeX toolchain for VS Code.

Included packages:

- `latexmk`
- `biber`
- `chktex`
- `texlive-latex-extra`
- `texlive-bibtex-extra`
- `texlive-xetex`
- common LaTeX fonts and English language support

### 📖 How to use

1. Open the repo in VS Code.
2. Run `Dev Containers: Reopen in Container`.
3. Wait for the container to build.
4. Edit `main.tex` and build the PDF using LaTeX Workshop.

## 📝 Template repository notes

This repository is intended as a reusable LaTeX template for academic writing.

- Use it as a GitHub template repository by clicking the "Use this template" button.
- Keep the source files in the repository and generate build artifacts in the `build/` folder.
