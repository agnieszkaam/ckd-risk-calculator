# app.py
import calendar
import json
import math
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

# ---- page & model loading ----
# Must be the FIRST Streamlit call on the page.

st.set_page_config(page_title="CKD Hospital Risk (Prototype)", layout="centered")
st.markdown('<div id="top"></div>', unsafe_allow_html=True)


@st.cache_data  # cache file read across reruns; invalidates if file changes
def load_cfg():
    """Load model coefficients JSON: data/model_coeffs.json"""
    p = Path(__file__).parent / "data" / "model_coeffs.json"
    if not p.exists():
        st.error(f"Missing {p}")
        st.stop()
    return json.loads(p.read_text())


cfg = load_cfg()


def predict(outcome: str, X: dict) -> float:
    """Logistic prediction: σ(β0 + Σ βk * xk). Expects keys matching JSON."""
    spec = cfg["outcomes"][outcome]
    eta = float(spec["intercept"]) + sum(
        float(spec["coeffs"].get(k, 0.0)) * float(X.get(k, 0.0)) for k in spec["coeffs"]
    )
    return 1.0 / (1.0 + math.exp(-eta))


def scroll_to(selector="#top", smooth=True):
    """Scroll the Streamlit page to a CSS selector (e.g., '#top', '#results')."""
    behavior = "smooth" if smooth else "instant"
    components.html(
        f"""
        <script>
        const el = window.parent.document.querySelector('{selector}');
        if (el) el.scrollIntoView({{behavior: '{behavior}', block: 'start'}});
        </script>
        """,
        height=0,
    )


# ---- UI ----
# Mobile-first CSS: fluid typography, consistent button styles, visible select borders.
st.markdown(
    """
<style>
/* Layout */
div.block-container { max-width: 720px; padding-top: calc(1.2rem + env(safe-area-inset-top)); }

/* Fluid type */
html, body { font-size: clamp(16px, 2.6vw, 18px); }
h1 { font-size: clamp(22px, 5vw, 34px); margin-bottom: .25rem; text-align:center; }
h2, h3 { font-size: clamp(18px, 3.6vw, 22px); }

/* Metrics */
div[data-testid="stMetricValue"] { font-size: clamp(24px, 7vw, 40px); color: #c85040; }
div[data-testid="stMetricLabel"] { font-size: clamp(12px, 3vw, 16px); }

/* Buttons (unified for submit + normal buttons) */
.stForm button[kind], .stButton > button {
  appearance: none; background: #6495ed !important; border: 1px solid #6495ed !important; color: #fff !important;
  width: 100%; font-size: clamp(16px, 3.5vw, 18px); min-height: 48px !important; height: 48px !important;
  padding: 0 16px !important; display: flex !important; align-items: center !important; justify-content: center !important;
  border-radius: 8px !important; box-shadow: none !important; white-space: nowrap;
}
.stForm button[kind]:hover, .stButton > button:hover { filter: brightness(.96); }

/* Notice */
.notice { background:#fff2ef; border:1px solid #f6c6bf; color:#c85040; padding:10px 12px; border-radius:10px; font-size: clamp(13px, 3.2vw, 15px); }

/* Selects: visible borders + tap targets */
div[data-baseweb="select"] > div { border: 1px solid #cbd5e1 !important; box-shadow: none !important; min-height: 44px; }
div[data-baseweb="select"] > div:hover { border-color: #94a3b8 !important; }
div[data-baseweb="select"] > div:focus-within { box-shadow: none !important; }

/* Radios/checkboxes */
div[role="radiogroup"] label, div[data-baseweb="checkbox"] label { padding: 6px 0; font-size: clamp(16px, 3.5vw, 18px); }

/* Stack columns on small screens */
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


# simple state flag: show form first, then results-only view
if "show_results" not in st.session_state:
    st.session_state.show_results = False


if not st.session_state.show_results:
    # Eligibility gate (stops early if not CKD primary)
    scroll_to("#top", smooth=False)
    st.markdown("##### Is the primary diagnosis Chronic Kidney Disease (ICD-10 N18.*)?")
    primary_ckd = st.radio(" ", ["Yes", "No / Unsure"], label_visibility="collapsed")
    if primary_ckd != "Yes":
        st.error(
            "This calculator is intended only for admissions where CKD (ICD-10 N18.*) is the primary diagnosis."
        )
        st.stop()

    # Inputs (form groups inputs and gives a single submit)
    with st.form("inputs"):
        # Sex (horizontal radio: inline + wraps on small screens)
        sex = st.radio("Sex", ["Female", "Male"], horizontal=True)

        # Age (dropdown keeps vertical footprint small on phones)
        age_options = list(range(18, 121))
        age = st.selectbox(
            "Age (years)", options=age_options, index=age_options.index(65)
        )

        # Admission type (horizontal radio)
        admission_type = st.radio(
            "Admission type", ["Emergency", "Scheduled"], horizontal=True
        )

        # Admission month
        months = list(calendar.month_name)[1:]
        month_name = st.selectbox("Admission month", options=months)

        # Comorbidities (compact 2-column grid)
        COMORB_LIST = [
            ("Neoplasms (C00–D49)", "comorb_neoplasm"),
            ("Blood/immune (D50–D89)", "comorb_blood"),
            ("Endocrine/metabolic (E00–E89)", "comorb_endocrine"),
            ("Circulatory (I00–I99)", "comorb_circulatory"),
            ("Respiratory (J00–J99)", "comorb_respiratory"),
            ("Digestive (K00–K95)", "comorb_digestive"),
        ]
        st.markdown(
            "<div style='font-size:16px'>Comorbidities</div>", unsafe_allow_html=True
        )
        cols = st.columns(2)
        comorb = {}
        for i, (label, key) in enumerate(COMORB_LIST):
            with cols[i % 2]:
                comorb[key] = int(st.checkbox(label, key=f"cb_{key}"))

        submitted = st.form_submit_button(
            "Calculate risk", type="primary", use_container_width=True
        )

        if submitted:
            # Map UI to model features expected by JSON
            admission_month = months.index(month_name) + 1
            features = {
                "female": 1 if sex == "Female" else 0,
                "age_ge70": 1 if age >= 70 else 0,
                "scheduled_admission": 1 if admission_type == "Scheduled" else 0,
                "warm_month": 1 if admission_month in (3, 4, 5, 6, 7, 8) else 0,
                **comorb,
            }

            # Save inputs for display later (avoid key clash with form)
            selected_comorb = [label for (label, key) in COMORB_LIST if comorb.get(key)]
            st.session_state.input_summary = {
                "Sex": sex,
                "Age (years)": age,
                "Admission type": admission_type,
                "Admission month": month_name,
                "Comorbidities": (
                    ", ".join(selected_comorb) if selected_comorb else "None"
                ),
            }

            # Compute and show results-only view
            st.session_state.results = {
                "death": predict("death_in_hospital", features),
                "los": predict("prolonged_los", features),
            }
            st.session_state.show_results = True
            st.rerun()
else:
    # Results-only view (compact metrics for mobile)
    r = st.session_state.get("results", {})
    st.subheader("Predicted risks*")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("In-Hospital Death", f"{r.get('death', 0.0)*100:.1f}%")
        st.caption("Death from any cause during hospitalization.")
    with c2:
        st.metric("Prolonged Length of Stay", f"{r.get('los', 0.0)*100:.1f}%")
        st.caption("Hospital stay of 8 days or longer.")

    scroll_to("#top")

    # Only show the list if inputs were captured
    inputs = st.session_state.get("input_summary")
    if inputs:
        st.markdown("##### Inputs used")
        for k, v in inputs.items():
            st.markdown(f"- **{k}:** {v}")

    if st.button("New calculation", type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.caption("*Outputs are estimated probabilities (uncalibrated).")
