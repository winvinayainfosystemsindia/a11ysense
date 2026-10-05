"""
A11ySense AI — Cost and Effort Estimation Calculator.
Calculates API usage costs, platform charges, manual verification effort (hrs),
30% profit margin, and final quoted costs based on page complexity.
"""
from typing import Dict, Any, List

# Default constants
DEFAULT_HOURLY_RATE = 40.0         # $40.00 per hour of assistive tech verification
DEFAULT_PLATFORM_FEE_PER_PAGE = 10.0 # $10.00 automated browser scanning & hosting fee
DEFAULT_PROFIT_MARGIN_PCT = 30.0   # 30% margin

# Complexity Profiles
COMPLEXITY_PROFILES = {
    "simple": {
        "label": "Simple",
        "manual_hours": 1.0,
        "api_cost": 0.15,
        "description": "Static content only. Read top-to-bottom with standard links and basic elements."
    },
    "medium": {
        "label": "Medium",
        "manual_hours": 2.5,
        "api_cost": 0.60,
        "description": "Standard interactive controls: basic forms, data tables, expanding menus, tabs, or media."
    },
    "complex": {
        "label": "Complex",
        "manual_hours": 5.5,
        "api_cost": 1.80,
        "description": "Dynamic custom widgets, modals, multi-step wizards, live updates, or complex tables."
    }
}


def calculate_page_estimate(
    page_data: Dict[str, Any],
    hourly_rate: float = DEFAULT_HOURLY_RATE,
    platform_fee_per_page: float = DEFAULT_PLATFORM_FEE_PER_PAGE,
    profit_margin_pct: float = DEFAULT_PROFIT_MARGIN_PCT
) -> Dict[str, Any]:
    """Calculates estimation line item for a single page."""
    complexity = str(page_data.get("complexity", "medium")).lower()
    profile = COMPLEXITY_PROFILES.get(complexity, COMPLEXITY_PROFILES["medium"])

    manual_hours = float(profile["manual_hours"])
    api_cost = float(profile["api_cost"])
    platform_cost = float(platform_fee_per_page)
    manual_cost = round(manual_hours * hourly_rate, 2)

    base_cost = round(api_cost + platform_cost + manual_cost, 2)
    profit_margin = round(base_cost * (profit_margin_pct / 100.0), 2)
    final_cost = round(base_cost + profit_margin, 2)

    return {
        **page_data,
        "complexity": complexity,
        "complexity_label": profile["label"],
        "manual_hours": manual_hours,
        "manual_cost": manual_cost,
        "api_cost": api_cost,
        "platform_cost": platform_cost,
        "base_cost": base_cost,
        "profit_margin": profit_margin,
        "final_cost": final_cost
    }


def calculate_total_estimate(
    pages: List[Dict[str, Any]],
    hourly_rate: float = DEFAULT_HOURLY_RATE,
    platform_fee_per_page: float = DEFAULT_PLATFORM_FEE_PER_PAGE,
    profit_margin_pct: float = DEFAULT_PROFIT_MARGIN_PCT
) -> Dict[str, Any]:
    """Aggregates all analyzed pages into a comprehensive audit estimate."""
    calculated_pages = [
        calculate_page_estimate(
            p,
            hourly_rate=hourly_rate,
            platform_fee_per_page=platform_fee_per_page,
            profit_margin_pct=profit_margin_pct
        )
        for p in pages
    ]

    total_pages = len(calculated_pages)
    total_manual_hours = round(sum(p["manual_hours"] for p in calculated_pages), 1)
    total_manual_cost = round(sum(p["manual_cost"] for p in calculated_pages), 2)
    total_api_cost = round(sum(p["api_cost"] for p in calculated_pages), 2)
    total_platform_cost = round(sum(p["platform_cost"] for p in calculated_pages), 2)
    total_base_cost = round(sum(p["base_cost"] for p in calculated_pages), 2)
    total_profit_margin = round(sum(p["profit_margin"] for p in calculated_pages), 2)
    total_final_cost = round(sum(p["final_cost"] for p in calculated_pages), 2)

    # Complexity breakdown counts
    simple_count = sum(1 for p in calculated_pages if p["complexity"] == "simple")
    medium_count = sum(1 for p in calculated_pages if p["complexity"] == "medium")
    complex_count = sum(1 for p in calculated_pages if p["complexity"] == "complex")

    return {
        "pages": calculated_pages,
        "summary": {
            "total_pages": total_pages,
            "simple_pages": simple_count,
            "medium_pages": medium_count,
            "complex_pages": complex_count,
            "hourly_rate": hourly_rate,
            "platform_fee_per_page": platform_fee_per_page,
            "profit_margin_pct": profit_margin_pct,
            "total_manual_hours": total_manual_hours,
            "total_manual_cost": total_manual_cost,
            "total_api_cost": total_api_cost,
            "total_platform_cost": total_platform_cost,
            "total_base_cost": total_base_cost,
            "total_profit_margin": total_profit_margin,
            "total_final_cost": total_final_cost
        }
    }
