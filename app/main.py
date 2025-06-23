from app import create_app
import vertexai
from vertexai import model_garden

# Initialize Vertex AI with your project and location
PROJECT_ID = "meeting-record-whisper-program"  # Your Google Cloud Project ID
LOCATION = "asia-southeast1"  # Location for Whisper model (SINGAPORE)

# Initialize Vertex AI
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print("Vertex AI initialized successfully")
    
    # Initialize the Whisper model
    try:
        whisper_model = model_garden.OpenModel("openai/whisper-large@whisper-large-v3-turbo")
        print("Whisper model initialized successfully")
    except Exception as e:
        print(f"Error initializing Whisper model: {e}")
except Exception as e:
    print(f"Error initializing Vertex AI: {e}")

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)