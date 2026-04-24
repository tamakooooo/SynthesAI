---
version: "alpha"
name: SynthesAI
description: AI-powered learning assistant - warm minimalism meets knowledge workspace

colors:
  primary: "#37352f"
  secondary: "#9b9a97"
  accent: "#03689b"
  accent-secondary: "#448361"
  neutral: "#ffffff"
  neutral-warm: "#fbf6f3"
  surface: "#f7f6f3"
  border: "#e3e2de"
  success: "#448361"
  warning: "#d9730d"
  error: "#d44c47"
  info: "#03689b"
  highlight-yellow: "#fbf3db"
  highlight-blue: "#ddebf1"
  highlight-green: "#dbeddb"
  highlight-red: "#ffe2dd"
  highlight-purple: "#eae4f2"

typography:
  h1:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: 600
    lineHeight: 1.2
  h2:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.3
  h3:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.4
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.5
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.4
  code:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5

rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 12px
  full: 9999px

spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px

components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  input:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
    borderWidth: 1px
    borderColor: "{colors.border}"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  tag:
    backgroundColor: "{colors.highlight-blue}"
    textColor: "{colors.accent}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
---

## Overview

Warm Minimalism meets Knowledge Workspace. SynthesAI's UI evokes a premium notebook aesthetic — clean surfaces, thoughtful typography, and subtle depth that makes knowledge feel valuable.

The design philosophy emphasizes:
- **Clarity first**: Every element serves a purpose, nothing decorative
- **Progressive disclosure**: Simple by default, powerful when needed
- **Knowledge-centric**: Content takes center stage, UI fades back
- **Friendly professionalism**: Warm tones that invite exploration

## Colors

The palette balances warmth with clarity:

- **Primary (#37352f)**: Warm dark gray — the default text color, softer than pure black
- **Secondary (#9b9a97)**: Warm gray — for captions, metadata, borders
- **Accent (#03689b)**: Deep blue — primary interactive color, trustworthy
- **Accent-secondary (#448361)**: Forest green — success states, secondary actions
- **Surface (#f7f6f3)**: Warm off-white — card backgrounds, elevated surfaces
- **Border (#e3e2de)**: Light gray — subtle boundaries, never harsh

Semantic colors are reserved for their specific purposes:
- **Success**: Forest green, never overwhelming
- **Warning**: Burnt orange, clearly distinct
- **Error**: Terracotta red, alerting but not alarming

Highlight colors create visual variety in knowledge cards:
- **Yellow**: Definitions, important terms
- **Blue**: Examples, code snippets
- **Green**: Success, completion
- **Purple**: Advanced concepts

## Typography

Inter is the primary typeface — modern, readable, friendly:
- Clear letterforms optimized for screens
- Wide language support for international users
- Distinct weights for hierarchy without heaviness

JetBrains Mono handles code and technical content:
- Monospace for transcription text, URLs
- Excellent readability for dense content

Type scale follows a comfortable rhythm:
- **H1 (32px)**: Page titles, welcoming presence
- **H2 (24px)**: Section headers, clear division
- **H3 (20px)**: Card titles, content labels
- **Body (16px)**: Primary content, comfortable reading
- **Small (14px)**: Metadata, secondary info
- **Label (12px)**: Tags, badges, compact labels

## Layout

Spacing follows an 4px base unit:
- **xs (4px)**: Tight grouping, inline elements
- **sm (8px)**: Default gap, comfortable proximity
- **md (16px)**: Paragraph separation, clear breaks
- **lg (24px)**: Section margins, visual breathing room
- **xl (32px)**: Major sections, page-level structure
- **2xl (48px)**: Hero spacing, welcoming entry

Content width is capped at 708px for optimal reading.
Sidebar width: 240px for navigation clarity.
Page margins: 96px desktop for comfortable framing.

## Shapes

Corners are rounded with restraint:
- **sm (4px)**: Buttons, inputs — subtle softness
- **md (8px)**: Cards, containers — friendly frames
- **lg (12px)**: Larger surfaces, prominent elements
- **full**: Tags, badges — pill shapes

Never harsh, never childish — the right warmth for each context.

## Components

### Buttons

**Primary**: Deep blue background with white text — confident calls to action
- Hover: Slightly lighter blue
- Active: Darker shade
- Disabled: Gray background, muted text

**Secondary**: Surface background with primary text — softer alternatives
- Hover: Lighter surface with border
- Focus: Accent border ring

### Inputs

Clean inputs with warm borders:
- Default: White background, light border
- Focus: Accent border, subtle glow
- Error: Error-colored border, gentle alert
- Disabled: Surface background, secondary text

### Cards

Content containers that breathe:
- Surface background, slightly elevated
- Large rounded corners for friendliness
- Adequate padding (24px) for content comfort
- Hover: Subtle shadow for interactive cards

### Tags

Pill-shaped labels:
- Highlight-colored backgrounds
- Accent-colored text
- Full rounded corners
- Compact padding

## Do's and Don'ts

**Do:**
- Use warm colors for comfort
- Give content generous space
- Highlight important information with color blocks
- Show loading states for long operations
- Provide clear feedback for actions

**Don't:**
- Use harsh pure black (#000000)
- Overcrowd with decoration
- Hide important actions
- Use multiple accent colors simultaneously
- Skip loading states for async operations

## Responsive Behavior

- **Desktop (≥1024px)**: Full sidebar, generous margins
- **Tablet (768-1023px)**: Collapsible sidebar, reduced margins
- **Mobile (<768px)**: Bottom navigation, stacked layouts

Touch targets: Minimum 44px for all interactive elements.