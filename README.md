# Blockchain Node Provider Hotswap

A service that streams blockchain blocks from multiple providers and automatically switches between them when issues are detected, ensuring a continuous and reliable block stream.

## Features

- Connects to multiple blockchain node providers (Alchemy, Chainstack, etc.)
- Continuously fetches and processes blocks in sequential order
- Detects issues with providers based on health metrics:
  - Block delay (significant deviation from expected block times)
  - Block integrity (missing or malformed block data)
  - Provider health (response times, HTTP errors, connectivity failures)
- Automatically switches to a healthy provider when issues are detected
- Keeps track of missing blocks and attempts to recover them
- Outputs block data in structured JSON format

## Setup

### Prerequisites

- Python 3.8+ or Docker
- Alchemy API key (free tier available at [https://dashboard.alchemy.com](https://dashboard.alchemy.com))

### Quick Setup

1. Clone the Repository:

```bash
git clone <repository-url>
cd blockchain-hotswap-service
```

2. Set Up Environment:

```
# Create virtual environment
python -m venv venv
source venv/bin/activate 
```

3. create and edit .env file with your providers configurations:

```
cp .env.example .env
```

### Running with Python

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the service:

```bash
python main.py
```

3. running test:

```bash
python -m pytest ./tests -v
````

### Running with Docker

1. Build and run with Docker:

```bash
docker build -t block-streamer:latest . 
docker run -d  block-streamer:latest

```

2. running tests in existing image:

```bash
docker run block-streamer:latest python -m pytest 
```



## Adding New Providers

To add a new provider, update the `providers` in `config.yaml`:

```
  - name: Alchemy
    url_template: "${ALCHEMY_BASE_URL}/${ALCHEMY_API_KEY}"
    -name: <your-provider-name>
    url_template: "${<PROVIDER_BASE_URL}/${<PROVIDER_API_KEY}"

```

## Production Monitoring

### Recommended Monitoring Approach

For a production environment, the following monitoring strategies are recommended:

1. **Logs Aggregation**: Use a service like ELK stack (Elasticsearch, Logstash, Kibana), Datadog, or CloudWatch Logs to collect and analyze logs.

2. **Metrics Collection**: Expose metrics via Prometheus and visualize with Grafana.

3. **Alerting**: Slack integration for critical failures (all providers down, blocks stopped flowing).
Tiered Alerts: Warning (1 provider down) → Critical (multiple providers down) → Emergency (service stopped)

4. **Health Endpoint**: Add a dedicated HTTP endpoint to expose service health information.

### Key Metrics to Track

- **Block Processing**: 
  - Blocks processed per minute
  - Missing blocks count
  - Block processing latency
  
- **Provider Health**:
  - Response times per provider
  - Error rates per provider
  - Provider switching frequency
  - Time spent on each provider
  
- **System Health**:
  - CPU/Memory usage
  - Network I/O
  - Error rates by type

## Future Improvements

Given ample time to build, these improvements would enhance the solution:

1. Probe idle providers every 10-30 s to keep fresh health scores and avoid switching to another bad node
2. Utilize the async await design for better concurrency in more areas in the app (e.g. processing blocks)

3. Advanced Provider Metrics: More sophisticated health scoring based on historical performance.

4. Provider Backends: Support for more blockchain networks and providers.

5. Circuit Breaker Pattern: Implement circuit breakers to prevent overwhelming failing providers.

6.  Use a message queue to decouple block fetching from processing.

7. Scaling: Support for distributed instances with leader election.

8. Load Balancing: Distribute requests across multiple endpoints of the same provider.

9. Caching Layer: Cache recent blocks to reduce API calls.

10. Chaos-test harness (kill provider pods, inject 500s) in CI.
11. Persistence Layer: Store block data in a database for historical analysis and to prevent data loss during restarts.
