"""
Checklist of critical provisions to check for, per contract type.
Used by the Risk Analyzer to look for MISSING protections that matter
specifically for that kind of contract (an NDA and a lease care about
different things).
"""

CHECKLISTS = {
    "NDA": [
        "Definition of confidential information",
        "Duration of confidentiality obligation",
        "Permitted disclosures / exceptions (e.g. legally required, already public)",
        "Return or destruction of confidential material upon termination",
        "Governing law / jurisdiction",
    ],
    "SaaS / Software Agreement": [
        "Cap on liability",
        "Service level agreement (uptime/support commitments)",
        "Data ownership and data export rights",
        "Termination for convenience",
        "Auto-renewal notice period",
        "Governing law / jurisdiction",
    ],
    "Employment Agreement": [
        "Notice period for termination",
        "Non-compete duration and scope",
        "Compensation and benefits clarity",
        "Confidentiality obligations",
        "Grounds for termination for cause",
    ],
    "Vendor / Service Agreement": [
        "Cap on liability",
        "Indemnification terms",
        "Payment terms and late payment consequences",
        "Termination for convenience",
        "Governing law / jurisdiction",
    ],
    "Lease / Rental Agreement": [
        "Security deposit terms and return conditions",
        "Maintenance and repair responsibilities",
        "Notice period for termination or non-renewal",
        "Rent escalation clause",
        "Governing law / jurisdiction",
    ],
    "Other / General Commercial Agreement": [
        "Cap on liability",
        "Termination for convenience",
        "Governing law / jurisdiction",
        "Confidentiality / data handling",
        "Indemnification terms",
    ],
}

DOCUMENT_TYPES = list(CHECKLISTS.keys())


def get_checklist(document_type: str) -> list:
    return CHECKLISTS.get(document_type, CHECKLISTS["Other / General Commercial Agreement"])