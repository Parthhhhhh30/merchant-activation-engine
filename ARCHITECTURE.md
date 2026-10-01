# Architecture and Control Design

## System flow

```text
Synthetic merchant input
        |
        v
Airtable - Applications
(system of record)
        |
        +------------------------------+
        |                              |
        v                              v
Python validator                 Airtable helper formulas
12 common checks                 readiness/blocker helpers
+ 6 MoR checks                         |
        |                              |
        +---------------+--------------+
                        |
                        v
                  readiness + blockers
                        |
             +----------+----------+
             |                     |
             v                     v
         Streamlit               Make
       operator view       workflow orchestration
                                   |
                                   v
                          AI-assisted wording
                                   |
                                   v
                              human review
                                   |
                                   v
                        Airtable update + log
```

## Why deterministic checks come first

The completeness rules are known and testable. A model should not decide whether a required field exists or whether a checkbox is present when a deterministic rule can answer that question reproducibly.

The model is therefore restricted to a low-risk role: converting an already-determined blocker list into concise merchant-facing wording. It is not allowed to add requirements, alter the blocker list, or approve/reject a merchant.

## Decision ownership

### Deterministic

- required-field presence
- selected-region presence
- basic email shape
- HTTP(S) website shape
- two-character country-code shape
- product-aware applicability of MoR evidence checks
- readiness calculation
- blocker count and blocker list

### Human evidence review

The following fields can be checked for **presence** deterministically, but their validity remains a human responsibility:

- beneficial-owner / party information
- certificate of incorporation
- articles of association
- shareholder register
- payout banking evidence
- regulatory disclosures

### AI-assisted only

- merchant-facing follow-up wording
- optional operator summarisation

### Never delegated to AI in this prototype

- KYB/KYC approval
- document authenticity decisions
- sanctions or identity decisions
- legal/tax interpretation
- final merchant approval or rejection

## Auditability

A live validation write creates or updates:

- readiness score
- blocker count
- blocker text
- operator summary
- merchant follow-up draft
- last validated timestamp

It also creates an Activity Log event containing the application reference, validation result, details and event time.

## Tested failure mode

### Airtable unchecked checkbox → pandas `NaN`

During live testing, Airtable omitted an unchecked checkbox. When multiple records were assembled into a pandas DataFrame, the missing value became `NaN`. Python's truthiness rules can treat `NaN` as true, which caused a missing Shareholder Register to pass incorrectly.

Mitigation:

- central `is_present()` helper treats `NaN` as missing
- Streamlit imports the shared validator rather than duplicating validation rules
- regression test locks the behavior
- portfolio-level test checks every deliberate synthetic failure case

## Public-deployment safety

The Streamlit public demo is read-only unless `ENABLE_LIVE_WRITE=true` is explicitly configured. This prevents portfolio visitors from changing the Airtable base or consuming write operations.

## Scope boundary

This is a pre-review completeness and operations prototype. It is not a compliance engine and is not connected to Outpost production systems.
