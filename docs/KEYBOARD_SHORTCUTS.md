# SIAD Keyboard Shortcuts Specification

**Version:** 1.0
**Last Updated:** 2026-03-03
**Owner:** Agent 5 (UX/Interaction)
**For Implementation by:** Agent 4 (Frontend)

---

## Design Philosophy

**Target User:** Alex Chen - Power analyst who uses SIAD daily, needs fast workflow

**Principles:**
1. **Vim-inspired navigation:** `j/k` for up/down (familiar to terminal users)
2. **Mnemonic keys:** `e` for Export, `n` for Normalize, `b` for Baselines
3. **No conflicts:** Avoid browser shortcuts (Ctrl+T, Ctrl+W, etc.)
4. **Context-aware:** Same key does different things on different pages (consistent within context)
5. **Discoverable:** `?` always shows help modal

---

## Global Shortcuts (Work Anywhere)

| Key | Action | Context | Visual Feedback |
|-----|--------|---------|-----------------|
| `?` | Show keyboard shortcuts help modal | Any page | Modal slides in from center |
| `/` | Focus search/filter input | Any page | Input highlights, cursor blinks |
| `Esc` | Cancel/Close/Go back | Any page | Close modal, clear selection, or navigate back |
| `Ctrl + K` | Command palette (quick actions) | Any page | Command palette modal opens |
| `g h` | Go to home/dashboard | Any page | Navigate to dashboard (vim-style "go home") |
| `g s` | Go to settings | Any page | Navigate to settings page |
| `Ctrl + ,` | Open settings (alternative) | Any page | Settings modal opens |

---

## Dashboard Page Shortcuts

### Navigation
| Key | Action | Visual Feedback |
|-----|--------|-----------------|
| `j` | Move focus to next hotspot card | Next card highlights with focus ring |
| `k` | Move focus to previous hotspot card | Previous card highlights |
| `g g` | Jump to top of list (vim-style) | Scroll to first hotspot, focus on it |
| `G` (Shift+g) | Jump to bottom of list | Scroll to last hotspot, focus on it |
| `Enter` / `Space` | Open focused hotspot detail | Navigate to detail page |
| `1` - `9` | Jump to hotspot rank 1-9 | Focus and highlight corresponding card |

### Filtering
| Key | Action | Visual Feedback |
|-----|--------|-----------------|
| `/` | Focus search input | Input highlights, placeholder updates |
| `f d` | Open date filter | Date picker modal opens (mnemonic: Filter Date) |
| `f s` | Open score threshold filter | Score slider focuses (mnemonic: Filter Score) |
| `f a` | Open alert type filter | Alert dropdown opens (mnemonic: Filter Alert) |
| `f r` | Reset all filters | Filters animate back to defaults, toast confirms |
| `Ctrl + Shift + F` | Toggle filter panel visibility | Filter sidebar slides in/out |

### Selection & Bulk Actions
| Key | Action | Visual Feedback |
|-----|--------|-----------------|
| `x` | Select/deselect focused hotspot | Checkbox appears, card highlights |
| `Shift + j/k` | Extend selection up/down | Multiple cards highlight |
| `Ctrl + A` | Select all visible hotspots | All cards highlight, toast shows count |
| `e` | Export selected hotspots | Export modal opens (if 1+ selected) |
| `d` | Dismiss selected hotspots | Confirmation modal opens |

### View Options
| Key | Action | Visual Feedback |
|-----|--------|-----------------|
| `v l` | Switch to list view | View changes to vertical list |
| `v g` | Switch to grid view | View changes to card grid |
| `v m` | Toggle map overlay | Map pane slides in/out from right |
| `s` | Sort by... (opens menu) | Sort dropdown menu appears |

---

## Hotspot Detail Page Shortcuts

### Navigation
| Key | Action | Visual Feedback |
|-----|--------|-----------------|
| `Esc` | Return to dashboard | Navigate back, preserve scroll position |
| `n` | Next hotspot (if viewing from list) | Navigate to next in list, smooth transition |
| `p` | Previous hotspot | Navigate to previous in list |
| `[` | Previous month in timeline | Timeline scrolls left, imagery updates |
| `]` | Next month in timeline | Timeline scrolls right, imagery updates |
| `Home` | Jump to onset month | Timeline jumps to first month, imagery updates |
| `End` | Jump to latest month | Timeline jumps to most recent month |

### Analysis Actions
| Key | Action | Visual Feedback |
|-----|--------|-----------------|
| `h` | Toggle token heatmap visibility | Heatmap panel slides in/out |
| `i` | Toggle satellite imagery viewer | Imagery panel slides in/out |
| `t` | Toggle timeline visibility | Timeline panel collapses/expands |
| `c` | Toggle baseline comparison chart | Chart panel slides in/out |
| `Space` | Play/pause timeline animation | Months auto-advance (1s intervals) |

### Environmental Controls
| Key | Action | Visual Feedback |
|-----|--------|-----------------|
| `n` | Toggle environmental normalization | Switch flips, controls panel expands/collapses |
| `r` | Focus rain slider (then Arrow keys to adjust) | Rain slider highlights, value updates |
| `t` | Focus temperature slider | Temp slider highlights, value updates |
| `0` (zero) | Reset environmental controls to neutral | Sliders animate to center, score recomputes |
| `1` | Apply "Wet Season" preset | Sliders jump to preset values |
| `2` | Apply "Dry Season" preset | Sliders jump to preset values |
| `3` | Apply "Winter" preset | Sliders jump to preset values |

**Slider Adjustment (when focused):**
| Key | Action |
|-----|--------|
| `←` / `→` | Decrease/increase value by 5% |
| `Shift + ←/→` | Decrease/increase value by 1% (fine-tune) |
| `Home` | Set to minimum value |
| `End` | Set to maximum value |

### Token Heatmap
| Key | Action | Visual Feedback |
|-----|--------|-----------------|
| `h` | Toggle heatmap visibility | Heatmap panel slides in/out |
| `Arrow keys` | Navigate tokens (when heatmap focused) | Token highlights, imagery syncs |
| `Enter` | Click current token (zoom imagery) | Imagery zooms to pixel region |
| `+` / `-` | Zoom heatmap in/out | Heatmap scale increases/decreases |
| `0` | Reset heatmap zoom to 1x | Heatmap resets to original size |
| `Tab` | Cycle through high-residual tokens | Jump to next token > threshold |
| `Shift + Tab` | Cycle backward through tokens | Jump to previous high-residual token |

### Actions
| Key | Action | Visual Feedback |
|-----|--------|-----------------|
| `e` | Export hotspot | Export modal opens with this hotspot pre-selected |
| `f` | Flag for review | Flag modal opens, cursor in notes field |
| `d` | Dismiss as false positive | Confirmation modal opens |
| `Ctrl + C` | Copy coordinates to clipboard | Toast: "Coordinates copied!" |
| `Ctrl + Shift + C` | Copy full hotspot JSON | Toast: "JSON copied to clipboard" |
| `s` | Share hotspot (generate link) | Share modal with copyable URL |

### Comparison
| Key | Action | Visual Feedback |
|-----|--------|-----------------|
| `b` | Toggle baseline comparison | Baseline chart slides in/out |
| `1` - `3` | Highlight baseline (1=Persistence, 2=Seasonal, 3=World Model) | Bar highlights, tooltip appears |
| `a` | Show all baselines | All bars visible, chart rescales |

---

## Modal Shortcuts (Context-Dependent)

### Help Modal (`?`)
| Key | Action |
|-----|--------|
| `Esc` | Close help modal |
| `Tab` / `Shift+Tab` | Navigate sections |
| `1` - `5` | Jump to section (1=Navigation, 2=Filters, etc.) |
| `Ctrl + F` | Search within help modal |

### Export Modal (`e`)
| Key | Action |
|-----|--------|
| `g` | Select GeoJSON format (radio button) |
| `c` | Select CSV format |
| `k` | Select KML format |
| `s` | Select Shapefile format |
| `Enter` | Confirm and export |
| `Esc` | Cancel export |

### Filter Modal
| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Navigate filter fields |
| `Space` | Toggle checkboxes |
| `Enter` | Apply filters |
| `Ctrl + Backspace` | Reset all filters |
| `Esc` | Cancel changes, restore previous filters |

### Command Palette (`Ctrl + K`)
| Key | Action |
|-----|--------|
| `Esc` | Close command palette |
| `↓` / `↑` | Navigate commands |
| `Enter` | Execute selected command |
| Type to filter commands (fuzzy search) |

**Command Palette Commands:**
- "Export all hotspots"
- "Go to hotspot #5"
- "Apply wet season preset"
- "Reset all filters"
- "Toggle dark mode"
- "Show keyboard shortcuts"
- etc.

---

## Accessibility Shortcuts

| Key | Action | Purpose |
|-----|--------|---------|
| `Alt + 1` | Skip to main content | Bypass navigation for screen readers |
| `Alt + 2` | Skip to filter panel | Jump to filtering controls |
| `Alt + 3` | Skip to hotspot list | Jump directly to results |
| `Tab` | Navigate interactive elements | Standard tab order |
| `Shift + Tab` | Navigate backward | Reverse tab order |
| `Enter` / `Space` | Activate focused element | Standard activation |
| `Ctrl + Home` | Jump to page top | Quick navigation |
| `Ctrl + End` | Jump to page bottom | Quick navigation |

---

## Shortcut Conflicts & Resolutions

### Browser Conflicts (Avoided)
- `Ctrl + T` (New tab) - NOT used
- `Ctrl + W` (Close tab) - NOT used
- `Ctrl + R` (Reload) - NOT used
- `Ctrl + F` (Find in page) - Only used within modals (local context)
- `Ctrl + P` (Print) - NOT used (use `Ctrl + Shift + P` for command palette alt)

### Screen Reader Conflicts
- JAWS/NVDA use many shortcuts - our shortcuts deactivate when screen reader detected
- Provide alternative: Command Palette (`Ctrl + K`) for all actions

### Context-Aware Resolution
| Key | Dashboard | Detail Page | Modal |
|-----|-----------|-------------|-------|
| `n` | Next page | Toggle normalization | Next modal section |
| `b` | (unused) | Toggle baselines | (unused) |
| `h` | (unused) | Toggle heatmap | Navigate to Help section |
| `Esc` | Clear selection | Back to dashboard | Close modal |

---

## Help Modal Design

**Trigger:** Press `?` key from any page

### Modal Layout

```
┌────────────────────────────────────────────────────────────┐
│  SIAD Keyboard Shortcuts                            [×]    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  📌 Quick Reference                                        │
│                                                            │
│  Global                                                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  ?        Show this help                             │ │
│  │  /        Search or filter                           │ │
│  │  Esc      Cancel, close, or go back                  │ │
│  │  Ctrl+K   Command palette (quick actions)            │ │
│  │  g h      Go to home/dashboard                       │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Navigation (Dashboard)                                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  j / k    Next/previous hotspot                      │ │
│  │  Enter    Open hotspot detail                        │ │
│  │  1-9      Jump to hotspot rank 1-9                   │ │
│  │  g g      Jump to top of list                        │ │
│  │  G        Jump to bottom of list                     │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Filtering (Dashboard)                                     │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  f d      Filter by date                             │ │
│  │  f s      Filter by score                            │ │
│  │  f a      Filter by alert type                       │ │
│  │  f r      Reset all filters                          │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Analysis (Hotspot Detail)                                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  n        Toggle environmental normalization         │ │
│  │  b        Toggle baseline comparison                 │ │
│  │  h        Toggle token heatmap                       │ │
│  │  [ / ]    Previous/next month in timeline            │ │
│  │  Space    Play/pause timeline animation              │ │
│  │  e        Export hotspot                             │ │
│  │  f        Flag for review                            │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ─────────────────────────────────────────────────────    │
│                                                            │
│  💡 Tip: Press Ctrl+K to open command palette for quick   │
│     access to all actions with fuzzy search.              │
│                                                            │
│  🖨️ Print this guide   📥 Download PDF                    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Help Modal Features

1. **Categorized Shortcuts:**
   - Global (always available)
   - Page-specific (Dashboard, Detail)
   - Modal-specific
   - Accessibility

2. **Search Within Help:**
   - Type to filter shortcuts
   - Fuzzy search: "export" finds all export-related shortcuts
   - Highlight matching text

3. **Visual Key Indicators:**
   - Keys shown in rounded rectangles: `Esc` `Enter` `Ctrl+K`
   - Key combinations clearly separated: `Ctrl` + `K`
   - Mnemonic hints in descriptions

4. **Interactive Elements:**
   - Click shortcut to see demo (animated GIF)
   - Click category to expand/collapse
   - Click "Try it" button to trigger action from help modal

5. **Responsive Design:**
   - Desktop: Modal (800px wide)
   - Tablet: Full-screen modal with scroll
   - Mobile: Bottom sheet with swipe gestures

---

## Command Palette Design

**Trigger:** `Ctrl + K` (or `Cmd + K` on Mac)

### Palette Layout

```
┌────────────────────────────────────────────────────────────┐
│  🔍 Type a command or search...                       [×]  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Recent                                                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  📊 Export all hotspots                         Ctrl+E│ │
│  │  🎯 Go to hotspot #5                             g 5  │ │
│  │  🌧️  Apply wet season preset                       1  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Suggestions                                               │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  🏠 Go to dashboard                              g h  │ │
│  │  🔍 Search hotspots                                /  │ │
│  │  ❓ Show keyboard shortcuts                        ?  │ │
│  │  ⚙️  Open settings                            Ctrl+,  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Palette Features

1. **Fuzzy Search:**
   - Type "exp" → Shows "Export all hotspots", "Export timeline"
   - Type "base" → Shows "Toggle baseline comparison"
   - Type "norm" → Shows "Toggle environmental normalization"

2. **Command Categories:**
   - Navigation (Go to...)
   - Actions (Export, Flag, Dismiss)
   - View Toggles (Show/Hide panels)
   - Filters (Apply, Reset)
   - Settings (Preferences, Theme)

3. **Keyboard Shortcuts Shown:**
   - Each command shows its keyboard shortcut on the right
   - Grayed out if no shortcut assigned
   - Learn shortcuts through repetition

4. **Recent Commands:**
   - Remember last 5 commands executed
   - Quick access to frequent actions

5. **Smart Suggestions:**
   - Context-aware: Different suggestions on Dashboard vs Detail page
   - Learns from usage: Most-used commands float to top

---

## Shortcut Customization (Optional)

**Location:** Settings > Keyboard Shortcuts

### Customization Features

1. **Remap Keys:**
   - Click shortcut, press new key combination
   - Validate: No conflicts with browser/OS shortcuts
   - Reset to defaults button

2. **Import/Export Presets:**
   - Export as JSON file (share with team)
   - Import from file
   - Presets: "Vim-style", "Emacs-style", "Default"

3. **Disable Shortcuts:**
   - Toggle individual shortcuts on/off
   - Useful if conflicts with other tools

4. **Shortcut Profiles:**
   - "Beginner" (only essential shortcuts)
   - "Power User" (all shortcuts)
   - "Custom" (user-defined)

---

## Onboarding: Teaching Shortcuts

### First-Time User Flow

1. **Welcome Modal (optional):**
   - "Welcome to SIAD! Press `?` anytime for keyboard shortcuts."
   - "Try it now" button → Opens help modal

2. **Tooltip Hints:**
   - On first hover of interactive element:
     - "Tip: Press `j` to navigate to next hotspot"
   - Dismiss permanently: "Don't show again"

3. **Shortcut Badges:**
   - Show key hint next to button text (first 3 sessions)
   - Example: [Export `e`] button
   - Fade out after user learns shortcut

4. **Progressive Disclosure:**
   - Week 1: Teach global shortcuts (?, /, Esc)
   - Week 2: Teach navigation (j, k, Enter)
   - Week 3: Teach analysis shortcuts (n, b, h)

5. **Achievement Unlocks (gamification, optional):**
   - "Keyboard Ninja: Used 10 different shortcuts!"
   - "Speed Demon: Navigated 5 hotspots without mouse"

---

## Implementation Notes (for Agent 4)

### Event Handling

```javascript
// Global keyboard event listener
document.addEventListener('keydown', (event) => {
  // Ignore if typing in input field (except search shortcut '/')
  if (
    document.activeElement.tagName === 'INPUT' ||
    document.activeElement.tagName === 'TEXTAREA'
  ) {
    if (event.key !== '/') return;
    event.preventDefault(); // Prevent '/' from appearing in input
  }

  // Handle shortcuts
  switch (event.key) {
    case '?':
      openHelpModal();
      break;
    case '/':
      focusSearchInput();
      break;
    case 'Escape':
      handleEscape();
      break;
    // ... more shortcuts
  }
});
```

### Context-Aware Shortcuts

```javascript
// Different behavior based on current page/component
const handleShortcut = (key) => {
  const context = getCurrentContext(); // 'dashboard', 'detail', 'modal'

  if (key === 'n') {
    switch (context) {
      case 'dashboard':
        navigateToNextPage();
        break;
      case 'detail':
        toggleNormalization();
        break;
      case 'modal':
        navigateToNextModalSection();
        break;
    }
  }
};
```

### Preventing Conflicts

```javascript
// Detect screen reader
const isScreenReaderActive = () => {
  // Check ARIA attributes, navigator.mediaSession, etc.
  return document.body.getAttribute('data-screen-reader') === 'true';
};

// Disable shortcuts if screen reader detected
if (isScreenReaderActive()) {
  disableKeyboardShortcuts();
  // Only allow command palette (Ctrl+K) for all actions
}
```

### Accessibility

```html
<!-- ARIA labels for shortcuts -->
<button
  aria-label="Export hotspot (shortcut: E)"
  data-shortcut="e"
  onClick={handleExport}
>
  Export
</button>

<!-- Screen reader announcements -->
<div aria-live="polite" aria-atomic="true">
  Keyboard shortcut activated: Export hotspot
</div>
```

---

## Testing Checklist

- [ ] All shortcuts work on Dashboard page
- [ ] All shortcuts work on Hotspot Detail page
- [ ] Modal shortcuts work in all modals (Help, Export, Filter)
- [ ] No conflicts with browser shortcuts
- [ ] No conflicts with OS shortcuts (Mac, Windows, Linux)
- [ ] Shortcuts disabled when typing in input fields (except `/`)
- [ ] Help modal (`?`) shows all current shortcuts
- [ ] Command palette (`Ctrl+K`) lists all commands
- [ ] Shortcuts work with screen readers (or gracefully disabled)
- [ ] Visual feedback for all shortcut actions
- [ ] Keyboard-only navigation is complete (no mouse needed)
- [ ] Focus indicators visible on all interactive elements
- [ ] Tab order is logical
- [ ] Shortcut hints appear on first-time use
- [ ] Customization settings save and persist
- [ ] Export/import shortcut presets works

---

## Metrics & Success Criteria

### Adoption Metrics
- % of users who use at least 1 shortcut per session
- Most-used shortcuts (track frequency)
- Time to complete task: Mouse vs Keyboard

### Success Targets (Week 4)
- **50%** of power users use shortcuts daily
- **Top 5 shortcuts** used in >80% of sessions: `?`, `/`, `j/k`, `Enter`, `Esc`
- **Average task time** reduced by 30% for keyboard users

### User Feedback
- Survey: "Do shortcuts make you more efficient?" (1-5 scale)
- Track: How often is help modal (`?`) opened?
- Track: How often is command palette (`Ctrl+K`) used?

---

## Future Enhancements (Post-MVP)

1. **Vim-style Command Mode:**
   - Press `:` to enter command mode
   - Type commands: `:export`, `:goto 5`, `:filter date=2024-06`

2. **Macro Recording:**
   - Record sequence of actions
   - Replay with single shortcut
   - Example: "Apply filters + Export top 5"

3. **Voice Commands (accessibility):**
   - "Export hotspot 3"
   - "Toggle normalization"
   - Useful for visually impaired users

4. **Gesture Shortcuts (mobile):**
   - Swipe left on card → Export
   - Swipe right → Dismiss
   - Two-finger tap → Baseline comparison

5. **AI-Suggested Shortcuts:**
   - "You frequently export after normalization. Create shortcut?"
   - Auto-suggest based on usage patterns

---

**Deliverable Status:** COMPLETE ✓

**Next Steps:**
1. Review with Agent 4 (Frontend) for implementation
2. Create interactive prototype for user testing
3. Design help modal visuals (collaborate with Agent 3)
4. Write tooltip content (collaborate with Agent 6)

**Dependencies:**
- Agent 4: Implement shortcuts in React components
- Agent 3: Design help modal and shortcut badge visuals
- Agent 6: Write shortcut descriptions and tooltip copy
