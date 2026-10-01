# 90-second Demo Script

> I noticed merchant onboarding and operational scaling are part of the Strategy & Operations role, so I built a pre-review readiness engine around Outpost's public onboarding documentation.

Open **APP-002 - Atlas Learning Ltd**.

> This is a synthetic Merchant-of-Record application. The system applies 12 common completeness checks plus six MoR evidence-presence checks. It currently scores 94% because the Shareholder Register is missing.

Show the blocker and per-check table.

> The key design choice is that the blocker is deterministic. I don't use AI to decide whether a merchant is compliant.

Show the follow-up draft / system-design tab.

> AI is only suitable downstream for wording the merchant follow-up from the already-determined blocker list. Evidence validity, compliance judgement and approval remain human-controlled.

Show the architecture / audit trail explanation.

> The system can write readiness, blockers and the follow-up back to Airtable and create an audit event. During live testing I also caught a real data-shape bug: an unchecked Airtable checkbox became NaN and was initially treated as present. I fixed the shared validator and added a regression test.

Finish:

> If I extended this, I would connect it to the real application API and measure review-cycle reduction, time-to-first-action and repeat merchant follow-ups rather than assuming savings upfront.
