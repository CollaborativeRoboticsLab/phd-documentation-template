FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    texlive-latex-extra \
    texlive-lang-english \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-bibtex-extra \
    texlive-xetex \
    latexmk \
    biber \
    chktex \
    make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
