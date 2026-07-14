import logging
import re
from typing import List, Dict, Any
from playwright.async_api import Page
from app.schemas import Violation

logger = logging.getLogger(__name__)

class LandmarkSkill:
    """
    Skill for testing page landmarks for appropriate, descriptive, and unique accessible names.
    Ensures landmarks are highly usable for screen reader users.
    """
    
    async def run_landmark_test(self, page: Page) -> dict:
        logger.info("Running Landmark Accessibility checks")
        violations = []
        passes = []
        
        # 1. Retrieve all visible landmarks on the page
        try:
            landmarks = await page.evaluate("""() => {
                const landmarkSelectors = [
                    'main', '[role="main"]',
                    'nav', '[role="navigation"]',
                    'aside', '[role="complementary"]',
                    'header', '[role="banner"]',
                    'footer', '[role="contentinfo"]',
                    '[role="search"]',
                    'form', '[role="form"]',
                    'section', '[role="region"]'
                ];
                
                const elements = Array.from(document.querySelectorAll(landmarkSelectors.join(', ')));
                
                function getLandmarkRole(el) {
                    let role = el.getAttribute('role');
                    if (role) return role.toLowerCase();
                    
                    const tagName = el.tagName.toLowerCase();
                    if (tagName === 'main') return 'main';
                    if (tagName === 'nav') return 'navigation';
                    if (tagName === 'aside') return 'complementary';
                    if (tagName === 'header') return 'banner';
                    if (tagName === 'footer') return 'contentinfo';
                    if (tagName === 'form') return 'form';
                    if (tagName === 'section') return 'region';
                    return '';
                }

                function getAccessibleName(el) {
                    let name = "";
                    if (el.getAttribute("aria-labelledby")) {
                        const ids = el.getAttribute("aria-labelledby").split(/\s+/);
                        const labels = ids.map(id => {
                            const lbl = document.getElementById(id);
                            return lbl ? lbl.innerText || lbl.textContent : "";
                        }).filter(Boolean);
                        if (labels.length > 0) name = labels.join(" ");
                    }
                    
                    if (!name && el.getAttribute("aria-label")) {
                        name = el.getAttribute("aria-label");
                    }
                    
                    if (!name && el.getAttribute("title")) {
                        name = el.getAttribute("title");
                    }
                    
                    return name.trim().replace(/\s+/g, " ");
                }
                
                return elements.filter(el => {
                    // Filter out nested headers/footers that are not landmarks.
                    const tagName = el.tagName.toLowerCase();
                    if (tagName === 'header' || tagName === 'footer') {
                        const closestParent = el.parentElement ? el.parentElement.closest('article, aside, main, nav, section') : null;
                        if (closestParent) return false;
                    }
                    
                    // Filter visible
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) return false;
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                    
                    // Form and section are only landmarks if they have an accessible name or explicit role
                    const role = getLandmarkRole(el);
                    if (role === 'form' || role === 'region') {
                        const hasName = el.hasAttribute('aria-label') || el.hasAttribute('aria-labelledby') || el.hasAttribute('title');
                        const hasExplicitRole = el.hasAttribute('role');
                        if (!hasName && !hasExplicitRole) return false;
                    }
                    
                    return true;
                }).map(el => {
                    const role = getLandmarkRole(el);
                    const name = getAccessibleName(el);
                    return {
                        tagName: el.tagName.toLowerCase(),
                        id: el.id || "",
                        role: role,
                        name: name,
                        html: el.outerHTML.substring(0, 500)
                    };
                });
            }""")
        except Exception as e:
            logger.error(f"Failed to evaluate landmarks script: {e}")
            return {"violations": [], "passes": []}
            
        # Group landmarks by role/type
        landmarks_by_role: Dict[str, List[Dict[str, Any]]] = {}
        for lm in landmarks:
            role = lm["role"]
            if role not in landmarks_by_role:
                landmarks_by_role[role] = []
            landmarks_by_role[role].append(lm)
            
        # Define redundant keywords regex for each role
        redundant_patterns = {
            "navigation": re.compile(r"\b(nav|navigation)\b", re.IGNORECASE),
            "banner": re.compile(r"\b(banner|header)\b", re.IGNORECASE),
            "contentinfo": re.compile(r"\b(contentinfo|footer)\b", re.IGNORECASE),
            "complementary": re.compile(r"\b(complementary|aside)\b", re.IGNORECASE),
            "main": re.compile(r"\bmain\b", re.IGNORECASE),
            "search": re.compile(r"\bsearch\b", re.IGNORECASE),
            "form": re.compile(r"\bform\b", re.IGNORECASE),
            "region": re.compile(r"\b(region|section)\b", re.IGNORECASE)
        }
        
        for role, group in landmarks_by_role.items():
            role_display = role.capitalize()
            
            # Check 1: Multiple landmarks of the same type
            if len(group) > 1:
                names_seen = {}
                for lm in group:
                    name = lm["name"]
                    html = lm["html"]
                    target = [f"{lm['tagName']}{'#' + lm['id'] if lm['id'] else ''}"]
                    
                    if not name:
                        # Violation: Landmark has no accessible name, but there are multiple of this type
                        violations.append(Violation(
                            id="landmark-multiple-unlabeled",
                            impact="moderate",
                            description=f"Multiple {role_display} landmarks detected without accessible names. When multiple landmarks of the same type exist, each must have a unique label to distinguish them.",
                            help=f"Provide a unique accessible name (using aria-label or aria-labelledby) for this {role_display} landmark.",
                            helpUrl="https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html",
                            nodes=[{"html": html, "target": target}],
                            metadata={
                                "friendly_name": f"Unlabeled Landmark in Multiple {role_display} Group",
                                "wcag_criteria": "1.3.1 Info and Relationships",
                                "wcag_level": "A",
                                "severity": "Medium",
                                "business_impact": "Screen reader users will hear multiple identical landmark roles announced (e.g., 'navigation', 'navigation') with no text label, forcing them to guess where each nav leads.",
                                "expected_result": f"Each {role_display} landmark must have a unique accessible name specifying its purpose (e.g., 'Primary', 'Footer').",
                                "actual_result": f"Multiple {role_display} landmarks found, but this landmark has no accessible name.",
                                "steps_to_reproduce": f"1. Audit the page's landmarks.\n2. Locate the multiple <{lm['tagName']}> landmarks.\n3. Verify if each has a unique aria-label or aria-labelledby.",
                                "remediation": f"Add a descriptive 'aria-label' or 'aria-labelledby' to this <{lm['tagName']}> landmark.",
                                "refined_by": "LandmarkSkill"
                            }
                        ))
                    else:
                        if name not in names_seen:
                            names_seen[name] = []
                        names_seen[name].append(lm)
                
                # Check for duplicate names within the same role group
                for name, lms in names_seen.items():
                    if len(lms) > 1:
                        for lm in lms:
                            html = lm["html"]
                            target = [f"{lm['tagName']}{'#' + lm['id'] if lm['id'] else ''}"]
                            violations.append(Violation(
                                id="landmark-duplicate-name",
                                impact="moderate",
                                description=f"Multiple {role_display} landmarks have duplicate accessible names: '{name}'. Each must have a unique name.",
                                help=f"Ensure all {role_display} landmarks have distinct accessible names to help screen reader users distinguish them.",
                                helpUrl="https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html",
                                nodes=[{"html": html, "target": target}],
                                metadata={
                                    "friendly_name": "Duplicate Landmark Accessible Names",
                                    "wcag_criteria": "1.3.1 Info and Relationships",
                                    "wcag_level": "A",
                                    "severity": "Medium",
                                    "business_impact": "Users navigating landmarks by name will hear duplicate choices, causing confusion and making it hard to find the desired page region.",
                                    "expected_result": f"Each {role_display} landmark should have a unique, distinguishing label.",
                                    "actual_result": f"Found duplicate accessible name '{name}' on multiple {role_display} landmarks.",
                                    "steps_to_reproduce": f"1. Locate multiple {role_display} landmarks.\n2. Verify their aria-label or aria-labelledby values.\n3. Check for duplicates.",
                                    "remediation": f"Rename one of the {role_display} landmarks to differentiate them (e.g., 'Primary' vs. 'Footer').",
                                    "refined_by": "LandmarkSkill"
                                }
                            ))
                    else:
                        # Unique name pass
                        lm = lms[0]
                        passes.append({
                            "id": "landmark-unique-name-pass",
                            "help": f"{role_display} landmark unique name verified",
                            "description": f"The {role_display} landmark has a unique and appropriate accessible name: '{name}'.",
                            "helpUrl": "https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html",
                            "tags": ["wcag2a", "wcag131"],
                            "nodes": [{
                                "html": lm["html"],
                                "target": [f"{lm['tagName']}{'#' + lm['id'] if lm['id'] else ''}"]
                            }],
                            "metadata": {
                                "wcag_criteria": "1.3.1 Info and Relationships",
                                "wcag_level": "A",
                                "severity": "Medium",
                                "expected_result": f"Multiple {role_display} landmarks must have unique descriptive accessible names.",
                                "actual_result": f"Verification passed: Landmark has a unique accessible name '{name}'.",
                                "steps_to_reproduce": "1. Identify landmarks.\n2. Confirm names are unique and descriptive.",
                                "remediation": "No remediation required. Landmark is correctly labeled.",
                                "business_impact": "Allows screen reader users to quickly distinguish between different landmarks of the same type."
                            }
                        })
            else:
                # Single landmark of this type
                lm = group[0]
                html = lm["html"]
                target = [f"{lm['tagName']}{'#' + lm['id'] if lm['id'] else ''}"]
                name = lm["name"]
                
                # Under ARIA, forms and regions MUST have names to act as landmarks.
                if role in ["form", "region"] and not name:
                    violations.append(Violation(
                        id="landmark-missing-name",
                        impact="minor",
                        description=f"The {role_display} landmark is missing an accessible name.",
                        help=f"Add an accessible name (using aria-label or aria-labelledby) so that this region acts as a valid landmark.",
                        helpUrl="https://www.w3.org/WAI/ARIA/apg/practices/landmark-regions/",
                        nodes=[{"html": html, "target": target}],
                        metadata={
                            "friendly_name": f"Missing Landmark Accessible Name on {role_display}",
                            "wcag_criteria": "1.3.1 Info and Relationships",
                            "wcag_level": "A",
                            "severity": "Minor",
                            "business_impact": "Without an accessible name, the screen reader user cannot understand the purpose of this form or region landmark, reducing its navigation benefit.",
                            "expected_result": f"A {role_display} landmark should have an accessible name describing its purpose.",
                            "actual_result": f"The {role_display} landmark has no accessible name.",
                            "steps_to_reproduce": f"1. Inspect the <{lm['tagName']}> landmark.\n2. Verify if it has an aria-label or aria-labelledby attribute.",
                            "remediation": f"Add a descriptive 'aria-label' or 'aria-labelledby' to this <{lm['tagName']}> landmark.",
                            "refined_by": "LandmarkSkill"
                        }
                    ))
                else:
                    passes.append({
                        "id": "landmark-single-pass",
                        "help": f"Single {role_display} landmark structured correctly",
                        "description": f"The {role_display} landmark is structured correctly.",
                        "helpUrl": "https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html",
                        "tags": ["wcag2a", "wcag131"],
                        "nodes": [{
                            "html": html,
                            "target": target
                        }],
                        "metadata": {
                            "wcag_criteria": "1.3.1 Info and Relationships",
                            "wcag_level": "A",
                            "severity": "Medium",
                            "expected_result": f"A single {role_display} landmark is correctly defined.",
                            "actual_result": f"Verification passed: Landmark structure conforms to accessibility rules.",
                            "steps_to_reproduce": "1. Confirm structure of single landmark.",
                            "remediation": "No remediation required. Landmark conforms.",
                            "business_impact": "Enables users to navigate to this section of the page."
                        }
                    })

            # Check 2: Accessible name content appropriateness (for any landmark with a name)
            for lm in group:
                name = lm["name"]
                if not name:
                    continue
                
                html = lm["html"]
                target = [f"{lm['tagName']}{'#' + lm['id'] if lm['id'] else ''}"]
                
                # Rule A: Check for redundant role term in the name
                pattern = redundant_patterns.get(role)
                if pattern and pattern.search(name):
                    violations.append(Violation(
                        id="landmark-redundant-name",
                        impact="minor",
                        description=f"The {role_display} landmark has a redundant accessible name '{name}' that contains its own role. Screen readers automatically announce the landmark role.",
                        help=f"Remove the role term (like '{role}') from the landmark accessible name.",
                        helpUrl="https://www.w3.org/WAI/ARIA/apg/practices/landmark-regions/",
                        nodes=[{"html": html, "target": target}],
                        metadata={
                            "friendly_name": f"Redundant Landmark Accessible Name on {role_display}",
                            "wcag_criteria": "1.3.1 Info and Relationships",
                            "wcag_level": "A",
                            "severity": "Minor",
                            "business_impact": "Screen reader users will hear redundant phrasing (e.g. 'Primary Navigation navigation'), which is verbose, repetitive, and detracts from a clean user experience.",
                            "expected_result": f"The accessible name of a landmark should not include words like '{role}' or 'nav' or 'landmark'.",
                            "actual_result": f"The accessible name '{name}' contains the redundant word.",
                            "steps_to_reproduce": f"1. Inspect the accessible name of the {role_display} landmark.\n2. Verify if the name contains the word '{role}' or related role terms.",
                            "remediation": f"Update the 'aria-label' or 'aria-labelledby' to omit the word '{role}' or related terms (e.g. change 'Primary Navigation' to 'Primary').",
                            "refined_by": "LandmarkSkill"
                        }
                    ))
                
                # Rule B: Check for generic name (e.g. "nav1", "nav2", "landmark", "placeholder")
                generic_patterns = [
                    re.compile(r"^(nav|aside|section|form|header|footer|banner|main|landmark|placeholder)\d*$", re.IGNORECASE),
                    re.compile(r"^\d+$")
                ]
                is_generic = any(p.match(name) for p in generic_patterns)
                if is_generic:
                    violations.append(Violation(
                        id="landmark-generic-name",
                        impact="minor",
                        description=f"The {role_display} landmark has a generic accessible name '{name}'. Names should be descriptive of the landmark's specific content or location.",
                        help="Provide a more descriptive and meaningful accessible name for the landmark.",
                        helpUrl="https://www.w3.org/WAI/ARIA/apg/practices/landmark-regions/",
                        nodes=[{"html": html, "target": target}],
                        metadata={
                            "friendly_name": f"Generic Landmark Accessible Name on {role_display}",
                            "wcag_criteria": "1.3.1 Info and Relationships",
                            "wcag_level": "A",
                            "severity": "Minor",
                            "business_impact": "Users hearing generic labels like '{name}' will not understand the purpose of this section, defeating the purpose of labeling landmarks.",
                            "expected_result": f"Accessible name for the landmark should be descriptive of its content.",
                            "actual_result": f"Accessible name '{name}' is generic.",
                            "steps_to_reproduce": f"1. Inspect landmark name.\n2. Observe if it uses generic placeholder terms.",
                            "remediation": "Provide a descriptive label that conveys the specific content or location (e.g. 'Main site navigation' or 'Related products').",
                            "refined_by": "LandmarkSkill"
                        }
                    ))
                    
        return {"violations": violations, "passes": passes}

landmark_skill = LandmarkSkill()
