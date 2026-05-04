"""Tests for mcp.shared._context utilities."""

import contextvars
from typing import Any

from mcp.shared._context import merge_contexts, tenant_id_var

_SENDER_VAR: contextvars.ContextVar[str] = contextvars.ContextVar("_sender_var")
_SERVER_VAR: contextvars.ContextVar[str] = contextvars.ContextVar("_server_var")


def _context_with(*pairs: tuple[contextvars.ContextVar[Any], Any]) -> contextvars.Context:
    def _setup() -> contextvars.Context:
        for var, val in pairs:
            var.set(val)
        return contextvars.copy_context()

    return contextvars.copy_context().run(_setup)


def test_merge_sender_only_vars():
    sender = _context_with((_SENDER_VAR, "from-client"))
    server = _context_with()

    merged = merge_contexts(sender, server)
    assert merged[_SENDER_VAR] == "from-client"


def test_merge_server_only_vars():
    sender = _context_with()
    server = _context_with((_SERVER_VAR, "from-server"))

    merged = merge_contexts(sender, server)
    assert merged[_SERVER_VAR] == "from-server"


def test_merge_both_present():
    sender = _context_with((_SENDER_VAR, "from-client"))
    server = _context_with((_SERVER_VAR, "from-server"))

    merged = merge_contexts(sender, server)
    assert merged[_SENDER_VAR] == "from-client"
    assert merged[_SERVER_VAR] == "from-server"


def test_merge_server_wins_on_conflict():
    shared_var: contextvars.ContextVar[str] = contextvars.ContextVar("shared")
    sender = _context_with((shared_var, "sender-value"))
    server = _context_with((shared_var, "server-value"))

    merged = merge_contexts(sender, server)
    assert merged[shared_var] == "server-value"


def test_merge_server_wins_tenant_id_spoof():
    """A sender context that sets tenant_id_var must be overridden by the server."""
    sender = _context_with((tenant_id_var, "spoofed-tenant"))
    server = _context_with((tenant_id_var, "real-tenant"))

    merged = merge_contexts(sender, server)
    assert merged[tenant_id_var] == "real-tenant"


def test_merge_empty_sender():
    sender = _context_with()
    server = _context_with((_SERVER_VAR, "from-server"))

    merged = merge_contexts(sender, server)
    assert merged[_SERVER_VAR] == "from-server"


def test_merge_empty_server():
    sender = _context_with((_SENDER_VAR, "from-client"))
    server = _context_with()

    merged = merge_contexts(sender, server)
    assert merged[_SENDER_VAR] == "from-client"
