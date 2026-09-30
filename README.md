# Merchant Onboarding & Activation Engine

A portfolio prototype inspired by Outpost's public merchant onboarding documentation.

## What it demonstrates

- Deterministic completeness checks before an application reaches human review
- Separate handling of general application requirements vs Merchant-of-Record KYB evidence
- Operator-facing readiness score and blocker queue
- Draft merchant follow-up generation
- Airtable as the system of record
- Audit logging
- Explicit control boundary: the system does **not** make compliance approval decisions

## Why this architecture

Compliance-sensitive decisions should not be delegated to an LLM. The prototype therefore uses deterministic checks for known completeness requirements and keeps KYB/compliance review human-led. AI can later be added for low-risk unstructured tasks such as summarisation and drafting, while final decisions remain controlled.

## Data

The included Airtable base uses **synthetic merchant data only**. Do not store real customer PII or real compliance documents in this demo.

## Public source used to shape the rule catalogue

Outpost Partner API onboarding documentation:
https://outpost.ai/partner-docs/api-onboarding/

The prototype is independent portfolio work and is not an official Outpost product or integration.

## Run locally

1. Install Python 3.11+
2. `pip install -r requirements.txt`
3. Optional for live mode: create an Airtable Personal Access Token with read/write access to the demo base. Without a token, the app runs fully in bundled synthetic demo mode.
4. Set:
   - `AIRTABLE_TOKEN`
   - `AIRTABLE_BASE_ID=apppey78aejeyVjMD`
5. Run:
   - `streamlit run app.py`

## Test

`pytest -q`

## Current scope

Version 0.2 focuses on pre-review completeness and operational activation readiness.

Next planned layers:
- n8n webhook orchestration
- LLM-assisted merchant follow-up drafting with strict prompt/output schema
- human approval queue
- validation performance test across a larger synthetic portfolio
- Streamlit Cloud deployment
