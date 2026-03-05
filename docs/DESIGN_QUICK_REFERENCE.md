# SIAD Design Quick Reference

**For Agent 4 (Frontend) - TL;DR Version**

---

## Design Files Location

```
/docs/
├── DESIGN_SYSTEM.md         ← Colors, fonts, spacing (862 lines)
├── COMPONENT_SPECS.md       ← 5 components with CSS (1,672 lines)
├── DASHBOARD_MOCKUP.md      ← Full screen layout (1,214 lines)
└── DESIGN_WEEK1_SUMMARY.md  ← Overview + handoff (444 lines)
```

**Total: 4,192 lines of design specifications**

---

## Colors (Copy-Paste Ready)

```css
/* Background */
--bg-base: #0A0E14;
--bg-elevated: #151922;
--bg-overlay: #1F242F;

/* Text */
--text-primary: #E6E8EB;
--text-secondary: #9BA1A6;
--text-disabled: #4A5056;

/* Data */
--data-value: #00D9FF;    /* Cyan - use for all numbers */
--data-label: #7A8288;    /* Gray - use for labels */

/* Alerts */
--alert-high: #FF4757;    /* Red */
--alert-medium: #FFA502;  /* Orange */
--alert-low: #FFD93D;     /* Yellow */
--success: #6BCF7F;       /* Green */

/* Spacing (8px grid) */
--space-1: 4px;
--space-2: 8px;
--space-3: 16px;
--space-4: 24px;
--space-5: 32px;
--space-6: 48px;

/* Typography */
--font-ui: 'Inter', -apple-system, sans-serif;
--font-data: 'JetBrains Mono', 'SF Mono', monospace;
```

---

## Typography Rules

```
Headings:     Inter, 600 weight, sizes: 32px/24px/18px/14px
Body text:    Inter, 400 weight, 14px
Data/numbers: JetBrains Mono, 400-500 weight, 13-14px
Labels:       Inter, 500 weight, 12px, UPPERCASE
```

**Golden Rule:** Use monospace for ALL numbers (scores, dates, coordinates)

---

## Component Sizes (Quick Reference)

| Component              | Width  | Height | Use Case                |
|------------------------|--------|--------|-------------------------|
| Token Heatmap          | 400px  | 480px  | 16×16 residual grid     |
| Hotspot Card           | 100%   | 140px  | Ranked list item        |
| Timeline Chart         | 500px  | 250px  | Score over time         |
| Environmental Controls | 320px  | 240px  | Weather sliders         |
| Baseline Comparison    | 320px  | 280px  | Bar chart (3 bars)      |

---

## Dashboard Layout (ASCII)

```
┌────────────────────────────────────────────┐
│ HEADER (64px)                              │
├──────────────┬─────────────────────────────┤
│ SIDEBAR      │ MAP VIEW                    │
│ (400px)      │ (flex-grow)                 │
│              │                             │
│ [10 cards]   │ [Hex map + controls]        │
│              │                             │
│ [Filters]    │                             │
│ (280px)      │                             │
└──────────────┴─────────────────────────────┘
```

**Dimensions:**
- Screen: 1440×900px
- Header: 64px height (fixed)
- Sidebar: 400px width (fixed)
- Map: flex-grow

---

## 5 Core Components

### 1. Token Heatmap (16×16 grid)
**File:** COMPONENT_SPECS.md (lines 1-150)

```css
.heatmap-cell {
  width: 24px;
  height: 24px;
  border: 1px solid rgba(10, 14, 20, 0.5);
  cursor: pointer;
}

.heatmap-cell:hover {
  border: 2px solid var(--text-primary);
  z-index: 10;
}
```

**Use:** Viridis colorscale (#440154 → #FDE724)

---

### 2. Hotspot Card (list item)
**File:** COMPONENT_SPECS.md (lines 151-350)

```css
.hotspot-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  padding: 16px;
  min-height: 140px;
}

.hotspot-card:hover {
  border-color: var(--data-value);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}
```

**Includes:** Rank, name, score, onset, duration, confidence bar

---

### 3. Timeline Chart (line chart)
**File:** COMPONENT_SPECS.md (lines 351-500)

**Recommended library:** Recharts or D3.js

```jsx
<LineChart width={468} height={180} data={timeline}>
  <Line dataKey="score" stroke="var(--data-value)" />
  <ReferenceLine y={0.5} stroke="var(--alert-medium)" />
</LineChart>
```

---

### 4. Environmental Controls (sliders)
**File:** COMPONENT_SPECS.md (lines 501-700)

```css
.env-slider-thumb {
  width: 16px;
  height: 16px;
  background: var(--data-value);
  border-radius: 50%;
}

.env-toggle-switch {
  width: 40px;
  height: 20px;
  background: rgba(230, 232, 235, 0.2);
}
```

**Includes:** 2 sliders (rain, temp) + 1 toggle + Reset/Apply buttons

---

### 5. Baseline Comparison (bar chart)
**File:** COMPONENT_SPECS.md (lines 701-900)

```css
.baseline-bar-fill {
  height: 24px;
  background: var(--data-value);
  transition: width 200ms ease-in-out;
}

.baseline-bar-fill.world-model {
  background: var(--success); /* Green = best */
}
```

**Shows:** World Model vs Persistence vs Seasonal

---

## Interaction States (All Components)

```css
/* Default */
border: 1px solid var(--border-default);

/* Hover */
border-color: var(--data-value);
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
cursor: pointer;

/* Selected */
border: 2px solid var(--data-value);
background: rgba(0, 217, 255, 0.05);

/* Focus (keyboard) */
outline: 2px solid var(--data-value);
outline-offset: 2px;

/* Disabled */
opacity: 0.4;
cursor: not-allowed;
```

---

## Accessibility Checklist

```
[x] Color contrast ≥ 4.5:1 (WCAG AA)
[x] Keyboard navigation (Tab, Enter, Space, Esc)
[x] Focus indicators (2px cyan outline)
[x] ARIA labels on interactive elements
[x] Screen reader friendly (semantic HTML)
[x] No color-only information (use icons + text)
```

---

## Fonts to Install

1. **Inter** (UI font)
   - Source: https://rsms.me/inter/
   - License: SIL Open Font License
   - Weights: 400 (regular), 500 (medium), 600 (semibold)

2. **JetBrains Mono** (data font)
   - Source: https://www.jetbrains.com/lp/mono/
   - License: Apache 2.0
   - Weights: 400 (regular), 500 (medium)

**Install via:**
```bash
npm install @fontsource/inter @fontsource/jetbrains-mono
```

---

## Import Design Tokens

**Option 1: CSS Variables (Recommended)**
```css
/* src/styles/tokens.css */
:root {
  --bg-base: #0A0E14;
  --bg-elevated: #151922;
  /* ... (see DESIGN_SYSTEM.md) */
}
```

**Option 2: JavaScript Object**
```javascript
// src/styles/tokens.js
export const colors = {
  bgBase: '#0A0E14',
  textPrimary: '#E6E8EB',
  dataValue: '#00D9FF',
  // ...
};
```

**Option 3: Tailwind Config**
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    colors: {
      'bg-base': '#0A0E14',
      // ...
    }
  }
}
```

---

## Implementation Order (Week 1-2)

```
Week 1:
1. Setup design tokens (Day 1)
2. Build Hotspot Card (Day 2-3)
3. Build dashboard layout (Day 4-5)

Week 2:
4. Build Token Heatmap (Day 1-2)
5. Build Timeline Chart (Day 2-3)
6. Build Environmental Controls (Day 3)
7. Build Baseline Comparison (Day 4)
8. Integrate map library (Day 5)

Week 3:
9. Add interactions (filters, selection)
10. Accessibility pass
11. Performance optimization
```

---

## Common Patterns

### Card Container
```css
.card {
  background: var(--bg-elevated);
  border: 1px solid rgba(230, 232, 235, 0.2);
  border-radius: 4px;
  padding: 16px;
  transition: all 100ms ease-in-out;
}
```

### Button (Primary)
```css
.button-primary {
  background: var(--data-value);
  color: var(--bg-base);
  padding: 8px 16px;
  border-radius: 2px;
  font-weight: 600;
  border: none;
}
```

### Data Row (Label + Value)
```html
<div class="data-row">
  <span class="label">Score:</span>
  <span class="value">0.82</span>
</div>
```

```css
.label {
  font-family: var(--font-ui);
  font-size: 12px;
  color: var(--data-label);
  text-transform: uppercase;
}

.value {
  font-family: var(--font-data);
  font-size: 14px;
  color: var(--data-value);
  font-weight: 500;
}
```

---

## Anti-Patterns (Don't Do This)

```
❌ Rounded corners > 6px
❌ Drop shadows > 24px blur
❌ Gradients (use flat colors)
❌ Animations > 300ms
❌ Bright colors (except alerts)
❌ Sans-serif for numbers (use monospace)
❌ Color-only information (add icons/text)
❌ Small touch targets < 36px
```

---

## Debugging Tips

### Color Contrast Checker
```bash
# Install tool
npm install -g wcag-contrast

# Check contrast
wcag-contrast #E6E8EB on #0A0E14
# Output: 11.2:1 (AAA) ✓
```

### Font Loading Check
```javascript
// Add to console
document.fonts.check('14px Inter');
// Should return true when loaded
```

### CSS Variable Inspector
```javascript
// Check if tokens are loaded
getComputedStyle(document.documentElement)
  .getPropertyValue('--bg-base');
// Should return: #0A0E14
```

---

## FAQs for Agent 4

**Q: Can I use a different font?**
A: No. Inter and JetBrains Mono are specified for consistency. System fallbacks are okay for dev.

**Q: Can I round these corners more?**
A: No. Max radius is 6px. Tactical aesthetic requires restraint.

**Q: Can I add animations?**
A: Only if ≤ 200ms. Analysts need instant feedback, not smooth transitions.

**Q: What about dark mode toggle?**
A: Not needed. This IS dark mode (always on).

**Q: Can I use Material UI / Ant Design?**
A: No. Pre-built component libraries clash with tactical aesthetic. Build custom.

**Q: Mapbox or Leaflet?**
A: Mapbox recommended (better performance), but Leaflet is acceptable.

**Q: D3 or Recharts?**
A: Recharts for MVP (faster), D3 if you need more control.

**Q: Redux or Context API?**
A: Context API for MVP (simpler). Redux only if state gets complex.

---

## Getting Help

1. **Design System questions:** Check DESIGN_SYSTEM.md
2. **Component specs:** Check COMPONENT_SPECS.md
3. **Layout questions:** Check DASHBOARD_MOCKUP.md
4. **General questions:** Check DESIGN_WEEK1_SUMMARY.md

**Still stuck?** Ping Agent 3 (Design) for clarification.

---

## Success Checklist

Before marking implementation complete:

**Design System:**
- [ ] All CSS variables imported
- [ ] Fonts loaded (Inter + JetBrains Mono)
- [ ] Spacing scale consistent (8px grid)

**Components:**
- [ ] All 5 components match specs (pixel-perfect)
- [ ] Hover states work on all interactive elements
- [ ] Focus indicators visible (keyboard nav)
- [ ] Tooltips show on hover

**Dashboard:**
- [ ] Header, sidebar, map layout correct
- [ ] Hotspot cards scroll in sidebar
- [ ] Filters apply and update data
- [ ] Empty/loading/error states work

**Accessibility:**
- [ ] All interactive elements keyboard accessible
- [ ] Focus order follows visual flow
- [ ] ARIA labels on all buttons/cards
- [ ] Color contrast passes WCAG AA

**Performance:**
- [ ] Initial load < 2 seconds
- [ ] Filter update < 500ms
- [ ] Map pan/zoom at 60 FPS
- [ ] No layout shift on load

---

## Key Takeaways

1. **Dark theme always** (#0A0E14 base)
2. **Monospace for data** (JetBrains Mono)
3. **Cyan for values** (#00D9FF)
4. **Minimal animation** (≤ 200ms)
5. **8px grid spacing**
6. **WCAG AA contrast** (≥ 4.5:1)
7. **Keyboard nav first** (Tab, Enter, Space)
8. **No decoration** (flat design)

---

**Design System Status:** ✓ Complete

**Ready to Code:** YES

**Start Here:** Import design tokens → Build Hotspot Card → Build dashboard layout

🎨 → 💻 Let's build a tactical analyst interface.
