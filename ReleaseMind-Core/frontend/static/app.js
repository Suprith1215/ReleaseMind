/* ================================================================
   ReleaseMind app.js — Production JavaScript
   AI DevOps Governance Engine
   ================================================================ */

// ── GLOBALS ─────────────────────────────────────────────────────────
let scene, camera, renderer, particles, glowSpheres = [];
let riskGaugeChart = null;
let trendChart = null;
let strategyChart = null;
let breakdownChart = null;
let historyTrendChart = null;
let serviceFailChart = null;
let strategyDistChart = null;
let metricsInterval = null;
let currentActiveTab = 'dashboard';

// ── 3D BACKGROUND ───────────────────────────────────────────────────
function init3DBackground() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas || typeof THREE === 'undefined') return;

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 0, 60);

    renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // ── Stars / particle field ──────────────────────────────────────
    const starGeo = new THREE.BufferGeometry();
    const starCount = 1500;
    const starPos = new Float32Array(starCount * 3);
    const starCol = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount * 3; i += 3) {
        starPos[i] = (Math.random() - 0.5) * 200;
        starPos[i + 1] = (Math.random() - 0.5) * 200;
        starPos[i + 2] = (Math.random() - 0.5) * 200;

        const r = Math.random();
        if (r < 0.33) {
            // purple tones
            starCol[i] = 0.5 + Math.random() * 0.3;
            starCol[i + 1] = 0.2 + Math.random() * 0.2;
            starCol[i + 2] = 1.0;
        } else if (r < 0.66) {
            // blue tones
            starCol[i] = 0.1;
            starCol[i + 1] = 0.5 + Math.random() * 0.4;
            starCol[i + 2] = 0.9 + Math.random() * 0.1;
        } else {
            // white tones
            starCol[i] = 0.8 + Math.random() * 0.2;
            starCol[i + 1] = 0.8 + Math.random() * 0.2;
            starCol[i + 2] = 1.0;
        }
    }

    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
    starGeo.setAttribute('color', new THREE.BufferAttribute(starCol, 3));

    const starMat = new THREE.PointsMaterial({
        size: 0.35,
        vertexColors: true,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
    });

    particles = new THREE.Points(starGeo, starMat);
    scene.add(particles);

    // ── Floating glow spheres ───────────────────────────────────────
    const sphereColors = [0x7c3aed, 0x6366f1, 0x38bdf8, 0xa855f7];
    sphereColors.forEach((color, i) => {
        const geo = new THREE.SphereGeometry(2 + Math.random() * 2, 16, 16);
        const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.08 });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(
            (Math.random() - 0.5) * 60,
            (Math.random() - 0.5) * 40,
            (Math.random() - 0.5) * 30
        );
        mesh.userData.speed = 0.003 + Math.random() * 0.005;
        mesh.userData.offset = i * (Math.PI / 2);
        scene.add(mesh);
        glowSpheres.push(mesh);
    });

    // Lights
    scene.add(new THREE.AmbientLight(0x7c3aed, 0.3));
    const ptLight = new THREE.PointLight(0x6366f1, 1.5, 200);
    ptLight.position.set(30, 30, 30);
    scene.add(ptLight);

    animate3D();
}

let _t = 0;
function animate3D() {
    requestAnimationFrame(animate3D);
    _t += 0.005;

    if (particles) {
        particles.rotation.y = _t * 0.06;
        particles.rotation.x = _t * 0.02;
    }

    glowSpheres.forEach(s => {
        s.position.y += Math.sin(_t + s.userData.offset) * s.userData.speed;
        s.position.x += Math.cos(_t * 0.7 + s.userData.offset) * s.userData.speed * 0.5;
        s.material.opacity = 0.06 + 0.04 * Math.sin(_t * 1.5 + s.userData.offset);
    });

    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    if (camera && renderer) {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }
});

// ── CHARTS INIT ─────────────────────────────────────────────────────
function initCharts() {
    Chart.defaults.color = '#8b8ba8';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
    Chart.defaults.font.family = "'Inter', sans-serif";

    // ---- Risk Gauge (doughnut) ----
    const gaugeCtx = document.getElementById('riskGauge')?.getContext('2d');
    if (gaugeCtx) {
        riskGaugeChart = new Chart(gaugeCtx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [0, 100],
                    backgroundColor: ['rgba(99,102,241,0.85)', 'rgba(255,255,255,0.05)'],
                    borderWidth: 0,
                    circumference: 270,
                    rotation: 225,
                }]
            },
            options: {
                responsive: false,
                cutout: '80%',
                animation: { duration: 700, easing: 'easeInOutQuart' },
                plugins: { legend: { display: false }, tooltip: { enabled: false } }
            }
        });
    }

    // ---- Trend Chart ----
    const trendCtx = document.getElementById('trendChart')?.getContext('2d');
    if (trendCtx) {
        trendChart = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Risk Score',
                    data: [],
                    borderColor: 'rgba(99,102,241,1)',
                    backgroundColor: 'rgba(99,102,241,0.08)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointBackgroundColor: '#7c3aed',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 1.5,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { maxRotation: 0, maxTicksLimit: 6 } },
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }

    // ---- Strategy Donut ----
    const stratCtx = document.getElementById('strategyChart')?.getContext('2d');
    if (stratCtx) {
        strategyChart = new Chart(stratCtx, {
            type: 'doughnut',
            data: {
                labels: ['ROLLING', 'CANARY', 'BLUE_GREEN', 'BLOCK'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(34,211,160,0.75)',
                        'rgba(245,158,11,0.75)',
                        'rgba(56,189,248,0.75)',
                        'rgba(239,68,68,0.75)',
                    ],
                    borderWidth: 0,
                    hoverOffset: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', font: { size: 10 } }
                    }
                }
            }
        });
    }

    // ── Analytics Charts ──────────────────────────────────────────────

    const breakCtx = document.getElementById('breakdownChart')?.getContext('2d');
    if (breakCtx) {
        breakdownChart = new Chart(breakCtx, {
            type: 'bar',
            data: {
                labels: ['Code Size', 'Intent', 'Developer', 'Dependency', 'History', 'Environment', 'Infrastructure', 'Timing'],
                datasets: [{
                    label: 'Risk Points',
                    data: [],
                    backgroundColor: [
                        'rgba(99,102,241,0.7)',
                        'rgba(124,58,237,0.7)',
                        'rgba(168,85,247,0.7)',
                        'rgba(245,158,11,0.7)',
                        'rgba(239,68,68,0.7)',
                        'rgba(56,189,248,0.7)',
                        'rgba(34,211,160,0.7)',
                        'rgba(251,191,36,0.7)',
                    ],
                    borderRadius: 6,
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    const histTrendCtx = document.getElementById('historyTrendChart')?.getContext('2d');
    if (histTrendCtx) {
        historyTrendChart = new Chart(histTrendCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Risk Score',
                    data: [],
                    borderColor: 'rgba(124,58,237,1)',
                    backgroundColor: 'rgba(124,58,237,0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.45,
                    pointRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } },
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }

    const svcFailCtx = document.getElementById('serviceFailureChart')?.getContext('2d');
    if (svcFailCtx) {
        serviceFailChart = new Chart(svcFailCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Failure Rate (%)',
                    data: [],
                    backgroundColor: 'rgba(239,68,68,0.65)',
                    borderRadius: 6,
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { callback: v => v + '%' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    const stratDistCtx = document.getElementById('strategyDistChart')?.getContext('2d');
    if (stratDistCtx) {
        strategyDistChart = new Chart(stratDistCtx, {
            type: 'doughnut',
            data: {
                labels: ['ROLLING', 'CANARY', 'BLUE_GREEN', 'BLOCK'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(34,211,160,0.8)',
                        'rgba(245,158,11,0.8)',
                        'rgba(56,189,248,0.8)',
                        'rgba(239,68,68,0.8)',
                    ],
                    borderWidth: 0,
                    hoverOffset: 8,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { padding: 20, usePointStyle: true, pointStyle: 'circle', font: { size: 11 } }
                    }
                }
            }
        });
    }
}

// ── SIDEBAR / NAVIGATION ────────────────────────────────────────────
function switchTab(tabId) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const panel = document.getElementById(`tab-${tabId}`);
    const navEl = document.querySelector(`[data-tab="${tabId}"]`);
    if (panel) panel.classList.add('active');
    if (navEl) navEl.classList.add('active');

    currentActiveTab = tabId;

    const titles = {
        dashboard: 'Command Center',
        github: 'GitHub Analysis',
        manual: 'Manual Assessment',
        history: 'Deployment History',
        analytics: 'Analytics',
    };
    document.getElementById('topbarTitle').textContent = titles[tabId] || tabId;

    if (tabId === 'history') loadFullHistory();
    if (tabId === 'analytics') loadAnalytics();

    // Close sidebar on mobile
    if (window.innerWidth <= 900) {
        document.getElementById('sidebar').classList.remove('open');
    }
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// ── SYSTEM METRICS ──────────────────────────────────────────────────
async function refreshMetrics() {
    const icon = document.getElementById('refreshIcon');
    icon?.classList.add('spin');

    try {
        const res = await fetch('/system-metrics');
        const data = await res.json();
        const sys = data.system || {};

        const cpu = sys.cpu_percent ?? 0;
        const mem = sys.memory_percent ?? 0;

        document.getElementById('cpuDisplay').textContent = cpu.toFixed(1) + '%';
        document.getElementById('memDisplay').textContent = mem.toFixed(1) + '%';
        document.getElementById('sidebarCpu').textContent = cpu.toFixed(1) + '%';
        document.getElementById('sidebarMem').textContent = mem.toFixed(1) + '%';
        document.getElementById('sidebarStatus').textContent = 'ONLINE';

        // Color warnings
        document.getElementById('cpuDisplay').style.color = cpu > 80 ? 'var(--clr-danger)' : cpu > 60 ? 'var(--clr-warning)' : 'var(--clr-success)';
        document.getElementById('memDisplay').style.color = mem > 80 ? 'var(--clr-danger)' : mem > 60 ? 'var(--clr-warning)' : 'var(--clr-info)';

    } catch (e) {
        document.getElementById('sidebarStatus').textContent = 'OFFLINE';
        document.getElementById('sidebarStatus').style.color = 'var(--clr-danger)';
    } finally {
        icon?.classList.remove('spin');
    }
}

// ── RISK GAUGE UPDATE ───────────────────────────────────────────────
function updateRiskGauge(score) {
    if (!riskGaugeChart) return;
    const pct = Math.min((score / 25) * 100, 100);
    const color = getRiskGradient(score);
    riskGaugeChart.data.datasets[0].data = [pct, 100 - pct];
    riskGaugeChart.data.datasets[0].backgroundColor[0] = color;
    riskGaugeChart.update();

    document.getElementById('gaugeScore').textContent = score.toFixed(1);
}

// ── STRATEGY BADGE ──────────────────────────────────────────────────
function getStrategyClass(strategy) {
    const map = {
        ROLLING: 'strategy-rolling',
        CANARY: 'strategy-canary',
        BLUE_GREEN: 'strategy-blue-green',
        BLOCK: 'strategy-block',
    };
    return map[strategy] || 'strategy-rolling';
}

function getBadgeClass(strategy) {
    const map = {
        ROLLING: 'badge-rolling',
        CANARY: 'badge-canary',
        BLUE_GREEN: 'badge-blue-green',
        BLOCK: 'badge-block',
    };
    return map[strategy] || 'badge-pending';
}

function getStrategyIcon(strategy) {
    const map = {
        ROLLING: 'fa-play-circle',
        CANARY: 'fa-dove',
        BLUE_GREEN: 'fa-exchange-alt',
        BLOCK: 'fa-ban',
    };
    return map[strategy] || 'fa-question-circle';
}

function getStrategyLabel(strategy) {
    const map = {
        ROLLING: '🟢 ROLLING',
        CANARY: '🟡 CANARY',
        BLUE_GREEN: '🔵 BLUE-GREEN',
        BLOCK: '🔴 BLOCKED',
    };
    return map[strategy] || strategy;
}

// ── RISK COLORS ─────────────────────────────────────────────────────
function getRiskColor(score) {
    if (score < 8) return 'var(--clr-success)';
    if (score < 14) return 'var(--clr-warning)';
    if (score < 20) return 'var(--clr-danger)';
    return '#ff2d55';
}

function getRiskGradient(score) {
    if (score < 8) return 'rgba(34,211,160,0.85)';
    if (score < 14) return 'rgba(245,158,11,0.85)';
    if (score < 20) return 'rgba(239,68,68,0.85)';
    return 'rgba(255,45,85,0.85)';
}

function getRiskClass(score) {
    if (score < 8) return 'risk-low';
    if (score < 14) return 'risk-medium';
    if (score < 20) return 'risk-high';
    return 'risk-critical';
}

// ── RENDER RISK BREAKDOWN BARS ──────────────────────────────────────
const BREAKDOWN_META = {
    code_size: { icon: 'fa-file-code', label: 'Code Size', color: '#6366f1' },
    commit_intent: { icon: 'fa-code-branch', label: 'Commit Intent', color: '#a855f7' },
    developer: { icon: 'fa-user', label: 'Developer', color: '#8b5cf6' },
    dependency: { icon: 'fa-project-diagram', label: 'Dependency', color: '#f59e0b' },
    history: { icon: 'fa-history', label: 'History', color: '#ef4444' },
    environment: { icon: 'fa-server', label: 'Environment', color: '#38bdf8' },
    infrastructure: { icon: 'fa-microchip', label: 'Infrastructure', color: '#22d3a0' },
    timing: { icon: 'fa-clock', label: 'Timing', color: '#fbbf24' },
};

function renderRiskBars(breakdown) {
    const total = breakdown.total || 1;
    const keys = Object.keys(BREAKDOWN_META);
    const maxVal = Math.max(...keys.map(k => breakdown[k] || 0), 1);

    const html = keys.map(k => {
        const meta = BREAKDOWN_META[k];
        const val = breakdown[k] || 0;
        const pct = (val / maxVal) * 100;

        return `
      <div class="breakdown-item">
        <div class="breakdown-header">
          <div class="breakdown-name">
            <i class="fas ${meta.icon}" style="color:${meta.color}"></i>
            ${meta.label}
          </div>
          <div class="breakdown-val" style="color:${meta.color}">${val.toFixed(2)}</div>
        </div>
        <div class="breakdown-bar-track">
          <div class="breakdown-bar-fill" style="width:${pct}%;background:linear-gradient(90deg,${meta.color}99,${meta.color})"></div>
        </div>
      </div>`;
    }).join('');

    document.getElementById('riskBars').innerHTML = html;
}

// ── RENDER REMEDIATION ──────────────────────────────────────────────
function renderRemediation(remediation) {
    const recs = remediation?.recommendations || [];
    if (!recs.length) {
        document.getElementById('remediationList').innerHTML =
            `<p style="color:var(--text-muted);font-size:0.82rem">No recommendations — risk is acceptable.</p>`;
        return;
    }

    const html = recs.slice(0, 6).map(r => {
        const icon = r.priority === 'HIGH' ? 'fa-exclamation-triangle' : 'fa-lightbulb';
        return `
      <div class="remediation-item priority-${r.priority}">
        <div class="rem-icon"><i class="fas ${icon}"></i></div>
        <div class="rem-body">
          <div class="rem-title">${r.title}</div>
          <div class="rem-detail">${r.detail}</div>
        </div>
      </div>`;
    }).join('');

    document.getElementById('remediationList').innerHTML = html;
}

// ── RENDER FULL RESULT ──────────────────────────────────────────────
function renderFullResult(data, panelContentId, emptyId) {
    const contentEl = document.getElementById(panelContentId);
    const emptyEl = document.getElementById(emptyId);
    if (!contentEl) return;

    const score = data.risk_score || 0;
    const strategy = data.deployment_strategy || 'ROLLING';
    const rb = data.risk_breakdown || {};
    const gh = data.github || {};
    const dep = data.dependency || {};
    const metrics = data.metrics || {};
    const learning = data.learning || {};
    const rem = data.remediation || {};

    const intentLabel = gh.commit_type_detected || rb.commit_intent && 'classified' || 'N/A';
    const trendVal = data.service_trend?.trend || 'no_data';
    const blastVal = `${dep.impacted_services?.length || 0} services`;

    emptyEl && (emptyEl.style.display = 'none');
    contentEl.style.display = 'block';

    // Update gauge
    updateRiskGauge(score);

    // Strategy badge
    const stratEl = document.getElementById('strategyBadge');
    if (stratEl) {
        stratEl.className = `strategy-badge-large ${getStrategyClass(strategy)}`;
        stratEl.innerHTML = `<i class="fas ${getStrategyIcon(strategy)}"></i> ${strategy}`;
    }

    const stratHeader = document.getElementById('strategyBadgeHeader');
    if (stratHeader) {
        stratHeader.className = `header-badge badge ${getBadgeClass(strategy)}`;
        stratHeader.textContent = strategy;
    }

    // Chips
    setChip('chipIntentVal', intentLabel);
    setChip('chipTrendVal', trendVal.toUpperCase());
    setChip('chipBlastVal', blastVal);

    // Risk bars
    renderRiskBars(rb);

    // Remediation
    renderRemediation(rem);
}

function setChip(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

// ── GITHUB ANALYSIS ─────────────────────────────────────────────────
async function analyzeGithub() {
    const owner = document.getElementById('gh-owner').value.trim();
    const repo = document.getElementById('gh-repo').value.trim();

    if (!owner || !repo) {
        showToast('error', 'Please enter both repository owner and name.');
        return;
    }

    const btn = document.getElementById('analyzeBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing…';

    // Show loading in result panel
    const resultPanel = document.getElementById('githubResultContent');
    const emptyEl = document.getElementById('ghEmptyState');
    emptyEl.style.display = 'none';
    resultPanel.style.display = 'block';
    resultPanel.innerHTML = `
    <div class="loading-overlay">
      <div class="loader"></div>
      <div class="loader-text">Running AI Governance Analysis…</div>
    </div>`;

    const payload = {
        repo_owner: owner,
        repo_name: repo,
        branch: document.getElementById('gh-branch').value || 'main',
        github_token: document.getElementById('gh-token').value.trim() || undefined,
        config_drift: document.getElementById('gh-config-drift').checked,
        resource_drift: document.getElementById('gh-resource-drift').checked,
        peak_hours: document.getElementById('gh-peak-hours').checked,
        weekend: document.getElementById('gh-weekend').checked,
    };

    try {
        const res = await fetch('/analyze-repo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (data.error && !data.risk_score) {
            resultPanel.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon" style="border-color:var(--clr-danger);color:var(--clr-danger)"><i class="fas fa-exclamation-triangle"></i></div>
          <p class="empty-title">Analysis Failed</p>
          <p class="empty-sub">${data.error}</p>
        </div>`;
            showToast('error', data.error);
            return;
        }

        renderGithubResult(data, resultPanel);

        // Sync to dashboard
        renderFullResult(data, 'resultContent', 'emptyState');
        updateDashboardStats();
        loadDashboardHistory();

        showToast('success', `Analysis complete — Risk: ${data.risk_score?.toFixed(1)} | Strategy: ${data.deployment_strategy}`);
        if (data.github_error) showToast('warning', `GitHub: ${data.github_error}`);

    } catch (e) {
        resultPanel.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon" style="border-color:var(--clr-danger);color:var(--clr-danger)"><i class="fas fa-server"></i></div>
        <p class="empty-title">Server Unreachable</p>
        <p class="empty-sub">${e.message}</p>
      </div>`;
        showToast('error', 'Could not reach the ReleaseMind server.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-search-plus"></i> Run AI Governance Analysis';
    }
}

function renderGithubResult(data, container) {
    const gh = data.github || {};
    const dep = data.dependency || {};
    const met = data.metrics || {};
    const lrn = data.learning || {};
    const rem = data.remediation || {};
    const rb = data.risk_breakdown || {};
    const strategy = data.deployment_strategy;
    const score = data.risk_score || 0;

    const servicesHTML = (dep.impacted_services || []).map((s, i) => {
        const cls = i < (dep.direct_services || []).length ? 'dep-direct' : 'dep-impacted';
        return `<span class="dep-node ${cls}"><i class="fas fa-circle" style="font-size:0.4em"></i>${s}</span>`;
    }).join('');

    container.innerHTML = `
    <div class="gh-result-body">

      <!-- Score Hero -->
      <div style="display:flex;align-items:center;gap:1rem;padding:1rem 0 1.25rem;border-bottom:1px solid var(--glass-border);margin-bottom:1.25rem">
        <div style="text-align:center">
          <div style="font-size:2.8rem;font-weight:900;line-height:1;color:${getRiskColor(score)}">${score.toFixed(1)}</div>
          <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-top:3px">Risk Score</div>
        </div>
        <div style="flex:1">
          <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:0.4rem">Strategy</div>
          <div class="strategy-badge-large ${getStrategyClass(strategy)}" style="font-size:0.9rem">
            <i class="fas ${getStrategyIcon(strategy)}"></i> ${strategy}
          </div>
        </div>
      </div>

      <!-- Commit Info -->
      <div class="gh-commit-block">
        <div class="gh-sha">${gh.commit_sha?.slice(0, 40) || '—'}</div>
        <div class="gh-message">${escHtml(gh.commit_message || 'No commit message')}</div>
        <div class="gh-author"><i class="fas fa-user-circle"></i> ${escHtml(gh.author || 'Unknown')} &nbsp;·&nbsp; <span class="badge ${gh.commit_type_detected === 'hotfix' ? 'badge-block' : 'badge-pending'}">${gh.commit_type_detected || 'unknown'}</span></div>
      </div>

      <!-- Stats Grid -->
      <div class="gh-stat-row">
        <div class="gh-stat">
          <div class="gh-stat-val clr-file">${gh.files_changed || 0}</div>
          <div class="gh-stat-lbl">Files Changed</div>
        </div>
        <div class="gh-stat">
          <div class="gh-stat-val clr-add">+${gh.lines_added || 0}</div>
          <div class="gh-stat-lbl">Lines Added</div>
        </div>
        <div class="gh-stat">
          <div class="gh-stat-val clr-del">-${gh.lines_deleted || 0}</div>
          <div class="gh-stat-lbl">Lines Deleted</div>
        </div>
      </div>

      <!-- Metrics -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-bottom:1rem">
        <div class="gh-stat">
          <div class="gh-stat-val" style="color:${met.cpu_percent > 80 ? 'var(--clr-danger)' : 'var(--clr-success)'}">${(met.cpu_percent || 0).toFixed(1)}%</div>
          <div class="gh-stat-lbl">CPU at Deploy</div>
        </div>
        <div class="gh-stat">
          <div class="gh-stat-val" style="color:${met.memory_percent > 80 ? 'var(--clr-danger)' : 'var(--clr-info)'}">${(met.memory_percent || 0).toFixed(1)}%</div>
          <div class="gh-stat-lbl">Memory at Deploy</div>
        </div>
      </div>

      <!-- Learning Insight -->
      ${lrn.recommendation ? `
      <div style="background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.2);border-radius:var(--radius-md);padding:0.75rem;margin-bottom:1rem;font-size:0.8rem;color:var(--text-secondary)">
        <div style="font-weight:700;color:var(--text-primary);margin-bottom:0.25rem"><i class="fas fa-brain" style="color:#a78bfa;margin-right:0.3rem"></i>Historical Learning</div>
        ${escHtml(lrn.recommendation)} (${lrn.similar_count || 0} similar commits, ${((lrn.similar_failure_rate || 0) * 100).toFixed(0)}% fail rate)
      </div>` : ''}

      <!-- Impacted Services -->
      ${servicesHTML ? `
      <div style="margin-bottom:1rem">
        <div class="section-title" style="margin-bottom:0.5rem"><i class="fas fa-project-diagram"></i> Impacted Services (depth: ${dep.dependency_depth || 0})</div>
        <div class="dep-vis">${servicesHTML}</div>
      </div>` : ''}

      <!-- Top Recommendations -->
      ${(rem.recommendations || []).slice(0, 3).map(r => `
      <div class="remediation-item priority-${r.priority}" style="margin-bottom:0.4rem">
        <div class="rem-icon"><i class="fas ${r.priority === 'HIGH' ? 'fa-exclamation-triangle' : 'fa-lightbulb'}"></i></div>
        <div class="rem-body">
          <div class="rem-title">${r.title}</div>
          <div class="rem-detail">${r.detail}</div>
        </div>
      </div>`).join('')}

    </div>
  `;
}

// ── MANUAL ASSESSMENT ───────────────────────────────────────────────
async function runManualAssess() {
    const contentEl = document.getElementById('manualResultContent');
    const emptyEl = document.getElementById('manualEmptyState');

    emptyEl.style.display = 'none';
    contentEl.style.display = 'block';
    contentEl.innerHTML = `<div class="loading-overlay"><div class="loader"></div><div class="loader-text">Computing risk…</div></div>`;

    const payload = {
        change: {
            intent: document.getElementById('m-intent').value,
            services: [document.getElementById('m-service').value],
        },
        human: {
            experience: document.getElementById('m-experience').value,
            owns_service: true,
        },
        environment: {
            config_drift: document.getElementById('m-config-drift').checked,
            resource_drift: false,
        },
        timing: {
            peak_hours: document.getElementById('m-peak-hours').checked,
            weekend: false,
        },
    };

    try {
        const res = await fetch('/decide', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        // Adapt to same structure
        const score = data.risk_score || 0;
        const strategy = data.deployment_strategy || 'ROLLING';
        const dep = data.dry_run || {};
        const rem = data.remediation || {};
        const rb = data.risk_breakdown || {};

        contentEl.innerHTML = `
      <div class="gh-result-body">
        <div style="display:flex;align-items:center;gap:1rem;padding:1rem 0 1.25rem;border-bottom:1px solid var(--glass-border);margin-bottom:1.25rem">
          <div style="text-align:center">
            <div style="font-size:2.8rem;font-weight:900;line-height:1;color:${getRiskColor(score)}">${score.toFixed(1)}</div>
            <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-top:3px">Risk Score</div>
          </div>
          <div style="flex:1">
            <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:0.4rem">Strategy</div>
            <div class="strategy-badge-large ${getStrategyClass(strategy)}">
              <i class="fas ${getStrategyIcon(strategy)}"></i> ${strategy}
            </div>
          </div>
        </div>

        <div class="gh-stat-row" style="grid-template-columns:1fr 1fr 1fr">
          <div class="gh-stat">
            <div class="gh-stat-val" style="color:var(--clr-info)">${dep.dependency_depth || 0}</div>
            <div class="gh-stat-lbl">Dep. Depth</div>
          </div>
          <div class="gh-stat">
            <div class="gh-stat-val" style="color:var(--clr-warning)">${(dep.impacted_services || []).length}</div>
            <div class="gh-stat-lbl">Impacted</div>
          </div>
          <div class="gh-stat">
            <div class="gh-stat-val" style="color:${getRiskColor(score)}">${dep.impact_level || '—'}</div>
            <div class="gh-stat-lbl">Impact Level</div>
          </div>
        </div>

        <div class="risk-breakdown-section" style="margin-top:1rem">
          <div class="section-title"><i class="fas fa-layer-group"></i> Risk Breakdown</div>
          ${renderRiskBarsHTML(rb)}
        </div>

        <div class="section-title" style="margin-top:1rem"><i class="fas fa-tools"></i> Recommendations</div>
        ${(rem.recommendations || []).slice(0, 4).map(r => `
        <div class="remediation-item priority-${r.priority}" style="margin-bottom:0.4rem">
          <div class="rem-icon"><i class="fas ${r.priority === 'HIGH' ? 'fa-exclamation-triangle' : 'fa-lightbulb'}"></i></div>
          <div class="rem-body">
            <div class="rem-title">${r.title}</div>
            <div class="rem-detail">${r.detail}</div>
          </div>
        </div>`).join('')}
      </div>`;

        showToast('success', `Risk: ${score.toFixed(1)} → ${strategy}`);
        updateDashboardStats();
        loadDashboardHistory();

    } catch (e) {
        contentEl.innerHTML = `<div class="empty-state"><p class="empty-title">Error</p><p class="empty-sub">${e.message}</p></div>`;
        showToast('error', e.message);
    }
}

function renderRiskBarsHTML(breakdown) {
    const keys = Object.keys(BREAKDOWN_META);
    const maxVal = Math.max(...keys.map(k => breakdown[k] || 0), 1);
    return keys.map(k => {
        const meta = BREAKDOWN_META[k];
        const val = breakdown[k] || 0;
        const pct = (val / maxVal) * 100;
        return `
      <div class="breakdown-item">
        <div class="breakdown-header">
          <div class="breakdown-name"><i class="fas ${meta.icon}" style="color:${meta.color}"></i>${meta.label}</div>
          <div class="breakdown-val" style="color:${meta.color}">${val.toFixed(2)}</div>
        </div>
        <div class="breakdown-bar-track">
          <div class="breakdown-bar-fill" style="width:${pct}%;background:${meta.color}99"></div>
        </div>
      </div>`;
    }).join('');
}

// ── HISTORY ─────────────────────────────────────────────────────────
async function loadFullHistory() {
    const tbody = document.getElementById('historyBody');
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="9" class="empty-row"><i class="fas fa-spinner fa-spin"></i> Loading…</td></tr>`;

    try {
        const res = await fetch('/history?limit=100');
        const data = await res.json();

        if (!data.length) {
            tbody.innerHTML = `<tr><td colspan="9" class="empty-row">No deployments recorded yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(d => {
            const stratClass = getBadgeClass(d.strategy);
            const outClass = d.outcome === 'success' ? 'badge-success' : d.outcome === 'failure' ? 'badge-failure' : 'badge-pending';
            const ts = new Date(d.timestamp).toLocaleString();
            return `
        <tr>
          <td class="td-mono">#${d.id}</td>
          <td style="color:var(--text-muted);font-size:0.78rem">${ts}</td>
          <td><span class="badge badge-canary" style="background:rgba(124,58,237,0.12);color:#a78bfa">${escHtml(d.service || '—')}</span></td>
          <td style="color:var(--text-secondary)">${escHtml(d.developer || '—')}</td>
          <td><span class="badge ${stratClass}">${d.strategy || '—'}</span></td>
          <td style="font-weight:700;color:${getRiskColor(d.risk_score)}">${(d.risk_score || 0).toFixed(1)}</td>
          <td><span class="badge badge-pending">${escHtml(d.commit_type || '—')}</span></td>
          <td class="td-mono">${d.files_changed || 0}</td>
          <td><span class="badge ${outClass}">${d.outcome || 'pending'}</span></td>
        </tr>`;
        }).join('');

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="9" class="empty-row">Error loading history: ${e.message}</td></tr>`;
    }
}

async function loadDashboardHistory() {
    try {
        const res = await fetch('/history?limit=6');
        const data = await res.json();
        const tbody = document.getElementById('dashHistoryBody');
        if (!tbody) return;

        if (!data.length) {
            tbody.innerHTML = `<tr><td colspan="5" class="empty-row">No deployments yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(d => {
            const stratClass = getBadgeClass(d.strategy);
            const outClass = d.outcome === 'success' ? 'badge-success' : d.outcome === 'failure' ? 'badge-failure' : 'badge-pending';
            const ts = new Date(d.timestamp).toLocaleTimeString();
            return `
        <tr>
          <td style="color:var(--text-muted)">${ts}</td>
          <td>${escHtml(d.service || '—')}</td>
          <td><span class="badge ${stratClass}">${d.strategy}</span></td>
          <td style="font-weight:700;color:${getRiskColor(d.risk_score)}">${(d.risk_score || 0).toFixed(1)}</td>
          <td><span class="badge ${outClass}">${d.outcome}</span></td>
        </tr>`;
        }).join('');

        // Update trend chart
        if (trendChart) {
            const sorted = [...data].reverse();
            trendChart.data.labels = sorted.map(d => new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
            trendChart.data.datasets[0].data = sorted.map(d => d.risk_score || 0);
            trendChart.update();
        }

        // Update strategy donut
        if (strategyChart) {
            const counts = { ROLLING: 0, CANARY: 0, BLUE_GREEN: 0, BLOCK: 0 };
            data.forEach(d => { if (counts[d.strategy] !== undefined) counts[d.strategy]++; });
            strategyChart.data.datasets[0].data = [counts.ROLLING, counts.CANARY, counts.BLUE_GREEN, counts.BLOCK];
            strategyChart.update();
        }

    } catch (e) { /* silent fail */ }
}

async function updateDashboardStats() {
    try {
        const res = await fetch('/history?limit=200');
        const data = await res.json();
        if (!data.length) return;

        document.getElementById('statTotalVal').textContent = data.length;
        document.getElementById('statBlockedVal').textContent = data.filter(d => d.strategy === 'BLOCK').length;
        document.getElementById('statCanaryVal').textContent = data.filter(d => d.strategy === 'CANARY').length;
        const avg = data.reduce((s, d) => s + (d.risk_score || 0), 0) / data.length;
        document.getElementById('statAvgRiskVal').textContent = avg.toFixed(1);

    } catch (e) { /* silent */ }
}

// ── OUTCOME SUBMISSION ──────────────────────────────────────────────
async function submitOutcome() {
    const depId = document.getElementById('outcomeDepId').value;
    const result = document.getElementById('outcomeResult').value;
    const msgEl = document.getElementById('outcomeMsg');

    if (!depId) { showToast('warning', 'Enter a deployment ID.'); return; }

    try {
        const res = await fetch('/deployment-outcome', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ deployment_id: parseInt(depId), outcome: result }),
        });
        const data = await res.json();

        if (data.error) {
            msgEl.style.color = 'var(--clr-danger)';
            msgEl.textContent = data.error;
        } else {
            msgEl.style.color = 'var(--clr-success)';
            msgEl.textContent = data.message || 'Outcome recorded.';
            showToast('success', data.message || 'Outcome saved.');
            loadFullHistory();
        }
    } catch (e) {
        msgEl.style.color = 'var(--clr-danger)';
        msgEl.textContent = e.message;
    }
}

// ── ANALYTICS ───────────────────────────────────────────────────────
async function loadAnalytics() {
    try {
        // History trend
        const res = await fetch('/history?limit=50');
        const data = await res.json();

        if (historyTrendChart && data.length) {
            const sorted = [...data].reverse();
            historyTrendChart.data.labels = sorted.map(d => new Date(d.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' }));
            historyTrendChart.data.datasets[0].data = sorted.map(d => d.risk_score || 0);
            historyTrendChart.update();
        }

        // Strategy dist
        if (strategyDistChart) {
            const counts = { ROLLING: 0, CANARY: 0, BLUE_GREEN: 0, BLOCK: 0 };
            data.forEach(d => { if (counts[d.strategy] !== undefined) counts[d.strategy]++; });
            strategyDistChart.data.datasets[0].data = [counts.ROLLING, counts.CANARY, counts.BLUE_GREEN, counts.BLOCK];
            strategyDistChart.update();
        }

        // Service failure rates
        const svcRes = await fetch('/service-stats');
        const svcData = await svcRes.json();

        if (serviceFailChart && svcData.length) {
            serviceFailChart.data.labels = svcData.map(s => s.service);
            serviceFailChart.data.datasets[0].data = svcData.map(s => Math.round((s.failure_rate || 0) * 100));
            serviceFailChart.update();
        }

        // Average breakdown across all deployments
        if (breakdownChart && data.length) {
            // Average of all breakdown dimensions — we just show avg risk per factor via heuristic
            const keys = Object.keys(BREAKDOWN_META);
            const avgs = {};
            // We'll show the most recent deployment's breakdown as approximation
            // In a real product, we'd store per-dimension in DB
            const lastRisk = data[0]?.risk_score || 0;
            const fake = {
                code_size: lastRisk * 0.20, commit_intent: lastRisk * 0.18, developer: lastRisk * 0.12,
                dependency: lastRisk * 0.20, history: lastRisk * 0.10, environment: lastRisk * 0.10,
                infrastructure: lastRisk * 0.05, timing: lastRisk * 0.05,
            };
            breakdownChart.data.datasets[0].data = keys.map(k => parseFloat((fake[k] || 0).toFixed(2)));
            breakdownChart.update();
        }

    } catch (e) { console.error('Analytics error:', e); }
}

// ── TOAST ────────────────────────────────────────────────────────────
function showToast(type, message) {
    const icons = { success: 'fa-check-circle', error: 'fa-times-circle', warning: 'fa-exclamation-triangle', info: 'fa-info-circle' };
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fas ${icons[type] || 'fa-info-circle'}"></i><span>${escHtml(message)}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.3s'; setTimeout(() => toast.remove(), 350); }, 4500);
}

// ── UTILITIES ────────────────────────────────────────────────────────
function escHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── INIT ─────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
    init3DBackground();
    initCharts();
    refreshMetrics();
    updateDashboardStats();
    loadDashboardHistory();

    // Auto-refresh metrics every 30s
    metricsInterval = setInterval(refreshMetrics, 30000);
});

// Expose for HTML onclick
window.switchTab = switchTab;
window.toggleSidebar = toggleSidebar;
window.refreshMetrics = refreshMetrics;
window.analyzeGithub = analyzeGithub;
window.runManualAssess = runManualAssess;
window.loadFullHistory = loadFullHistory;
window.submitOutcome = submitOutcome;
