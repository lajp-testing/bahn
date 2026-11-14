# Design plan — kartta yöllä (a road map after dark)

Written before the rebuild, per the frontend-design skill: subject, tokens, layout,
principles, then a review against the generic defaults.

**Subject.** One dispatcher's week moving cars across Finland in November: polar night,
road maps, timetables, dealers, freelance drivers. **Audience.** Peer reviewers at a
laptop or a projector, most of whom don't know the challenge. **Primary job.** Make the
challenge and our decisions legible in minutes — the map replay is the hero, the
explainer and inspector are the supporting acts.

## Colour tokens

| Name | Hex | Role |
|---|---|---|
| Polar night | `#0A141F` | page ground — deep blue night, never neutral black |
| Kartta land | `#142A44` | the map's Finland fill, on a darker sea `#0C1A2C` |
| Birch | `#EFE9DC` | primary text (birch bark, warm white) |
| Frost | `#8FA6BE` | secondary text, rules, roads |
| Headlight | `#F0A532` | attention only: live pulses, the time cursor, keyboard focus, the tour |
| On-time | `#54C08A` | green strictly for on-time / delivered / margin earned |
| Late | `#EF6D6D` | red strictly for late cars and refunds |

Water and coast tones (`#0C1A2C`, `#33608C`) live inside the map only.

## Type

- **Fraunces** (variable 300–900, optical size) — display: the page title, section
  headings, the guided-tour captions. A warm, slightly wonky serif: the explainer's voice.
- **IBM Plex Sans** (400/600) — body and UI text, sentence case.
- **IBM Plex Mono** (400/600) — money, times, counters, request and driver IDs: the
  timetable register. Used for real data at readable sizes, never as tracked-out labels.

All three are vendored as woff2 in `demo/fonts/` (offline). Extreme contrast comes from
Fraunces 300 vs 900 and from size: the running margin is the biggest number on the page.

## Layout

**The week** — the map is the hero at ~75% width, full height; the side rail is a
manifest (big mono numbers between hairline rules, no cards); one full-width timeline
strip under the map carries the controls, day ticks, an activity sparkline and story
markers — not a thin slider.

```
┌──────────────────────────────────────────────┬────────────────────┐
│  A dispatcher's week in Finland      [tabs]   │   €3,997.35        │
│  ┌────────────────────────────────────────┐   │   margin           │
│  │           F I N L A N D   (zoom/pan)   │   │   ─────────────   │
│  │   graticule · roads · towns · cars     │   │   555  requests    │
│  │                                        │   │   173  won         │
│  │                                        │   │   98.9% on time    │
│  └────────────────────────────────────────┘   │   ─────────────    │
│  ▶ ‹ event  −1h  −day   Mon 09:20   1 h/s     │   right now        │
│  ─┬Mon─┬Tue─┬Wed─┬Thu─┬Fri─┬Sat─┬Mon─┬        │   09:58 R00307 …   │
│  █ sparkline: requests/hour, wins/hour  ▌cursor   09:57 gig g142… │
└──────────────────────────────────────────────┴────────────────────┘
```

**Inspect a decision** — a real flow: the request list on the left, and on the right a
vertical spine the request travels down, node to node, each stage hanging off the line
with its evidence. Not stacked boxes.

```
┌ requests (ruled table) ┐┌ the spine ────────────────────────────┐
│ Mon 09:15 R00008 won   ││ ● the note          "Ei erityistä"    │
│ Mon 09:16 R00009 lost  ││ │                                    │
│ …                      ││ ● the intake        slack, the queue  │
│                        ││ │                                    │
│                        ││ ● the cost model  ≈ expected fee      │
│                        ││ │                                    │
│                        ││ ● the quoter       level, chances    │
│                        ││ ▼ outcome → gig → money               │
└────────────────────────┘└──────────────────────────────────────┘
```

**The challenge** — five numbered steps (a real sequence) as an editorial two-column
spread; the flow of a request drawn as a road: one line, eight stops, like a route on a
road map. **How it works** — the eight parts as a ruled list (name, reason, measured
effect), not a card grid; adoption bars and the rejected table to one side. **The
race** — two quiet line charts.

## Principles

1. Spend the boldness on the map; everything else whispers (rules, not cards).
2. Money and time always in Plex Mono, tabular, never rounded for looks.
3. Amber means "look here", green means "on time", red means "late" — nothing else
   is coloured.
4. Every number carries its truth: exact or marked ≈.
5. One orchestrated page-load reveal; after that, motion answers actions only
   (scrubbing, selecting a request, the tour). `prefers-reduced-motion` removes all of it.
6. Projector floor: 15px body text, high contrast, visible keyboard focus.

## Review against the generic defaults

- *Near-black + one acid accent* → replaced by a blue polar-night ground with three
  subject-grounded roles (headlights, on-time green, late red), not one accent.
- *Monospace for small data labels* → mono only for real data (times, money, IDs) at
  working sizes; UI labels are sentence-case Plex Sans, no tracked caps.
- *ALL-CAPS eyebrows, `A · B · C` meta strings* → none; headings are Fraunces sentence
  case, metadata is written as prose.
- *Identical rounded cards with soft shadows* → ruled lists, a manifest rail, a spine;
  the only surfaces are the map and the tour caption.
- *Cream + serif + terracotta* → no cream, no terracotta; amber is a headlight, not clay.
- *Fade-and-slide-up on every section* → one load reveal; the spine draws in when a
  request is chosen, because that answers the click.
- *Numbered markers* → kept only where the content is genuinely a sequence: the five
  steps of the challenge and the inspector's pipeline.
- *`→` on buttons* → buttons say what they do.
