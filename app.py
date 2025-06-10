from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import os
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from dotenv import load_dotenv
import subprocess
import threading
import time
import re

load_dotenv()

app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL')

# Global status for background tasks
task_status = {"running": False, "task": "", "progress": 0, "total": 0}

def clean_column_name(col):
    """Convert column name to PostgreSQL-friendly format"""
    # Convert to lowercase
    col = col.lower()
    # Replace special characters with underscores
    col = re.sub(r'[^\w\s]', '_', col)
    # Replace spaces with underscores
    col = re.sub(r'\s+', '_', col)
    # Remove leading/trailing underscores
    col = col.strip('_')
    # Replace multiple underscores with single
    col = re.sub(r'_+', '_', col)
    return col

@app.route('/')
def index():
    # Get counts from database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM apollo_table")
    total_companies = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM apollo_table WHERE website IS NULL OR website = ''")
    missing_websites = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM apollo_table WHERE status IS NOT NULL")
    processed_companies = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Odigon Control Panel</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>ODIGON</h1>
                <div class="subtitle">Industrial Data Enrichment Platform v2.1</div>
            </div>
            
            <div class="content">
                <div class="status-panel">
                    <div class="status-grid">
                        <div class="status-item">
                            <div class="status-value">{{ total_companies }}</div>
                            <div class="status-label">Total Records</div>
                        </div>
                        <div class="status-item">
                            <div class="status-value">{{ missing_websites }}</div>
                            <div class="status-label">Missing Websites</div>
                        </div>
                        <div class="status-item">
                            <div class="status-value">{{ processed_companies }}</div>
                            <div class="status-label">Processed</div>
                        </div>
                    </div>
                </div>
                
                <div class="task-status" id="taskStatus">
                    <div class="task-title">Operation in Progress</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text" id="progressText"></div>
                </div>
                
                <div class="section">
                    <div class="section-header">
                        <span class="icon">⚠️</span> Database Control
                    </div>
                    <div class="section-content">
                        <div class="warning">
                            Warning: This will permanently delete all {{ total_companies }} records
                        </div>
                        <button class="danger" onclick="truncateDatabase()">TRUNCATE DATABASE</button>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-header">
                        <span class="icon">📁</span> Data Import
                    </div>
                    <div class="section-content">
                        <div class="help-text">Upload a CSV file to import company data</div>
                        <form action="/upload" method="post" enctype="multipart/form-data">
                            <input type="file" name="file" accept=".csv" required>
                            <button type="submit">UPLOAD CSV</button>
                        </form>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-header">
                        <span class="icon">🔍</span> Website Discovery
                    </div>
                    <div class="section-content">
                        <div class="help-text">Search for websites for {{ missing_websites }} companies</div>
                        <button onclick="findWebsites()" {% if missing_websites == 0 %}disabled{% endif %}>
                            FIND WEBSITES
                        </button>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-header">
                        <span class="icon">🏭</span> Classification
                    </div>
                    <div class="section-content">
                        <div class="help-text">Process {{ total_companies - processed_companies }} unclassified companies</div>
                        <button onclick="classifyCompanies()">
                            CLASSIFY COMPANIES
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let statusCheckInterval;
            
            function truncateDatabase() {
                if (confirm('Are you sure you want to delete all {{ total_companies }} records? This cannot be undone.')) {
                    if (confirm('FINAL WARNING: This will permanently delete all data. Continue?')) {
                        fetch('/truncate', { method: 'POST' })
                            .then(response => response.json())
                            .then(data => {
                                alert(data.message);
                                location.reload();
                            });
                    }
                }
            }
            
            function findWebsites() {
                document.getElementById('taskStatus').style.display = 'block';
                fetch('/find-websites', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            checkTaskStatus();
                        }
                    });
            }
            
            function classifyCompanies() {
                document.getElementById('taskStatus').style.display = 'block';
                fetch('/classify-companies', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            checkTaskStatus();
                        }
                    });
            }
            
            function checkTaskStatus() {
                statusCheckInterval = setInterval(() => {
                    fetch('/task-status')
                        .then(response => response.json())
                        .then(data => {
                            if (data.running) {
                                document.getElementById('taskName').textContent = 
                                    'Task: ' + data.task;
                                document.getElementById('progressText').textContent = 
                                    data.progress + ' / ' + data.total + ' completed';
                                const percent = (data.progress / data.total * 100) || 0;
                                document.getElementById('progressFill').style.width = percent + '%';
                            } else {
                                clearInterval(statusCheckInterval);
                                document.getElementById('taskStatus').style.display = 'none';
                                location.reload();
                            }
                        });
                }, 2000);
            }
        </script>
    </body>
    </html>
    ''', total_companies=total_companies, missing_websites=missing_websites, processed_companies=processed_companies)

@app.route('/truncate', methods=['POST'])
def truncate():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE apollo_table")
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Database truncated successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        df = pd.read_csv(file)
        
        # Store original row count
        original_rows = len(df)
        
        # Clean column names before inserting
        df.columns = [clean_column_name(col) for col in df.columns]
        
        # Log the column mapping for debugging
        print("Column names after cleaning:")
        for col in df.columns:
            print(f"  - {col}")
        
        engine = create_engine(DATABASE_URL)
        df.to_sql('apollo_table', engine, if_exists='append', index=False, method='multi', chunksize=500)
        
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return f"Error: {str(e)} <a href='/'>Go back</a>"

# Background task functions
def run_website_finder():
    global task_status
    task_status = {"running": True, "task": "Website Discovery", "progress": 0, "total": 0}
    
    # Import here to avoid circular imports
    from populate_websites import find_websites_task
    find_websites_task(task_status)
    
    task_status["running"] = False

def run_classifier():
    global task_status
    task_status = {"running": True, "task": "Company Classification", "progress": 0, "total": 0}
    
    # Import here to avoid circular imports  
    from process_companies import classify_companies_task
    classify_companies_task(task_status)
    
    task_status["running"] = False

@app.route('/find-websites', methods=['POST'])
def find_websites():
    if task_status.get("running"):
        return jsonify({"success": False, "message": "Another task is running"})
    
    thread = threading.Thread(target=run_website_finder)
    thread.start()
    return jsonify({"success": True})

@app.route('/classify-companies', methods=['POST'])
def classify_companies():
    if task_status.get("running"):
        return jsonify({"success": False, "message": "Another task is running"})
    
    thread = threading.Thread(target=run_classifier)
    thread.start()
    return jsonify({"success": True})

@app.route('/task-status')
def get_task_status():
    return jsonify(task_status)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)