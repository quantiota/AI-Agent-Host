
# Claude Code Integration for AI Agent Host

This folder contains the files needed to integrate **Claude Code** into the AI Agent Host by extending the existing Code-Server container.  

It enables Claude Code to directly interact with Code-Server, QuestDB and Grafana over the internal Docker network, while preserving the AI Agent Host as an **agentic environment**.

To apply this integration, replace the corresponding files in the main `docker` directory with the updated versions provided here.


## Why This Environment Is Unique

This agentic environment is uncommon. Most AI deployments operate in:

**Typical AI environments:**
- Text-only conversational interfaces
- Read-only code analysis
- Sandboxed execution with limited capabilities
- Interactions mediated through frameworks or APIs with restrictions

**Key differences in this environment:**
- **Direct system access** – Bash execution, file modification, and network calls are permitted.
- **Multi-container orchestration** – Services communicate directly over the Docker network.
- **Persistent state changes** – Actions can permanently alter the system.
- **No strict sandboxing** – Real database operations and file modifications are possible.
- **Infrastructure control** – Interaction with production-like services is supported.

This level of autonomy and system access is generally limited to:
- Senior developers with full system privileges
- DevOps automation workflows
- CI/CD pipelines
- Infrastructure-as-code tools

In most AI environments, it is not possible to:
- Execute live `curl` requests against databases
- Modify running services
- Perform system-level operations with real-world impact

This configuration enables **true autonomous task execution** rather than limited, sandboxed demonstrations.
