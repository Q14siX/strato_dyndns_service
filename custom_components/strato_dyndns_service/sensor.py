"""Sensor platform for STRATO DynDNS Service."""

from __future__ import annotations

from homeassistant.components.sensor import RestoreSensor, SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CURRENT_IPV4,
    ATTR_CURRENT_IPV6,
    ATTR_DOMAIN,
    ATTR_FRITZBOX_URL,
    ATTR_LAST_SERVER_RESPONSE,
    ATTR_LAST_UPDATE,
    ATTR_LAST_WEBHOOK_RESPONSE,
    ATTR_REQUEST_FROM,
    ATTR_RESPONSE_CODE,
    ATTR_STATUS,
    ATTR_UPDATE_MODE,
    ATTR_WEBHOOK_URL,
    RESPONSE_UNKNOWN,
)
from .entity import StratoDynDNSDomainEntity, StratoDynDNSServiceEntity

PARALLEL_UPDATES = 0

DOMAIN_DIAGNOSTIC_KEYS = [
    ATTR_STATUS,
    ATTR_UPDATE_MODE,
    ATTR_CURRENT_IPV4,
    ATTR_CURRENT_IPV6,
    ATTR_LAST_UPDATE,
    ATTR_LAST_SERVER_RESPONSE,
]
SERVICE_DIAGNOSTIC_KEYS = [
    ATTR_WEBHOOK_URL,
    ATTR_FRITZBOX_URL,
    ATTR_LAST_WEBHOOK_RESPONSE,
    ATTR_CURRENT_IPV4,
    ATTR_CURRENT_IPV6,
    ATTR_LAST_UPDATE,
    ATTR_REQUEST_FROM,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up STRATO DynDNS sensors from a config entry."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    entities.extend(StratoDynDNSServiceDiagnosticSensor(coordinator, key) for key in SERVICE_DIAGNOSTIC_KEYS)
    for hostname in coordinator.domain_configs:
        entities.append(StratoDynDNSDomainResponseSensor(coordinator, hostname))
        entities.extend(
            StratoDynDNSDomainDiagnosticSensor(coordinator, hostname, key)
            for key in DOMAIN_DIAGNOSTIC_KEYS
        )
    async_add_entities(entities, update_before_add=False)


class StratoDynDNSRestoreSensor(RestoreSensor):
    """Restore the last native sensor value after a restart."""

    def __init__(self) -> None:
        """Initialize restore state."""
        self._restored_native_value = None

    async def async_added_to_hass(self) -> None:
        """Restore the last stored native sensor value."""
        await super().async_added_to_hass()
        if restored_data := await self.async_get_last_sensor_data():
            self._restored_native_value = restored_data.native_value


class StratoDynDNSDomainResponseSensor(StratoDynDNSDomainEntity, StratoDynDNSRestoreSensor, SensorEntity):
    """Represent the last STRATO response code of one configured domain."""

    _attr_translation_key = "domain_response"
    _attr_has_entity_name = False

    def __init__(self, coordinator, hostname: str) -> None:
        """Initialize the domain response sensor."""
        StratoDynDNSDomainEntity.__init__(self, coordinator, hostname)
        StratoDynDNSRestoreSensor.__init__(self)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{hostname}_response"
        self._attr_name = hostname

    @property
    def native_value(self) -> str:
        """Return the normalized response code."""
        state = self.coordinator.get_state(self._hostname)
        current_value = self.coordinator.build_domain_diagnostic_value(self._hostname, ATTR_RESPONSE_CODE)
        if state.last_response is None and self._restored_native_value is not None:
            return self._restored_native_value
        return current_value or RESPONSE_UNKNOWN

    @property
    def extra_state_attributes(self) -> dict:
        """Return minimal attributes to help service targeting."""
        return {ATTR_DOMAIN: self._hostname}


class StratoDynDNSDomainDiagnosticSensor(StratoDynDNSDomainEntity, StratoDynDNSRestoreSensor, SensorEntity):
    """Diagnostic sensor for one configured domain."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, hostname: str, key: str) -> None:
        """Initialize the domain diagnostic sensor."""
        StratoDynDNSDomainEntity.__init__(self, coordinator, hostname)
        StratoDynDNSRestoreSensor.__init__(self)
        self._key = key
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{hostname}_{key}"
        self._attr_translation_key = f"domain_{key}"
        if key == ATTR_LAST_UPDATE:
            self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        """Return the diagnostic sensor value."""
        current_value = self.coordinator.build_domain_diagnostic_value(self._hostname, self._key)
        state = self.coordinator.get_state(self._hostname)

        if self._key == ATTR_UPDATE_MODE:
            return current_value

        if self._key == ATTR_STATUS:
            if state.last_response is None and self._restored_native_value is not None:
                return self._restored_native_value
            return current_value

        if current_value is None and self._restored_native_value is not None:
            return self._restored_native_value

        return current_value

    @property
    def extra_state_attributes(self) -> dict:
        """Return the hostname for service targeting."""
        return {ATTR_DOMAIN: self._hostname}


class StratoDynDNSServiceDiagnosticSensor(StratoDynDNSServiceEntity, StratoDynDNSRestoreSensor, SensorEntity):
    """Diagnostic sensor exposing service-level technical details."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, key: str) -> None:
        """Initialize the service diagnostic sensor."""
        StratoDynDNSServiceEntity.__init__(self, coordinator)
        StratoDynDNSRestoreSensor.__init__(self)
        self._key = key
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_translation_key = f"service_{key}"
        if key == ATTR_LAST_UPDATE:
            self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        """Return the diagnostic sensor value."""
        current_value = self.coordinator.build_webhook_service_sensor_value(self._key)
        if self._key == ATTR_LAST_WEBHOOK_RESPONSE and current_value == RESPONSE_UNKNOWN and self._restored_native_value is not None:
            return self._restored_native_value
        if current_value is None and self._restored_native_value is not None:
            return self._restored_native_value
        return current_value
