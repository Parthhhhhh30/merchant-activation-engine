import math
import re


def is_present(value):
    """Return False for Airtable/pandas-style missing values as well as blanks."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    try:
        if math.isnan(value):
            return False
    except (TypeError, ValueError):
        pass
    return bool(value)


COMMON_RULES = [
    ("selectedRegions", "Selected Regions", lambda r: is_present(r.get("Selected Regions"))),
    ("businessDescription", "Business Description", lambda r: is_present(r.get("Business Description"))),
    ("checkoutUrl", "Store URLs", lambda r: is_present(r.get("Store URLs"))),
    (
        "legalRepresentative",
        "Legal Representative",
        lambda r: is_present(r.get("Legal Rep Name"))
        and is_present(r.get("Legal Rep Email"))
        and bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(r.get("Legal Rep Email")).strip())),
    ),
    ("company.legalName", "Company Legal Name", lambda r: is_present(r.get("Company Legal Name"))),
    ("company.registrationNumber", "Registration Number", lambda r: is_present(r.get("Registration Number"))),
    ("company.taxId", "Tax ID", lambda r: is_present(r.get("Tax ID"))),
    (
        "company.website",
        "Company Website",
        lambda r: is_present(r.get("Company Website"))
        and str(r.get("Company Website")).strip().startswith(("http://", "https://")),
    ),
    ("company.registeredAddress.line1", "Address Line 1", lambda r: is_present(r.get("Address Line 1"))),
    ("company.registeredAddress.city", "City", lambda r: is_present(r.get("City"))),
    ("company.registeredAddress.postalCode", "Postal Code", lambda r: is_present(r.get("Postal Code"))),
    (
        "company.registeredAddress.country",
        "Country Code",
        lambda r: is_present(r.get("Country Code")) and len(str(r.get("Country Code")).strip()) == 2,
    ),
]

MOR_FIELDS = [
    ("parties", "Parties / beneficial owners", "Parties Complete"),
    ("documents[CERTIFICATE_OF_INCORPORATION]", "Certificate of Incorporation", "Certificate of Incorporation"),
    ("documents[ARTICLES_OF_ASSOCIATION]", "Articles of Association", "Articles of Association"),
    ("documents[SHAREHOLDER_REGISTER]", "Shareholder Register", "Shareholder Register"),
    ("payoutBanking", "Payout Banking", "Payout Banking"),
    ("regulatoryDisclosures", "Regulatory Disclosures", "Regulatory Disclosures"),
]


def validate(row):
    results = []
    for key, label, fn in COMMON_RULES:
        try:
            ok = bool(fn(row))
        except Exception:
            ok = False
        results.append((key, label, ok))

    if row.get("Product") == "MoR":
        for key, label, field in MOR_FIELDS:
            results.append((key, label, is_present(row.get(field))))

    score = sum(x[2] for x in results) / len(results) if results else 0
    blockers = [label for _, label, ok in results if not ok]
    return score, blockers, results
