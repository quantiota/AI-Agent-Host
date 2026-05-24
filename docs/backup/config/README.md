

# README

This folder contains configuration files and scripts for automating backups using **rsnapshot**, a filesystem snapshot utility based on `rsync`.

## Contents

- **`rsnapshot.conf`**: The main configuration file for `rsnapshot`. It specifies backup intervals, retention policies, and the directories or systems to back up.
- **`cron`**: A cron job script that schedules `rsnapshot` to run at specified intervals.

## Additional Resources

- rsnapshot [Documentation](http://rsnapshot.org/) 
- Cron How-To: [Cron Tutorial](https://help.ubuntu.com/community/CronHowto)