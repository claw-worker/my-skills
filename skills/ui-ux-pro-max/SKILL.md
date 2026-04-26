---
name: ui-ux-pro-max
description: "UI/UX design intelligence. 67 styles, 96 palettes, 57 font pairings, 25 charts, 13 stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui). Actions: plan, build, create, design, implement, review, fix, improve, optimize, enhance, refactor, check UI/UX code. Projects: website, landing page, dashboard, admin panel, e-commerce, SaaS, portfolio, blog, mobile app, .html, .tsx, .vue, .svelte. Elements: button, modal, navbar, sidebar, card, table, form, chart. Styles: glassmorphism, claymorphism, minimalism, brutalism, neumorphism, bento grid, dark mode, responsive, skeuomorphism, flat design. Topics: color palette, accessibility, animation, layout, typography, font pairing, spacing, hover, shadow, gradient. Integrations: shadcn/ui MCP for component search and examples."
---

# UI/UX Pro Max - Design Intelligence

Comprehensive design guide for web and mobile applications. Contains 67 styles, 96 color palettes, 57 font pairings, 99 UX guidelines, and 25 chart types across 13 technology stacks. Searchable database with priority-based recommendations.

## When to Apply

When the task involves **UI structure, visual design decisions, interaction patterns, or user experience quality control**, use this Skill.

### Must Use

- Designing new pages (Landing Page, Dashboard, Admin, SaaS, Mobile App)
- Creating or refactoring UI components (buttons, modals, forms, tables, charts)
- Choosing color schemes, font systems, spacing standards, or layout systems
- Reviewing UI code for user experience, accessibility, or visual consistency
- Implementing navigation structures, animations, or responsive behavior
- Making product-level design decisions (style, information hierarchy, brand expression)
- Improving perceived quality, clarity, or usability of interfaces

### Skip

- Pure backend logic development
- Only API or database design
- Non-UI performance optimization
- Infrastructure or DevOps work

**Decision rule**: If the task will change how something **looks, feels, moves, or is interacted with**, use this Skill.

## Rule Categories by Priority

| Priority | Category | Impact | Domain |
|----------|----------|--------|--------|
| 1 | Accessibility | CRITICAL | `ux` |
| 2 | Touch & Interaction | CRITICAL | `ux` |
| 3 | Performance | HIGH | `ux` |
| 4 | Style Selection | HIGH | `style`, `product` |
| 5 | Layout & Responsive | HIGH | `ux` |
| 6 | Typography & Color | MEDIUM | `typography`, `color` |
| 7 | Animation | MEDIUM | `ux` |
| 8 | Forms & Feedback | MEDIUM | `ux` |
| 9 | Navigation Patterns | HIGH | `ux` |
| 10 | Charts & Data | LOW | `chart` |

---

## Prerequisites

Python 3 is required. On this system, use `python` (not `python3`).

```bash
python --version
```

---

## How to Use This Skill

| Scenario | Trigger Examples | Start From |
|----------|-----------------|------------|
| **New project / page** | "Build a landing page", "Build a dashboard" | Step 1 then Step 2 (design system) |
| **New component** | "Create a pricing card", "Add a modal" | Step 3 (domain search: style, ux) |
| **Choose style / color / font** | "What style fits a fintech app?" | Step 2 (design system) |
| **Review existing UI** | "Review this page for UX issues" | Quick Reference checklist |
| **Fix a UI bug** | "Button hover is broken" | Quick Reference |
| **Improve / optimize** | "Make this faster", "Improve mobile experience" | Step 3 (domain search: ux, react) |
| **Add charts / data viz** | "Add an analytics dashboard chart" | Step 3 (domain: chart) |
| **Stack best practices** | "React performance tips" | Step 4 (stack search) |

### Step 1: Analyze User Requirements

Extract: product type, target audience, style keywords, stack.

### Step 2: Generate Design System (REQUIRED)

```bash
python skills/ui-ux-pro-max/scripts/search.py "<product_type> <industry> <keywords>" --design-system [-p "Project Name"]
```

**With persistence:**
```bash
python skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system --persist -p "Project Name"
```

### Step 3: Supplement with Detailed Searches

```bash
python skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain <domain> [-n <max_results>]
```

| Need | Domain | Example |
|------|--------|---------|
| Product type patterns | `product` | `--domain product "entertainment social"` |
| More style options | `style` | `--domain style "glassmorphism dark"` |
| Color palettes | `color` | `--domain color "entertainment vibrant"` |
| Font pairings | `typography` | `--domain typography "playful modern"` |
| Chart recommendations | `chart` | `--domain chart "real-time dashboard"` |
| UX best practices | `ux` | `--domain ux "animation accessibility"` |
| Landing structure | `landing` | `--domain landing "hero social-proof"` |
| React/Next.js perf | `react` | `--domain react "rerender memo list"` |
| App interface a11y | `web` | `--domain web "accessibilityLabel touch"` |

### Step 4: Stack Guidelines

```bash
python skills/ui-ux-pro-max/scripts/search.py "<keyword>" --stack react-native
```

---

## Output Formats

```bash
# ASCII box (default)
python skills/ui-ux-pro-max/scripts/search.py "fintech crypto" --design-system

# Markdown
python skills/ui-ux-pro-max/scripts/search.py "fintech crypto" --design-system -f markdown
```

---

## Pre-Delivery Checklist

- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set (Phosphor or Heroicons)
- [ ] Semantic theme tokens used (no hardcoded hex)
- [ ] All tappable elements provide pressed feedback
- [ ] Touch targets >= 44x44pt (iOS) / 48x48dp (Android)
- [ ] Micro-interactions 150-300ms with native easing
- [ ] Text contrast >= 4.5:1 in both light and dark mode
- [ ] Safe areas respected for fixed headers/tab bars
- [ ] 4/8dp spacing rhythm maintained
- [ ] Tested on small phone, large phone, and tablet
- [ ] Screen reader focus order matches visual order
- [ ] `prefers-reduced-motion` respected

## Gotchas
<!-- 実行時に失敗したパターンを蓄積する -->
- （実行時に失敗したら追記）
