# UNIFIED SINGLE-PAGE LAYOUT DESIGN
## 광고 분석 대시보드 - 통합 단일 페이지 레이아웃

### Overall Structure
Grid layout: 1fr (main) + 320px (sidebar)
- Left: Scrollable main content
- Right: Sticky sidebar (height: 100vh, overflow-y: auto)
- Top: Sticky header (z-index: 100)

### Main Content Sections (Top to Bottom)
1. Metrics Grid (8 cards: Spend, Revenue, ROAS, Conversions, Impressions, Clicks, CTR, CVR)
2. Daily Trend Chart (full width, height: 350px)
3. ROAS Distribution + Budget Pie (2x1 grid)
4. Conversion Funnel + Campaign Comparison (2x1 grid)
5. Weekday Heatmap (full width, ROAS + CTR)
6. CREATIVE ANALYSIS ⭐ (HIGHLIGHTED - blue border, gradient bg)
   - 4 Tabs: Top ROAS | Top CVR | All Creatives | Low Performers
   - Tables with: Rank, Creative Name, Metrics, Status
7. Campaign Performance Table (full width, sortable)
8. AI Insights (full width, text area)

### Right Sidebar Sections
1. Saved Analyses (recent 2-3, "more" button)
2. Period Comparison (select A, select B, compare button, result area)
3. Goals & Budget Pacing (month input, budget, ROAS target, pacing display)

### Sticky Header Content
- Title + Subtitle
- Action Buttons: Upload, Manual Input, Save, PDF, Excel
- Date Filter: Today | 7 Days | 30 Days | Custom

### Modal Dialogs
1. Upload Modal (file drop zone + templates)
2. Manual Input Modal (form with row preview)
3. Save Analysis Modal (name, tags, memo)
4. Saved Analyses List Modal
5. Campaign Details Modal

### CSS Classes Reference

Layout:
- .dashboard-wrapper (grid: 1fr 320px)
- .main-scroll (overflow-y: auto)
- .sidebar-panel (position: sticky, height: 100vh)
- .sticky-header (position: sticky, top: 0, z-index: 100)
- .main-container (max-width: 1200px, margin: 0 auto)

Sections:
- .section (white card, shadow, rounded)
- .section-header (padding, border-bottom, flex)
- .section-content (padding)
- .section-title (flex, gap)
- .section-icon (font-size: 18px)

Metrics:
- .metrics-grid (auto-fit, minmax 140px)
- .metric-card (gradient bg, color-coded)
- .metric-card.green / .orange / .red / .purple
- .metric-label (uppercase, small)
- .metric-value (large font)
- .metric-change (small, opacity)

Charts:
- .charts-grid (grid: 2fr)
- .chart-container (position: relative, height: 350px)
- .full-width (grid-column: 1 / -1)

Tables:
- .table-wrapper (overflow-x: auto)
- table (100% width)
- th (bg-hover, uppercase, letter-spacing)
- td (padding, border-bottom)
- tr:hover (bg-hover)

Badges:
- .badge (inline-block, text-uppercase)
- .badge-success / .warning / .danger / .neutral

Sidebar:
- .sidebar-section (border-bottom)
- .sidebar-section-header (bg-hover, uppercase)
- .sidebar-section-content (flex, flex-direction: column)
- .sidebar-item (padding, bg-hover, cursor)
- .sidebar-item.active (bg-blue-light, color: blue)

Creative:
- .creative-analysis-highlight (border: 2px solid blue, gradient bg)
- .creative-analysis-badge (inline-block, blue bg, white text)
- .section-tabs (flex, gap, overflow-x: auto)
- .section-tab (padding, border-bottom: 3px solid transparent)
- .section-tab.active (color: blue, border-bottom-color: blue)
- .creative-tab (hidden by default, show when active)

Modals:
- .modal (position: fixed, z-index: 1000, bg: rgba)
- .modal.active (display: flex)
- .modal-content (white bg, padding, border-radius, shadow)
- .modal-header (flex, justify-between)
- .modal-close (background: none, border: none, cursor)

Forms:
- .form-group (margin-bottom)
- .form-label (display: block, font-weight)
- .form-input / .form-select / .form-textarea (width: 100%, padding, border)
- .form-input:focus (outline: none, border-color: blue, box-shadow)

Heatmap:
- .heatmap-container (grid: 7fr)
- .heatmap-cell (aspect-ratio: 1, cursor: pointer)
- .heatmap-cell.low / .medium / .high (color gradient)

Upload:
- .upload-area (border: 2px dashed, padding, text-align: center)
- .upload-area:hover (border-color: blue, bg: blue-light)
- .upload-area.dragging (border-color: green, bg: green-light)

Utilities:
- .hidden (display: none !important)
- .text-center (text-align: center)
- .mt-lg / .mb-lg (margin-top/bottom)
- .gap-md (gap)
- .status-up / .status-down (color)
- .full-width

### Responsive Breakpoints

Desktop (>1400px):
- Grid: 1fr 320px (sidebar visible)
- Charts: 2 column
- Metrics: auto-fit

Tablet (1200-1400px):
- Grid: 1fr (sidebar hidden)
- Charts: 1 column
- Metrics: auto-fit

Mobile (<768px):
- Full stack
- Metrics: 2 column
- Header actions: icons only
- Filter: compact
- Sidebar: hidden / modal

### Colors
Primary: #1a73e8 (blue)
Green: #0f9d58
Orange: #f9ab00
Red: #ea4335
Purple: #9c27b0
Gray: #f8f9fa / #ffffff / #dadce0

### Key JavaScript Functions

Init:
- initDashboard()
- initTabs()
- initUploadArea()
- initDateFilter()

Data:
- loadMetrics()
- loadCharts()
- loadCreativeAnalysis()
- loadCampaigns()
- loadAIInsights()
- loadSavedAnalyses()

Filters:
- setDateRange(type) // today, 7days, 30days, custom
- applyCustomDateRange()

UI:
- switchCreativeTab(tabName)
- sortCampaigns(sortBy)
- toggleSidebarSection(id)

Modals:
- openUploadModal() / closeUploadModal()
- openManualInputModal() / closeManualInputModal()
- openSaveModal() / closeSaveModal()
- openSavedAnalysesModal() / closeSavedAnalysesModal()
- openCampaignDetailsModal(id) / closeCampaignDetailsModal()

Actions:
- uploadFile(file)
- addManualDataRow(event)
- submitManualData()
- saveCurrentAnalysis()
- confirmSave()
- compareAnalysis()
- saveGoal()
- loadBudgetPacing()
- exportPDF() / exportExcel()
- downloadTemplate(type)

### Scroll Flow (Top to Bottom)
1. Sticky Header (always visible at top)
2. Metrics Cards (first impression)
3. Daily Trend (trend overview)
4. Distribution Charts (deeper analysis)
5. Funnel & Comparison (multi-view)
6. Heatmap (pattern discovery)
7. CREATIVE ANALYSIS ⭐ (main focus, highlighted)
8. Campaign Table (detailed tracking)
9. AI Insights (actionable conclusions)

Sidebar:
- Always visible (on desktop)
- Sticky top
- Independent scroll
- Quick access to comparisons and goals

### Highlight: Creative Analysis Section

Why emphasized:
- Most actionable insights
- Direct optimization opportunities
- Multi-perspective analysis (ROAS, CVR, all, low performers)
- Directly impacts budget allocation

How emphasized:
- Blue 2px border
- Light gradient background
- "⭐ CORE ANALYSIS" badge
- Prominent position (after heatmap)
- 4-tab interface for depth
- Color-coded status badges

Tabs provide:
💎 Top ROAS: Which creatives drive revenue
🎯 Top CVR: Which creatives convert best
📋 All Creatives: Complete overview
⚠️ Low Performers: Which to pause/optimize

### Implementation Priority
Phase 1: Layout & Structure (HTML skeleton)
Phase 2: Styling (CSS grid, spacing, colors)
Phase 3: Components (Cards, charts, tables)
Phase 4: Interactivity (Tabs, modals, filters)
Phase 5: Data Integration (API calls)
Phase 6: Responsive (Media queries)
Phase 7: Polish (Animations, accessibility)

