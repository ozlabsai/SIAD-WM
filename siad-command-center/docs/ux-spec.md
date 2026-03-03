# SIAD Command Center — UX Specification

**Document Version:** 1.0
**Status:** Active Specification
**Last Updated:** 2026-03-03
**Audience:** UI/Frontend Designers, Frontend Engineers, Product Managers

---

## 1. Executive Overview

The **SIAD Command Center** is a Palantir/Anduril-style tactical intelligence interface for visualizing and exploring a world model's satellite image predictions 6 months into the future. Users can adjust climate actions (rainfall/temperature anomalies) per month and observe how the satellite imagery is expected to change. The interface combines data density with scannability, emphasizing real-time feedback and confidence signals.

### Core Value Proposition
- **Counterfactual exploration:** What if rainfall increases? How does that change what we see?
- **Persistent anomaly detection:** Show infrastructure changes that deviate from weather-baseline expectations
- **Tactical confidence:** Multi-modal data (SAR, optical, lights) corroborates predictions
- **Spatial reasoning:** Hex map + timeline allows fast pattern recognition across regions and time

---

## 2. User Personas & Flows

### Persona A: Intelligence Analyst (Primary)
**Goal:** Quickly identify regions with structural anomalies over the next 6 months
**Tasks:**
- Land on dashboard, scan for hotspots (highest priority)
- Click tile to see time-series predictions and metadata
- Adjust weather scenarios to isolate weather-driven vs. structural changes
- Deep-dive into 1–2 tiles for confidence assessment

**Key Flow:**
```
Landing → Gallery Browse → Hotspot Selection → Tile View →
  [Climate Adjustment Loop] → Export/Save
```

### Persona B: Model Validator (Secondary)
**Goal:** Verify model coherence and identify failure modes
**Tasks:**
- Compare best/worst predictions side-by-side
- Inspect loss/residual heatmaps overlaid on imagery
- Verify that neutral weather scenarios match seasonal norms
- Flag suspicious false positives (e.g., cloud artifacts)

**Key Flow:**
```
Landing → Gallery (Best/Worst) → Tile Inspector →
  [Compare Ground Truth vs. Prediction] → Notes/Export
```

### Persona C: Executive Stakeholder (Tertiary)
**Goal:** Understand what the model can do and credibility
**Tasks:**
- Watch guided demo showing hotspot detection
- See before/after imagery and confidence badges
- Review single best-case prediction
- Ask "Why should I trust this?"

**Key Flow:**
```
Landing → Guided Demo → Gallery Hero Tile → Close
```

---

## 3. Information Hierarchy

### Primary (Attention-Grabbing, Always Visible)
1. **Live Tile Predictions** — large, photo-realistic imagery with model output
2. **Hotspot Badges** — confidence tier (Structural/Activity/Environmental), persistence metrics
3. **Timeline Slider** — 6-month rollout with month labels
4. **Climate Controls** — rainfall/temperature sliders (per month, when inspecting a tile)

### Secondary (Scannable, Context-Sensitive)
5. **Metrics Overlay** — residual score, valid pixel %, modality composition
6. **Hex Map Legend** — tile coordinates, percentile rank
7. **Comparison Toggle** — Ground Truth vs. Prediction side-by-side
8. **Attribution Tags** — "SAR-dominant," "Optical-only," "Activity-like"

### Tertiary (Reference, Low Visual Weight)
9. **Model Metadata** — version, validation loss, dataset size
10. **Accessibility Notes** — alt text, keyboard shortcuts
11. **Help Panel** — how to interpret residuals, confidence tiers, scenario knobs
12. **Data Lineage** — tile coordinates, month range, preprocessing version

---

## 4. Primary User Flows

### Flow 1: Landing → Gallery Browse → Hotspot Deep-Dive

```
┌─────────────────────────────────────────────────────────┐
│ 1. LANDING PAGE                                         │
├─────────────────────────────────────────────────────────┤
│ - Hero image: Best prediction tile (before/after)       │
│ - Headline: "6-Month Satellite Predictions Ready"       │
│ - Two CTAs:                                             │
│   a) "Explore Gallery" (best/worst/avg)                │
│   b) "Interactive Hex Map" (select tile)               │
│ - Tagline: "SIAD World Model at work"                   │
└────────────────┬──────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 2. GALLERY VIEW (Category: Best/Worst/Average)          │
├─────────────────────────────────────────────────────────┤
│ - 3-column grid: thumbnail (prediction), rank, score    │
│ - Hover: before/after swap, details popup               │
│ - Click: → Tile Inspector                              │
│ - Filter bar: Category, confidence tier, month range    │
└────────────────┬──────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 3. TILE INSPECTOR (Full Screen)                         │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ LEFT PANEL: Imagery Stack                           │ │
│ │ ┌──────────────────────────────────────────────────┐│ │
│ │ │ [Large Live Prediction]                          ││ │
│ │ │ Toggle: Ground Truth <-> Prediction              ││ │
│ │ │                                                  ││ │
│ │ │ Month Label: Mar 2026 [◀ MAR APR MAY JUN JUL▶]  ││ │
│ │ │ (Timeline scrubber below)                        ││ │
│ │ │                                                  ││ │
│ │ │ [Heatmap Overlay: Residuals]                    ││ │
│ │ │ Toggle: On/Off                                   ││ │
│ │ └──────────────────────────────────────────────────┘│ │
│ │                                                     │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ Modality Controls (checkboxes):                    │ │
│ │ ☑ SAR  ☑ Optical  ☑ Lights                        │ │
│ │ (Allows user to isolate channel contributions)    │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ RIGHT PANEL: Scenario & Metadata                    │ │
│ │                                                     │ │
│ │ ┌─ Climate Scenario Controls ─────────────────────┐│ │
│ │ │ Rainfall Anomaly (month-by-month):              ││ │
│ │ │  MAR: [▓░░░░░] (neutral)                         ││ │
│ │ │  APR: [░░░░░░] (neutral)                         ││ │
│ │ │  ... (6 total)                                   ││ │
│ │ │                                                 ││ │
│ │ │ Temperature Anomaly (month-by-month):           ││ │
│ │ │  MAR: [░░░░░░] (neutral)                         ││ │
│ │ │  ... (6 total)                                   ││ │
│ │ │                                                 ││ │
│ │ │ [Preset Buttons]                                ││ │
│ │ │ • Neutral  • Wet  • Dry  • Hot  • Custom         ││ │
│ │ └─────────────────────────────────────────────────┘│ │
│ │                                                     │ │
│ │ ┌─ Tile Metadata ─────────────────────────────────┐│ │
│ │ │ ID: tile_x001_y003                              ││ │
│ │ │ Lat/Lon: 37.4°N, 122.1°W                        ││ │
│ │ │ Hotspot?: YES (Structural confidence: 87%)     ││ │
│ │ │ Persistence: 2 months                           ││ │
│ │ │ Attribution: SAR-dominant                       ││ │
│ │ │ Val Loss: 0.0131                                ││ │
│ │ └─────────────────────────────────────────────────┘│ │
│ │                                                     │ │
│ │ ┌─ Residual Stats ────────────────────────────────┐│ │
│ │ │ Mean Residual: 0.042                            ││ │
│ │ │ Trend (3-month slope): 0.015 ↑ (increasing)     ││ │
│ │ │ Valid Pixels: 96.2%                             ││ │
│ │ │ Prediction Confidence: ████████░░ (82%)         ││ │
│ │ └─────────────────────────────────────────────────┘│ │
│ │                                                     │ │
│ │ [Compare] [Export] [Back to Gallery]               │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Flow 2: Hex Map → Select Tile → Inspect → Adjust Climate

```
┌─────────────────────────────────────────────────────────┐
│ 1. HEX MAP VIEW (2D Grid, SF Bay Area)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│     ┌─ Legend ──────────────────────────────┐         │
│     │ Color: Acceleration Percentile         │         │
│     │ 🟢 1-25%  🟡 26-75%  🔴 76-99%       │         │
│     │ 🔴 *Flagged hotspot                  │         │
│     │ Hover: Tile ID, Month Detected       │         │
│     └────────────────────────────────────────┘         │
│                                                         │
│              ◇ ◇ ◇ ◇ ◇ ◇ ◇                           │
│             ◇ ◇ ◇ ◇ ◇ ◇ ◇ ◇                          │
│            ◇ ◇ ◇ 🔴 ◇ ◇ ◇ ◇ ◇                         │
│             ◇ ◇ ◇ ◇ ◇ ◇ ◇ ◇                          │
│              ◇ ◇ ◇ ◇ ◇ ◇ ◇                           │
│                                                         │
│ Interaction:                                            │
│ - Click hex → Open Tile Inspector                      │
│ - Hover → Show tile ID, hotspot flag, top month      │
│ - Double-click → Zoom to region                       │
│ - Pan/zoom: Standard mouse/trackpad                   │
└─────────────────────────────────────────────────────────┘
```

### Flow 3: Scenario Comparison (Same Tile, Different Actions)

```
┌─────────────────────────────────────────────────────────┐
│ TILE INSPECTOR with Scenario Comparison                │
├─────────────────────────────────────────────────────────┤
│ ┌────────────────────────┬───────────────────────────┐  │
│ │ SCENARIO A             │ SCENARIO B                │  │
│ │ Neutral Weather        │ Extra Rainfall (Apr)      │  │
│ │                        │                           │  │
│ │ [Prediction A]         │ [Prediction B]            │  │
│ │ Month: APR             │ Month: APR                │  │
│ │ Residual: 0.038        │ Residual: 0.025          │  │
│ │ Notes: Less water      │ Notes: More vegetation   │  │
│ │ (Structural signal)    │ (Weather-driven)         │  │
│ │                        │                           │  │
│ │ [Timeline A]           │ [Timeline B]              │  │
│ │ Mean Res: ▓▓▓░░░░░░ 0.04│ Mean Res: ▓▓░░░░░░░░ 0.02│  │
│ └────────────────────────┴───────────────────────────┘  │
│                                                         │
│ Conclusion Panel:                                       │
│ "Scenario B (wet) shows LESS residual drift than      │
│  Scenario A (neutral). This suggests the anomaly      │
│  in APR-MAY is NOT explained by rainfall alone—       │
│  consistent with structural change hypothesis."        │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Key Interactions & Behaviors

### 5.1 Hex Map Interactions

| Interaction | Behavior | Visual Feedback |
|---|---|---|
| **Click Hex** | Open Tile Inspector for that tile | Highlight hex, animate expand transition |
| **Hover Hex** | Show tooltip: tile_id, hotspot flag, confidence | Glow aura (cyan if normal, amber if hotspot) |
| **Double-click** | Zoom to region (2x), highlight neighbors | Smooth zoom animation |
| **Drag** | Pan map | Cursor changes to grab |
| **Scroll/Pinch** | Zoom in/out | Smooth zoom, preserve center |
| **Right-click** | Context menu: Open Full Screen, Compare, Export | Modal popup menu |

### 5.2 Timeline Scrubber

**Default State:**
```
┌──────────────────────────────────────────────────────┐
│ MAR  APR  MAY  JUN  JUL  AUG                          │
│ |    |▓▓▓▓▓|    |    |    |    |                      │
│ 0    1    2    3    4    5    6                       │
│ ↑                                                      │
│ Current: April (Month 1)                              │
└──────────────────────────────────────────────────────┘
```

**Interactions:**
- **Click Month Label:** Jump to that month instantly
- **Drag Slider:** Scrub smoothly through timeline
- **Keyboard:** Arrow keys (← →) to move one month
- **Loop Toggle:** ☑ Auto-play (cycles MAR→AUG, loops)
- **Speed Control:** [▓░░] Slow, [▓▓░] Normal, [▓▓▓] Fast

**Feedback:**
- Month label highlights in accent color (cyan)
- Imagery updates with 150ms crossfade
- Metadata (residual, confidence) updates in real-time

### 5.3 Climate Control Sliders

Each month has two independent sliders: rainfall anomaly, temperature anomaly.

```
MAR Rainfall:  ← -2σ ─[●]─ 0σ ──→ +2σ
               (Dry)  (Neutral) (Wet)

MAR Temp:      ← -2σ ─────[●]─ 0σ ──→ +2σ
               (Cold)    (Neutral)   (Hot)
```

**Behavior:**
- Range: -2σ to +2σ (standard deviations from historical mean)
- Neutral position: center
- Dragging: Real-time inference (0-500ms latency)
- Preset buttons override all sliders

**Presets:**
- **Neutral:** all sliders at 0
- **Wet:** rainfall +1σ all months, temp neutral
- **Dry:** rainfall -1σ all months, temp neutral
- **Hot:** temp +1σ all months, rainfall neutral
- **Custom:** User-defined (save to browser session)

### 5.4 Imagery Comparison Toggle

```
┌─────────────────────────────────────┐
│ Toggle: Ground Truth <→ Prediction  │
│ [Ground Truth] ◯ → ◯ [Prediction]   │
└─────────────────────────────────────┘
```

**Behavior:**
- Click or press Space to swap
- Smooth crossfade (200ms)
- Label updates dynamically
- Works with timeline scrubber (each month can show either)

### 5.5 Residual Heatmap Overlay

```
┌──────────────────────────────────────┐
│ [Residual Heatmap]                   │
│ Toggle: ☑ On/Off                     │
│ ├─ Color scale:                      │
│ │  Blue (low residual, expected)     │
│ │  Yellow (medium)                   │
│ │  Red (high residual, anomaly)      │
│ │                                    │
│ │  0.0 ▓░░░░░░░░░░░░░░░░░░░░░░░░ 0.15 │
│ │                                    │
│ │ Opacity: [▓▓░░░░░░] 40%            │
│ └──────────────────────────────────────┘
```

**Interactions:**
- Click toggle to enable/disable overlay
- Slider adjusts transparency
- Heatmap updates when scenario changes (residuals recomputed server-side)

### 5.6 Modality Filter Checkboxes

Users can isolate which sensor modalities feed into the prediction:

```
┌──────────────────────────────────┐
│ Input Modalities                 │
│ ☑ Sentinel-2 (Optical)          │
│ ☑ Sentinel-1 (SAR)              │
│ ☑ VIIRS (Nightlights)           │
│                                  │
│ [Recompute] (only if all unchecked: disabled) │
└──────────────────────────────────┘
```

**Behavior:**
- Unchecking all disables the Recompute button (must select ≥1)
- Clicking Recompute triggers inference with subset of channels
- Results cached; re-checking same combo is instant
- Helps analysts identify which modality drives predictions

---

## 6. Screen States & Layouts

### Screen 1: Landing Page

**Viewport: Full desktop (1400px+)**

```
┌─────────────────────────────────────────────────────────┐
│ SIAD COMMAND CENTER                                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │                                                  │  │
│  │          [HERO PREDICTION IMAGE]                │  │
│  │          (Best-case tile, before/after)         │  │
│  │          Tile: x002_y001                         │  │
│  │          Confidence: 94% (Structural)           │  │
│  │                                                  │  │
│  │                                                  │  │
│  │    6-Month Satellite Predictions                │  │
│  │    Powered by SIAD World Model                  │  │
│  │                                                  │  │
│  │    [EXPLORE GALLERY] [INTERACTIVE MAP]          │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Quick Stats                                      │  │
│  │ • 15 tiles analyzed                             │  │
│  │ • 3 high-confidence hotspots detected          │  │
│  │ • 6-month rollout horizon                      │  │
│  │ • Model validation loss: 0.0131                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ What is SIAD?                                    │  │
│  │ A world model trained on monthly satellite      │  │
│  │ imagery that predicts future observations and   │  │
│  │ detects persistent anomalies that deviate from  │  │
│  │ weather-baseline expectations.                  │  │
│  │                                                  │  │
│  │ Use counterfactual scenarios to isolate        │  │
│  │ infrastructure changes from weather-driven     │  │
│  │ variation.                                       │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Screen 2: Gallery View

**Viewport: Full desktop, 3-column grid**

```
┌─────────────────────────────────────────────────────────┐
│ Gallery                                       [← Back]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Category: [Best ▼]  Tier: [All ▼]  Month: [All ▼]     │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Rank: 1      │  │ Rank: 2      │  │ Rank: 3      │  │
│  │              │  │              │  │              │  │
│  │ [THUMBNAIL]  │  │ [THUMBNAIL]  │  │ [THUMBNAIL]  │  │
│  │ x000_y001    │  │ x001_y003    │  │ x002_y002    │  │
│  │              │  │              │  │              │  │
│  │ Score: 0.042 │  │ Score: 0.038 │  │ Score: 0.036 │  │
│  │ Struct: 91%  │  │ Struct: 88%  │  │ Struct: 85%  │  │
│  │              │  │              │  │              │  │
│  │ [View Tile]  │  │ [View Tile]  │  │ [View Tile]  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Rank: 4      │  │ Rank: 5      │  │ Rank: 6      │  │
│  │              │  │              │  │              │  │
│  │ [THUMBNAIL]  │  │ [THUMBNAIL]  │  │ [THUMBNAIL]  │  │
│  │ ...          │  │ ...          │  │ ...          │  │
│  │              │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│ [← Previous] [1] [2] [3] [4] [5] [Next →]              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Hover Card Expansion:**
On hover, card expands to show before/after swipe:
```
  ┌─────────────────────────────┐
  │ Rank: 1 (x000_y001)         │
  │ ┌──────────────────────────┐│
  │ │ [GROUND TRUTH ←→ PRED]   ││
  │ │ (Swipeable)              ││
  │ └──────────────────────────┘│
  │ Score: 0.042  Str: 91%      │
  │ Detected: May 2026          │
  │ Attribution: SAR + Optical  │
  │                             │
  │ [View Full Tile] [Compare]  │
  └─────────────────────────────┘
```

### Screen 3: Tile Inspector (Full Screen)

**Viewport: 1400px+ (see Section 4, Flow 1)**

Key zones:
1. **Top Left (60% width):** Live prediction image + timeline
2. **Top Right (40% width):** Climate scenario controls
3. **Bottom Left (60%):** Modality toggles, comparison options
4. **Bottom Right (40%):** Metadata, residual stats, confidence

### Screen 4: Hex Map View

**Viewport: Full desktop, interactive canvas**

```
┌─────────────────────────────────────┐
│ [← Back]                             │
├─────────────────────────────────────┤
│                                     │
│    ◇ ◇ ◇ ◇ ◇ ◇ ◇                  │
│   ◇ ◇ 🟢 ◇ 🔴 ◇ ◇ ◇                │
│  ◇ ◇ ◇ 🟡 ◇ ◇ 🟡 ◇ ◇              │
│   ◇ ◇ ◇ ◇ ◇ ◇ ◇ ◇                │
│    ◇ ◇ ◇ ◇ ◇ ◇ ◇                  │
│                                     │
│ Hotspots (3):                       │
│ • tile_x000_y001 (May, Struct 91%)  │
│ • tile_x003_y001 (Jun, Act 78%)     │
│ • tile_x002_y004 (Apr, Env 65%)     │
│                                     │
│ Legend:                             │
│ 🟢 Low (1-25%)  🟡 Med (26-75%)     │
│ 🔴 High (76-99%) 🔴 *Flagged       │
└─────────────────────────────────────┘
```

---

## 7. Tactical Interface Principles

### 7.1 Data-Dense but Scannable

**Implementation:**
- **Visual hierarchy:** Use color, size, weight to guide eye
- **Grid alignment:** All elements snap to 4px grid
- **Whitespace intentional:** Gutters 12–16px between sections
- **Icons + text:** Pair every control with an icon (SAR icon, rainfall icon, etc.)
- **Micro-interactions:** Hover states (glow), selected states (amber highlight)

Example: Climate control slider should immediately signal "rainfall" via icon + label + color

### 7.2 Real-Time Feedback

**Performance targets:**
- **Slider drag → image update:** <500ms (accept 1s if GPU inference required)
- **Timeline scrub → image update:** <200ms (cached/precomputed)
- **Heatmap toggle:** Instant (already rendered)
- **Comparison toggle:** <200ms crossfade
- **Modality filter → recompute:** <2s (server inference)

**Loading states:**
- Spinner (pulsing cyan glow) during inference
- Progress bar for long operations (gallery generate)
- Optimistic updates: show slider change before result arrives

### 7.3 Professional/Military Aesthetic

**Visual language:**
- **Color palette:** Dark (charcoal #0a0a0a), cyan accents, amber for critical
- **Typography:** Rajdhani for headers (geometric, structured), JetBrains Mono for data
- **Borders:** Sharp 1px lines (no rounded corners except badges)
- **Shadows:** Subtle (0.5–1px blur), dark backgrounds
- **Glows:** Cyan glow on hover, amber glow on selection (10–20px blur)
- **Grid:** Visible 16px grid in background (optional, low opacity)

**References:**
- Palantir Gotham (dark, geometric, clean)
- Anduril interfaces (tactical overlays, high contrast)
- HUD aesthetics (transparent panels, data overlays)

### 7.4 Confidence Signals

**Show uncertainty/confidence through:**

1. **Confidence Bar (0–100%)**
   ```
   Prediction Confidence: ████████░░ (82%)
   ```

2. **Hotspot Tier Badges**
   - 🟢 High Confidence (Structural)
   - 🟡 Medium Confidence (Activity)
   - 🟡 Low Confidence (Environmental)

3. **Modality Attribution**
   - "SAR-dominant" → structural (reliable)
   - "Optical-only" → vegetation/water (seasonal)
   - "Multi-modal agreement" → high trust

4. **Residual Trend**
   - ↑ increasing residual (anomaly growing)
   - ↔ stable residual (static change)
   - ↓ decreasing residual (false alarm fade)

5. **Valid Pixel %**
   - >95% → good data quality
   - 80–95% → acceptable
   - <80% → flag (clouds, artifacts)

---

## 8. Mobile/Responsive Considerations

### Breakpoint: Tablet (768–1024px)
- 2-column gallery grid
- Hex map becomes smaller
- Tile Inspector: stack left/right panels vertically
- Climate controls: 2-month slider rows

### Breakpoint: Mobile (< 768px)
- **Not primary target** (intel analysts use desktops)
- **If needed:** Simplified view
  - Gallery only (cards full width)
  - Hero tile large
  - No hex map
  - Climate controls hidden by default

---

## 9. Accessibility

### 9.1 Keyboard Navigation

| Key | Action |
|---|---|
| `Tab` | Focus through all interactive elements |
| `Enter`/`Space` | Activate button/toggle |
| `Arrow Left/Right` | Scrub timeline, adjust slider |
| `Escape` | Close modal, return to gallery |
| `?` | Show help panel (hotkeys) |
| `Ctrl+S` | Export/save current tile |

### 9.2 Screen Reader Support

- **Images:** Alt text format: "Satellite prediction for [tile_id], [month], residual [score]"
- **Buttons:** Descriptive labels (not just "View")
- **Sliders:** ARIA labels: "Rainfall anomaly for March: [value]σ"
- **Heatmap toggle:** "Residual heatmap: on/off"

### 9.3 Color Accessibility

- **Not color-only:** Use icons + text + color
  - Red/green hotspots also tagged "High"/"Low"
  - Cyan/amber states also labeled "Hover"/"Selected"
- **Contrast ratios:**
  - Text on background: ≥4.5:1 (WCAG AA)
  - UI elements (borders): ≥3:1

### 9.4 Motion & Animation

- All animations ≤500ms
- Respect `prefers-reduced-motion`
- Disable autoplay (timeline loop) by default
- Warn before heavy operations (gallery generate)

---

## 10. Error States & Edge Cases

### 10.1 No Data / Empty States

**Gallery:** "No predictions match your filters"
**Hex map:** "Loading tiles... [spinner]"
**Tile inspector:** "Failed to load tile (network error) [Retry]"

### 10.2 Inference Failures

**Too long inference:** Show "Computation in progress... (30s elapsed)"
**Server error:** "Model service unavailable. Try again in 5 minutes."
**Invalid scenario:** "Temperature too extreme. Range: -3σ to +3σ"

### 10.3 Old/Outdated Model

**If checkpoint outdated:** Show "⚠ Model version is 2 months old. Results may be less accurate."

---

## 11. Information Architecture (Site Map)

```
Landing Page
├── [Explore Gallery]
│   ├── Gallery View (Category selector)
│   │   ├── Best Predictions
│   │   ├── Worst Predictions
│   │   └── Average Predictions
│   │
│   └── [Click Tile] → Tile Inspector
│       ├── Imagery + Timeline
│       ├── Scenario Controls
│       ├── Metadata + Residuals
│       ├── Comparison Mode
│       └── [Compare / Export / Back]
│
├── [Interactive Hex Map]
│   ├── 2D Grid (SF Bay Area)
│   │   ├── [Click Hex] → Tile Inspector
│   │   ├── Hover → Tooltip
│   │   └── Hotspot Legend
│   │
│   └── (Hex Map links to same Tile Inspector)
│
└── [Help / About]
    ├── Model Overview
    ├── Keyboard Shortcuts
    ├── How to Interpret Results
    └── Data Lineage
```

---

## 12. Performance & Technical Constraints

### 12.1 Image Optimization

- **Prediction images:** 256×256px, JPG or WebP, max 30KB
- **Heatmap overlays:** PNG (lossless), max 50KB
- **Gallery thumbnails:** 200×200px, WebP, max 10KB

### 12.2 Caching Strategy

- **Ground truth imagery:** Cache indefinitely (static)
- **Predictions (neutral scenario):** Cache for session
- **Scenario variants:** Cache for 5 minutes (or until new scenario)
- **Gallery metadata:** Cache for 24 hours

### 12.3 API Response Times

- `GET /tiles` → <100ms
- `POST /predict` (inference) → <1s (cached) or <10s (fresh)
- `GET /gallery` → <200ms

---

## 13. Future Enhancements (Post-MVP)

1. **Video playback:** Smooth 6-month animation (instead of month-by-month)
2. **3D globe view:** Global tile coverage (when expanded)
3. **Collaborative annotations:** Teams mark hotspots, leave comments
4. **Advanced filtering:** ML-powered search ("show me tiles with SAR changes")
5. **Export to Geojson:** Download predictions as vector tiles
6. **Time-series forecasting:** Show 12-month rollout (not just 6)
7. **Uncertainty quantification:** Per-pixel confidence maps

---

## 14. Design Tokens Reference

All colors, fonts, spacing are defined in `/frontend/src/styles/tokens.json` (already created).

### Key Tokens:
- **Primary background:** `#0a0a0a`
- **Accent (hover):** `#14b8a6` (cyan)
- **Accent (selected):** `#f59e0b` (amber)
- **Text primary:** `#f5f5f5`
- **Font (headers):** Rajdhani
- **Font (data):** JetBrains Mono
- **Spacing base:** 4px (grid)
- **Border radius:** 0 (sharp) or 0.5rem (badges)

---

## 15. Revision Log

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-03-03 | Initial spec: landing, gallery, tile inspector, hex map, climate controls, accessibility |
| (Next) | TBD | TBD |

---

## Appendix: ASCII Reference Diagrams

### Hotspot Confidence Tier System
```
┌─────────────────────────────────┐
│ STRUCTURAL (High Confidence)    │
│ • SAR signature change          │
│ • Often corr. with lights       │
│ • Persistent 2+ months          │
│ • Confidence: 80–99%            │
│ Color: 🔴 Red/Amber             │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ ACTIVITY (Medium Confidence)    │
│ • Lights change                 │
│ • SAR secondary signal          │
│ • May be seasonal               │
│ • Confidence: 60–80%            │
│ Color: 🟡 Yellow                │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ ENVIRONMENTAL (Low Confidence) │
│ • Vegetation/water primary      │
│ • Weak SAR signal               │
│ • Likely seasonal               │
│ • Confidence: 40–60%            │
│ Color: 🟢 Green                 │
└─────────────────────────────────┘
```

### Residual Score Interpretation
```
Low Residual (0.0–0.05):
  ✓ Prediction matches reality
  ✓ Model is confident & accurate
  ✓ No anomaly detected

Medium Residual (0.05–0.10):
  ~ Modest deviation
  ~ May indicate emerging change
  ~ Or weather-driven variation

High Residual (0.10–0.20+):
  ⚠ Strong deviation
  ⚠ Potential infrastructure change
  ⚠ Or data quality issue
```

---

**End of UX Specification**

For questions or clarifications, reach out to the Product/Design team.
