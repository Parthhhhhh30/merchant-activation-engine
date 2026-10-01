import os
import uuid
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

from validator import validate

BASE_ID = os.getenv("AIRTABLE_BASE_ID", "apppey78aejeyVjMD")
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
APPLICATIONS_TABLE = "Applications"
ACTIVITY_TABLE = "Activity Log"

st.set_page_config(page_title="Merchant Activation Engine", layout="wide")


def airtable_headers():
    if not AIRTABLE_TOKEN:
        raise RuntimeError("AIRTABLE_TOKEN is not configured.")
    return {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}


def fetch_table(table_name):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_name}"
    rows = []
    params = {"pageSize": 100}
    while True:
        resp = requests.get(url, headers=airtable_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("records", []):
            row = {"_record_id": item["id"]}
            row.update(item.get("fields", {}))
            rows.append(row)
        if "offset" not in data:
            break
        params["offset"] = data["offset"]
    return pd.DataFrame(rows)


def patch_record(record_id, fields):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{APPLICATIONS_TABLE}/{record_id}"
    resp = requests.patch(url, headers=airtable_headers(), json={"fields": fields}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def log_event(app_ref, result, details):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{ACTIVITY_TABLE}"
    payload = {"fields": {
        "Event ID": f"EVT-{uuid.uuid4().hex[:8].upper()}",
        "Application Ref": app_ref,
        "Event Type": "Validation",
        "Result": result,
        "Details": details,
        "Event Time": datetime.now(timezone.utc).isoformat(),
    }}
    resp = requests.post(url, headers=airtable_headers(), json=payload, timeout=30)
    resp.raise_for_status()


def validate_row(row):
    score, blockers, results = validate(row)
    human_keys = {
        "parties",
        "documents[CERTIFICATE_OF_INCORPORATION]",
        "documents[ARTICLES_OF_ASSOCIATION]",
        "documents[SHAREHOLDER_REGISTER]",
        "payoutBanking",
        "regulatoryDisclosures",
    }
    checks = [
        {
            "key": key,
            "label": label,
            "passed": ok,
            "type": "human-evidence" if key in human_keys else "deterministic",
        }
        for key, label, ok in results
    ]
    return score, blockers, checks


def follow_up(merchant_name, blockers):
    if not blockers:
        return f"Hi {merchant_name}, your application appears complete for pre-review. An operator should still perform the required human checks before submission."
    lines = "\n".join(f"- {b}" for b in blockers)
    return (
        f"Hi {merchant_name},\n\n"
        "Thanks for starting your onboarding. Before the application is ready for review, "
        "please complete the following items:\n"
        f"{lines}\n\n"
        "Once these are supplied, the application can be re-validated. "
        "This prototype does not make compliance decisions; final review remains human-led."
    )


def operator_summary(score, blockers, product):
    readiness = f"{score:.0%}"
    if not blockers:
        return f"{product} application is {readiness} complete against this prototype's documented pre-review checks. No completeness blockers detected; human compliance review is still required."
    return f"{product} application is {readiness} complete with {len(blockers)} blocker(s): " + ", ".join(blockers[:5]) + ("." if len(blockers) <= 5 else ", plus additional items.")


st.title("Merchant Onboarding & Activation Engine")
st.caption("Outpost-aligned portfolio prototype using synthetic data. Deterministic completeness checks + human-controlled compliance review.")

with st.sidebar:
    st.subheader("Architecture")
    st.write("Airtable → deterministic validator → operator queue → drafted merchant follow-up → audit log")
    st.warning("No real merchant PII. No live Outpost credentials. This is a portfolio prototype, not an official Outpost integration.")

demo_mode = not bool(AIRTABLE_TOKEN)
if demo_mode:
    st.info("Demo mode: using bundled synthetic data. Configure AIRTABLE_TOKEN to enable live Airtable read/write.")
    df = pd.read_csv("synthetic_applications.csv")
    df["Selected Regions"] = df["Selected Regions"].fillna("").map(lambda x: [s.strip() for s in str(x).split(",") if s.strip()])
    for col in ["Parties Complete", "Certificate of Incorporation", "Articles of Association", "Shareholder Register", "Payout Banking", "Regulatory Disclosures"]:
        df[col] = df[col].fillna(False).astype(bool)
    df["_record_id"] = df["Application Ref"]
else:
    try:
        df = fetch_table(APPLICATIONS_TABLE)
    except Exception as e:
        st.error(f"Could not load Airtable: {e}")
        st.stop()

if df.empty:
    st.info("No applications found.")
    st.stop()

summary_rows = []
for _, r in df.iterrows():
    score, blockers, _ = validate_row(r.to_dict())
    summary_rows.append({
        "Application Ref": r.get("Application Ref"),
        "Merchant": r.get("Merchant Name"),
        "Product": r.get("Product"),
        "Status": r.get("Application Status"),
        "Readiness": score,
        "Blockers": len(blockers),
    })
summary = pd.DataFrame(summary_rows)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Applications", len(summary))
c2.metric("Ready for pre-review", int((summary["Blockers"] == 0).sum()))
c3.metric("Blocked", int((summary["Blockers"] > 0).sum()))
c4.metric("Average readiness", f"{summary['Readiness'].mean():.0%}")

st.subheader("Portfolio")
show = summary.copy()
show["Readiness"] = show["Readiness"].map(lambda x: f"{x:.0%}")
st.dataframe(show, use_container_width=True, hide_index=True)

st.subheader("Validate an application")
choice = st.selectbox("Application", df["Application Ref"].tolist())
row = df.loc[df["Application Ref"] == choice].iloc[0].to_dict()
score, blockers, checks = validate_row(row)

a, b, c = st.columns(3)
a.metric("Readiness", f"{score:.0%}")
b.metric("Blockers", len(blockers))
c.metric("Product", row.get("Product", ""))

check_df = pd.DataFrame(checks)
check_df["status"] = check_df["passed"].map({True: "PASS", False: "BLOCK"})
st.dataframe(check_df[["label", "status", "type"]], use_container_width=True, hide_index=True)

draft = follow_up(row.get("Merchant Name", "merchant"), blockers)
summary_text = operator_summary(score, blockers, row.get("Product", ""))

st.text_area("Operator summary", summary_text, height=100)
st.text_area("Merchant follow-up draft", draft, height=220)

if st.button("Write validation result to Airtable", type="primary", disabled=demo_mode):
    fields = {
        "Readiness Score": score,
        "Blocker Count": len(blockers),
        "Blockers": "\n".join(blockers),
        "Operator Summary": summary_text,
        "Merchant Follow-up Draft": draft,
        "Last Validated": datetime.now(timezone.utc).isoformat(),
    }
    try:
        patch_record(row["_record_id"], fields)
        log_event(
            row["Application Ref"],
            "Pass" if not blockers else "Blocked",
            f"Readiness {score:.0%}; blockers: {', '.join(blockers) if blockers else 'none'}",
        )
        st.success("Validation result and audit event written to Airtable.")
    except Exception as e:
        st.error(f"Write failed: {e}")
