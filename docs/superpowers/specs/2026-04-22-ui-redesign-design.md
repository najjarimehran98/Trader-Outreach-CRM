# JobCRM UI Redesign — Design Spec

**Date:** 2026-04-22
**Status:** Approved

## Goal

Full visual redesign of the JobCRM frontend — elevate from functional dark UI to a soft, friendly glass-morphism design with vibrant colors. Same functionality, dramatically improved visual quality.

## Approach

Glass morphism system built on top of existing Tailwind CSS. Single-file architecture preserved. No framework changes.

## Design System

### Color Palette

| Role | Value |
|------|-------|
| Background | `#0a0c1a` (deep navy) |
| Surface glass | `rgba(20, 24, 50, 0.65)` + `backdrop-blur(16px)` |
| Surface-2 | `#1e2240` (warmer blue-gray) |
| Border (glass) | `1px solid rgba(255,255,255,0.1)` |
| Accent primary | `#a78bfa` (vibrant violet) |
| Accent secondary | `#f472b6` (hot pink) |
| Accent gradient | `linear-gradient(135deg, #818cf8, #c084fc, #f472b6)` |
| Text primary | `#eef0ff` (cool white) |
| Text muted | `#6b7094` (muted lavender) |
| Text mono | `#c4b5fd` (soft violet for numbers) |

### Status Colors (vibrant)

| Status | Color | Hex |
|--------|-------|-----|
| New | Bright cyan | `#22d3ee` |
| Reviewing | Bright amber | `#fbbf24` |
| Will Apply | Bright violet | `#818cf8` |
| Applied | Bright emerald | `#34d399` |
| Interviewing | Bright orange | `#fb923c` |
| Offer | Bright green | `#4ade80` |
| Rejected | Bright red | `#f87171` |

### Glass Card Component

```css
.glass {
  background: rgba(20, 24, 50, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255, 0.1);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
```

### Status Badge Style

Semi-transparent tint + matching glow:
```css
.status-badge-new {
  background: rgba(34, 211, 238, 0.15);
  color: #22d3ee;
  box-shadow: 0 0 16px rgba(34, 211, 238, 0.25);
  border: 1px solid rgba(34, 211, 238, 0.2);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

### Typography

- Font: DM Sans (unchanged), JetBrains Mono for numbers
- Headings: weight 700, `letter-spacing: -0.02em`
- Body: weight 400
- Muted: weight 400, color `#6b7094`
- Numbers/scores: JetBrains Mono, weight 600, color `#c4b5fd`

### Interactive Elements

- Buttons: glass background, gradient on primary actions (violet→pink), soft glow on hover
- Inputs: glass background, soft violet glow on focus (`box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.3)`)
- Range sliders: gradient track (violet→pink), larger thumb with glow
- Cards: glass background, hover lifts + border brightens to `rgba(255,255,255,0.15)`

## Page Designs

### Dashboard

- **Stat cards:** Glass cards with icon + large number. Subtle gradient accent line (2px) on left edge matching each stat's color.
- **Status distribution:** Horizontal bars with vibrant status colors, rounded ends (`border-radius: 4px`), animated fill on load.
- **High priority pipeline:** Cards with left-edge gradient accent (violet→pink, 3px), priority score as large glowing number in violet.
- **Recent jobs:** Compact list rows, hover adds glass highlight effect.

### Job List

- **Filter bar:** Pill-shaped toggle buttons with glass background. Active state gets gradient fill (violet→pink) with white text.
- **Job cards:** Glass cards. Company avatar (colored circle with first letter of company). Status badge top-right. Priority score as glowing chip bottom-right.
- **Search bar:** Glass background, wider, soft violet glow ring on focus.
- **Sort dropdown:** Glass background, custom styled.

### Job Detail

- **Header:** Role title large (text-2xl, weight 700) + company underneath. Status badge with glow. Gradient accent line (2px, violet→pink) below header.
- **Two-column layout:** Stays (3/5 + 2/5). Both columns use glass cards with increased padding (24px).
- **Job details section:** Glass card, parsed fields in 2-col grid. Editable fields section with glass input styling.
- **Raw message:** Collapsible glass panel, monospace on slightly lighter glass background.
- **AI section:** Glass card with gradient top border (3px, violet→pink). "Generate" buttons get gradient background.
- **Scoring sliders:** Custom gradient track (violet→pink), larger thumb (20px) with glow shadow.
- **Notes/cover letter:** Glass textarea with glass background.
- **Resume:** Glass upload zone with dashed border that glows on hover.
- **Outcome tracking:** Glass select inputs with custom styling.

### Inbox

- **Textarea:** Larger, glass background, soft violet focus glow.
- **Parse preview:** Glass card with gradient top border (3px, violet→pink).
- **Bot status:** Animated dot with pulse glow effect in emerald (connected) or red (disconnected). Connection text in muted lavender.
- **Recently ingested:** Compact list with glass hover effect.

### Sidebar

- **Logo area:** "JobCRM" in gradient text (violet→pink). Subtitle "Telegram Integration" in muted lavender.
- **Nav links:** Glass highlight (`rgba(255,255,255,0.05)`) on active with violet left edge indicator. Hover adds subtle glow.
- **Stats section:** Small glass chips with colored accent dots for New/Reviewing/Applied counts.

## Toast Notifications

Glass background with colored left border (4px matching type). Slightly wider for readability.

## Modal

Glass overlay + glass card. Softer backdrop blur. Gradient accent line on top of modal card.

## Animations

- Page transitions: `fadeIn` stays (0.2s)
- Card hover: slight lift (`translateY(-2px)`) + border brighten
- Status badge: subtle pulse glow (2s cycle) on New status only
- Stat numbers: count-up animation on dashboard load (optional, nice-to-have)
- Bar chart fills: `transition: width 0.6s ease-out` (stays)

## What Does NOT Change

- All JavaScript logic / API calls
- Backend (Python)
- Data structure / schema
- Functionality or features
- File architecture (single index.html)
