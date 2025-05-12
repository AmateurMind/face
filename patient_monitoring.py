import streamlit as st
import cv2
import time
import plotly.express as px
import pandas as pd
from emotion_detector import EmotionDetector, get_emotion_emoji

def show_person_monitoring():
    st.title("Emotion Monitoring")
    st.markdown("This mode allows monitoring of emotions over time.")
    
    # Add sidebar info
    st.sidebar.title("Emotion Monitor")
    st.sidebar.markdown("""
    ### Instructions
    1. Enter information
    2. Set monitoring duration and interval
    3. Click "Start Monitoring"
    4. Review results and export data when done
    """)
    
    # Display info about the system requirements
    with st.sidebar.expander("System Requirements"):
        st.markdown("""
        - Webcam must be connected
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
    
    # Form for person information
    with st.form("person_form"):
        st.subheader("Information")
        
        person_id = st.text_input("User ID", "P12345")
        
        # Using default camera (ID 0)
        camera_id = 0
        
        col3, col4 = st.columns(2)
        
        with col3:
            duration_minutes = st.number_input("Monitoring Duration (minutes)", 
                                            min_value=1, max_value=60, value=5, step=1)
        
        with col4:
            interval_seconds = st.number_input("Analysis Interval (seconds)", 
                                            min_value=1, max_value=30, value=2, step=1)
        
        submit_button = st.form_submit_button("Start Monitoring")
        
        if submit_button:
            st.session_state.person_detector = EmotionDetector(person_id)
            st.session_state.monitoring_active = True
            st.session_state.monitoring_start_time = time.time()
            st.session_state.monitoring_end_time = st.session_state.monitoring_start_time + (duration_minutes * 60)
            st.rerun()

    
    # Display monitoring progress
    if st.session_state.monitoring_active:
        # Progress bar
        progress_col, stop_col = st.columns([3, 1])
        
        with progress_col:
            progress_bar = st.progress(0)
        
        with stop_col:
            if st.button("Stop Monitoring"):
                st.session_state.monitoring_active = False
                st.experimental_rerun()
        
        # Status information
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            time_remaining = st.empty()
        
        with status_col2:
            readings_count = st.empty()
        
        # Video and emotion display
        video_col, emotion_col = st.columns([3, 2])
        
        with video_col:
            video_placeholder = st.empty()
            current_emotion = st.empty()
        
        with emotion_col:
            emotion_chart = st.empty()
        
        # Open camera
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            st.error("Could not open camera. Please check if camera is connected.")
            st.session_state.monitoring_active = False
        else:
            last_analysis_time = 0
            
            try:
                while st.session_state.monitoring_active:
                    current_time = time.time()
                    
                    # Check if monitoring period has ended
                    if current_time >= st.session_state.monitoring_end_time:
                        st.session_state.monitoring_active = False
                        break
                    
                    # Update progress bar
                    elapsed = current_time - st.session_state.monitoring_start_time
                    total_duration = st.session_state.monitoring_end_time - st.session_state.monitoring_start_time
                    progress = min(elapsed / total_duration, 1.0)
                    progress_bar.progress(progress)
                    
                    # Update time remaining
                    time_left = st.session_state.monitoring_end_time - current_time
                    minutes_left, seconds_left = divmod(int(time_left), 60)
                    time_remaining.markdown(f"**Time Remaining**: {minutes_left}m {seconds_left}s")
                    
                    # Update readings count
                    readings_count.markdown(f"**Readings**: {len(st.session_state.person_detector.emotions_log)}")
                    
                    # Capture frame
                    ret, frame = cap.read()
                    
                    if not ret:
                        st.error("Failed to capture frame")
                        continue
                    
                    # Display video
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    video_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)
                    
                    # Analyze emotions at specified interval
                    if current_time - last_analysis_time >= interval_seconds:
                        emotion_data = st.session_state.person_detector.analyze_frame(frame)
                        
                        if emotion_data:
                            emotion = emotion_data['dominant_emotion']
                            emoji = get_emotion_emoji(emotion)
                            current_emotion.markdown(f"## Current: {emotion} {emoji}")
                            
                            # Update chart if we have enough data
                            if len(st.session_state.person_detector.emotions_log) > 0:
                                df, summary_df = st.session_state.person_detector.get_summary()
                                
                                fig = px.pie(summary_df, values='Percentage', names='Emotion', 
                                            title='Emotion Distribution',
                                            color='Emotion',
                                            color_discrete_sequence=px.colors.qualitative.Plotly)
                                fig.update_traces(textposition='inside', textinfo='percent+label')
                                
                                emotion_chart.plotly_chart(fig, use_container_width=True)
                        
                        last_analysis_time = current_time
                    
                    time.sleep(0.1)  # Short delay
                    
            except Exception as e:
                st.error(f"Error during monitoring: {str(e)}")
            finally:
                cap.release()
                st.session_state.monitoring_active = False
    
    # Show results if monitoring is complete and we have data
    if not st.session_state.monitoring_active and st.session_state.person_detector and st.session_state.person_detector.emotions_log:
        st.subheader("Monitoring Results")
        
        # Summary visualization
        df, summary_df = st.session_state.person_detector.get_summary()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            fig1 = px.pie(summary_df, values='Percentage', names='Emotion', 
                        title='Emotion Distribution',
                        color='Emotion',
                        color_discrete_sequence=px.colors.qualitative.Plotly)
            fig1.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Bar chart
            fig2 = px.bar(summary_df, x='Emotion', y='Count', 
                        title='Emotion Counts',
                        color='Emotion',
                        text='Count',
                        color_discrete_sequence=px.colors.qualitative.Plotly)
            fig2.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)
        
        # Timeline visualization
        timeline_data = []
        for entry in st.session_state.person_detector.emotions_log:
            timeline_data.append({
                'Timestamp': entry['timestamp'],
                'Emotion': entry['dominant_emotion']
            })
        
        timeline_df = pd.DataFrame(timeline_data)
        
        fig3 = px.scatter(timeline_df, x='Timestamp', y='Emotion', 
                        title='Emotion Timeline',
                        color='Emotion',
                        color_discrete_sequence=px.colors.qualitative.Plotly)
        st.plotly_chart(fig3, use_container_width=True)
        
        # Export options
        st.subheader("Export Data")
        
        if st.button("Generate Report"):
            excel_data, filename = st.session_state.person_detector.export_to_excel()
            
            st.download_button(
                label="Download Excel Report",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Raw data
        with st.expander("View Raw Data"):
            st.dataframe(df)
