import math

from validator import validate


def base_tor():
    return {
        "Product":"ToR",
        "Selected Regions":["EU"],
        "Business Description":"Software",
        "Store URLs":"https://example.com/pay",
        "Legal Rep Name":"Test User",
        "Legal Rep Email":"test@example.com",
        "Company Legal Name":"Test Ltd",
        "Registration Number":"123",
        "Tax ID":"GB123",
        "Company Website":"https://example.com",
        "Address Line 1":"1 Road",
        "City":"London",
        "Postal Code":"E1 1AA",
        "Country Code":"GB",
    }


def test_complete_tor_passes():
    score, blockers, _ = validate(base_tor())
    assert score == 1
    assert blockers == []


def test_missing_region_blocks():
    row = base_tor()
    row["Selected Regions"] = []
    score, blockers, _ = validate(row)
    assert score < 1
    assert "Selected Regions" in blockers


def test_mor_adds_six_checks():
    row = base_tor()
    row["Product"] = "MoR"
    for field in ["Parties Complete","Certificate of Incorporation","Articles of Association","Shareholder Register","Payout Banking","Regulatory Disclosures"]:
        row[field] = True
    score, blockers, results = validate(row)
    assert score == 1
    assert len(results) == 18


def test_nan_checkbox_is_blocked():
    row = base_tor()
    row["Product"] = "MoR"
    for field in ["Parties Complete","Certificate of Incorporation","Articles of Association","Payout Banking","Regulatory Disclosures"]:
        row[field] = True
    row["Shareholder Register"] = float("nan")
    score, blockers, _ = validate(row)
    assert score < 1
    assert "Shareholder Register" in blockers
