# UX Implementation Priorities for Agent 4 (Frontend)

**From:** Agent 5 (UX/Interaction)
**To:** Agent 4 (Frontend)
**Date:** 2026-03-03

---

## Overview

This document prioritizes the UX specifications from Week 1 deliverables for implementation. Focus on high-impact, user-critical interactions first.

**Reference Documents:**
- `/docs/USER_FLOWS.md` - Complete user journey maps
- `/docs/INTERACTION_SPEC.md` - Detailed interaction behaviors
- `/docs/KEYBOARD_SHORTCUTS.md` - All keyboard shortcuts
- `/docs/UX_WEEK1_SUMMARY.md` - Executive summary

---

## Week 2 Implementation Priorities

### Priority 1: Core Navigation (CRITICAL)
**Impact:** Users can't use app without this
**Effort:** Medium

**Components:**
1. **Dashboard Hotspot List**
   - Keyboard navigation: `j/k` for next/prev
   - `Enter` to open detail page
   - Visual focus indicators (2px outline)
   - Reference: `INTERACTION_SPEC.md` Section 2.3

2. **Hotspot Card Interactions**
   - Hover effects (border glow, elevation)
   - Click to navigate
   - Loading state on navigation
   - Reference: `INTERACTION_SPEC.md` Section 2.1-2.2

3. **Global Shortcuts**
   - `?` to show help modal
   - `/` to focus search
   - `Esc` to go back/cancel
   - Reference: `KEYBOARD_SHORTCUTS.md` Global Shortcuts

**Acceptance Criteria:**
- [ ] Can navigate entire dashboard using only keyboard
- [ ] Focus indicators visible on all interactive elements
- [ ] Smooth transitions (200-300ms) between pages
- [ ] Help modal (`?`) displays all shortcuts

---

### Priority 2: Token Heatmap (HIGH)
**Impact:** Core analysis tool for identifying changes
**Effort:** High

**Interactions:**
1. **Hover Tooltip**
   - Show token index, residual value, coordinates
   - < 50ms to display
   - Follow cursor with smart positioning
   - Reference: `INTERACTION_SPEC.md` Section 1.1

2. **Click to Zoom Imagery**
   - Highlight clicked token (border + scale)
   - Sync with imagery viewer (scroll/zoom to pixel region)
   - 200-500ms transition
   - Reference: `INTERACTION_SPEC.md` Section 1.2

3. **Zoom/Pan (if dataset large)**
   - Scroll to zoom (max 3x)
   - Drag to pan (with inertia)
   - Keyboard: `+/-` to zoom, arrows to pan
   - Reference: `INTERACTION_SPEC.md` Section 1.3-1.4

**Acceptance Criteria:**
- [ ] Tooltip appears < 50ms on hover
- [ ] Click syncs with imagery viewer within 500ms
- [ ] Zoom animations smooth (60fps)
- [ ] Keyboard navigation works (arrow keys)

---

### Priority 3: Environmental Controls (HIGH)
**Impact:** Key feature to test structural vs environmental changes
**Effort:** Medium

**Interactions:**
1. **Toggle Normalization Switch**
   - Slide animation (200ms)
   - Expand/collapse controls panel
   - Reference: `INTERACTION_SPEC.md` Section 4.1

2. **Slider Drag with Debounce**
   - Real-time visual update (60fps)
   - Debounce API call (300ms after drag ends)
   - Show loading spinner during computation
   - Reference: `INTERACTION_SPEC.md` Section 4.2

3. **Reset Button**
   - Animate sliders back to center (300ms)
   - Recompute residuals
   - Reference: `INTERACTION_SPEC.md` Section 4.3

**Acceptance Criteria:**
- [ ] Slider drag smooth (60fps)
- [ ] API call debounced (300ms after last drag)
- [ ] Score updates with animation (count-up effect)
- [ ] Reset returns to baseline value

---

### Priority 4: Timeline Interactions (MEDIUM)
**Impact:** Understanding when change started
**Effort:** Medium

**Interactions:**
1. **Hover Data Point**
   - Enlarge point (4px → 8px)
   - Show tooltip (month, score, confidence)
   - Crosshair lines to axes
   - Reference: `INTERACTION_SPEC.md` Section 3.1

2. **Click Month to Jump**
   - Highlight clicked month
   - Imagery viewer jumps to that month
   - 400ms transition
   - Reference: `INTERACTION_SPEC.md` Section 3.2

3. **Keyboard Navigation**
   - `[/]` to navigate months
   - `Home/End` to jump to onset/latest
   - Reference: `KEYBOARD_SHORTCUTS.md` Hotspot Detail Page

**Acceptance Criteria:**
- [ ] Tooltip shows on hover < 50ms
- [ ] Click syncs with imagery (400ms transition)
- [ ] Keyboard shortcuts work
- [ ] Timeline remains visible during imagery changes

---

### Priority 5: Filter Panel (MEDIUM)
**Impact:** Critical for finding relevant hotspots
**Effort:** Medium

**Interactions:**
1. **Date Range Picker**
   - Calendar popup (< 100ms)
   - Highlight current range
   - Preset buttons ("Last 30 days", "This year")
   - Reference: `INTERACTION_SPEC.md` Section 6.1

2. **Score Threshold Slider**
   - Real-time value display
   - Debounced filter (500ms)
   - Preview count: "~15 hotspots"
   - Reference: `INTERACTION_SPEC.md` Section 6.2

3. **Reset Filters**
   - Animated return to defaults
   - Synchronized reset (all filters at once)
   - Reference: `INTERACTION_SPEC.md` Section 6.4

**Acceptance Criteria:**
- [ ] Filters apply with 500ms debounce
- [ ] Preview count updates in real-time
- [ ] Reset animates all filters simultaneously
- [ ] Keyboard shortcut `f r` works

---

## Week 3 Implementation Priorities

### Priority 6: Baseline Comparison (MEDIUM)
**Impact:** Validates world model superiority
**Effort:** Low

**Interactions:**
- Hover tooltip on bars
- Click to highlight
- Toggle visibility (checkboxes)
- Reference: `INTERACTION_SPEC.md` Section 5

---

### Priority 7: Export Modal (MEDIUM)
**Impact:** Essential for analyst workflow
**Effort:** Low

**Interactions:**
- Format selection (radio buttons)
- Progress bar (1-5s)
- Success toast + auto-download
- Reference: `INTERACTION_SPEC.md` Section 7

---

### Priority 8: Search/Filter (LOW)
**Impact:** Nice-to-have for large datasets
**Effort:** Medium

**Interactions:**
- Type-to-search (300ms debounce)
- Highlight matching terms
- Clear button
- Reference: `INTERACTION_SPEC.md` Section 8

---

### Priority 9: Advanced Features (LOW)
**Impact:** Power user enhancements
**Effort:** High

**Features:**
- Command Palette (`Ctrl+K`)
- Right-click context menus
- Drag range selection on timeline
- Shortcut customization
- Reference: `KEYBOARD_SHORTCUTS.md` Command Palette Design

---

## Technical Implementation Notes

### Debounce Utility
```javascript
// Use for sliders, search, filters
const debounce = (func, delay) => {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => func(...args), delay);
  };
};

// Usage
const handleSliderChange = debounce((value) => {
  apiCall(value);
}, 300);
```

### Keyboard Event Handler
```javascript
// Global listener, context-aware
document.addEventListener('keydown', (event) => {
  // Skip if typing (except '/' for search)
  if (isTyping(event) && event.key !== '/') return;

  const context = getCurrentContext(); // 'dashboard' | 'detail' | 'modal'
  handleShortcut(event.key, context);
});
```

### Animation Performance
```css
/* Use transform/opacity for 60fps animations */
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 200ms ease-out;
}

/* Avoid animating: width, height, top, left, margin, padding */
```

### ARIA Accessibility
```html
<!-- Focus indicator -->
<button class="hotspot-card" aria-label="Hotspot #1: Mission Bay, Score 0.82">
  ...
</button>

<!-- Live region for dynamic updates -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
  {statusMessage}
</div>
```

---

## Testing Checklist (Per Priority)

### For Each Component:
- [ ] Visual feedback < 100ms for all interactions
- [ ] Animations smooth (60fps)
- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] Screen reader announces changes (ARIA)
- [ ] Touch interactions work (mobile/tablet)
- [ ] No console errors
- [ ] Debounce working (check API call frequency)

---

## Performance Budgets

| Metric | Target | Critical |
|--------|--------|----------|
| Time to Interactive | < 3s | < 5s |
| First Contentful Paint | < 1s | < 2s |
| Hover Feedback | < 50ms | < 100ms |
| Click Feedback | < 100ms | < 200ms |
| Page Transition | < 300ms | < 500ms |
| API Call Response | < 1s | < 2s |

---

## Common Patterns

### Tooltip Pattern
```javascript
// Reusable for heatmap, timeline, chart
<Tooltip
  content="Token R12C8: 0.87"
  delay={50}
  position="auto"
  followCursor={true}
/>
```

### Loading State Pattern
```javascript
// Show spinner after 100ms (avoid flash for fast loads)
{isLoading && <Spinner delay={100} />}
```

### Focus Trap Pattern
```javascript
// For modals (help, export)
<Modal open={isOpen} onClose={handleClose} trapFocus={true}>
  {content}
</Modal>
```

---

## Questions for Agent 5 (UX)

**Before implementing, please confirm:**

1. **Debounce delays:** 300ms for sliders, 500ms for filters - correct?
2. **Transition timing:** 200-400ms - is this fast enough for analysts?
3. **Tooltip positioning:** Follow cursor or fixed position above element?
4. **Mobile priority:** Desktop-first or responsive from start?
5. **Error states:** Should we implement Week 2 error states now or wait?

**Contact:** Via SIAD team channel or docs/UX_*.md comments

---

## Resources

### React Libraries (Suggested)
- **Tooltips:** `@radix-ui/react-tooltip` (accessible, customizable)
- **Modals:** `@radix-ui/react-dialog` (focus trap, ARIA)
- **Sliders:** `@radix-ui/react-slider` (keyboard accessible)
- **Date Picker:** `react-day-picker` (accessible, customizable)
- **Charts:** `recharts` or `visx` (for timeline, baseline chart)

### Animation
- **Framer Motion:** Smooth, declarative animations
- **CSS Transitions:** For simple hover effects

### Accessibility
- **ARIA Guide:** https://www.w3.org/WAI/ARIA/apg/
- **Focus Visible:** `:focus-visible` polyfill if needed

---

## Success Metrics (Post-Implementation)

### Week 3 Targets:
- [ ] All Priority 1-3 interactions implemented
- [ ] Keyboard navigation complete (no mouse needed)
- [ ] 60fps animations on all transitions
- [ ] WCAG 2.1 AA compliance (color contrast, focus indicators)
- [ ] User testing sessions (3-5 analysts)

### Week 4 Targets:
- [ ] All Priority 4-5 interactions implemented
- [ ] Advanced features (Priority 6-9) if time permits
- [ ] User satisfaction > 4/5 (survey)
- [ ] Task completion time < 2 minutes (dashboard → export)

---

**Ready to implement! Focus on Priority 1-3 first, then iterate based on user feedback.**

**Next sync:** Mid-Week 2 - Review Priority 1-3 progress and adjust priorities if needed.
