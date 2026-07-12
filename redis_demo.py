def redis_command_demo1():
    """
    redis命令演示
    """

    from  redis import Redis

    #1、获取client对象
    client = Redis.from_url("redis://localhost:6379",decode_responses="True")

    #2、使用client对象执行一些命令
    #2.1 执行set命令，创建一个vlaud类型为string的key-value对
    client.set("name","张三")

    #执行get命令，获取到key为name的value
    name = client.get("name")
    print(name)
    #2.2 创建一个value为hash map的key-value对
    client.hset(
        "faq:items:address:test",
        mapping={
            "question":"地址是多少",
            "answer":"北京市海淀区"
        }
    )

    #获取到某个key所对应的hash map
    faq_item = client.hgetall("faq:items:address:test")
    print(faq_item)

redis_command_demo1()
