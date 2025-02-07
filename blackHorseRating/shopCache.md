---
title: 商户缓存
date: 2025-02-03
categories: ["BlackHorse Rating"]
tags:
- Java
- Redis
- Spring
---
## 缓存工具类
```java
@Slf4j
@Component
public class CacheClient {

    private final StringRedisTemplate stringRedisTemplate;

    private static final ExecutorService CACHE_REBUILD_EXECUTOR = Executors.newFixedThreadPool(10);

    public CacheClient(StringRedisTemplate stringRedisTemplate) {
        this.stringRedisTemplate = stringRedisTemplate;
    }

    public void set(String key, Object value, Long time, TimeUnit unit) {
        stringRedisTemplate.opsForValue().set(key, JSONUtil.toJsonStr(value), time, unit);
    }
}
```
1. ShopServiceImpl Bean 的创建时间
在 Spring 中，bean 的创建通常发生在 上下文启动时，也就是 Spring 启动并创建 ApplicationContext 时。具体来说，ShopServiceImpl 是一个标注为 @Service 的类，这表示它会被 Spring 自动扫描并注册为一个 bean。当 Spring 启动时，它会扫描到这个类并创建 ShopServiceImpl 的实例。

因此，ShopServiceImpl 实例会在 Spring 容器启动时被创建，通常是 应用启动时。

2. StringRedisTemplate 和 CacheClient 的创建与注入
StringRedisTemplate：

StringRedisTemplate 是一个由 Spring Boot 自动配置的 Redis 访问工具类，它会在 Spring 启动时根据 application.yml 中的配置自动实例化。Spring 会为每个 Redis 连接池和相关配置创建一个 StringRedisTemplate 的单例实例，并将它注入到需要的地方。
单例模式：Spring 默认将 bean 配置为单例（除非明确指定为其他作用域）。因此，StringRedisTemplate 是一个单例的 bean，并且它会在整个应用生命周期中共享。
CacheClient：

CacheClient 是一个标注为 @Component 的类，这意味着 Spring 会自动将它注册为一个 bean 并将其注入到其他类中。CacheClient 的实例会在 Spring 容器启动时被创建，通常也是 在应用启动时。
由于 CacheClient 使用构造器注入 StringRedisTemplate，因此 Spring 会先创建 StringRedisTemplate 的单例实例，然后将其传入 CacheClient 的构造函数，从而完成注入。