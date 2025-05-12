import cv2
import numpy as np
import pandas as pd
import datetime
import io
from deepface import DeepFace
import logging

class EmotionDetector:
    def __init__(self, patient_id=None, max_log_entries=100):
        """
        Initialize EmotionDetector with optional patient ID and max log entries.
        
        :param patient_id: Unique identifier for the patient
        :param max_log_entries: Maximum number of emotion entries to store
        """
        self.patient_id = patient_id or "default"
        self.emotions_log = []
        self.max_log_entries = max_log_entries
        
        # Configure logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def analyze_frame(self, frame):
        """
        Analyze emotion in a given frame.
        
        :param frame: OpenCV image frame
        :return: Dictionary with emotion analysis or None if analysis fails
        """
        try:
            # Validate input frame
            if frame is None or frame.size == 0:
                self.logger.warning("Empty or invalid frame received")
                return None
            
            # Use smaller size image for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            
            # Detect emotions with robust configuration
            result = DeepFace.analyze(small_frame, 
                                    actions=['emotion'],
                                    enforce_detection=False,
                                    detector_backend='opencv')  # Faster detector
            
            current_emotion = result[0]['dominant_emotion']
            emotion_scores = result[0]['emotion']
            
            # Convert all scores to percentages
            emotion_scores = {k: round(v, 2) for k, v in emotion_scores.items()}
            
            emotion_data = {
                'timestamp': datetime.datetime.now(),
                'dominant_emotion': current_emotion,
                'emotion_scores': emotion_scores
            }
            
            # Manage log entries
            if len(self.emotions_log) >= self.max_log_entries:
                self.emotions_log.pop(0)  # Remove oldest entry
            self.emotions_log.append(emotion_data)
                
            return emotion_data
            
        except Exception as e:
            self.logger.error(f"Error analyzing emotions: {str(e)}")
            return None
    
    def get_summary(self):
        """
        Generate summary of emotion data.
        
        :return: Tuple of detailed DataFrame and summary DataFrame
        """
        if not self.emotions_log:
            self.logger.warning("No emotion logs available")
            return None, None
            
        # Prepare data for export
        export_data = []
        for log in self.emotions_log:
            row = {
                'Timestamp': log['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                'Dominant_Emotion': log['dominant_emotion']
            }
            # Add emotion scores as percentages
            for emotion, score in log['emotion_scores'].items():
                row[f"{emotion}"] = score
            export_data.append(row)
            
        # Create DataFrame
        df = pd.DataFrame(export_data)
        
        # Calculate summary statistics
        total_readings = len(df)
        emotion_counts = df['Dominant_Emotion'].value_counts()
        
        summary_data = {
            'Emotion': emotion_counts.index,
            'Count': emotion_counts.values,
            'Percentage': (emotion_counts.values / total_readings * 100).round(2)
        }
        summary_df = pd.DataFrame(summary_data)
        
        return df, summary_df
    
    def export_to_excel(self):
        """
        Export emotion logs to Excel file with percentage formatting.
        
        :return: Tuple of BytesIO Excel file and filename
        """
        if not self.emotions_log:
            self.logger.warning("No emotion logs to export")
            return None, None
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"patient_{self.patient_id}_emotions_{timestamp}.xlsx"
        
        # Get summary data
        df, summary_df = self.get_summary()
        
        # Create Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Detailed log sheet
            df.to_excel(writer, sheet_name='Detailed_Log', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Detailed_Log']
            
            # Add percentage format for score columns
            percent_format = workbook.add_format({'num_format': '0.00"%"'})
            for col_num, column in enumerate(df.columns):
                if column in ['happy', 'sad', 'angry', 'fear', 'surprise', 'neutral', 'disgust']:
                    worksheet.set_column(col_num + 1, col_num + 1, 12, percent_format)
            
            # Summary sheet
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            summary_worksheet = writer.sheets['Summary']
            
            # Format percentage column in summary
            summary_worksheet.set_column('C:C', 12, percent_format)
        
        output.seek(0)
        return output, filename

def get_emotion_emoji(emotion):
    """
    Get emoji representation for a given emotion.
    
    :param emotion: Emotion string
    :return: Corresponding emoji or default unknown emoji
    """
    emoji_map = {
        "happy": "😊",
        "sad": "😢",
        "angry": "😠",
        "fear": "😨",
        "surprise": "😲",
        "neutral": "😐",
        "disgust": "🤢"
    }
    # Convert to lowercase and handle potential case variations
    return emoji_map.get(emotion.lower(), "❓")
