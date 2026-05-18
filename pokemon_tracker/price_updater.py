import logging
from apscheduler.schedulers.background import BackgroundScheduler
import database
import config

logger = logging.getLogger(__name__)


def update_all_prices(api):
    cards = [c for c in database.get_all_cards() if c.get("pokemontcg_id")]
    if not cards:
        logger.info("No cards with pokemontcg_id to update.")
        database.log_update(0, "skipped", "No cards with ID")
        return 0

    prices = {}
    for card in cards:
        try:
            prices[card["id"]] = api.get_prices(card["pokemontcg_id"])
        except Exception as exc:
            logger.error("Price fetch failed for %s: %s", card["name"], exc)

    if prices:
        database.update_prices(prices)

    updated = len(prices)
    database.log_update(updated, "ok", f"Updated {updated}/{len(cards)} cards")
    logger.info("Price update done: %d/%d", updated, len(cards))
    return updated


def start_scheduler(api):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        update_all_prices,
        args=[api],
        trigger="interval",
        hours=config.UPDATE_INTERVAL_HOURS,
        id="price_update",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
