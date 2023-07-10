# Docker

You will find all the Docker services set up in this folder.

## Services

### VSCode

:link: [docker image](https://hub.docker.com/r/codercom/code-server)
:link: [github repository](https://github.com/coder/code-server)

Access VSCode through [localhost:8080](http://localhost:8080).

:lock:
The password to access VSCode is `yourpassword` it can be set it in the [docker-compose.yaml file](docker-compose.yaml).

### QuestDB

:link: [docker image](https://hub.docker.com/r/questdb/questdb)
:link: [github repository](https://github.com/questdb/questdb)
:link: [questdb Docker documentation](https://questdb.io/docs/get-started/docker/)

Access QuestDB GUI through [localhost:9000](http://localhost:9000).
Access the database using [localhost:8812](http://localhost:8812).

:lock:
The user/password are the default one: `admin:quest` ([see the documentation](https://questdb.io/docs/reference/configuration/#postgres-wire-protocol)) and the database name is `qdb`.

### Grafana

:link: [docker image](https://hub.docker.com/r/grafana/grafana)
:link: [github repository](https://github.com/grafana/grafana)

Access Grafana through [localhost:3000](http://localhost:3000).

:lock:
The user/password are the default one: `admin:admin`.
You can add set the password adding the environment variable `GF_SECURITY_ADMIN_PASSWORD`.

:wrench: To configure Grafana, follow [this documentation](./grafana/README.md).

## Usage



### 1 Setup Environment Variables

First, you will want to create an .env file in the docker folder with the following variables:

```
DOMAIN=yourdomain.tld

PASSWORD=yourpassword
GRAFANA_QUESTDB_PASSWORD=quest
QDB_PG_USER=admin
QDB_PG_PASSWORD=quest

```
Remember to replace the values of the variables with your actual passwords and usernames. 

### 2 Generate dhparam.pem file

The **dhparam.pem** file is used for Diffie-Hellman key exchange, which is part of establishing a secure TLS connection. You can generate it with OpenSSL. Here's how to generate a 2048-bit key:

```
openssl dhparam -out ./nginx/certs/dhparam.pem 2048
```

Please note that generating a dhparam file can take a long time. For a more secure (but slower) 4096-bit key, simply replace 2048 with 4096

### 3 Generate .htpasswd file

The **.htpasswd** file is used for basic HTTP authentication. You can create it using the **htpasswd** utility, which is part of the Apache HTTP Server package. Here's how to create an **.htpasswd** file with a user named **yourusername**:
```
htpasswd -c ./nginx/.htpasswd yourusername
```
This command will prompt you for the password for **yourusername**. The **-c** flag tells **htpasswd** to create a new file. **Caution**: Using the **-c** flag will overwrite any existing **.htpasswd** file.

If **htpasswd** is not installed on your system, you can install it with **apt** on Ubuntu:

``````
sudo apt-get install apache2-utils

``````


You can up the stack using the command:

```
docker-compose up
```
