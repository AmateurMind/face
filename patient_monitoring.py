import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
import cv2
import time
import plotly.express as px
import pandas as pd
from emotion_detector import EmotionDetector, get_emotion_emoji

class EmotionVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.last_analysis_time = 0
        self.interval_seconds = 2
        self.emotion_detector = None
        self.current_emotion = ""
        self.emoji = ""
        self.frame = None

    def set_detector(self, detector):
        self.emotion_detector = detector

    def set_interval(self, interval):
        self.interval_seconds = interval

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        current_time = time.time()

        if self.emotion_detector and current_time - self.last_analysis_time >= self.interval_seconds:
            emotion_data = self.emotion_detector.analyze_frame(img)
            if emotion_data:
                emotion = emotion_data['dominant_emotion']
                self.current_emotion = emotion
                self.emoji = get_emotion_emoji(emotion)
            self.last_analysis_time = current_time

        self.frame = img
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def show_person_monitoring():
    st.title("Emotion Monitoring (WebRTC)")
    st.markdown("Monitor emotions via browser-based webcam.")

    with st.sidebar:
        st.header("Settings")
        person_id = st.text_input("User ID", "P12345")
        duration_minutes = st.slider("Monitoring Duration (minutes)", 1, 60, 5)
        interval_seconds = st.slider("Analysis Interval (seconds)", 1, 30, 2)

    processor = EmotionVideoProcessor()
    processor.set_detector(EmotionDetector(person_id))
    processor.set_interval(interval_seconds)

    webrtc_ctx = webrtc_streamer(
        key="emotion-monitoring",
        video_processor_factory=lambda: processor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True
    )

    if webrtc_ctx.video_processor:
        readings = processor.emotion_detector.emotions_log

        st.markdown(f"### Current Emotion: {processor.current_emotion} {processor.emoji}")
        st.markdown(f"**Readings Count:** {len(readings)}")

        if len(readings) > 0:
            df, summary_df = processor.emotion_detector.get_summary()
            fig1 = px.pie(summary_df, values='Percentage', names='Emotion',
                         title='Emotion Distribution')
            fig2 = px.bar(summary_df, x='Emotion', y='Count',
                         title='Emotion Counts', text='Count')

            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)

            st.subheader("Timeline")
            timeline_df = pd.DataFrame([
                {'Timestamp': entry['timestamp'], 'Emotion': entry['dominant_emotion']}
                for entry in readings
            ])
            fig3 = px.scatter(timeline_df, x='Timestamp', y='Emotion', color='Emotion')
            st.plotly_chart(fig3, use_container_width=True)

            st.subheader("Export Data")
            if st.button("Generate Report"):
                excel_data, filename = processor.emotion_detector.export_to_excel()
                st.download_button(
                    label="Download Excel Report",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
