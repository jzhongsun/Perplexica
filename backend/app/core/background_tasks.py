"""Background tasks for the application."""

import asyncio
from loguru import logger
from app.core.stream_manager import get_stream_manager


async def cleanup_expired_streams():
    """Background task to clean up expired streams."""
    stream_manager = get_stream_manager()
    
    while True:
        try:
            await stream_manager.cleanup_expired_streams()
            logger.debug("Completed stream cleanup cycle")
        except Exception as e:
            logger.error(f"Error during stream cleanup: {e}")
        
        # Run cleanup every 5 minutes
        await asyncio.sleep(300)


async def start_background_tasks():
    """Start all background tasks."""
    logger.info("Starting background tasks...")
    
    # Start stream cleanup task
    asyncio.create_task(cleanup_expired_streams())
    
    logger.info("Background tasks started") 