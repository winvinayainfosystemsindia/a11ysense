def get_admin_dashboard_html() -> str:
    """
    Returns the raw, responsive dark-mode HTML/CSS dashboard for central error auditing.
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A11ySense AI - Central Telemetry & Exceptions</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #09090b;
            --surface: #121214;
            --border: #27272a;
            --text: #f4f4f5;
            --text-secondary: #a1a1aa;
            --primary: #8b5cf6;
            --primary-glow: rgba(139, 92, 246, 0.15);
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.15);
            --warning: #f59e0b;
            --warning-glow: rgba(245, 158, 11, 0.15);
            --success: #10b981;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Outfit', sans-serif;
        }

        body {
            background-color: var(--bg);
            color: var(--text);
            padding: 2rem;
            min-height: 100vh;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.5rem;
        }

        .logo-group {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            width: 2.5rem;
            height: 2.5rem;
            background: linear-gradient(135deg, var(--primary), #ec4899);
            border-radius: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            color: white;
            box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
        }

        h1 {
            font-size: 1.75rem;
            font-weight: 700;
            background: linear-gradient(to right, #ffffff, var(--text-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-badge {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid var(--success);
            color: var(--success);
            padding: 0.4rem 0.8rem;
            border-radius: 2rem;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .status-dot {
            width: 0.5rem;
            height: 0.5rem;
            background-color: var(--success);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 1; }
            100% { transform: scale(0.9); opacity: 0.5; }
        }

        .grid-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            background-color: var(--surface);
            border: 1px solid var(--border);
            padding: 1.5rem;
            border-radius: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            border-color: var(--primary);
            box-shadow: 0 5px 20px var(--primary-glow);
        }

        .metric-card.critical:hover {
            border-color: var(--danger);
            box-shadow: 0 5px 20px var(--danger-glow);
        }

        .metric-title {
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-value {
            font-size: 2.25rem;
            font-weight: 700;
        }

        .dashboard-body {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }

        .section-card {
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem;
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            gap: 1rem;
        }

        .section-title {
            font-size: 1.2rem;
            font-weight: 600;
        }

        .search-input {
            background-color: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 0.6rem 1rem;
            border-radius: 0.75rem;
            outline: none;
            width: 300px;
            font-size: 0.9rem;
            transition: border-color 0.3s ease;
        }

        .search-input:focus {
            border-color: var(--primary);
        }

        .table-container {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th {
            border-bottom: 1px solid var(--border);
            padding: 0.75rem 1rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-weight: 600;
        }

        td {
            padding: 1rem;
            border-bottom: 1px solid #1c1c1f;
            font-size: 0.92rem;
        }

        tr:hover td {
            background-color: rgba(255, 255, 255, 0.02);
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 0.5rem;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge.critical {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
            border: 1px solid var(--danger);
        }

        .badge.error {
            background: rgba(245, 158, 11, 0.1);
            color: var(--warning);
            border: 1px solid var(--warning);
        }

        .badge.warning {
            background: rgba(139, 92, 246, 0.1);
            color: var(--primary);
            border: 1px solid var(--primary);
        }

        .accordion-btn {
            background: none;
            border: none;
            color: var(--primary);
            font-weight: 600;
            cursor: pointer;
            outline: none;
            font-size: 0.88rem;
        }

        .accordion-btn:hover {
            text-decoration: underline;
        }

        .traceback-row {
            display: none;
            background-color: #0b0b0d;
        }

        .traceback-container {
            padding: 1.5rem;
            border-left: 2px solid var(--primary);
            font-family: monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            color: #d4d4d8;
            max-height: 400px;
            overflow-y: auto;
            background-color: #050507;
            border-radius: 0.5rem;
        }

        .no-data {
            text-align: center;
            padding: 3rem;
            color: var(--text-secondary);
        }

        .metric-cards-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
    </style>
</head>
<body>

    <header>
        <div class="logo-group">
            <div class="logo-icon">A</div>
            <div>
                <h1>A11ySense AI</h1>
                <p style="font-size: 0.85rem; color: var(--text-secondary)">Central Distributed Fault Logging & Telemetry Dashboard</p>
            </div>
        </div>
        
        <div class="status-badge">
            <div class="status-dot"></div>
            Error Event Bus Active
        </div>
    </header>

    <div class="metric-cards-group">
        <div class="metric-card">
            <div class="metric-title">Total Logs Logged</div>
            <div class="metric-value" id="stat-total">0</div>
        </div>
        <div class="metric-card critical">
            <div class="metric-title">Critical Anomaly Crashes</div>
            <div class="metric-value" id="stat-critical" style="color: var(--danger)">0</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Standard Errors</div>
            <div class="metric-value" id="stat-error" style="color: var(--warning)">0</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Service Count</div>
            <div class="metric-value" id="stat-services">0</div>
        </div>
    </div>

    <div class="dashboard-body">
        <div class="section-card">
            <div class="section-header">
                <h2 class="section-title">Fault Stream Events (Real-time SQLite persistence)</h2>
                <input type="text" class="search-input" id="search-box" placeholder="Search by Message or Correlation ID..." onkeyup="filterTable()">
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Service</th>
                            <th>Severity</th>
                            <th>Correlation ID</th>
                            <th>Error Message</th>
                            <th>Timestamp</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="error-logs-body">
                        <!-- Loaded dynamically -->
                    </tbody>
                </table>
                <div id="no-data-msg" class="no-data" style="display: none;">
                    No faults persisted yet or matching filters!
                </div>
            </div>
        </div>
    </div>

    <script>
        let logsData = [];

        async function fetchStats() {
            try {
                const response = await fetch('/api/admin/errors/stats');
                if (!response.ok) throw new Error("HTTP failure");
                const data = await response.json();
                
                // Update stats cards
                document.getElementById('stat-total').innerText = data.total_errors || 0;
                document.getElementById('stat-critical').innerText = data.critical_count || 0;
                document.getElementById('stat-error').innerText = data.error_count || 0;
                document.getElementById('stat-services').innerText = Object.keys(data.service_breakdown || {}).length || 0;
                
                logsData = data.latest_logs || [];
                renderLogs(logsData);
            } catch (err) {
                console.error("Dashboard error:", err);
            }
        }

        function renderLogs(logs) {
            const tbody = document.getElementById('error-logs-body');
            tbody.innerHTML = '';
            
            if (logs.length === 0) {
                document.getElementById('no-data-msg').style.display = 'block';
                return;
            }
            document.getElementById('no-data-msg').style.display = 'none';

            logs.forEach((log, index) => {
                const context = JSON.parse(log.context_json || '{}');
                const traceback = context.traceback || 'No traceback captured.';
                const formattedDate = new Date(log.timestamp).toLocaleString();
                
                // Main Info Row
                const infoRow = document.createElement('tr');
                infoRow.innerHTML = `
                    <td><strong style="color: var(--primary)">${log.service_name.toUpperCase()}</strong></td>
                    <td><span class="badge ${log.severity}">${log.severity}</span></td>
                    <td style="font-family: monospace; color: var(--text-secondary); font-size: 0.85rem">${log.correlation_id}</td>
                    <td style="font-weight: 600; max-width: 350px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${log.message}</td>
                    <td style="color: var(--text-secondary); font-size: 0.85rem">${formattedDate}</td>
                    <td>
                        <button class="accordion-btn" onclick="toggleTraceback(${index})">Traceback</button>
                    </td>
                `;
                tbody.appendChild(infoRow);

                // Traceback Detail Row
                const detailRow = document.createElement('tr');
                detailRow.id = `trace-${index}`;
                detailRow.className = 'traceback-row';
                detailRow.innerHTML = `
                    <td colspan="6">
                        <div class="traceback-container">
<strong>Traceback Exception Context</strong>
--------------------------------------------------------------------------------
${traceback}
                        </div>
                    </td>
                `;
                tbody.appendChild(detailRow);
            });
        }

        function toggleTraceback(index) {
            const element = document.getElementById(`trace-${index}`);
            if (element.style.display === 'table-row') {
                element.style.display = 'none';
            } else {
                element.style.display = 'table-row';
            }
        }

        function filterTable() {
            const query = document.getElementById('search-box').value.toLowerCase().trim();
            if (!query) {
                renderLogs(logsData);
                return;
            }

            const filtered = logsData.filter(log => {
                return log.message.toLowerCase().includes(query) || 
                       log.correlation_id.toLowerCase().includes(query) ||
                       log.service_name.toLowerCase().includes(query);
            });
            renderLogs(filtered);
        }

        // Poll every 4 seconds for live updates
        fetchStats();
        setInterval(fetchStats, 4000);
    </script>
</body>
</html>
"""
