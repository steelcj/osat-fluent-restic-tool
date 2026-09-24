# run a backup

```bash
export RESTIC_REPOSITORY="/media/initial/512GB/backups/flow"
export RESTIC_PASSWORD_FILE="${HOME}/.private/restic-tool/password.txt"
```

### Setup a Keep and Clean Policy

The keep-and-clean policy for this target (see [Keeping your backups healthy](#keeping-your-backups-healthy) below):

```sh
export RESTIC_FORGET_OPTS="--keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune"
```

### 

### Activate a target before running restic

Unlike restic's own binary version (managed separately by `install-restic.py --switch`), a target is activated just by sourcing its `env` file in your current shell:

```bash
source ~/.config/restic-tool/env/flow/512GB/env
```

### Run a small backup test

This creates the vault (restic calls it a repository). Now do a tiny test backup, look at it, and check it:

```bash
restic backup ~/.config/restic-tool
```

Output example

```bash
repository b93a0b7e opened (version 2, compression level auto)
using parent snapshot d846dc21
[0:00] 100.00%  12 / 12 index files loaded

Files:           0 new,     0 changed,     4 unmodified
Dirs:            0 new,     7 changed,     0 unmodified
Added to the repository: 2.976 KiB (2.141 KiB stored)

processed 4 files, 552 B in 0:01
snapshot 38340bc3 saved
```

### Snapshots

```bash
restic snapshots
```

Output:

```bash
repository b93a0b7e opened (version 2, compression level auto)
ID        Time                 Host        Tags        Paths                              Size
-----------------------------------------------------------------------------------------------------
d846dc21  2026-07-18 14:27:17  flow                    /home/initial/.config/restic-tool  552 B
cfec250e  2026-07-18 14:30:21  flow                    /home/initial                      243.304 GiB
38340bc3  2026-07-21 08:02:25  flow                    /home/initial/.config/restic-tool  552 B
-----------------------------------------------------------------------------------------------------
Timestamps shown in local time
3 snapshots
```

### Restic check

```bash
restic check
```

Output example

```bash
using temporary cache in /tmp/restic-check-cache-3588666014
create exclusive lock for repository
repository b93a0b7e opened (version 2, compression level auto)
created new cache in /tmp/restic-check-cache-3588666014
load indexes
[0:00] 100.00%  13 / 13 index files loaded
check all packs
117 additional files were found in the repo, which likely contain duplicate data.
This is non-critical, you can run `restic prune` to correct this.
check snapshots, trees and blobs
[0:02] 100.00%  3 / 3 snapshots
no errors were found
```

Notice this part of the message:

```bash
117 additional files were found in the repo, which likely contain duplicate data.
This is non-critical, you can run `restic prune` to correct this.
```

### Reatic prune

#### Prune dry run

```bash
restic prune --dry-run
```

Output example:

```bash
repository b93a0b7e opened (version 2, compression level auto)
[0:00] 100.00%  18 / 18 index files loaded
loading all snapshots...
finding data that is still in use for 17 snapshots
[0:06] 100.00%  17 / 17 snapshots
searching used packs...
collecting packs for deletion and repacking
[0:00] 100.00%  14612 / 14612 packs processed

Would have made the following changes:

to repack:         20194 blobs / 68.812 MiB
this removes:          0 blobs / 0 B
to delete:             0 blobs / 0 B
total prune:           0 blobs / 0 B
remaining:        821967 blobs / 241.804 GiB
unused size after prune: 247.955 MiB (0.10% of remaining size)
```

#### Running the prune

```bash
restic prune
```

Output example:

```bash
repository b93a0b7e opened (version 2, compression level auto)
[0:00] 100.00%  18 / 18 index files loaded
loading all snapshots...
finding data that is still in use for 17 snapshots
[0:05] 100.00%  17 / 17 snapshots
searching used packs...
collecting packs for deletion and repacking
[0:00] 100.00%  14612 / 14612 packs processed

to repack:         20194 blobs / 68.812 MiB
this removes:          0 blobs / 0 B
to delete:             0 blobs / 0 B
total prune:           0 blobs / 0 B
remaining:        821967 blobs / 241.804 GiB
unused size after prune: 247.955 MiB (0.10% of remaining size)

repacking packs
[0:02] 100.00%  15 / 15 packs repacked
rebuilding index
[0:00] 100.00%  19 / 19 indexes processed
[0:00] 100.00%  7 / 7 old indexes deleted
removing 15 old packs
[0:00] 100.00%  15 / 15 files deleted
done
```

### restic check after prune

```bash
restic check
```

Output example

```bash
restic check
```

### restic backup

If `check` says everything is fine, do your first real backup, using the exclude list from your target's folder:

```bash
restic backup ~ --exclude-file ~/.config/restic-tool/env/flow/512GB/excludes
```

Output example

```bash
repository b93a0b7e opened (version 2, compression level auto)
using parent snapshot 13d47edb
[0:00] 100.00%  16 / 16 index files loaded
error: open /home/initial/.private/restic/password.txt: permission denied

Files:       19120 new, 11235 changed, 1093133 unmodified
Dirs:         1825 new,  2273 changed, 154242 unmodified
Added to the repository: 2.138 GiB (1.564 GiB stored)

processed 1123488 files, 323.726 GiB in 0:44
snapshot 161aa773 saved
Warning: at least one source file could not be read
```

**Notice**: Because of the restricted permissions on our `/home/initial/.private/something/secret.txt`this is not backed up.

### Second restic backup

After the first full backup is created , later backups are much faster as only the changes are backed up

```bash
restic backup ~ --exclude-file ~/.config/restic-tool/env/flow/512GB/excludes
```

Output example:

```bash
repository b93a0b7e opened (version 2, compression level auto)
using parent snapshot 976e96fc
[0:00] 100.00%  11 / 11 index files loaded
error: open /home/initial/.private/restic/password.txt: permission denied

Files:       73121 new, 10881 changed, 833548 unmodified
Dirs:         6455 new,  1621 changed, 124436 unmodified
Added to the repository: 46.168 GiB (45.117 GiB stored)

processed 917550 files, 272.093 GiB in 3:22
snapshot d853935b saved
Warning: at least one source file could not be read
```

## Restore Check

Prove that can recover files back

A backup only counts if you can restore from it. Try it now with one file:

```bash
restic restore latest --target /tmp/restore-test --include ~/Documents/output.pdf
```

Confirm

```bash
ls -al /tmp/restore-test/home/initial/Documents/
```

output:

```bash
total 132
drwxr-xr-x 2 initial initial   4096 May 13 08:19 .
drwxr-xr-x 3 initial initial   4096 Jul 21 00:15 ..
-rw-rw-r-- 1 initial initial 125597 Mar  6 09:40 output.pdf
```

Open and check the restored file. If it works, your safety net is functioning as it should and is real.

## 