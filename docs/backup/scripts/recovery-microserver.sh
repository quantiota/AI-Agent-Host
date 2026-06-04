#sudo bash -x recovery-microserver.sh

#!/bin/bash

rm -rf /home /opt
cp -pr /backup/rsnapshot/hourly.0/localhost/home /
cp -pr /backup/rsnapshot/hourly.0/localhost/opt /

