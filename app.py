from flask import Flask, jsonify, render_template, request
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

@socketio.on('process_file')
def handle_file(data):
    message_data = data.get('message', '')  # Use empty string if 'message' key is missing
    file_data = data.get('file')  # Safely get 'file' key, default to None if not present

    if file_data:
        file_extension = file_data['filename'].split('.')[-1]
        file_path = f'./uploaded_file.{file_extension}'
        
        with open(file_path, 'wb') as f:
            f.write(file_data['content'])
        
        # Processing based on file type
        if file_extension == 'pdf':
            text_by_pages = extract_text_from_pdf(file_path)
            text = ' '.join(text_by_pages)  # Concatenate all pages
        elif file_extension in ['xlsx', 'csv']:
            text = process_spreadsheet(file_path)
        elif file_extension in ['jpg', 'jpeg', 'png']:
            text = process_image(file_path)
        else:
            text = ''

    else:
        text = ''  # No file provided

    # Process text with Groq
    stream = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "you are a helpful assistant."},
            {"role": "user", "content": f"{message_data}\n{text}"}
        ],
        model="llama-3.1-70b-versatile",
        temperature=0.5,
        top_p=1,
        stream=True
    )

    for chunk in stream:
        data = chunk.choices[0].delta.content
        # print("Groq AI response:", data)  # Debugging print statement
        emit('stream', {"html_content": data})

@app.route('/')
def index():
    return render_template('index.html')

# if __name__ == "__main__":
#     socketio.run(app, debug=True)
