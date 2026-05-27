# 小林coding - 网络-无accept建立连接
阿里二面：没有 accept，能建立 TCP 连接吗？
---
## 4.21 没有 accept，能建立 TCP 连接吗？
[阿里二面：没有 accept，能建立 TCP 连接吗？](https://mp.weixin.qq.com/s/oPX_JoZUaLn6sW54yppfvA)
大家好，我是小林。
这次，我们来讨论一下，没有 accept，能建立 TCP 连接吗？
下面这个动图，是我们平时客户端和服务端建立连接时的代码流程。
对应的是下面一段简化过的服务端伪代码。
```
int main()
{
/*Step 1: 创建服务器端监听socket描述符listen_fd*/
listen_fd = socket(AF_INET, SOCK_STREAM, 0);
/*Step 2: bind绑定服务器端的IP和端口，所有客户端都向这个IP和端口发送和请求数据*/
bind(listen_fd, xxx);
/*Step 3: 服务端开启监听*/
listen(listen_fd, 128);
/*Step 4: 服务器等待客户端的链接，返回值cfd为客户端的socket描述符*/
cfd = accept(listen_fd, xxx);
/*Step 5: 读取客户端发来的数据*/
n = read(cfd, buf, sizeof(buf));
}
```
估计大家也是老熟悉这段伪代码了。
需要注意的是，在执行listen()方法之后还会执行一个accept()方法。
一般情况下，如果启动服务器，会发现最后程序会阻塞在accept()里。
此时服务端就算ok了，就等客户端了。
那么，再看下简化过的客户端伪代码。
```
int main()
{
/*Step 1: 创建客户端端socket描述符cfd*/
cfd = socket(AF_INET, SOCK_STREAM, 0);
/*Step 2: connect方法,对服务器端的IP和端口号发起连接*/
ret = connect(cfd, xxxx);
/*Step 4: 向服务器端写数据*/
write(cfd, buf, strlen(buf));
}
```
客户端比较简单，创建好socket之后，直接就发起connect方法。
此时回到服务端，会发现之前一直阻塞的accept方法，返回结果了。
这就算两端成功建立好了一条连接。之后就可以愉快的进行读写操作了。
那么，我们今天的问题是，如果没有这个accept方法，TCP连接还能建立起来吗？
其实只要在执行accept()之前执行一个sleep(20)，然后立刻执行客户端相关的方法，同时抓个包，就能得出结论。
从抓包结果看来，就算不执行accept()方法，三次握手照常进行，并顺利建立连接。
更骚气的是，在服务端执行accept()前，如果客户端发送消息给服务端，服务端是能够正常回复ack确认包的。
并且，sleep(20)结束后，服务端正常执行accept()，客户端前面发送的消息，还是能正常收到的。
通过这个现象，我们可以多想想为什么。顺便好好了解下三次握手的细节。
---
## 三次握手的细节分析
我们先看面试八股文的老股，三次握手。
服务端代码，对socket执行bind方法可以绑定监听端口，然后执行listen方法后，就会进入监听（LISTEN）状态。内核会为每一个处于LISTEN状态的socket分配两个队列，分别叫半连接队列和全连接队列。
---
### 半连接队列、全连接队列是什么
- 半连接队列（SYN队列），服务端收到第一次握手后，会将sock加入到这个队列中，队列内的sock都处于SYN_RECV状态。
- 全连接队列（ACCEPT队列），在服务端收到第三次握手后，会将半连接队列的sock取出，放到全连接队列中。队列里的sock都处于ESTABLISHED状态。这里面的连接，就等着服务端执行accept()后被取出了。
看到这里，文章开头的问题就有了答案，建立连接的过程中根本不需要accept()参与，执行accept()只是为了从全连接队列里取出一条连接。
我们把话题再重新回到这两个队列上。
虽然都叫队列，但其实全连接队列（icsk_accept_queue）是个链表，而半连接队列（syn_table）是个哈希表。
---
### 为什么半连接队列要设计成哈希表
先对比下全连接里队列，他本质是个链表，因为也是线性结构，说它是个队列也没毛病。它里面放的都是已经建立完成的连接，这些连接正等待被取走。而服务端取走连接的过程中，并不关心具体是哪个连接，只要是个连接就行，所以直接从队列头取就行了。这个过程算法复杂度为O(1)。
而半连接队列却不太一样，因为队列里的都是不完整的连接，嗷嗷等待着第三次握手的到来。那么现在有一个第三次握手来了，则需要从队列里把相应IP端口的连接取出，如果半连接队列还是个链表，那我们就需要依次遍历，才能拿到我们想要的那个连接，算法复杂度就是O(n)。
而如果将半连接队列设计成哈希表，那么查找半连接的算法复杂度就回到O(1)了。
因此出于效率考虑，全连接队列被设计成链表，而半连接队列被设计为哈希表。
---
### 怎么观察两个队列的大小
---
#### 查看全连接队列
```
---
## ss -lnt
State Recv-Q Send-Q Local Address:Port Peer Address:Port
LISTEN 0 128 127.0.0.1:46269 *:*
```
通过ss -lnt命令，可以看到全连接队列的大小，其中Send-Q是指全连接队列的最大值，可以看到我这上面的最大值是128；Recv-Q是指当前的全连接队列的使用值，我这边用了0个，也就是全连接队列里为空，连接都被取出来了。
当上面Send-Q和Recv-Q数值很接近的时候，那么全连接队列可能已经满了。可以通过下面的命令查看是否发生过队列溢出。
```
---
## netstat -s | grep overflowed
4343 times the listen queue of a socket overflowed
```
上面说明发生过4343次全连接队列溢出的情况。这个查看到的是历史发生过的次数。
如果配合使用watch -d命令，可以自动每2s间隔执行相同命令，还能高亮显示变化的数字部分，如果溢出的数字不断变多，说明正在发生溢出的行为。
```
---
## watch -d 'netstat -s | grep overflowed'
Every 2.0s: netstat -s | grep overflowed
Fri Sep 17 09:00:45 2021
4343 times the listen queue of a socket overflowed
```
---
#### 查看半连接队列
半连接队列没有命令可以直接查看到，但因为半连接队列里，放的都是SYN_RECV状态的连接，那可以通过统计处于这个状态的连接的数量，间接获得半连接队列的长度。
```
---
## netstat -nt | grep -i '127.0.0.1:8080' | grep -i 'SYN_RECV' | wc -l
0
```
注意半连接队列和全连接队列都是挂在某个Listen socket上的，我这里用的是127.0.0.1:8080，大家可以替换成自己想要查看的IP端口。
可以看到我的机器上的半连接队列长度为0，这个很正常，正经连接谁会没事老待在半连接队列里。
当队列里的半连接不断增多，最终也是会发生溢出，可以通过下面的命令查看。
```
---
## netstat -s | grep -i "SYNs to LISTEN sockets dropped"
26395 SYNs to LISTEN sockets dropped
```
可以看到，我的机器上一共发生了26395次半连接队列溢出。同样建议配合watch -d命令使用。
```
---
## watch -d 'netstat -s | grep -i "SYNs to LISTEN sockets dropped"'
Every 2.0s: netstat -s | grep -i "SYNs to LISTEN sockets dropped"
Fri Sep 17 08:36:38 2021
26395 SYNs to LISTEN sockets dropped
```