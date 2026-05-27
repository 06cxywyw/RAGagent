# 小林coding - 网络-断网Ping127
---
## 5.3 断网了，还能 ping 通 127.0.0.1 吗？
[断网了，还能 ping 通 127.0.0.1 吗？](https://mp.weixin.qq.com/s/qqfnyw4wKFjJqnV1eoRDhw)
你女神爱不爱你，你问她，她可能不会告诉你。
但网通不通，你ping一下就知道了。
可能看到标题，你就知道答案了，但是你了解背后的原因吗？
那如果把127.0.0.1换成0.0.0.0或localhost会怎么样呢？你知道这几个IP有什么区别吗？
以前面试的时候就遇到过这个问题，大家看个动图了解下面试官和我当时的场景，求当时我的心里阴影面积。
话不多说，我们直接开车。
拔掉网线，断网。
然后在控制台输入ping 127.0.0.1。
```
$ ping 127.0.0.1
PING 127.0.0.1 (127.0.0.1): 56 data bytes
64 bytes from 127.0.0.1: icmp_seq=0 ttl=64 time=0.080 ms
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.093 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.074 ms
64 bytes from 127.0.0.1: icmp_seq=3 ttl=64 time=0.079 ms
64 bytes from 127.0.0.1: icmp_seq=4 ttl=64 time=0.079 ms
^C
--- 127.0.0.1 ping statistics ---
5 packets transmitted, 5 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 0.074/0.081/0.093/0.006 ms
```
说明，拔了网线，ping 127.0.0.1是能ping通的。
其实这篇文章看到这里，标题前半个问题已经被回答了。但是我们可以再想深一点。
为什么断网了还能ping通127.0.0.1呢？
这能说明你不用交网费就能上网吗？
不能。
首先我们需要进入基础科普环节。
不懂的同学看了就懂了，懂的看了就当查漏补缺吧。