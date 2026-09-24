---
title: "Archive, Copy, and Restore a Directory with sudo" description: "A Linux command-line procedure for archiving a directory, copying the archive to an external drive, and restoring the directory."
---

# Archive, Copy, and Restore a Directory using sudo

This procedure uses `tar` to create a compressed archive, `cp` to copy the archive to an external drive, and `tar` to restore the directory.

The procedure assumes:

- The source directory is `/path/to/directory`.
- The external drive is mounted at `/media/user/external-drive`.
- The archive will be stored as `/media/user/external-drive/directory.tar.zst`.
- The restored directory will be `/path/to/restore/directory`.
- `zstd` compression is available.

Replace these paths with the actual paths for the system.

## 1. Verify the source directory

Confirm the directory exists before creating the archive:

```bash
sudo ls -ld /path/to/directory
```

For additional verification:

```bash
sudo du -sh /path/to/directory
```

## 2. Verify the external drive

Check mounted filesystems:

```bash
findmnt
```

Or check the specific mount point:

```bash
findmnt /media/user/external-drive
```

Verify that the destination is writable:

```bash
sudo touch /media/user/external-drive/.archive-test
sudo rm /media/user/external-drive/.archive-test
```

## 3. Create the archive

Create a compressed `tar` archive:

```bash
sudo tar \
  --create \
  --zstd \
  --file=/tmp/directory.tar.zst \
  --acls \
  --xattrs \
  --numeric-owner \
  -C /path/to \
  directory
```

The `-C /path/to` option is intentional. It causes the archive to contain:

```text
directory/
```

rather than the complete absolute pathname.

This makes the archive safer and more portable to restore.

### Verify the archive

List its contents:

```bash
sudo tar \
  --list \
  --zstd \
  --file=/tmp/directory.tar.zst
```

Check the archive size:

```bash
ls -lh /tmp/directory.tar.zst
```

## 4. Copy the archive to the external drive

Copy the archive:

```bash
sudo cp \
  --preserve=all \
  /tmp/directory.tar.zst \
  /media/user/external-drive/
```

Verify that the copy exists:

```bash
sudo ls -lh /media/user/external-drive/directory.tar.zst
```

For an additional integrity check, calculate a SHA-256 checksum:

```bash
sha256sum /tmp/directory.tar.zst
sudo sha256sum /media/user/external-drive/directory.tar.zst
```

The two checksums should be identical.

## 5. Safely unmount the external drive

Before removing the external drive, flush pending writes:

```bash
sync
```

Then unmount it:

```bash
sudo umount /media/user/external-drive
```

Confirm that it is no longer mounted:

```bash
findmnt /media/user/external-drive
```

No output indicates that the mount point is no longer mounted.

## 6. Mount the external drive again

After reconnecting the drive, identify its mount point:

```bash
findmnt
```

If necessary, mount the filesystem manually:

```bash
sudo mount /dev/sdX1 /media/user/external-drive
```

Replace `/dev/sdX1` with the actual filesystem device.

Verify the archive:

```bash
sudo ls -lh /media/user/external-drive/directory.tar.zst
```

## 7. Restore the directory

Create the parent directory if necessary:

```bash
sudo mkdir -p /path/to/restore
```

Restore the archive:

```bash
sudo tar \
  --extract \
  --zstd \
  --file=/media/user/external-drive/directory.tar.zst \
  --acls \
  --xattrs \
  --numeric-owner \
  -C /path/to/restore
```

The resulting directory will be:

```text
/path/to/restore/directory/
```

Because `tar` is being run with `sudo`, archived ownership information can be restored rather than being mapped to the invoking user's account.

## 8. Verify the restored directory

Check ownership and permissions:

```bash
sudo ls -ld /path/to/restore/directory
```

Inspect the contents:

```bash
sudo ls -la /path/to/restore/directory
```

Check the total size:

```bash
sudo du -sh /path/to/restore/directory
```

If ACLs are important, inspect them with:

```bash
sudo getfacl /path/to/restore/directory
```

If extended attributes are important:

```bash
sudo getfattr -d -m- /path/to/restore/directory
```

## 9. Optional: verify the archive without restoring it

An archive can be tested before restoration:

```bash
sudo tar \
  --extract \
  --zstd \
  --file=/media/user/external-drive/directory.tar.zst \
  --list \
  > /dev/null
```

A successful command with no error indicates that `tar` was able to read the archive.

## Complete workflow

For a simple archive → copy → restore workflow:

```bash
# Variables
SOURCE="/path/to/directory"
PARENT="/path/to"
ARCHIVE="/tmp/directory.tar.zst"
EXTERNAL="/media/user/external-drive"
RESTORE="/path/to/restore"

# Create archive
sudo tar \
  --create \
  --zstd \
  --file="$ARCHIVE" \
  --acls \
  --xattrs \
  --numeric-owner \
  -C "$PARENT" \
  "$(basename "$SOURCE")"

# Copy archive to external drive
sudo cp \
  --preserve=all \
  "$ARCHIVE" \
  "$EXTERNAL/"

# Flush writes
sync

# Restore
sudo mkdir -p "$RESTORE"

sudo tar \
  --extract \
  --zstd \
  --file="$EXTERNAL/$(basename "$ARCHIVE")" \
  --acls \
  --xattrs \
  --numeric-owner \
  -C "$RESTORE"
```

## Important considerations

### Do not archive the external drive inside itself

The archive destination must not be inside the directory being archived.

For example, avoid:

```text
/home/user/data/
└── external-drive/
    └── data.tar.zst
```

Instead, the external filesystem should be mounted outside the source tree.

### Preserve ownership

The following option is particularly useful for system or multi-user directories:

```bash
--numeric-owner
```

It records numeric UID/GID values instead of relying on usernames. This is useful when restoring onto a system where the same usernames may not exist or may map differently.

### Preserve ACLs and extended attributes

For filesystems and applications that use them, these options preserve additional metadata:

```bash
--acls
--xattrs
```

This is especially relevant for system directories, application data, security metadata, and filesystems using extended attributes.

### Avoid blindly restoring over an existing directory

Restoring an archive into an existing directory does not necessarily make the destination an exact replica of the source. Files already present in the destination but absent from the archive can remain.

For an exact replacement, move the existing directory out of the way first:

```bash
sudo mv /path/to/restore/directory \
  /path/to/restore/directory.old
```

Then restore the archive.

After verifying the restored copy, the old directory can be removed:

```bash
sudo rm -rf /path/to/restore/directory.old
```

Use `rm -rf` carefully. Verify the path before executing it.

## Recommended archive format

For general Linux backups, `tar` with Zstandard compression provides a good combination of:

- filesystem metadata preservation
- efficient compression
- fast compression and decompression
- straightforward restoration
- broad Linux availability

The resulting `.tar.zst` file is a single portable archive containing the directory hierarchy and its metadata.

## References

- GNU Project. (n.d.). *GNU tar manual*. GNU. https://www.gnu.org/software/tar/manual/
- GNU Project. (n.d.). *GNU coreutils manual*. GNU. https://www.gnu.org/software/coreutils/manual/
- Facebook Open Source. (n.d.). *Zstandard*. https://facebook.github.io/zstd/

```
This can also be adapted into a **backup/restore script with arguments such as `backup`, `verify`, `copy`, and `restore`**, which would make the workflow safer and repeatable.
```