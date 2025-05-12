import streamlit as st
import os
from emotion_detector import EmotionDetector
import about_page
import patient_monitoring  # Rename this module too if needed

def main():
    # Set page config
    st.set_page_config(page_title="Emotion Detection App", page_icon="🔍", layout="wide")
  
    
    # Sidebar
    st.sidebar.title("🎈Options")
    app_mode = st.sidebar.selectbox("Choose Mode", ["About", "Person Monitoring"])  # Renamed
    # Use session state to override selection if "Give it a shot" was pressed
    if 'app_mode' in st.session_state:
        app_mode = st.session_state.app_mode
    if app_mode == "About":
        st.sidebar.image("./assets/wow.png", use_container_width=True)
        st.sidebar.markdown("**Hey Bro🖐️**")
    # Main page
    if app_mode == "About":
        about_page.show_about_page()
    elif app_mode == "Person Monitoring":  # Renamed
        patient_monitoring.show_person_monitoring()  # Rename function if needed

# Run the app
if __name__ == "__main__":
    main()
