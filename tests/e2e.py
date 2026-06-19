"""End-to-end test for 용돈 기입장 (Day 38).

Covers the golden path: add transaction, list update, summary update, chart
render, JSON export. Captures screenshots and reports console errors.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, ConsoleMessage

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "tests" / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)

URL = os.environ.get("APP_URL", "http://127.0.0.1:5180/")

errors: list[str] = []
warnings: list[str] = []
page_errors: list[str] = []


def on_console(msg: ConsoleMessage) -> None:
    if msg.type == "error":
        errors.append(f"[console.error] {msg.text}")
    elif msg.type == "warning":
        warnings.append(f"[console.warn] {msg.text}")


def on_pageerror(exc) -> None:
    page_errors.append(f"[pageerror] {exc}")


def shot(page, name: str) -> None:
    page.screenshot(path=str(SCREENSHOTS / f"{name}.png"), full_page=True)


def main() -> int:
    failures: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        page.on("console", on_console)
        page.on("pageerror", on_pageerror)

        # Start with a clean storage by going to about:blank first
        page.goto(URL)
        page.wait_for_load_state("networkidle")
        page.evaluate("localStorage.clear()")
        page.reload()
        page.wait_for_load_state("networkidle")

        shot(page, "01-empty")

        # 1. Empty state visible
        empty_visible = page.locator("#empty-state").is_visible()
        if not empty_visible:
            failures.append("empty state should be visible on first load")

        # 2. Add an expense
        page.fill("#f-date", "2026-06-15")
        page.click('.toggle button[data-kind="expense"]')
        page.fill("#f-item", "떡볶이")
        page.fill("#f-amount", "3000")
        page.click('.cat-chip[data-cat="snack"]')
        page.click("#btn-add")
        page.wait_for_timeout(300)

        count_txt = page.locator("#list-count").inner_text()
        if "1건" not in count_txt:
            failures.append(f"after adding 1 txn, list count should show '1건' but got '{count_txt}'")

        expense_val = page.locator("#sum-expense").inner_text()
        if "3,000" not in expense_val:
            failures.append(f"expense summary should be 3,000원 but got '{expense_val}'")

        shot(page, "02-one-expense")

        # 3. Add income
        page.fill("#f-date", "2026-06-02")
        page.click('.toggle button[data-kind="income"]')
        page.fill("#f-item", "용돈")
        page.fill("#f-amount", "15000")
        page.click('.cat-chip[data-cat="saving"]')
        page.click("#btn-add")
        page.wait_for_timeout(300)

        income_val = page.locator("#sum-income").inner_text()
        if "15,000" not in income_val:
            failures.append(f"income should be 15,000원 but got '{income_val}'")

        balance_val = page.locator("#sum-balance").inner_text()
        if "12,000" not in balance_val:
            failures.append(f"balance should be 12,000원 but got '{balance_val}'")

        # 4. Add a few more expenses for chart variety
        for date, kind, item, amount, cat in [
            ("2026-06-08", "expense", "버스 충전",  5000, "transit"),
            ("2026-06-12", "expense", "선물",       4000, "gift"),
            ("2026-06-18", "expense", "노트",       2500, "school"),
        ]:
            page.fill("#f-date", date)
            page.click(f'.toggle button[data-kind="{kind}"]')
            page.fill("#f-item", item)
            page.fill("#f-amount", str(amount))
            page.click(f'.cat-chip[data-cat="{cat}"]')
            page.click("#btn-add")
            page.wait_for_timeout(150)

        shot(page, "03-multiple")

        # 5. Donut summary should mention top category
        donut_summary = page.locator("#donut-summary").inner_text()
        if not donut_summary or "1위" not in donut_summary:
            failures.append(f"donut summary text missing or wrong: '{donut_summary}'")

        # 6. Donut canvas rendered
        donut_canvas = page.locator("#donut-canvas")
        if donut_canvas.count() != 1:
            failures.append("donut canvas not present after adding expenses")

        # 7. Bar canvas rendered (non-empty pixels check)
        canvas_has_pixels = page.evaluate("""
            () => {
              const c = document.getElementById('bar-canvas');
              if(!c) return false;
              const ctx = c.getContext('2d');
              const d = ctx.getImageData(0,0,c.width,c.height).data;
              for(let i=3;i<d.length;i+=4){ if(d[i] !== 0) return true; }
              return false;
            }
        """)
        if not canvas_has_pixels:
            failures.append("bar canvas appears blank after rendering")

        # 8. Delete a transaction
        page.locator("[data-del]").first.click()
        page.wait_for_timeout(200)
        new_count = page.locator("#list-count").inner_text()
        if "4건" not in new_count:
            failures.append(f"after delete, list count should show '4건' but got '{new_count}'")

        shot(page, "04-after-delete")

        # 9. Month picker — switch to a month with no data
        page.select_option("#month-select", value="2026-06")
        page.wait_for_timeout(150)

        # 10. Persistence — reload
        page.reload()
        page.wait_for_load_state("networkidle")
        persisted = page.locator("#list-count").inner_text()
        if "4건" not in persisted:
            failures.append(f"data not persisted after reload — got '{persisted}'")

        shot(page, "05-after-reload")

        # 11. Form validation — try empty submit
        page.fill("#f-item", "")
        page.fill("#f-amount", "")
        page.click("#btn-add")
        err_msg = page.locator("#form-error").inner_text()
        if not err_msg:
            failures.append("form should show an error when submitting empty")

        # 12. Negative amount
        page.fill("#f-date", "2026-06-20")
        page.fill("#f-item", "테스트")
        page.fill("#f-amount", "-100")
        page.click("#btn-add")
        err_msg2 = page.locator("#form-error").inner_text()
        if "1원" not in err_msg2 and "이상" not in err_msg2:
            failures.append(f"form should reject negative amount, got '{err_msg2}'")

        # 13. JSON export
        with page.expect_download() as dl_info:
            page.click("#btn-export")
        download = dl_info.value
        export_path = SCREENSHOTS / "exported.json"
        download.save_as(str(export_path))
        try:
            data = json.loads(export_path.read_text(encoding="utf-8"))
            if not isinstance(data.get("txns"), list) or len(data["txns"]) != 4:
                failures.append(f"exported JSON should have 4 txns, got {len(data.get('txns', []))}")
        except Exception as e:
            failures.append(f"exported JSON unreadable: {e}")
        export_path.unlink(missing_ok=True)

        # 14. Clear all (cancel via accept=false)
        page.once("dialog", lambda d: d.dismiss())
        page.click("#btn-clear")
        page.wait_for_timeout(150)
        still = page.locator("#list-count").inner_text()
        if "4건" not in still:
            failures.append(f"cancel of clear should keep data — got '{still}'")

        # 15. Clear all (accept)
        page.once("dialog", lambda d: d.accept())
        page.click("#btn-clear")
        page.wait_for_timeout(200)
        zero = page.locator("#list-count").inner_text()
        if "0건" not in zero:
            failures.append(f"after clearing, count should be '0건' but got '{zero}'")

        shot(page, "06-final")

        browser.close()

    # Filter out noisy environment warnings (CDN cert, network)
    env_noise = ("cert", "tailwindcss.com", "favicon", "PWA")
    real_errors = [e for e in errors + page_errors if not any(n in e for n in env_noise)]

    print("\n=== TEST RESULT ===")
    print(f"failures: {len(failures)}")
    for f in failures:
        print(f"  FAIL: {f}")
    print(f"console errors: {len(real_errors)}")
    for e in real_errors:
        print(f"  {e}")
    print(f"console warnings: {len(warnings)} (informational)")

    ok = len(failures) == 0 and len(real_errors) == 0
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
