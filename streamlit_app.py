import streamlit as st
import joblib
import os

# Set up page config
st.set_page_config(
    page_title="Sinhala-Script LangID",
    page_icon="🔍",
    layout="centered"
)

# Use st.cache_resource so the models are only loaded once and stay in memory
@st.cache_resource
def load_models():
    # When deployed on Streamlit Cloud, the script runs from the repository root.
    model_dir = "models"
    vec_path = os.path.join(model_dir, "langid_vectorizer.pkl")
    model_path = os.path.join(model_dir, "langid_model.pkl")
    
    try:
        vectorizer = joblib.load(vec_path)
        model = joblib.load(model_path)
        return vectorizer, model
    except Exception as e:
        st.error(f"Failed to load models. Error: {e}")
        return None, None

vectorizer, model = load_models()

# UI Elements
st.title("Sinhala-Script Language Identifier")
st.markdown("""
This application identifies whether a given text (written in the Sinhala script) 
belongs to **Sinhala**, **Pali**, or **Sanskrit**.
""")

st.info("💡 **Instruction:** Submitting complete sentences yields significantly higher classification accuracy than submitting single, isolated words.")

# Text input
user_input = st.text_area("Enter text to classify:", height=150)

# Legend
st.markdown("### Color Legend")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("<div style='background-color:#E1F5FE; color:#000000; padding:10px; border-radius:5px; text-align:center;'><b>Sinhala</b></div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div style='background-color:#E8F5E9; color:#000000; padding:10px; border-radius:5px; text-align:center;'><b>Pali</b></div>", unsafe_allow_html=True)
with col3:
    st.markdown("<div style='background-color:#FFFDE7; color:#000000; padding:10px; border-radius:5px; text-align:center;'><b>Sanskrit</b></div>", unsafe_allow_html=True)

st.markdown("---")

if st.button("Classify", type="primary"):
    if not user_input.strip():
        st.warning("Please enter some text to classify.")
    elif vectorizer is None or model is None:
        st.error("Models are not loaded. Cannot perform classification.")
    else:
        with st.spinner("Analyzing text..."):
            text = user_input.strip()
            
            # Predict
            X = vectorizer.transform([text])
            pred_class = model.predict(X)[0]
            probs_array = model.predict_proba(X)[0]
            
            classes = model.classes_
            prob_dict = {classes[i]: float(probs_array[i]) for i in range(len(classes))}
            
            lang = pred_class.upper()
            
            # Determine highlight color
            bg_color = "#FFFFFF" # Default white
            if lang == "SINHALA":
                bg_color = "#E1F5FE" # Light Blue
            elif lang == "PALI":
                bg_color = "#E8F5E9" # Light Green
            elif lang == "SANSKRIT":
                bg_color = "#FFFDE7" # Light Yellow

            st.markdown("### Result")
            
            # Display the color-coded output
            st.markdown(
                f"""
                <div style="background-color: {bg_color}; color: #000000; padding: 20px; border-radius: 10px; border: 1px solid #ddd; font-size: 1.2rem; line-height: 1.6; margin-bottom: 20px;">
                    {user_input}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown(f"**Predicted Language:** {lang}")
            
            st.markdown("### Confidence Scores")
            
            # Ensure consistent order
            for class_name in ["sinhala", "pali", "sanskrit"]:
                if class_name in prob_dict:
                    score = prob_dict[class_name]
                    st.markdown(f"**{class_name.capitalize()}**: {score * 100:.2f}%")
                    st.progress(score)
