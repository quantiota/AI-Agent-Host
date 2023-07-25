## How to test

The AI Agent Host was tested on Ubuntu 22.04. No other Linux distributions have been tested, but the instructions should be reasonably straightforward to adapt.

When testing the AI Agent Host, you can expect several types of test results depending on the specific aspects you are testing. Here are some common types of test results you might encounter:

1. **Successful deployment**: This result indicates that your Docker Compose configuration successfully deploys and starts all the services defined in your configuration file. It means that the containers are running, and the services are accessible as expected.

2. **Connectivity tests**: These tests verify whether the services within your Docker Compose setup can communicate with each other. They ensure that the networking between the containers is properly configured, and the services can interact as intended.

3. **Functional tests**: These tests assess the functionality of the services running within the Docker Compose setup. For example, if you have a web application container, you might test whether it responds correctly to HTTP requests, processes user input, and produces the expected output. Additionally, you can add the possibility to run notebooks as part of your functional tests. For instance, if your Docker Compose setup includes a Jupyter Notebook, you can design tests that execute specific notebook cells or workflows and verify the expected results. This allows you to validate the functionality of your notebooks and ensure that they produce the desired outcomes when running within the Docker Compose environment. Running notebooks as functional tests can help you ensure the correctness and reliability of your data processing, analysis, or machine learning workflows encapsulated in the notebooks within the Docker Compose environment.

4. **Integration tests**: These tests evaluate how well the different services integrated within your Docker Compose configuration work together. They validate whether the services can cooperate and exchange information or perform complex tasks as expected.

5. **Performance tests**: These tests focus on assessing the performance characteristics of your Docker Compose setup. They might involve measuring response times, throughput, resource utilization, or scalability under different workloads or stress conditions.

6. **Error handling tests**: These tests check how your Docker Compose configuration handles various error scenarios. For example, you might deliberately simulate a service failure and observe if the system gracefully recovers or if error conditions are properly handled.

7. **Security tests**: These tests assess the security posture of your Docker Compose setup. They might involve vulnerability scanning, penetration testing, or checking for misconfigurations that could expose your services to potential threats.

The specific test results you will obtain depend on the test cases you execute and the quality of your Docker Compose configuration. It's important to design and execute a comprehensive set of tests to ensure the reliability, performance, and security of your Dockerized application.

## Getting Started

To test the AI Agent Host, follow these steps:

1. Set up or use an existing environment with [Docker](https://github.com/quantiota/AI-Agent-Farm/tree/master/doc/webapps/docker) installed.

2. Clone the AI Agent Host repository and navigate to the docker directory.
```
git clone https://github.com/quantiota/AI-Agent-Host.git
cd AI-Agent-Host/docker

```













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

