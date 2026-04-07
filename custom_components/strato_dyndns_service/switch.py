"""Switch platform for STRATO DynDNS Service."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_DOMAIN, MODE_IPV4, MODE_IPV6
from .entity import StratoDynDNSDomainEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up STRATO DynDNS switches from a config entry."""
    coordinator = entry.runtime_data
    entities: list[SwitchEntity] = []
    for hostname in coordinator.domain_configs:
        entities.append(StratoDynDNSDomainFamilySwitch(coordinator, hostname, MODE_IPV4))
        entities.append(StratoDynDNSDomainFamilySwitch(coordinator, hostname, MODE_IPV6))
    async_add_entities(entities, update_before_add=False)


class StratoDynDNSDomainFamilySwitch(StratoDynDNSDomainEntity, SwitchEntity):
    """Switch to enable or disable one IP family for a configured domain."""

    def __init__(self, coordinator, hostname: str, ip_version: str) -> None:
        """Initialize the family switch."""
        super().__init__(coordinator, hostname)
        self._ip_version = ip_version
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{hostname}_{ip_version}_switch"
        self._attr_translation_key = f"domain_{ip_version}_switch"

    @property
    def is_on(self) -> bool:
        """Return whether this IP family is enabled for the domain."""
        state = self.coordinator.get_state(self._hostname)
        return bool(state.ipv4_enabled if self._ip_version == MODE_IPV4 else state.ipv6_enabled)

    async def async_turn_on(self, **kwargs) -> None:
        """Enable updates for this domain and family."""
        await self.coordinator.async_set_domain_family_enabled(self._hostname, self._ip_version, True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable updates for this domain and family."""
        await self.coordinator.async_set_domain_family_enabled(self._hostname, self._ip_version, False)

    @property
    def extra_state_attributes(self) -> dict:
        """Expose the related hostname."""
        return {ATTR_DOMAIN: self._hostname}
