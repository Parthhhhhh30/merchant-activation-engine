# Outpost Application Notes

## Built project — concise answer

I built a merchant onboarding readiness engine inspired by Outpost's public onboarding workflow. It uses deterministic checks to validate application completeness across common and Merchant-of-Record-specific requirements, surfaces blockers and readiness to an operator, supports merchant follow-up drafting, writes validation results back to Airtable and maintains an audit trail. I deliberately kept compliance-sensitive decisions human-led rather than delegating them to AI. I also deployed an interactive Streamlit demo and added regression tests around the live Airtable data path.

**Demo:** https://merchant-activation-engine.streamlit.app

**Code:** https://github.com/Parthhhhhh30/merchant-activation-engine

## One-line automation answer

I'd automate merchant onboarding first: deterministic checks would validate application completeness and surface blockers before Ops review, while AI would summarise unstructured inputs and draft follow-ups, with human approval retained for compliance decisions.

## 90-second interview structure

1. Problem: prevent incomplete applications reaching high-value human review.
2. Show APP-002 at 94% readiness with Shareholder Register missing.
3. Explain 12 common checks + 6 MoR evidence-presence checks.
4. Explain deterministic vs AI vs human decision ownership.
5. Show that the system can write validation outputs and an audit event to Airtable.
6. Mention the NaN checkbox bug discovered in live testing and the regression test added afterward.
7. Finish with the next measurement: review-cycle reduction, time-to-first-action and repeat follow-up rate.

## Claims I will not make

- not an official Outpost integration
- not used by real merchants
- not a KYC/KYB approval engine
- no claim of time or cost savings without measurement
- no claim that a 100% readiness score means compliant or approved

## Evidence currently demonstrated

- public deployed Streamlit application
- public GitHub repository
- deterministic shared validator
- 12 deliberately constructed synthetic applications
- exact expected blocker tests across the full synthetic portfolio
- live Airtable read/write path tested
- audit-log creation tested
- real live-data bug reproduced and fixed
- automated GitHub test workflow
