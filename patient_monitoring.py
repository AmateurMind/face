import streamlit as st
import cv2
import time
import plotly.express as px
import pandas as pd
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
from emotion_detector import EmotionDetector, get_emotion_emoji

class EmotionVideoTransformer(VideoTransformerBase):
    def __init__(self, person_id, interval_seconds):
        self.person_detector = EmotionDetector(person_id)
        self.interval_seconds = interval_seconds
        self.last_analysis_time = 0
        self.current_emotion = None
        self.emotion_emoji = None

    def transform(self, frame):
        # Convert WebRTC frame to OpenCV format
        img = frame.to_ndarray(format="bgr")
        
        current_time = time.time()
        if current_time - self.last_analysis_time >= self.interval_seconds:
            emotion_data = self.person_detector.analyze_frame(img)
            if emotion_data:
                self.current_emotion = emotion_data['dominant_emotion']
                self.emotion_emoji = get_emotion_emoji(self.current_emotion)
                self.last_analysis_time = current_time
        
        return img

def show_person_monitoring():
    st.title("Emotion Monitoring")
    st.markdown("This mode allows monitoring of emotions over time.")

    st.sidebar.title("Emotion Monitor")
    st.sidebar.markdown("""
    ### Instructions
    1. Allow camera access  
    2. Set monitoring duration and interval  
    3. Click "Start Monitoring"  
    4. Review results and export data when done
    """)

    with st.sidebar.expander("System Requirements"):
        st.markdown("""
        - Camera access required  
        - Good lighting for accurate detection  
        - Person should face the camera  
        - Requires Python 3.6+ and DeepFace
        """)

    if 'monitoring_active' not in st.session_state:
        st.session_state.monitoring_active = False
    if 'person_detector' not in st.session_state:
        st.session_state.person_detector = None
    if 'monitoring_start_time' not in st.session_state:
        st.session_state.monitoring_start_time = None
    if 'monitoring_end_time' not in st.session_state:
        st.session_state.monitoring_end_time = None

    with st.form("person_form"):
        st.subheader("Information")
        person_id = st.text_input("User ID", "P12345")

        col1, col2 = st.columns(2)
        with col1:
            duration_minutes = st.number_input("Monitoring Duration (minutes)", 1, 60, 5, 1)
        with col2:
            interval_seconds = st.number_input("Analysis Interval (seconds)", 1, 30, 2, 1)

        submit_button = st.form_submit_button("Start Monitoring")

        if submit_button:
            st.session_state.monitoring_active = True
            st.session_state.monitoring_start_time = time.time()
            st.session_state.monitoring_end_time = st.session_state.monitoring_start_time + (duration_minutes * 60)
            st.rerun()

    if st.session_state.monitoring_active:
        progress_col, stop_col = st.columns([3, 1])
        with progress_col:
            progress_bar = st.progress(0)
        with stop_col:
            if st.button("Stop Monitoring"):
                st.session_state.monitoring_active = False
                st.experimental_rerun()

        col1, col2 = st.columns(2)
        time_remaining = col1.empty()
        readings_count = col2.empty()

        # WebRTC Streamer
        video_transformer = EmotionVideoTransformer(person_id, interval_seconds)
        webrtc_ctx = webrtc_streamer(
            key="emotion-monitoring",
            video_transformer_factory=lambda: video_transformer,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )

        # Display current emotion if available
        if video_transformer.current_emotion:
            st.markdown(f"## Current: {video_transformer.current_emotion} {video_transformer.emotion_emoji}")

        # Monitoring time and progress tracking
        while st.session_state.monitoring_active:
            current_time = time.time()
            if current_time >= st.session_state.monitoring_end_time:
                st.session_state.monitoring_active = False
                break

            elapsed = current_time - st.session_state.monitoring_start_time
            total_duration = st.session_state.monitoring_end_time - st.session_state.monitoring_start_time
            progress_bar.progress(min(elapsed / total_duration, 1.0))

            time_left = int(st.session_state.monitoring_end_time - current_time)
            m, s = divmod(time_left, 60)
            time_remaining.markdown(f"**Time Remaining:** {m}m {s}s")
            
            # Update readings count if emotions are being logged
            if hasattr(video_transformer, 'person_detector'):
                readings_count.markdown(f"**Readings:** {len(video_transformer.person_detector.emotions_log)}")

            time.sleep(1)

    # Display results after monitoring
    if not st.session_state.monitoring_active and video_transformer.person_detector and video_transformer.person_detector.emotions_log:
        st.subheader("Monitoring Results")
        df, summary_df = video_transformer.person_detector.get_summary()

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(summary_df, values='Percentage', names='Emotion', title='Emotion Distribution',
                          color_discrete_sequence=px.colors.qualitative.Plotly)
            fig1.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(summary_df, x='Emotion', y='Count', text='Count',
                          color_discrete_sequence=px.colors.qualitative.Plotly)
            fig2.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)

        timeline_data = [{'Timestamp': e['timestamp'], 'Emotion': e['dominant_emotion']}
                         for e in video_transformer.person_detector.emotions_log]
        timeline_df = pd.DataFrame(timeline_data)

        fig3 = px.scatter(timeline_df, x='Timestamp', y='Emotion', title='Emotion Timeline',
                          color='Emotion', color_discrete_sequence=px.colors.qualitative.Plotly)
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Export Data")
        if st.button("Generate Report"):
            excel_data, filename = video_transformer.person_detector.export_to_excel()
            st.download_button("Download Excel Report", data=excel_data, file_name=filename,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with st.expander("View Raw Data"):
            st.dataframe(df)

# Requirements for this script
# pip install streamlit streamlit-webrtc opencv-python plotly pandas deepface openpyxl
