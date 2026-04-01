"""HTTP view for router-triggered STRATO DynDNS updates."""

from __future__ import annotations

import logging
import socket

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATORS, DOMAIN, WEBHOOK_URL
from .helpers import parse_myip

_LOGGER = logging.getLogger(__name__)


async def _describe_requester(hass: HomeAssistant, request: web.Request) -> str | None:
    """Build a human-readable requester string as hostname plus IPs."""
    remote_ip = request.remote
    if not remote_ip:
        return None

    try:
        hostname, _aliases, ip_addresses = await hass.async_add_executor_job(socket.gethostbyaddr, remote_ip)
    except OSError:
        hostname = remote_ip
        ip_addresses = [remote_ip]

    unique_ips = []
    for value in [*ip_addresses, remote_ip]:
        if value not in unique_ips:
            unique_ips.append(value)

    return f"{hostname} ({', '.join(unique_ips)})"


class StratoDynDNSWebhookView(HomeAssistantView):
    """Handle unauthenticated DynDNS-style webhook requests."""

    name = f"api:{DOMAIN}"
    url = WEBHOOK_URL
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the webhook view."""
        self.hass = hass

    async def get(self, request: web.Request, webhook_id: str) -> web.Response:
        """Handle a GET webhook request."""
        return await self._handle_request(request, webhook_id)

    async def post(self, request: web.Request, webhook_id: str) -> web.Response:
        """Handle a POST webhook request."""
        return await self._handle_request(request, webhook_id)

    async def _handle_request(self, request: web.Request, webhook_id: str) -> web.Response:
        """Process a router webhook and return one DynDNS-style status line."""
        coordinators = self.hass.data[DOMAIN][DATA_COORDINATORS]
        coordinator = coordinators.get(webhook_id)
        if coordinator is None:
            return web.Response(status=404, text="nohost", content_type="text/plain")

        raw_myip = request.query.get("myip")
        ipv4, ipv6 = parse_myip(raw_myip)
        if not ipv4:
            ipv4 = request.query.get("ipaddr")
        if not ipv6:
            ipv6 = request.query.get("ip6addr")

        requester = await _describe_requester(self.hass, request)

        response_text, _results = await coordinator.async_update_all_domains_via_webhook(
            supplied_ipv4=ipv4,
            supplied_ipv6=ipv6,
            request_from=requester,
            source="router_webhook",
        )

        _LOGGER.debug("Webhook %s returned: %s", webhook_id, response_text)
        return web.Response(text=response_text, content_type="text/plain")
