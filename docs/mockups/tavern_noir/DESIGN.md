---
name: Tavern Noir
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1b1b1b'
  surface-container: '#1f1f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353535'
  on-surface: '#e2e2e2'
  on-surface-variant: '#c4c7c8'
  inverse-surface: '#e2e2e2'
  inverse-on-surface: '#303030'
  outline: '#8e9192'
  outline-variant: '#444748'
  surface-tint: '#c6c6c7'
  primary: '#ffffff'
  on-primary: '#2f3131'
  primary-container: '#e2e2e2'
  on-primary-container: '#636565'
  inverse-primary: '#5d5f5f'
  secondary: '#c8c6c5'
  on-secondary: '#313030'
  secondary-container: '#474746'
  on-secondary-container: '#b7b5b4'
  tertiary: '#ffffff'
  on-tertiary: '#303030'
  tertiary-container: '#e4e2e1'
  on-tertiary-container: '#656464'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e2e2e2'
  primary-fixed-dim: '#c6c6c7'
  on-primary-fixed: '#1a1c1c'
  on-primary-fixed-variant: '#454747'
  secondary-fixed: '#e5e2e1'
  secondary-fixed-dim: '#c8c6c5'
  on-secondary-fixed: '#1c1b1b'
  on-secondary-fixed-variant: '#474746'
  tertiary-fixed: '#e4e2e1'
  tertiary-fixed-dim: '#c8c6c6'
  on-tertiary-fixed: '#1b1c1c'
  on-tertiary-fixed-variant: '#474747'
  background: '#131313'
  on-background: '#e2e2e2'
  surface-variant: '#353535'
typography:
  display-lg:
    fontFamily: Bricolage Grotesque
    fontSize: 56px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Bricolage Grotesque
    fontSize: 40px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-lg-mobile:
    fontFamily: Bricolage Grotesque
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Bricolage Grotesque
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: 0.05em
spacing:
  margin-sm: 1rem
  margin-md: 2rem
  margin-lg: 4rem
  gutter: 1.5rem
  unit: 4px
---

## Brand & Style

This design system blends the gritty, high-contrast atmosphere of a noir film with the weathered, communal spirit of a coastal tavern. It is designed to feel personal and hand-crafted, moving away from formal academic structures toward a "journal-entry" aesthetic. The brand personality is raw, authentic, and slightly rebellious, targeting an audience that values storytelling and texture over polished corporate minimalism.

The visual style is a fusion of **Brutalism** and **Tactile Noir**. It utilizes heavy black backgrounds, high-contrast white elements, and "sketched" visual cues. The interface should feel like a collection of notes, posters, and artifacts pinned to a dark wooden wall, evoking a sense of history and lived-in mystery.

## Colors

The palette is strictly monochromatic, adhering to the Noir Edition principles. 
- **Primary:** Stark White (#FFFFFF) used for text and primary interactive boundaries to ensure maximum legibility against the dark void.
- **Backgrounds:** Absolute Black (#000000) serves as the primary canvas, creating a sense of infinite depth.
- **Surfaces:** Dark Grays (#1A1A1A, #333333) are used sparingly to define "paper" elements or containers, mimicking the look of weathered slate or charred wood.

Color is intentionally absent; hierarchy is instead established through line weight, scale, and the "hand-drawn" texture of the typography.

## Typography

The typography is the soul of the system. We replace formal serifs with **Bricolage Grotesque** for all headings. Its quirky, characterful, and slightly "broken" construction mimics the hand-drawn energy of chalk on a tavern board or a marker on a concert poster. 

- **Headlines:** Use Bricolage Grotesque at large scales. It should feel intentional and expressive, with tight tracking on display sizes to maximize the "sketched" impact.
- **Body:** **Geist** provides a clean, technical contrast that ensures long-form content remains readable within the high-contrast environment.
- **Metadata & Data:** **JetBrains Mono** is used for technical details, labels, and small captions to evoke the feeling of a typewriter or a printed manifest.

## Layout & Spacing

The layout follows a **Fluid Grid** model with an emphasis on "framed" content. Containers should not always reach the edge of the screen; instead, they should feel like objects placed on a dark surface.

- **Breakpoints:** Mobile (under 600px), Tablet (600px - 1024px), and Desktop (1024px+).
- **The Frame:** Use thick white borders (2px-4px) for major sections. On desktop, these borders should have a "rough" or slightly irregular appearance where possible to maintain the rustic theme.
- **Rhythm:** Use an 8px base grid, but allow for "loose" alignment in decorative elements to reinforce the hand-sketched aesthetic. Components like chips or images can be slightly rotated (1-2 degrees) to mimic the look of pinned notes.

## Elevation & Depth

In a noir system, depth is conveyed through **Bold Borders** and **Tonal Layers** rather than soft shadows. 

- **Layering:** Elements are stacked like physical paper. A "card" is simply a dark gray surface with a 2px stark white border.
- **Foreground:** Interactive elements should "pop" by using white fills with black text, effectively inverting the theme for maximum focus.
- **Textures:** Use subtle grain overlays or "noise" on dark surfaces to simulate the grit of paper or aged wood. Avoid all glows or blurs; every edge must remain sharp and decisive.

## Shapes

The shape language is **Sharp (0)**. There are no rounded corners in this design system. Every box, button, and image container must have 0px corner radii. This reinforces the "brutalist" and "raw" nature of the Tavern Noir aesthetic. 

For a more "hand-drawn" feel, borders of primary containers should occasionally feature a "double-line" or a "dashed-marker" style rather than a single solid stroke.

## Components

- **Buttons:** Rectangular, sharp edges. Primary buttons are White with Black text (Bricolage Grotesque Bold). Secondary buttons are Black with a 2px White border.
- **Cards:** Defined by a solid 2px white border. No shadows. Headers inside cards should be separated by a single horizontal white line.
- **Input Fields:** Bottom-border only, mimicking a lined notebook. The cursor should be a thick white block.
- **Chips/Tags:** Small boxes with JetBrains Mono text. Unlike standard rounded chips, these are sharp-edged boxes.
- **Lists:** Bullet points are replaced with "X" marks or hand-drawn style dashes. 
- **Checkboxes:** Simple squares that fill with a solid white block when selected.
- **Special Elements:** "Torn Paper" dividers or "Duct Tape" style headers are encouraged for high-priority callouts to enhance the tactile, collage feel.