# Keeping your backups healthy output example

```bash
repository b93a0b7e opened (version 2, compression level auto)
Applying Policy: keep 7 daily, 4 weekly, 12 monthly snapshots
keep 8 snapshots:
ID        Time                 Host        Tags        Reasons                  Paths          Size
----------------------------------------------------------------------------------------------------------
cfec250e  2026-07-18 14:30:21  flow                    oldest monthly snapshot  /home/initial  243.304 GiB
d853935b  2026-07-28 17:27:52  flow                    daily snapshot           /home/initial  272.093 GiB
f647986f  2026-07-30 13:42:32  flow                    daily snapshot           /home/initial  272.262 GiB
                                                       weekly snapshot
                                                       monthly snapshot
1e660b7b  2026-08-05 17:41:24  flow                    daily snapshot           /home/initial  273.153 GiB
155aac8e  2026-08-07 00:31:11  flow                    daily snapshot           /home/initial  275.278 GiB
                                                       weekly snapshot
045726ab  2026-08-11 08:23:54  flow                    daily snapshot           /home/initial  276.308 GiB
d79be9a1  2026-08-15 10:27:48  flow                    daily snapshot           /home/initial  322.091 GiB
                                                       weekly snapshot
9e3b614d  2026-08-24 12:19:27  flow                    daily snapshot           /home/initial  322.510 GiB
                                                       weekly snapshot
                                                       monthly snapshot
----------------------------------------------------------------------------------------------------------
Timestamps shown in local time
8 snapshots

remove 4 snapshots:
ID        Time                 Host        Tags        Paths          Size
---------------------------------------------------------------------------------
a54a86f9  2026-07-21 23:14:40  flow                    /home/initial  218.546 GiB
976e96fc  2026-07-22 00:07:49  flow                    /home/initial  218.546 GiB
529ec6eb  2026-08-15 10:23:40  flow                    /home/initial  322.091 GiB
c35cb7a1  2026-08-24 12:14:59  flow                    /home/initial  322.510 GiB
---------------------------------------------------------------------------------
Timestamps shown in local time
4 snapshots

keep 7 snapshots:
ID        Time                 Host        Tags        Reasons                  Paths                              Size
------------------------------------------------------------------------------------------------------------------------
d846dc21  2026-07-18 14:27:17  flow                    daily snapshot           /home/initial/.config/restic-tool  552 B
                                                       oldest monthly snapshot
38340bc3  2026-07-21 08:02:25  flow                    daily snapshot           /home/initial/.config/restic-tool  552 B
929fed05  2026-07-28 17:24:41  flow                    daily snapshot           /home/initial/.config/restic-tool  526 B
cecc7f98  2026-07-30 13:41:17  flow                    daily snapshot           /home/initial/.config/restic-tool  526 B
                                                       weekly snapshot
                                                       monthly snapshot
e90edb6d  2026-08-05 17:34:44  flow                    daily snapshot           /home/initial/.config/restic-tool  526 B
                                                       weekly snapshot
1a4e8ff1  2026-08-15 10:22:00  flow                    daily snapshot           /home/initial/.config/restic-tool  526 B
                                                       weekly snapshot
8b18c2d4  2026-08-24 12:13:36  flow                    daily snapshot           /home/initial/.config/restic-tool  526 B
                                                       weekly snapshot
                                                       monthly snapshot
------------------------------------------------------------------------------------------------------------------------
Timestamps shown in local time
7 snapshots

remove 1 snapshots:
ID        Time                 Host        Tags        Paths                              Size
-----------------------------------------------------------------------------------------------
f5dbccc7  2026-08-15 10:19:39  flow                    /home/initial/.config/restic-tool  526 B
-----------------------------------------------------------------------------------------------
Timestamps shown in local time
1 snapshots

[0:00] 100.00%  5 / 5 files deleted
5 snapshots have been removed, running prune
[0:00] 100.00%  23 / 23 index files loaded
loading all snapshots...
finding data that is still in use for 15 snapshots
[0:05] 100.00%  15 / 15 snapshots
searching used packs...
collecting packs for deletion and repacking
[0:00] 100.00%  14592 / 14592 packs processed

to repack:         45183 blobs / 69.916 MiB
this removes:       1216 blobs / 8.709 MiB
to delete:             3 blobs / 760 B
total prune:        1219 blobs / 8.710 MiB
remaining:        818450 blobs / 241.497 GiB
unused size after prune: 247.955 MiB (0.10% of remaining size)

repacking packs
[0:02] 100.00%  5 / 5 packs repacked
rebuilding index
[0:00] 100.00%  24 / 24 indexes processed
[0:00] 100.00%  12 / 12 old indexes deleted
removing 6 old packs
[0:00] 100.00%  6 / 6 files deleted
done
```

