# Merchant Onboarding & Activation Engine

**Live demo:** https://merchant-activation-engine.streamlit.app

An Outpost-aligned portfolio prototype that turns merchant onboarding inputs into a transparent pre-review readiness assessment. It detects missing information with deterministic rules, surfaces blockers to an operator, drafts merchant follow-ups with AI, routes those drafts to a human-review queue, and preserves an audit trail.

> Independent portfolio work using synthetic data. This is not an official Outpost product or integration.

## Problem

A merchant application can reach an operator with avoidable omissions: missing company details, incomplete URLs, or missing Merchant-of-Record evidence. Repeated manual completeness checks create unnecessary review cycles before higher-value compliance judgement can begin.

This prototype separates **mechanical completeness checking** from **human judgement**.

## What I built

- Airtable system of record with `Applications`, `Requirements`, `Follow-up Queue`, and `Activity Log` tables
- 12 deterministic common pre-review checks
- 6 additional Merchant-of-Record evidence-presence checks
- Product-aware readiness scoring and exact blocker detection
- Streamlit operator dashboard and application review screen
- Controlled Airtable read/write path and audit-event creation
- Make workflow that watches merchant-input changes, uses AI only to draft wording, writes drafts to a human-review queue, and records an audit event
- Synthetic portfolio with deliberately constructed pass/fail cases
- Unit, regression, and portfolio-wide tests
- GitHub Actions CI

## Finished workflow

```text
Merchant application changes
        ↓
Airtable - Applications
        ↓
Deterministic helper formulas
readiness + exact blocker list
        ↓
Make workflow
        ↓
AI drafts merchant-facing wording
        ↓
Airtable - Follow-up Queue
status = Pending review
        ↓
Human review / approval
        ↓
Airtable - Activity Log
```

The Streamlit app independently exposes the same deterministic readiness logic for an operator-facing portfolio demo.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the control design and failure modes.

## Control boundary

| Task | Owner | Why |
|---|---|---|
| Required-field presence | Deterministic | Known rule, binary check |
| Email / URL shape | Deterministic | Mechanical validation |
| Readiness and blocker calculation | Deterministic | Must be reproducible |
| Merchant follow-up wording | AI-assisted | Low-risk communication task |
| Follow-up approval | Human | AI output is a draft only |
| Document validity | Human | Requires evidence judgement |
| Beneficial-owner assessment | Human | Compliance-sensitive |
| Merchant approval / rejection | Human | Never delegated to the model |

A `100%` readiness score means **the documented completeness checks passed**. It does not mean the merchant is compliant or approved.

## Rule catalogue

### Common checks - 12

1. Selected regions
2. Business description
3. Store / checkout URL
4. Legal representative name + valid-looking email
5. Company legal name
6. Registration number
7. Tax ID
8. Company website with HTTP(S) scheme
9. Registered address line 1
10. City
11. Postal code
12. Two-character country code

### Additional MoR evidence-presence checks - 6

1. Parties / beneficial owners marked complete
2. Certificate of incorporation present
3. Articles of association present
4. Shareholder register present
5. Payout banking evidence present
6. Regulatory disclosures present

These six checks only confirm that evidence is marked as present. They do **not** validate the evidence itself.

## Verified end-to-end case

`APP-002 - Atlas Learning Ltd` is a synthetic MoR application with one deliberately missing requirement: **Shareholder Register**.

Expected deterministic result:

- 17 / 18 applicable checks pass
- readiness = **94.44%**
- blocker count = **1**
- blocker = **Shareholder Register**

On 1 October 2026 the Make workflow was run end-to-end against this test case. It successfully:

1. read the merchant-input change,
2. consumed the deterministic result,
3. generated a constrained AI follow-up draft,
4. created a `Pending review` record in `Follow-up Queue`, and
5. created a `Follow-up drafted` event in `Activity Log`.

The AI output did not change the deterministic blocker list and did not approve or reject the merchant.

## Synthetic test portfolio

The repository contains 12 synthetic applications with deliberately constructed failure cases. Examples:

- `APP-001`: complete MoR case
- `APP-002`: missing Shareholder Register -> 94.44% readiness
- `APP-005`: missing Store URLs, Articles of Association and Shareholder Register
- `APP-010`: ToR case missing Selected Regions
- `APP-012`: five missing MoR evidence items

`test_portfolio.py` asserts the exact expected blocker list for every synthetic record.

## Failure discovered during live testing

During the first live Airtable write test, an unchecked checkbox was omitted by Airtable and became `NaN` after records were assembled into pandas. The initial implementation interpreted that value as truthy, causing `APP-002` to be incorrectly reported as 100% complete.

The failure was:

1. reproduced against the live synthetic Airtable base,
2. traced to missing-value handling,
3. fixed in the shared validator, and
4. protected with a regression test (`test_nan_checkbox_is_blocked`).

The corrected result for `APP-002` is **94.44% readiness with one blocker: Shareholder Register**.

## Public-demo security

The deployed Streamlit app is read-only by default. Airtable write-back is enabled only when both an Airtable token is configured and `ENABLE_LIVE_WRITE=true` is explicitly set. This prevents a public portfolio visitor from mutating the demo base.

The Make scenario writes AI output to a separate review queue rather than treating it as an approved merchant communication.

No real merchant PII, production credentials, or real compliance documents should be stored in this prototype.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Optional live Airtable mode:

```bash
export AIRTABLE_TOKEN="..."
export AIRTABLE_BASE_ID="apppey78aejeyVjMD"
export ENABLE_LIVE_WRITE="false"
```

Keep `ENABLE_LIVE_WRITE=false` for public deployments. Turn it on only in a controlled test environment.

## Test

```bash
pip install pytest
pytest -q
```

The repository also runs the test suite in GitHub Actions on pushes and pull requests.

## Public source used to shape the prototype

Outpost Partner API onboarding documentation: https://outpost.ai/partner-docs/api-onboarding/

The rule catalogue is an interpretation for portfolio purposes, based on public documentation at the time of development. Production requirements can differ and change over time.

## Limitations

This project does not perform identity verification, sanction screening, legal analysis, tax advice, document-authenticity checks, or compliance approval. It is a pre-review operations prototype focused on completeness, exception visibility, communication support and auditability.
