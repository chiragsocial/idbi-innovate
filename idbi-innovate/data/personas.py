"""
Persona (borrower-segment) definitions for the synthetic MSME data engine.

Each segment differs in:
  - scale        : realistic monthly revenue/income range (INR)
  - vintage      : business age range (months)
  - ntc_prob     : P(New-to-Credit) — no bureau history
  - ntb_prob     : P(New-to-Bank)
  - udyam_prob   : P(registered as MSME on Udyam)
  - avail        : P(each alternate-data source is present) — THIS is what makes
                   one persona lean on electricity, another on FASTag, etc.
  - cw_mean      : mean latent creditworthiness (0..1, higher = safer)

The availability profile is the crux of the "thin-file / adaptive" story:
a gig worker has almost no GST but rich UPI; a manufacturer has strong
electricity; a transporter has strong fuel + FASTag.
"""

# Alternate-data sources whose presence varies by persona.
SOURCES = [
    "gst", "upi", "aa", "epf", "electricity", "fuel", "fastag",
]

PERSONAS = {
    "manufacturer": {
        "scale": (300_000, 5_000_000),
        "vintage": (18, 240),
        "ntc_prob": 0.35, "ntb_prob": 0.55, "udyam_prob": 0.80, "cw_mean": 0.55,
        "avail": {"gst": .90, "upi": .80, "aa": .80, "epf": .80,
                  "electricity": .95, "fuel": .30, "fastag": .10},
    },
    "trader": {
        "scale": (200_000, 4_000_000),
        "vintage": (12, 180),
        "ntc_prob": 0.40, "ntb_prob": 0.55, "udyam_prob": 0.65, "cw_mean": 0.52,
        "avail": {"gst": .85, "upi": .90, "aa": .80, "epf": .40,
                  "electricity": .50, "fuel": .40, "fastag": .20},
    },
    "transport": {
        "scale": (150_000, 3_000_000),
        "vintage": (12, 180),
        "ntc_prob": 0.45, "ntb_prob": 0.60, "udyam_prob": 0.55, "cw_mean": 0.50,
        "avail": {"gst": .60, "upi": .70, "aa": .80, "epf": .30,
                  "electricity": .30, "fuel": .90, "fastag": .90},
    },
    "services": {
        "scale": (100_000, 2_000_000),
        "vintage": (6, 150),
        "ntc_prob": 0.45, "ntb_prob": 0.55, "udyam_prob": 0.55, "cw_mean": 0.53,
        "avail": {"gst": .70, "upi": .85, "aa": .80, "epf": .50,
                  "electricity": .50, "fuel": .20, "fastag": .10},
    },
    "retail": {
        "scale": (80_000, 1_500_000),
        "vintage": (6, 150),
        "ntc_prob": 0.50, "ntb_prob": 0.55, "udyam_prob": 0.45, "cw_mean": 0.50,
        "avail": {"gst": .60, "upi": .95, "aa": .80, "epf": .20,
                  "electricity": .60, "fuel": .10, "fastag": .05},
    },
    "agri": {
        "scale": (50_000, 1_000_000),
        "vintage": (6, 240),
        "ntc_prob": 0.60, "ntb_prob": 0.60, "udyam_prob": 0.25, "cw_mean": 0.48,
        "avail": {"gst": .20, "upi": .50, "aa": .70, "epf": .10,
                  "electricity": .50, "fuel": .50, "fastag": .10},
    },
    "gig": {
        "scale": (20_000, 120_000),
        "vintage": (3, 96),
        "ntc_prob": 0.60, "ntb_prob": 0.50, "udyam_prob": 0.10, "cw_mean": 0.50,
        "avail": {"gst": .10, "upi": .95, "aa": .80, "epf": .05,
                  "electricity": .20, "fuel": .30, "fastag": .20},
    },
    "salaried": {
        "scale": (25_000, 200_000),
        "vintage": (6, 360),   # "vintage" ~ months in current employment
        "ntc_prob": 0.40, "ntb_prob": 0.50, "udyam_prob": 0.02, "cw_mean": 0.58,
        "avail": {"gst": .05, "upi": .90, "aa": .90, "epf": .85,
                  "electricity": .40, "fuel": .20, "fastag": .20},
    },
    "professional": {
        "scale": (100_000, 1_500_000),
        "vintage": (12, 300),
        "ntc_prob": 0.35, "ntb_prob": 0.50, "udyam_prob": 0.40, "cw_mean": 0.60,
        "avail": {"gst": .60, "upi": .85, "aa": .85, "epf": .40,
                  "electricity": .50, "fuel": .20, "fastag": .15},
    },
}

# Rough population mix (weights) so the dataset looks like a real MSME book.
SEGMENT_WEIGHTS = {
    "retail": 0.22, "trader": 0.16, "services": 0.15, "manufacturer": 0.12,
    "transport": 0.10, "gig": 0.09, "professional": 0.07, "agri": 0.06,
    "salaried": 0.03,
}

# Indian states (with a coarse regional-risk nudge) for geography features.
STATES = [
    ("Maharashtra", 0.00), ("Gujarat", -0.02), ("Karnataka", -0.01),
    ("Tamil Nadu", -0.01), ("Delhi", 0.00), ("Uttar Pradesh", 0.04),
    ("Bihar", 0.06), ("West Bengal", 0.03), ("Rajasthan", 0.02),
    ("Telangana", -0.01), ("Punjab", 0.01), ("Kerala", -0.01),
    ("Madhya Pradesh", 0.03), ("Odisha", 0.03), ("Assam", 0.04),
]
