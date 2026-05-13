#!/usr/bin/env python3
"""
Pokemon Card Price Tracker
Entry point: starts the Flask web server in a background thread,
then runs the Tkinter desktop app on the main thread.
"""
import sys
import threading
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import database
import config
from cardmarket_api import CardMarketAPI
from price_updater import start_scheduler, update_all_prices
from web_app import create_app
from desktop_app import PokemonTrackerApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    database.init_db()

    api = CardMarketAPI()
    if not api.is_configured:
        logging.warning(
            "CardMarket API not configured. "
            "Edit pokemon_tracker/.env with your credentials."
        )

    # Flask web interface (background thread)
    flask_app = create_app(api)
    threading.Thread(
        target=flask_app.run,
        kwargs={
            "host": config.FLASK_HOST,
            "port": config.FLASK_PORT,
            "use_reloader": False,
            "threaded": True,
        },
        daemon=True,
        name="flask",
    ).start()
    logging.info("Web interface → http://localhost:%d", config.FLASK_PORT)

    # Background price scheduler
    scheduler = start_scheduler(api)

    # Run one price update immediately on startup (non-blocking)
    if api.is_configured:
        threading.Thread(
            target=update_all_prices, args=[api],
            daemon=True, name="initial-update"
        ).start()

    # Tkinter app — must run on main thread
    app = PokemonTrackerApp(api)
    try:
        app.mainloop()
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
