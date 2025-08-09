
# Claude Code Integration for AI Agent Host

This folder contains the files needed to integrate **Claude Code** into the AI Agent Host by extending the existing Code-Server container.  

It enables Claude Code to directly interact with QuestDB and Grafana over the internal Docker network, while preserving the AI Agent Host as an **agentic environment**.

To apply this integration, replace the corresponding files in the main `docker` directory with the updated versions provided here.
