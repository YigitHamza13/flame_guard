"""Printable PDF mission report built from the same HTML the cargo page shows (no new claims, same wording)."""
from __future__ import annotations

import datetime as _dt
import html as _html
import re
from html.parser import HTMLParser
from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace

from src.i18n import t

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "static" / "fonts"
LOGO = ROOT / "assets" / "flameguard-icon.png"
# Plex has no geometric symbols; the words next to them carry the meaning, so plain marks are enough.
GLYPHS = {"▲": "(+)", "▼": "(–)", "◆": "(±)", "◌": "", "⚠": "!", "➜": "→"}
INK, MUTED, ACCENT, LINE = (24, 32, 44), (90, 102, 120), (214, 96, 40), (210, 216, 224)


def clean(text: str) -> str:
    for k, v in GLYPHS.items():
        text = text.replace(k, v)
    return re.sub(r"\s+", " ", text).strip()


class _Card(HTMLParser):
    """Pull title, badges, sentence and next-evidence line out of one plain-card."""

    def __init__(self):
        super().__init__()
        self.parts, self.cls, self.skip = [], [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "button":
            self.skip += 1
        self.cls.append(a.get("class", "") or tag)

    def handle_endtag(self, tag):
        if tag == "button":
            self.skip -= 1
        if self.cls:
            self.cls.pop()

    def handle_data(self, data):
        if self.skip or not data.strip():
            return
        kind = next((c for c in reversed(self.cls) if c.startswith("plain-")), "p")
        self.parts.append((kind, data))


def card_parts(card_html: str) -> dict:
    p = _Card()
    p.feed(card_html)
    out = {"title": "", "map": "", "sub": "", "badges": [], "text": "", "next": ""}
    for kind, data in p.parts:
        if kind == "plain-title":
            out["title"] += data + " "
        elif kind == "plain-map":
            out["map"] += data + " "
        elif kind == "plain-sub":
            out["sub"] += data + " "
        elif kind.startswith("plain-badge"):
            out["badges"].append(clean(data))
        elif kind == "plain-next":
            out["next"] += data + " "
        else:
            out["text"] += data + " "
    return {k: (clean(v) if isinstance(v, str) else v) for k, v in out.items()}


class _Table(HTMLParser):
    """Rows of cells; each cell is (text, [(label, href), ...])."""

    def __init__(self):
        super().__init__()
        self.rows, self.cell, self.href, self.in_cell = [], None, None, False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.rows.append([])
        elif tag in ("td", "th"):
            self.cell = ["", []]
        elif tag == "a":
            self.href = [dict(attrs).get("href", ""), ""]
        elif tag == "br" and self.cell is not None:
            self.cell[0] += "; "

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.rows[-1].append((clean(self.cell[0]).strip("; "), self.cell[1]))
            self.cell = None
        elif tag == "a" and self.href and self.cell is not None:
            self.cell[1].append((clean(self.href[1]), self.href[0]))
            self.href = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell[0] += data
            if self.href:
                self.href[1] += data


def table_rows(table_html: str) -> list:
    p = _Table()
    p.feed(table_html)
    return [r for r in p.rows if r]


class _PDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Plex", "", 7.5)
        self.set_text_color(*MUTED)
        self.cell(0, 5, clean(t("FLAMEGUARD · independent student project, not NASA-approved · not a safety rating")), align="L")
        self.cell(0, 5, f"{self.page_no()}/{{nb}}", align="R")


def build(env_label: str, assumptions: str, snapshot: str, cards: list, cargo_table: str, env_table: str) -> bytes:
    """cards: list of plain-card HTML strings; tables: the risk-table HTML shown on the page."""
    pdf = _PDF(orientation="P", unit="mm", format="A4")
    pdf.add_font("Plex", "", str(FONTS / "IBMPlexSans-Regular.ttf"))
    pdf.add_font("Plex", "B", str(FONTS / "IBMPlexSans-SemiBold.ttf"))
    pdf.set_auto_page_break(True, margin=16)
    pdf.set_margins(16, 14, 16)
    pdf.alias_nb_pages()
    pdf.set_title("FLAMEGUARD cargo evidence report")
    pdf.set_author("FLAMEGUARD (BeatlessFlame)")
    pdf.set_lang("tr" if t("Read aloud") == "Sesli oku" else "en")
    pdf.add_page()
    w = pdf.epw

    if LOGO.exists():
        pdf.image(str(LOGO), x=16, y=13, h=16)
    pdf.set_xy(36, 14)
    pdf.set_font("Plex", "B", 17)
    pdf.set_text_color(*INK)
    pdf.cell(0, 8, clean(t("Cargo evidence report")), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(36)
    pdf.set_font("Plex", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 5, clean(t("What NASA's space fire tests found for your cargo, with report pages.")), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_fill_color(255, 241, 230)
    pdf.set_draw_color(*ACCENT)
    pdf.set_text_color(*INK)
    pdf.set_font("Plex", "", 9)
    meta = [(t("Environment"), env_label), (t("Assumptions"), assumptions),
            (t("Date"), _dt.date.today().isoformat()), (t("Data snapshot (SHA-256)"), snapshot[:16] + "…")]
    for k, v in meta:
        pdf.set_font("Plex", "B", 9)
        pdf.cell(48, 5.5, clean(k))
        pdf.set_font("Plex", "", 9)
        pdf.multi_cell(w - 48, 5.5, clean(str(v)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Plex", "B", 9)
    pdf.multi_cell(w, 5, clean(t("This report lists evidence, not a risk score. Missing data does not mean safe. Each result describes the closest NASA-tested specimen, not your exact product.")),
                   border="L", fill=True, padding=(2, 3), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Plex", "B", 12.5)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 7, clean(t("What NASA found, in one sentence per item")), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    for card_html in cards:
        c = card_parts(card_html)
        if pdf.will_page_break(30):
            pdf.add_page()
        y0 = pdf.get_y()
        pdf.set_x(19)
        pdf.set_text_color(*INK)
        pdf.set_font("Plex", "B", 10.5)
        pdf.multi_cell(w - 3, 5.5, c["title"] + (f"  {c['map']}" if c["map"] else ""), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*MUTED)
        pdf.set_font("Plex", "", 8.5)
        line = " · ".join(x for x in [c["sub"], *c["badges"]] if x)
        if line:
            pdf.set_x(19)
            pdf.multi_cell(w - 3, 4.6, line, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)
        pdf.set_font("Plex", "", 9.5)
        pdf.set_x(19)
        pdf.multi_cell(w - 3, 5, c["text"], new_x="LMARGIN", new_y="NEXT")
        if c["next"]:
            pdf.set_text_color(*ACCENT)
            pdf.set_font("Plex", "B", 8.8)
            pdf.set_x(19)
            pdf.multi_cell(w - 3, 4.8, c["next"].replace("→", "→ ", 1), new_x="LMARGIN", new_y="NEXT")
        y1 = pdf.get_y()
        pdf.set_draw_color(*ACCENT)
        pdf.set_line_width(0.8)
        pdf.line(16.4, y0 + 0.5, 16.4, y1 - 0.5)
        pdf.set_line_width(0.2)
        pdf.ln(3)

    def table(title: str, rows: list, widths: list, size=7.6):
        if not rows:
            return
        if pdf.will_page_break(40):
            pdf.add_page()
        pdf.ln(2)
        pdf.set_font("Plex", "B", 12.5)
        pdf.set_text_color(*ACCENT)
        pdf.cell(0, 7, clean(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Plex", "", size)
        pdf.set_text_color(*INK)
        pdf.set_draw_color(*LINE)
        cols = [w * x / sum(widths) for x in widths]
        head, body = rows[0], rows[1:]
        with pdf.table(col_widths=cols, line_height=size * 0.55, text_align="LEFT", borders_layout="HORIZONTAL_LINES",
                       headings_style=FontFace(emphasis="BOLD", color=INK, fill_color=(255, 241, 230)), first_row_as_headings=True, repeat_headings=1) as tb:
            hr = tb.row()
            for text, _ in head:
                hr.cell(text)
            for r in body:
                row = tb.row()
                for i, (text, links) in enumerate(r):
                    if links and i == len(r) - 1:
                        row.cell(", ".join(lbl for lbl, _ in links), link=links[0][1])
                    else:
                        row.cell(text, colspan=(len(head) - 1) if len(r) == 2 and i == 1 else 1)
        links = [(lbl, u) for r in body for _t, ls in r for lbl, u in ls]
        if links:
            pdf.ln(1.5)
            pdf.set_font("Plex", "", 7)
            pdf.set_text_color(*MUTED)
            for lbl, u in dict.fromkeys(links):
                pdf.multi_cell(w, 3.8, f"{lbl}: {u}", link=u, new_x="LMARGIN", new_y="NEXT")

    table(t("Risk factor table · your cargo"), table_rows(cargo_table), [10, 13, 12, 10, 10, 10, 7, 12, 13, 9])
    table(t("Risk factors in the cabin environment"), table_rows(env_table), [12, 36, 30, 16], size=8)

    pdf.ln(3)
    pdf.set_font("Plex", "", 8)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(w, 4.4, clean(t("Sources: NASA Technical Reports Server documents, each value checked on the cited PDF page. Generated by FLAMEGUARD.")))
    return bytes(pdf.output())


def esc(text: str) -> str:
    return _html.escape(text)
