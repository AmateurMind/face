import cv2
import numpy as np
import pandas as pd
import datetime
import io
from deepface import DeepFace

class EmotionDetector:
    def __init__(self, patient_id=None):
        self.patient_id = patient_id if patient_id else "default"
        self.emotions_log = []
        
    def analyze_frame(self, frame):
        try:
            # Use smaller size image for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            
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
            
            # Only store if we need it (limit memory usage)
            if len(self.emotions_log) < 100:  # Limit stored history
                self.emotions_log.append(emotion_data)
            else:
                # Replace oldest entry
                self.emotions_log.pop(0)
                self.emotions_log.append(emotion_data)
                
            return emotion_data
            
        except Exception as e:
            print(f"Error analyzing emotions: {str(e)}")
            return None
    
    def get_summary(self):
        if not self.emotions_log:
            return None
            
        # Prepare data for export
        export_data = []
        for log in self.emotions_log:
            row = {
                'Timestamp': log['timestamp'].strftime("%H:%M:%S"),
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
        if total_readings == 0:
            return None
            
        emotion_counts = df['Dominant_Emotion'].value_counts()
        
        summary_data = {
            'Emotion': emotion_counts.index,
            'Count': emotion_counts.values,
            'Percentage': (emotion_counts.values / total_readings * 100).round(2)
        }
        summary_df = pd.DataFrame(summary_data)
        
        return df, summary_df
    
    def export_to_excel(self):
        """Export emotion logs to Excel file with percentage formatting."""
        if not self.emotions_log:
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

# Function to get emoji for emotion
def get_emotion_emoji(emotion):
    emoji_map = {
        "happy": "😊",
        "sad": "😢",
        "angry": "😠",
        "fear": "😨",
        "surprise": "😲",
        "neutral": "😐",
        "disgust": "🤢"
    }
    return emoji_map.get(emotion.lower(), "❓")
