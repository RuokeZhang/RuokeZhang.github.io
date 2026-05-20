from collections import defaultdict, deque
from math import inf
from typing import List

class BusRoutes:
    def __init__(self, routes: List[List[int]]):
        self.routes = routes
        self.n = len(routes)
        self.stop_to_bus = defaultdict(list)

        for i, route in enumerate(routes):
            for stop in route:
                self.stop_to_bus[stop].append(i)

        self.dist = [[inf] * self.n for _ in range(self.n)]

        for bus in range(self.n):
            self.bfs(bus)

    def bfs(self, start_bus: int):
        q = deque([start_bus])
        vis_bus = set([start_bus])
        used_stop = set()

        self.dist[start_bus][start_bus] = 1

        while q:
            cur_bus = q.popleft()

            for stop in self.routes[cur_bus]:
                if stop in used_stop:
                    continue

                for nxt_bus in self.stop_to_bus[stop]:
                    if nxt_bus not in vis_bus:
                        vis_bus.add(nxt_bus)
                        self.dist[start_bus][nxt_bus] = self.dist[start_bus][cur_bus] + 1
                        q.append(nxt_bus)

                used_stop.add(stop)

    def query(self, source: int, target: int) -> int:
        if source == target:
            return 0

        if source not in self.stop_to_bus or target not in self.stop_to_bus:
            return -1

        ans = inf

        for b1 in self.stop_to_bus[source]:
            for b2 in self.stop_to_bus[target]:
                ans = min(ans, self.dist[b1][b2])

        return -1 if ans == inf else ans