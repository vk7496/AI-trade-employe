import os
import re
import smtplib
from email.message import EmailMessage
from html.parser import HTMLParser
from urllib.parse import quote_plus, urlparse
from typing import Optional, Tuple, List, Dict

import httpx
import streamlit as st
from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ============================================================
# MEHR ARA AI TRADE EMPLOYEE
# Groq primary -> OpenRouter backup -> Demo fallback
# Includes deterministic pricing, live web research via Groq,
# buyer/supplier discovery, customs/compliance, PDF, and Email/WhatsApp dispatch.
# ============================================================

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

st.set_page_config(
    page_title="Mehr Ara AI Trade Employee",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

LANG = {
    "EN": {
        "title": "MEHR ARA AI TRADE EMPLOYEE",
        "subtitle": "A digital commercial employee for selling, sourcing, exporting, pricing, document generation and communication.",
        "today": "What do you want your digital employee to do today?",
        "sell": "Sell a Product", "source": "Source a Product", "export": "Export a Product",
        "buyers": "Find Buyers", "pricing": "Calculate Price", "operations": "Trade Operations",
        "assistant": "AI Trade Employee", "active_cases": "Active Cases", "buyer_leads": "Buyer Leads",
        "suppliers": "Suppliers", "ai_mode": "AI Mode", "demo": "Demo Mode", "ai": "AI",
        "request": "Trade Request", "product": "Product", "quantity": "Quantity", "origin": "Origin",
        "destination": "Destination", "budget": "Budget / Target Price", "notes": "Additional Requirements",
        "generate": "Generate Trade Plan", "result": "AI Employee Result", "chat": "Ask your AI Trade Employee",
        "message": "Message", "working": "AI Trade Employee is preparing the work...",
        "pricing_title": "Commercial Price Calculator", "calculate": "Calculate Commercial Price",
        "purchase_unit": "Purchase price / unit", "inland": "Inland transport", "freight": "International freight",
        "insurance": "Insurance", "duty": "Customs duty %", "vat": "Import VAT %", "bank": "Bank / LC fee %",
        "other": "Other costs", "margin": "Target margin %", "research": "Live Trade Research",
        "research_caption": "Uses Groq web search for current companies, buyers, suppliers and official regulatory sources.",
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
        "assistant": "نیروی هوشمند بازرگانی", "active_cases": "پرونده‌های فعال", "buyer_leads": "سرنخ‌های خریدار",
        "suppliers": "تأمین‌کنندگان", "ai_mode": "حالت هوش مصنوعی", "demo": "حالت نمایشی", "ai": "Groq AI",
        "request": "درخواست بازرگانی", "product": "کالا", "quantity": "مقدار", "origin": "مبدأ",
        "destination": "مقصد", "budget": "بودجه / قیمت هدف", "notes": "نیازمندی‌های بیشتر",
        "generate": "ساخت برنامه بازرگانی", "result": "خروجی نیروی هوشمند", "chat": "از نیروی هوشمند بازرگانی بپرسید",
        "message": "پیام", "working": "نیروی هوشمند در حال آماده‌سازی نتیجه است...",
        "pricing_title": "محاسبه‌گر قیمت تجاری", "calculate": "محاسبه قیمت",
        "purchase_unit": "قیمت خرید هر واحد", "inland": "حمل داخلی", "freight": "حمل بین‌المللی",
        "insurance": "بیمه", "duty": "حقوق و عوارض گمرکی %", "vat": "مالیات واردات / VAT %", "bank": "کارمزد بانک / LC %",
        "other": "سایر هزینه‌ها", "margin": "حاشیه سود هدف %", "research": "تحقیق زنده بازرگانی",
        "research_caption": "برای یافتن شرکت‌ها، خریداران، تأمین‌کنندگان و منابع رسمی مقرراتی از جستجوی وب استفاده می‌شود.",
        "research_run": "شروع تحقیق", "customs": "گمرک و انطباق", "buyer_research": "پیدا کردن خریدار",
        "supplier_research": "پیدا کردن تأمین‌کننده", "research_working": "در حال جستجوی منابع به‌روز...",
        "demo_notice": "قیمت، هزینه حمل، تعرفه، مالیات، اطلاعات تماس و الزامات قانونی باید پیش از معامله تأیید شوند.",
    },
}

# ----------------------------- state --------------------------
for key, default in {
    "language": "FA",
    "selected_action": "فروش کالا",
    "chat_history": [],
    "last_trade_case": None,
    "last_error": None,
    "last_provider": None,
    "last_model": None,
    "research_result": None,
    "calc_result": None,
    "market_price_result": None,
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
            if self._current and self._current.get("title") and self._current.get("url", "").startswith("http"):
                self.results.append(self._current)
            self._current = None
            self._in_result = False
            self._snippet = False
        elif tag in ("p", "div"):
            self._snippet = False


def live_web_search(query: str, limit: int = 6) -> List[Dict[str, str]]:
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
                return results
        except Exception:
            continue
    return []


def format_search_results(results: List[Dict[str, str]]) -> str:
    if not results:
        return "NO SEARCH RESULTS RETURNED."
    return "\n\n".join(
        f"[{i}] {r['title']}\nURL: {r['url']}\nSnippet: {r.get('snippet') or 'No snippet available'}"
        for i, r in enumerate(results, 1)
    )


def demo_response(language: str) -> str:
    if language == "FA":
        return """### گزارش نمایشی

این پاسخ در **حالت Demo** تولید شده و به اطلاعات زنده بازار متصل نیست.

برای اجرای واقعی باید مشخصات کالا، مقدار، واحد قیمت، Incoterm، هزینه‌های حمل، شرایط پرداخت و الزامات واردات تأیید شوند."""
    return """### Demo Trade Report

This is a clearly labeled demo response. Live prices, duties, taxes, freight, company contacts and stock must be verified before execution."""


def clean_farsi_prompt(language: str) -> str:
    if language == "FA":
        return """پاسخ را کاملاً به فارسی طبیعی و حرفه‌ای بنویس. از فارسی استاندارد استفاده کن. اصطلاحات استاندارد تجارت بین‌الملل مانند USD, kg, MT, FOB, CIF, CFR, EXW, LC, RFQ و HS Code را در لاتین نگه دار. جدول‌ها را خوانا و منظم بنویس."""
    return "Write clear professional English with consistent terminology and readable Markdown tables."


def provider_call(provider: str, model: str, prompt: str, language: str, history=None, web_search=False) -> Tuple[bool, str, str]:
    key_name = "GROQ_API_KEY" if provider == "Groq" else "OPENROUTER_API_KEY"
    api_key = get_secret(key_name)
    if not api_key:
        return False, "", f"{key_name} is missing"

    messages = [{
        "role": "system",
        "content": f"""You are Mehr Ara AI Trade Employee, a practical B2B trade operations analyst.

{clean_farsi_prompt(language)}

Reliability and compliance rules:
- Never invent a real company, person, phone, WhatsApp, email, quotation, stock level, market price, freight rate, tariff, tax, permit, certificate, legal requirement or customs procedure.
- Clearly distinguish: 1) User-provided facts, 2) Estimate/assumption, 3) Must verify.
- For any current buyer/supplier/company research, use web search when enabled and provide the source URL/title for each important result.
- For customs/legal questions, prefer official government/customs/tax sources. Do not present a legal requirement as confirmed unless an authoritative source supports it.
- For pricing, show arithmetic, units and formulas.
- For HS Code, give a candidate only when the product description supports it, and label it 'candidate HS Code — official classification required'.
"""}]
    if history:
        messages.extend(history[-8:])
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 3200,
    }
    if provider == "Groq" and web_search:
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
            return content
        errors.append(f"Groq / {model}: {detail}")

    or_model = get_secret("OPENROUTER_MODEL", "openrouter/free")
    ok, content, detail = provider_call("OpenRouter", or_model, prompt, language, history, web_search=False)
    if ok:
        st.session_state.last_provider = "OpenRouter"
        st.session_state.last_model = or_model
        st.session_state.last_error = None
        return content
    errors.append(f"OpenRouter / {or_model}: {detail}")

    st.session_state.last_provider = "Demo"
    st.session_state.last_model = None
    st.session_state.last_error = " | ".join(errors)
    return demo_response(language)


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


def market_price_research(product: str, quantity: str, origin: str, destination: str, language: str) -> str:
    query = f'wholesale B2B price {product} per kg supplier quotation {origin} {destination} 2026'
    results = live_web_search(query, limit=8)
    if not results:
        results = live_web_search(f'{product} exporter wholesale price per kg quotation', limit=8)
    source_block = format_search_results(results)
    if not results:
        return ("**قیمت بازار تأیید نشد.** جست‌وجوی وب در این اجرا نتیجه قابل بازیابی نداد.\n\nMARKET_PRICE_RANGE_USD_PER_KG: UNAVAILABLE")

    prompt = f"""You are the commercial market analyst for Mehr Ara AI Trade Employee.
Analyze ONLY the web search results supplied below.
Product: {product or 'not specified'}
Quantity: {quantity or 'not specified'}
Origin: {origin or 'not specified'}
Destination: {destination or 'not specified'}
Current date: 2026-10-12

Search results retrieved now:
{source_block}

Output exactly one machine-readable line:
MARKET_PRICE_RANGE_USD_PER_KG: <low>-<high>
Or if not supported:
MARKET_PRICE_RANGE_USD_PER_KG: UNAVAILABLE
{clean_farsi_prompt(language)}"""
    analysis = call_ai(prompt, language, web_search=False)
    source_footer = "\n\n### منابع جست‌وجوشده\n" + "\n".join(
        f"- [{r['title']}]({r['url']}) — {r.get('snippet') or ''}"
        for r in results
    )
    if "MARKET_PRICE_RANGE_USD_PER_KG:" not in analysis:
        analysis += "\n\nMARKET_PRICE_RANGE_USD_PER_KG: UNAVAILABLE"
    st.session_state.last_provider = st.session_state.last_provider or "Groq"
    return analysis.strip() + source_footer


def calculate_price(quantity, unit_purchase, inland, freight, insurance, duty_pct, vat_pct, bank_pct, other, margin_pct):
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
    if q is None or unit is None or q <= 0 or unit < 0:
        return None, "برای محاسبه قطعی، مقدار و قیمت خرید هر واحد را وارد کنید."

    goods = q * unit
    customs_value = goods + vals["freight"] + vals["insurance"]
    duty = customs_value * vals["duty_pct"] / 100
    vat_base = customs_value + duty
    vat = vat_base * vals["vat_pct"] / 100
    pre_bank_cost = goods + vals["inland"] + vals["freight"] + vals["insurance"] + duty + vat + vals["other"]
    bank_fee = pre_bank_cost * vals["bank_pct"] / 100
    total_cost = pre_bank_cost + bank_fee
    sale_price = total_cost * (1 + vals["margin_pct"] / 100)
    unit_sale = sale_price / q

    return {
        "quantity": q, "unit_purchase": unit, "goods": goods,
        "customs_value": customs_value, "duty": duty, "vat_base": vat_base,
        "vat": vat, "bank_fee": bank_fee, "total_cost": total_cost,
        "sale_price": sale_price, "unit_sale": unit_sale, **vals,
    }, None


def calculator_markdown(c, language):
    if language == "FA":
        return f"""### نتیجه محاسبه تجاری

| ردیف | مبلغ |
|---|---:|
| ارزش کالا | {money(c['goods'])} |
| حمل داخلی | {money(c['inland'])} |
| حمل بین‌المللی | {money(c['freight'])} |
| بیمه | {money(c['insurance'])} |
| ارزش مبنای گمرکی مدل | {money(c['customs_value'])} |
| حقوق و عوارض گمرکی | {money(c['duty'])} |
| VAT / مالیات واردات | {money(c['vat'])} |
| کارمزد بانک / LC | {money(c['bank_fee'])} |
| سایر هزینه‌ها | {money(c['other'])} |
| **هزینه نهایی مدل (Landed Cost)** | **{money(c['total_cost'])}** |
| **قیمت فروش پیشنهادی با {pct(c['margin_pct'])} سود** | **{money(c['sale_price'])}** |
| **قیمت فروش هر واحد** | **{money(c['unit_sale'])}** |"""
    return f"""### Calculation Result

| Item | Amount |
|---|---:|
| Goods value | {money(c['goods'])} |
| Inland transport | {money(c['inland'])} |
| International freight | {money(c['freight'])} |
| Insurance | {money(c['insurance'])} |
| Model customs value | {money(c['customs_value'])} |
| Customs duty | {money(c['duty'])} |
| Import VAT | {money(c['vat'])} |
| Bank / LC fee | {money(c['bank_fee'])} |
| Other costs | {money(c['other'])} |
| **Model landed cost** | **{money(c['total_cost'])}** |
| **Suggested sale price at {pct(c['margin_pct'])} margin** | **{money(c['sale_price'])}** |
| **Suggested sale price / unit** | **{money(c['unit_sale'])}** |"""


# ----------------------------- CSS ----------------------------
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)

# ----------------------------- sidebar ------------------------
with st.sidebar:
    st.markdown("## 🤖 Mehr Ara")
    language = st.selectbox("Language / زبان", ["FA", "EN"], index=0 if st.session_state.language == "FA" else 1)
    if language != st.session_state.language:
        st.session_state.language = language
        st.rerun()
    T = LANG[st.session_state.language]
    st.divider()
    st.markdown("### AI Configuration")
    groq_ready = has_key("GROQ_API_KEY")
    or_ready = has_key("OPENROUTER_API_KEY")
    st.success("✓ Groq API Ready" if groq_ready else "⚠ Groq API not configured")
    st.success("✓ OpenRouter API Ready" if or_ready else "○ OpenRouter backup not configured")
    st.divider()
    st.markdown("### Trade Employee\n\n• Sell & Source\n\n• Export Planning\n\n• Customs Check\n\n• Buyer/Supplier Search\n\n• PDF & Email/WhatsApp")

T = LANG[st.session_state.language]

# ----------------------------- header -------------------------
st.markdown(f'<div class="hero"><div class="badge">AI-POWERED COMMERCIAL OPERATIONS</div><div class="hero-title">{T["title"]}</div><div class="hero-subtitle">{T["subtitle"]}</div></div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
mode = st.session_state.last_provider or ("Groq" if groq_ready else "OpenRouter" if or_ready else "Demo")
for col, label, value in [(m1, T["active_cases"], "12"), (m2, T["buyer_leads"], "47"), (m3, T["suppliers"], "31"), (m4, T["ai_mode"], mode)]:
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
with c2:
    destination = st.text_input(T["destination"], placeholder="مثال: Muscat, Oman")
    budget = st.text_input(T["budget"], placeholder="مثال: USD 2,000")
    notes = st.text_area(T["notes"], placeholder="پرداخت، زمان تحویل، کیفیت، بسته‌بندی...", height=115)

if st.button(T["generate"], type="primary", use_container_width=True):
    market_text = ""
    market_data = None
    if product and quantity and groq_ready:
        with st.spinner("در حال جستجوی قیمت فعلی بازار..." if st.session_state.language == "FA" else "Researching market price..."):
            market_text = market_price_research(product, quantity, origin, destination, st.session_state.language)
        market_data = extract_market_price(market_text)
        st.session_state.market_price_result = {"text": market_text, "data": market_data, "product": product, "quantity": quantity, "destination": destination}
        if market_data:
            if not str(st.session_state.get("calc_unit", "")).strip():
                st.session_state["calc_unit"] = f"{market_data['mid']:.2f} USD/kg"
            if not str(st.session_state.get("calc_qty", "")).strip():
                parsed_q = parse_number(quantity)
                if parsed_q:
                    st.session_state["calc_qty"] = str(parsed_q)

    prompt = f"""Trade case for Mehr Ara:
Workflow: {st.session_state.selected_action}
Product: {product or 'Not provided'}
Quantity: {quantity or 'Not provided'}
Origin: {origin or 'Not provided'}
Destination: {destination or 'Not provided'}
Budget / target: {budget or 'Not provided'}
Additional requirements: {notes or 'Not provided'}

LIVE MARKET PRICE RESEARCH:
{market_text or 'No live market price research available.'}

{clean_farsi_prompt(st.session_state.language)}

Create an operational report with:
1. Executive summary / خلاصه مدیریتی
2. Known facts vs assumptions table
3. Current market price benchmark & Incoterm
4. Buyer/supplier strategy
5. Customs, HS Code and import-compliance checklist for destination
6. 5-7 day action plan
7. Draft RFQ/commercial message
"""
    with st.spinner(T["working"]):
        result = call_ai(prompt, st.session_state.language, web_search=bool(groq_ready))
    st.session_state.last_trade_case = {
        "action": st.session_state.selected_action,
        "product": product,
        "quantity": quantity,
        "origin": origin,
        "destination": destination,
        "budget": budget,
        "notes": notes,
        "result": result
    }
    st.session_state["show_latest_result"] = True

if st.session_state.get("show_latest_result") and st.session_state.last_trade_case:
    st.markdown(f'<div class="section-title">{T["result"]}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        provider = st.session_state.last_provider or "Demo"
        model = st.session_state.last_model or ""
        st.caption(f"🤖 AI Provider: {provider} • {model}" if model else f"🤖 AI Provider: {provider}")
        st.markdown(st.session_state.last_trade_case["result"])

# -------------------------- calculator ------------------------
st.markdown(f'<div class="section-title">{T["pricing_title"]}</div>', unsafe_allow_html=True)
q1, q2, q3 = st.columns(3)
with q1:
    calc_qty = st.text_input(T["quantity"], value=quantity if 'quantity' in locals() else "20", key="calc_qty")
    calc_unit = st.text_input(T["purchase_unit"], placeholder="مثال: 80 USD/kg", key="calc_unit")
    calc_inland = st.text_input(T["inland"], value="0", key="calc_inland")
    calc_freight = st.text_input(T["freight"], value="0", key="calc_freight")
with q2:
    calc_ins = st.text_input(T["insurance"], value="0", key="calc_ins")
    calc_duty = st.text_input(T["duty"], value="0", key="calc_duty")
    calc_vat = st.text_input(T["vat"], value="0", key="calc_vat")
    calc_bank = st.text_input(T["bank"], value="0", key="calc_bank")
with q3:
    calc_other = st.text_input(T["other"], value="0", key="calc_other")
    calc_margin = st.text_input(T["margin"], value="10", key="calc_margin")
    if st.button(T["calculate"], type="secondary", use_container_width=True):
        calc, err = calculate_price(calc_qty, calc_unit, calc_inland, calc_freight, calc_ins, calc_duty, calc_vat, calc_bank, calc_other, calc_margin)
        if err:
            st.session_state.calc_result = (None, err)
        else:
            st.session_state.calc_result = (calc, None)

if st.session_state.calc_result:
    calc, err = st.session_state.calc_result
    with st.container(border=True):
        if err:
            st.warning(err)
        else:
            st.markdown(calculator_markdown(calc, st.session_state.language))

# ---------------------- live research -------------------------
st.markdown(f'<div class="section-title">{T["research"]}</div>', unsafe_allow_html=True)
r1, r2, r3 = st.columns(3)
with r1:
    research_mode = st.selectbox("Research type / نوع تحقیق", [T["buyer_research"], T["supplier_research"], T["customs"]])
with r2:
    research_product = st.text_input("Product / کالا", value=product if 'product' in locals() else "", key="research_product")
with r3:
    research_market = st.text_input("Market / بازار", value=destination if 'destination' in locals() else "Oman", key="research_market")

if st.button(T["research_run"], use_container_width=True):
    if not groq_ready:
        st.warning("برای تحقیق زنده باید GROQ_API_KEY فعال باشد.")
    else:
        if research_mode == T["buyer_research"]:
            prompt = f"Find current potential BUYERS/importers for {research_product or 'product'} in {research_market or 'Oman'}. Use web search and return a markdown table of leads with source URLs."
        elif research_mode == T["supplier_research"]:
            prompt = f"Find current potential SUPPLIERS/producers for {research_product or 'product'} in {research_market or 'market'}. Use web search and return a markdown table with source URLs."
        else:
            prompt = f"Research CUSTOMS / IMPORT COMPLIANCE requirements for importing {research_product or 'product'} into {research_market or 'Oman'}. Cite official sources."
        
        with st.spinner(T["research_working"]):
            web_results = live_web_search(f"{research_product} {research_market} official website", limit=8)
            if web_results:
                prompt += "\n\nWEB SEARCH RESULTS:\n" + format_search_results(web_results)
            research = call_ai(prompt, st.session_state.language, web_search=False)
            if web_results:
                research += "\n\n### منابع بازیابی‌شده\n" + "\n".join(f"- [{r['title']}]({r['url']})" for r in web_results)
        st.session_state.research_result = research

if st.session_state.research_result:
    with st.container(border=True):
        st.markdown(st.session_state.research_result)

# ---------------------- invoice & document center with email & whatsapp ----------------------
st.markdown('<div class="section-title">Invoice & Dispatch Center / صدور پیش‌فاکتور و ارسال به مشتری</div>', unsafe_allow_html=True)
st.caption("صدور پیش‌فاکتور رسمی، دانلود PDF و ارسال مستقیم به ایمیل یا واتساپ مشتری.")

# اصلاح ایمن برای جلوگیری از ارور NoneType (رفع مشکل گزارش‌شده کاربر)
last_case = st.session_state.get("last_trade_case") or {}

with st.form("invoice_form"):
    inv_cols = st.columns(2)
    with inv_cols[0]:
        inv_type = st.selectbox("نوع سند", ["Proforma Invoice — Buyer", "Purchase Order — Supplier"])
        inv_no = st.text_input("شماره سند", value=f"MA-{date.today().strftime('%Y%m%d')}-001")
        inv_seller = st.text_input("فروشنده / صادرکننده", value="Mehr Ara")
        inv_buyer = st.text_input("نام خریدار / شرکت مقابل")
        inv_product = st.text_input("شرح کالا", value=last_case.get("product", ""))
        customer_email = st.text_input("ایمیل مشتری (برای ارسال خودکار)", placeholder="client@example.com")
    with inv_cols[1]:
        inv_qty = st.text_input("مقدار و واحد", value=last_case.get("quantity", ""))
        inv_unit_price = st.text_input("قیمت هر واحد (USD)", value="")
        customer_phone = st.text_input("شماره واتساپ مشتری (با کد کشور)", placeholder="+96891234567")
        inv_incoterm = st.selectbox("Incoterm", ["EXW", "FCA", "FOB", "CFR", "CIF", "DAP", "DDP"], index=4)
        inv_payment = st.text_input("شرایط پرداخت", value="LC at Sight / T.T.")
        inv_validity = st.text_input("اعتبار پیش‌فاکتور", value="7 days")
    
    inv_confirm = st.checkbox("اطلاعات پیش‌فاکتور، مشخصات کالا و قیمت‌ها را بازبینی و تایید می‌کنم.")
    inv_submit = st.form_submit_button("تولید نهایی پیش‌فاکتور و آماده‌سازی ارسال", type="primary", use_container_width=True)

if inv_submit:
    qv = parse_number(inv_qty)
    uv = parse_number(inv_unit_price)
    if not inv_confirm:
        st.error("لطفاً تایید اطلاعات پیش‌فاکتور را علامت بزنید.")
    elif not inv_product.strip() or not inv_buyer.strip() or qv is None or uv is None or qv <= 0 or uv < 0:
        st.error("شرح کالا، نام خریدار، مقدار و قیمت واحد معتبر الزامی است.")
    else:
        total = qv * uv
        # ساخت PDF در حافظه
        buf = BytesIO()
        pdf = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        pdf.setTitle(inv_no)
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(48, height-55, "MEHR ARA COMMERCIAL")
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(48, height-85, inv_type)
        pdf.setFont("Helvetica", 10)
        rows = [
            ("Document No.", inv_no), ("Date", date.today().isoformat()),
            ("Seller", inv_seller), ("Buyer", inv_buyer),
            ("Product", inv_product), ("Quantity", inv_qty),
            ("Unit Price", f"USD {uv:,.2f}"), ("Total Goods Value", f"USD {total:,.2f}"),
            ("Incoterm", inv_incoterm), ("Payment Terms", inv_payment),
            ("Validity", inv_validity),
        ]
        y = height - 125
        for label, value in rows:
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(48, y, label + ":")
            pdf.setFont("Helvetica", 10)
            pdf.drawString(180, y, str(value)[:95])
            y -= 25
        pdf.save()
        pdf_bytes = buf.getvalue()
        st.session_state["generated_pdf"] = pdf_bytes
        st.session_state["inv_details"] = {
            "no": inv_no, "buyer": inv_buyer, "total": total, 
            "email": customer_email, "phone": customer_phone, "product": inv_product
        }
        st.success(f"پیش‌فاکتور {inv_no} با موفقیت آماده شد! کل مبلغ: USD {total:,.2f}")

# دکمه‌های دانلود، ارسال ایمیل و ارسال واتساپ (خارج از فرم برای تعامل روان)
if "generated_pdf" in st.session_state and st.session_state.get("inv_details"):
    det = st.session_state["inv_details"]
    st.markdown("---")
    st.markdown("### 📤 ارسال و دانلود پیش‌فاکتور")
    
    col_dl, col_em, col_wa = st.columns(3)
    
    with col_dl:
        st.download_button(
            "📥 دانلود فایل PDF پیش‌فاکتور", 
            data=st.session_state["generated_pdf"], 
            file_name=f"{det['no']}.pdf", 
            mime="application/pdf", 
            use_container_width=True
        )
        
    with col_em:
        if st.button("📧 ارسال پیش‌فاکتور به ایمیل", use_container_width=True):
            if not det["email"]:
                st.error("لطفاً ایمیل مشتری را وارد کنید.")
            else:
                try:
                    # خواندن تنظیمات SMTP از Streamlit Secrets
                    smtp_server = get_secret("SMTP_SERVER", "smtp.gmail.com")
                    smtp_port = int(get_secret("SMTP_PORT", "587"))
                    smtp_user = get_secret("SMTP_USER")
                    smtp_pass = get_secret("SMTP_PASSWORD")
                    sender_email = get_secret("SENDER_EMAIL", smtp_user)
                    
                    if not smtp_user or not smtp_pass:
                        st.error("تنظیمات SMTP (ایمیل فرستنده، نام کاربری و رمز عبور) در Secrets تنظیم نشده است.")
                    else:
                        msg = EmailMessage()
                        msg["Subject"] = f"Proforma Invoice {det['no']} - Mehr Ara"
                        msg["From"] = sender_email
                        msg["To"] = det["email"]
                        msg.set_content(f"Dear {det['buyer']},\n\nPlease find attached the Proforma Invoice {det['no']} for {det['product']}.\nTotal Amount: USD {det['total']:,.2f}.\n\nBest regards,\nMehr Ara Trade Team")
                        
                        msg.add_attachment(st.session_state["generated_pdf"], maintype="application", subtype="pdf", filename=f"{det['no']}.pdf")
                        
                        with smtplib.SMTP(smtp_server, smtp_port) as server:
                            server.starttls()
                            server.login(smtp_user, smtp_pass)
                            server.send_message(msg)
                        st.success(f"پیش‌فاکتور با موفقیت به ایمیل {det['email']} ارسال شد!")
                except Exception as e:
                    st.error(f"خطا در ارسال ایمیل: {e}")

    with col_wa:
        if st.button("💬 ارسال لینک/پیام به واتساپ", use_container_width=True):
            if not det["phone"]:
                st.error("لطفاً شماره واتساپ مشتری را وارد کنید.")
            else:
                wa_msg = quote_plus(f"سلام {det['buyer']} عزیز، پیش‌فاکتور شماره {det['no']} به مبلغ USD {det['total']:,.2f} برای کالا ({det['product']}) صادر گردید. لطفاً فایل را بررسی فرمایید. - گروه بازرگانی مهرآرا")
                clean_phone = re.sub(r"\D", "", det["phone"])
                whatsapp_url = f"https://wa.me/{clean_phone}?text={wa_msg}"
                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:8px; font-weight:bold; cursor:pointer;">کلیک برای ارسال در واتساپ ↗</button></a>', unsafe_allow_html=True)

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
        context = f"Current case: Product={tc['product']}; Quantity={tc['quantity']}; Origin={tc['origin']}; Destination={tc['destination']}"
    prior = st.session_state.chat_history[:-1][-8:]
    answer = call_ai(f"{context}\nUser follow-up: {user_message}", st.session_state.language, prior, web_search=bool(groq_ready))
    st.session_state.chat_history.append({"role": "assistant", "content": answer})
    st.rerun()

st.markdown("---")
st.markdown(f'<div class="warning-box">⚠️ {T["demo_notice"]}</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;margin-top:22px" class="small-muted">Mehr Ara AI Trade Employee • Commercial Intelligence</div>', unsafe_allow_html=True)
