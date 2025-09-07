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
/* Layout */
div.block-container { max-width: 720px; padding-top: calc(1.2rem + env(safe-area-inset-top)); }

/* Fluid type: scales from small phones to desktop */
html, body { font-size: clamp(16px, 2.6vw, 18px); }
h1 { font-size: clamp(22px, 5vw, 34px); margin-bottom: .25rem; text-align:center; }
h2, h3 { font-size: clamp(18px, 3.6vw, 22px); }

/* Metrics: big, readable on phones */
div[data-testid="stMetricValue"] { font-size: clamp(24px, 7vw, 40px); color: #c85040; }
div[data-testid="stMetricLabel"] { font-size: clamp(12px, 3vw, 16px); }

/* Make Calculate + New calculation identical */
.stForm button[kind],           /* form submit */
.stButton > button {            /* normal button */
  appearance: none;
  background: #6495ed !important;
  border: 1px solid #6495ed !important;
  color: #fff !important;
  width: 100%;
  font-size: clamp(16px, 3.5vw, 18px);
  /* exact same height on both */
  min-height: 48px !important;
  height: 48px !important;
  padding: 0 16px !important;   /* vertical height now controlled by height */
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 8px !important;
  box-shadow: none !important;
  white-space: nowrap;          /* prevent wrapping -> keeps heights equal */
}
.stForm button[kind]:hover,
.stButton > button:hover { filter: brightness(.96); }


/* Notice box */
.notice {
  background:#fff2ef; border:1px solid #f6c6bf; color:#c85040;
  padding:10px 12px; border-radius:10px; font-size: clamp(13px, 3.2vw, 15px);
}

/* Always-visible borders + bigger tap targets for selects */
div[data-baseweb="select"] > div {
  border: 1px solid #cbd5e1 !important; box-shadow: none !important; min-height: 44px;
}
div[data-baseweb="select"] > div:hover { border-color: #94a3b8 !important; }
div[data-baseweb="select"] > div:focus-within { box-shadow: none !important; }

/* Radios/checkboxes: larger labels/tap area */
div[role="radiogroup"] label, div[data-baseweb="checkbox"] label { padding: 6px 0; font-size: clamp(16px, 3.5vw, 18px); }

/* Stack columns on small screens (metrics one per row) */
@media (max-width: 480px) {
  [data-testid="column"] { width:100% !important; flex: 1 0 100% !important; }
  [data-testid="column"] + [data-testid="column"] { margin-top: .5rem; }
}
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    '<h2 style="text-align:center;">CKD Hospital Outcomes<br>Risk Calculator</h2>',
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

        submitted = st.form_submit_button(
            "Calculate risk", type="primary", use_container_width=True
        )

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
        st.metric("Prolonged Length of Stay", f"{r.get('los', 0.0)*100:.1f}%")
        st.caption("Hospital stay of 8 days or longer.")

    if st.button("New calculation", type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()
