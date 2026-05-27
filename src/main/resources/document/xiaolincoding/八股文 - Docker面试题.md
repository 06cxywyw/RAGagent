# 小林coding - Docker面试题
---
## docker面试题
---
## docker底层依托于linux怎么实现资源隔离的？
- 基于 Namespace 的视图隔离：Docker利用Linux命名空间（Namespace）来实现不同容器之间的隔离。每个容器都运行在自己的一组命名空间中，包括PID（进程）、网络、挂载点、IPC（进程间通信）等。这样，容器中的进程只能看到自己所在命名空间内的进程，而不会影响其他容器中的进程。
- 基于 cgroups 的资源隔离：cgroups 是Linux内核的一个功能，允许在进程组之间分配、限制和优先处理系统资源，如CPU、内存和磁盘I/O。它们提供了一种机制，用于管理和隔离进程集合的资源使用，有助于资源限制、工作负载隔离以及在不同进程组之间进行资源优先处理。
---
## 讲讲cgroup v2.0
cgroup v2 是 Linux cgroup API 的下一个版本。cgroup v2 提供了一个具有增强资源管理能力的统一控制系统。
cgroup v2 对 cgroup v1 进行了多项改进，例如：
- API 中单个统一的层次结构设计
- 更安全的子树委派给容器
- 更新的功能特性， 例如[压力阻塞信息（Pressure Stall Information，PSI）](https://www.kernel.org/doc/html/latest/accounting/psi.html)
- 跨多个资源的增强资源分配管理和隔离
- 统一核算不同类型的内存分配（网络内存、内核内存等）
- 考虑非即时资源变化，例如页面缓存回写
v1 的 cgroup 为每个控制器都使用独立的树(目录)
```
[root@docker cgroup]# ls /sys/fs/cgroup/ blkio cpu cpuacct cpuacct,cpu cpu,cpuacct cpuset devices freezer hugetlb memory net_cls net_cls,net_prio net_prio perf_event pids rdma systemd
```
每个目录就代表了一个 cgroup subsystem，比如要限制 cpu 则需要到 cpu 目录下创建子目录(树)，限制 memory 则需要到 memory 目录下去创建子目录(树)。
比如 Docker 就会在 cpu、memory 等等目录下都创建一个名为 docker 的目录，在 docker 目录下在根据 containerID 创建子目录来实现资源限制。
各个 Subsystem 各自为政，看起来比混乱，难以管理
因此最终的结果就是：
- 用户空间最后管理着多个非常类似的 hierarchy，
- 在执行 hierarchy 管理操作时，每个 hierarchy 上都重复着相同的操作。
v2 中对 cgroups 的最大更改是将重点放在简化层次结构上
- v1 为每个控制器使用独立的树（例如 /sys/fs/cgroup/cpu/GROUPNAME和 /sys/fs/cgroup/memory/GROUPNAME）。
- v2 将统一/sys/fs/cgroup/GROUPNAME中的树，如果进程 X 加入/sys/fs/cgroup/test，则启用 test 的每个控制器都将控制进程 X。
---
## Docker 和虚拟机有什么区别？
核心区别：虚拟机虚拟化的是操作系统，Docker 虚拟化的是进程。
- 虚拟机（VM）：通过 Hypervisor 在宿主机上模拟一整套硬件，每台 VM 都跑着一个完整的 Guest OS 内核，隔离性极强但开销大——启动要几十秒、镜像几个 GB、单实例内存占用 GB 级别。
- Docker 容器：所有容器共享宿主机的 Linux 内核，通过 Namespace 做视图隔离、cgroups 做资源限制，本质上容器就是一组被隔离起来的特殊进程。启动秒级、镜像几十到几百 MB、内存开销 MB 级别。
形象一点说：VM 像"独立的房子"，容器像"同一栋楼里的房间"。容器牺牲了一点隔离性（共用内核），换来了远高于 VM 的启动速度和资源利用率，这也是云原生时代首选 Docker 的根本原因。
---
## Docker 有哪几个核心组件？
主要是三个：
- 镜像（Image）：只读的模板，包含了运行一个应用所需要的代码、依赖、环境变量、配置等，相当于"安装包"。
- 容器（Container）：镜像的运行时实例，可以启动、停止、删除，是一个独立隔离的进程组，相当于"安装后运行起来的程序"。
- 仓库（Registry）：存储和分发镜像的地方，分公有仓库（如 Docker Hub）和私有仓库（如 Harbor、阿里云 ACR、腾讯云 TCR），类似于"应用商店"。
三者的协作流程是：从 Registry 拉镜像 → 由镜像启动容器 → 容器运行应用。
---
## 镜像和容器有什么区别？
最常被问的基础题，一句话记住：镜像是静态的模板，容器是镜像的动态运行实例。
类比关系就像编程里的类（Class）和对象（Object）：
- 镜像 = 类，定义了应用的结构和行为，是只读的
- 容器 = 对象，是镜像被启动后的具体实例，有自己的文件系统读写层、网络、进程
一个镜像可以启动多个容器实例，每个容器之间互不影响；停止/删除容器也不会影响镜像本身。
---
## Docker 镜像的分层原理是什么？
Docker 镜像采用分层只读的结构，底层基于UnionFS（联合文件系统），现代 Docker 主要使用overlay2作为默认的存储驱动。
Dockerfile 里每一条指令都会产生一个新的镜像层，这些层都是只读的。例如：
```
FROM ubuntu:22.04 # 层 1
RUN apt-get update # 层 2
COPY app /app # 层 3
CMD ["./app"] # 层 4
```
当容器启动时，Docker 会在所有只读层之上再叠加一层可写层（容器层），容器对文件的任何修改都发生在这一层，通过Copy-on-Write（写时复制）机制实现。
分层带来的好处：
- 共享与复用：多个镜像可以共享相同的底层（比如都基于ubuntu:22.04），节省存储和网络传输
- 构建缓存：重新构建时，只要某一层没变就直接复用缓存，速度极快
- 增量分发：docker pull只会下载变化的那一层
这也解释了 Dockerfile 最佳实践里的一条重要原则：把"不常变的层"（如依赖安装）放在"常变的层"（如 COPY 源码）之前，这样缓存命中率更高、构建更快。
---
## Dockerfile 常用指令有哪些？
面试一般不会考冷门指令，记住这几个就足够：
- FROM：指定基础镜像，必须是 Dockerfile 的第一条指令
- WORKDIR：设置容器内的工作目录，相当于cd
- COPY/ADD：把宿主机的文件拷贝到镜像里
- RUN：在构建阶段执行命令（如安装依赖），每条RUN产生一个新层
- ENV：设置环境变量（运行时也能看到）
- ARG：构建时的参数，只在docker build阶段有效
- EXPOSE：声明容器要监听的端口（只是声明，不会真的开放端口）
- VOLUME：声明数据卷挂载点
- CMD/ENTRYPOINT：指定容器启动时默认要运行的命令
- USER：切换到非 root 用户运行
一个典型的 Java Spring Boot 应用 Dockerfile：
```
FROM openjdk:17-jdk-slim
WORKDIR /app
COPY target/app.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```
---
## Dockerfile 中 CMD 和 ENTRYPOINT 有什么区别？
两者都用于指定容器启动时执行的命令，但有微妙而关键的区别：
- CMD：提供"默认命令"，可以被docker run后面跟的参数完全覆盖。
- ENTRYPOINT：设置容器的"主命令"，不会被docker run覆盖，后面跟的参数会作为参数追加到 ENTRYPOINT 后面。
推荐组合用法：ENTRYPOINT设主命令，CMD设默认参数，这样用户既能使用默认行为，也能灵活传参：
```
ENTRYPOINT ["java", "-jar", "app.jar"]
CMD ["--spring.profiles.active=prod"]
```
- docker run myapp：运行java -jar app.jar --spring.profiles.active=prod
- docker run myapp --server.port=9090：运行java -jar app.jar --server.port=9090（--server.port=9090覆盖了 CMD）
另外，两者都有两种语法写法：
- exec 形式（推荐）：CMD ["java", "-jar", "app.jar"]，直接 exec，PID=1 就是你的进程，能正确接收 SIGTERM 等信号，优雅停止
- shell 形式：CMD java -jar app.jar，会通过/bin/sh -c启动，PID=1 其实是 sh，容器停止时信号传不到应用进程，可能导致无法优雅退出
---
## Dockerfile 中 COPY 和 ADD 有什么区别？
两者都是把文件从宿主机拷贝到镜像里，但ADD 多了两个"魔法"功能：
- 自动解压：如果源文件是tar.gz之类的压缩包，ADD会自动解压到目标目录
- 支持 URL：ADD可以直接从 URL 下载远程文件到镜像里
听起来方便，但官方和 Docker 最佳实践都推荐优先使用COPY，原因是：
- ADD的行为"太聪明"反而不透明，容易出 bug
- 如果需要下载远程文件，推荐用RUN curl -fLO https://... && ...明确写出来，行为可控
- 如果需要解压，在RUN里显式处理更清晰
简单原则：除非你明确需要ADD的自动解压或 URL 下载功能，否则一律用COPY。
---
## 什么是多阶段构建（multi-stage build）？有什么好处？
多阶段构建是 Docker 17.05 引入的一个重要特性，允许在一个 Dockerfile 里写多个FROM，每个FROM开启一个"构建阶段"，后面的阶段可以从前面的阶段拷贝文件，但最终只有最后一个阶段的镜像会被保留。
核心价值：把"构建环境"和"运行环境"分开，大幅减小最终镜像体积。
以一个 Go 应用为例，传统做法：
```
FROM golang:1.21
COPY . /src
RUN cd /src && go build -o /app
CMD ["/app"]
```
问题是最终镜像里包含了整个 Go 编译器、依赖、源码，可能有 800MB+。
多阶段构建写法：
```
---
## 第一阶段：构建
FROM golang:1.21 AS builder
WORKDIR /src
COPY . .
RUN go build -o app
---
## 第二阶段：运行
FROM alpine:3.18
COPY --from=builder /src/app /app
CMD ["/app"]
```
最终镜像只基于 alpine（5MB）加上编译好的二进制，可能只有 15MB，瘦身 50 倍。Java、Node.js、前端项目都适合用这种模式。
---
## 如何减小 Docker 镜像体积？
常见手段，面试可以组合说出：
- 选小的基础镜像：用alpine（5MB）代替ubuntu（70MB+），用openjdk:17-jre-slim代替openjdk:17
- 多阶段构建：构建和运行分离，最终镜像只保留运行所需的产物
- 合并 RUN 指令：每条RUN都会产生一个新层，用&&把多个命令合并成一条RUN，减少层数
- 清理构建中间产物：在同一条RUN里装完包就立刻清理缓存，例如：```
RUN apt-get update && apt-get install -y curl \
&& rm -rf /var/lib/apt/lists/*
```
- 使用.dockerignore：像.gitignore一样，排除不需要 COPY 进镜像的文件（比如node_modules、.git、日志文件）
- 避免在镜像里装无关调试工具：调试工具应该在需要时docker exec临时装，不该塞进生产镜像
---
## Docker 容器数据持久化有哪些方式？
容器本身是"用完即扔"的，想持久化数据必须用外部存储。Docker 提供三种方式：
- Volume（数据卷）：Docker 官方推荐。由 Docker 管理，默认存储在宿主机的/var/lib/docker/volumes/下，可以用docker volume系列命令管理，最通用也最推荐。```
docker run -v mydata:/app/data myimage
```
- Bind Mount（目录挂载）：把宿主机的任意路径直接挂进容器，灵活但耦合宿主机路径、不利于迁移，适合开发阶段的热更新调试。```
docker run -v /home/user/code:/app myimage
```
- tmpfs：挂载到宿主机内存里，容器停止数据就没了，适合存放敏感临时数据（如解密后的密钥、临时缓存）。
常见的最佳实践是：开发阶段用 bind mount 方便热更新，生产环境用 volume 保证可移植性和可管理性。
---
## Docker 的网络模式有哪些？
Docker 默认提供五种网络模式：
- bridge（默认）：Docker 创建一个 docker0 虚拟网桥，每个容器分配独立 IP，容器之间通过网桥通信，访问外网通过 NAT。单机多容器的默认场景。
- host：容器直接使用宿主机的网络栈，不做隔离。性能最好但会和宿主机抢端口，无法在一台机器上起多个监听同一端口的容器。
- none：容器没有任何网络，只有 loopback。适合完全不需要网络的纯计算任务。
- container：和指定的另一个容器共享同一个网络栈（Kubernetes 里 Pod 内多个容器就是类似机制）。
- overlay：跨宿主机的网络，通常在 Docker Swarm 或 Kubernetes 里使用。
日常接触最多的是bridge，跨主机通信是overlay。
---
## 同一个宿主机上的多个容器之间怎么通信？
有几种常见方式：
- 默认 bridge 网络（不推荐）：通过容器的 IP 直接访问，但 IP 不固定、也不支持容器名 DNS 解析。
- 自定义 bridge 网络（推荐）：自己创建一个网络，加入同一网络的容器之间可以直接用容器名作为 DNS 名互访：```
docker network create mynet
docker run -d --name redis --network mynet redis
docker run -d --name app --network mynet myapp
---
## app 容器里可以直接通过 "redis:6379" 访问 redis
```
- host 模式：所有容器共享宿主机网络，直接通过localhost:port访问，但失去了端口隔离。
- 通过 Docker Compose：Compose 会自动为一个 project 创建一个 bridge 网络，service 名就是容器名，互访非常方便。
生产中最常用的组合是自定义网络 + 容器名 DNS，既保留了隔离又方便访问。
---
## Docker Compose 是什么？什么场景用？
Docker Compose 是 Docker 官方提供的单机容器编排工具，用一个 YAML 文件定义一组相关服务，然后一条命令启动或停止整组服务。
典型场景：本地开发或小型单机部署一套"Web 应用 + 数据库 + 缓存"的组合。
```
---
## docker-compose.yml
version: "3.9"
services:
web:
build: .
ports:
- "8080:8080"
depends_on:
- db
- redis
db:
image: mysql:8
environment:
MYSQL_ROOT_PASSWORD: root
volumes:
- db_data:/var/lib/mysql
redis:
image: redis:7
volumes:
db_data:
```
常用命令：
- docker compose up -d：后台启动所有服务
- docker compose down：停止并删除所有服务
- docker compose logs -f：实时查看日志
- docker compose ps：查看服务状态
需要注意：Docker Compose 只解决单机编排；跨主机编排应该用Docker Swarm或者Kubernetes。
---
## Docker 常用命令有哪些？
面试里经常让你当场说几个常用命令，下面这些是必须记住的：
镜像相关：
- docker pull <image>：拉镜像
- docker images：列出本地镜像
- docker rmi <image>：删除镜像
- docker build -t name:tag .：基于当前目录的 Dockerfile 构建镜像
容器相关：
- docker run -d -p 8080:80 --name web nginx：启动一个后台容器
- docker ps：查看运行中的容器（加-a看所有）
- docker stop / start / restart <container>：停止 / 启动 / 重启
- docker rm <container>：删除容器
- docker logs -f <container>：查看日志（-f实时跟踪）
- docker exec -it <container> bash：进入容器
- docker inspect <container>：查看详细信息（JSON 格式）
- docker stats：查看容器资源占用
系统相关：
- docker system df：查看 Docker 占用了多少磁盘
- docker system prune：清理无用资源
---
## 如何进入一个运行中的容器？
最常用的方式是docker exec：
```
docker exec -it bash