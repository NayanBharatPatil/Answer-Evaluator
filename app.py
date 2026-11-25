"""Streamlit UI for the Answer Sheet Evaluator.  Run: streamlit run app.py"""
import streamlit as st

from evaluator import PROVIDERS, evaluate

st.set_page_config(page_title="Answer Sheet Evaluator", page_icon="📝", layout="wide")
st.title("📝 Answer Sheet Evaluator")
st.caption("Compare a student's answer with the model answer and get a suggested score with feedback.")

with st.sidebar:
    st.header("LLM settings")
    provider = st.selectbox("Provider", list(PROVIDERS))
    model = st.text_input("Model", PROVIDERS[provider]["model"])
    api_key = st.text_input("API key (or set env variable)", type="password")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1,
                            help="0 gives the most consistent grading.")

col1, col2 = st.columns(2)
with col1:
    question = st.text_area("Question", height=100)
    model_answer = st.text_area("Model answer", height=220)
with col2:
    max_marks = st.number_input("Maximum marks", min_value=1.0, value=10.0, step=1.0)
    student_answer = st.text_area("Student answer", height=220)

if st.button("Evaluate", type="primary"):
    if not (question.strip() and model_answer.strip()):
        st.warning("Please provide the question and the model answer.")
    else:
        try:
            with st.spinner("Evaluating..."):
                r = evaluate(question, model_answer, student_answer, max_marks,
                             provider, model, api_key or None, temperature)
        except Exception as e:
            st.error(f"Evaluation failed: {e}")
        else:
            st.subheader(f"Suggested score: {r.marks:g} / {r.max_marks:g}  ({r.percent:.0f}%)")
            st.progress(min(r.percent / 100, 1.0))
            c1, c2, c3 = st.columns(3)
            c1.metric("Content accuracy", f"{r.rubric['content_accuracy']}/50")
            c2.metric("Completeness", f"{r.rubric['completeness']}/30")
            c3.metric("Clarity", f"{r.rubric['clarity']}/20")

            icons = {"covered": "✅", "partial": "🟡", "missing": "❌"}
            st.markdown("**Key points check**")
            for kp in r.key_points:
                st.write(f"{icons.get(kp.get('status'), '•')} {kp.get('point')}")
            if r.missing_points:
                st.markdown("**Missing points**")
                for p in r.missing_points:
                    st.write(f"- {p}")
            if r.incorrect_statements:
                st.markdown("**Incorrect statements**")
                for p in r.incorrect_statements:
                    st.write(f"- {p}")
            st.markdown("**Feedback**")
            st.info(r.feedback)
            st.caption("This score is a suggestion; the teacher makes the final decision.")
