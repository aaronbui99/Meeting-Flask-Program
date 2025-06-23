import os
import tempfile
from flask import Flask, render_template, request, jsonify


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
        
    # Define routes for all templates
    @app.route('/')
    def index():
        return render_template('index.html')
        
    @app.route('/about')
    def about():
        return render_template('about.html')
        
    @app.route('/contact')
    def contact():
        return render_template('contact.html')
        
    @app.route('/services')
    def services():
        return render_template('services.html')
        
    @app.route('/login')
    def login():
        return render_template('login.html')
        
    @app.route('/register')
    def register():
        return render_template('register.html')
        
    # Route to test Whisper model
    @app.route('/test-whisper')
    def test_whisper_page():
        return render_template('test_whisper.html')
    
    # API endpoint for audio transcription
    @app.route('/transcribe', methods=['POST'])
    def transcribe_audio():
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400

        import vertexai
        from vertexai.preview import model_garden

        vertexai.init(project="meeting-record-whisper-program", location="asia-southeast1")  # e.g., "us-central1"

        try:

            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                audio_file.save(temp_audio.name)
                temp_audio_path = temp_audio.name
            # Load Whisper model from Model Garden
            whisper_model = model_garden.OpenModel("openai/whisper-large@whisper-large-v3")

            # Deploy the model (or skip if already deployed)
            endpoint = whisper_model.deploy()  # You can cache this in real app

            # Read audio file
            with open(temp_audio_path, "rb") as f:
                audio_content = f.read()

            # Make prediction
            response = endpoint.predict(
                audio=audio_content,
                mime_type="audio/wav"  # or "audio/mpeg", "audio/flac", etc.
            )

            # Clean up
            os.unlink(temp_audio_path)

            return jsonify({
                "success": True,
                "transcription": response.text
            })

        except Exception as e:
            os.unlink(temp_audio_path)
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return app