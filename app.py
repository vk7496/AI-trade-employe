import os
import json
from datetime import datetime
from typing import Dict, Any, List

import streamlit as st
import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Mehr Ara AI Trade Employee",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# LANGUAGE
# ============================================================

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
        "demo": "Demo",
        "groq": "OpenRouter AI",
        "run": "Run AI Employee",
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
        "send": "Send",
        "message": "Message",
        "demo_notice": "Demo data is illustrative. Verify commercial information before making a transaction.",
    },
    "FA": {
        "title": "نیروی هوشمند بازرگانی مهرآرا",
        "subtitle": "یک نیروی دیجیتال برای فروش، تأمین، صادرات، قیمت‌گذاری و پیگیری امور بازرگانی.",
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
        "ai_mode": "حالت AI",
        "demo": "دمو",
        "groq": "OpenRouter AI",
        "run": "اجرای نیروی هوشمند",
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
        "send": "ارسال",
        "message": "پیام",
        "demo_notice": "اطلاعات این نسخه نمایشی و نمونه هستند. قبل از هر معامله، اطلاعات تجاری باید بررسی و تأیید شوند.",
    },
}


# ============================================================
# SESSION STATE
# ============================================================

if "language" not in st.session_state:
    st.session_state.language = "EN"

if "selected_action" not in st.session_state:
    st.session_state.selected_action = "Sell a Product"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_trade_case" not in st.session_state:
    st.session_state.last_trade_case = None


T = LANG[st.session_state.language]


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

.hero {
    padding: 38px 42px;
    border-radius: 24px;
    background:
        radial-gradient(circle at 85% 20%, rgba(67, 97, 238, .22), transparent 28%),
        radial-gradient(circle at 10% 90%, rgba(0, 200, 180, .13), transparent 30%),
        linear-gradient(135deg, #101827, #182235);
    border: 1px solid rgba(255,255,255,.08);
    margin-bottom: 25px;
}

.hero-title {
    font-size: 38px;
    font-weight: 800;
    letter-spacing: .5px;
    margin-bottom: 8px;
    color: #f5f8fc;
}

.hero-subtitle {
    font-size: 17px;
    color: #b7c2d5;
    max-width: 900px;
}

.badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,.08);
    color: #d8e2f3;
    font-size: 12px;
    margin-bottom: 15px;
}

.metric-card {
    padding: 22px;
    border-radius: 18px;
    background: #111a29;
    border: 1px solid rgba(255,255,255,.07);
    min-height: 120px;
}

.metric-label {
    color: #93a0b5;
    font-size: 13px;
}

.metric-value {
    font-size: 31px;
    font-weight: 800;
    margin-top: 8px;
    color: #f5f8fc;
}

.action-card {
    padding: 22px;
    border-radius: 18px;
    background: linear-gradient(145deg,#121c2c,#182437);
    border: 1px solid rgba(255,255,255,.07);
    min-height: 150px;
}

.action-title {
    font-size: 18px;
    font-weight: 750;
    margin-bottom: 8px;
    color: #eef3fb;
}

.action-description {
    font-size: 13px;
    color: #9eabc0;
    line-height: 1.5;
}

.section-title {
    font-size: 24px;
    font-weight: 750;
    margin-top: 35px;
    margin-bottom: 15px;
}

/* AI result box: rendered via st.container(border=True) + st.markdown()
   so markdown (###, **bold**, tables, lists) parses into real HTML
   instead of showing raw symbols. This targets Streamlit's own
   bordered-container wrapper. */

[data-testid="stVerticalBlockBorderWrapper"] {
    background: #0e1725 !important;
    border: 1px solid rgba(91, 123, 255, .25) !important;
    border-radius: 18px !important;
    padding: 6px 20px 20px 20px;
}

[data-testid="stVerticalBlockBorderWrapper"] p,
[data-testid="stVerticalBlockBorderWrapper"] li,
[data-testid="stVerticalBlockBorderWrapper"] span {
    color: #dce6f7 !important;
    line-height: 1.7;
}

[data-testid="stVerticalBlockBorderWrapper"] h1,
[data-testid="stVerticalBlockBorderWrapper"] h2,
[data-testid="stVerticalBlockBorderWrapper"] h3,
[data-testid="stVerticalBlockBorderWrapper"] h4 {
    color: #f5f8fc !important;
    margin-top: 18px;
    margin-bottom: 8px;
}

[data-testid="stVerticalBlockBorderWrapper"] strong,
[data-testid="stVerticalBlockBorderWrapper"] b {
    color: #ffffff !important;
}

[data-testid="stVerticalBlockBorderWrapper"] a {
    color: #7fb3ff !important;
}

[data-testid="stVerticalBlockBorderWrapper"] code {
    background: rgba(255,255,255,.08);
    color: #9fd8ff !important;
    padding: 2px 6px;
    border-radius: 4px;
}

[data-testid="stVerticalBlockBorderWrapper"] ul,
[data-testid="stVerticalBlockBorderWrapper"] ol {
    padding-left: 22px;
    margin: 8px 0;
}

[data-testid="stVerticalBlockBorderWrapper"] table {
    color: #dce6f7 !important;
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
}

[data-testid="stVerticalBlockBorderWrapper"] table th,
[data-testid="stVerticalBlockBorderWrapper"] table td {
    border: 1px solid rgba(255,255,255,.12);
    padding: 6px 10px;
}

.warning-box {
    padding: 14px 18px;
    border-radius: 12px;
    background: rgba(255, 193, 7, .08);
    border: 1px solid rgba(255, 193, 7, .2);
    color: #d9c98e;
    margin-top: 20px;
}

.small-muted {
    color: #8996aa;
    font-size: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def get_openrouter_key():
    return st.secrets.get("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY"))


def call_groq(prompt: str, language: str = "EN", history: list = None) -> str:
    api_key = get_openrouter_key()

    if not api_key:
        return demo_response(prompt)

    model = st.secrets.get(
        "OPENROUTER_MODEL",
        os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
    )

    language_instruction = (
        "Respond entirely in Persian (Farsi), using clear and natural "
        "business Persian. Keep numbers, currency codes (USD, MT, kg) "
        "and document names in Latin script where that is standard "
        "commercial practice, but all explanations, headings and labels "
        "must be in Persian."
        if language == "FA"
        else "Respond entirely in English."
    )

    messages = [
        {
            "role": "system",
            "content": f"""
You are Mehr Ara AI Trade Employee.

You support a commercial trading company with:
- product sourcing
- buyer discovery
- export planning
- pricing calculations
- supplier comparison
- trade documentation
- commercial emails
- follow-ups
- risk identification

Do not invent verified facts, prices, contact details, shipping costs,
taxes or regulations.

Clearly distinguish:
1. Known information
2. Assumptions
3. Information that must be verified

PRICE / QUANTITY UNITS:
Whenever a price, budget or target value is given without an explicit
unit (for example: no clear "per kg", "per MT", "per ton" or "total
contract value"), do NOT silently pick one. Instead:
- State clearly, near the top of your answer, which unit you are
  assuming and why (e.g. "Assuming the target price is per kg, since
  the total would be unrealistic for this quantity").
- Mark this as a "Must verify with the user before proceeding" item.
- If the assumed unit makes the deal commercially unrealistic (far
  above or below typical market prices), say so explicitly and
  recommend the value be confirmed before any further calculation.

LANGUAGE:
{language_instruction}

Your job is to prepare practical commercial work that a human trade
employee can review and execute.
""",
        }
    ]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": prompt})

    try:
        with httpx.Client(timeout=60) as http_client:
            response = http_client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    # OpenRouter asks for these two for routing/analytics;
                    # harmless to omit, but recommended.
                    "HTTP-Referer": "https://mehrara.streamlit.app",
                    "X-Title": "Mehr Ara AI Trade Employee",
                },
                json={
                    "model": model,
                    "temperature": 0.2,
                    "max_tokens": 1800,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    except Exception as e:
        return (
            "AI service could not be reached.\n\n"
            f"Technical message: {str(e)}\n\n"
            "The application has switched to Demo Mode."
        )


def demo_response(prompt: str) -> str:
    return """
### AI Trade Employee — Demo Result

**Recommended workflow**

1. Define the exact product specification.
2. Confirm quantity and delivery destination.
3. Identify suitable target markets.
4. Build a shortlist of potential buyers or suppliers.
5. Compare commercial terms.
6. Calculate the indicative landed/export cost.
7. Prepare an RFQ or buyer quotation.
8. Prepare the required commercial documents.
9. Flag information that needs verification.
10. Create follow-up tasks.

### Initial commercial assessment

**Market:** Target market should be validated based on product,
regulatory requirements and current demand.

**Buyer/Supplier:** A verified company list should be created from
public and authorized business sources.

**Pricing:** Final pricing should only use verified purchase,
logistics, duties/taxes and other documented costs.

**Risk flags:**
- Product specification incomplete
- Commercial terms not yet confirmed
- Logistics cost not verified
- Buyer/supplier identity requires verification

### Next Action

Provide the real product, quantity, origin, destination and target
commercial terms. The AI employee can then turn the request into a
structured trade case.
"""


def build_trade_prompt(
    action: str,
    product: str,
    quantity: str,
    origin: str,
    destination: str,
    budget: str,
    notes: str,
) -> str:

    return f"""
Trade task:

ACTION:
{action}

PRODUCT:
{product}

QUANTITY:
{quantity}

ORIGIN:
{origin}

DESTINATION:
{destination}

BUDGET / TARGET PRICE:
{budget}

ADDITIONAL REQUIREMENTS:
{notes}

Prepare a practical commercial workflow.

Include:

1. Executive summary
2. Required information
3. Market / buyer / supplier strategy
4. Commercial calculation framework
5. Documents required
6. Risk flags
7. Recommended next actions
8. Draft RFQ or buyer message if relevant

Do not invent factual contact information, market prices,
shipping rates, taxes or regulations.
"""


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🤖 Mehr Ara")

    language = st.selectbox(
        "Language / زبان",
        ["EN", "FA"],
        index=0 if st.session_state.language == "EN" else 1,
        key="language_selector",
    )

    if language != st.session_state.language:
        st.session_state.language = language
        st.rerun()

    st.divider()

    st.markdown("### AI Configuration")

    ai_available = get_openrouter_key() is not None

    if ai_available:
        st.success("OpenRouter AI Connected")
        current_mode = T["groq"]
    else:
        st.info("Demo Mode")
        current_mode = T["demo"]

    st.caption(
        "OPENROUTER_API_KEY can be added through Streamlit Secrets."
    )

    st.divider()

    st.markdown("### Trade Employee")

    st.markdown(
        """
**Core workflows**

• Sell  
• Source  
• Export  
• Buyers  
• Pricing  
• Operations
"""
    )

    st.divider()

    st.caption("Mehr Ara AI Trade Employee")
    st.caption("Commercial Intelligence Demo")


# ============================================================
# HERO
# ============================================================

st.markdown(
    f"""
<div class="hero">

<div class="badge">AI-POWERED COMMERCIAL OPERATIONS</div>

<div class="hero-title">
{T["title"]}
</div>

<div class="hero-subtitle">
{T["subtitle"]}
</div>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# METRICS
# ============================================================

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(
        f"""
        <div class="metric-card">
        <div class="metric-label">{T["active_cases"]}</div>
        <div class="metric-value">12</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
        <div class="metric-card">
        <div class="metric-label">{T["buyer_leads"]}</div>
        <div class="metric-value">47</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
        <div class="metric-card">
        <div class="metric-label">{T["suppliers"]}</div>
        <div class="metric-value">31</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        f"""
        <div class="metric-card">
        <div class="metric-label">{T["ai_mode"]}</div>
        <div class="metric-value" style="font-size:21px;">
        {current_mode}
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# ACTIONS
# ============================================================

st.markdown(
    f'<div class="section-title">{T["today"]}</div>',
    unsafe_allow_html=True,
)


actions = [
    (
        "📦",
        T["sell"],
        "Find markets, buyers and prepare a sales workflow.",
    ),
    (
        "🔎",
        T["source"],
        "Find and compare potential suppliers.",
    ),
    (
        "🚢",
        T["export"],
        "Prepare an export plan, cost structure and documents.",
    ),
    (
        "🎯",
        T["buyers"],
        "Build a buyer discovery and outreach workflow.",
    ),
    (
        "💰",
        T["pricing"],
        "Calculate indicative commercial pricing.",
    ),
    (
        "📁",
        T["operations"],
        "Manage trade cases, documents and follow-ups.",
    ),
]


cols = st.columns(3)

for i, (icon, title, description) in enumerate(actions):

    with cols[i % 3]:

        st.markdown(
            f"""
            <div class="action-card">
            <div style="font-size:28px;">{icon}</div>
            <div class="action-title">{title}</div>
            <div class="action-description">{description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            title,
            key=f"action_{i}",
            use_container_width=True,
        ):
            st.session_state.selected_action = title


# ============================================================
# TRADE REQUEST
# ============================================================

st.markdown(
    f'<div class="section-title">{T["request"]}</div>',
    unsafe_allow_html=True,
)

selected_action = st.session_state.selected_action

st.info(f"Selected workflow: **{selected_action}**")

c1, c2 = st.columns(2)

with c1:

    product = st.text_input(
        T["product"],
        placeholder=(
            "Example: Industrial Grade Material X"
            if st.session_state.language == "EN"
            else "مثال: ماده صنعتی X"
        ),
    )

    quantity = st.text_input(
        T["quantity"],
        placeholder="Example: 5000 MT",
    )

    origin = st.text_input(
        T["origin"],
        placeholder="Example: China",
    )

with c2:

    destination = st.text_input(
        T["destination"],
        placeholder="Example: Oman",
    )

    budget = st.text_input(
        T["budget"],
        placeholder="Example: USD 800 / MT",
    )

    notes = st.text_area(
        T["notes"],
        placeholder=(
            "Payment terms, delivery time, quality requirements..."
        ),
        height=120,
    )


if st.button(
    T["generate"],
    type="primary",
    use_container_width=True,
):

    prompt = build_trade_prompt(
        selected_action,
        product,
        quantity,
        origin,
        destination,
        budget,
        notes,
    )

    with st.spinner("AI Trade Employee is working..."):

        result = call_groq(prompt, st.session_state.language)

    st.session_state.last_trade_case = {
        "action": selected_action,
        "product": product,
        "quantity": quantity,
        "origin": origin,
        "destination": destination,
        "budget": budget,
        "notes": notes,
        "result": result,
    }

    st.markdown(
        f'<div class="section-title">{T["result"]}</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(result)


# ============================================================
# DEMO CASE
# ============================================================

st.markdown(
    '<div class="section-title">Live Trade Case — Demo</div>',
    unsafe_allow_html=True,
)

case_col1, case_col2 = st.columns([1.4, 1])

with case_col1:

    st.markdown(
        """
### Industrial Material X

**Trade Case:** MA-2026-014

| Field | Value |
|---|---|
| Quantity | 5,000 MT |
| Origin | China |
| Destination | Oman |
| Payment | LC at Sight |
| Target Delivery | ≤ 35 days |
| Status | Supplier Shortlist |

### AI Employee Tasks

- Supplier discovery
- Supplier comparison
- Commercial terms review
- Logistics verification
- RFQ preparation
- Risk identification
- Follow-up tracking
""",
    )

with case_col2:

    st.markdown(
        """
### Supplier Intelligence

**Supplier A**  
China  
MOQ: 1,000 MT  
Lead Time: 28–35 days

**Supplier B**  
China  
MOQ: 2,000 MT  
Lead Time: 25–30 days

**Supplier C**  
China  
MOQ: 5,000 MT  
Lead Time: 30–40 days

⚠️ These are demonstration records.

Before any transaction, supplier identity, quotation,
quality certificates, payment terms and logistics must be verified.
"""
    )


# ============================================================
# CHAT
# ============================================================

st.markdown(
    f'<div class="section-title">{T["assistant"]}</div>',
    unsafe_allow_html=True,
)

st.caption(T["chat"])

for item in st.session_state.chat_history:

    with st.chat_message(item["role"]):
        st.markdown(item["content"])


user_message = st.chat_input(
    T["message"]
)

if user_message:

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    context_note = ""

    if st.session_state.last_trade_case:
        tc = st.session_state.last_trade_case
        context_note = f"""
Context: the AI employee already generated a trade plan for this case
earlier in this session. Use it to answer follow-up questions about
this case unless the user clearly asks about something unrelated.

Action: {tc["action"]}
Product: {tc["product"]}
Quantity: {tc["quantity"]}
Origin: {tc["origin"]}
Destination: {tc["destination"]}
Budget / Target Price: {tc["budget"]}
Additional Requirements: {tc["notes"]}

Full previously generated plan:
{tc["result"]}
"""

    # Prior turns (everything before the message just appended above),
    # capped to keep the request small.
    prior_turns = st.session_state.chat_history[:-1][-8:]

    response = call_groq(
        f"""
{context_note}

The commercial user asked:

{user_message}

Answer as Mehr Ara AI Trade Employee.

Be practical and concise.

If information is missing, clearly identify it.

Never invent verified company contacts, prices,
shipping rates or regulations.
""",
        st.session_state.language,
        prior_turns,
    )

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    f"""
<div class="warning-box">
⚠️ {T["demo_notice"]}
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div style="text-align:center; margin-top:25px;"
     class="small-muted">
Mehr Ara AI Trade Employee • Commercial Intelligence Platform
</div>
""",
    unsafe_allow_html=True,
)
