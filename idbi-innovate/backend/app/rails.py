"""
Mocked integration with India's digital lending rails — Account Aggregator (AA),
OCEN and ULI. These return realistic request/response SHAPES so the demo shows
exactly where the product plugs into the ecosystem; on the bank's sandbox these
handlers would call the real APIs.

Also provides deterministic source-synthesis for the what-if simulator: when an
underwriter "requests AA consent" or "pulls GST", we fill that source with values
consistent with the applicant's cross-validated revenue, then re-score.
"""

# Fields each source contributes, and how to synthesize them from an estimated
# monthly revenue (deterministic — no randomness, so the demo is reproducible).
_SYNTH = {
    "gst": lambda rev, seg: {
        "gst_available": 1,
        "gst_turnover_monthly": int(rev * 0.85),
        "gst_trend_pct": 6.0,
        "gst_volatility": 0.28,
        "gst_filing_regularity": 0.85,
        "gst_months_filed": 24,
    },
    "aa": lambda rev, seg: {
        "aa_available": 1,
        "bank_inflow_monthly": int(rev * 1.05),
        "bank_outflow_monthly": int(rev * 0.85),
        "bank_avg_balance": int(rev * 0.30),
        "bank_buffer_days": 32.0,
        "bank_bounces_12m": 1,
        "existing_emi_monthly": int(rev * 0.10),
    },
    "epf": lambda rev, seg: {
        "epf_available": 1,
        "epf_employee_count": max(1, int(rev / 150000)),
        "epf_months_contributed": 36,
    },
    "electricity": lambda rev, seg: {
        "electricity_available": 1,
        "electricity_units_monthly": int(rev / 130),
        "electricity_trend_pct": 8.0,
    },
    "upi": lambda rev, seg: {
        "upi_available": 1,
        "upi_inflow_monthly": int(rev * 0.6),
        "upi_txn_count": int(rev * 0.6 / 600),
        "upi_volatility": 0.30,
    },
}

_SOURCE_FIELDS = {
    "gst": ["gst_available", "gst_turnover_monthly", "gst_trend_pct", "gst_volatility",
            "gst_filing_regularity", "gst_months_filed"],
    "aa": ["aa_available", "bank_inflow_monthly", "bank_outflow_monthly", "bank_avg_balance",
           "bank_buffer_days", "bank_bounces_12m", "existing_emi_monthly"],
    "epf": ["epf_available", "epf_employee_count", "epf_months_contributed"],
    "electricity": ["electricity_available", "electricity_units_monthly", "electricity_trend_pct"],
    "upi": ["upi_available", "upi_inflow_monthly", "upi_txn_count", "upi_volatility"],
}


def apply_source(row, source, est_rev):
    """Return a COPY of row with `source` added (synthesized) — for the simulator."""
    new = dict(row)
    if source in _SYNTH:
        new.update(_SYNTH[source](est_rev or 300000, row.get("segment", "trader")))
    return new


def remove_source(row, source):
    """Return a COPY of row with `source` removed (blanked)."""
    new = dict(row)
    for field in _SOURCE_FIELDS.get(source, []):
        new[field] = 0 if field.endswith("_available") else ""
    return new


# ------------------------------------------------------------------ mocked rails
def aa_consent(entity_id, fips=("HDFC Bank", "SBI")):
    """Mock an Account Aggregator consent artefact (RBI/Sahamati flow shape)."""
    return {
        "rail": "Account Aggregator",
        "consent_id": f"AA-CONSENT-{entity_id}",
        "status": "ACTIVE",
        "purpose": "Loan underwriting — MSME credit assessment",
        "data_fetched": ["Bank statements (12 mo)", "Deposits", "Recurring debits"],
        "fips": list(fips),
        "consent_expiry": "consent valid for this application only (data-minimisation)",
        "audit": f"Consent recorded in audit trail for {entity_id}.",
    }


def ocen_application(entity_id):
    """Mock an OCEN loan-application lifecycle (LSP <-> lender protocol)."""
    return {
        "rail": "OCEN",
        "application_id": f"OCEN-APP-{entity_id}",
        "states": ["APPLICATION_INITIATED", "OFFER_GENERATED", "OFFER_ACCEPTED",
                   "DISBURSAL_PENDING"],
        "current_state": "OFFER_GENERATED",
        "loan_service_provider": "IDBI MSME Digital Lending",
    }


def uli_pull(entity_id):
    """Mock a ULI data-aggregation pull (RBI Unified Lending Interface)."""
    return {
        "rail": "ULI (Unified Lending Interface)",
        "request_id": f"ULI-{entity_id}",
        "sources_aggregated": ["GSTN returns", "Aadhaar eKYC", "Land records",
                               "Bank AA feed", "EPFO", "Udyam registry"],
        "latency_ms": 850,
        "note": "Consent-driven, standardized data aggregation for real-time appraisal.",
    }
