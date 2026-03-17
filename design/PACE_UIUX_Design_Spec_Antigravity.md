# PACE (Predictive Accessorial Cost Engine) — UI/UX Design Specification
**Target implementer**: Google Antigravity  
**Target framework**: Streamlit (Python)  
**Scope**: Public (pre-auth) + Authenticated (post-auth) web UI for freight logistics risk prediction  
**Primary users**: Logistics Analysts, Viewers, Admins  
**Core value**: Predict unexpected accessorial charges (detention, lumper, layover, etc.) before execution

---

## Table of contents
- **1. Information architecture & routing**
- **2. Design foundations (tokens)**
- **3. App shell (navigation, layout, responsive)**
- **4. Component library (system + patterns)**
- **5. Page specifications**
- **6. States, validation, and empty/loading/error**
- **7. Accessibility & content guidelines**
- **8. Streamlit implementation mapping**
- **9. Analytics & instrumentation (optional)**

---

## 1. Information architecture & routing

### 1.1 Public (pre-auth)
- **`/` Home (Landing)**
- **`/login` Login**
- **`/register` Create Account**

### 1.2 Authenticated (post-login)
Primary navigation items for **Analyst / Viewer**:
- **Dashboard Home** (User Home / landing after login)
- **Dashboards**
- **Risk Estimator**
- **Routes**
- **Carriers**
- **Accessorial**
- **Sign Out** (top-right action; always visible)

Additional for **Admin**:
- **Admin Panel** (separate section in nav)

### 1.3 Access control matrix (RBAC)
- **Viewer**
  - Can view: User Home, Dashboards, Routes, Carriers, Accessorial
  - Risk Estimator: view + run calculations **allowed** (default) or **read-only** (if business rules require; choose one and keep consistent)
  - Cannot: Admin Panel, user creation, role changes
- **Analyst**
  - Everything Viewer can do
  - Can: save risk calculations (optional), export filtered tables (optional)
  - Cannot: Admin Panel
- **Admin**
  - Everything Analyst can do
  - Can: create/edit/deactivate users, reset passwords, view audit log

---

## 2. Design foundations (tokens)

### 2.1 Color palette (source of truth)
**Brand**
- **Primary (Deep blue)**: `#1B435E` (headers, primary buttons, key accents)
- **Secondary (Purple)**: `#563457` (secondary accents, highlights, charts)
- **Accent (Teal)**: `#2DD4BF` (success/highlights, interactive focus)

**Surface**
- **Background (Dark navy)**: `#161638`
- **Surface 1 (Card)**: `rgba(255,255,255,0.06)` (dark glass)
- **Surface 2 (Elevated)**: `rgba(255,255,255,0.09)`
- **Border**: `rgba(241,245,249,0.12)`

**Text**
- **Primary text**: `#F1F5F9`
- **Secondary text**: `#94A3B8`
- **Disabled text**: `rgba(148,163,184,0.55)`

**Semantic / Risk**
- **Low**: `#10B981`
- **Medium**: `#F59E0B`
- **High**: `#EF4444`

**Focus ring**
- **Focus**: `rgba(45,212,191,0.45)` (2–3px outer ring)

### 2.2 Typography
- **Font**: Inter (preferred) or system fallback (SF Pro/Segoe UI)
- **H1**: 34px / 42px, 700
- **H2**: 28px / 36px, 700
- **H3**: 22px / 30px, 600
- **Body**: 14–16px / 22–26px, 400–500
- **Caption/Meta**: 12–13px / 18–20px, 400–500
- **Numbers (KPI emphasis)**: same family, weight 700, tracking -0.02em

### 2.3 Spacing & layout grid
- **Base unit**: 8px
- **Page max width**: 1200–1400px (desktop)
- **Gutters**: 24px (desktop), 16px (tablet), 12px (mobile)
- **Card padding**: 16–24px
- **Radius**: 8–16px (use 12px default)
- **Shadow**: subtle (dark UI): `0 8px 30px rgba(0,0,0,0.35)`

### 2.4 Iconography
- Use one set consistently (Lucide or Heroicons).  
- Icon stroke color defaults to `#94A3B8` and brightens on hover.

---

## 3. App shell (navigation, layout, responsive)

### 3.1 Public navigation (Landing)
Top nav layout:
- **Left**: PACE logo (wordmark + small icon)
- **Center**: Dropdown menu label “Menu” (or “Explore”) with items: **About**, **Features**, **Get Started**
- **Right**: **Login** button (Primary)

Dropdown behavior:
- On desktop: click opens popover under menu; closes on click outside/ESC.
- On mobile: nav collapses to hamburger; “Login” remains a prominent CTA.

### 3.2 Authenticated navigation
Choose **Top bar + optional collapsible left rail**. In Streamlit, implement as a **top bar** (consistent with your existing `top_nav`) and use page grouping for Admin.

Top bar anatomy:
- **Left**: PACE logo (click → Dashboard Home)
- **Center/Left**: Primary links: Dashboards, Risk Estimator, Routes, Carriers, Accessorial
- **Right**: user chip (name + role) + **Sign Out** button (Primary/outline depending on density)
- **Admin**: show “Admin Panel” grouped under a subtle separator (or right-aligned “Admin” link)

Current location indication:
- Active link uses **Accent teal underline** (2px) and brighter text.

### 3.3 Page layout primitives
- **Canvas**: full width background `#161638`
- **Content width**: max 1400px, centered
- **Sections**: stacked vertical rhythm (24–40px)

### 3.4 Responsive breakpoints
- **Desktop**: ≥ 1200px (default layouts in this spec)
- **Tablet**: 768–1199px (collapse 3–4 column grids to 2 columns; tables add horizontal scroll)
- **Mobile**: < 768px (single column; nav collapses; charts stack; table becomes cards or scroll)

### 3.5 Motion/animation guidelines
- **Principle**: subtle, lightweight, never block interaction.
- **Loading**: skeletons for cards/charts (shimmer at 1.2–1.6s)
- **Hover**: 150–200ms transitions; elevation and border brighten
- **Page transitions**: optional fade-in 120–180ms (Streamlit page switch is instant; animate sections)
- **Welcome animation**: Lottie/CSS (truck across route line OR pulsating heat map)

---

## 4. Component library (system + patterns)

### 4.1 Buttons
Variants:
- **Primary**: fill `#1B435E`, text `#F1F5F9`, hover brighten + slight lift
- **Secondary**: outline border `rgba(241,245,249,0.25)`, text `#F1F5F9`, hover fill `rgba(241,245,249,0.06)`
- **Tertiary/Ghost**: no border, text `#94A3B8`, hover text `#F1F5F9`
- **Danger**: fill `#EF4444`

Sizes:
- **sm** 32px height, **md** 40px, **lg** 48px

States:
- default / hover / active / disabled / loading (spinner left of label)

### 4.2 Inputs (text, password, number, select)
Visual:
- Background: `rgba(255,255,255,0.06)`
- Border: `rgba(241,245,249,0.12)`; on focus border `#2DD4BF` + focus ring
- Label: `#94A3B8`, 12–13px
- Helper/error: 12px; error `#EF4444`

Validation:
- Inline message below field; don’t rely on color alone.

### 4.3 Cards
Default card:
- Background: `rgba(255,255,255,0.06)`
- Border: `rgba(241,245,249,0.12)`
- Radius: 12px
- Shadow: `0 8px 30px rgba(0,0,0,0.35)`

### 4.4 KPI stat card
Anatomy:
- Label (caps, 12px)
- Value (28–34px, bold)
- Delta (optional) with arrow + semantic color
- Optional icon watermark (5–8% opacity)

### 4.5 Badges / Chips
- **Risk badge**: Low/Medium/High with background tint and text color:
  - Low: bg `rgba(16,185,129,0.14)`, fg `#10B981`
  - Medium: bg `rgba(245,158,11,0.14)`, fg `#F59E0B`
  - High: bg `rgba(239,68,68,0.14)`, fg `#EF4444`
- **Status chip** (Paid/Disputed/etc.): neutral gray tint

### 4.6 Tables
Desktop behavior:
- Sticky header, sortable columns, row hover highlight
- Pagination bottom-right; rows-per-page selector

Styling:
- Header bg `rgba(255,255,255,0.05)`
- Row bg alternates between `rgba(255,255,255,0.03)` and `transparent`
- Divider lines `rgba(241,245,249,0.08)`

Mobile:
- Horizontal scroll OR switch to stacked “row cards” (preferred for shipments list)

### 4.7 Charts (placeholders + final styling)
Use consistent theme:
- Axis/labels: `#94A3B8`
- Gridlines: `rgba(241,245,249,0.08)`
- Series colors: deep blue, purple, teal, then semantic risk colors
- Tooltips: dark surface with border; readable numbers

### 4.8 Modals & dialogs
- Backdrop: `rgba(0,0,0,0.55)`
- Modal: elevated surface, 12–16px radius
- Primary action right, secondary left

### 4.9 Notifications (toast/banner)
- Info / success / warning / error variants; dismissible.

---

## 5. Page specifications

## 5.1 Public — Home (Landing)

### Layout
1) **Top navigation** (see 3.1)  
2) **Hero**
- Headline (H1): “Predict accessorial costs before they hit your margin.”
- Subtext: 1–2 sentences about predicting detention/lumper/layover risk.
- Primary CTA: “Get Started Today”
- Secondary CTA: “View Features” (outline)
- Visual: abstract map route + dots OR minimal freight illustration (no heavy imagery)
3) **About**
- Problem statement: accessorials appear after completion → margin erosion
- Solution: predictive analytics + proactive actions
4) **Features** (3-column grid on desktop; stack on mobile)
- Risk Prediction (ML scoring)
- Cost Estimation (expected $ impact)
- Carrier Analytics (insights by carrier)
5) **Get Started Today**
- Steps: Create account → connect data → run estimator/dashboards
- CTA: “Create Account”
6) **Footer**
- Links: Privacy, Terms, Support

### Interactions
- Dropdown jumps to sections (anchor scrolling).
- CTA routes to register; Login to `/login`.

---

## 5.2 Public — Login
Centered card with:
- Username/email
- Password
- Primary: Sign In
- Links: Create Account, Forgot Password
- Link back to Home (logo click)

Error states:
- Invalid credentials: inline banner + field highlight.

---

## 5.3 Public — Create Account
Form fields:
- Full name
- Email
- Username
- Password (+ strength indicator: weak/fair/strong)
- Confirm password
- Role selection: Analyst / Viewer (Admin not selectable)
- Checkboxes: Terms + Privacy (required)
- Primary: Create Account
- Link: Back to Login

Validation:
- Password rules displayed (min length, mix of characters as required by policy).

---

## 5.4 Auth — User Home (Dashboard Landing)

### Header
- “Welcome back, [User Name]!”
- Subtext: “Here’s what’s happening in your network today.”

### Freight animation (lightweight)
Pick one:
- **Truck-on-route**: small truck icon moving along dotted polyline (CSS)
- **Heat map pulse**: 6–12 dots pulsing in place (CSS)
- **Lottie**: only if file size is small and cached

### Quick stats (4 cards)
- Total shipments this month
- High-risk shipments pending
- Average risk score
- Estimated accessorial exposure

### Secondary actions
- “New Risk Estimate” button
- “View Dashboards” link

---

## 5.5 Auth — Dashboards page

### KPI summary (top row)
- Total Shipments
- Avg Risk Score (%)
- High-Risk Shipments (count)
- Estimated Accessorial Costs ($)

### Main visualizations (2-column layout)
Left:
- Risk Distribution (bar chart: 0–20, 21–40, 41–60, 61–80, 81–100)
- Avg Risk by Carrier (horizontal bar)
Right:
- Risk Tier Breakdown (stacked: counts + expected cost by tier)
- Shipments Volume Over Time with Risk Overlay (combo)

### Bottom section
Searchable shipments table columns:
- Shipment ID
- Origin/Destination
- Carrier
- Risk Score
- Status
- Actions (View Details)

Filters:
- Date range
- Carrier dropdown
- Risk tier selector
- Facility type filter

Interactions:
- Clicking row or “View Details” opens shipment detail drawer/modal or routes to Shipment view.
- Table supports sort by risk score, cost exposure.

---

## 5.6 Auth — Risk Estimator

### Form (left) + results (right) on desktop; stack on mobile
Inputs:
- Carrier dropdown (DB)
- Facility dropdown (with type)
- Appointment type: Live Load, Drop, Preloaded
- Weight (lbs), Miles
- Primary: Calculate Risk

Results (after calculation):
- Large Risk Score card with color coding:
  - Green < 40%
  - Yellow 40–70%
  - Red > 70%
- Risk category badge (Low/Medium/High)
- Expected cost estimate ($)
- Recommendation (actionable sentence)

Optional history:
- Recent calculations table
- Save calculation to shipments (Analyst/Admin)

---

## 5.7 Auth — Routes
Summary cards:
- Active Lanes
- Busiest Lane
- Most Expensive Lane
- Cheapest Lane

Main:
- Lane Search
- Lanes table (Origin, Destination, Volume, Avg Risk, Avg CPM, Accessorial Rate)
- Optional map heat layer

Filters:
- Carrier
- Date range
- Risk threshold

---

## 5.8 Auth — Carriers
Summary:
- Avg cost per mile (overall)
- High-risk shipment rate
- Accessorial cost rate

Visualizations:
- Carrier comparison chart
- Risk trend line

Table:
- Carrier Name, DOT, Volume, Avg Risk, CPM, Accessorial Rate, Safety Rating, Actions

Detail view:
- Profile + trends + recent shipments + facility performance

---

## 5.9 Auth — Accessorial
Top metrics:
- Total accessorial costs
- Affected shipments
- Accessorial rate
- Avg price per affected shipment
- Percent of total spend

Charts:
- Cost by type (toggle count vs $)
- Trend over time
- Cost by facility type
- Cost by carrier

Table:
- Shipment ref, type, amount, date, status (paid/disputed)

---

## 5.10 Auth — Admin Panel (Admin only)
User management:
- Create User (name, email, username, role, temp password)
- Users table (name/email/username/role/status/last login/actions)
- Modals: delete confirm, reset password confirm
- Role assignment dropdown (guardrails: confirm before demoting last admin)

Audit log (optional):
- Login history + key actions

---

## 6. States, validation, and empty/loading/error
- **Loading**: show skeleton cards + “Loading shipments…” text (avoid spinners alone)
- **Empty state**: show illustration + “No shipments match filters” + “Clear filters” action
- **Error**: show banner with retry; for DB errors, provide “demo mode” note (if enabled)
- **Caching**: show small “Cached” indicator in footer of heavy charts (optional)

---

## 7. Accessibility & content guidelines
- **Contrast**: meet WCAG AA for text on dark background
- **Keyboard**: dropdowns, modals, and navigation operable by keyboard
- **Focus**: visible focus ring `rgba(45,212,191,0.45)`
- **Copy tone**: concise, operational; avoid jargon without definitions
- **Number formatting**: commas; currency `$1,234`; risk as `%` with 0–1 or 0–100 consistent

---

## 8. Streamlit implementation mapping (repo-aligned)

### 8.1 Authentication integration
- Preserve `auth_utils.py` session semantics:
  - `st.session_state["authenticated"]` boolean
  - `logout()` clears session and `st.cache_data`

### 8.2 Session state keys (recommended)
- `username`, `role`, `user_id`
- Filters: `date_range`, `carrier_ids`, `risk_tiers`, `facility_types`

### 8.3 DB schema alignment (Azure SQL)
Tables referenced:
- `Shipments (shipment_id, ship_date, origin_region, dest_region, carrier_id, facility_type, appointment_type, distance_miles, revenue, linehaul_cost, accessorial_flag, accessorial_cost)`
- `Carriers (carrier_id, carrier_name, dot_number, safety_rating, fleet_size)`
- `Facilities (facility_id, facility_name, city, state, facility_type, avg_dwell_time_hrs, appointment_required)`
- `Accessorial_Charges (charge_id, shipment_id, charge_type, amount, risk_flag)`

### 8.4 Caching
- Cache DB reads with `st.cache_data(ttl=300)` keyed by filters.
- Cache model load with `st.cache_resource` (keep warm across sessions).

### 8.5 Navigation
- Use Streamlit multipage (`pages/`) + role-gated link rendering.
- “Sign Out” always available; redirect to login.

---

## 9. Analytics & instrumentation (optional)
- Track events: login success/failure, estimator run, filter changes, exports, admin actions.
- Keep PII out of analytics payloads by default.

