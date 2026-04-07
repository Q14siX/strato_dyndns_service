"""Coordinator for STRATO DynDNS Service."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
import ipaddress
import logging
from typing import Any

from aiohttp import BasicAuth, ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_CURRENT_IPV4,
    ATTR_CURRENT_IPV6,
    ATTR_DOMAIN,
    ATTR_ENABLED,
    ATTR_FRITZBOX_URL,
    ATTR_LAST_SERVER_RESPONSE,
    ATTR_LAST_UPDATE,
    ATTR_LAST_WEBHOOK_RESPONSE,
    ATTR_REQUEST_FROM,
    ATTR_RESPONSE_CODE,
    ATTR_STATUS,
    ATTR_UPDATE_MODE,
    ATTR_WEBHOOK_URL,
    CONF_HOSTNAME,
    CONF_IPV4_ENABLED,
    CONF_IPV6_ENABLED,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_WEBHOOK_ID,
    DEFAULT_NAME,
    DOMAIN,
    ENABLED_STATE_DISABLED,
    ENABLED_STATE_ENABLED,
    IP_VERSION_AUTO,
    MAIN_DEVICE_SUFFIX,
    MODE_BOTH,
    MODE_IPV4,
    MODE_IPV6,
    PUBLIC_IPV4_DISCOVERY_URL,
    PUBLIC_IPV6_DISCOVERY_URL,
    RESPONSE_911,
    RESPONSE_ABUSE,
    RESPONSE_BADAGENT,
    RESPONSE_BADAUTH,
    RESPONSE_DISABLED,
    RESPONSE_DNSERR,
    RESPONSE_DONATOR,
    RESPONSE_ERROR,
    RESPONSE_GOOD,
    RESPONSE_NOCHG,
    RESPONSE_NOHOST,
    RESPONSE_NOTFQDN,
    RESPONSE_NUMHOST,
    RESPONSE_OK,
    RESPONSE_SKIPPED,
    RESPONSE_TIMEOUT,
    RESPONSE_UNKNOWN,
    STATUS_DISABLED,
    STATUS_ERROR,
    STATUS_IDLE,
    STATUS_SKIPPED,
    STATUS_UNCHANGED,
    STATUS_UPDATED,
    STRATO_UPDATE_URL,
    WEBHOOK_URL,
)
from .helpers import build_domain_configs, normalize_hostname
from .models import DomainConfig, DomainState, UpdateResult

_LOGGER = logging.getLogger(__name__)


class StratoDynDNSCoordinator(DataUpdateCoordinator[dict[str, DomainState]]):
    """Coordinate runtime state and updates for STRATO DynDNS domains."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, config: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DEFAULT_NAME,
            update_method=self._async_update_data,
        )
        self.config_entry = entry
        self._session = async_get_clientsession(hass)
        self._username = str(config[CONF_USERNAME]).strip()
        self._password = str(config[CONF_PASSWORD]).strip()
        self.webhook_id = str(config[CONF_WEBHOOK_ID]).strip()
        self.domain_configs: dict[str, DomainConfig] = {
            item.hostname: item for item in build_domain_configs(config)
        }
        self._states: dict[str, DomainState] = {
            item.hostname: DomainState(
                hostname=item.hostname,
                ipv4_enabled=item.ipv4_enabled,
                ipv6_enabled=item.ipv6_enabled,
                status=STATUS_IDLE if item.enabled else STATUS_DISABLED,
            )
            for item in self.domain_configs.values()
        }
        self._last_webhook_response: str = RESPONSE_UNKNOWN
        self._service_current_ipv4: str | None = None
        self._service_current_ipv6: str | None = None
        self._service_last_update: str | None = None
        self._service_request_from: str | None = None

    async def _async_update_data(self) -> dict[str, DomainState]:
        """Return the current in-memory runtime state."""
        return dict(self._states)

    @property
    def last_webhook_response(self) -> str:
        """Return the last webhook response code."""
        return self._last_webhook_response

    def get_state(self, hostname: str) -> DomainState:
        """Return the runtime state for one hostname."""
        return self._states[hostname]

    def resolve_domains_from_entity_ids(self, entity_ids: Iterable[str]) -> list[str]:
        """Resolve configured hostnames from selected entity IDs."""
        hostnames: list[str] = []
        for entity_id in entity_ids:
            state = self.hass.states.get(entity_id)
            if state is None:
                continue
            hostname = state.attributes.get(ATTR_DOMAIN)
            if not hostname:
                continue
            hostname = str(hostname).strip().lower()
            if hostname in self.domain_configs and hostname not in hostnames:
                hostnames.append(hostname)
        return hostnames

    def resolve_domains_from_device_ids(self, device_ids: Iterable[str]) -> list[str]:
        """Resolve configured hostnames from selected device IDs."""
        hostnames: list[str] = []
        registry = dr.async_get(self.hass)
        for device_id in device_ids:
            device = registry.async_get(device_id)
            if device is None:
                continue
            for identifier in device.identifiers:
                if len(identifier) != 3:
                    continue
                domain, entry_id, hostname = identifier
                if domain != DOMAIN or entry_id != self.config_entry.entry_id:
                    continue
                if hostname == MAIN_DEVICE_SUFFIX:
                    continue
                if hostname in self.domain_configs and hostname not in hostnames:
                    hostnames.append(hostname)
        return hostnames

    def webhook_path(self) -> str:
        """Return the relative webhook path."""
        return WEBHOOK_URL.format(webhook_id=self.webhook_id)

    def external_webhook_url(self) -> str | None:
        """Return the best possible webhook URL for external callers."""
        try:
            base_url = get_url(
                self.hass,
                allow_internal=True,
                allow_external=True,
                allow_cloud=True,
                prefer_external=True,
            )
        except NoURLAvailableError:
            return None
        return f"{base_url}{self.webhook_path()}"

    def fritzbox_update_template(self) -> str | None:
        """Return a FRITZ!Box-compatible update URL template."""
        webhook_url = self.external_webhook_url()
        if webhook_url is None:
            return None
        return f"{webhook_url}?myip=<ipaddr>,<ip6addr>"

    def build_domain_attribute_reference(self, hostname: str) -> dict[str, Any]:
        """Build a minimal domain reference attribute map."""
        return {ATTR_DOMAIN: hostname}

    def _build_entry_domains_payload(self) -> list[dict[str, Any]]:
        """Build the persisted domain payload for the config entry."""
        payload: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in self.config_entry.data.get("domains", []):
            hostname = normalize_hostname(item.get(CONF_HOSTNAME))
            if not hostname or hostname in seen:
                continue
            config = self.domain_configs.get(hostname)
            if config is None:
                continue
            payload.append(
                {
                    CONF_HOSTNAME: config.hostname,
                    CONF_IPV4_ENABLED: bool(config.ipv4_enabled),
                    CONF_IPV6_ENABLED: bool(config.ipv6_enabled),
                }
            )
            seen.add(hostname)

        for hostname, config in self.domain_configs.items():
            if hostname in seen:
                continue
            payload.append(
                {
                    CONF_HOSTNAME: config.hostname,
                    CONF_IPV4_ENABLED: bool(config.ipv4_enabled),
                    CONF_IPV6_ENABLED: bool(config.ipv6_enabled),
                }
            )

        return payload

    def _persist_config_entry(self) -> None:
        """Persist the current runtime configuration to the config entry."""
        data = dict(self.config_entry.data)
        data["domains"] = self._build_entry_domains_payload()
        self.hass.config_entries.async_update_entry(self.config_entry, data=data)

    async def async_set_domain_family_enabled(self, hostname: str, ip_version: str, enabled: bool) -> None:
        """Enable or disable one IP family for a configured domain and persist it."""
        config = self.domain_configs.get(hostname)
        state = self._states.get(hostname)
        if config is None or state is None:
            return

        enabled = bool(enabled)
        if ip_version == MODE_IPV4:
            if config.ipv4_enabled == enabled and state.ipv4_enabled == enabled:
                return
            config.ipv4_enabled = enabled
            state.ipv4_enabled = enabled
        elif ip_version == MODE_IPV6:
            if config.ipv6_enabled == enabled and state.ipv6_enabled == enabled:
                return
            config.ipv6_enabled = enabled
            state.ipv6_enabled = enabled
        else:
            return

        if state.enabled:
            if state.status == STATUS_DISABLED:
                state.status = STATUS_IDLE
        else:
            state.status = STATUS_DISABLED

        self._persist_config_entry()
        self.async_set_updated_data(dict(self._states))

    def _store_service_snapshot(
        self,
        *,
        ipv4: str | None = None,
        ipv6: str | None = None,
        request_from: str | None = None,
    ) -> None:
        """Persist service-level diagnostic details for the last request."""
        self._service_last_update = dt_util.now().isoformat()
        if ipv4 is not None:
            self._service_current_ipv4 = ipv4
        if ipv6 is not None:
            self._service_current_ipv6 = ipv6
        if request_from is not None:
            self._service_request_from = request_from

    async def async_update_domains(
        self,
        hostnames: list[str] | None = None,
        *,
        ip_version: str = IP_VERSION_AUTO,
        supplied_ipv4: str | None = None,
        supplied_ipv6: str | None = None,
        source: str = "manual",
    ) -> dict[str, UpdateResult]:
        """Update one or more configured domains individually at STRATO."""
        selected = hostnames or list(self.domain_configs)
        public_ip_cache: dict[int, str | None] = {}
        results: dict[str, UpdateResult] = {}
        last_used_ipv4: str | None = None
        last_used_ipv6: str | None = None

        for hostname in selected:
            domain_config = self.domain_configs.get(hostname)
            if domain_config is None:
                results[hostname] = UpdateResult(
                    hostname=hostname,
                    status=STATUS_ERROR,
                    response=RESPONSE_NOHOST,
                    response_code=RESPONSE_NOHOST,
                )
                continue

            state = self._states[hostname]
            state.ipv4_enabled = domain_config.ipv4_enabled
            state.ipv6_enabled = domain_config.ipv6_enabled

            if not domain_config.enabled:
                state.status = STATUS_DISABLED
                results[hostname] = UpdateResult(
                    hostname=hostname,
                    status=STATUS_DISABLED,
                    response=RESPONSE_DISABLED,
                    response_code=RESPONSE_DISABLED,
                    ipv4=state.current_ipv4,
                    ipv6=state.current_ipv6,
                )
                continue

            if ip_version == MODE_IPV4:
                do_ipv4 = domain_config.ipv4_enabled
                do_ipv6 = False
            elif ip_version == MODE_IPV6:
                do_ipv4 = False
                do_ipv6 = domain_config.ipv6_enabled
            else:
                do_ipv4 = domain_config.ipv4_enabled
                do_ipv6 = domain_config.ipv6_enabled

            if not do_ipv4 and not do_ipv6:
                state.status = STATUS_DISABLED
                results[hostname] = UpdateResult(
                    hostname=hostname,
                    status=STATUS_DISABLED,
                    response=RESPONSE_DISABLED,
                    response_code=RESPONSE_DISABLED,
                    ipv4=state.current_ipv4,
                    ipv6=state.current_ipv6,
                )
                continue

            ipv4 = supplied_ipv4 if do_ipv4 else None
            ipv6 = supplied_ipv6 if do_ipv6 else None

            if do_ipv4 and not ipv4:
                ipv4 = await self._async_get_public_ip(4, public_ip_cache)
            if do_ipv6 and not ipv6:
                ipv6 = await self._async_get_public_ip(6, public_ip_cache)

            if ipv4:
                last_used_ipv4 = ipv4
            if ipv6:
                last_used_ipv6 = ipv6

            myip_parts = [part for part in (ipv4, ipv6) if part]
            if not myip_parts:
                self._apply_state_from_response(
                    hostname,
                    RESPONSE_911,
                    ipv4=state.current_ipv4,
                    ipv6=state.current_ipv6,
                )
                results[hostname] = UpdateResult(
                    hostname=hostname,
                    status=STATUS_ERROR,
                    response=RESPONSE_911,
                    response_code=RESPONSE_911,
                    ipv4=state.current_ipv4,
                    ipv6=state.current_ipv6,
                )
                continue

            response_lines = await self._async_call_strato_group([hostname], ",".join(myip_parts))
            response_text = response_lines[0]
            response_code = self._response_code(response_text)
            parsed_status = self._parse_status(response_code)
            self._apply_state_from_response(hostname, response_text, ipv4=ipv4, ipv6=ipv6)

            _LOGGER.debug(
                "Updated STRATO DynDNS host %s via %s with result %s",
                hostname,
                source,
                response_text,
            )

            results[hostname] = UpdateResult(
                hostname=hostname,
                status=parsed_status,
                response=response_text,
                response_code=response_code,
                ipv4=ipv4 or state.current_ipv4,
                ipv6=ipv6 or state.current_ipv6,
            )

        if results:
            self._store_service_snapshot(ipv4=last_used_ipv4, ipv6=last_used_ipv6)
        self.async_set_updated_data(dict(self._states))
        return results

    async def async_update_supported_domains_for_family(
        self,
        ip_version: str,
        *,
        supplied_ipv4: str | None = None,
        supplied_ipv6: str | None = None,
        source: str = "service_button",
    ) -> tuple[str, dict[str, UpdateResult]]:
        """Update all enabled domains that support one IP family."""
        hostnames = [
            hostname
            for hostname, config in self.domain_configs.items()
            if (ip_version == MODE_IPV4 and config.ipv4_enabled)
            or (ip_version == MODE_IPV6 and config.ipv6_enabled)
        ]
        if not hostnames:
            return RESPONSE_UNKNOWN, {}

        public_ip_cache: dict[int, str | None] = {}
        ipv4 = supplied_ipv4
        ipv6 = supplied_ipv6
        if ip_version == MODE_IPV4 and not ipv4:
            ipv4 = await self._async_get_public_ip(4, public_ip_cache)
        if ip_version == MODE_IPV6 and not ipv6:
            ipv6 = await self._async_get_public_ip(6, public_ip_cache)

        if ip_version == MODE_IPV4:
            if not ipv4:
                results = self._apply_group_failure(hostnames)
            else:
                results = await self._async_apply_group_update(
                    hostnames=hostnames,
                    myip=ipv4,
                    ipv4=ipv4,
                    ipv6=None,
                    source=source,
                )
        else:
            if not ipv6:
                results = self._apply_group_failure(hostnames)
            else:
                results = await self._async_apply_group_update(
                    hostnames=hostnames,
                    myip=ipv6,
                    ipv4=None,
                    ipv6=ipv6,
                    source=source,
                )

        overall_response = self.pick_worst_response_code([result.response_code for result in results.values()])
        self._last_webhook_response = overall_response
        self._store_service_snapshot(ipv4=ipv4, ipv6=ipv6)
        self.async_set_updated_data(dict(self._states))
        return overall_response, results

    async def async_update_all_domains_via_webhook(
        self,
        *,
        supplied_ipv4: str | None = None,
        supplied_ipv6: str | None = None,
        request_from: str | None = None,
        source: str = "router_webhook",
    ) -> tuple[str, dict[str, UpdateResult]]:
        """Update all configured domains in up to three grouped STRATO requests."""
        public_ip_cache: dict[int, str | None] = {}
        grouped_hostnames = {
            MODE_IPV4: [
                hostname
                for hostname, config in self.domain_configs.items()
                if config.ipv4_enabled and not config.ipv6_enabled
            ],
            MODE_IPV6: [
                hostname
                for hostname, config in self.domain_configs.items()
                if config.ipv6_enabled and not config.ipv4_enabled
            ],
            MODE_BOTH: [
                hostname
                for hostname, config in self.domain_configs.items()
                if config.ipv4_enabled and config.ipv6_enabled
            ],
        }
        results: dict[str, UpdateResult] = {}
        response_codes_for_severity: list[str] = []

        for hostname, domain_config in self.domain_configs.items():
            state = self._states[hostname]
            state.ipv4_enabled = domain_config.ipv4_enabled
            state.ipv6_enabled = domain_config.ipv6_enabled
            if not domain_config.enabled:
                state.status = STATUS_DISABLED

        if grouped_hostnames[MODE_IPV4]:
            ipv4 = supplied_ipv4 or await self._async_get_public_ip(4, public_ip_cache)
            if ipv4:
                group_results = await self._async_apply_group_update(
                    hostnames=grouped_hostnames[MODE_IPV4],
                    myip=ipv4,
                    ipv4=ipv4,
                    ipv6=None,
                    source=source,
                )
            else:
                group_results = self._apply_group_failure(grouped_hostnames[MODE_IPV4])
            results.update(group_results)
            response_codes_for_severity.extend(result.response_code for result in group_results.values())

        if grouped_hostnames[MODE_IPV6]:
            ipv6 = supplied_ipv6 or await self._async_get_public_ip(6, public_ip_cache)
            if ipv6:
                group_results = await self._async_apply_group_update(
                    hostnames=grouped_hostnames[MODE_IPV6],
                    myip=ipv6,
                    ipv4=None,
                    ipv6=ipv6,
                    source=source,
                )
            else:
                group_results = self._apply_group_failure(grouped_hostnames[MODE_IPV6])
            results.update(group_results)
            response_codes_for_severity.extend(result.response_code for result in group_results.values())

        if grouped_hostnames[MODE_BOTH]:
            ipv4 = supplied_ipv4 or await self._async_get_public_ip(4, public_ip_cache)
            ipv6 = supplied_ipv6 or await self._async_get_public_ip(6, public_ip_cache)
            if ipv4 and ipv6:
                group_results = await self._async_apply_group_update(
                    hostnames=grouped_hostnames[MODE_BOTH],
                    myip=f"{ipv4},{ipv6}",
                    ipv4=ipv4,
                    ipv6=ipv6,
                    source=source,
                )
            else:
                group_results = self._apply_group_failure(grouped_hostnames[MODE_BOTH])
            results.update(group_results)
            response_codes_for_severity.extend(result.response_code for result in group_results.values())

        overall_response = self.pick_worst_response_code(response_codes_for_severity)
        self._last_webhook_response = overall_response
        self._store_service_snapshot(
            ipv4=supplied_ipv4 or public_ip_cache.get(4),
            ipv6=supplied_ipv6 or public_ip_cache.get(6),
            request_from=request_from,
        )
        self.async_set_updated_data(dict(self._states))
        return overall_response, results

    def _apply_group_failure(self, hostnames: list[str]) -> dict[str, UpdateResult]:
        """Apply a synthetic 911 error to a whole group."""
        results: dict[str, UpdateResult] = {}
        for hostname in hostnames:
            self._apply_state_from_response(hostname, RESPONSE_911)
            state = self._states[hostname]
            results[hostname] = UpdateResult(
                hostname=hostname,
                status=STATUS_ERROR,
                response=RESPONSE_911,
                response_code=RESPONSE_911,
                ipv4=state.current_ipv4,
                ipv6=state.current_ipv6,
            )
        return results

    async def _async_apply_group_update(
        self,
        *,
        hostnames: list[str],
        myip: str,
        ipv4: str | None,
        ipv6: str | None,
        source: str,
    ) -> dict[str, UpdateResult]:
        """Apply one grouped STRATO update call and map each line back to a domain."""
        response_lines = await self._async_call_strato_group(hostnames, myip)
        results: dict[str, UpdateResult] = {}

        for index, hostname in enumerate(hostnames):
            response_text = response_lines[index] if index < len(response_lines) else RESPONSE_911
            response_code = self._response_code(response_text)
            parsed_status = self._parse_status(response_code)
            self._apply_state_from_response(hostname, response_text, ipv4=ipv4, ipv6=ipv6)
            state = self._states[hostname]

            _LOGGER.debug(
                "Updated STRATO DynDNS host %s via %s with result %s",
                hostname,
                source,
                response_text,
            )

            results[hostname] = UpdateResult(
                hostname=hostname,
                status=parsed_status,
                response=response_text,
                response_code=response_code,
                ipv4=ipv4 or state.current_ipv4,
                ipv6=ipv6 or state.current_ipv6,
            )

        return results

    def _apply_state_from_response(
        self,
        hostname: str,
        response_text: str,
        *,
        ipv4: str | None = None,
        ipv6: str | None = None,
    ) -> None:
        """Persist one response line onto a domain state."""
        state = self._states[hostname]
        response_code = self._response_code(response_text)
        state.last_updated = dt_util.now().isoformat()
        state.last_response = response_text
        state.last_response_code = response_code
        state.status = self._parse_status(response_code)
        if ipv4:
            state.current_ipv4 = ipv4
        if ipv6:
            state.current_ipv6 = ipv6

    async def _async_get_public_ip(
        self, ip_version: int, cache: dict[int, str | None]
    ) -> str | None:
        """Determine the current public IPv4 or IPv6 address."""
        if ip_version in cache:
            return cache[ip_version]

        url = PUBLIC_IPV4_DISCOVERY_URL if ip_version == 4 else PUBLIC_IPV6_DISCOVERY_URL
        value: str | None = None
        try:
            async with asyncio.timeout(15):
                async with self._session.get(url, headers={"User-Agent": DEFAULT_NAME}) as response:
                    response.raise_for_status()
                    candidate = (await response.text()).strip()
            parsed = ipaddress.ip_address(candidate)
            if parsed.version == ip_version:
                value = str(parsed)
        except (ClientError, TimeoutError, ValueError, OSError) as err:
            _LOGGER.debug("Could not determine public IPv%s address: %s", ip_version, err)

        cache[ip_version] = value
        return value

    async def _async_call_strato_group(self, hostnames: list[str], myip: str) -> list[str]:
        """Call the STRATO DynDNS update endpoint for one or more hostnames."""
        try:
            async with asyncio.timeout(30):
                async with self._session.get(
                    STRATO_UPDATE_URL,
                    params={"hostname": ",".join(hostnames), "myip": myip},
                    auth=BasicAuth(self._username, self._password),
                    headers={"User-Agent": DEFAULT_NAME},
                ) as response:
                    text = (await response.text()).strip()
        except TimeoutError:
            _LOGGER.warning("STRATO DynDNS update timed out for %s", ",".join(hostnames))
            return [RESPONSE_911] * max(1, len(hostnames))
        except (ClientError, OSError) as err:
            _LOGGER.warning("STRATO DynDNS update failed for %s: %s", ",".join(hostnames), err)
            return [RESPONSE_911] * max(1, len(hostnames))

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            lines = [RESPONSE_ERROR]

        if len(lines) == 1 and len(hostnames) > 1:
            return lines * len(hostnames)
        if len(lines) < len(hostnames):
            return [*lines, *([RESPONSE_911] * (len(hostnames) - len(lines)))]
        return lines[: len(hostnames)]

    @staticmethod
    def _response_code(response_text: str | None) -> str:
        """Normalize a full response line to a response code."""
        if not response_text:
            return RESPONSE_UNKNOWN
        token = str(response_text).strip().split()[0].lower()
        if token.startswith(RESPONSE_GOOD):
            return RESPONSE_GOOD
        if token.startswith(RESPONSE_NOCHG):
            return RESPONSE_NOCHG
        if token in {
            RESPONSE_DONATOR,
            RESPONSE_911,
            RESPONSE_ABUSE,
            RESPONSE_BADAGENT,
            RESPONSE_BADAUTH,
            RESPONSE_DNSERR,
            RESPONSE_ERROR,
            RESPONSE_NOHOST,
            RESPONSE_NOTFQDN,
            RESPONSE_NUMHOST,
            RESPONSE_OK,
            RESPONSE_TIMEOUT,
            RESPONSE_UNKNOWN,
        }:
            return token
        if token.startswith("http_"):
            return RESPONSE_ERROR
        if token == RESPONSE_DISABLED:
            return RESPONSE_DISABLED
        if token == RESPONSE_SKIPPED:
            return RESPONSE_SKIPPED
        return RESPONSE_UNKNOWN

    @staticmethod
    def _parse_status(response_code: str) -> str:
        """Map a response code to an internal status."""
        if response_code in (RESPONSE_GOOD, RESPONSE_OK):
            return STATUS_UPDATED
        if response_code == RESPONSE_NOCHG:
            return STATUS_UNCHANGED
        if response_code == RESPONSE_DISABLED:
            return STATUS_DISABLED
        if response_code == RESPONSE_SKIPPED:
            return STATUS_SKIPPED
        if response_code == RESPONSE_UNKNOWN:
            return STATUS_IDLE
        return STATUS_ERROR

    @staticmethod
    def _response_severity(response_code: str) -> int:
        """Return a severity score for a normalized response code."""
        if response_code in (RESPONSE_GOOD, RESPONSE_OK):
            return 0
        if response_code == RESPONSE_NOCHG:
            return 1
        if response_code == RESPONSE_UNKNOWN:
            return 40
        if response_code == RESPONSE_NOHOST:
            return 50
        if response_code in (RESPONSE_NOTFQDN, RESPONSE_NUMHOST):
            return 55
        if response_code == RESPONSE_DNSERR:
            return 70
        if response_code == RESPONSE_BADAGENT:
            return 75
        if response_code == RESPONSE_BADAUTH:
            return 80
        if response_code == RESPONSE_ABUSE:
            return 85
        if response_code == RESPONSE_DONATOR:
            return 86
        if response_code == RESPONSE_911:
            return 90
        if response_code == RESPONSE_TIMEOUT:
            return 95
        if response_code == RESPONSE_ERROR:
            return 96
        return 99

    @classmethod
    def pick_worst_response_code(cls, response_codes: list[str]) -> str:
        """Pick the single most severe response code for the caller."""
        if not response_codes:
            return RESPONSE_UNKNOWN
        return max(response_codes, key=cls._response_severity)

    def build_service_response(
        self,
        results: dict[str, UpdateResult],
        overall_response: str,
    ) -> dict[str, Any]:
        """Build a structured response for the Home Assistant service call."""
        return {
            "overall_response": overall_response,
            "domains": {
                hostname: {
                    "status": result.status,
                    "response_code": result.response_code,
                    "response": result.response,
                    "ipv4": result.ipv4,
                    "ipv6": result.ipv6,
                }
                for hostname, result in sorted(results.items())
            },
        }

    def build_webhook_service_sensor_value(self, key: str) -> Any:
        """Return the native value for a service-level diagnostic sensor."""
        if key == ATTR_WEBHOOK_URL:
            return self.external_webhook_url()
        if key == ATTR_FRITZBOX_URL:
            return self.fritzbox_update_template()
        if key == ATTR_LAST_WEBHOOK_RESPONSE:
            return self._last_webhook_response
        if key == ATTR_CURRENT_IPV4:
            return self._service_current_ipv4
        if key == ATTR_CURRENT_IPV6:
            return self._service_current_ipv6
        if key == ATTR_LAST_UPDATE:
            return dt_util.parse_datetime(self._service_last_update) if self._service_last_update else None
        if key == ATTR_REQUEST_FROM:
            return self._service_request_from
        return None

    def build_domain_diagnostic_value(self, hostname: str, key: str) -> Any:
        """Return the native value for one domain diagnostic sensor."""
        state = self._states[hostname]
        if key == ATTR_STATUS:
            return state.status or STATUS_IDLE
        if key == ATTR_ENABLED:
            return ENABLED_STATE_ENABLED if state.enabled else ENABLED_STATE_DISABLED
        if key == ATTR_UPDATE_MODE:
            return state.update_mode
        if key == ATTR_CURRENT_IPV4:
            return state.current_ipv4
        if key == ATTR_CURRENT_IPV6:
            return state.current_ipv6
        if key == ATTR_LAST_UPDATE:
            return dt_util.parse_datetime(state.last_updated) if state.last_updated else None
        if key == ATTR_LAST_SERVER_RESPONSE:
            return state.last_response
        if key == ATTR_RESPONSE_CODE:
            return state.last_response_code
        return None
