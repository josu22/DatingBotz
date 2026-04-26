"""
Versión mayor de Chrome instalada (alinear ChromeDriver sin depender del canal Stable remoto).
"""
import os
import re
import shutil
import subprocess
from typing import Optional


def detect_installed_chrome_major() -> Optional[int]:
    """
    Devuelve la versión mayor de Chrome instalada (ej. 146).
    Windows: lee el registro (no ejecuta chrome.exe).
    Otros SO: intenta chrome/chromium --version.
    """
    if os.name == "nt":
        v = _chrome_major_from_windows_registry()
        if v is not None:
            return v
    return _chrome_major_from_cli()


def _chrome_major_from_windows_registry() -> Optional[int]:
    try:
        import winreg
    except ImportError:
        return None
    keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon"),
    ]
    for hive, subkey in keys:
        try:
            with winreg.OpenKey(hive, subkey) as k:
                version, _ = winreg.QueryValueEx(k, "version")
            if isinstance(version, str):
                m = re.match(r"^(\d+)\.", version.strip())
                if m:
                    return int(m.group(1))
        except OSError:
            continue
    return None


def _chrome_major_from_cli() -> Optional[int]:
    candidates = []
    if os.name == "nt":
        for key in ("PROGRAMFILES", "PROGRAMFILES(X86)"):
            base = os.environ.get(key, "")
            if base:
                p = os.path.join(base, "Google", "Chrome", "Application", "chrome.exe")
                if p not in candidates:
                    candidates.append(p)
        la = os.environ.get("LOCALAPPDATA", "")
        if la:
            p = os.path.join(la, "Google", "Chrome", "Application", "chrome.exe")
            if p not in candidates:
                candidates.append(p)
    else:
        for name in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium"):
            w = shutil.which(name)
            if w:
                candidates.append(w)
                break

    run_kw = dict(capture_output=True, text=True, timeout=15)
    if os.name == "nt":
        run_kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    for chrome in candidates:
        if not chrome or not os.path.isfile(chrome):
            continue
        try:
            out = subprocess.run([chrome, "--version"], **run_kw)
            text = (out.stdout or "") + (out.stderr or "")
            m = re.search(r"(?:Chrome|Chromium)\s+(\d+)\.", text, re.IGNORECASE)
            if m:
                return int(m.group(1))
        except Exception:
            continue
    return None


def parse_browser_major_from_session_error(message: str) -> Optional[int]:
    """
    Extrae la versión mayor del navegador desde el mensaje de SessionNotCreatedException.
    Ej.: 'Current browser version is 146.0.7680.165' -> 146
    """
    if not message:
        return None
    m = re.search(
        r"Current browser version is (\d+)\.",
        message,
        re.IGNORECASE,
    )
    if m:
        return int(m.group(1))
    return None
