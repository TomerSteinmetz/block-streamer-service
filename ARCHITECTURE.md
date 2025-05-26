# 🏗️ **Architecture & Design Documentation**

## **System Overview**

The Blockchain Block Streamer is a fault-tolerant, high-performance service designed to continuously stream blockchain blocks from multiple providers with intelligent hot-swapping capabilities. The system prioritizes **reliability**, **performance**, and **real-time responsiveness**.

## **Core Design Principles**

### **1. Fault Tolerance First**
- **Multiple Provider Support**: Never rely on a single point of failure
- **Intelligent Switching**: Automatic failover based on real-time health metrics
- **Graceful Degradation**: Continue operation even when providers are degraded

### **2. Performance-Oriented**
- **Async/Await Throughout**: I tried to lay a foundation for non-blocking I/O for maximum throughput
- **Rate Limiting**: Respect provider API limits while maximizing performance
- **Minimal Latency**: Fast detection and response to provider issues

### **3. Observable & Maintainable**
- **Structured Logging**: Clear insight into system behavior
- **Clean Separation**: Modular design for easy testing and maintenance



---

## **Component Deep Dive**

### **1. BlockStreamService** (`block_streamer.py`)

**Purpose**: Orchestrates the main block streaming workflow and coordinates with provider management.

**Key Design Choices**:

- **Sequential Block Processing**: Processes blocks one at a time to maintain order and consistency
  ```python
  # Design Choice: Sequential processing ensures block order integrity
  for _ in range(head_block_number - self.last_processed_block):
      block = await self.provider_manager.active.get_block(self.last_processed_block + 1)
  ```

- **Exception-Driven Control Flow**: Uses specific exception types to trigger different recovery strategies
  ```python
  # Design Choice: Explicit exception handling for different failure modes
  except BlockInconsistentHashError:
      await self.provider_manager.switch_provider_consensus_based()
  except Exception:
      await self.provider_manager.switch_to_healthy_provider()
  ```

- **Stateful Processing**: Maintains processing state to resume from correct position after failures
  ```python
  # Design Choice: State persistence for recovery
  self.last_processed_block = last_processed_block_number
  self.last_hash = None  # For chain integrity validation
  ```

**Trade-offs**:
- ✅ **Pros**: Guaranteed block order, simple recovery logic, clear failure modes
- ❌ **Cons**: No parallel block fetching (current design enables quick and easy enhancement for catch-up scenarios)

---

### **2. ProviderManager** (`provider_manager.py`)

**Purpose**: Implements the intelligent hot-swapping logic with health-based provider selection.

**Key Design Choices**:

- **Health-Based Switching**: Uses EWMA metrics rather than simple counters
  ```python
  # Design Choice: EWMA provides smooth, time-weighted health assessment
  class ProviderScore:
      def __init__(self, lag_thr: float, error_thr: float, halflife: float):
          self.lag_ema = ExponentiallyWeightedMovingAverage(halflife)
          self.err_ema = ExponentiallyWeightedMovingAverage(halflife)
  ```

- **Consensus-Based Fork Resolution**: Queries multiple providers to find network consensus
  ```python
  # Design Choice: Democratic approach to resolve blockchain forks
  async def switch_provider_consensus_based(self):
      head_tasks = [provider.head() for provider in self.providers]
      heads = await asyncio.gather(*head_tasks, return_exceptions=True)
      consensus_head = max(set(valid_heads), key=valid_heads.count)
  ```

- **Thread-Safe Operations**: Uses asyncio locks for safe concurrent access
  ```python
  # Design Choice: Prevent race conditions in multi-async environment
  async with self._lock:
      self.active_index = i
  ```



---

### **3. ProviderClient** (`provider_client.py`)

**Purpose**: Wraps individual blockchain provider APIs with performance monitoring and rate limiting.

**Key Design Choices**:

- **Rate Limiting with Semaphores**: Prevents overwhelming provider APIs
  ```python
  # Design Choice: Semaphore-based rate limiting for API respect
  self._rate_sem = asyncio.Semaphore(max_rate_per_sec)
  async with self._rate_sem:
      result = await coro
  ```

- **Sliding Window Metrics**: Uses deque for efficient metric collection
  ```python
  # Design Choice: Fixed-size deque for O(1) metric updates
  self.latencies = deque(maxlen=30)  # Last 30 requests
  self.errors = deque(maxlen=30)
  ```

- **Timing Decorator Pattern**: Transparent performance measurement
  ```python
  # Design Choice: Decorator pattern for clean metric collection
  async def _timed(self, coro):
      start = time.perf_counter()
      try:
          # ... execute request
      finally:
          self.latencies.append(time.perf_counter() - start)
  ```

---

### **4. Configuration System** (`config.py`)

**Purpose**: Provides flexible, secure configuration management with environment variable support.

**Key Design Choices**:

- **Dataclass-Based Configuration**: Type-safe, IDE-friendly configuration
  ```python
  # Design Choice: Dataclasses for type safety and validation
  @dataclass
  class AppConfig:
      lag_threshold_s: int = 30
      failure_ratio: float = 0.2
  ```

- **Environment Variable Substitution**: Secure API key management
  ```python
  # Design Choice: Template-based env var substitution for security
  def _substitute_env_vars(template: str) -> str:
      return re.sub(r'\$\{([^}]+)\}', replace_var, template)
  ```

- **Layered Configuration**: YAML defaults + environment overrides
  ```python
  # Design Choice: Flexible configuration precedence
  config_data = {
      'lag_threshold_s': int(os.getenv('LAG_THRESHOLD_S', raw.get('lag_threshold_s', 30))),
  }
  ```

---

### **5. Health Monitoring** (`ewma.py`)

**Purpose**: Implements time-weighted health scoring using Exponentially Weighted Moving Average.

**Key Design Choices**:

- **Time-Based Decay**: Health scores naturally decay over time
  ```python
  # Design Choice: Time-based decay prevents stale health assessments
  history_weight = math.exp(-self._decay_rate * delta_seconds)
  self._ema_value = (history_weight * self._ema_value + (1.0 - history_weight) * new_sample)
  ```

- **Configurable Half-Life**: Tunable responsiveness to performance changes
  ```python
  # Design Choice: Configurable sensitivity to performance changes
  self._decay_rate = math.log(2) / half_life_seconds
  ```

**Trade-offs**:
- ✅ **Pros**: Smooth health transitions, time-aware, mathematically sound
- ❌ **Cons**: More complex than simple averages, requires tuning

---

### **6. Block Validation** (`block_validator.py`)

**Purpose**: Ensures data integrity and detects blockchain inconsistencies.

**Key Design Choices**:

- **Exception-Based Error Signaling**: Different exceptions for different error types
  ```python
  # Design Choice: Specific exceptions enable targeted error handling
  raise BlockCorruptedDataError  # Data integrity issue
  raise BlockInconsistentHashError  # Chain consistency issue
  ```

- **Parent Hash Validation**: Ensures chain continuity
  ```python
  # Design Choice: Parent hash validation prevents fork acceptance
  if parent_hash and serialize_data['parentHash'] != parent_hash:
      raise BlockInconsistentHashError
  ```

**Trade-offs**:
- ✅ **Pros**: Clear error semantics, chain integrity protection
- ❌ **Cons**: Simple validation (could be enhanced with more checks)

---



## **Configuration**

### **Health Threshold Tuning**

```yaml
# Design Choice: Conservative defaults with tunable sensitivity
lag_threshold_s: 30      # Switch if response time > 30s
failure_ratio: 0.2       # Switch if error rate > 20%
score_halflife_s: 60     # Health score half-life of 1 minute
```

**Rationale**:
- **30s lag threshold**: Balances responsiveness with network variance
- **20% error ratio**: Tolerates occasional failures while catching systemic issues  
- **60s half-life**: Provides recent-weighted but not overly reactive scoring

---




---
### TLDR
This architecture prioritizes **operational simplicity** while providing **reliability** but designed in a clean architecture mindset for better readiness and easy enhancements. 
