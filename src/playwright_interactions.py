from playwright.sync_api import sync_playwright
import json
import sys
from urllib.parse import urljoin, urlparse

# ==========================
# CONFIG
# ==========================

POPUP_SELECTOR = (
    "[role='dialog']:visible, "
    "[aria-modal='true']:visible, "
    ".modal:visible, "
    ".popup:visible, "
    ".popup-box:visible, "
    ".overlay:visible, "
    "[class*='modal']:visible, "
    "[class*='popup']:visible, "
    "[id*='interstitial']:visible, "
    "#third_party_interstitial_h1:visible"
)

INTERACTIVE_SELECTOR = (
    "a:visible, "
    "button:visible, "
    "[role='button']:visible, "
    "input[type='button']:visible"
)

HOVER_TRIGGER_SELECTOR = (
    "nav a:visible, nav button:visible, "
    "header a:visible, header button:visible"
)

MAX_CLICKABLES = 120  # safety cap


# ==========================
# UTILITIES
# ==========================

def safe_print(msg: str) -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "ignore").decode("ascii"))


def normalize_href(base_url: str, href: str | None) -> str | None:
    if not href:
        return None
    href = href.strip()
    if not href or href.startswith("#") or href.lower().startswith("javascript:"):
        return None
    return urljoin(base_url, href)


def safe_text(el, max_len: int = 200) -> str | None:
    """
    Extract text safely from dynamic elements without throwing.
    All timeouts/exceptions are swallowed here.
    """
    for method in [
        lambda e: e.inner_text(timeout=300),
        lambda e: e.text_content(timeout=300),
        lambda e: e.get_attribute("aria-label"),
        lambda e: e.get_attribute("title"),
        lambda e: e.get_attribute("value"),
        lambda e: e.get_attribute("href"),
        lambda e: e.get_attribute("id"),
    ]:
        try:
            txt = method(el)
            if txt:
                txt = " ".join(txt.split())
                if 0 < len(txt) <= max_len:
                    return txt
        except Exception:
            continue
    return None


def auto_accept_cookies(page):
    """Try to dismiss cookie banners so they don't block clicks."""
    cand_names = [
        "Accept All Cookies",
        "Accept all",
        "Accept",
        "Confirm My Choices",
        "Agree",
        "Got it",
    ]
    for name in cand_names:
        try:
            btn = page.get_by_role("button", name=name)
            if btn.count() > 0:
                btn.first.click(timeout=1000)
                page.wait_for_timeout(500)
                safe_print(f"[cookie] Clicked '{name}'")
                return
        except Exception:
            continue
    # Some cookie UIs use generic classes / aria labels
    try:
        candidate = page.locator("button.cookie, button[aria-label*='cookie']")
        if candidate.count() > 0:
            candidate.first.click(timeout=1000)
            page.wait_for_timeout(500)
            safe_print("[cookie] Clicked generic cookie button")
    except Exception:
        pass


def get_scroll_y(page) -> int:
    try:
        val = page.evaluate("() => window.scrollY") or 0
        return int(val)
    except Exception:
        return 0


def same_page_path(url1: str, url2: str) -> bool:
    """Check if scheme + host + path are same (ignore hash & query)."""
    u1, u2 = urlparse(url1), urlparse(url2)
    return (u1.scheme, u1.netloc, u1.path) == (u2.scheme, u2.netloc, u2.path)


# ==========================
# POPUP ANALYSIS
# ==========================

def detect_popup_in_page(page):
    """
    Look for a visible popup on the current page.
    Returns: (popup_locator, title, popup_button_labels, nested_links)
    """
    popup = page.locator(POPUP_SELECTOR).first
    if popup.count() == 0:
        return None, None, None, None

    # If we matched the internal heading, climb up to container
    try:
        if popup.evaluate("el => el.id === 'third_party_interstitial_h1'"):
            popup = popup.locator(
                "xpath=ancestor::*[contains(@class,'popup-box') "
                "or contains(@class,'container') or contains(@class,'modal')]"
            ).first
    except Exception:
        pass

    # Title extraction
    title = ""
    title_selectors = [
        "#third_party_interstitial_h1",
        ".popup_header h1",
        ".popup_header",
        "h1, h2, h3"
    ]
    for sel in title_selectors:
        loc = popup.locator(sel)
        if loc.count() > 0:
            t = safe_text(loc.first, max_len=200)
            if t:
                title = t
                break

    # Nested links in popup
    nested_links = []
    anchors = popup.locator("a:visible")
    count = min(anchors.count(), 20)
    for i in range(count):
        a = anchors.nth(i)
        txt = safe_text(a, max_len=200)
        href = normalize_href(page.url, a.get_attribute("href"))
        if txt and href:
            nested_links.append({"text": txt, "href": href})

    # Popup action buttons
    popup_buttons = []
    buttons = popup.locator(
        "button:visible, a:visible, [role='button']:visible, input[type='button']:visible"
    )
    seen = set()
    for i in range(min(buttons.count(), 10)):
        b = buttons.nth(i)
        label = safe_text(b, max_len=150)
        if not label or label in seen:
            continue
        seen.add(label)
        popup_buttons.append(label)

    return popup, title, popup_buttons, nested_links


def test_popup_button_behavior(browser, base_url: str, trigger_text: str, button_text: str):
    """
    For each popup button:
      - Open new context
      - Click trigger → open popup
      - Click that popup button
      - Classify: navigate / stay_on_same_page
    """
    ctx = browser.new_context()
    page = ctx.new_page()
    safe_print(f"      [popup-btn] trigger='{trigger_text}' button='{button_text}'")

    result = None
    try:
        page.goto(base_url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(1000)
        auto_accept_cookies(page)
        page.wait_for_timeout(500)

        trigger = page.locator(INTERACTIVE_SELECTOR, has_text=trigger_text).first
        if trigger.count() == 0:
            safe_print("        -> Trigger not found in fresh context")
            ctx.close()
            return None

        try:
            trigger.scroll_into_view_if_needed(timeout=800)
        except Exception:
            pass

        before_url = page.url
        trigger.click(timeout=3000, force=True)
        page.wait_for_timeout(1500)

        popup, _, _, _ = detect_popup_in_page(page)
        if not popup:
            safe_print("        -> Popup did not appear in fresh context")
            ctx.close()
            return None

        btn = popup.locator(
            "button:visible, a:visible, [role='button']:visible, input[type='button']:visible",
            has_text=button_text
        ).first
        if btn.count() == 0:
            safe_print("        -> Button not found inside popup")
            ctx.close()
            return None

        try:
            btn.scroll_into_view_if_needed(timeout=800)
        except Exception:
            pass

        before_btn_url = page.url
        btn.click(timeout=3000, force=True)
        page.wait_for_timeout(2000)
        after_btn_url = page.url

        pages = ctx.pages
        if len(pages) > 1:
            new_page = pages[-1]
            try:
                new_page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass

            new_url = new_page.url
            safe_print(f"        -> Opened new tab: {new_url}")

            result = {
                "text": button_text,
                "expected": "navigate_new_tab",
                "target_url": new_url
            }
            ctx.close()
            return result

        if after_btn_url != before_btn_url:
            safe_print(f"        -> Navigated to {after_btn_url}")
            result = {
                "text": button_text,
                "expected": "navigate",
                "target_url": after_btn_url
            }
        else:
            safe_print("        -> Stayed on same page after button click")
            result = {
                "text": button_text,
                "expected": "stay_on_same_page",
                "target_url": None
            }

    except Exception as e:
        safe_print(f"        -> Error in popup button flow: {e}")
        result = {
            "text": button_text,
            "expected": "stay_on_same_page",
            "target_url": None
        }

    ctx.close()
    return result


# ==========================
# HOVER SCAN
# ==========================

def detect_hover_interactions(page):
    """
    Hover on nav/header items and capture new links revealed.
    """
    hover_results = []

    nav_items = page.locator(HOVER_TRIGGER_SELECTOR)
    total = nav_items.count()
    safe_print(f"[hover] Found {total} hover triggers")

    seen_triggers = set()

    for i in range(total):
        el = nav_items.nth(i)
        try:
            if not el.is_visible(timeout=400):
                continue
        except Exception:
            continue

        trigger_text = safe_text(el, max_len=100)
        if not trigger_text or trigger_text in seen_triggers:
            continue
        seen_triggers.add(trigger_text)

        safe_print(f"  [hover] Trigger: '{trigger_text}'")

        # links BEFORE hover
        before_links = {}
        anchors_before = page.locator("a:visible")
        for j in range(anchors_before.count()):
            a = anchors_before.nth(j)
            href = normalize_href(page.url, a.get_attribute("href"))
            if not href:
                continue
            txt = safe_text(a, max_len=200)
            if not txt:
                continue
            before_links[href] = txt

        # perform hover
        try:
            el.hover(timeout=1000)
            page.wait_for_timeout(800)
        except Exception as e:
            safe_print(f"    -> Hover failed: {e}")
            continue

        # links AFTER hover
        after_links = {}
        anchors_after = page.locator("a:visible")
        for j in range(anchors_after.count()):
            a = anchors_after.nth(j)
            href = normalize_href(page.url, a.get_attribute("href"))
            if not href:
                continue
            txt = safe_text(a, max_len=200)
            if not txt:
                continue
            after_links[href] = txt

        new_hrefs = set(after_links.keys()) - set(before_links.keys())
        if not new_hrefs:
            safe_print("    -> No new links revealed")
        else:
            safe_print(f"    -> {len(new_hrefs)} new hover links")
            revealed = []
            for href in new_hrefs:
                revealed.append({
                    "text": after_links[href],
                    "href": href
                })
            hover_results.append({
                "trigger": {
                    "text": trigger_text,
                    "selector_hint": f"text={trigger_text}"
                },
                "revealed_links": revealed
            })

        # move mouse away
        try:
            page.mouse.move(0, 0)
        except Exception:
            pass
        page.wait_for_timeout(200)

    return hover_results


# ==========================
# CLICKABLE COLLECTION
# ==========================

def collect_base_clickables(page):
    """
    Collect unique clickable labels on the page (without clicking yet).
    """
    labels = []
    seen = set()

    candidates = page.locator(INTERACTIVE_SELECTOR)
    total = min(candidates.count(), 50)
    safe_print(f"[base-scan] Found {total} clickable elements (capped)")

    for i in range(total):
        el = candidates.nth(i)
        try:
            if not el.is_visible(timeout=400):
                continue
        except Exception:
            continue

        label = safe_text(el, max_len=150)
        if not label or label in seen:
            continue
        seen.add(label)
        labels.append(label)

    return labels


# ==========================
# PER-CLICK ANALYSIS
# ==========================

def test_click_in_fresh_context(browser, base_url: str, trigger_text: str):
    """
    For one clickable label:
      - new context
      - load base page
      - click element with that text
      - classify: popup / navigate / navigate_internal / scroll / none
      - if popup: analyze title + nested links + popup button behaviors
    """
    ctx = browser.new_context()
    page = ctx.new_page()
    safe_print(f"[click-test] Trigger: '{trigger_text}'")

    interaction = {
        "trigger": {
            "text": trigger_text,
            "selector_hint": f"text={trigger_text}"
        },
        "result": {
            "type": "none"
        }
    }

    try:
        page.goto(base_url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(1000)
        auto_accept_cookies(page)
        page.wait_for_timeout(500)

        el = page.locator(INTERACTIVE_SELECTOR, has_text=trigger_text).first
        if el.count() == 0:
            safe_print("  -> Trigger not found in fresh context")
            ctx.close()
            return None

        try:
            el.scroll_into_view_if_needed(timeout=800)
        except Exception:
            pass

        before_url = page.url
        before_scroll = get_scroll_y(page)

        try:
            el.click(timeout=3000, force=True)
        except Exception as e:
            safe_print(f"  -> Click failed: {e}")
            ctx.close()
            return None

        page.wait_for_timeout(2000)

        # 1) Check for popup first
        popup, title, popup_buttons, nested_links = detect_popup_in_page(page)
        if popup:
            safe_print(f"  -> Popup detected with title: '{title}'")
            actions = []
            if popup_buttons:
                for btn_label in popup_buttons:
                    safe_print(f"    -> Testing popup button '{btn_label}'")
                    action = test_popup_button_behavior(browser, base_url, trigger_text, btn_label)
                    if action:
                        actions.append(action)

            interaction["result"] = {
                "type": "popup",
                "title": title,
                "actions": actions,
                "nested_links": nested_links or []
            }
            ctx.close()
            return interaction

        # 2) No popup: check navigation vs scroll
        after_url = page.url
        after_scroll = get_scroll_y(page)
        delta = after_scroll - before_scroll

        if after_url != before_url:
            if same_page_path(before_url, after_url):
                # same path, likely hash or internal navigation
                safe_print(f"  -> Internal navigation to {after_url} (scroll Δ={delta})")
                interaction["result"] = {
                    "type": "navigate_internal",
                    "target_url": after_url,
                    "scroll_delta": delta
                }
            else:
                safe_print(f"  -> Navigation to {after_url}")
                interaction["result"] = {
                    "type": "navigate",
                    "target_url": after_url
                }
        elif abs(delta) > 30:
            safe_print(f"  -> Scroll interaction (Δ={delta})")
            interaction["result"] = {
                "type": "scroll",
                "target_url": after_url,
                "scroll_delta": delta
            }
        else:
            safe_print("  -> No visible effect (none)")
            interaction["result"] = {
                "type": "none"
            }

    except Exception as e:
        safe_print(f"  -> Error during click test: {e}")

    ctx.close()
    return interaction


# ==========================
# MAIN SCAN
# ==========================

def scan_homepage(url: str):
    result = {
        "page_url": url,
        "hover_interactions": [],
        "click_interactions": []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # 1) Base load for hover + clickable label discovery
        base_ctx = browser.new_context()
        base_page = base_ctx.new_page()

        safe_print(f"[start] Loading base page: {url}")
        base_page.goto(url, wait_until="domcontentloaded", timeout=90000)
        base_page.wait_for_timeout(1500)
        auto_accept_cookies(base_page)
        base_page.wait_for_timeout(500)

        # Hover interactions
        hover_data = detect_hover_interactions(base_page)
        result["hover_interactions"] = hover_data

        # Clickable labels
        base_clickables = collect_base_clickables(base_page)
        safe_print(f"[base-scan] Unique trigger labels collected: {len(base_clickables)}")

        base_ctx.close()

        # 2) Analyze each clickable label in a fresh context
        for label in base_clickables:
            interaction = test_click_in_fresh_context(browser, url, label)
            if interaction:
                result["click_interactions"].append(interaction)

        browser.close()

    return result


# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        start_url = sys.argv[1]
    else:
        start_url = "https://www.tivdak.com/patient-stories/"

    data = scan_homepage(start_url)

    with open("homepage_interactions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    safe_print("\n=== FINAL HOMEPAGE INTERACTION MAP ===")
    safe_print(json.dumps(data, indent=2, ensure_ascii=False))
    safe_print("Saved to homepage_interactions.json")
