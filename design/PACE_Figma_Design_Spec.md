# PACE — Figma Design Specification
**Predictive Accessorial Cost Engine**
Version 1.0 | Spring 2026

---

## Table of Contents
1. [Design Tokens (Foundations)](#1-design-tokens)
2. [Component Library](#2-component-library)
3. [Page 1 — Login](#3-page-1--login)
4. [Page 2 — Main Dashboard](#4-page-2--main-dashboard)
5. [Page 3 — Upload & Validate](#5-page-3--upload--validate)
6. [Page 4 — Shipment Detail View](#6-page-4--shipment-detail-view)
7. [Figma Setup Notes](#7-figma-setup-notes)

---

## 1. Design Tokens

### 1.1 Color Palette

#### Brand / Primary
| Token Name          | Hex       | Usage                                      |
|---------------------|-----------|--------------------------------------------|
| `navy-900`          | `#0F2B4A` | Top nav background, primary CTA buttons    |
| `navy-700`          | `#1A3F6F` | Hover states on nav, active states         |
| `navy-500`          | `#2563A8` | Links, secondary buttons, chart accents    |
| `navy-100`          | `#DBEAFE` | Button hover bg, info backgrounds          |

#### Neutral / Surface
| Token Name          | Hex       | Usage                                      |
|---------------------|-----------|--------------------------------------------|
| `white`             | `#FFFFFF` | Card surfaces, modal backgrounds           |
| `gray-50`           | `#F9FAFB` | Page background                            |
| `gray-100`          | `#F3F4F6` | Table row alternating, input backgrounds   |
| `gray-200`          | `#E5E7EB` | Borders, dividers, skeleton loaders        |
| `gray-400`          | `#9CA3AF` | Placeholder text, disabled states          |
| `gray-600`          | `#6B7280` | Secondary text, captions, meta labels      |
| `gray-900`          | `#111827` | Primary body text, headings                |

#### Semantic / Risk
| Token Name          | Hex       | Usage                                      |
|---------------------|-----------|--------------------------------------------|
| `risk-low`          | `#059669` | Low-risk badge bg, success states          |
| `risk-low-light`    | `#D1FAE5` | Low-risk badge text background             |
| `risk-medium`       | `#D97706` | Medium-risk badge, warning states          |
| `risk-medium-light` | `#FEF3C7` | Medium-risk badge text background          |
| `risk-high`         | `#DC2626` | High-risk badge, error states              |
| `risk-high-light`   | `#FEE2E2` | High-risk badge text background            |

#### Functional
| Token Name          | Hex       | Usage                                      |
|---------------------|-----------|--------------------------------------------|
| `success`           | `#059669` | Upload success, validation pass            |
| `warning`           | `#D97706` | Validation warnings                        |
| `error`             | `#DC2626` | Validation errors, destructive actions     |
| `info`              | `#2563A8` | Informational messages                     |

---

### 1.2 Typography

**Font Family**: `Inter` (Google Fonts — import as web font or install locally)

| Style           | Size  | Weight     | Line Height | Usage                           |
|-----------------|-------|------------|-------------|---------------------------------|
| `display`       | 32px  | Bold (700) | 40px        | Page hero titles                |
| `h1`            | 24px  | Bold (700) | 32px        | Page titles                     |
| `h2`            | 20px  | SemiBold (600) | 28px    | Section headings                |
| `h3`            | 16px  | SemiBold (600) | 24px    | Card titles, subsection headers |
| `body-lg`       | 15px  | Regular (400)  | 24px    | Important body copy             |
| `body`          | 14px  | Regular (400)  | 22px    | Standard body text              |
| `label`         | 13px  | Medium (500)   | 20px    | Form labels, table headers      |
| `caption`       | 12px  | Regular (400)  | 18px    | Metadata, footnotes, timestamps |
| `badge`         | 11px  | SemiBold (600) | 16px    | Status badges, tags             |

---

### 1.3 Spacing Scale (8px base)

| Token      | Value | Use Case                                      |
|------------|-------|-----------------------------------------------|
| `space-1`  | 4px   | Icon-to-label gap, tight insets               |
| `space-2`  | 8px   | Input padding, compact list items             |
| `space-3`  | 12px  | Card internal padding (tight)                 |
| `space-4`  | 16px  | Standard element gap, badge padding           |
| `space-5`  | 20px  | Card internal padding (standard)              |
| `space-6`  | 24px  | Section padding, column gutter                |
| `space-8`  | 32px  | Card-to-card gap, major section padding       |
| `space-12` | 48px  | Page section gaps                             |
| `space-16` | 64px  | Hero sections, full-page vertical rhythm      |

---

### 1.4 Border Radius

| Token       | Value | Use Case                               |
|-------------|-------|----------------------------------------|
| `radius-sm` | 4px   | Tags, badges, small chips              |
| `radius-md` | 8px   | Cards, inputs, dropdowns               |
| `radius-lg` | 12px  | Large cards, modals                    |
| `radius-xl` | 16px  | Upload zone, feature cards             |
| `radius-full` | 9999px | Avatars, pills, toggle buttons      |

---

### 1.5 Elevation / Shadow

| Level       | CSS Box Shadow Value                           | Use Case                    |
|-------------|------------------------------------------------|-----------------------------|
| `shadow-xs` | `0 1px 2px rgba(0,0,0,0.05)`                  | Subtle card borders         |
| `shadow-sm` | `0 1px 3px rgba(0,0,0,0.10), 0 1px 2px rgba(0,0,0,0.06)` | Default cards  |
| `shadow-md` | `0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)` | Dropdowns, popovers |
| `shadow-lg` | `0 10px 15px rgba(0,0,0,0.10), 0 4px 6px rgba(0,0,0,0.05)` | Modals       |

---

### 1.6 Grid & Layout

- **Canvas width**: 1440px
- **Content max-width**: 1280px
- **Columns**: 12
- **Gutter**: 24px
- **Side margins**: 40px
- **Top nav height**: 64px
- **Left sidebar width** (when present): 240px

---

## 2. Component Library

Create the following components in Figma as **reusable components** with variants.

### 2.1 Button

**Variants**: `primary` | `secondary` | `ghost` | `destructive`
**Sizes**: `sm` | `md` | `lg`
**States**: `default` | `hover` | `active` | `disabled` | `loading`

| Variant       | Background   | Text      | Border       |
|---------------|--------------|-----------|--------------|
| `primary`     | `navy-900`   | `white`   | none         |
| `secondary`   | `white`      | `navy-900`| `gray-200`   |
| `ghost`       | transparent  | `navy-500`| none         |
| `destructive` | `error`      | `white`   | none         |

**Dimensions** (md size):
- Height: 40px
- Horizontal padding: 16px
- Border radius: `radius-md` (8px)
- Font: `label` style, medium weight

**Loading state**: Replace label with spinner icon (16px, white) + "Loading..." text

---

### 2.2 Input Field

**Variants**: `text` | `password` | `search`
**States**: `default` | `focused` | `filled` | `error` | `disabled`

- Height: 40px
- Horizontal padding: 12px
- Border: 1px solid `gray-200`
- Border radius: `radius-md`
- Background: `white`
- Focused border: 2px solid `navy-500`
- Error border: 2px solid `error`
- Font: `body` style
- Placeholder color: `gray-400`

**Anatomy (top to bottom)**:
1. Label (optional) — `label` style, `gray-900`, 4px below label to field
2. Input field
3. Helper text or error message — `caption` style, 4px below field
   - Helper: `gray-600`
   - Error: `error`

---

### 2.3 Risk Badge

**Variants**: `low` | `medium` | `high`

| Variant  | Background        | Text Color   | Icon      |
|----------|-------------------|--------------|-----------|
| `low`    | `risk-low-light`  | `risk-low`   | ● (dot)   |
| `medium` | `risk-medium-light`| `risk-medium`| ▲ (triangle) |
| `high`   | `risk-high-light` | `risk-high`  | ✕ or ⚠    |

- Padding: 4px 8px
- Border radius: `radius-sm` (4px)
- Font: `badge` style (11px SemiBold)
- Gap between icon and text: 4px

---

### 2.4 Metric Card

Used in the dashboard for KPI display.

**Structure**:
```
┌──────────────────────────────────┐
│  [Icon]  Label text              │
│                                  │
│  000,000       ↑ +2.4%           │
│  (primary value)  (trend)        │
└──────────────────────────────────┘
```

- Width: fills column (approx 280px in 4-column layout)
- Padding: 20px
- Background: `white`
- Border: 1px solid `gray-200`
- Border radius: `radius-lg`
- Shadow: `shadow-sm`
- Label: `caption` style, `gray-600`, uppercase, letter-spacing 0.5px
- Value: `h1` style (24px Bold), `gray-900`
- Trend: `label` style (13px), green if positive (`success`), red if negative (`error`)
- Icon: 20px, `gray-400`, top-right corner (optional)

---

### 2.5 Data Table

**Anatomy**:
- Header row: `gray-100` background, `label` style, `gray-600`, 40px row height
- Body rows: `white` background, `body` style, 48px row height, alternating `gray-50`
- Hover: `navy-100` row highlight
- Selected: left border 3px `navy-500`
- Column sorting: arrow icon after header text
- Pagination row: bottom, `caption` style

**Columns to define (for shipments table)**:
| Column             | Width  | Alignment | Notes                    |
|--------------------|--------|-----------|--------------------------|
| Shipment ID        | 120px  | Left      | Monospace font           |
| Ship Date          | 110px  | Left      | MM/DD/YYYY               |
| Carrier            | 140px  | Left      | Text                     |
| Facility           | 160px  | Left      | Text                     |
| Risk Score         | 100px  | Center    | Progress bar + % value   |
| Risk Tier          | 100px  | Center    | Risk Badge component     |
| Base Freight       | 120px  | Right     | $0.00 format             |
| Accessorial Est.   | 120px  | Right     | $0.00 format             |

---

### 2.6 Risk Score Bar

An inline progress bar used in tables and detail views.

- Width: 80px (in table), 200px (in detail card)
- Height: 6px
- Background: `gray-200`
- Fill:
  - 0–33%: `risk-low` (green)
  - 34–66%: `risk-medium` (amber)
  - 67–100%: `risk-high` (red)
- Border radius: `radius-full`

---

### 2.7 Alert / Banner

**Variants**: `success` | `warning` | `error` | `info`

```
[icon]  [Title — bold]  [Body text]          [× close]
```

- Height: auto (min 48px)
- Padding: 12px 16px
- Border-left: 4px solid (semantic color)
- Border radius: `radius-md`
- Background: light variant of semantic color
- Icon: 20px, matches border color

---

### 2.8 Top Navigation Bar

- Height: 64px
- Background: `navy-900`
- Full width
- Left: PACE logo (white wordmark, 24px) + "PACE" text
- Center: Navigation links — Dashboard | Uploads | Shipments | Settings
  - Font: `label` style, `white` (opacity 0.75 inactive, full white active)
  - Active indicator: 3px border-bottom, `white`
  - Gap between links: 32px
- Right: User display + Logout button
  - User avatar: 32px circle, `navy-500` bg, white initials
  - Username: `label` style, `white` (opacity 0.9)
  - Logout: `ghost` button variant, small, white text
  - Gap between avatar and button: 12px

---

### 2.9 Upload Zone

- Width: 100% of container
- Height: 200px
- Border: 2px dashed `gray-300`
- Border radius: `radius-xl`
- Background: `gray-50`
- Hover: border `navy-500`, background `navy-100`
- Center content (vertically and horizontally):
  - Upload icon: 40px, `gray-400`
  - Primary text: `h3` style — "Drag & drop your CSV file here"
  - Secondary text: `body` style, `gray-600` — "or click to browse files"
  - File type hint: `caption` style, `gray-400` — "Accepts: .csv — Max size: 10MB"
- Active/dragging state: border `navy-500`, background `navy-100`, icon changes to `navy-500`

---

## 3. Page 1 — Login

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                        Page bg: gray-50                          │
│                                                                  │
│              ┌──────────────────────────────┐                   │
│              │  ┌────────────────────────┐  │                   │
│              │  │  PACE logo (navy-900)  │  │                   │
│              │  └────────────────────────┘  │                   │
│              │  Predictive Accessorial       │                   │
│              │  Cost Engine                  │                   │
│              │                              │                   │
│              │  ┌────────────────────────┐  │                   │
│              │  │  Username              │  │                   │
│              │  └────────────────────────┘  │                   │
│              │  ┌────────────────────────┐  │                   │
│              │  │  Password              │  │                   │
│              │  └────────────────────────┘  │                   │
│              │                              │                   │
│              │  [        Sign In         ]   │                   │
│              │                              │                   │
│              │  Forgot password?            │                   │
│              └──────────────────────────────┘                   │
│                                                                  │
│              © 2026 PACE — University of Arkansas               │
└──────────────────────────────────────────────────────────────────┘
```

### Specifications

**Page**
- Background: `gray-50`
- Vertical alignment: center (use auto layout, vertical centering)

**Login Card**
- Width: 440px
- Padding: 40px
- Background: `white`
- Border: 1px solid `gray-200`
- Border radius: `radius-lg` (12px)
- Shadow: `shadow-md`

**Header block (inside card)**
- PACE wordmark: `display` style (32px Bold), `navy-900`
- Subtitle: `body` style, `gray-600` — "Predictive Accessorial Cost Engine"
- Bottom margin: `space-8` (32px)

**Form fields**
- Label: `label` style
- Field: Input component (text / password variants)
- Gap between username and password fields: `space-4` (16px)

**Sign In button**
- `primary` variant, `lg` size, full width (100% of card)
- Top margin: `space-6` (24px)

**Forgot password link**
- `body` style, `navy-500`
- Centered, top margin: `space-4` (16px)

**Footer**
- Outside card, centered, `caption` style, `gray-400`
- Text: "© 2026 PACE — University of Arkansas"

---

## 4. Page 2 — Main Dashboard

### Layout Overview

```
┌────────────────────────────────────────────────────────────────┐
│  [PACE logo]  Dashboard  Uploads  Shipments  Settings   [user] │  ← nav (64px)
├────────────────────────────────────────────────────────────────┤
│ Page bg: gray-50                                               │
│  Padding: 32px                                                 │
│                                                                │
│  Risk Dashboard                    [Date Range ▼] [Export ↓]  │  ← Page header
│  ─────────────────────────────────────────────────────────    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  ← KPI Cards (4-col)
│  │Total     │ │Avg Risk  │ │High Risk │ │Est. Cost │         │
│  │Shipments │ │Score     │ │Shipments │ │Impact    │         │
│  │  1,284   │ │  67%     │ │  312     │ │$42,600   │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                                                                │
│  ┌──────────────────────┐  ┌──────────────────────┐           │  ← Charts (2-col)
│  │  Risk Distribution   │  │  Risk by Carrier     │           │
│  │  (Bar chart)         │  │  (Horizontal bar)    │           │
│  └──────────────────────┘  └──────────────────────┘           │
│                                                                │
│  ┌────────────────────────────────────────────────┐           │  ← Shipments Table
│  │  Recent Shipments           [Search...] [Filter]│           │
│  │  ───────────────────────────────────────────── │           │
│  │  ID    Date   Carrier  Facility  Score  Tier   │           │
│  │  ...   ...    ...      ...       ...    ...    │           │
│  └────────────────────────────────────────────────┘           │
└────────────────────────────────────────────────────────────────┘
```

### Section Specifications

#### Page Header Row
- Left: Page title — `h1` style (24px Bold), `gray-900`, text "Risk Dashboard"
- Left below title: `body` style, `gray-600` — "Showing risk predictions for all active shipments"
- Right: Two inline elements:
  - Date range selector (custom input with calendar icon, width 240px)
  - Export button (`secondary` variant, with download icon)
- Bottom border: 1px solid `gray-200`, `space-6` margin below

#### KPI Cards Row
- 4 columns, equal width, gap: `space-6` (24px)
- Each card uses the **Metric Card** component

| Card               | Value Example | Trend      | Icon         |
|--------------------|---------------|------------|--------------|
| Total Shipments    | 1,284         | ↑ +14 this week | package icon |
| Avg Risk Score     | 67%           | ↑ +3% vs last week | gauge icon |
| High-Risk Count    | 312           | ↓ -8 this week | warning icon |
| Est. Cost Impact   | $42,600       | ↑ +$1,200 vs last week | dollar icon |

- Trend color: green if improvement (risk going down), red if worsening

#### Charts Row
- 2 columns, gap: `space-6`
- Both are cards: `white` bg, `shadow-sm`, `radius-lg`, padding `space-5`

**Chart 1 — Risk Score Distribution**
- Title: "Risk Score Distribution" (`h3` style)
- Sub-label: "Count of shipments by risk score bracket" (`caption` style, `gray-600`)
- Chart type: Vertical bar chart
- X-axis: Risk brackets (0–10%, 10–20%, ... 90–100%)
- Y-axis: Shipment count
- Bar colors: Use gradient or segment fill:
  - Bars 0–33%: `risk-low`
  - Bars 34–66%: `risk-medium`
  - Bars 67–100%: `risk-high`
- Chart height: 240px

**Chart 2 — Risk by Carrier**
- Title: "Average Risk Score by Carrier" (`h3` style)
- Sub-label: "Top 8 carriers ranked by avg risk score" (`caption` style, `gray-600`)
- Chart type: Horizontal bar chart
- Bars ranked highest to lowest
- Bar fill: `navy-500` (or gradient `navy-700` → `navy-500`)
- Show value label at end of each bar
- Chart height: 240px

#### Shipment Table Section
- Full-width card: `white` bg, `shadow-sm`, `radius-lg`, padding `space-5`
- Table header row:
  - Left: "Recent Shipments" (`h3` style)
  - Right: Search input (220px, search icon) + Filter button (`secondary` variant, with filter icon)
- Divider below header, then Data Table component
- Pagination: bottom of card — "Showing 1–25 of 1,284" + prev/next buttons

---

## 5. Page 3 — Upload & Validate

### Layout Overview

```
┌────────────────────────────────────────────────────────────────┐
│  [PACE logo]  Dashboard  Uploads  Shipments  Settings   [user] │  ← nav
├────────────────────────────────────────────────────────────────┤
│  Upload Shipment Data                                          │  ← Page header
│  Upload a CSV file to validate and generate risk scores        │
│  ─────────────────────────────────────────────────────────    │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │          ↑                                             │   │  ← Upload Zone
│  │   Drag & drop your CSV file here                       │   │
│  │   or click to browse files                             │   │
│  │   Accepts: .csv — Max size: 10MB                       │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ── OR ──                                                      │  ← Divider
│                                                                │
│  [Use sample data]  (ghost button)                             │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Validation Results                                    │   │  ← Results card
│  │  ● 1,284 rows passed   ▲ 12 warnings   ✕ 3 errors     │   │
│  │  ─────────────────────────────────────────────────    │   │
│  │  ERRORS:                                               │   │
│  │  Row 42: missing value in 'carrier' column             │   │
│  │  Row 107: 'weight_lbs' value -200 is out of range     │   │
│  │                                                        │   │
│  │  WARNINGS:                                             │   │
│  │  Rows 12, 34, 89...: 'risk_tier' defaulted to 'Low'   │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Data Preview (first 25 rows)           [  Score →  ]  │   │  ← Preview + CTA
│  │  ID    Date   Carrier  ...  Risk Score  Risk Tier      │   │
│  │  ...   ...    ...      ...  ...         ...            │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### Section Specifications

#### Page Header
- Title: "Upload Shipment Data" — `h1` style
- Subtitle: "Upload a CSV file to validate and generate risk predictions" — `body` style, `gray-600`

#### Upload Zone (see component 2.9)
- Default state as described in component spec
- **Uploading state**:
  - Replace content with progress bar (linear, `navy-500` fill, `gray-200` background, height 8px)
  - Filename shown above: `label` style, `gray-900`
  - "Uploading... 64%" text below bar: `caption` style, `gray-600`
  - Cancel button (ghost, small, `error` color)
- **Success state**:
  - Green border (2px solid `risk-low`)
  - Background: `risk-low-light`
  - Checkmark icon (24px, `risk-low`)
  - Filename + filesize: "shipments_q1.csv — 2.4 MB"
  - "Change file" link

#### Divider & Sample Data
- Horizontal rule with "OR" label centered
- "Use sample data" ghost button — loads mock CSV for demo/testing

#### Validation Results Card
- Only shown after upload is complete
- Card: `white` bg, `shadow-sm`, `radius-lg`, padding `space-5`
- Summary row (3 inline badges):
  - Pass count: `success` color with checkmark icon
  - Warning count: `warning` color with triangle icon
  - Error count: `error` color with X icon
- Divider
- **Error section** (if errors > 0):
  - Section label: `label` style, `error` — "ERRORS"
  - Each error: `body` style, one per row, alternating `gray-50` background
  - Row number highlighted in `error` color
- **Warning section** (if warnings > 0):
  - Section label: `label` style, `warning` — "WARNINGS"
  - Same row format, row numbers in `warning` color
- If 0 errors + 0 warnings:
  - Show success Alert Banner: "All rows passed validation — ready to score"

#### Data Preview Card
- Only shown after successful validation
- Card: same styling
- Header row: "Data Preview — First 25 rows" + primary button "Generate Risk Scores →"
- Data Table component (read-only, no row selection)
- Risk Score and Risk Tier columns show placeholder skeleton/dash until scoring is run
- After scoring: Risk Score Bar + Risk Badge populate in table

---

## 6. Page 4 — Shipment Detail View

### Layout Overview

```
┌────────────────────────────────────────────────────────────────┐
│  [PACE logo]  Dashboard  Uploads  Shipments  Settings   [user] │  ← nav
├────────────────────────────────────────────────────────────────┤
│  ← Dashboard  /  Shipments  /  SHP-00842                       │  ← breadcrumb
│  ─────────────────────────────────────────────────────────    │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  SHP-00842                                  [HIGH RISK]  │ │  ← Header Card
│  │  Origin: Dallas, TX → Destination: Memphis, TN           │ │
│  │  Carrier: XPO Logistics   Facility: Warehouse D          │ │
│  │  Ship Date: 03/14/2026    Base Freight: $1,240.00        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌───────────────────────┐  ┌──────────────────────────────┐  │
│  │  Risk Score           │  │  Risk Factor Breakdown       │  │
│  │                       │  │                              │  │
│  │      82%              │  │  Carrier History   ████ 34%  │  │
│  │  ████████████░░ High  │  │  Facility Type     ███░ 28%  │  │
│  │                       │  │  Appointment Time  ██░░ 19%  │  │
│  │  $640 est. accessorial│  │  Miles             █░░░ 12%  │  │
│  │  cost exposure        │  │  Weight            █░░░  7%  │  │
│  └───────────────────────┘  └──────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Recommended Actions                                     │ │  ← Actions Card
│  │  ① Consider alternative carrier with lower detention risk│ │
│  │  ② Request early appointment window (before 10 AM)       │ │
│  │  ③ Add $400–$650 accessorial buffer to quote             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Similar Shipments — Historical Comparison               │ │  ← History Table
│  │  Last 10 shipments with similar profile                  │ │
│  │  ID    Date   Carrier  Score  Actual Accessorial         │ │
│  │  ...   ...    ...      ...    ...                        │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

### Section Specifications

#### Breadcrumb
- `caption` style (12px), `gray-600`
- Active page (SHP-00842): `gray-900`, not a link
- Back arrow (←) before first item: `navy-500`, clickable
- Gap between items: `space-2` (8px), "/" separator color `gray-400`

#### Shipment Header Card
- Full-width card: `white` bg, `shadow-sm`, `radius-lg`, padding `space-6`
- Top-right: Risk Badge (high/medium/low variant, large size)
- Shipment ID: `h1` style, `navy-900`
- Route line: `body-lg` style, `gray-700`
- Metadata grid (2 columns × 2 rows):
  - Label: `caption` style, `gray-400`, uppercase
  - Value: `label` style, `gray-900`

#### Risk Score Card (left of 2-column row)
- Width: ~40% (5/12 columns)
- Card: `white`, `shadow-sm`, `radius-lg`, padding `space-6`
- Title: "Risk Score" — `h3` style
- Large number: `display` style (32px Bold)
  - Color: `risk-low` / `risk-medium` / `risk-high` depending on score
- Progress bar (Risk Score Bar component, large: 200px wide × 10px tall)
- Risk tier label: right of bar, Risk Badge component
- Cost estimate line: `body` style, `gray-600` — "Estimated $640 accessorial exposure"
  - "$640" in `risk-high` color (bold)

#### Risk Factor Breakdown Card (right of 2-column row)
- Width: ~60% (7/12 columns)
- Card: same styling
- Title: "Risk Factor Breakdown" — `h3` style
- Subtitle: `caption` style, `gray-600` — "Top factors contributing to this prediction"
- Table of factors (no outer borders, internal dividers only):
  - Column 1: Factor name — `label` style, 180px
  - Column 2: Horizontal mini bar (total width 160px, fill = percentage) — `navy-500` fill
  - Column 3: Percentage — `label` style, right-aligned, `gray-900`
  - Row height: 36px, alternating `gray-50`

#### Recommended Actions Card
- Full-width card
- Title: "Recommended Actions" — `h3` style
- Background: `navy-100` (light blue tint)
- Border-left: 4px solid `navy-500`
- List of numbered recommendations
  - Number badge: 20px circle, `navy-500` bg, white text, `badge` font
  - Action text: `body` style, `gray-900`
  - Gap between items: `space-4` (16px)

#### Historical Comparison Table
- Full-width card
- Title: "Similar Shipments — Historical" — `h3` style
- Subtitle: "Last 10 shipments with a similar carrier/facility profile" — `caption`, `gray-600`
- Data Table component
- Additional column: "Actual Accessorial" — shows real charge (if any) or "—"
- Row with matching current shipment highlighted in `navy-100`

---

## 7. Figma Setup Notes

### Recommended Figma File Structure

```
PACE Design System
├── 🎨 Foundations
│   ├── Color Styles (all tokens from Section 1.1)
│   ├── Text Styles (all from Section 1.2)
│   └── Effect Styles (shadows from Section 1.5)
│
├── 🧩 Components
│   ├── Buttons (with variants)
│   ├── Input Fields (with variants)
│   ├── Risk Badge (with variants)
│   ├── Metric Card
│   ├── Data Table
│   ├── Risk Score Bar
│   ├── Alert / Banner
│   ├── Top Navigation
│   └── Upload Zone
│
└── 📄 Pages
    ├── Login
    ├── Dashboard
    ├── Upload & Validate
    └── Shipment Detail
```

### Figma Page Setup

1. Set each page frame to **1440 × 1024** (desktop, auto-height)
2. Enable **layout grid**: 12 columns, 24px gutter, 40px margin
3. Use **Auto Layout** on all cards, rows, and lists — this makes the design responsive-friendly
4. Define all colors as **local styles** before starting components
5. Use **component variants** for all interactive states (hover, active, error) — do not duplicate frames manually

### Prototyping Flows to Connect

| Trigger                   | Action                              | Transition     |
|---------------------------|-------------------------------------|----------------|
| Login → Sign In button    | Navigate to Dashboard               | Dissolve 300ms |
| Dashboard → Upload tab    | Navigate to Upload page             | Instant        |
| Dashboard → Row click     | Navigate to Shipment Detail         | Slide left     |
| Shipment Detail → back    | Navigate to Dashboard               | Slide right    |
| Upload Zone → file drop   | Show uploading state (overlay)      | Dissolve       |
| Uploading → complete      | Show validation results             | Smart Animate  |

### Icon Library
Use **Heroicons** (Tailwind) or **Lucide Icons** — both are available as free Figma plugins. Recommended icons:

| Usage              | Icon Name (Heroicons)     |
|--------------------|---------------------------|
| Upload             | `arrow-up-tray`           |
| Dashboard          | `squares-2x2`             |
| Shipments          | `truck`                   |
| Risk/Warning       | `exclamation-triangle`    |
| Settings           | `cog-6-tooth`             |
| Logout             | `arrow-right-on-rectangle`|
| Success/Check      | `check-circle`            |
| Error/X            | `x-circle`                |
| Filter             | `funnel`                  |
| Export             | `arrow-down-tray`         |
| Search             | `magnifying-glass`        |
| Calendar           | `calendar-days`           |
| User               | `user-circle`             |

---

*End of PACE Figma Design Specification v1.0*
