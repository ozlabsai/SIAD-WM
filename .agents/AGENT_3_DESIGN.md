# Agent 3: Design (Anduril/Palantir Style) - Initialization Brief

**Role:** UI/UX Design System & Visual Design
**Phase:** MVP (Weeks 1-3)
**Status:** 🟢 Ready to Start

---

## Your Mission

Create a tactical, analyst-focused design system inspired by Anduril and Palantir aesthetics. Design all screens and components for the SIAD demo.

---

## Design Philosophy

**Target aesthetic:** Military/intelligence analyst tooling
- Dark theme (reduce eye strain for long sessions)
- High information density
- Clear visual hierarchy
- Data-first, no decoration
- Monospace for numerical data
- Confidence through restraint

**Anti-patterns to avoid:**
- Bright colors (except for alerts/warnings)
- Rounded corners everywhere
- Drop shadows
- Gradients
- Unnecessary animations
- "AI glow" effects

---

## What's Already Done ✅

1. **API Spec** (`docs/API_SPEC.md`) - Data structures you'll visualize
2. **Existing Demo** (`siad-command-center/frontend/`) - Reference but redesign
3. **Detection Modules** - Technical foundation for what you're designing

---

## Your Week 1 Tasks

### Task 1: Design System Foundation
**Deliverable:** Figma file or design doc

**Color Palette:**
```
Background Layers:
- bg-base:       #0A0E14 (darkest)
- bg-elevated:   #151922
- bg-overlay:    #1F242F

Text:
- text-primary:  #E6E8EB (high contrast)
- text-secondary: #9BA1A6 (subdued)
- text-disabled: #4A5056

Data/Accents:
- data-value:    #00D9FF (cyan, for numbers)
- data-label:    #7A8288 (gray, for labels)

Alerts:
- alert-high:    #FF4757 (red)
- alert-medium:  #FFA502 (orange)
- alert-low:     #FFD93D (yellow)
- success:       #6BCF7F (green)

Residual Heatmap:
- Use viridis or plasma colorscale
- Blue (low) → Yellow → Red (high)
```

**Typography:**
```
Headings:
- Font: Inter or SF Pro (sans-serif)
- Sizes: 32px (h1), 24px (h2), 18px (h3), 14px (h4)
- Weight: 600 (semibold)

Body:
- Font: Inter or SF Pro
- Size: 14px
- Weight: 400 (regular)

Data/Code:
- Font: JetBrains Mono or SF Mono (monospace)
- Size: 13px
- Use for: tile IDs, scores, coordinates, dates
```

**Spacing:**
- Base unit: 8px
- Scale: 4px, 8px, 16px, 24px, 32px, 48px, 64px

**Deliverable:** Design system spec (colors, typography, spacing)

---

### Task 2: Component Library
**Deliverable:** Figma components or component spec

**Core Components:**

1. **Token Heatmap** (16×16 grid)
   - Cell size: 24px × 24px (total: 384px × 384px)
   - Color: Viridis scale (blue → yellow → red)
   - Hover state: Border highlight + tooltip
   - Tooltip: Token index, residual value

2. **Hotspot Card** (for ranked list)
   ```
   ┌─────────────────────────────────────┐
   │ #1  Mission Bay Development     HIGH│
   │                                     │
   │ Score: 0.82  |  Onset: Jun 2024    │
   │ Duration: 4mo | Type: Structural   │
   │                                     │
   │ ▓▓▓▓▓▓▓▓▓▓▓░░  82% Confidence      │
   └─────────────────────────────────────┘
   ```

3. **Timeline Chart**
   - Line chart showing score over time
   - X-axis: Months (Jan, Feb, Mar...)
   - Y-axis: Residual score (0-1)
   - Threshold line at 0.5
   - Highlight onset month

4. **Environmental Controls**
   - Slider: Rain anomaly (-3σ to +3σ)
   - Slider: Temp anomaly (-2°C to +2°C)
   - Toggle: "Normalize to Neutral Weather"
   - Visual indicator when active

5. **Baseline Comparison**
   - Bar chart or grouped lines
   - World Model vs Persistence vs Seasonal
   - Show improvement %

**Deliverable:** 5 core component designs

---

### Task 3: Dashboard Screen (Overview)
**Deliverable:** Figma screen design

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│ SIAD Detection System                    [Filters]  [?]│
├────────────────────────────────────────────────────────┤
│                                                        │
│  TOP HOTSPOTS (Jun 2024 - Dec 2024)                  │
│                                                        │
│  ┌─────────────────────┐  ┌──────────────────────┐   │
│  │ Hotspot List        │  │ Map View            │   │
│  │ (10 ranked cards)   │  │ (hex map w/ overlay)│   │
│  │                     │  │                      │   │
│  │ [Cards scroll here] │  │  [3D map from       │   │
│  │                     │  │   existing demo]     │   │
│  └─────────────────────┘  └──────────────────────┘   │
│                                                        │
│  FILTERS:                                             │
│  Date Range: [Jan 2024] ──── [Dec 2024]              │
│  Min Score: [▓▓▓▓▓░░░░░░] 0.5                        │
│  Alert Type: [●Structural] [○Activity] [○All]        │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Key elements:**
- Header with title and help icon
- Split view: list (left) + map (right)
- Filter controls at bottom
- High information density

**Deliverable:** Dashboard mockup

---

## Your Week 2 Tasks

### Task 4: Hotspot Detail Screen
**Deliverable:** Figma screen design

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│ ← Back to Dashboard        Hotspot #1: Mission Bay    │
├────────────────────────────────────────────────────────┤
│                                                        │
│ ┌──────────────────┐  ┌──────────────────┐           │
│ │ Timeline         │  │ Token Heatmap    │           │
│ │                  │  │ (16×16 grid)     │           │
│ │ [Line chart]     │  │                  │           │
│ └──────────────────┘  └──────────────────┘           │
│                                                        │
│ ┌────────────────────────────────────────────┐        │
│ │ Satellite Imagery                          │        │
│ │ [S2 RGB] [S1 SAR] [VIIRS] [Residual]     │        │
│ │                                            │        │
│ │ Month: ◄ Jun 2024 ►                       │        │
│ └────────────────────────────────────────────┘        │
│                                                        │
│ ┌──────────────────┐  ┌──────────────────┐           │
│ │ Environmental    │  │ Baseline         │           │
│ │ Controls         │  │ Comparison       │           │
│ │                  │  │                  │           │
│ │ [Sliders]        │  │ [Bar chart]      │           │
│ └──────────────────┘  └──────────────────┘           │
│                                                        │
│ EXPLANATION:                                          │
│ Structural acceleration detected. Change persists     │
│ under neutral weather (residual=0.82), indicating     │
│ it is NOT explained by weather anomalies.             │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Key panels:**
- Panel A: Timeline (top-left)
- Panel B: Token heatmap (top-right)
- Panel C: Imagery viewer (middle)
- Panel D: Environmental controls (bottom-left)
- Panel E: Baseline comparison (bottom-right)
- Panel F: Auto-generated explanation (bottom)

**Deliverable:** Detail screen mockup

---

### Task 5: Interaction States
**Deliverable:** State variations for key components

Design hover, active, and disabled states for:

1. **Hotspot Card:**
   - Default
   - Hover (subtle border glow)
   - Selected (cyan border)
   - Disabled (grayed out)

2. **Token Grid Cell:**
   - Default (colored by value)
   - Hover (border + tooltip)
   - Selected (thick border)

3. **Timeline Chart:**
   - Default
   - Hover over data point (show value)
   - Month selected (highlight region)

4. **Sliders:**
   - Default
   - Hover (handle scales up)
   - Dragging (show live value)

**Deliverable:** Component state variations

---

### Task 6: Empty & Error States
**Deliverable:** Screen designs for edge cases

1. **Empty State (No Hotspots):**
   ```
   ┌────────────────────────────────┐
   │                                │
   │         [Icon: Search]         │
   │                                │
   │   No hotspots detected         │
   │   in selected date range.      │
   │                                │
   │   Try expanding the date range │
   │   or lowering the min score.   │
   │                                │
   └────────────────────────────────┘
   ```

2. **Loading State:**
   ```
   ┌────────────────────────────────┐
   │                                │
   │    [Spinner or skeleton]       │
   │                                │
   │    Computing residuals...      │
   │    (Est. 3 seconds)            │
   │                                │
   └────────────────────────────────┘
   ```

3. **Error State:**
   ```
   ┌────────────────────────────────┐
   │                                │
   │     [Icon: Alert Triangle]     │
   │                                │
   │   Failed to load hotspot data  │
   │                                │
   │   Error: Tile tile_999 not     │
   │   found in database.           │
   │                                │
   │   [Retry Button]               │
   │                                │
   └────────────────────────────────┘
   ```

**Deliverable:** Empty, loading, and error state designs

---

## Your Week 3 Tasks

### Task 7: Responsive Layout
**Deliverable:** Tablet & mobile breakpoints

Design for 3 breakpoints:
- Desktop: 1440px+ (primary target)
- Tablet: 768px - 1439px (optional for MVP)
- Mobile: < 768px (not required for MVP)

**Focus on desktop first!** Tablet is nice-to-have.

**Deliverable:** Responsive layout guide

---

### Task 8: Design Handoff
**Deliverable:** Developer-ready specs

Create handoff document with:

1. **Component Specs:**
   - Dimensions (px)
   - Spacing (px)
   - Colors (hex codes)
   - Fonts (family, size, weight)

2. **Assets:**
   - Icons (SVG exports)
   - Logo (if needed)

3. **Interaction Notes:**
   - Hover behaviors
   - Click targets
   - Animations (if any, keep minimal)

4. **Accessibility:**
   - Color contrast ratios (WCAG AA minimum)
   - Focus indicators
   - Screen reader labels

**Deliverable:** Complete design system documentation for Agent 4

---

## Key Design Principles

### 1. Information Density
Show as much relevant data as possible without overwhelming.
- Use tables, not cards, when appropriate
- Leverage whitespace for grouping, not decoration

### 2. Hierarchy Through Typography
- Don't rely on color alone
- Use font weight and size for hierarchy
- Monospace for data, sans-serif for labels

### 3. Confidence Through Restraint
- No gradients, drop shadows, or glow effects
- Flat design with subtle borders
- Let the data be the star

### 4. Tactical Aesthetic
- Think mission control, not consumer app
- Dark theme reduces eye strain
- Red = high alert, green = success, cyan = data

---

## Tools

**Recommended:**
- Figma (preferred, collaborative)
- Sketch (alternative)
- Adobe XD (alternative)

**For color schemes:**
- https://coolors.co/
- Use viridis/plasma from matplotlib for heatmaps

**For fonts:**
- Inter: https://rsms.me/inter/
- JetBrains Mono: https://www.jetbrains.com/lp/mono/

---

## Reference Designs

**Inspiration (Anduril/Palantir style):**
- Palantir Gotham: Dark theme, high density, monospace data
- Anduril Lattice: Tactical aesthetic, map-centric
- Bloomberg Terminal: Information density, dark theme

**Anti-examples (avoid these):**
- Consumer dashboards with bright colors
- Rounded corners everywhere
- Excessive whitespace
- "AI glow" effects

---

## Dependencies

**You depend on:**
- API spec (`docs/API_SPEC.md`) for data structures
- Agent 6 (Copy) for UI text content

**Others depend on you:**
- Agent 4 (Frontend) needs your designs to implement
- Agent 5 (UX) needs your designs to plan interactions

---

## Success Criteria (Week 3)

- [ ] Design system documented (colors, typography, spacing)
- [ ] 5 core components designed
- [ ] Dashboard screen mockup complete
- [ ] Detail screen mockup complete
- [ ] Empty/loading/error states designed
- [ ] Design handoff doc ready for Agent 4
- [ ] At least 2 design reviews with team

---

## Communication

**Sync with:**
- **Agent 4 (Frontend):** Daily in Week 2-3 for implementation questions
- **Agent 5 (UX):** Mid-week on interaction patterns
- **Agent 6 (Copy):** Early for UI text content
- **All agents:** End of Week 1 for design system review

---

**Deliverables location:**
- Figma: Share link with team
- Exports: `/siad-command-center/frontend/public/designs/`
- Specs: `/docs/DESIGN_SYSTEM.md`

---

**Ready to design? Start with Task 1: Design System Foundation!**

🎨 Make it beautiful (but tactical)!
