// ==================== GLOBAL VARIABLES ====================
let riskGaugeChart = null;
let riskDistributionChart = null;
let strategyChart = null;
let trendChart = null;
let scene, camera, renderer, particles;

// ==================== 3D BACKGROUND INITIALIZATION ====================
function init3DBackground() {
  const canvas = document.getElementById('bg-canvas');
  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 50;

  renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);

  // Create particle system
  const particlesGeometry = new THREE.BufferGeometry();
  const particleCount = 1000;
  const positions = new Float32Array(particleCount * 3);
  const colors = new Float32Array(particleCount * 3);

  for (let i = 0; i < particleCount * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 100;
    positions[i + 1] = (Math.random() - 0.5) * 100;
    positions[i + 2] = (Math.random() - 0.5) * 100;

    // Purple-blue gradient colors
    colors[i] = 0.4 + Math.random() * 0.3;     // R
    colors[i + 1] = 0.5 + Math.random() * 0.3; // G
    colors[i + 2] = 0.9 + Math.random() * 0.1; // B
  }

  particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  const particlesMaterial = new THREE.PointsMaterial({
    size: 0.5,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending
  });

  particles = new THREE.Points(particlesGeometry, particlesMaterial);
  scene.add(particles);

  // Add ambient light
  const ambientLight = new THREE.AmbientLight(0x667eea, 0.5);
  scene.add(ambientLight);

  // Add point lights
  const pointLight1 = new THREE.PointLight(0x667eea, 1, 100);
  pointLight1.position.set(10, 10, 10);
  scene.add(pointLight1);

  const pointLight2 = new THREE.PointLight(0x764ba2, 1, 100);
  pointLight2.position.set(-10, -10, -10);
  scene.add(pointLight2);

  animate3D();
}

function animate3D() {
  requestAnimationFrame(animate3D);

  particles.rotation.x += 0.0005;
  particles.rotation.y += 0.001;

  renderer.render(scene, camera);
}

// Handle window resize
window.addEventListener('resize', () => {
  if (camera && renderer) {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }
});

// ==================== CHART INITIALIZATION ====================
function initializeCharts() {
  // Risk Gauge Chart (Doughnut)
  const gaugeCtx = document.getElementById('riskGauge').getContext('2d');
  riskGaugeChart = new Chart(gaugeCtx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [0, 100],
        backgroundColor: [
          'rgba(102, 126, 234, 0.8)',
          'rgba(255, 255, 255, 0.1)'
        ],
        borderWidth: 0,
        circumference: 180,
        rotation: 270
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '75%',
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false }
      }
    }
  });

  // Risk Distribution Chart (Bar)
  const distCtx = document.getElementById('riskDistributionChart').getContext('2d');
  riskDistributionChart = new Chart(distCtx, {
    type: 'bar',
    data: {
      labels: ['Intent', 'Human', 'Environment', 'Timing', 'Dependencies'],
      datasets: [{
        label: 'Risk Contribution',
        data: [0, 0, 0, 0, 0],
        backgroundColor: [
          'rgba(102, 126, 234, 0.8)',
          'rgba(118, 75, 162, 0.8)',
          'rgba(240, 147, 251, 0.8)',
          'rgba(245, 87, 108, 0.8)',
          'rgba(79, 172, 254, 0.8)'
        ],
        borderRadius: 8,
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          ticks: { color: '#b4b4c8' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#b4b4c8' }
        }
      }
    }
  });

  // Strategy Chart (Pie)
  const strategyCtx = document.getElementById('strategyChart').getContext('2d');
  strategyChart = new Chart(strategyCtx, {
    type: 'pie',
    data: {
      labels: ['ALLOW', 'BLOCK', 'CANARY'],
      datasets: [{
        data: [0, 0, 0],
        backgroundColor: [
          'rgba(79, 172, 254, 0.8)',
          'rgba(250, 112, 154, 0.8)',
          'rgba(254, 225, 64, 0.8)'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#b4b4c8', padding: 15 }
        }
      }
    }
  });

  // Trend Chart (Line)
  const trendCtx = document.getElementById('trendChart').getContext('2d');
  trendChart = new Chart(trendCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Risk Score',
        data: [],
        borderColor: 'rgba(102, 126, 234, 1)',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgba(102, 126, 234, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          ticks: { color: '#b4b4c8' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#b4b4c8', maxRotation: 0 }
        }
      }
    }
  });
}

// ==================== SIMULATE DEPLOYMENT ====================
function simulate() {
  const payload = {
    change: {
      intent: document.getElementById("intent").value,
      services: [document.getElementById("service").value]
    },
    human: {
      experience: document.getElementById("experience").value,
      owns_service: true
    },
    environment: {
      config_drift: document.getElementById("config_drift").checked,
      resource_drift: false
    },
    timing: {
      peak_hours: document.getElementById("peak_hours").checked,
      weekend: false
    }
  };

  fetch("/decide", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(res => res.json())
    .then(data => {
      renderCurrent(data);
      updateRiskGauge(data.risk_score);
      updateRiskFactors(data, payload);
      loadHistory();
    })
    .catch(err => {
      document.getElementById("output").innerHTML = `
      <div class="placeholder-state">
        <i class="fas fa-exclamation-triangle" style="color: #fa709a;"></i>
        <p>Error: ${err.message}</p>
      </div>
    `;
    });
}

// ==================== RENDER CURRENT RESULT ====================
function renderCurrent(data) {
  const isBlocked = data.deployment_strategy === "BLOCK";
  const strategyClass = isBlocked ? "strategy-block" : "strategy-allow";
  const icon = isBlocked ? "fa-ban" : "fa-check-circle";

  document.getElementById("output").innerHTML = `
    <div class="risk-result">
      <p>
        <b>Deployment Strategy:</b>
        <span class="strategy-badge ${strategyClass}">
          <i class="fas ${icon}"></i>
          ${data.deployment_strategy}
        </span>
      </p>
      <p><b>Risk Score:</b> <span style="font-size: 1.5rem; font-weight: 700; color: ${getRiskColor(data.risk_score)}">${data.risk_score}</span></p>
      <p><b>Impact Level:</b> <span style="color: ${getImpactColor(data.dry_run.impact_level)}">${data.dry_run.impact_level}</span></p>
      <p><b>Impacted Services:</b> ${data.dry_run.impacted_services.join(", ")}</p>
    </div>
  `;
}

// ==================== UPDATE RISK GAUGE ====================
function updateRiskGauge(riskScore) {
  const maxRisk = 30; // Approximate max risk
  const percentage = Math.min((riskScore / maxRisk) * 100, 100);

  if (riskGaugeChart) {
    riskGaugeChart.data.datasets[0].data = [percentage, 100 - percentage];
    riskGaugeChart.data.datasets[0].backgroundColor[0] = getRiskGradient(riskScore);
    riskGaugeChart.update();
  }
}

// ==================== UPDATE RISK FACTORS ====================
function updateRiskFactors(data, payload) {
  const factors = [];

  // Intent risk
  const intentWeights = { hotfix: 2, feature: 4, refactor: 6 };
  factors.push({
    label: 'Change Intent',
    value: intentWeights[payload.change.intent] || 3,
    icon: 'fa-code-branch',
    color: '#667eea'
  });

  // Human risk
  let humanRisk = 0;
  if (payload.human.experience === 'new') humanRisk += 3;
  if (!payload.human.owns_service) humanRisk += 2;
  factors.push({
    label: 'Human Factor',
    value: humanRisk,
    icon: 'fa-user',
    color: '#764ba2'
  });

  // Environment risk
  let envRisk = 0;
  if (payload.environment.config_drift) envRisk += 4;
  if (payload.environment.resource_drift) envRisk += 3;
  factors.push({
    label: 'Environment',
    value: envRisk,
    icon: 'fa-server',
    color: '#f093fb'
  });

  // Timing risk
  let timingRisk = 0;
  if (payload.timing.peak_hours) timingRisk += 2;
  if (payload.timing.weekend) timingRisk += 1;
  factors.push({
    label: 'Timing',
    value: timingRisk,
    icon: 'fa-clock',
    color: '#f5576c'
  });

  // Dependencies
  const depRisk = payload.change.services.length * 2;
  factors.push({
    label: 'Dependencies',
    value: depRisk,
    icon: 'fa-project-diagram',
    color: '#4facfe'
  });

  // Render factors
  const factorsHTML = factors.map(f => `
    <div class="risk-factor-item">
      <div class="risk-factor-label">
        <i class="fas ${f.icon}" style="color: ${f.color}"></i>
        <span>${f.label}</span>
      </div>
      <div class="risk-factor-value" style="color: ${f.color}">+${f.value}</div>
    </div>
  `).join('');

  document.getElementById('riskFactors').innerHTML = factorsHTML;

  // Update distribution chart
  if (riskDistributionChart) {
    riskDistributionChart.data.datasets[0].data = factors.map(f => f.value);
    riskDistributionChart.update();
  }
}

// ==================== LOAD HISTORY ====================
function loadHistory() {
  fetch("/decisions")
    .then(res => res.json())
    .then(data => {
      const tbody = document.querySelector("#history-table tbody");
      tbody.innerHTML = "";

      let allowCount = 0;
      let blockCount = 0;
      let canaryCount = 0;
      let totalRisk = 0;
      const trendData = [];

      data.forEach((d, index) => {
        // Count strategies
        if (d.deployment_strategy === "ALLOW") allowCount++;
        else if (d.deployment_strategy === "BLOCK") blockCount++;
        else if (d.deployment_strategy === "CANARY") canaryCount++;

        totalRisk += d.risk_score;

        // Collect trend data (last 10)
        if (index < 10) {
          trendData.unshift({
            time: new Date(d.timestamp).toLocaleTimeString(),
            risk: d.risk_score
          });
        }

        const strategyClass = d.deployment_strategy === "BLOCK" ? "strategy-block-cell" : "strategy-allow-cell";

        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${new Date(d.timestamp).toLocaleString()}</td>
          <td><span class="strategy-cell ${strategyClass}">${d.deployment_strategy}</span></td>
          <td style="color: ${getRiskColor(d.risk_score)}; font-weight: 700;">${d.risk_score}</td>
          <td>${d.dry_run.impacted_services.join(", ")}</td>
          <td>${d.explanation?.human?.experience || 'N/A'}</td>
          <td>${d.dry_run.impact_level}</td>
        `;
        tbody.appendChild(row);
      });

      // Update stats
      document.getElementById('totalDeployments').textContent = data.length;
      document.getElementById('blockedDeployments').textContent = blockCount;
      document.getElementById('allowedDeployments').textContent = allowCount;
      document.getElementById('avgRisk').textContent = data.length > 0 ? (totalRisk / data.length).toFixed(1) : 0;

      // Update strategy chart
      if (strategyChart) {
        strategyChart.data.datasets[0].data = [allowCount, blockCount, canaryCount];
        strategyChart.update();
      }

      // Update trend chart
      if (trendChart && trendData.length > 0) {
        trendChart.data.labels = trendData.map(t => t.time);
        trendChart.data.datasets[0].data = trendData.map(t => t.risk);
        trendChart.update();
      }
    })
    .catch(err => {
      console.error('Error loading history:', err);
    });
}

// ==================== UTILITY FUNCTIONS ====================
function getRiskColor(risk) {
  if (risk < 10) return '#4facfe';
  if (risk < 15) return '#fee140';
  return '#fa709a';
}

function getRiskGradient(risk) {
  if (risk < 10) return 'rgba(79, 172, 254, 0.8)';
  if (risk < 15) return 'rgba(254, 225, 64, 0.8)';
  return 'rgba(250, 112, 154, 0.8)';
}

function getImpactColor(impact) {
  if (impact === 'LOW') return '#4facfe';
  if (impact === 'MEDIUM') return '#fee140';
  return '#fa709a';
}

// ==================== INITIALIZATION ====================
window.onload = function () {
  init3DBackground();
  initializeCharts();
  loadHistory();
};
