# app.py
import calendar
import json
import math
from pathlib import Path
import streamlit as st


# ---- model loading ----
st.set_page_config(page_title="CKD Hospital Risk (Prototype)", layout="centered")


@st.cache_data
def load_cfg():
    p = Path(__file__).parent / "data" / "model_coeffs.json"
    if not p.exists():
        st.error(f"Missing {p}")
        st.stop()
    return json.loads(p.read_text())


cfg = load_cfg()


def predict(outcome: str, X: dict) -> float:
    spec = cfg["outcomes"][outcome]
    eta = float(spec["intercept"]) + sum(
        float(spec["coeffs"].get(k, 0.0)) * float(X.get(k, 0.0)) for k in spec["coeffs"]
    )
    return 1.0 / (1.0 + math.exp(-eta))


# ---- UI ----

st.markdown(
    """
<style>
div.block-container { max-width: 720px; padding-top: calc(1.5rem + env(safe-area-inset-top)); }
html, body { font-size: 18px; }

/* Metric styles */
div[data-testid="stMetricValue"] { font-size: 2rem; color: #c85040; }
div[data-testid="stMetricLabel"] { font-size: 0.95rem; }

/* Buttons: apply to normal + form submit, same size & color */
.stButton > button,
.stForm > form button {
  background:#6495ed; border-color:#6495ed; color:#fff;
  font-size:1rem; padding:.8rem 1.2rem; width:100%;
}
.stButton > button:hover,
.stForm > form button:hover { filter:brightness(.96); }

/* Notice box */
.notice { background:#fff2ef; border:1px solid #f6c6bf; color:#c85040; padding:10px 12px; border-radius:10px; font-size:0.95rem; }

/* Always show borders on selectboxes (Age, Admission month) */
div[data-baseweb="select"] > div { border: 1px solid #cbd5e1 !important; box-shadow: none !important; }
div[data-baseweb="select"] > div:hover { border-color: #94a3b8 !important; }
div[data-baseweb="select"] > div:focus-within { box-shadow: none !important; }
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    '<h1 style="text-align:center;">CKD Hospital Outcomes<br>Risk Calculator</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="notice">Research demo — Not for clinical use</div>',
    unsafe_allow_html=True,
)

if "show_results" not in st.session_state:
    st.session_state.show_results = False

if not st.session_state.show_results:
    # Eligibility
    st.subheader("Is the primary diagnosis Chronic Kidney Disease (ICD-10 N18.*)?")
    primary_ckd = st.radio(" ", ["Yes", "No / Unsure"], label_visibility="collapsed")
    if primary_ckd != "Yes":
        st.error(
            "This calculator is intended only for admissions where CKD (ICD-10 N18.*) is the primary diagnosis."
        )
        st.stop()

    # Inputs
    with st.form("inputs"):
        st.subheader("Sex")
        sex = st.radio(" ", ["Female", "Male"], label_visibility="collapsed")

        st.subheader("Age")
        age_options = list(range(18, 121))
        age = st.selectbox(
            " ",
            options=age_options,
            index=age_options.index(65),
            label_visibility="collapsed",
        )

        st.subheader("Admission type")
        admission_type = st.radio(
            " ", ["Emergency", "Scheduled"], label_visibility="collapsed"
        )

        st.subheader("Admission month")
        months = list(calendar.month_name)[1:]
        month_name = st.selectbox(" ", options=months, label_visibility="collapsed")

        st.subheader("Comorbidities")
        COMORB_LIST = [
            ("Neoplasms (C00–D49)", "comorb_neoplasm"),
            ("Blood/immune (D50–D89)", "comorb_blood"),
            ("Endocrine/metabolic (E00–E89)", "comorb_endocrine"),
            ("Circulatory (I00–I99)", "comorb_circulatory"),
            ("Respiratory (J00–J99)", "comorb_respiratory"),
            ("Digestive (K00–K95)", "comorb_digestive"),
        ]
        comorb = {key: int(st.checkbox(label)) for label, key in COMORB_LIST}

        submitted = st.form_submit_button("Calculate risk", use_container_width=True)

    if submitted:
        admission_month = months.index(month_name) + 1
        features = {
            "female": 1 if sex == "Female" else 0,
            "age_ge70": 1 if age >= 70 else 0,
            "scheduled_admission": 1 if admission_type == "Scheduled" else 0,
            "warm_month": 1 if admission_month in (3, 4, 5, 6, 7, 8) else 0,
            **comorb,
        }
        st.session_state.results = {
            "death": predict("death_in_hospital", features),
            "los": predict("prolonged_los", features),
        }
        st.session_state.show_results = True
        st.rerun()
else:
    # Results-only view
    r = st.session_state.get("results", {})
    st.subheader("Predicted risks")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("In-Hospital Death", f"{r.get('death', 0.0)*100:.1f}%")
        st.caption("Death from any cause during hospitalization.")
    with c2:
        st.metric("Prolonged Length of Stay (≥8 days)", f"{r.get('los', 0.0)*100:.1f}%")
        st.caption("Hospital stay of 8 days or longer.")

    if st.button("New calculation", use_container_width=True):
        st.session_state.clear()
        st.rerun()
