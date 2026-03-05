# SIAD Interaction Specification

**Version:** 1.0
**Last Updated:** 2026-03-03
**Owner:** Agent 5 (UX/Interaction)
**For Implementation by:** Agent 4 (Frontend)

---

## Interaction Design Principles

### 1. Immediate Feedback (< 100ms)
Every user action receives instant visual acknowledgment

### 2. Debounced Computations (300-500ms)
Expensive operations wait for user to finish input

### 3. Progressive Loading
Show content as soon as available, enhance progressively

### 4. Forgiving Interactions
Undo, reset, and cancel options for all significant actions

---

## Component-Level Interactions

---

## 1. Token Heatmap

**Context:** Hotspot detail page, shows 16×16 grid of latent tokens colored by residual value

### 1.1 Hover Interaction

**Trigger:** Mouse enters token cell
**Timing:** < 50ms to show tooltip
**Visual Feedback:**
- Token cell brightens (lighten by 10%)
- Subtle border appears (1px solid white, 50% opacity)
- Crosshair guides appear (optional, for precision)

**Tooltip Content:**
```
┌─────────────────────────┐
│ Token: R12C8            │
│ Residual: 0.87          │
│ Coordinates: 37.76°N,   │
│              122.39°W   │
│ Click to zoom imagery   │
└─────────────────────────┘
```

**Tooltip Position:**
- Follow cursor with 10px offset
- Smart positioning (avoid edge clipping)
- Arrow points to token center

**Exit Behavior:**
- Tooltip fades out over 150ms
- Cell returns to normal state immediately

---

### 1.2 Click Interaction

**Trigger:** Mouse click on token cell
**Timing:** < 100ms to highlight, 200-500ms to sync imagery

**Immediate Feedback (< 100ms):**
- Token cell highlighted with thick border (3px solid yellow)
- Cell scale increases slightly (105% transform)
- Ripple animation from click point (optional)

**Secondary Feedback (200-500ms):**
- Imagery viewer scrolls/zooms to corresponding pixel region
- Smooth animated transition (easing: ease-out)
- Region outline appears in imagery (yellow box)

**Persistent State:**
- Highlighted token remains highlighted until:
  - Another token is clicked (transfer highlight)
  - User clicks outside heatmap (clear highlight)
  - User presses Escape (clear highlight)

**Visual State:**
```
Normal Token:     [  0.45  ]
Hovered Token:    [  0.45  ]  (lighter background)
Clicked Token:    [ >0.45< ]  (border + scale)
```

---

### 1.3 Drag Interaction (Optional, for Large Datasets)

**Trigger:** Mouse down + move on heatmap canvas
**Timing:** 60fps smooth panning

**Behavior:**
- Cursor changes to grab hand (open) on hover over draggable area
- Cursor changes to grabbing hand (closed) while dragging
- Heatmap pans in direction of drag
- Inertia scrolling on release (deceleration over 300ms)

**Constraints:**
- Can't pan beyond heatmap bounds
- Edge resistance (rubber band effect at boundaries)

**Accessibility:**
- Keyboard alternative: Arrow keys to pan (10% viewport per press)

---

### 1.4 Scroll/Zoom Interaction

**Trigger:** Mouse wheel scroll over heatmap
**Timing:** Smooth zoom animation 200ms

**Behavior:**
- Scroll up: Zoom in (scale += 0.1, max 3x)
- Scroll down: Zoom out (scale -= 0.1, min 1x)
- Zoom center point: Current mouse position
- Token grid scales while maintaining aspect ratio

**Visual Feedback:**
- Zoom level indicator in corner (e.g., "2.5x")
- Reset zoom button appears when zoomed (> 1x)

**Keyboard Alternative:**
- `+` / `-` keys to zoom in/out
- `0` key to reset to 1x

---

## 2. Hotspot Card (Dashboard)

**Context:** Dashboard list item, represents a single hotspot

### 2.1 Hover Interaction

**Trigger:** Mouse enters card area
**Timing:** < 50ms

**Visual Feedback:**
- Subtle border glow (0px → 2px shadow, color: brand-primary)
- Card elevates slightly (box-shadow increases)
- Background lightens (5% lighter)
- "View Details" arrow appears/animates in

**Map Sync (Optional, if map present):**
- After 300ms hover (debounced): Show preview on map
- Map marker pulses at hotspot location
- Hover ends: Preview fades out over 200ms

**CSS Transition:**
```css
transition: all 200ms ease-out;
```

---

### 2.2 Click Interaction

**Trigger:** Mouse click anywhere on card
**Timing:** < 100ms to navigate

**Immediate Feedback:**
- Card flashes (quick opacity change: 1 → 0.8 → 1, 150ms total)
- Ripple effect from click point (material design style)

**Navigation:**
- Route to hotspot detail page
- Smooth page transition (fade out/in, 300ms)
- Preserve scroll position in history (for back navigation)

**Loading State:**
- If detail page data not ready: Show skeleton screen immediately
- Don't wait for data before navigating (optimistic navigation)

---

### 2.3 Keyboard Focus Interaction

**Trigger:** Tab key navigation
**Timing:** Instant

**Visual Feedback:**
- 2px solid outline (color: focus-ring, typically blue)
- Outline offset: 2px (clear separation from card)
- Card slightly highlights (same as hover, but distinct outline)

**Keyboard Actions:**
- `Enter` or `Space`: Open detail page (same as click)
- `j` / `k`: Move focus to next/previous card
- `Escape`: Remove focus

---

### 2.4 Right-Click Context Menu (Optional)

**Trigger:** Right mouse button click on card
**Timing:** < 100ms to show menu

**Context Menu Options:**
```
┌──────────────────────────┐
│ Open in New Tab          │
│ Export as GeoJSON        │
│ Flag for Review          │
│ Copy Coordinates         │
│ ────────────────────     │
│ Dismiss as False Positive│
└──────────────────────────┘
```

**Menu Behavior:**
- Appears at cursor position
- Smart positioning (stay on screen)
- Dismiss on: Click outside, Escape key, select option

---

## 3. Timeline Chart

**Context:** Hotspot detail page, line chart showing score over time

### 3.1 Hover over Data Point

**Trigger:** Mouse within 10px radius of data point
**Timing:** < 50ms

**Visual Feedback:**
- Data point enlarges (radius: 4px → 8px)
- Vertical crosshair line appears (from point to x-axis)
- Horizontal line to y-axis (optional, shows score level)

**Tooltip Content:**
```
┌─────────────────────────┐
│ June 2024               │
│ Score: 0.67             │
│ Confidence: Medium      │
│ Click to jump to month  │
└─────────────────────────┘
```

**Tooltip Position:**
- Above data point (10px offset)
- If near top edge: Position below point

---

### 3.2 Click on Month

**Trigger:** Click on data point or month label
**Timing:** 200-500ms to load imagery

**Immediate Feedback:**
- Data point highlights (fill with accent color)
- Month label underlines

**Action:**
- Imagery viewer jumps to that month
- Smooth transition (fade between months, 400ms)
- Timeline remains visible (split view or sticky header)

**State Persistence:**
- Clicked month remains highlighted
- Clear with: Click another month, press Escape

---

### 3.3 Drag Range Selection (Advanced)

**Trigger:** Mouse down on timeline, drag to select range
**Timing:** Real-time visual feedback during drag

**Visual Feedback:**
- Shaded region between start and end points
- Start/end points show date labels
- Selected area highlights (semi-transparent overlay)

**On Release:**
- Modal or panel appears: "Analyze June - August 2024?"
- Options: "Export Range", "View Average", "Cancel"

**Keyboard Alternative:**
- Click first month, Shift+Click second month to select range

---

## 4. Environmental Controls

**Context:** Hotspot detail page, sliders for rain and temperature normalization

### 4.1 Toggle Normalization Switch

**Trigger:** Click toggle switch
**Timing:** < 50ms to update UI, 300-800ms to compute

**Immediate Feedback (< 50ms):**
- Switch animates to new position (slide + color change)
- Label updates: "Off" → "On" or vice versa
- Controls panel expands/collapses (slide animation, 200ms)

**State Changes:**
- OFF → ON: Controls slide in from collapsed state
- ON → OFF: Controls slide out, confirm modal if values changed?

**Animation:**
```css
transition: all 200ms ease-in-out;
```

---

### 4.2 Slider Drag Interaction

**Trigger:** Mouse down on slider handle, drag
**Timing:** Real-time visual update, debounced API call (300ms)

**Immediate Visual Feedback:**
- Slider handle follows cursor precisely (60fps)
- Current value displays above handle (live update)
- Slider track fills/empties to show value
- Value label updates in real-time (e.g., "+15% Rain")

**Debounced Computation:**
- Wait 300ms after user stops dragging
- Show loading spinner near affected component (score badge)
- API call: Recompute residuals with new environmental params

**On Computation Complete:**
- Score updates with smooth number transition (count-up animation)
- If score changes significantly (>20%): Show badge "Score changed!"
- Color-code change: Green (decreased) / Red (increased)

**Visual States:**
```
Dragging:     [===|----]  +25%  ⟳ Computing...
Complete:     [===|----]  +25%  Score: 0.45 ↓
```

---

### 4.3 Reset Button

**Trigger:** Click "Reset" button
**Timing:** < 100ms to reset, 300ms to recompute

**Immediate Feedback:**
- Button click animation (scale down/up, 100ms)
- Sliders animate back to center (0 position)
- Value labels reset to "0% Rain", "0°C Temp"

**Computation:**
- Recompute residuals with neutral environmental params
- Show loading state (same as slider drag)
- Score returns to baseline value

**Animation:**
- Slider handles smoothly slide to center (300ms ease-out)
- Synchronized animation (all sliders reset together)

---

### 4.4 Preset Buttons (Optional)

**Trigger:** Click preset button (e.g., "Wet Season", "Dry Season")
**Timing:** < 100ms to apply preset

**Immediate Feedback:**
- Button highlights (active state)
- Sliders animate to preset values
- Tooltip shows: "Simulating +40% rain, +5°C temp"

**Presets:**
- "Wet Season": Rain +40%, Temp +5°C
- "Dry Season": Rain -30%, Temp +10°C
- "Winter": Rain +20%, Temp -10°C
- "Neutral": Rain 0%, Temp 0°C (same as reset)

---

## 5. Baseline Comparison Chart

**Context:** Hotspot detail page, bar chart comparing world model to baselines

### 5.1 Hover over Bar

**Trigger:** Mouse enters bar area
**Timing:** < 50ms

**Visual Feedback:**
- Bar brightens (opacity increases)
- Tooltip appears above bar

**Tooltip Content:**
```
┌─────────────────────────────┐
│ Persistence Baseline        │
│ Residual: 0.68 ± 0.04       │
│ 24% worse than World Model  │
└─────────────────────────────┘
```

**Tooltip Formatting:**
- Bold model name
- Show confidence interval
- Percentage difference from best model (if not best)

---

### 5.2 Click to Highlight

**Trigger:** Click on bar
**Timing:** < 100ms

**Behavior:**
- Bar remains highlighted (border + glow)
- Explanation text updates to focus on this model
- Side-by-side comparison appears (optional): "World Model vs Persistence"

**Persistent State:**
- Highlight remains until: Click another bar, click outside, Escape

---

### 5.3 Toggle Baseline Visibility

**Trigger:** Click checkbox next to baseline name in legend
**Timing:** < 200ms animation

**Behavior:**
- Bar fades out if unchecked (opacity 1 → 0, 200ms)
- Chart re-scales to fit remaining bars (animated)
- Checkbox state persists (local storage)

**Accessibility:**
- Keyboard: Tab to checkbox, Space to toggle

---

## 6. Filter Panel (Dashboard)

**Context:** Dashboard sidebar or collapsible panel

### 6.1 Date Range Picker

**Trigger:** Click on date input field
**Timing:** < 100ms to show calendar

**Behavior:**
- Calendar popup appears below input (or above if near bottom)
- Current range highlighted in calendar
- Click date to select start, click again for end
- Drag across dates to select range (advanced)

**Immediate Feedback:**
- Selected dates highlight instantly
- Input field updates with formatted date
- "Apply" button enables (if auto-apply is off)

**Debounced Filter:**
- If auto-apply: Wait 500ms after last date selection
- If manual apply: Wait for "Apply Filters" button click

**Preset Ranges:**
- "Last 30 days" button
- "Last 3 months" button
- "This year" button
- "Custom" (manual date picker)

---

### 6.2 Score Threshold Slider

**Trigger:** Drag slider handle
**Timing:** Real-time visual, debounced filter (500ms)

**Immediate Feedback:**
- Slider value updates in real-time (e.g., "0.65")
- Preview count updates (debounced 300ms): "~15 hotspots"

**Debounced Filter:**
- Wait 500ms after user stops dragging
- Apply filter, reload hotspot list
- Show loading skeleton during reload

**Visual Hint:**
- Color-code slider track:
  - Low (0-0.3): Gray (few results)
  - Medium (0.3-0.7): Yellow (balanced)
  - High (0.7-1.0): Red (high confidence only)

---

### 6.3 Alert Type Dropdown

**Trigger:** Click dropdown button
**Timing:** < 100ms to open menu

**Dropdown Options:**
```
[v] Structural Acceleration
[v] Activity Surge
[ ] Environmental (excluded by default)
[ ] Anomaly (rare events)
```

**Behavior:**
- Checkboxes allow multiple selection
- "Apply" button or auto-apply on check/uncheck
- Selected types show as chips below dropdown

**Immediate Feedback:**
- Checkbox animates (checkmark slides in)
- Chip appears/disappears below (slide animation)

---

### 6.4 Reset Filters Button

**Trigger:** Click "Reset All Filters" button
**Timing:** < 100ms to reset

**Behavior:**
- All filters return to default values (animated)
- Hotspot list reloads with defaults
- Confirmation modal if user has unsaved work? (optional)

**Animation:**
- Sliders slide to default positions
- Dropdowns collapse
- Date pickers clear
- All synchronized (simultaneous reset)

---

## 7. Export Modal

**Context:** Triggered by "Export" button on dashboard or detail page

### 7.1 Modal Open Animation

**Trigger:** Click "Export" button
**Timing:** 200ms fade-in

**Animation:**
- Backdrop fades in (opacity 0 → 0.5, 200ms)
- Modal slides in from top (translateY -20px → 0, 200ms)
- Focus traps inside modal (keyboard navigation)

**Initial State:**
- All checkboxes unchecked (user must select format)
- "Export" button disabled until format selected

---

### 7.2 Format Selection

**Trigger:** Click checkbox or radio button
**Timing:** < 50ms

**Options:**
```
Format:
( ) GeoJSON
( ) CSV
( ) KML
( ) Shapefile

Include:
[v] Coordinates
[v] Scores
[v] Timeline Data
[ ] Imagery Links
```

**Immediate Feedback:**
- Selected format highlights
- Preview text updates: "Exporting 10 hotspots as GeoJSON..."
- "Export" button enables

---

### 7.3 Export Progress

**Trigger:** Click "Export" button
**Timing:** 1-5 seconds depending on data size

**Progress Indicator:**
- Progress bar (0% → 100%)
- Status text: "Generating GeoJSON... (3 of 10 hotspots)"
- Animated spinner (optional, alongside progress bar)

**On Complete:**
- Success toast: "Export complete! (Download)"
- Auto-download file (or show download link)
- Modal remains open (allow another export) or closes (user preference)

**On Error:**
- Error message in modal: "Export failed. Please try again."
- Retry button
- "Contact Support" link with pre-filled error details

---

## 8. Search/Filter Input

**Context:** Dashboard top bar, global search

### 8.1 Focus Interaction

**Trigger:** Click input field or press `/` key
**Timing:** < 50ms

**Immediate Feedback:**
- Input field border highlights (thicker, accent color)
- Placeholder text changes: "Search hotspots..." → "Type to filter..."
- Cursor blinks in input field

**Keyboard Shortcut:**
- `/` key focuses search from anywhere on page
- `Escape` clears search and removes focus

---

### 8.2 Type to Search

**Trigger:** User types in input field
**Timing:** Debounced search (300ms)

**Immediate Visual Feedback:**
- Characters appear in input field (60fps typing)
- "Clear" button (X icon) appears after first character

**Debounced Search:**
- Wait 300ms after last keystroke
- Send search query to API
- Show loading spinner in input field (right side)

**Results:**
- Hotspot list filters in real-time
- Result count updates: "5 results for 'Mission Bay'"
- Highlight matching terms in results (bold)

**No Results:**
- Show empty state: "No hotspots match 'xyz'"
- Suggestions: "Try different keywords or reset filters"

---

### 8.3 Clear Search

**Trigger:** Click "X" button in input field
**Timing:** < 100ms

**Behavior:**
- Input field clears instantly
- Search results reset to full list
- Focus remains in input field (allow new search)

**Animation:**
- "X" button fades out
- Input text fades out (don't just delete, animate)

---

## 9. Satellite Imagery Viewer

**Context:** Hotspot detail page, before/after comparison

### 9.1 Image Comparison Slider

**Trigger:** Drag vertical divider between before/after images
**Timing:** 60fps smooth dragging

**Immediate Feedback:**
- Divider follows cursor precisely
- Before image reveals/hides based on divider position
- Current position percentage shows (optional): "50%"

**Constraints:**
- Divider constrained to image bounds (10% - 90%)
- Edge resistance at boundaries

**Keyboard Alternative:**
- Arrow keys to move divider (5% increments)
- `0` key to center (50/50 split)

---

### 9.2 Zoom Controls

**Trigger:** Click zoom buttons or scroll over image
**Timing:** < 200ms smooth zoom

**Buttons:**
- `+` button: Zoom in (scale += 0.2, max 5x)
- `-` button: Zoom out (scale -= 0.2, min 1x)
- `Reset` button: Return to 1x fit

**Scroll Zoom:**
- Same as heatmap (scroll to zoom, center on cursor)

**Visual Feedback:**
- Zoom level indicator: "2.5x"
- Smooth animation (ease-out, 200ms)

---

### 9.3 Pan Image

**Trigger:** Click and drag on image (when zoomed > 1x)
**Timing:** 60fps panning

**Behavior:**
- Cursor changes to grab hand
- Image pans in drag direction
- Inertia on release (deceleration)

**Constraints:**
- Can't pan beyond image bounds
- Rubber band effect at edges

---

### 9.4 Date Navigation (Timeline Sync)

**Trigger:** Click month in timeline
**Timing:** 400ms to load and transition

**Loading State:**
- Show loading spinner overlay on image
- Current image fades out (opacity 1 → 0.3)

**Transition:**
- New image fades in (opacity 0 → 1, 400ms)
- Crossfade effect (blend between images)

**State Sync:**
- Timeline month highlights
- Image caption updates: "June 2024"

---

## Timing Summary

| Action | Immediate Feedback | Completion | Total |
|--------|-------------------|------------|-------|
| Button Click | < 50ms (visual state) | N/A | 50ms |
| Hover Tooltip | < 50ms (show) | 150ms (fade out) | 200ms |
| Slider Drag | 16ms (60fps) | 300ms (debounce) | 316ms |
| Filter Apply | < 100ms (UI update) | 500ms (API call) | 600ms |
| Navigate Page | < 100ms (route) | 300ms (transition) | 400ms |
| Residual Compute | < 100ms (loading state) | 800ms (API) | 900ms |
| Export | < 100ms (modal open) | 1-5s (generation) | 1-5s |

---

## Animation Easing Functions

### Default Transitions
```css
transition: all 200ms ease-out;
```

### Specific Use Cases
- **Entrance animations:** `ease-out` (fast start, slow end)
- **Exit animations:** `ease-in` (slow start, fast end)
- **Hover effects:** `ease-in-out` (smooth both ends)
- **Physics-based:** `cubic-bezier(0.34, 1.56, 0.64, 1)` (bounce effect)

---

## Touch/Mobile Interactions

### Token Heatmap (Touch)
- Tap: Highlight + zoom imagery (same as click)
- Long press: Show tooltip (equivalent to hover)
- Pinch to zoom: Standard pinch gesture
- Two-finger drag: Pan heatmap

### Hotspot Card (Touch)
- Tap: Navigate to detail (same as click)
- Swipe left: Quick action menu (export, flag)
- Long press: Context menu (same as right-click)

### Timeline (Touch)
- Tap point: Jump to month (same as click)
- Drag range: Two-finger selection

### Sliders (Touch)
- Large touch target (44px minimum)
- Haptic feedback on value snap points (optional)

---

## Accessibility Enhancements

### Focus Indicators
All interactive elements must have visible focus:
```css
:focus-visible {
  outline: 2px solid var(--focus-ring-color);
  outline-offset: 2px;
}
```

### ARIA Live Regions
Dynamic updates announced to screen readers:
```html
<div aria-live="polite" aria-atomic="true">
  Score updated: 0.82 (High confidence)
</div>
```

### Keyboard Navigation
- Tab order follows visual layout (left-to-right, top-to-bottom)
- Shortcuts don't conflict with browser/screen reader shortcuts
- All shortcuts listed in help modal (`?` key)

---

## Error Handling Interactions

### Failed API Call
1. Show toast notification (top-right, 5s auto-dismiss)
2. Replace affected component with error state
3. Provide retry button
4. Log error details (for support)

### Network Offline
1. Detect offline state (navigator.onLine)
2. Show banner at top: "You're offline. Some features unavailable."
3. Disable actions requiring network
4. Cache available for offline viewing (service worker)

### Invalid Input
1. Inline error message below input field
2. Red border on input
3. Error icon (!) next to input
4. Focus returns to invalid field

---

## Performance Targets

### Interaction Response Times
- **Instant:** < 100ms (feels immediate)
- **Quick:** 100ms - 1s (perceptible, but fast)
- **Slow:** 1s - 5s (needs progress indicator)
- **Very Slow:** > 5s (needs progress + cancel button)

### Animation Frame Rate
- **Smooth:** 60fps (16.67ms per frame)
- **Acceptable:** 30fps (33.33ms per frame)
- **Janky:** < 30fps (avoid)

### Debounce Delays
- **Typing/search:** 300ms
- **Slider drag:** 300ms
- **Resize events:** 150ms
- **Scroll events:** 100ms

---

## Next Steps

1. **Review with Agent 4 (Frontend):** Implementation feasibility and technical constraints
2. **Create prototypes:** Interactive mockups for user testing
3. **Design keyboard shortcuts:** Task 3
4. **Define empty/loading/error states:** Week 2 Task 6

---

**Deliverable Status:** COMPLETE ✓
**Dependencies:** Agent 4 (implementation), Agent 3 (visual design for states)
