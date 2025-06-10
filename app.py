from flask import Flask, render_template_string, request, jsonify
import os
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from dotenv import load_dotenv
import time
import threading
from perplexity_find_website import find_website

load_dotenv()

app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL')

# Global variable to track processing status
processing_status = {"running": False, "progress": 0, "total": 0}

@app.route('/')
def index():
    # Get counts from database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM apollo_table")
    total_companies = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM apollo_table WHERE Website IS NULL OR Website = ''")
    missing_websites = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Odigon - Company Enrichment</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .stats { background: #f0f0f0; padding: 20px; margin: 20px 0; }
            button { padding: 10px 20px; margin: 10px 0; cursor: pointer; }
            .progress { margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>Odigon Company Enrichment Tool</h1>
        
        <div class="stats">
            <h3>Database Stats</h3>
            <p>Total Companies: {{ total_companies }}</p>
            <p>Missing Websites: {{ missing_websites }}</p>
        </div>
        
        <h2>Upload CSV File</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".csv" required>
            <button type="submit">Upload and Import</button>
        </form>
        
        <h2>Find Missing Websites</h2>
        <button onclick="startWebsiteSearch()" id="searchBtn">Start Website Search</button>
        <div id="progress" class="progress"></div>
        
        <script>
            function startWebsiteSearch() {
                document.getElementById('searchBtn').disabled = true;
                document.getElementById('progress').innerHTML = 'Starting...';
                
                fetch('/find-websites', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            document.getElementById('progress').innerHTML = 'Error: ' + data.error;
                            document.getElementById('searchBtn').disabled = false;
                        } else {
                            checkProgress();
                        }
                    });
            }
            
            function checkProgress() {
                fetch('/progress')
                    .then(response => response.json())
                    .then(data => {
                        if (data.running) {
                            document.getElementById('progress').innerHTML = 
                                `Processing: ${data.progress} / ${data.total} companies`;
                            setTimeout(checkProgress, 2000);  // Check every 2 seconds
                        } else {
                            document.getElementById('progress').innerHTML = 'Complete!';
                            document.getElementById('searchBtn').disabled = false;
                            location.reload();  // Reload to update stats
                        }
                    });
            }
        </script>
    </body>
    </html>
    ''', total_companies=total_companies, missing_websites=missing_websites)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        df = pd.read_csv(file)
        
        engine = create_engine(DATABASE_URL)
        df.to_sql('apollo_table', engine, if_exists='append', index=False, method='multi', chunksize=500)
        
        return f"Successfully imported {len(df)} rows! <a href='/'>Go back</a>"
    except Exception as e:
        return f"Error: {str(e)} <a href='/'>Go back</a>"

def process_websites():
    """Background function to find websites"""
    global processing_status
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Get companies without websites
    cursor.execute('''
        SELECT Company, "Company City", "Company State"
        FROM apollo_table
        WHERE (Website IS NULL OR Website = '') 
        AND Company IS NOT NULL
    ''')
    rows = cursor.fetchall()
    
    processing_status["total"] = len(rows)
    processing_status["running"] = True
    
    for i, (company, city, state) in enumerate(rows):
        website = find_website(company, city, state)
        
        if website:
            cursor.execute('''
                UPDATE apollo_table 
                SET Website = %s
                WHERE Company = %s AND "Company City" = %s AND "Company State" = %s
            ''', (website, company, city, state))
            conn.commit()
        
        processing_status["progress"] = i + 1
        time.sleep(1)  # Rate limiting
    
    conn.close()
    processing_status["running"] = False

@app.route('/find-websites', methods=['POST'])
def find_websites_route():
    global processing_status
    
    if processing_status["running"]:
        return jsonify({"error": "Already processing"})
    
    # Start processing in background thread
    thread = threading.Thread(target=process_websites)
    thread.start()
    
    return jsonify({"success": True})

@app.route('/progress')
def progress():
    return jsonify(processing_status)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)