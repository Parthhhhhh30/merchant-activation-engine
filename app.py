import os
import uuid
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

from validator import validate

st.set_page_config(
    page_title="Merchant Activation Engine",
    page_icon="✓",
    layout="wide",
)


def config_value(name, default=None):
    """Read Streamlit secrets when available, then fall back to environment variables."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


BASE_ID = config_value("AIRTABLE_BASE_ID", "apppey78aejeyVjMD")
AIRTABLE_TOKEN = config_value("AIRTABLE_TOKEN")
ENABLE_LIVE_WRITE = str(config_value("ENABLE_LIVE_WRITE", "false")).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
APPLICATIONS_TABLE = "Applications"
ACTIVITY_TABLE = "Activity Log"
MOR_EVIDENCE_KEYS = {
    "parties",
    "documents[CERTIFICATE_OF_INCORPORATION]",
    "documents[ARTICLES_OF_ASSOCIATION]",
    "documents[SHAREHOLDER_REGISTER]",
    "payoutBanking",
    "regulatoryDisclosures",
}


def airtable_headers():
    if not AIRTABLE_TOKEN:
        raise RuntimeError("AIRTABLE_TOKEN is not configured.")
    return {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}


def fetch_table(table_name):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_name}"
    rows = []
    params = {"pageSize": 100}
    while True:
        response = requests.get(url, headers=airtable_headers(), params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("records", []):
            row = {"_record_id": item["id"]}
            row.update(item.get("fields", {}))
            rows.append(row)
        if "offset" not in payload:
            break
        params["offset"] = payload["offset"]
    return pd.DataFrame(rows)


def patch_record(record_id, fields):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{APPLICATIONS_TABLE}/{record_id}"
    response = requests.patch(
        url,
        headers=airtable_headers(),
        json={"fields": fields},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def log_event(application_ref, result, details):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{ACTIVITY_TABLE}"
    payload = {
        "fields": {
            "Event ID": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "Application Ref": application_ref,
            "Event Type": "Validation",
            "Result": result,
            "Details": details,
            "Event Time": datetime.now(timezone.utc).isoformat(),
        }
    }
    response = requests.post(url, headers=airtable_headers(), json=payload, timeout=30)
    response.raise_for_status()


def parse_bool(value):
    """Safely parse CSV/Airtable booleans without treating the string 'False' as truthy."""
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


def validate_row(row):
    score, blockers, results = validate(row)
    checks = [
        {
            "Requirement": label,
            "Status": "PASS" if ok else "BLOCK",
            "Control": "Human evidence review" if key in MOR_EVIDENCE_KEYS else "Deterministic",
        }
        for key, label, ok in results
    ]
    return score, blockers, checks


def follow_up(merchant_name, blockers):
    """Deterministic fallback draft. The Make workflow can replace this with AI-assisted phrasing."""
    if not blockers:
        return (
            f"Hi {merchant_name},\n\n"
            "Your application appears complete for pre-review. An operator should still perform "
            "the required human checks before any compliance-sensitive decision is made."
        )
    lines = "\n".join(f"- {blocker}" for blocker in blockers)
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
        return (
            f"{product} application is {readiness} complete against this prototype's documented "
            "pre-review checks. No completeness blockers detected; human compliance review is still required."
        )
    shown = ", ".join(blockers[:5])
    suffix = "." if len(blockers) <= 5 else ", plus additional items."
    return f"{product} application is {readiness} complete with {len(blockers)} blocker(s): {shown}{suffix}"


def load_demo_data():
    frame = pd.read_csv("synthetic_applications.csv")
    frame["Selected Regions"] = frame["Selected Regions"].fillna("").map(
        lambda value: [item.strip() for item in str(value).split(",") if item.strip()]
    )
    for column in [
        "Parties Complete",
        "Certificate of Incorporation",
        "Articles of Association",
        "Shareholder Register",
        "Payout Banking",
        "Regulatory Disclosures",
    ]:
        frame[column] = frame[column].map(parse_bool)
    frame["_record_id"] = frame["Application Ref"]
    return frame


st.title("Merchant Onboarding & Activation Engine")
st.caption(
    "Outpost-aligned portfolio prototype using synthetic data. "
    "Deterministic pre-review checks, AI-suitable communication support, human-controlled compliance decisions."
)

with st.sidebar:
    st.subheader("Prototype boundary")
    st.write("**Deterministic:** completeness, field shape, readiness, blocker detection")
    st.write("**AI-suitable:** summarisation and merchant-facing draft wording")
    st.write("**Human-only:** evidence validity, compliance judgement, approval/rejection")
    st.divider()
    st.caption("No real merchant PII. No live Outpost credentials. Independent portfolio work, not an official Outpost integration.")

live_read_mode = bool(AIRTABLE_TOKEN)
if live_read_mode:
    try:
        df = fetch_table(APPLICATIONS_TABLE)
        source_label = "Live synthetic Airtable base"
    except Exception as exc:
        st.warning(f"Airtable could not be loaded; falling back to bundled demo data. ({exc})")
        df = load_demo_data()
        live_read_mode = False
        source_label = "Bundled synthetic dataset"
else:
    df = load_demo_data()
    source_label = "Bundled synthetic dataset"

if df.empty:
    st.info("No applications found.")
    st.stop()

summary_rows = []
for _, record in df.iterrows():
    score, blockers, _ = validate_row(record.to_dict())
    summary_rows.append(
        {
            "Application Ref": record.get("Application Ref"),
            "Merchant": record.get("Merchant Name"),
            "Product": record.get("Product"),
            "Application Status": record.get("Application Status"),
            "Readiness": score,
            "Blockers": len(blockers),
        }
    )
summary = pd.DataFrame(summary_rows)

overview_tab, review_tab, design_tab = st.tabs(["Portfolio overview", "Application review", "System design"])

with overview_tab:
    st.caption(f"Data source: {source_label}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Applications", len(summary))
    c2.metric("Ready for pre-review", int((summary["Blockers"] == 0).sum()))
    c3.metric("Blocked", int((summary["Blockers"] > 0).sum()))
    c4.metric("Average readiness", f"{summary['Readiness'].mean():.0%}")

    display = summary.copy()
    display["Readiness"] = display["Readiness"].map(lambda value: f"{value:.0%}")
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.info(
        "A 'ready for pre-review' result means the documented completeness checks passed. "
        "It does not mean the merchant is compliant or approved."
    )

with review_tab:
    application_ref = st.selectbox("Application", df["Application Ref"].tolist(), index=1 if len(df) > 1 else 0)
    row = df.loc[df["Application Ref"] == application_ref].iloc[0].to_dict()
    score, blockers, checks = validate_row(row)

    a, b, c = st.columns(3)
    a.metric("Readiness", f"{score:.0%}")
    b.metric("Blockers", len(blockers))
    c.metric("Product", row.get("Product", ""))
    st.progress(score)

    if blockers:
        st.error("Pre-review blockers: " + ", ".join(blockers))
    else:
        st.success("No completeness blockers detected. Human evidence/compliance review is still required.")

    st.dataframe(pd.DataFrame(checks), use_container_width=True, hide_index=True)

    draft = follow_up(row.get("Merchant Name", "merchant"), blockers)
    summary_text = operator_summary(score, blockers, row.get("Product", ""))

    left, right = st.columns(2)
    with left:
        st.text_area("Operator summary", summary_text, height=170, disabled=True)
    with right:
        st.text_area("Merchant follow-up draft", draft, height=170, disabled=True)

    can_write = live_read_mode and ENABLE_LIVE_WRITE
    if not can_write:
        st.caption(
            "Public demo is read-only by default. The live write-back path was tested against the synthetic Airtable base; "
            "set ENABLE_LIVE_WRITE=true only in a controlled environment."
        )

    if st.button("Write validation result to Airtable", type="primary", disabled=not can_write):
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
        except Exception as exc:
            st.error(f"Write failed: {exc}")

with design_tab:
    st.subheader("Workflow")
    st.code(
        "Merchant application\n"
        "        ↓\n"
        "Airtable system of record\n"
        "        ↓\n"
        "Deterministic readiness checks\n"
        "        ↓\n"
        "Readiness + blocker list\n"
        "        ↓\n"
        "Make orchestration / AI-assisted wording\n"
        "        ↓\n"
        "Human review\n"
        "        ↓\n"
        "Airtable update + audit trail",
        language="text",
    )

    st.subheader("Control boundary")
    control_df = pd.DataFrame(
        [
            ["Required-field presence", "Deterministic", "Yes"],
            ["Email / URL shape", "Deterministic", "Yes"],
            ["Readiness / blocker calculation", "Deterministic", "Yes"],
            ["Merchant follow-up wording", "AI-assisted or deterministic fallback", "Human can review"],
            ["Document validity", "Human", "Required"],
            ["Beneficial-owner assessment", "Human", "Required"],
            ["Compliance approval / rejection", "Human", "Required"],
        ],
        columns=["Task", "Owner", "Control"],
    )
    st.dataframe(control_df, use_container_width=True, hide_index=True)

    st.subheader("Tested failure mode")
    st.write(
        "During live Airtable testing, an unchecked checkbox arrived as a missing pandas value (NaN). "
        "The first implementation interpreted it as truthy. The bug was reproduced, fixed in the shared validator, "
        "and protected with a regression test."
    )

    st.subheader("Limitations")
    st.write(
        "This prototype tests completeness against a documented rule catalogue. It does not verify identities, "
        "validate uploaded documents, make legal/tax determinations, or represent Outpost production logic."
    )
