from flask import Flask, render_template_string, request, jsonify
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL')

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Odigon - Company Enrichment</title>
    </head>
    <body>
        <h1>Odigon Company Enrichment Tool</h1>
        <h2>Upload CSV File</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".csv" required>
            <button type="submit">Upload and Import</button>
        </form>
    </body>
    </html>
    ''')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        df = pd.read_csv(file)
        
        # Import to PostgreSQL
        engine = create_engine(DATABASE_URL)
        df.to_sql('apollo_table', engine, if_exists='append', index=False, method='multi', chunksize=500)
        
        return f"Successfully imported {len(df)} rows!"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)