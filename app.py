# app.py
import calendar
import streamlit as st

st.set_page_config(page_title="CKD Hospital Risk (Prototype)", layout="centered")
st.title("CKD Hospital Risk Calculator")
st.caption("Research demo • Not for clinical use")

# --- Eligibility ---
primary_ckd = st.radio(
    "Is the **primary diagnosis** Chronic Kidney Disease (ICD-10 N18.*)?",
    ["Yes", "No / Unsure"],
    horizontal=True,
)
if primary_ckd != "Yes":
    st.error(
        "This calculator is intended **only** for admissions where CKD (ICD-10 N18.*) is the **primary diagnosis**."
    )
    st.stop()
st.success("Eligible: primary diagnosis is CKD (N18.*).")

# app.py (snippet — keep imports/eligibility above)

# --- Patient factors aligned to ORs ---
st.subheader("Patient factors")

sex = st.radio("Sex", ["Female", "Male"], horizontal=True)
female = 1 if sex == "Female" else 0  # OR for female

age_group = st.radio("Age group", ["< 70 years", "≥ 70 years"], index=0, horizontal=True)
age_ge70 = 1 if age_group == "≥ 70 years" else 0  # OR for ≥70

admission_type = st.radio("Admission type", ["Emergency", "Scheduled"], horizontal=True)
scheduled_admission = 1 if admission_type == "Scheduled" else 0  # OR for scheduled

months = list(calendar.month_name)[1:]  # Jan–Dec
month_name = st.selectbox("Admission month", options=months)
admission_month = months.index(month_name) + 1
warm_month = 1 if admission_month in (3, 4, 5, 6, 7, 8) else 0  # OR for Mar–Aug

# --- Comorbidities (presence = 1) ---
st.subheader("Comorbidities")
CATEGORIES = [
    {"label": "Neoplasms (C00–D49)", "key": "comorb_neoplasm"},
    {"label": "Blood/immune (D50–D89)", "key": "comorb_blood"},
    {"label": "Endocrine/metabolic (E00–E89)", "key": "comorb_endocrine"},
    {"label": "Circulatory (I00–I99)", "key": "comorb_circulatory"},
    {"label": "Respiratory (J00–J99)", "key": "comorb_respiratory"},
    {"label": "Digestive (K00–K95)", "key": "comorb_digestive"},
]
cols = st.columns(2)
comorb = {c["key"]: int(st.checkbox(c["label"])) for c in CATEGORIES for _ in [0]] if False else {}
# expanded to keep two-column layout:
comorb = {}
for i, c in enumerate(CATEGORIES):
    with cols[i % 2]:
        comorb[c["key"]] = int(st.checkbox(c["label"]))

# Package features for the backend later
features = {
    "female": female,
    "age_ge70": age_ge70,
    "scheduled_admission": scheduled_admission,
    "warm_month": warm_month,
    **comorb,
}
st.session_state["features"] = features

st.caption("Reference groups: male, <70, emergency, Sep–Feb, and no comorbidity in each category.")
