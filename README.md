# Pathfinder – AI-Powered Group Trip Planner

[![CI / CD](https://github.com/vedprakashmishra/pathfinder/actions/workflows/ci-cd-pipeline.yml/badge.svg)](https://github.com/vedprakashmishra/pathfinder/actions)
[![Pause / Resume](https://github.com/vedprakashmishra/pathfinder/actions/workflows/pause-resume.yml/badge.svg)](https://github.com/vedprakashmishra/pathfinder/actions)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

Pathfinder eliminates the chaos of planning **multi-family group trips** by centralising communication, preference gathering and AI-generated itineraries – all secured by Auth0 and deployed cost-efficiently on Azure.

---
## Table of Contents
1. Key Features  
2. Architecture Overview  
3. Quick Start (Local)  
4. Cloud Deployment (Azure)  
5. Development Workflow  
6. Cost Optimisation & Pause/Resume  
7. License

---
## 1. Key Features
• **AI Itinerary Generation** – Multi-provider LLM orchestration (OpenAI / Gemini / Claude).  
• **Real-Time Collaboration** – Socket.IO chat, live presence and smart polls.  
• **Budget & Expense Tracking** – Shared cost breakdowns and settlement suggestions.  
• **Enterprise-grade Security** – Auth0 zero-trust model and Key Vault- backed secrets.  
• **Hybrid Storage** – Azure SQL (relational) + Cosmos DB (documents) + Storage Account (files).  
• **Cost-Aware Architecture** – Two-layer pause/resume model provides ± 70 % savings when idle.

---
## 2. Architecture Overview
A full description lives in [`docs/metadata.md`](docs/metadata.md) (single source of truth).  
High-level summary:

```
Persistent Layer (pathfinder-db-rg)   Ephemeral Layer (pathfinder-rg)
┌──────────────────────────────┐     ┌──────────────────────────────┐
│  • Azure SQL & Cosmos DB     │     │  • Azure Container Apps      │
│  • Storage Account (files)   │◄───►│  • Backend & Frontend        │
│  • Key Vault (secrets)       │     │  • Container Registry        │
└──────────────────────────────┘     │  • Application Insights      │
                                     └──────────────────────────────┘
```
Resume in 5-10 minutes; delete compute layer anytime for immediate savings.

---
## 3. Quick Start (Local Development)
Prerequisites: **Node 18+**, **Python 3.12+**, **Docker**
```bash
# Clone & prepare
git clone https://github.com/vedprakashmishra/pathfinder.git
cd pathfinder

# Back-end
cp backend/.env.example backend/.env

# Front-end
cp frontend/.env.example frontend/.env.local

# Launch full stack
docker compose up -d
open http://localhost:3000        # React PWA
open http://localhost:8000/docs   # FastAPI docs
```

---
## 4. Cloud Deployment (Azure)
Infrastructure is defined with **Bicep** in `infrastructure/bicep/` and automated by GitHub Actions.

1. **Secrets** – Add `AZURE_CREDENTIALS`, `SQL_ADMIN_USERNAME`, `SQL_ADMIN_PASSWORD`, (optional) `OPENAI_API_KEY` to your repository.  
2. **Deploy Data Layer (one-time)**
   ```bash
   ./scripts/deploy-data-layer.sh   # or run the “Deploy Infrastructure” workflow
   ```
3. **Resume / Deploy Compute Layer**
   ```bash
   ./scripts/resume-environment.sh  # or commit/push to trigger CI/CD
   ```
4. **Pause to Save Cost**  
   ```bash
   ./scripts/pause-environment.sh
   ```

For advanced options, see the **Pause / Resume** workflow or the scripts in `scripts/`.

---
## 5. Development Workflow
```bash
# Back-end – type safety & style
ruff . && mypy . && pytest -q

# Front-end – lint & tests
npm run lint && npm test

# Pre-commit hooks
pre-commit run --all-files
```

Continuous integration executes the full test suite and, on main, builds & deploys containers to Azure Container Apps.

---
## 6. Cost Optimisation
• **Active**: ≈ $50–75 / month  
• **Paused (compute deleted)**: ≈ $15–25 / month  
Save ≈ 70 % with one command:
```bash
./scripts/pause-environment.sh   # Pause
./scripts/resume-environment.sh  # Resume
```

---
## 7. License
This project is licensed under the **GNU Affero General Public License v3.0** – see [`LICENSE`](LICENSE).  
Commercial or closed-source usage is available via dual-licensing; contact the maintainer for details.
