from __future__ import annotations

import socket

import pytest


@pytest.fixture(autouse=True)
def block_outbound_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """The public demo and its tests must remain deterministic and offline."""

    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_create_connection = socket.create_connection

    def is_loopback(address) -> bool:
        if not isinstance(address, tuple):
            return True
        return str(address[0]).lower() in {"127.0.0.1", "::1", "localhost"}

    def guarded_connect(instance, address):
        if is_loopback(address):
            return original_connect(instance, address)
        raise AssertionError("outbound network access is forbidden in the synthetic demo")

    def guarded_connect_ex(instance, address):
        if is_loopback(address):
            return original_connect_ex(instance, address)
        raise AssertionError("outbound network access is forbidden in the synthetic demo")

    def guarded_create_connection(address, *args, **kwargs):
        if is_loopback(address):
            return original_create_connection(address, *args, **kwargs)
        raise AssertionError("outbound network access is forbidden in the synthetic demo")

    monkeypatch.setattr(socket, "create_connection", guarded_create_connection)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
