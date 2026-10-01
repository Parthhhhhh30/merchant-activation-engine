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
12 common checks                 readiness + blocker helpers
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
                    Airtable - Follow-up Queue
                      status: Pending review
                                   |
                                   v
                              human review
                                   |
                                   v
                        Airtable - Activity Log
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
- deterministic operator summary

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

AI output is written to a separate `Follow-up Queue` with `Pending review` status. It is not treated as an approved communication.

### Never delegated to AI in this prototype

- KYB/KYC approval
- document authenticity decisions
- sanctions or identity decisions
- legal/tax interpretation
- final merchant approval or rejection

## Operational tables

### Applications

Source merchant inputs, current deterministic readiness helpers, and operator-facing validation outputs.

### Requirements

Explainable catalogue of the public-documentation-derived checks used to shape the prototype.

### Follow-up Queue

Stores AI-assisted merchant follow-up drafts together with application reference, merchant name, blocker list, generation time and review status. New drafts enter as `Pending review`.

### Activity Log

Stores timestamped validation and follow-up events for auditability.

## Verified automation path

For `APP-002 - Atlas Learning Ltd`, the deterministic layer returns:

- MoR application
- readiness = 94.44%
- blocker count = 1
- blocker = Shareholder Register

The verified Make flow is:

```text
Watch merchant-input changes
        ↓
Read deterministic Airtable outputs
        ↓
AI drafts constrained follow-up wording
        ↓
Create Follow-up Queue record
        ↓
Create Activity Log event
```

The successful end-to-end test created both the review-queue record and corresponding audit event without changing the deterministic blocker result.

## Streamlit controlled-write path

In a controlled environment, the Streamlit application can write these deterministic outputs back to the Applications row:

- readiness score
- blocker count
- blocker text
- operator summary
- deterministic fallback merchant follow-up
- last validated timestamp

It also creates an Activity Log validation event.

The public deployment keeps this write path disabled by default.

## Tested failure mode

### Airtable unchecked checkbox -> pandas `NaN`

During live testing, Airtable omitted an unchecked checkbox. When multiple records were assembled into a pandas DataFrame, the missing value became `NaN`. Python's truthiness rules can treat `NaN` as true, which caused a missing Shareholder Register to pass incorrectly.

Mitigation:

- central `is_present()` helper treats `NaN` as missing
- Streamlit imports the shared validator rather than duplicating validation rules
- regression test locks the behavior
- portfolio-level test checks every deliberate synthetic failure case

## Public-deployment safety

The Streamlit public demo is read-only unless `ENABLE_LIVE_WRITE=true` is explicitly configured. This prevents portfolio visitors from changing the Airtable base or consuming write operations.

The Make automation separates generated text from source application data by routing drafts into a human-review queue rather than treating them as approved communications.

## Scope boundary

This is a pre-review completeness and operations prototype. It is not a compliance engine and is not connected to Outpost production systems.
