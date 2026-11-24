"""
Screen complexity audit (Simple / Medium / Complex) for Android APKs using the 3-tier rubric.

Features:
    1. Discovers all top-level user-facing Activities from AndroidManifest.xml.
    2. Discovers and parses all UI Layout screens, Fragments, Dialogs, and Bottom Sheets from res/layout.
    3. Unifies activities with their corresponding layouts and inspects full view hierarchies.
    4. Computes element counts: buttons, form inputs, lists/grids, modals, custom widgets,
       auth/OTP/biometric steps, live/media content, headings.
    5. Classifies each screen into the 3-tier rubric:
         - Complex (5.5 hrs): Auth/OTP/Biometric/KYC/Payment steps, Modals/Sheets, Custom widgets, Live content, >90 elements
         - Medium  (2.5 hrs): Form controls, Tabs, Lists/Tables, Media, 35-90 elements
         - Simple  (1.0 hr):  Static informational display, simple text/icons (< 35 elements)
    6. Outputs a formatted report and writes audit_results.csv.

Usage:
    python audit.py [path/to/app.apk]
    Example:
        python audit.py base.apk
"""

import csv
import os
import re
import shutil
import subprocess
import sys
import zipfile
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set


# ── AAPT Auto-Detection ─────────────────────────────────────────────────────────

def find_aapt() -> Optional[str]:
    """Find aapt or aapt2 executable on the machine."""
    # 1. Check system PATH
    for cmd in ("aapt.exe", "aapt", "aapt2.exe", "aapt2"):
        p = shutil.which(cmd)
        if p and os.path.isfile(p):
            return p

    # 2. Check ANDROID_HOME / ANDROID_SDK_ROOT
    for env_var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        val = os.environ.get(env_var)
        if val:
            bt_dir = Path(val) / "build-tools"
            if bt_dir.exists():
                for version_dir in sorted(bt_dir.glob("*"), reverse=True):
                    for exe_name in ("aapt.exe", "aapt", "aapt2.exe", "aapt2"):
                        p = version_dir / exe_name
                        if p.exists():
                            return str(p)

    # 3. Check standard OS SDK directories
    standard_paths = [
        Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "build-tools",
        Path.home() / "Library" / "Android" / "sdk" / "build-tools",
        Path.home() / "Android" / "Sdk" / "build-tools",
        Path("/opt/android-sdk/build-tools"),
    ]
    for bt_dir in standard_paths:
        if bt_dir.exists():
            for version_dir in sorted(bt_dir.glob("*"), reverse=True):
                for exe_name in ("aapt.exe", "aapt", "aapt2.exe", "aapt2"):
                    p = version_dir / exe_name
                    if p.exists():
                        return str(p)

    return None


# ── Pure-Python AXML Fallback Parser ───────────────────────────────────────────

def parse_axml_pure_python(data: bytes) -> Tuple[List[str], List[str]]:
    """
    Fallback Android Binary XML parser that extracts tag names and raw attribute values.
    Returns (tags, attr_strings).
    """
    import struct
    if len(data) < 8:
        return [], []
    magic, file_size = struct.unpack('<II', data[0:8])
    if magic != 0x00080003:
        return [], []

    pos = 8
    strings: List[str] = []
    tags: List[str] = []
    attr_texts: List[str] = []

    while pos + 8 <= len(data):
        chunk_type, chunk_size = struct.unpack('<II', data[pos:pos+8])
        if chunk_size <= 0:
            break

        if chunk_type == 0x001c0001:  # String Pool
            if pos + 28 <= len(data):
                sc, sc_str, flags, str_offset, styles_offset = struct.unpack('<IIIII', data[pos+8:pos+28])
                base_str = pos + str_offset
                is_utf8 = bool(flags & (1 << 8))
                offsets = []
                for i in range(sc):
                    off_p = pos + 28 + i * 4
                    if off_p + 4 <= len(data):
                        offsets.append(struct.unpack('<I', data[off_p:off_p+4])[0])
                for off in offsets:
                    p = base_str + off
                    if p >= len(data):
                        continue
                    try:
                        if is_utf8:
                            u8len = data[p]
                            p += 2 if (u8len & 0x80) else 1
                            if p < len(data):
                                u8bytelen = data[p]
                                p += 2 if (u8bytelen & 0x80) else 1
                                strings.append(data[p:p+u8bytelen].decode('utf-8', errors='ignore'))
                        else:
                            u16len = struct.unpack('<H', data[p:p+2])[0]
                            p += 2
                            strings.append(data[p:p+u16len*2].decode('utf-16le', errors='ignore'))
                    except Exception:
                        pass
        elif chunk_type == 0x00100102:  # Start Element
            if pos + 30 <= len(data):
                line_num, comment_idx, ns_idx, name_idx, attr_start, attr_size, attr_count = struct.unpack(
                    '<IIIIHHH', data[pos+8:pos+30]
                )
                if 0 <= name_idx < len(strings):
                    tags.append(strings[name_idx])
                attr_offset = pos + attr_start
                for a in range(attr_count):
                    ap = attr_offset + a * 20
                    if ap + 20 <= len(data):
                        a_ns, a_name, a_val_str, a_type, a_data = struct.unpack('<IIIII', data[ap:ap+20])
                        if 0 <= a_val_str < len(strings):
                            attr_texts.append(strings[a_val_str])
                        elif a_type == 3 and 0 <= a_data < len(strings):
                            attr_texts.append(strings[a_data])

        pos += chunk_size

    return tags, attr_texts


# ── Layout & View Hierarchy Analysis ──────────────────────────────────────────

def analyze_view_metrics(tags: List[str], attrs: List[str], name_hint: str = "") -> Dict[str, Any]:
    """Analyzes tags and attributes to produce metrics for the 3-tier rubric."""
    tag_lower = [t.lower() for t in tags]
    attr_lower = [a.lower() for a in attrs]
    all_text = " ".join(tag_lower + attr_lower + [name_hint.lower()])

    # Form controls
    form_controls = sum(
        1 for t in tag_lower
        if any(k in t for k in ['edittext', 'textinput', 'spinner', 'checkbox', 'radiobutton', 'switch', 'togglebutton'])
    )

    # Buttons
    buttons = sum(
        1 for t in tag_lower
        if any(k in t for k in ['button', 'floatingactionbutton']) and 'radio' not in t
    )

    # Headings / Toolbars
    headings = sum(
        1 for t in tag_lower
        if any(k in t for k in ['toolbar', 'actionbar', 'titleview', 'header'])
    )

    # Tabs
    tabs = sum(
        1 for t in tag_lower
        if any(k in t for k in ['tablayout', 'bottomnavigationview', 'tabhost', 'navigationview'])
    )

    # Lists & Data Grids
    lists_tables = sum(
        1 for t in tag_lower
        if any(k in t for k in ['recycler', 'listview', 'gridview', 'tablelayout', 'viewpager', 'scrollview'])
    )

    # Modals / Bottom Sheets / Dialogs
    modals = sum(
        1 for t in tag_lower
        if any(k in t for k in ['dialog', 'bottomsheet', 'popupwindow', 'alertdialog'])
    )
    if any(k in name_hint.lower() for k in ['dialog', 'bottom_sheet', 'modal', 'sheet']):
        modals = max(modals, 1)

    # Custom complex interactive widgets
    custom_widgets = sum(
        1 for t in tag_lower
        if any(k in t for k in [
            'seekbar', 'ratingbar', 'progressbar', 'circularprogress', 'datepicker',
            'timepicker', 'numberpicker', 'cameraview', 'surfaceview', 'textureview', 'canvas'
        ])
    )

    # Auth / OTP / Biometrics / Passwords / KYC Camera / Payment
    auth_steps = 0
    if any(k in all_text for k in [
        'password', 'otp', 'mpin', 'pin', 'biometric', 'iris', 'fingerprint', 'captcha', 'esign', 'aadhaar', 'face'
    ]):
        auth_steps += 1
    # Check specific tag triggers
    auth_steps += sum(
        1 for t in tag_lower
        if any(k in t for k in ['biometric', 'iris', 'fingerprint', 'face', 'camera', 'barcode', 'qr'])
    )
    # Check attribute triggers (e.g., inputType password)
    auth_steps += sum(
        1 for a in attr_lower
        if any(k in a for k in ['password', 'otp', 'mpin', 'pin'])
    )

    # Live / Animated / Media content
    live_content = sum(
        1 for t in tag_lower
        if any(k in t for k in ['videoview', 'webview', 'mapview', 'lottie', 'motionlayout', 'animation', 'player'])
    )
    if 'webview' in name_hint.lower() or 'video' in name_hint.lower():
        live_content = max(live_content, 1)

    # Payment triggers
    if any(k in all_text for k in ['upi', 'payment', 'penny_drop', 'mandate', 'nach']):
        auth_steps = max(auth_steps, 1)
        custom_widgets = max(custom_widgets, 1)

    return {
        "visible_elements": len(tags),
        "buttons": buttons,
        "form_controls": form_controls,
        "tabs": tabs,
        "lists_tables": lists_tables,
        "modals": modals,
        "custom_widgets": custom_widgets,
        "auth_steps": auth_steps,
        "live_content": live_content,
        "headings": headings,
    }


# ── 3-Tier Classification ───────────────────────────────────────────────────────

def classify(m: Dict[str, Any]) -> Tuple[str, float, str]:
    """
    Classifies an Android screen into Simple, Medium, or Complex:
        - Complex (5.5 hrs): Modals, custom widgets, auth steps, live content, or >90 elements
        - Medium  (2.5 hrs): Form controls, tabs, lists/tables, media, or 35-90 elements
        - Simple  (1.0 hr):  Static display, simple text/icons, elements < 35
    """
    t3 = {
        "auth_steps": m.get("auth_steps", 0),
        "modals": m.get("modals", 0),
        "custom_widgets": m.get("custom_widgets", 0),
        "live_content": m.get("live_content", 0),
    }
    reasons_t3 = [f"{k}={v}" for k, v in t3.items() if v]
    if m.get("visible_elements", 0) > 90:
        reasons_t3.append(f"elements={m['visible_elements']}>90")
    if (m.get("buttons", 0) + m.get("form_controls", 0)) > 20:
        reasons_t3.append(f"interactive={m.get('buttons', 0) + m.get('form_controls', 0)}>20")

    if reasons_t3:
        return "Complex", 5.5, "; ".join(reasons_t3)

    t2 = {
        "form_controls": m.get("form_controls", 0),
        "tabs": m.get("tabs", 0),
        "lists_tables": m.get("lists_tables", 0),
    }
    reasons_t2 = [f"{k}={v}" for k, v in t2.items() if v]
    if 35 <= m.get("visible_elements", 0) <= 90:
        reasons_t2.append(f"elements={m['visible_elements']}")
    if m.get("buttons", 0) >= 4:
        reasons_t2.append(f"buttons={m['buttons']}")

    if reasons_t2:
        return "Medium", 2.5, "; ".join(reasons_t2)

    return "Simple", 1.0, f"elements={m.get('visible_elements', 0)}, static/simple content"


# ── Human-Readable Screen Title Generator ──────────────────────────────────────

def format_screen_title(raw_name: str) -> str:
    """Converts activity or layout names into clean, readable screen titles."""
    # Strip package prefixes
    base = raw_name.split(".")[-1]
    # Remove common prefixes/suffixes
    base = re.sub(r'^(activity_|fragment_|screen_|layout_|dialog_)', '', base, flags=re.IGNORECASE)
    base = re.sub(r'(_activity|_fragment|_screen|_layout|_dialog)$', '', base, flags=re.IGNORECASE)
    # Split camelCase and snake_case
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', base)
    if not words:
        words = [base]
    title = " ".join(w.capitalize() for w in words)
    if not any(k in title.lower() for k in ['screen', 'activity', 'dialog', 'sheet', 'view', 'flow']):
        title += " Screen"
    return title


# ── APK Scanner Engine ─────────────────────────────────────────────────────────

def audit_apk(apk_path: str) -> List[Dict[str, Any]]:
    """Analyzes the APK file and returns audited screen records."""
    if not os.path.exists(apk_path):
        raise FileNotFoundError(f"APK file not found: {apk_path}")

    aapt_exe = find_aapt()
    if aapt_exe:
        print(f"[*] Android Asset Packaging Tool: {aapt_exe}")
    else:
        print("[!] AAPT not found on system. Using built-in AXML fallback parser.")

    z = zipfile.ZipFile(apk_path, 'r')
    all_files = z.namelist()

    # 1. Extract Activities from AndroidManifest.xml
    manifest_activities: List[Dict[str, str]] = []
    if aapt_exe:
        try:
            out = subprocess.check_output(
                [aapt_exe, "dump", "xmltree", apk_path, "AndroidManifest.xml"],
                text=True,
                errors="ignore"
            )
            current_act: Optional[Dict[str, str]] = None
            for line in out.splitlines():
                if "E: activity " in line:
                    current_act = {}
                    manifest_activities.append(current_act)
                elif current_act is not None:
                    if "A: android:name" in line:
                        m = re.search(r'Raw:\s*"([^"]+)"', line)
                        if m:
                            current_act["name"] = m.group(1)
                    elif "A: android:exported" in line:
                        current_act["exported"] = "true" if "0xffffffff" in line else "false"
                    elif "A: android:label" in line:
                        m = re.search(r'Raw:\s*"([^"]+)"', line)
                        if m:
                            current_act["label"] = m.group(1)
                    elif "E: " in line and not any(
                        line.strip().startswith(p)
                        for p in ("E: intent-filter", "E: action", "E: category", "E: meta-data", "E: property")
                    ):
                        current_act = None
        except Exception as e:
            print(f"[!] Warning: AAPT manifest dump failed ({e}). Falling back to zip parser.")
            manifest_activities = []

    if not manifest_activities and "AndroidManifest.xml" in all_files:
        raw_manifest = z.read("AndroidManifest.xml")
        tags, attrs = parse_axml_pure_python(raw_manifest)
        act_names = [a for a in attrs if "activity" in a.lower() or "." in a]
        for a in set(act_names):
            manifest_activities.append({"name": a})

    # Filter out intent category stubs or internal services accidentally captured
    valid_activities = []
    for a in manifest_activities:
        name = a.get("name", "")
        if name and "." in name and not name.startswith("android.intent") and not name.startswith("android.hardware"):
            valid_activities.append(a)

    print(f"[*] Discovered {len(valid_activities)} Activities declared in AndroidManifest.xml")

    # 2. Extract Screen Layouts from res/layout/*.xml
    raw_layouts = [n[11:-4] for n in all_files if n.startswith("res/layout/") and n.endswith(".xml")]

    def is_screen_layout(name: str) -> bool:
        # Ignore internal framework / support library layouts
        if any(name.startswith(p) for p in ("abc_", "notification_", "select_dialog_", "design_", "mtrl_", "browser_actions_")):
            return False
        # Ignore small sub-component items, list cells, dividers
        if any(s in name for s in ("_item", "item_", "_row", "row_", "_holder", "_cell", "divider", "_separator", "tooltip", "_chip", "_badge", "_icon")):
            return False
        return True

    screen_layouts = [l for l in raw_layouts if is_screen_layout(l)]
    print(f"[*] Discovered {len(screen_layouts)} UI Layout screens & modals in res/layout/")

    # 3. Analyze all layout files (parallel for maximum speed)
    def dump_layout(layout_name: str) -> Tuple[str, List[str], List[str]]:
        rel_path = f"res/layout/{layout_name}.xml"
        if aapt_exe:
            try:
                res = subprocess.check_output(
                    [aapt_exe, "dump", "xmltree", apk_path, rel_path],
                    text=True,
                    errors="ignore"
                )
                tags = []
                attrs = []
                for line in res.splitlines():
                    s = line.strip()
                    if s.startswith("E: "):
                        parts = s.split()
                        if len(parts) > 1:
                            tags.append(parts[1])
                    elif s.startswith("A: "):
                        attrs.append(s)
                return layout_name, tags, attrs
            except Exception:
                pass

        # Fallback to pure Python
        try:
            raw = z.read(rel_path)
            tags, attrs = parse_axml_pure_python(raw)
            return layout_name, tags, attrs
        except Exception:
            return layout_name, [], []

    layout_metrics_map: Dict[str, Dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for layout_name, tags, attrs in executor.map(dump_layout, screen_layouts):
            layout_metrics_map[layout_name] = analyze_view_metrics(tags, attrs, layout_name)

    # 4. Map and unify Activities with Layouts
    audited_rows: List[Dict[str, Any]] = []
    used_layouts: Set[str] = set()

    # Process Activities
    for act in valid_activities:
        act_name = act["name"]
        short_name = act_name.split(".")[-1].lower()

        # Find best matching layout
        matched_layout = None
        for l in screen_layouts:
            l_clean = l.lower().replace("_", "")
            if short_name in l_clean or l_clean in short_name:
                matched_layout = l
                break

        if matched_layout and matched_layout in layout_metrics_map:
            metrics = dict(layout_metrics_map[matched_layout])
            used_layouts.add(matched_layout)
        else:
            # Activity without dedicated static XML layout (e.g. React Native container or dynamic view)
            metrics = analyze_view_metrics([], [], act_name)
            metrics["visible_elements"] = max(metrics["visible_elements"], 15)

        # Activity specific triggers
        if any(k in act_name.lower() for k in ['payment', 'upi', 'checkout']):
            metrics["auth_steps"] = max(metrics.get("auth_steps", 0), 1)
            metrics["custom_widgets"] = max(metrics.get("custom_widgets", 0), 1)
        if any(k in act_name.lower() for k in ['biometric', 'iris', 'face', 'otp', 'camera', 'esign', 'kyc']):
            metrics["auth_steps"] = max(metrics.get("auth_steps", 0), 2)
        if any(k in act_name.lower() for k in ['video', 'preview', 'webview']):
            metrics["live_content"] = max(metrics.get("live_content", 0), 1)
        if any(k in act_name.lower() for k in ['dialog', 'wrapper', 'permission']):
            metrics["modals"] = max(metrics.get("modals", 0), 1)

        tier, est_hours, why = classify(metrics)
        title = act.get("label") or format_screen_title(act_name)

        audited_rows.append({
            "screen_name": act_name,
            "screen_type": "Activity Screen",
            "title": title,
            "tier": tier,
            "est_hours": est_hours,
            "why": why,
            **metrics
        })

    # Process remaining standalone Layout Screens, Fragments, Dialogs, Bottom Sheets
    for l_name in screen_layouts:
        if l_name in used_layouts:
            continue

        metrics = layout_metrics_map[l_name]
        # Classify screen type
        if any(k in l_name.lower() for k in ['dialog', 'bottom_sheet', 'modal', 'popup']):
            screen_type = "Modal / Dialog Sheet"
        elif any(k in l_name.lower() for k in ['fragment', 'tab']):
            screen_type = "Fragment / Sub-screen"
        elif any(k in l_name.lower() for k in ['workflow', 'flow', 'stepper', 'screen', 'screens', 'activity']):
            screen_type = "Feature Workflow Screen"
        else:
            screen_type = "UI Layout Screen"

        tier, est_hours, why = classify(metrics)
        title = format_screen_title(l_name)

        audited_rows.append({
            "screen_name": f"layout/{l_name}",
            "screen_type": screen_type,
            "title": title,
            "tier": tier,
            "est_hours": est_hours,
            "why": why,
            **metrics
        })

    z.close()
    return audited_rows


# ── Main Entrypoint ─────────────────────────────────────────────────────────────

def main():
    # Determine target APK path
    if len(sys.argv) > 1:
        target_apk = sys.argv[1]
    else:
        # Check current directory for any .apk file
        candidates = list(Path(".").glob("*.apk"))
        if candidates:
            target_apk = str(candidates[0])
            print(f"[*] No APK specified. Defaulting to local candidate: {target_apk}")
        else:
            target_apk = input("Enter path to APK file: ").strip()

    if not target_apk or not os.path.exists(target_apk):
        print(f"Error: APK file '{target_apk}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*95}")
    print(f" A11ySense — Android APK Screen Complexity Audit")
    print(f" Target APK: {os.path.abspath(target_apk)}")
    print(f"{'='*95}\n")

    rows = audit_apk(target_apk)

    # Sort rows by Tier priority: Complex first, then Medium, then Simple
    tier_order = {"Complex": 0, "Medium": 1, "Simple": 2}
    rows.sort(key=lambda r: (tier_order.get(r["tier"], 3), r["screen_name"]))

    # Print formatted table
    print(f"\n{'-'*115}")
    print(f"{'Tier':<9} {'Est Hours':<11} {'Screen Type':<24} {'Screen / Component Name':<42} {'Rationale'}")
    print(f"{'-'*115}")

    for r in rows:
        disp_name = r["screen_name"]
        if len(disp_name) > 40:
            disp_name = "..." + disp_name[-37:]
        why_disp = r["why"]
        if len(why_disp) > 45:
            why_disp = why_disp[:42] + "..."
        print(f"{r['tier']:<9} {r['est_hours']:>4.1f} hrs    {r['screen_type']:<24} {disp_name:<42} {why_disp}")

    # Write CSV
    if rows:
        fieldnames = [
            "screen_name", "screen_type", "title", "tier", "est_hours", "why",
            "visible_elements", "buttons", "form_controls", "tabs", "lists_tables",
            "modals", "custom_widgets", "auth_steps", "live_content", "headings"
        ]
        output_csv = "audit_results.csv"
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)

        total_hours = sum(r.get("est_hours", 0) for r in rows)
        complex_count = sum(1 for r in rows if r["tier"] == "Complex")
        medium_count = sum(1 for r in rows if r["tier"] == "Medium")
        simple_count = sum(1 for r in rows if r["tier"] == "Simple")

        print(f"\n{'-'*115}")
        print(f" Summary Audit Results:")
        print(f"   Total Screens Audited : {len(rows)}")
        print(f"   Complex Screens (5.5h): {complex_count}")
        print(f"   Medium Screens  (2.5h): {medium_count}")
        print(f"   Simple Screens  (1.0h): {simple_count}")
        print(f"   Total Audit Effort    : {total_hours:.1f} hours")
        print(f"   Report Written To     : {os.path.abspath(output_csv)}")
        print(f"{'='*115}\n")


if __name__ == "__main__":
    main()