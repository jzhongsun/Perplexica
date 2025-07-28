"""Redis Stream Manager for Chat Streams."""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set, AsyncGenerator
from redis.asyncio import Redis
from loguru import logger
import traceback

from app.core.cache import get_redis
from app.core.ui_message_stream import ErrorUIMessageStreamPart


class ChatStreamManager:
    """Manages Redis Streams for chat sessions."""
    
    def __init__(self, redis: Optional[Redis] = None):
        self.redis = redis or get_redis()
        self.active_streams: Dict[str, Set[str]] = {}  # stream_key -> set of consumer_ids
        self.producer_tasks: Dict[str, asyncio.Task] = {}  # stream_key -> producer_task
        self._lock = asyncio.Lock()
    
    async def create_stream(self, chat_id: str, session_id: Optional[str] = None) -> str:
        """Create a new chat stream and return the stream key."""
        session_id = session_id or str(uuid.uuid4())
        stream_key = f"chat_stream:{chat_id}:{session_id}"
        
        async with self._lock:
            if stream_key not in self.active_streams:
                self.active_streams[stream_key] = set()
        
        return stream_key
    
    async def start_producer(self, stream_key: str, producer_func, *args, **kwargs) -> bool:
        """Start a producer for the given stream key."""
        async with self._lock:
            if stream_key in self.producer_tasks:
                # Producer already running
                return False
            
            # Create producer task
            producer_task = asyncio.create_task(
                self._run_producer(stream_key, producer_func, *args, **kwargs)
            )
            self.producer_tasks[stream_key] = producer_task
            return True
    
    async def _run_producer(self, stream_key: str, producer_func, *args, **kwargs):
        """Run the producer function and handle cleanup."""
        try:
            # Initialize stream with metadata
            await self.redis.xadd(
                stream_key,
                {
                    "type": "stream_start",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "producer_id": str(uuid.uuid4())
                }
            )
            
            # Run the producer function
            await producer_func(stream_key, *args, **kwargs)
            
            # Mark stream as completed
            await self.redis.xadd(
                stream_key,
                {
                    "type": "stream_end",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error in producer for {stream_key}: {str(e)}\nTraceback:\n{traceback.format_exc()}")
            # Write error to stream
            await self.redis.xadd(
                stream_key,
                {
                    "type": "stream_error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        finally:
            # Cleanup producer task
            async with self._lock:
                self.producer_tasks.pop(stream_key, None)
            
            # Set stream expiration (1 hour)
            await self.redis.expire(stream_key, 3600)
    
    async def add_consumer(self, stream_key: str, consumer_id: Optional[str] = None) -> str:
        """Add a consumer to the stream and return consumer_id."""
        consumer_id = consumer_id or f"consumer:{str(uuid.uuid4())}"
        
        async with self._lock:
            if stream_key not in self.active_streams:
                self.active_streams[stream_key] = set()
            self.active_streams[stream_key].add(consumer_id)
        
        return consumer_id
    
    async def remove_consumer(self, stream_key: str, consumer_id: str):
        """Remove a consumer from the stream."""
        async with self._lock:
            if stream_key in self.active_streams:
                self.active_streams[stream_key].discard(consumer_id)
                
                # If no more consumers, clean up
                if not self.active_streams[stream_key]:
                    del self.active_streams[stream_key]
                    
                    # Cancel producer if still running
                    if stream_key in self.producer_tasks:
                        producer_task = self.producer_tasks[stream_key]
                        if not producer_task.done():
                            producer_task.cancel()
        
        # Clean up consumer from Redis consumer group
        try:
            consumer_group = f"{stream_key}:consumers"
            await self.redis.xgroup_delconsumer(consumer_group, consumer_id)
        except Exception as e:
            logger.warning(f"Failed to delete consumer {consumer_id}: {e}")
    
    async def consume_stream(self, stream_key: str, consumer_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Consume messages from the stream."""
        consumer_group = f"{stream_key}:consumers"
        
        # Setup consumer group if it doesn't exist
        try:
            await self.redis.xgroup_create(
                stream_key, 
                consumer_group, 
                id="0", 
                mkstream=True
            )
        except Exception as e:
            # Group might already exist, which is fine
            if "BUSYGROUP" not in str(e):
                logger.warning(f"Failed to create consumer group: {e}")
        
        try:
            while True:
                try:
                    # Read from consumer group
                    messages = await self.redis.xreadgroup(
                        consumer_group,
                        consumer_id,
                        {stream_key: ">"},
                        count=1,
                        block=1000  # Block for 1 second
                    )
                    
                    if not messages:
                        continue
                    
                    for stream, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            message_type = fields.get("type")
                            
                            if message_type == "stream_start":
                                logger.info(f"Stream started for consumer {consumer_id}")
                                
                            elif message_type == "stream_part":
                                data = fields.get("data")
                                if data:
                                    yield {
                                        "id": str(uuid.uuid4()),
                                        "event": "message",
                                        "data": data,
                                    }
                                    
                            elif message_type == "stream_end":
                                logger.info(f"Stream ended for consumer {consumer_id}")
                                # Acknowledge the message
                                await self.redis.xack(consumer_group, stream_key, message_id)
                                return
                                
                            elif message_type == "stream_error":
                                error_msg = fields.get("error", "Unknown error")
                                logger.error(f"Stream error: {error_msg}")
                                yield {
                                    "id": str(uuid.uuid4()),
                                    "event": "message",
                                    "data": ErrorUIMessageStreamPart(errorText=error_msg).model_dump_json(exclude_none=True),
                                }
                                # Acknowledge the message
                                await self.redis.xack(consumer_group, stream_key, message_id)
                                return
                            
                            # Acknowledge the message
                            await self.redis.xack(consumer_group, stream_key, message_id)
                            
                except asyncio.TimeoutError:
                    # Check if stream still exists or if we should exit
                    stream_exists = await self.redis.exists(stream_key)
                    if not stream_exists:
                        logger.info(f"Stream {stream_key} no longer exists, exiting consumer")
                        return
                    continue
                    
                except Exception as e:
                    logger.error(f"Error in consumer {consumer_id}: {str(e)}")
                    yield {
                        "id": str(uuid.uuid4()),
                        "event": "message",
                        "data": ErrorUIMessageStreamPart(errorText=str(e)).model_dump_json(exclude_none=True),
                    }
                    return
                    
        except Exception as e:
            logger.error(f"Fatal error in consumer {consumer_id}: {str(e)}")
            yield {
                "id": str(uuid.uuid4()),
                "event": "message", 
                "data": ErrorUIMessageStreamPart(errorText=str(e)).model_dump_json(exclude_none=True),
            }
    
    async def publish_to_stream(self, stream_key: str, message_type: str, data: Dict[str, Any]):
        """Publish a message to the stream."""
        message = {
            "type": message_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }
        await self.redis.xadd(stream_key, message)
    
    async def get_stream_info(self, stream_key: str) -> Dict[str, Any]:
        """Get information about a stream."""
        try:
            info = await self.redis.xinfo_stream(stream_key)
            return {
                "length": info.get("length", 0),
                "consumers": len(self.active_streams.get(stream_key, set())),
                "has_producer": stream_key in self.producer_tasks,
                "producer_running": stream_key in self.producer_tasks and not self.producer_tasks[stream_key].done()
            }
        except Exception as e:
            logger.error(f"Error getting stream info for {stream_key}: {e}")
            return {}
    
    async def cleanup_expired_streams(self):
        """Clean up expired streams and their associated resources."""
        async with self._lock:
            expired_streams = []
            
            for stream_key in list(self.active_streams.keys()):
                try:
                    exists = await self.redis.exists(stream_key)
                    if not exists:
                        expired_streams.append(stream_key)
                except Exception as e:
                    logger.error(f"Error checking stream {stream_key}: {e}")
                    expired_streams.append(stream_key)
            
            for stream_key in expired_streams:
                logger.info(f"Cleaning up expired stream: {stream_key}")
                
                # Cancel producer task if running
                if stream_key in self.producer_tasks:
                    producer_task = self.producer_tasks[stream_key]
                    if not producer_task.done():
                        producer_task.cancel()
                    del self.producer_tasks[stream_key]
                
                # Remove from active streams
                if stream_key in self.active_streams:
                    del self.active_streams[stream_key]


# Global instance
_stream_manager = None

def get_stream_manager() -> ChatStreamManager:
    """Get the global stream manager instance."""
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = ChatStreamManager()
    return _stream_manager 