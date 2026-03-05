# SIAD Component Specifications v1.0

**Detailed Component Design Specifications**

Last Updated: 2026-03-03
Design Lead: Agent 3 (Design)

---

## Overview

This document specifies the 5 core components for the SIAD detection interface:

1. **Token Heatmap** - 16×16 grid visualizing residual patterns
2. **Hotspot Card** - Ranked list item showing hotspot metadata
3. **Timeline Chart** - Line chart showing score evolution
4. **Environmental Controls** - Weather parameter sliders
5. **Baseline Comparison** - Bar chart comparing model performance

All components follow the [Design System](/docs/DESIGN_SYSTEM.md) tokens.

---

## 1. Token Heatmap

### Purpose
Visualize the 16×16 token residual pattern for a specific tile and month. Allows analysts to identify which spatial regions show anomalous behavior.

### Data Source
API: `GET /api/tiles/{tile_id}/heatmap?month=YYYY-MM`

Returns: 16×16 array of residual values (0.0 - 1.0)

---

### Dimensions

```
Total Size: 400px × 400px (including padding)
Grid Size:  384px × 384px (16 cells × 24px)
Cell Size:  24px × 24px
Cell Gap:   0px (no gap, borders define cells)
Padding:    8px all sides
```

**Layout:**
```
┌────────────────────────────────────────┐
│        Token Heatmap - Jun 2024        │ ← Header: 24px height
├────────────────────────────────────────┤
│ ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐ │
│ │▓▓│▓▓│░░│░░│▒▒│▓▓│▓▓│▓▓│░░│▒▒│▓▓│▓▓│ │ ← Each cell: 24×24px
│ ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤ │
│ │▓▓│▓▓│░░│▒▒│▓▓│▓▓│▓▓│▓▓│▒▒│▓▓│▓▓│▓▓│ │
│ │  ... (16 rows total) ...           │ │
│ └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘ │
│                                        │
│ Color Scale: 0.0 ───────────── 1.0    │ ← Legend: 32px height
│             Blue → Yellow → Red        │
└────────────────────────────────────────┘
```

---

### Styling

#### Container
```css
.heatmap-container {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-2);
  width: 400px;
  height: 480px; /* Including header + legend */
}
```

#### Header
```css
.heatmap-header {
  font-family: var(--font-ui);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-2);
  text-align: center;
}
```

#### Grid
```css
.heatmap-grid {
  display: grid;
  grid-template-columns: repeat(16, 24px);
  grid-template-rows: repeat(16, 24px);
  gap: 0;
  border: 1px solid var(--border-default);
}
```

#### Cell
```css
.heatmap-cell {
  width: 24px;
  height: 24px;
  border: 1px solid rgba(10, 14, 20, 0.5); /* Subtle border in bg-base */
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

/* Color mapping (use Viridis scale) */
.heatmap-cell[data-value="0.0"] { background: #440154; }
.heatmap-cell[data-value="0.1"] { background: #482677; }
.heatmap-cell[data-value="0.2"] { background: #31688E; }
.heatmap-cell[data-value="0.3"] { background: #26828E; }
.heatmap-cell[data-value="0.4"] { background: #35B779; }
.heatmap-cell[data-value="0.5"] { background: #6ECE58; }
.heatmap-cell[data-value="0.6"] { background: #B5DE2B; }
.heatmap-cell[data-value="0.7"] { background: #FDE724; }
.heatmap-cell[data-value="0.8"] { background: #FDE724; }
.heatmap-cell[data-value="0.9"] { background: #FDE724; }
/* Interpolate for granular values */

/* Hover state */
.heatmap-cell:hover {
  border: 2px solid var(--text-primary);
  z-index: 10;
  box-shadow: 0 0 4px rgba(255, 255, 255, 0.3);
}

/* Selected state (if implementing click-to-select) */
.heatmap-cell.selected {
  border: 2px solid var(--data-value);
  z-index: 11;
}
```

---

### Interactions

#### Hover Tooltip
**Trigger:** Mouse hover over cell
**Display:** Tooltip above/beside cell
**Content:**
```
Token: [row, col] (e.g., "Token: [3, 7]")
Residual: 0.67
```

**Tooltip Styling:**
```css
.heatmap-tooltip {
  background: var(--bg-overlay);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  font-family: var(--font-data);
  font-size: 12px;
  color: var(--text-primary);
  box-shadow: var(--shadow-md);
  pointer-events: none;
  position: absolute;
  z-index: 100;
}

.heatmap-tooltip-label {
  color: var(--data-label);
  font-weight: 500;
}

.heatmap-tooltip-value {
  color: var(--data-value);
  font-weight: 600;
}
```

#### Click Interaction (Optional)
**Trigger:** Click on cell
**Action:** Highlight cell, optionally show detailed panel with:
- Satellite imagery for that token region
- Historical residuals for that token
- Neighboring token values

---

### Legend

```css
.heatmap-legend {
  margin-top: var(--space-2);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.heatmap-legend-gradient {
  height: 8px;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    to right,
    #440154,  /* 0.0 */
    #31688E,  /* 0.3 */
    #35B779,  /* 0.5 */
    #FDE724   /* 1.0 */
  );
}

.heatmap-legend-labels {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-data);
  font-size: 11px;
  color: var(--data-label);
}
```

**HTML Structure:**
```html
<div class="heatmap-legend">
  <div class="heatmap-legend-gradient"></div>
  <div class="heatmap-legend-labels">
    <span>0.0 (Low)</span>
    <span>0.5 (Medium)</span>
    <span>1.0 (High)</span>
  </div>
</div>
```

---

### Responsive Behavior

**Desktop (>= 1440px):** 400px × 480px (full size)
**Tablet (768-1439px):** Scale proportionally (80% = 320px × 384px)
**Mobile (< 768px):** Not required for MVP

---

### Implementation Notes

**For Agent 4:**
- Use canvas or SVG for rendering (better performance than 256 DOM elements)
- Implement color interpolation for smooth gradients (don't hardcode 10 colors)
- Use `d3-scale` or similar for Viridis colorscale mapping
- Debounce tooltip updates on rapid mouse movement
- Cache rendered heatmap by tile_id + month (avoid re-render on hover)

**Example (React + Canvas):**
```jsx
<HeatmapCanvas
  data={residuals}      // 16×16 array
  cellSize={24}
  colorScale="viridis"
  onCellHover={handleHover}
  onCellClick={handleClick}
/>
```

---

## 2. Hotspot Card

### Purpose
Display key metadata for a single hotspot in a compact, scannable format. Used in the ranked list on the dashboard.

### Data Source
API: `GET /api/hotspots`

Returns: Array of hotspot objects with:
- rank, tile_id, region, score, onset, duration, alert_type, confidence

---

### Dimensions

```
Width:  100% (flex container, typically 300-400px)
Height: 140px (fixed)
Padding: 16px
Gap between elements: 8px
```

**Layout:**
```
┌─────────────────────────────────────────┐
│ #1  Mission Bay Development        HIGH │ ← Header: rank + name + badge
│                                         │
│ Score: 0.82    |    Onset: Jun 2024    │ ← Metadata row 1
│ Duration: 4mo  |    Type: Structural   │ ← Metadata row 2
│                                         │
│ ▓▓▓▓▓▓▓▓▓▓▓▓░░░  82% Confidence        │ ← Confidence bar
│                                         │
│ [View Details →]                        │ ← Action button (optional)
└─────────────────────────────────────────┘
```

---

### Styling

#### Container
```css
.hotspot-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  min-height: 140px;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  transition: all var(--transition-fast);
  cursor: pointer;
}

/* Hover state */
.hotspot-card:hover {
  border-color: var(--data-value);
  box-shadow: var(--shadow-sm);
  transform: translateY(-2px);
}

/* Selected state */
.hotspot-card.selected {
  border: 2px solid var(--data-value);
  background: rgba(0, 217, 255, 0.05);
}
```

---

#### Header Section
```css
.hotspot-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  justify-content: space-between;
}

.hotspot-rank {
  font-family: var(--font-data);
  font-size: 18px;
  font-weight: 600;
  color: var(--data-value);
  min-width: 32px;
}

.hotspot-name {
  font-family: var(--font-ui);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  flex-grow: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hotspot-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.hotspot-badge.high {
  background: rgba(255, 71, 87, 0.15);
  color: var(--alert-high);
  border: 1px solid var(--alert-high);
}

.hotspot-badge.medium {
  background: rgba(255, 165, 2, 0.15);
  color: var(--alert-medium);
  border: 1px solid var(--alert-medium);
}

.hotspot-badge.low {
  background: rgba(255, 217, 61, 0.15);
  color: var(--alert-low);
  border: 1px solid var(--alert-low);
}
```

---

#### Metadata Section
```css
.hotspot-metadata {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hotspot-metadata-row {
  display: flex;
  gap: var(--space-3);
  align-items: center;
}

.hotspot-metadata-item {
  display: flex;
  gap: 6px;
  align-items: baseline;
}

.hotspot-metadata-label {
  font-family: var(--font-ui);
  font-size: 12px;
  color: var(--data-label);
  font-weight: 500;
}

.hotspot-metadata-value {
  font-family: var(--font-data);
  font-size: 13px;
  color: var(--data-value);
  font-weight: 500;
}

/* Divider between items */
.hotspot-metadata-row > *:not(:last-child)::after {
  content: "|";
  margin-left: var(--space-2);
  color: var(--border-strong);
}
```

---

#### Confidence Bar
```css
.hotspot-confidence {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hotspot-confidence-bar {
  height: 6px;
  background: rgba(230, 232, 235, 0.1);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.hotspot-confidence-fill {
  height: 100%;
  background: var(--data-value);
  border-radius: 3px;
  transition: width var(--transition-base);
}

/* High confidence (>80%) */
.hotspot-confidence-fill.high {
  background: var(--success);
}

/* Medium confidence (50-80%) */
.hotspot-confidence-fill.medium {
  background: var(--data-value);
}

/* Low confidence (<50%) */
.hotspot-confidence-fill.low {
  background: var(--alert-medium);
}

.hotspot-confidence-label {
  font-family: var(--font-data);
  font-size: 11px;
  color: var(--text-secondary);
  text-align: right;
}
```

---

### HTML Structure

```html
<div class="hotspot-card" data-hotspot-id="hs_001">
  <!-- Header -->
  <div class="hotspot-card-header">
    <span class="hotspot-rank">#1</span>
    <span class="hotspot-name">Mission Bay Development</span>
    <span class="hotspot-badge high">HIGH</span>
  </div>

  <!-- Metadata -->
  <div class="hotspot-metadata">
    <div class="hotspot-metadata-row">
      <div class="hotspot-metadata-item">
        <span class="hotspot-metadata-label">Score:</span>
        <span class="hotspot-metadata-value">0.82</span>
      </div>
      <div class="hotspot-metadata-item">
        <span class="hotspot-metadata-label">Onset:</span>
        <span class="hotspot-metadata-value">Jun 2024</span>
      </div>
    </div>
    <div class="hotspot-metadata-row">
      <div class="hotspot-metadata-item">
        <span class="hotspot-metadata-label">Duration:</span>
        <span class="hotspot-metadata-value">4mo</span>
      </div>
      <div class="hotspot-metadata-item">
        <span class="hotspot-metadata-label">Type:</span>
        <span class="hotspot-metadata-value">Structural</span>
      </div>
    </div>
  </div>

  <!-- Confidence Bar -->
  <div class="hotspot-confidence">
    <div class="hotspot-confidence-bar">
      <div class="hotspot-confidence-fill high" style="width: 82%;"></div>
    </div>
    <span class="hotspot-confidence-label">82% Confidence</span>
  </div>
</div>
```

---

### Interaction States

#### Default
- Border: 1px solid --border-default
- Background: --bg-elevated
- Cursor: pointer

#### Hover
- Border: 1px solid --data-value (cyan)
- Shadow: --shadow-sm
- Transform: translateY(-2px)

#### Selected
- Border: 2px solid --data-value
- Background: rgba(0, 217, 255, 0.05) (faint cyan tint)

#### Focus (Keyboard Navigation)
- Outline: 2px solid --data-value
- Outline-offset: 2px

---

### Variants

#### Alert Type Badge Colors
```css
/* Structural acceleration */
.hotspot-badge.structural { /* Use high styles */ }

/* Activity surge */
.hotspot-badge.activity {
  background: rgba(255, 165, 2, 0.15);
  color: var(--alert-medium);
  border: 1px solid var(--alert-medium);
}

/* Combined alert */
.hotspot-badge.combined {
  background: rgba(255, 71, 87, 0.15);
  color: var(--alert-high);
  border: 1px solid var(--alert-high);
}
```

---

### Responsive Behavior

**Desktop (>= 1440px):** Full size (300-400px width)
**Tablet (768-1439px):** Full width (minus padding)
**Mobile (< 768px):** Not required for MVP

---

### Implementation Notes

**For Agent 4:**
- Use semantic HTML (`<article>` for card, `<h3>` for name)
- Add `aria-label` for screen readers: "Hotspot rank 1, Mission Bay Development, high priority, score 0.82"
- Implement keyboard navigation (Enter/Space to select)
- Use CSS Grid for metadata rows (easier alignment)
- Animate confidence bar fill on mount (CSS animation or JS)

**Example (React):**
```jsx
<HotspotCard
  rank={1}
  name="Mission Bay Development"
  score={0.82}
  onset="2024-06"
  duration={4}
  alertType="structural"
  confidence="high"
  onSelect={handleSelect}
/>
```

---

## 3. Timeline Chart

### Purpose
Show the evolution of a hotspot's residual score over time, highlighting onset month and threshold crossings.

### Data Source
API: `GET /api/hotspots/{hotspot_id}/timeline`

Returns: Array of `{ month: "YYYY-MM", score: 0.0-1.0, confidence: "high|medium|low" }`

---

### Dimensions

```
Width:  500px (can flex to container)
Height: 250px
Padding: 16px
Chart Area: 468px × 180px (accounting for axes labels)
```

**Layout:**
```
┌──────────────────────────────────────────────┐
│           Residual Score Over Time           │ ← Title: 24px height
├──────────────────────────────────────────────┤
│ 1.0┤                                         │
│    │              ╱╲                         │
│ 0.8│         ╱───╱  ╲                        │
│    │    ╱───╱        ╲                       │
│ 0.6│   ╱              ╲─────╲                │
│    │  ╱                       ╲              │
│ 0.4│ ╱                         ╲             │
│    │╱                           ───          │
│ 0.2│- - - - - - - - - - - - - - - - - - - - │ ← Threshold line
│    │                                         │
│ 0.0└─┬───┬───┬───┬───┬───┬───┬───┬───┬──   │
│     Jan Feb Mar Apr May Jun Jul Aug Sep Oct  │ ← X-axis labels
│                     ↑                        │
│                   Onset                      │
└──────────────────────────────────────────────┘
```

---

### Styling

#### Container
```css
.timeline-chart {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  width: 500px;
  height: 250px;
}
```

#### Title
```css
.timeline-title {
  font-family: var(--font-ui);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: var(--space-2);
}
```

#### SVG Chart
```css
.timeline-svg {
  width: 468px;
  height: 180px;
}

/* Line */
.timeline-line {
  fill: none;
  stroke: var(--data-value);
  stroke-width: 2px;
  stroke-linejoin: round;
  stroke-linecap: round;
}

/* Data points */
.timeline-point {
  fill: var(--data-value);
  stroke: var(--bg-elevated);
  stroke-width: 2px;
  r: 4px;
  cursor: pointer;
  transition: r var(--transition-fast);
}

.timeline-point:hover {
  r: 6px;
  fill: var(--text-primary);
}

/* Onset marker */
.timeline-onset-marker {
  fill: var(--alert-high);
  stroke: var(--bg-elevated);
  stroke-width: 2px;
  r: 6px;
}

/* Threshold line */
.timeline-threshold {
  stroke: var(--alert-medium);
  stroke-width: 1px;
  stroke-dasharray: 4 4;
  opacity: 0.6;
}

/* Axes */
.timeline-axis-line {
  stroke: var(--border-default);
  stroke-width: 1px;
}

.timeline-axis-label {
  font-family: var(--font-data);
  font-size: 11px;
  fill: var(--data-label);
  text-anchor: middle;
}

.timeline-axis-title {
  font-family: var(--font-ui);
  font-size: 12px;
  fill: var(--text-secondary);
  font-weight: 500;
}

/* Grid lines (optional, subtle) */
.timeline-grid-line {
  stroke: var(--border-subtle);
  stroke-width: 1px;
  opacity: 0.3;
}
```

---

### Chart Elements

#### X-Axis (Time)
- **Position:** Bottom, 20px padding
- **Labels:** Month names (Jan, Feb, Mar...) or YYYY-MM for long ranges
- **Font:** var(--font-data), 11px
- **Color:** var(--data-label)
- **Spacing:** Evenly distributed based on data points

#### Y-Axis (Score)
- **Position:** Left, 40px padding
- **Range:** 0.0 - 1.0
- **Ticks:** 0.0, 0.2, 0.4, 0.6, 0.8, 1.0
- **Labels:** Aligned right, 2px padding from axis
- **Font:** var(--font-data), 11px
- **Color:** var(--data-label)

#### Threshold Line
- **Position:** Y = 0.5 (or configurable)
- **Style:** Dashed (4px dash, 4px gap)
- **Color:** var(--alert-medium) at 60% opacity
- **Label:** "Threshold" at right end (optional)

#### Onset Marker
- **Position:** At onset month
- **Style:** Red circle (r=6px), stroke=bg-elevated
- **Label:** "Onset" below X-axis
- **Color:** var(--alert-high)

#### Data Line
- **Interpolation:** Linear (straight lines between points)
- **Stroke:** var(--data-value), 2px
- **Smooth corners:** stroke-linejoin: round

#### Data Points
- **Style:** Circles (r=4px), filled
- **Color:** var(--data-value)
- **Hover:** Scale to r=6px, change to --text-primary

---

### Interactions

#### Hover on Data Point
**Trigger:** Mouse hover
**Display:** Tooltip with:
```
Month: Jun 2024
Score: 0.67
Confidence: High
```

**Tooltip Styling:** (same as heatmap tooltip)
```css
.timeline-tooltip {
  background: var(--bg-overlay);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-family: var(--font-data);
  font-size: 12px;
  color: var(--text-primary);
  box-shadow: var(--shadow-md);
}
```

#### Click on Data Point (Optional)
**Action:** Jump to that month in detail view or update imagery panel

---

### Legend

```css
.timeline-legend {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-2);
  justify-content: center;
}

.timeline-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-secondary);
}

.timeline-legend-icon {
  width: 16px;
  height: 2px;
  background: var(--data-value);
}

.timeline-legend-icon.threshold {
  background: var(--alert-medium);
  background-image: repeating-linear-gradient(
    to right,
    var(--alert-medium),
    var(--alert-medium) 4px,
    transparent 4px,
    transparent 8px
  );
}

.timeline-legend-icon.onset {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--alert-high);
}
```

---

### Responsive Behavior

**Desktop (>= 1440px):** 500px width
**Tablet (768-1439px):** Scale to container width (min 400px)
**Mobile:** Not required for MVP

---

### Implementation Notes

**For Agent 4:**
- Use D3.js or Recharts for charting (easier than raw SVG)
- Implement responsive resizing (listen to container width)
- Add transitions on data updates (animate line growth)
- Clip data points outside chart area
- Format dates consistently (use Intl.DateTimeFormat or date-fns)

**Example (React + Recharts):**
```jsx
<LineChart width={468} height={180} data={timelineData}>
  <CartesianGrid stroke="var(--border-subtle)" opacity={0.3} />
  <XAxis dataKey="month" tick={{ fill: 'var(--data-label)' }} />
  <YAxis domain={[0, 1]} tick={{ fill: 'var(--data-label)' }} />
  <Line
    type="linear"
    dataKey="score"
    stroke="var(--data-value)"
    strokeWidth={2}
    dot={{ r: 4, fill: 'var(--data-value)' }}
  />
  <ReferenceLine y={0.5} stroke="var(--alert-medium)" strokeDasharray="4 4" />
  <Tooltip content={<CustomTooltip />} />
</LineChart>
```

---

## 4. Environmental Controls

### Purpose
Allow analysts to adjust simulated weather parameters (rain, temperature) to test counterfactual scenarios. Shows whether detected changes persist under neutral weather conditions.

### Data Source
Not a display component - sends parameters back to API:
```
POST /api/detect/residuals
{
  "normalize_weather": true,
  "rain_anomaly_sigma": -1.5,
  "temp_anomaly_celsius": 2.0
}
```

---

### Dimensions

```
Width:  320px
Height: 240px
Padding: 16px
```

**Layout:**
```
┌──────────────────────────────────────────┐
│        Environmental Controls            │ ← Title
├──────────────────────────────────────────┤
│                                          │
│ Rain Anomaly:                     -1.5σ  │ ← Label + value
│ ├───────●──────────────────────────┤    │ ← Slider
│ -3σ                              +3σ     │ ← Min/max labels
│                                          │
│ Temperature Anomaly:              +2.0°C │
│ ├──────────────────●───────────────┤    │
│ -2°C                            +2°C     │
│                                          │
│ [ ] Normalize to Neutral Weather         │ ← Toggle
│                                          │
│ ┌──────────┐  ┌──────────┐             │
│ │  Reset   │  │  Apply   │             │ ← Action buttons
│ └──────────┘  └──────────┘             │
└──────────────────────────────────────────┘
```

---

### Styling

#### Container
```css
.env-controls {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
```

#### Title
```css
.env-controls-title {
  font-family: var(--font-ui);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-1);
}
```

---

#### Slider Component
```css
.env-slider-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.env-slider-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.env-slider-label {
  font-family: var(--font-ui);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.env-slider-value {
  font-family: var(--font-data);
  font-size: 13px;
  font-weight: 600;
  color: var(--data-value);
}

.env-slider-track {
  width: 100%;
  height: 6px;
  background: rgba(230, 232, 235, 0.1);
  border-radius: 3px;
  position: relative;
  cursor: pointer;
}

.env-slider-fill {
  height: 100%;
  background: var(--data-value);
  border-radius: 3px;
  position: absolute;
  left: 0;
  transition: width var(--transition-fast);
}

.env-slider-thumb {
  width: 16px;
  height: 16px;
  background: var(--data-value);
  border: 2px solid var(--bg-elevated);
  border-radius: 50%;
  position: absolute;
  top: -5px;
  cursor: grab;
  transition: all var(--transition-fast);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.env-slider-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 0 8px rgba(0, 217, 255, 0.5);
}

.env-slider-thumb:active {
  cursor: grabbing;
  transform: scale(1.1);
}

.env-slider-range {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
}

.env-slider-range-label {
  font-family: var(--font-data);
  font-size: 10px;
  color: var(--data-label);
}
```

---

#### Toggle Component
```css
.env-toggle-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2);
  background: rgba(230, 232, 235, 0.03);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
}

.env-toggle-switch {
  width: 40px;
  height: 20px;
  background: rgba(230, 232, 235, 0.2);
  border-radius: 10px;
  position: relative;
  cursor: pointer;
  transition: background var(--transition-base);
}

.env-toggle-switch.active {
  background: var(--data-value);
}

.env-toggle-thumb {
  width: 16px;
  height: 16px;
  background: var(--bg-elevated);
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: left var(--transition-base);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.env-toggle-switch.active .env-toggle-thumb {
  left: 22px;
}

.env-toggle-label {
  font-family: var(--font-ui);
  font-size: 13px;
  color: var(--text-secondary);
  flex-grow: 1;
}

.env-toggle-switch.active + .env-toggle-label {
  color: var(--data-value);
  font-weight: 500;
}
```

---

#### Action Buttons
```css
.env-controls-actions {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.env-button {
  flex: 1;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-family: var(--font-ui);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
}

.env-button-reset {
  background: transparent;
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
}

.env-button-reset:hover {
  border-color: var(--text-primary);
  color: var(--text-primary);
}

.env-button-apply {
  background: var(--data-value);
  color: var(--bg-base);
  font-weight: 600;
}

.env-button-apply:hover {
  background: lighten(var(--data-value), 10%);
  box-shadow: 0 0 8px rgba(0, 217, 255, 0.4);
}

.env-button-apply:active {
  transform: scale(0.98);
}
```

---

### HTML Structure

```html
<div class="env-controls">
  <h3 class="env-controls-title">Environmental Controls</h3>

  <!-- Rain Slider -->
  <div class="env-slider-group">
    <div class="env-slider-header">
      <span class="env-slider-label">Rain Anomaly</span>
      <span class="env-slider-value">-1.5σ</span>
    </div>
    <div class="env-slider-track">
      <div class="env-slider-fill" style="width: 25%;"></div>
      <div class="env-slider-thumb" style="left: 25%;"></div>
    </div>
    <div class="env-slider-range">
      <span class="env-slider-range-label">-3σ</span>
      <span class="env-slider-range-label">+3σ</span>
    </div>
  </div>

  <!-- Temperature Slider -->
  <div class="env-slider-group">
    <div class="env-slider-header">
      <span class="env-slider-label">Temperature Anomaly</span>
      <span class="env-slider-value">+2.0°C</span>
    </div>
    <div class="env-slider-track">
      <div class="env-slider-fill" style="width: 75%;"></div>
      <div class="env-slider-thumb" style="left: 75%;"></div>
    </div>
    <div class="env-slider-range">
      <span class="env-slider-range-label">-2°C</span>
      <span class="env-slider-range-label">+2°C</span>
    </div>
  </div>

  <!-- Normalize Toggle -->
  <div class="env-toggle-group">
    <div class="env-toggle-switch active">
      <div class="env-toggle-thumb"></div>
    </div>
    <label class="env-toggle-label">Normalize to Neutral Weather</label>
  </div>

  <!-- Action Buttons -->
  <div class="env-controls-actions">
    <button class="env-button env-button-reset">Reset</button>
    <button class="env-button env-button-apply">Apply</button>
  </div>
</div>
```

---

### Interactions

#### Slider Drag
**Trigger:** Click and drag thumb
**Behavior:**
- Update value label in real-time
- Clamp to min/max range
- Snap to reasonable increments (0.1σ for rain, 0.5°C for temp)

#### Toggle Click
**Trigger:** Click switch or label
**Behavior:**
- Animate thumb slide (200ms transition)
- Change background color to cyan when active
- Update label color to cyan when active

#### Reset Button
**Action:** Restore all sliders to neutral (0) and toggle to off

#### Apply Button
**Action:**
- Send parameters to API
- Show loading spinner
- Update heatmap/timeline with new residuals
- Highlight button briefly on success (green glow)

---

### Responsive Behavior

**Desktop (>= 1440px):** 320px fixed width
**Tablet (768-1439px):** Scale to container width
**Mobile:** Not required for MVP

---

### Implementation Notes

**For Agent 4:**
- Use native `<input type="range">` with custom styling, or build custom slider
- Debounce slider updates (don't fire API call on every pixel drag)
- Show loading state on Apply (disable inputs, show spinner)
- Validate input ranges (clamp to min/max)
- Store state in parent component to sync with other panels

**Example (React):**
```jsx
<EnvironmentalControls
  rainAnomaly={-1.5}
  tempAnomaly={2.0}
  normalizeWeather={true}
  onApply={(params) => fetchResiduals(params)}
  onReset={() => setDefaults()}
/>
```

---

## 5. Baseline Comparison

### Purpose
Show how the world model residuals compare to simpler baseline methods (persistence, seasonal), demonstrating the value of the latent residual approach.

### Data Source
API: `GET /api/baselines/{tile_id}?month=YYYY-MM`

Returns:
```json
{
  "residuals": {
    "world_model": 0.52,
    "persistence": 0.68,
    "seasonal": 0.71
  },
  "improvement": {
    "vs_persistence": 0.24,  // Lower is better
    "vs_seasonal": 0.27
  }
}
```

---

### Dimensions

```
Width:  320px
Height: 280px
Padding: 16px
```

**Layout:**
```
┌──────────────────────────────────────────┐
│        Baseline Comparison               │ ← Title
├──────────────────────────────────────────┤
│                                          │
│ World Model          0.52  ▓▓▓▓▓▓░░░░   │ ← Bar 1
│                            ↑ 24% better  │
│                                          │
│ Persistence          0.68  ▓▓▓▓▓▓▓▓░░   │ ← Bar 2
│                                          │
│ Seasonal             0.71  ▓▓▓▓▓▓▓▓▓░   │ ← Bar 3
│                                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                          │
│ Lower residual = better anomaly          │ ← Legend
│ detection capability                     │
└──────────────────────────────────────────┘
```

---

### Styling

#### Container
```css
.baseline-comparison {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
```

#### Title
```css
.baseline-title {
  font-family: var(--font-ui);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}
```

---

#### Bar Component
```css
.baseline-bar-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.baseline-bar-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 4px;
}

.baseline-bar-label {
  font-family: var(--font-ui);
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.baseline-bar-value {
  font-family: var(--font-data);
  font-size: 14px;
  font-weight: 600;
  color: var(--data-value);
}

.baseline-bar-track {
  width: 100%;
  height: 24px;
  background: rgba(230, 232, 235, 0.08);
  border-radius: var(--radius-sm);
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border-subtle);
}

.baseline-bar-fill {
  height: 100%;
  background: var(--data-value);
  border-radius: var(--radius-sm);
  transition: width var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
}

/* World Model (best) */
.baseline-bar-fill.world-model {
  background: var(--success);
}

/* Persistence */
.baseline-bar-fill.persistence {
  background: var(--data-value);
}

/* Seasonal (worst) */
.baseline-bar-fill.seasonal {
  background: var(--alert-medium);
}

.baseline-bar-improvement {
  font-size: 11px;
  color: var(--success);
  font-weight: 600;
  margin-left: 8px;
}
```

---

#### Legend
```css
.baseline-legend {
  padding-top: var(--space-2);
  border-top: 1px solid var(--border-subtle);
}

.baseline-legend-text {
  font-family: var(--font-ui);
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.4;
  text-align: center;
}

.baseline-legend-highlight {
  color: var(--success);
  font-weight: 600;
}
```

---

### HTML Structure

```html
<div class="baseline-comparison">
  <h3 class="baseline-title">Baseline Comparison</h3>

  <!-- World Model Bar -->
  <div class="baseline-bar-group">
    <div class="baseline-bar-header">
      <span class="baseline-bar-label">World Model</span>
      <span class="baseline-bar-value">0.52</span>
    </div>
    <div class="baseline-bar-track">
      <div class="baseline-bar-fill world-model" style="width: 52%;">
        <span class="baseline-bar-improvement">24% better ↓</span>
      </div>
    </div>
  </div>

  <!-- Persistence Bar -->
  <div class="baseline-bar-group">
    <div class="baseline-bar-header">
      <span class="baseline-bar-label">Persistence</span>
      <span class="baseline-bar-value">0.68</span>
    </div>
    <div class="baseline-bar-track">
      <div class="baseline-bar-fill persistence" style="width: 68%;"></div>
    </div>
  </div>

  <!-- Seasonal Bar -->
  <div class="baseline-bar-group">
    <div class="baseline-bar-header">
      <span class="baseline-bar-label">Seasonal</span>
      <span class="baseline-bar-value">0.71</span>
    </div>
    <div class="baseline-bar-track">
      <div class="baseline-bar-fill seasonal" style="width: 71%;"></div>
    </div>
  </div>

  <!-- Legend -->
  <div class="baseline-legend">
    <p class="baseline-legend-text">
      <span class="baseline-legend-highlight">Lower residual</span> = better anomaly detection capability
    </p>
  </div>
</div>
```

---

### Interactions

#### Hover on Bar
**Trigger:** Mouse hover
**Display:** Tooltip showing:
```
Method: World Model
Residual: 0.52
Improvement vs Persistence: 24%
Improvement vs Seasonal: 27%
```

**Optional:** Click to show detailed comparison chart

---

### Color Coding Logic

```javascript
function getBarColor(method, isLowest) {
  if (isLowest) return '--success';      // Green for best
  if (method === 'world_model') return '--success';
  if (method === 'persistence') return '--data-value';
  if (method === 'seasonal') return '--alert-medium';
}
```

---

### Responsive Behavior

**Desktop (>= 1440px):** 320px fixed width
**Tablet (768-1439px):** Scale to container width
**Mobile:** Not required for MVP

---

### Implementation Notes

**For Agent 4:**
- Animate bar widths on mount (CSS transition or GSAP)
- Sort bars by residual value (lowest first)
- Show improvement percentage only for world model
- Format percentages as integers (24%, not 24.3%)
- Update bars in real-time when environmental controls change

**Example (React):**
```jsx
<BaselineComparison
  worldModel={0.52}
  persistence={0.68}
  seasonal={0.71}
  improvements={{
    vs_persistence: 0.24,
    vs_seasonal: 0.27
  }}
/>
```

---

## Component Integration

### Data Flow

```
API
 ├─► Token Heatmap (GET /api/tiles/{id}/heatmap)
 ├─► Hotspot Card (GET /api/hotspots)
 ├─► Timeline Chart (GET /api/hotspots/{id}/timeline)
 ├─► Environmental Controls (POST /api/detect/residuals)
 └─► Baseline Comparison (GET /api/baselines/{id})
```

### Component Dependencies

```
Dashboard Screen
 ├─► Hotspot Card (list of 10)
 └─► Map View (not in this spec)

Detail Screen
 ├─► Timeline Chart
 ├─► Token Heatmap
 ├─► Environmental Controls
 └─► Baseline Comparison
```

---

## Accessibility Checklist

For all components:
- [ ] Keyboard navigable (Tab, Enter, Space, Arrow keys)
- [ ] Focus indicators visible (2px cyan outline)
- [ ] ARIA labels for interactive elements
- [ ] Color contrast meets WCAG AA (4.5:1 minimum)
- [ ] Screen reader friendly (semantic HTML, alt text)
- [ ] Tooltips dismissible with Escape key
- [ ] No reliance on color alone for information

---

## Design Handoff Checklist

- [ ] All dimensions specified in px
- [ ] All colors referenced from design system
- [ ] All fonts/sizes specified
- [ ] Interaction states documented (hover, active, disabled)
- [ ] Responsive breakpoints defined
- [ ] Example HTML provided
- [ ] Example CSS provided
- [ ] Component props/API defined
- [ ] Accessibility notes included

---

## Next Steps

1. **Create Dashboard Mockup** - Arrange components in full screen layout
2. **Create Detail Screen Mockup** - Show all components together
3. **Design Empty/Error States** - Handle edge cases
4. **Export Assets** - Icons, logos, etc.
5. **Write Handoff Doc** - Final package for Agent 4

---

## Version History

- **v1.0** (2026-03-03): Initial component specifications
  - Token Heatmap spec complete
  - Hotspot Card spec complete
  - Timeline Chart spec complete
  - Environmental Controls spec complete
  - Baseline Comparison spec complete

---

**Component Specs Status:** ✓ Complete - Ready for Dashboard Mockup

**Contact:** Agent 3 (Design)
**Next Deliverable:** Dashboard screen mockup (Task 3)
