from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import database
import config


def create_app(api):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = config.FLASK_SECRET_KEY

    @app.route("/")
    def index():
        cards = database.get_all_cards()
        stats = database.get_collection_stats()
        last_update = database.get_last_update()
        return render_template("collection.html", cards=cards, stats=stats,
                               last_update=last_update,
                               update_hours=config.UPDATE_INTERVAL_HOURS)

    @app.route("/card/<int:card_id>")
    def card_detail(card_id):
        card = database.get_card(card_id)
        if not card:
            flash("Carta no encontrada.", "danger")
            return redirect(url_for("index"))
        history = database.get_price_history(card_id)
        return render_template("card_detail.html", card=card, history=history)

    @app.route("/api/price_history/<int:card_id>")
    def api_price_history(card_id):
        history = database.get_price_history(card_id)
        return jsonify(list(reversed(history)))

    @app.route("/add")
    def add_card():
        return render_template("add_card.html")

    @app.route("/search", methods=["POST"])
    def search():
        name = request.form.get("name", "").strip()
        if not name:
            flash("Introduce el nombre de la carta.", "warning")
            return redirect(url_for("add_card"))
        try:
            cards = api.search_cards(name)
            return render_template("search_results.html", cards=cards, query=name)
        except Exception as exc:
            flash(f"Error al buscar: {exc}", "danger")
            return redirect(url_for("add_card"))

    @app.route("/add_from_search", methods=["POST"])
    def add_from_search():
        database.add_card(
            name=request.form.get("name", ""),
            set_name=request.form.get("set_name", ""),
            card_number=request.form.get("card_number", ""),
            quantity=request.form.get("quantity", 1, type=int),
            condition=request.form.get("condition", "NM"),
            language=request.form.get("language", "ES"),
            foil=request.form.get("foil") == "true",
            pokemontcg_id=request.form.get("pokemontcg_id", ""),
            image_url=request.form.get("image_url", ""),
            image_url_large=request.form.get("image_url_large", ""),
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

    @app.route("/update_prices", methods=["POST"])
    def trigger_update():
        from price_updater import update_all_prices
        updated = update_all_prices(api)
        flash(f"Precios actualizados: {updated} cartas.", "success")
        return redirect(url_for("index"))

    @app.route("/api/cards")
    def api_cards():
        return jsonify(database.get_all_cards())

    @app.route("/api/debug/card/<int:card_id>")
    def debug_card(card_id):
        card = database.get_card(card_id)
        if not card:
            return jsonify({"error": "card not found"}), 404
        if not card.get("pokemontcg_id"):
            return jsonify({"error": "no pokemontcg_id", "card": dict(card)})
        try:
            raw = api.get_card(card["pokemontcg_id"])
        except Exception as exc:
            return jsonify({"error": str(exc)})
        return jsonify({
            "pokemontcg_id": card["pokemontcg_id"],
            "api_set": raw.get("set", {}).get("name"),
            "api_cardmarket": raw.get("cardmarket"),
            "db_prices": {k: card[k] for k in
                          ("price_low", "price_trend", "price_avg",
                           "price_avg1", "price_avg7", "price_avg30", "last_updated")},
        })

    return app
