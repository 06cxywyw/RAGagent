# 小林coding - OS-写文件崩溃
---
## 7.2 进程写文件时，进程发生了崩溃，已写入的数据会丢失吗？
大家好，我是小林。
前几天，有位读者问了我这么个问题：
大概就是，进程写文件（使用缓冲 IO）过程中，写一半的时候，进程发生了崩溃，已写入的数据会丢失吗？
答案，是不会的。
因为进程在执行 write （使用缓冲 IO）系统调用的时候，实际上是将文件数据写到了内核的 page cache，它是文件系统中用于缓存文件数据的缓冲，所以即使进程崩溃了，文件数据还是保留在内核的 page cache，我们读数据的时候，也是从内核的 page cache 读取，因此还是依然读的进程崩溃前写入的数据。
内核会找个合适的时机，将 page cache 中的数据持久化到磁盘。但是如果 page cache 里的文件数据，在持久化到磁盘之前，系统发生了崩溃，那这部分数据就会丢失了。
当然， 我们也可以在程序里调用 fsync 函数，在写文件的时候，立刻将文件数据持久化到磁盘，这样就可以解决系统崩溃导致的文件数据丢失的问题。
我在网上看到一篇介绍 page cache 很好的文章， 分享给大家一起学习。
作者：spongecaptain
[Linux 的 Page Cache](https://spongecaptain.cool/SimpleClearFileIO/1.%20page%20cache.html)
---
## Page Cache
---
### Page Cache 是什么？
为了理解 Page Cache，我们不妨先看一下 Linux 的文件 I/O 系统，如下图所示：
上图中，红色部分为 Page Cache。可见 Page Cache 的本质是由 Linux 内核管理的内存区域。我们通过 mmap 以及 buffered I/O 将文件读取到内存空间实际上都是读取到 Page Cache 中。
---
### 如何查看系统的 Page Cache？
通过读取/proc/meminfo文件，能够实时获取系统内存情况：
```
$ cat /proc/meminfo
...
Buffers: 1224 kB
Cached: 111472 kB
SwapCached: 36364 kB
Active: 6224232 kB
Inactive: 979432 kB
Active(anon): 6173036 kB
Inactive(anon): 927932 kB
Active(file): 51196 kB
Inactive(file): 51500 kB
...
Shmem: 10000 kB
...
SReclaimable: 43532 kB
...
```
根据上面的数据，你可以简单得出这样的公式（等式两边之和都是 112696 KB）：
```
Buffers + Cached + SwapCached = Active(file) + Inactive(file) + Shmem + SwapCached
```
两边等式都是 Page Cache，即：
```
Page Cache = Buffers + Cached + SwapCached
```
通过阅读下面的小节，就能够理解为什么 SwapCached 与 Buffers 也是 Page Cache 的一部分。