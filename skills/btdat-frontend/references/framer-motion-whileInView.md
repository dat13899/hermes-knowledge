# framer-motion whileInView — mobile rendering pitfall

## Problem
`motion.div` with `whileInView` + `viewport={{ once: true }}` silently fails to animate elements into view on mobile browsers. Sections appear blank — content exists in DOM but opacity stays at 0 because the animation never fires.

Root cause: framer-motion's `whileInView` uses Intersection Observer internally. Without an `amount` threshold, the observer may never consider the element "in view" on small mobile screens where elements enter the viewport differently than on desktop.

## Fix: always add `amount`
```jsx
// WRONG — fails to render on mobile
<motion.div
  initial={{ opacity: 0, y: 30 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true }}              // ← missing amount
  transition={{ duration: 0.6 }}
>

// RIGHT — renders reliably on all viewports
<motion.div
  initial={{ opacity: 0, y: 30 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, amount: 0.1 }} // ← 10% of element must be visible
  transition={{ duration: 0.6 }}
>
```

## useInView hook — same fix
```jsx
// WRONG
const inView = useInView(ref, { once: true, margin: '-80px' });

// RIGHT
const inView = useInView(ref, { once: true, amount: 0.1 });
```

## Anti-pattern: negative margin on mobile
`margin: '-80px'` means "don't trigger until element is 80px past the viewport edge." On short mobile screens this means the user scrolls past the element before it ever triggers. Never use negative margin for mobile whileInView triggers.

## Where to check
Every `viewport={{ once: true }}` without `amount` — search codebase for the pattern. Applies to:
- `motion.div` / `motion.section` / `motion.li` with `whileInView`
- `useInView(ref, ...)` hook calls
- Section headers, stat cards, feature cards, contact sections

## amount values
- `0.1` — safe default (10% of element visible = trigger)
- `'some'` — alternative (any part visible, works for very tall elements)
- Don't use `0` or omit — unreliable on mobile
