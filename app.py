import os
import re
from typing import Optional, Tuple

import httpx
import streamlit as st

# ============================================================
# MEHR ARA AI TRADE EMPLOYEE
# Groq primary -> OpenRouter backup -> Demo fallback
# Includes deterministic pricing, live web research via Groq,
# buyer/supplier discovery, and customs/compliance verification.
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
        "subtitle": "A digital commercial employee for selling, sourcing, exporting, pricing and follow-up.",
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
        "subtitle": "نیروی دیجیتال برای فروش، تأمین، صادرات، قیمت‌گذاری و پیگیری امور بازرگانی.",
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
        "research_caption": "برای یافتن شرکت‌ها، خریداران، تأمین‌کنندگان و منابع رسمی مقرراتی از جستجوی وب Groq استفاده می‌شود.",
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
    # Keep decimal point; extract first normal numeric value.
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


def demo_response(language: str) -> str:
    if language == "FA":
        return """### گزارش نمایشی

این پاسخ در **حالت Demo** تولید شده و به اطلاعات زنده بازار متصل نیست.

برای اجرای واقعی باید مشخصات کالا، مقدار، واحد قیمت، Incoterm، هزینه‌های حمل، شرایط پرداخت و الزامات واردات تأیید شوند.

**قانون مهم:** قیمت بازار، تعرفه گمرکی، مالیات، هزینه حمل، موجودی و اطلاعات تماس نباید حدس زده شوند."""
    return """### Demo Trade Report

This is a clearly labeled demo response. Live prices, duties, taxes, freight, company contacts and stock must be verified before execution."""


def clean_farsi_prompt(language: str) -> str:
    if language == "FA":
        return """پاسخ را کاملاً به فارسی طبیعی و حرفه‌ای بنویس. از فارسی استاندارد استفاده کن و از ترکیب تصادفی فارسی با انگلیسی، عربی، روسی یا حروف نامرتبط جلوگیری کن. اصطلاحات استاندارد تجارت بین‌الملل مانند USD, kg, MT, FOB, CIF, CFR, EXW, LC, RFQ و HS Code را در لاتین نگه دار. جدول‌ها را خوانا و منظم بنویس."""
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
- For customs/legal questions, prefer official government/customs/tax sources. Do not present a legal requirement as confirmed unless a current authoritative source supports it.
- For pricing, show arithmetic, units and formulas. Never replace an unknown cost with a guessed number.
- For HS Code, give a candidate only when the product description supports it, and label it 'candidate HS Code — official classification required'.
- Never claim that a buyer or supplier is verified merely because a company appears on a search result.
- Avoid filler. Make the answer operational and specific.
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
    # Primary: Groq 120B, fallback: Groq 20B.
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

    # Backup: OpenRouter. The free router is preferred, but can be overridden in Secrets.
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
    """Extract a deliberately machine-readable USD/kg market benchmark from the research response.
    We never invent a number here: if the AI/web research does not provide the marker, return None.
    """
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
    """Live market-price research. Groq GPT-OSS browser search is used; no hard-coded price is used."""
    prompt = f"""You are the live market-pricing researcher for Mehr Ara AI Trade Employee.

Research the CURRENT 2026 wholesale/B2B market price for this trade request:
Product: {product or 'Not provided'}
Quantity: {quantity or 'Not provided'}
Origin: {origin or 'Not provided'}
Destination: {destination or 'Not provided'}

Use browser search and prioritize:
1) recent supplier quotations/listings for the same product and grade;
2) credible trade-market sources;
3) official trade statistics such as UN Comtrade/WITS as a historical benchmark, clearly labeled as historical/unit-value data.

Rules:
- Do NOT invent a price.
- Do NOT mix retail per-gram prices with wholesale per-kg prices.
- Do NOT treat an old trade statistic as today's quotation.
- If the product is saffron, distinguish Super Negin/Negin/Sargol/Pushal and only use the requested grade when it is known. If grade is missing, explicitly say that grade is required and give separate ranges only when sources support them.
- Prefer at least two independent current/recent sources when available.
- State Incoterm for every direct quotation (EXW/FOB/CIF/etc.). Never convert EXW/FOB/CIF into another Incoterm unless a documented cost supports the conversion.
- The result is a MARKET BENCHMARK, not a confirmed supplier quotation.

At the end, output EXACTLY one machine-readable line in this format if a defensible wholesale range is available:
MARKET_PRICE_RANGE_USD_PER_KG: <low>-<high>
If no defensible USD/kg range is available, output:
MARKET_PRICE_RANGE_USD_PER_KG: UNAVAILABLE

Then output:
MARKET_PRICE_BASIS: <one sentence explaining the basis and Incoterm>
MARKET_PRICE_CONFIDENCE: HIGH|MEDIUM|LOW

Also provide a short readable explanation with source names/URLs and the date of each relevant source.
{clean_farsi_prompt(language)}"""
    return call_ai(prompt, language, web_search=True)

# ------------------------- deterministic calculator ----------
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
    # Simplified commercial estimate. Exact VAT/customs valuation must be verified.
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
        return f"""### نتیجه محاسبه

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
| **هزینه نهایی مدل** | **{money(c['total_cost'])}** |
| **قیمت فروش پیشنهادی با {pct(c['margin_pct'])} سود** | **{money(c['sale_price'])}** |
| **قیمت فروش هر واحد** | **{money(c['unit_sale'])}** |

**فرمول:** `قیمت فروش = هزینه نهایی × (1 + حاشیه سود)`

> ⚠️ مبنای Customs Duty و VAT در این ابزار یک **مدل برآورد تجاری** است. نرخ و مبنای قانونی باید برای HS Code و کشور مقصد از مرجع رسمی گمرک/مالیات تأیید شود."""
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
| **Suggested sale price / unit** | **{money(c['unit_sale'])}** |

**Formula:** `Sale price = Total cost × (1 + margin)`

> ⚠️ Customs duty and VAT are modeled estimates here. Verify the legal rate and tax base for the actual HS Code and destination with official authorities."""

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
.result-panel{background:#fff;color:#1c2735;border:1px solid #d7dee8;border-radius:14px;padding:20px 24px}
.result-panel h1,.result-panel h2,.result-panel h3,.result-panel h4{color:#172b4d!important}
.result-panel p,.result-panel li,.result-panel td,.result-panel th{color:#263445!important;line-height:1.75}
.result-panel strong{color:#111827!important}.result-panel table{width:100%;border-collapse:collapse}
.result-panel th,.result-panel td{border:1px solid #d8e0ea;padding:8px 10px}.warning-box{padding:13px 16px;border-radius:10px;background:#fff8e5;border:1px solid #f2d58a;color:#684f10}
.small-muted{color:#78869a;font-size:12px}
.research-card{padding:15px;border-radius:14px;border:1px solid #cbd7e5;background:#f7faff;color:#23344d}
@media(max-width:900px){.action-description{font-size:12px}.hero{padding:22px}.result-panel{padding:14px 12px;overflow-x:auto}}
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
    if groq_ready:
        st.info("AI routing: Groq → OpenRouter → Demo")
    elif or_ready:
        st.info("AI routing: OpenRouter → Demo")
    else:
        st.info("AI routing: Demo only")
    st.markdown("### Models")
    st.caption(f"Groq primary: `{get_secret('GROQ_MODEL','openai/gpt-oss-120b')}`")
    st.caption("Groq fallback: `openai/gpt-oss-20b`")
    st.caption(f"OpenRouter: `{get_secret('OPENROUTER_MODEL','openrouter/free')}`")
    st.divider()
    st.markdown("### Trade Employee\n\n• Sell\n\n• Source\n\n• Export\n\n• Buyers\n\n• Pricing\n\n• Operations")

T = LANG[st.session_state.language]

# ----------------------------- header -------------------------
st.markdown(f'<div class="hero"><div class="badge">AI-POWERED COMMERCIAL OPERATIONS</div><div class="hero-title">{T["title"]}</div><div class="hero-subtitle">{T["subtitle"]}</div></div>', unsafe_allow_html=True)

m1,m2,m3,m4=st.columns(4)
mode = st.session_state.last_provider or ("Groq" if groq_ready else "OpenRouter" if or_ready else "Demo")
for col,label,value in [(m1,T["active_cases"],"12"),(m2,T["buyer_leads"],"47"),(m3,T["suppliers"],"31"),(m4,T["ai_mode"],mode)]:
    with col:
        st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value" style="font-size:{"18px" if len(value)>10 else "28px"}">{value}</div></div>',unsafe_allow_html=True)

st.markdown(f'<div class="section-title">{T["today"]}</div>',unsafe_allow_html=True)
actions=[
    ("📦",T["sell"],"Find markets, buyers and prepare a sales workflow."),
    ("🔎",T["source"],"Find and compare potential suppliers."),
    ("🚢",T["export"],"Prepare an export plan, cost structure and documents."),
    ("🎯",T["buyers"],"Research current buyers and build an outreach workflow."),
    ("💰",T["pricing"],"Calculate documented commercial pricing."),
    ("📁",T["operations"],"Manage trade cases, documents and follow-ups."),
]
cols=st.columns(3)
for i,(emoji,title,description) in enumerate(actions):
    with cols[i%3]:
        st.markdown(f'<div class="action-card"><div style="font-size:27px">{emoji}</div><div class="action-title">{title}</div><div class="action-description">{description}</div></div>',unsafe_allow_html=True)
        if st.button(title,key=f"workflow_{i}",use_container_width=True):
            st.session_state.selected_action=title
            st.rerun()

# -------------------------- trade request ---------------------
st.markdown(f'<div class="section-title">{T["request"]}</div>',unsafe_allow_html=True)
st.info(f"Selected workflow: **{st.session_state.selected_action}**")
c1,c2=st.columns(2)
with c1:
    product=st.text_input(T["product"],placeholder="مثال: زعفران نگین" if st.session_state.language=="FA" else "Example: premium saffron")
    quantity=st.text_input(T["quantity"],placeholder="مثال: 20 kg")
    origin=st.text_input(T["origin"],placeholder="مثال: Mashhad, Iran")
with c2:
    destination=st.text_input(T["destination"],placeholder="مثال: Muscat, Oman")
    budget=st.text_input(T["budget"],placeholder="مثال: USD 2,000 total or USD 100/kg")
    notes=st.text_area(T["notes"],placeholder="پرداخت، زمان تحویل، کیفیت، بسته‌بندی، Incoterm..." if st.session_state.language=="FA" else "Payment, delivery, quality, packaging, Incoterm...",height=115)

if st.button(T["generate"],type="primary",use_container_width=True):
    market_text = ""
    market_data = None
    # When a product/quantity is supplied, obtain a live market benchmark first.
    # This is intentionally separate from the LLM's prose so the calculator can use a traced number.
    if product and quantity and groq_ready:
        with st.spinner("در حال جستجوی قیمت فعلی بازار..." if st.session_state.language=="FA" else "Researching the current market price..."):
            market_text = market_price_research(product, quantity, origin, destination, st.session_state.language)
        market_data = extract_market_price(market_text)
        st.session_state.market_price_result = {"text": market_text, "data": market_data, "product": product, "quantity": quantity, "destination": destination}
        if market_data:
            # Feed ONLY the researched midpoint into the deterministic calculator.
            # User-entered calculator values remain untouched once the user has explicitly entered one.
            if not str(st.session_state.get("calc_unit", "")).strip():
                st.session_state["calc_unit"] = f"{market_data['mid']:.2f} USD/kg"
            if not str(st.session_state.get("calc_qty", "")).strip() or str(st.session_state.get("calc_qty", "")).strip() in {"20", "30"}:
                parsed_q = parse_number(quantity)
                if parsed_q:
                    st.session_state["calc_qty"] = str(parsed_q)

    prompt=f"""Trade case for Mehr Ara:
Workflow: {st.session_state.selected_action}
Product: {product or 'Not provided'}
Quantity: {quantity or 'Not provided'}
Origin: {origin or 'Not provided'}
Destination: {destination or 'Not provided'}
Budget / target: {budget or 'Not provided'}
Additional requirements: {notes or 'Not provided'}

LIVE MARKET PRICE RESEARCH:
{market_text or 'No live market price research was available. Do not invent a price.'}

If the live research contains MARKET_PRICE_RANGE_USD_PER_KG, use that range as the market benchmark. Do not replace it with the user's budget. The budget is a constraint, not evidence of market price.

{clean_farsi_prompt(st.session_state.language)}

Create an operational report with:
1. Executive summary / خلاصه مدیریتی
2. Known facts vs assumptions vs must-verify table
3. Unit and quantity ambiguity check
4. CURRENT MARKET PRICE BENCHMARK: show price/kg, source basis, date and Incoterm; distinguish benchmark from confirmed quotation
5. Compare the user's budget with the market benchmark if a budget was supplied
6. Buyer/supplier strategy
7. Deterministic pricing inputs required
8. Customs, HS Code and import-compliance checklist for the destination
9. Risks and mitigations
10. 5–7 day action plan
11. Draft RFQ/commercial message
12. Three next actions

Never invent missing freight, duty, VAT, stock, contact details or quotation values.
For current regulatory or company information, use live research and cite the source."""
    with st.spinner(T["working"]):
        result=call_ai(prompt,st.session_state.language,web_search=bool(groq_ready))
    if market_data:
        benchmark = (
            f"\n\n### {'بنچمارک قیمت بازار' if st.session_state.language=='FA' else 'Current Market Price Benchmark'}\n"
            f"**USD {market_data['low']:,.0f}–{market_data['high']:,.0f} / kg** "
            f"(midpoint: **USD {market_data['mid']:,.0f}/kg**)\n\n"
            f"For **{parse_number(quantity) or quantity} kg**, indicative goods value = "
            f"**USD {(parse_number(quantity) or 0)*market_data['low']:,.0f}–{(parse_number(quantity) or 0)*market_data['high']:,.0f}**.\n\n"
            f"> This is a live market benchmark from web research, not a confirmed supplier quotation. Verify grade, specification, Incoterm, packaging and supplier quote before issuing an invoice."
        )
        result = result + benchmark
    st.session_state.last_trade_case={"action":st.session_state.selected_action,"product":product,"quantity":quantity,"origin":origin,"destination":destination,"budget":budget,"notes":notes,"result":result}
    st.session_state["show_latest_result"]=True

if st.session_state.get("show_latest_result") and st.session_state.last_trade_case:
    st.markdown(f'<div class="section-title">{T["result"]}</div>',unsafe_allow_html=True)
    with st.container(border=True):
        provider=st.session_state.last_provider or "Demo"
        model=st.session_state.last_model or ""
        st.caption(f"🤖 AI Provider: {provider} • {model}" if model else f"🤖 AI Provider: {provider}")
        st.markdown(st.session_state.last_trade_case["result"])

# ---------------------- market price benchmark ----------------
if st.session_state.get("market_price_result"):
    mp = st.session_state.market_price_result
    st.markdown('<div class="section-title">Live Market Price Benchmark</div>', unsafe_allow_html=True)
    with st.container(border=True):
        if mp.get("data"):
            d = mp["data"]
            qty = parse_number(mp.get("quantity", ""))
            total_low = d["low"] * qty if qty else None
            total_high = d["high"] * qty if qty else None
            if st.session_state.language == "FA":
                st.markdown(f"**بازه فعلی بازار: USD {d['low']:,.0f} تا USD {d['high']:,.0f} به ازای هر کیلو**")
                if qty:
                    st.markdown(f"برای **{qty:g} کیلو**: حدود **USD {total_low:,.0f} تا USD {total_high:,.0f}** فقط ارزش کالا.")
                st.caption("این عدد بنچمارک تحقیق بازار است، نه quotation قطعی تأمین‌کننده. مبنای قیمت و Incoterm باید بررسی شود.")
            else:
                st.markdown(f"**Current market range: USD {d['low']:,.0f}–USD {d['high']:,.0f} per kg**")
                if qty:
                    st.markdown(f"For **{qty:g} kg**: approximately **USD {total_low:,.0f}–USD {total_high:,.0f}** for goods value only.")
                st.caption("This is a market benchmark, not a confirmed supplier quotation. Verify source, grade/specification and Incoterm.")
        st.markdown(mp.get("text", ""))

# -------------------------- calculator ------------------------
st.markdown(f'<div class="section-title">{T["pricing_title"]}</div>',unsafe_allow_html=True)
st.caption("مدل محاسباتی قیمت، مستقل از متن AI است تا عددها قابل ردیابی باشند." if st.session_state.language=="FA" else "The calculator is deterministic and separate from the AI text, so the arithmetic is traceable.")
q1,q2,q3=st.columns(3)
with q1:
    calc_qty=st.text_input(T["quantity"],value=quantity if 'quantity' in locals() else "20",key="calc_qty")
    calc_unit=st.text_input(T["purchase_unit"],placeholder="مثال: 80 USD/kg",key="calc_unit")
    calc_inland=st.text_input(T["inland"],value="0",key="calc_inland")
    calc_freight=st.text_input(T["freight"],value="0",key="calc_freight")
with q2:
    calc_ins=st.text_input(T["insurance"],value="0",key="calc_ins")
    calc_duty=st.text_input(T["duty"],value="0",key="calc_duty")
    calc_vat=st.text_input(T["vat"],value="0",key="calc_vat")
    calc_bank=st.text_input(T["bank"],value="0",key="calc_bank")
with q3:
    calc_other=st.text_input(T["other"],value="0",key="calc_other")
    calc_margin=st.text_input(T["margin"],value="10",key="calc_margin")
    st.caption("واحد همه هزینه‌ها باید یکسان باشد؛ مثلاً USD." if st.session_state.language=="FA" else "Keep all monetary inputs in the same currency, e.g. USD.")
    if st.button(T["calculate"],type="secondary",use_container_width=True):
        calc,err=calculate_price(calc_qty,calc_unit,calc_inland,calc_freight,calc_ins,calc_duty,calc_vat,calc_bank,calc_other,calc_margin)
        if err:
            st.session_state.calc_result=(None,err)
        else:
            st.session_state.calc_result=(calc,None)

if st.session_state.calc_result:
    calc,err=st.session_state.calc_result
    with st.container(border=True):
        if err:
            st.warning(err)
        else:
            st.markdown(calculator_markdown(calc,st.session_state.language))

# ---------------------- live research -------------------------
st.markdown(f'<div class="section-title">{T["research"]}</div>',unsafe_allow_html=True)
st.caption(T["research_caption"])
r1,r2,r3=st.columns(3)
with r1:
    research_mode=st.selectbox("Research type / نوع تحقیق",[T["buyer_research"],T["supplier_research"],T["customs"]])
with r2:
    research_product=st.text_input("Product / کالا",value=product if 'product' in locals() else "",key="research_product")
with r3:
    research_market=st.text_input("Market / بازار",value=destination if 'destination' in locals() else "Oman",key="research_market")

if st.button(T["research_run"],use_container_width=True):
    if not groq_ready:
        st.warning("برای تحقیق زنده باید GROQ_API_KEY فعال باشد." if st.session_state.language=="FA" else "Live research requires GROQ_API_KEY.")
    else:
        if research_mode==T["buyer_research"]:
            prompt=f"""Find current potential BUYERS/importers/distributors for {research_product or 'the specified product'} in {research_market or 'Oman'}.

Use browser search. Prioritize official company websites and credible business sources. Return up to 8 prospects in a Markdown table with: Company, Country/City, Business relevance, Evidence from source, Official website/source URL, and verification status.
Do not invent email, phone or WhatsApp numbers. Only include contact details when visible in the source. Mark every result as 'Lead — not verified' unless there is strong evidence of current business activity.
Also provide a short outreach angle for each lead.
{clean_farsi_prompt(st.session_state.language)}"""
        elif research_mode==T["supplier_research"]:
            prompt=f"""Find current potential SUPPLIERS/producers/exporters for {research_product or 'the specified product'} in or serving {research_market or 'the requested market'}.

Use browser search. Prioritize official company websites, manufacturers, exporters and credible trade sources. Return up to 8 prospects with Company, Location, Product relevance, evidence, official source URL and verification status.
Do not invent contact details or certifications. A directory listing is a lead, not proof of capability. Clearly list what must be checked: specification, MOQ, capacity, certificates, export history, payment terms and quotation authenticity.
{clean_farsi_prompt(st.session_state.language)}"""
        else:
            prompt=f"""Research current CUSTOMS / IMPORT COMPLIANCE requirements for importing {research_product or 'the specified product'} into {research_market or 'Oman'}.

Use browser search and prioritize official government sources such as customs and tax authorities. Return a practical checklist covering: candidate HS classification (not final), customs declaration requirements, duties/taxes, VAT, import permits or product-specific certificates, origin documents, labeling/packaging rules if applicable, prohibited/restricted issues, and official source links.
For every legal or rate claim, cite the source. If the exact rate depends on HS code or product attributes, say so and do not guess.
{clean_farsi_prompt(st.session_state.language)}"""
        with st.spinner(T["research_working"]):
            research=call_ai(prompt,st.session_state.language,web_search=True)
        st.session_state.research_result=research

if st.session_state.research_result:
    with st.container(border=True):
        st.markdown(st.session_state.research_result)

# -------------------------- demo case -------------------------
st.markdown('<div class="section-title">Live Trade Case — Demo</div>',unsafe_allow_html=True)
case_col1,case_col2=st.columns([1.4,1])
with case_col1:
    st.markdown("""### Industrial Material X

**Trade Case:** MA-2026-014

| Field | Value |
|---|---|
| Quantity | 5,000 MT |
| Origin | China |
| Destination | Oman |
| Payment | LC at Sight |
| Target Delivery | ≤ 35 days |
| Status | Sample workflow |

### AI Employee Tasks
- Supplier discovery
- Buyer discovery
- Supplier comparison
- Commercial pricing
- Customs/compliance checks
- RFQ preparation
- Risk identification
- Follow-up tracking
""")
with case_col2:
    st.markdown("""### Supplier Intelligence

**Sample Supplier A**  
China · MOQ: 1,000 MT · Lead time: 28–35 days

**Sample Supplier B**  
China · MOQ: 2,000 MT · Lead time: 25–30 days

**Sample Supplier C**  
China · MOQ: 5,000 MT · Lead time: 30–40 days

⚠️ Fictional demonstration records. Real supplier/buyer research is available above through Groq web search.
""")

# ----------------------------- chat ----------------------------
st.markdown(f'<div class="section-title">{T["assistant"]}</div>',unsafe_allow_html=True)
st.caption(T["chat"])
for item in st.session_state.chat_history:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

user_message=st.chat_input(T["message"])
if user_message:
    st.session_state.chat_history.append({"role":"user","content":user_message})
    context=""
    if st.session_state.last_trade_case:
        tc=st.session_state.last_trade_case
        context=f"""Current case: Product={tc['product']}; Quantity={tc['quantity']}; Origin={tc['origin']}; Destination={tc['destination']}; Budget={tc['budget']}; Notes={tc['notes']}"""
    prior=st.session_state.chat_history[:-1][-8:]
    answer=call_ai(f"{context}\nUser follow-up: {user_message}\nAnswer operationally. If this requires current company, price or legal information, use live research when possible.",st.session_state.language,prior,web_search=bool(groq_ready))
    st.session_state.chat_history.append({"role":"assistant","content":answer})
    st.rerun()

# -------------------------- diagnostics -----------------------
if st.session_state.last_error:
    with st.expander("Connection diagnostics / جزئیات اتصال"):
        st.code(st.session_state.last_error)

st.markdown("---")
st.markdown(f'<div class="warning-box">⚠️ {T["demo_notice"]}</div>',unsafe_allow_html=True)
st.markdown('<div style="text-align:center;margin-top:22px" class="small-muted">Mehr Ara AI Trade Employee • Commercial Intelligence Demo</div>',unsafe_allow_html=True)
