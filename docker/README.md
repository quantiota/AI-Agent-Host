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


### 1 Generate Certificates with Certbot

We will use the Certbot Docker image to generate certificates. This service will bind on ports 80 and 443, which are the standard HTTP and HTTPS ports, respectively. It will also bind mount some directories for persistent storage of certificates and challenge responses. 

If you want to obtain separate certificates for each subdomain, you will need to run the **certbot certonly** command for each one. You can specify the subdomain for which you want to obtain a certificate with the -d option, like this:

```
docker-compose -f init.yaml run certbot certonly -d vscode.yourdomain.tld
docker-compose -f init.yaml run certbot certonly -d questdb.yourdomain.tld
docker-compose -f init.yaml run certbot certonly -d grafana.yourdomain.tld

```
Please note that the **certonly** command will obtain the certificate but not install it. You will have to configure your Nginx service to use the certificate. Additionally, make sure that your domain points to the server on which you're running this setup, as Let's Encrypt validates domain ownership by making an HTTP request.

Also, remember to periodically renew your certificates, as Let's Encrypt's certificates expire every 90 days. You can automate this task by setting up a cron job or using a similar task scheduling service.


```
# /etc/cron.d/certbot: crontab entries for the certbot package (5 am, every monday)
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

 0 5 * * 1 docker-compose run certbot renew

```

### 2 Setup Environment Variables

Firstly, you will want to create an .env file in the docker folder with the following variables:

```
DOMAIN=yourdomain.tld
PASSWORD=yourpassword
GRAFANA_QUESTDB_PASSWORD=quest
QDB_PG_USER=admin
QDB_PG_PASSWORD=quest

```
Remember to replace the placeholders with your actual domain, passwords, and usernames.

The environment variables, specifically ${DOMAIN}, will be replaced directly within the Nginx configuration file when the Docker services are started.

### 3 Generate dhparam.pem file

The **dhparam.pem** file is used for Diffie-Hellman key exchange, which is part of establishing a secure TLS connection. You can generate it with OpenSSL. Here's how to generate a 2048-bit key:

```
openssl dhparam -out ./nginx/certs/dhparam.pem 2048
```

Generating a dhparam file can take a long time. For a more secure (but slower) 4096-bit key, simply replace 2048 with 4096 in the above command.

### 4 Generate .htpasswd file for QuestDB 

The user/password are the default one: admin:admin

The **.htpasswd** file is used for basic HTTP authentication. You can change it using the **htpasswd** utility, which is part of the Apache HTTP Server package. Here's how to create an **.htpasswd** file with a user named **yourusername**:
```
htpasswd -c ./nginx/.htpasswd yourusername
```
This command will prompt you for the password for **yourusername**. The **-c** flag tells **htpasswd** to create a new file. **Caution**: Using the **-c** flag will overwrite any existing **.htpasswd** file. 

If **htpasswd** is not installed on your system, you can install it with **apt** on Ubuntu:

``````
sudo apt-get install apache2-utils

``````


After completing these steps, you can bring up the Docker stack using the following command:

```
docker-compose up
```
This will start all services as defined in your **docker-compose.yaml** file.