from flask import Flask, jsonify, render_template, request,Response
from flask_socketio import SocketIO, emit
import fitz  # PyMuPDF
import pandas as pd
from PIL import Image
import pytesseract
from groq import Groq
import markdown

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hello2'

# Initialize Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Groq client
client = Groq(api_key="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")

def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text_by_pages = []
    for page_number in range(len(document)):
        page = document.load_page(page_number)
        text = page.get_text()
        text_by_pages.append(text)
    return text_by_pages

def process_spreadsheet(file_path):
    df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
    return df.to_json(orient='records')

def process_image(file_path):
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)
    return text

def process_text_with_groq(text):
    stream = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Make a table according to this data:\n{text}"}
        ],
        model="llama3-8b-8192",
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        stop=None,
        stream=True
    )
    return stream

@app.route('/your-flask-endpoint', methods=['POST'])
def handle_file():
    data = request.get_json()
    message_data = data.get('name', '')  # Default to empty string if 'name' is not present
    # print(message_data)
    # Process text with Groq
  
    stream = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message_data}
            ],
            model="llama-3.1-70b-versatile",
            temperature=0.5,
            max_tokens=1024,
            top_p=1,
            stop=None,
            stream=True
        )

        # Function to generate response data as a stream
    for chunk in stream:
        content = chunk.choices[0].delta.content
        # print("Groq AI response:", content)  # Debugging print statement
        socketio.emit('file-processed', {'message': content})

    


        # Return response as a streaming response
        
          
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)
