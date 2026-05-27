# JavaGuide - 计算机网络

> 来源: https://javaguide.cn/cs-basics/network/http1.0-vs-http1.1.html

# HTTP 1.0 vs HTTP 1.1：长连接、缓存、Host 头等核心差异（应用层）
[Guide](https://javaguide.cn/article/)计算机基础计算机网络约 2719 字大约 9 分钟HTTP/1.0 和 HTTP/1.1 名字只差一个小版本，但它们在连接复用、缓存、Host 头、状态码和带宽优化上都有明显差异。

这些差异不是单纯的协议细节，它们直接影响浏览器如何发请求、服务器如何复用连接、缓存如何生效，以及虚拟主机如何工作。

这篇文章主要回答几个问题：

- HTTP/1.1 相比 HTTP/1.0 新增了哪些常见状态码？
- HTTP/1.0 和 HTTP/1.1 的缓存机制有什么差异？
- HTTP/1.1 为什么默认支持长连接？
- Host 头和带宽优化分别解决了什么问题？

开始之前，先简单回顾一下 HTTP 协议：

![HTTP：超文本传输协议概览](https://oss.javaguide.cn/github/javaguide/cs-basics/network/http-overview.png)

---
## 响应状态码
HTTP/1.0 仅定义了 16 种状态码。HTTP/1.1 中新加入了大量的状态码，光是错误响应状态码就新增了 24 种。比如说，100 (Continue)——在请求大资源前的预热请求，206 (Partial Content)——范围请求的标识码，409 (Conflict)——请求与当前资源的规定冲突，410 (Gone)——资源已被永久转移，而且没有任何已知的转发地址。

---
## 缓存处理
缓存技术通过避免用户与源服务器的频繁交互，节约了大量的网络带宽，降低了用户接收信息的延迟。

---
### HTTP/1.0
HTTP/1.0 提供的缓存机制非常简单。服务器端使用Expires标签来标志（时间）一个响应体，在Expires标志时间内的请求，都会获得该响应体缓存。服务器端在初次返回给客户端的响应体中，有一个Last-Modified标签，该标签标记了被请求资源在服务器端的最后一次修改。在请求头中，使用If-Modified-Since标签，该标签标志一个时间，意为客户端向服务器进行问询：“该时间之后，我要请求的资源是否有被修改过？”通常情况下，请求头中的If-Modified-Since的值即为上一次获得该资源时，响应体中的Last-Modified的值。

如果服务器接收到了请求头，并判断If-Modified-Since时间后，资源确实没有修改过，则返回给客户端一个304 Not Modified响应头，表示“缓冲可用，你从浏览器里拿吧！”。

如果服务器判断If-Modified-Since时间后，资源被修改过，则返回给客户端一个200 OK的响应体，并附带全新的资源内容，表示“你要的我已经改过的，给你一份新的”。

![HTTP1.0cache1](https://javaguide.cn/assets/HTTP1.0cache1-DCTyGd2J.png)

![HTTP1.0cache2](https://javaguide.cn/assets/HTTP1.0cache2-F-Ctbiw3.png)

---
### HTTP/1.1
HTTP/1.1 的缓存机制在 HTTP/1.0 的基础上，大大增加了灵活性和扩展性。基本工作原理和 HTTP/1.0 保持不变，而是增加了更多细致的特性。其中，请求头中最常见的特性就是Cache-Control，详见 MDN Web 文档[Cache-Control](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Headers/Cache-Control)。

---
## 连接方式
HTTP/1.0 默认使用短连接，也就是说，客户端和服务器每进行一次 HTTP 操作，就建立一次连接，任务结束就中断连接。当客户端浏览器访问的某个 HTML 或其他类型的 Web 页中包含有其他的 Web 资源（如 JavaScript 文件、图像文件、CSS 文件等），每遇到这样一个 Web 资源，浏览器就会重新建立一个 TCP 连接，这样就会导致有大量的“握手报文”和“挥手报文”占用了带宽。

为了解决 HTTP/1.0 存在的资源浪费的问题，HTTP/1.1 优化为默认长连接模式。采用长连接模式的请求报文会通知服务端：“我向你请求连接，并且连接成功建立后，请不要关闭”。因此，该 TCP 连接将持续打开，为后续的客户端-服务端的数据交互服务。也就是说在使用长连接的情况下，当一个网页打开完成后，客户端和服务器之间用于传输 HTTP 数据的 TCP 连接不会关闭，客户端再次访问这个服务器时，会继续使用这一条已经建立的连接。

如果 TCP 连接一直保持的话也是对资源的浪费，因此，一些服务器软件（如 Apache）还会支持超时时间选项。在超时时间之内没有新的请求到达，TCP 连接才会被关闭。

有必要说明的是，HTTP/1.0 仍提供了长连接选项，即在请求头中加入Connection: Keep-Alive。同样的，在 HTTP/1.1 中，如果不希望使用长连接选项，也可以在请求头中加入Connection: close，这样会通知服务器端：“我不需要长连接，连接成功后即可关闭”。

HTTP 协议的长连接和短连接，实质上是 TCP 协议的长连接和短连接。

实现长连接需要客户端和服务端都支持长连接。

---
## Host 头处理
域名系统（DNS）允许多个主机名绑定到同一个 IP 地址上，但是 HTTP/1.0 并没有考虑这个问题。假设我们有一个资源 URL 是http://example1.org/home.html，HTTP/1.0 的请求报文中，将会请求的是GET /home.html HTTP/1.0，也就是不会加入主机名。这样的报文送到服务器端，服务器是理解不了客户端想请求的真正网址。

因此，HTTP/1.1 在请求头中加入了Host字段。加入Host字段的报文头部将会是：

```plain
GET /home.html HTTP/1.1
Host: example1.org
```
这样，服务器端就可以确定客户端想要请求的真正的网址了。

---
## 带宽优化

---
### 范围请求
HTTP/1.1 引入了范围请求（range request）机制，以避免带宽的浪费。当客户端想请求一个文件的一部分，或者需要继续下载一个已经下载了部分但被终止的文件，HTTP/1.1 可以在请求中加入Range头部，以请求（并只能请求字节型数据）数据的一部分。服务器端可以忽略Range头部，也可以返回若干Range响应。

206 (Partial Content)状态码的主要作用是确保客户端和代理服务器能正确识别部分内容响应，避免将其误认为完整资源并错误地缓存。这对于正确处理范围请求和缓存管理非常重要。

一个典型的 HTTP/1.1 范围请求示例：

```http
# 获取一个文件的前 1024 个字节
GET /z4d4kWk.jpg HTTP/1.1
Host: i.imgur.com
Range: bytes=0-1023
```
206 Partial Content响应：

```http
HTTP/1.1 206 Partial Content
Content-Range: bytes 0-1023/146515
Content-Length: 1024
…
（二进制内容）
```
简单解释一下 HTTP 范围响应头部中的字段：

- Content-Range头部：指示返回数据在整个资源中的位置，包括起始和结束字节以及资源的总长度。例如，Content-Range: bytes 0-1023/146515表示服务器端返回了第 0 到 1023 字节的数据（共 1024 字节），而整个资源的总长度是 146,515 字节。
- Content-Length头部：指示此次响应中实际传输的字节数。例如，Content-Length: 1024表示服务器端传输了 1024 字节的数据。

Range请求头不仅可以请求单个字节范围，还可以一次性请求多个范围。这种方式被称为“多重范围请求”（multiple range requests）。

客户端想要获取资源的第 0 到 499 字节以及第 1000 到 1499 字节：

```http
GET /path/to/resource HTTP/1.1
Host: example.com
Range: bytes=0-499,1000-1499
```
服务器端返回多个字节范围，每个范围的内容以分隔符分开：

```http
HTTP/1.1 206 Partial Content
Content-Type: multipart/byteranges; boundary=3d6b6a416f9b5
Content-Length: 376

--3d6b6a416f9b5
Content-Type: application/octet-stream
Content-Range: bytes 0-99/2000

(第 0 到 99 字节的数据块)

--3d6b6a416f9b5
Content-Type: application/octet-stream
Content-Range: bytes 500-599/2000

(第 500 到 599 字节的数据块)

--3d6b6a416f9b5
Content-Type: application/octet-stream
Content-Range: bytes 1000-1099/2000

(第 1000 到 1099 字节的数据块)

--3d6b6a416f9b5--
```

---
### 状态码 100
HTTP/1.1 中新加入了状态码100。该状态码的使用场景为，存在某些较大的文件请求，服务器可能不愿意响应这种请求，此时状态码100可以作为指示请求是否会被正常响应，过程如下图：

![HTTP1.1continue1](data:image/png;base64,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)

![HTTP1.1continue2](https://javaguide.cn/assets/HTTP1.1continue2-BkTNR_OC.png)

然而在 HTTP/1.0 中，并没有100 (Continue)状态码，要想触发这一机制，可以发送一个Expect头部，其中包含一个100-continue的值。

---
### 压缩
许多格式的数据在传输时都会做预压缩处理。数据的压缩可以大幅优化带宽的利用。然而，HTTP/1.0 对数据压缩的选项提供的不多，不支持压缩细节的选择，也无法区分端到端（end-to-end）压缩或者是逐跳（hop-by-hop）压缩。

HTTP/1.1 则对内容编码（content-codings）和传输编码（transfer-codings）做了区分。内容编码总是端到端的，传输编码总是逐跳的。

HTTP/1.0 包含了Content-Encoding头部，对消息进行端到端编码。HTTP/1.1 加入了Transfer-Encoding头部，可以对消息进行逐跳传输编码。HTTP/1.1 还加入了Accept-Encoding头部，是客户端用来指示它能处理什么样的内容编码。

---
## 总结

- 连接方式：HTTP/1.0 为短连接，HTTP/1.1 支持长连接。
- 状态响应码：HTTP/1.1 中新加入了大量的状态码，光是错误响应状态码就新增了 24 种。比如说，100 (Continue)——在请求大资源前的预热请求，206 (Partial Content)——范围请求的标识码，409 (Conflict)——请求与当前资源的规定冲突，410 (Gone)——资源已被永久转移，而且没有任何已知的转发地址。
- 缓存处理：在 HTTP/1.0 中主要使用 header 里的If-Modified-Since、Expires来作为缓存判断的标准，HTTP/1.1 则引入了更多的缓存控制策略，例如Entity Tag、If-Unmodified-Since、If-Match、If-None-Match等更多可供选择的缓存头来控制缓存策略。
- 带宽优化及网络连接的使用：HTTP/1.0 中，存在一些浪费带宽的现象，例如客户端只是需要某个对象的一部分，而服务器却将整个对象送过来了，并且不支持断点续传功能。HTTP/1.1 则在请求头引入了Range头域，它允许只请求资源的某个部分，即返回码是206 (Partial Content)，这样就方便了开发者自由选择以便于充分利用带宽和连接。
- Host 头处理：HTTP/1.1 在请求头中加入了Host字段。

---
## 参考资料
[Key differences between HTTP/1.0 and HTTP/1.1](http://www.ra.ethz.ch/cdstore/www8/data/2136/pdf/pd1.pdf)

---
## 写在最后
感谢你能看到这里，也希望这篇文章对你有点用。

JavaGuide 坚持更新 6 年多，近 6000 次提交、600+ 位贡献者一起打磨。如果这些内容对你有帮助，非常欢迎点个免费的 Star 支持下（完全自愿，觉得有收获再点就好）：[GitHub](https://github.com/Snailclimb/JavaGuide)|[Gitee](https://gitee.com/SnailClimb/JavaGuide)。

如果你想要付费支持/面试辅导（比如实战项目、简历优化、一对一提问、高频考点突击资料等）的话，欢迎了解我的[知识星球](https://javaguide.cn/about-the-author/zhishixingqiu-two-years.html)。已经坚持维护六年，内容持续更新，虽白菜价（0.4元/天）但质量很高，主打一个良心！

![JavaGuide 公众号](https://oss.javaguide.cn/github/javaguide/gongzhonghao-javaguide.png)