import pandas as pd

from validator import validate


EXPECTED_BLOCKERS = {
    "APP-001": [],
    "APP-002": ["Shareholder Register"],
    "APP-003": [],
    "APP-004": ["Business Description"],
    "APP-005": ["Store URLs", "Articles of Association", "Shareholder Register"],
    "APP-006": ["Legal Representative"],
    "APP-007": ["Parties / beneficial owners", "Payout Banking", "Regulatory Disclosures"],
    "APP-008": ["Registration Number"],
    "APP-009": ["Regulatory Disclosures"],
    "APP-010": ["Selected Regions"],
    "APP-011": ["Tax ID"],
    "APP-012": [
        "Certificate of Incorporation",
        "Articles of Association",
        "Shareholder Register",
        "Payout Banking",
        "Regulatory Disclosures",
    ],
}


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


def load_portfolio():
    df = pd.read_csv("synthetic_applications.csv")
    df["Selected Regions"] = df["Selected Regions"].fillna("").map(
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
        df[column] = df[column].map(parse_bool)
    return df


def test_all_synthetic_cases_match_expected_blockers():
    df = load_portfolio()
    assert set(df["Application Ref"]) == set(EXPECTED_BLOCKERS)

    for _, record in df.iterrows():
        _, blockers, _ = validate(record.to_dict())
        assert blockers == EXPECTED_BLOCKERS[record["Application Ref"]]
