---
title:  优惠券秒杀
date: 2025-02-01
categories: ["BlackHorse Rating"]
tags:
- Java
- Redis
---
## 全局ID生成器: Redis自增
使用数据库自增ID的缺点：
1. 可能会暴露给用户一些信息：用户可能会根据此推断，一天之内销售出了多少张优惠券。
2. 当优惠券太多时，会导致数据库ID过大。但如果为优惠券分表，又会出现许多优惠券共用同一个ID的情况。
![Alt text](/uniqueID.png)
```java
//符号位0+时间戳31bit+序列号32bit
public long nextId(String keyPrefix){
    //生成时间戳
    LocalDateTime now=LocalDateTime.now();
    long nowSecond=now.toEpochSecond(ZoneOffset.UTC);
    long timestamp=nowSecond-BEGIN_TIMESTAMP;
    //生成序列号. 每一天下的单使用同一个Key
    String date=now.format(DateTimeFormatter.ofPattern("yyyy:MM:dd"));
    long count=  stringRedisTemplate.opsForValue().increment("icr:"+keyPrefix+":"+date);
    //拼接并返回
    return timestamp<<COUNT_BITS|count;
}
```
这里的 keyPrefix表示一种object,比如优惠券订单

## 超卖问题
假设200qps，200 个请求同时抢优惠券，然而优惠券的总数只有 100 张。
JMeter 测试发现，有 45% 的失败率；数据库查看，发现此时该库存数量为 -9，出现超卖情况。
### 乐观锁-版本号法
![Alt text](/chaomai.png)
先从数据库查到一个版本号 A，向数据库更新的时候确认一下自己拿到的版本号A和此时数据库里的版本号B是否一致。 如果一致, set version+1; 不一致，则放弃更新操作。
### 乐观锁-CAS
```java
//扣减库存
boolean success= seckillVoucherService.update().setSql("stock=stock-1")
        .eq("voucher_id",voucherId)
        .eq("stock",voucher.getStock()) //乐观锁CAS 方法
        .update();
```
Jmeter测试发现，请求失败率高达 89%，查看数据库库存，发现还剩 79 张优惠券，根本没卖完。
这是因为有很多请求，在它第一遍查库存（voucher.getStock()）和发出 update 请求之间，有别的线程已经修改了数据库里的库存。

这样做的好处就是不会出现超卖现象，但是请求失败率太高了。

### 改进
```java
boolean success= seckillVoucherService.update().setSql("stock=stock-1")
        .eq("voucher_id",voucherId)
        .gt("stock", 0) //把加锁操作交给数据库
        .update();
```
本质上是悲观锁，数据库的行锁。JMeter 测试，请求成功率为 50%，查询数据库发现优惠券刚好买完。

## 一人一单


### 初步想法
创建订单时，先查数据库看这个用户是否下过单；再往数据库里添加 order。

问题：多个并发请求来自于同一个用户时，“查数据库”——“给数据库里加 order”存在线程安全问题。

### synchronized悲观锁
#### 锁下单function
锁住下单 function。为什么不能用Java 实现乐观锁？乐观锁只应用于 update，而这里是新创建订单。
```java
@Transactional
public synchronized Result createVoucherOrder(Long voucherId){
    Long userId=UserHolder.getUser().getId();
    int count=query().eq("user_id",userId).eq("voucher_id", voucherId).count();
    if(count>0){
        return Result.fail("用户已经购买过一次了～");
    }
    //扣减库存
    boolean success= seckillVoucherService.update().setSql("stock=stock-1")
            .eq("voucher_id",voucherId)
            .gt("stock", 0)
            .update();
    if(!success){
        return Result.fail("库存不足，数据库更新失败");
    }
    //创建订单
    VoucherOrder voucherOrder=new VoucherOrder();
    //返回订单id
    Long orderId= redisIdWorker.nextId("order");
    voucherOrder.setId(orderId);
    voucherOrder.setUserId(userId);
    voucherOrder.setVoucherId(voucherId);
    save(voucherOrder);
    return Result.ok(orderId);
}
```
假设有 200 个请求同时到达 服务器，都想抢优惠券，其中 100 个请求来自用户 A ，100个请求来自用户 B。
synchronized 作用于该 instance method, 它只允许同一时间，只能有一个线程执行这个方法。一个线程为一个请求执行完这个方法后，其它线程才能开始。

事务与锁的顺序：事务开始、获取锁、数据库操作、提交事务、释放锁
线程 A 提交完事务了，线程 B 才有获取锁的可能，因此只要事务隔离级别在**读已提交**及以上，那么这种操作是线程安全的。

缺点：锁的粒度太大！我只需要同一个用户的请求被串行化，不同用户的请求其实可以被多线程并发处理。

#### 改进：减小锁粒度
把锁的粒度换成用户ID。对于那些并发线程，首先判断它们来自于哪个用户，然后对来自于同一个用户的请求处理做串行化。

userId.toString()一般会进行new String()操作，导致同一个用户的 userId可能被创建为许多不同的字符串。而intern()方法会优先从字符串常量池中拿字符串，确保同一个用户拥有唯一的userId对象。
代码如下：
```java
@Transactional
public Result createVoucherOrder(Long voucherId){
    Long userId=UserHolder.getUser().getId();
    synchronized(userId.toString().intern()){
        //code 省略
    }
}
```
缺点：如果把 synchronized 代码块放进这个@transactional 标注的方法之内，顺序就是事务开始——获取锁——释放锁——事务提交。

如果事务隔离级别设置的是读未提交**以上**的，那么在线程 A 释放锁之后，事务提交之前，线程B 获取锁，然后会读到旧数据。

#### synchronized 代码块放在事务外面
```java
Long userId=UserHolder.getUser().getId();
synchronized(userId.toString().intern()){
    return createVoucherOrder(voucherId);
}
```
把这个函数放进代码块里面，某个线程获取锁——事务提交——释放锁，严格按照这样的顺序执行。
这样保证其它线程在尝试获取锁时，读到的一定是数据库被上一个线程修改过的数据。


缺点：如果启动两个服务，负载均衡把来自同一个用户的两个请求分别发到两个服务，锁则没有用了，这个用户可以下两次单。
两个 JVM 不可能被同一个synchronized 锁给锁住。
![Alt text](/2JVM.png)

### Redis 互斥锁
```java
//这里加个锁。预防多 JVM 情况下，来自同一用户的同一时间的多个请求，分别占用了不同 JVM 的 synchronized 锁。
SimpleRedisLock lock=new SimpleRedisLock("order:"+userId, stringRedisTemplate);
boolean isLock=lock.tryLock(1200);
if(!isLock){
    return Result.fail("不允许重复下单");
}
try{
    IVoucherOrderService proxy=(IVoucherOrderService) AopContext.currentProxy();
    return  proxy.createVoucherOrder(voucherId);
}finally{
    lock.unlock();
}
```
在8081和8083开启两个服务，向8082发起两个请求，分别被nginx转发给这两个服务。

POST http://localhost:8082/api/voucher-order/seckill/11

![Alt text](/8083.png)
可以看到8083的服务拿到了锁
![Alt text](/lock.png)
redis里面显示了它拿到的互斥锁，其值为线程ID 30
![Alt text](/8081.png)
8081的服务没拿到锁

![Alt text](/123.png)
缺点：如果线程1拿到锁之后，业务阻塞了，因为锁是设置了expire time，所以在业务完成之前，它就把锁释放了。这时候线程2趁虚而入，拿到了锁，开始执行任务。
线程1业务跑完，释放锁，结果把线程2的锁给释放掉了。这时候线程3又拿到锁，开始执行任务。

改进：释放锁的时候，判断一下锁是否是自己的。
但是线程1和线程2同时跑业务这件事也是不对的！

#### 线程标示：解决锁误删
1. 获取锁的时候存入线程标示（UUID）。原来存的是线程ID，是由JVM维护的。但如果在集群运行，会有多个JVM，那么线程ID会有重复
2. 释放锁之前比较一下线程标示
3. 可以解决锁误删问题，但是不能解决线程 1 业务阻塞导致锁过期，线程 2 和线程 1 一起执行业务的问题。
```java
@Override
public void unlock(){
    //获取线程标示
    String threadId=ID_PREFIX+Thread.currentThread().getId();
    //获取锁中的标示
    String id=stringRedisTemplate.opsForValue().get(KEY_PREFIX+threadId);
    if(threadId.equals(id)){
        //线程 1判断和主动释放之间，可能会有阻塞。如果这时候锁自动过期，会有别的线程2抢锁。那么线程 1阻塞完了之后，就直接把线程2的锁给释放了
        stringRedisTemplate.delete(KEY_PREFIX+name);
    }
}
```
#### 避免锁误删需原子性操作
Redis里面运行Lua脚本，可以保证该脚本是原子性操作
```
EVAL "return redis.call('set', KEYS[1], ARGV[1])" 1 name Ruoke
```
Redis CLI里面这样写，EVAL后面跟着脚本内容，也可以允许传参

```Lua
-- 这里的 KEYS[1] 就是锁的key，这里的ARGV[1] 就是当前线程标示
-- 获取锁中的标示，判断是否与当前线程标示一致
if (redis.call('GET', KEYS[1]) == ARGV[1]) then
    -- 一致，则删除锁
    return redis.call('DEL', KEYS[1])
end
-- 不一致，则直接返回
return 0
```
#### 缺点
1. 不可重入：同一个线程不可以多次获取同一把锁。如果一个线程想要在多个方法时都保持只有它自己进入，那么需要为每个方法都设置单独的互斥锁。
2. 不可重试：当前的实现中，获取锁失败一次就立刻返回 false，非阻塞式。
3. 业务堵塞造成锁过期，此时会有其它线程拿到锁。 
4. 主从一致性问题：主从节点的数据同步存在延迟。假如一个线程在主节点那拿到了锁（SETNX），然后主节点宕机，从节点还没有拿到同步的数据，就被推选为新的主节点。这时候其它线程可能从新的主节点那里拿到锁。 


### Redisson锁
```java
@Configuration
public class RedissonConfig {
    @Bean
    public RedissonClient redissonClient() {
        Config config=new Config();
        config.useSingleServer().setAddress("redis://localhost:6379");
        return Redisson.create(config);
    }
}
```
新建一个配置类，之后调用redissonClient的方法就行。
```java
RLock lock=redissonClient.getLock("lock:order:"+userId);
boolean isLock=lock.tryLock();
```
获取锁的操作
![Alt text](/redisson.png)
在释放锁之前打个断点，可以发现redis里面出现一个 key-value
### 总结
#### 方案对比

| 方案               | 优点                     | 缺点                         | 适用场景         |
|--------------------|--------------------------|------------------------------|------------------|
| 方法级synchronized | 实现简单                 | 性能差（所有用户串行）       | 绝对不推荐       |
| 用户ID锁（JVM内）  | 细粒度、性能较好          | 集群环境下失效               | 单机部署         |
| Redis分布式锁      | 支持集群、细粒度控制      | 实现略复杂                   | 生产环境推荐     |

#### Redis分布式锁的问题及解决方案

| 问题类型           | 解决方案        |
|--------------------|-----------------|
| 锁误删             | Lua脚本原子解锁 |
| 锁超时导致并发     | Redisson看门狗  |
