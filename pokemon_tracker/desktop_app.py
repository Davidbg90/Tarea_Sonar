import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
import database
import config

# ── colour palette ──────────────────────────────────────────────────────────
BG       = "#1e1e2e"
CARD_BG  = "#2a2a3e"
ACCENT   = "#a855f7"
TEXT     = "#e0e0e0"
SUBTEXT  = "#7070a0"
GREEN    = "#22c55e"
YELLOW   = "#eab308"

COLUMNS = [
    ("name",         "Nombre",       200, tk.W),
    ("set_name",     "Set",          120, tk.CENTER),
    ("card_number",  "Nº",            50, tk.CENTER),
    ("quantity",     "Cant.",          55, tk.CENTER),
    ("condition",    "Estado",         65, tk.CENTER),
    ("language",     "Idioma",         60, tk.CENTER),
    ("price_low",    "Mín. €",         75, tk.CENTER),
    ("price_trend",  "Trend €",        75, tk.CENTER),
    ("price_avg",    "Media €",        75, tk.CENTER),
    ("last_updated", "Actualizado",   135, tk.CENTER),
]


class PokemonTrackerApp(tk.Tk):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self.title("Pokemon Card Price Tracker")
        self.configure(bg=BG)
        self.geometry("1100x660")
        self.minsize(800, 500)

        self._apply_styles()
        self._build_ui()
        self.refresh_data()
        self._schedule_auto_refresh()

    # ── styling ──────────────────────────────────────────────────────────────

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview",
                        background=CARD_BG, foreground=TEXT,
                        fieldbackground=CARD_BG, rowheight=30,
                        font=("Helvetica", 10))
        style.configure("Treeview.Heading",
                        background=BG, foreground=ACCENT,
                        font=("Helvetica", 10, "bold"), relief=tk.FLAT)
        style.map("Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])
        style.configure("Vertical.TScrollbar", background=CARD_BG, troughcolor=BG)

    # ── widgets ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── header ──
        header = tk.Frame(self, bg=BG, pady=8)
        header.pack(fill=tk.X, padx=12)

        tk.Label(header, text="Pokemon Card Price Tracker",
                 font=("Helvetica", 16, "bold"),
                 bg=BG, fg=ACCENT).pack(side=tk.LEFT)

        btn_web = tk.Button(header, text="Gestionar coleccion",
                            bg=CARD_BG, fg=TEXT, relief=tk.FLAT,
                            font=("Helvetica", 10), padx=10, pady=4,
                            cursor="hand2", command=self._open_web)
        btn_web.pack(side=tk.RIGHT, padx=4)

        btn_refresh = tk.Button(header, text="Actualizar precios",
                                bg=ACCENT, fg="white", relief=tk.FLAT,
                                font=("Helvetica", 10), padx=10, pady=4,
                                cursor="hand2", command=self._update_prices_bg)
        btn_refresh.pack(side=tk.RIGHT, padx=4)

        # ── stats bar ──
        stats_bar = tk.Frame(self, bg=CARD_BG, pady=6)
        stats_bar.pack(fill=tk.X, padx=12, pady=(0, 6))

        self.lbl_cards = tk.Label(stats_bar, text="Cartas: 0",
                                  bg=CARD_BG, fg=TEXT,
                                  font=("Helvetica", 11), padx=16)
        self.lbl_cards.pack(side=tk.LEFT)

        self.lbl_qty = tk.Label(stats_bar, text="Piezas: 0",
                                bg=CARD_BG, fg=TEXT,
                                font=("Helvetica", 11), padx=16)
        self.lbl_qty.pack(side=tk.LEFT)

        self.lbl_value = tk.Label(stats_bar, text="Valor: €0.00",
                                  bg=CARD_BG, fg=GREEN,
                                  font=("Helvetica", 11, "bold"), padx=16)
        self.lbl_value.pack(side=tk.LEFT)

        # ── table ──
        table_frame = tk.Frame(self, bg=BG)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=12)

        self.tree = ttk.Treeview(
            table_frame,
            columns=[c[0] for c in COLUMNS],
            show="headings",
            selectmode="browse",
        )
        for col_id, col_name, width, anchor in COLUMNS:
            self.tree.heading(col_id, text=col_name)
            self.tree.column(col_id, width=width, anchor=anchor, stretch=(col_id == "name"))

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # ── status bar ──
        status_bar = tk.Frame(self, bg=CARD_BG, pady=4)
        status_bar.pack(fill=tk.X, padx=12, pady=(6, 10))

        self.lbl_status = tk.Label(status_bar, text="",
                                   bg=CARD_BG, fg=SUBTEXT,
                                   font=("Helvetica", 9), padx=12)
        self.lbl_status.pack(side=tk.LEFT)

        self.lbl_interval = tk.Label(status_bar,
                                     text=f"Actualizacion automatica cada {config.UPDATE_INTERVAL_HOURS}h",
                                     bg=CARD_BG, fg=SUBTEXT,
                                     font=("Helvetica", 9), padx=12)
        self.lbl_interval.pack(side=tk.RIGHT)

    # ── data refresh ─────────────────────────────────────────────────────────

    def refresh_data(self):
        cards = database.get_all_cards()
        stats = database.get_collection_stats()
        last = database.get_last_update()

        # stats bar
        self.lbl_cards.config(text=f"Cartas unicas: {stats.get('total_cards', 0)}")
        self.lbl_qty.config(text=f"Piezas: {stats.get('total_quantity', 0)}")
        value = stats.get("total_value") or 0.0
        self.lbl_value.config(text=f"Valor coleccion: €{value:.2f}")

        # table
        for item in self.tree.get_children():
            self.tree.delete(item)

        for card in cards:
            row = []
            for col_id, _, _, _ in COLUMNS:
                val = card.get(col_id)
                if col_id in ("price_low", "price_trend", "price_avg"):
                    val = f"€{val:.2f}" if val is not None else "—"
                elif val is None or val == "":
                    val = "—"
                row.append(val)
            self.tree.insert("", tk.END, values=row)

        # status
        if last:
            self.lbl_status.config(text=f"Ultima actualizacion: {last['updated_at']}")
        else:
            self.lbl_status.config(text="Sin actualizaciones aun")

    def _schedule_auto_refresh(self):
        """Refresh display every 60 seconds so it stays in sync with the DB."""
        self.refresh_data()
        self.after(60_000, self._schedule_auto_refresh)

    # ── actions ──────────────────────────────────────────────────────────────

    def _update_prices_bg(self):
        def run():
            from price_updater import update_all_prices
            self.lbl_status.config(text="Actualizando precios...", fg=YELLOW)
            updated = update_all_prices(self.api)
            self.lbl_status.config(
                text=f"Actualizadas {updated} cartas.", fg=GREEN)
            self.refresh_data()

        threading.Thread(target=run, daemon=True).start()

    def _open_web(self):
        webbrowser.open(f"http://localhost:{config.FLASK_PORT}")
