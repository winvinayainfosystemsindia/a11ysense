"""
A11ySense AI — Page Complexity Analyzer for Estimation Module.
Evaluates pages by extracting DOM elements and classifying complexity
(Simple, Medium, Complex) according to standard accessibility auditing criteria.
"""
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

COMPLEXITY_EVAL_JS = """
(() => {
    // Visibility checker: only consider elements that are rendered and visible to the user
    const isVisible = (el) => {
        if (!el) return false;
        if (el.hasAttribute('hidden') || el.getAttribute('aria-hidden') === 'true') return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    };

    // 1. Element counts (visible elements)
    const links = Array.from(document.querySelectorAll('a[href]')).filter(isVisible);
    const buttons = Array.from(document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]')).filter(isVisible);
    const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]')).filter(isVisible);
    const paragraphs = Array.from(document.querySelectorAll('p')).filter(isVisible);
    const lists = Array.from(document.querySelectorAll('ul, ol')).filter(isVisible);
    const images = Array.from(document.querySelectorAll('img, svg:not([role="button"]):not(button svg)')).filter(isVisible);
    const forms = Array.from(document.querySelectorAll('form')).filter(isVisible);
    const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), select, textarea')).filter(isVisible);
    const tables = Array.from(document.querySelectorAll('table, [role="table"], [role="grid"]')).filter(isVisible);
    const media = Array.from(document.querySelectorAll('video, audio, iframe, embed, object')).filter(isVisible);

    const linksCount = links.length;
    const buttonsCount = buttons.length;
    const totalNavElements = linksCount + buttonsCount;

    // 2. Detection of COMPLEX Triggers
    const complexTriggers = [];

    // Pop-ups, Modals, Dialogs, Cookie banners (Must be visible/open)
    const allDialogs = Array.from(document.querySelectorAll('dialog, [role="dialog"], [role="alertdialog"], [aria-modal="true"], [id*="cookie-banner"], [class*="cookie-banner"], [id*="onetrust"], [class*="cc-banner"], [class*="cookieConsent"]'));
    const activeDialogs = allDialogs.filter(el => {
        if (!isVisible(el)) return false;
        if (el.tagName === 'DIALOG' && !el.open) return false;
        return true;
    });
    if (activeDialogs.length > 0) {
        complexTriggers.push(`Active pop-up / modal dialog / cookie consent banner detected (${activeDialogs.length})`);
    }

    // Custom controls (auto-suggest, sliders, rich text, datepicker, tree, drag-drop)
    const allCustom = Array.from(document.querySelectorAll('[role="slider"], [role="tree"], [role="treeitem"], [role="combobox"], [role="spinbutton"], [role="progressbar"], [aria-autocomplete], input[list], [class*="datepicker"], [class*="date-picker"], [contenteditable="true"]'));
    const visibleCustom = allCustom.filter(isVisible);
    if (visibleCustom.length > 0) {
        complexTriggers.push(`Custom interactive widgets (sliders, comboboxes, date pickers) detected (${visibleCustom.length})`);
    }

    // Multi-step forms / wizards / checkout
    const multiStep = Array.from(document.querySelectorAll('[class*="stepper"], [class*="wizard"], [data-step], .checkout-form, [class*="multi-step"]')).filter(isVisible);
    if (multiStep.length > 0) {
        complexTriggers.push("Multi-step form / wizard / checkout flow detected");
    }

    // Sign-in, OTP, Captcha
    const authControls = Array.from(document.querySelectorAll('input[type="password"], input[autocomplete="one-time-code"], [class*="captcha"], [id*="captcha"], iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="turnstile"]')).filter(isVisible);
    if (authControls.length > 0) {
        complexTriggers.push("Authentication / password / CAPTCHA controls detected");
    }

    // Moving content / carousels / tickers / autoplay video
    const carousels = Array.from(document.querySelectorAll('[class*="carousel"], [class*="swiper"], [class*="slick"], [class*="splide"], marquee, video[autoplay]')).filter(el => {
        if (!isVisible(el)) return false;
        if (el.tagName === 'VIDEO' && el.autoplay && !el.paused) return true;
        if (el.tagName === 'MARQUEE') return true;
        return !!el.querySelector('.swiper-slide, .slick-slide, .carousel-item, .splide__slide, [class*="slide"]');
    });
    if (carousels.length > 0) {
        complexTriggers.push(`Moving content / carousel / auto-playing media detected (${carousels.length})`);
    }

    // Live updates / aria-live regions (CRITICAL: exclude empty framework announcer divs like Chakra/WordPress/React toast containers)
    const liveCandidates = Array.from(document.querySelectorAll('[aria-live], [role="status"], [role="log"], [role="alert"]'));
    const activeLive = liveCandidates.filter(el => {
        if (!isVisible(el)) return false;
        const idAndClass = (el.id + ' ' + (el.className || '')).toLowerCase();
        // Ignore framework toast/notification placeholders and a11y announcer stubs
        if (idAndClass.includes('toast') || idAndClass.includes('wp-a11y') || idAndClass.includes('announcer') || idAndClass.includes('screen-reader') || idAndClass.includes('sr-only')) {
            return false;
        }
        // Must contain actual non-empty live status text or tickers
        return el.innerText && el.innerText.trim().length > 0;
    });
    if (activeLive.length > 0) {
        complexTriggers.push(`Active live updating content / ticker detected (${activeLive.length})`);
    }

    // Charts, interactive maps, dashboards
    const chartsAndMaps = Array.from(document.querySelectorAll('canvas, svg[class*="chart"], [class*="highcharts"], [class*="recharts"], [class*="chartjs"], [class*="dashboard"], [class*="leaflet"], [class*="mapbox"]')).filter(el => {
        if (!isVisible(el)) return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 50 && rect.height > 50;
    });
    if (chartsAndMaps.length > 0) {
        complexTriggers.push(`Data visualization / charts / interactive maps detected (${chartsAndMaps.length})`);
    }

    // Complex tables (merged cells, sortable, nested)
    const complexTables = Array.from(document.querySelectorAll('table td[colspan], table td[rowspan], table th[colspan], table th[rowspan], table table, th[aria-sort], [class*="datatable"]')).filter(isVisible);
    if (complexTables.length > 0) {
        complexTriggers.push("Complex tables (merged cells, sortable columns, or nested tables) detected");
    }

    // File upload
    const fileInputs = Array.from(document.querySelectorAll('input[type="file"]')).filter(isVisible);
    if (fileInputs.length > 0) {
        complexTriggers.push(`File upload controls detected (${fileInputs.length})`);
    }

    // Third-party widgets (chat, payments)
    const thirdPartyWidgets = Array.from(document.querySelectorAll('iframe[src*="stripe"], iframe[src*="paypal"], iframe[src*="intercom"], iframe[src*="zendesk"], iframe[src*="tawk"], iframe[src*="crisp"], iframe[src*="calendly"]')).filter(isVisible);
    if (thirdPartyWidgets.length > 0) {
        complexTriggers.push("Third-party embeds (payment gateway, live chat, or booking widget) detected");
    }

    // 3. Detection of MEDIUM Triggers
    const mediumTriggers = [];

    // Basic forms
    if (forms.length > 0 || inputs.length > 0) {
        mediumTriggers.push(`Standard form with input fields detected (${inputs.length} fields)`);
    }

    // Data table with headers
    const dataTables = Array.from(document.querySelectorAll('table th, [role="rowheader"], [role="columnheader"]')).filter(isVisible);
    if (dataTables.length > 0 && complexTables.length === 0) {
        mediumTriggers.push(`Standard data table with column/row headings detected (${tables.length})`);
    }

    // Embedded video, audio, or iframe
    if (media.length > 0 && carousels.length === 0 && thirdPartyWidgets.length === 0) {
        mediumTriggers.push(`Embedded media or player detected (${media.length})`);
    }

    // Navigation that opens: dropdowns, accordions, tabs
    const openingNav = Array.from(document.querySelectorAll('[aria-expanded="true"], [role="tab"], details, [class*="dropdown-menu"].show')).filter(isVisible);
    if (openingNav.length > 0) {
        mediumTriggers.push(`Interactive expanding navigation (dropdown, accordion, or tabs) detected (${openingNav.length})`);
    }

    // Search box with plain results
    const searchBoxes = Array.from(document.querySelectorAll('input[type="search"], input[name*="search"], [role="search"] input')).filter(isVisible);
    if (searchBoxes.length > 0) {
        mediumTriggers.push("Search input box detected");
    }

    // Many links and buttons (over about 60)
    if (totalNavElements > 60) {
        mediumTriggers.push(`High link/button density (${totalNavElements} total navigation controls, > 60)`);
    }

    // 4. Decision Logic
    let complexity = "simple";
    let activeTriggers = [];
    let summaryRationale = "";

    if (complexTriggers.length > 0) {
        complexity = "complex";
        activeTriggers = complexTriggers;
        summaryRationale = "Page contains dynamic, custom, or focus-shifting interactive components.";
    } else if (mediumTriggers.length > 0) {
        complexity = "medium";
        activeTriggers = mediumTriggers;
        summaryRationale = "Page includes standard interactive controls (forms, expanding menus, tables, or media).";
    } else {
        complexity = "simple";
        activeTriggers = [
            "Static content only (headings, paragraphs, lists)",
            `Standard navigation (${totalNavElements} total links/buttons <= 60)`,
            "No dynamic popups, complex forms, or custom widgets"
        ];
        summaryRationale = "Clean static page readable from top to bottom with standard navigational links.";
    }

    return {
        complexity: complexity,
        summary_rationale: summaryRationale,
        triggers: activeTriggers,
        counts: {
            links: linksCount,
            buttons: buttonsCount,
            headings: headings.length,
            paragraphs: paragraphs.length,
            lists: lists.length,
            images: images.length,
            forms: forms.length,
            inputs: inputs.length,
            tables: tables.length,
            media: media.length,
            total_elements: document.querySelectorAll('*').length
        }
    };
})();
"""


async def analyze_page_complexity(page, url: str) -> Dict[str, Any]:
    """
    Evaluates a live Playwright page for accessibility audit estimation,
    returning element statistics, complexity rating (Simple, Medium, Complex),
    and evidence triggers.
    """
    try:
        # Wait for DOM and allow modern SPAs to hydrate client-side state
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass

        try:
            await page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass

        # Brief hydration delay for JavaScript frameworks
        await page.wait_for_timeout(1000)

        title = await page.title() or "Untitled Page"
        data = await page.evaluate(COMPLEXITY_EVAL_JS)

        return {
            "url": url,
            "title": title,
            "complexity": data.get("complexity", "simple"),
            "summary_rationale": data.get("summary_rationale", ""),
            "triggers": data.get("triggers", []),
            "counts": data.get("counts", {}),
            "status": "success",
            "error": None
        }
    except Exception as e:
        logger.error(f"Error analyzing page complexity for {url}: {e}")
        return {
            "url": url,
            "title": "Page (Inspection Failed)",
            "complexity": "medium",  # safe default fallback
            "summary_rationale": f"Automated inspection encountered: {str(e)[:80]}. Defaulting to Medium.",
            "triggers": ["Page structure could not be fully analyzed; estimated as standard interaction."],
            "counts": {
                "links": 30,
                "buttons": 5,
                "headings": 4,
                "paragraphs": 10,
                "lists": 2,
                "images": 5,
                "forms": 1,
                "inputs": 3,
                "tables": 0,
                "media": 0,
                "total_elements": 150
            },
            "status": "fallback",
            "error": str(e)
        }
