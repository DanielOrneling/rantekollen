"""Sensorer för listräntor."""
import logging
import aiohttp
from bs4 import BeautifulSoup

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

URL = "https://www.konsumenternas.se/konsumentstod/jamforelser/lan--betalningar/lan/jamfor-borantor/"
TERMS = ["3 mån", "1 år", "2 år", "3 år", "5 år"]

class ListratesCoordinator(DataUpdateCoordinator):
    """Koordinator för listräntor."""

    def __init__(self, hass, bank):
        self.bank = bank
        super().__init__(
            hass,
            _LOGGER,
            name=f"Listräntor {bank}",
            update_interval=None,  # kan sättas till timedelta(hours=24)
        )

    async def _async_update_data(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                table = soup.find("table")
                if not table:
                    raise UpdateFailed("Ingen tabell hittad på sidan")
                rates = {}
                for row in table.find_all("tr")[1:]:
                    cells = row.find_all("td")
                    if len(cells) < 2:
                        continue
                    bank_name = cells[0].get_text(strip=True)
                    if bank_name != self.bank:
                        continue
                    for i, term in enumerate(TERMS, start=1):
                        if i < len(cells):
                            value = cells[i].get_text(strip=True).replace(",", ".")
                            try:
                                rates[term] = float(value)
                            except ValueError:
                                rates[term] = None
                if not rates:
                    raise UpdateFailed(f"Inga räntor hittades för {self.bank}")
                return rates

from homeassistant.components.sensor import SensorEntity

class ListrateSensor(SensorEntity):
    """Sensor för en viss bindningstid."""

    def __init__(self, coordinator, term):
        self.coordinator = coordinator
        self.term = term
        self._attr_name = f"Listränta {term}"
        self._attr_unique_id = f"{coordinator.bank}_{term}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self.term)

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_update(self):
        await self.coordinator.async_request_refresh()
