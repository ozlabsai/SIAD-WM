# SIAD Value Proposition & Messaging

**Last Updated:** 2026-03-03
**Status:** Week 1 Deliverable - Ready for Team Review

---

## Primary Value Proposition

### Technical Version (for analysts/engineers)

**SIAD detects infrastructure acceleration that violates expected world dynamics under environmental normalization.**

*Translation:* SIAD uses a world model trained on 36 months of satellite imagery to predict how regions should evolve. By comparing predictions under neutral weather conditions to observed reality, it isolates structural changes from seasonal and environmental patterns. Persistent deviations flag infrastructure acceleration.

### Simplified Version (for executives/non-technical users)

**SIAD finds infrastructure changes that aren't explained by weather or seasonal patterns.**

*Translation:* Satellite imagery shows many changes over time—crops growing, snow melting, floods. SIAD filters out these natural patterns and highlights only the changes that matter: new construction, structural modifications, and activity surges.

---

## Tagline Options

Test these with mixed audiences to determine which resonates best:

### Option 1: Intelligence Focus
**"AI that understands how regions normally evolve"**

*Rationale:* Emphasizes the world model's understanding of normal patterns. Accessible to non-technical audiences while implying sophisticated modeling to technical users.

### Option 2: Signal-to-Noise Focus
**"Detect what matters, ignore what doesn't"**

*Rationale:* Speaks to the core problem: reducing false positives. Short, punchy, problem-focused. Works for all audiences.

### Option 3: Technical Differentiation
**"Infrastructure intelligence, weather-normalized"**

*Rationale:* Highlights the key technical differentiator (environmental normalization) while remaining accessible. Appeals to technical buyers who understand the false positive problem.

**Recommendation:** Test Option 2 first. It's the clearest articulation of value without requiring domain knowledge.

---

## 30-Second Elevator Pitch

**Version 1: Mixed Audience**

SIAD is an AI system that detects infrastructure changes in satellite imagery. Unlike simple change detection, SIAD understands how regions normally evolve—including seasonal patterns and weather effects. It highlights deviations that matter: new construction, activity surges, and structural acceleration. Analysts get ranked detections with confidence scores and explanations, dramatically reducing false positives from agriculture, floods, and vegetation cycles.

**Version 2: Technical Audience**

SIAD is a multi-modal world model trained on 36 months of Sentinel-1 SAR, Sentinel-2 optical, and VIIRS nightlights. It learns spatiotemporal evolution under exogenous stressors—rain and temperature anomalies. By rolling out counterfactual futures under neutral climate scenarios, SIAD isolates persistent structural deviations from seasonal and environmental noise. The system uses modality-specific attribution to classify detections as structural acceleration, activity surges, or environmental variability.

**Version 3: Executive Audience**

Satellite imagery captures everything: crop cycles, snow melt, construction. Traditional systems flag all changes equally, creating thousands of false alarms. SIAD learned what "normal" looks like for each region—including weather patterns and seasons. It only flags changes that persist and can't be explained by natural patterns. This means your analysts focus on real infrastructure changes, not agricultural fields or flood zones.

---

## Core Messaging Framework

### The Problem
- Traditional change detection flags all differences in satellite imagery
- Natural patterns (agriculture, weather, seasons) create overwhelming false positives
- Analysts waste time investigating crop cycles and flood zones
- Critical infrastructure changes get buried in noise

### How SIAD Solves It
- **World model** learns normal spatiotemporal evolution for each region
- **Environmental normalization** predicts under neutral weather conditions
- **Counterfactual rollouts** isolate structural changes from environmental effects
- **Modality attribution** distinguishes structural vs. activity vs. environmental changes

### Key Differentiators
1. **Weather-normalized predictions** - Not available in commercial change detection tools
2. **Multi-modal fusion** - SAR + optical + nightlights for robust detection
3. **Explainable detections** - Auto-generated explanations for each hotspot
4. **Baseline comparison** - Demonstrates improvement over simple prediction models

### What SIAD Provides
- **Ranked hotspots** with confidence scores (high/medium/low)
- **Timeline analysis** showing when acceleration began
- **Before/after thumbnails** across multiple modalities
- **Counterfactual scenarios** to validate structural vs. environmental attribution
- **GeoJSON exports** for integration with existing workflows

---

## Use Cases & Scenarios

### Analyst Workflow
*"An analyst investigating potential infrastructure activity in a 50x50 km region receives 200+ monthly change alerts from traditional systems. With SIAD, they see 12 high-confidence structural acceleration detections—each with explanation, timeline, and multi-modal evidence. Investigation time drops from days to hours."*

### Seasonal False Positive Reduction
*"Agricultural regions show massive NDVI changes every planting season. SIAD understands these patterns and predicts them accurately. Only when SAR shows structural change AND it persists under neutral weather does SIAD flag it—reducing agricultural false positives by 90%."*

### Construction Detection
*"New port construction begins in June. Traditional systems flag it immediately but also flag 50 other 'changes' that are flood patterns and crop cycles. SIAD detects the construction in July (after persistence threshold) and correctly attributes it as 'structural acceleration' with high confidence. The signal stands out clearly."*

---

## Key Metrics & Claims

### Credible Claims
- **Persistent detection:** Only flags changes lasting 2+ months
- **Multi-modal validation:** Structural detections require SAR + optical/lights correlation
- **Weather-aware:** Demonstrates that detections persist under neutral climate scenarios
- **Baseline outperformance:** Shows lower residuals than persistence and seasonal baselines on normal patterns
- **Spatial coherence:** Flags clusters of 3+ tiles, reducing isolated pixel noise

### What NOT to Claim
- Pixel-level precision (we work at 2.56 km tile scale)
- Causal attribution from weather to construction
- Intent inference or actor identification
- Real-time detection (monthly cadence)
- Global coverage (MVP is single AOI)

---

## Audience-Specific Positioning

### For Geospatial Analysts
- Focus on **technical methodology**: latent space residuals, cosine distance, JEPA-style encoders
- Emphasize **reproducibility**: UV dependency locking, deterministic seeds, versioned checkpoints
- Highlight **modality attribution**: Ability to isolate SAR vs. optical vs. lights contributions

### For Intelligence Managers
- Focus on **workflow efficiency**: Ranked detections reduce manual review time
- Emphasize **confidence scoring**: High/medium/low tiers enable prioritization
- Highlight **explainability**: Auto-generated summaries explain each detection

### For Executives/Decision-Makers
- Focus on **signal-to-noise**: Dramatic reduction in false positives
- Emphasize **actionable intelligence**: Only see changes that matter
- Highlight **time savings**: Days to hours for regional analysis

---

## Objection Handling

### "This is just fancy change detection"
**Response:** Traditional change detection compares pixels. SIAD predicts how regions should evolve under observed conditions. The difference: we flag deviations from expected dynamics, not just visual differences. This eliminates false positives from predictable patterns.

### "Weather normalization sounds like magic"
**Response:** It's counterfactual modeling. We train on 36 months of data where we observe weather conditions and outcomes. When we predict under neutral weather (rain anomaly = 0, temp anomaly = 0), we're asking: "What would this region look like without weather stress?" If reality diverges from that neutral prediction, it's not explained by weather.

### "Can you detect [specific thing]?"
**Response:** SIAD detects persistent spatial patterns in multi-modal satellite data. If your target creates lasting changes visible in SAR, optical, or nightlights over 2+ months at ~2.5 km scale, SIAD will likely flag it. We don't guarantee detection of specific entities—we provide persistent deviation signals for analyst review.

### "How accurate is it?"
**Response:** SIAD is designed to reduce false positives, not maximize recall. In validation regions with known construction, it achieves high precision on structural acceleration detections. We measure success by: (1) outperforming baselines on normal patterns, (2) flagging known events, (3) suppressing agricultural/seasonal noise. We provide confidence scores so analysts can calibrate their trust.

---

## Messaging Do's and Don'ts

### DO
- Use precise numbers: "Score: 0.82" not "High score"
- Emphasize persistence: "Detected for 4 consecutive months"
- Highlight multi-modal validation: "SAR and nightlights confirm change"
- Show confidence levels: "High confidence structural acceleration"
- Reference baselines: "Outperforms persistence baseline by 24%"

### DON'T
- Claim pixel-level precision
- Promise detection of specific actors or intent
- Use marketing fluff: "revolutionary," "game-changing"
- Overstate accuracy without caveats
- Imply causal relationships between weather and construction

---

## Testing & Validation

### Recommended Tests
1. **Tagline A/B Test:** Show all three options to 10 mixed-audience users, ask which is clearest
2. **Pitch Test:** Deliver 30-second pitch to non-technical person, ask them to explain back
3. **Value Prop Clarity:** Ask analysts: "Does 'environmental normalization' make sense?" Adjust if not
4. **Objection Handling:** Role-play skeptical buyer scenarios with team

### Success Criteria
- [ ] Non-technical users can explain SIAD's value in their own words
- [ ] Technical users understand the world model approach
- [ ] Tagline resonates with 70%+ of test audience
- [ ] Elevator pitch elicits follow-up questions (not confusion)
- [ ] Objection responses feel credible and non-defensive

---

## Next Steps

**Week 1:**
- [ ] Team review of value prop and taglines (by Friday)
- [ ] Select final tagline based on informal testing
- [ ] Incorporate feedback into glossary and UI copy (Tasks 2-3)

**Week 2:**
- [ ] Integrate value prop into dashboard header
- [ ] Use messaging framework for help documentation
- [ ] Test pitch with external stakeholders

**Week 3:**
- [ ] Finalize messaging for demo storyboard
- [ ] Create speaker notes using elevator pitches
- [ ] Update README with simplified value prop

---

**Prepared by:** Agent 6 (Copy/Content)
**For:** SIAD MVP Demo Rebuild
**Feedback to:** Agent 4 (Frontend), Agent 5 (UX), All Agents (tagline selection)
