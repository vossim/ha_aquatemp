from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import TextSelector

from .domain.exceptions import AquaTempError
from .infrastructure.ble.frame_codec import build_read_frame
from .infrastructure.ble.transport import BleakTransport

DOMAIN = "aquatemp"

_MAC_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")

_SCHEMA = vol.Schema({vol.Required("mac_address"): TextSelector()})


class AquaTempConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            mac = user_input["mac_address"].strip().upper()

            if not _MAC_PATTERN.match(mac):
                errors["mac_address"] = "invalid_mac"
            else:
                try:
                    await self._validate_connection(mac)
                except AquaTempError:
                    errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(mac)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"AquaTemp {mac}",
                    data={"mac_address": mac},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_SCHEMA,
            errors=errors,
        )

    @staticmethod
    async def _validate_connection(mac_address: str) -> None:
        transport = BleakTransport(mac_address)
        await transport.send_and_receive(build_read_frame())
