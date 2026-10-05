import os
from typing import Optional, List, Dict

import streamlit as st
import httpx


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Mehr Ara AI Trade Employee",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


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
    st.session_state.language = "FA"

if "selected_action" not in st.session_state:
    st.session_state.selected_action = "فروش کالا"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_trade_case" not in st.session_state:
    st.session_state.last_trade_case = None

if "last_provider" not in st.session_state:
    st.session_state.last_provider = None


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

.provider-box {
    padding: 10px 14px;
    border-radius: 10px;
    background: rgba(67, 97, 238, .08);
    border: 1px solid rgba(67, 97, 238, .18);
    margin-bottom: 15px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# API KEY HELPERS
# ============================================================

def get_secret(name: str, default=None):
    """
    Safely read from Streamlit Secrets first,
    then environment variables.
    """
    try:
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass

    return os.getenv(name, default)


def get_groq_key():
    return get_secret("GROQ_API_KEY")


def get_openrouter_key():
    return get_secret("OPENROUTER_API_KEY")


# ============================================================
# MODELS
# ============================================================

# Current Groq models.
# We deliberately do NOT use the old Llama models that were deprecated.
GROQ_MODELS = [
    get_secret(
        "GROQ_MODEL",
        "openai/gpt-oss-120b",
    ),
    "openai/gpt-oss-20b",
]


# OpenRouter free router.
# It automatically selects an available free model.
OPENROUTER_MODELS = [
    get_secret(
        "OPENROUTER_MODEL",
        "openrouter/free",
    )
]


# ============================================================
# SYSTEM PROMPT
# ============================================================

def build_system_prompt(language: str) -> str:

    if language == "FA":
        language_instruction = """
پاسخ را کاملاً به زبان فارسی بنویس.
زبان باید طبیعی، حرفه‌ای و مناسب مدیر بازرگانی باشد.
اعداد، ارزها مثل USD و واحدهایی مثل MT و kg را در صورت نیاز
به شکل استاندارد تجاری نگه دار.
"""
    else:
        language_instruction = """
Respond entirely in English.
Use professional commercial and trade terminology.
"""

    return f"""
You are Mehr Ara AI Trade Employee.

You are a digital commercial employee for a trading company.

Your responsibilities include:

- product sourcing
- supplier discovery
- supplier comparison
- buyer discovery
- market research
- export planning
- import planning
- pricing calculations
- landed-cost calculations
- RFQ preparation
- buyer quotations
- commercial emails
- follow-ups
- document checklists
- risk identification
- trade operations
- negotiation preparation

You are NOT merely a chatbot.

Your job is to turn a commercial request into practical,
structured work that a human trade employee can review and execute.

IMPORTANT:

Never invent:

- company contacts
- personal phone numbers
- WhatsApp numbers
- email addresses
- market prices
- shipping rates
- customs duties
- taxes
- regulations
- supplier certifications
- buyer information
- delivery promises

Clearly distinguish:

1. Known information
2. Assumptions
3. Information that must be verified

PRICE / QUANTITY RULE:

If the user gives a price without a clear unit such as:

USD/kg
USD/MT
USD/ton
total contract value

DO NOT silently choose a unit.

State the ambiguity clearly.

If necessary, ask the user to confirm the unit.

For calculations:

Show the formula.

Do not pretend an estimated price is a verified market price.

TRADE OPERATIONS:

Whenever appropriate, produce:

- next action
- responsible person
- required information
- expected output
- following step

If the user asks for buyers or suppliers, explain what
information must be collected and how those companies should
be verified.

{language_instruction}
"""


# ============================================================
# NORMALIZE API RESPONSE
# ============================================================

def extract_response(data: dict) -> str:

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:

        # Some providers may return slightly different structures.
        try:
            return data["choices"][0]["text"]
        except Exception:
            return "The AI provider returned an unexpected response format."


# ============================================================
# GROQ CALL
# ============================================================

def call_groq(
    messages: List[Dict[str, str]],
) -> tuple:

    api_key = get_groq_key()

    if not api_key:
        return None, "Groq API key is not configured."

    errors = []

    for model in GROQ_MODELS:

        try:

            with httpx.Client(timeout=60) as client:

                response = client.post(
                    GROQ_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_tokens": 1800,
                    },
                )

                if response.status_code == 200:

                    data = response.json()

                    result = extract_response(data)

                    return result, f"Groq • {model}"

                else:

                    try:
                        error_data = response.json()
                        error_message = error_data.get(
                            "error",
                            {}
                        ).get(
                            "message",
                            response.text
                        )
                    except Exception:
                        error_message = response.text

                    errors.append(
                        f"{model}: HTTP {response.status_code} - {error_message}"
                    )

        except Exception as e:

            errors.append(
                f"{model}: {str(e)}"
            )

    return None, " | ".join(errors)


# ============================================================
# OPENROUTER CALL
# ============================================================

def call_openrouter(
    messages: List[Dict[str, str]],
) -> tuple:

    api_key = get_openrouter_key()

    if not api_key:
        return None, "OpenRouter API key is not configured."

    errors = []

    for model in OPENROUTER_MODELS:

        try:

            with httpx.Client(timeout=60) as client:

                response = client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://mehrara.streamlit.app",
                        "X-Title": "Mehr Ara AI Trade Employee",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_tokens": 1800,
                    },
                )

                if response.status_code == 200:

                    data = response.json()

                    result = extract_response(data)

                    return result, f"OpenRouter • {model}"

                else:

                    try:
                        error_data = response.json()
                        error_message = error_data.get(
                            "error",
                            {}
                        ).get(
                            "message",
                            response.text
                        )
                    except Exception:
                        error_message = response.text

                    errors.append(
                        f"{model}: HTTP {response.status_code} - {error_message}"
                    )

        except Exception as e:

            errors.append(
                f"{model}: {str(e)}"
            )

    return None, " | ".join(errors)


# ============================================================
# DEMO RESPONSE
# ============================================================

def demo_response(prompt: str) -> str:

    return """
### AI Trade Employee — Demo Mode

**Recommended workflow**

1. Define the exact product specification.
2. Confirm quantity and destination.
3. Identify the target market.
4. Build a verified buyer or supplier shortlist.
5. Compare commercial terms.
6. Calculate the indicative landed/export cost.
7. Prepare an RFQ or buyer quotation.
8. Prepare required commercial documents.
9. Identify risks and missing information.
10. Create follow-up tasks.

### Commercial Assessment

**Known information**

The request contains basic commercial information.

**Information requiring verification**

- Product specification
- Supplier identity
- Buyer identity
- Current market price
- Logistics cost
- Payment terms
- Taxes and duties
- Required certificates

### Next Action

Provide the real product, quantity, origin, destination,
target price and commercial requirements.
"""


# ============================================================
# SMART AI ROUTER
# ============================================================

def call_ai(
    prompt: str,
    language: str = "FA",
    history: Optional[List[Dict[str, str]]] = None,
):

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(language),
        }
    ]

    if history:
        messages.extend(history)

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    # --------------------------------------------------------
    # 1. TRY GROQ
    # --------------------------------------------------------

    result, provider = call_groq(messages)

    if result:

        st.session_state.last_provider = provider

        return result, provider, None

    groq_error = provider


    # --------------------------------------------------------
    # 2. TRY OPENROUTER
    # --------------------------------------------------------

    result, provider = call_openrouter(messages)

    if result:

        st.session_state.last_provider = provider

        return result, provider, None

    openrouter_error = provider


    # --------------------------------------------------------
    # 3. DEMO MODE
    # --------------------------------------------------------

    combined_error = f"""
Groq:
{groq_error}

OpenRouter:
{openrouter_error}
"""

    st.session_state.last_provider = "Demo Mode"

    return (
        demo_response(prompt),
        "Demo Mode",
        combined_error,
    )


# ============================================================
# TRADE PROMPT
# ============================================================

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
TRADE TASK

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

### 1. Executive Summary

### 2. Information We Already Have

### 3. Missing Information

### 4. Commercial Strategy

Depending on the action, explain:

- buyer strategy
- supplier strategy
- export strategy
- sourcing strategy
- pricing strategy

### 5. Commercial Calculation Framework

Show formulas where relevant.

### 6. Required Documents

### 7. Risk Flags

### 8. Immediate Next Actions

For every important action specify:

- Task
- Required information
- Expected output
- Next step

### 9. Draft RFQ / Buyer Message

Provide a draft if relevant.

Do not invent factual contacts, prices,
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
    )

    if language != st.session_state.language:

        st.session_state.language = language

        st.rerun()

    T = LANG[st.session_state.language]

    st.divider()

    st.markdown("### AI Configuration")

    groq_available = bool(get_groq_key())
    openrouter_available = bool(get_openrouter_key())

    if groq_available:

        st.success("✓ Groq API Ready")

    else:

        st.warning("Groq API not configured")

    if openrouter_available:

        st.success("✓ OpenRouter API Ready")

    else:

        st.warning("OpenRouter API not configured")

    if groq_available and openrouter_available:

        st.info(
            "AI routing: Groq → OpenRouter → Demo"
        )

    elif groq_available:

        st.info(
            "AI routing: Groq → Demo"
        )

    elif openrouter_available:

        st.info(
            "AI routing: OpenRouter → Demo"
        )

    else:

        st.info(
            "AI routing: Demo Mode"
        )

    st.divider()

    st.markdown("### Models")

    st.caption(
        f"Groq primary:\n{GROQ_MODELS[0]}"
    )

    st.caption(
        f"Groq fallback:\n{GROQ_MODELS[1]}"
    )

    st.caption(
        f"OpenRouter:\n{OPENROUTER_MODELS[0]}"
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

<div class="badge">
AI-POWERED COMMERCIAL OPERATIONS
</div>

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
        <div class="metric-label">
        {T["active_cases"]}
        </div>
        <div class="metric-value">
        12
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:

    st.markdown(
        f"""
        <div class="metric-card">
        <div class="metric-label">
        {T["buyer_leads"]}
        </div>
        <div class="metric-value">
        47
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m3:

    st.markdown(
        f"""
        <div class="metric-card">
        <div class="metric-label">
        {T["suppliers"]}
        </div>
        <div class="metric-value">
        31
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m4:

    if groq_available or openrouter_available:

        mode_text = "AUTO AI"

    else:

        mode_text = "DEMO"

    st.markdown(
        f"""
        <div class="metric-card">
        <div class="metric-label">
        {T["ai_mode"]}
        </div>
        <div class="metric-value"
             style="font-size:21px;">
        {mode_text}
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
            <div style="font-size:28px;">
            {icon}
            </div>

            <div class="action-title">
            {title}
            </div>

            <div class="action-description">
            {description}
            </div>
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

st.info(
    f"Selected workflow: **{selected_action}**"
)


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


# ============================================================
# GENERATE TRADE PLAN
# ============================================================

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

    with st.spinner(
        "AI Trade Employee is working..."
    ):

        result, provider, error = call_ai(
            prompt,
            st.session_state.language,
        )

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

    # --------------------------------------------------------
    # Provider status
    # --------------------------------------------------------

    if provider != "Demo Mode":

        st.markdown(
            f"""
            <div class="provider-box">
            🤖 <strong>AI Provider:</strong> {provider}
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.warning(
            "AI providers were unavailable. "
            "The application is showing Demo Mode."
        )

        with st.expander(
            "Connection diagnostics / جزئیات اتصال"
        ):

            st.code(
                error or "No diagnostic information.",
                language="text",
            )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

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
"""
    )


with case_col2:

    st.markdown(
        """
### Supplier Intelligence

**Sample Supplier A**

China  
MOQ: 1,000 MT  
Lead Time: 28–35 days

**Sample Supplier B**

China  
MOQ: 2,000 MT  
Lead Time: 25–30 days

**Sample Supplier C**

China  
MOQ: 5,000 MT  
Lead Time: 30–40 days

⚠️ These are fictional demonstration records.

Before any transaction, supplier identity,
quotation, quality certificates, payment terms
and logistics must be verified.
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

        st.markdown(
            item["content"]
        )


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
A trade plan was already created earlier in this session.

Use this case context for follow-up questions:

Action:
{tc["action"]}

Product:
{tc["product"]}

Quantity:
{tc["quantity"]}

Origin:
{tc["origin"]}

Destination:
{tc["destination"]}

Budget / Target Price:
{tc["budget"]}

Additional Requirements:
{tc["notes"]}

Previous Trade Plan:
{tc["result"]}
"""


    prior_turns = (
        st.session_state.chat_history[:-1][-8:]
    )


    response, provider, error = call_ai(
        f"""
{context_note}

The commercial user asked:

{user_message}

Answer as Mehr Ara AI Trade Employee.

Be practical and concise.

If information is missing,
clearly identify it.

Never invent verified company contacts,
prices, shipping rates or regulations.
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
