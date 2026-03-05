# SIAD Agent Team - Coordination Hub

**Project:** SIAD Demo v2.0 (Latent Residual Detection)
**Timeline:** 3-week MVP → 6-week Full → 8+ week Polished
**Approach:** Phased, parallel development

---

## 🎯 Mission

Rebuild SIAD demo to work entirely in latent space (no decoder), focusing on:
- Environmental normalization (neutral weather)
- Baseline comparisons (persistence, seasonal)
- Analyst-focused UI for infrastructure detection
- Mixed audience (technical + business stakeholders)

---

## 👥 Agent Team

| Agent | Role | Primary Focus | Contact |
|-------|------|---------------|---------|
| **Agent 1** | Architecture | Detection pipeline, storage, baselines | [AGENT_1_ARCHITECTURE.md](./AGENT_1_ARCHITECTURE.md) |
| **Agent 2** | API/Backend | FastAPI endpoints, model services | [AGENT_2_API_BACKEND.md](./AGENT_2_API_BACKEND.md) |
| **Agent 3** | Design | Anduril/Palantir aesthetic, components | [AGENT_3_DESIGN.md](./AGENT_3_DESIGN.md) |
| **Agent 4** | Frontend | React implementation, visualizations | [AGENT_4_FRONTEND.md](./AGENT_4_FRONTEND.md) |
| **Agent 5** | UX/Interaction | User flows, accessibility, testing | [AGENT_5_UX.md](./AGENT_5_UX.md) |
| **Agent 6** | Copy/Content | Messaging, tooltips, documentation | [AGENT_6_COPY.md](./AGENT_6_COPY.md) |

---

## 📅 Timeline & Milestones

### **Week 1: Foundation**
**Goal:** Architecture defined, API spec implemented, design system created

**Agent 1 (Architecture):**
- [ ] Baseline comparison module
- [ ] Storage schema (HDF5)
- [ ] Data flow diagram

**Agent 2 (API/Backend):**
- [ ] Extend inference service
- [ ] Implement `/api/detect/residuals`
- [ ] Implement `/api/hotspots`

**Agent 3 (Design):**
- [ ] Design system (colors, typography, spacing)
- [ ] Component library (5 core components)
- [ ] Dashboard mockup

**Agent 4 (Frontend):**
- [ ] Project setup + dependencies
- [ ] API service layer
- [ ] Design system tokens

**Agent 5 (UX):**
- [ ] User flow mapping
- [ ] Interaction requirements
- [ ] Keyboard shortcuts

**Agent 6 (Copy):**
- [ ] Value proposition + taglines
- [ ] Glossary (tooltips)
- [ ] UI microcopy spreadsheet

**🎯 Milestone: Architecture Review (Friday EOD)**
- All agents present their Week 1 work
- Validate API contract
- Confirm design direction

---

### **Week 2: Implementation**
**Goal:** Core components functional, API integrated, first working prototype

**Agent 1:**
- [ ] Spatial clustering algorithm
- [ ] Batch inference pipeline design
- [ ] Caching strategy

**Agent 2:**
- [ ] Pre-computation script
- [ ] HDF5 storage service
- [ ] Baseline endpoints

**Agent 3:**
- [ ] Hotspot detail screen mockup
- [ ] Interaction state variations
- [ ] Empty/error state designs

**Agent 4:**
- [ ] Token heatmap component
- [ ] Hotspot list component
- [ ] Timeline chart component
- [ ] Environmental controls

**Agent 5:**
- [ ] Feedback mechanisms
- [ ] Accessibility checklist
- [ ] Empty/loading/error states

**Agent 6:**
- [ ] Error messages catalog
- [ ] Auto-generated explanation templates
- [ ] Empty state copy

**🎯 Milestone: Working Prototype (Friday EOD)**
- Agent 2 + Agent 4 demo functional API + UI
- Agent 3 presents complete design system
- Agent 5 conducts first usability review

---

### **Week 3: Integration & Polish**
**Goal:** MVP complete, tested, documented

**Agent 1:**
- [ ] Integration testing
- [ ] Performance profiling
- [ ] Optimization recommendations

**Agent 2:**
- [ ] Heatmap endpoint
- [ ] Export endpoints (GeoJSON/CSV)
- [ ] Performance optimization

**Agent 3:**
- [ ] Responsive layout (tablet breakpoint)
- [ ] Design handoff document
- [ ] Asset exports (icons, etc.)

**Agent 4:**
- [ ] Dashboard page complete
- [ ] Hotspot detail page complete
- [ ] State management (Zustand)
- [ ] Component tests

**Agent 5:**
- [ ] User testing (3-5 sessions)
- [ ] Onboarding flow design
- [ ] Help system design

**Agent 6:**
- [ ] Help documentation (Markdown)
- [ ] README updates
- [ ] FAQ (mixed audience)

**🎯 Milestone: MVP Demo (Friday EOD)**
- Full end-to-end demo
- All agents present final deliverables
- Validate against success criteria

---

## 🔗 Dependencies

### Critical Path
```
Week 1:
  Agent 1 (storage schema) → Agent 2 (data services)
  Agent 3 (design system) → Agent 4 (implementation)

Week 2:
  Agent 2 (API endpoints) → Agent 4 (integration)
  Agent 3 (components) → Agent 4 (implementation)

Week 3:
  Agent 2 + Agent 4 (working app) → Agent 5 (user testing)
```

### Cross-Agent Dependencies

**Agent 2 ← Agent 1:**
- Needs: Storage schema, baseline module
- When: Week 1 Thursday

**Agent 4 ← Agent 2:**
- Needs: Working API endpoints
- When: Week 2 Monday

**Agent 4 ← Agent 3:**
- Needs: Component designs, design tokens
- When: Week 1 Friday

**Agent 5 ← Agent 4:**
- Needs: Working prototype for testing
- When: Week 2 Friday

**Agent 4 ← Agent 6:**
- Needs: UI copy, tooltip content
- When: Week 2 Monday

---

## 📞 Communication

### Daily Standups (Async)
Post in shared channel:
1. What did you complete yesterday?
2. What are you working on today?
3. Any blockers?

### Sync Points

**Monday Morning:**
- Week kickoff (30 min)
- Review dependencies for the week
- Clarify any blockers from previous week

**Wednesday Mid-Week:**
- Integration check (30 min)
- Agent 2 + Agent 4 sync on API
- Agent 3 + Agent 4 sync on design

**Friday EOD:**
- Milestone demo (1 hour)
- All agents show progress
- Plan for next week

---

## 📁 Shared Resources

### Documentation
- `/docs/API_SPEC.md` - API contract (Agent 2 maintains)
- `/docs/ARCHITECTURE_V2.md` - System architecture (Agent 1 maintains)
- `/docs/DESIGN_SYSTEM.md` - Design tokens (Agent 3 creates)
- `/docs/UX_SPEC.md` - Interaction patterns (Agent 5 creates)

### Code
- `/src/siad/detect/` - Detection modules (Agent 1 + Agent 2)
- `/siad-command-center/api/` - Backend (Agent 2)
- `/siad-command-center/frontend/` - Frontend (Agent 4)

### Design
- Figma link: [To be added by Agent 3]
- Design exports: `/siad-command-center/frontend/public/designs/`

### Content
- `/src/content/` - Copy, glossary, templates (Agent 6)
- `/docs/HELP.md` - User documentation (Agent 6)

---

## ✅ Success Criteria

### MVP (Week 3)

**Technical:**
- [ ] API serves residuals in < 2s (uncached)
- [ ] Frontend renders 16×16 heatmap smoothly
- [ ] 10+ demo tiles with pre-computed residuals
- [ ] Environmental normalization toggle functional
- [ ] At least 1 baseline comparison working

**User Experience:**
- [ ] Non-technical user understands "what changed" in < 30s
- [ ] Technical user can drill into token-level details
- [ ] All key concepts have tooltip explanations
- [ ] Empty/loading/error states polished

**Validation:**
- [ ] Agricultural noise does NOT dominate top 10 hotspots
- [ ] At least 1 known SF infrastructure change ranks in top 10
- [ ] Model residuals show spatial clustering (not random)
- [ ] Passes basic accessibility checks (color contrast, keyboard nav)

---

## 🚨 Escalation

**Blocker Protocol:**
1. Post in shared channel immediately
2. Tag dependent agents
3. If not resolved in 4 hours → escalate to team lead
4. If critical → schedule sync call

**Examples of blockers:**
- Agent 2: Can't implement endpoint without Agent 1's storage schema
- Agent 4: Can't build component without Agent 3's design spec
- Agent 5: Can't test without Agent 4's working prototype

---

## 🎓 Onboarding New Agents

1. Read your agent brief (`AGENT_X_*.md`)
2. Review shared docs (`/docs/API_SPEC.md`, etc.)
3. Check dependencies (who do you need? who needs you?)
4. Join shared channel and introduce yourself
5. Post first standup update

---

## 📊 Progress Tracking

Use GitHub Projects or similar:
- **Backlog:** All tasks from agent briefs
- **In Progress:** Currently working on
- **Blocked:** Waiting on dependency
- **Review:** Ready for feedback
- **Done:** Completed and validated

---

## 🔧 Tools

**Shared:**
- GitHub: Code + docs
- Figma: Design (Agent 3)
- Slack/Discord: Communication
- Google Docs: Collaborative docs (UX specs, copy)

**Per Agent:**
- Agent 1: Python, PyTorch, HDF5
- Agent 2: FastAPI, Python, HDF5, pytest
- Agent 3: Figma, design tools
- Agent 4: React, TypeScript, Vite, Plotly.js
- Agent 5: Figma, Miro, usability testing tools
- Agent 6: Markdown, Google Docs, copywriting tools

---

## 📖 Quick Links

- [API Specification](../docs/API_SPEC.md)
- [System Architecture](../docs/ARCHITECTURE_V2.md) (when created by Agent 1)
- [PRD](../SIAD_DEMO_PRD.md) (original requirements)
- [Model Documentation](../docs/MODEL.md)
- [Existing Codebase](../src/siad/)

---

**Last Updated:** 2026-03-03
**Next Review:** End of Week 1

---

## 🚀 Getting Started

**Each agent should:**
1. Read your brief (`AGENT_X_*.md`)
2. Review dependencies
3. Set up your tools
4. Start Week 1 Task 1
5. Post daily updates

**Let's build!** 💪
