"""Runtime models for STRATO DynDNS Service."""

from __future__ import annotations

from dataclasses import dataclass

from .const import RESPONSE_UNKNOWN, STATUS_IDLE


@dataclass(slots=True)
class DomainConfig:
    """Configured STRATO DynDNS host entry."""

    hostname: str
    update_mode: str
    enabled: bool = True


@dataclass(slots=True)
class DomainState:
    """Runtime state of a configured STRATO DynDNS host entry."""

    hostname: str
    update_mode: str
    enabled: bool = True
    current_ipv4: str | None = None
    current_ipv6: str | None = None
    last_updated: str | None = None
    last_response: str | None = None
    last_response_code: str = RESPONSE_UNKNOWN
    status: str = STATUS_IDLE


@dataclass(slots=True)
class UpdateResult:
    """Result of a domain update request."""

    hostname: str
    status: str
    response: str
    response_code: str
    ipv4: str | None = None
    ipv6: str | None = None
