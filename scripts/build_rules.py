#!/usr/bin/env python3
"""Fetch Sukka rules, normalize them, merge categories, and write text inputs.

The output is intentionally kept in mihomo's plain text rule-provider format.
Compilation to MRS is a separate adapter so other output formats can be added
without changing source fetching or normalization.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


DOMAIN_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-WILDCARD"}
IP_TYPES = {"IP-CIDR", "IP-CIDR6", "IP-SUFFIX"}
CIDR_RE = re.compile(r"^[0-9a-fA-F:.]+/[0-9]{1,3}$")


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "skk-merged-rules/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8-sig")


def lines(text: str):
    for number, raw in enumerate(text.splitlines(), 1):
        value = raw.strip()
        if not value or value.startswith(("#", ";", "//")):
            continue
        yield number, value


def normalize_domain(value: str, source: str, line_no: int, logger: logging.Logger) -> str | None:
    fields = [field.strip() for field in value.split(",")]
    if len(fields) == 1:
        # domainset files are already in mihomo domain-provider syntax.
        return fields[0].strip("\"'")
    rule_type = fields[0].upper()
    if rule_type not in DOMAIN_TYPES or len(fields) < 2 or not fields[1]:
        logger.warning("unconvertible domain rule %s:%d: %s", source, line_no, value)
        return None
    domain = fields[1].strip().strip("\"'").lower().rstrip(".")
    if rule_type == "DOMAIN-SUFFIX":
        # `+.` retains the DOMAIN-SUFFIX behavior, including the apex domain.
        return "+." + domain
    if rule_type == "DOMAIN-WILDCARD":
        return domain
    return domain


def normalize_ip(value: str, source: str, line_no: int, logger: logging.Logger) -> str | None:
    fields = [field.strip() for field in value.split(",")]
    if len(fields) == 1 and CIDR_RE.match(fields[0]):
        return fields[0]
    if len(fields) >= 2 and fields[0].upper() in IP_TYPES and CIDR_RE.match(fields[1]):
        return fields[1]
    logger.warning("unconvertible ip rule %s:%d: %s", source, line_no, value)
    return None


def build(kind: str, config: dict, root: Path, logger: logging.Logger) -> None:
    base_url = config["base_url"].rstrip("/")
    output = root / "data" / kind
    output.mkdir(parents=True, exist_ok=True)
    for category, sources in config[kind].items():
        values: set[str] = set()
        for relative in sources:
            url = f"{base_url}/{relative}"
            try:
                payload = fetch(url)
            except (urllib.error.URLError, TimeoutError) as exc:
                logger.error("failed to fetch %s: %s", url, exc)
                raise
            for number, value in lines(payload):
                normalized = (normalize_domain if kind == "domain" else normalize_ip)(
                    value, relative, number, logger
                )
                if normalized:
                    values.add(normalized)
        destination = output / f"{category}.txt"
        destination.write_text("\n".join(sorted(values, key=lambda item: (item.lstrip("+."), item))) + "\n", encoding="utf-8")
        logger.info("%s/%s: %d rules", kind, category, len(values))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="sources.json")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    root = Path(args.root).resolve()
    config = json.loads((root / args.config).read_text(encoding="utf-8"))
    build("domain", config, root, logging.getLogger("domain"))
    build("ip", config, root, logging.getLogger("ip"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
