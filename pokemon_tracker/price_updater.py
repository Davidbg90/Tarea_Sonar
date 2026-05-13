import logging
from apscheduler.schedulers.background import BackgroundScheduler
import database
import config

logger = logging.getLogger(__name__)


def update_all_prices(api):
    """Fetch updated prices for every card that has a CardMarket ID."""
    if not api.is_configured:
        logger.warning("CardMarket API not configured — skipping price update.")
        database.log_update(0, "skipped", "API not configured")
        return 0

    cards = [c for c in database.get_all_cards() if c.get("cardmarket_id")]
    if not cards:
        logger.info("No cards with CardMarket IDs to update.")
        return 0

    prices = {}
    for card in cards:
        try:
            prices[card["id"]] = api.get_prices(card["cardmarket_id"])
        except Exception as exc:
            logger.error("Price fetch failed for %s: %s", card["name"], exc)

    if prices:
        database.update_prices(prices)

    updated = len(prices)
    database.log_update(updated, "ok", f"Updated {updated}/{len(cards)} cards")
    logger.info("Price update done: %d/%d cards", updated, len(cards))
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
    logger.info("Scheduler started — prices update every %dh", config.UPDATE_INTERVAL_HOURS)
    return scheduler
