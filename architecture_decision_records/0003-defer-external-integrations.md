# ADR 0003: Defer External Data Integration Features

**Status:** Accepted  
**Date:** November 2, 2025  
**Decision Makers:** Product & Engineering Leadership  
**Context:** MCP (Model Context Protocol) integration evaluation

---

## Context

During Phase 1 development, we evaluated incorporating MCP (Model Context Protocol) to integrate external travel data sources (flights, hotels, weather, events, etc.) into the Pathfinder Assistant.

### Original Proposal
- Add MCP gateway service for external API orchestration
- Integrate 6-8 external data providers (flights, hotels, weather, maps, events, transport)
- Real-time price monitoring and disruption management
- Booking workflow orchestration

### Estimated Impact
- **Complexity Increase:** 300-400%
- **Timeline Impact:** 6-12 months
- **Cost Impact:** $500-2000/month + API fees
- **Architecture Impact:** Conflicts with serverless cost optimization (70% savings)

---

## Decision

**We will defer all external data integrations until Phase 5+ and only after explicit user validation.**

### What We Will NOT Build (Strategic Non-Goals)
1. ❌ Booking aggregation or price monitoring
2. ❌ Real-time disruption management
3. ❌ Flight/hotel search and comparison
4. ❌ Transactional booking workflows
5. ❌ Integration with travel booking platforms

### What We MAY Consider (Phase 5+, User-Validated Only)
After successfully launching Phases 1-4 and validating core collaboration features:

**Minimal Read-Only Context Enrichment:**
- ✅ Weather forecasts (OpenWeatherMap, $0-10/month)
- ✅ Local events feed (PredictHQ, $50-100/month)
- ✅ Basic place information (Google Places, capped usage)

**Design Constraints (If Implemented):**
- Read-only queries only
- Aggressive caching (24hr+ TTL)
- Graceful degradation (never blocks core features)
- Cost-capped at $100/month maximum
- Maintains serverless architecture advantages

---

## Rationale

### 1. **Mission Alignment**
Our differentiation is **family-atomic collaboration and AI-powered consensus**, not booking aggregation.

**Problem We Solve:** Multi-family coordination paralysis  
**Problem We Don't Solve:** Finding/booking travel services

### 2. **Competitive Positioning**
We are **not** competing with:
- Booking aggregators (Kayak, Expedia, Hopper)
- Price monitoring platforms ($700M+ funding, 1000+ employees)
- Travel marketplaces (Booking.com ecosystem)

**Our Lane:** Collaboration platform that helps families make better decisions *before* they book.

### 3. **Architecture Preservation**
Our key technical differentiator is **70% cost savings during idle periods** through:
- Serverless Cosmos DB
- Container Apps scaling to zero
- No persistent connections or polling

External integrations would:
- Require 24/7 monitoring
- Add constant API polling costs
- Prevent scale-to-zero architecture
- Eliminate cost optimization advantage

### 4. **Development Focus**
Current roadmap delivers unique value:
- **Phase 1 (Q1 2025):** AI Assistant, Golden Path Onboarding, Itinerary Generation
- **Phase 2 (Q2 2025):** Magic Polls, Consensus Engine
- **Phase 3 (Q3 2025):** Mobile/PWA optimization
- **Phase 4 (Q4 2025):** Analytics and personalization

External integrations would delay core features by 6-12 months.

### 5. **User Validation Required**
No evidence that users need booking integrations for our collaboration use case. Must validate:
- Do families want weather context in the app?
- Would local events improve decision-making?
- Are restaurant suggestions valuable during planning?

**Validation Approach:** Survey beta users after Phase 2 launch.

---

## Consequences

### Positive
✅ **Maintained Focus:** Deliver core collaboration features faster  
✅ **Cost Optimization:** Preserve 70% infrastructure savings  
✅ **Architecture Simplicity:** No complex API gateway or orchestration  
✅ **Clear Positioning:** Distinct from booking platforms  
✅ **Reduced Risk:** Avoid dependency on 6-8 external services  

### Neutral
🔄 **Future Optionality:** Can add minimal context enrichment in Phase 5+ if validated  
🔄 **Booking Support:** Users can paste booking URLs/confirmations (existing feature)  

### Negative
❌ **No Live Price Data:** AI suggestions won't include real-time pricing  
❌ **No Weather Integration:** No automatic weather-based replanning  
❌ **Manual Context:** Users provide destination details themselves  

**Mitigation:** These are "nice-to-haves" not "must-haves" for core collaboration value. Can be added later if users request.

---

## Implementation

### Immediate (Phase 1-4)
1. ✅ Focus exclusively on current roadmap features
2. ✅ Document strategic non-goals in product specs
3. ✅ Design booking URL fields for user-provided links
4. ✅ Build robust collaboration features without external dependencies

### Future Validation (Post-Phase 4)
1. Survey beta users on context enrichment needs
2. A/B test basic weather/events integration if validated
3. Monitor user requests for external data
4. Evaluate minimal MCP implementation only if clear user demand

### If Pursuing Context Enrichment (Phase 5+)
**Prerequisites:**
- ✅ Phases 1-4 successfully launched
- ✅ Core metrics achieved (85% trip completion, 4+ family participation)
- ✅ Explicit user requests for context features
- ✅ Cost-benefit analysis shows positive ROI

**Implementation Constraints:**
- Maximum $100/month budget
- Read-only APIs only
- 24hr+ caching TTL
- Graceful degradation required
- No impact on core feature reliability

---

## Related Decisions
- [ADR-0001: Adopt Clean Architecture](../architecture_decision_records/0001-adopt-clean-architecture.md)
- [ADR-0002: Unified Cosmos DB Architecture](../architecture_decision_records/0002-adopt-unified-cosmos-architecture.md)

---

## References
- MCP Protocol Specification: https://modelcontextprotocol.io
- PRD Section 1.2: Competitive Positioning
- Tech Spec Section 12.3: Contextual Data Enrichment
- Cost Optimization Strategy: 70% savings during idle periods
