# SIAD Dashboard Screen Mockup v1.0

**Overview Screen - Hotspot Detection Dashboard**

Last Updated: 2026-03-03
Design Lead: Agent 3 (Design)

---

## Screen Purpose

The Dashboard is the primary entry point for analysts to:
- View ranked list of detected hotspots
- See geographic distribution on map
- Filter by date range, score threshold, and alert type
- Select hotspot to view detailed analysis

**Target Users:** Military/intelligence analysts, satellite imagery analysts
**Usage Context:** Long-session analysis (hours), low-light environment

---

## Screen Dimensions

```
Desktop (Primary): 1440px × 900px (16:10 aspect ratio)
Minimum: 1280px × 720px
Maximum: 1920px × 1080px
```

**Layout Structure:**
- Header: 64px fixed height
- Content: calc(100vh - 64px) flexible
- Sidebar (Hotspot List): 400px fixed width
- Main (Map View): flex-grow
- Filter Panel: 280px height (bottom of sidebar)

---

## Full Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  SIAD Detection System                          Jun 2024 - Dec 2024          [?] [Settings]  │ ← Header (64px)
├─────────────────────────┬────────────────────────────────────────────────────────────────────┤
│                         │                                                                    │
│  TOP HOTSPOTS (47)      │                      MAP VIEW                                      │
│                         │                                                                    │
│ ┌─────────────────────┐ │  ┌──────────────────────────────────────────────────────────────┐ │
│ │ #1  Mission Bay Dev │ │  │                                                              │ │
│ │                     │ │  │         [Interactive Hex Map]                                │ │
│ │ Score: 0.82  │ Jun  │ │  │                                                              │ │
│ │ Duration: 4mo│Struct│ │  │         - Hexagonal grid overlay                             │ │
│ │                     │ │  │         - Color-coded by max score                           │ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓░  82%  │ │  │         - Zoom/pan controls                                  │ │
│ └─────────────────────┘ │  │         - Clicking hex shows detail                          │ │
│                         │  │                                                              │ │
│ ┌─────────────────────┐ │  │                                                              │ │
│ │ #2  Oakland Port    │ │  │                  San Francisco Bay                           │ │
│ │                     │ │  │                       Region                                 │ │
│ │ Score: 0.76  │ Jul  │ │  │                                                              │ │
│ │ Duration: 3mo│Activ │ │  │                                                              │ │
│ │                     │ │  │                                                              │ │
│ │ ▓▓▓▓▓▓▓▓▓░░   76%  │ │  │                                                              │ │
│ └─────────────────────┘ │  │                                                              │ │
│                         │  │                                                              │ │
│ [... 8 more cards ...]  │  │                                                              │ │
│                         │  │                                                              │ │
│ ┌─────────────────────┐ │  │                                                              │ │
│ │ FILTERS             │ │  │                                                              │ │
│ │                     │ │  │                                                              │ │
│ │ Date Range          │ │  │                                                              │ │
│ │ ├───●─────────●────┤│ │  │                                                              │ │
│ │ Jan 24      Dec 24  │ │  │                                                              │ │
│ │                     │ │  │                                                              │ │
│ │ Min Score: 0.5      │ │  │                                                              │ │
│ │ ├─────●──────────┤ │ │  │                                                              │ │
│ │                     │ │  │                                                              │ │
│ │ Alert Type:         │ │  │                                                              │ │
│ │ ●Structural ○Activ  │ │  │                                                              │ │
│ │ ○All                │ │  │                                                              │ │
│ │                     │ │  └──────────────────────────────────────────────────────────────┘ │
│ │ [Apply Filters]     │ │                                                                    │
│ └─────────────────────┘ │                                                                    │
└─────────────────────────┴────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Header (64px height)

**Layout:**
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [Logo] SIAD Detection System          Jun 2024 - Dec 2024    [?] [Settings] │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Specifications:**

#### Logo & Title (Left Section)
```css
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-left: 48px;
}

.header-logo {
  width: 32px;
  height: 32px;
  /* Satellite icon or SIAD emblem */
}

.header-title {
  font-family: var(--font-ui);
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}
```

#### Date Range (Center Section)
```css
.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--font-data);
  font-size: 14px;
  color: var(--data-value);
  font-weight: 500;
}
```

#### Actions (Right Section)
```css
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-right: 48px;
}

.header-icon-button {
  width: 36px;
  height: 36px;
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.header-icon-button:hover {
  border-color: var(--data-value);
  background: rgba(0, 217, 255, 0.1);
}
```

#### Header Container
```css
.dashboard-header {
  height: 64px;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}
```

---

### 2. Sidebar (400px width)

**Layout:**
```
┌─────────────────────────┐
│ TOP HOTSPOTS (47)       │ ← Section title (40px)
│                         │
│ [Scrollable list]       │ ← Hotspot cards (variable)
│ - Card 1                │
│ - Card 2                │
│ - ...                   │
│ - Card 10               │
│                         │
│ ┌─────────────────────┐ │
│ │ FILTERS             │ │ ← Filter panel (280px)
│ │ ...                 │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

**Specifications:**

#### Sidebar Container
```css
.dashboard-sidebar {
  width: 400px;
  height: calc(100vh - 64px);
  background: var(--bg-base);
  border-right: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
```

#### Section Title
```css
.sidebar-title {
  height: 40px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-subtle);
}

.sidebar-title-text {
  font-family: var(--font-ui);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-title-count {
  font-family: var(--font-data);
  font-size: 12px;
  color: var(--data-value);
  font-weight: 600;
}
```

**HTML Example:**
```html
<div class="sidebar-title">
  <span class="sidebar-title-text">Top Hotspots</span>
  <span class="sidebar-title-count">(47)</span>
</div>
```

#### Hotspot List (Scrollable)
```css
.sidebar-hotspot-list {
  flex-grow: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Custom scrollbar */
.sidebar-hotspot-list::-webkit-scrollbar {
  width: 6px;
}

.sidebar-hotspot-list::-webkit-scrollbar-track {
  background: rgba(230, 232, 235, 0.05);
}

.sidebar-hotspot-list::-webkit-scrollbar-thumb {
  background: rgba(230, 232, 235, 0.2);
  border-radius: 3px;
}

.sidebar-hotspot-list::-webkit-scrollbar-thumb:hover {
  background: var(--data-value);
}
```

**Content:** 10 Hotspot Cards (see Component Specs for card design)

---

### 3. Filter Panel (280px height, bottom of sidebar)

**Layout:**
```
┌─────────────────────────┐
│ FILTERS                 │ ← Title (32px)
├─────────────────────────┤
│ Date Range              │
│ ├───●─────────●────┤    │ ← Range slider (60px)
│ Jan 24      Dec 24      │
│                         │
│ Min Score: 0.5          │
│ ├─────●──────────┤      │ ← Single slider (52px)
│                         │
│ Alert Type:             │
│ ● Structural  ○ Activity│ ← Radio buttons (52px)
│ ○ All                   │
│                         │
│ [Apply Filters]         │ ← Button (44px)
└─────────────────────────┘
```

**Specifications:**

#### Filter Container
```css
.sidebar-filters {
  height: 280px;
  padding: 16px 24px;
  background: var(--bg-elevated);
  border-top: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  gap: 16px;
}
```

#### Filter Title
```css
.filter-title {
  font-family: var(--font-ui);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}
```

#### Date Range Slider
```css
.filter-date-range {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-date-label {
  font-family: var(--font-ui);
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.filter-date-slider {
  /* Dual-thumb range slider */
  height: 6px;
  background: rgba(230, 232, 235, 0.1);
  border-radius: 3px;
  position: relative;
}

.filter-date-range-values {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-data);
  font-size: 11px;
  color: var(--data-label);
}
```

#### Min Score Slider
```css
.filter-score {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-score-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.filter-score-label {
  font-family: var(--font-ui);
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.filter-score-value {
  font-family: var(--font-data);
  font-size: 13px;
  color: var(--data-value);
  font-weight: 600;
}

.filter-score-slider {
  /* Single-thumb slider */
  height: 6px;
  background: rgba(230, 232, 235, 0.1);
  border-radius: 3px;
}
```

#### Alert Type Radio Buttons
```css
.filter-alert-type {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-alert-options {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-radio-option {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.filter-radio-button {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-default);
  border-radius: 50%;
  position: relative;
  transition: all var(--transition-fast);
}

.filter-radio-button.selected {
  border-color: var(--data-value);
}

.filter-radio-button.selected::after {
  content: '';
  width: 8px;
  height: 8px;
  background: var(--data-value);
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.filter-radio-label {
  font-family: var(--font-ui);
  font-size: 12px;
  color: var(--text-secondary);
}

.filter-radio-option:hover .filter-radio-label {
  color: var(--text-primary);
}
```

#### Apply Button
```css
.filter-apply-button {
  width: 100%;
  height: 36px;
  background: var(--data-value);
  color: var(--bg-base);
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font-ui);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-apply-button:hover {
  background: lighten(var(--data-value), 10%);
  box-shadow: 0 0 12px rgba(0, 217, 255, 0.5);
}

.filter-apply-button:active {
  transform: scale(0.98);
}
```

---

### 4. Map View (Main Content Area)

**Layout:**
```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  [Zoom Controls]                                           │
│   + -  □                                                   │
│                                                            │
│                   [Interactive Hex Map]                    │
│                                                            │
│           ⬡ ⬡ ⬡ ⬡ ⬡                                       │
│          ⬡ ⬡ ⬡ ⬡ ⬡ ⬡                                     │
│           ⬡ ⬡ ⬡ ⬡ ⬡                                       │
│          ⬡ ⬡ ⬡ ⬡ ⬡ ⬡                                     │
│           ⬡ ⬡ ⬡ ⬡ ⬡                                       │
│                                                            │
│                San Francisco Bay Region                    │
│                                                            │
│  [Legend]                                                  │
│  Score: ▓ 0.8-1.0  ▒ 0.6-0.8  ░ 0.4-0.6  □ <0.4          │
└────────────────────────────────────────────────────────────┘
```

**Specifications:**

#### Map Container
```css
.dashboard-map {
  flex-grow: 1;
  height: calc(100vh - 64px);
  background: var(--bg-base);
  position: relative;
  overflow: hidden;
}
```

#### Zoom Controls (Top-Left)
```css
.map-controls {
  position: absolute;
  top: 24px;
  left: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10;
}

.map-control-button {
  width: 36px;
  height: 36px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.map-control-button:hover {
  border-color: var(--data-value);
  background: rgba(0, 217, 255, 0.1);
  color: var(--data-value);
}
```

**Buttons:**
- `+` Zoom In
- `-` Zoom Out
- `□` Reset View

#### Hex Grid Overlay
```css
.map-hex-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.map-hex-cell {
  stroke: var(--border-subtle);
  stroke-width: 1px;
  cursor: pointer;
  pointer-events: all;
  transition: all var(--transition-fast);
}

/* Color-code by score */
.map-hex-cell[data-score="high"] {
  fill: var(--alert-high);
  fill-opacity: 0.4;
}

.map-hex-cell[data-score="medium"] {
  fill: var(--alert-medium);
  fill-opacity: 0.3;
}

.map-hex-cell[data-score="low"] {
  fill: var(--alert-low);
  fill-opacity: 0.2;
}

.map-hex-cell[data-score="none"] {
  fill: transparent;
}

.map-hex-cell:hover {
  stroke: var(--data-value);
  stroke-width: 2px;
  fill-opacity: 0.6;
}

.map-hex-cell.selected {
  stroke: var(--data-value);
  stroke-width: 3px;
  fill-opacity: 0.7;
}
```

#### Legend (Bottom-Right)
```css
.map-legend {
  position: absolute;
  bottom: 24px;
  right: 24px;
  background: rgba(21, 25, 34, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.map-legend-title {
  font-family: var(--font-ui);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.map-legend-items {
  display: flex;
  gap: 12px;
}

.map-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.map-legend-swatch {
  width: 16px;
  height: 16px;
  border-radius: 2px;
  border: 1px solid var(--border-subtle);
}

.map-legend-label {
  font-family: var(--font-data);
  font-size: 10px;
  color: var(--text-secondary);
}
```

#### Map Tooltip (on hex hover)
```css
.map-tooltip {
  position: absolute;
  background: var(--bg-overlay);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-size: 12px;
  color: var(--text-primary);
  box-shadow: var(--shadow-md);
  pointer-events: none;
  z-index: 100;
}

.map-tooltip-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.map-tooltip-data {
  font-family: var(--font-data);
  font-size: 11px;
  color: var(--data-value);
}
```

**Tooltip Content (on hex hover):**
```
Tile: tile_042
Region: Mission Bay
Max Score: 0.82
Onset: Jun 2024
```

---

## Interaction Flows

### 1. Hotspot Selection

**Trigger:** Click on hotspot card in sidebar
**Behavior:**
1. Highlight selected card (cyan border, background tint)
2. Pan map to corresponding hex tile
3. Highlight hex on map (cyan stroke, increased opacity)
4. Show route animation from card to map

**Visual Feedback:**
```css
.hotspot-card.selected {
  border: 2px solid var(--data-value);
  background: rgba(0, 217, 255, 0.05);
  transform: translateX(4px);
}

.map-hex-cell.selected {
  stroke: var(--data-value);
  stroke-width: 3px;
  fill-opacity: 0.7;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
```

---

### 2. Hex Click (Map to Detail)

**Trigger:** Click on hex tile in map
**Behavior:**
1. Navigate to detail screen for that hotspot
2. Transition animation (slide left)
3. Preserve filter state in URL params

**URL Structure:**
```
/dashboard?start=2024-01&end=2024-12&min_score=0.5&alert=all
/hotspot/:hotspot_id?month=2024-06
```

---

### 3. Filter Application

**Trigger:** Click "Apply Filters" button
**Behavior:**
1. Disable button, show loading spinner
2. Fetch filtered hotspots from API
3. Update hotspot list (fade out old, fade in new)
4. Update map hexes (remove/add based on filters)
5. Update count in sidebar title
6. Re-enable button

**Loading State:**
```css
.filter-apply-button.loading {
  pointer-events: none;
  opacity: 0.6;
}

.filter-apply-button.loading::after {
  content: '';
  width: 16px;
  height: 16px;
  border: 2px solid var(--bg-base);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

---

### 4. Scroll Behavior

**Sidebar Hotspot List:**
- Smooth scroll
- Show scrollbar on hover
- Maintain scroll position after filter update
- Infinite scroll (load more on scroll bottom)

**Map View:**
- Pan with mouse drag
- Zoom with scroll wheel
- Pinch to zoom (touch devices)
- Momentum scrolling

---

## Responsive Behavior

### Desktop (>= 1440px) - Primary Target
- Sidebar: 400px fixed
- Map: Flex-grow
- All components full-size

### Large Desktop (>= 1920px)
- Sidebar: 480px
- Map: Flex-grow
- Increase font sizes by 10%

### Tablet (768px - 1439px)
- Sidebar: 320px
- Map: Flex-grow
- Smaller font sizes
- Compact hotspot cards (reduce padding)

### Mobile (< 768px) - Not Required for MVP
- Stack layout (no sidebar)
- Full-width hotspot list
- Swipe to switch between list/map
- Bottom sheet filters

---

## Empty States

### No Hotspots Found

```
┌─────────────────────────┬────────────────────────────────────────────────┐
│                         │                                                │
│  TOP HOTSPOTS (0)       │                                                │
│                         │                                                │
│ ┌─────────────────────┐ │              [Search Icon]                     │
│ │                     │ │                                                │
│ │  [Search Icon]      │ │         No hotspots detected                   │
│ │                     │ │         in selected date range.                │
│ │  No hotspots found  │ │                                                │
│ │                     │ │         Try:                                   │
│ │  Try expanding the  │ │         - Expanding date range                 │
│ │  date range or      │ │         - Lowering min score threshold         │
│ │  lowering min score │ │         - Selecting "All" alert types          │
│ │                     │ │                                                │
│ └─────────────────────┘ │                                                │
└─────────────────────────┴────────────────────────────────────────────────┘
```

**Styling:**
```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.empty-state-icon {
  width: 64px;
  height: 64px;
  opacity: 0.3;
  margin-bottom: 24px;
}

.empty-state-title {
  font-family: var(--font-ui);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.empty-state-description {
  font-family: var(--font-ui);
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 320px;
}

.empty-state-suggestions {
  margin-top: 16px;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.8;
}

.empty-state-suggestions strong {
  color: var(--data-value);
}
```

---

### Loading State

```
┌─────────────────────────┬────────────────────────────────────────────────┐
│                         │                                                │
│  TOP HOTSPOTS           │                                                │
│                         │                                                │
│ ┌─────────────────────┐ │            [Spinner Animation]                 │
│ │ [Skeleton Card 1]   │ │                                                │
│ └─────────────────────┘ │         Loading hotspots...                    │
│                         │                                                │
│ ┌─────────────────────┐ │         Analyzing residuals across             │
│ │ [Skeleton Card 2]   │ │         47 tiles for Jun-Dec 2024              │
│ └─────────────────────┘ │                                                │
│                         │         (Est. 3 seconds)                       │
└─────────────────────────┴────────────────────────────────────────────────┘
```

**Skeleton Card:**
```css
.skeleton-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  height: 140px;
  position: relative;
  overflow: hidden;
}

.skeleton-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(230, 232, 235, 0.05),
    transparent
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  to { left: 100%; }
}
```

---

### Error State

```
┌─────────────────────────┬────────────────────────────────────────────────┐
│                         │                                                │
│  TOP HOTSPOTS           │                                                │
│                         │                                                │
│ ┌─────────────────────┐ │         [Alert Triangle Icon]                  │
│ │                     │ │                                                │
│ │  [Alert Icon]       │ │      Failed to load hotspot data               │
│ │                     │ │                                                │
│ │  Error loading data │ │      Error: Connection timeout                 │
│ │                     │ │      (Server did not respond in time)          │
│ │  [Retry Button]     │ │                                                │
│ │                     │ │      [ Retry ]                                 │
│ └─────────────────────┘ │                                                │
└─────────────────────────┴────────────────────────────────────────────────┘
```

**Styling:**
```css
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.error-state-icon {
  width: 64px;
  height: 64px;
  color: var(--alert-high);
  margin-bottom: 24px;
}

.error-state-title {
  font-family: var(--font-ui);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.error-state-message {
  font-family: var(--font-data);
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 320px;
  margin-bottom: 24px;
}

.error-state-retry {
  padding: 8px 24px;
  background: transparent;
  border: 1px solid var(--alert-high);
  border-radius: var(--radius-sm);
  color: var(--alert-high);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.error-state-retry:hover {
  background: rgba(255, 71, 87, 0.1);
}
```

---

## Accessibility Features

### Keyboard Navigation

**Tab Order:**
1. Header help button
2. Header settings button
3. Sidebar hotspot cards (1-10)
4. Filter date range slider
5. Filter min score slider
6. Filter radio buttons (Structural, Activity, All)
7. Apply filters button
8. Map zoom controls
9. Map hex cells (in reading order)

**Keyboard Shortcuts:**
- `Tab` / `Shift+Tab`: Navigate between elements
- `Enter` / `Space`: Activate button/card
- `Arrow Keys`: Navigate between radio buttons
- `Esc`: Deselect hotspot, close tooltip
- `/` : Focus filter panel (quick search)

### Screen Reader Labels

```html
<!-- Hotspot Card -->
<article
  role="button"
  aria-label="Hotspot rank 1, Mission Bay Development, high priority, score 0.82, onset June 2024"
  tabindex="0"
>
  <!-- Card content -->
</article>

<!-- Filter Slider -->
<input
  type="range"
  aria-label="Minimum score threshold"
  aria-valuemin="0"
  aria-valuemax="1"
  aria-valuenow="0.5"
  aria-valuetext="0.5 out of 1.0"
>

<!-- Map Hex -->
<polygon
  role="button"
  aria-label="Tile tile_042, Mission Bay region, score 0.82"
  tabindex="0"
>
```

### Focus Indicators

```css
*:focus-visible {
  outline: 2px solid var(--data-value);
  outline-offset: 2px;
}

.hotspot-card:focus-visible {
  border-color: var(--data-value);
  box-shadow: 0 0 0 3px rgba(0, 217, 255, 0.2);
}
```

---

## Performance Considerations

### Optimization Strategies

1. **Virtual Scrolling** (Hotspot List)
   - Render only visible cards (10-15)
   - Use `react-window` or similar
   - Recycle DOM elements

2. **Map Rendering**
   - Use WebGL for hex layer (Deck.gl)
   - Tile-based loading (load visible region only)
   - Debounce zoom/pan events

3. **Data Caching**
   - Cache hotspot data by filter params
   - Use SWR or React Query for smart refetch
   - Cache map tiles locally

4. **Code Splitting**
   - Lazy load map component
   - Lazy load filter panel
   - Preload on route hover

### Performance Targets

- **Initial Load:** < 2 seconds (on 3G)
- **Filter Update:** < 500ms
- **Map Pan/Zoom:** 60 FPS
- **Hotspot Card Hover:** < 16ms (instant)

---

## Implementation Checklist

### Phase 1: Layout (Week 1)
- [ ] Header component with logo, title, actions
- [ ] Sidebar container with scroll
- [ ] Main content area (map placeholder)
- [ ] Responsive grid system

### Phase 2: Components (Week 1-2)
- [ ] Hotspot card component (all states)
- [ ] Filter panel (sliders, radio, button)
- [ ] Map controls (zoom buttons)
- [ ] Empty state component
- [ ] Loading state (skeleton cards)
- [ ] Error state component

### Phase 3: Interactions (Week 2)
- [ ] Card selection (highlight, map sync)
- [ ] Filter application (API call, update)
- [ ] Map hex hover/click
- [ ] Keyboard navigation
- [ ] Focus management

### Phase 4: Map Integration (Week 2-3)
- [ ] Base map layer (Mapbox/Leaflet)
- [ ] Hex overlay layer
- [ ] Color-coding by score
- [ ] Tooltip on hover
- [ ] Click to detail view

### Phase 5: Polish (Week 3)
- [ ] Transitions/animations
- [ ] Loading states
- [ ] Error handling
- [ ] Accessibility testing
- [ ] Performance optimization

---

## Design Handoff Assets

### Required Files
1. **Figma/Sketch File** (if available)
2. **Icon Set** (SVG exports)
   - Search icon
   - Alert triangle icon
   - Settings icon
   - Help icon
   - Zoom in/out/reset icons
3. **Color Palette** (CSS variables file)
4. **Typography Spec** (Font files + CSS)
5. **Component Storybook** (if using Storybook)

### Export Locations
- `/siad-command-center/frontend/public/designs/` (mockups)
- `/siad-command-center/frontend/src/assets/icons/` (SVG icons)
- `/siad-command-center/frontend/src/styles/tokens.css` (design tokens)

---

## Version History

- **v1.0** (2026-03-03): Initial dashboard mockup
  - Full layout specification
  - All component placements
  - Interaction flows defined
  - Empty/loading/error states
  - Responsive breakpoints
  - Accessibility features

---

**Dashboard Mockup Status:** ✓ Complete - Ready for Agent 4 Implementation

**Next Steps:**
1. Create detail screen mockup (Week 2)
2. Export design assets
3. Conduct design review with team
4. Hand off to Agent 4 for implementation

**Contact:** Agent 3 (Design)
**Dependencies:** Agent 4 (Frontend), Agent 5 (UX), Agent 6 (Copy)
