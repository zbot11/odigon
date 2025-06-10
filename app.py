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