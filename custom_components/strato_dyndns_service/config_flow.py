"""Config flow for STRATO DynDNS Service."""

from __future__ import annotations

import secrets
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_DOMAINS,
    CONF_HOSTNAME,
    CONF_IPV4_ENABLED,
    CONF_IPV6_ENABLED,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_WEBHOOK_ID,
    DEFAULT_NAME,
    DOMAIN,
)
from .helpers import build_domain_configs, ensure_list, is_valid_hostname, merged_entry_config, normalize_hostname

CONF_DOMAINS_INPUT = "domains"
FLOW_MODE_USER = "user"
FLOW_MODE_RECONFIGURE = "reconfigure"


def _domains_selector(default: list[str] | None = None) -> SelectSelector:
    """Build a chip-style selector for domains/subdomains."""
    values = default or []
    return SelectSelector(
        SelectSelectorConfig(
            options=values,
            multiple=True,
            custom_value=True,
            mode=SelectSelectorMode.DROPDOWN,
            translation_key="domains_input",
        )
    )


def _prepare_domains(raw_value: Any) -> tuple[list[str], str | None]:
    """Normalize and validate a list of hostnames."""
    normalized: list[str] = []
    seen: set[str] = set()

    for item in ensure_list(raw_value):
        hostname = normalize_hostname(item)
        if not hostname:
            continue
        if not is_valid_hostname(hostname):
            return [], "invalid_hostname"
        if hostname in seen:
            return [], "duplicate_hostname"
        seen.add(hostname)
        normalized.append(hostname)

    if not normalized:
        return [], "no_domains"

    return normalized, None


def _build_entry_title(hostnames: list[str]) -> str:
    """Build a human-readable config-entry title."""
    if not hostnames:
        return DEFAULT_NAME
    ordered = sorted(hostnames)
    first = ordered[0]
    remaining = len(ordered) - 1
    if remaining <= 0:
        return f"{DEFAULT_NAME} ({first})"
    return f"{DEFAULT_NAME} ({first} +{remaining})"


class _BaseDomainWizard:
    """Shared helper logic for the setup and reconfigure wizards."""

    _username: str
    _password: str
    _pending_hostnames: list[str]
    _domains: list[dict[str, Any]]
    _defaults_by_hostname: dict[str, dict[str, bool]]
    _webhook_id: str
    _flow_mode: str
    _existing_domains: list[dict[str, Any]]

    def _init_wizard_state(self) -> None:
        """Initialize common wizard state."""
        self._username = ""
        self._password = ""
        self._pending_hostnames = []
        self._domains = []
        self._defaults_by_hostname = {}
        self._webhook_id = ""
        self._flow_mode = FLOW_MODE_USER
        self._existing_domains = []

    def _credentials_schema(self, *, username: str, password: str) -> vol.Schema:
        """Return a schema for the credentials page."""
        return vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=username): str,
                vol.Required(CONF_PASSWORD, default=password): str,
            }
        )

    def _domains_schema(self, *, hostnames: list[str]) -> vol.Schema:
        """Return a schema for the dedicated domains page."""
        return vol.Schema(
            {
                vol.Required(CONF_DOMAINS_INPUT, default=hostnames): _domains_selector(hostnames),
            }
        )

    def _set_credentials_from_input(self, user_input: dict[str, Any]) -> str | None:
        """Store credentials from a wizard page and return an error if invalid."""
        self._username = str(user_input.get(CONF_USERNAME, "")).strip().lower()
        self._password = str(user_input.get(CONF_PASSWORD, "")).strip()
        if not self._username or not self._password:
            return "invalid_auth"
        return None

    def _prepare_and_store_hostnames(self, raw_value: Any) -> tuple[dict[str, str], list[str] | None]:
        """Validate hostnames from the dedicated domains page."""
        errors: dict[str, str] = {}
        hostnames, host_error = _prepare_domains(raw_value)
        if host_error:
            errors[CONF_DOMAINS_INPUT] = host_error
            return errors, None
        self._pending_hostnames = hostnames
        return errors, hostnames

    def _prepare_domain_defaults(
        self,
        *,
        existing_domains: list[dict[str, Any]] | None,
        webhook_id: str | None,
        flow_mode: str,
    ) -> None:
        """Store normalized wizard data before building the final payload."""
        self._domains = []
        self._flow_mode = flow_mode
        self._existing_domains = list(existing_domains or [])
        self._webhook_id = webhook_id or secrets.token_urlsafe(24)
        self._defaults_by_hostname = {
            config.hostname: {
                CONF_IPV4_ENABLED: bool(config.ipv4_enabled),
                CONF_IPV6_ENABLED: bool(config.ipv6_enabled),
            }
            for config in build_domain_configs({CONF_DOMAINS: self._existing_domains})
        }

    def _build_domains_payload(self) -> list[dict[str, Any]]:
        """Build the final domain payload with per-family toggles."""
        payload: list[dict[str, Any]] = []
        for hostname in self._pending_hostnames:
            defaults = self._defaults_by_hostname.get(
                hostname,
                {
                    CONF_IPV4_ENABLED: True,
                    CONF_IPV6_ENABLED: True,
                },
            )
            payload.append(
                {
                    CONF_HOSTNAME: hostname,
                    CONF_IPV4_ENABLED: bool(defaults.get(CONF_IPV4_ENABLED, True)),
                    CONF_IPV6_ENABLED: bool(defaults.get(CONF_IPV6_ENABLED, True)),
                }
            )
        return payload


class StratoDynDNSServiceConfigFlow(
    _BaseDomainWizard, config_entries.ConfigFlow, domain=DOMAIN
):
    """Handle a config flow for STRATO DynDNS Service."""

    VERSION = 1
    MINOR_VERSION = 6

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._init_wizard_state()

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Collect STRATO DynDNS credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            auth_error = self._set_credentials_from_input(user_input)
            if auth_error:
                errors["base"] = auth_error
            else:
                self._flow_mode = FLOW_MODE_USER
                return await self.async_step_domains()

        return self.async_show_form(
            step_id="user",
            data_schema=self._credentials_schema(username=self._username, password=self._password),
            errors=errors,
        )

    async def async_step_domains(self, user_input: dict[str, Any] | None = None):
        """Collect all domains or subdomains on a dedicated wizard page."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors, hostnames = self._prepare_and_store_hostnames(user_input.get(CONF_DOMAINS_INPUT))
            if not errors and hostnames is not None:
                self._prepare_domain_defaults(
                    existing_domains=[],
                    webhook_id=None,
                    flow_mode=FLOW_MODE_USER,
                )
                self._domains = self._build_domains_payload()
                return await self._async_finish_domain_configuration()

        return self.async_show_form(
            step_id="domains",
            data_schema=self._domains_schema(hostnames=self._pending_hostnames),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Allow reconfiguration from the config-entry action."""
        entry = self._get_reconfigure_entry()
        config = merged_entry_config(entry)
        errors: dict[str, str] = {}

        if user_input is not None:
            auth_error = self._set_credentials_from_input(user_input)
            if auth_error:
                errors["base"] = auth_error
            else:
                self._flow_mode = FLOW_MODE_RECONFIGURE
                self._existing_domains = list(config.get(CONF_DOMAINS, []))
                self._webhook_id = str(config.get(CONF_WEBHOOK_ID, "")) or ""
                return await self.async_step_reconfigure_domains()
        else:
            self._flow_mode = FLOW_MODE_RECONFIGURE
            self._username = str(config.get(CONF_USERNAME, ""))
            self._password = str(config.get(CONF_PASSWORD, ""))
            self._pending_hostnames = [
                normalize_hostname(item.get(CONF_HOSTNAME))
                for item in config.get(CONF_DOMAINS, [])
                if normalize_hostname(item.get(CONF_HOSTNAME))
            ]
            self._existing_domains = list(config.get(CONF_DOMAINS, []))
            self._webhook_id = str(config.get(CONF_WEBHOOK_ID, "")) or ""

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._credentials_schema(username=self._username, password=self._password),
            errors=errors,
        )

    async def async_step_reconfigure_domains(self, user_input: dict[str, Any] | None = None):
        """Edit all domains or subdomains on a dedicated reconfigure page."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors, hostnames = self._prepare_and_store_hostnames(user_input.get(CONF_DOMAINS_INPUT))
            if not errors and hostnames is not None:
                self._prepare_domain_defaults(
                    existing_domains=self._existing_domains,
                    webhook_id=self._webhook_id,
                    flow_mode=FLOW_MODE_RECONFIGURE,
                )
                self._domains = self._build_domains_payload()
                return await self._async_finish_domain_configuration()

        return self.async_show_form(
            step_id="reconfigure_domains",
            data_schema=self._domains_schema(hostnames=self._pending_hostnames),
            errors=errors,
        )

    async def _async_finish_domain_configuration(self):
        """Finalize the user or reconfigure wizard."""
        payload = {
            CONF_USERNAME: self._username,
            CONF_PASSWORD: self._password,
            CONF_DOMAINS: self._domains,
            CONF_WEBHOOK_ID: self._webhook_id,
        }
        title = _build_entry_title(self._pending_hostnames)

        if self._flow_mode == FLOW_MODE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            self.hass.config_entries.async_update_entry(entry, title=title)
            return self.async_update_reload_and_abort(
                entry,
                data_updates=payload,
            )

        await self.async_set_unique_id(self._webhook_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=title, data=payload)
