import logging


logger = logging.getLogger(__name__)

class BlockCorruptedDataError(Exception):
    pass

class BlockInconsistentHashError(Exception):
    pass

def validate_block_integrity(serialize_data, parent_hash) -> bool:
    required_fields = ['number', 'hash', 'timestamp', 'parentHash']
    for field in required_fields:
        if field not in serialize_data or not serialize_data[field]:
            logger.error(f"Block missing required field: {field}")
            raise BlockCorruptedDataError

    if parent_hash and serialize_data['parentHash'] != parent_hash:
        logger.error(f"Invalid block hash {serialize_data['hash']}, expected {parent_hash}")
        raise BlockInconsistentHashError
    return True

