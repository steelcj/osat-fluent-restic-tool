# Backup before OS Upgrade and Restore after OS Upgrade

* [x] Backup with restic
* [x] Manually backup ~/.private (using sudo)
* [ ] Do restore test for ~/.ssh to ~/.ssh-restore
* [ ] Install clean OS

## Manually backup `~/.private` using sudo

Confirm location

```bash
sudo ls -ld ~/.private
```

Output

```bash
drwx------ 24 initial initial 4096 Sep 23 00:25 /home/initial/.private
```

Verify external drive

```bash
findmnt | grep media
```

Confirmation

```bash
├─/media/initial/512GB                            /dev/sda               ext4            rw,nosuid,nodev,relatime,errors=remount-ro
```

Confirm writable

```bash
sudo touch /media/${USER}/512GB/test
sudo rm /media/${USER}/512GB/test
```

Create archive

```bash
sudo tar \
  --create \
  --zstd \
  --file=/tmp/.private.tar.zst \
  --acls \
  --xattrs \
  --numeric-owner \
  -C ${HOME} \
  .private
```

Confirm contents

```bash
sudo tar \
  --list \
  --zstd \
  --file=/tmp/.private.tar.zst
```

Copy to external drive

```bash
sudo cp \
  --preserve=all \
  /tmp/.private.tar.zst \
  /media/${USER}/512GB/
```

Confirm

```bash
sudo ls -lh /media/${USER}/512GB/.private.tar.zst
```

output: 

```bash
-rw-r--r-- 1 root root 634K Sep 24 14:12 /media/${USER}/512GB/.private.tar.zst
```

Generate and compare checksum:

```bash
sha256sum /tmp/.private.tar.zst
sudo sha256sum /media/${USER}/512GB/.private.tar.zst
```

Before removing the external drive, flush pending writes:

    sync

### Restore the directory

```bash
sudo tar \
  --extract \
  --zstd \
  --file=/media/${USER}/512GB/.private.tar.zst \
  --acls \
  --xattrs \
  --numeric-owner \
  -C ${HOME}/
```

Confirm all owners and permissions

```bash
sudo chown ${USER}:${USER} -R ~/.private
sudo chmod 700 -R ~/.private
sudo ls -al .private/signal/
sudo ls -al .private/restic
```

## Before upgrading your OS

### Do a restore test

A backup only counts if you can restore from it. Try it now with one file:

Create a timestamp var

```bash
export TIMESTAMP="$(date +"%Y-%m-%d--%H:%M:%S")"
echo ${TIMESTAMP}
```

Output example:

```bash
2026-09-24--14:36:12
```

Create archive restoration point

```bash
mkdir ${HOME}/archive/${TIMESTAMP}
```

Test restore of .ssh to archives /tmp

```bash
restic restore latest --target ${HOME}/archive/${TIMESTAMP}/.ssh --include ~/.ssh
```

Confirm

```bash
ls -al ${HOME}/archive/${TIMESTAMP}/.ssh
```

Open and check a restored file. If it works, your safety net is functioning as it should and is real.

```bash
ls -al ~/archive/${TIMESTAMP}/.ssh/${HOME}/.ssh
```

### Complete restore to `${HOME}/archive/${TIMESTAMP}`

```bash
restic restore latest --target "${HOME}/archive/${TIMESTAMP}"
```

## Install or upgrade your OS

Do your clean OS installation or upgrade your OS

## Install Restic Requirements

* git
* python

## Install Restic

## Test restic

## Do you restore

### Set a datetime stamp

```bash
export TIMESTAMP="$(date +"%Y-%m-%d--%H:%M:%S")"
```

#### Confirm

```bash
echo $TIMESTAMP
```

### Restore your backup

#### Archive approach

in order to avoid the temptation to reorganize all of your now that you have a fresh system you might want to consider this approach.

If you restore your data to an dated archive or restore directory then you can reorganize your data only when you need it.

Then the things you never use remain in your archive.

#### Restore point approach

If all of your data is organized well then you might want to restore to a restore directory.

The advantage of this is that any new configuration files created during your OS installation do not get clobber by your old system files and, like in the archive directory example above, all of your files remain readily available when and if you need them.

This is the same approach as the archive method but since your data is already organized you can move all with the exception of configuration files for applications.

### Create you recovery directory

I tend to go with an archive directory as I use the PARA method of organization. This makes it a convenient to reorganize when I need something and see that it is not in the right place.

```bash
mkdir ~/archive
```

#### Set a timestamp

```bash
export TIMESTAMP="$(date +"%Y-%m-%d--%H:%M:%S")"
```

#### Restore your data

You might restore to a directory called archive or restore.

```bash
restic restore latest --target ~/archive/$TIMESTAMP/ --include ~/
```

#### Do some data sanity checks

Ensure that your data is as it should be

```bash
ls -al ~/archive/$TIMESTAMP/
tree ~/archive/$TIMESTAMP/
...
```

## Post restore

Move files out of your archive or restore directory as you needed. This is an efficient time to reorganize them so they are more accessible to you for the work you are currently engaged in.