import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Set, Any

logger = logging.getLogger("quickdesk.broadcaster")


class EventBroadcaster:
    """
    In-memory pub/sub broker for Server-Sent Events (SSE).
    Enables real-time push notifications from ticket workflows
    to connected agent dashboards without external message brokers.
    """

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """
        Registers a new subscriber and yields SSE-formatted events.
        Automatically sends keepalive pings and cleans up on client disconnect.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.add(queue)
            logger.info(f"[SSE] New agent subscribed. Total active connections: {len(self._subscribers)}")

        try:
            # Send initial connection confirmation
            yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'message': 'Subscribed to QuickDesk real-time events'})}\n\n"

            while True:
                try:
                    # Wait for an event with a 20-second timeout to send keepalive ping
                    event = await asyncio.wait_for(queue.get(), timeout=20.0)
                    event_type = event.get("event", "message")
                    payload = event.get("data", {})
                    yield f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    # Keepalive comment to prevent proxy and browser timeout
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            logger.info("[SSE] Client disconnected (cancelled).")
            raise
        finally:
            async with self._lock:
                self._subscribers.discard(queue)
                logger.info(f"[SSE] Subscriber removed. Total active connections: {len(self._subscribers)}")

    def broadcast(self, event_type: str, data: Any):
        """
        Dispatches an event payload to all currently active subscriber queues.
        Synchronous and thread-safe using queue.put_nowait().
        """
        if not self._subscribers:
            return

        message = {"event": event_type, "data": data}
        for q in list(self._subscribers):
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning("[SSE] Dropping event for slow subscriber (queue full).")
            except Exception as e:
                logger.warning(f"[SSE] Error queuing event: {e}")


# Singleton instance shared across FastAPI application
broadcaster = EventBroadcaster()
