"""Chat stream admin router for monitoring and management."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.core.stream_manager import get_stream_manager

router = APIRouter(prefix="/chat-admin", tags=["chat-admin"])


class StreamInfo(BaseModel):
    """Stream information model."""

    stream_key: str
    length: int
    consumers: int
    has_producer: bool
    producer_running: bool


class StreamListResponse(BaseModel):
    """Response model for stream list."""

    streams: List[StreamInfo]
    total_streams: int


@router.get("/streams", response_model=StreamListResponse)
async def list_active_streams() -> StreamListResponse:
    """List all active chat streams."""
    stream_manager = get_stream_manager()

    streams = []
    for stream_key in stream_manager.active_streams.keys():
        info = await stream_manager.get_stream_info(stream_key)
        streams.append(
            StreamInfo(
                stream_key=stream_key,
                length=info.get("length", 0),
                consumers=info.get("consumers", 0),
                has_producer=info.get("has_producer", False),
                producer_running=info.get("producer_running", False),
            )
        )

    return StreamListResponse(streams=streams, total_streams=len(streams))


@router.get("/streams/{stream_key}/info", response_model=StreamInfo)
async def get_stream_info(
    stream_key: str,
) -> StreamInfo:
    """Get detailed information about a specific stream."""
    stream_manager = get_stream_manager()

    if stream_key not in stream_manager.active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")

    info = await stream_manager.get_stream_info(stream_key)
    return StreamInfo(
        stream_key=stream_key,
        length=info.get("length", 0),
        consumers=info.get("consumers", 0),
        has_producer=info.get("has_producer", False),
        producer_running=info.get("producer_running", False),
    )


@router.delete("/streams/{stream_key}")
async def terminate_stream(
    stream_key: str,
) -> Dict[str, str]:
    """Terminate a specific stream and clean up its resources."""
    stream_manager = get_stream_manager()

    if stream_key not in stream_manager.active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")

    try:
        # Get all consumers for this stream
        consumers = list(stream_manager.active_streams[stream_key])

        # Remove all consumers
        for consumer_id in consumers:
            await stream_manager.remove_consumer(stream_key, consumer_id)

        # Delete the stream from Redis
        await stream_manager.redis.delete(stream_key)

        logger.info(f"Terminated stream {stream_key} with {len(consumers)} consumers")

        return {"message": f"Stream {stream_key} terminated successfully"}

    except Exception as e:
        logger.error(f"Error terminating stream {stream_key}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to terminate stream: {str(e)}"
        )


@router.post("/cleanup")
async def manual_cleanup() -> Dict[str, str]:
    """Manually trigger cleanup of expired streams."""
    stream_manager = get_stream_manager()

    try:
        await stream_manager.cleanup_expired_streams()
        return {"message": "Stream cleanup completed successfully"}
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get("/stats")
async def get_stream_stats() -> Dict[str, Any]:
    """Get overall statistics about the streaming system."""
    stream_manager = get_stream_manager()

    total_streams = len(stream_manager.active_streams)
    total_consumers = sum(
        len(consumers) for consumers in stream_manager.active_streams.values()
    )
    active_producers = len(stream_manager.producer_tasks)
    running_producers = sum(
        1 for task in stream_manager.producer_tasks.values() if not task.done()
    )

    return {
        "total_streams": total_streams,
        "total_consumers": total_consumers,
        "active_producers": active_producers,
        "running_producers": running_producers,
        "redis_connected": await _check_redis_connection(stream_manager.redis),
    }


async def _check_redis_connection(redis) -> bool:
    """Check if Redis connection is healthy."""
    try:
        await redis.ping()
        return True
    except Exception:
        return False
