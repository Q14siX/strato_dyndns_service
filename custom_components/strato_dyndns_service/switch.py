"""Switch platform for STRATO DynDNS Service."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_DOMAIN
from .entity import StratoDynDNSDomainEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up STRATO DynDNS switches from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [StratoDynDNSDomainEnabledSwitch(coordinator, hostname) for hostname in coordinator.domain_configs],
        update_before_add=False,
    )


class StratoDynDNSDomainEnabledSwitch(StratoDynDNSDomainEntity, SwitchEntity):
    """Switch to enable or disable updates for one configured domain."""

    def __init__(self, coordinator, hostname: str) -> None:
        """Initialize the enabled switch."""
        super().__init__(coordinator, hostname)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{hostname}_enabled_switch"
        self._attr_translation_key = "domain_enabled_switch"

    @property
    def is_on(self) -> bool:
        """Return whether updates are enabled for this domain."""
        return bool(self.coordinator.get_state(self._hostname).enabled)

    async def async_turn_on(self, **kwargs) -> None:
        """Enable updates for this domain."""
        await self.coordinator.async_set_domain_enabled(self._hostname, True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable updates for this domain."""
        await self.coordinator.async_set_domain_enabled(self._hostname, False)

    @property
    def extra_state_attributes(self) -> dict:
        """Expose the related hostname."""
        return {ATTR_DOMAIN: self._hostname}
