# 小林coding - MySQL-字节面试加锁
---
## 字节面试：加了什么锁，导致死锁的？
大家好，我是小林。
之前收到读者面试字节时，被问到一个关于 MySQL 的问题。
如果对 MySQL 加锁机制比较熟悉的同学，应该一眼就能看出会发生死锁，但是具体加了什么锁而导致死锁，是需要我们具体分析的。
接下来，就跟聊聊上面两个事务执行 SQL 语句的过程中，加了什么锁，从而导致死锁的。
---
## 准备工作
先创建一张 t_student 表，假设除了 id 字段，其他字段都是普通字段。
```
CREATE TABLE `t_student` (
`id` int NOT NULL,
`no` varchar(255) DEFAULT NULL,
`name` varchar(255) DEFAULT NULL,
`age` int DEFAULT NULL,
`score` int DEFAULT NULL,
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
然后，插入相关的数据后，t_student 表中的记录如下：
---
## 开始实验
在实验开始前，先说明下实验环境：
- MySQL 版本：8.0.26
- 隔离级别：可重复读（RR）
启动两个事务，按照题目的 SQL 执行顺序，过程如下表格：
可以看到，事务 A 和 事务 B 都在执行 insert 语句后，都陷入了等待状态（前提没有打开死锁检测），也就是发生了死锁，因为都在相互等待对方释放锁。
---
## 为什么会发生死锁？
我们可以通过select * from performance_schema.data_locks\G;这条语句，查看事务执行 SQL 过程中加了什么锁。
接下来，针对每一条 SQL 语句分析具体加了什么锁。
---
### Time 1 阶段加锁分析
Time 1 阶段，事务 A 执行以下语句：
```
---
## 事务 A
mysql> begin;
Query OK, 0 rows affected (0.00 sec)
mysql> update t_student set score = 100 where id = 25;
Query OK, 0 rows affected (0.01 sec)
Rows matched: 0 Changed: 0 Warnings: 0
```
然后执行select * from performance_schema.data_locks\G;这条语句，查看事务 A 此时加了什么锁。
从上图可以看到，共加了两个锁，分别是：
- 表锁：X 类型的意向锁；
- 行锁：X 类型的间隙锁；
这里我们重点关注行锁，图中 LOCK_TYPE 中的 RECORD 表示行级锁，而不是记录锁的意思，通过 LOCK_MODE 可以确认是 next-key 锁，还是间隙锁，还是记录锁：
- 如果 LOCK_MODE 为X，说明是 next-key 锁；
- 如果 LOCK_MODE 为X, REC_NOT_GAP，说明是记录锁；
- 如果 LOCK_MODE 为X, GAP，说明是间隙锁；
因此，此时事务 A 在主键索引（INDEX_NAME : PRIMARY）上加的是间隙锁，锁范围是(20, 30)。
间隙锁的范围(20, 30)，是怎么确定的？
根据我的经验，如果 LOCK_MODE 是 next-key 锁或者间隙锁，那么 LOCK_DATA 就表示锁的范围最右值，此次的事务 A 的 LOCK_DATA 是 30。
然后锁范围的最左值是 t_student 表中 id 为 30 的上一条记录的 id 值，即 20。
因此，间隙锁的范围(20, 30)。
---
### Time 2 阶段加锁分析
Time 2 阶段，事务 B 执行以下语句：
```
---
## 事务 B
mysql> begin;
Query OK, 0 rows affected (0.00 sec)
mysql> update t_student set score = 100 where id = 26;
Query OK, 0 rows affected (0.01 sec)
Rows matched: 0 Changed: 0 Warnings: 0
```
然后执行select * from performance_schema.data_locks\G;这条语句，查看事务 B 此时加了什么锁。
从上图可以看到，行锁是 X 类型的间隙锁，间隙锁的范围是(20, 30)。
事务 A 和 事务 B 的间隙锁范围都是一样的，为什么不会冲突？
两个事务的间隙锁之间是相互兼容的，不会产生冲突。
在MySQL官网上还有一段非常关键的描述：
Gap locks in InnoDB are “purely inhibitive”, which means that their only purpose is to prevent other transactions from Inserting to the gap. Gap locks can co-exist. A gap lock taken by one transaction does not prevent another transaction from taking a gap lock on the same gap. There is no difference between shared and exclusive gap locks. They do not conflict with each other, and they perform the same function.
间隙锁的意义只在于阻止区间被插入，因此是可以共存的。一个事务获取的间隙锁不会阻止另一个事务获取同一个间隙范围的间隙锁，共享（S型）和排他（X型）的间隙锁是没有区别的，他们相互不冲突，且功能相同。