# JavaGuide - 计算机网络

> 来源: https://javaguide.cn/cs-basics/network/tcp-connection-and-disconnection.html

# TCP 三次握手和四次挥手（传输层）
[Guide](https://javaguide.cn/article/)计算机基础计算机网络约 7657 字大约 26 分钟TCP（Transmission Control Protocol）是一种面向连接、可靠的传输层协议。这里的“可靠”，通常体现在按序交付、差错检测、丢包重传、流量控制和拥塞控制等方面。

TCP 连接的建立和释放，最常被问到的就是三次握手和四次挥手。它们看起来像固定流程，背后其实是在同步序列号、确认双方收发能力，并尽量安全地释放连接状态。

这篇文章主要回答几个问题：

- TCP 三次握手每一步分别做了什么？
- 为什么建立连接需要三次握手，而不是两次或四次？
- TCP 四次挥手每一步分别做了什么？
- TIME_WAIT、CLOSE_WAIT、半连接队列和全连接队列分别该怎么理解？

术语约定：本文正文统一使用SYN_RCVD、TIME_WAIT这类下划线写法；RFC 中常写作SYN-RECEIVED、TIME-WAIT，Linuxss命令中常显示为syn-recv、time-wait。它们指向的是同一类 TCP 状态，只是不同语境下的写法不同。

---
## 建立连接：TCP 三次握手
![TCP 三次握手图解](https://oss.javaguide.cn/github/javaguide/cs-basics/network/tcp-shakes-hands-three-times.png)

在最常见的“一端主动发起连接、一端被动监听”的场景下，TCP 连接通常通过三次握手建立：

- 第一次握手（SYN）：客户端向服务端发送一个 SYN（Synchronize Sequence Numbers）报文段，其中包含客户端生成的初始序列号（Initial Sequence Number，ISN），例如seq=x。发送后，客户端进入SYN_SENT状态，等待服务端确认。
- 第二次握手（SYN+ACK）：服务端收到 SYN 后，如果同意建立连接，会回复一个 SYN+ACK 报文段。这个报文段包含两个关键信息：SYN：服务端也需要同步自己的初始序列号，因此会携带服务端生成的 ISN，例如seq=y。ACK：用于确认收到客户端的 SYN，确认号设置为客户端初始序列号加一，即ack=x+1。发送该报文段后，服务端进入SYN_RCVD状态。
- SYN：服务端也需要同步自己的初始序列号，因此会携带服务端生成的 ISN，例如seq=y。
- ACK：用于确认收到客户端的 SYN，确认号设置为客户端初始序列号加一，即ack=x+1。
- 发送该报文段后，服务端进入SYN_RCVD状态。
- 第三次握手（ACK）：客户端收到服务端的 SYN+ACK 后，会向服务端发送最终确认报文段，确认号为ack=y+1。发送后，客户端进入ESTABLISHED状态。服务端收到这个 ACK 后，也进入ESTABLISHED状态。

至此，双方完成初始序列号同步，并确认这条连接可以开始双向传输数据。

---
### 什么是半连接队列和全连接队列？
图表加载中在 TCP 三次握手过程中，服务端内核通常会用两个队列来管理连接请求。下面以常见 Linux 行为为例，不同操作系统、内核版本、socket 选项和部署环境可能会有细节差异。

- 半连接队列（SYN Queue）：保存“握手未完成”的请求。服务端收到 SYN 并回复 SYN+ACK 后，连接进入SYN_RCVD，等待客户端最终 ACK。如果一直收不到 ACK，内核会按重传策略重发 SYN+ACK，最终超时清理。常见相关参数包括net.ipv4.tcp_max_syn_backlog。在 SYN Flood 场景下，还会涉及net.ipv4.tcp_syncookies。
- 保存“握手未完成”的请求。服务端收到 SYN 并回复 SYN+ACK 后，连接进入SYN_RCVD，等待客户端最终 ACK。
- 如果一直收不到 ACK，内核会按重传策略重发 SYN+ACK，最终超时清理。
- 常见相关参数包括net.ipv4.tcp_max_syn_backlog。在 SYN Flood 场景下，还会涉及net.ipv4.tcp_syncookies。
- 全连接队列（Accept Queue）：保存“握手已完成但应用还没有 accept”的连接。服务端收到最终 ACK 后，连接变为ESTABLISHED，并进入全连接队列，等待应用层accept()取走。队列容量受listen(fd, backlog)和系统上限net.core.somaxconn共同影响。实践中常见有效上限可以近似理解为min(backlog, somaxconn)，具体行为仍要看内核版本和应用配置。总结一下：
- 保存“握手已完成但应用还没有 accept”的连接。服务端收到最终 ACK 后，连接变为ESTABLISHED，并进入全连接队列，等待应用层accept()取走。
- 队列容量受listen(fd, backlog)和系统上限net.core.somaxconn共同影响。实践中常见有效上限可以近似理解为min(backlog, somaxconn)，具体行为仍要看内核版本和应用配置。

| 队列 | 作用 | 状态 | 移出条件 |
| --- | --- | --- | --- |
| 半连接队列（SYN Queue） | 保存未完成握手的连接 | SYN_RCVD | 收到 ACK / 超时重传失败 |
| 全连接队列（Accept Queue） | 保存已完成握手、等待应用 accept 的连接 | ESTABLISHED | 被应用层accept()取出 |

当全连接队列满时，net.ipv4.tcp_abort_on_overflow会影响处理策略：

- 0（默认）：Linux 通常不会立即返回 RST，而可能丢弃第三次握手 ACK，使服务端继续停留在握手未完全完成的状态，并重传 SYN+ACK。客户端侧可能已经认为connect()成功，但首包发送后迟迟没有响应，最终表现为首包阻塞、读超时或重试。
- 1：直接对客户端回复RST，让连接快速失败。

排查时可以用ss -ltn看监听 socket。对于LISTEN状态，Recv-Q通常表示当前 backlog 中等待应用 accept 的连接数，Send-Q表示 socket backlog 上限。如果Recv-Q长时间接近Send-Q，就要重点怀疑应用 accept 不及时、backlog 偏小、线程池卡住、GC 抖动或者短时间连接突刺。

当半连接队列满时，如果tcp_syncookies=1，Linux 会在 SYN backlog 溢出时启用 SYN Cookie：服务端把必要信息编码进返回的 SYN+ACK 中，而不是为每个请求都保留完整的半连接状态。只有收到合法的最终 ACK 后，内核才会重建连接所需的信息。

但 SYN Cookie 是防护手段，不是扩容手段。它能缓解 SYN Flood 对半连接队列的冲击，但仍会消耗 CPU；如果攻击流量已经打满带宽，SYN Cookie 也无法从根本上恢复可用性。另外，SYN Cookie 模式下部分 TCP 扩展能力可能受限，在高延迟、高带宽链路下可能出现性能退化。tcp_syncookies=2更偏测试用途，不建议作为生产环境默认配置。

---
### 为什么要三次握手？
TCP 三次握手主要做两件事：同步双方的初始序列号，并且确认双方的收发路径是可用的。真正的数据可靠交付，还要依赖后续传输过程中的确认、重传、窗口控制和拥塞控制。

---
#### 1. 确认双方收发能力，并同步初始序列号
图表加载中TCP 依赖序列号（SEQ）和确认号（ACK）来保证数据有序、去重和重传。三次握手通过交换并确认双方的 ISN，让两端对“从哪个序号开始收发数据”达成一致，同时避免只凭单向信息就进入已建立状态。

可以用下面这张表来记：

| 步骤 | 报文 | 能确认什么 |
| --- | --- | --- |
| 1 | C→S：SYN | 服务端知道：客户端能发，服务端能收，C→S 方向可达 |
| 2 | S→C：SYN+ACK | 客户端知道：服务端能发，客户端能收；同时确认服务端收到了自己的 SYN |
| 3 | C→S：ACK | 服务端知道：客户端收到了 SYN+ACK，S→C 方向也被服务端确认；至此握手闭环 |

注意，第 2 步之后只是客户端确认了双向可达，服务端还不知道客户端是否收到了 SYN+ACK。服务端只有收到第 3 次握手的 ACK 后，才真正确认这个闭环。

---
#### 2. 防止已失效的连接请求被错误建立
图表加载中设想一个场景：客户端发送的第一个连接请求 SYN1 因网络延迟而滞留。客户端超时后，重新发送 SYN2，并成功建立连接，数据传输完毕后连接也释放了。此时，延迟的 SYN1 才到达服务端。

- 如果是两次握手：服务端收到这个失效的 SYN1 后，可能误认为这是一个新的连接请求，并立即分配资源、建立连接。但客户端已经没有这个连接意图，不会继续配合传输，服务端就会单方面维持一个无效连接。
- 有了第三次握手：服务端收到失效的 SYN1 并回复 SYN+ACK 后，还要等待客户端最终 ACK。由于客户端当前没有这个连接状态，它可能直接丢弃，也可能发送 RST。服务端收不到合法 ACK，最终就会清理这个错误连接。

所以，三次握手不是“多发一次包而已”，它让连接建立过程形成闭环，避免网络中的延迟、重复历史请求干扰新的连接。

---
### 第 2 次握手已经传回 ACK，为什么还要传回 SYN？
第二次握手里的 ACK 是为了确认“服务端收到了客户端的 SYN”，也就是确认 C→S 方向的请求已经到达。

同时携带 SYN，是因为服务端也需要把自己的 ISN 同步给客户端，并要求客户端确认。只有双方的 ISN 都完成同步，后续可靠传输才有共同的序列号起点。

简言之：ACK 表示“我收到了你的 SYN”，SYN 表示“我也要同步我的初始序列号，请你确认”。

SYN（Synchronize Sequence Numbers）是 TCP 建立连接时使用的同步信号。客户端先发送 SYN，服务端使用 SYN+ACK 应答，最后客户端再用 ACK 确认。这样双方才能完成初始序列号同步，建立一条可用于可靠数据传输的 TCP 连接。

---
### 三次握手过程中可以携带数据吗？
普通 TCP 中，第三次握手的 ACK 可以携带数据。RFC 9293 也允许连接同步阶段出现携带数据的报文，但接收端在确认数据有效前，不能把这部分数据交付给应用；通常需要等连接进入ESTABLISHED后，应用层才能读到这些数据。

如果第三次握手的 ACK 丢失，但客户端随后发送了一个携带数据且带 ACK 标志的报文，服务端收到后可以把它视为有效的第三次握手确认。连接被认为建立后，服务端再继续处理该数据。

需要注意，这和 TCP Fast Open（TFO）不是一回事。TFO 讨论的是第一次 SYN 就携带应用数据，需要客户端、服务端和系统配置共同支持，不是普通 TCP 默认行为。

---
## 断开连接：TCP 四次挥手
![TCP 四次挥手图解](https://oss.javaguide.cn/github/javaguide/cs-basics/network/tcp-waves-four-times.png)

TCP 是全双工通信，两端的发送方向彼此独立。关闭连接时，通常需要两个方向分别完成“我不发了”和“我确认你不发了”的过程，所以逻辑上常被讲成“四次挥手”。

不过要注意：四次挥手说的是逻辑动作，不一定意味着抓包时总能看到 4 个独立报文段。在某些场景下，ACK 和 FIN 可以合并在同一个报文段里。

典型流程如下：

- 第一次挥手（FIN）：客户端，或者任意一方，决定关闭自己的发送方向时，会发送一个 FIN 报文段，表示自己已经没有数据要发送了。该报文段包含一个序列号，例如seq=u。发送后，主动关闭方进入FIN_WAIT_1状态。
- 第二次挥手（ACK）：服务端收到 FIN 后，会回复 ACK，确认号为ack=u+1。发送后，服务端进入CLOSE_WAIT状态。客户端收到 ACK 后，进入FIN_WAIT_2状态。此时连接处于半关闭（Half-Close）状态：客户端到服务端的发送方向已关闭，但服务端仍然可以继续向客户端发送剩余数据。
- 第三次挥手（FIN）：当服务端确认剩余数据都发送完毕后，也会发送 FIN，表示自己也准备关闭发送方向。该报文段同样包含一个序列号，例如seq=y。发送后，服务端进入LAST_ACK状态，等待客户端最终确认。
- 第四次挥手（ACK）：客户端收到服务端的 FIN 后，回复最终 ACK，确认号为ack=y+1。发送后，客户端进入TIME_WAIT状态。服务端收到这个 ACK 后进入CLOSED。客户端则在TIME_WAIT状态等待 2MSL 后，最终进入CLOSED。

注意区分：半关闭（Half-Close）指一个方向已经发送 FIN，另一个方向仍可继续发送数据；半开连接（Half-Open Connection）通常指一端崩溃、重启或状态丢失后，另一端仍以为连接存在。两者不是同一个概念。

TCP 连接建立与关闭的常见状态迁移路径如下。图中省略了同时打开、同时关闭、RST、CLOSING 等少见或异常分支。

![TCP 连接建立与关闭的常见状态迁移路径](https://oss.javaguide.cn/github/javaguide/cs-basics/network/tcp-state-diagram.png)

---
### 为什么要四次挥手？
因为 TCP 是全双工的。A 不想发了，不代表 B 也立刻没有数据要发。

举个例子，A 和 B 打电话，通话即将结束：

- A 说：“我没什么要说的了。”（A 发 FIN）
- B 回答：“我知道了。”但 B 可能还有话要说。（B 回 ACK）
- B 继续说完剩下的话，最后说：“我也说完了。”（B 发 FIN）
- A 回答：“知道了。”（A 回 ACK）

这对应到 TCP 中，就是两个方向分别关闭、分别确认。

---
### 为什么不能把服务端发送的 ACK 和 FIN 合并起来，变成三次挥手？
图表加载中关键原因是：回复 ACK和发送 FIN的触发时机通常不同。

- 当服务端收到客户端 FIN 时，内核协议栈会立即回复 ACK，确认“我收到了你要关闭发送方向的请求”。此时服务端进入CLOSE_WAIT，等待本端应用处理剩余数据。
- 只有当服务端应用处理完毕，并调用close()或shutdown()后，内核才会发送本端 FIN。
- 因此，“内核自动回 ACK”和“应用决定发 FIN”在时间上是解耦的，通常无法合并。只有在服务端恰好也准备立即关闭时，才可能出现 FIN+ACK 合并在一个报文段中的情况。

---
### 如果第二次挥手时服务端的 ACK 没有送达客户端，会怎样？
客户端发送第一次 FIN 后进入FIN_WAIT_1，并启动重传计时器。如果在超时时间内没有收到对端对 FIN 的确认 ACK，客户端会重传 FIN。

服务端如果收到重复 FIN，通常会再次发送 ACK。如果由于网络问题 ACK 一直无法送达，客户端在达到一定重试或超时阈值后，可能报错或放弃。具体行为受实现和参数影响，例如 Linux 中的tcp_retries2等。

---
### 为什么第四次挥手后要等待 2MSL？
第四次挥手时，主动关闭方发送给被动关闭方的最后一个 ACK 可能丢失。如果被动关闭方没有收到 ACK，就会重传 FIN。主动关闭方还在TIME_WAIT里，就能再次回复 ACK。

如果主动关闭方发完最后一个 ACK 后立刻进入CLOSED，当对端重传 FIN 到达时，本端可能已经没有对应连接状态，只能回复 RST，导致对端看到异常关闭或连接被重置。

图表加载中MSL（Maximum Segment Lifetime）是报文段在网络中的最大生存时间。2MSL 不是一次请求-响应的最大 RTT，而是一个保守等待窗口：既给最后 ACK 丢失后的 FIN 重传留出处理机会，也尽量保证旧连接中的延迟报文从网络中消失。

需要注意，RFC 里的 MSL 是协议层概念，具体系统实现可能不同。Linux 常见实现中，TIME_WAIT保留时间通常是 60 秒。还有一个常见误区：tcp_fin_timeout控制的是 orphaned connection 的FIN_WAIT_2超时，不是TIME_WAIT。想缓解TIME_WAIT带来的端口压力，优先看连接复用、端口范围、主动关闭方和tcp_tw_reuse条件，而不是试图用tcp_fin_timeout缩短TIME_WAIT。

---
## TIME_WAIT 常见问题：为什么要等、会不会出问题、能不能复用？
这部分内容已单独成文，详见[TCP TIME_WAIT 详解：为什么要等、会不会出问题、能不能复用？](https://javaguide.cn/cs-basics/network/tcp-time-wait.html)。

上一节讲了为什么四次挥手最后要等 2MSL，这一节继续回答几个线上最常见的问题：大量TIME_WAIT会不会拖垮系统，为什么不建议随便开tcp_tw_reuse，以及TIME_WAIT和CLOSE_WAIT到底怎么区分。

---
### TIME_WAIT 不只是“等一会儿再关”
ACK 都已经发出去了，为什么还要占着端口等几十秒？

主动关闭方发出最后一个 ACK 后，不会立刻释放连接，而是进入TIME_WAIT。RFC 9293 的连接状态图里也能看到，TIME_WAIT会在 2MSL 超时后删除 TCB，并进入CLOSED。

这里要注意一个细节：不是“谁收到 FIN 谁就一定进入 TIME_WAIT”。被动关闭方收到 FIN 后，通常会先进入CLOSE_WAIT，等待本端应用处理完剩余数据并调用close()或shutdown()。更常见的情况是，主动关闭方收到对端最后的 FIN，并回复最后一个 ACK 后，进入TIME_WAIT。

一般来说，谁主动关闭连接，谁就更容易进入 TIME_WAIT。比如客户端主动断开 HTTP 短连接，TIME_WAIT往往出现在客户端；如果服务端主动断开连接，服务端也可能堆出大量TIME_WAIT。

看起来像是多等了一会儿，实际上是在解决两个问题。

---
### 第一个原因：让最后一个 ACK 有补救机会
主动关闭方发送最后一个 ACK 后，如果这个 ACK 在网络中丢了，被动关闭方会以为自己的 FIN 没被确认，于是重发 FIN。主动关闭方还在TIME_WAIT里，就能再次回复 ACK；如果它已经进入CLOSED，就可能回 RST，让对端感知为异常关闭或连接被重置。

---
### 第二个原因：别让旧连接的包混进新连接
TCP 连接靠四元组定位：源 IP、源端口、目的 IP、目的端口。如果旧连接刚关闭，立刻用同一个四元组建立新连接，旧连接里延迟到达的数据包可能刚好落在新连接接收窗口里，被当成新连接的数据处理。

举个例子：

```text
旧连接：client:50000 -> server:443
服务端发出的 SEQ=301 数据包在网络里绕了一圈，迟迟没到。

旧连接关闭后，客户端很快复用了同一个源端口：
新连接：client:50000 -> server:443

这时旧的 SEQ=301 抵达客户端。
如果它刚好落在新连接接收窗口里，就有可能被误收。
```
TCP 序列号空间是 0 到 2^32 - 1，会按模 2^32 回绕，所以不能只靠序列号永久区分新老报文。实际系统还有时间戳、PAWS（Protection Against Wrapped Sequences）、随机 ISN 等保护，但它们不是“完全替代 TIME_WAIT”的万能方案。RFC 1337 也讨论过旧重复报文导致的 TIME_WAIT 风险。

---
### 大量 TIME_WAIT 到底有没有问题？
TIME_WAIT本身是正常状态。真正的问题通常出现在主动关闭方短时间内创建大量到同一个目标 IP + 目标端口的连接，导致本地临时端口被占住。

Linux 本地临时端口范围可通过net.ipv4.ip_local_port_range查看和调整。上游内核文档里的默认范围是32768 60999，实际环境以本机输出为准：

```bash
cat /proc/sys/net/ipv4/ip_local_port_range
```
如果客户端短时间内反复连接同一个目标 IP + 目标端口，旧连接又都停在TIME_WAIT，本地可用临时端口可能被占满，导致新连接无法分配源端口，常见报错如：

```text
Cannot assign requested address
```
可以按这个思路判断：

- 如果服务端上看到很多 TIME_WAIT：先看是不是服务端主动关闭了连接，比如服务端主动断开短连接、网关主动关闭上游连接、连接池主动淘汰连接。
- 如果客户端或网关上看到很多 TIME_WAIT：重点看是否存在短连接风暴、连接池未复用、HTTP keep-alive 没打开、上游频繁断连。

还可以做一个粗略估算：

```text
同一目标 IP:Port 的短连接上限 ≈ 可用临时端口数 / TIME_WAIT 保留时间
```
比如默认端口范围32768~60999，大约 2.8 万个端口。如果TIME_WAIT保留约 60 秒，那么同一目标 IP:Port 上持续新建短连接的上限大约是数百 QPS 量级。实际结果还会受到连接复用、端口保留、NAT、内核策略和不同远端四元组复用规则影响，不能只看TIME_WAIT总数就下结论。

---
### 为什么不建议随便开 tcp_tw_reuse？
tcp_tw_reuse允许在协议认为安全的条件下，为新的主动连接复用TIME_WAITsocket。它看起来像是缓解端口压力的捷径，但这类参数改变的是 TCP 对旧连接报文的等待策略，不能当成通用开关。

这里要分三层看：

- 它依赖时间戳等条件判断“新报文是否足够新”。时间戳可以过滤一部分旧报文，但不是所有异常都能覆盖。RFC 1337 重点讨论过TIME_WAIT状态被旧 RST 等报文提前终止的风险。旧数据段如果落入新连接可接受窗口，可能造成新旧数据混淆；旧 ACK 的影响则依赖序列号、窗口和实现细节，不宜和旧 RST 直接并列成同一种断连风险。
- 当前上游 Linux 文档中，tcp_tw_reuse可取 0/1/2，默认值为 2，表示仅允许 loopback 流量复用；1才是全局开启。但旧版内核文档、发行版 man page 或历史资料可能仍写作“默认关闭”，实际机器必须以sysctl net.ipv4.tcp_tw_reuse为准。内核文档也明确提示，不要在没有专家建议或明确需求时修改。
- 不要把tcp_tw_reuse和已经废弃的tcp_tw_recycle搞混。tcp_tw_recycle在 NAT 环境下会导致时间戳冲突，大量连接被异常丢弃，Linux 4.12 之后已经被移除。网上很多老文章仍然会建议同时打开tcp_tw_reuse和tcp_tw_recycle，这类配置不要照搬。

一句话：tcp_tw_reuse可以讨论，但必须结合 Linux 版本、是否 loopback、是否经过 NAT、是否启用时间戳、是否真的存在端口耗尽来判断。能在应用层解决的，优先在应用层解决。

---
### TIME_WAIT 和 CLOSE_WAIT：一个正常等待，一个更像应用没收尾
排查连接状态时，CLOSE_WAIT通常比TIME_WAIT更值得警惕。

收到对端 FIN 后，本端内核会回 ACK，然后进入CLOSE_WAIT，等待应用处理完剩余数据并调用close()或shutdown()。在 Java 服务里，CLOSE_WAIT堆积经常和连接没有正确关闭有关。比如手写 Socket、HTTP 客户端响应体没有 close、异常分支提前 return、连接池连接没有归还，都可能让内核已经 ACK 了对端 FIN，但应用迟迟不调用 close。

可以先按这个思路判断：

- TIME_WAIT：主动关闭方在等 2MSL，通常是协议设计的一部分。
- CLOSE_WAIT：被动关闭方已经知道对端不发了，但本端应用还没关闭 socket。大量堆积时，优先怀疑应用代码没释放连接、线程卡住、连接池归还异常、读写流程没有走到 finally。

| 状态 | 常见出现方 | 含义 | 排查方向 |
| --- | --- | --- | --- |
| TIME_WAIT | 主动关闭方 | 等最后 ACK 重传机会，也等旧报文消失 | 短连接、连接池、keep-alive、端口范围 |
| CLOSE_WAIT | 被动关闭方 | 对端已关闭，本端应用还没 close | 代码是否释放 socket、线程是否卡住、连接池是否泄漏 |

---
### 排查时别只盯着数量，要先看谁在主动关闭
TIME_WAIT 与 CLOSE_WAIT 排查思路。TIME_WAIT 重点看谁在主动关闭连接，CLOSE_WAIT 则优先排查应用是否正确释放 socket 或归还连接。

![TIME_WAIT 与 CLOSE_WAIT 排查流程](https://oss.javaguide.cn/github/javaguide/cs-basics/network/tcp-time-wait-close-wait-troubleshooting-flowchart.png)

看到大量TIME_WAIT或CLOSE_WAIT，可以先用下面几条命令定位方向：

ss是 Linux 上iproute2提供的命令，macOS 默认没有。如果你的开发环境是 macOS，可以用netstat和lsof替代。

```bash
# Linux：查看各 TCP 状态数量
ss -ant | awk 'NR>1 {cnt[$1]++} END {for (s in cnt) print s, cnt[s]}'

# macOS：查看各 TCP 状态数量
netstat -anp tcp | awk '$1 ~ /^tcp/ {cnt[$NF]++} END {for (s in cnt) print s, cnt[s]}'

# Linux：查看 TIME-WAIT 主要集中在哪些目标
ss -ant state time-wait | awk 'NR>1 {print $5}' | sort | uniq -c | sort -nr | head

# macOS：查看 TIME-WAIT 主要集中在哪些远端
netstat -anp tcp | awk '$1 ~ /^tcp/ && $NF=="TIME_WAIT" {print $(NF-1)}' | sort | uniq -c | sort -nr | head

# Linux：查看 CLOSE-WAIT 对应哪个进程（需要 sudo 才能看到进程信息）
sudo ss -tanp state close-wait

# macOS：查看 CLOSE-WAIT 对应哪个进程
sudo lsof -nP -iTCP -sTCP:CLOSE_WAIT

# Linux：查看监听 socket 的 accept queue 情况
ss -ltn
```
![macOS：查看各 TCP 状态数量和 TIME-WAIT 主要集中在哪些远端](https://oss.javaguide.cn/github/javaguide/cs-basics/network/macos-check-tcp-state-count-and-time-wait-remote-distribution.png)

命令背后的判断：

- TIME_WAIT 集中在某个远端服务：检查是否短连接太多、HTTP 连接复用没生效、连接池配置过小、连接池被频繁销毁，或者对端频繁主动断开。
- CLOSE_WAIT 集中在某个本地进程：优先查应用代码，尤其是异常分支有没有关闭响应体、socket 或连接对象。
- LISTEN socket 的 Recv-Q 长时间接近 Send-Q：重点排查 accept queue 堆积，看看应用 accept 是否及时、线程池是否卡住、backlog 配置是否过小。
- 如果是网关、代理、爬虫、压测客户端，TIME_WAIT更常见；如果是 Java 服务端内部依赖调用泄漏，CLOSE_WAIT更常见。

---
### 克制的优化建议
按优先级排查：

- 优先减少不必要的短连接：开启 HTTP keep-alive，复用连接池。
- 确认谁在主动关闭连接：服务端、客户端、网关、连接池都有可能成为主动关闭方。
- 检查应用侧资源释放：尤其是 HTTP 响应体、Socket、数据库连接、连接池连接归还。
- 扩大本地端口范围：在客户端短连接确实很高、且存在端口耗尽证据时，再考虑调整ip_local_port_range。
- 最后才看内核参数：tcp_tw_reuse、tcp_abort_on_overflow、tcp_syncookies都要结合 Linux 版本、业务连接模型、是否经过 NAT、是否被攻击、是否有真实观测数据来判断，不建议直接照抄网上配置。

TIME_WAIT多，不一定是故障；CLOSE_WAIT多，通常要先看代码。这两个状态看起来都像“连接没关干净”，但问题方向完全不同。

---
## 参考

- 《计算机网络（第 7 版）》
- 《图解 HTTP》
- TCP and UDP Tutorial：[https://www.9tut.com/tcp-and-udp-tutorial](https://www.9tut.com/tcp-and-udp-tutorial)
- 从一次线上问题说起，详解 TCP 半连接队列、全连接队列：[https://mp.weixin.qq.com/s/YpSlU1yaowTs-pF6R43hMw](https://mp.weixin.qq.com/s/YpSlU1yaowTs-pF6R43hMw)
- RFC 9293: Transmission Control Protocol (TCP)：[https://www.rfc-editor.org/rfc/rfc9293](https://www.rfc-editor.org/rfc/rfc9293)
- RFC 1337: TIME-WAIT Assassination Hazards in TCP：[https://www.rfc-editor.org/rfc/rfc1337](https://www.rfc-editor.org/rfc/rfc1337)
- Linux 内核 ip-sysctl 文档：[https://www.kernel.org/doc/Documentation/networking/ip-sysctl.txt](https://www.kernel.org/doc/Documentation/networking/ip-sysctl.txt)
- SoByte - 为什么 TCP 需要 TIME_WAIT 状态：[https://www.sobyte.net/post/2022-10/tcp-time-wait/](https://www.sobyte.net/post/2022-10/tcp-time-wait/)

---
## 写在最后
感谢你能看到这里，也希望这篇文章对你有点用。

JavaGuide 坚持更新 6 年多，近 6000 次提交、600+ 位贡献者一起打磨。如果这些内容对你有帮助，非常欢迎点个免费的 Star 支持下（完全自愿，觉得有收获再点就好）：[GitHub](https://github.com/Snailclimb/JavaGuide)|[Gitee](https://gitee.com/SnailClimb/JavaGuide)。

如果你想要付费支持/面试辅导（比如实战项目、简历优化、一对一提问、高频考点突击资料等）的话，欢迎了解我的[知识星球](https://javaguide.cn/about-the-author/zhishixingqiu-two-years.html)。已经坚持维护六年，内容持续更新，虽白菜价（0.4元/天）但质量很高，主打一个良心！

![JavaGuide 公众号](https://oss.javaguide.cn/github/javaguide/gongzhonghao-javaguide.png)