"""Minimal Model Context Protocol connector abstraction."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MCPContext:
    """Serializable context packet for enterprise copilots."""

    resource: str
    payload: dict[str, Any]


class MCPServerConnector:
    """Creates MCP-compatible context packets for downstream copilots."""

    def __init__(self, namespace: str = "comptext.v7") -> None:
        self.namespace = namespace

    def build_context(self, resource: str, payload: dict[str, Any]) -> MCPContext:
        """Wrap a payload in a namespaced MCP resource identifier."""
        return MCPContext(resource=f"{self.namespace}/{resource}", payload=payload)
