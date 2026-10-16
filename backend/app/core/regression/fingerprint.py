"""
Stable defect fingerprints for regression matching.

Why this exists
---------------
The old fingerprint hashed the raw HTML snippet (aria-label, href, text...) of the failing
element.  Components that render LIVE DATA (stock tickers, prices, % change, recommendation
cards) change that text on every scan, so the same component looked "Fixed" in one run and
"New" in the next.

The fingerprint built here identifies a defect by *what kind of component it is* and not by
the data it currently shows:

    rule id | page path | tag | role | sorted attribute NAMES | normalized accessible name
    | normalized href | landmark text (optional)

Generated CSS classes, inline styles and other volatile attributes are ignored, and live
data inside names (prices, %, numbers, trend words, entity names of repeating card templates)
is replaced by placeholder tokens.  All patterns live in ``normalization_rules.json`` so they
can be extended without code changes.

Several elements can legitimately share one fingerprint (e.g. 6 ticker cards failing the same
rule).  Those form a *group*; ``matcher.match_groups`` compares group COUNTS between runs.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

RULES_ENV_VAR = "A11YSENSE_NORMALIZATION_RULES"
DEFAULT_RULES_PATH = os.path.join(os.path.dirname(__file__), "normalization_rules.json")

_PLACEHOLDER_RE = re.compile(r"<(?!entity>)[a-z]+>")
# Tokens that prove LIVE data was normalized away (plain <num>/<n>/<m> may just be static digits).
_LIVE_DATA_RE = re.compile(r"<(?:entity|price|pct|trend)>")


# ── Rule set (loaded from JSON config) ────────────────────────────────────────

class RuleSet:
    """Compiled view of normalization_rules.json."""

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.ignored_attributes = {a.lower() for a in cfg.get("ignored_attributes", [])}
        self.include_criterion = bool(cfg.get("include_criterion_in_fingerprint", False))
        self.max_name_length = int(cfg.get("max_name_length", 120))
        self.max_text_name_length = int(cfg.get("max_text_name_length", 40))
        self.container_tags_ignore_text = {t.lower() for t in cfg.get("container_tags_ignore_text", [])}
        self.text_rules: List[Tuple[re.Pattern, str]] = [
            (re.compile(r["pattern"], re.IGNORECASE), r["replacement"])
            for r in cfg.get("dynamic_text_rules", [])
        ]

        ent = cfg.get("entity", {})
        self.entity_enabled = bool(ent.get("enabled", True))
        self.entity_prefix_re = re.compile(ent.get("prefix_pattern", r"^$"))
        self.entity_separator = ent.get("separator", ",")
        self.entity_min_repeats = int(ent.get("min_repeats", 3))
        self.entity_require_dynamic = bool(ent.get("require_dynamic_token", True))
        self.list_tags = {t.lower() for t in ent.get("list_tags", [])}
        self.list_roles = {r.lower() for r in ent.get("list_roles", [])}
        self.list_class_hints = [h.lower() for h in ent.get("list_class_hints", [])]
        self.ordinal_is_list_hint = bool(ent.get("ordinal_is_list_hint", True))

        href = cfg.get("href", {})
        self.href_prefixes = [p.lower() for p in href.get("dynamic_prefixes", [])]
        self.href_rules: List[Tuple[re.Pattern, str]] = [
            (re.compile(r["pattern"], re.IGNORECASE), r["replacement"]) for r in href.get("rules", [])
        ]


_rules_cache: Optional[RuleSet] = None


def load_rules(path: Optional[str] = None) -> RuleSet:
    path = path or os.environ.get(RULES_ENV_VAR) or DEFAULT_RULES_PATH
    with open(path, "r", encoding="utf-8") as fh:
        return RuleSet(json.load(fh))


def get_rules() -> RuleSet:
    global _rules_cache
    if _rules_cache is None:
        _rules_cache = load_rules()
    return _rules_cache


def reset_rules_cache() -> None:
    global _rules_cache
    _rules_cache = None


# ── URL helpers ───────────────────────────────────────────────────────────────

def normalize_url(url: str) -> str:
    """Normalize a page URL for comparison across scans (no scheme, query, fragment, trailing /)."""
    if not url:
        return ""
    clean = url.strip().split("?")[0].split("#")[0].lower().rstrip("/")
    for prefix in ("https://", "http://"):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    return clean


def normalize_href(href: str, rules: Optional[RuleSet] = None) -> str:
    """Normalize an href; last path segment of known dynamic lists becomes '*' (/stocks/* )."""
    rules = rules or get_rules()
    href = (href or "").strip()
    if not href or href.startswith("#"):
        return ""
    low = href.lower()
    if low.startswith("javascript:"):
        return "javascript:"
    try:
        parts = urlsplit(href)
    except ValueError:
        return low.split("?")[0].split("#")[0]
    if parts.scheme in ("mailto", "tel"):
        return f"{parts.scheme}:{parts.path.lower()}"
    path = parts.path or "/"
    for prefix in rules.href_prefixes:
        if path.lower().startswith(prefix) and len(path) > len(prefix):
            path = prefix + "*"
            break
    path = path.rstrip("/") or "/"
    for pattern, repl in rules.href_rules:
        path = pattern.sub(repl, path)
    host = parts.netloc.lower()
    return f"{host}{path}".lower()


# ── Dynamic text normalization ────────────────────────────────────────────────

def _collapse(text: str) -> str:
    return " ".join((text or "").split())


def _entity_split(base: str, rules: RuleSet) -> Optional[Tuple[str, str, str]]:
    """
    Split an already-normalized label into (prefix, entity, rest), or None if it does not look
    like '<entity>, <data...>'.

    The entity is everything before the separator that precedes the first dynamic token
    ('tata motors, ltd, price <price>' -> entity 'tata motors, ltd').
    """
    if not rules.entity_enabled or not base:
        return None
    sep = rules.entity_separator
    m = rules.entity_prefix_re.match(base)
    prefix = m.group(0) if m else ""
    body = base[len(prefix):]

    first = body.find(sep)
    if first <= 0:
        return None
    token = _PLACEHOLDER_RE.search(body, first)
    if token:
        end = body.rfind(sep, 0, token.start())
    elif prefix:
        end = first  # ordinal prefix ("Stock <N> of <M>:") is itself the dynamic signal
    else:
        return None
    if end <= 0:
        return None

    entity, rest = body[:end].strip(), body[end:]
    if not entity or not rest.strip(sep + " "):
        return None
    return prefix, entity, rest


def _entity_shape(base: str, rules: RuleSet) -> Optional[str]:
    parts = _entity_split(base, rules)
    if not parts:
        return None
    prefix, _entity, rest = parts
    shape = f"{prefix}<entity>{rest}"
    if rules.entity_require_dynamic and not _PLACEHOLDER_RE.search(shape):
        return None
    return shape


def normalize_dynamic_text(text: str, is_template: bool = False, rules: Optional[RuleSet] = None) -> str:
    """
    Replace live data inside an accessible name / visible text / title so the same component
    gets the same text across runs.

      * currency amounts (₹ $ Rs ...)          -> <PRICE>
      * 'Increased/Decreased/Up/Down by 3.4%'   -> <TREND>
      * other percentages (+/-/unsigned)        -> <PCT>
      * 'Stock 1 of 5'                          -> 'stock <N> of <M>'
      * remaining numbers                       -> <NUM>
      * (is_template) entity name of a repeating card template -> <ENTITY>
      * whitespace collapsed, lowercased

    The regex list comes from normalization_rules.json.
    """
    rules = rules or get_rules()
    out = text or ""
    for pattern, repl in rules.text_rules:
        out = pattern.sub(repl, out)
    out = _collapse(out).lower()
    if is_template:
        shape = _entity_shape(out, rules)
        if shape:
            out = shape
    return out


# ── HTML snippet parsing ──────────────────────────────────────────────────────

class _FirstElementParser(HTMLParser):
    """Captures the first start tag (the failing element) and the text beneath it."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tag: Optional[str] = None
        self.attrs: Dict[str, str] = {}
        self.text: List[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if self.tag is None:
            self.tag = tag.lower()
            self.attrs = {k.lower(): (v or "") for k, v in attrs}
        elif tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self.tag is not None and not self._skip:
            self.text.append(data)


_PARTIAL_TAG_RE = re.compile(r"^\s*<([a-zA-Z][\w:-]*)(.*)$", re.DOTALL)
_ATTR_RE = re.compile(r"""([^\s"'<>/=]+)(?:\s*=\s*(?:"([^"]*)"?|'([^']*)'?|([^\s"'>]+)))?""")


@dataclass
class ParsedElement:
    tag: str
    attrs: Dict[str, str]
    text: str
    raw: str  # whitespace-collapsed source (identity of the element within a run)


def parse_element(html_or_selector: str) -> ParsedElement:
    """Parse the (possibly truncated) HTML snippet of a failing element."""
    src = html_or_selector or ""
    raw = _collapse(src)
    if "<" not in src:  # plain selector / free text / "N/A"
        return ParsedElement(tag="", attrs={}, text=raw, raw=raw)

    parser = _FirstElementParser()
    try:
        parser.feed(src)
        parser.close()
    except Exception:
        pass
    if parser.tag:
        return ParsedElement(parser.tag, parser.attrs, _collapse(" ".join(parser.text)), raw)

    # First tag itself was cut off by snippet truncation - recover what we can.
    m = _PARTIAL_TAG_RE.match(src)
    if not m:
        return ParsedElement(tag="", attrs={}, text=raw, raw=raw)
    attrs: Dict[str, str] = {}
    for am in _ATTR_RE.finditer(m.group(2).split(">")[0]):
        name = am.group(1).lower()
        attrs[name] = am.group(2) or am.group(3) or am.group(4) or ""
    return ParsedElement(m.group(1).lower(), attrs, "", raw)


def _name_source(el: ParsedElement, rules: RuleSet) -> Tuple[str, str]:
    """
    Accessible-name candidate in priority order: aria-label, visible text, title, alt.

    Returns (value, kind).  Visible text of container tags (nav, div, ul ...) is ignored: it is
    the (truncated) content of the whole subtree, not the name of the element.
    """
    candidates = [
        (el.attrs.get("aria-label"), "label"),
        (None if el.tag in rules.container_tags_ignore_text else el.text, "text"),
        (el.attrs.get("title"), "title"),
        (el.attrs.get("alt"), "alt"),
    ]
    for value, kind in candidates:
        if value and value.strip():
            return value, kind
    return "", ""


def _is_list_hint(el: ParsedElement, has_ordinal_prefix: bool, rules: RuleSet) -> bool:
    """Is the element visibly part of a list/carousel/grid rendered from data?"""
    if el.tag in rules.list_tags:
        return True
    if el.attrs.get("role", "").strip().lower() in rules.list_roles:
        return True
    cls = el.attrs.get("class", "").lower()
    if cls and any(h in cls for h in rules.list_class_hints):
        return True
    if has_ordinal_prefix and rules.ordinal_is_list_hint:
        return True
    href_path = (el.attrs.get("href") or "").lower()
    if href_path:
        try:
            path = urlsplit(href_path).path
        except ValueError:
            path = href_path
        if any(path.startswith(p) and len(path) > len(p) for p in rules.href_prefixes):
            return True
    return False


# ── Fingerprinting ────────────────────────────────────────────────────────────

@dataclass
class FingerprintResult:
    fp: str               # 40-char sha1 of the stable identity (shared by the whole group)
    occurrence: int       # 0-based index among elements with the same fp in this batch
    dynamic: bool         # True if live data was normalized away (name changed by the rules)
    page: str             # normalized page url
    name: str             # normalized accessible name used in the hash


def _compose(rule_id: str, criterion: str, page: str, el: ParsedElement, name: str,
             landmark: str, rules: RuleSet) -> str:
    attr_names = sorted(a for a in el.attrs if a not in rules.ignored_attributes)
    parts = [
        "v2",
        (rule_id or "").strip().lower(),
        criterion if rules.include_criterion else "",
        page,
        el.tag,
        el.attrs.get("role", "").strip().lower(),
        ",".join(attr_names),
        name,
        normalize_href(el.attrs.get("href", ""), rules),
        _collapse(landmark).lower(),
    ]
    return "|".join(parts)


def fingerprint_batch(records: List[Dict[str, Any]], rules: Optional[RuleSet] = None) -> List[FingerprintResult]:
    """
    Fingerprint a batch of failing elements (all rules, all pages of one side of a comparison).

    Each record: ``rule_id``, ``html`` (snippet or selector), ``page_url`` and optionally
    ``criteria`` ("2.4.3 Focus Order") and ``landmark`` (nearest landmark/heading text).

    The batch is needed to detect repeating templates: a label shape such as
    '<ENTITY>, price <PRICE>, <TREND>, view details' that is seen on 3+ distinct elements of a
    page is a data template, so its entity name is normalized too.
    """
    rules = rules or get_rules()

    prepared = []
    for rec in records:
        el = parse_element(rec.get("html") or "")
        src, kind = _name_source(el, rules)
        base = normalize_dynamic_text(src, False, rules)
        if kind == "text":
            base = base[: rules.max_text_name_length]
        prepared.append((rec, el, src, base, _entity_shape(base, rules)))

    distinct: Dict[Tuple[str, str], set] = defaultdict(set)
    for rec, el, _src, _base, shape in prepared:
        if shape:
            distinct[(normalize_url(rec.get("page_url") or ""), shape)].add(el.raw)

    occurrences: Dict[str, int] = defaultdict(int)
    results: List[FingerprintResult] = []
    for rec, el, src, base, shape in prepared:
        page = normalize_url(rec.get("page_url") or "")
        name = base
        if shape:
            ordinal_prefix = bool(rules.entity_prefix_re.match(base))
            repeating = len(distinct[(page, shape)]) >= rules.entity_min_repeats
            if repeating or _is_list_hint(el, ordinal_prefix, rules):
                name = shape
        name = name[: rules.max_name_length]

        criterion = ((rec.get("criteria") or "").split(" ")[0]).strip()
        raw = _compose(rec.get("rule_id", ""), criterion, page, el, name, rec.get("landmark") or "", rules)
        fp = hashlib.sha1(raw.encode("utf-8")).hexdigest()

        idx = occurrences[fp]
        occurrences[fp] += 1
        results.append(FingerprintResult(
            fp=fp,
            occurrence=idx,
            dynamic=bool(_LIVE_DATA_RE.search(name)),
            page=page,
            name=name,
        ))
    return results


def compute_fingerprint(rule_id: str, html_or_selector: str, page_url: str,
                        criteria: str = "", landmark: str = "") -> str:
    """Stable fingerprint of one failing element (see module docstring)."""
    return fingerprint_batch([{
        "rule_id": rule_id,
        "html": html_or_selector,
        "page_url": page_url,
        "criteria": criteria,
        "landmark": landmark,
    }])[0].fp


def compute_loose_fingerprint(rule_id: str, page_url: str, role_or_name: str) -> str:
    """Loose fingerprint: rule + page + normalized role/name (kept for display/diagnostics)."""
    norm_rule = (rule_id or "").strip().lower()
    norm_url = normalize_url(page_url)
    norm_name = normalize_dynamic_text(role_or_name or "")
    return hashlib.sha1(f"{norm_rule}|{norm_url}|{norm_name}".encode("utf-8")).hexdigest()
