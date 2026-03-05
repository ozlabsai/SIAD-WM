# SIAD User Flow Diagrams

**Version:** 1.0
**Last Updated:** 2026-03-03
**Owner:** Agent 5 (UX/Interaction)

---

## Target User: Alex Chen

**Role:** Geospatial Intelligence Analyst
**Experience:** 5+ years analyzing satellite imagery
**Context:** Works long hours, needs efficient workflow, must explain findings to stakeholders
**Primary Goal:** Quickly identify high-confidence infrastructure changes and distinguish them from weather/seasonal patterns

---

## Primary User Flow

### Complete Analyst Workflow

```mermaid
flowchart TD
    Start([Analyst Opens Dashboard]) --> Load{Data Loaded?}

    Load -->|Yes| ViewList[View Ranked Hotspot List<br/>Top 10 by Score]
    Load -->|No| LoadState[Show Loading State<br/>Skeleton Screens]
    LoadState --> Load

    ViewList --> HasHotspots{Hotspots Found?}

    HasHotspots -->|Yes| Review[Review Hotspot Cards<br/>Score, Region, Onset]
    HasHotspots -->|No| EmptyState[Empty State:<br/>No Hotspots Detected]

    Review --> NeedFilter{Need to Filter?}
    NeedFilter -->|Yes| ApplyFilters[Apply Filters:<br/>Date, Score, Alert Type]
    NeedFilter -->|No| SelectHotspot[Select Hotspot Card<br/>Click or Keyboard]

    ApplyFilters --> ViewList
    EmptyState --> AdjustFilters[Adjust Filters:<br/>Expand Range, Lower Threshold]
    AdjustFilters --> ViewList

    SelectHotspot --> DetailPage[Hotspot Detail Page]

    DetailPage --> ViewTimeline[Examine Timeline<br/>When did it start?]
    ViewTimeline --> IdentifyOnset[Identify Onset Month]

    IdentifyOnset --> ViewHeatmap[Examine Token Heatmap<br/>Where exactly?]
    ViewHeatmap --> HoverTokens[Hover over High-Residual Tokens<br/>View Values]
    HoverTokens --> ClickToken{Click Token?}

    ClickToken -->|Yes| ZoomImagery[Zoom to Pixel Region<br/>in Satellite Imagery]
    ClickToken -->|No| CompareImagery[Compare Satellite Imagery<br/>Before/After]

    ZoomImagery --> CompareImagery

    CompareImagery --> TestStructural{Structural or<br/>Environmental?}

    TestStructural -->|Test It| ToggleNorm[Toggle Environmental<br/>Normalization]
    TestStructural -->|Skip| ReadExplanation

    ToggleNorm --> AdjustSliders[Adjust Rain/Temp Sliders]
    AdjustSliders --> ObserveChange{Score Changes<br/>Significantly?}

    ObserveChange -->|Yes, Score Drops| EnvFalsePos[Likely Environmental<br/>False Positive]
    ObserveChange -->|No, Score Stable| StructuralChange[Likely Structural<br/>Change]

    StructuralChange --> CompareBaselines[Compare with Baselines<br/>Persistence, Seasonal]
    EnvFalsePos --> CompareBaselines

    CompareBaselines --> ViewBaselines[View Baseline Comparison<br/>World Model vs Others]
    ViewBaselines --> Assessment{Better than<br/>Baselines?}

    Assessment -->|Yes| ReadExplanation[Read Auto-Generated<br/>Explanation]
    Assessment -->|No| FlagReview[Flag for Technical<br/>Review]

    ReadExplanation --> Decision{Analyst<br/>Decision}

    Decision -->|High Confidence| Export[Export Hotspot<br/>GeoJSON/CSV]
    Decision -->|Needs Review| FlagReview
    Decision -->|False Positive| Dismiss[Dismiss/Annotate<br/>as False Positive]
    Decision -->|Need More Data| NextHotspot

    Export --> NextHotspot{More Hotspots<br/>to Review?}
    FlagReview --> NextHotspot
    Dismiss --> NextHotspot

    NextHotspot -->|Yes| BackToDashboard[Back to Dashboard<br/>Press Esc]
    NextHotspot -->|No| FinalExport[Export Final Report<br/>All Flagged Hotspots]

    BackToDashboard --> ViewList
    FinalExport --> End([End Session])
```

---

## Alternative Flow 1: Empty State (No Hotspots)

**Trigger:** No hotspots match current filters
**User Goal:** Find hotspots by adjusting parameters

```mermaid
flowchart TD
    Start([Dashboard Loads]) --> CheckData{Hotspots<br/>Available?}

    CheckData -->|No Results| EmptyState[Empty State Display:<br/>Icon + Message]

    EmptyState --> ShowSuggestions[Show Suggestions:<br/>• Expand date range<br/>• Lower min score<br/>• Change alert type]

    ShowSuggestions --> UserChoice{User Action}

    UserChoice -->|Click Suggestion| AutoAdjust[Auto-Adjust Filter<br/>Based on Suggestion]
    UserChoice -->|Manual Filter| OpenFilters[Open Filter Panel]
    UserChoice -->|Reset All| ResetFilters[Click Reset Filters Button]

    AutoAdjust --> Reload[Reload Hotspot List]
    OpenFilters --> AdjustManual[Manually Adjust Filters]
    AdjustManual --> Reload
    ResetFilters --> Reload

    Reload --> CheckData

    CheckData -->|Results Found| Success[Display Hotspot List]
    Success --> End([Continue Normal Flow])
```

---

## Alternative Flow 2: Loading States

**Trigger:** API calls, computations, data fetching
**User Goal:** Understand progress and maintain control

```mermaid
flowchart TD
    Start([User Action Triggers Load]) --> InitLoad[Show Immediate Feedback<br/>Button State Change]

    InitLoad --> CheckDuration{Expected<br/>Duration?}

    CheckDuration -->|< 1s| QuickLoad[Inline Spinner<br/>No Additional UI]
    CheckDuration -->|1-5s| MediumLoad[Loading Indicator<br/>+ Progress Text]
    CheckDuration -->|> 5s| LongLoad[Progress Bar<br/>+ Cancel Button<br/>+ Time Estimate]

    QuickLoad --> Complete{Load<br/>Complete?}
    MediumLoad --> Complete
    LongLoad --> UserCancel{User Clicks<br/>Cancel?}

    UserCancel -->|Yes| AbortRequest[Abort API Request]
    UserCancel -->|No| Complete

    AbortRequest --> Cancelled[Show Cancellation<br/>Toast]
    Cancelled --> End([Return to Previous State])

    Complete -->|Success| ShowResult[Display Results<br/>Smooth Transition]
    Complete -->|Error| ErrorFlow[Go to Error Flow]

    ShowResult --> End
    ErrorFlow --> End
```

---

## Alternative Flow 3: Error States

**Trigger:** API failure, network issue, computation error
**User Goal:** Understand problem and recover

```mermaid
flowchart TD
    Start([Error Occurs]) --> CategorizeError{Error Type}

    CategorizeError -->|Network Error| NetworkError[Network Error Message:<br/>'Unable to connect to server']
    CategorizeError -->|Not Found| NotFoundError[404 Not Found:<br/>'Tile or hotspot not found']
    CategorizeError -->|Server Error| ServerError[500 Server Error:<br/>'Computation failed']
    CategorizeError -->|Timeout| TimeoutError[Timeout Error:<br/>'Request took too long']

    NetworkError --> ShowError[Display Error Toast<br/>Top-Right Corner]
    NotFoundError --> ShowInline[Display Inline Error<br/>In Content Area]
    ServerError --> ShowError
    TimeoutError --> ShowError

    ShowError --> OfferActions[Offer Actions:<br/>• Retry Button<br/>• Contact Support Link]
    ShowInline --> OfferActions

    OfferActions --> UserAction{User Action}

    UserAction -->|Retry| Retry[Retry Request]
    UserAction -->|Contact Support| OpenSupport[Open Support Modal<br/>Pre-filled Error Details]
    UserAction -->|Dismiss| Dismiss[Dismiss Error]
    UserAction -->|Go Back| GoBack[Navigate to Previous Page]

    Retry --> CheckRetry{Retry<br/>Successful?}

    CheckRetry -->|Yes| Success[Show Success State]
    CheckRetry -->|No| RetryCount{Retry Count<br/>< 3?}

    RetryCount -->|Yes| Retry
    RetryCount -->|No| FinalError[Show Final Error:<br/>'Multiple attempts failed'<br/>Contact Support]

    Success --> End([Continue Normal Flow])
    OpenSupport --> End
    Dismiss --> End
    GoBack --> End
    FinalError --> End
```

---

## Micro-Flows: Key Interactions

### Micro-Flow A: Token Heatmap Exploration

**Duration:** 30-60 seconds
**Goal:** Identify exact pixel location of change

```mermaid
flowchart TD
    Start([View Heatmap]) --> InitialView[Overview: 16×16 Token Grid<br/>Color-coded by Residual]

    InitialView --> Scan[Visually Scan for<br/>Hot Spots - Red/Orange]

    Scan --> HoverToken[Hover over High-Residual Token]
    HoverToken --> ShowTooltip[Tooltip Appears:<br/>• Token Index - R12C8<br/>• Residual Value - 0.87<br/>• Pixel Coordinates]

    ShowTooltip --> UserChoice{User Action}

    UserChoice -->|Click Token| HighlightToken[Highlight Token<br/>Show Border]
    UserChoice -->|Move to Next| HoverToken
    UserChoice -->|Zoom In| ZoomHeatmap[Zoom into Region<br/>Scroll to Zoom]

    HighlightToken --> SyncImagery[Sync with Imagery Viewer:<br/>Zoom to Corresponding Pixels]
    ZoomHeatmap --> HoverToken

    SyncImagery --> ComparePixels[Compare Pixels<br/>Before/After]
    ComparePixels --> End([Analysis Complete])
```

### Micro-Flow B: Environmental Normalization Test

**Duration:** 20-40 seconds
**Goal:** Determine if change is structural or environmental

```mermaid
flowchart TD
    Start([View Hotspot Detail]) --> InitialScore[Note Current Score<br/>e.g., 0.82]

    InitialScore --> ToggleNorm[Click 'Normalize Weather'<br/>Toggle Button]

    ToggleNorm --> ShowControls[Environmental Controls Appear:<br/>• Rain Slider -50% to +50%<br/>• Temp Slider -10°C to +10°C]

    ShowControls --> AdjustRain[Drag Rain Slider<br/>Simulate +30% Rainfall]

    AdjustRain --> Debounce[Debounce 300ms<br/>Before API Call]

    Debounce --> UpdateScore[Recompute Residuals<br/>Update Score in Real-Time]

    UpdateScore --> ShowNewScore[New Score Displayed<br/>e.g., 0.45]

    ShowNewScore --> Interpret{Score Change<br/>Significant?}

    Interpret -->|Dropped >30%| EnvSensitive[Likely Environmental<br/>Show Warning Badge]
    Interpret -->|Stable ±10%| Structural[Likely Structural<br/>Show Confidence Badge]

    EnvSensitive --> ResetOption[Offer Reset Button]
    Structural --> ResetOption

    ResetOption --> UserDecision{User Action}

    UserDecision -->|Reset| ResetValues[Reset Sliders to 0]
    UserDecision -->|Continue Testing| AdjustTemp[Adjust Temp Slider]
    UserDecision -->|Accept Result| End([Mark as Structural/Env])

    ResetValues --> ShowControls
    AdjustTemp --> Debounce
```

### Micro-Flow C: Baseline Comparison

**Duration:** 15-30 seconds
**Goal:** Validate world model superiority

```mermaid
flowchart TD
    Start([Hotspot Detail Page]) --> ClickBaseline[Click 'Compare Baselines'<br/>Button]

    ClickBaseline --> LoadBaselines[Fetch Baseline Data<br/>Persistence, Seasonal]

    LoadBaselines --> ShowChart[Display Bar Chart:<br/>World Model vs Baselines]

    ShowChart --> HighlightBest[Highlight Lowest Residual<br/>Ideally World Model]

    HighlightBest --> HoverBar[Hover over Each Bar]
    HoverBar --> ShowTooltip[Tooltip Shows:<br/>• Model Name<br/>• Residual Value<br/>• Confidence Interval]

    ShowTooltip --> Interpret{World Model<br/>Best?}

    Interpret -->|Yes| GreenBadge[Show Green Badge:<br/>'World Model -24% better']
    Interpret -->|No| YellowWarning[Show Yellow Warning:<br/>'World Model Not Best']

    GreenBadge --> ReadExplanation[Auto-Explanation Updates:<br/>'...outperforms baselines...']
    YellowWarning --> ReadExplanation

    ReadExplanation --> End([Continue Analysis])
```

---

## Decision Points & User Goals

### Decision Point 1: Filter or Not?
**Location:** Dashboard hotspot list
**User Question:** "Are these the right hotspots for my analysis?"
**Options:**
- Yes → Proceed to select hotspot
- No → Apply filters (date range, score threshold, alert type)

**Design Implications:**
- Make current filters clearly visible
- Provide filter shortcuts (preset ranges: "Last 30 days", "High confidence only")
- Show result count: "Showing 10 of 47 hotspots"

---

### Decision Point 2: Structural or Environmental?
**Location:** Hotspot detail page
**User Question:** "Is this change real infrastructure or just weather?"
**Options:**
- Test with environmental normalization
- Skip testing (trust initial score)
- View historical weather data

**Design Implications:**
- Prominent "Test Environmental Sensitivity" button
- Clear visual feedback when score changes
- Auto-suggest: "Score dropped 40% when rain adjusted → Likely environmental"

---

### Decision Point 3: Export or Flag?
**Location:** After analysis
**User Question:** "What should I do with this hotspot?"
**Options:**
- Export for report (high confidence)
- Flag for technical review (uncertain)
- Dismiss as false positive
- Continue to next hotspot

**Design Implications:**
- Action buttons clearly labeled
- Export options visible: "Export as GeoJSON", "Export Timeline CSV"
- Flag modal: "Add note for reviewer"

---

### Decision Point 4: Click Token or Not?
**Location:** Token heatmap
**User Question:** "Do I need to see the exact pixels?"
**Options:**
- Click to zoom into imagery (precision analysis)
- Just hover for quick check
- Skip heatmap, rely on timeline

**Design Implications:**
- Heatmap optional but prominent
- Tooltip hints: "Click to zoom imagery"
- Keyboard shortcut: `h` to toggle heatmap visibility

---

## User Goals by Page

### Dashboard Page
**Primary Goal:** Quickly identify the most important hotspots
**Secondary Goals:**
- Understand recent trends (new hotspots this week)
- Filter to relevant region/timeframe
- Compare hotspot severity

**Success Metrics:**
- Time to identify top hotspot < 10 seconds
- Can explain why hotspot is ranked #1

---

### Hotspot Detail Page
**Primary Goal:** Determine if hotspot is actionable
**Secondary Goals:**
- Understand when change started (onset)
- Identify exact location (heatmap)
- Rule out environmental false positives
- Compare to baseline models

**Success Metrics:**
- Time to make decision < 2 minutes
- Confidence in decision (self-reported)

---

### Export/Report Flow
**Primary Goal:** Extract data for external reporting
**Secondary Goals:**
- Include metadata (score, onset, confidence)
- Format for GIS tools (GeoJSON)
- Share with stakeholders (CSV)

**Success Metrics:**
- Time to export < 30 seconds
- Export includes all necessary fields

---

## Flow Optimization Opportunities

### Speed Improvements
1. **Keyboard Navigation:** Power users never need mouse
2. **Predictive Loading:** Preload detail page on hover (speculative)
3. **Cached Baselines:** Don't recompute on every visit
4. **Bulk Export:** Select multiple hotspots → Export all

### Clarity Improvements
1. **Progressive Disclosure:** Hide advanced features until needed
2. **Contextual Help:** `?` icon next to complex terms
3. **Visual Timeline:** Color-coded months (onset=red, peak=orange)
4. **Confidence Indicators:** High/Medium/Low badges

### Error Prevention
1. **Confirm Destructive Actions:** "Are you sure you want to dismiss?"
2. **Auto-Save Filters:** Remember user's preferred settings
3. **Warn on Edge Cases:** "Only 2 months of data available"

---

## Accessibility Considerations

### Screen Reader Flow
- Logical heading structure (H1: Dashboard, H2: Hotspot #1)
- ARIA live regions for dynamic updates
- Alt text for heatmap: "Token heatmap showing high residuals in northeast quadrant"

### Keyboard-Only Flow
- All actions accessible via Tab + Enter
- Skip navigation: "Skip to hotspot list"
- Focus trap in modals
- Clear focus indicators (2px border)

### Low Vision Flow
- High contrast mode support
- Zoom up to 200% without breaking layout
- Text alternatives for color-coded data

---

## Next Steps

1. **Review with Agent 3 (Design):** Visual states for each flow node
2. **Review with Agent 4 (Frontend):** Implementation feasibility
3. **Create Interaction Spec:** Detailed timing and feedback (Task 2)
4. **Design Keyboard Shortcuts:** Power user efficiency (Task 3)

---

**Deliverable Status:** COMPLETE ✓
**Dependencies:** Agent 3 (visual design), Agent 4 (implementation)
