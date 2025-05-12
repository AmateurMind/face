import streamlit as st
import openai
import requests
from streamlit_lottie import st_lottie


def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


def show_about_page():

    # ---- LOAD ASSETS ----
    lottie_intro = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_fcfjwiyb.json")
    lottie_coding = load_lottieurl("https://lottie.host/1e018e77-81c2-4bbc-bd08-71806d50ab03/hCNWwtpJms.json")

    # --- HERO SECTION ---
    st.title("Facial Emotion Detection😎")
    if st.button("Give it a shot"):
        st.session_state.app_mode = "Person Monitoring"
        st.rerun()  # Force rerun to redirect to monitoring page
    col1, col2 = st.columns(2, gap="small")
    with col1:
        st_lottie(lottie_intro, height=230, key="intro")

    with col2:
        st.title("This is me", anchor=False)
        st.write("Bored with Life.")
        st.markdown("This webpage detects facial emotions in a live webcam feed.")


    with st.container():
        st.write("---")
        left_column, right_column = st.columns(2)
        with left_column:
            st.header("What I do")
            st.write("##")
            st.write(
            """
            This website uses AI to detect and understand **your emotions** while you're browsing.
            
            Here's what it can do:
            - Analyze your facial expressions (if you allow camera access).
            - Read your reactions and engagement with the content.
            - Give you insights into how you might be feeling — happy, bored, focused, or even confused.
            - Adapt or suggest content based on your emotional state.

            It's like having a mirror for your mood — but smarter. Give it a try and see what your face says about you!

            This is AI-Model Video👇
            """
            )
            st.write("[YouTube Channel >](https://www.youtube.com/watch?v=HhHFVPdCgmA)")
        with right_column:
    # Create a new column to control the layout and add some space
            col1, col2 = st.columns([0.1, 1])  # Adjust the 0.1 value to shift the content more right
            with col2:
                st_lottie(lottie_coding, height=300, key="coding")
                st.markdown("""
                    ### Emotions Detected
                    - 😊 **Happy**
                    - 😢 **Sad**
                    - 😠 **Angry**
                    - 😨 **Fear**
                    - 😲 **Surprise**
                    - 😐 **Neutral**
                    - 🤢 **Disgust**
                """)
