"""
Base Runner for Hermes Agents
=============================

Provides a working run() loop with inbox processing.
"""

import time
import logging

logger = logging.getLogger("AgentRunner")


def run_agent(agent, poll_interval: float = 1.0):
    """Run an agent with inbox processing."""
    logger.info(f"{agent.__class__.__name__} starting message loop...")

    # Get handlers from the MCP protocol if available
    def get_handlers():
        if hasattr(agent, 'mcp') and hasattr(agent.mcp, '_handlers'):
            return agent.mcp._handlers
        elif hasattr(agent, '_handlers'):
            return agent._handlers
        return {}

    while True:
        try:
            handlers = get_handlers()

            if hasattr(agent, 'mcp'):
                messages = agent.mcp.receive()
                for msg in messages:
                    handler = handlers.get(msg.message_type)
                    if handler:
                        try:
                            handler(msg)
                        except Exception as e:
                            logger.exception(f"Handler error: {e}")

            time.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("Agent stopped.")
            break
        except Exception as e:
            logger.error(f"Runner error: {e}")
            time.sleep(poll_interval)