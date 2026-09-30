import re

COMMON_RULES = [
    ("selectedRegions", "Selected Regions", lambda r: bool(r.get("Selected Regions"))),
    ("businessDescription", "Business Description", lambda r: bool(str(r.get("Business Description", "")).strip())),
    ("checkoutUrl", "Store URLs", lambda r: bool(str(r.get("Store URLs", "")).strip())),
    ("legalRepresentative", "Legal Representative", lambda r: bool(str(r.get("Legal Rep Name", "")).strip()) and bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(r.get("Legal Rep Email", "")).strip()))),
    ("company.legalName", "Company Legal Name", lambda r: bool(str(r.get("Company Legal Name", "")).strip())),
    ("company.registrationNumber", "Registration Number", lambda r: bool(str(r.get("Registration Number", "")).strip())),
    ("company.taxId", "Tax ID", lambda r: bool(str(r.get("Tax ID", "")).strip())),
    ("company.website", "Company Website", lambda r: str(r.get("Company Website", "")).startswith(("http://", "https://"))),
    ("company.registeredAddress.line1", "Address Line 1", lambda r: bool(str(r.get("Address Line 1", "")).strip())),
    ("company.registeredAddress.city", "City", lambda r: bool(str(r.get("City", "")).strip())),
    ("company.registeredAddress.postalCode", "Postal Code", lambda r: bool(str(r.get("Postal Code", "")).strip())),
    ("company.registeredAddress.country", "Country Code", lambda r: len(str(r.get("Country Code", "")).strip()) == 2),
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
        results.append((key, label, bool(fn(row))))
    if row.get("Product") == "MoR":
        for key, label, field in MOR_FIELDS:
            results.append((key, label, bool(row.get(field, False))))
    score = sum(x[2] for x in results) / len(results)
    blockers = [label for _, label, ok in results if not ok]
    return score, blockers, results
