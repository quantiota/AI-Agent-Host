# === Productivity tools (PDF) ===

USER root

# In your existing docker/vscode/Dockerfile, add Pandoc + Poppler + LaTeX: 
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    pandoc \
    poppler-utils \
    texlive \
    texlive-latex-extra && \
    rm -rf /var/lib/apt/lists/*
# end

USER coder