# SIAD Copy Quick Reference

**Last Updated:** 2026-03-03
**For:** All Agents - Quick access to approved copy

---

## Value Proposition (One-Liners)

### Technical
**SIAD detects infrastructure acceleration that violates expected world dynamics under environmental normalization.**

### Simplified
**SIAD finds infrastructure changes that aren't explained by weather or seasonal patterns.**

### Current Tagline
**"Detect what matters, ignore what doesn't"**
*(Pending team vote - see `/docs/VALUE_PROP.md` for alternatives)*

---

## 30-Second Pitch (Mixed Audience)

SIAD is an AI system that detects infrastructure changes in satellite imagery. Unlike simple change detection, SIAD understands how regions normally evolve—including seasonal patterns and weather effects. It highlights deviations that matter: new construction, activity surges, and structural acceleration. Analysts get ranked detections with confidence scores and explanations, dramatically reducing false positives from agriculture, floods, and vegetation cycles.

---

## Key Terminology (Top 10)

| Term | One-Line Definition | When to Use |
|------|---------------------|-------------|
| **World Model** | AI that learns how regions normally evolve | Explaining core technology |
| **Residual** | Difference between predicted and observed | Describing detection metric |
| **Environmental Normalization** | Predicting with neutral weather to isolate structural changes | Explaining key differentiator |
| **Structural Acceleration** | Persistent infrastructure change (2+ months) | Describing high-priority detections |
| **Activity Surge** | Short-term increase in nightlights/activity | Describing temporary detections |
| **Counterfactual** | Prediction under hypothetical conditions | Explaining scenario analysis |
| **Hotspot** | Cluster of high-residual tiles (3+ tiles) | Referring to detection units |
| **Confidence** | Model certainty (high/medium/low) | Describing detection reliability |
| **Onset** | First month detection appears | Timeline discussions |
| **Modality** | Type of satellite data (SAR/optical/lights) | Attribution analysis |

*Full glossary: `/src/content/glossary.json`*

---

## Common UI Copy

### Buttons (Most Used)
- **Primary CTA:** "View Details"
- **Export:** "Export GeoJSON"
- **Reset:** "Reset Filters"
- **Toggle:** "Normalize Weather"

### Loading States
- Initial: "Loading hotspots..."
- Computation: "Computing residuals... (Est. 3 seconds)"
- Export: "Exporting 47 hotspots..." *(dynamic count)*

### Error Messages (Most Common)
- **No Results:** "No hotspots detected in selected time period. Try adjusting your filters."
- **Tile Error:** "Tile 'tile_999' not found. Try selecting a valid tile from the list."
- **Network:** "Could not connect to SIAD API. Check your network connection and try again."

*Full catalog: `/docs/UI_COPY.csv`*

---

## Confidence Levels

| Level | Badge | When to Use | Color |
|-------|-------|-------------|-------|
| **High** | High | 3+ months persistence, strong signal | Green |
| **Medium** | Medium | 2 months persistence, moderate signal | Yellow |
| **Low** | Low | 1 month or weak signal | Gray |

---

## Alert Types

| Type | Description | Typical Duration | Primary Modality |
|------|-------------|------------------|------------------|
| **Structural Acceleration** | Permanent infrastructure change | 3+ months | SAR (radar) |
| **Activity Surge** | Temporary activity increase | <3 months | VIIRS (nightlights) |

---

## Baseline Comparisons

| Baseline | Definition | What It Shows |
|----------|------------|---------------|
| **Persistence** | Assumes no change from last month | SIAD learns dynamics, not just repetition |
| **Seasonal** | Assumes same pattern as last year | SIAD detects infrastructure beyond seasonal cycles |

---

## Messaging Do's and Don'ts

### DO ✅
- Use precise numbers: "Score: 0.82"
- Show duration: "Detected for 4 consecutive months"
- Indicate confidence: "High confidence structural acceleration"
- Reference baselines: "24% better than persistence"
- Active voice: "Detected 47 hotspots"

### DON'T ❌
- Use marketing fluff: "revolutionary," "game-changing"
- Promise pixel precision (we work at 2.56 km tile scale)
- Claim actor identification or intent inference
- Imply causality: weather causing construction
- Vague qualifiers: "High score" without numbers

---

## Common Objections & Responses

### "This is just fancy change detection"
**Response:** Traditional change detection compares pixels. SIAD predicts how regions should evolve under observed conditions, then flags deviations from expected dynamics. This eliminates false positives from predictable patterns.

### "Weather normalization sounds like magic"
**Response:** It's counterfactual modeling. We train on 36 months where we observe weather and outcomes. When we predict under neutral weather (rain = 0, temp = 0), we're asking: "What would this look like without weather stress?" If reality diverges, it's not weather-driven.

### "How accurate is it?"
**Response:** SIAD reduces false positives, not maximizes recall. It outperforms baselines on normal patterns while flagging known events. We provide confidence scores so analysts calibrate their trust.

*Full objection handling: `/docs/VALUE_PROP.md`*

---

## Audience Tailoring

### For Geospatial Analysts
- Emphasize: Latent space residuals, cosine distance, JEPA-style encoders
- Highlight: Reproducibility (UV deps, deterministic seeds)
- Show: Modality attribution (SAR vs. optical vs. lights)

### For Intelligence Managers
- Emphasize: Ranked detections reduce review time
- Highlight: Confidence scoring enables prioritization
- Show: Auto-generated explanations

### For Executives
- Emphasize: Signal-to-noise improvement
- Highlight: Only see changes that matter
- Show: Time savings (days to hours)

---

## Date/Time Formats

| Context | Format | Example |
|---------|--------|---------|
| Timeline labels | Short month + year | Jan 2024 |
| Data exports | ISO date | 2024-01-15 |
| Relative time | Time ago | 2 months ago |
| Date range | Month range | Jan 2024 - Dec 2024 |

---

## Number Formats

| Type | Format | Example |
|------|--------|---------|
| Score | 2 decimal places | 0.82 |
| Percentage | Integer % | 24% |
| Count | Integer with label | 47 hotspots |
| Coordinates | 4 decimal places | 37.7599, -122.3894 |
| Duration | Integer + months | 4 months |

---

## File Locations

| Asset | Path | Format |
|-------|------|--------|
| Full Value Prop | `/docs/VALUE_PROP.md` | Markdown |
| Glossary | `/src/content/glossary.json` | JSON |
| UI Copy | `/docs/UI_COPY.csv` | CSV |
| Summary | `/docs/WEEK1_COPY_DELIVERABLES.md` | Markdown |
| This Reference | `/docs/COPY_QUICK_REFERENCE.md` | Markdown |

---

## Integration Examples

### Tooltip (TypeScript)
```typescript
import glossary from '@/content/glossary.json';

<Tooltip>
  <TooltipTrigger>Residual</TooltipTrigger>
  <TooltipContent>
    <p className="font-bold">{glossary.residual.term}</p>
    <p>{glossary.residual.long}</p>
  </TooltipContent>
</Tooltip>
```

### Error Message (Dynamic)
```typescript
const tileError = (tileId: string, availableTiles: string[]) => ({
  title: "Tile not found",
  message: `Tile '${tileId}' doesn't exist in the database.`,
  suggestion: `Available tiles: ${availableTiles.slice(0, 5).join(', ')}...`
});
```

### Loading State (Dynamic Count)
```typescript
const exportMessage = (count: number) =>
  `Exporting ${count} hotspot${count !== 1 ? 's' : ''}...`;
```

---

## Contact

**Questions about copy?** See full documentation in `/docs/VALUE_PROP.md`
**Need new UI text?** Check `/docs/UI_COPY.csv` first, then request addition
**Glossary additions?** Propose to Agent 6 with short + long definitions
**Tone questions?** Reference "Messaging Do's and Don'ts" above

---

**Quick Reference Version:** 1.0
**Next Update:** After tagline selection (Week 1 Friday)
