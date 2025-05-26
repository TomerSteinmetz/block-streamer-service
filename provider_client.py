import logging
import time
from collections import deque

import asyncio

from web3 import AsyncWeb3

class ProviderClient:
    def __init__(self, cfg, max_rate_per_sec=10):
        self.name = cfg.name
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(cfg.url, request_kwargs={"timeout": 15}))
        self.latencies = deque(maxlen=30)
        self.errors = deque(maxlen=30)
        self._rate_sem = asyncio.Semaphore(max_rate_per_sec)

    async def _timed(self, coro):
        start = time.perf_counter()
        try:
            async with self._rate_sem:
                result = await coro
            self.errors.append(0)
            return result
        except Exception as e:
            self.errors.append(1)
            raise e
        finally:
            self.latencies.append(time.perf_counter() - start)

    async def head(self):
        return await self._timed(self.w3.eth.block_number)

    async def get_block(self, block_number):
        return await self._timed(self.w3.eth.get_block(block_number))

    def get_average_latency(self):
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    def get_error_ratio(self):
        if not self.errors:
            return 0.0
        return sum(self.errors) / len(self.errors)

