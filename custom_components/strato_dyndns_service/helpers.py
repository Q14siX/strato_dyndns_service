"""Helper functions for STRATO DynDNS Service."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Iterable

from .const import (
    CONF_DOMAINS,
    CONF_ENABLED,
    CONF_IPV4_ENABLED,
    CONF_IPV6_ENABLED,
    CONF_UPDATE_MODE,
    MODE_BOTH,
    MODE_IPV4,
    MODE_IPV6,
)
from .models import DomainConfig

_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$",
    re.IGNORECASE,
)


def is_valid_hostname(value: str | None) -> bool:
    """Return True if the provided value looks like a valid domain/subdomain."""
    if not value:
        return False
    hostname = value.strip().rstrip(".").lower()
    return bool(_HOSTNAME_RE.fullmatch(hostname))


def normalize_hostname(value: str | None) -> str:
    """Normalize a hostname for storage and comparison."""
    return (value or "").strip().rstrip(".").lower()


def _legacy_family_flags(item: dict) -> tuple[bool, bool]:
    """Map legacy enabled/update_mode fields to per-family flags."""
    if not bool(item.get(CONF_ENABLED, True)):
        return False, False

    update_mode = str(item.get(CONF_UPDATE_MODE, MODE_BOTH)).lower()
    if update_mode == MODE_IPV4:
        return True, False
    if update_mode == MODE_IPV6:
        return False, True
    return True, True


def build_domain_configs(entry_data: dict) -> list[DomainConfig]:
    """Create typed domain configs from config entry data."""
    domains: list[DomainConfig] = []
    for item in entry_data.get(CONF_DOMAINS, []):
        hostname = normalize_hostname(item.get("hostname"))
        if not hostname:
            continue

        if CONF_IPV4_ENABLED in item or CONF_IPV6_ENABLED in item:
            ipv4_enabled = bool(item.get(CONF_IPV4_ENABLED, True))
            ipv6_enabled = bool(item.get(CONF_IPV6_ENABLED, True))
        else:
            ipv4_enabled, ipv6_enabled = _legacy_family_flags(item)

        domains.append(
            DomainConfig(
                hostname=hostname,
                ipv4_enabled=ipv4_enabled,
                ipv6_enabled=ipv6_enabled,
            )
        )
    return domains


def serialize_domain_configs(domain_configs: Iterable[DomainConfig]) -> list[dict]:
    """Serialize typed domain configs back to config-entry payloads."""
    return [
        {
            "hostname": config.hostname,
            CONF_IPV4_ENABLED: bool(config.ipv4_enabled),
            CONF_IPV6_ENABLED: bool(config.ipv6_enabled),
        }
        for config in domain_configs
    ]


def merged_entry_config(entry) -> dict:
    """Return config-entry data merged with legacy options, where data wins."""
    data = dict(entry.options) if getattr(entry, "options", None) else {}
    data.update(entry.data)
    return data


def ensure_list(value) -> list[str]:
    """Normalize a scalar or iterable to a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value]
    return [str(value)]


def split_hostnames(raw_value: str | None) -> list[str]:
    """Split comma-separated hostnames into a normalized list."""
    if not raw_value:
        return []
    return [normalize_hostname(item) for item in raw_value.split(",") if item.strip()]


def parse_myip(raw_value: str | None) -> tuple[str | None, str | None]:
    """Parse a DynDNS myip parameter into IPv4 and IPv6 parts."""
    ipv4: str | None = None
    ipv6: str | None = None
    if not raw_value:
        return ipv4, ipv6

    for item in (part.strip() for part in raw_value.split(",")):
        if not item:
            continue
        try:
            parsed = ipaddress.ip_address(item)
        except ValueError:
            continue
        if parsed.version == 4 and ipv4 is None:
            ipv4 = str(parsed)
        elif parsed.version == 6 and ipv6 is None:
            ipv6 = str(parsed)
    return ipv4, ipv6
