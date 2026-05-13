import requests
from requests_oauthlib import OAuth1
from urllib.parse import quote
import config


class CardMarketAPI:
    POKEMON_GAME_ID = 3  # Pokemon TCG on CardMarket

    def __init__(self):
        if config.CARDMARKET_SANDBOX:
            self.base_url = "https://sandbox.cardmarket.com/ws/v2.0/output.json"
        else:
            self.base_url = "https://api.cardmarket.com/ws/v2.0/output.json"

        self.auth = OAuth1(
            config.CARDMARKET_APP_TOKEN,
            client_secret=config.CARDMARKET_APP_SECRET,
            resource_owner_key=config.CARDMARKET_ACCESS_TOKEN,
            resource_owner_secret=config.CARDMARKET_ACCESS_SECRET,
        )

    @property
    def is_configured(self):
        return all([
            config.CARDMARKET_APP_TOKEN,
            config.CARDMARKET_APP_SECRET,
            config.CARDMARKET_ACCESS_TOKEN,
            config.CARDMARKET_ACCESS_SECRET,
        ])

    def search_products(self, name, exact=False):
        """Search for Pokemon products by name. Returns a list of product dicts."""
        encoded = quote(name, safe="")
        exact_flag = 1 if exact else 0
        url = f"{self.base_url}/products/{encoded}/{self.POKEMON_GAME_ID}/0/{exact_flag}"
        r = requests.get(url, auth=self.auth, timeout=15)
        r.raise_for_status()
        data = r.json()
        products = data.get("product", [])
        # API returns a dict for single result, list for multiple
        if isinstance(products, dict):
            products = [products]
        return products

    def get_product(self, product_id):
        """Get full product details including priceGuide."""
        url = f"{self.base_url}/products/{product_id}"
        r = requests.get(url, auth=self.auth, timeout=15)
        r.raise_for_status()
        return r.json().get("product", {})

    def get_prices(self, product_id):
        """Return normalised price dict for a product."""
        product = self.get_product(product_id)
        guide = product.get("priceGuide", {})
        return {
            "price_low": guide.get("LOW"),
            "price_trend": guide.get("TREND"),
            "price_avg": guide.get("AVG"),
        }
