import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler
import database
import config

logger = logging.getLogger(__name__)

_CALL_DELAY = 0.3   # seconds between API calls
_RETRY_DELAY = 5    # seconds before retrying a failed card


def update_all_prices(api):
    cards = [c for c in database.get_all_cards() if c.get("pokemontcg_id")]
    if not cards:
        logger.info("No cards with pokemontcg_id to update.")
        database.log_update(0, "skipped", "No cards with ID")
        return 0

    prices = {}
    failed = []

    for card in cards:
        try:
            p = api.get_prices(card["pokemontcg_id"])
            prices[card["id"]] = p
            trend = p.get("price_trend")
            img = p.get("image_url", "")
            logger.info("  %-35s trend=%s  img=%s", card["name"],
                        f"€{trend:.2f}" if trend is not None else "null",
                        "ok" if img else "MISSING")
        except Exception as exc:
            logger.warning("Price fetch failed for %s (will retry): %s", card["name"], exc)
            failed.append(card)
        time.sleep(_CALL_DELAY)

    if failed:
        logger.info("Retrying %d failed cards after %ds...", len(failed), _RETRY_DELAY)
        time.sleep(_RETRY_DELAY)
        for card in failed:
            try:
                prices[card["id"]] = api.get_prices(card["pokemontcg_id"])
                logger.info("Retry succeeded for %s", card["name"])
            except Exception as exc:
                logger.error("Price fetch failed permanently for %s: %s", card["name"], exc)
            time.sleep(_CALL_DELAY)

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
