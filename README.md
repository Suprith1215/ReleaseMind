# 🚀 ReleaseMind — DevOps Release Governance Platform

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Docker](https://img.shields.io/badge/Container-Docker-blue)
![Kubernetes](https://img.shields.io/badge/Orchestration-Kubernetes-blue)
![CI](https://img.shields.io/badge/CI-Simulated-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Overview

**ReleaseMind** is an intelligent DevOps governance platform that evaluates deployment risk and automatically selects Kubernetes rollout strategies before release.

It simulates a real production pipeline where:

- Code changes are analyzed
- Risk is calculated
- Deployment strategy is selected
- Kubernetes rollout is executed

This project demonstrates practical understanding of:

- CI/CD concepts
- Containerization
- Kubernetes deployment strategies
- DevOps automation
- Policy-driven release control

---

## 🧠 Key Features

- ✅ Risk-based deployment decisions  
- ✅ CI pipeline simulation  
- ✅ Automatic rollout strategy selection  
- ✅ Kubernetes deployment execution  
- ✅ Browser UI for testing decisions  
- ✅ Decision logging for audit/history  

---

## ⚙️ Architecture

Developer Input
│
▼
┌──────────────────────┐
│ ReleaseMind UI/API │
└──────────┬───────────┘
▼
┌──────────────────────┐
│ Risk Engine │
│ Decision Engine │
│ Simulator │
└──────────┬───────────┘
▼
┌──────────────────────┐
│ CI Simulation │
│ pipeline.bat │
└──────────┬───────────┘
▼
┌──────────────────────┐
│ Kubernetes Hook │
│ deploy.bat │
└──────────┬───────────┘
▼
┌──────────────────────┐
│ Minikube Cluster │
│ Rolling / Canary │
│ Blue-Green Deploy │
└──────────────────────┘

## 🖥️ Demo — Run Locally

### 1️⃣ Start Docker Backend

```bash
docker run -d -p 7000:7000 --name releasemind-brain releasemind-brain
2️⃣ Start Kubernetes
minikube start --driver=docker


3️⃣ Run CI Simulation
bash
Copy code
cd ReleaseMind-Core/ci-local
pipeline.bat
4️⃣ Deploy Based on Strategy
bash
Copy code
copy response.json ../k8s-hook
cd ../k8s-hook
deploy.bat
5️⃣ Verify Pods
bash
Copy code
kubectl get pods
🌐 Open Browser
arduino
Copy code
http://localhost:7000
🛠️ Tech Stack
Area	Tools
Backend	Python Flask
Containers	Docker
Orchestration	Kubernetes (Minikube)
Automation	Batch CI Simulation
Frontend	HTML/CSS/JS
Version Control	GitHub

🎯 Learning Outcomes
This project demonstrates:

CI/CD pipeline concepts

Container lifecycle management

Kubernetes rollout strategies

DevOps automation design

Deployment risk governance

🔮 Future Enhancements
Repo quality scanner integration

AWS EKS deployment

Real GitHub Actions pipeline

Prometheus monitoring

React dashboard UI

👤 Author
Thati Sai Suprith
GitHub: https://github.com/Suprith1215

📄 License
MIT License



# ✅ STEP 2 — Push README

Run:
git add README.md
git commit -m "Added professional README"
git push
