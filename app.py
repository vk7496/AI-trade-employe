import os
import re
import json
import hmac
import base64
import smtplib
from email.message import EmailMessage
from html.parser import HTMLParser
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
from typing import Optional, Tuple, List, Dict

import httpx
import streamlit as st
from io import BytesIO
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

# ============================================================
# MEHR ARA AI TRADE EMPLOYEE  (v2)
# Groq primary -> OpenRouter backup -> Demo fallback
# Live research (Tavily if configured, else Bing/DDG scraping),
# fixed HS table, anti-fabrication guards, deterministic price
# normalization, PDF, Email/WhatsApp.
#
# Optional secrets: GROQ_API_KEY, OPENROUTER_API_KEY, TAVILY_API_KEY,
# APP_PASSWORD (recommended: protects your API keys / SMTP),
# SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SENDER_EMAIL
# ============================================================

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

st.set_page_config(
    page_title="Mehr Ara AI Trade Employee",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto",  # collapsed automatically on phones
)

LANG = {
    "EN": {
        "title": "MEHR ARA AI TRADE EMPLOYEE",
        "subtitle": "A digital commercial employee for selling, sourcing, exporting, pricing, document generation and communication.",
        "today": "What do you want your digital employee to do today?",
        "sell": "Sell a Product", "source": "Source a Product", "export": "Export a Product",
        "buyers": "Find Buyers", "pricing": "Calculate Price", "operations": "Trade Operations",
        "assistant": "AI Trade Employee", "active_cases": "Cases (this session)", "buyer_leads": "Buyer sources found",
        "suppliers": "Supplier sources found", "ai_mode": "AI Mode", "demo": "Demo Mode", "ai": "AI",
        "request": "Trade Request", "product": "Product", "quantity": "Quantity", "origin": "Origin",
        "destination": "Destination", "budget": "Budget / Target Price", "notes": "Additional Requirements",
        "payment": "Payment terms (you decide)",
        "incoterm": "Incoterm (you decide)",
        "fx": "FX rate (1 USD = ? IRT) — optional",
        "generate": "Generate Trade Plan", "result": "AI Employee Result", "chat": "Ask your AI Trade Employee",
        "message": "Message", "working": "AI Trade Employee is preparing the work...",
        "pricing_title": "Commercial Price Calculator", "calculate": "Calculate Commercial Price",
        "calc_currency": "Currency of ALL amounts below",
        "purchase_unit": "Purchase price / unit", "inland": "Inland transport", "freight": "International freight",
        "insurance": "Insurance", "duty": "Customs duty %", "vat": "Import VAT %", "bank": "Bank / LC fee %",
        "other": "Other costs", "margin": "Target margin % (of sale price)", "research": "Live Trade Research",
        "research_caption": "Searches the web for current companies and official sources. Only sources actually retrieved are shown.",
        "research_run": "Research Now", "customs": "Customs & Compliance", "buyer_research": "Find Buyers",
        "supplier_research": "Find Suppliers", "research_working": "Searching current sources...",
        "demo_notice": "Commercial data, prices, duties, taxes, contacts and legal requirements must be verified before a transaction.",
    },
    "FA": {
        "title": "نیروی هوشمند بازرگانی مهرآرا",
        "subtitle": "نیروی دیجیتال برای فروش، تأمین، صادرات، قیمت‌گذاری، صدور اسناد و ارتباط با مشتریان.",
        "today": "امروز می‌خواهید نیروی دیجیتال شما چه کاری انجام دهد؟",
        "sell": "فروش کالا", "source": "تأمین کالا", "export": "صادرات کالا",
        "buyers": "پیدا کردن خریدار", "pricing": "محاسبه قیمت", "operations": "عملیات بازرگانی",
        "assistant": "نیروی هوشمند بازرگانی", "active_cases": "پرونده‌ها (این نشست)", "buyer_leads": "منابع خریدار یافت‌شده",
        "suppliers": "منابع تأمین‌کننده یافت‌شده", "ai_mode": "حالت هوش مصنوعی", "demo": "حالت نمایشی", "ai": "Groq AI",
        "request": "درخواست بازرگانی", "product": "کالا", "quantity": "مقدار", "origin": "مبدأ",
        "destination": "مقصد", "budget": "بودجه / قیمت هدف", "notes": "نیازمندی‌های بیشتر",
        "payment": "شرایط پرداخت (خودتان تعیین کنید)",
        "incoterm": "Incoterm (خودتان تعیین کنید)",
        "fx": "نرخ ارز (۱ دلار = ؟ تومان) — اختیاری",
        "generate": "ساخت برنامه بازرگانی", "result": "خروجی نیروی هوشمند", "chat": "از نیروی هوشمند بازرگانی بپرسید",
        "message": "پیام", "working": "نیروی هوشمند در حال آماده‌سازی نتیجه است...",
        "pricing_title": "محاسبه‌گر قیمت تجاری", "calculate": "محاسبه قیمت",
        "calc_currency": "ارز همه مبالغ زیر",
        "purchase_unit": "قیمت خرید هر واحد", "inland": "حمل داخلی", "freight": "حمل بین‌المللی",
        "insurance": "بیمه", "duty": "حقوق و عوارض گمرکی %", "vat": "مالیات واردات / VAT %", "bank": "کارمزد بانک / LC %",
        "other": "سایر هزینه‌ها", "margin": "حاشیه سود هدف % (از قیمت فروش)", "research": "تحقیق زنده بازرگانی",
        "research_caption": "برای یافتن شرکت‌ها و منابع رسمی در وب جستجو می‌شود. فقط منابعی که واقعاً بازیابی شده‌اند نمایش داده می‌شوند.",
        "research_run": "شروع تحقیق", "customs": "گمرک و انطباق", "buyer_research": "پیدا کردن خریدار",
        "supplier_research": "پیدا کردن تأمین‌کننده", "research_working": "در حال جستجوی منابع به‌روز...",
        "demo_notice": "قیمت، هزینه حمل، تعرفه، مالیات، اطلاعات تماس و الزامات قانونی باید پیش از معامله تأیید شوند.",
    },
}

# ------------------------------------------------------------
# Fixed HS reference table (CANDIDATE codes — official classification
# is still required). The model is only allowed to use these.
# Extend this list with your own products.
# ------------------------------------------------------------
HS_TABLE = [
    (("زعفران", "saffron"), "0910.20", "Saffron"),
    (("کیوی", "kiwi"), "0810.50", "Kiwifruit"),
    (("پسته", "pistachio"), "0802.51 (in shell) / 0802.52 (shelled)", "Pistachios"),
    (("خرما", "dates"), "0804.10", "Dates"),
    (("کشمش", "raisin", "raisins"), "0806.20", "Raisins"),
    (("تلیسه", "گوساله", "گاو", "holstein", "heifer", "calf", "calves", "cattle"),
     "0102.21 (pure-bred breeding) / 0102.29 (other)", "Live bovine animals"),
]
HS_RE = re.compile(r"\b\d{4}\.\d{2}(?:\.\d{2})?\b")
HS_CONTEXT_RE = re.compile(r"(?i)\bhs\b|hs\s*code|harmonized|tariff|کد|تعرفه")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"https?://[^\s)\]>\"'|]+")
PHONE_RES = [
    re.compile(r"(?<![\w+])(?:\+|00)\d[\d\s\-()]{6,}\d"),
    re.compile(r"(?<!\d)09\d{9}(?!\d)"),
    re.compile(r"(?<!\d)0\d{2,3}[\s\-]\d{7,8}(?!\d)"),
]

# currencies / units used by the deterministic price normalizer
CURRENCIES = ["USD", "EUR", "AED", "OMR", "IRT", "IRR"]
PEG = {"USD": 1.0, "AED": 3.6725, "OMR": 0.3845}  # units of currency per 1 USD (official pegs)
UNIT_TO_KG = {"kg": 1.0, "g": 1000.0, "100g": 10.0, "mithqal": 1000.0 / 4.608}  # multiply price/unit -> price/kg
CUR_WORDS = {"usd": "USD", "$": "USD", "دلار": "USD", "eur": "EUR", "€": "EUR", "یورو": "EUR",
             "aed": "AED", "درهم": "AED", "omr": "OMR", "irt": "IRT", "تومان": "IRT",
             "irr": "IRR", "ریال": "IRR"}
IRAN_KEYS = ["iran", "tehran", "mashhad", "shiraz", "isfahan", "tabriz", "ایران", "تهران", "مشهد", "شیراز", "اصفهان", "تبریز"]
INCOTERMS = ["EXW", "FCA", "FOB", "CFR", "CIF", "DAP", "DDP"]

# ----------------------------- state --------------------------
for key, default in {
    "language": "FA",
    "selected_action": "فروش کالا",
    "chat_history": [],
    "last_trade_case": None,
    "last_error": None,
    "last_provider": None,
    "last_model": None,
    "fallback_note": None,
    "search_engine": None,
    "research_result": None,
    "calc_result": None,
    "market_price_result": None,
    "counters": {"cases": 0, "buyers": 0, "suppliers": 0},
    "calc_qty": "",
    "calc_unit": "",
    "calc_cur": "USD",
    "calc_inland": "0",
    "calc_freight": "0",
    "calc_ins": "0",
    "calc_duty": "0",
    "calc_vat": "0",
    "calc_bank": "0",
    "calc_other": "0",
    "calc_margin": "10",
    "research_product": "",
    "research_market": "Oman",
    "authed": False,
    "emails_sent": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

T = LANG[st.session_state.language]

# ----------------------------- helpers ------------------------
def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    try:
        value = st.secrets.get(name, None)
    except Exception:
        value = None
    return value or os.getenv(name) or default


def has_key(name: str) -> bool:
    return bool((get_secret(name) or "").strip())


def check_password() -> bool:
    """If APP_PASSWORD is set in Secrets, require it. Protects your API keys and SMTP."""
    expected = (get_secret("APP_PASSWORD") or "").strip()
    if not expected or st.session_state.get("authed"):
        return True
    st.markdown("### 🔒 Mehr Ara AI Trade Employee")
    with st.form("login_form"):
        pw = st.text_input("Password / رمز عبور", type="password")
        ok = st.form_submit_button("Login / ورود")
    if ok:
        if hmac.compare_digest(pw.encode("utf-8"), expected.encode("utf-8")):
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("رمز اشتباه است. / Wrong password.")
    return False


if not check_password():
    st.stop()


def normalize_digits(value: str) -> str:
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return (value or "").translate(trans)


def parse_number(value: str) -> Optional[float]:
    if value is None:
        return None
    s = normalize_digits(str(value)).strip().replace("٬", "").replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", s)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def money(x: float, currency: str = "USD") -> str:
    return f"{currency} {x:,.2f}"


def pct(x: float) -> str:
    return f"{x:.2f}%"


def pdf_safe(value: str) -> bool:
    """Helvetica in the PDF can only render Latin-1 text."""
    return all(ord(c) < 256 for c in (value or ""))


def detect_currencies(text: str) -> set:
    t = (text or "").lower()
    found = set()
    for k, v in CUR_WORDS.items():
        if re.fullmatch(r"[a-z]+", k):
            if re.search(rf"(?<![a-z]){k}(?![a-z])", t):
                found.add(v)
        elif k in t:
            found.add(v)
    return found


def involves_iran(*values: str) -> bool:
    return any(_has_any(v or "", IRAN_KEYS) for v in values)


# ---------------- output cleaning / anti-fabrication guards ----------------
def clean_output(text: str) -> str:
    """Remove raw HTML (e.g. <br>) that Streamlit would show literally."""
    text = re.sub(r"【[^】]*】", "", text or "")
    text = re.sub(r"<br\s*/?>", " / ", text, flags=re.I)
    text = re.sub(
        r"</?(?:p|div|span|b|i|u|strong|em|ul|ol|li|table|thead|tbody|tr|td|th|center|font|small|sup|sub)\b[^>]*>",
        "", text, flags=re.I,
    )
    return text


def scrub_unverified(text: str, allowed_text: str = "", allowed_urls: Optional[List[str]] = None,
                     scrub_links: bool = False) -> str:
    """Replace emails / phones / placeholder strings that do not appear in the
    allowed source text. Optionally also replace links whose host is not in allowed_urls."""
    allowed_lower = (allowed_text or "").lower()
    allowed_digits = re.sub(r"\D", "", normalize_digits(allowed_text or ""))

    def fix_email(m):
        return m.group(0) if m.group(0).lower() in allowed_lower else "[unverified]"

    def fix_phone(m):
        digits = re.sub(r"\D", "", normalize_digits(m.group(0)))
        return m.group(0) if digits and digits in allowed_digits else "[unverified]"

    text = EMAIL_RE.sub(fix_email, text or "")
    for rx in PHONE_RES:
        text = rx.sub(fix_phone, text)
    text = re.sub(r"(?i)\b(?:x{4,}|example\.(?:com|ir|org|net))\b", "[unverified]", text)

    if scrub_links:
        hosts = {urlparse(u).netloc.lower().removeprefix("www.") for u in (allowed_urls or [])}

        def fix_url(m):
            raw = m.group(0)
            url = raw.rstrip(".,;:!?")
            host = urlparse(url).netloc.lower().removeprefix("www.")
            return raw if host in hosts else "[unverified link]" + raw[len(url):]

        text = URL_RE.sub(fix_url, text)
    return text


def lookup_hs(product: str) -> Optional[Dict[str, str]]:
    p = (product or "").lower()
    for keys, code, name in HS_TABLE:
        for k in keys:
            if re.search(rf"(?<![a-z]){re.escape(k.lower())}(?![a-z])", p):
                return {"code": code, "name": name}
    return None


def hs_instruction(product: str) -> str:
    hit = lookup_hs(product)
    if hit:
        return (f"HS_REFERENCE (internal table, candidate — official classification required): "
                f"{hit['name']} = {hit['code']}. Use ONLY this code and do not state any other HS code.")
    return ("HS_REFERENCE: product is not in the internal table. Do NOT guess an HS code; "
            "write 'HS Code: official classification required'.")


def find_hs_codes(text: str) -> set:
    """Only lines that talk about HS / tariff / کد are inspected, so prices like 5000.00 are not mistaken for HS codes."""
    codes = set()
    for line in normalize_digits(text or "").splitlines():
        if HS_CONTEXT_RE.search(line):
            codes |= {c[:7] for c in HS_RE.findall(line)}
    return codes


def hs_guard(text: str, product: str, language: str) -> str:
    found = find_hs_codes(text)
    if not found:
        return text
    hit = lookup_hs(product)
    allowed = {c[:7] for c in HS_RE.findall(hit["code"])} if hit else set()
    bad = sorted(found - allowed)
    if not bad:
        return text
    if language == "FA":
        note = (f"\n\n> ⚠️ **هشدار کد HS:** کد(های) {', '.join(bad)} در جدول داخلی تأیید نشده‌اند و ممکن است اشتباه باشند. "
                "طبقه‌بندی رسمی را از گمرک/تعرفه رسمی بگیرید.")
    else:
        note = (f"\n\n> ⚠️ **HS code warning:** code(s) {', '.join(bad)} are not confirmed by the internal table "
                "and may be wrong. Get the official classification from customs / the official tariff.")
    return text + note


def strip_machine_line(text: str) -> str:
    return re.sub(r"MARKET_PRICE_RANGE_USD_PER_KG:.*\n?", "", text or "").strip()


def numbers_in(text: str) -> List[float]:
    vals = []
    cleaned = normalize_digits(text or "").replace("٬", "")
    for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", cleaned):
        try:
            vals.append(float(m.group(0).replace(",", "")))
        except ValueError:
            pass
    return vals


def number_in_text(x: float, text: str) -> bool:
    return any(abs(n - x) <= max(0.01, x * 0.005) for n in numbers_in(text))


# ---------------- web search ----------------
class DuckDuckGoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self._current = None
        self._in_title = False
        self._in_snippet = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls = attrs.get("class", "")
        href = attrs.get("href", "")
        if tag == "a" and "result__a" in cls:
            self._current = {"title": "", "url": href, "snippet": ""}
            self._in_title = True
            self._in_snippet = False
        elif self._current is not None and tag in ("a", "div", "span") and "result__snippet" in cls:
            self._in_snippet = True
            self._in_title = False

    def handle_data(self, data):
        if self._current is None:
            return
        if self._in_title:
            self._current["title"] += data
        elif self._in_snippet:
            self._current["snippet"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._in_title and self._current is not None:
            self._in_title = False
            if self._current.get("title") and self._current.get("url"):
                self.results.append(self._current)
                self._current = None
        if tag in ("div", "span"):
            self._in_snippet = False


class BingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self._in_result = False
        self._in_h2 = False
        self._in_a = False
        self._current = None
        self._snippet = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls = attrs.get("class", "")
        if tag == "li" and "b_algo" in cls:
            self._in_result = True
            self._current = {"title": "", "url": "", "snippet": ""}
        elif self._in_result and tag == "h2":
            self._in_h2 = True
        elif self._in_result and tag == "a" and self._in_h2:
            self._in_a = True
            if self._current is not None:
                self._current["url"] = attrs.get("href", "")
        elif self._in_result and tag in ("p", "div") and ("b_caption" in cls or "b_snippet" in cls):
            self._snippet = True

    def handle_data(self, data):
        if self._current is None:
            return
        if self._in_a:
            self._current["title"] += data
        elif self._snippet:
            self._current["snippet"] += data

    def handle_endtag(self, tag):
        if tag == "a":
            self._in_a = False
        elif tag == "h2":
            self._in_h2 = False
        elif tag == "li" and self._in_result:
            if self._current and self._current.get("title") and self._current.get("url"):
                self.results.append(self._current)
            self._current = None
            self._in_result = False
            self._snippet = False
        elif tag in ("p", "div"):
            self._snippet = False


def unwrap_redirect(link: str) -> str:
    """DuckDuckGo / Bing return redirect links; decode them to the real URL."""
    try:
        p = urlparse(link)
        qs = parse_qs(p.query)
        if "duckduckgo.com" in p.netloc and "uddg" in qs:
            return unquote(qs["uddg"][0])
        if "bing.com" in p.netloc and p.path.startswith("/ck/") and "u" in qs:
            u = qs["u"][0]
            if u.startswith("a1"):
                b = u[2:]
                b += "=" * (-len(b) % 4)
                return base64.urlsafe_b64decode(b).decode("utf-8", "ignore")
    except Exception:
        pass
    return link


def tavily_search(query: str, limit: int = 8) -> List[Dict[str, str]]:
    key = (get_secret("TAVILY_API_KEY") or "").strip()
    if not key:
        return []
    try:
        with httpx.Client(timeout=httpx.Timeout(20.0, connect=8.0)) as client:
            r = client.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"query": query, "max_results": limit, "search_depth": "basic"},
            )
        if r.status_code >= 400:
            return []
        out = []
        for item in r.json().get("results", []):
            url = (item.get("url") or "").strip()
            title = re.sub(r"\s+", " ", item.get("title") or "").strip()
            if url.startswith("http") and title:
                snippet = re.sub(r"\s+", " ", item.get("content") or "").strip()[:400]
                out.append({"title": title, "url": url, "snippet": snippet})
        return out[:limit]
    except Exception:
        return []


def live_web_search(query: str, limit: int = 6) -> List[Dict[str, str]]:
    results = tavily_search(query, limit)
    if results:
        st.session_state.search_engine = "Tavily"
        return results

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36"}
    search_targets = [
        ("bing", "https://www.bing.com/search?q=" + quote_plus(query)),
        ("ddg", "https://html.duckduckgo.com/html/?q=" + quote_plus(query)),
    ]
    for engine, url in search_targets:
        try:
            with httpx.Client(timeout=httpx.Timeout(18.0, connect=8.0), follow_redirects=True) as client:
                response = client.get(url, headers=headers)
            if response.status_code >= 400 or not response.text:
                continue
            parser = BingParser() if engine == "bing" else DuckDuckGoParser()
            parser.feed(response.text)
            results, seen = [], set()
            for item in parser.results:
                link = (item.get("url") or "").strip()
                if link.startswith("//"):
                    link = "https:" + link
                link = unwrap_redirect(link)
                if not link.startswith("http"):
                    continue
                host = urlparse(link).netloc.lower()
                if any(bad in host for bad in ("bing.com", "duckduckgo.com", "google.com")) or link in seen:
                    continue
                title = re.sub(r"\s+", " ", item.get("title", "")).strip()
                snippet = re.sub(r"\s+", " ", item.get("snippet", "")).strip()
                if not title:
                    continue
                seen.add(link)
                results.append({"title": title, "url": link, "snippet": snippet})
                if len(results) >= limit:
                    break
            if results:
                st.session_state.search_engine = "Bing" if engine == "bing" else "DuckDuckGo"
                return results
        except Exception:
            continue
    st.session_state.search_engine = None
    return []


def multi_search(queries: List[str], limit: int = 10, per_query: Optional[int] = None) -> List[Dict[str, str]]:
    per = per_query or limit
    merged, seen = [], set()
    for q in queries:
        for r in live_web_search(q, limit=per):
            if r["url"] not in seen:
                seen.add(r["url"])
                merged.append(r)
        if len(merged) >= limit:
            break
    return merged[:limit]


def format_search_results(results: List[Dict[str, str]]) -> str:
    if not results:
        return "NO SEARCH RESULTS RETURNED."
    return "\n\n".join(
        f"[{i}] {r['title']}\nURL: {r['url']}\nSnippet: {r.get('snippet') or 'No snippet available'}"
        for i, r in enumerate(results, 1)
    )


def sources_table(results: List[Dict[str, str]], language: str) -> str:
    def esc(x: str, n: int = 160) -> str:
        x = re.sub(r"[#*_>`~]+", "", x or "")          # strip leaked markdown from snippets
        x = re.sub(r"\s+", " ", x).strip()
        return x.replace("|", "/").replace("[", "(").replace("]", ")")[:n]

    if language == "FA":
        head = "| # | منبع | خلاصه |\n|---|---|---|\n"
    else:
        head = "| # | Source | Snippet |\n|---|---|---|\n"
    rows = []
    for i, r in enumerate(results, 1):
        host = urlparse(r["url"]).netloc.removeprefix("www.")
        rows.append(f"| {i} | [{esc(r['title'], 80)}]({r['url']}) ({host}) | {esc(r.get('snippet', ''))} |")
    return head + "\n".join(rows)


def _has_any(text: str, keys: List[str]) -> bool:
    t = (text or "").lower()
    for k in keys:
        k = (k or "").strip().lower()
        if k and re.search(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])", t):
            return True
    return False


MARKET_ALIASES = {
    "oman": ["oman", "muscat", "salalah", "sohar", "عمان", "مسقط", "صلالة", "صحار"],
    "uae": ["uae", "united arab emirates", "dubai", "abu dhabi", "sharjah", "الإمارات", "دبي", "امارات", "دبی"],
    "turkey": ["turkey", "türkiye", "turkiye", "istanbul", "ankara", "ترکیه", "استانبول", "آنکارا"],
    "iran": ["iran", "tehran", "mashhad", "ایران", "تهران", "مشهد"],
}
AR_NAMES = {"Saffron": "زعفران", "Kiwifruit": "كيوي", "Pistachios": "فستق", "Dates": "تمر",
            "Raisins": "زبيب", "Live bovine animals": "أبقار"}
INFO_HOSTS = ("wikipedia.org", "webmd.com", "clevelandclinic.org", "healthline.com", "mayoclinic.org",
              "britannica.com", "medicalnewstoday.com", "verywellhealth.com", "naturalremedyideas.com")
GULF_WORDS = ("oman", "uae", "dubai", "abu dhabi", "qatar", "kuwait", "bahrain", "saudi", "muscat",
              "عمان", "مسقط", "امارات", "دبی", "قطر", "کویت", "بحرین", "عربستان")


def market_keywords(market: str) -> List[str]:
    m = (market or "").strip().lower()
    keys = [m] if m else []
    for name, aliases in MARKET_ALIASES.items():
        if _has_any(m, [name] + aliases):
            keys += aliases
    return list(dict.fromkeys(k for k in keys if k))


def filter_relevant(results: List[Dict[str, str]], keywords: List[str],
                    also: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """Keep results that mention the product (any keyword) AND, if given, the market (any `also` keyword)."""
    keys = [k for k in keywords if k and k.strip()]
    if not keys:
        return results
    out = []
    for r in results:
        blob = f"{r.get('title', '')} {r.get('snippet', '')} {r.get('url', '')}"
        if _has_any(blob, keys) and (not also or _has_any(blob, also)):
            out.append(r)
    return out


# ---------------- AI ----------------
def demo_response(language: str) -> str:
    if language == "FA":
        return """### گزارش نمایشی

این پاسخ در **حالت Demo** تولید شده و به اطلاعات زنده بازار متصل نیست.

برای اجرای واقعی باید مشخصات کالا، مقدار، واحد قیمت، Incoterm، هزینه‌های حمل، شرایط پرداخت و الزامات واردات تأیید شوند."""
    return """### Demo Trade Report

This is a clearly labeled demo response. Live prices, duties, taxes, freight, company contacts and stock must be verified before execution."""


def clean_farsi_prompt(language: str) -> str:
    if language == "FA":
        return """پاسخ را کاملاً به فارسی طبیعی و حرفه‌ای بنویس. از فارسی استاندارد استفاده کن. اصطلاحات استاندارد تجارت بین‌الملل مانند USD, kg, MT, FOB, CIF, CFR, EXW, LC, RFQ و HS Code را در لاتین نگه دار.
فقط Markdown ساده بنویس: هرگز تگ HTML (مثل <br>) ننویس. عنوان‌ها را با ## و بدون شماره‌گذاری (بدون «1.» یا «۲.») بنویس. جدول‌ها را کوتاه، خوانا و با سلول‌های تک‌خطی بنویس.
اعداد را با جداکننده هزارگان بنویس (مثلاً 5,600,000) و واحد را بعد از عدد با یک فاصله بیاور (مثلاً 10 kg، 18,000 USD)."""
    return ("Write clear professional English with consistent terminology and readable Markdown tables. "
            "Plain Markdown only: never use HTML tags such as <br>. Use ## headings WITHOUT numbering. Keep table cells single-line. "
            "Write numbers with thousands separators (5,600,000) and put the unit after the number with a space (10 kg, 18,000 USD).")


def provider_call(provider: str, model: str, prompt: str, language: str, history=None, web_search=False) -> Tuple[bool, str, str]:
    key_name = "GROQ_API_KEY" if provider == "Groq" else "OPENROUTER_API_KEY"
    api_key = get_secret(key_name)
    if not api_key:
        return False, "", f"{key_name} is missing"

    messages = [{
        "role": "system",
        "content": f"""You are Mehr Ara AI Trade Employee, a practical B2B trade operations analyst.
Today's date: {date.today().isoformat()}.

{clean_farsi_prompt(language)}

Reliability and compliance rules:
- Never invent a real company, person, phone, WhatsApp, email, website, quotation, stock level, market price, freight rate, tariff, tax, permit, certificate, legal requirement or customs procedure.
- Name a company, website, email or phone ONLY if it appears verbatim in sources supplied to you in this conversation. Never output placeholders such as example.com, xxx or info@company.
- Never assume the payment method, Incoterm, price, currency, FX rate or quantity unit. Use only what the user provided; if something is missing, list it under 'must be specified by the user' instead of choosing a default (do not default to LC).
- Clearly distinguish: 1) User-provided facts, 2) Estimate/assumption, 3) Must verify.
- For customs/legal questions, prefer official government/customs/tax sources. Do not present a legal requirement as confirmed unless an authoritative source supports it.
- For pricing, show arithmetic, units and formulas.
- For HS Code, use ONLY the HS_REFERENCE given in the prompt. If none is given, write 'HS Code: official classification required'. Always label it 'candidate — official classification required'.
- If Iran is the origin or destination, add a checklist item about banking / payment-channel / sanctions restrictions (including whether an LC is practical) and mark it 'must verify with bank and legal counsel'. Do not state specific sanctions rules as confirmed.
"""}]
    if history:
        messages.extend(history[-8:])
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 4000,
    }
    if provider == "Groq" and web_search and "gpt-oss" in model:
        payload["tools"] = [{"type": "browser_search"}]
        payload["tool_choice"] = "auto"

    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    if provider == "OpenRouter":
        headers["HTTP-Referer"] = "https://mehrara.streamlit.app"
        headers["X-Title"] = "Mehr Ara AI Trade Employee"

    url = GROQ_URL if provider == "Groq" else OPENROUTER_URL
    try:
        with httpx.Client(timeout=httpx.Timeout(120.0, connect=25.0)) as client:
            response = client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            try:
                detail = response.json().get("error", {}).get("message", response.text)
            except Exception:
                detail = response.text
            return False, "", f"HTTP {response.status_code}: {detail}"
        data = response.json()
        content = data["choices"][0]["message"].get("content", "")
        if not str(content).strip():
            return False, "", "Empty provider response"
        return True, str(content).strip(), "OK"
    except httpx.TimeoutException:
        return False, "", "Request timed out"
    except httpx.RequestError as exc:
        return False, "", f"Network error: {exc}"
    except Exception as exc:
        return False, "", f"Unexpected response: {exc}"


def call_ai(prompt: str, language: str, history=None, web_search=False) -> str:
    errors = []
    groq_models = [
        get_secret("GROQ_MODEL", "openai/gpt-oss-120b"),
        "openai/gpt-oss-20b",
    ]
    seen = set()
    for model in groq_models:
        if model in seen:
            continue
        seen.add(model)
        ok, content, detail = provider_call("Groq", model, prompt, language, history, web_search=web_search)
        if ok:
            st.session_state.last_provider = "Groq"
            st.session_state.last_model = model
            st.session_state.last_error = None
            st.session_state.fallback_note = " | ".join(errors) if errors else None
            return clean_output(content)
        errors.append(f"Groq / {model}: {detail}")

    or_model = get_secret("OPENROUTER_MODEL", "openrouter/free")
    ok, content, detail = provider_call("OpenRouter", or_model, prompt, language, history, web_search=False)
    if ok:
        st.session_state.last_provider = "OpenRouter"
        st.session_state.last_model = or_model
        st.session_state.last_error = None
        st.session_state.fallback_note = " | ".join(errors) if errors else None
        return clean_output(content)
    errors.append(f"OpenRouter / {or_model}: {detail}")

    st.session_state.last_provider = "Demo"
    st.session_state.last_model = None
    st.session_state.last_error = " | ".join(errors)
    st.session_state.fallback_note = None
    return demo_response(language)


# ---------------- deterministic market-price normalization ----------------
def extract_market_price(text: str):
    if not text:
        return None
    m = re.search(r"MARKET_PRICE_RANGE_USD_PER_KG\s*:\s*\$?\s*([0-9][0-9,]*(?:\.\d+)?)\s*(?:-|–|—|to)\s*\$?\s*([0-9][0-9,]*(?:\.\d+)?)", text, re.I)
    if not m:
        return None
    try:
        low = float(m.group(1).replace(",", ""))
        high = float(m.group(2).replace(",", ""))
    except ValueError:
        return None
    if low < 0 or high < low:
        return None
    return {"low": low, "high": high, "mid": (low + high) / 2.0}


def parse_json_array(text: str) -> List[Dict]:
    t = re.sub(r"```(?:json)?", "", text or "")
    m = re.search(r"\[.*\]", t, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except Exception:
        return []
    return [d for d in data if isinstance(d, dict)] if isinstance(data, list) else []


def normalize_quotes(quotes: List[Dict], results: List[Dict[str, str]], fx_rate: Optional[float]) -> Tuple[List[Dict], bool]:
    """Python (not the LLM) verifies each price against the snippet and converts it to USD/kg.
    Returns (rows, unit_mismatch_suspected)."""
    rows = []
    for q in quotes[:20]:
        try:
            idx = int(q.get("source"))
        except (TypeError, ValueError):
            continue
        if not 1 <= idx <= len(results):
            continue
        r = results[idx - 1]
        price = parse_number(str(q.get("price", "")))
        cur = str(q.get("currency", "")).upper().strip()
        unit = str(q.get("unit", "")).lower().strip()
        row = {"src": idx, "host": urlparse(r["url"]).netloc.removeprefix("www."),
               "price": price, "cur": cur, "unit": unit, "usd_kg": None, "status": "ok"}
        blob = f"{r.get('title', '')} {r.get('snippet', '')}"
        if price is None or price <= 0 or not number_in_text(price, blob):
            row["status"] = "unsupported"
        elif unit not in UNIT_TO_KG:
            row["status"] = "unit_unclear"
        else:
            per_kg = price * UNIT_TO_KG[unit]
            if cur in PEG:
                row["usd_kg"] = per_kg / PEG[cur]
            elif cur == "IRT" and fx_rate:
                row["usd_kg"] = per_kg / fx_rate
            elif cur == "IRR" and fx_rate:
                row["usd_kg"] = per_kg / 10.0 / fx_rate
            elif cur in ("IRT", "IRR"):
                row["status"] = "needs_fx"
            else:
                row["status"] = "currency"
        rows.append(row)

    ok = [r for r in rows if r["status"] == "ok" and r["usd_kg"]]
    mismatch = False
    if len(ok) >= 2:
        vals = sorted(r["usd_kg"] for r in ok)
        if vals[-1] / vals[0] > 10:
            mismatch = True
            if len(ok) >= 3:
                med = vals[len(vals) // 2]
                for r in ok:
                    if not (med / 3 <= r["usd_kg"] <= med * 3):
                        r["status"] = "outlier"
            else:
                for r in ok:
                    r["status"] = "conflict"
    return rows, mismatch


STATUS_TEXT = {
    "FA": {"ok": "✅ پذیرفته شد", "unsupported": "❌ عدد در متن منبع نبود", "unit_unclear": "❌ واحد نامشخص",
           "needs_fx": "⚠️ نرخ ارز لازم است", "currency": "❌ ارز قابل تبدیل نیست",
           "outlier": "❌ پرت (احتمال اشتباه واحد)", "conflict": "❌ تناقض (احتمال اشتباه واحد)"},
    "EN": {"ok": "✅ accepted", "unsupported": "❌ number not in source text", "unit_unclear": "❌ unit unclear",
           "needs_fx": "⚠️ FX rate needed", "currency": "❌ currency not convertible",
           "outlier": "❌ outlier (possible unit mismatch)", "conflict": "❌ conflict (possible unit mismatch)"},
}


def market_price_research(product: str, quantity: str, origin: str, destination: str, language: str,
                          fx_rate: Optional[float] = None) -> str:
    year = date.today().year
    results = multi_search([
        f"wholesale B2B price {product} per kg supplier quotation {origin} {destination} {year}",
        f"{product} exporter wholesale price per kg quotation {year}",
    ], limit=8)
    if not results:
        msg = ("**قیمت بازار تأیید نشد.** جست‌وجوی وب در این اجرا نتیجه قابل بازیابی نداد؛ هیچ قیمتی حدس زده نشد."
               if language == "FA" else
               "**Market price not verified.** Web search returned nothing; no price was guessed.")
        return msg + "\n\nMARKET_PRICE_RANGE_USD_PER_KG: UNAVAILABLE"

    source_block = format_search_results(results)
    prompt = f"""You extract price quotes from web search results for Mehr Ara.
Use ONLY the results below. Never use outside knowledge for prices.
Product: {product or 'not specified'}
Origin: {origin or 'not specified'}
Destination: {destination or 'not specified'}

Search results:
{source_block}

Return ONLY a JSON array (no prose, no code fences). Each element:
{{"source": <result number>, "price": <number exactly as written in that result>, "currency": "USD|AED|OMR|EUR|IRT|IRR|OTHER", "unit": "kg|g|100g|mithqal|unclear", "grade": "<short text>"}}
Rules: include a price only if that exact number appears in the result's title or snippet. Use IRT for toman and IRR for rial. If the unit is not explicit use "unclear". Skip results that are not about this product. Return [] if there are none."""
    raw = call_ai(prompt, "EN", web_search=False)
    quotes = parse_json_array(raw)
    rows, mismatch = normalize_quotes(quotes, results, fx_rate)
    kept = [r["usd_kg"] for r in rows if r["status"] == "ok" and r["usd_kg"]]
    stx = STATUS_TEXT["FA" if language == "FA" else "EN"]

    if language == "FA":
        title = "### قیمت‌های استخراج‌شده (تأییدنشده)"
        head = "| # | منبع | قیمت در منبع | واحد | ≈ USD/kg | وضعیت |\n|---|---|---|---|---|---|\n"
        none_msg = "هیچ قیمتی که هم در متن منبع باشد و هم قابل تبدیل به USD/kg باشد پیدا نشد؛ چیزی حدس زده نشد."
        mm_msg = ("> ⚠️ قیمت‌های منابع بیش از ۱۰ برابر با هم فرق دارند؛ احتمالاً اشتباه واحد (مثقال/گرم/کیلو یا ریال/تومان) است. "
                  "قیمت‌های مشکوک کنار گذاشته شد.")
        sources_heading = "### منابع جست‌وجوشده"
        fx_msg = "> برای تبدیل تومان/ریال، «نرخ ارز» را در فرم درخواست وارد کنید."
    else:
        title = "### Extracted prices (unverified)"
        head = "| # | Source | Price in source | Unit | ≈ USD/kg | Status |\n|---|---|---|---|---|---|\n"
        none_msg = "No price was both present in a source text and convertible to USD/kg; nothing was guessed."
        mm_msg = ("> ⚠️ Source prices differ by more than 10x; this is probably a unit mismatch "
                  "(mithqal/gram/kg or rial/toman). Suspect prices were excluded.")
        sources_heading = "### Sources searched"
        fx_msg = "> To convert toman/rial, enter the FX rate in the request form."

    lines = []
    for r in rows:
        price_txt = f"{r['price']:,.2f}".rstrip("0").rstrip(".") if r["price"] is not None else "-"
        usd_txt = f"{r['usd_kg']:,.2f}" if r["usd_kg"] else "-"
        lines.append(f"| {r['src']} | {r['host']} | {price_txt} {r['cur']} | {r['unit']} | {usd_txt} | {stx.get(r['status'], r['status'])} |")

    parts = [title]
    if rows:
        parts.append(head + "\n".join(lines))
    else:
        parts.append(none_msg)
    if mismatch:
        parts.append(mm_msg)
    if any(r["status"] == "needs_fx" for r in rows):
        parts.append(fx_msg)
    if rows and not kept:
        parts.append(none_msg)

    if kept:
        parts.append(f"MARKET_PRICE_RANGE_USD_PER_KG: {min(kept):.2f}-{max(kept):.2f}")
    else:
        parts.append("MARKET_PRICE_RANGE_USD_PER_KG: UNAVAILABLE")
    parts.append(f"{sources_heading}\n" + sources_table(results, language))
    return "\n\n".join(parts)


def run_live_research(mode: str, product: str, market: str, language: str, ai_ready: bool):
    """Returns (markdown, number_of_sources). Never fabricates: if search returns nothing, says so."""
    product = (product or "").strip()
    market = (market or "").strip() or "Oman"
    hit = lookup_hs(product)
    pq = hit["name"] if hit else product  # English name searches far better than Persian
    ar = AR_NAMES.get(hit["name"]) if hit else None
    is_gulf = any(g in market.lower() or g in market for g in GULF_WORDS)
    if mode == "buyers":
        queries = [f"{pq} importers {market} company", f"{pq} wholesale trading LLC {market}",
                   f"{pq} importer directory {market} contact"]
        if ar and is_gulf:
            queries.append(f"مستورد {ar} {market}")
    elif mode == "suppliers":
        queries = [f"{pq} exporter producer supplier {market}", f"{pq} manufacturer wholesale {market}",
                   f"{pq} exporters directory {market}"]
    else:
        queries = [f"{market} customs import requirements {pq}", f"{market} import permit {pq} ministry official"]

    raw_results = multi_search(queries, limit=24, per_query=8)
    results = raw_results
    dropped = 0
    if mode in ("buyers", "suppliers") and raw_results:
        n_raw = len(raw_results)
        kept = [r for r in raw_results
                if not any(urlparse(r["url"]).netloc.lower().removeprefix("www.").endswith(h) for h in INFO_HOSTS)]
        pk = [product] + ([hit["name"]] if hit else []) + ([ar] if ar else [])
        results = filter_relevant(kept, pk, market_keywords(market))
        dropped = n_raw - len(results)
        if not results:
            msg = ("نتایج پیدا شد ولی هیچ‌کدام همزمان به کالا و بازار انتخاب‌شده اشاره نمی‌کردند، پس چیزی نمایش داده نمی‌شود (چیزی ساخته نشد). "
                   "برای خریدار واقعی از Trade Map / UN Comtrade (فهرست کشورها و واردکنندگان)، دایرکتوری اتاق بازرگانی مقصد (مثلاً OCCI برای عمان) "
                   "و فهرست غرفه‌داران نمایشگاه‌های غذایی/کشاورزی استفاده کنید."
                   if language == "FA" else
                   "Results were found but none mentioned both the product and the chosen market, so nothing is shown (nothing was invented). "
                   "For real buyers use Trade Map / UN Comtrade, the destination chamber-of-commerce directory (e.g. OCCI for Oman) "
                   "and exhibitor lists of food/agri trade fairs.")
            return msg, 0
    if not results:
        msg = ("جست‌وجوی وب در این اجرا هیچ نتیجه‌ای بازیابی نکرد، بنابراین **هیچ شرکت یا اطلاعات تماسی نمایش داده نمی‌شود** (چیزی ساخته نشد). "
               "برای نتیجه پایدارتر، `TAVILY_API_KEY` را در Secrets اضافه کنید."
               if language == "FA" else
               "Web search returned nothing, so **no companies or contacts are shown** (nothing was invented). "
               "For more reliable results add `TAVILY_API_KEY` to Secrets.")
        return msg, 0

    source_block = format_search_results(results)
    engine = st.session_state.get("search_engine") or "web"
    heading = "### منابع بازیابی‌شده" if language == "FA" else "### Retrieved sources"
    table = f"{heading} ({engine})\n" + sources_table(results, language)
    if dropped:
        table += (f"\n\n_{dropped} نتیجه نامرتبط (بدون اشاره به کالا) حذف شد._" if language == "FA"
                  else f"\n\n_{dropped} irrelevant results (not mentioning the product) were hidden._")
    if not ai_ready:
        return table, len(results)

    if mode in ("buyers", "suppliers"):
        task = ("Return a markdown table: Organization | Type | What the source says | Source # | Confidence (High/Medium/Low). "
                "List ONLY organizations that are named in the sources. If a source is only an article, directory or marketplace, say so. "
                "Do NOT output emails, phone numbers or addresses unless they appear verbatim in a snippet. "
                "Give 'High' confidence ONLY if the snippet shows the organization actually trades this product; otherwise Low. "
                "Do not merge details of different sources into one organization. End with short 'next verification steps'.")
    else:
        task = ("Summarize import/customs requirements ONLY where a snippet explicitly supports them, citing Source #. "
                "List everything else as 'must verify with the official customs authority'. "
                "Do not state duty or tax rates unless a snippet gives them.")
    prompt = f"""Mode: {mode}
Product: {product}
Market: {market}
Today: {date.today().isoformat()}
{hs_instruction(product)}

SOURCES (the ONLY information you may use):
{source_block}

Task: {task}
{clean_farsi_prompt(language)}"""
    analysis = call_ai(prompt, language, web_search=False)
    analysis = scrub_unverified(analysis, source_block, [r["url"] for r in results], scrub_links=True)
    analysis = hs_guard(analysis, product, language)
    return analysis.strip() + "\n\n" + table, len(results)


# ---------------- calculator ----------------
def calculate_price(quantity, unit_purchase, inland, freight, insurance, duty_pct, vat_pct, bank_pct, other,
                    margin_pct, currency="USD", language="FA"):
    q = parse_number(quantity)
    unit = parse_number(unit_purchase)
    vals = {
        "inland": parse_number(inland) or 0,
        "freight": parse_number(freight) or 0,
        "insurance": parse_number(insurance) or 0,
        "duty_pct": parse_number(duty_pct) or 0,
        "vat_pct": parse_number(vat_pct) or 0,
        "bank_pct": parse_number(bank_pct) or 0,
        "other": parse_number(other) or 0,
        "margin_pct": parse_number(margin_pct) or 0,
    }
    fa = language == "FA"
    if q is None or unit is None or q <= 0 or unit < 0:
        return None, ("برای محاسبه قطعی، مقدار و قیمت خرید هر واحد را وارد کنید." if fa
                      else "Enter a valid quantity and unit purchase price.")
    detected = detect_currencies(unit_purchase)
    if detected and currency not in detected:
        return None, (f"قیمت خرید به نظر با ارز {', '.join(sorted(detected))} نوشته شده ولی ارز انتخاب‌شده {currency} است. "
                      "ارز را درست انتخاب کنید یا قیمت را تبدیل کنید." if fa else
                      f"The unit price looks like it is in {', '.join(sorted(detected))} but the selected currency is {currency}. "
                      "Fix the currency or convert the price.")
    if vals["margin_pct"] >= 100 or vals["margin_pct"] < 0:
        return None, ("حاشیه سود باید بین ۰ و کمتر از ۱۰۰ باشد." if fa else "Margin must be between 0 and under 100.")

    goods = q * unit
    customs_value = goods + vals["freight"] + vals["insurance"]
    duty = customs_value * vals["duty_pct"] / 100
    vat_base = customs_value + duty
    vat = vat_base * vals["vat_pct"] / 100
    pre_bank_cost = goods + vals["inland"] + vals["freight"] + vals["insurance"] + duty + vat + vals["other"]
    bank_fee = pre_bank_cost * vals["bank_pct"] / 100
    total_cost = pre_bank_cost + bank_fee
    sale_price = total_cost / (1 - vals["margin_pct"] / 100)   # true margin on the sale price
    unit_sale = sale_price / q
    markup_pct = (sale_price / total_cost - 1) * 100 if total_cost else 0.0

    return {
        "quantity": q, "unit_purchase": unit, "goods": goods, "currency": currency,
        "customs_value": customs_value, "duty": duty, "vat_base": vat_base,
        "vat": vat, "bank_fee": bank_fee, "total_cost": total_cost,
        "sale_price": sale_price, "unit_sale": unit_sale, "markup_pct": markup_pct, **vals,
    }, None


def calculator_markdown(c, language):
    cur = c["currency"]
    if language == "FA":
        return f"""### نتیجه محاسبه تجاری

| ردیف | مبلغ |
|---|---:|
| ارزش کالا | {money(c['goods'], cur)} |
| حمل داخلی | {money(c['inland'], cur)} |
| حمل بین‌المللی | {money(c['freight'], cur)} |
| بیمه | {money(c['insurance'], cur)} |
| ارزش مبنای گمرکی مدل | {money(c['customs_value'], cur)} |
| حقوق و عوارض گمرکی | {money(c['duty'], cur)} |
| VAT / مالیات واردات | {money(c['vat'], cur)} |
| کارمزد بانک / LC | {money(c['bank_fee'], cur)} |
| سایر هزینه‌ها | {money(c['other'], cur)} |
| **هزینه نهایی مدل (Landed Cost)** | **{money(c['total_cost'], cur)}** |
| **قیمت فروش پیشنهادی با حاشیه سود {pct(c['margin_pct'])}** | **{money(c['sale_price'], cur)}** |
| معادل افزایش روی هزینه (Markup) | {pct(c['markup_pct'])} |
| **قیمت فروش هر واحد** | **{money(c['unit_sale'], cur)}** |"""
    return f"""### Calculation Result

| Item | Amount |
|---|---:|
| Goods value | {money(c['goods'], cur)} |
| Inland transport | {money(c['inland'], cur)} |
| International freight | {money(c['freight'], cur)} |
| Insurance | {money(c['insurance'], cur)} |
| Model customs value | {money(c['customs_value'], cur)} |
| Customs duty | {money(c['duty'], cur)} |
| Import VAT | {money(c['vat'], cur)} |
| Bank / LC fee | {money(c['bank_fee'], cur)} |
| Other costs | {money(c['other'], cur)} |
| **Model landed cost** | **{money(c['total_cost'], cur)}** |
| **Suggested sale price at {pct(c['margin_pct'])} margin** | **{money(c['sale_price'], cur)}** |
| Equivalent markup on cost | {pct(c['markup_pct'])} |
| **Suggested sale price / unit** | **{money(c['unit_sale'], cur)}** |"""


# ---------------- PDF ----------------
def int_to_words(n: int) -> str:
    if n == 0:
        return "zero"
    ones = ("one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
            "fifteen sixteen seventeen eighteen nineteen").split()
    tens = "twenty thirty forty fifty sixty seventy eighty ninety".split()

    def below1000(k: int) -> str:
        parts = []
        if k >= 100:
            parts.append(ones[k // 100 - 1] + " hundred")
            k %= 100
        if k >= 20:
            parts.append(tens[k // 10 - 2] + ("-" + ones[k % 10 - 1] if k % 10 else ""))
        elif k > 0:
            parts.append(ones[k - 1])
        return " ".join(parts)

    out = []
    for name, size in (("billion", 10 ** 9), ("million", 10 ** 6), ("thousand", 1000)):
        if n >= size:
            out.append(below1000(n // size) + " " + name)
            n %= size
    if n:
        out.append(below1000(n))
    return " ".join(out)


def amount_in_words(x: float) -> str:
    whole = int(x)
    cents = int(round((x - whole) * 100))
    if cents == 100:
        whole, cents = whole + 1, 0
    s = f"{int_to_words(whole)} US dollars"
    if cents:
        s += f" and {cents:02d}/100"
    return s.capitalize() + " only"


def valid_until(validity: str) -> str:
    m = re.search(r"(\d+)\s*day", (validity or "").lower())
    if m:
        return (date.today() + timedelta(days=int(m.group(1)))).isoformat()
    return ""


def make_pdf(d: Dict) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    pdf.setTitle(d["no"])

    def header():
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(48, H - 55, "MEHR ARA COMMERCIAL")
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(48, H - 82, d["type"].upper())
        pdf.line(48, H - 92, W - 48, H - 92)

    header()
    y = H - 120
    for label, value in d["rows"]:
        lines = []
        for part in (str(value).splitlines() or [""]):
            lines += simpleSplit(part, "Helvetica", 10, W - 48 - 190) or [""]
        if y - (14 * len(lines) + 6) < 120:
            pdf.showPage()
            header()
            y = H - 120
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(48, y, label + ":")
        pdf.setFont("Helvetica", 10)
        for ln in lines:
            pdf.drawString(190, y, ln)
            y -= 14
        y -= 6
    pdf.line(48, 100, 230, 100)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(48, 88, "Authorized signature / stamp")
    pdf.setFont("Helvetica-Oblique", 8)
    pdf.drawString(48, 62, "Prices and terms are subject to written confirmation. Generated by Mehr Ara AI Trade Employee.")
    pdf.save()
    return buf.getvalue()


# ----------------------------- CSS ----------------------------
BASE_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
.block-container{padding-top:1.2rem;padding-bottom:3rem;max-width:1450px}
.hero{padding:30px 34px;border-radius:22px;background:linear-gradient(135deg,#101827,#1b2b43);border:1px solid #293b55;margin-bottom:22px}
.hero-title{font-size:clamp(25px,4vw,38px);font-weight:800;color:#f5f8fc;margin-bottom:8px}
.hero-subtitle{font-size:16px;color:#c6d2e3;max-width:900px;line-height:1.8}
.badge{display:inline-block;padding:6px 12px;border-radius:999px;background:#293b55;color:#e7effb;font-size:12px;margin-bottom:14px}
.metric-card,.action-card{padding:19px;border-radius:16px;background:#152238;border:1px solid #2c405e;min-height:115px}
.metric-label{color:#b9c7da;font-size:13px}.metric-value{font-size:28px;font-weight:800;color:#fff;margin-top:7px}
.action-title{font-size:17px;font-weight:750;color:#f4f7fb;margin:8px 0}.action-description{font-size:13px;color:#bdcbe0;line-height:1.6}
.section-title{font-size:23px;font-weight:750;margin-top:30px;margin-bottom:13px}
.warning-box{padding:13px 16px;border-radius:10px;background:#fff8e5;border:1px solid #f2d58a;color:#684f10}
.small-muted{color:#78869a;font-size:12px}
/* tables: scroll horizontally instead of being cut off on mobile */
[data-testid="stMarkdownContainer"] table{display:block;max-width:100%;overflow-x:auto;border-collapse:collapse}
[data-testid="stMarkdownContainer"] th,[data-testid="stMarkdownContainer"] td{vertical-align:top;padding:6px 10px;word-break:break-word}
/* code blocks (e.g. the RFQ text) stay left-to-right and wrap instead of being cut off */
[data-testid="stMarkdownContainer"] pre, [data-testid="stMarkdownContainer"] code{direction:ltr !important;text-align:left !important;white-space:pre-wrap !important;word-break:break-word}
@media (max-width:640px){
  .hero{padding:20px 18px}.hero-subtitle{font-size:14px}.metric-value{font-size:22px}
  .metric-card,.action-card{min-height:auto;padding:14px}.section-title{font-size:19px}
}
</style>
"""

RTL_CSS = """
<style>
html, body, [data-testid="stMarkdownContainer"], .hero, .metric-card, .action-card, .section-title, label, input, textarea {
    font-family: 'Vazirmatn', 'Segoe UI', sans-serif !important;
}
[data-testid="stMarkdownContainer"], .hero, .metric-card, .action-card, .section-title, .warning-box {
    direction: rtl; text-align: right;
}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] td, [data-testid="stMarkdownContainer"] th {
    unicode-bidi: plaintext;
}
</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)
if st.session_state.language == "FA":
    st.markdown(RTL_CSS, unsafe_allow_html=True)

# ----------------------------- sidebar ------------------------
groq_ready = has_key("GROQ_API_KEY")
or_ready = has_key("OPENROUTER_API_KEY")
ai_ready = groq_ready or or_ready

with st.sidebar:
    st.markdown("## 🤖 Mehr Ara")
    language = st.selectbox("Language / زبان", ["FA", "EN"], index=0 if st.session_state.language == "FA" else 1)
    if language != st.session_state.language:
        st.session_state.language = language
        st.rerun()
    T = LANG[st.session_state.language]
    st.divider()
    st.markdown("### AI Configuration")
    st.success("✓ Groq API Ready" if groq_ready else "⚠ Groq API not configured")
    st.success("✓ OpenRouter API Ready" if or_ready else "○ OpenRouter backup not configured")
    st.success("✓ Tavily search Ready" if has_key("TAVILY_API_KEY") else "○ Tavily not configured (using basic scraping)")
    if not has_key("APP_PASSWORD"):
        st.warning("⚠ APP_PASSWORD not set: anyone with the link can use your API keys / SMTP.")
    st.divider()
    st.markdown("### Trade Employee\n\n• Sell & Source\n\n• Export Planning\n\n• Customs Check\n\n• Buyer/Supplier Search\n\n• PDF & Email/WhatsApp")

T = LANG[st.session_state.language]

# ----------------------------- header -------------------------
st.markdown(f'<div class="hero"><div class="badge">AI-POWERED COMMERCIAL OPERATIONS</div><div class="hero-title">{T["title"]}</div><div class="hero-subtitle">{T["subtitle"]}</div></div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
mode = st.session_state.last_provider or ("Groq" if groq_ready else "OpenRouter" if or_ready else "Demo")
cnt = st.session_state.counters
for col, label, value in [
    (m1, T["active_cases"], str(cnt["cases"])),
    (m2, T["buyer_leads"], str(cnt["buyers"])),
    (m3, T["suppliers"], str(cnt["suppliers"])),
    (m4, T["ai_mode"], mode),
]:
    with col:
        st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

st.markdown(f'<div class="section-title">{T["today"]}</div>', unsafe_allow_html=True)
actions = [
    ("📦", T["sell"], "Find markets, buyers and prepare a sales workflow."),
    ("🔎", T["source"], "Find and compare potential suppliers."),
    ("🚢", T["export"], "Prepare an export plan, cost structure and documents."),
    ("🎯", T["buyers"], "Research current buyers and build an outreach workflow."),
    ("💰", T["pricing"], "Calculate documented commercial pricing."),
    ("📁", T["operations"], "Manage trade cases, documents and follow-ups."),
]
cols = st.columns(3)
for i, (emoji, title, description) in enumerate(actions):
    with cols[i % 3]:
        st.markdown(f'<div class="action-card"><div style="font-size:27px">{emoji}</div><div class="action-title">{title}</div><div class="action-description">{description}</div></div>', unsafe_allow_html=True)
        if st.button(title, key=f"workflow_{i}", use_container_width=True):
            st.session_state.selected_action = title
            st.rerun()

# -------------------------- trade request ---------------------
st.markdown(f'<div class="section-title">{T["request"]}</div>', unsafe_allow_html=True)
st.info(f"Selected workflow: **{st.session_state.selected_action}**")
c1, c2 = st.columns(2)
with c1:
    product = st.text_input(T["product"], placeholder="مثال: زعفران نگین")
    quantity = st.text_input(T["quantity"], placeholder="مثال: 20 kg")
    origin = st.text_input(T["origin"], placeholder="مثال: Mashhad, Iran")
    incoterm = st.selectbox(T["incoterm"], [""] + INCOTERMS, format_func=lambda x: x if x else "—")
with c2:
    destination = st.text_input(T["destination"], placeholder="مثال: Muscat, Oman")
    budget = st.text_input(T["budget"], placeholder="مثال: USD 2,000")
    payment = st.text_input(T["payment"], placeholder="خالی بگذارید تا به‌عنوان «باید مشخص شود» ثبت شود")
    fx_text = st.text_input(T["fx"], placeholder="مثال: 1,000,000")
    notes = st.text_area(T["notes"], placeholder="زمان تحویل، کیفیت، بسته‌بندی...", height=100)

if st.button(T["generate"], type="primary", use_container_width=True):
    st.session_state.market_price_result = None
    market_text = ""
    market_data = None
    fx_rate = parse_number(fx_text)
    if fx_rate is not None and fx_rate <= 0:
        fx_rate = None
    if product and quantity and ai_ready:
        with st.spinner("در حال جستجوی قیمت فعلی بازار..." if st.session_state.language == "FA" else "Researching market price..."):
            market_text = market_price_research(product, quantity, origin, destination, st.session_state.language, fx_rate)
        market_data = extract_market_price(market_text)
        st.session_state.market_price_result = {"text": market_text, "data": market_data, "product": product, "quantity": quantity, "destination": destination}
        if not str(st.session_state.get("calc_qty", "")).strip():
            parsed_q = parse_number(quantity)
            if parsed_q:
                st.session_state["calc_qty"] = str(parsed_q)

    if st.session_state.language == "FA":
        sec = ["خلاصه مدیریتی", "حقایق در برابر فرضیات", "قیمت مرجع بازار و Incoterm", "راهبرد خریدار و تأمین‌کننده",
               "چک‌لیست گمرک، HS Code و انطباق واردات", "برنامه عملیاتی ۵ تا ۷ روزه", "پیش‌نویس RFQ / پیام تجاری"]
        status = "تأییدشده با منبع / باید تأیید شود / اعلام‌شده توسط کاربر"
        missing = "باید توسط کاربر مشخص شود"
    else:
        sec = ["Executive summary", "Known facts vs assumptions", "Market price benchmark and Incoterm", "Buyer and supplier strategy",
               "Customs, HS Code and import-compliance checklist", "5-7 day action plan", "Draft RFQ / commercial message"]
        status = "verified-by-source / must-verify / user-provided"
        missing = "must be specified by the user"
    prompt = f"""Trade case for Mehr Ara:
Workflow: {st.session_state.selected_action}
Product: {product or 'Not provided'}
Quantity: {quantity or 'Not provided'}
Origin: {origin or 'Not provided'}
Destination: {destination or 'Not provided'}
Budget / target: {budget or 'Not provided'}
Incoterm: {incoterm or 'NOT PROVIDED — must be specified by the user; do not assume one'}
FX rate (toman per 1 USD): {fx_text.strip() if fx_text.strip() else 'NOT PROVIDED — must be specified by the user; do not guess an exchange rate'}
Payment terms: {payment or 'NOT PROVIDED — must be specified by the user; do not assume LC or any other method'}
Additional requirements: {notes or 'Not provided'}

{hs_instruction(product)}

LIVE MARKET PRICE RESEARCH (already normalized and verified by code; do not recompute or invent other prices):
{market_text or 'No live market price research available.'}

{clean_farsi_prompt(st.session_state.language)}

Create an operational report with exactly these sections as ## headings (use these exact titles, no numbers):
## {sec[0]}
## {sec[1]} (table; mark every missing input as '{missing}')
## {sec[2]} (only from the research above; if it says UNAVAILABLE, say the benchmark could not be verified)
## {sec[3]}: describe TYPES of buyers/suppliers and channels only. Do NOT name specific companies, emails or phones here — named leads come only from the Live Trade Research section.
## {sec[4]} (use HS_REFERENCE only; mark each item with one status: {status}; the HS Code row must read 'candidate (internal table) — official classification required', never 'verified')
## {sec[5]}
## {sec[6]}
"""
    with st.spinner(T["working"]):
        result = call_ai(prompt, st.session_state.language, web_search=False)
    allowed = " ".join([market_text, product, quantity, origin, destination, budget, payment, incoterm, fx_text, notes])
    result = scrub_unverified(result, allowed, URL_RE.findall(market_text or ""), scrub_links=True)
    result = hs_guard(result, product, st.session_state.language)
    st.session_state.last_trade_case = {
        "action": st.session_state.selected_action,
        "product": product,
        "quantity": quantity,
        "origin": origin,
        "destination": destination,
        "budget": budget,
        "payment": payment,
        "incoterm": incoterm,
        "fx": fx_text,
        "notes": notes,
        "result": result
    }
    st.session_state.counters["cases"] += 1
    st.session_state["show_latest_result"] = True

if st.session_state.get("show_latest_result") and st.session_state.last_trade_case:
    st.markdown(f'<div class="section-title">{T["result"]}</div>', unsafe_allow_html=True)
    tc_now = st.session_state.last_trade_case
    if involves_iran(tc_now.get("origin", ""), tc_now.get("destination", "")):
        st.warning("⚠️ مبدأ/مقصد ایران است: روش پرداخت (به‌ویژه LC)، بانک‌های درگیر، تحریم‌ها و محدودیت‌های صادرات/واردات باید پیش از معامله با بانک، کارگزار گمرکی و مشاور حقوقی تأیید شود. این اپ آن‌ها را تأیید نمی‌کند."
                   if st.session_state.language == "FA" else
                   "⚠️ Iran is the origin/destination: the payment method (especially an LC), the banks involved, sanctions and export/import restrictions must be verified with your bank, a customs broker and legal counsel before any deal. This app does not confirm them.")
    with st.container(border=True):
        provider = st.session_state.last_provider or "Demo"
        model = st.session_state.last_model or ""
        st.caption(f"🤖 AI Provider: {provider} • {model}" if model else f"🤖 AI Provider: {provider}")
        if st.session_state.fallback_note:
            st.caption(f"↪ fallback used — {st.session_state.fallback_note}")
        st.markdown(tc_now["result"])
    mp = st.session_state.get("market_price_result")
    if mp and mp.get("text"):
        with st.expander("📊 Market price research / تحقیق قیمت بازار"):
            if mp.get("data"):
                d = mp["data"]
                st.caption(f"Benchmark traced to sources: USD {d['low']:,.2f} – {d['high']:,.2f} per kg (unverified; confirm with real quotations)")
            st.markdown(strip_machine_line(mp["text"]))

# -------------------------- calculator ------------------------
st.markdown(f'<div class="section-title">{T["pricing_title"]}</div>', unsafe_allow_html=True)
st.caption("💡 برای فروش FOB/CIF/CFR به خریدار خارجی، حقوق گمرکی و مالیات واردات کشور مقصد معمولاً با خریدار است؛ این دو را فقط برای قیمت DDP پر کنید. VAT واردات هم برای ثبت‌نام‌شدگان اغلب قابل بازیافت است."
           if st.session_state.language == "FA" else
           "💡 For FOB/CIF/CFR sales to a foreign buyer, destination import duty and VAT are normally the buyer's cost; fill them only for DDP quotes. Import VAT is often recoverable for registered importers.")
mp_calc = st.session_state.get("market_price_result")
if mp_calc and mp_calc.get("data"):
    d = mp_calc["data"]
    st.caption(f"Market benchmark (unverified, from search sources): USD {d['low']:,.2f} – {d['high']:,.2f} per kg. Enter YOUR actual purchase price below.")
q1, q2, q3 = st.columns(3)
with q1:
    calc_cur = st.selectbox(T["calc_currency"], CURRENCIES, key="calc_cur")
    calc_qty = st.text_input(T["quantity"], key="calc_qty")
    calc_unit = st.text_input(T["purchase_unit"], placeholder="مثال: 80", key="calc_unit")
    calc_inland = st.text_input(T["inland"], key="calc_inland")
with q2:
    calc_freight = st.text_input(T["freight"], key="calc_freight")
    calc_ins = st.text_input(T["insurance"], key="calc_ins")
    calc_duty = st.text_input(T["duty"], key="calc_duty")
    calc_vat = st.text_input(T["vat"], key="calc_vat")
with q3:
    calc_bank = st.text_input(T["bank"], key="calc_bank")
    calc_other = st.text_input(T["other"], key="calc_other")
    calc_margin = st.text_input(T["margin"], key="calc_margin")
    if st.button(T["calculate"], type="secondary", use_container_width=True):
        calc, err = calculate_price(calc_qty, calc_unit, calc_inland, calc_freight, calc_ins, calc_duty, calc_vat,
                                    calc_bank, calc_other, calc_margin, calc_cur, st.session_state.language)
        st.session_state.calc_result = (None, err) if err else (calc, None)

if st.session_state.calc_result:
    calc, err = st.session_state.calc_result
    with st.container(border=True):
        if err:
            st.warning(err)
        else:
            st.markdown(calculator_markdown(calc, st.session_state.language))

# ---------------------- live research -------------------------
st.markdown(f'<div class="section-title">{T["research"]}</div>', unsafe_allow_html=True)
st.caption(T["research_caption"])
if product and not st.session_state.research_product:
    st.session_state["research_product"] = product
if destination and st.session_state.research_market == "Oman":
    st.session_state["research_market"] = destination

r1, r2, r3 = st.columns(3)
with r1:
    research_mode = st.selectbox(
        "Research type / نوع تحقیق", ["buyers", "suppliers", "customs"],
        format_func=lambda k: {"buyers": T["buyer_research"], "suppliers": T["supplier_research"], "customs": T["customs"]}[k],
    )
with r2:
    research_product = st.text_input("Product / کالا", key="research_product")
with r3:
    research_market = st.text_input("Market / بازار", key="research_market")

if st.button(T["research_run"], use_container_width=True):
    if not research_product.strip():
        st.warning("نام کالا را وارد کنید." if st.session_state.language == "FA" else "Enter a product name.")
    else:
        with st.spinner(T["research_working"]):
            research, n_sources = run_live_research(research_mode, research_product, research_market, st.session_state.language, ai_ready)
        st.session_state.research_result = research
        if research_mode == "buyers":
            st.session_state.counters["buyers"] += n_sources
        elif research_mode == "suppliers":
            st.session_state.counters["suppliers"] += n_sources

if st.session_state.research_result:
    with st.container(border=True):
        st.markdown(st.session_state.research_result)

# ---------------------- invoice & document center with email & whatsapp ----------------------
st.markdown('<div class="section-title">Invoice & Dispatch Center / صدور پیش‌فاکتور و ارسال به مشتری</div>', unsafe_allow_html=True)
st.caption("صدور پیش‌فاکتور یا سفارش خرید، دانلود PDF و ارسال به ایمیل یا واتساپ. متن‌های داخل PDF باید انگلیسی باشند.")

last_case = st.session_state.get("last_trade_case") or {}


def safe_default(v: str) -> str:
    return v if pdf_safe(v) else ""


_hs_hit = lookup_hs(last_case.get("product", ""))
_inc_default = last_case.get("incoterm", "")
_inc_options = [""] + INCOTERMS

with st.form("invoice_form"):
    inv_cols = st.columns(2)
    with inv_cols[0]:
        inv_type = st.selectbox("نوع سند", ["Proforma Invoice (Buyer)", "Purchase Order (Supplier)"])
        inv_no = st.text_input("شماره سند", value=f"MA-{date.today().strftime('%Y%m%d')}-001")
        inv_seller = st.text_input("صادرکننده سند / Issuer (English)", value="Mehr Ara")
        inv_seller_addr = st.text_input("آدرس صادرکننده (English)")
        inv_buyer = st.text_input("نام طرف مقابل: خریدار یا تأمین‌کننده (English)")
        inv_product = st.text_input("شرح کالا (English)", value=safe_default(last_case.get("product", "")))
        inv_origin_country = st.text_input("کشور مبدأ کالا (English)", placeholder="Iran")
        customer_email = st.text_input("ایمیل مشتری (برای ارسال خودکار)", placeholder="client@example.com")
    with inv_cols[1]:
        inv_qty = st.text_input("مقدار و واحد", value=safe_default(last_case.get("quantity", "")))
        inv_unit_price = st.text_input("قیمت هر واحد (USD)", value="")
        inv_hs = st.text_input("HS Code (candidate — verify)", value=(_hs_hit["code"] if _hs_hit else ""))
        customer_phone = st.text_input("شماره واتساپ مشتری (با کد کشور)", placeholder="+96891234567")
        inv_incoterm = st.selectbox("Incoterm", _inc_options, index=_inc_options.index(_inc_default) if _inc_default in _inc_options else 0,
                                    format_func=lambda x: x if x else "—")
        inv_payment = st.text_input("شرایط پرداخت (الزامی، English)", value=safe_default(last_case.get("payment", "")))
        inv_validity = st.text_input("اعتبار سند (مثلاً 7 days)", value="7 days")
        inv_bank = st.text_area("اطلاعات بانکی (اختیاری، English)", height=80)

    inv_confirm = st.checkbox("اطلاعات سند، مشخصات کالا و قیمت‌ها را بازبینی و تایید می‌کنم.")
    inv_submit = st.form_submit_button("تولید نهایی سند و آماده‌سازی ارسال", type="primary", use_container_width=True)

if inv_submit:
    qv = parse_number(inv_qty)
    uv = parse_number(inv_unit_price)
    pdf_fields = {
        "document type": inv_type, "document no.": inv_no, "issuer": inv_seller, "issuer address": inv_seller_addr,
        "counterparty": inv_buyer, "product": inv_product, "country of origin": inv_origin_country,
        "quantity": inv_qty, "HS code": inv_hs, "payment terms": inv_payment, "validity": inv_validity, "bank details": inv_bank,
    }
    non_latin = [k for k, v in pdf_fields.items() if not pdf_safe(v)]
    if not inv_confirm:
        st.error("لطفاً تایید اطلاعات سند را علامت بزنید.")
    elif not inv_product.strip() or not inv_buyer.strip() or qv is None or uv is None or qv <= 0 or uv < 0:
        st.error("شرح کالا، نام طرف مقابل، مقدار و قیمت واحد معتبر الزامی است.")
    elif not inv_payment.strip():
        st.error("شرایط پرداخت را خودتان مشخص کنید (به‌صورت پیش‌فرض فرض نمی‌شود).")
    elif not inv_incoterm:
        st.error("Incoterm را انتخاب کنید (به‌صورت پیش‌فرض فرض نمی‌شود).")
    elif non_latin:
        st.error("PDF فقط حروف انگلیسی (Latin) را پشتیبانی می‌کند. این فیلدها را انگلیسی بنویسید: " + ", ".join(non_latin))
    else:
        total = qv * uv
        is_po = inv_type.startswith("Purchase")
        doc_name = "Purchase Order" if is_po else "Proforma Invoice"
        vu = valid_until(inv_validity)
        rows = [
            ("Document No.", inv_no), ("Date", date.today().isoformat()),
            ("Buyer (issuer)" if is_po else "Seller", inv_seller),
        ]
        if inv_seller_addr.strip():
            rows.append(("Address", inv_seller_addr))
        rows += [
            ("Supplier" if is_po else "Buyer", inv_buyer),
            ("Product", inv_product), ("Quantity", inv_qty),
        ]
        if inv_origin_country.strip():
            rows.append(("Country of Origin", inv_origin_country))
        if inv_hs.strip():
            rows.append(("HS Code (candidate)", inv_hs))
        rows += [
            ("Unit Price", f"USD {uv:,.2f}"), ("Total Goods Value", f"USD {total:,.2f}"),
            ("Amount in Words", amount_in_words(total)),
            ("Incoterm", inv_incoterm), ("Payment Terms", inv_payment),
            ("Validity", inv_validity + (f" (until {vu})" if vu else "")),
        ]
        if inv_bank.strip():
            rows.append(("Bank Details", inv_bank))
        st.session_state["generated_pdf"] = make_pdf({"no": inv_no, "type": doc_name, "rows": rows})
        st.session_state["inv_details"] = {
            "no": inv_no, "buyer": inv_buyer, "total": total, "doc_name": doc_name, "is_po": is_po,
            "email": customer_email.strip(), "phone": customer_phone, "product": inv_product
        }
        st.success(f"سند {inv_no} با موفقیت آماده شد! کل مبلغ: USD {total:,.2f}")

if "generated_pdf" in st.session_state and st.session_state.get("inv_details"):
    det = st.session_state["inv_details"]
    st.markdown("---")
    st.markdown("### 📤 ارسال و دانلود سند")

    col_dl, col_em, col_wa = st.columns(3)

    with col_dl:
        st.download_button(
            "📥 دانلود فایل PDF",
            data=st.session_state["generated_pdf"],
            file_name=f"{det['no']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col_em:
        if st.button("📧 ارسال به ایمیل", use_container_width=True):
            if st.session_state.emails_sent >= 5:
                st.error("سقف ارسال ایمیل در این نشست (۵ عدد) پر شده است.")
            elif not det["email"] or not EMAIL_RE.fullmatch(det["email"]):
                st.error("ایمیل مشتری را درست وارد کنید.")
            else:
                try:
                    smtp_server = get_secret("SMTP_SERVER", "smtp.gmail.com")
                    smtp_port = int(get_secret("SMTP_PORT", "587"))
                    smtp_user = get_secret("SMTP_USER")
                    smtp_pass = get_secret("SMTP_PASSWORD")
                    sender_email = get_secret("SENDER_EMAIL", smtp_user)

                    if not smtp_user or not smtp_pass:
                        st.error("تنظیمات SMTP (ایمیل فرستنده، نام کاربری و رمز عبور) در Secrets تنظیم نشده است.")
                    else:
                        msg = EmailMessage()
                        msg["Subject"] = f"{det['doc_name']} {det['no']} - Mehr Ara"
                        msg["From"] = sender_email
                        msg["To"] = det["email"]
                        msg.set_content(f"Dear {det['buyer']},\n\nPlease find attached the {det['doc_name']} {det['no']} for {det['product']}.\nTotal Amount: USD {det['total']:,.2f}.\n\nBest regards,\nMehr Ara Trade Team")
                        msg.add_attachment(st.session_state["generated_pdf"], maintype="application", subtype="pdf", filename=f"{det['no']}.pdf")

                        smtp_cls = smtplib.SMTP_SSL if smtp_port == 465 else smtplib.SMTP
                        with smtp_cls(smtp_server, smtp_port, timeout=30) as server:
                            if smtp_port != 465:
                                server.starttls()
                            server.login(smtp_user, smtp_pass)
                            server.send_message(msg)
                        st.session_state.emails_sent += 1
                        st.success(f"سند با موفقیت به ایمیل {det['email']} ارسال شد!")
                except Exception as e:
                    st.error(f"خطا در ارسال ایمیل: {e}")

    with col_wa:
        clean_phone = re.sub(r"\D", "", det["phone"] or "")
        if clean_phone:
            fa_name = "سفارش خرید" if det["is_po"] else "پیش‌فاکتور"
            wa_msg = quote_plus(f"سلام {det['buyer']} عزیز، {fa_name} شماره {det['no']} به مبلغ USD {det['total']:,.2f} برای کالا ({det['product']}) صادر شد. فایل PDF را جداگانه برایتان ارسال می‌کنم. - گروه بازرگانی مهرآرا")
            st.link_button("💬 باز کردن واتساپ با پیام آماده", f"https://wa.me/{clean_phone}?text={wa_msg}", use_container_width=True)
            st.caption("واتساپ فقط متن را پیش‌پر می‌کند؛ فایل PDF را بعد از باز شدن گفتگو دستی پیوست کنید.")
        else:
            st.caption("شماره واتساپ مشتری را در فرم وارد کنید.")

# ----------------------------- chat ----------------------------
st.markdown(f'<div class="section-title">{T["assistant"]}</div>', unsafe_allow_html=True)
st.caption(T["chat"])
for item in st.session_state.chat_history:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

user_message = st.chat_input(T["message"])
if user_message:
    st.session_state.chat_history.append({"role": "user", "content": user_message})
    context = ""
    if st.session_state.last_trade_case:
        tc = st.session_state.last_trade_case
        context = (f"Current case: Product={tc['product']}; Quantity={tc['quantity']}; Origin={tc['origin']}; "
                   f"Destination={tc['destination']}; Incoterm={tc.get('incoterm') or 'not specified'}; "
                   f"Payment terms={tc.get('payment') or 'not specified'}")
    prior = st.session_state.chat_history[:-1][-8:]
    answer = call_ai(f"{context}\n{hs_instruction((st.session_state.last_trade_case or {}).get('product', ''))}\nUser follow-up: {user_message}",
                     st.session_state.language, prior, web_search=False)
    allowed_chat = " ".join([context, st.session_state.get("research_result") or "",
                             (st.session_state.last_trade_case or {}).get("result", "")]
                            + [m["content"] for m in st.session_state.chat_history if m["role"] == "user"])
    answer = scrub_unverified(answer, allowed_chat, URL_RE.findall(allowed_chat), scrub_links=True)
    st.session_state.chat_history.append({"role": "assistant", "content": answer})
    st.rerun()

with st.expander("Diagnostics"):
    st.write({
        "provider": st.session_state.last_provider,
        "model": st.session_state.last_model,
        "fallback_note": st.session_state.fallback_note,
        "last_error": st.session_state.last_error,
        "search_engine": st.session_state.search_engine,
    })

st.markdown("---")
st.markdown(f'<div class="warning-box">⚠️ {T["demo_notice"]}</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;margin-top:22px" class="small-muted">Mehr Ara AI Trade Employee • Commercial Intelligence</div>', unsafe_allow_html=True)
