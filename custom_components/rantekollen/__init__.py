"""Räntekollen integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .sensor import ListratesCoordinator

_LOGGER = logging.getLogger(__name__)
DOMAIN = "rantekollen"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up sensors via config flow."""
    coordinator = ListratesCoordinator(hass, entry.data["bank"])

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Kunde inte hämta listräntor: %s", err)
        raise ConfigEntryNotReady from err

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    return True
