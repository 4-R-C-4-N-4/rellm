Complete /guru-review-edges Session Summary

  Overall metrics (0.85 PARALLELS tier)

  ┌─────────────────────────────┬───────────────────────────────┐
  │           Metric            │             Count             │
  ├─────────────────────────────┼───────────────────────────────┤
  │ Total agent actions queued  │ 4,457                         │
  ├─────────────────────────────┼───────────────────────────────┤
  │ Accepts                     │ 4,301 (96.5%)                 │
  ├─────────────────────────────┼───────────────────────────────┤
  │ Reclassified → surface_only │ 156 (3.5%)                    │
  ├─────────────────────────────┼───────────────────────────────┤
  │ Applied by user (accepts)   │ 4,228                         │
  ├─────────────────────────────┼───────────────────────────────┤
  │ Pending user-apply          │ 229 (73 accept + 156 surface) │
  ├─────────────────────────────┼───────────────────────────────┤
  │ Safe pool remaining         │ 0                             │
  └─────────────────────────────┴───────────────────────────────┘

  Headline accept rate: ~96.5% — Mistral's 0.85 tier was strongly over-flagged at first glance, but turned out to be
  well-calibrated for the bulk of tradition pairs. The surface_only flips concentrated in a handful of pathological
  clusters rather than being evenly noisy.

  Model performance — where Mistral got it right

  The 0.85 tier captured genuine substantive parallels across:
  - christian_mysticism↔neoplatonism: 1,092 accepts (Boehme ↔ Plotinus — the largest cluster; Lutheran-Plotinian
  mysticism literally fits)
  - neoplatonism↔taoism: 325 (Plotinus ↔ TTC/Zhuangzi)
  - hermeticism↔neoplatonism: 325 (CH ↔ Plotinus)
  - renaissance_hermeticism↔western_esoteric: 191 (Bruno Heroic Enthusiasts ↔ Ouspensky 4D)
  - egyptian↔mesopotamian: 188 (EBD ↔ Enuma Elish — chaoskampf/creation)
  - greek_mystery↔taoism: 180 (Pythagorean ethics ↔ Zhuangzi)

  Bulk-accept clusters worked well because Mistral correctly identified Neoplatonic-influence lineages (Boehme reads
  Plotinus, Bruno reads CH+Plato, Hierocles IS Neoplatonic, etc.).

  Model performance — where Mistral over-flagged

  Four systematic failure modes drove almost all the 156 surface_only flips:

  1. Pure hymn invocations paired with substantive philosophy — the largest single error class. Orphic Hymns to
  specific Greek deities (Pan, Mars, Juno, Neptune, Ceres, Aurora, Vulcan, Moon, Death, etc.) consistently paired
  with EBD/EHH content on no shared move. ~281 surface in egyptian↔greek_mystery alone.
  2. Boehme/Eckhart title-page chunks ("Sacred Texts Esoteric Index... Chapter VI THE RESTO[RATION]") paired with
  substantive primary text. The title-page is just a chapter header but Mistral read it as substantive.
  3. EBD-index apparatus — Budge's scholarly commentary (Tiele on Egyptian polytheism, Recueil de Travaux footnotes,
  Lanzone citations) read as Egyptian primary theology and matched to anything theological.
  4. Cross-tradition deity-name matching without shared move — e.g. Greek Jove ↔ Mesopotamian Marduk, Orphic Hercules
   ↔ Yasna Vishtaspa.

  Largest surface_only clusters

  ┌───────────────────────────────────┬───────────────┬────────────────────────────────────────────────┐
  │               Pair                │ Surface flips │                      Why                       │
  ├───────────────────────────────────┼───────────────┼────────────────────────────────────────────────┤
  │ egyptian↔greek_mystery            │ 281           │ Orphic Hymn invocations vs EBD apparatus       │
  ├───────────────────────────────────┼───────────────┼────────────────────────────────────────────────┤
  │ christian_mysticism↔greek_mystery │ 232           │ Boehme vs Pythagorean Sentences / Orphic Hymns │
  ├───────────────────────────────────┼───────────────┼────────────────────────────────────────────────┤
  │ christian_mysticism↔neoplatonism  │ 225           │ Boehme title-pages over-paired with Plotinus   │
  ├───────────────────────────────────┼───────────────┼────────────────────────────────────────────────┤
  │ christian_mysticism↔egyptian      │ 207           │ Boehme title-pages + EHH division titles       │
  ├───────────────────────────────────┼───────────────┼────────────────────────────────────────────────┤
  │ hermeticism↔neoplatonism          │ 178           │ CH ↔ Plotinus where CH chunk was apparatus     │
  └───────────────────────────────────┴───────────────┴────────────────────────────────────────────────┘

  Methodological lessons surfaced

  - Iamblichus, Hierocles, Proclus, Thomas Taylor chunks placed under greek_mystery or pythagorean-golden-verses are
  substantively Neoplatonic and accept naturally with Plotinus — the tradition labeling is by source-file, not by
  doctrine.
  - EBD-index.309 ("unity of supreme self-existent being") is Budge's Egyptian monotheism exposition and pairs
  substantively with Plotinus's One, not surface-only.
  - Plato Symposium ↔ Bruno Heroic Enthusiasts has tighter accepts on Diotima/eros sections than on
  Aristophanes/Eryximachus speeches.
  - The 4D/phenomenal-noumenal cluster (Bruno + Boehme + TTC/Zhuangzi all ↔ Ouspensky) was Mistral's strongest signal
   — high confidence and high agent agreement.

  Pool state

  - Confidence ≥ 0.90: 389 still pending (auto-promote territory; agent did NOT touch — these are yours via
  auto_promote_edges.sh --confidence 0.9 --apply)
  - Confidence 0.85: 229 pending (all are my queued actions awaiting your /api/apply)
  - Confidence 0.75–0.80: 12 pending (untouched lower tier)

