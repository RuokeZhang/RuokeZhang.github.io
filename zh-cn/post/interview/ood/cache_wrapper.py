from abc import ABC, abstractmethod
class Storage(ABC):
    @abstractmethod
    def read(self, key):
        pass
    @abstractmethod
    def write(self, key, value):
        pass
    @abstractmethod
    def delete(self, key):
        pass

class SlowStorage(Storage):
    def __init__(self):
        self.data={}
    def read(self, key):
        if key not in self.data:
            return None
        return self.data[key]
    def write(self, key, value):
        self.data[key]=value
    def delete(self, key):
        if key not in self.data:
            return None
        value=self.data[key]
        del self.data[key]
        return value

class Cache(ABC):
    @abstractmethod
    def get(self, key):
        pass
    @abstractmethod
    def put(self, key, value):
        pass
    @abstractmethod
    def remove(self, key):
        pass

class SimpleCache(Cache):
    def __init__(self):
        self.data={}
    def get(self, key):
        if key not in self.data:
            return None
        return self.data[key]
    def remove(self, key):
        self.data.pop(key)
    def put(self, key, value):
        self.data[key]=value

class Node:
    def __init__(self, key=None, value=None, nxt=None, prv=None):
        self.key=key
        self.value=value
        self.nxt=nxt
        self.prv=prv

class LRUCache(Cache):
    def __init__(self, capacity):
        self.capacity=capacity
        self.dummy=Node()
        self.dummy.nxt=self.dummy
        self.dummy.prv=self.dummy
        self.key_to_node={}
    
    def pushToFront(self, node):
        sec=self.dummy.nxt
        self.dummy.nxt=node
        node.nxt=sec
        sec.prv=node
        node.prv=self.dummy
        # add to dict
        self.key_to_node[node.key]=node

    def getNode(self, key):
        if key in self.key_to_node:
            return self.key_to_node[key]
        return None
    def removeNode(self, node):
        node.prv.nxt=node.nxt
        node.nxt.prv=node.prv
    def remove(self, key):
        if key not in self.key_to_node:
            return
        node=self.getNode(key)
        self.removeNode(node)
        del self.key_to_node[key]
    def get(self, key):
        # try get node
        node=self.getNode(key)
        if not node:
            return None
        #remove it
        self.removeNode(node)
        # push to Front
        self.pushToFront(node)
        return node.value
    def put(self, key, value):
        #check if the key exists
        if key in self.key_to_node:
            self.removeNode(self.key_to_node[key])
        node=Node(key, value)
        #push if to front
        self.pushToFront(node)
        #check capacity
        if len(self.key_to_node)>self.capacity:
            to_delete=self.dummy.prv
            self.removeNode(to_delete)
            del self.key_to_node[to_delete.key]
        
class CacheWrapper(Storage):
    def __init__(self, storage, cache):
        self.storage=storage
        self.cache=cache
    def read(self, key):
        value=self.cache.get(key)
        if value is None:
            value=self.storage.read(key)
            if value is not None:
                self.cache.put(key, value)
        return value
    def write(self, key, value):
        self.storage.write(key, value)
        self.cache.put(key, value)
    def delete(self, key):
        self.storage.delete(key)
        self.cache.remove(key)
import time
class TTLCache(Cache):
    def __init__(self, ttl):
        self.data={} #key->(value, expire)
        self.ttl=ttl
    def get(self, key):
        # get the key value, check if it expires
        if key not in self.data:
            return None
        value, expire=self.data[key]
        if time.time()>expire:
            del self.data[key]
            return None
        return value
    def put(self, key, value):
        cur_time=time.time()
        self.data[key]=[value, cur_time+self.ttl]
    def remove(self, key):
        del self.data[key]

def test_ttl_cache():
    print("=== Test TTLCache ===")
    cache = TTLCache(ttl=2)

    cache.put("a", 100)
    print("put a=100")
    print("immediately get a =", cache.get("a"))   # 100

    time.sleep(1)
    print("after 1 second, get a =", cache.get("a"))   # 100

    time.sleep(2)
    print("after 3 seconds total, get a =", cache.get("a"))   # None
    print("internal data =", cache.data)
    print()


def test_wrapper_with_ttl():
    print("=== Test CacheWrapper + TTLCache ===")
    storage = SlowStorage()
    cache = TTLCache(ttl=2)
    wrapper = CacheWrapper(storage, cache)

    wrapper.write("x", 10)
    print("write x=10")
    print("read x immediately =", wrapper.read("x"))   # 10
    print("cache data =", cache.data)
    print("storage data =", storage.data)

    time.sleep(3)
    print("after ttl expired, read x =", wrapper.read("x"))  
    # 应该 cache miss，但 storage 还有，所以返回 10，并重新写回 cache

    print("cache data after refill =", cache.data)
    print("storage data =", storage.data)
    print()


def test_ttl_remove():
    print("=== Test TTLCache remove ===")
    cache = TTLCache(ttl=5)
    cache.put("k1", "v1")
    print("before remove, get k1 =", cache.get("k1"))   # v1
    cache.remove("k1")
    print("after remove, get k1 =", cache.get("k1"))    # None
    print()


if __name__ == "__main__":
    test_ttl_cache()
    test_wrapper_with_ttl()
    test_ttl_remove()
