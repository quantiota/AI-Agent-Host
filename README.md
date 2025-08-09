# AI Agent Host

The AI Agent Host is a module-based environment designed to facilitate rapid experimentation and testing. It includes a docker-compose configuration with QuestDB, Grafana, Code-Server and Nginx. The AI Agent Host provides a seamless interface for managing and querying data, visualizing results, and coding in real-time.

The AI Agent Host is built specifically for `LangChain`, a framework dedicated to developing applications powered by language models. LangChain recognizes that the most powerful and distinctive applications go beyond simply utilizing a language model and strive to be data-aware and agentic. Being `data-aware` involves connecting a language model to other sources of data, enabling a comprehensive understanding and analysis of information. Additionally, being `agentic` allows a language model to actively interact with its environment. The AI Agent Host aligns with these principles and serves as a framework that supports LangChain's vision, providing a module-based environment for seamless data management, visualization, and real-time coding, thereby empowering developers to create advanced language model-driven applications.

## Features

1. **QuestDB**: QuestDB is a high-performance, open-source time-series database. It allows for efficient storage and querying of time-series data, making it ideal for working with real-time data streams.

2. **Grafana**: Grafana is a popular open-source platform for data visualization and monitoring. It provides a rich set of features for creating interactive dashboards and visualizing data from various sources.

3. **Code-Server**: Code-Server is a web-based IDE based on Visual Studio Code. It provides a familiar coding environment with features such as code completion, syntax highlighting, and debugging capabilities.

4. **Nginx**: Nginx is a widely-used web server and reverse proxy server. It enhances the AI Agent Host by providing additional functionality for routing and load balancing, improving performance and security

## Getting Started

To use the AI Agent Host, follow these steps:

1. Set up or use an existing environment with [Docker](https://github.com/quantiota/AI-Agent-Farm/tree/master/doc/webapps/docker) installed.

2. Clone the AI Agent Host repository and navigate to the docker directory.
```
git clone https://github.com/quantiota/AI-Agent-Host.git
cd AI-Agent-Host/docker

```

3. Follow all prerequisite steps that should be completed before bringing the  Docker Stack. Refer to the Docker [Readme](https://github.com/quantiota/AI-Agent-Host/tree/main/docker) file for guidance


4. Launch the AI Agent Host using the provided docker-compose configuration.

```
docker compose up --build -d

```

5. Once the services are up and running, you can access the AI Agent Host interfaces:

- QuestDB: Visit https://questdb.domain.tld in your web browser.
- Grafana: Visit https://grafana.domain.tld in your web browser.
- Code-Server: Visit https://vscode.domain.tld in your web browser.

6. To connect the AI Agent Host to a remote JupyterHub environment from Code-Server:

- Set up or use an existing remote JupyterHub that includes the necessary dependencies for working with your notebooks and data.

- Connect to the remote JupyterHub environment from within the Code-Server interface provided by the AI Agent Host

Start working with your notebooks and data, using the pre-installed tools and libraries that are included in your remote environment.

Here’s a small add-on section you can drop into the README (no other parts changed):

---

## Example: Integrating an AI Agent (Claude Code)

This example shows how to add an **AI agent** to the AI Agent Host **without changing** the core stack. The agent runs in its own service and talks **directly** to Code-Server, QuestDB and Grafana over the internal Docker network, preserving the Host’s role as an **agentic environment**.

### Folder Layout

```
/claude-code/
├─ Dockerfile
└─ docker-compose.yaml   # override/extension for the base stack
```

### What This Adds

* A containerized **Claude Code** service (via `Dockerfile`).
* A **compose override** (`docker-compose.yaml`) that plugs the agent into the same network as QuestDB, Grafana, and Code-Server.

### Service Discovery (no middleware required)

From the agent container, use service names:

* QuestDB REST: `http://questdb:9000`
* QuestDB PG wire: `questdb:8812`
* Grafana API/UI: `http://grafana:3000`

### How to Run (example)

From the `/docker` directory:

```bash
# Bring up the base stack
docker compose up -d

# Then start the agent using the override in /docker/claude-code
docker compose -f docker-compose.yaml -f claude-code/docker-compose.yaml up -d --build
```

### Notes

* Keep credentials in environment variables or Docker secrets (do **not** hard-code).
* Grant the agent **least-privilege** DB access (e.g., read-only when possible).
* This pattern is generic—swap in any agent container while keeping the Host intact.

### AI Agent Host Architecture Diagram

 ![AI Agent Host diagram](./ai-agent-host-diagram.png)
 
:pencil: High resolution diagram [Application architecture diagram](https://raw.githubusercontent.com/quantiota/AI-Agent-Host/master/ai-agent-host-diagram.png)



## References


- Connect to a JupyterHub from Visual Studio Code. [Visual Studio Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks#_connect-to-a-remote-jupyter-server)

- Create an API Token. [JupyterHub](https://jupyterhub.readthedocs.io/en/stable/howto/rest.html#create-an-api-token)

- [Visual Studio Code](https://code.visualstudio.com/)

- [QuestDB - The Fastest Open Source Time Series Database](https://questdb.io/)

- [Grafana - The open observability platform](https://grafana.com/)

- [Langchain](https://python.langchain.com)

