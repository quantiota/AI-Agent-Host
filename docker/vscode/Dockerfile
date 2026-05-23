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


# Switch to coder user
USER coder


# Install VS Code extensions

RUN code-server --install-extension ms-toolsai.jupyter@2023.9.100 \
    		--install-extension ms-toolsai.vscode-jupyter-powertoys \
    		--install-extension ms-python.python