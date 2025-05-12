import streamlit as st
import cv2
import time
import plotly.express as px
import pandas as pd
from emotion_detector import EmotionDetector, get_emotion_emoji


def get_available_cameras(max_to_check=5):
    available_cameras = []
    for i in range(max_to_check):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    available_cameras.append(i)
                cap.release()
        except Exception as e:
            st.warning(f"Error checking camera {i}: {str(e)}")
    return available_cameras


def show_person_monitoring():
    st.title("Emotion Monitoring")
    st.markdown("This mode allows monitoring of emotions over time.")

    st.sidebar.title("Emotion Monitor")
    st.sidebar.markdown("""
    ### Instructions
    1. Enter information  
    2. Set monitoring duration and interval  
    3. Click "Start Monitoring"  
    4. Review results and export data when done
    """)

    with st.sidebar.expander("System Requirements"):
        st.markdown("""
        - Webcam must be connected  
        - Good lighting for accurate detection  
        - Person should face the camera  
        - Requires Python 3.6+ and DeepFace
        """)

    available_cameras = get_available_cameras()
    

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
        camera_id = st.selectbox("Select Camera", available_cameras, index=0)

        col1, col2 = st.columns(2)
        with col1:
            duration_minutes = st.number_input("Monitoring Duration (minutes)", 1, 60, 5, 1)
        with col2:
            interval_seconds = st.number_input("Analysis Interval (seconds)", 1, 30, 2, 1)

        submit_button = st.form_submit_button("Start Monitoring")

        if submit_button:
            st.session_state.person_detector = EmotionDetector(person_id)
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

        video_col, emotion_col = st.columns([3, 2])
        video_placeholder = video_col.empty()
        current_emotion = video_col.empty()
        emotion_chart = emotion_col.empty()

        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            st.error(f"Could not open camera with index {camera_id}.")
            st.session_state.monitoring_active = False
            return

        last_analysis_time = 0
        try:
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
                readings_count.markdown(f"**Readings:** {len(st.session_state.person_detector.emotions_log)}")

                ret, frame = cap.read()
                if not ret or frame is None or frame.size == 0:
                    st.error("Failed to capture frame.")
                    break

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)

                if current_time - last_analysis_time >= interval_seconds:
                    emotion_data = st.session_state.person_detector.analyze_frame(frame)
                    if emotion_data:
                        emotion = emotion_data['dominant_emotion']
                        emoji = get_emotion_emoji(emotion)
                        current_emotion.markdown(f"## Current: {emotion} {emoji}")

                        if st.session_state.person_detector.emotions_log:
                            df, summary_df = st.session_state.person_detector.get_summary()
                            fig = px.pie(summary_df, values='Percentage', names='Emotion',
                                         title='Emotion Distribution',
                                         color_discrete_sequence=px.colors.qualitative.Plotly)
                            fig.update_traces(textposition='inside', textinfo='percent+label')
                            emotion_chart.plotly_chart(fig, use_container_width=True)
                    last_analysis_time = current_time

                time.sleep(0.1)
        except Exception as e:
            st.error(f"Error during monitoring: {e}")
        finally:
            cap.release()
            st.session_state.monitoring_active = False

    if not st.session_state.monitoring_active and st.session_state.person_detector and st.session_state.person_detector.emotions_log:
        st.subheader("Monitoring Results")
        df, summary_df = st.session_state.person_detector.get_summary()

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
                         for e in st.session_state.person_detector.emotions_log]
        timeline_df = pd.DataFrame(timeline_data)

        fig3 = px.scatter(timeline_df, x='Timestamp', y='Emotion', title='Emotion Timeline',
                          color='Emotion', color_discrete_sequence=px.colors.qualitative.Plotly)
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Export Data")
        if st.button("Generate Report"):
            excel_data, filename = st.session_state.person_detector.export_to_excel()
            st.download_button("Download Excel Report", data=excel_data, file_name=filename,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with st.expander("View Raw Data"):
            st.dataframe(df)
