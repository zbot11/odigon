from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import os
import threading
from dotenv import load_dotenv
from database_operations import (
    get_database_stats, 
    truncate_database, 
    import_csv_file,
    find_websites_task,
    classify_companies_task
)

load_dotenv()

app = Flask(__name__)

# Global status for background tasks
task_status = {"running": False, "task": "", "progress": 0, "total": 0}

@app.route('/')
def index():
    stats = get_database_stats()
    
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
                
                <div class="task-status" id="taskStatus" style="display: none;">
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
    ''', stats=stats)

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

# Background task runners
def run_website_finder():
    global task_status
    task_status = {"running": True, "task": "Website Discovery", "progress": 0, "total": 0}
    find_websites_task(task_status)
    task_status["running"] = False

def run_classifier():
    global task_status
    task_status = {"running": True, "task": "Company Classification", "progress": 0, "total": 0}
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