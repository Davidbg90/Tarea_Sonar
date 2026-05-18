import requests
import config


class PokemonTCGAPI:
    BASE_URL = "https://api.pokemontcg.io/v2"

    def __init__(self):
        self.headers = {}
        if config.POKEMONTCG_API_KEY:
            self.headers["X-Api-Key"] = config.POKEMONTCG_API_KEY

    @property
    def is_configured(self):
        return True  # Works without API key (1000 req/day)

    def search_cards(self, name):
        r = requests.get(
            f"{self.BASE_URL}/cards",
            params={"q": f'name:"{name}"', "orderBy": "-set.releaseDate", "pageSize": 20},
            headers=self.headers,
            timeout=20,
        )
        r.raise_for_status()
        return r.json().get("data", [])

    def get_card(self, card_id):
        r = requests.get(f"{self.BASE_URL}/cards/{card_id}", headers=self.headers, timeout=20)
        r.raise_for_status()
        return r.json().get("data", {})

    def get_prices(self, pokemontcg_id):
        card = self.get_card(pokemontcg_id)
        cm = card.get("cardmarket", {}).get("prices", {})
        images = card.get("images", {})
        return {
            "price_low": cm.get("lowPrice"),
            "price_trend": cm.get("trendPrice"),
            "price_avg": cm.get("averageSellPrice"),
            "price_avg1": cm.get("avg1"),
            "price_avg7": cm.get("avg7"),
            "price_avg30": cm.get("avg30"),
            "image_url": images.get("small", ""),
            "image_url_large": images.get("large", ""),
        }
