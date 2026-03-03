# SIAD Command Center — Copy & Microcopy Style Guide

**Version:** 1.0
**Status:** Production Reference
**Last Updated:** 2026-03-03
**Owner:** Copy Writer (Agent 3)
**Audience:** Frontend Engineers, UI Designers, Product Managers

---

## Overview

This guide defines all interface copy for the SIAD Command Center tactical demo. Tone is **military precision meets data science clarity**—direct, technical, and authoritative. No marketing fluff. Every word serves navigation or decision-making.

**Style Rules:**
- **Commands/Actions:** UPPERCASE + verb (e.g., "OPEN INSPECTOR")
- **Descriptions:** Sentence case, technical but plain English
- **Metrics:** Monospace format, precise notation (e.g., "MSE: 0.0664")
- **Status:** Present tense, active voice
- **Uncertainty:** Explicit confidence ranges, no hedging

---

## 1. Main Headlines & Page Titles

### 1.1 Application Title
```
Display: "SIAD COMMAND CENTER"
Font: Rajdhani Bold, 2.5rem, letter-spacing: 0.1em
Color: #14b8a6 (with glow)
Context: Header, all pages
Meaning: Tactical earth observation command center
```

### 1.2 Application Tagline
```
Display: "Satellite Imagery Anticipatory Dynamics — 6-Month Prediction Gallery"
Font: Inter, 0.875rem, letter-spacing: 0.05em
Color: #737373 (dim)
Context: Below title, landing
Purpose: Sets scope: satellite data, 6-month rollout, gallery format
```

### 1.3 Section Headers

#### Gallery Section
```
Display: "PREDICTION GALLERY"
Font: Rajdhani Semibold, 1.5rem, uppercase
Color: #f5f5f5
Context: Gallery view
Purpose: Category browser for best/worst/average predictions
```

#### Hex Map Section
```
Display: "REGIONAL HOTSPOT MAP"
Font: Rajdhani Semibold, 1.5rem, uppercase
Color: #f5f5f5
Context: 2D tile map
Purpose: Geographic overview of all tiles with anomaly flags
```

#### Tile Inspector Section
```
Display: "TILE INSPECTOR"
Font: Rajdhani Semibold, 1.5rem, uppercase
Color: #f5f5f5
Context: Full-screen tile analysis
Purpose: Deep-dive on single tile, imagery + controls
```

#### Analysis Panel Section
```
Display: "SCENARIO ANALYSIS"
Font: Rajdhani Semibold, 1.5rem, uppercase
Color: #f5f5f5
Context: Comparison view
Purpose: Counterfactual scenario side-by-side
```

### 1.4 Empty States

#### No Tiles Loaded
```
Display: "No tiles available."
Font: Inter, 0.875rem
Color: #a3a3a3
Context: Gallery grid when no predictions loaded
Action: Below, show instruction
Help Text: "Start FastAPI backend or load gallery data."
```

#### Loading Predictions
```
Display: "Loading predictions..."
Font: Inter, 0.875rem
Color: #a3a3a3
Context: Gallery or tile inspector during fetch
Visual: Spinner icon with glow effect
```

#### No Tile Selected
```
Display: "Select a tile to begin analysis."
Font: Inter, 0.875rem
Color: #a3a3a3
Context: Right panel before user clicks hex
Help: "Click any hex on the map or card in the gallery."
```

#### Inference Failed (Timeout/Error)
```
Display: "Tile data unavailable."
Font: Inter, 0.875rem
Color: #ef4444
Context: When API returns 404 or timeout
Action: "RETRY" button below
Help: "Check backend connection or select another tile."
```

---

## 2. UI Labels & Form Fields

### 2.1 Tab/Filter Labels

#### Gallery Category Tabs
```
"All Tiles"    (neutral)
"Best"         (when selected: amber glow)
"Average"      (when selected: amber glow)
"Worst"        (when selected: amber glow)
Font: JetBrains Mono, 0.875rem, uppercase
Color: #14b8a6 (border), #f5f5f5 (text)
```

#### Comparison Toggle
```
"Prediction"   (left segment, default active)
"Ground Truth" (right segment)
Font: JetBrains Mono, 0.75rem, uppercase
Color: Active = #a5f3fc on glow bg
```

#### Modality Checkboxes
```
"☑ SAR"
"☑ Optical"
"☑ Lights"
Font: Inter, 0.875rem
Color: #f5f5f5
Meaning: Toggle input modalities in RGB composition
```

### 2.2 Climate Control Labels

#### Rainfall Anomaly
```
Label: "RAINFALL ANOMALY (MM)"
Range: -2σ (Dry) ← Neutral (0) → +2σ (Wet)
Font: JetBrains Mono, 0.75rem, uppercase
Color: #d4d4d4
Per-Month Display: "MAR: [slider]"
```

#### Temperature Anomaly
```
Label: "TEMPERATURE DEVIATION (°C)"
Range: -2σ (Cold) ← Neutral (0) → +2σ (Hot)
Font: JetBrains Mono, 0.75rem, uppercase
Color: #d4d4d4
Per-Month Display: "MAR: [slider]"
```

### 2.3 Preset Buttons

```
Button Text:     "NEUTRAL" | "WET" | "DRY" | "HOT" | "CUSTOM"
Font:            JetBrains Mono, 0.75rem, uppercase, semibold
Color (Default): #737373 on transparent
Color (Active):  #f59e0b on rgba(245,158,11,0.15)
Border (Active): 1px #f59e0b with amber glow
Meaning:
  - NEUTRAL: All sliders to 0 (baseline scenario)
  - WET: Rainfall +1σ all months
  - DRY: Rainfall -1σ all months
  - HOT: Temperature +1σ all months
  - CUSTOM: User-defined from sliders
```

### 2.4 Metadata Labels (Right Panel)

```
Label Style: All-caps, JetBrains Mono, 0.75rem, #a3a3a3

"TILE ID"
"LATITUDE / LONGITUDE"
"HOTSPOT?"
"PERSISTENCE"
"ATTRIBUTION"
"VALIDATION LOSS"
"MEAN RESIDUAL"
"TREND (3-MONTH SLOPE)"
"VALID PIXELS"
"PREDICTION CONFIDENCE"
"DATE RANGE"
"MODALITY COMPOSITION"
```

---

## 3. Button Labels & Actions

### 3.1 Primary Action Buttons

#### Initialize Prediction (Tile Inspector)
```
Display:  "INITIALIZE PREDICTION"
Font:     JetBrains Mono, 0.875rem, semibold, uppercase
Color:    #14b8a6 on rgba(20,184,166,0.1)
Border:   1px #14b8a6
Glow:     0 0 20px rgba(20,184,166,0.3)
Behavior: Starts inference for current tile + climate params
Icon:     Lightning bolt (optional)
Meaning:  Trigger new prediction run with adjusted climate
```

#### Adjust Climate Parameters
```
Display:  "ADJUST CLIMATE"
Font:     JetBrains Mono, 0.875rem, semibold, uppercase
Color:    #14b8a6 on rgba(20,184,166,0.1)
Border:   1px #14b8a6
Behavior: Focus/scroll to climate slider section
Meaning:  Emphasize climate controls are ready for input
```

#### Compare Ground Truth
```
Display:  "COMPARE GROUND TRUTH"
Font:     JetBrains Mono, 0.875rem, semibold, uppercase
Color:    #14b8a6 on rgba(20,184,166,0.1)
Border:   1px #14b8a6
Behavior: Toggle imagery between prediction and actual
Icon:     Swap arrows (optional)
Meaning:  Side-by-side validation
```

### 3.2 Secondary Action Buttons

#### Export Results
```
Display:  "EXPORT"
Font:     JetBrains Mono, 0.75rem, semibold, uppercase
Color:    #d4d4d4 on transparent
Border:   1px #262626
Behavior: Download tile analysis as JSON/PNG zip
Meaning:  Save prediction for external use
```

#### Open Full Inspector
```
Display:  "OPEN INSPECTOR"
Font:     JetBrains Mono, 0.75rem, semibold, uppercase
Color:    #d4d4d4 on transparent
Border:   1px #262626
Behavior: Expand tile view to full screen
Meaning:  Maximize workspace for deep analysis
```

#### Back to Gallery
```
Display:  "BACK TO GALLERY"
Font:     JetBrains Mono, 0.75rem, semibold, uppercase
Color:    #d4d4d4 on transparent
Border:   1px #262626
Behavior: Return to gallery view, preserve scroll position
Meaning:  Navigation breadcrumb
```

#### Close / Dismiss
```
Display:  "CLOSE"
Font:     JetBrains Mono, 0.75rem, semibold, uppercase
Color:    #d4d4d4 on transparent
Border:   1px #262626
Icon:     × (optional)
Behavior: Close modal/panel without saving
Meaning:  Dismiss contextual UI
```

### 3.3 Tertiary/Status Buttons

#### Refresh Data
```
Display:  "REFRESH"
Font:     JetBrains Mono, 0.7rem, uppercase
Color:    #737373
Icon:     Circular arrow
Behavior: Re-fetch tile metadata from backend
Meaning:  Update cache if data changed
```

#### Help / Documentation
```
Display:  "?"
Font:     JetBrains Mono, 0.875rem, bold
Color:    #14b8a6
Behavior: Show tooltip or slide-in help panel
Meaning:  Context-sensitive documentation
```

---

## 4. Status Indicators & Badges

### 4.1 Model & System Status

#### Model Ready
```
Display:  "MODEL READY"
Font:     JetBrains Mono, 0.75rem, uppercase, semibold
Badge BG: rgba(34, 197, 94, 0.15) (success green)
Text:    #22c55e
Border:  1px rgba(34, 197, 94, 0.3)
Glow:    0 0 10px rgba(34,197,94,0.4)
Context: System is operational, ready for inference
Placement: Header status bar
```

#### Inference Running
```
Display:  "INFERENCE RUNNING"
Font:     JetBrains Mono, 0.75rem, uppercase, semibold
Badge BG: rgba(245, 158, 11, 0.15) (warning amber)
Text:    #f59e0b
Border:  1px rgba(245, 158, 11, 0.3)
Glow:    0 0 10px rgba(245,158,11,0.4)
Context: Model is actively processing
Placement: Header status bar
Animation: Pulse effect
```

#### Prediction Complete
```
Display:  "PREDICTION COMPLETE"
Font:     JetBrains Mono, 0.75rem, uppercase, semibold
Badge BG: rgba(34, 197, 94, 0.15) (success green)
Text:    #22c55e
Border:  1px rgba(34, 197, 94, 0.3)
Glow:    0 0 10px rgba(34,197,94,0.4)
Context: Inference finished, results ready
Placement: Near imagery in tile inspector
```

#### Backend Unavailable
```
Display:  "BACKEND UNAVAILABLE"
Font:     JetBrains Mono, 0.75rem, uppercase, semibold
Badge BG: rgba(239, 68, 68, 0.15) (error red)
Text:    #ef4444
Border:  1px rgba(239, 68, 68, 0.3)
Glow:    0 0 10px rgba(239,68,68,0.4)
Context: API unreachable, inference disabled
Placement: Header status bar
Action:  Show "RETRY" button below
```

### 4.2 Confidence Indicators

#### High Confidence
```
Display:  "H" | "HI" | "HIGH"
Font:     JetBrains Mono, 0.75rem, bold, uppercase
Badge:   24px circle
BG:      rgba(34, 197, 94, 0.15) (green)
Border:  2px #22c55e
Text:    #22c55e
Glow:    0 0 10px rgba(34,197,94,0.4)
Meaning: >80% confidence in prediction
```

#### Medium Confidence
```
Display:  "M" | "MED" | "MEDIUM"
Font:     JetBrains Mono, 0.75rem, bold, uppercase
Badge:   24px circle
BG:      rgba(245, 158, 11, 0.15) (amber)
Border:  2px #f59e0b
Text:    #f59e0b
Glow:    0 0 10px rgba(245,158,11,0.4)
Meaning: 50–80% confidence in prediction
```

#### Low Confidence
```
Display:  "L" | "LOW" | "⚠"
Font:     JetBrains Mono, 0.75rem, bold, uppercase
Badge:   24px circle
BG:      rgba(239, 68, 68, 0.15) (red)
Border:  2px #ef4444
Text:    #ef4444
Glow:    0 0 10px rgba(239,68,68,0.4)
Meaning: <50% confidence, manual review recommended
```

### 4.3 Category Badges

#### Hotspot Tier: Structural
```
Display:  "STRUCTURAL"
Font:     JetBrains Mono, 0.7rem, uppercase, semibold
BG:      rgba(245, 158, 11, 0.15)
Text:    #fcd34d
Border:  1px rgba(245, 158, 11, 0.3)
Meaning: Human-made infrastructure change detected
```

#### Hotspot Tier: Activity
```
Display:  "ACTIVITY"
Font:     JetBrains Mono, 0.7rem, uppercase, semibold
BG:      rgba(20, 184, 166, 0.15)
Text:    #a5f3fc
Border:  1px rgba(20, 184, 166, 0.3)
Meaning: Movement/temporal signal detected
```

#### Hotspot Tier: Environmental
```
Display:  "ENVIRONMENTAL"
Font:     JetBrains Mono, 0.7rem, uppercase, semibold
BG:      rgba(34, 197, 94, 0.15)
Text:    #86efac
Border:  1px rgba(34, 197, 94, 0.3)
Meaning: Natural feature change (vegetation, water)
```

#### Attribution: SAR-Dominant
```
Display:  "SAR-DOMINANT"
Font:     JetBrains Mono, 0.7rem, uppercase, semibold
BG:      rgba(139, 92, 246, 0.12)
Text:    #d8b4fe
Border:  1px rgba(139, 92, 246, 0.3)
Meaning: Prediction primarily from radar data
```

#### Attribution: Optical-Only
```
Display:  "OPTICAL-ONLY"
Font:     JetBrains Mono, 0.7rem, uppercase, semibold
BG:      rgba(245, 158, 11, 0.12)
Text:    #fde68a
Border:  1px rgba(245, 158, 11, 0.3)
Meaning: Prediction uses visible-spectrum imagery only
```

### 4.4 Metric Badges

#### MSE (Mean Squared Error)
```
Display:  "MSE: 0.0664"
Font:     JetBrains Mono, 0.75rem, semibold
Badge:   Inline-flex, rounded 12px padding
BG:      rgba(20, 184, 166, 0.12)
Text:    #a5f3fc
Border:  1px rgba(20, 184, 166, 0.4)
Format:  "MSE: " + decimal (4 significant figures)
Example: "MSE: 0.0664" not "Loss: 6.64×10⁻²" (keep readable)
```

#### PSNR (Peak Signal-to-Noise Ratio)
```
Display:  "PSNR: 28.4 dB"
Font:     JetBrains Mono, 0.75rem, semibold
Badge:   Inline-flex, rounded 12px padding
BG:      rgba(245, 158, 11, 0.12)
Text:    #fde68a
Border:  1px rgba(245, 158, 11, 0.4)
Format:  "PSNR: " + decimal (1 decimal place) + " dB"
Meaning: Image quality metric (higher is better)
```

#### SSIM (Structural Similarity)
```
Display:  "SSIM: 0.847"
Font:     JetBrains Mono, 0.75rem, semibold
Badge:   Inline-flex, rounded 12px padding
BG:      rgba(34, 197, 94, 0.12)
Text:    #86efac
Border:  1px rgba(34, 197, 94, 0.4)
Format:  "SSIM: " + decimal (3 significant figures)
Range:   0.0–1.0 (1.0 = identical)
Meaning: Structural perceptual similarity
```

#### Accuracy
```
Display:  "ACCURACY: 94.2%"
Font:     JetBrains Mono, 0.75rem, semibold
Badge:   Inline-flex, rounded 12px padding
BG:      rgba(139, 92, 246, 0.12)
Text:    #d8b4fe
Border:  1px rgba(139, 92, 246, 0.4)
Format:  "ACCURACY: " + decimal (1 decimal place) + "%"
Meaning: Pixel-wise prediction accuracy
```

---

## 5. Tooltips & Help Text

### 5.1 Climate Controls (Rainfall Anomaly)

#### Slider Tooltip
```
Title:   "RAINFALL ANOMALY"
Text:    "Adjustment to expected rainfall for this month.
         -2σ = severe drought, 0 = seasonal average, +2σ = very wet."
Font:    Inter, 0.75rem
Color:   #d4d4d4
Position: Appear on hover, arrow pointing to slider
Glow:    Optional cyan glow
```

#### Preset Tooltip: "WET"
```
Title:   "WET SCENARIO"
Text:    "All months: +1σ rainfall anomaly. Useful for isolating
         vegetation response independent of structural change."
Font:    Inter, 0.75rem
Color:   #d4d4d4
```

#### Preset Tooltip: "DRY"
```
Title:   "DRY SCENARIO"
Text:    "All months: -1σ rainfall anomaly. Tests model sensitivity
         to water stress on vegetation/reflectance."
Font:    Inter, 0.75rem
Color:   #d4d4d4
```

### 5.2 Climate Controls (Temperature Anomaly)

#### Slider Tooltip
```
Title:   "TEMPERATURE DEVIATION"
Text:    "Adjustment to expected temperature for this month.
         -2σ = severe cold, 0 = seasonal average, +2σ = very hot."
Font:    Inter, 0.75rem
Color:   #d4d4d4
Position: Appear on hover, arrow pointing to slider
Glow:    Optional amber glow
```

#### Preset Tooltip: "HOT"
```
Title:   "HOT SCENARIO"
Text:    "All months: +1σ temperature anomaly. Tests model
         sensitivity to heat stress on vegetation and urban features."
Font:    Inter, 0.75rem
Color:   #d4d4d4
```

### 5.3 Metrics Interpretation

#### MSE Tooltip
```
Title:   "MEAN SQUARED ERROR"
Text:    "Average squared pixel-level difference between prediction
         and ground truth. Lower is better. Range: 0–1 (normalized)."
Font:    Inter, 0.75rem
Color:   #d4d4d4
Learn More: Link to docs/metrics.md
```

#### Confidence Tooltip
```
Title:   "PREDICTION CONFIDENCE"
Text:    "Model's self-assessed uncertainty estimate over latent space.
         Based on ensemble entropy; validated against residual distribution."
Font:    Inter, 0.75rem
Color:   #d4d4d4
Learn More: Link to docs/confidence.md
```

#### Residual Trend Tooltip
```
Title:   "3-MONTH TREND"
Text:    "Linear slope of mean residual over months 0–3.
         Positive = increasing error, negative = improving prediction."
Font:    Inter, 0.75rem
Color:   #d4d4d4
Learn More: Link to docs/residuals.md
```

### 5.4 Timeline Scrubber

#### Month Label Tooltip
```
Display:   "Click to jump, or drag thumb to scrub"
Font:      Inter, 0.7rem
Color:     #a3a3a3
Position:  Below scrubber track
Behavior:  Appear on hover, fade on leave
```

#### Speed Control Tooltip
```
Title:    "PLAYBACK SPEED"
Text:     "Slow = 1000ms/frame, Normal = 500ms/frame, Fast = 250ms/frame"
Font:     Inter, 0.75rem
Color:    #d4d4d4
Position: Hover on speed buttons
```

### 5.5 Hex Map

#### Hex Hover Tooltip
```
Format:   "tile_x001_y003"
          "Hotspot: YES"
          "Confidence: 87% (Structural)"
          "Month Detected: APR"
Font:     JetBrains Mono, 0.75rem
Color:    #f5f5f5
BG:       rgba(10,10,10,0.9) with border #14b8a6
Position: Follow cursor, offset 8px
```

#### Map Legend Entry
```
"🟢 1–25th percentile (Low anomaly)"
"🟡 26–75th percentile (Medium anomaly)"
"🔴 76–99th percentile (High anomaly)"
"🔴* Flagged hotspot (Multi-month persistence)"
Font: Inter, 0.75rem
Color: #a3a3a3
```

---

## 6. Microcopy: Loading States & Transitions

### 6.1 Encoding & Preprocessing

```
"Encoding observations..."
Font: Inter, 0.875rem
Color: #a3a3a3
Position: Below spinner
Duration: Variable, until latent encode complete
Next: → "Rolling out predictions..."
```

### 6.2 Inference Progression

```
"Rolling out predictions..."
Font: Inter, 0.875rem
Color: #a3a3a3
Position: Below spinner
Duration: Variable, during 6-month forward pass
Next: → "Decoding to pixel space..."
```

### 6.3 Decoding

```
"Decoding to pixel space..."
Font: Inter, 0.875rem
Color: #a3a3a3
Position: Below spinner
Duration: Variable, during RGB reconstruction
Next: → "Prediction Complete" (green badge)
```

### 6.4 Comparison Generation

```
"Generating comparison metrics..."
Font: Inter, 0.875rem
Color: #a3a3a3
Position: Below spinner
Duration: Variable, during residual + SSIM calculation
Next: → "Comparison Ready"
```

### 6.5 Gallery Loading

```
"Fetching gallery entries..."
Font: Inter, 0.875rem
Color: #a3a3a3
Context: Gallery view on initial load
Next: → Gallery grid populated or empty state
```

### 6.6 Data Fetch (Tile Details)

```
"Loading tile metadata..."
Font: Inter, 0.875rem
Color: #a3a3a3
Context: Right panel on tile selection
Next: → Metadata panel populated
```

---

## 7. Error Messages & Recovery

### 7.1 Network Errors

#### Backend Unreachable
```
Display:  "Backend unavailable. Check API connection."
Font:     Inter, 0.875rem
Color:    #ef4444
Position: Alert banner at top of app
Action:   [RETRY] button, or [REFRESH PAGE] button
Next:     Auto-retry every 5s until success
```

#### Timeout (>30s)
```
Display:  "Request timed out. The model may be slow or unresponsive."
Font:     Inter, 0.875rem
Color:    #f59e0b (warning, not critical)
Position: Alert banner
Action:   [RETRY] button
Fallback: Offer to load cached result if available
```

### 7.2 Data Errors

#### Tile Not Found
```
Display:  "Tile tile_x001_y003 not found."
Font:     Inter, 0.875rem
Color:    #ef4444
Position: In tile inspector
Help:     "Available tiles: tile_x000_y001, tile_x000_y002, ..."
Action:   [SELECT ANOTHER TILE] button
```

#### Missing Predictions
```
Display:  "No predictions generated for this tile yet."
Font:     Inter, 0.875rem
Color:    #f59e0b
Position: Gallery grid
Help:     "Click GENERATE GALLERY to run inference."
Action:   [GENERATE GALLERY] button
```

#### Invalid Climate Parameters
```
Display:  "Rainfall anomaly must be between -2σ and +2σ."
Font:     Inter, 0.875rem
Color:    #ef4444
Position: Below climate slider
Action:   Reset slider to valid range automatically
```

### 7.3 Model/System Errors

#### Model Failed to Load
```
Display:  "Model initialization failed: {error_code}"
Font:     Inter, 0.875rem
Color:    #ef4444
Position: Alert banner on startup
Help:     "Check checkpoint path and device memory. Restart backend."
Action:   [RETRY] button, or link to docs/troubleshooting.md
```

#### Out of Memory (OOM)
```
Display:  "Out of memory during inference. Try smaller tile or fewer months."
Font:     Inter, 0.875rem
Color:    #ef4444
Position: Alert banner
Action:   Suggest reducing resolution or tile size
```

#### Inference NaN/Inf
```
Display:  "Prediction contains invalid values. Try different climate params."
Font:     Inter, 0.875rem
Color:    #f59e0b
Position: Alert below imagery
Help:     "This may indicate model instability under extreme scenarios."
Action:   [RESET TO NEUTRAL] button
```

---

## 8. Success Confirmations & Feedback

### 8.1 Prediction Confirmations

#### Prediction Generated
```
Display:  "Prediction generated."
Font:     Inter, 0.875rem
Color:    #22c55e
Position: Transient toast, top-right, 3s duration
Icon:     Checkmark
Next:     Auto-dismiss
```

#### Parameters Updated
```
Display:  "Climate parameters updated."
Font:     Inter, 0.875rem
Color:    #22c55e
Position: Transient toast, top-right, 2s duration
Icon:     Checkmark
```

#### Gallery Generated
```
Display:  "Gallery generated: 15 tiles processed."
Font:     Inter, 0.875rem
Color:    #22c55e
Position: Alert banner, top
Duration: Persistent until dismissed
Action:   [DISMISS] button
```

#### Results Exported
```
Display:  "Results exported to siad-tile-x001-y003.zip"
Font:     Inter, 0.875rem
Color:    #22c55e
Position: Transient toast, top-right, 4s duration
Action:   [OPEN] link to download
```

### 8.2 Interaction Confirmations

#### Comparison Activated
```
Display:  "Showing ground truth."
Font:     Inter, 0.75rem, dim
Color:    #a3a3a3
Position: Above imagery toggle
Duration: Transient, fade after 2s
```

#### Scenario Saved
```
Display:  "Custom scenario saved."
Font:     Inter, 0.875rem
Color:    #22c55e
Position: Transient toast, 2s duration
Help:     "Reload page to restore."
```

---

## 9. Data Formatting Standards

### 9.1 MSE / Loss Values

**Rule:** Display as plain decimal, 4 significant figures. No scientific notation unless <0.0001.

```
Examples:
  ✓ "MSE: 0.0664"
  ✓ "MSE: 0.1079"
  ✗ "MSE: 6.64×10⁻²" (too technical for UI)
  ✗ "Loss: 0.066" (lacks precision)
  ✓ "MSE: 0.000089" (if extremely small)
  ✗ "MSE: 8.9e-5" (scientific notation OK only in logs)

Badge Format: "MSE: 0.0664"
Tooltip Format: "Mean squared error: 0.0664 (loss per normalized pixel)"
```

### 9.2 Date Formats

**Rule:** Use "YYYY-MM" in data contexts; "Month YYYY" in narratives.

```
Data Contexts (Monospace):
  "2024-03"   (tile metadata)
  "2024-03 to 2024-08" (date range)
  "MAR 2024"  (month label on timeline)

Narrative Contexts (Prose):
  "March 2024"
  "6-month rollout from March 2024 to August 2024"

Timeline Labels:
  "MAR" "APR" "MAY" "JUN" "JUL" "AUG"
  (all-caps, 3-letter month abbreviation)

Tooltip Format:
  "April 2024 (Month 1)"
```

### 9.3 Coordinate Formats

**Rule:** Use "tile_xNNN_yNNN" for tile IDs; lat/lon in decimal degrees with compass direction.

```
Tile ID Format:
  "tile_x001_y003"  (monospace, snake_case)
  Not: "X001Y003", "x1y3", "Tile-001-003"

Latitude/Longitude (Decimal Degrees):
  "37.4°N, 122.1°W"  (degrees symbol + compass)
  "37.4°N"           (if Y alone)
  "122.1°W"          (if X alone)
  Format: DDD.D°[N|S|E|W]

Bounds (if needed):
  "Bounds: 37.3–37.5°N, 122.0–122.2°W"
  (dash for range, all directions explicit)
```

### 9.4 Confidence / Percentage Formats

**Rule:** Use whole numbers for % unless sub-1% precision is critical.

```
Display Formats:
  "Confidence: 87%"       ✓
  "Confidence: 87.3%"     ✓ (if detail needed)
  "Confidence: 87.26%"    ✗ (too precise for UI)
  "Hotspot confidence: 87%" (label + value)

Visual Representations:
  Bar chart:     "████████░░ 87%"
  Confidence indicator badge: "H" (High > 80%), "M" (50–80%), "L" (<50%)
```

### 9.5 Temperature / Rainfall Anomalies

**Rule:** Use "σ" (sigma) notation for standard deviations; show plain units where helpful.

```
Data Representation:
  "Rainfall: +1σ"        (in sliders, concise)
  "Temperature: -0.5σ"   (fractional deviations OK)
  "Rainfall: +25 mm"     (optional: add absolute if available)

Slider Labels:
  Range: "-2σ (Dry) ← Neutral (0) → +2σ (Wet)"
  "Temperature: [-2°C ...... 0°C ...... +2°C]" (optional: units)

Metadata Display:
  "Rainfall Anomaly (MAR): +0.8σ"
  "Temperature Anomaly (APR): -0.3σ"
```

### 9.6 Pixel Count / Valid Pixels

**Rule:** Use percentage unless exact count is critical for debugging.

```
Display Formats:
  "Valid Pixels: 96.2%"   ✓ (UI)
  "Valid Pixels: 38,456 / 40,000" ✓ (logs/detailed view)
  "Masked Pixels: 1,544"  (if showing bad pixels)
```

---

## 10. Accessibility & Inclusive Language

### 10.1 Color-Independent Status

Always pair color badges with text or icons to avoid relying on color alone:

```
✓ "HOTSPOT (Amber glow + icon + badge)"
✓ "MODEL READY (Green + checkmark icon)"
✗ "Green badge only" (fails for colorblind users)
```

### 10.2 Abbreviations

All-caps abbreviations explained on first use:

```
First use:  "MSE (Mean Squared Error): 0.0664"
Subsequent: "MSE: 0.0664"

Similarly:
  SSIM (Structural Similarity): 0.847
  PSNR (Peak Signal-to-Noise Ratio): 28.4 dB
  SAR (Synthetic Aperture Radar)
  RGB (Red-Green-Blue)
```

### 10.3 Plain Language for Technical Terms

Where possible, provide plain-English alternate:

```
✓ "Residual (difference between predicted and actual): 0.042"
✓ "Confidence (model's estimated accuracy): 87%"
✗ "Latent entropy: 0.43" (without explanation)
```

### 10.4 Icon + Text Pairing

Never rely on icons alone for critical info:

```
✓ [Compare] button + text label
✓ ⚠ "Tile data unavailable" (icon + text)
✗ ⚠ (icon alone, no alt-text)
```

---

## 11. Style Checklist for Engineers

When implementing UI copy:

- [ ] **All action labels are UPPERCASE and start with verb**: "INITIALIZE PREDICTION", not "Start"
- [ ] **Form labels use sentence case**: "Rainfall anomaly", not "RAINFALL ANOMALY" (unless it's a section header)
- [ ] **Status/state copy is present tense**: "Inference running", not "Inferencing"
- [ ] **Error copy is specific**: "Tile not found" includes tile ID
- [ ] **Numbers use consistent formatting**: "0.0664" not "0.066" or "6.64e-2"
- [ ] **Date labels follow "YYYY-MM" or "Month YYYY"** depending on context
- [ ] **Coordinates include compass direction**: "37.4°N, 122.1°W"
- [ ] **Tooltips explain "why", not just "what"**: "Useful for isolating vegetation response..."
- [ ] **Color-coded status is paired with text/icon**: No color-only alerts
- [ ] **Abbreviations are explained on first use**: "MSE (Mean Squared Error)"
- [ ] **No marketing fluff**: Pure utility, direct address to user intent
- [ ] **Glow effects on cyan (#14b8a6) or amber (#f59e0b)** match tokens.json

---

## 12. Version History & Updates

| Version | Date       | Author      | Changes                                      |
|---------|-----------|-------------|----------------------------------------------|
| 1.0     | 2026-03-03 | Agent 3     | Initial spec: headlines, labels, buttons, tooltips, formatting |

---

## 13. Related Documents

- `ux-spec.md` — Full UX specification, user flows, interaction details
- `tokens.json` — Design tokens (colors, typography, spacing, shadows)
- `tactical.css` — Implementation styles and utility classes
- `docs/metrics.md` — Detailed explanation of MSE, SSIM, PSNR
- `docs/confidence.md` — How confidence scores are calculated
- `docs/troubleshooting.md` — Error recovery and debugging

---

## 14. Quick Reference: Copy by Context

### Landing Page
- Title: "SIAD COMMAND CENTER"
- Tagline: "Satellite Imagery Anticipatory Dynamics — 6-Month Prediction Gallery"
- CTA: "EXPLORE GALLERY" or "OPEN HEX MAP"

### Gallery View
- Section: "PREDICTION GALLERY"
- Tabs: "All Tiles", "Best", "Average", "Worst"
- Empty: "No tiles available. Start FastAPI backend..."

### Hex Map
- Section: "REGIONAL HOTSPOT MAP"
- Legend: "🟢 1–25%", "🟡 26–75%", "🔴 76–99%", "🔴* Flagged"
- Hover: "tile_x001_y003 | Hotspot: YES | Confidence: 87%"

### Tile Inspector
- Section: "TILE INSPECTOR"
- Toggle: "Prediction" / "Ground Truth"
- Labels: "RAINFALL ANOMALY (MM)", "TEMPERATURE DEVIATION (°C)"
- Presets: "NEUTRAL", "WET", "DRY", "HOT", "CUSTOM"
- Buttons: "INITIALIZE PREDICTION", "COMPARE GROUND TRUTH", "EXPORT"
- Metadata: "TILE ID", "LATITUDE / LONGITUDE", "HOTSPOT?", "PERSISTENCE", etc.

### Status Bar
- Model ready: "MODEL READY" (green badge)
- Inferring: "INFERENCE RUNNING" (amber badge, pulsing)
- Complete: "PREDICTION COMPLETE" (green badge)
- Error: "BACKEND UNAVAILABLE" (red badge)

### Errors
- Network: "Backend unavailable. Check API connection. [RETRY]"
- Timeout: "Request timed out. [RETRY]"
- Not found: "Tile tile_x001_y003 not found."
- Model fail: "Model initialization failed: {error_code}"
- OOM: "Out of memory during inference. Try smaller tile."

### Confirmations
- Generated: "Prediction generated." (3s toast)
- Updated: "Climate parameters updated." (2s toast)
- Exported: "Results exported to siad-tile-x001-y003.zip" (4s toast)

---

**This guide is the source of truth for all SIAD Command Center interface copy. When in doubt, refer here. When you find gaps, update this document.**
