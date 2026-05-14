---
name: playlist-curation
description: Use when user asks for music recommendations, Spotify playlists, song suggestions by mood/genre/scene/atmosphere, playlist naming, or curating tracks for a specific vibe
---

# Playlist Curation

Curate Spotify-style playlists with point-of-view taste and a Big-O naming convention that encodes musical density at a glance.

## When to Use

- User asks for music recommendations
- User describes a mood, scene, time-of-day, weather, or genre and wants tracks
- User asks to name an existing playlist or sketch
- User wants 15-20 song suggestions for a specific vibe

**Don't use for:** generic top-40 requests, mainstream chart lookups, or "play me [specific artist]" — this skill is for *curation*, not lookup.

## Naming Convention

```
O(complexity): English Descriptor
```

Two parts, always:
1. **`O(?)`** — Big-O notation encoding musical density / information complexity
2. **English descriptor** — the scene, mood, or moment

The descriptor must be in **English only** (no mixed Chinese), so the list reads like a tidy commit log in Spotify's UI.

## Complexity Classes

| Class | Density | Music Type | Reference Artists |
|---|---|---|---|
| `O(1)` | Constant, minimal | Ambient, drone, lowercase | Brian Eno, Stars of the Lid, AMM |
| `O(log n)` | Efficient, contemplative | Jazz trios, ECM, chamber, late-night | Bill Evans, Keith Jarrett, Arvo Pärt |
| `O(n)` | Linear, walking pace | Folk, singer-songwriter, bossa | Nick Drake, Sufjan Stevens, João Gilberto |
| `O(n log n)` | Structured, layered | Prog, rigorous classical, art-rock | Bach, Radiohead, King Crimson |
| `O(n²)` | Building density | Post-rock, shoegaze, dream pop | Mogwai, Slowdive, Sigur Rós |
| `O(2ⁿ)` | Exponential intensity | Noise, metal, maximalism | Swans, Sunn O))), Lightning Bolt |
| `O(n!)` | Combinatorial chaos | Free jazz, avant-garde | Cecil Taylor, Albert Ayler, Naked City |

## Process

### For a new playlist

1. Identify the right `O(?)` class from the user's request
2. Propose 2-3 English descriptor options, let the user pick
3. Confirm the final name before building the tracklist
4. Curate 15-20 tracks (see Curation Style below)
5. Present the tracklist with brief curation rationale
6. Append the entry to the Existing Playlists canon below

### For naming an existing playlist or sketch

1. Infer the density class from the track list
2. Propose a descriptor matching the mood
3. Default format: `O(?): Descriptor`

### When in doubt about complexity class

- Ask: "Is this denser/sparser than [reference]?" using a known reference artist
- Lean toward the lower complexity if borderline (a too-quiet name on dense music is funnier than the inverse)

## Curation Style

- **Point of view, not popular picks.** Curate with taste, not chart positions.
- **Mix canonical anchors with one or two less-obvious personal choices.** Anchors build trust; sleepers reward discovery.
- **Order for arc, not random shuffle.** Opening (set the scene) → middle (develop) → close (resolve or fade).
- **Briefly explain the curation logic** so the user sees the thread connecting the tracks.

Each track entry: `Artist — Track Title (Album, Year)` for clarity.

## Existing Playlists

| Name | Theme | Notes |
|---|---|---|
| `O(log n): After Midnight` | Late-night jazz | Curated 2026-05, 15 tracks |

Append new entries below as the canon grows.

## Future Series Ideas (Parked)

Alternative naming systems considered but not adopted. Available as fallback or sub-series — **don't suggest unless the user explicitly asks to spin off a sub-collection.**

- **Mathematical constants** — π / e / φ / i / ∞ / 0 / γ — each maps to a different mood archetype
- **Untranslatable emotion words** — Saudade / Sehnsucht / Mono no aware / Hiraeth / Duende / Ataraxia
- **Unix process states** — /root, /tmp, daemon, fork, segfault, zombie, cache miss

## Common Mistakes

| Mistake | Fix |
|---|---|
| Mixing Chinese into the descriptor | English only — the format is for clean reading in Spotify |
| Suggesting parked naming systems unprompted | Default is `O(?)`; only spin off when user asks |
| Random track order | Order for arc: opening → development → close |
| All canonical picks, no surprises | Include 1-2 personal-taste choices per playlist |
| All sleepers, no anchors | Anchor with recognizable picks so the user trusts the rest |
| Skipping descriptor confirmation | Propose 2-3 options and let user pick before building tracklist |
| Forgetting to update canon | After confirming a new playlist, append it to Existing Playlists |
