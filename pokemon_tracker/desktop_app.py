import tkinter as tk
from tkinter import ttk
import threading
import webbrowser
import hashlib
from io import BytesIO

import requests
import database
import config

BG      = "#1e1e2e"
CARD_BG = "#2a2a3e"
ACCENT  = "#a855f7"
TEXT    = "#e0e0e0"
SUBTEXT = "#7070a0"
GREEN   = "#22c55e"
YELLOW  = "#eab308"

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL_AVAILABLE = True
except ImportError:
    MPL_AVAILABLE = False

_img_mem = {}  # keep refs to prevent GC

COLUMNS = [
    ("name",        "Nombre",      200, tk.W),
    ("set_name",    "Set",         120, tk.CENTER),
    ("card_number", "Nº",           50, tk.CENTER),
    ("quantity",    "Cant.",         55, tk.CENTER),
    ("condition",   "Estado",        65, tk.CENTER),
    ("price_trend", "Trend €",       80, tk.CENTER),
    ("price_avg7",  "7d €",          72, tk.CENTER),
    ("price_avg30", "30d €",         72, tk.CENTER),
    ("last_updated","Actualizado",  130, tk.CENTER),
]


def _fetch_image(url, size):
    if not url or not PIL_AVAILABLE:
        return None
    key = (url, size)
    if key in _img_mem:
        return _img_mem[key]
    cache_dir = config.IMG_CACHE_DIR
    cache_dir.mkdir(exist_ok=True)
    fname = hashlib.md5(url.encode()).hexdigest() + ".png"
    path = cache_dir / fname
    try:
        if path.exists():
            img = Image.open(path).convert("RGBA")
        else:
            r = requests.get(url, timeout=10)
            img = Image.open(BytesIO(r.content)).convert("RGBA")
            img.save(path)
        img.thumbnail(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        _img_mem[key] = photo
        return photo
    except Exception:
        return None


class DetailPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CARD_BG, width=270)
        self.pack_propagate(False)
        self._photo = None
        self._build()

    def _build(self):
        # Image placeholder
        self.img_lbl = tk.Label(self, bg=CARD_BG, text="Selecciona\nuna carta",
                                 fg=SUBTEXT, font=("Helvetica", 10), height=10)
        self.img_lbl.pack(pady=(10, 4))

        self.lbl_name = tk.Label(self, bg=CARD_BG, fg=ACCENT,
                                  font=("Helvetica", 11, "bold"),
                                  wraplength=240, justify=tk.CENTER)
        self.lbl_name.pack(padx=8)

        self.lbl_meta = tk.Label(self, bg=CARD_BG, fg=SUBTEXT, font=("Helvetica", 9))
        self.lbl_meta.pack()

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10, pady=6)

        prices_f = tk.Frame(self, bg=CARD_BG)
        prices_f.pack(fill=tk.X, padx=12)
        self._price_lbls = {}
        for key, label, color in [
            ("price_low",   "Mínimo",      TEXT),
            ("price_trend", "Trend",       GREEN),
            ("price_avg",   "Media venta", TEXT),
        ]:
            row = tk.Frame(prices_f, bg=CARD_BG)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, bg=CARD_BG, fg=SUBTEXT,
                     font=("Helvetica", 9), width=12, anchor=tk.W).pack(side=tk.LEFT)
            v = tk.Label(row, text="—", bg=CARD_BG, fg=color,
                          font=("Helvetica", 10, "bold"))
            v.pack(side=tk.RIGHT)
            self._price_lbls[key] = v

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10, pady=6)

        tk.Label(self, text="Promedios CardMarket",
                  bg=CARD_BG, fg=SUBTEXT, font=("Helvetica", 8, "bold")).pack(padx=12, anchor=tk.W)

        avg_f = tk.Frame(self, bg=CARD_BG)
        avg_f.pack(fill=tk.X, padx=12, pady=(2, 0))
        self._avg_lbls = {}
        for key, label in [("price_avg1", "Ayer"), ("price_avg7", "7 días"), ("price_avg30", "30 días")]:
            row = tk.Frame(avg_f, bg=CARD_BG)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, bg=CARD_BG, fg=SUBTEXT,
                     font=("Helvetica", 9), width=12, anchor=tk.W).pack(side=tk.LEFT)
            v = tk.Label(row, text="—", bg=CARD_BG, fg=TEXT, font=("Helvetica", 9))
            v.pack(side=tk.RIGHT)
            self._avg_lbls[key] = v

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10, pady=6)

        tk.Label(self, text="Historial guardado",
                  bg=CARD_BG, fg=SUBTEXT, font=("Helvetica", 8, "bold")).pack(padx=12, anchor=tk.W)

        self.chart_f = tk.Frame(self, bg=CARD_BG)
        self.chart_f.pack(fill=tk.BOTH, expand=True, padx=6, pady=(2, 8))

    def show(self, card):
        self.lbl_name.config(text=card.get("name", ""))
        meta = card.get("set_name", "")
        if card.get("card_number"):
            meta += f"  ·  {card['card_number']}"
        self.lbl_meta.config(text=meta)

        for key, lbl in self._price_lbls.items():
            v = card.get(key)
            lbl.config(text=f"€{v:.2f}" if v is not None else "—")

        for key, lbl in self._avg_lbls.items():
            v = card.get(key)
            lbl.config(text=f"€{v:.2f}" if v is not None else "—")

        # Image async
        url = card.get("image_url_large") or card.get("image_url", "")
        self.img_lbl.config(text="Cargando...", image="")
        self._photo = None
        threading.Thread(target=self._load_img, args=(url,), daemon=True).start()

        # Chart
        history = database.get_price_history(card["id"])
        self._render_chart(history, card)

    def _load_img(self, url):
        photo = _fetch_image(url, (200, 280))
        def _apply():
            if photo:
                self._photo = photo
                self.img_lbl.config(image=photo, text="")
            else:
                self.img_lbl.config(text="Sin imagen", image="")
        self.img_lbl.after(0, _apply)

    def _render_chart(self, history, card):
        for w in self.chart_f.winfo_children():
            w.destroy()

        if MPL_AVAILABLE:
            # Prefer real history, fall back to avg1/avg7/avg30
            if history and len(history) >= 2:
                entries = list(reversed(history))
                xs = list(range(len(entries)))
                ys = [e.get("price_trend") or e.get("price_avg") or 0 for e in entries]
                labels = [e["recorded_at"][:10] for e in entries]
                self._draw_line(xs, ys, labels)
            else:
                pairs = [
                    ("30d", card.get("price_avg30")),
                    ("7d",  card.get("price_avg7")),
                    ("Ayer", card.get("price_avg1")),
                    ("Hoy", card.get("price_trend")),
                ]
                pairs = [(l, v) for l, v in pairs if v is not None]
                if pairs:
                    ls, vs = zip(*pairs)
                    self._draw_bar(list(ls), list(vs))
                else:
                    self._no_data()
        else:
            if history:
                for e in history[:6]:
                    v = e.get("price_trend") or e.get("price_avg")
                    text = f"{e['recorded_at'][:10]}: {'€'+f'{v:.2f}' if v else '—'}"
                    tk.Label(self.chart_f, text=text, bg=CARD_BG, fg=TEXT,
                              font=("Courier", 8)).pack(anchor=tk.W)
            else:
                self._no_data()

    def _draw_line(self, xs, ys, labels):
        fig = Figure(figsize=(2.6, 1.7), facecolor=CARD_BG, dpi=80)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CARD_BG)
        ax.plot(xs, ys, color=ACCENT, linewidth=1.5, marker="o", markersize=3)
        ax.set_xticks([])
        ax.tick_params(colors=SUBTEXT, labelsize=7)
        for spine in ax.spines.values():
            spine.set_color("#3a3a5a")
        ax.yaxis.set_tick_params(labelcolor=SUBTEXT)
        ax.set_ylabel("€", color=SUBTEXT, fontsize=8)
        fig.tight_layout(pad=0.4)
        c = FigureCanvasTkAgg(fig, master=self.chart_f)
        c.draw()
        c.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _draw_bar(self, labels, values):
        fig = Figure(figsize=(2.6, 1.7), facecolor=CARD_BG, dpi=80)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CARD_BG)
        bars = ax.bar(labels, values, color=ACCENT, alpha=0.8)
        ax.tick_params(colors=SUBTEXT, labelsize=7)
        for spine in ax.spines.values():
            spine.set_color("#3a3a5a")
        ax.yaxis.set_tick_params(labelcolor=SUBTEXT)
        ax.set_ylabel("€", color=SUBTEXT, fontsize=8)
        fig.tight_layout(pad=0.4)
        c = FigureCanvasTkAgg(fig, master=self.chart_f)
        c.draw()
        c.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _no_data(self):
        tk.Label(self.chart_f,
                  text="Sin historial aún.\nSe acumula en\ncada actualización.",
                  bg=CARD_BG, fg=SUBTEXT, font=("Helvetica", 8),
                  justify=tk.CENTER).pack(expand=True)


class PokemonTrackerApp(tk.Tk):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self._cards = []
        self.title("Pokemon Card Price Tracker")
        self.configure(bg=BG)
        self.geometry("1200x700")
        self.minsize(900, 520)
        self._apply_styles()
        self._build_ui()
        self.refresh_data()
        self._schedule_auto_refresh()

    def _apply_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", background=CARD_BG, foreground=TEXT,
                    fieldbackground=CARD_BG, rowheight=28, font=("Helvetica", 10))
        s.configure("Treeview.Heading", background=BG, foreground=ACCENT,
                    font=("Helvetica", 10, "bold"), relief=tk.FLAT)
        s.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", "white")])

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=8)
        hdr.pack(fill=tk.X, padx=12)
        tk.Label(hdr, text="Pokemon Card Price Tracker",
                  font=("Helvetica", 16, "bold"), bg=BG, fg=ACCENT).pack(side=tk.LEFT)
        tk.Button(hdr, text="Gestionar coleccion", bg=CARD_BG, fg=TEXT,
                   relief=tk.FLAT, font=("Helvetica", 10), padx=10, pady=4,
                   cursor="hand2", command=self._open_web).pack(side=tk.RIGHT, padx=4)
        tk.Button(hdr, text="Actualizar precios", bg=ACCENT, fg="white",
                   relief=tk.FLAT, font=("Helvetica", 10), padx=10, pady=4,
                   cursor="hand2", command=self._update_prices_bg).pack(side=tk.RIGHT, padx=4)

        # Stats bar
        stats = tk.Frame(self, bg=CARD_BG, pady=6)
        stats.pack(fill=tk.X, padx=12, pady=(0, 4))
        self.lbl_cards  = tk.Label(stats, text="Cartas: 0", bg=CARD_BG, fg=TEXT,
                                    font=("Helvetica", 11), padx=16)
        self.lbl_cards.pack(side=tk.LEFT)
        self.lbl_qty    = tk.Label(stats, text="Piezas: 0", bg=CARD_BG, fg=TEXT,
                                    font=("Helvetica", 11), padx=16)
        self.lbl_qty.pack(side=tk.LEFT)
        self.lbl_value  = tk.Label(stats, text="Valor: €0.00", bg=CARD_BG, fg=GREEN,
                                    font=("Helvetica", 11, "bold"), padx=16)
        self.lbl_value.pack(side=tk.LEFT)

        # Main pane
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

        # Table
        table_f = tk.Frame(paned, bg=BG)
        self.tree = ttk.Treeview(table_f, columns=[c[0] for c in COLUMNS],
                                  show="headings", selectmode="browse")
        for col_id, col_name, width, anchor in COLUMNS:
            self.tree.heading(col_id, text=col_name)
            self.tree.column(col_id, width=width, anchor=anchor,
                             stretch=(col_id == "name"))
        vsb = ttk.Scrollbar(table_f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        paned.add(table_f, weight=3)

        # Detail panel
        self.detail = DetailPanel(paned)
        paned.add(self.detail, weight=1)

        # Status bar
        sb = tk.Frame(self, bg=CARD_BG, pady=4)
        sb.pack(fill=tk.X, padx=12, pady=(0, 8))
        self.lbl_status = tk.Label(sb, text="", bg=CARD_BG, fg=SUBTEXT,
                                    font=("Helvetica", 9), padx=12)
        self.lbl_status.pack(side=tk.LEFT)
        tk.Label(sb, text=f"Actualizacion automatica cada {config.UPDATE_INTERVAL_HOURS}h",
                  bg=CARD_BG, fg=SUBTEXT, font=("Helvetica", 9), padx=12).pack(side=tk.RIGHT)

    def refresh_data(self):
        self._cards = database.get_all_cards()
        stats = database.get_collection_stats()
        last  = database.get_last_update()

        self.lbl_cards.config(text=f"Cartas unicas: {stats.get('total_cards', 0)}")
        self.lbl_qty.config(text=f"Piezas: {stats.get('total_quantity', 0)}")
        value = stats.get("total_value") or 0.0
        self.lbl_value.config(text=f"Valor coleccion: €{value:.2f}")

        sel_id = None
        sel = self.tree.selection()
        if sel:
            idx = self.tree.index(sel[0])
            if idx < len(self._cards):
                sel_id = self._cards[idx]["id"]

        for item in self.tree.get_children():
            self.tree.delete(item)

        new_sel = None
        for card in self._cards:
            row = []
            for col_id, _, _, _ in COLUMNS:
                v = card.get(col_id)
                if col_id in ("price_trend", "price_avg7", "price_avg30"):
                    v = f"€{v:.2f}" if v is not None else "—"
                elif v is None or v == "":
                    v = "—"
                row.append(v)
            iid = self.tree.insert("", tk.END, values=row)
            if card["id"] == sel_id:
                new_sel = iid

        if new_sel:
            self.tree.selection_set(new_sel)

        if last:
            self.lbl_status.config(text=f"Ultima actualizacion: {last['updated_at']}")
        else:
            self.lbl_status.config(text="Sin actualizaciones aun")

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if idx < len(self._cards):
            self.detail.show(self._cards[idx])

    def _schedule_auto_refresh(self):
        self.refresh_data()
        self.after(60_000, self._schedule_auto_refresh)

    def _update_prices_bg(self):
        def run():
            from price_updater import update_all_prices
            self.lbl_status.config(text="Actualizando precios...", fg=YELLOW)
            updated = update_all_prices(self.api)
            self.lbl_status.config(text=f"Actualizadas {updated} cartas.", fg=GREEN)
            self.refresh_data()
        threading.Thread(target=run, daemon=True).start()

    def _open_web(self):
        webbrowser.open(f"http://localhost:{config.FLASK_PORT}")
