"""Render an HTML/SVG diagram to a tightly cropped vector PDF and a 300-dpi PNG with headless Edge/Chrome.

    python tools/render_html.py paper/diagrams/fig_architecture.html          -> paper/figures/fig_architecture.{pdf,png}
    python tools/render_html.py paper/diagrams/*.html

The page must contain one element with id="fig" whose box is the figure. Diagrams are authored at the printed size
in CSS pixels (96 px = 1 in; full text width = 520 px, full text height = 730 px) so that 1 CSS px of text = 0.75 pt in print.
Requires `pip install playwright` and an installed Microsoft Edge or Google Chrome (no browser download).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper/figures"


def render(paths, out=OUT, scale=300 / 96):
    from playwright.sync_api import sync_playwright
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = None
        for ch in ("msedge", "chrome"):
            try:
                browser = p.chromium.launch(channel=ch)
                break
            except Exception:  # noqa: BLE001
                continue
        if browser is None:
            browser = p.chromium.launch()
        ctx = browser.new_context(device_scale_factor=scale, viewport={"width": 1400, "height": 1000})
        page = ctx.new_page()
        for path in paths:
            path = Path(path).resolve()
            page.goto(path.as_uri())
            page.wait_for_load_state("networkidle")
            page.evaluate("document.fonts.ready")
            if page.evaluate("typeof window.figReady !== 'undefined'"):
                page.wait_for_function("window.figReady === true", timeout=20000)
            el = page.locator("#fig")
            box = el.bounding_box()
            name = path.stem
            el.screenshot(path=str(out / f"{name}.png"), omit_background=False)
            w, h = box["width"], box["height"]
            page.add_style_tag(content=f"@page {{ size: {w + 0.5}px {h + 0.5}px; margin: 0 }} "
                                       "html, body { margin:0 !important; padding:0 !important; }"
                                       "#fig { position: absolute !important; left: 0 !important; top: 0 !important;"
                                       " margin: 0 !important; }")
            page.pdf(path=str(out / f"{name}.pdf"), width=f"{w + 0.5}px", height=f"{h + 0.5}px",
                     print_background=True, page_ranges="1")
            print(f"figure {name}  {w / 96:.2f} x {h / 96:.2f} in")
        browser.close()


if __name__ == "__main__":
    args = sys.argv[1:] or sorted(str(p) for p in (ROOT / "paper/diagrams").glob("*.html"))
    render(args)
