# Use the specified base image
FROM codercom/code-server:4.113.0

# Switch to root user for permissions
USER root

# Update system and install Python
RUN apt-get update && apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---- Python virtual environment (PEP 668 compliant) ----
RUN python3 -m venv /opt/venv

# Make venv the default Python
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip inside venv
RUN pip install --upgrade pip

# Copy requirements and install them
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt



# Create and set permissions for Claude directories
RUN mkdir -p /home/coder/.claude /home/coder/.config/claude-code && \
    chown -R coder:coder /home/coder/.claude /home/coder/.config && \
    chmod -R u+rwX /home/coder/.claude /home/coder/.config

# Switch to coder user
USER coder

# Install Claude Code via native installer
RUN curl -fsSL https://claude.ai/install.sh | bash


# Install VS Code extensions

RUN code-server --install-extension ms-toolsai.jupyter@2025.9.1 \
    		--install-extension ms-toolsai.vscode-jupyter-powertoys \
    		--install-extension ms-python.python