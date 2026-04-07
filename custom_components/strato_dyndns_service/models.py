"""Runtime models for STRATO DynDNS Service."""

from __future__ import annotations

from dataclasses import dataclass

from .const import MODE_BOTH, MODE_IPV4, MODE_IPV6, MODE_NONE, RESPONSE_UNKNOWN, STATUS_IDLE


@dataclass(slots=True)
class DomainConfig:
    """Configured STRATO DynDNS host entry."""

    hostname: str
    ipv4_enabled: bool = True
    ipv6_enabled: bool = True

    @property
    def enabled(self) -> bool:
        """Return whether any IP family is enabled for updates."""
        return self.ipv4_enabled or self.ipv6_enabled

    @property
    def update_mode(self) -> str:
        """Return the derived update mode for this domain."""
        if self.ipv4_enabled and self.ipv6_enabled:
            return MODE_BOTH
        if self.ipv4_enabled:
            return MODE_IPV4
        if self.ipv6_enabled:
            return MODE_IPV6
        return MODE_NONE


@dataclass(slots=True)
class DomainState:
    """Runtime state of a configured STRATO DynDNS host entry."""

    hostname: str
    ipv4_enabled: bool = True
    ipv6_enabled: bool = True
    current_ipv4: str | None = None
    current_ipv6: str | None = None
    last_updated: str | None = None
    last_response: str | None = None
    last_response_code: str = RESPONSE_UNKNOWN
    status: str = STATUS_IDLE

    @property
    def enabled(self) -> bool:
        """Return whether any IP family is enabled for updates."""
        return self.ipv4_enabled or self.ipv6_enabled

    @property
    def update_mode(self) -> str:
        """Return the derived update mode for this runtime state."""
        if self.ipv4_enabled and self.ipv6_enabled:
            return MODE_BOTH
        if self.ipv4_enabled:
            return MODE_IPV4
        if self.ipv6_enabled:
            return MODE_IPV6
        return MODE_NONE


@dataclass(slots=True)
class UpdateResult:
    """Result of a domain update request."""

    hostname: str
    status: str
    response: str
    response_code: str
    ipv4: str | None = None
    ipv6: str | None = None
