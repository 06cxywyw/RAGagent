# JavaGuide - Java基础

> 来源: https://javaguide.cn/home.html

# Java 面试指南（JavaGuide 后端通用面试题总结）
[Guide](https://javaguide.cn/article/)约 3101 字大约 10 分钟[![JavaGuide 官方知识星球](https://oss.javaguide.cn/xingqiu/xingqiu.png)](https://javaguide.cn/about-the-author/zhishixingqiu-two-years.html)

JavaGuide 是一份系统化的Java 面试指南和后端通用面试复习资料，内容覆盖 Java 基础、集合、并发编程、JVM、Spring/Spring Boot、MySQL、Redis、分布式、高并发、高可用和系统设计等核心知识点。

如果你正在准备校招、社招或跳槽面试，可以从[Java 后端面试通关计划](https://javaguide.cn/interview-preparation/backend-interview-plan.html)开始，再按下面的模块逐步复习高频 Java 八股文和后端面试题。

本站所有内容都已免费开源，欢迎一起[维护完善](http://localhost:8080/javaguide/contribution-guideline.html)，有帮助的话，欢迎 Star！

- 项目地址：[https://github.com/Snailclimb/JavaGuide](https://github.com/Snailclimb/JavaGuide)
- 在线阅读：[https://javaguide.cn/](https://javaguide.cn/)

---
## 面试准备

- [⭐Java 后端面试通关计划（涵盖后端通用体系）](https://javaguide.cn/interview-preparation/backend-interview-plan.html)(一定要看 👍)
- [如何高效准备 Java 面试？](https://javaguide.cn/interview-preparation/teach-you-how-to-prepare-for-the-interview-hand-in-hand.html)
- [Java 后端面试重点总结](https://javaguide.cn/interview-preparation/key-points-of-interview.html)
- [Java 学习路线（最新版，4w+ 字）](https://javaguide.cn/interview-preparation/java-roadmap.html)
- [程序员简历编写指南](https://javaguide.cn/interview-preparation/resume-guide.html)
- [项目经验指南](https://javaguide.cn/interview-preparation/project-experience-guide.html)
- [面试太紧张怎么办？](https://javaguide.cn/interview-preparation/how-to-handle-interview-nerves.html)
- [校招没有实习经历怎么办？实习经历怎么写？](https://javaguide.cn/interview-preparation/internship-experience.html)

---
## Java

---
### 基础
知识点/面试题总结: (必看👍 )：

- [Java 基础常见知识点&面试题总结(上)](https://javaguide.cn/java/basis/java-basic-questions-01.html)
- [Java 基础常见知识点&面试题总结(中)](https://javaguide.cn/java/basis/java-basic-questions-02.html)
- [Java 基础常见知识点&面试题总结(下)](https://javaguide.cn/java/basis/java-basic-questions-03.html)

重要知识点详解：

- [为什么 Java 中只有值传递？](https://javaguide.cn/java/basis/why-there-only-value-passing-in-java.html)
- [Java 序列化详解](https://javaguide.cn/java/basis/serialization.html)
- [泛型&通配符详解](https://javaguide.cn/java/basis/generics-and-wildcards.html)
- [Java 反射机制详解](https://javaguide.cn/java/basis/reflection.html)
- [Java 代理模式详解](https://javaguide.cn/java/basis/proxy.html)
- [BigDecimal 详解](https://javaguide.cn/java/basis/bigdecimal.html)
- [Java 魔法类 Unsafe 详解](https://javaguide.cn/java/basis/unsafe.html)
- [Java SPI 机制详解](https://javaguide.cn/java/basis/spi.html)
- [Java 语法糖详解](https://javaguide.cn/java/basis/syntactic-sugar.html)

---
### 集合
知识点/面试题总结：

- [Java 集合常见知识点&面试题总结(上)](https://javaguide.cn/java/collection/java-collection-questions-01.html)(必看 👍)
- [Java 集合常见知识点&面试题总结(下)](https://javaguide.cn/java/collection/java-collection-questions-02.html)(必看 👍)
- [Java 集合使用注意事项总结](https://javaguide.cn/java/collection/java-collection-precautions-for-use.html)

源码分析：

- [ArrayList 核心源码+扩容机制分析](https://javaguide.cn/java/collection/arraylist-source-code.html)
- [LinkedList 核心源码分析](https://javaguide.cn/java/collection/linkedlist-source-code.html)
- [HashMap 核心源码+底层数据结构分析](https://javaguide.cn/java/collection/hashmap-source-code.html)
- [ConcurrentHashMap 核心源码+底层数据结构分析](https://javaguide.cn/java/collection/concurrent-hash-map-source-code.html)
- [LinkedHashMap 核心源码分析](https://javaguide.cn/java/collection/linkedhashmap-source-code.html)
- [CopyOnWriteArrayList 核心源码分析](https://javaguide.cn/java/collection/copyonwritearraylist-source-code.html)
- [ArrayBlockingQueue 核心源码分析](https://javaguide.cn/java/collection/arrayblockingqueue-source-code.html)
- [PriorityQueue 核心源码分析](https://javaguide.cn/java/collection/priorityqueue-source-code.html)
- [DelayQueue 核心源码分析](https://javaguide.cn/java/collection/priorityqueue-source-code.html)

---
### IO

- [IO 基础知识总结](https://javaguide.cn/java/io/io-basis.html)
- [IO 设计模式总结](https://javaguide.cn/java/io/io-design-patterns.html)
- [IO 模型详解](https://javaguide.cn/java/io/io-model.html)
- [NIO 核心知识总结](https://javaguide.cn/java/io/nio-basis.html)

---
### 并发
知识点/面试题总结: (必看 👍)

- [Java 并发常见知识点&面试题总结（上）](https://javaguide.cn/java/concurrent/java-concurrent-questions-01.html)
- [Java 并发常见知识点&面试题总结（中）](https://javaguide.cn/java/concurrent/java-concurrent-questions-02.html)
- [Java 并发常见知识点&面试题总结（下）](https://javaguide.cn/java/concurrent/java-concurrent-questions-03.html)

重要知识点详解：

- [乐观锁和悲观锁详解](https://javaguide.cn/java/concurrent/optimistic-lock-and-pessimistic-lock.html)
- [CAS 详解](https://javaguide.cn/java/concurrent/cas.html)
- [JMM（Java 内存模型）详解](https://javaguide.cn/java/concurrent/jmm.html)
- 线程池：[Java 线程池详解](https://javaguide.cn/java/concurrent/java-thread-pool-summary.html)、[Java 线程池最佳实践](https://javaguide.cn/java/concurrent/java-thread-pool-best-practices.html)
- [ThreadLocal 详解](https://javaguide.cn/java/concurrent/threadlocal.html)
- [Java 并发容器总结](https://javaguide.cn/java/concurrent/java-concurrent-collections.html)
- [Atomic 原子类总结](https://javaguide.cn/java/concurrent/atomic-classes.html)
- [AQS 详解](https://javaguide.cn/java/concurrent/aqs.html)
- [CompletableFuture 详解](https://javaguide.cn/java/concurrent/completablefuture-intro.html)

---
### JVM (必看 👍)
JVM 这部分内容主要参考[JVM 虚拟机规范-Java8](https://docs.oracle.com/javase/specs/jvms/se8/html/index.html)和周志明老师的[《深入理解 Java 虚拟机（第 3 版）》](https://book.douban.com/subject/34907497/)（强烈建议阅读多遍！）。

- [Java 内存区域](https://javaguide.cn/java/jvm/memory-area.html)
- [JVM 垃圾回收](https://javaguide.cn/java/jvm/jvm-garbage-collection.html)
- [类文件结构](https://javaguide.cn/java/jvm/class-file-structure.html)
- [类加载过程](https://javaguide.cn/java/jvm/class-loading-process.html)
- [类加载器](https://javaguide.cn/java/jvm/classloader.html)
- [【待完成】最重要的 JVM 参数总结（翻译完善了一半）](https://javaguide.cn/java/jvm/jvm-parameters-intro.html)
- [【加餐】大白话带你认识 JVM](https://javaguide.cn/java/jvm/jvm-intro.html)
- [JDK 监控和故障处理工具](https://javaguide.cn/java/jvm/jdk-monitoring-and-troubleshooting-tools.html)

---
### 新特性

- Java 8：[Java 8 新特性总结（翻译）](https://javaguide.cn/java/new-features/java8-tutorial-translate.html)、[Java8 常用新特性总结](https://javaguide.cn/java/new-features/java8-common-new-features.html)
- [Java 9 新特性概览](https://javaguide.cn/java/new-features/java9.html)
- [Java 10 新特性概览](https://javaguide.cn/java/new-features/java10.html)
- [Java 11 新特性概览](https://javaguide.cn/java/new-features/java11.html)
- [Java 12 & 13 新特性概览](https://javaguide.cn/java/new-features/java12-13.html)
- [Java 14 & 15 新特性概览](https://javaguide.cn/java/new-features/java14-15.html)
- [Java 16 新特性概览](https://javaguide.cn/java/new-features/java16.html)
- [Java 17 新特性概览](https://javaguide.cn/java/new-features/java17.html)
- [Java 18 新特性概览](https://javaguide.cn/java/new-features/java18.html)
- [Java 19 新特性概览](https://javaguide.cn/java/new-features/java19.html)
- [Java 20 新特性概览](https://javaguide.cn/java/new-features/java20.html)
- [Java 21 新特性概览](https://javaguide.cn/java/new-features/java21.html)
- [Java 22 & 23 新特性概览](https://javaguide.cn/java/new-features/java22-23.html)
- [Java 24 新特性概览](https://javaguide.cn/java/new-features/java24.html)
- [Java 25 新特性概览](https://javaguide.cn/java/new-features/java25.html)

---
## 计算机基础
计算机基础（计算机网络、操作系统、数据结构与算法）已独立为单独模块，详见[计算机基础知识总结](https://javaguide.cn/cs-basics/)。

[![Banner](https://oss.javaguide.cn/xingqiu/xingqiu.png)](https://javaguide.cn/about-the-author/zhishixingqiu-two-years.html)

---
## 数据库

---
### 基础

- [数据库基础知识总结](https://javaguide.cn/database/basis.html)
- [NoSQL 基础知识总结](https://javaguide.cn/database/nosql.html)
- [字符集详解](https://javaguide.cn/database/character-set.html)
- SQL :[SQL 语法基础知识总结](https://javaguide.cn/database/sql/sql-syntax-summary.html)[SQL 常见面试题总结](https://javaguide.cn/database/sql/sql-questions-01.html)
- [SQL 语法基础知识总结](https://javaguide.cn/database/sql/sql-syntax-summary.html)
- [SQL 常见面试题总结](https://javaguide.cn/database/sql/sql-questions-01.html)

---
### MySQL
知识点/面试题总结：

- [MySQL 常见知识点&面试题总结](https://javaguide.cn/database/mysql/mysql-questions-01.html)(必看 👍)
- [MySQL 高性能优化规范建议总结](https://javaguide.cn/database/mysql/mysql-high-performance-optimization-specification-recommendations.html)

重要知识点：

- [MySQL 索引详解](https://javaguide.cn/database/mysql/mysql-index.html)
- [MySQL 索引失效场景总结](https://javaguide.cn/database/mysql/mysql-index-invalidation.html)
- [MySQL 事务隔离级别图文详解)](https://javaguide.cn/database/mysql/transaction-isolation-level.html)
- [MySQL 三大日志(binlog、redo log 和 undo log)详解](https://javaguide.cn/database/mysql/mysql-logs.html)
- [InnoDB 存储引擎对 MVCC 的实现](https://javaguide.cn/database/mysql/innodb-implementation-of-mvcc.html)
- [SQL 语句在 MySQL 中的执行过程](https://javaguide.cn/database/mysql/how-sql-executed-in-mysql.html)
- [MySQL 查询缓存详解](https://javaguide.cn/database/mysql/mysql-query-cache.html)
- [MySQL 执行计划分析](https://javaguide.cn/database/mysql/mysql-query-execution-plan.html)
- [MySQL 自增主键一定是连续的吗](https://javaguide.cn/database/mysql/mysql-auto-increment-primary-key-continuous.html)
- [MySQL 时间类型数据存储建议](https://javaguide.cn/database/mysql/some-thoughts-on-database-storage-time.html)
- [MySQL 隐式转换造成索引失效](https://javaguide.cn/database/mysql/index-invalidation-caused-by-implicit-conversion.html)

---
### Redis
知识点/面试题总结: (必看👍 )：

- [Redis 常见知识点&面试题总结(上)](https://javaguide.cn/database/redis/redis-questions-01.html)
- [Redis 常见知识点&面试题总结(下)](https://javaguide.cn/database/redis/redis-questions-02.html)

重要知识点：

- [3 种常用的缓存读写策略详解](https://javaguide.cn/database/redis/3-commonly-used-cache-read-and-write-strategies.html)
- [Redis 能做消息队列吗？怎么实现？](https://javaguide.cn/database/redis/redis-stream-mq.html)
- [Redis 5 种基本数据结构详解](https://javaguide.cn/database/redis/redis-data-structures-01.html)
- [Redis 3 种特殊数据结构详解](https://javaguide.cn/database/redis/redis-data-structures-02.html)
- [Redis 持久化机制详解](https://javaguide.cn/database/redis/redis-persistence.html)
- [Redis 内存碎片详解](https://javaguide.cn/database/redis/redis-memory-fragmentation.html)
- [Redis 常见阻塞原因总结](https://javaguide.cn/database/redis/redis-common-blocking-problems-summary.html)
- [Redis 集群详解](https://javaguide.cn/database/redis/redis-cluster.html)

---
### MongoDB

- [MongoDB 常见知识点&面试题总结(上)](https://javaguide.cn/database/mongodb/mongodb-questions-01.html)
- [MongoDB 常见知识点&面试题总结(下)](https://javaguide.cn/database/mongodb/mongodb-questions-02.html)

---
## 搜索引擎
[Elasticsearch 常见面试题总结(付费)](https://javaguide.cn/database/elasticsearch/elasticsearch-questions-01.html)

![JavaGuide 官方公众号](https://oss.javaguide.cn/github/javaguide/gongzhonghaoxuanchuan.png)

---
## 开发工具

---
### Maven

- [Maven 核心概念总结](https://javaguide.cn/tools/maven/maven-core-concepts.html)
- [Maven 最佳实践](https://javaguide.cn/tools/maven/maven-best-practices.html)

---
### Gradle
[Gradle 核心概念总结](https://javaguide.cn/tools/gradle/gradle-core-concepts.html)（可选，目前国内还是使用 Maven 普遍一些）

---
### Docker

- [Docker 核心概念总结](https://javaguide.cn/tools/docker/docker-intro.html)
- [Docker 实战](https://javaguide.cn/tools/docker/docker-in-action.html)

---
### Git

- [Git 核心概念总结](https://javaguide.cn/tools/git/git-intro.html)
- [GitHub 实用小技巧总结](https://javaguide.cn/tools/git/github-tips.html)

---
## 系统设计

- [⭐系统设计常见面试题总结](https://javaguide.cn/system-design/system-design-questions.html)
- [⭐设计模式常见面试题总结](https://interview.javaguide.cn/system-design/design-pattern.html)

---
### 基础

- [RestFul API 简明教程](https://javaguide.cn/system-design/basis/RESTfulAPI.html)
- [软件工程简明教程](https://javaguide.cn/system-design/basis/software-engineering.html)
- [代码命名指南](https://javaguide.cn/system-design/basis/naming.html)
- [代码重构指南](https://javaguide.cn/system-design/basis/refactoring.html)
- [单元测试指南](https://javaguide.cn/system-design/basis/unit-test.html)

---
### 常用框架

---
#### Spring/SpringBoot (必看 👍)
知识点/面试题总结:

- [Spring 常见知识点&面试题总结](https://javaguide.cn/system-design/framework/spring/spring-knowledge-and-questions-summary.html)
- [SpringBoot 常见知识点&面试题总结](https://javaguide.cn/system-design/framework/spring/springboot-knowledge-and-questions-summary.html)
- [Spring/Spring Boot 常用注解总结](https://javaguide.cn/system-design/framework/spring/spring-common-annotations.html)
- [SpringBoot 入门指南](https://github.com/Snailclimb/springboot-guide)

重要知识点详解：

- [IoC & AOP 详解（快速搞懂）](https://javaguide.cn/system-design/framework/spring/ioc-and-aop.html)
- [Spring 事务详解](https://javaguide.cn/system-design/framework/spring/spring-transaction.html)
- [Spring 中的设计模式详解](https://javaguide.cn/system-design/framework/spring/spring-design-patterns-summary.html)
- [SpringBoot 自动装配原理详解](https://javaguide.cn/system-design/framework/spring/spring-boot-auto-assembly-principles.html)

---
#### MyBatis
[MyBatis 常见面试题总结](https://javaguide.cn/system-design/framework/mybatis/mybatis-interview.html)

---
### 安全

---
#### 认证授权

- [认证授权基础概念详解](https://javaguide.cn/system-design/security/basis-of-authority-certification.html)
- [JWT 基础概念详解](https://javaguide.cn/system-design/security/jwt-intro.html)
- [JWT 优缺点分析以及常见问题解决方案](https://javaguide.cn/system-design/security/advantages-and-disadvantages-of-jwt.html)
- [SSO 单点登录详解](https://javaguide.cn/system-design/security/sso-intro.html)
- [权限系统设计详解](https://javaguide.cn/system-design/security/design-of-authority-system.html)

---
#### 数据安全

- [常见加密算法总结](https://javaguide.cn/system-design/security/encryption-algorithms.html)
- [敏感词过滤方案总结](https://javaguide.cn/system-design/security/sentive-words-filter.html)
- [数据脱敏方案总结](https://javaguide.cn/system-design/security/data-desensitization.html)
- [为什么前后端都要做数据校验](https://javaguide.cn/system-design/security/data-validation.html)
- [为什么忘记密码时只能重置，不能告诉你原密码？](https://javaguide.cn/system-design/security/why-password-reset-instead-of-retrieval.html)

---
### 定时任务
[Java 定时任务详解](https://javaguide.cn/system-design/schedule-task.html)

---
### Web 实时消息推送
[Web 实时消息推送详解](https://javaguide.cn/system-design/web-real-time-message-push.html)

---
## 分布式

- [⭐分布式高频面试题](https://interview.javaguide.cn/distributed-system/distributed-system.html)

---
### 理论&算法&协议

- [CAP 理论和 BASE 理论解读](https://javaguide.cn/distributed-system/protocol/cap-and-base-theorem.html)
- [Paxos 算法解读](https://javaguide.cn/distributed-system/protocol/paxos-algorithm.html)
- [Raft 算法解读](https://javaguide.cn/distributed-system/protocol/raft-algorithm.html)
- [ZAB 协议解读](https://javaguide.cn/distributed-system/protocol/zab.html)
- [Gossip 协议详解](https://javaguide.cn/distributed-system/protocol/gossip-protocol.html)
- [一致性哈希算法详解](https://javaguide.cn/distributed-system/protocol/consistent-hashing.html)

---
### RPC

- [RPC 基础知识总结](https://javaguide.cn/distributed-system/rpc/rpc-intro.html)
- [Dubbo 常见知识点&面试题总结](https://javaguide.cn/distributed-system/rpc/dubbo.html)

---
### ZooKeeper
这两篇文章可能有内容重合部分，推荐都看一遍。

- [ZooKeeper 相关概念总结(入门)](https://javaguide.cn/distributed-system/distributed-process-coordination/zookeeper/zookeeper-intro.html)
- [ZooKeeper 相关概念总结(进阶)](https://javaguide.cn/distributed-system/distributed-process-coordination/zookeeper/zookeeper-plus.html)

---
### API 网关

- [API 网关基础知识总结](https://javaguide.cn/distributed-system/api-gateway.html)
- [Spring Cloud Gateway 常见知识点&面试题总结](https://javaguide.cn/distributed-system/spring-cloud-gateway-questions.html)

---
### 分布式 ID

- [分布式 ID 常见知识点&面试题总结](https://javaguide.cn/distributed-system/distributed-id.html)
- [分布式 ID 设计指南](https://javaguide.cn/distributed-system/distributed-id-design.html)

---
### 分布式锁

- [分布式锁介绍](https://javaguide.cn/distributed-system/distributed-lock.html)
- [分布式锁常见实现方案总结](https://javaguide.cn/distributed-system/distributed-lock-implementations.html)

---
### 分布式事务
[分布式事务常见知识点&面试题总结](https://javaguide.cn/distributed-system/distributed-transaction.html)

---
### 分布式配置中心
[分布式配置中心常见知识点&面试题总结](https://javaguide.cn/distributed-system/distributed-configuration-center.html)

---
## 高性能

---
### 数据库优化

- [数据库读写分离和分库分表](https://javaguide.cn/high-performance/read-and-write-separation-and-library-subtable.html)
- [数据冷热分离](https://javaguide.cn/high-performance/data-cold-hot-separation.html)
- [常见 SQL 优化手段总结](https://javaguide.cn/high-performance/sql-optimization.html)
- [深度分页介绍及优化建议](https://javaguide.cn/high-performance/deep-pagination-optimization.html)

---
### 负载均衡
[负载均衡常见知识点&面试题总结](https://javaguide.cn/high-performance/load-balancing.html)

---
### CDN
[CDN（内容分发网络）常见知识点&面试题总结](https://javaguide.cn/high-performance/cdn.html)

---
### 消息队列

- [消息队列基础知识总结](https://javaguide.cn/high-performance/message-queue/message-queue.html)
- [Disruptor 常见知识点&面试题总结](https://javaguide.cn/high-performance/message-queue/disruptor-questions.html)
- [RabbitMQ 常见知识点&面试题总结](https://javaguide.cn/high-performance/message-queue/rabbitmq-questions.html)
- [RocketMQ 常见知识点&面试题总结](https://javaguide.cn/high-performance/message-queue/rocketmq-questions.html)
- [Kafka 常见知识点&面试题总结](https://javaguide.cn/high-performance/message-queue/kafka-questions-01.html)

---
## 高可用
[高可用系统设计指南](https://javaguide.cn/high-availability/high-availability-system-design.html)

---
### 冗余设计
[冗余设计详解](https://javaguide.cn/high-availability/redundancy.html)

---
### 限流
[服务限流详解](https://javaguide.cn/high-availability/limit-request.html)

---
### 降级&熔断
[降级&熔断详解](https://javaguide.cn/high-availability/fallback-and-circuit-breaker.html)

---
### 超时&重试
[超时&重试详解](https://javaguide.cn/high-availability/timeout-and-retry.html)

---
### 集群
相同的服务部署多份，避免单点故障。

---
### 灾备设计和异地多活
灾备= 容灾 + 备份。

- 备份：将系统所产生的所有重要数据多备份几份。
- 容灾：在异地建立两个完全相同的系统。当某个地方的系统突然挂掉，整个应用系统可以切换到另一个，这样系统就可以正常提供服务了。

异地多活描述的是将服务部署在异地并且服务同时对外提供服务。和传统的灾备设计的最主要区别在于“多活”，即所有站点都是同时在对外提供服务的。异地多活是为了应对突发状况比如火灾、地震等自然或者人为灾害。

---
## Star 趋势
![Stars](https://api.star-history.com/svg?repos=Snailclimb/JavaGuide&type=Date)

---
## 公众号
如果大家想要实时关注我更新的文章以及分享的干货的话，可以关注我的公众号“JavaGuide”。

![JavaGuide 官方公众号](https://oss.javaguide.cn/github/javaguide/gongzhonghaoxuanchuan.png)