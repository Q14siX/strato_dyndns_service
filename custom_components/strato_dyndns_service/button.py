"""Button platform for STRATO DynDNS Service."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_DOMAIN, MODE_BOTH, MODE_IPV4, MODE_IPV6
from .entity import StratoDynDNSDomainEntity, StratoDynDNSServiceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up STRATO DynDNS buttons from a config entry."""
    coordinator = entry.runtime_data
    entities: list[ButtonEntity] = [
        StratoDynDNSServiceUpdateButton(coordinator, MODE_IPV4),
        StratoDynDNSServiceUpdateButton(coordinator, MODE_IPV6),
    ]
    for hostname, domain_config in coordinator.domain_configs.items():
        if domain_config.update_mode in (MODE_IPV4, MODE_BOTH):
            entities.append(StratoDynDNSDomainUpdateButton(coordinator, hostname, MODE_IPV4))
        if domain_config.update_mode in (MODE_IPV6, MODE_BOTH):
            entities.append(StratoDynDNSDomainUpdateButton(coordinator, hostname, MODE_IPV6))
    async_add_entities(entities, update_before_add=False)


class StratoDynDNSDomainUpdateButton(StratoDynDNSDomainEntity, ButtonEntity):
    """Button to update a configured STRATO DynDNS host."""

    def __init__(self, coordinator, hostname: str, ip_version: str) -> None:
        """Initialize the update button."""
        super().__init__(coordinator, hostname)
        self._ip_version = ip_version
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{hostname}_{ip_version}_button"
        self._attr_translation_key = f"update_{ip_version}"

    @property
    def available(self) -> bool:
        """Return whether the domain is currently enabled."""
        return super().available and bool(self.coordinator.get_state(self._hostname).enabled)

    async def async_press(self) -> None:
        """Trigger an on-demand update for one IP family."""
        await self.coordinator.async_update_domains(
            [self._hostname],
            ip_version=self._ip_version,
            source=f"button_{self._ip_version}",
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Expose the related hostname."""
        return {ATTR_DOMAIN: self._hostname}


class StratoDynDNSServiceUpdateButton(StratoDynDNSServiceEntity, ButtonEntity):
    """Button to update all enabled domains for one IP family."""

    def __init__(self, coordinator, ip_version: str) -> None:
        """Initialize the integration-wide update button."""
        super().__init__(coordinator)
        self._ip_version = ip_version
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_service_{ip_version}_button"
        self._attr_translation_key = f"update_{ip_version}"

    async def async_press(self) -> None:
        """Trigger a grouped update for all domains supporting one IP family."""
        await self.coordinator.async_update_supported_domains_for_family(
            self._ip_version,
            source=f"service_button_{self._ip_version}",
        )
