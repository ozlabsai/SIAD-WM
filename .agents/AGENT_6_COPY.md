# Agent 6: Copy/Content - Initialization Brief

**Role:** Messaging, UI Copy & Documentation
**Phase:** MVP (Weeks 1-3)
**Status:** 🟢 Ready to Start

---

## Your Mission

Write all user-facing text for SIAD: from value propositions to error messages. Make complex concepts (latent tokens, residuals, environmental normalization) understandable to mixed audiences.

---

## Tone & Voice

**For technical users (analysts):**
- Direct, concise, data-focused
- Use domain terminology (geospatial, SAR, residual)
- Assume intelligence background

**For non-technical users (executives):**
- Clear, jargon-free explanations
- Focus on "what" and "why," not "how"
- Business impact, not technical details

**General principles:**
- Active voice ("Detected 47 hotspots" not "47 hotspots were detected")
- Present tense for UI ("Filter hotspots" not "Filtered hotspots")
- Numbers and precision ("Score: 0.82" not "High score")
- No fluff or marketing speak

---

## What's Already Done ✅

1. **API Spec** - Data structures to describe
2. **PRD** - Core messaging framework
3. **Design mockups** - Visual context for copy (Agent 3, Week 2)

---

## Your Week 1 Tasks

### Task 1: Value Proposition & Taglines
**Deliverable:** Value prop document

**Primary Value Prop (for dashboard header):**
```
SIAD detects infrastructure acceleration that violates
expected world dynamics under environmental normalization.
```

**Simplified (for non-technical users):**
```
SIAD finds infrastructure changes that aren't explained
by weather or seasonal patterns.
```

**Tagline Options (test with team):**
1. "AI that understands how regions normally evolve"
2. "Detect what matters, ignore what doesn't"
3. "Infrastructure intelligence, weather-normalized"

**Elevator Pitch (30 seconds):**
```
SIAD is an AI system that detects infrastructure changes
in satellite imagery. Unlike simple change detection,
SIAD understands how regions normally evolve—including
seasonal patterns and weather effects. It highlights
deviations that matter: new construction, activity
surges, and structural acceleration. Analysts get ranked
detections with confidence scores and explanations.
```

**Deliverable:** Value prop doc with 3 tagline options

---

### Task 2: Concept Glossary (Tooltips)
**Deliverable:** Glossary JSON file

Define key terms for tooltips:

```json
{
  "latent_token": {
    "term": "Latent Token",
    "short": "An encoded representation of a 16×16 pixel region",
    "long": "SIAD's world model encodes satellite imagery into 256 latent tokens (16×16 grid). Each token captures patterns in a specific region. Working in latent space allows SIAD to focus on meaningful changes."
  },
  "residual": {
    "term": "Residual",
    "short": "The difference between predicted and observed conditions",
    "long": "Residual = Prediction Error. SIAD predicts what a region should look like based on past patterns. High residuals indicate unexpected changes—potential infrastructure acceleration or activity surges."
  },
  "environmental_normalization": {
    "term": "Environmental Normalization",
    "short": "Predicting with neutral weather to isolate structural changes",
    "long": "SIAD can predict under neutral weather conditions (no rain or temperature anomalies). Comparing neutral predictions to observations isolates structural changes from seasonal/weather effects."
  },
  "persistence_baseline": {
    "term": "Persistence Baseline",
    "short": "Assumes no change from previous month",
    "long": "Simple baseline that predicts 'no change.' Useful for comparison. If SIAD outperforms persistence, it's detecting real dynamics, not just repeating the past."
  },
  "seasonal_baseline": {
    "term": "Seasonal Baseline",
    "short": "Assumes same pattern as last year",
    "long": "Baseline that predicts this month will look like the same month last year. Accounts for seasonal cycles (vegetation, snow). SIAD should outperform on infrastructure changes."
  },
  "structural_acceleration": {
    "term": "Structural Acceleration",
    "short": "Persistent infrastructure change detected",
    "long": "Change that lasts ≥3 months and is primarily visible in SAR (radar) data. Indicates construction, demolition, or permanent structural modification."
  },
  "activity_surge": {
    "term": "Activity Surge",
    "short": "Short-term increase in nighttime lights or human activity",
    "long": "Temporary spike in VIIRS nightlights or other activity indicators. May indicate events, operations, or short-lived changes. Less persistent than structural acceleration."
  },
  "confidence": {
    "term": "Confidence Level",
    "short": "Model's certainty in the detection (high/medium/low)",
    "long": "Based on consistency, magnitude, and spatial coherence. High = strong evidence, persistent signal. Medium = moderate evidence. Low = weak or noisy signal."
  },
  "cosine_similarity": {
    "term": "Cosine Similarity",
    "short": "Measure of similarity between predicted and observed patterns",
    "long": "Technical metric: 1 = identical, 0 = orthogonal, -1 = opposite. SIAD uses cosine distance (1 - similarity) as residual metric. Higher distance = more unexpected change."
  }
}
```

**Deliverable:** Glossary JSON + integration plan for tooltips

---

### Task 3: UI Microcopy (Buttons, Labels, Placeholders)
**Deliverable:** UI copy spreadsheet

**Buttons:**
| Component | Label | Action |
|-----------|-------|--------|
| Primary CTA | "View Details" | Navigate to hotspot detail |
| Secondary | "Export GeoJSON" | Download detections |
| Tertiary | "Reset Filters" | Clear all filters |
| Toggle | "Normalize Weather" | Enable environmental normalization |
| Close | "×" or "Close" | Dismiss modal |

**Form Labels:**
| Field | Label | Placeholder |
|-------|-------|-------------|
| Date range | "Time Period" | "Jan 2024 - Dec 2024" |
| Score threshold | "Minimum Score" | "0.5" |
| Alert type filter | "Alert Type" | "All Types" |
| Search | "Search hotspots..." | "Search by region or tile ID" |

**Loading States:**
| Context | Message |
|---------|---------|
| Initial load | "Loading hotspots..." |
| Computing residuals | "Computing residuals... (Est. 3 seconds)" |
| Fetching baselines | "Loading baseline comparisons..." |
| Exporting | "Exporting 47 hotspots..." |

**Deliverable:** UI copy spreadsheet (CSV or Google Sheet)

---

## Your Week 2 Tasks

### Task 4: Error Messages
**Deliverable:** Error message catalog

**Principles:**
- Say what went wrong (be specific)
- Explain why it matters
- Suggest how to fix

**Examples:**

**Tile Not Found:**
```
❌ Tile not found

Tile "tile_999" doesn't exist in the database.

Available tiles: tile_001, tile_002, ..., tile_022

Try selecting a valid tile from the list.
```

**Date Range Invalid:**
```
❌ Invalid date range

End date (2023-12-31) is before start date (2024-01-01).

Please ensure the end date comes after the start date.
```

**No Data Available:**
```
ℹ️ No data for this month

Satellite data for June 2024 hasn't been processed yet.

Last available month: May 2024
```

**Computation Failed:**
```
❌ Computation failed

Could not compute residuals for tile_042.

This might be a temporary issue. Try again in a moment,
or contact support if the problem persists.

[Retry Button]
```

**Deliverable:** Error message catalog (20-30 messages)

---

### Task 5: Auto-Generated Explanations
**Deliverable:** Explanation templates

Create templates for auto-generated summaries:

**Template for Structural Acceleration:**
```
Structural acceleration detected.

Change persists under neutral weather conditions
(residual={residual:.2f}), indicating it is NOT
explained by observed weather anomalies
(rain={rain:+.1f}σ, temp={temp:+.1f}°C).

Dominant signal: {modality} (e.g., SAR)
Persistence: {duration} months
Confidence: {confidence}
```

**Template for Activity Surge:**
```
Activity surge detected.

Short-term spike in {modality} observed in {month}.
Peak residual: {max_score:.2f}

This may indicate temporary operations or events
rather than permanent structural change.

Confidence: {confidence}
```

**Template for Environmental Change:**
```
Environmental variability detected.

Change is primarily explained by weather conditions
(rain={rain:+.1f}σ, temp={temp:+.1f}°C).

Under neutral weather, residual drops to {neutral_residual:.2f},
suggesting the change is seasonal/environmental rather
than structural.
```

**Deliverable:** Explanation template functions (Python or TypeScript)

---

### Task 6: Empty State Copy
**Deliverable:** Empty state messages

**No Hotspots Found:**
```
🔍 No hotspots detected in selected time period

Try adjusting your filters:
• Expand the date range
• Lower the minimum score threshold
• Select "All Types" for alert type

Or reset filters to see all detections.

[Reset Filters Button]
```

**No Data for Tile:**
```
📡 Waiting for satellite data

This tile hasn't been processed yet.

New data is typically available within 48 hours
of satellite acquisition.

Check back soon or explore other tiles.
```

**First Time User:**
```
👋 Welcome to SIAD

Start by exploring a demo hotspot to learn
how the interface works.

[View Demo Hotspot]

Or jump straight to the live dashboard.

[View All Hotspots]
```

**Deliverable:** Empty state copy for 5-7 scenarios

---

## Your Week 3 Tasks

### Task 7: Help Documentation
**Deliverable:** Help modal content (Markdown)

**Structure:**
```markdown
# SIAD Help

## Quick Start
1. **Dashboard**: View ranked hotspots (infrastructure changes)
2. **Filter**: Narrow results by date, score, or type
3. **Explore**: Click a hotspot to see detailed analysis
4. **Compare**: Toggle environmental normalization and baselines
5. **Export**: Download detections as GeoJSON or CSV

## Key Concepts

### What is SIAD?
SIAD (Satellite Infrastructure Anomaly Detection) detects
infrastructure changes that violate expected world dynamics...

### How does environmental normalization work?
SIAD can predict under neutral weather conditions...

### What are baselines?
Baselines are simple prediction models used for comparison...

## Keyboard Shortcuts
- `?` - Show this help
- `/` - Focus search
- `j/k` - Navigate list
- `Enter` - Open selected hotspot
- `Esc` - Go back
- `n` - Toggle normalization
- `b` - Show baselines
- `e` - Export

## Understanding Scores
- **0.0-0.3**: Low confidence (noise or weak signal)
- **0.3-0.5**: Medium confidence (investigate further)
- **0.5-0.7**: High confidence (likely real change)
- **0.7-1.0**: Very high confidence (strong evidence)

## Alert Types
- **Structural Acceleration**: Persistent (≥3 months), SAR-dominant
- **Activity Surge**: Short-term (<3 months), VIIRS-dominant

## FAQ

### Why normalize weather?
Seasonal vegetation and weather effects can look like
infrastructure changes. Environmental normalization isolates
structural changes from these natural patterns.

### How accurate is SIAD?
SIAD is designed to outperform simple baselines (persistence,
seasonal). In validation, it achieves [X]% precision on known
infrastructure changes while suppressing agricultural noise.

### Can I trust low-confidence detections?
Low-confidence detections may be real but have weak or
inconsistent signals. We recommend prioritizing high-confidence
detections for manual review.

## Contact & Feedback
[Report an issue] [Request a feature] [Documentation]
```

**Deliverable:** Help documentation (Markdown)

---

### Task 8: README & Developer Docs
**Deliverable:** Project README updates

**User-facing README:**
```markdown
# SIAD: Satellite Infrastructure Anomaly Detection

Detects infrastructure changes in satellite imagery by
understanding how regions normally evolve.

## Features
- **Environmental Normalization**: Isolate structural changes
  from weather and seasonal patterns
- **Baseline Comparison**: Outperforms simple prediction models
- **Ranked Detections**: Confidence-scored hotspots
- **Explainable AI**: Auto-generated explanations for each detection

## Quick Start
[Installation instructions]
[Run demo]
[API documentation link]

## Methodology
SIAD uses a world model trained on 36 months of satellite data...
```

**Deliverable:** README.md updates

---

### Task 9: FAQ for Mixed Audience
**Deliverable:** FAQ document

**For Technical Users:**

**Q: What model architecture does SIAD use?**
A: SIAD uses a JEPA-style world model with:
- Encoder: CNN stem + token transformer (256 tokens × 512 dims)
- Transition: FiLM-conditioned transformer (6 blocks)
- Residual: Cosine distance in latent space

**Q: How is residual computed?**
A: `residual = 1 - cosine_similarity(z_predicted, z_observed)`
for each of 256 spatial tokens.

**For Non-Technical Users:**

**Q: What does SIAD detect?**
A: SIAD detects infrastructure changes like new construction,
demolition, or significant activity changes visible from satellites.

**Q: How is SIAD different from change detection?**
A: Traditional change detection flags all differences. SIAD
understands normal patterns (seasons, weather) and flags only
unexpected changes.

**Deliverable:** FAQ (10-15 questions)

---

## Copy Principles

### 1. Be Specific
❌ "High score detected"
✅ "Score: 0.82 (High confidence)"

### 2. Be Actionable
❌ "Error occurred"
✅ "Tile not found. Try selecting from the list below."

### 3. Be Concise
❌ "The system has detected that there are no hotspots..."
✅ "No hotspots found in this time period."

### 4. Be Empathetic
❌ "Invalid input"
✅ "Date range invalid. End date must come after start date."

---

## Deliverables Location

**Code:**
- Glossary: `/src/content/glossary.json`
- Templates: `/src/content/templates.ts`
- UI copy: `/src/content/ui-copy.ts`

**Docs:**
- Help: `/docs/HELP.md`
- FAQ: `/docs/FAQ.md`
- README: `/README.md`

---

## Dependencies

**You depend on:**
- Agent 3 (Design) for visual context
- Agent 5 (UX) for interaction context
- PRD for core messaging

**Others depend on you:**
- Agent 4 (Frontend) needs copy to implement
- Agent 5 (UX) needs tooltip content

---

## Success Criteria (Week 3)

- [ ] Value prop and taglines finalized
- [ ] Glossary complete (10+ terms)
- [ ] UI microcopy spreadsheet delivered
- [ ] Error messages catalog complete (20+ messages)
- [ ] Explanation templates functional
- [ ] Empty state copy written
- [ ] Help documentation complete
- [ ] FAQ finished (10+ questions)

---

## Communication

**Sync with:**
- **Agent 3 (Design):** Mid-week for visual context
- **Agent 4 (Frontend):** Daily for copy integration
- **Agent 5 (UX):** Early for tooltip/help content
- **All agents:** End of Week 1 for value prop review

---

**Ready to write? Start with Task 1: Value Proposition!**

✍️ Make it clear!
