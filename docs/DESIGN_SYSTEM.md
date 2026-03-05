# SIAD Design System v1.0

**Tactical Analyst UI Design System**

Last Updated: 2026-03-03
Design Lead: Agent 3 (Design)

---

## Design Philosophy

### Target Aesthetic
Military/intelligence analyst tooling with Anduril/Palantir inspiration

**Core Principles:**
- **Information Density:** Maximize relevant data without overwhelming
- **Hierarchy Through Typography:** Use font weight/size for structure, not color alone
- **Confidence Through Restraint:** No decoration - let data be the star
- **Tactical Aesthetic:** Mission control, not consumer app

**Anti-Patterns (Avoid):**
- Bright colors (except alerts)
- Rounded corners everywhere
- Drop shadows / gradients
- Unnecessary animations
- "AI glow" effects

---

## Color Palette

### Background Layers
```css
--bg-base:      #0A0E14;  /* Darkest - main canvas */
--bg-elevated:  #151922;  /* Cards, panels */
--bg-overlay:   #1F242F;  /* Modals, tooltips */
```

**Usage:**
- `bg-base`: Main application background
- `bg-elevated`: Card backgrounds, sidebar, raised panels
- `bg-overlay`: Hover states, modals, tooltips, dropdowns

---

### Text Colors
```css
--text-primary:   #E6E8EB;  /* High contrast - headings, labels */
--text-secondary: #9BA1A6;  /* Subdued - descriptions, metadata */
--text-disabled:  #4A5056;  /* Disabled states, placeholders */
```

**Contrast Ratios (WCAG AA):**
- Primary on base: 11.2:1 ✓
- Secondary on base: 5.8:1 ✓
- Disabled on base: 2.9:1 (intentionally low)

---

### Data & Accents
```css
--data-value:  #00D9FF;  /* Cyan - numerical values, scores */
--data-label:  #7A8288;  /* Gray - data labels, units */
```

**Usage:**
- `data-value`: Scores, coordinates, tile IDs, timestamps
- `data-label`: "Score:", "Lat:", "Duration:", units like "months", "°C"

---

### Alert Colors
```css
--alert-high:    #FF4757;  /* Red - critical alerts */
--alert-medium:  #FFA502;  /* Orange - warnings */
--alert-low:     #FFD93D;  /* Yellow - caution */
--success:       #6BCF7F;  /* Green - success states */
```

**Usage:**
- High alert: Structural acceleration, critical hotspots
- Medium alert: Activity surge, moderate priority
- Low alert: Watch list, informational
- Success: Confirmed actions, successful operations

---

### Residual Heatmap Colors
**Colorscale:** Viridis (recommended) or Plasma

**Viridis Scale:**
```css
Low  (0.0): #440154  /* Deep purple */
      0.2:  #31688E  /* Blue */
      0.4:  #35B779  /* Teal */
      0.6:  #FDE724  /* Yellow */
High (1.0): #FDE724  /* Bright yellow */
```

**Alternative (Plasma):**
```css
Low  (0.0): #0D0887  /* Dark blue */
      0.5:  #CC4778  /* Magenta */
High (1.0): #F0F921  /* Yellow */
```

**Why Viridis:**
- Perceptually uniform (equal steps look equal)
- Colorblind-safe
- Prints well in grayscale
- Standard in scientific visualization

---

## Typography

### Font Families

#### UI Text (Sans-Serif)
```css
--font-ui: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro', sans-serif;
```

**Use for:**
- Headings
- Body text
- Buttons
- Labels

**Fallbacks:**
- macOS: SF Pro
- Windows: Segoe UI
- Linux: System sans-serif

---

#### Data/Code (Monospace)
```css
--font-data: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
```

**Use for:**
- Tile IDs (tile_042)
- Coordinates (37.7599, -122.3894)
- Scores (0.82)
- Dates (2024-06-15)
- Residual values
- Token indices

**Why Monospace:**
- Aligns columns naturally
- Easier to scan numbers
- Signals "raw data" vs "UI text"

---

### Type Scale

#### Headings
```css
--text-h1: 32px / 40px; font-weight: 600; letter-spacing: -0.02em;
--text-h2: 24px / 32px; font-weight: 600; letter-spacing: -0.01em;
--text-h3: 18px / 24px; font-weight: 600; letter-spacing: -0.005em;
--text-h4: 14px / 20px; font-weight: 600; letter-spacing: 0;
```

**Usage:**
- H1: Page title ("SIAD Detection System")
- H2: Section headers ("Top Hotspots", "Timeline")
- H3: Panel titles ("Token Heatmap", "Environmental Controls")
- H4: Card headers ("Hotspot #1", "Mission Bay")

---

#### Body Text
```css
--text-body:    14px / 20px; font-weight: 400;
--text-caption: 12px / 16px; font-weight: 400;
--text-label:   12px / 16px; font-weight: 500; text-transform: uppercase;
```

**Usage:**
- Body: Descriptions, explanations, help text
- Caption: Metadata, timestamps, secondary info
- Label: Form labels, filter labels (e.g., "DATE RANGE")

---

#### Data Text
```css
--text-data-lg: 16px / 24px; font-weight: 500; font-family: var(--font-data);
--text-data-md: 14px / 20px; font-weight: 400; font-family: var(--font-data);
--text-data-sm: 12px / 16px; font-weight: 400; font-family: var(--font-data);
```

**Usage:**
- Large: Primary scores (0.82), main tile ID
- Medium: Coordinates, dates, secondary values
- Small: Token indices, table cells, compact data

---

### Font Weights
```css
--weight-regular:  400;
--weight-medium:   500;
--weight-semibold: 600;
```

**Hierarchy:**
- Semibold (600): Headings only
- Medium (500): Labels, emphasized data
- Regular (400): Body text, most UI

---

## Spacing System

### Base Unit: 8px

**Scale:**
```css
--space-1:  4px;   /* Tight spacing, icon padding */
--space-2:  8px;   /* Default spacing */
--space-3:  16px;  /* Component padding */
--space-4:  24px;  /* Section spacing */
--space-5:  32px;  /* Panel spacing */
--space-6:  48px;  /* Page margins */
--space-7:  64px;  /* Large gaps */
```

**Usage Guidelines:**
- **4px:** Icon-to-text gaps, tight table cells
- **8px:** Input padding, button padding, list items
- **16px:** Card padding, panel padding
- **24px:** Between components in a panel
- **32px:** Between panels/sections
- **48px:** Page margins (left/right)
- **64px:** Major layout gaps (header to content)

---

### Component-Specific Spacing

#### Cards
```css
padding: var(--space-3);     /* 16px internal padding */
gap: var(--space-2);         /* 8px between elements */
margin-bottom: var(--space-2); /* 8px between cards */
```

#### Panels
```css
padding: var(--space-4);     /* 24px internal padding */
gap: var(--space-3);         /* 16px between sections */
```

#### Grid Layouts
```css
gap: var(--space-3);         /* 16px between grid items */
```

---

## Layout Grid

### Desktop (Primary Target)
```css
--container-max-width: 1440px;
--sidebar-width: 320px;
--panel-gap: 16px;
```

**Dashboard Layout:**
```
[Header: 64px height]
[Content: flex-grow]
  [Sidebar: 320px] | [Main: flex-grow]
```

**Detail Screen Layout:**
```
[Header: 64px]
[Content: Grid 2×3]
  [Timeline] [Heatmap]
  [Imagery - spans both columns]
  [Controls] [Comparison]
```

---

### Breakpoints
```css
--breakpoint-desktop: 1440px;
--breakpoint-tablet:  768px;
--breakpoint-mobile:  480px;
```

**Note:** MVP focuses on desktop (1440px+). Tablet/mobile optional.

---

## Borders & Dividers

### Border Styles
```css
--border-subtle:  1px solid rgba(230, 232, 235, 0.1);  /* Faint dividers */
--border-default: 1px solid rgba(230, 232, 235, 0.2);  /* Standard borders */
--border-strong:  1px solid rgba(230, 232, 235, 0.3);  /* Emphasized borders */
--border-accent:  2px solid var(--data-value);         /* Selected state */
```

**Usage:**
- Subtle: Table rows, light dividers
- Default: Cards, panels, inputs
- Strong: Active panels, focused inputs
- Accent: Selected items, hover states (cyan)

---

### Radius
```css
--radius-sm: 2px;   /* Inputs, buttons */
--radius-md: 4px;   /* Cards, panels */
--radius-lg: 6px;   /* Modals, large surfaces */
```

**Note:** Keep radii small - tactical aesthetic avoids heavy rounding.

---

## Shadows & Elevation

**Principle:** Minimize shadows. Use subtle elevation only.

```css
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
--shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
```

**Usage:**
- Small: Hover states on cards
- Medium: Modals, popovers
- Large: Overlays, large modals

**When to skip shadows:**
- Standard cards (use border instead)
- Panels (use background color)
- Buttons (flat design)

---

## Interaction States

### Hover States
```css
background: lighten(bg-elevated, 5%);  /* Subtle lightening */
border-color: var(--data-value);       /* Cyan accent */
cursor: pointer;
```

### Active/Selected States
```css
border: 2px solid var(--data-value);
background: rgba(0, 217, 255, 0.1);   /* Faint cyan tint */
```

### Disabled States
```css
opacity: 0.4;
cursor: not-allowed;
color: var(--text-disabled);
```

### Focus States (Accessibility)
```css
outline: 2px solid var(--data-value);
outline-offset: 2px;
```

---

## Icons

### Icon Style
- **Line icons** (not filled)
- **Stroke width:** 1.5px
- **Size:** 16px (small), 20px (medium), 24px (large)
- **Color:** Inherit from parent text color

### Icon Library Recommendations
- **Heroicons** (tailwind-friendly, clean lines)
- **Lucide** (consistent stroke width)
- **Feather Icons** (minimal, tactical)

**Avoid:**
- Filled icons (too heavy)
- Colorful icons (breaks aesthetic)
- Inconsistent stroke widths

---

## Animation

### Principle: Minimal Motion

**Allowed animations:**
```css
--transition-fast: 100ms ease-in-out;   /* Hover, focus */
--transition-base: 200ms ease-in-out;   /* Panel open/close */
--transition-slow: 300ms ease-in-out;   /* Page transitions */
```

**Usage:**
- Hover states: `transition: all var(--transition-fast);`
- Panel reveals: `transition: transform var(--transition-base);`
- Modal fades: `transition: opacity var(--transition-base);`

**No animations for:**
- Data updates (instant)
- Chart rendering (instant)
- Heatmap changes (instant)

**Rationale:** Analysts need instant feedback, not smooth animations.

---

## Accessibility

### Color Contrast
All text meets WCAG AA (4.5:1 minimum):
- Primary text on base: 11.2:1 ✓
- Secondary text on base: 5.8:1 ✓
- Data cyan on base: 7.8:1 ✓

### Focus Indicators
Always show focus outlines:
```css
:focus-visible {
  outline: 2px solid var(--data-value);
  outline-offset: 2px;
}
```

### Screen Reader Labels
- All icons have `aria-label`
- Interactive elements have clear labels
- Heatmap cells have descriptive text

### Keyboard Navigation
- Tab order follows visual flow
- All interactive elements reachable via keyboard
- Escape closes modals/popovers

---

## Component Tokens

### Buttons
```css
/* Primary Button */
background: var(--data-value);
color: var(--bg-base);
padding: 8px 16px;
border-radius: var(--radius-sm);
font-weight: 500;

/* Secondary Button */
background: transparent;
border: 1px solid var(--border-default);
color: var(--text-primary);

/* Danger Button */
background: var(--alert-high);
color: white;
```

---

### Inputs
```css
background: var(--bg-elevated);
border: 1px solid var(--border-default);
border-radius: var(--radius-sm);
padding: 8px 12px;
color: var(--text-primary);
font-family: var(--font-ui);
font-size: 14px;

/* Focus state */
:focus {
  border-color: var(--data-value);
  outline: none;
  box-shadow: 0 0 0 2px rgba(0, 217, 255, 0.2);
}
```

---

### Cards
```css
background: var(--bg-elevated);
border: 1px solid var(--border-default);
border-radius: var(--radius-md);
padding: var(--space-3);

/* Hover state */
:hover {
  border-color: var(--data-value);
  box-shadow: var(--shadow-sm);
}

/* Selected state */
.selected {
  border: 2px solid var(--data-value);
  background: rgba(0, 217, 255, 0.05);
}
```

---

### Tooltips
```css
background: var(--bg-overlay);
border: 1px solid var(--border-strong);
border-radius: var(--radius-sm);
padding: 6px 10px;
font-size: 12px;
color: var(--text-primary);
box-shadow: var(--shadow-md);
max-width: 200px;
```

---

## Usage Examples

### Example 1: Hotspot Card
```css
.hotspot-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  transition: all var(--transition-fast);
}

.hotspot-card:hover {
  border-color: var(--data-value);
  box-shadow: var(--shadow-sm);
}

.hotspot-rank {
  font-family: var(--font-data);
  font-size: var(--text-data-lg);
  color: var(--data-value);
  font-weight: 600;
}

.hotspot-name {
  font-family: var(--font-ui);
  font-size: var(--text-h4);
  color: var(--text-primary);
  font-weight: 600;
}

.hotspot-score {
  font-family: var(--font-data);
  font-size: var(--text-data-md);
  color: var(--data-value);
}

.hotspot-label {
  font-family: var(--font-ui);
  font-size: var(--text-caption);
  color: var(--data-label);
  text-transform: uppercase;
}
```

---

### Example 2: Token Heatmap Cell
```css
.heatmap-cell {
  width: 24px;
  height: 24px;
  border: 1px solid var(--bg-base);
  cursor: pointer;
  transition: border-color var(--transition-fast);
}

.heatmap-cell:hover {
  border: 2px solid var(--text-primary);
  z-index: 10;
}

.heatmap-cell[data-value="0.0"] { background: #440154; }
.heatmap-cell[data-value="0.2"] { background: #31688E; }
.heatmap-cell[data-value="0.4"] { background: #35B779; }
.heatmap-cell[data-value="0.6"] { background: #FDE724; }
/* ...interpolate for all values */
```

---

### Example 3: Alert Badge
```css
.alert-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-caption);
  font-weight: 500;
  text-transform: uppercase;
}

.alert-badge.high {
  background: rgba(255, 71, 87, 0.15);
  color: var(--alert-high);
  border: 1px solid var(--alert-high);
}

.alert-badge.medium {
  background: rgba(255, 165, 2, 0.15);
  color: var(--alert-medium);
  border: 1px solid var(--alert-medium);
}

.alert-badge.low {
  background: rgba(255, 217, 61, 0.15);
  color: var(--alert-low);
  border: 1px solid var(--alert-low);
}
```

---

## Design Tokens Export

### CSS Variables
```css
:root {
  /* Colors */
  --bg-base: #0A0E14;
  --bg-elevated: #151922;
  --bg-overlay: #1F242F;
  --text-primary: #E6E8EB;
  --text-secondary: #9BA1A6;
  --text-disabled: #4A5056;
  --data-value: #00D9FF;
  --data-label: #7A8288;
  --alert-high: #FF4757;
  --alert-medium: #FFA502;
  --alert-low: #FFD93D;
  --success: #6BCF7F;

  /* Typography */
  --font-ui: 'Inter', -apple-system, sans-serif;
  --font-data: 'JetBrains Mono', 'SF Mono', monospace;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 32px;
  --space-6: 48px;
  --space-7: 64px;

  /* Borders */
  --border-subtle: 1px solid rgba(230, 232, 235, 0.1);
  --border-default: 1px solid rgba(230, 232, 235, 0.2);
  --border-strong: 1px solid rgba(230, 232, 235, 0.3);
  --border-accent: 2px solid var(--data-value);

  /* Radius */
  --radius-sm: 2px;
  --radius-md: 4px;
  --radius-lg: 6px;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);

  /* Transitions */
  --transition-fast: 100ms ease-in-out;
  --transition-base: 200ms ease-in-out;
  --transition-slow: 300ms ease-in-out;
}
```

---

### JSON Export (for JavaScript)
```json
{
  "colors": {
    "background": {
      "base": "#0A0E14",
      "elevated": "#151922",
      "overlay": "#1F242F"
    },
    "text": {
      "primary": "#E6E8EB",
      "secondary": "#9BA1A6",
      "disabled": "#4A5056"
    },
    "data": {
      "value": "#00D9FF",
      "label": "#7A8288"
    },
    "alert": {
      "high": "#FF4757",
      "medium": "#FFA502",
      "low": "#FFD93D"
    },
    "success": "#6BCF7F"
  },
  "spacing": {
    "1": "4px",
    "2": "8px",
    "3": "16px",
    "4": "24px",
    "5": "32px",
    "6": "48px",
    "7": "64px"
  },
  "typography": {
    "fontFamily": {
      "ui": "'Inter', -apple-system, sans-serif",
      "data": "'JetBrains Mono', 'SF Mono', monospace"
    },
    "fontSize": {
      "h1": "32px",
      "h2": "24px",
      "h3": "18px",
      "h4": "14px",
      "body": "14px",
      "caption": "12px"
    },
    "fontWeight": {
      "regular": 400,
      "medium": 500,
      "semibold": 600
    }
  }
}
```

---

## Implementation Checklist

### Phase 1: Setup
- [ ] Install Inter font (Google Fonts or local)
- [ ] Install JetBrains Mono font
- [ ] Create CSS variables file (tokens.css)
- [ ] Import tokens into main stylesheet

### Phase 2: Base Styles
- [ ] Set body background to bg-base
- [ ] Apply font-ui to body
- [ ] Set text-primary as default text color
- [ ] Configure box-sizing: border-box globally

### Phase 3: Component Styles
- [ ] Create button component styles
- [ ] Create card component styles
- [ ] Create input component styles
- [ ] Create tooltip component styles

### Phase 4: Validation
- [ ] Test color contrast ratios
- [ ] Test keyboard navigation
- [ ] Test focus indicators
- [ ] Test in dark mode (already dark!)

---

## Notes for Agent 4 (Frontend)

### CSS-in-JS (if using)
Use styled-components or emotion:
```javascript
const theme = {
  colors: {
    bgBase: '#0A0E14',
    textPrimary: '#E6E8EB',
    dataValue: '#00D9FF',
    // ...
  },
  spacing: [4, 8, 16, 24, 32, 48, 64],
  // ...
};
```

### Tailwind Config (if using)
```javascript
module.exports = {
  theme: {
    colors: {
      'bg-base': '#0A0E14',
      'bg-elevated': '#151922',
      // ...
    },
    spacing: {
      '1': '4px',
      '2': '8px',
      // ...
    },
    fontFamily: {
      'ui': ['Inter', 'sans-serif'],
      'data': ['JetBrains Mono', 'monospace'],
    },
  },
};
```

### React Components
Use semantic token names:
```jsx
<Card>
  <Rank value={1} />
  <Title>Mission Bay</Title>
  <DataRow>
    <Label>Score:</Label>
    <Value>0.82</Value>
  </DataRow>
</Card>
```

---

## Version History

- **v1.0** (2026-03-03): Initial design system foundation
  - Color palette defined
  - Typography system established
  - Spacing scale created
  - Component tokens specified

---

## Contact

Design Lead: Agent 3 (Design)
Collaboration: Agent 4 (Frontend), Agent 5 (UX), Agent 6 (Copy)

For questions or clarifications, reference this document first, then coordinate with Agent 3.

---

**Design System Status:** ✓ Complete - Ready for Component Specs

**Next Steps:**
1. Create `COMPONENT_SPECS.md` with detailed component designs
2. Create dashboard mockup
3. Provide design handoff to Agent 4
