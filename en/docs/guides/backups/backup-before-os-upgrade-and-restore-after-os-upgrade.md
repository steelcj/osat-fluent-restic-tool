# Backup before OS Upgrade and Restore after OS Upgrade

* Backup with restic
* Manually backup ~/.private (using sudo)
* Do restore test for ~/.ssh to ~/.ssh-restore
* Install clean OS

## Before upgrading your OS

### Do a restore test

A backup only counts if you can restore from it. Try it now with one file:

Create a timestamp var

```bash
export TIMESTAMP="$(date +"%Y-%m-%d--%H:%M:%S")"
echo $TIMESTAMP
```

Test restore to archives /tmp

```bash
restic restore latest --target /tmp/$TIMESTAMP/.ssh --include ~/.ssh
```

Confirm

```bash
ls -al /tmp/$TIMESTAMP/.ssh/${HOME}/.ssh
```

Open and check a restored file. If it works, your safety net is functioning as it should and is real.

```bash
cat /tmp/$TIMESTAMP/.ssh/${HOME}/.ssh/id_ed25519.pub
```

Cleanup

```bash
rm -R /tmp/$TIMESTAMP
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