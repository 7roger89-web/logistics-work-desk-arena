"""Live FX sources adapters (BOC, Agribank, BIDV).

Each adapter:
 - parses a given HTML/text offline (no network required for unit tests)
 - fetches live via urllib when possible, but fails closed with RATE_UNAVAILABLE
 - preserves source URL, publication time, captured time, and distinguishes MANUAL

Spec details:
 - BOC USD→CNY: https://www.boc.cn/sourcedb/whpj/enindex_1619.html
   BOC publishes per 100 units. usd_to_cny = Buying Rate / 100
   Preserve Buying Rate, Cash Buying Rate, Selling Rate, Cash Selling Rate,
   Middle Rate, Pub Time, source URL, captured time. Do not use Middle Rate as business conversion rate.

 - Agribank USD/VND SELL: https://www.agribank.com.vn/vn/ty-gia
   Extract USD → Giá bán (sell). Preserve source and publication/capture time.

 - BIDV: https://bidv.com.vn/vn/ty-gia-ngoai-te/
   Visible page uses dynamic data source. Find and use only OFFICIAL BIDV public
   data path behind that page. If official-source extraction cannot be proven,
   BIDV_RATE_STATUS=UNAVAILABLE and keep manual entry.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

BOC_URL = "https://www.boc.cn/sourcedb/whpj/enindex_1619.html"
AGRIBANK_URL = "https://www.agribank.com.vn/vn/ty-gia"
BIDV_URL = "https://bidv.com.vn/vn/ty-gia-ngoai-te/"

# Candidate official BIDV API paths (if page uses JSON)
BIDV_API_CANDIDATES = [
    "https://bidv.com.vn/ServicesBIDV/HomeExchangeRate",
    "https://bidv.com.vn/ServicesBIDV/ExchangeRate",
    "https://bidv.com.vn/api/tygia",
    "https://bidv.com.vn/vn/ty-gia-ngoai-te/api",
    "https://openapi.bidv.com.vn/exchange-rates",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_number(txt: str) -> str:
    # Remove commas, spaces, non-breaking spaces
    s = txt.strip().replace(",", "").replace(" ", "").replace("\xa0", "")
    # keep decimal dot
    return s


def _parse_decimal(txt: str) -> Decimal | None:
    s = _clean_number(txt)
    if not s or s == "-" or s.lower() == "nan":
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


def _extract_pub_time_boc(html: str) -> str | None:
    # Pub Time looks like 2026/09/23 18:40:28
    m = re.search(r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})", html)
    if m:
        return m.group(1)
    return None


def _is_valid_boc_pub_time(txt: str | None) -> bool:
    if not txt or not isinstance(txt, str):
        return False
    # exact YYYY/MM/DD HH:MM:SS
    return bool(re.match(r"^\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}$", txt.strip()))


def _is_valid_agribank_pub_time(txt: str | None) -> bool:
    if not txt or not isinstance(txt, str):
        return False
    # expected "HH:MM ngày DD/MM/YYYY" per official page
    return bool(re.search(r"^\d{1,2}:\d{2}\s+ngày\s+\d{1,2}/\d{1,2}/\d{4}$", txt.strip()) or
                re.search(r"\d{1,2}:\d{2}\s+ngày\s+\d{1,2}/\d{1,2}/\d{4}", txt))


def parse_boc_html(html: str, source_url: str = BOC_URL, captured_at: str | None = None) -> dict[str, Any]:
    """Parse BOC page HTML. Offline parser, no network required.

    Returns dict with status OK or RATE_UNAVAILABLE, and preserves all fields.
    usd_to_cny = Buying Rate /100  (per spec, not middle rate)
    """
    captured_at = captured_at or _now_iso()
    if not html or not isinstance(html, str):
        return {
            "status": "RATE_UNAVAILABLE",
            "reason": "empty_html",
            "source_url": source_url,
            "captured_at": captured_at,
            "currency": "USD",
            "usd_to_cny": None,
        }

    # Try to find USD row via regex extracting <tr>...USD...
    # Approach: find all <tr> blocks
    tr_blocks = re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.IGNORECASE | re.DOTALL)
    usd_row = None
    for block in tr_blocks:
        # extract td texts
        tds = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", block, flags=re.IGNORECASE | re.DOTALL)
        # Strip tags inside
        cleaned = []
        for td in tds:
            # remove inner tags like <a>, <img>
            inner = re.sub(r"<[^>]+>", "", td).strip()
            # decode html entities minimal
            inner = inner.replace("&nbsp;", " ").strip()
            cleaned.append(inner)
        if not cleaned:
            continue
        first = cleaned[0].strip().upper()
        # Some rows have "USD" exactly, some have "USD" with extra spaces
        if first == "USD" or first.startswith("USD "):
            # Could also have row where first is icon etc. Check length >=7 (Currency Name + 5 rates + Pub Time)
            # Header row is "Currency Name | Buying Rate | ..."
            if len(cleaned) >= 7 and "BUYING" in cleaned[1].upper():
                continue
            # need at least 7 cells: USD, buying, cash buying, selling, cash selling, middle, pub
            # But some representations have merged columns; check pattern
            # In fetched markdown, the row is "| USD | 669.64 | 669.64 | 672.45 | 672.45 | 674.68 | 2026/09/23 18:40:28 |"
            # We'll extract last 6 numeric-ish columns
            # Try to map: if len cleaned >=7:
            #   idx0 USD, idx1 buying, idx2 cash buying, idx3 selling, idx4 cash selling, idx5 middle, idx6 pub
            if len(cleaned) >= 7:
                # heuristic: check idx1 is numeric
                if _parse_decimal(cleaned[1]) is not None:
                    usd_row = cleaned
                    break
            # alternative: try to find row that starts with USD and has 6 columns after
        # also consider markdown-style fallback: lines like "| USD | 669.64 | ..."
        # Our tr_blocks may not capture markdown; also try line search
    # Fallback: search markdown table line
    if usd_row is None:
        # Try regex for "| USD | NUM | NUM | NUM | NUM | NUM | DATETIME |"
        md_pattern = r"\|\s*USD\s*\|\s*([0-9.\-,]+)\s*\|\s*([0-9.\-,]+)\s*\|\s*([0-9.\-,]+)\s*\|\s*([0-9.\-,]+)\s*\|\s*([0-9.\-,]+)\s*\|\s*([0-9/:\s]+)\s*\|"
        m = re.search(md_pattern, html, flags=re.IGNORECASE)
        if m:
            buying, cash_buying, selling, cash_selling, middle, pub = [x.strip() for x in m.groups()]
            usd_row = ["USD", buying, cash_buying, selling, cash_selling, middle, pub]
        else:
            # Try more flexible: USD row in markdown with fewer cols?
            # Search for "USD" line with numbers
            lines = html.splitlines()
            for line in lines:
                if "USD" in line.upper() and "|" in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    # parts should start with USD and contain numerics
                    if parts and parts[0].upper() == "USD" and len(parts) >= 6:
                        # parts: USD, buying, cash buying, selling, cash selling, middle, pub
                        # Adjust if pub time is combined
                        if len(parts) >= 7:
                            # ensure parts[1] numeric
                            if _parse_decimal(parts[1]) is not None:
                                usd_row = parts[:7]
                                break
                        elif len(parts) == 6:
                            # maybe missing? treat
                            usd_row = parts
                            break
    if usd_row is None:
        return {
            "status": "RATE_UNAVAILABLE",
            "reason": "USD row missing",
            "source_url": source_url,
            "captured_at": captured_at,
            "currency": "USD",
            "usd_to_cny": None,
        }

    # usd_row now should have at least 7 entries
    # Normalize: row = [USD, buying, cash_buying, selling, cash_selling, middle, pub]
    # Some rows may have missing values like "" for TWD; but for USD all present.
    try:
        buying_txt = usd_row[1] if len(usd_row) > 1 else ""
        cash_buying_txt = usd_row[2] if len(usd_row) > 2 else ""
        selling_txt = usd_row[3] if len(usd_row) > 3 else ""
        cash_selling_txt = usd_row[4] if len(usd_row) > 4 else ""
        middle_txt = usd_row[5] if len(usd_row) > 5 else ""
        pub_txt = usd_row[6] if len(usd_row) > 6 else ""
        # Pub time may also be elsewhere; fallback to global extraction
        if not pub_txt or "/" not in pub_txt:
            pub_txt = _extract_pub_time_boc(html) or pub_txt

        buying = _parse_decimal(buying_txt)
        cash_buying = _parse_decimal(cash_buying_txt)
        selling = _parse_decimal(selling_txt)
        cash_selling = _parse_decimal(cash_selling_txt)
        middle = _parse_decimal(middle_txt)

        if buying is None:
            return {
                "status": "RATE_UNAVAILABLE",
                "reason": "USD Buying Rate missing",
                "source_url": source_url,
                "captured_at": captured_at,
                "currency": "USD",
                "buying_rate": buying_txt,
                "cash_buying_rate": cash_buying_txt,
                "selling_rate": selling_txt,
                "cash_selling_rate": cash_selling_txt,
                "middle_rate": middle_txt,
                "pub_time": pub_txt,
            }

        usd_to_cny = buying / Decimal("100")

        # E — timestamp fail-closed: missing/invalid BOC Pub Time => RATE_UNAVAILABLE
        pub_valid = _is_valid_boc_pub_time(pub_txt)
        if not pub_valid:
            return {
                "status": "RATE_UNAVAILABLE",
                "reason": "BOC Pub Time missing/invalid — fail closed per issue #98",
                "source_url": source_url,
                "captured_at": captured_at,
                "currency": "USD",
                "buying_rate": buying,
                "buying_rate_raw": buying_txt,
                "cash_buying_rate": cash_buying,
                "selling_rate": selling,
                "cash_selling_rate": cash_selling,
                "middle_rate": middle,
                "pub_time": pub_txt,
                "pub_time_raw": pub_txt,
                "usd_to_cny": None,
            }

        return {
            "status": "OK",
            "currency": "USD",
            "buying_rate": buying,
            "cash_buying_rate": cash_buying,
            "selling_rate": selling,
            "cash_selling_rate": cash_selling,
            "middle_rate": middle,
            "buying_rate_raw": buying_txt,
            "cash_buying_rate_raw": cash_buying_txt,
            "selling_rate_raw": selling_txt,
            "cash_selling_rate_raw": cash_selling_txt,
            "middle_rate_raw": middle_txt,
            "pub_time": pub_txt.strip() if isinstance(pub_txt, str) else pub_txt,
            "source_url": source_url,
            "captured_at": captured_at,
            "usd_to_cny": usd_to_cny,
            "note": "Business conversion uses Buying Rate /100, not Middle Rate",
            "source": "BOC",
        }
    except Exception as exc:
        return {
            "status": "RATE_UNAVAILABLE",
            "reason": f"parse_error: {exc}",
            "source_url": source_url,
            "captured_at": captured_at,
            "currency": "USD",
        }


def parse_agribank_html(html: str, source_url: str = AGRIBANK_URL, captured_at: str | None = None) -> dict[str, Any]:
    """Parse Agribank ty gia page. Extract USD Sell (Giá bán)."""
    captured_at = captured_at or _now_iso()
    if not html or not isinstance(html, str):
        return {
            "status": "RATE_UNAVAILABLE",
            "reason": "empty_html",
            "source_url": source_url,
            "captured_at": captured_at,
            "currency": "USD",
        }

    # Extract update time: "Tỷ giá được cập nhật lúc 11:30 ngày 23/09/2026"
    pub_time = None
    m_pub = re.search(r"cập nhật lúc\s*([0-9:]+)\s*ngày\s*([0-9/]+)", html, flags=re.IGNORECASE)
    if m_pub:
        pub_time = f"{m_pub.group(1)} ngày {m_pub.group(2)}"
        pub_time_raw = m_pub.group(0)
    else:
        pub_time_raw = None
        # Try alternative: "Updated at ..." but keep none

    # Strategy: find table rows for USD
    # Markdown table like: "| USD | 25,770.00 | 25,800.00 | 26,180.00 |"
    # Need to find line containing USD
    usd_sell = None
    usd_buy_cash = None
    usd_buy_transfer = None

    # Try tr blocks first
    tr_blocks = re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.IGNORECASE | re.DOTALL)
    for block in tr_blocks:
        tds = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", block, flags=re.IGNORECASE | re.DOTALL)
        cleaned = [re.sub(r"<[^>]+>", "", td).strip().replace("\xa0", "") for td in tds]
        if not cleaned:
            continue
        # Check first cell is USD
        if cleaned[0].strip().upper() == "USD":
            # Expect 4 cols: Ngoại tệ, Mua tiền mặt, Mua CK, Giá bán
            if len(cleaned) >= 4:
                usd_buy_cash = cleaned[1]
                usd_buy_transfer = cleaned[2]
                usd_sell = cleaned[3]
                break

    if usd_sell is None:
        # Fallback markdown
        # Search for pattern "| USD | ... | ... | ... |"
        md_pat = r"\|\s*USD\s*\|\s*([0-9,.\- ]*)\s*\|\s*([0-9,.\- ]*)\s*\|\s*([0-9,.\- ]*)\s*\|"
        m = re.search(md_pat, html, flags=re.IGNORECASE)
        if m:
            usd_buy_cash, usd_buy_transfer, usd_sell = [x.strip() for x in m.groups()]
        else:
            # Try line split
            for line in html.splitlines():
                if "USD" in line.upper() and "|" in line and "Mua" not in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if parts and parts[0].upper() == "USD" and len(parts) >= 4:
                        usd_buy_cash = parts[1]
                        usd_buy_transfer = parts[2]
                        usd_sell = parts[3]
                        break
                    elif parts and parts[0].upper() == "USD" and len(parts) == 3:
                        # Maybe missing one?
                        pass

    if usd_sell is None or not _clean_number(usd_sell) or _clean_number(usd_sell) == "-":
        return {
            "status": "RATE_UNAVAILABLE",
            "reason": "USD sell row missing",
            "source_url": source_url,
            "captured_at": captured_at,
            "pub_time": pub_time,
            "pub_time_raw": pub_time_raw,
            "currency": "USD",
        }

    sell_decimal = _parse_decimal(usd_sell)
    buy_cash_decimal = _parse_decimal(usd_buy_cash) if usd_buy_cash else None
    buy_transfer_decimal = _parse_decimal(usd_buy_transfer) if usd_buy_transfer else None

    if sell_decimal is None:
        return {
            "status": "RATE_UNAVAILABLE",
            "reason": "USD sell parse invalid",
            "source_url": source_url,
            "captured_at": captured_at,
            "pub_time": pub_time,
            "pub_time_raw": pub_time_raw,
            "currency": "USD",
            "sell_raw": usd_sell,
        }
    if not _is_valid_agribank_pub_time(pub_time):
        return {
            "status": "RATE_UNAVAILABLE",
            "reason": "Agribank pub time missing/invalid — fail closed per issue #98",
            "source_url": source_url,
            "captured_at": captured_at,
            "currency": "USD",
            "pub_time": pub_time,
            "pub_time_raw": pub_time_raw,
            "sell": sell_decimal,
            "sell_raw": usd_sell,
            "usd_sell_vnd": None,
        }

    return {
        "status": "OK",
        "currency": "USD",
        "buy_cash": buy_cash_decimal,
        "buy_cash_raw": usd_buy_cash,
        "buy_transfer": buy_transfer_decimal,
        "buy_transfer_raw": usd_buy_transfer,
        "sell": sell_decimal,
        "sell_raw": usd_sell,
        "usd_sell_vnd": sell_decimal,
        "pub_time": pub_time,
        "pub_time_raw": pub_time_raw,
        "source_url": source_url,
        "captured_at": captured_at,
        "source": "Agribank",
    }


def parse_bidv_html(html: str, source_url: str = BIDV_URL, captured_at: str | None = None) -> dict[str, Any]:
    """Parse BIDV static HTML table (fallback). Extract USD Sell (Bán)."""
    captured_at = captured_at or _now_iso()
    if not html or not isinstance(html, str):
        return {
            "status": "RATE_UNAVAILABLE",
            "reason": "empty_html",
            "source_url": source_url,
            "captured_at": captured_at,
            "currency": "USD",
        }

    pub_time = None
    m_pub = re.search(r"Cập nhật lúc\s*([0-9:]+)\s*ngày\s*([0-9/]+)", html, flags=re.IGNORECASE)
    if m_pub:
        pub_time = f"{m_pub.group(1)} ngày {m_pub.group(2)}"
        pub_time_raw = m_pub.group(0)
    else:
        pub_time_raw = None

    # Try to find USD row. BIDV markdown example:
    # "| Ký hiệu ngoại tệCurrencyUSD | Tên ngoại tệCurrency nameUS DollarDollar Mỹ | Mua tiền mặt và SécBuy25,800 | Mua chuyển khoảnTransfer25,800 | BánSell26,180 |"
    # This is more complex; the raw HTML may have separate tds:
    # Instead search for USD and then "Bán" value nearby.

    # Strategy: find all lines containing USD and extract numbers after Sell
    # Simplified: regex for USD row with Sell value
    # Expect pattern: USD ... Sellxx,xxx
    # Use flexible regex
    # Look for "USD" then non-greedy until "Bán" or "Sell" then number
    usd_sell = None
    usd_buy_cash = None
    usd_buy_transfer = None

    # Try tr parsing
    tr_blocks = re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.IGNORECASE | re.DOTALL)
    found = False
    for block in tr_blocks:
        tds = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", block, flags=re.IGNORECASE | re.DOTALL)
        cleaned = [re.sub(r"<[^>]+>", "", td).strip() for td in tds]
        # Check if any cell contains USD
        joined = " ".join(cleaned).upper()
        if "USD" in joined and "KÝ HIỆU" not in joined:
            # Expect at least 5 cells: Currency, Name, Mua cash, Mua CK, Bán
            # The Bán column is last
            # Find numeric sell: last cell should contain number
            # Clean last cell: remove non-digit except . ,
            last = cleaned[-1] if cleaned else ""
            # Extract number from last cell
            num_match = re.search(r"([0-9,]+\.?[0-9]*)", last)
            candidate = num_match.group(1) if num_match else last
            # Validate: ensure first cell indicates USD (maybe "USD" or "CurrencyUSD")
            has_usd_first = any("USD" in c.upper() and ("KÝ" not in c.upper() or len(c) < 20) for c in cleaned[:2])
            # For markdown complex, first cell may be "Ký hiệu ngoại tệCurrencyUSD"
            if "USD" in last.upper() and not candidate:
                continue
            # Try to identify sell column specifically: look for cell containing Sell or Bán keyword
            # Or assume last numeric is sell
            if candidate and _parse_decimal(candidate):
                # Check that this row indeed is USD row (not EUR etc)
                # Use heuristic: if first two cells contain USD
                if any("USD" in c for c in cleaned[:2]):
                    # Now figure buy values: try to extract 3rd and 4th numeric
                    # Buy cash is 3rd column, buy transfer 4th
                    # Clean numeric extraction
                    nums = re.findall(r"([0-9,]+\.?[0-9]*)", " ".join(cleaned[2:]))
                    # In typical BIDV row, we have 3 numbers after USD: buy cash, buy CK, sell
                    # So use last as sell, previous two as buys
                    if len(nums) >= 3:
                        usd_buy_cash = nums[-3]
                        usd_buy_transfer = nums[-2]
                        usd_sell = nums[-1]
                    elif len(nums) == 1:
                        usd_sell = nums[0]
                    else:
                        usd_sell = candidate
                    found = True
                    break
    if not found or usd_sell is None:
        # Fallback markdown regex: look for USD and then numbers
        # Example: "| Ký hiệu ngoại tệCurrencyUSD | ... | Mua tiền mặt và SécBuy25,800 | Mua chuyển khoảnTransfer25,800 | BánSell26,180 |"
        # We can search for "CurrencyUSD" then capture last Sell number
        md_pat = r"USD[^|]*\|\s*[^|]*Mua[^|]*?([0-9,]+\.?[0-9]*)[^|]*\|\s*[^|]*Mua[^|]*?([0-9,]+\.?[0-9]*)[^|]*\|\s*[^|]*Bán[^|]*?([0-9,]+\.?[0-9]*)"
        m = re.search(md_pat, html, flags=re.IGNORECASE | re.DOTALL)
        if m:
            usd_buy_cash, usd_buy_transfer, usd_sell = [x.strip() for x in m.groups()]
            found = True
        else:
            # Another fallback: generic Sell extraction for USD
            # Find segment containing USD until next "|"
            lines = html.splitlines()
            for line in lines:
                if "USD" in line.upper() and "Sell" in line:
                    nums = re.findall(r"([0-9,]+\.?[0-9]*)", line)
                    if nums:
                        usd_sell = nums[-1]
                        if len(nums) >= 3:
                            usd_buy_cash = nums[-3]
                            usd_buy_transfer = nums[-2]
                        found = True
                        break

    if not usd_sell or not _parse_decimal(usd_sell):
        return {
            "status": "RATE_UNAVAILABLE",
            "reason": "USD sell row missing or invalid",
            "source_url": source_url,
            "captured_at": captured_at,
            "pub_time": pub_time,
            "pub_time_raw": pub_time_raw,
            "currency": "USD",
        }

    sell_dec = _parse_decimal(usd_sell)
    buy_cash_dec = _parse_decimal(usd_buy_cash) if usd_buy_cash else None
    buy_transfer_dec = _parse_decimal(usd_buy_transfer) if usd_buy_transfer else None

    return {
        "status": "OK",
        "currency": "USD",
        "buy_cash": buy_cash_dec,
        "buy_cash_raw": usd_buy_cash,
        "buy_transfer": buy_transfer_dec,
        "buy_transfer_raw": usd_buy_transfer,
        "sell": sell_dec,
        "sell_raw": usd_sell,
        "usd_sell_vnd": sell_dec,
        "pub_time": pub_time,
        "pub_time_raw": pub_time_raw,
        "source_url": source_url,
        "captured_at": captured_at,
        "source": "BIDV",
        "note": "Parsed from HTML table; official dynamic API not proven in this environment",
    }


def discover_bidv_api_url(html: str) -> str | None:
    """Attempt to discover official BIDV JSON API endpoint from page source.

    Scans for known candidate strings and for generic ExchangeRate / ty-gia JSON URLs.
    Returns URL string if found, else None.
    """
    if not html:
        return None
    # Look for candidate URLs explicitly
    for cand in BIDV_API_CANDIDATES:
        if cand in html:
            return cand
    # Generic regex for json endpoints
    m = re.search(r"https?://[^\"'\\s<>]+(?:ExchangeRate|ty-?gia|exchange)[^\"'\\s<>]*\\.json[^\"'\\s<>]*", html, flags=re.IGNORECASE)
    if m:
        return m.group(0)
    m2 = re.search(r"https?://[^\"'\\s<>]+/ServicesBIDV/[^\"'\\s<>]+", html, flags=re.IGNORECASE)
    if m2:
        return m2.group(0)
    return None


def fetch_live_fx(source: str = "all", timeout: int = 5) -> dict[str, Any]:
    """Attempt live fetch for requested source(s). Fails closed with RATE_UNAVAILABLE.

    This uses urllib with minimal deps. In sandbox without outbound network,
    it will return UNAVAILABLE rather than inventing values.
    """
    import urllib.request
    import urllib.error

    results: dict[str, Any] = {}
    sources = []
    if source == "all":
        sources = ["boc", "agribank", "bidv"]
    else:
        sources = [source]

    for src in sources:
        url = {"boc": BOC_URL, "agribank": AGRIBANK_URL, "bidv": BIDV_URL}[src]
        parser = {"boc": parse_boc_html, "agribank": parse_agribank_html, "bidv": parse_bidv_html}[src]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                # Try to detect charset
                charset = resp.headers.get_content_charset() or "utf-8"
                data = resp.read().decode(charset, errors="ignore")
                # For BIDV, also try to discover API
                if src == "bidv":
                    api_url = discover_bidv_api_url(data)
                    if api_url:
                        try:
                            api_req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
                            with urllib.request.urlopen(api_req, timeout=timeout) as api_resp:
                                api_data = api_resp.read().decode(api_resp.headers.get_content_charset() or "utf-8", errors="ignore")
                                # Attempt to parse JSON
                                import json

                                try:
                                    j = json.loads(api_data)
                                    # Look for USD sell in json
                                    # Generic search: find dict containing USD and Sell
                                    # This is best-effort; if fails, fallback to HTML parse
                                    # For now, mark as unavailable if JSON structure unknown
                                    # But we can attempt to find numbers
                                    text_j = json.dumps(j)
                                    m = re.search(r'"(?:USD|usd)[^"]*".*?"(?:sell|ban|Sell)[^"]*"\s*:\s*"?([0-9,.\"]+)"?', text_j, flags=re.IGNORECASE)
                                    if m:
                                        # Use json-derived value
                                        sell_txt = m.group(1).replace('"', "").replace(",", "")
                                        sell_dec = _parse_decimal(sell_txt)
                                        if sell_dec:
                                            results[src] = {
                                                "status": "OK",
                                                "currency": "USD",
                                                "usd_sell_vnd": sell_dec,
                                                "sell": sell_dec,
                                                "sell_raw": sell_txt,
                                                "source_url": api_url,
                                                "captured_at": _now_iso(),
                                                "pub_time": None,
                                                "source": "BIDV-API",
                                            }
                                            continue
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    # No proven API => spec requires UNAVAILABLE
                    # We will still parse HTML but mark as UNPROVEN? For strict fail-closed, return UNAVAILABLE
                    # To be truthful, we return UNAVAILABLE with HTML parsed as evidence but not official
                    html_parsed = parser(data, source_url=url)
                    # If HTML parse succeeded, we keep it but flag status as UNAVAILABLE? Spec says BIDV_RATE_STATUS=UNAVAILABLE and keep manual entry
                    # So we return UNAVAILABLE regardless, but keep parsed value for debugging
                    results[src] = {
                        "status": "RATE_UNAVAILABLE",
                        "reason": "official BIDV dynamic API not proven; HTML fallback not accepted as official",
                        "source_url": url,
                        "captured_at": _now_iso(),
                        "pub_time": html_parsed.get("pub_time"),
                        "html_sell": html_parsed.get("sell_raw"),
                        "html_sell_vnd": html_parsed.get("usd_sell_vnd"),
                        "bidv_rate_status": "UNAVAILABLE",
                    }
                    continue
                parsed = parser(data, source_url=url)
                results[src] = parsed
        except Exception as exc:
            results[src] = {
                "status": "RATE_UNAVAILABLE",
                "reason": f"fetch_error: {type(exc).__name__}: {exc}",
                "source_url": url,
                "captured_at": _now_iso(),
                "currency": "USD",
            }
            if src == "bidv":
                results[src]["bidv_rate_status"] = "UNAVAILABLE"

    return results
