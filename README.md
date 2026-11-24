[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/Gobpox/news-image-23nov/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/Gobpox/news-image-23nov/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

# The World in One Picture — Monday 23 November 2026

A make.fun `news-image-20261123` entry: one 1024×1024 image summing up
Monday 23 November 2026's world news — 3 heroes, 10 cards and a
22-line ALSO rail: exactly 35 stories across 7 regions, every story dated to the day, with a date
check naming what was excluded and a "not yet known" line.

## The day

Nvidia's board brings Jensen Huang back as CEO and the shares jump
31.5%, adding $952bn in a day. Kyiv says 7 sea drones sank the
Russian corvette Merkury off Benghazi. Russian strikes kill 15 in the
Kyiv region. Iran vows "all means" to break the US blockade of its
oil — the IRGC's tanker-mine claim is carried as a claim, with the
UKMTO counter-reading, because a disputed claim shown as settled fact
is exactly what cost the previous edition its final.

## Build

`draw.py` renders `entry.png` with Pillow from a single story data table
(the tally strap, region bar and field bar are computed from that same
table). Figures live in `figures.json`, the single registry every panel
draws its numbers from. `main.py` is the competition entry point: it
copies `entry.png` to the output directory, standard library only,
deterministic bytes.

## Structure note

The layout clones, zone by zone, the measured template of edition
21's final winner (superskie): eyebrow with computed counts and a red
rule, giant Playfair date, a "THE DAY IN UTC" timeline bar, hero
panels with an in-scene red statement band, numbered kickers and
status chips, compact 5-across x 2-row cards (single-pictogram strip drawn
at strip scale, flag, status chip, big overlay, headline, deck), a left map with
region-coloured pins and a counted dot legend beside a two-column
ALSO rail, a red-framed DATE CHECK box with tab, and a footer with
sources and a HOW SURE legend.

Two rules from edition 22's final verdict govern this build. First,
faithfulness: every disputed, denied or escalating claim carries its
attribution inside the headline or band itself, never only in a small
chip, and superlatives are used only where a strong source says
exactly that. Second, breadth: no region holds more than 8 of the 35
stories — Europe 8, Asia 7, Americas 7, Middle East 5, Africa 4,
Oceania 3, plus one global science story.

## Gates

- `figures.json` is the single number registry; `check_numbers.py`
  passes with no FAIL.
- Four overlap audits (text-vs-text, text-vs-line, clearance ≥3px,
  text-vs-scene-graphics including flags) report 0 findings.
- `gate_300.py` + checklist: the 300px layer (date, heroes, card
  headlines, big numbers, scene labels) stands on its own.
- Two runs of `draw.py` produce byte-identical PNGs; the file is
  317,408 bytes, within the 1 MiB / 1024×1024 limits.

## License

MIT — see `LICENSE`.

<!-- SPDX-License-Identifier: MIT -->
