import asyncio
import logging
import time

from ewma import ExponentiallyWeightedMovingAverage

logger = logging.getLogger(__name__)

class ProviderScore:
    def __init__(self, lag_thr: float, error_thr: float, halflife: float):
        self.lag_ema = ExponentiallyWeightedMovingAverage(halflife)
        self.err_ema = ExponentiallyWeightedMovingAverage(halflife)
        self.lag_thr = lag_thr
        self.err_thr = error_thr


    def update(self, lag_s: float, err_ratio: float):
        self.lag_ema.update(lag_s)
        self.err_ema.update(err_ratio)

    @property
    def is_healthy(self) -> bool:
        return (self.lag_ema.value < self.lag_thr) and (self.err_ema.value < self.err_thr)

class ProviderManager:
    def __init__(self, providers, lag_thr, error_thr, halflife) -> None:
        if not providers:
            raise ValueError("At least one provider required")
        self.providers = providers
        self.active_index = 0
        self.last_block_ts = None
        self.metrics = [ProviderScore(lag_thr, error_thr, halflife) for _ in providers]
        self._lock = asyncio.Lock()

    @property
    def active(self):
        return self.providers[self.active_index]

    async def record_metrics(self, lag_s):
        async with self._lock:
            self.metrics[self.active_index].update(
                lag_s,
                self.active.get_error_ratio(),
            )

    async def switch_provider_consensus_based(self):
        if len(self.providers) < 2:
            return
        head_tasks = [provider.head() for provider in self.providers]
        heads = await asyncio.gather(*head_tasks, return_exceptions=True)

        valid_heads = [h for h in heads if not isinstance(h, Exception)]
        if not valid_heads:
            return

        consensus_head = max(set(valid_heads), key=valid_heads.count)
        async with self._lock:
            if heads[self.active_index] != consensus_head:
                for i, head in enumerate(heads):
                    if head == consensus_head:
                        self.active_index = i
                        logger.info(f"Switched to provider {self.providers[i].name} for fork resolution")
                        return

    async def switch_to_healthy_provider(self):
        async with self._lock:
            for index, metric in enumerate(self.metrics):
                if index == self.active_index:
                    continue
                if metric.is_healthy:
                    logger.info(f"Switching to provider {self.active.name}")
                    self.active_index = index
                    return
        logger.info(f"Failed to find healthy provider")
        await asyncio.sleep(2)
