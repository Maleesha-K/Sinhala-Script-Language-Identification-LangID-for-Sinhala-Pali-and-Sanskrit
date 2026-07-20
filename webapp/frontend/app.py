import streamlit as st
import requests

# Constants
API_URL = "http://localhost:8000/predict"

# Set up page config
st.set_page_config(
    page_title="Sinhala-Script LangID",
    page_icon="🔍",
    layout="centered"
)

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
    else:
        with st.spinner("Analyzing text..."):
            try:
                # Send request to FastAPI backend
                response = requests.post(API_URL, json={"text": user_input})
                
                if response.status_code == 200:
                    result = response.json()
                    lang = result.get("language")
                    conf = result.get("confidence", 0.0)
                    
                    # Determine highlight color
                    bg_color = "#FFFFFF" # Default white
                    if lang == "SINHALA":
                        bg_color = "#E1F5FE" # Light Blue
                    elif lang == "PALI":
                        bg_color = "#E8F5E9" # Light Green
                    elif lang == "SANSKRIT":
                        bg_color = "#FFFDE7" # Light Yellow
                    elif lang == "Unknown":
                        bg_color = "#FFEBEE" # Light Red (Error)

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
                    probs = result.get("probabilities", {})
                    
                    # Ensure consistent order
                    for class_name in ["sinhala", "pali", "sanskrit"]:
                        if class_name in probs:
                            score = probs[class_name]
                            st.markdown(f"**{class_name.capitalize()}**: {score * 100:.2f}%")
                            st.progress(score)
                    
                else:
                    st.error(f"Error from backend: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend API. Please ensure the FastAPI server is running on localhost:8000.")
