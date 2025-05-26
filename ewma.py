import math
import time

class ExponentiallyWeightedMovingAverage:
    """Exponentially-weighted moving average (EWMA) with a configurable half-life."""

    def __init__(self, half_life_seconds: float):
        self.half_life_seconds = half_life_seconds
        self._ema_value = None
        self._last_sample_timestamp = None
        # decay per second so that weight falls to 0.5 after one half-life
        self._decay_rate = math.log(2) / half_life_seconds

    def update(self, new_sample):
        current_time = time.time()

        if self._ema_value is None:
            self._ema_value = new_sample
        else:
            delta_seconds = current_time - self._last_sample_timestamp
            history_weight = math.exp(-self._decay_rate * delta_seconds)
            self._ema_value = (history_weight * self._ema_value + (1.0 - history_weight) * new_sample)

        self._last_sample_timestamp = current_time

    @property
    def value(self) -> float:
        return 0.0 if self._ema_value is None else self._ema_value
