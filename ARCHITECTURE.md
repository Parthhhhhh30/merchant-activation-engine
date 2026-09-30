# Architecture

```text
Synthetic merchant application
          |
          v
      Airtable
  (system of record)
          |
          v
Deterministic readiness validator
  |                   |
  | complete          | blockers
  v                   v
operator review     blocker queue
  |                   |
  +---------+---------+
            |
            v
  follow-up draft layer
            |
            v
     human approval
            |
            v
       merchant
            |
            v
        audit log
```

## Control design

- **Deterministic:** required fields, URL/email shape, presence checks, product-specific requirements.
- **Human-controlled:** beneficial-owner completeness, document validity, bank evidence, regulatory disclosures.
- **LLM-suitable later:** summarising descriptions, drafting communications, categorising free text.
- **Never delegated blindly:** compliance approval, identity verification, regulatory judgment.
