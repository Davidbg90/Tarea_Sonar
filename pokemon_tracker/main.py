#!/usr/bin/env python3
import sys
import threading
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import database
import config
from pokemon_tcg_api import PokemonTCGAPI
from price_updater import start_scheduler, update_all_prices
from web_app import create_app
from desktop_app import PokemonTrackerApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    database.init_db()

    api = PokemonTCGAPI()

    flask_app = create_app(api)
    threading.Thread(
        target=flask_app.run,
        kwargs={"host": config.FLASK_HOST, "port": config.FLASK_PORT,
                "use_reloader": False, "threaded": True},
        daemon=True, name="flask",
    ).start()
    logging.info("Web interface → http://localhost:%d", config.FLASK_PORT)

    scheduler = start_scheduler(api)

    threading.Thread(
        target=update_all_prices, args=[api],
        daemon=True, name="initial-update"
    ).start()

    app = PokemonTrackerApp(api)
    try:
        app.mainloop()
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
