"""The STRATO DynDNS Service integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

try:
    from homeassistant.core import SupportsResponse
except ImportError:  # pragma: no cover - fallback for older cores
    SupportsResponse = None

from .const import (
    CONF_DOMAINS,
    CONF_WEBHOOK_ID,
    DATA_COORDINATORS,
    DATA_SERVICES_REGISTERED,
    DATA_VIEW_REGISTERED,
    DOMAIN,
    IP_VERSION_AUTO,
    PLATFORMS,
    RESPONSE_UNKNOWN,
    SERVICE_FIELD_DEVICE_ID,
    SERVICE_FIELD_IP_VERSION,
    SERVICE_UPDATE_DOMAINS,
)
from .coordinator import StratoDynDNSCoordinator
from .helpers import build_domain_configs, ensure_list, merged_entry_config, serialize_domain_configs
from .http import StratoDynDNSWebhookView


type StratoDynDNSConfigEntry = ConfigEntry[StratoDynDNSCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration domain."""
    domain_data = hass.data.setdefault(
        DOMAIN,
        {
            DATA_COORDINATORS: {},
            DATA_VIEW_REGISTERED: False,
            DATA_SERVICES_REGISTERED: False,
        },
    )

    if not domain_data[DATA_VIEW_REGISTERED]:
        hass.http.register_view(StratoDynDNSWebhookView(hass))
        domain_data[DATA_VIEW_REGISTERED] = True

    if not domain_data[DATA_SERVICES_REGISTERED]:

        async def handle_update_domains(call: ServiceCall) -> dict[str, Any] | None:
            """Handle the update_domains service call."""
            coordinators: Mapping[str, StratoDynDNSCoordinator] = hass.data[DOMAIN][DATA_COORDINATORS]
            if not coordinators:
                return None

            device_ids = ensure_list(call.data.get(SERVICE_FIELD_DEVICE_ID))
            ip_version = str(call.data.get(SERVICE_FIELD_IP_VERSION, IP_VERSION_AUTO)).lower()
            if not device_ids:
                return {"overall_response": RESPONSE_UNKNOWN, "instances": {}}

            instance_payload: dict[str, Any] = {}
            all_response_codes: list[str] = []

            for coordinator in coordinators.values():
                hostnames = coordinator.resolve_domains_from_device_ids(device_ids)
                if not hostnames:
                    continue
                results = await coordinator.async_update_domains(
                    hostnames,
                    ip_version=ip_version,
                    source="service",
                )
                response_codes = [result.response_code for result in results.values()]
                instance_overall = coordinator.pick_worst_response_code(response_codes)
                all_response_codes.extend(response_codes)
                instance_payload[coordinator.config_entry.entry_id] = {
                    "title": coordinator.config_entry.title,
                    **coordinator.build_service_response(results, instance_overall),
                }

            overall_response = (
                StratoDynDNSCoordinator.pick_worst_response_code(all_response_codes)
                if all_response_codes
                else RESPONSE_UNKNOWN
            )
            return {
                "overall_response": overall_response,
                "instances": instance_payload,
            }

        register_kwargs = {}
        if SupportsResponse is not None:
            register_kwargs["supports_response"] = SupportsResponse.OPTIONAL
        hass.services.async_register(
            DOMAIN,
            SERVICE_UPDATE_DOMAINS,
            handle_update_domains,
            **register_kwargs,
        )
        domain_data[DATA_SERVICES_REGISTERED] = True

    return True


async def async_setup_entry(hass: HomeAssistant, entry: StratoDynDNSConfigEntry) -> bool:
    """Set up STRATO DynDNS Service from a config entry."""
    config = merged_entry_config(entry)
    coordinator = StratoDynDNSCoordinator(hass, entry, config)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    hass.data[DOMAIN][DATA_COORDINATORS][coordinator.webhook_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: StratoDynDNSConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = entry.runtime_data
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN][DATA_COORDINATORS].pop(coordinator.webhook_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries."""
    updates: dict[str, Any] = {}
    webhook_id = entry.data.get(CONF_WEBHOOK_ID)
    if webhook_id and entry.unique_id != webhook_id:
        updates["unique_id"] = str(webhook_id)

    normalized_domains = serialize_domain_configs(build_domain_configs(entry.data))
    if normalized_domains != entry.data.get(CONF_DOMAINS, []):
        data = dict(entry.data)
        data[CONF_DOMAINS] = normalized_domains
        updates["data"] = data

    if entry.version != 1:
        updates["version"] = 1
    if entry.minor_version != 6:
        updates["minor_version"] = 6

    if updates:
        hass.config_entries.async_update_entry(entry, **updates)
    return True
