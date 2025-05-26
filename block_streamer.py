import asyncio
import logging
import time
from block_validator import BlockInconsistentHashError, validate_block_integrity, BlockCorruptedDataError
logger = logging.getLogger(__name__)


class BlockStreamService:

    def __init__(self, provider_manager, last_processed_block_number=None, poll_interval=12):
        self.provider_manager = provider_manager
        self.last_processed_block = last_processed_block_number
        self.last_hash = None
        self.last_block_ts = None
        self.running = False
        self.poll_interval = poll_interval

    async def stream(self):
        logger.info("Starting block stream service")
        self.running = True
        active_provider = self.provider_manager.active

        while self.running:
            try:
                head_block_number = await active_provider.head()
                if self.last_processed_block is None:
                    self.last_processed_block = head_block_number

                await self.process_blocks(head_block_number)

            except (BlockInconsistentHashError, BlockCorruptedDataError):
                logger.error(f"Incorrect hashes detected, searching for consensus head")
                await self.provider_manager.switch_provider_consensus_based()

            except Exception as e:
                logger.error(f"Failed to process block {e}")
                await self.provider_manager.switch_to_healthy_provider()
            finally:
                if self.last_block_ts is not None:
                    await self.provider_manager.record_metrics(time.time() - self.last_block_ts)
                await asyncio.sleep(self.poll_interval)

    async def process_blocks(self, head_block_number):
        for _ in range(head_block_number - self.last_processed_block):
            block = await self.provider_manager.active.get_block(self.last_processed_block + 1)
            serialize_data = self._serialize_block(block)
            if validate_block_integrity(serialize_data, self.last_hash):

                print(serialize_data)
                self.last_processed_block += 1
                self.last_hash = serialize_data['hash']
                self.last_block_ts = serialize_data['timestamp']
        return

    @staticmethod
    def _serialize_block(block):
        return {
            "number": block.number,
            "hash": block.hash.hex(),
            "parentHash": block.parentHash.hex(),
            "timestamp": block.timestamp,
            "tx_count": len(block.transactions),
        }
