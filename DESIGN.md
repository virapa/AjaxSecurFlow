---
name: AjaxSecurFlow Dashboard
description: Industrial dark console for the AjaxSecurFlow SaaS dashboard.
colors:
  ground: "#020617"
  surface: "#0F172A"
  surface-raised: "#1E293B"
  border: "#FFFFFF0D"
  primary: "#0891B2"
  primary-hover: "#06B6D4"
  primary-text: "#22D3EE"
  on-surface: "#FFFFFF"
  on-surface-muted: "#6B7280"
  on-surface-faint: "#4B5563"
  success: "#4ADE80"
  warning: "#FACC15"
  error: "#F87171"
typography:
  headline-lg: { fontFamily: Inter, fontSize: 30px, fontWeight: 900, lineHeight: 1.1, letterSpacing: -0.02em }
  headline-md: { fontFamily: Inter, fontSize: 18px, fontWeight: 700, lineHeight: 1.2 }
  section-title: { fontFamily: Inter, fontSize: 14px, fontWeight: 900, lineHeight: 1.2, letterSpacing: 0.1em }
  body-md: { fontFamily: Inter, fontSize: 14px, fontWeight: 500, lineHeight: 1.5 }
  body-sm: { fontFamily: Inter, fontSize: 12px, fontWeight: 700, lineHeight: 1.4 }
  label-xs: { fontFamily: Inter, fontSize: 10px, fontWeight: 900, lineHeight: 1.2, letterSpacing: 0.1em }
  mono-sm: { fontFamily: ui-monospace, fontSize: 12px, fontWeight: 500, lineHeight: 1.5 }
rounded:
  md: 12px
  lg: 16px
  xl: 24px
  hero: 40px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 32px
  xl: 40px
components:
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.xl}"
    padding: 32px
  field:
    backgroundColor: "#FFFFFF0D"
    rounded: "{rounded.md}"
    padding: 12px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: 16px
    typography: "{typography.label-xs}"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-danger:
    backgroundColor: "#F8717126"
    textColor: "{colors.error}"
    rounded: "{rounded.md}"
    padding: 8px
  chip-code:
    backgroundColor: "#FFFFFF0D"
    textColor: "{colors.primary-text}"
    rounded: "{rounded.md}"
    padding: 8px
    typography: "{typography.mono-sm}"
---

# AjaxSecurFlow Dashboard

## Overview
A control-room console for security professionals. Dark, dense, confident. Everything sits on a near-black navy ground; cyan is reserved for the primary action and live status. Section titles are tiny, black-weight, uppercase and letter-spaced, like an equipment label.

## Colors
- **Ground (#020617)** page background. **Surface (#0F172A)** cards at 40% opacity over ground. **Surface raised (#1E293B)** hero gradients.
- **Primary (#0891B2)** the only saturated call to action; hover lifts to **#06B6D4**. **Primary text (#22D3EE)** for accent text and code chips.
- **Borders** are white at 5% opacity, never solid grey.
- **Success / Warning / Error** appear only on status pills and inline alerts, at 10% background + 20% border tints.

## Typography
Inter throughout. Two registers: black-weight uppercase micro-labels (`label-xs`, `section-title`) for structure, and medium-weight body for content. Monospace is used only for tokens, ids and code.

## Layout
Content column `max-width 896px`, page padding `xl`, vertical rhythm `xl` between cards, `md` inside. Two-column grid on `md+`, single column below.

## Elevation & Depth
Flat. Depth comes from tonal layering (ground → surface → field) and 5% white borders. The only shadow is the primary button glow (`shadow-cyan-500/20`).

## Shapes
Generous radii: fields `md`, buttons `lg`, cards `xl`, hero `hero`. Never mix square corners into a view.

## Components
- **Card**: `surface` at 40%, 5% border, `xl` radius, 32px padding, `section-title` heading with `md` gap below.
- **Field (read-only)**: 5% white background, 10% border, `md` radius, `body-md` text, `label-xs` muted label above.
- **Button primary**: full width in forms, `label-xs` uppercase, cyan glow, `active:scale-[0.98]`.
- **Button danger**: small, error tint background, error text, used for revoke/delete with a confirmation step.
- **Chip code**: monospace, primary-text on 5% white, for token prefixes and ids.
- **Inline alert**: 10% tint background + 20% tint border of the semantic color, `body-sm`, centered.

## Do's and Don'ts
- Do keep cyan for one primary action per card.
- Do use `label-xs` uppercase for every field label and table header.
- Don't introduce purple or gradients outside the hero card.
- Don't use solid grey borders or drop shadows on cards.
- Don't show secrets more than once; after creation, replace with the prefix chip.
