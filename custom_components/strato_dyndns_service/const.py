"""Constants for the STRATO DynDNS Service integration."""

from __future__ import annotations

DOMAIN = "strato_dyndns_service"
DEFAULT_NAME = "STRATO DynDNS Service"
PLATFORMS: list[str] = ["sensor", "button", "switch"]

CONF_DOMAINS = "domains"
CONF_ENABLED = "enabled"
CONF_HOSTNAME = "hostname"
CONF_IPV4_ENABLED = "ipv4_enabled"
CONF_IPV6_ENABLED = "ipv6_enabled"
CONF_PASSWORD = "password"
CONF_UPDATE_MODE = "update_mode"
CONF_USERNAME = "username"
CONF_WEBHOOK_ID = "webhook_id"

DATA_COORDINATORS = "coordinators"
DATA_SERVICES_REGISTERED = "services_registered"
DATA_VIEW_REGISTERED = "view_registered"

MODE_NONE = "none"
MODE_IPV4 = "ipv4"
MODE_IPV6 = "ipv6"
MODE_BOTH = "both"
VALID_MODES = [MODE_NONE, MODE_IPV4, MODE_IPV6, MODE_BOTH]

IP_VERSION_AUTO = "auto"
IP_VERSION_OPTIONS = [IP_VERSION_AUTO, MODE_IPV4, MODE_IPV6]

SERVICE_UPDATE_DOMAINS = "update_domains"
SERVICE_FIELD_DEVICE_ID = "device_id"
SERVICE_FIELD_IP_VERSION = "ip_version"

ATTR_CURRENT_IPV4 = "current_ipv4"
ATTR_CURRENT_IPV6 = "current_ipv6"
ATTR_LAST_UPDATE = "last_update"
ATTR_LAST_SERVER_RESPONSE = "last_server_response"
ATTR_DOMAIN = "domain"
ATTR_ENABLED = "enabled"
ATTR_UPDATE_MODE = "update_mode"
ATTR_WEBHOOK_URL = "webhook_url"
ATTR_FRITZBOX_URL = "fritzbox_update_url"
ATTR_LAST_WEBHOOK_RESPONSE = "last_webhook_response"
ATTR_REQUEST_FROM = "request_from"
ATTR_RESPONSE_CODE = "response_code"
ATTR_STATUS = "status"

STATUS_IDLE = "idle"
STATUS_UPDATED = "updated"
STATUS_UNCHANGED = "unchanged"
STATUS_DISABLED = "disabled"
STATUS_SKIPPED = "skipped"
STATUS_ERROR = "error"

RESPONSE_DONATOR = "!donator"
RESPONSE_911 = "911"
RESPONSE_ABUSE = "abuse"
RESPONSE_BADAGENT = "badagent"
RESPONSE_BADAUTH = "badauth"
RESPONSE_DNSERR = "dnserr"
RESPONSE_ERROR = "error"
RESPONSE_GOOD = "good"
RESPONSE_NOCHG = "nochg"
RESPONSE_NOHOST = "nohost"
RESPONSE_NOTFQDN = "notfqdn"
RESPONSE_NUMHOST = "numhost"
RESPONSE_OK = "ok"
RESPONSE_TIMEOUT = "timeout"
RESPONSE_UNKNOWN = "unknown"
RESPONSE_DISABLED = "disabled"
RESPONSE_SKIPPED = "skipped"

RESPONSE_CODES = [
    RESPONSE_DONATOR,
    RESPONSE_911,
    RESPONSE_ABUSE,
    RESPONSE_BADAGENT,
    RESPONSE_BADAUTH,
    RESPONSE_DNSERR,
    RESPONSE_ERROR,
    RESPONSE_GOOD,
    RESPONSE_NOCHG,
    RESPONSE_NOHOST,
    RESPONSE_NOTFQDN,
    RESPONSE_NUMHOST,
    RESPONSE_OK,
    RESPONSE_TIMEOUT,
    RESPONSE_UNKNOWN,
]

ENABLED_STATE_ENABLED = "enabled"
ENABLED_STATE_DISABLED = "disabled"

STRATO_UPDATE_URL = "https://dyndns.strato.com/nic/update"
PUBLIC_IPV4_DISCOVERY_URL = "https://api.ipify.org"
PUBLIC_IPV6_DISCOVERY_URL = "https://api6.ipify.org"

WEBHOOK_URL = f"/api/{DOMAIN}/{{webhook_id}}"
MAIN_DEVICE_SUFFIX = "service"
