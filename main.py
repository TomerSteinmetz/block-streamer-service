import argparse
import asyncio
import logging

from block_streamer import BlockStreamService
from config import AppConfig
from provider_client import ProviderClient
from provider_manager import ProviderManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def build_streamer(cfg_path):
    app_cfg = AppConfig.load(cfg_path)
    providers = [ProviderClient(p) for p in app_cfg.providers]
    manager = ProviderManager(
        providers,
        lag_thr=app_cfg.lag_threshold_s,
        error_thr=app_cfg.failure_ratio,
        halflife=app_cfg.score_halflife_s
    )
    return BlockStreamService(manager)

async def main():
    parser = argparse.ArgumentParser(description="Node provider hot‑swap block streamer")
    parser.add_argument("--config", "-c", help="Path to config.yaml", default="config.yaml")
    args = parser.parse_args()

    block_streamer = build_streamer(args.config)
    block_streamer.running = True
    await block_streamer.stream()

if __name__ == "__main__":
    asyncio.run(main())
