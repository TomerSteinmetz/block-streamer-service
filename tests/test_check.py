import asyncio
from unittest.mock import MagicMock, AsyncMock
import pytest
from block_streamer import BlockStreamService
from provider_client import ProviderClient
from provider_manager import ProviderManager


@pytest.fixture
def healthy_mock_providers():
    providers = []
    for i in range(3):
        provider = AsyncMock(spec=ProviderClient)
        provider.name = f"Provider{i}"
        provider.head.return_value = 111
        provider.get_average_latency.return_value = 0.1
        provider.get_error_ratio.return_value = 0.05  # Healthy: 5% error rate
        provider.get_block.return_value = create_mock_block(100)
        providers.append(provider)
    return providers


@pytest.mark.asyncio
async def test_provider_switches_on_failure(healthy_mock_providers):
    provider_manager = ProviderManager(
        providers=healthy_mock_providers,
        lag_thr=1.0,
        error_thr=0.1,  # 10% threshold
        halflife=60.0
    )
    original_provider = provider_manager.active
    original_provider.get_block.side_effect = Exception("Provider failed")

    block_stream_service = BlockStreamService(provider_manager, 99, 0.1)  # Fast polling

    stream_task = asyncio.create_task(block_stream_service.stream())

    try:
        await asyncio.wait_for(
            _wait_for_switch_away_from(provider_manager, original_provider),
            timeout=5.0
        )
        assert provider_manager.active != original_provider
        assert provider_manager.active.name != original_provider.name
    finally:
        block_stream_service.running = False  # Stop the stream
        stream_task.cancel()
        try:
            await stream_task
        except asyncio.CancelledError:
            pass


async def _wait_for_switch_away_from(manager, original_provider):
    while manager.active is original_provider:
        await asyncio.sleep(0.1)


def create_mock_block(block_number):
    block = MagicMock()
    block.number = block_number
    block.hash = MagicMock()
    block.hash.hex.return_value = f"0x{'0' * 62}{block_number:02x}"
    block.parentHash = MagicMock()
    block.parentHash.hex.return_value = f"0x{'0' * 62}{block_number - 1:02x}"
    block.timestamp = 1000000 + block_number
    block.transactions = [f"tx_{i}" for i in range(3)]
    return block