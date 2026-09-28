# AI-trade-employe
# Mehr Ara AI Trade Employee

AI-powered digital commercial employee for Mehr Ara Business.

The platform is designed to support real-world commercial workflows such as:

- Selling products
- Finding buyers
- Sourcing products
- Finding suppliers
- Export planning
- Commercial pricing
- Supplier comparison
- RFQ preparation
- Negotiation preparation
- Trade documentation
- Follow-up management

---

## Product Concept

### MEHR ARA AI TRADE EMPLOYEE

A digital commercial employee for:

> Sell → Source → Export → Find Buyers → Calculate Price → Follow Up

Instead of being only a chatbot, the system is designed around
commercial workflows.

---

# Main Modules

## 1. Sell a Product

The AI can help structure:

- Product information
- Target markets
- Buyer profile
- Potential buyer companies
- Decision-maker roles
- Sales message
- Follow-up plan

---

## 2. Source a Product

The workflow can include:

- Product specification
- Required quantity
- Supplier discovery
- Supplier comparison
- MOQ
- Lead time
- Payment terms
- Risk flags
- RFQ preparation

---

## 3. Export a Product

The AI can structure an export case around:

- Product
- Quantity
- Origin
- Destination
- Purchase price
- Logistics costs
- Other documented costs
- Target margin
- Indicative selling price
- Commercial documents

The system does not intentionally invent shipping,
tax or customs costs.

These values should be supplied from verified sources.

---

## 4. Find Buyers

The production version can connect the workflow to
authorized business research sources.

Potential workflow:

Market
↓
Target industries
↓
Buyer companies
↓
Relevant departments
↓
Decision-maker roles
↓
Contact / outreach
↓
Follow-up
↓
CRM / Trade Case

---

## 5. Calculate Price

Example structure:

Purchase Cost
+ Logistics
+ Other Documented Costs
+ Target Margin
= Indicative Selling Price

The calculation should use verified commercial inputs.

---

## 6. Trade Operations

A Trade Case can eventually contain:

- Buyer
- Supplier
- Product
- Quotations
- Proforma Invoice
- Documents
- Shipping information
- Emails
- Tasks
- Deadlines
- Follow-ups
- Status

---

# AI Architecture

The application supports two modes.

## Demo Mode

No API key is required.

The application uses deterministic demonstration responses.

This makes it suitable for:

- Client demonstrations
- UI testing
- Early pilot
- Streamlit deployment

---

## Groq AI Mode

Add the following to Streamlit Secrets:

```toml
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
GROQ_MODEL = "llama-3.1-70b-versatile"
