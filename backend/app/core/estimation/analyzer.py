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
    // 1. Element counts
    const links = document.querySelectorAll('a[href]');
    const buttons = document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]');
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]');
    const paragraphs = document.querySelectorAll('p');
    const lists = document.querySelectorAll('ul, ol');
    const images = document.querySelectorAll('img, svg:not([role="button"]):not(button svg)');
    const forms = document.querySelectorAll('form');
    const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), select, textarea');
    const tables = document.querySelectorAll('table, [role="table"], [role="grid"]');
    const media = document.querySelectorAll('video, audio, iframe, embed, object');

    const linksCount = links.length;
    const buttonsCount = buttons.length;
    const totalNavElements = linksCount + buttonsCount;

    // 2. Detection of COMPLEX Triggers
    const complexTriggers = [];

    // Pop-ups, Modals, Dialogs, Cookie banners
    const dialogs = document.querySelectorAll('dialog, [role="dialog"], [role="alertdialog"], [aria-modal="true"], [class*="modal"], [class*="popup"], [id*="cookie-banner"], [class*="cookie-banner"], [id*="onetrust"], [class*="cc-banner"]');
    if (dialogs.length > 0) {
        complexTriggers.push(`Pop-up windows / modal dialogs / cookie banners detected (${dialogs.length})`);
    }

    // Custom controls (auto-suggest, sliders, rich text, datepicker, tree, drag-drop)
    const customWidgets = document.querySelectorAll('[role="slider"], [role="tree"], [role="treeitem"], [role="combobox"], [role="spinbutton"], [role="progressbar"], [aria-autocomplete], input[list], [class*="datepicker"], [class*="date-picker"], [contenteditable="true"], [draggable="true"]');
    if (customWidgets.length > 0) {
        complexTriggers.push(`Custom interactive widgets (sliders, comboboxes, date pickers, or editable content) detected (${customWidgets.length})`);
    }

    // Multi-step forms / wizards / checkout
    const multiStep = document.querySelectorAll('[class*="stepper"], [class*="wizard"], [data-step], .checkout-form, [class*="multi-step"]');
    if (multiStep.length > 0) {
        complexTriggers.push("Multi-step form / wizard / checkout flow detected");
    }

    // Sign-in, OTP, Captcha
    const authControls = document.querySelectorAll('input[type="password"], input[autocomplete="one-time-code"], [class*="captcha"], [id*="captcha"], iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="turnstile"]');
    if (authControls.length > 0) {
        complexTriggers.push("Authentication / password / CAPTCHA controls detected");
    }

    // Moving content / carousels / tickers / autoplay video
    const movingContent = document.querySelectorAll('[class*="carousel"], [class*="swiper"], [class*="slick"], marquee, video[autoplay], [class*="ticker"]');
    if (movingContent.length > 0) {
        complexTriggers.push(`Moving content / carousel / auto-playing video detected (${movingContent.length})`);
    }

    // Live updates / aria-live regions
    const liveRegions = document.querySelectorAll('[aria-live], [role="status"], [role="log"], [role="alert"]');
    if (liveRegions.length > 0) {
        complexTriggers.push(`Live updating regions / status messages detected (${liveRegions.length})`);
    }

    // Charts, interactive maps, dashboards
    const chartsAndMaps = document.querySelectorAll('canvas, svg[class*="chart"], [class*="highcharts"], [class*="recharts"], [class*="chartjs"], [class*="dashboard"], [class*="leaflet"], [class*="mapbox"]');
    if (chartsAndMaps.length > 0) {
        complexTriggers.push(`Data visualization / charts / interactive maps detected (${chartsAndMaps.length})`);
    }

    // Complex tables (merged cells, sortable, nested)
    const complexTables = document.querySelectorAll('table td[colspan], table td[rowspan], table th[colspan], table th[rowspan], table table, th[aria-sort], [class*="datatable"]');
    if (complexTables.length > 0) {
        complexTriggers.push("Complicated tables (merged cells, sortable columns, or nested tables) detected");
    }

    // File upload
    const fileInputs = document.querySelectorAll('input[type="file"]');
    if (fileInputs.length > 0) {
        complexTriggers.push(`File upload controls detected (${fileInputs.length})`);
    }

    // Third-party widgets (chat, payments)
    const thirdPartyWidgets = document.querySelectorAll('iframe[src*="stripe"], iframe[src*="paypal"], iframe[src*="intercom"], iframe[src*="zendesk"], iframe[src*="tawk"], iframe[src*="crisp"], iframe[src*="calendly"]');
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
    const dataTables = document.querySelectorAll('table th, [role="rowheader"], [role="columnheader"]');
    if (dataTables.length > 0 && complexTables.length === 0) {
        mediumTriggers.push(`Standard data table with column/row headings detected (${tables.length})`);
    }

    // Embedded video, audio, or iframe
    if (media.length > 0 && movingContent.length === 0 && thirdPartyWidgets.length === 0) {
        mediumTriggers.push(`Embedded media or frame detected (${media.length})`);
    }

    // Navigation that opens: dropdowns, accordions, tabs
    const openingNav = document.querySelectorAll('[aria-expanded], [role="tab"], [role="tablist"], details, summary, [class*="accordion"], [class*="dropdown-menu"]');
    if (openingNav.length > 0) {
        mediumTriggers.push(`Interactive expanding navigation (dropdown, accordion, or tabs) detected (${openingNav.length})`);
    }

    // Search box with plain results
    const searchBoxes = document.querySelectorAll('input[type="search"], input[name*="search"], [role="search"]');
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
        # Wait for initial DOM stabilization
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass

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
