"""
Base Runner for Hermes Agents
=============================

Provides a simple run() loop so agents can process their inbox.
"""

import time
import logging
from mcp.protocol import MCPProtocol, MessageType

logger = logging.getLogger("AgentRunner")


class AgentRunner:
    """Mixin / base class that gives agents a run() loop."""

    def run(self, poll_interval: float = 1.0):
        """Continuously process incoming messages."""
        logger.info(f"{self.name} starting message processing loop...")
        while True:
            try:
                messages = self.mcp.receive() if hasattr(self, 'mcp') else []
                for msg in messages:
                    handler = self._handlers.get(msg.message_type)
                    if handler:
                        try:
                            handler(msg)
                        except Exception as e:
                            logger.exception(f"Handler error: {e}")
                time.sleep(poll_interval)
            except KeyboardInterrupt:
                logger.info("Agent stopped by user.")
                break
            except Exception as e:
                logger.error(f"Runner error: {e}")
                time.sleep(poll_interval)