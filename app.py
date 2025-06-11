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
        <title>Company Data Enrichment Tool</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: #333;
                background-color: #f5f5f5;
                line-height: 1.4;
            }
            
            .header {
                background-color: #4a4a4a;
                color: white;
                padding: 15px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header h1 {
                font-size: 20px;
                font-weight: normal;
            }
            
            .logo {
                width: 40px;
                height: 40px;
                background-color: #cc0000;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                color: white;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .metrics-table {
                background-color: white;
                border: 1px solid #ddd;
                margin-bottom: 20px;
                width: 100%;
            }
            
            .metrics-table th {
                background-color: #4a73a8;
                color: white;
                padding: 10px 15px;
                text-align: left;
                font-weight: normal;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 0.5px;
            }
            
            .metrics-row {
                display: flex;
                border-bottom: 1px solid #e0e0e0;
            }
            
            .metric-label {
                flex: 1;
                padding: 12px 15px;
                background-color: #f8f8f8;
                font-weight: bold;
                border-right: 1px solid #e0e0e0;
            }
            
            .metric-value {
                flex: 1;
                padding: 12px 15px;
                text-align: right;
                font-family: 'Courier New', monospace;
            }
            
            .metric-status {
                flex: 0.5;
                padding: 12px 15px;
                text-align: center;
                font-weight: bold;
            }
            
            .status-good { color: #28a745; }
            .status-warning { color: #ffc107; }
            .status-bad { color: #dc3545; }
            
            .section {
                background-color: white;
                border: 1px solid #ddd;
                margin-bottom: 20px;
            }
            
            .section-header {
                background-color: #b8c6db;
                color: #333;
                padding: 10px 15px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 0.5px;
            }
            
            .section-content {
                padding: 20px;
            }
            
            .button-group {
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }
            
            button {
                background-color: #4a73a8;
                color: white;
                border: none;
                padding: 10px 20px;
                cursor: pointer;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                transition: background-color 0.2s;
            }
            
            button:hover:not(:disabled) {
                background-color: #365a8a;
            }
            
            button:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
            
            button.danger {
                background-color: #dc3545;
            }
            
            button.danger:hover {
                background-color: #c82333;
            }
            
            button.success {
                background-color: #28a745;
            }
            
            button.success:hover {
                background-color: #218838;
            }
            
            input[type="file"] {
                padding: 5px;
                border: 1px solid #ddd;
                background-color: white;
            }
            
            textarea {
                width: 100%;
                min-height: 120px;
                padding: 10px;
                border: 1px solid #ddd;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                resize: vertical;
            }
            
            .progress-section {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                margin-bottom: 20px;
                display: none;
            }
            
            .progress-bar {
                background-color: #e0e0e0;
                height: 20px;
                margin: 10px 0;
                position: relative;
            }
            
            .progress-fill {
                background-color: #4a73a8;
                height: 100%;
                transition: width 0.3s;
            }
            
            .current-task {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: #666;
                margin-top: 10px;
            }
            
            .help-text {
                color: #666;
                font-size: 12px;
                margin-bottom: 10px;
            }
            
            .key-metric {
                font-size: 24px;
                font-weight: bold;
                color: #4a73a8;
            }
            
            .small-text {
                font-size: 11px;
                color: #999;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Company Data Enrichment Tool: Database Analytics</h1>
            <div class="logo">O</div>
        </div>
        
        <div class="container">
            <!-- Key Metrics Table -->
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th colspan="3">DATABASE METRICS</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 0;">
                            <div class="metrics-row">
                                <div class="metric-label">Total Records</div>
                                <div class="metric-value">{{ "{:,}".format(stats.total_companies) }}</div>
                                <div class="metric-status">
                                    {% if stats.total_companies > 0 %}
                                        <span class="status-good">✓</span>
                                    {% else %}
                                        <span class="status-bad">✗</span>
                                    {% endif %}
                                </div>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0;">
                            <div class="metrics-row">
                                <div class="metric-label">Missing Websites</div>
                                <div class="metric-value">{{ "{:,}".format(stats.missing_websites) }}</div>
                                <div class="metric-status">
                                    {% if stats.missing_websites == 0 %}
                                        <span class="status-good">✓</span>
                                    {% elif stats.missing_websites < stats.total_companies * 0.1 %}
                                        <span class="status-warning">!</span>
                                    {% else %}
                                        <span class="status-bad">✗</span>
                                    {% endif %}
                                </div>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0;">
                            <div class="metrics-row">
                                <div class="metric-label">Processed Records</div>
                                <div class="metric-value">{{ "{:,}".format(stats.processed_companies) }}</div>
                                <div class="metric-status">
                                    {% if stats.processed_companies == stats.total_companies %}
                                        <span class="status-good">✓</span>
                                    {% else %}
                                        <span class="status-warning">!</span>
                                    {% endif %}
                                </div>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0;">
                            <div class="metrics-row">
                                <div class="metric-label">Companies Marked YES</div>
                                <div class="metric-value key-metric" id="yesCount">{{ "{:,}".format(yes_count) }}</div>
                                <div class="metric-status">
                                    <span class="status-good">{{ "{:.1%}".format(yes_count / stats.total_companies if stats.total_companies > 0 else 0) }}</span>
                                </div>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
            
            <!-- Progress Section -->
            <div class="progress-section" id="progressSection">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>TASK IN PROGRESS: <span id="taskName"></span></strong>
                    <span id="progressText">0 / 0</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="current-task">
                    <span id="currentCompany">Initializing...</span>
                    <span id="progressStats" style="float: right;"></span>
                </div>
            </div>
            
            <!-- Data Management Section -->
            <div class="section">
                <div class="section-header">DATA MANAGEMENT</div>
                <div class="section-content">
                    <div class="button-group">
                        <form action="/upload" method="post" enctype="multipart/form-data" style="display: flex; gap: 10px; flex: 1;">
                            <input type="file" name="file" accept=".csv" required style="flex: 1;">
                            <button type="submit">UPLOAD CSV</button>
                        </form>
                        <button onclick="downloadData()" class="success">EXPORT ALL</button>
                        <button onclick="downloadData('YES')" class="success">EXPORT YES ONLY</button>
                        <button onclick="truncateDatabase()" class="danger">TRUNCATE</button>
                    </div>
                    <div class="small-text">
                        Upload new company data | Export processed results | Clear database
                    </div>
                </div>
            </div>
            
            <!-- Processing Section -->
            <div class="section">
                <div class="section-header">DATA ENRICHMENT OPERATIONS</div>
                <div class="section-content">
                    <div class="button-group">
                        <button onclick="findWebsites()" {% if stats.missing_websites == 0 %}disabled{% endif %}>
                            FIND WEBSITES ({{ "{:,}".format(stats.missing_websites) }} REMAINING)
                        </button>
                        <button onclick="classifyCompanies()" {% if stats.total_companies - stats.processed_companies == 0 %}disabled{% endif %}>
                            CLASSIFY COMPANIES ({{ "{:,}".format(stats.total_companies - stats.processed_companies) }} REMAINING)
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Classification Prompt Section -->
            <div class="section">
                <div class="section-header">CLASSIFICATION PARAMETERS</div>
                <div class="section-content">
                    <div class="help-text">Modify the classification prompt to target different industries or criteria:</div>
                    <textarea id="classificationPrompt">{{ current_prompt }}</textarea>
                    <div style="margin-top: 10px;">
                        <button onclick="updatePrompt()">UPDATE CLASSIFICATION PROMPT</button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let statusCheckInterval;
            
            function truncateDatabase() {
                if (confirm('Delete all {{ "{:,}".format(stats.total_companies) }} records from the database?')) {
                    if (confirm('This action cannot be undone. Proceed?')) {
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
                    alert('Classification prompt updated successfully');
                });
            }
            
            function findWebsites() {
                document.getElementById('progressSection').style.display = 'block';
                document.getElementById('taskName').textContent = 'WEBSITE DISCOVERY';
                fetch('/find-websites', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            checkTaskStatus();
                        }
                    });
            }
            
            function classifyCompanies() {
                document.getElementById('progressSection').style.display = 'block';
                document.getElementById('taskName').textContent = 'COMPANY CLASSIFICATION';
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
                                    data.progress.toLocaleString() + ' / ' + data.total.toLocaleString();
                                const percent = (data.progress / data.total * 100) || 0;
                                document.getElementById('progressFill').style.width = percent + '%';
                                
                                // Update current company
                                if (data.current_company) {
                                    document.getElementById('currentCompany').textContent = 
                                        'Processing: ' + data.current_company;
                                }
                                
                                // Update YES/NO stats for classification
                                if (data.task === 'Company Classification') {
                                    document.getElementById('progressStats').textContent = 
                                        'YES: ' + data.yes_count + ' | NO: ' + data.no_count;
                                    document.getElementById('yesCount').textContent = 
                                        ({{ yes_count }} + data.yes_count).toLocaleString();
                                }
                            } else {
                                clearInterval(statusCheckInterval);
                                document.getElementById('progressSection').style.display = 'none';
                                location.reload();
                            }
                        });
                }, 1000);
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