from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import database
import config


def create_app(api):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = config.FLASK_SECRET_KEY

    # ------------------------------------------------------------------ #
    #  Collection overview
    # ------------------------------------------------------------------ #

    @app.route("/")
    def index():
        cards = database.get_all_cards()
        stats = database.get_collection_stats()
        last_update = database.get_last_update()
        return render_template(
            "collection.html",
            cards=cards,
            stats=stats,
            last_update=last_update,
            api_configured=api.is_configured,
            update_hours=config.UPDATE_INTERVAL_HOURS,
        )

    # ------------------------------------------------------------------ #
    #  Add card
    # ------------------------------------------------------------------ #

    @app.route("/add")
    def add_card():
        return render_template("add_card.html")

    @app.route("/search", methods=["POST"])
    def search():
        name = request.form.get("name", "").strip()
        if not name:
            flash("Introduce el nombre de la carta.", "warning")
            return redirect(url_for("add_card"))

        if not api.is_configured:
            flash("API de CardMarket no configurada. Edita el archivo .env con tus credenciales.", "danger")
            return redirect(url_for("add_card"))

        try:
            products = api.search_products(name)
            return render_template("search_results.html", products=products, query=name)
        except Exception as exc:
            flash(f"Error al buscar en CardMarket: {exc}", "danger")
            return redirect(url_for("add_card"))

    @app.route("/add_from_search", methods=["POST"])
    def add_from_search():
        database.add_card(
            name=request.form.get("name", ""),
            set_name=request.form.get("set_name", ""),
            quantity=request.form.get("quantity", 1, type=int),
            condition=request.form.get("condition", "NM"),
            language=request.form.get("language", "ES"),
            foil=request.form.get("foil") == "true",
            cardmarket_id=request.form.get("cardmarket_id", type=int),
            image_url=request.form.get("image_url", ""),
        )
        flash(f"'{request.form.get('name')}' añadida a la colección.", "success")
        return redirect(url_for("index"))

    @app.route("/add_manual", methods=["POST"])
    def add_manual():
        name = request.form.get("name", "").strip()
        if not name:
            flash("El nombre es obligatorio.", "warning")
            return redirect(url_for("add_card"))

        database.add_card(
            name=name,
            set_name=request.form.get("set_name", ""),
            card_number=request.form.get("card_number", ""),
            quantity=request.form.get("quantity", 1, type=int),
            condition=request.form.get("condition", "NM"),
            language=request.form.get("language", "ES"),
            foil=request.form.get("foil") == "on",
        )
        flash(f"'{name}' añadida manualmente.", "success")
        return redirect(url_for("index"))

    # ------------------------------------------------------------------ #
    #  Edit / delete
    # ------------------------------------------------------------------ #

    @app.route("/edit/<int:card_id>", methods=["GET", "POST"])
    def edit_card(card_id):
        card = database.get_card(card_id)
        if not card:
            flash("Carta no encontrada.", "danger")
            return redirect(url_for("index"))

        if request.method == "POST":
            database.update_card(
                card_id,
                name=request.form.get("name"),
                set_name=request.form.get("set_name", ""),
                card_number=request.form.get("card_number", ""),
                quantity=request.form.get("quantity", 1, type=int),
                condition=request.form.get("condition", "NM"),
                language=request.form.get("language", "ES"),
                foil=int(request.form.get("foil") == "on"),
            )
            flash("Carta actualizada.", "success")
            return redirect(url_for("index"))

        return render_template("edit_card.html", card=card)

    @app.route("/delete/<int:card_id>", methods=["POST"])
    def delete_card(card_id):
        card = database.get_card(card_id)
        if card:
            database.delete_card(card_id)
            flash(f"'{card['name']}' eliminada.", "info")
        return redirect(url_for("index"))

    # ------------------------------------------------------------------ #
    #  Price update (manual trigger)
    # ------------------------------------------------------------------ #

    @app.route("/update_prices", methods=["POST"])
    def trigger_update():
        from price_updater import update_all_prices
        updated = update_all_prices(api)
        flash(f"Precios actualizados: {updated} cartas.", "success")
        return redirect(url_for("index"))

    # ------------------------------------------------------------------ #
    #  JSON API (used by desktop app for live refresh)
    # ------------------------------------------------------------------ #

    @app.route("/api/cards")
    def api_cards():
        return jsonify(database.get_all_cards())

    @app.route("/api/stats")
    def api_stats():
        return jsonify(database.get_collection_stats())

    return app
