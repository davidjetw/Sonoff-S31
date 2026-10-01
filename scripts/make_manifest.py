"""Package an ESPHome OTA binary and its real checksum for GitHub Pages."""
import argparse
from datetime import date
import hashlib
import html
import json
import re
import shutil
from pathlib import Path


def validate_version(version: str) -> str:
    match = re.fullmatch(r"([0-9]{2})[.]([0-9]{2})[.]([0-9]{2})[+]([1-9][0-9]*)", version)
    if not match:
        raise ValueError("Use YY.MM.DD+REVISION, e.g. 26.10.02+1")
    year, month, day, _ = map(int, match.groups())
    date(2000 + year, month, day)
    return version


def package(binary: Path, version: str, output: Path) -> dict:
    validate_version(version)
    data = binary.read_bytes()
    if len(data) < 1024 or data[0] != 0xE9:
        raise ValueError("Expected an uncompressed ESP8266 OTA image (magic 0xE9)")
    firmware_dir = output / "firmware"
    firmware_dir.mkdir(parents=True, exist_ok=True)
    filename = f"sonoff-s31-{version}.ota.bin"
    shutil.copyfile(binary, firmware_dir / filename)
    manifest = {
        "name": "Sonoff S31",
        "version": version,
        "builds": [{
            "chipFamily": "ESP8266",
            "ota": {
                "path": filename,
                "md5": hashlib.md5(data).hexdigest(),
                "summary": f"Sonoff S31 firmware {version}",
            },
        }],
    }
    (firmware_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (firmware_dir / "firmware.md5").write_text(
        manifest["builds"][0]["ota"]["md5"] + "\n", encoding="ascii"
    )
    (output / ".nojekyll").touch()
    (output / "index.html").write_text(
        '<!doctype html><html lang="zh-Hant"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Sonoff S31 OTA</title><body><h1>Sonoff S31 OTA</h1>'
        f'<p>Firmware version: {html.escape(version)}</p>'
        '<p><a href="firmware/manifest.json">OTA manifest</a></p>'
        f'<p><a href="firmware/{filename}">OTA firmware</a></p>'
        '<p>Use Home Assistant to install an update. This page does not flash devices.</p>'
        '</body></html>', encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", default="site", type=Path)
    args = parser.parse_args()
    result = package(args.binary, args.version, args.output)
    print(json.dumps(result, indent=2))
