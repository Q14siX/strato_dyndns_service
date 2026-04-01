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
    CONF_ENABLED,
    CONF_HOSTNAME,
    CONF_PASSWORD,
    CONF_UPDATE_MODE,
    CONF_USERNAME,
    CONF_WEBHOOK_ID,
    DEFAULT_NAME,
    DOMAIN,
    MODE_BOTH,
    MODE_IPV4,
    MODE_IPV6,
)
from .helpers import ensure_list, is_valid_hostname, merged_entry_config, normalize_hostname

CONF_DOMAINS_INPUT = "domains"
FLOW_MODE_USER = "user"
FLOW_MODE_RECONFIGURE = "reconfigure"


def _update_mode_selector(default: str = MODE_BOTH) -> SelectSelector:
    """Build a translated select selector for the update mode."""
    return SelectSelector(
        SelectSelectorConfig(
            options=[MODE_IPV4, MODE_IPV6, MODE_BOTH],
            mode=SelectSelectorMode.LIST,
            translation_key="update_mode",
        )
    )


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
    _configure_index: int
    _defaults_by_hostname: dict[str, dict[str, Any]]
    _webhook_id: str
    _flow_mode: str
    _existing_domains: list[dict[str, Any]]

    def _init_wizard_state(self) -> None:
        """Initialize common wizard state."""
        self._username = ""
        self._password = ""
        self._pending_hostnames = []
        self._domains = []
        self._configure_index = 0
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

    def _start_domain_configuration(
        self,
        *,
        existing_domains: list[dict[str, Any]] | None,
        webhook_id: str | None,
        flow_mode: str,
    ) -> None:
        """Store normalized wizard data before per-domain configuration."""
        self._domains = []
        self._configure_index = 0
        self._flow_mode = flow_mode
        self._existing_domains = list(existing_domains or [])
        self._webhook_id = webhook_id or secrets.token_urlsafe(24)
        self._defaults_by_hostname = {
            normalize_hostname(item.get(CONF_HOSTNAME)): {
                CONF_UPDATE_MODE: str(item.get(CONF_UPDATE_MODE, MODE_BOTH)).lower(),
                CONF_ENABLED: bool(item.get(CONF_ENABLED, True)),
            }
            for item in self._existing_domains
            if normalize_hostname(item.get(CONF_HOSTNAME))
        }

    async def _async_next_domain_step(self):
        """Continue to the per-domain configuration step."""
        self._configure_index = 0
        return await self.async_step_configure_domain()

    async def async_step_configure_domain(self, user_input: dict[str, Any] | None = None):
        """Configure one previously collected domain."""
        hostname = self._pending_hostnames[self._configure_index]
        defaults = self._defaults_by_hostname.get(
            hostname,
            {CONF_UPDATE_MODE: MODE_BOTH, CONF_ENABLED: True},
        )

        if user_input is not None:
            self._domains.append(
                {
                    CONF_HOSTNAME: hostname,
                    CONF_UPDATE_MODE: str(user_input[CONF_UPDATE_MODE]).lower(),
                    CONF_ENABLED: bool(user_input[CONF_ENABLED]),
                }
            )
            self._configure_index += 1
            if self._configure_index < len(self._pending_hostnames):
                return await self.async_step_configure_domain()
            return await self._async_finish_domain_configuration()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_MODE,
                    default=defaults.get(CONF_UPDATE_MODE, MODE_BOTH),
                ): _update_mode_selector(str(defaults.get(CONF_UPDATE_MODE, MODE_BOTH)).lower()),
                vol.Required(
                    CONF_ENABLED,
                    default=bool(defaults.get(CONF_ENABLED, True)),
                ): bool,
            }
        )
        return self.async_show_form(
            step_id="configure_domain",
            data_schema=schema,
            description_placeholders={
                "hostname": hostname,
                "position": str(self._configure_index + 1),
                "total": str(len(self._pending_hostnames)),
            },
        )


class StratoDynDNSServiceConfigFlow(
    _BaseDomainWizard, config_entries.ConfigFlow, domain=DOMAIN
):
    """Handle a config flow for STRATO DynDNS Service."""

    VERSION = 1
    MINOR_VERSION = 5

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
                flow_mode = self._flow_mode or FLOW_MODE_USER
                existing_domains = self._existing_domains if flow_mode != FLOW_MODE_USER else []
                webhook_id = self._webhook_id if flow_mode != FLOW_MODE_USER else None
                self._start_domain_configuration(
                    existing_domains=existing_domains,
                    webhook_id=webhook_id,
                    flow_mode=flow_mode,
                )
                return await self._async_next_domain_step()

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
                self._start_domain_configuration(
                    existing_domains=self._existing_domains,
                    webhook_id=self._webhook_id,
                    flow_mode=FLOW_MODE_RECONFIGURE,
                )
                return await self._async_next_domain_step()

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

