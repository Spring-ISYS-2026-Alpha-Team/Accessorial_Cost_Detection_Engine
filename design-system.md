## MARA.com Design System Analysis

This document summarizes observable patterns from `mara.com` to guide implementing PACE with a similar look-and-feel.

---

### 1. Layout grid structure

- **Page width**
  - Content is centered with a **max-width around 1200–1280px** on large screens.
  - Background color/imagery runs full-bleed; content bands sit as centered columns within.
- **Grid**
  - **Single-column hero**: main headline + lead text + primary CTA and secondary content stacked vertically.
  - **Two-column sections**:
    - Text on one side, visual or callout card on the other.
    - Columns appear to be ~60/40 or 50/50 depending on emphasis.
  - **Three-column feature rows**:
    - For “We Balance / We Own & Operate / We Develop”, cards are arranged in equal-width columns at large breakpoints, stacking vertically on smaller screens.
  - **Card rails / carousels**:
    - Insights/news cards arranged in horizontal rows (likely a CSS grid or flex row) with consistent widths and gaps.
- **Vertical rhythm**
  - Clear vertical banding: hero → “This is MARA” section → “We Balance / Own / Develop” carousel → Operations band → Strategic Growth band → Investors band → Insights band → Footer.
  - Spacing between major sections appears to be **4–6× base spacing unit** (e.g., 48–72px).

---

### 2. Typography hierarchy

*(Exact font files aren’t visible via text scrape, but the hierarchy is consistent and modern-sans-serif-based.)*

- **Global font**
  - Clean sans-serif (likely something in the Inter/IBM Plex/TWK family) with good legibility and modest letter-spacing.
- **Heading hierarchy**
  - **H1 (hero)**: Large (approx 40–56px), high weight, tight leading, often single line:
    - Example: “Advancing the world’s energy systems”
  - **H2 (section titles)**: ~28–32px, bold; used for “We Balance”, “Operations”, “Expanding our global footprint”, “The industries shaping tomorrow…”, etc.
  - **H3 (subtitles / labels)**: ~20–24px, semibold; e.g., “Securing the Future of AI”.
  - **H4 / meta labels**: smaller uppercase labels, often used for content type chips (“Blog”, “Announcement”, “Video”).
- **Body text**
  - **Primary body**: ~16px, regular, comfortable line-height (~1.5–1.7).
  - **Secondary copy**: ~14px for supporting paragraphs and card descriptions.
  - **Micro/meta text**: 12–13px for captions, disclaimers, and footer links.
- **Stylistic details**
  - Headlines and important phrases occasionally use **line breaks deliberately** (e.g., energy phrase broken across two lines) to control rhythm.
  - **Mixed weight emphasis** inside paragraphs (bold for key phrases).

---

### 3. Card component styling

- **General card archetype**
  - **Surface**: Dark or very deep-colored background with subtle gradient, distinct from page background.
  - **Corner radius**: ~12–20px, giving a soft, modern feel.
  - **Border**: Very subtle 1px border with low-contrast color in some cards; others rely solely on shadow and gradient.
  - **Shadow**: Soft box-shadow for elevation (blur ~12–24px, alpha 0.15–0.3).
- **Content anatomy**
  - Optional **eyebrow/label**: “Blog”, “Announcement”, “Video” above title.
  - **Title**: 18–22px, medium/bold, usually 1–2 lines.
  - **Supporting text**: short summary or one-liner; restrained length.
  - **CTA**: text link with arrow or “Read more” placed at bottom.
- **Interaction states**
  - Cards are **clickable** with:
    - Slight scale-up on hover.
    - Increase in shadow or border brightness.
    - Sometimes a subtle gradient shift.
- **Variations**
  - **Feature cards** (e.g., “We Balance / We Own & Operate / We Develop”):
    - Larger imagery or iconography; symmetric card heights.
  - **Insight cards**:
    - Stronger emphasis on text; category label, title, and small preview text.

---

### 4. Navigation behavior

- **Primary nav**
  - Fixed **top horizontal bar** with logo on the left and primary links to:
    - About / Operations / Insights / Investors / More
  - On scroll, nav likely remains sticky with a solid background to preserve contrast over content.
- **Logo**
  - Left aligned, brand wordmark; clicking returns to home.
- **Nav link styling**
  - Horizontal list with medium-weight text, spacing ~24–32px between links.
  - Active/hover states:
    - Color shift to higher-contrast text.
    - Possible subtle underline, border, or background pill.
- **Responsive behavior**
  - On smaller screens, nav items are probably collapsed into a menu/hamburger while logo remains visible.
  - Global CTAs (e.g., Investors, Insights) are always quickly accessible from the nav or footer.
- **Secondary navigation**
  - **Footer nav**: multiple columns (About / Operations / More) with sub-links arranged in vertical lists.
  - **Contextual CTAs** in-page:
    - “Learn about our operations”, “Read more”, “View all insights” — these act like secondary navigation into key sections or content types.

---

### 5. Color usage

*(Exact hex codes are approximated from visual inspection, but relative usage is clear.)*

- **Background**
  - Dark, desaturated blues/purples with rich gradients.
  - Occasional overlay of **subtle noise or particles** in hero backgrounds.
- **Brand colors**
  - **Deep navy/blue** for brand foundation and some text accents.
  - **Electric magenta/fuchsia/pink** used heavily in the hero (energy/compute feel).
  - **Electric teal/cyan** elements in smaller accents and gradients, particularly around energy/technology imagery.
- **Text**
  - Primary text: near-white (off-white) for legibility on dark backgrounds.
  - Secondary text: cool gray with lower contrast.
  - Links/CTAs: higher-saturation accent colors (teal or magenta) depending on context.
- **Semantic hints**
  - While MARA isn’t primarily a risk app, **signal colors** appear:
    - **Green** for growth/positive outcomes.
    - **Attention-grabbing accent** for tags like “Announcement” or “Video”.
- **Gradients**
  - Many sections use **directional gradients** (e.g., top-left magenta to bottom-right navy) to create motion and depth.
  - Some cards sit on top of gradient-illuminated regions, giving a “glow from behind” effect.

---

### 6. Spacing patterns

- **Base spacing unit**
  - Visual spacing suggests an 8px or 4px base grid; typical increments:
    - 8, 12, 16, 24, 32, 48, 64px.
- **Section spacing**
  - Top/bottom padding for major sections ~48–72px on desktop.
  - Footer has generous vertical padding to make dense link lists comfortable.
- **Card/internal padding**
  - Cards have **16–24px internal padding** on all sides.
  - Title to body text spacing ~8–12px.
  - Card-to-card horizontal and vertical gaps ~16–24px.
- **Nav spacing**
  - Horizontal padding in nav bar ~16–24px.
  - Space between individual nav links ~24–32px for easy tapping/clicking.
- **Vertical hierarchy**
  - Headline to subheading: ~12–16px.
  - Subheading to CTA: ~20–28px.
  - Section title to content: ~16–24px.

---

### 7. Key takeaways for PACE implementation

When we bring this into PACE, we should:

- Use a **centered, max-width content column** with full-bleed dark gradients behind it.
- Mirror the **hero → feature bands → insights/news** rhythm using:
  - Multi-column grids for feature explanations.
  - Card rails for historical/risk insights.
- Follow a **clean heading hierarchy**:
  - H1 for page hero titles.
  - H2 for section headings.
  - H3 for card titles and sub-sections.
- Style cards with:
  - Rounded corners (12–20px), subtle shadow, and gradient or dark surfaces.
  - Clear title, short description, and “View details / Read more” CTAs.
- Keep navigation:
  - Fixed top bar with left-aligned PACE logo and concise nav items.
  - Strong footer with grouped informational links and contact details.
- Apply a **dark, moody, gradient-rich color system** with bright accents for risk-level and action states, while maintaining strong contrast and clear spacing.

