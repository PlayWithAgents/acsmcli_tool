#!/usr/bin/env python3
"""Small ACSM helper CLI prototype.

This tool intentionally focuses on reading ACSM metadata and performing a
straightforward fulfillment request to the URL encoded in the ACSM file.
It does not attempt DRM removal or decryption.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


NS = {
    "adept": "http://ns.adobe.com/adept",
}


@dataclass
class AcsmDocument:
    path: Path
    fulfillment_url: str
    download_type: Optional[str]
    resource_item_info: Optional[str]


def _find_text(root: ET.Element, xpath: str) -> Optional[str]:
    node = root.find(xpath, NS)
    if node is None:
        return None
    text = (node.text or "").strip()
    return text if text else None


def parse_acsm(path: Path) -> AcsmDocument:
    root = ET.fromstring(path.read_text(encoding="utf-8"))

    fulfillment_url = _find_text(root, ".//adept:operatorURL")
    if fulfillment_url is None:
        fulfillment_url = _find_text(root, ".//adept:fulfillmentURL")
    if fulfillment_url is None:
        raise ValueError("Could not find operatorURL/fulfillmentURL in ACSM file")

    download_type = _find_text(root, ".//adept:downloadType")
    resource_item_info = _find_text(root, ".//adept:resourceItemInfo")

    return AcsmDocument(
        path=path,
        fulfillment_url=fulfillment_url,
        download_type=download_type,
        resource_item_info=resource_item_info,
    )


def infer_output_path(input_path: Path, content_type: str | None) -> Path:
    if content_type:
        ct = content_type.lower()
        if "epub" in ct:
            return input_path.with_suffix(".epub")
        if "pdf" in ct:
            return input_path.with_suffix(".pdf")

    return input_path.with_suffix(".bin")


def request_fulfillment(url: str, timeout: int = 30) -> tuple[bytes, Optional[str]]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "acsmcli-prototype/0.1",
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = resp.read()
        return payload, resp.headers.get("Content-Type")


def cmd_info(args: argparse.Namespace) -> int:
    doc = parse_acsm(Path(args.acsm_file))
    output = {
        "acsm_file": str(doc.path),
        "fulfillment_url": doc.fulfillment_url,
        "download_type": doc.download_type,
        "resource_item_info": doc.resource_item_info,
    }
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"ACSM file: {output['acsm_file']}")
        print(f"Fulfillment URL: {output['fulfillment_url']}")
        print(f"Download type: {output['download_type'] or 'unknown'}")
        print(f"Resource info present: {'yes' if output['resource_item_info'] else 'no'}")
    return 0


def cmd_fulfill(args: argparse.Namespace) -> int:
    doc = parse_acsm(Path(args.acsm_file))

    if args.dry_run:
        print("Dry run: would request fulfillment from")
        print(doc.fulfillment_url)
        return 0

    payload, content_type = request_fulfillment(doc.fulfillment_url, timeout=args.timeout)

    out_path = Path(args.output) if args.output else infer_output_path(Path(args.acsm_file), content_type)
    out_path.write_bytes(payload)

    print(f"Saved fulfillment payload to: {out_path}")
    print(f"Content-Type: {content_type or 'unknown'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="acsmcli",
        description="Prototype helper for reading ACSM metadata and requesting fulfillment payloads.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_info = sub.add_parser("info", help="Read ACSM metadata")
    p_info.add_argument("acsm_file", help="Path to the .acsm file")
    p_info.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    p_info.set_defaults(func=cmd_info)

    p_fulfill = sub.add_parser("fulfill", help="Request and save fulfillment payload")
    p_fulfill.add_argument("acsm_file", help="Path to the .acsm file")
    p_fulfill.add_argument("-o", "--output", help="Output path for saved payload")
    p_fulfill.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    p_fulfill.add_argument("--dry-run", action="store_true", help="Do not send network requests")
    p_fulfill.set_defaults(func=cmd_fulfill)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except ET.ParseError as exc:
        print(f"Invalid ACSM XML: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except urllib.error.URLError as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
