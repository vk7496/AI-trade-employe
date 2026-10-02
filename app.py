import os
from typing import Optional

import httpx
import streamlit as st

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
        "sell": "Sell a Product",
        "source": "Source a Product",
        "export": "Export a Product",
        "buyers": "Find Buyers",
        "pricing": "Calculate Price",
        "operations": "Trade Operations",
        "assistant": "AI Trade Employee",
        "active_cases": "Active Cases",
        "buyer_leads": "Buyer Leads",
        "suppliers": "Suppliers",
        "ai_mode": "AI Mode",
        "demo": "Demo Mode",
        "ai": "OpenRouter AI",
        "request": "Trade Request",
        "product": "Product",
        "quantity": "Quantity",
        "origin": "Origin",
        "destination": "Destination",
        "budget": "Budget / Target Price",
        "notes": "Additional Requirements",
        "generate": "Generate Trade Plan",
        "result": "AI Employee Result",
        "chat": "Ask your AI Trade Employee",
        "message": "Message",
        "demo_notice": "Demo data is illustrative. Verify commercial information before making a transaction.",
        "working": "AI Trade Employee is preparing the work...",
        "api_connected": "OpenRouter key detected",
        "api_missing": "API key not found — Demo Mode",
    },
    "FA": {
        "title": "نیروی هوشمند بازرگانی مهرآرا",
        "subtitle": "نیروی دیجیتال برای فروش، تأمین، صادرات، قیمت‌گذاری و پیگیری امور بازرگانی.",
        "today": "امروز می‌خواهید نیروی دیجیتال شما چه کاری انجام دهد؟",
        "sell": "فروش کالا",
        "source": "تأمین کالا",
        "export": "صادرات کالا",
        "buyers": "پیدا کردن خریدار",
        "pricing": "محاسبه قیمت",
        "operations": "عملیات بازرگانی",
        "assistant": "نیروی هوشمند بازرگانی",
        "active_cases": "پرونده‌های فعال",
        "buyer_leads": "سرنخ‌های خریدار",
        "suppliers": "تأمین‌کنندگان",
        "ai_mode": "حالت هوش مصنوعی",
        "demo": "حالت نمایشی",
        "ai": "هوش مصنوعی OpenRouter",
        "request": "درخواست بازرگانی",
        "product": "کالا",
        "quantity": "مقدار",
        "origin": "مبدأ",
        "destination": "مقصد",
        "budget": "بودجه / قیمت هدف",
        "notes": "نیازمندی‌های بیشتر",
        "generate": "ساخت برنامه بازرگانی",
        "result": "خروجی نیروی هوشمند",
        "chat": "از نیروی هوشمند بازرگانی بپرسید",
        "message": "پیام",
        "demo_notice": "اطلاعات این نسخه نمایشی هستند. پیش از هر معامله، داده‌های تجاری باید بررسی و تأیید شوند.",
        "working": "نیروی هوشمند در حال آماده‌سازی نتیجه است...",
        "api_connected": "کلید OpenRouter شناسایی شد",
        "api_missing": "کلید API پیدا نشد — حالت نمایشی",
    },
}

if "language" not in st.session_state:
    st.session_state.language = "FA"
if "selected_action" not in st.session_state:
    st.session_state.selected_action = "Sell a Product"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_trade_case" not in st.session_state:
    st.session_state.last_trade_case = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None

T = LANG[st.session_state.language]


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read Streamlit secrets safely, then environment variables."""
    try:
        value = st.secrets.get(name, None)
    except Exception:
        value = None
    return value or os.getenv(name) or default


def demo_response(prompt: str, language: str) -> str:
    if language == "FA":
        return """### گزارش نمایشی نیروی هوشمند بازرگانی

**وضعیت:** این پاسخ از الگوی نمایشی ساخته شده و به داده زنده بازار یا شرکت‌ها متصل نیست.

### جمع‌بندی اولیه
برای تبدیل درخواست به پرونده قابل اجرا، ابتدا مشخصات دقیق کالا، واحد مقدار، واحد قیمت، شرایط تحویل و مدارک موردنیاز باید روشن شود.

### اطلاعات موردنیاز
- مشخصات فنی و گرید دقیق کالا
- مقدار و واحد اندازه‌گیری
- قیمت خرید یا قیمت هدف و اینکه مبلغ کل است یا قیمت واحد
- کشور/شهر مبدأ و مقصد
- اینکوترمز، روش حمل و زمان تحویل
- شرایط پرداخت و اسناد موردنیاز

### برنامه اجرایی
1. تکمیل اطلاعات ناقص و ثبت آن در پرونده.
2. تعریف معیارهای انتخاب خریدار یا تأمین‌کننده.
3. تهیه RFQ یا پیام معرفی تجاری.
4. دریافت پیشنهادهای واقعی و مقایسه بر اساس قیمت، کیفیت، MOQ، زمان تحویل و شرایط پرداخت.
5. محاسبه قیمت با هزینه‌های مستند.
6. بررسی ریسک‌ها و آماده‌سازی مدارک برای بازبینی نیروی انسانی.

### مواردی که نباید حدس زده شوند
قیمت بازار، اطلاعات تماس، هزینه حمل، تعرفه، مالیات، مجوزها و موجودی باید از منبع معتبر و به‌روز تأیید شوند.

### اقدام بعدی
یک پیش‌فاکتور، استعلام واقعی یا مشخصات کالا را وارد کنید تا پرونده با داده‌های قابل بررسی تکمیل شود.
"""
    return """### AI Trade Employee — Demo Result

**Status:** This is a template response. It is not connected to live market or company data.

### Initial assessment
Confirm the exact product specification, quantity unit, price unit, delivery terms and required documents before treating the request as executable.

### Required information
- Exact product specification and grade
- Quantity and unit of measure
- Whether the target amount is total value or unit price
- Origin and destination
- Incoterm, shipping mode and delivery deadline
- Payment terms and required documents

### Execution plan
1. Complete missing information and open a trade case.
2. Define buyer or supplier qualification criteria.
3. Prepare an RFQ or commercial introduction.
4. Compare real offers by price, quality, MOQ, lead time and payment terms.
5. Calculate pricing from documented costs.
6. Flag risks and prepare documents for human review.

### Must not be guessed
Market prices, contact details, freight, duties, taxes, permits and stock availability require current verification.

### Next action
Provide a real quotation, inquiry or product specification to develop a reviewable case.
"""


def call_ai(prompt: str, language: str, history=None) -> str:
    api_key = get_secret("OPENROUTER_API_KEY")
    if not api_key:
        st.session_state.last_error = "OPENROUTER_API_KEY is missing."
        return demo_response(prompt, language)

    model = get_secret("OPENROUTER_MODEL", "openai/gpt-oss-120b")
    lang_instruction = (
        "Write entirely in natural Persian (Farsi). Use Persian headings and explanations. "
        "Keep standard trade terms, currency codes and units such as USD, MT, kg, FOB, CIF, LC in Latin script."
        if language == "FA"
        else "Write entirely in clear professional English."
    )

    system_prompt = f"""You are Mehr Ara AI Trade Employee, a practical assistant for a commercial trading company.

Support selling, sourcing, export planning, buyer research workflows, pricing frameworks, trade documents, RFQs, commercial correspondence, risk flags and follow-up plans.

{lang_instruction}

Reliability rules:
- Never fabricate verified company names, contact details, quotations, live prices, freight rates, taxes, duties, legal requirements, certifications or stock.
- Separate user-provided facts, assumptions, and items requiring verification.
- If an amount has no unit, do not silently assume total or per-unit. Ask for clarification and show alternative interpretations when useful.
- Do not claim to have searched live sources unless an enabled search tool actually did so.
- For calculations, show formula, units and arithmetic. Identify missing inputs rather than filling them with invented values.
- Provide an actionable next step and assign it to a human role where needed.
- Do not make binding commitments, send messages, place orders or approve counterparties.
"""

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history[-8:])
    messages.append({"role": "user", "content": prompt})

    try:
        with httpx.Client(timeout=httpx.Timeout(75.0, connect=20.0)) as client:
            response = client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key.strip()}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://mehrara.streamlit.app",
                    "X-Title": "Mehr Ara AI Trade Employee",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 2400,
                },
            )

        if response.status_code >= 400:
            try:
                detail = response.json().get("error", {}).get("message", response.text)
            except Exception:
                detail = response.text
            st.session_state.last_error = f"HTTP {response.status_code}: {detail}"
            return (
                "### اتصال هوش مصنوعی برقرار نشد / AI connection failed\n\n"
                f"**Provider:** OpenRouter  \n**Model:** `{model}`  \n"
                f"**Error:** {detail}\n\n"
                "برنامه در این نوبت پاسخ نمایشی نشان می‌دهد. کلید، اعتبار حساب، دسترسی مدل و نام مدل را در تنظیمات OpenRouter بررسی کنید."
                if language == "FA"
                else
                f"### AI connection failed\n\n**Provider:** OpenRouter  \n**Model:** `{model}`  \n"
                f"**Error:** {detail}\n\nThe app will show a clearly labeled demo response for this turn. Check the API key, account credits, model access and model ID."
            )

        data = response.json()
        content = data["choices"][0]["message"].get("content")
        if not content or not str(content).strip():
            st.session_state.last_error = "Provider returned an empty response."
            return demo_response(prompt, language)
        st.session_state.last_error = None
        return str(content).strip()

    except httpx.TimeoutException:
        st.session_state.last_error = "Request timed out."
        return (
            "زمان پاسخ‌گویی سرویس تمام شد. لطفاً دوباره تلاش کنید یا متن درخواست را کوتاه‌تر کنید."
            if language == "FA"
            else "The AI request timed out. Please retry or shorten the request."
        )
    except httpx.RequestError as e:
        st.session_state.last_error = f"Network error: {e}"
        return (
            f"خطای شبکه در اتصال به OpenRouter: {e}"
            if language == "FA"
            else f"Network error while connecting to OpenRouter: {e}"
        )
    except (KeyError, IndexError, ValueError) as e:
        st.session_state.last_error = f"Unexpected API response: {e}"
        return (
            "پاسخ سرویس قابل خواندن نبود. لطفاً دوباره تلاش کنید."
            if language == "FA"
            else "The provider response could not be parsed. Please retry."
        )


def build_trade_prompt(action, product, quantity, origin, destination, budget, notes, language):
    if language == "FA":
        return f"""درخواست واقعی/آزمایشی پرونده بازرگانی مهرآرا:

نوع کار: {action}
کالا: {product or "وارد نشده"}
مقدار: {quantity or "وارد نشده"}
مبدأ: {origin or "وارد نشده"}
مقصد: {destination or "وارد نشده"}
بودجه یا قیمت هدف: {budget or "وارد نشده"}
شرایط تکمیلی: {notes or "وارد نشده"}

یک گزارش عملیاتی فارسی تهیه کن با این بخش‌ها:
1. خلاصه مدیریتی
2. داده‌های اعلام‌شده، فرضیات و موارد نیازمند تأیید (جدول)
3. بررسی ابهام واحد قیمت و مقدار؛ اگر لازم است سؤال روشن‌کننده مطرح کن
4. برنامه بازار/خریدار/تأمین‌کننده، بدون جعل نام یا اطلاعات تماس واقعی
5. ساختار محاسبه قیمت با فرمول و واحدها؛ هزینه نامعلوم را خالی/نیازمند استعلام بگذار
6. اسناد و مجوزهایی که باید با مرجع رسمی بررسی شوند
7. ریسک‌ها و کنترل پیشنهادی
8. برنامه اجرایی 5 تا 7 روزه با مسئول، خروجی و گام بعد
9. پیش‌نویس RFQ یا پیام تجاری مناسب
10. سه اقدام بعدی مشخص برای کارمند بازرگانی مهرآرا

هیچ قیمت بازار، تعرفه، هزینه حمل، قانون یا مخاطب واقعی را از خودت نساز. برچسب بزن که این گزارش تحلیل اولیه است و تأیید انسانی لازم دارد."""
    return f"""Prepare a practical trade-case report for Mehr Ara.

Workflow: {action}
Product: {product or "Not provided"}
Quantity: {quantity or "Not provided"}
Origin: {origin or "Not provided"}
Destination: {destination or "Not provided"}
Budget / target price: {budget or "Not provided"}
Additional requirements: {notes or "Not provided"}

Include:
1. Executive summary
2. Known facts, assumptions and items to verify (table)
3. Clarify price/quantity units where ambiguous
4. Buyer/supplier/market workflow without inventing real names or contacts
5. Pricing formulas with units; leave unknown costs as quote-required
6. Documents and official requirements to verify
7. Risks and mitigations
8. A 5–7 day action plan with owner, output and next step
9. A suitable draft RFQ or commercial message
10. Three concrete next actions for the Mehr Ara trade employee

Do not invent live prices, freight, duties, laws or real contacts. Label this as preliminary analysis requiring human verification."""


# CSS: light result panel with high contrast; avoid styling every Streamlit bordered wrapper globally.
st.markdown(
    """
<style>
.block-container {padding-top:1.3rem; padding-bottom:3rem; max-width:1450px;}
.hero {padding:32px 36px;border-radius:22px;background:linear-gradient(135deg,#101827,#1b2b43);border:1px solid #293b55;margin-bottom:22px;}
.hero-title {font-size:clamp(25px,4vw,38px);font-weight:800;color:#f5f8fc;margin-bottom:8px;}
.hero-subtitle {font-size:16px;color:#c6d2e3;max-width:900px;}
.badge {display:inline-block;padding:6px 12px;border-radius:999px;background:#293b55;color:#e7effb;font-size:12px;margin-bottom:14px;}
.metric-card,.action-card {padding:19px;border-radius:16px;background:#152238;border:1px solid #2c405e;min-height:115px;}
.metric-label {color:#b9c7da;font-size:13px;}
.metric-value {font-size:28px;font-weight:800;color:#fff;margin-top:7px;}
.action-title {font-size:17px;font-weight:750;color:#f4f7fb;margin:8px 0;}
.action-description {font-size:13px;color:#bdcbe0;line-height:1.5;}
.section-title {font-size:23px;font-weight:750;margin-top:30px;margin-bottom:13px;}
.result-panel {background:#fff;color:#1c2735;border:1px solid #d7dee8;border-radius:14px;padding:20px 24px;margin:10px 0 20px;}
.result-panel h1,.result-panel h2,.result-panel h3,.result-panel h4 {color:#172b4d!important;}
.result-panel p,.result-panel li,.result-panel td,.result-panel th {color:#263445!important;line-height:1.7;}
.result-panel strong {color:#111827!important;}
.result-panel table {width:100%;border-collapse:collapse;}
.result-panel th,.result-panel td {border:1px solid #d8e0ea;padding:7px 9px;text-align:left;}
.warning-box {padding:13px 16px;border-radius:10px;background:#fff8e5;border:1px solid #f2d58a;color:#684f10;margin-top:18px;}
.small-muted {color:#78869a;font-size:12px;}
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## 🤖 Mehr Ara")
    language = st.selectbox(
        "Language / زبان",
        ["FA", "EN"],
        index=0 if st.session_state.language == "FA" else 1,
        key="language_selector",
    )
    if language != st.session_state.language:
        st.session_state.language = language
        st.rerun()

    T = LANG[st.session_state.language]
    st.divider()
    st.markdown("### AI Configuration")
    api_key_present = bool(get_secret("OPENROUTER_API_KEY"))
    if api_key_present:
        st.success(T["api_connected"])
    else:
        st.info(T["api_missing"])
    active_model = get_secret("OPENROUTER_MODEL", "openai/gpt-oss-120b")
    st.caption(f"Provider: OpenRouter\n\nModel: `{active_model}`")
    st.caption("Secrets must use OPENROUTER_API_KEY and optionally OPENROUTER_MODEL.")
    st.divider()
    st.markdown("### Core workflows\n\n• Sell\n\n• Source\n\n• Export\n\n• Find buyers\n\n• Pricing\n\n• Operations")

T = LANG[st.session_state.language]

st.markdown(
    f'<div class="hero"><div class="badge">AI-POWERED COMMERCIAL OPERATIONS</div>'
    f'<div class="hero-title">{T["title"]}</div>'
    f'<div class="hero-subtitle">{T["subtitle"]}</div></div>',
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
for col, label, value in [
    (m1, T["active_cases"], "12"),
    (m2, T["buyer_leads"], "47"),
    (m3, T["suppliers"], "31"),
    (m4, T["ai_mode"], T["ai"] if api_key_present else T["demo"]),
]:
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div>'
            f'<div class="metric-value" style="font-size:{"18px" if len(value)>10 else "28px"}">{value}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown(f'<div class="section-title">{T["today"]}</div>', unsafe_allow_html=True)
actions = [
    ("📦", T["sell"], "Find markets, buyers and prepare a sales workflow."),
    ("🔎", T["source"], "Find and compare potential suppliers."),
    ("🚢", T["export"], "Prepare an export plan, cost structure and documents."),
    ("🎯", T["buyers"], "Build a buyer discovery and outreach workflow."),
    ("💰", T["pricing"], "Calculate indicative commercial pricing."),
    ("📁", T["operations"], "Manage trade cases, documents and follow-ups."),
]
cols = st.columns(3)
for i, (emoji, title, description) in enumerate(actions):
    with cols[i % 3]:
        st.markdown(
            f'<div class="action-card"><div style="font-size:27px">{emoji}</div>'
            f'<div class="action-title">{title}</div><div class="action-description">{description}</div></div>',
            unsafe_allow_html=True,
        )
        if st.button(title, key=f"workflow_{i}", use_container_width=True):
            st.session_state.selected_action = title
            st.rerun()

st.markdown(f'<div class="section-title">{T["request"]}</div>', unsafe_allow_html=True)
selected_action = st.session_state.selected_action
st.info(f"Selected workflow: **{selected_action}**")

c1, c2 = st.columns(2)
with c1:
    product = st.text_input(T["product"], placeholder="مثال: زعفران نگین" if st.session_state.language == "FA" else "Example: premium saffron")
    quantity = st.text_input(T["quantity"], placeholder="مثال: 500 kg")
    origin = st.text_input(T["origin"], placeholder="مثال: Mashhad, Iran")
with c2:
    destination = st.text_input(T["destination"], placeholder="مثال: Muscat, Oman")
    budget = st.text_input(T["budget"], placeholder="مثال: USD 2000 total or USD 40/kg")
    notes = st.text_area(T["notes"], placeholder="شرایط پرداخت، زمان تحویل، کیفیت، بسته‌بندی..." if st.session_state.language == "FA" else "Payment, delivery, quality, packaging...", height=115)

if st.button(T["generate"], type="primary", use_container_width=True):
    prompt = build_trade_prompt(
        selected_action, product, quantity, origin, destination, budget, notes,
        st.session_state.language,
    )
    with st.spinner(T["working"]):
        result = call_ai(prompt, st.session_state.language)
    st.session_state.last_trade_case = {
        "action": selected_action, "product": product, "quantity": quantity,
        "origin": origin, "destination": destination, "budget": budget,
        "notes": notes, "result": result,
    }
    st.session_state["show_latest_result"] = True

if st.session_state.get("show_latest_result") and st.session_state.last_trade_case:
    st.markdown(f'<div class="section-title">{T["result"]}</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="result-panel">', unsafe_allow_html=True)
        st.markdown(st.session_state.last_trade_case["result"])
        st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.last_error:
    with st.expander("Connection diagnostics / جزئیات اتصال"):
        st.code(st.session_state.last_error)

st.markdown('<div class="section-title">Live Trade Case — Demo</div>', unsafe_allow_html=True)
case_col1, case_col2 = st.columns([1.4, 1])
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
- Supplier comparison
- Commercial terms review
- Logistics verification
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

⚠️ These are fictional demonstration records. Verify identity, quotation, certificates, payment terms and logistics before any transaction.
""")

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
        context = f"""Current case context:
Action: {tc['action']}
Product: {tc['product']}
Quantity: {tc['quantity']}
Origin: {tc['origin']}
Destination: {tc['destination']}
Budget: {tc['budget']}
Notes: {tc['notes']}
Previous plan:
{tc['result']}
"""
    prior = st.session_state.chat_history[:-1][-8:]
    answer = call_ai(
        f"{context}\nUser follow-up: {user_message}\nAnswer practically, identify missing facts, and do not invent live facts.",
        st.session_state.language,
        prior,
    )
    st.session_state.chat_history.append({"role": "assistant", "content": answer})
    st.rerun()

st.markdown("---")
st.markdown(f'<div class="warning-box">⚠️ {T["demo_notice"]}</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;margin-top:22px" class="small-muted">Mehr Ara AI Trade Employee • Commercial Intelligence Demo</div>', unsafe_allow_html=True)
