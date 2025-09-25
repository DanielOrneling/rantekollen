"""Config flow för Räntekollen."""
from homeassistant import config_entries
import aiohttp
from bs4 import BeautifulSoup

from . import DOMAIN

BANKS_URL = "https://www.konsumenternas.se/konsumentstod/jamforelser/lan--betalningar/lan/jamfor-borantor/"

async def fetch_banks():
    async with aiohttp.ClientSession() as session:
        async with session.get(BANKS_URL) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            options = []
            table = soup.find("table")
            if not table:
                return options
            for row in table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if cells:
                    bank = cells[0].get_text(strip=True)
                    if bank and bank not in options:
                        options.append(bank)
            return options

class RantekollenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow för Räntekollen."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input["bank"], data=user_input)

        banks = await fetch_banks()
        if not banks:
            banks = ["Ingen bank hittad"]
        return self.async_show_form(
            step_id="user",
            data_schema=self.hass.helpers.config_validation.Schema({
                "bank": self.hass.helpers.config_validation.Select(banks)
            })
        )
