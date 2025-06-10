from flask import Flask, render_template_string, request, jsonify, redirect, url_for, send_file
import os
import threading
import io
import pandas as pd
from dotenv import load_dotenv
from database_operations import (
    get_database_stats, 
    truncate_database, 
    import_csv_file,
    find_websites_task,
    classify_companies_task,
    get_companies_for_export
)

load_dotenv()

app = Flask(__name__)

# Global status for background tasks
task_status = {
    "running": False, 
    "task": "", 
    "progress": 0, 
    "total": 0,
    "current_company": "",
    "yes_count": 0,
    "no_count": 0
}

# Store the current prompt
current_prompt = """Search the internet for the company {company_name}, website {website} and determine if the company is a home furnishings manufacturer or not. 

A home furnishings manufacturer must meet ALL of these criteria:
- They must MANUFACTURE (not just retail) furniture
- The furniture must be for HOME/RESIDENTIAL use (not commercial, office, or institutional)
- They must make furniture like sofas, chairs, tables, beds, dressers, or other residential furniture
- They are NOT just cabinetry, casework, mattresses only, or building materials

IMPORTANT: Respond with ONLY the single word YES or NO. Do not include any explanation."""

@app.route('/')
def index():
    stats = get_database_stats()
    
    # Calculate YES count from database
    import psycopg2
    from database_operations import DATABASE_URL
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM apollo_table WHERE status = 'YES'")
    yes_count = cursor.fetchone()[0]
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enrich Company Records</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
        <style>
            .yes-count-box {
                background: #28a745;
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
            }
            .yes-count-box .count {
                font-size: 48px;
                font-weight: bold;
            }
            .yes-count-box .label {
                font-size: 18px;
                margin-top: 10px;
            }
            .current-company-box {
                background: #f8f9fa;
                border: 2px solid #dee2e6;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                min-height: 60px;
            }
            .current-company-box .label {
                font-weight: bold;
                color: #495057;
                margin-bottom: 5px;
            }
            .current-company-box .company-name {
                font-size: 18px;
                color: #007bff;
            }
            .prompt-section {
                margin: 20px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }
            .prompt-section textarea {
                width: 100%;
                min-height: 150px;
                padding: 10px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-family: monospace;
                font-size: 14px;
            }
            .prompt-section button {
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>ENRICH COMPANY RECORDS</h1>
            </div>
            
            <div class="content">
                <div class="status-panel">
                    <div class="status-grid">
                        <div class="status-item">
                            <div class="status-value">{{ stats.total_companies }}</div>
                            <div class="status-label">Total Records</div>
                        </div>
                        <div class="status-item">
                            <div class="status-value">{{ stats.missing_websites }}</div>
                            <div class="status-label">Missing Websites</div>
                        </div>
                        <div class="status-item">
                            <div class="status-value">{{ stats.processed_companies }}</div>
                            <div class="status-label">Processed</div>
                        </div>
                    </div>
                </div>
                
                <div class="yes-count-box">
                    <div class="count" id="yesCount">{{ yes_count }}</div>
                    <div class="label">Companies Marked YES</div>
                </div>
                
                <div class="current-company-box" id="currentCompanyBox" style="display: none;">
                    <div class="label">Currently Processing:</div>
                    <div class="company-name" id="currentCompany">-</div>
                </div>
                
                <div class="task-status" id="taskStatus" style="display: none;">
                    <div class="task-title">Operation in Progress</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text" id="progressText"></div>
                    <div class="progress-stats" id="progressStats" style="margin-top: 10px;"></div>
                </div>
                
                <div class="section">
                    <div class="section-header">
                        <span class="icon">💾</span> Export Data
                    </div>
                    <div class="section-content">
                        <div class="help-text">Download the complete company database as CSV</div>
                        <button onclick="downloadData()">DOWNLOAD ALL DATA</button>
                        <button onclick="downloadData('YES')" style="background-color: #28a745;">DOWNLOAD YES ONLY</button>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-header">
                        <span class="icon">⚠️</span> Database Control
                    </div>
                    <div class="section-content">
                        <div class="warning">
                            Warning: This will permanently delete all {{ stats.total_companies }} records
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
                        <div class="help-text">Search for websites for {{ stats.missing_websites }} companies</div>
                        <button onclick="findWebsites()" {% if stats.missing_websites == 0 %}disabled{% endif %}>
                            FIND WEBSITES
                        </button>
                    </div>
                </div>
                
                <div class="section prompt-section">
                    <div class="section-header">
                        <span class="icon">📝</span> Classification Prompt
                    </div>
                    <div class="section-content">
                        <div class="help-text">Edit the prompt used for company classification</div>
                        <textarea id="classificationPrompt">{{ current_prompt }}</textarea>
                        <button onclick="updatePrompt()">UPDATE PROMPT</button>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-header">
                        <span class="icon">🏭</span> Classification
                    </div>
                    <div class="section-content">
                        <div class="help-text">Process {{ stats.total_companies - stats.processed_companies }} unclassified companies</div>
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
                if (confirm('Are you sure you want to delete all {{ stats.total_companies }} records? This cannot be undone.')) {
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
            
            function downloadData(statusFilter) {
                let url = '/download';
                if (statusFilter) {
                    url += '?status=' + statusFilter;
                }
                window.location.href = url;
            }
            
            function updatePrompt() {
                const prompt = document.getElementById('classificationPrompt').value;
                fetch('/update-prompt', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt: prompt })
                })
                .then(response => response.json())
                .then(data => {
                    alert('Prompt updated successfully!');
                });
            }
            
            function findWebsites() {
                document.getElementById('taskStatus').style.display = 'block';
                document.getElementById('currentCompanyBox').style.display = 'block';
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
                document.getElementById('currentCompanyBox').style.display = 'block';
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
                                document.getElementById('progressText').textContent = 
                                    data.progress + ' / ' + data.total + ' completed';
                                const percent = (data.progress / data.total * 100) || 0;
                                document.getElementById('progressFill').style.width = percent + '%';
                                
                                // Update current company
                                if (data.current_company) {
                                    document.getElementById('currentCompany').textContent = data.current_company;
                                }
                                
                                // Update YES/NO stats for classification
                                if (data.task === 'Company Classification') {
                                    document.getElementById('progressStats').textContent = 
                                        `YES: ${data.yes_count} | NO: ${data.no_count}`;
                                    document.getElementById('yesCount').textContent = 
                                        {{ yes_count }} + data.yes_count;
                                }
                            } else {
                                clearInterval(statusCheckInterval);
                                document.getElementById('taskStatus').style.display = 'none';
                                document.getElementById('currentCompanyBox').style.display = 'none';
                                location.reload();
                            }
                        });
                }, 1000);  // Update every second
            }
        </script>
    </body>
    </html>
    ''', stats=stats, yes_count=yes_count, current_prompt=current_prompt)

@app.route('/truncate', methods=['POST'])
def truncate():
    success, message = truncate_database()
    return jsonify({"success": success, "message": message})

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        success, message, details = import_csv_file(file_object=file)
        
        if success:
            return redirect(url_for('index'))
        else:
            return f"Error: {message} <a href='/'>Go back</a>"
    except Exception as e:
        return f"Error: {str(e)} <a href='/'>Go back</a>"

@app.route('/download')
def download():
    status_filter = request.args.get('status')
    df = get_companies_for_export(status_filter)
    
    # Create a BytesIO object
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    filename = f"companies_{'yes_only' if status_filter == 'YES' else 'all'}.csv"
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/update-prompt', methods=['POST'])
def update_prompt():
    global current_prompt
    data = request.get_json()
    current_prompt = data.get('prompt', current_prompt)
    return jsonify({"success": True})

# Background task runners
def run_website_finder():
    global task_status
    task_status = {
        "running": True, 
        "task": "Website Discovery", 
        "progress": 0, 
        "total": 0,
        "current_company": "",
        "yes_count": 0,
        "no_count": 0
    }
    find_websites_task(task_status)
    task_status["running"] = False

def run_classifier():
    global task_status, current_prompt
    task_status = {
        "running": True, 
        "task": "Company Classification", 
        "progress": 0, 
        "total": 0,
        "current_company": "",
        "yes_count": 0,
        "no_count": 0
    }
    # Pass the current prompt to the classification task
    classify_companies_task(task_status, current_prompt)
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