# VSCode LaTeX Template

[![License](https://img.shields.io/badge/License-BSD-yellow)](./LICENSE)
[![Template Repository](https://img.shields.io/badge/Use-Template-purple)](https://github.com/mik-p/vscode-latex-template)

This is a fork of [CollaborativeRoboticsLab/vscode-latex-template](https://github.com/CollaborativeRoboticsLab/vscode-latex-template) specifically tailored for research documentation and academic writing.

## Why this template exists

When working on a research project, it is essential to maintain a clear and organized structure for documentation, experiments, and publications. 

One unique issue we face is that, since we work on multiple documents such as theses and research papers simultaneously, the source of truth for the research content can change frequently, making it challenging to keep all documents consistent and up-to-date. Consider the following scenario:

- You start working on your thesis and complete introduction, literature review, and first contribution sections.
- Then, you begin writing a research paper based on the same content. At this stage, the source of truth is the `Thesis`
- You submit the paper and gets the review feedback, which may required updating the paper accordingly.
- Paper gets accepted and now the source of truth may shift to the `Paper`, requiring updates to the thesis as well.
- Without a structured template and clear organization, it becomes cumbersome to keep both documents consistent and up-to-date.

This template aims to address this issue by providing a well-structured environment for managing multiple research documents, ensuring consistency and ease of updates across all related files.

Also this repo aims to be github-copilot friendly, providing a structure that allows,

- For content and language suggestions while writing research documents.
- For code suggestions and automation while writing LaTeX documents.
- Agentic capabilities for managing and updating multiple research documents efficiently.

## Prerequisites

1. Install Visual Studio Code.
2. Install the `Remote - Containers` extension.
3. Open this repository in VS Code.
4. Open the Command Palette and choose `Dev Containers: Reopen in Container`.
5. Ensure that the container has added `LaTeX Workshop` (`james-yu.latex-workshop`) extension.

## Project structure

- `thesis` folder is dedicated for the thesis documentation. This is maintained in both markdown and latex formats.

```text
thesis/
├── bibliography.bib
├── latex/
│    ├── main.tex
│    ├── prepages/
│    ├── abstract.tex
│    ├── introduction.tex
│    ├── literature/
│    │    ├── introduction.tex
│    │    ├── related_work.tex
│    │    └── summary.tex
│    ├── contribution_1/
│    │    ├── introduction.tex
│    │    ├── literature.tex
│    │    ├── methodology.tex
│    │    ├── implementation.tex
│    │    └── results.tex
│    ├── contribution_2/
│    │    ├── introduction.tex
│    │    ├── literature.tex
│    │    ├── methodology.tex
│    │    ├── implementation.tex
│    │    └── results.tex  
│    ├── contribution_3/
│    │    ├── introduction.tex
│    │    ├── literature.tex
│    │    ├── methodology.tex
│    │    ├── implementation.tex
│    │    └── results.tex
│    ├── conclusion.tex
│    └── postpages/
│
└──  markdown/
     ├── main.md
     ├── introduction.md
     ├── literature.md
     ├── contribution_1/
     │    ├── introduction.md
     │    ├── literature.md
     │    ├── methodology.md
     │    ├── implementation.md
     │    └── results.md
     ├── contribution_2/
     │    ├── introduction.md
     │    ├── literature.md
     │    ├── methodology.md
     │    ├── implementation.md
     │    └── results.md  
     ├── contribution_3/
     │    ├── introduction.md
     │    ├── literature.md
     │    ├── methodology.md
     │    ├── implementation.md
     │    └── results.md
     └── conclusion.md
```

- `papers` folder is intended for storing research papers in latex format. Depending on the conference or journal, the style files (`.sty`) and formatting requirements may vary.

```text
papers/
├── paper_1/
│    ├── style.sty
│    ├── main.tex
│    └── bibliography.bib
├── paper_2/
│    ├── style.sty
│    ├── main.tex
│    └── bibliography.bib
└── paper_3/
     ├── style.sty
     ├── main.tex
     └── bibliography.bib
```
    
- `paper_experiments` folder is intended for storing git repos linked with each paper's experimental results and related files. Since these are git repositories, each repo is maintained separately and linked to the paper it corresponds to. Within this workspace, these repos are treated as submodules.

```text
paper_experiments/
├── paper_1/
├── paper_2/
└── paper_3/
```

use git submodules to link the experimental repositories with the corresponding papers.

```bash
cd paper_experiments
git submodule add https://github.com/CollaborativeRoboticsLab/Academic-project-page-template.git
```


## Clone this repository as a private repository

### Method: Using GitHub's Import Tool

This approach uses GitHub's built-in web interface to duplicate the public repository directly into a new private repository without using the command line.

1. **Log in** to your account on [GitHub](https://github.com).
2. Navigate directly to the [GitHub Repository Import Page](https://github.com/new/import).
3. **Paste the URL** of this repository into the box labeled **"Your old repository’s clone URL"**.
4. **Name your new repository** and ensure you select **Private** for the visibility level.
5. Click **Begin Import** and wait for GitHub to complete the duplication process.

Once the import tool finishes, clone your brand-new private repository to your local computer to begin working on it:

```bash
git clone https://github.com/your-username/your-private-repo.git
```

### How to Sync Future Changes from the this Public Repository

Because your new private repository is a duplicate rather than an official GitHub fork, the web interface will not display a "Sync Fork" button. You must use the command line to pull updates from the original public repository.

### 1. Link the Original Repository
Move into your local repository folder and add the original public repository as a remote source named `upstream`:

```bash
cd your-private-repo
git remote add upstream https://github.com/CollaborativeRoboticsLab/phd-documentation-workspace-template.git
```

### 2. Verify Your Remotes

Ensure that both your private copy (`origin`) and the original project (`upstream`) are properly listed:
```bash
git remote -v
```

### 3. Pull and Push Updates
Whenever you need to bring in updates from the original project's main branch, run the following commands:

```bash
# Fetch and merge the latest changes from the public repo
git pull upstream main

# Push those updates to your private GitHub repository
git push origin main
```