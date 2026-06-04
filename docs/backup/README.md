

# README

This folder contains configuration files and scripts for automating backups using **rsnapshot**, a filesystem snapshot utility based on `rsync`.

## Contents

- **`rsnapshot.conf`**: The main configuration file for `rsnapshot`. It specifies backup intervals, retention policies, and the directories or systems to back up.
- **`cron`**: A cron job script that schedules `rsnapshot` to run at specified intervals.

## Optional: back up Docker named volumes

`rsnapshot.conf` includes a commented line (232):

```
#backup	/var/lib/docker/volumes/	localhost/
```

Uncomment it to also back up the Docker named volumes (QuestDB, Grafana, Claude session/config). It's **optional** — by default only `/home`, `/etc`, `/usr/local`, `/usr/share`, and `/opt` are backed up.


## Additional Resources

- rsnapshot [Documentation](http://rsnapshot.org/) 
- Cron How-To: [Cron Tutorial](https://help.ubuntu.com/community/CronHowto)