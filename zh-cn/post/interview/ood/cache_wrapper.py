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



def print_lru(cache):
    cur = cache.dummy.nxt
    arr = []
    while cur != cache.dummy:
        arr.append(f"{cur.key}:{cur.value}")
        cur = cur.nxt
    print("LRU order (MRU -> LRU):", " -> ".join(arr) if arr else "empty")


def test_simple_cache():
    print("=== Test SimpleCache + CacheWrapper ===")
    storage = SlowStorage()
    cache = SimpleCache()
    wrapper = CacheWrapper(storage, cache)

    wrapper.write("a", 1)
    wrapper.write("b", 2)

    print("read a =", wrapper.read("a"))   # 1
    print("read b =", wrapper.read("b"))   # 2
    print("read c =", wrapper.read("c"))   # None

    wrapper.delete("a")
    print("after delete a, read a =", wrapper.read("a"))  # None

    print("storage =", storage.data)
    print("cache =", cache.data)
    print()


def test_lru_cache():
    print("=== Test LRUCache ===")
    lru = LRUCache(2)

    lru.put("a", 1)
    print_lru(lru)   # a

    lru.put("b", 2)
    print_lru(lru)   # b -> a

    print("get a =", lru.get("a"))   # 1
    print_lru(lru)   # a -> b

    lru.put("c", 3)  # should evict b
    print_lru(lru)   # c -> a
    print("get b =", lru.get("b"))   # None
    print("get a =", lru.get("a"))   # 1
    print("get c =", lru.get("c"))   # 3

    lru.remove("a")
    print_lru(lru)   # c

    print()


def test_wrapper_with_lru():
    print("=== Test CacheWrapper + LRUCache ===")
    storage = SlowStorage()
    cache = LRUCache(2)
    wrapper = CacheWrapper(storage, cache)

    wrapper.write("x", 10)
    wrapper.write("y", 20)
    print_lru(cache)   # y -> x

    print("read x =", wrapper.read("x"))   # x becomes MRU
    print_lru(cache)   # x -> y

    wrapper.write("z", 30)   # should evict y
    print_lru(cache)         # z -> x

    print("read y =", wrapper.read("y"))   # miss in cache, hit in storage, refill
    print_lru(cache)         # y -> z or y -> x depending on refill/eject sequence
    print("storage =", storage.data)
    print()


if __name__ == "__main__":
    test_simple_cache()
    test_lru_cache()
    test_wrapper_with_lru()