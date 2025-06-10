from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import os
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from dotenv import load_dotenv
import subprocess
import threading
import time

load_dotenv()

app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL')

# Global status for background tasks
task_status = {"running": False, "task": "", "progress": 0, "total": 0}

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
        <title>ODIGON CONTROL SYSTEM</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
            
            body {
                background: #0a0a0a;
                color: #00ff00;
                font-family: 'Share Tech Mono', monospace;
                margin: 0;
                padding: 20px;
                font-size: 14px;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
                border: 2px solid #00ff00;
                padding: 20px;
                box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
            }
            
            h1 {
                color: #00ff00;
                text-align: center;
                font-size: 28px;
                margin: 0 0 10px 0;
                text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
                letter-spacing: 3px;
            }
            
            .subtitle {
                text-align: center;
                color: #888;
                margin-bottom: 30px;
                font-size: 12px;
            }
            
            .status-panel {
                background: #1a1a1a;
                border: 1px solid #00ff00;
                padding: 15px;
                margin-bottom: 20px;
            }
            
            .status-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
            }
            
            .status-item {
                text-align: center;
                padding: 10px;
                background: #0f0f0f;
                border: 1px solid #333;
            }
            
            .status-value {
                font-size: 32px;
                color: #00ff00;
                font-weight: bold;
                text-shadow: 0 0 5px rgba(0, 255, 0, 0.5);
            }
            
            .status-label {
                font-size: 11px;
                color: #888;
                text-transform: uppercase;
                margin-top: 5px;
            }
            
            .control-panel {
                background: #1a1a1a;
                border: 1px solid #00ff00;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .control-section {
                margin-bottom: 25px;
                padding-bottom: 25px;
                border-bottom: 1px solid #333;
            }
            
            .control-section:last-child {
                border-bottom: none;
                margin-bottom: 0;
                padding-bottom: 0;
            }
            
            h2 {
                color: #ffaa00;
                font-size: 16px;
                margin: 0 0 15px 0;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            button {
                background: #1a1a1a;
                color: #00ff00;
                border: 2px solid #00ff00;
                padding: 10px 20px;
                font-family: 'Share Tech Mono', monospace;
                font-size: 14px;
                cursor: pointer;
                text-transform: uppercase;
                transition: all 0.3s;
                margin-right: 10px;
            }
            
            button:hover:not(:disabled) {
                background: #00ff00;
                color: #000;
                box-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
            }
            
            button:disabled {
                opacity: 0.3;
                cursor: not-allowed;
            }
            
            button.danger {
                border-color: #ff0000;
                color: #ff0000;
            }
            
            button.danger:hover:not(:disabled) {
                background: #ff0000;
                color: #000;
                box-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
            }
            
            input[type="file"] {
                background: #0a0a0a;
                color: #00ff00;
                border: 1px solid #00ff00;
                padding: 5px;
                font-family: 'Share Tech Mono', monospace;
            }
            
            .warning {
                background: #330000;
                border: 1px solid #ff0000;
                padding: 10px;
                margin: 10px 0;
                color: #ff6666;
            }
            
            .task-status {
                background: #001100;
                border: 1px solid #00ff00;
                padding: 15px;
                margin: 20px 0;
                display: none;
            }
            
            .blink {
                animation: blink 1s infinite;
            }
            
            @keyframes blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0.3; }
            }
            
            .progress-bar {
                background: #0a0a0a;
                border: 1px solid #00ff00;
                height: 20px;
                margin: 10px 0;
                position: relative;
            }
            
            .progress-fill {
                background: #00ff00;
                height: 100%;
                width: 0%;
                transition: width 0.3s;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ODIGON CONTROL SYSTEM</h1>
            <div class="subtitle">INDUSTRIAL DATA ENRICHMENT PLATFORM v2.1</div>
            
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
                <h2 class="blink">OPERATION IN PROGRESS</h2>
                <div id="taskName"></div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div id="progressText"></div>
            </div>
            
            <div class="control-panel">
                <div class="control-section">
                    <h2>⚠️ Database Control</h2>
                    <div class="warning">
                        WARNING: Truncate will permanently delete all {{ total_companies }} records
                    </div>
                    <button class="danger" onclick="truncateDatabase()">TRUNCATE DATABASE</button>
                </div>
                
                <div class="control-section">
                    <h2>📁 Data Import</h2>
                    <form action="/upload" method="post" enctype="multipart/form-data" style="display: inline;">
                        <input type="file" name="file" accept=".csv" required id="fileInput">
                        <button type="submit">UPLOAD CSV</button>
                    </form>
                </div>
                
                <div class="control-section">
                    <h2>🔍 Website Discovery</h2>
                    <p>Scan for {{ missing_websites }} missing websites</p>
                    <button onclick="findWebsites()" {% if missing_websites == 0 %}disabled{% endif %}>
                        INITIATE SCAN
                    </button>
                </div>
                
                <div class="control-section">
                    <h2>🏭 Classification Process</h2>
                    <p>Classify {{ total_companies - processed_companies }} unprocessed companies</p>
                    <button onclick="classifyCompanies()">
                        START CLASSIFICATION
                    </button>
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
        
        engine = create_engine(DATABASE_URL)
        df.to_sql('apollo_table', engine, if_exists='append', index=False, method='multi', chunksize=500)
        
        return redirect(url_for('index'))
    except Exception as e:
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