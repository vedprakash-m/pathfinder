# Pathfinder – Project Metadata (Source of Truth)

**Version:** 5.0  
**Last Updated:** June 14 2025  
**Maintainer:** Vedprakash Mishra  

---
## 1  Platform Purpose
Pathfinder is an AI-powered platform that eliminates the chaos of planning multi-family group trips. It centralises communication, preference collection and AI-generated itineraries while enforcing enterprise-grade security.

---
## 2  Current Production-Ready Architecture

### 2.1  Two-Layer Pause/Resume Model (Azure-only)
• **`pathfinder-db-rg` (Persistent Data)** – Azure SQL, Cosmos DB (serverless), Storage Account, Key Vault. _Never deleted._  
• **`pathfinder-rg` (Ephemeral Compute)** – Azure Container Apps env, backend & frontend apps, Container Registry, Application Insights. _Safe to delete for cost savings._  
→ **70 % cost reduction** when compute layer is paused (≈ $35-50 / month saved).  
→ Resume time: **5-10 minutes**, fully automated via CI/CD.

### 2.2  Technology Stack
Frontend (React 18 + Vite + Tailwind + Fluent UI v9 + PWA)  
Backend (FastAPI + Python 3.12 + Pydantic v2 + SQLAlchemy + Alembic + Socket.IO)  
AI (Custom LLM Orchestration – OpenAI / Gemini / Claude)  
Data (Azure SQL + Cosmos DB) Files (Azure Storage – _in data layer_)  
Infrastructure (Docker, **Bicep IaC**, Azure Container Apps, Key Vault, Application Insights)  
CI/CD (GitHub Actions – see § 4) Auth (Auth0)

### 2.3  Cost Profile
| State | Data Layer | Compute Layer | Monthly Total |
| --- | --- | --- | --- |
| **Active** | $15-25 | $35-50 | **$50-75** |
| **Paused** | $15-25 | $0 | **$15-25** |

---
## 3  Infrastructure as Code (Bicep)
Essential templates (all under `infrastructure/bicep/`):
1. `pathfinder-single-rg.bicep` – legacy always-on option.  
2. `persistent-data.bicep` – data layer.  
3. `compute-layer.bicep` – compute layer (references data layer).

All templates use globally unique names via `uniqueString()`.

---
## 4  CI/CD Workflows (GitHub Actions)
| Workflow | Purpose |
| --- | --- |
| `ci-cd-pipeline.yml` | Build & deploy apps to Container Apps |
| `infrastructure-deploy.yml` | Deploy Bicep templates (supports two-layer model) |
| `pause-resume.yml` | Pause/Resume compute layer, deploy data layer |

### 4.1  Required Repository Secrets
`AZURE_CREDENTIALS`, `SQL_ADMIN_USERNAME`, `SQL_ADMIN_PASSWORD`, `OPENAI_API_KEY`  
_Optional (pause/resume):_ `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `LLM_ORCHESTRATION_URL`, `LLM_ORCHESTRATION_API_KEY`.

---
## 5  Operational Commands (Scripts)
```bash
# One-time data layer
./scripts/deploy-data-layer.sh

# Resume full environment (compute layer)
./scripts/resume-environment.sh

# Pause to save cost
./scripts/pause-environment.sh

# Complete manual deployment (all-in-one)
./scripts/complete-deployment.sh
```

---
## 6  Open Tasks (as of June 15 2025)
### Completed (June 15 2025)
✔ Implemented `/trips/sample` API endpoint to support Golden-Path onboarding.  
✔ **CRITICAL**: Fixed CSRF/CORS compatibility issues - production blocker resolved.  
✔ **CRITICAL**: Resolved database migration conflicts and persistence issues.  
✔ Enhanced sample trip generation with realistic data and decision scenarios.  
✔ Added security permission guards to test endpoints.  
✔ Enabled CSRF protection with CORS compatibility mode.  

### In-Progress
1. ~~Add Container Registry resource to `compute-layer.bicep`~~ ✔ Already exists - verified in template.  
2. Configure email service (SendGrid) for notifications and invitations.  
3. Set up monitoring alerts and health check endpoints.  

### Planned
4. Refactor CI/CD for efficiency:  
   • Single reusable composite action for Docker build & push  
   • Matrix strategy for backend / frontend tests  
   • Cache dependencies to cut build time by >40 %  
5. Final pipeline validation and SLA alerting integration.  
6. Complete frontend navigation restoration and accessibility improvements.  

---
## 7  Contact / Handoff
All infrastructure fixes are committed to `main`.  
Blocking issues: Container Registry & SQL password policy.  
Next focus: finish infrastructure deployment → validate CI/CD → document auto-pause scheduling.  

---
© Pathfinder 2025 – Licensed under the project LICENSE.
