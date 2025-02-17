On modern Ubuntu the build-in backup tool is Duplicity. Under the hood it uses Deja-dup.

When Duplicity is running, this is what is executed:

```bash 
/usr/bin/python3.12 /usr/bin/duplicity --log-fd=30 incremental --dry-run \
  --include=/home/paul/.cache/deja-dup/metadata --exclude=/home/paul/snap/*/*/.cache \ 
  --exclude=/home/paul/.var/app/*/cache --include=/home/paul/mnt/bigData 
  --exclude=/home/paul/.local/share/Trash --exclude=/home/paul/.xsession-errors 
  --exclude=/home/paul/.cache/deja-dup --exclude=/home/paul/.cache --include=/home/paul 
  --exclude=/sys --exclude=/run --exclude=/proc --exclude=/dev --exclude=/var/tmp 
  --exclude=/tmp --exclude=/media/paul/backUpDrive2025/backup-2025-02-14 
  --exclude=** --exclude-if-present=CACHEDIR.TAG --exclude-if-present=.deja-dup-ignore 
  --volsize=200 / gio+file:///media/paul/backUpDrive2025/backup-2025-02-14 
  --verbosity=9 --timeout=120 --archive-dir=/home/paul/.cache/deja-dup --tempdir=/tmp
```

Well, you're not 'paul' and your devices will be different.

The key thing the `deja-dup-ignores.py` will do utilize `--exclude-if-present=.deja-dup-ignore` to mark 
some more things as not-to-backup.  As someone who develops, I would kike to skip Git clones that are no
different to origin/main, any recreatable build dirs (maven's `target` etc), and package libraries which 
can be gotten again by `npm install` and alike. This script attempts to 
do that. You would run it for you home directory before using Duplicity (which uses deja-dup). A faster 
backup is the goal.

If you're using Restic instead to backup, tack the following on to the backup sub-command:

```
--exclude-if-present=.deja-dup-ignore
```

Oh, and you might want to put `.deja-dup-ignore` in your global `~/.gitignore` file
