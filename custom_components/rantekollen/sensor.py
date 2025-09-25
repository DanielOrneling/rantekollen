"""Sensorer för Räntekollen (listräntor)."""
import logging
import aiohttp
from bs4 import BeautifulSoup
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.sensor import SensorEntity

_LOGGER = logging.getLogger(__name__)
URL = "https://www.konsumenternas.se/konsumentstod/jamforelser/lan--betalningar/lan/jamfor-borantor/"

# Bindningstider som vi vill skapa sensorer för
TERMS = ["3 mån", "1 år", "2 år", "3 år", "5 år"]

# Mappa till sensor-ID format
TERM_MAP = {
    "3 mån": "3_man",
    "1 år": "1_ar",
    "2 år": "2_ar",
    "3 år": "3_ar",
    "5 år": "5_ar",
}

# Bankförkortningar för sensor-ID
BANK_ABBREVIATIONS = {
    "Länsförsäkringar": "lf",
    "ICA Banken": "ica",
    "Nordea": "nordea",
    "SEB": "seb",
    "Swedbank": "swedbank",
    "Handelsbanken": "handelsbanken",
    "SBAB": "sbab",
    "Danske Bank": "db"
    # Lägg till fler banker från sidan om behövs
}

class ListratesCoordinator(DataUpdateCoordinator):
    """Koordinator för listräntor."""

    def __init__(self, hass, bank):
        self.bank = bank
        super().__init__(
            hass,
            _LOGGER,
            name=f"Räntekollen {bank}",
            update_interval=timedelta(hours=24),  # uppdateras varje dag
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


class ListrateSensor(SensorEntity):
    """Sensor för en viss bindningstid."""

    def __init__(self, coordinator, term):
        self.coordinator = coordinator
        self.term = term

        # Bestäm bankförkortning
        abbr = BANK_ABBREVIATIONS.get(self.coordinator.bank, self.coordinator.bank.lower().replace(" ", "_"))

        # Bestäm term-ID
        term_id = TERM_MAP.get(self.term, self.term.lower().replace(" ", "_"))

        # Sätt sensor-name och unique_id
        self._attr_name = f"Listränta {self.coordinator.bank} {self.term}"
        self._attr_unique_id = f"listranta_{abbr}_{term_id}"

    @property
    def native_value(self):
        """Returnerar räntan för denna bindningstid."""
        return self.coordinator.data.get(self.term)

    @property
    def available(self):
        """Sensor är tillgänglig om koordinatorn lyckats hämta data."""
        return self.coordinator.last_update_success

    async def async_update(self):
        """Uppdatera data via koordinatorn."""
        await self.coordinator.async_request_refresh()
