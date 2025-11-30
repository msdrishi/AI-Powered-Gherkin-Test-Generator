from playwright.sync_api import sync_playwright
import json
import sys

SCROLL_STEP = 600
MAX_SCROLLS = 5
# Target main navigation items specifically
NAV_SELECTOR = "nav a:visible, nav button:visible, header a:visible, header button:visible"
HOVER_CANDIDATE_SELECTOR = "a:visible, button:visible, [role='button']:visible"
POPUP_SELECTOR = "[role='dialog'], .modal, .popup, .overlay, [class*='modal'], [class*='popup'], [class*='dialog']"

def safe_print(message):
    """Print with safe encoding for Windows console"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Remove emojis and special characters for Windows console
        print(message.encode('ascii', 'ignore').decode('ascii'))

def get_links_snapshot(page):
    """Return dict[href] = text for all visible links."""
    links = {}
    anchors = page.locator("a:visible")
    count = anchors.count()
    for i in range(count):
        a = anchors.nth(i)
        href = a.get_attribute("href")
        if not href:
            continue
        # Make href absolute
        if href.startswith('/'):
            href = page.url.rstrip('/') + href
        elif not href.startswith('http'):
            continue
        try:
            text = a.inner_text(timeout=300).strip()
        except Exception:
            text = ""
        links[href] = text
    return links


def detect_hover_interactions(page, seen_triggers):
    """Try hovering over elements and see if new links appear."""
    safe_print("\nLooking for hover interactions...")
    interactions = []
    
    # First, try navigation items (higher priority)
    safe_print("  Scanning navigation elements...")
    nav_candidates = page.locator(NAV_SELECTOR)
    nav_count = nav_candidates.count()
    
    # Collect all navigation links first (direct links without hover)
    safe_print("  Collecting direct navigation links...")
    for i in range(nav_count):
        el = nav_candidates.nth(i)
        try:
            if not el.is_visible(timeout=200):
                continue
            trigger_text = el.inner_text(timeout=200).strip()
            trigger_href = el.get_attribute("href")
        except Exception:
            continue

        if not trigger_text or len(trigger_text) > 100:
            continue

        # Skip if already tested this trigger
        if trigger_text in seen_triggers:
            continue

        # If element has direct href (not a dropdown trigger), capture it
        if trigger_href and trigger_href != "#" and not trigger_href.startswith("javascript:"):
            # Make href absolute
            if trigger_href.startswith('/'):
                full_href = page.url.rstrip('/') + trigger_href
            elif trigger_href.startswith('http'):
                full_href = trigger_href
            else:
                continue
            
            safe_print(f"  Direct navigation link: '{trigger_text}' -> {full_href}")
            
            # Store as single-link interaction
            interaction = {
                "trigger_element": {
                    "text": trigger_text,
                    "selector": f"text={trigger_text}"
                },
                "revealed_links": [
                    {
                        "text": trigger_text,
                        "href": full_href
                    }
                ]
            }
            interactions.append(interaction)
            seen_triggers.add(trigger_text)
            continue  # Skip hover test for direct links
    
    # Then test for hover interactions
    all_candidates = page.locator(HOVER_CANDIDATE_SELECTOR)
    total_count = min(all_candidates.count(), 40)
    
    safe_print(f"Found {total_count} elements to test for hover dropdowns")

    for i in range(total_count):
        el = all_candidates.nth(i)
        try:
            if not el.is_visible(timeout=200):
                continue
            trigger_text = el.inner_text(timeout=200).strip()
        except Exception:
            continue

        if not trigger_text or len(trigger_text) > 100:
            continue

        # Skip if already tested this trigger
        if trigger_text in seen_triggers:
            continue

        safe_print(f"  Testing hover on: '{trigger_text[:50]}'")
        
        # Move mouse away first to ensure clean state
        try:
            page.mouse.move(0, 0)
            page.wait_for_timeout(200)
        except Exception:
            pass
        
        before_links = get_links_snapshot(page)
        
        try:
            el.hover(timeout=800, force=True)
            page.wait_for_timeout(800)
        except Exception:
            continue

        after_links = get_links_snapshot(page)
        new_hrefs = set(after_links.keys()) - set(before_links.keys())
        
        # If new links appeared, it means there's a dropdown/menu
        if new_hrefs:
            safe_print(f"    Found dropdown with {len(new_hrefs)} new links!")
            
            # Try to find the dropdown container that appeared
            try:
                dropdown_selectors = [
                    "[role='menu']:visible",
                    "[class*='menu']:visible",
                    "[class*='dropdown']:visible",
                    "[class*='flyout']:visible",
                ]
                
                dropdown = None
                for selector in dropdown_selectors:
                    dropdown_loc = page.locator(selector)
                    if dropdown_loc.count() > 0:
                        for j in range(min(dropdown_loc.count(), 2)):
                            test_dropdown = dropdown_loc.nth(j)
                            link_count = test_dropdown.locator("a:visible").count()
                            if link_count >= len(new_hrefs) * 0.5:
                                dropdown = test_dropdown
                                break
                        if dropdown:
                            break
                
                if dropdown:
                    dropdown_links = dropdown.locator("a:visible")
                    link_count = dropdown_links.count()
                    safe_print(f"    Extracting all {link_count} links from dropdown...")
                    
                    revealed_links = []
                    for j in range(link_count):
                        link = dropdown_links.nth(j)
                        try:
                            link_text = link.inner_text(timeout=200).strip()
                            link_href = link.get_attribute("href")
                            
                            if not link_text or len(link_text) > 150:
                                continue
                            
                            if link_href:
                                if link_href.startswith('/'):
                                    link_href = page.url.rstrip('/') + link_href
                                elif not link_href.startswith('http'):
                                    link_href = None
                            
                            revealed_links.append({
                                "text": link_text,
                                "href": link_href
                            })
                        except Exception:
                            continue
                    
                    if revealed_links:
                        interaction = {
                            "trigger_element": {
                                "text": trigger_text,
                                "selector": f"text={trigger_text}"
                            },
                            "revealed_links": revealed_links
                        }
                        interactions.append(interaction)
                        seen_triggers.add(trigger_text)
                else:
                    revealed_links = []
                    for href in new_hrefs:
                        link_text = after_links[href]
                        revealed_links.append({
                            "text": link_text,
                            "href": href
                        })
                    
                    interaction = {
                        "trigger_element": {
                            "text": trigger_text,
                            "selector": f"text={trigger_text}"
                        },
                        "revealed_links": revealed_links
                    }
                    interactions.append(interaction)
                    seen_triggers.add(trigger_text)
                    
            except Exception as e:
                safe_print(f"    Error extracting dropdown links: {e}")
        
        # Move mouse away after testing
        try:
            page.mouse.move(0, 0)
            page.wait_for_timeout(100)
        except Exception:
            pass

    safe_print(f"\nTotal hover interactions found: {len(interactions)}")
    return interactions


def get_popup_locator(page):
    return page.locator(POPUP_SELECTOR)


def extract_popup_info(modal, page):
    title = ""
    try:
        title_loc = modal.locator("h1, h2, h3, [role='heading'], .title, .modal-title").first
        if title_loc.count() > 0:
            title = title_loc.inner_text(timeout=300).strip()  # Reduced timeout
    except Exception:
        pass

    actions = []
    try:
        buttons = modal.locator("button:visible, a:visible, [role='button']:visible")
        btn_count = min(buttons.count(), 10)
        
        for i in range(btn_count):
            b = buttons.nth(i)
            try:
                text = b.inner_text(timeout=200).strip()  # Reduced timeout
            except Exception:
                text = ""
            if not text or len(text) > 50:
                continue
            
            expected = None
            target_url = None
            
            try:
                href = b.get_attribute("href")
                if href:
                    if href.startswith('/'):
                        target_url = page.url.rstrip('/') + href
                    elif href.startswith('http'):
                        target_url = href
                    expected = "navigate"
                else:
                    expected = "stay_on_same_page"
            except Exception:
                pass
            
            actions.append({
                "text": text,
                "expected": expected,
                "target_url": target_url
            })
    except Exception:
        pass

    return {
        "title": title,
        "actions": actions
    }


def detect_popup_interactions(page, seen_triggers, initial_url):
    """Click elements and see if any popup appears."""
    safe_print("\nLooking for popup interactions...")
    interactions = []
    candidates = page.locator(HOVER_CANDIDATE_SELECTOR)
    count = min(candidates.count(), 30)  # Reduced from 50 to 30
    safe_print(f"Found {count} elements to test for popups")

    for i in range(count):
        el = candidates.nth(i)
        try:
            if not el.is_visible(timeout=200):  # Reduced timeout
                continue
            text = el.inner_text(timeout=200).strip()  # Reduced timeout
        except Exception:
            continue
        
        if not text or len(text) > 100:
            continue

        # Skip if already tested
        if text in seen_triggers:
            continue

        safe_print(f"  Testing click on: '{text[:50]}'")
        before_popup_count = get_popup_locator(page).count()
        before_url = page.url

        try:
            el.click(timeout=1000)  # Reduced timeout
            page.wait_for_timeout(800)  # Reduced wait
        except Exception:
            continue

        after_popup_loc = get_popup_locator(page)
        after_popup_count = after_popup_loc.count()
        after_url = page.url

        # Case 1: popup appeared
        if after_popup_count > before_popup_count:
            safe_print(f"    Popup appeared!")
            modal = after_popup_loc.first
            popup_info = extract_popup_info(modal, page)

            if popup_info["title"] or popup_info["actions"]:
                interaction = {
                    "trigger_button": {
                        "text": text,
                        "selector": f"text={text}"
                    },
                    "popup": popup_info
                }
                interactions.append(interaction)
                seen_triggers.add(text)

            # Close popup
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)  # Reduced wait
            except Exception:
                pass

        # Case 2: navigation happened - record it
        elif after_url != before_url:
            safe_print(f"    Navigated to: {after_url}")
            
            # Create a navigation interaction record
            interaction = {
                "trigger_button": {
                    "text": text,
                    "selector": f"text={text}"
                },
                "popup": {
                    "title": "",
                    "actions": [
                        {
                            "text": text,
                            "expected": "navigate",
                            "target_url": after_url
                        }
                    ]
                }
            }
            interactions.append(interaction)
            seen_triggers.add(text)
            
            # Navigate back to initial URL
            try:
                page.goto(initial_url, wait_until="load", timeout=8000)  # Reduced timeout
                page.wait_for_timeout(500)  # Reduced wait
            except Exception:
                pass

    safe_print(f"\nTotal popup/navigation interactions found: {len(interactions)}")
    return interactions


def scan_website(url: str):
    with sync_playwright() as p:
        safe_print("Starting browser...")
        browser = p.chromium.launch(headless=False)  # Changed to headless for speed
        page = browser.new_page()
        
        # Store the initial URL
        initial_url = url
        
        try:
            safe_print(f"\nNavigating to: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=15000)  # Changed wait_until
            safe_print("Page loaded!")
            
            page.wait_for_timeout(2000)  # Reduced wait
            
            title = page.title()
            safe_print(f"\nPage Title: {title}")
            safe_print(f"Initial URL: {initial_url}")
            
        except Exception as e:
            safe_print(f"Error loading page: {e}")
            browser.close()
            return

        all_hover_interactions = []
        all_popup_interactions = []
        seen_hover_triggers = set()
        seen_popup_triggers = set()

        # Initial viewport scan
        safe_print("\n" + "="*60)
        safe_print("SCANNING INITIAL VIEWPORT")
        safe_print("="*60)
        
        all_hover_interactions.extend(detect_hover_interactions(page, seen_hover_triggers))
        # Skip popup interactions for speed - uncomment if needed
        # all_popup_interactions.extend(detect_popup_interactions(page, seen_popup_triggers, initial_url))

        # Use initial_url instead of page.url
        scenario_data = {
            "page_url": initial_url,
            "hover_interactions": all_hover_interactions,
            "popup_interactions": all_popup_interactions,
        }

        safe_print("\n" + "="*60)
        safe_print("FINAL SCAN RESULTS:")
        safe_print("="*60)
        safe_print(f"Base URL: {initial_url}")
        safe_print(f"Total Hover Interactions: {len(all_hover_interactions)}")
        safe_print(f"Total Popup/Navigation Interactions: {len(all_popup_interactions)}")
        safe_print(f"\nTotal Links Captured in Hovers: {sum(len(h['revealed_links']) for h in all_hover_interactions)}")
        
        with open("scan_results.json", "w", encoding="utf-8") as f:
            json.dump(scenario_data, f, indent=2, ensure_ascii=False)
        safe_print("\nResults saved to scan_results.json")
        
        browser.close()


if __name__ == "__main__":
    # Accept URL from command line argument
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = "https://www.nike.com/in/"
    
    scan_website(target_url)