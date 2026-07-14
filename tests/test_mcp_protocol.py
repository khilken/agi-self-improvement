from __future__ import annotations

from mcp.protocol import MCPMessage, MCPProtocol, MessageType


class CapturingTransport:
    def __init__(self):
        self.sent: list[MCPMessage] = []

    def send(self, msg: MCPMessage) -> str:
        self.sent.append(msg)
        return f"captured://{msg.message_id}"

    def receive(self, agent: str, delete_after_read: bool = True) -> list[MCPMessage]:
        return []


def test_report_result_generates_correlation_id_when_missing():
    transport = CapturingTransport()
    protocol = MCPProtocol(agent_name="tester", transport=transport)  # type: ignore[arg-type]

    msg = protocol.report_result(
        to_agent="hermes",
        correlation_id=None,
        result={"ok": True},
    )

    assert msg.message_type == MessageType.TASK_RESULT
    assert msg.correlation_id
    assert transport.sent == [msg]
