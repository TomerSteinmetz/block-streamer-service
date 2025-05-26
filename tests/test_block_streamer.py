import pytest
from unittest.mock import MagicMock, call, AsyncMock

from block_streamer import BlockStreamService
from block_validator import BlockInconsistentHashError, BlockCorruptedDataError


@pytest.fixture
def mock_provider():
    provider = AsyncMock()
    provider.name = "TestProvider"
    provider.head.return_value = 100
    provider.get_block.return_value = create_mock_block(99)
    return provider

@pytest.fixture
def mock_provider_manager(mock_provider):
    manager = AsyncMock()
    manager.active = mock_provider
    return manager


@pytest.fixture
def block_stream_service(mock_provider_manager):
    return BlockStreamService(
        provider_manager=mock_provider_manager,
        last_processed_block_number=99,
        poll_interval=1
    )


def create_mock_block(block_number):
    block = MagicMock()
    block.number = block_number
    block.hash = MagicMock()
    block.hash.hex.return_value = f"0x{'0' * 62}{block_number:02x}"
    block.parentHash = MagicMock()
    block.parentHash.hex.return_value = f"0x{'0' * 62}{block_number-1:02x}"
    block.timestamp = 1000000 + block_number
    block.transactions = [f"tx_{i}" for i in range(3)]  # Mock 3 transactions
    return block


class TestBlockStreamService:
    @pytest.mark.asyncio
    async def test_process_blocks_success(self, mock_provider, block_stream_service):
        block_stream_service.last_processed_block = 97
        blocks = [create_mock_block(i) for i in range(97, 100)]
        mock_provider.get_block.side_effect = blocks
        expected_calls = [call(98), call(99)]

        await block_stream_service.process_blocks(100)

        mock_provider.get_block.assert_has_calls(expected_calls)
        assert block_stream_service.last_processed_block == 100
        assert block_stream_service.last_hash == blocks[-1].hash.hex()
        assert block_stream_service.last_block_ts == blocks[-1].timestamp

    @pytest.mark.asyncio
    async def test_block_process_throw_exception_on_corrupted_data(self, mock_provider, block_stream_service):
        block_stream_service.last_processed_block = 97
        blocks = [create_mock_block(i) for i in range(97, 100)]
        mock_provider.get_block.side_effect = blocks
        blocks[1].hash.hex.return_value = None

        with pytest.raises(BlockCorruptedDataError):
            await block_stream_service.process_blocks(100)

    @pytest.mark.asyncio
    async def test_block_process_throw_exception_on_hash(self, mock_provider, block_stream_service):
        block_stream_service.last_processed_block = 97
        blocks = [create_mock_block(i) for i in range(97, 100)]
        mock_provider.get_block.side_effect = blocks
        blocks[1].hash.hex.return_value = 'not a number'

        with pytest.raises(BlockInconsistentHashError):
            await block_stream_service.process_blocks(100)



