"""Turn free-text job titles into a small set of job families."""

import re

import pandas as pd

ABBREVIATIONS = {
    r"\brn\b": "registered nurse",
    r"\blpn\b": "licensed practical nurse",
    r"\bcna\b": "nursing assistant",
    r"\bmgr\b": "manager",
    r"\basst\b": "assistant",
    r"\bsr\b": "senior",
    r"\bjr\b": "junior",
    r"\badmin\b": "administrative",
    r"\bvp\b": "vice president",
    r"\bceo\b": "chief executive",
    r"\bcfo\b": "chief financial",
    r"\bcpa\b": "accountant",
    r"\bit\b": "information technology",
    r"\bcsr\b": "customer service",
    r"\bsgt\b": "sergeant",
    r"\busaf\b": "air force",
}

JOB_FAMILIES = [
    ("Nursing", ["nurse", "nurses", "nursing"]),
    ("Healthcare", ["physician", "doctor", "pharmacist", "pharmacy", "therapist", "medical",
                    "dental", "hospital", "health", "clinical", "paramedic", "kaiser",
                    "social worker", "caregiver"]),
    ("Education", ["teacher", "professor", "instructor", "educator", "school", "principal", "tutor"]),
    ("Public safety & military", ["police", "sheriff", "deputy", "firefighter", "army", "navy",
                                  "air force", "marine", "military", "sergeant", "correctional"]),
    ("Senior management", ["president", "director", "chief", "partner"]),
    ("Legal, finance & consulting", ["attorney", "lawyer", "paralegal", "accountant", "accounting",
                                     "finance", "financial", "bank", "banker", "underwriter",
                                     "auditor", "controller", "bookkeeper", "teller", "wells fargo",
                                     "consultant"]),
    ("Engineering & IT", ["engineer", "developer", "software", "programmer", "information technology",
                          "systems", "network", "data", "analyst"]),
    ("Driving & transport", ["driver", "trucker", "pilot", "dispatcher", "delivery", "courier",
                             "usps", "postal", "letter carrier", "mail carrier", "ups", "fedex",
                             "flight attendant"]),
    ("Skilled trades", ["electrician", "mechanic", "technician", "tech", "foreman", "carpenter",
                        "plumber", "welder", "machinist", "operator", "maintenance", "construction",
                        "installer", "hvac"]),
    ("Food & hospitality", ["server", "cook", "chef", "bartender", "waiter", "waitress",
                            "restaurant", "hotel", "housekeeper"]),
    ("Management", ["manager", "supervisor", "lead", "superintendent", "administrator"]),
    ("Labor & service", ["laborer", "custodian", "janitor", "warehouse", "security", "guard"]),
    ("Sales & retail", ["sales", "retail", "cashier", "store", "merchandiser", "walmart", "wal mart",
                        "home depot", "account executive", "agent"]),
    ("Office & admin", ["assistant", "clerk", "office", "receptionist", "secretary",
                        "administrative", "customer service", "coordinator", "specialist",
                        "representative", "associate"]),
    ("Owner & self-employed", ["owner", "self employed", "contractor"]),
]

_PATTERNS = [
    (family, re.compile(r"\b(" + "|".join(re.escape(word) for word in words) + r")\b"))
    for family, words in JOB_FAMILIES
]


def clean_title(title):
    """Lowercase, remove punctuation, expand common abbreviations."""
    if title is None or pd.isna(title):
        return ""
    text = str(title).lower().strip()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    for pattern, replacement in ABBREVIATIONS.items():
        text = re.sub(pattern, replacement, text)
    return re.sub(r"\s+", " ", text).strip()


def job_family(title):
    """Map one raw job title to its job family."""
    text = clean_title(title)
    if not text:
        return "Missing"
    for family, pattern in _PATTERNS:
        if pattern.search(text):
            return family
    return "Other"



def add_job_family(df):
    """Add a job_family column from the raw emp_title column, then drop emp_title."""
    df = df.copy()
    if "emp_title" in df.columns:
        titles = df["emp_title"]
    else:
        titles = pd.Series(index=df.index, dtype="object")
    df["job_family"] = titles.map(job_family)
    return df.drop(columns=["emp_title"], errors="ignore")