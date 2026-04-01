"""Shared entity helpers for STRATO DynDNS Service."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN, MAIN_DEVICE_SUFFIX


class StratoDynDNSDomainEntity(CoordinatorEntity):
    """Base entity for one configured domain."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, hostname: str) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._hostname = hostname

    @property
    def device_info(self) -> DeviceInfo:
        """Return the per-domain device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id, self._hostname)},
            manufacturer="STRATO",
            model="Configured Domain",
            translation_key="configured_domain",
            translation_placeholders={"domain": self._hostname},
            via_device=(DOMAIN, self.coordinator.config_entry.entry_id, MAIN_DEVICE_SUFFIX),
        )


class StratoDynDNSServiceEntity(CoordinatorEntity):
    """Base entity for the integration-wide service device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        """Initialize the base service entity."""
        super().__init__(coordinator)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the integration-wide service device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id, MAIN_DEVICE_SUFFIX)},
            manufacturer="STRATO",
            model="Service Endpoint",
            name=DEFAULT_NAME,
        )
