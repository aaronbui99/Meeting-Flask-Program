import os
import tempfile
import datetime
from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


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
    
    # Function to generate PDF from transcription
    def generate_pdf(transcription, filename=None):
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcription_{timestamp}.pdf"
        
        pdf_path = os.path.join(tempfile.gettempdir(), filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            title="Meeting Transcription"
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        normal_style = styles['Normal']
        
        # Create content
        content = []
        
        # Add title
        content.append(Paragraph("Meeting Transcription", title_style))
        content.append(Spacer(1, 12))
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content.append(Paragraph(f"Generated on: {timestamp}", normal_style))
        content.append(Spacer(1, 12))
        
        # Add transcription text
        content.append(Paragraph("Transcription:", styles['Heading2']))
        content.append(Spacer(1, 6))
        
        # Split transcription into paragraphs and add them
        paragraphs = transcription.split('\n\n')
        for para in paragraphs:
            if para.strip():
                content.append(Paragraph(para, normal_style))
                content.append(Spacer(1, 6))
        
        # Build the PDF
        doc.build(content)
        
        return pdf_path
    
    # API endpoint for audio transcription
    @app.route('/transcribe', methods=['POST'])
    def transcribe_audio():
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
            
        # Get format preference (text or PDF)
        format_type = request.form.get('format', 'text')  # Default to text if not specified
        
        temp_audio_path = None
        
        try:
            import vertexai
            from vertexai.preview import model_garden

            # Initialize Vertex AI
            vertexai.init(project="meeting-record-whisper-program", location="asia-southeast1")

            # Save the uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                audio_file.save(temp_audio.name)
                temp_audio_path = temp_audio.name
                
            # Load Whisper model from Model Garden
            whisper_model = model_garden.OpenModel("openai/whisper-large@whisper-large-v3")

            # Deploy the model
            endpoint = whisper_model.deploy()

            # Read audio file
            with open(temp_audio_path, "rb") as f:
                audio_content = f.read()

            # Make prediction
            response = endpoint.predict(
                audio=audio_content,
                mime_type="audio/wav"  # or "audio/mpeg", "audio/flac", etc.
            )
            
            transcription_text = response.text
            
            # Clean up the temporary audio file
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                temp_audio_path = None
            
            # If PDF format is requested, generate PDF
            if format_type.lower() == 'pdf':
                pdf_path = generate_pdf(transcription_text)
                
                # Return the PDF file
                return send_file(
                    pdf_path,
                    as_attachment=True,
                    download_name=os.path.basename(pdf_path),
                    mimetype='application/pdf'
                )
            
            # Otherwise return JSON with transcription text
            return jsonify({
                "success": True,
                "transcription": transcription_text
            })

        except Exception as e:
            # Clean up the temporary file in case of error
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
        
    return app