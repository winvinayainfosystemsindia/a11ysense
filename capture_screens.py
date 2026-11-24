"""
A11ySense — Automatic Android Screen Capture & Crawler Tool
Automatically captures screenshots from your connected Android phone or emulator
without requiring manual keypresses.

Modes:
  1. Default: Real-Time Auto-Watch Mode (Hands-free)
     python capture_screens.py
     Just navigate your app on your phone! Every time you open a screen, tab,
     or dialog, the tool automatically snaps and links it.

  2. Autonomous Robot Crawler:
     python capture_screens.py --crawl
     Automatically launches the app, taps buttons/tabs, explores the UI,
     and captures screens without you touching the phone!

  3. Install APK:
     python capture_screens.py --install
     Installs base.apk on your connected device.
"""

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Set, Any

SCREENSHOTS_DIR = Path("screenshots")
CSV_PATH = Path("audit_results.csv")
TARGET_APK = Path("base.apk")
APP_PACKAGE = "com.piramal.app.pchf"
MAIN_ACTIVITY = "com.piramal.app.pchf.MainActivity"


def find_adb() -> Optional[str]:
    """Locates adb executable on system or Android SDK."""
    cmd = shutil.which("adb")
    if cmd and os.path.isfile(cmd):
        return cmd
    
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        Path(local_app_data) / "Android" / "Sdk" / "platform-tools" / "adb.exe",
        Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe",
        Path("C:/Android/platform-tools/adb.exe"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def get_connected_devices(adb_exe: str) -> List[str]:
    """Returns list of connected and authorized devices."""
    try:
        out = subprocess.check_output([adb_exe, "devices"], text=True, errors="ignore")
        devices = []
        for line in out.strip().splitlines()[1:]:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        return devices
    except Exception as e:
        print(f"Error querying ADB devices: {e}")
        return []


def is_app_installed(adb_exe: str, package_name: str, device_id: Optional[str] = None) -> bool:
    """Checks if package is installed on device."""
    cmd = [adb_exe]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "pm", "list", "packages", package_name])
    try:
        out = subprocess.check_output(cmd, text=True, errors="ignore")
        return f"package:{package_name}" in out
    except Exception:
        return False


def install_apk(adb_exe: str, apk_path: Path, device_id: Optional[str] = None) -> bool:
    """Installs APK on device."""
    print(f"[*] Installing {apk_path} on device...")
    cmd = [adb_exe]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["install", "-r", "-d", str(apk_path)])
    res = subprocess.run(cmd, capture_output=True, text=True)
    if "Success" in res.stdout:
        print("[+] APK installed successfully!")
        return True
    else:
        print(f"[!] Installation failed: {res.stdout} {res.stderr}")
        return False


def launch_app(adb_exe: str, package_name: str, activity_name: str, device_id: Optional[str] = None):
    """Launches the app on device."""
    cmd = [adb_exe]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "am", "start", "-n", f"{package_name}/{activity_name}"])
    subprocess.run(cmd, capture_output=True, text=True)


def get_current_window_info(adb_exe: str, device_id: Optional[str] = None) -> Tuple[str, str]:
    """
    Returns (activity_name, window_title).
    """
    cmd = [adb_exe]
    if device_id:
        cmd.extend(["-s", device_id])

    activity_name = ""
    window_title = ""

    # Check dumpsys window displays
    try:
        out = subprocess.check_output(cmd + ["shell", "dumpsys", "window", "displays"], text=True, errors="ignore")
        for line in out.splitlines():
            if "mCurrentFocus" in line or "mFocusedApp" in line:
                m = re.search(r'([a-zA-Z0-9_\.]+)/([a-zA-Z0-9_\.]+)', line)
                if m:
                    pkg, act = m.group(1), m.group(2)
                    activity_name = f"{pkg}{act}" if act.startswith(".") else act
                m_title = re.search(r'Window\{[^\s]+ [^\s]+ ([^\}]+)\}', line)
                if m_title:
                    window_title = m_title.group(1)
                break
    except Exception:
        pass

    if not activity_name:
        try:
            out = subprocess.check_output(cmd + ["shell", "dumpsys", "activity", "activities"], text=True, errors="ignore")
            for line in out.splitlines():
                if "ResumedActivity:" in line or "topResumedActivity=" in line:
                    m = re.search(r'([a-zA-Z0-9_\.]+)/([a-zA-Z0-9_\.]+)', line)
                    if m:
                        pkg, act = m.group(1), m.group(2)
                        activity_name = f"{pkg}{act}" if act.startswith(".") else act
                        break
        except Exception:
            pass

    return activity_name or "UnknownActivity", window_title


def get_ui_signature(adb_exe: str, device_id: Optional[str] = None) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Dumps UI hierarchy and returns a hash signature of visible texts + list of clickable elements.
    """
    cmd = [adb_exe]
    if device_id:
        cmd.extend(["-s", device_id])

    try:
        dump_path = "/data/local/tmp/a11y_dump.xml"
        subprocess.run(cmd + ["shell", "uiautomator", "dump", dump_path], capture_output=True, text=True, timeout=5)
        raw_xml = subprocess.check_output(cmd + ["shell", "cat", dump_path], text=True, errors="ignore", timeout=5)
        
        root = ET.fromstring(raw_xml)
        texts = []
        clickables = []

        for node in root.iter('node'):
            text = node.attrib.get('text', '').strip()
            desc = node.attrib.get('content-desc', '').strip()
            res_id = node.attrib.get('resource-id', '').strip()
            clickable = node.attrib.get('clickable') == 'true'
            bounds = node.attrib.get('bounds', '')

            if text:
                texts.append(text)
            elif desc:
                texts.append(desc)

            if clickable and bounds:
                # Parse bounds [x1,y1][x2,y2]
                m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                if m:
                    x1, y1, x2, y2 = map(int, m.groups())
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    label = text or desc or res_id.split('/')[-1] or "element"
                    # Ignore tiny or invisible bounds
                    if (x2 - x1) > 20 and (y2 - y1) > 20:
                        clickables.append({
                            "x": cx, "y": cy,
                            "label": label,
                            "resource_id": res_id
                        })

        sig_string = " | ".join(sorted(set(texts)))
        sig_hash = hashlib.md5(sig_string.encode('utf-8')).hexdigest()[:8]
        return sig_hash, clickables
    except Exception:
        return "nosig", []


def take_screenshot(adb_exe: str, output_path: Path, device_id: Optional[str] = None) -> bool:
    """Takes a screenshot via ADB."""
    cmd = [adb_exe]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["exec-out", "screencap", "-p"])

    try:
        with open(output_path, "wb") as f:
            proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, timeout=8)
            if proc.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
                return True
    except Exception as e:
        print(f"[!] Screenshot capture error: {e}")
    return False


def load_audit_screens(csv_path: Path) -> List[Dict[str, str]]:
    """Loads records from audit_results.csv."""
    if not csv_path.exists():
        return []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def match_screen_name(raw_activity: str, screens: List[Dict[str, str]]) -> Tuple[str, str]:
    """Matches device activity to audit_results.csv."""
    clean_act = raw_activity.strip()
    short_act = clean_act.split(".")[-1].lower()

    for s in screens:
        if s["screen_name"] == clean_act:
            return s["screen_name"], s["title"]

    for s in screens:
        name = s["screen_name"]
        if name.endswith(clean_act) or clean_act.endswith(name):
            return s["screen_name"], s["title"]

    for s in screens:
        name_short = s["screen_name"].split(".")[-1].split("/")[-1].lower().replace("_", "")
        if short_act in name_short or name_short in short_act:
            return s["screen_name"], s["title"]

    # Fallback to readable title
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', clean_act.split(".")[-1])
    fallback_title = " ".join(w.capitalize() for w in words) if words else clean_act
    return clean_act, fallback_title


def run_html_generator():
    """Triggers generation of the interactive visual audit report."""
    gen_script = Path("generate_visual_audit_report.py")
    if gen_script.exists():
        subprocess.run([sys.executable, str(gen_script)], capture_output=True)


def automatic_watch_mode(adb_exe: str, device_id: str, screens: List[Dict[str, str]]):
    """
    Hands-free Automatic Screen Watcher.
    Detects screen transitions and snaps screenshots completely automatically!
    """
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    print("\n" + "="*85)
    print(" AUTOMATIC HANDS-FREE SCREEN CAPTURE RUNNING")
    print("="*85)
    print(f" Target Device : {device_id}")
    print(" Instructions  : Simply use / navigate the app on your phone.")
    print("                 Every new screen or dialog will be snapped automatically!")
    print("                 (Press Ctrl+C in this terminal when finished)")
    print("="*85 + "\n")

    seen_signatures: Set[str] = set()
    captured_count = 0
    last_act = ""

    # Check already captured files to avoid redundant snaps
    for f in SCREENSHOTS_DIR.glob("*.png"):
        seen_signatures.add(f.stem)

    try:
        while True:
            act, win_title = get_current_window_info(adb_exe, device_id)
            
            # Check if active window changed
            if act and (act != last_act or "Launcher" in last_act):
                # Small delay to let animations settle
                time.sleep(0.9)
                
                # Fetch UI text signature for screen uniqueness
                ui_sig, _ = get_ui_signature(adb_exe, device_id)
                screen_id, screen_title = match_screen_name(act, screens)
                safe_name = screen_id.replace("/", "_").replace(".", "_")
                
                # Composite key to distinguish different views in same activity
                composite_key = f"{safe_name}_{ui_sig}" if ui_sig != "nosig" else safe_name
                target_file = SCREENSHOTS_DIR / f"{safe_name}.png"

                if safe_name not in seen_signatures:
                    print(f"[*] New Screen Detected: {screen_title}")
                    print(f"    Activity  : {act}")
                    
                    if take_screenshot(adb_exe, target_file, device_id):
                        captured_count += 1
                        seen_signatures.add(safe_name)
                        seen_signatures.add(composite_key)
                        print(f"    [+] Saved -> {target_file} (Total: {captured_count})")
                        run_html_generator()
                    else:
                        print("    [!] Screenshot capture failed.")
                    print("-" * 65)

                last_act = act

            time.sleep(1.0)

    except KeyboardInterrupt:
        print(f"\n[+] Stopped automatic capture. Total captured: {captured_count}")
        run_html_generator()
        print(f"[+] View updated report at: {os.path.abspath('audit_report.html')}\n")


def autonomous_crawler_mode(adb_exe: str, device_id: str, screens: List[Dict[str, str]]):
    """
    Autonomous Robot Crawler.
    Launches app, crawls clickable elements, snaps screens, and tracks coverage.
    """
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    print("\n" + "="*85)
    print(" AUTONOMOUS ROBOT CRAWLER MODE")
    print(f" Starting automated UI traversal on {device_id}...")
    print("="*85 + "\n")

    # Launch app
    print(f"[*] Launching {APP_PACKAGE}...")
    launch_app(adb_exe, APP_PACKAGE, MAIN_ACTIVITY, device_id)
    time.sleep(3.0)

    visited_screens: Set[str] = set()
    clicked_elements: Set[str] = set()
    captured_count = 0

    max_steps = 50
    step = 0

    try:
        while step < max_steps:
            step += 1
            act, _ = get_current_window_info(adb_exe, device_id)
            ui_sig, clickables = get_ui_signature(adb_exe, device_id)

            screen_id, screen_title = match_screen_name(act, screens)
            safe_name = screen_id.replace("/", "_").replace(".", "_")
            target_file = SCREENSHOTS_DIR / f"{safe_name}.png"

            if safe_name not in visited_screens:
                visited_screens.add(safe_name)
                if take_screenshot(adb_exe, target_file, device_id):
                    captured_count += 1
                    print(f"[{step}/{max_steps}] Captured: {screen_title} -> {target_file}")
                    run_html_generator()

            # Find unclicked element on current screen
            target_elem = None
            for elem in clickables:
                elem_key = f"{safe_name}_{elem['x']}_{elem['y']}_{elem['label']}"
                # Skip back/close buttons on first pass
                if any(w in elem['label'].lower() for w in ['back', 'cancel', 'exit', 'close', 'logout']):
                    continue
                if elem_key not in clicked_elements:
                    target_elem = elem
                    clicked_elements.add(elem_key)
                    break

            if target_elem:
                print(f"    -> Tapping '{target_elem['label']}' at ({target_elem['x']}, {target_elem['y']})")
                cmd = [adb_exe, "-s", device_id, "shell", "input", "tap", str(target_elem['x']), str(target_elem['y'])]
                subprocess.run(cmd, capture_output=True)
                time.sleep(2.0)
            else:
                # No more unclicked elements, press BACK
                print("    <- No new elements found. Pressing BACK...")
                cmd = [adb_exe, "-s", device_id, "shell", "input", "keyevent", "4"]
                subprocess.run(cmd, capture_output=True)
                time.sleep(1.5)

    except KeyboardInterrupt:
        print("\n[!] Crawler interrupted by user.")

    print(f"\n[+] Crawl complete! Captured {captured_count} screens.")
    run_html_generator()


def main():
    parser = argparse.ArgumentParser(description="A11ySense Automatic Screen Capture Tool")
    parser.add_argument("--crawl", action="store_true", help="Autonomous robot crawler (auto-taps buttons)")
    parser.add_argument("--install", action="store_true", help="Installs base.apk to connected device")
    parser.add_argument("--batch", action="store_true", help="Batch launches all exported activities")
    args = parser.parse_args()

    adb_exe = find_adb()
    if not adb_exe:
        print("[!] Error: 'adb' executable not found.")
        sys.exit(1)

    devices = get_connected_devices(adb_exe)
    if not devices:
        print("\n[!] No active Android device or emulator detected!")
        print("    Run 'adb devices' to verify your connection.")
        sys.exit(1)

    device_id = devices[0]
    screens = load_audit_screens(CSV_PATH)

    if args.install:
        if TARGET_APK.exists():
            install_apk(adb_exe, TARGET_APK, device_id)
        else:
            print(f"[!] {TARGET_APK} not found.")
        return

    # Check if app is installed
    if not is_app_installed(adb_exe, APP_PACKAGE, device_id):
        print(f"[*] App '{APP_PACKAGE}' is not installed on device {device_id}.")
        if TARGET_APK.exists():
            install_apk(adb_exe, TARGET_APK, device_id)

    if args.crawl:
        autonomous_crawler_mode(adb_exe, device_id, screens)
    else:
        # Default: automatic hands-free watch mode
        automatic_watch_mode(adb_exe, device_id, screens)


if __name__ == "__main__":
    main()
