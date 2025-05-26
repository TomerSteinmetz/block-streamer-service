# Blockchain Node Provider Hotswap

A service that streams blockchain blocks from multiple providers and automatically switches between them when issues are detected, ensuring a continuous and reliable block stream.

[Architecture Documentation](ARCHITECTURE.md)
[Monitoring and Production Improvements Doc](MONITORING_AND_IMPROVEMENTS.md)


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

