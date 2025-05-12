# Facial Emotion Detection App

This Streamlit application analyzes facial expressions in real-time to detect emotions using the DeepFace library.

## Features

- **Live Detection**: Analyze emotions in real-time using your webcam
- **Patient Monitoring**: Track emotions over time and generate reports
- **Data Export**: Save emotion data to Excel for further analysis

## Emotions Detected

- Happy 😊
- Sad 😢
- Angry 😠
- Fear 😨
- Surprise 😲
- Neutral 😐
- Disgust 🤢

## Project Structure

```
facial-emotion-detection/
├── app.py                # Main application file
├── emotion_detector.py   # Core emotion detection functionality
├── about_page.py         # About page content
├── live_detection.py     # Live detection mode interface
├── patient_monitoring.py # Patient monitoring mode interface
└── requirements.txt      # Required dependencies
```

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   streamlit run app.py
   ```

## Usage

1. Select a mode from the sidebar:
   - **About**: Learn about the application
   - **Live Detection**: Real-time emotion analysis
   - **Patient Monitoring**: Track emotions over time

2. For live detection:
   - Click "Start Camera" to begin
   - Your emotions will be analyzed in real-time
   - View summarized results when complete

3. For patient monitoring:
   - Enter patient information
   - Set monitoring duration and interval
   - Click "Start Monitoring"
   - Review results and export when done

## Technical Details

- Built with Streamlit for the user interface
- Uses DeepFace for facial emotion analysis
- OpenCV for webcam integration
- Plotly for interactive visualizations
- Pandas for data handling
- Memory-efficient design for continuous monitoring

## Privacy

All processing happens locally on your device. No video or images are sent to any server.

## Requirements

- Python 3.6+
- Webcam for live detection
- Dependencies listed in requirements.txt