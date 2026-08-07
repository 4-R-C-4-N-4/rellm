# Gold-set adjudication sheet

56 candidates · 20 proposed homologies / 36 proposed false friends · 31 borderline.
Proposed 2026-08-03 by Claude agents (independent of the Qwen base to be scored);
all pairs machine-validated: taxonomy IDs exist, both cells have n≥10 teacher-tagged
chunks, every quote verified verbatim against its corpus file.

For each candidate mark **Verdict:** `homology` / `false_friend` / `rejected` (+ optional note).
Ratified records then go to `ratified.jsonl` (schema in README.md). The proposer's verdict is
a proposal, not a default — reclassification is expected and healthy.

## Overlapping pairs — adjudicate once

- **DUP-1** (B-04, D-04): soul_migration buddhism↔platonism, both proposed false_friend. Same pair, two evidence sets.
- **DUP-2** (C-07, D-05): theosis_deification egyptian↔christian_mysticism, both proposed false_friend (C-07 borderline w/ Frazer counter-case; D-05 easy w/ Dionysius definition).
- **CONFLICT-1** (B-06, D-09): fana_annihilation sufism↔christian_mysticism — **the two proposer lanes disagree** (B-06: homology; D-09: false_friend), each citing Shah-Kazemi for the other side's case. Prime borderline specimen; one verdict decides both records.

---


## Lane A — Hellenic-esoteric cluster

### A-01 · proposed **homology** · easy
**neoplatonism / apophatic_theology** (“presence overpassing all knowledge; the way beyond knowing”, n=297)  ↔  **christian_mysticism / apophatic_theology** (“via negativa; super-essential (hyperousios) transcendence”, n=173)

**Claim:** Dionysius's via negativa is a lineage-backed continuation of the Plotinian-Proclan negative approach to the first principle.

**Rationale:** Both make the identical conceptual move: the first principle transcends every predicate, so negation outranks affirmation and even negations are finally surpassed in a knowing-beyond-knowing. The dependence is genetic, not coincidental - Dionysius demonstrably borrows Proclan technical vocabulary. The one real difference (the Christian God is also Trinity and Creator) modifies the object, not the apophatic mechanism itself.

**Primary evidence:**
> The main part of the difficulty is that awareness of this Principle comes neither by knowing nor by the Intellection that discovers the Intellectual Beings but by a presence overpassing all knowledge. In knowing, soul or mind abandons its unity; it cannot remain a simplex: knowing is taking account […]
> — `neoplatonism/plotinus-select-works-index/chunks/742.toml`
> Methinks he has shown by these his words how marvellously he has understood that the Good Cause of all things is eloquent yet speaks few words, or rather none; possessing neither speech nor understanding because it exceedeth all things in a super-essential manner, and is revealed in Its naked truth […]
> — `christian_mysticism/dionysius-mystical-theology/chunks/002.toml`

**Secondary citations:**
- E. R. Dodds (ed.), Proclus: The Elements of Theology (2nd ed., Oxford 1963), Introduction - documents Ps.-Dionysius's close verbal dependence on Proclus, including in negative theology.
- Andrew Louth, The Origins of the Christian Mystical Tradition: From Plato to Denys (1981), ch. on Denys the Areopagite - argues Dionysius's apophatic ascent continues the Neoplatonist method while bending it to Christian ends.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-02 · proposed **homology** · easy
**platonism / return_to_source** (“the heavenward pilgrimage; regrowing of the soul's wings”, n=88)  ↔  **neoplatonism / return_to_source** (“flight to the beloved Fatherland (epistrophe)”, n=278)

**Claim:** Plotinus's flight to the Fatherland self-consciously reworks Plato's heavenward return of the soul; Neoplatonic epistrophe is a systematization of the Phaedrus/Phaedo ascent.

**Rationale:** Both frame embodiment as exile from a native region, purification as the vehicle, and return to origin as the telos. Plotinus explicitly builds his return doctrine out of Platonic and Homeric imagery and interiorizes it: the journey is not spatial but a conversion of attention. The correspondence is genetic - Plotinus presents himself as exegete of Plato - not merely structural.

**Primary evidence:**
> For those who have once begun the heavenward pilgrimage may not go down again to darkness and the journey beneath the earth, but they live in light always; happy companions in their pilgrimage, and when the time comes at which they receive their wings they have the same plumage because of their […]
> — `platonism/plato-phaedrus/chunks/022.toml`
> "Let us flee then to the beloved Fatherland": this is the soundest counsel. But what is this flight? How are we to gain the open sea? For Odysseus is surely a parable to us when he commands the flight from the sorceries of Circe or Calypso- not content to linger for all the pleasure offered to his […]
> — `neoplatonism/plotinus-select-works-index/chunks/063.toml`

**Secondary citations:**
- A. H. Armstrong (ed.), The Cambridge History of Later Greek and Early Medieval Philosophy (1967), Part III on Plotinus - presents Plotinian procession and return as a systematization of the Platonic ascent texts.
- Pierre Hadot, Plotinus or the Simplicity of Vision (trans. 1993) - reads Plotinus's flight/return as an interiorized exegesis of Plato's ascent imagery (citation uncertain as to chapter).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-03 · proposed **homology** · easy
**neoplatonism / evil_as_privation** (“evil as privation and deficiency of Matter”, n=216)  ↔  **christian_mysticism / evil_as_privation** (“evil as warping, declension, lack of Good”, n=139)

**Claim:** Dionysius's treatment of evil in Divine Names 4 is textually derived from the Neoplatonic privation doctrine: evil has no substance of its own but is lack and failure of the good.

**Rationale:** Both deny evil an ideal archetype or positive principle and analyze it as parasitic deficiency in something otherwise good. Dionysius's chapter even rehearses and rejects the matter-is-evil option in Neoplatonic terms. Scholarship has shown the dependence is nearly verbatim (on Proclus's De malorum subsistentia), making this one of the clearest lineage homologies in the cluster.

**Primary evidence:**
> But first we will consider how it stands with artistic creations: there is no question of an ideal archetype of evil: the evil of this world is begotten of need, privation, deficiency, and is a condition peculiar to Matter distressed and to what has come into likeness with Matter.
> — `neoplatonism/plotinus-select-works-index/chunks/525.toml`
> but they are called evil because they fail in the exercise of their natural activity. The evil in them is therefore a warping, a declension from their right condition; a failure, an imperfection, an. impotence, and a weakness, loss and lapse of that power which would preserve their perfection in […]
> — `christian_mysticism/dionysius-divine-names-4/chunks/024.toml`

**Secondary citations:**
- Josef Stiglmayr, 'Der Neuplatoniker Proclus als Vorlage des sogen. Dionysius Areopagita in der Lehre vom Uebel', Historisches Jahrbuch 16 (1895) - demonstrated that Divine Names 4's evil-as-privation section closely follows Proclus's De malorum subsistentia.
- Jan Opsomer & Carlos Steel (trans.), Proclus: On the Existence of Evils (2003), Introduction - reviews the Proclus-Dionysius dependence and the privation analysis of evil.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-04 · proposed **homology** · easy
**neoplatonism / cosmic_sympathy** (“sympathetic One-All; one living being”, n=152)  ↔  **renaissance_hermeticism / cosmic_sympathy** (“inferiors answer superiors; Spirit of the World (quintessence)”, n=85)

**Claim:** Agrippa's chain by which inferior things 'answer' their superiors and draw down celestial gifts is the operative application of Plotinian cosmic sympathy within one ensouled living cosmos.

**Rationale:** Both hold that the cosmos is a single living being whose distant parts co-affect one another through likeness rather than contact. Agrippa names his sources ('Platonists, together with Hermes') and grounds all magic in exactly this structure, received via Ficino's Plotinus. The shift from contemplative explanation to operative technique changes the use, not the conceptual move.

**Primary evidence:**
> But, with all this gradation, each several thing is affected by all else in virtue of the common participation in the All, and to the degree of its own participation. This One-All, therefore, is a sympathetic total and stands as one living being; the far is near; it happens as in one animal with […]
> — `neoplatonism/plotinus-select-works-index/chunks/372.toml`
> And, after this course, that every inferior thing should, in its kind, answer its superior thing, and through this the Supreme Itself, and receive from heaven that celestial power they call the quintessence, or the Spirit of the World, or the Middle Nature; and from the Intellectual World a […]
> — `renaissance_hermeticism/agrippa-natural-magic-ch-37/chunks/001.toml`

**Secondary citations:**
- D. P. Walker, Spiritual and Demonic Magic from Ficino to Campanella (1958), chs. 1-2 - shows Ficinian-Agrippan magic theorizes its efficacy through the Neoplatonic spiritus and cosmic sympathy.
- Frances A. Yates, Giordano Bruno and the Hermetic Tradition (1964), ch. on Agrippa - Agrippa's occult philosophy systematizes the Neoplatonic-Hermetic sympathetic cosmos.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-05 · proposed **homology** · easy
**platonism / divine_madness** (“inspired madness (mantike/manike)”, n=18)  ↔  **renaissance_hermeticism / divine_madness** (“heroic fury (eroico furore)”, n=67)

**Claim:** Bruno's heroic furor explicitly reworks Plato's divine madness: a rapture that looks irrational but is supra-rational, carefully distinguished from pathological madness, and winged toward the divine.

**Rationale:** Plato's move is to split mania in two - disease versus divine gift - and rank the gift above sanity; Bruno performs the same split ('not a fury of black bile' but a fire from the intellectual sun) and even reuses the Phaedrus wing image. The transmission runs through Ficino's commentary on the four furores, so this is lineage plus preserved structure, not resemblance alone.

**Primary evidence:**
> For prophecy is a madness, and the prophetess at Delphi and the priestesses at Dodona when out of their senses have conferred great benefits on Hellas, both in public and private life, but when in their senses few or none. ... they must have thought that there was an inspired madness which was a […]
> — `platonism/plato-phaedrus/chunks/013.toml`
> It is not a fury of black bile which sends him drifting outside of judgment, reason, and acts of prudence, and tossed by the discordant tempest ... but it is aglow kindled by the intellectual sun in the soul, and a divine impetus which lends it wings, with which, drawing nearer and nearer to the […]
> — `renaissance_hermeticism/heroic-enthusiasts-pt1/chunks/027.toml`

**Secondary citations:**
- Paul Eugene Memmo (trans.), Giordano Bruno's The Heroic Frenzies (1964), Introduction - traces Bruno's furori to the four furores of Plato's Phaedrus as mediated by Ficino's commentaries.
- Frances A. Yates, Giordano Bruno and the Hermetic Tradition (1964), discussion of the Eroici furori - reads Bruno's heroic enthusiasm as Platonic-Ficinian divine madness (citation uncertain as to chapter).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-06 · proposed **homology** · easy
**hermeticism / microcosm_macrocosm** (“Man, after the image of the Cosmos made”, n=29)  ↔  **renaissance_hermeticism / microcosm_macrocosm** (“microcosm; likeness of all things in the world”, n=61)

**Claim:** The microcosm-macrocosm doctrine passes by direct textual lineage from the Hermetica into Renaissance Hermeticism, where Paracelsus receives 'their microcosm' as an inherited term of art and builds medicine and alchemy on it.

**Rationale:** The shared move is structural containment: a lower whole (man, or the Stone as man's analogue) replicates the architecture of the universal whole and therefore gives knowledge of and operative purchase on it. CH VIII derives man's cognitive reach from being made after the image of the Cosmos; Paracelsus reports the microcosm as received doctrine, explicitly linking it back to the Platonic world-animal. Renaissance usage extends the schema operationally but preserves its structure.

**Primary evidence:**
> Now the third life - Man, after the image of the Cosmos made, [and] having mind, after the Father's will, beyond all earthly lives - not only doth have feeling with the second God <i.e., the Cosmos>, but also hath conception of the first; for of the one 'tis sensible as of a body, while of the […]
> — `hermeticism/corpus-hermeticum-08/chunks/002.toml`
> Hence it comes to pass that this Stone is called animal, because in its blood a soul lies hid. It is likewise composed of body, spirit, and soul. For the same reason they called it their microcosm, because it has the likeness of all things in the world, and thence they termed it animal, as Plato […]
> — `renaissance_hermeticism/paracelsus-aurora-of-philosophers/chunks/007.toml`

**Secondary citations:**
- Walter Pagel, Paracelsus: An Introduction to Philosophical Medicine in the Era of the Renaissance (1958) - documents Paracelsus's microcosm doctrine and its Hermetic-Neoplatonic sources.
- Frances A. Yates, Giordano Bruno and the Hermetic Tradition (1964), chs. 1-2 - the Renaissance magus's man-as-microcosm derives from the Ficino-translated Hermetica.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-07 · proposed **homology** · borderline
**neoplatonism / emanation_hierarchy** (“procession from the One; unfailing spring”, n=592)  ↔  **gnosticism / emanation_hierarchy** (“emanations of the great Forefather Invisible”, n=83)

**Claim:** Gnostic aeon-emanation and Plotinian procession share the schema 'derivation-without-diminution of ordered plurality from a single transcendent source' - a correspondence seriously defended from common Platonic ancestry, yet polemically denied by Plotinus himself.

**Rationale:** For: both posit eternal, non-temporal generation of a graded hierarchy from one source that remains undiminished, and Sethian and Plotinian systems plausibly share Middle Platonic ancestry (Turner). Against: Plotinus's procession is necessary, continuous, and involves no fault, while the Pistis Sophia's emanations are discrete mythic persons whose hierarchy includes rupture, envy, and fall; Plotinus (Enn. II.9) attacks precisely this multiplication and dramatization of hypostases. A genuinely arguable case in both directions, which is its value.

**Primary evidence:**
> Imagine a spring that has no source outside itself; it gives itself to all the rivers, yet is never exhausted by what they take, but remains always integrally as it was; the tides that proceed from it are at one within it before they run their several ways, yet all, in some sense, know beforehand […]
> — `neoplatonism/plotinus-select-works-index/chunks/288.toml`
> Since the Pistis Sophia with her partner, they with the other twenty-two emanations are wont to make (up) twenty-four emanations, [41 ] these which emanated them out the great Forefather Invisible, he with the great two Triple powers.
> — `gnosticism/pistis-sophia/chunks/017.toml`

**Secondary citations:**
- John D. Turner, Sethian Gnosticism and the Platonic Tradition (2001) - argues Gnostic emanation systems and Plotinian procession descend from shared Middle Platonic metaphysics.
- Plotinus, Ennead II.9 (Against the Gnostics) - primary-source polemic rejecting the Gnostic multiplication of hypostases as a distortion of procession.
- R. T. Wallis & J. Bregman (eds.), Neoplatonism and Gnosticism (1992) - collection devoted to exactly this contested correspondence.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-08 · proposed **homology** · borderline
**neoplatonism / mystical_union** (“henosis; beholder one with beheld”, n=279)  ↔  **christian_mysticism / mystical_union** (“union with the Uncreated; vanishing in God”, n=253)

**Claim:** Plotinian henosis and Christian unio mystica: the same terminal state of undifferenced union, or two different moves - identity-union versus a love-union that preserves the creature?

**Rationale:** Plotinus describes a state where 'there were not two' and even the self is suspended; Eckhart (citing Dionysius) has the soul lose 'its own distinctiveness' and vanish in God like dawn-red in the sun - historically fed by Plotinus via Dionysius, and as close to identity-union as Christian mysticism gets. But mainstream Christian mysticism, and Eckhart's own defenses, re-inscribe the Creator/creature distinction and make grace the means, which Plotinus neither has nor needs. Whether that difference is doctrinal gloss over the same experience-structure or a genuinely different conceptual move is exactly what a gold set should force a decision on.

**Primary evidence:**
> There were not two; beholder was one with beheld; it was not a vision compassed but a unity apprehended. The man formed by this mingling with the Supreme must- if he only remember- carry its image impressed upon him: he is become the Unity, nothing within him or without inducing any diversity; no […]
> — `neoplatonism/plotinus-select-works-index/chunks/751.toml`
> St Dionysius commenting on the text, "Know ye not that all run, but one receiveth the prize?" says "this running is nothing else than a turning away from all creatures and being united to the Uncreated." When the soul gets to this point, it loses its own distinctiveness, and vanishes in God as the […]
> — `christian_mysticism/eckhart-sermons-field/chunks/019.toml`

**Secondary citations:**
- Bernard McGinn, The Foundations of Mysticism (1991), Appendix on theoretical foundations - surveys the debate over whether unio mystica entails identity or union-in-distinction.
- Bernard McGinn, The Mystical Thought of Meister Eckhart (2001), ch. on the union of indistinction - Eckhart's unitas indistinctionis as the limit case bridging Plotinian henosis and Christian union.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-09 · proposed **false_friend** · borderline
**neoplatonism / gnosis_direct_knowledge** (“knowledge of the Principle by becoming one”, n=280)  ↔  **gnosticism / gnosis_direct_knowledge** (“gnosis; knowing yourselves as sons of the living father”, n=199)

**Claim:** Both corpora carry the tag 'salvation through direct knowledge,' but Plotinian knowing of the One is a self-wrought dialectical and ascetic becoming, while Thomas's gnosis is recognition of one's divine origin delivered through a revealer's hidden sayings - a shared label over different epistemic machineries.

**Rationale:** In Plotinus the knower ascends by purification and self-unification ('from many, we must become one'); there is no revealer, no elect, and the terminus is a presence beyond knowledge available in principle to any soul that does the work. In Thomas, knowing yourself means discovering you are a son of the living Father, and the discovery is triggered by Jesus's words; salvation hangs on receiving a disclosure. Borderline rather than easy: both make knowledge (not faith or works) soteriologically decisive and both interiorize the divine - which is why Plotinus bothered to write against the Gnostics at all.

**Primary evidence:**
> Cleared of all evil in our intention towards The Good, we must ascend to the Principle within ourselves; from many, we must become one; only so do we attain to knowledge of that which is Principle and Unity. We shape ourselves into Intellectual-Principle; we make over our soul in trust to […]
> — `neoplatonism/plotinus-select-works-index/chunks/740.toml`
> Rather, the kingdom is inside of you, and it is outside of you. When you come to know yourselves, then you will become known, and you will realize that it is you who are the sons of the living father. But if you will not know yourselves, you dwell in poverty and it is you who are that poverty.
> — `gnosticism/gospel-of-thomas/chunks/003.toml`

**Secondary citations:**
- A. H. Armstrong, 'Gnosis and Greek Philosophy', in B. Aland (ed.), Gnosis: Festschrift fuer Hans Jonas (1978) - distinguishes philosophic knowledge won by ascesis and dialectic from revealed, saving Gnostic gnosis.
- Plotinus, Ennead II.9 (Against the Gnostics) - rejects claims to salvation by special revealed knowledge for an elect while defending contemplative ascent.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-10 · proposed **false_friend** · easy
**neoplatonism / theurgy** (“theurgy; ineffable works and inexplicable symbols”, n=99)  ↔  **western_esoteric / theurgy** (“the Great Work; Universal Magical Agent”, n=82)

**Claim:** The occult revival claimed the word and pedigree of Neoplatonic theurgy, but Levi's magic is will-powered operation on the Universal Agent, while Iamblichus explicitly denies that any human conception effects the union - the gods act; shared vocabulary, inverted agency.

**Rationale:** Iamblichus is categorical: 'a conception of the mind does not conjoin theurgists with the Gods'; efficacy comes from the divine side through rites and symbols the gods themselves instituted, which is why theoretical philosophy cannot substitute for them. Levi grounds the Great Work in 'the creation of man by himself' and the emancipated will's 'full power over the Universal Magical Agent' - an anthropocentric, Promethean mechanism. A translation-level matcher linking 'theurgy/high magic' across these corpora would join two opposite accounts of where the power sits.

**Primary evidence:**
> For a conception of the mind does not conjoin theurgists with the Gods; since, if this were the case, what would hinder those who philosophize theoretically, from having a theurgic union with the Gods? Now, however, in reality, this is not the case. For the perfect efficacy of ineffable works, […]
> — `neoplatonism/iamblichus-on-the-mysteries/chunks/044.toml`
> THE Great Work is, before all things, the creation of man by himself, that is to say, the full and entire conquest of his faculties and his future; it is especially the perfect emancipation of his will, assuring him universal dominion over Azoth and the domain of Magnesia, in other words, full […]
> — `western_esoteric/transcendental-magic-doctrine/chunks/060.toml`

**Secondary citations:**
- Gregory Shaw, Theurgy and the Soul: The Neoplatonism of Iamblichus (1995) - theurgy as receptivity to divine energeia through god-given symbols, explicitly not a human technique of compulsion.
- Christopher McIntosh, Eliphas Levi and the French Occult Revival (1972) - Levi's magic rests on the trained human will and imagination directing the astral agent.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-11 · proposed **false_friend** · easy
**gnosticism / pleroma** (“the fullness (pleroma)”, n=15)  ↔  **neoplatonism / monad** (“The One; the all-transcending”, n=373)

**Claim:** A lexical matcher pairing each tradition's 'supreme divine realm' would link the Pleroma with the One, but the Pleroma is an articulated plurality of aeons and attributes while the One excludes all multiplicity on principle.

**Rationale:** Philip's fullness is a populated interiority - the innermost place containing the divine totality - and Gnostic pleromatology enumerates its contents in syzygies. Plotinus's One 'is in truth beyond all statement,' and to make it knowable or internally articulated is precisely to 'make it a manifold,' i.e. to demote it. Comparative scholarship aligns the Pleroma with the noetic cosmos (Intellect, the second hypostasis), not the One: equating the two supreme terms mistakes one ontological level for another.

**Primary evidence:**
> He said, "My father who is in secret." He said, "Go into the chamber and shut the door behind you, and pray to your father who is in secret," the one who is innermost. But what is within them all is the fullness. Beyond it there is nothing inside. This is the place they call "the uppermost."
> — `gnosticism/gospel-of-philip/chunks/007.toml`
> Thus The One is in truth beyond all statement: any affirmation is of a thing; but the all-transcending, resting above even the most august divine Mind, possesses alone of all true being, and is not a thing among things; we can give it no name because that would imply predication ... If we make it […]
> — `neoplatonism/plotinus-select-works-index/chunks/469.toml`

**Secondary citations:**
- John Dillon, 'Pleroma and Noetic Cosmos: A Comparative Study', in R. T. Wallis & J. Bregman (eds.), Neoplatonism and Gnosticism (1992) - argues the Gnostic Pleroma corresponds structurally to the Neoplatonic noetic cosmos (Intellect), not to the One.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-12 · proposed **false_friend** · borderline
**gnosticism / divine_sparks** (“light within a man of light”, n=26)  ↔  **neoplatonism / divine_sparks** (“the undescended soul; not sunk entire”, n=61)

**Claim:** Both corpora assert an uncorrupted divine element in the human being, but the Gnostic light is a trapped fragment awaiting rescue by an external call, while Plotinus's higher soul never fell and needs only redirected attention - same tag, different soteriological mechanics.

**Rationale:** The Gnostic spark is embedded in a hostile cosmos whose rulers block ascent, so liberation requires a transmundane messenger; the spark can fail to shine ('if he does not shine, he is darkness'). Plotinus's undescended phase is 'continuously in the Intellectual Realm' - never in jeopardy, only occluded when the lower phase holds mastery - so salvation collapses into attention. Borderline because scholarship reads the undescended soul precisely as Plotinus's rival answer to the same problem, and later Platonists rejected the doctrine as conceding too much; the structural proximity is real.

**Primary evidence:**
> He said to them, "Whoever has ears, let him hear. There is light within a man of light, and he lights up the whole world. If he does not shine, he is darkness."
> — `gnosticism/gospel-of-thomas/chunks/024.toml`
> even our human soul has not sunk entire; something of it is continuously in the Intellectual Realm, though if that part, which is in this sphere of sense, hold the mastery, or rather be mastered here and troubled, it keeps us blind to what the upper phase holds in contemplation.
> — `neoplatonism/plotinus-select-works-index/chunks/431.toml`

**Secondary citations:**
- Jean-Marc Narbonne, Plotinus in Dialogue with the Gnostics (2011) - reads the undescended soul as Plotinus's counterpart and rival to the Gnostic pneuma-spark.
- Hans Jonas, The Gnostic Religion (1958), ch. 3 - the spark/pneuma requires awakening by the call from without, unlike philosophic self-recovery.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-13 · proposed **false_friend** · borderline
**hermeticism / theosis_deification** (“thou hast been born a God, Son of the One”, n=22)  ↔  **christian_mysticism / theosis_deification** (“being deified and united (theosis)”, n=170)

**Claim:** CH XIII's rebirth as a god and Christian theosis share the translation term 'deification,' but Hermetic rebirth is recovered essential divinity completed in gnosis, while Dionysian deification is a granted, participatory assimilation that never erases the creature.

**Rationale:** In CH XIII the initiate, once the ten Powers displace the twelve torments, simply is 'born a God, Son of the One' - deification is the recognition of what man essentially is, achieved within the initiatory dialogue. Dionysius's deification is 'according to their powers,' through the ceasing of natural activities, toward a Light that still 'surpasseth Deity' - asymptotic participation by grace, not recovered identity. Borderline because patristic theosis vocabulary demonstrably absorbed Hellenistic deification language, and both are staged transformations of the whole person; a geometry might legitimately see either one shared move or two.

**Primary evidence:**
> The natural body which our sense perceives is far removed from this essential birth. The first must be dissolved, the last can never be; the first must die, the last death cannot touch. Dost thou not know thou hast been born a God, Son of the One, even as I myself?
> — `hermeticism/corpus-hermeticum-13/chunks/004.toml`
> entering (according to their powers) unto such states of union and being deified and united, through the ceasing of their natural activities, unto the Light Which surpasseth Deity, can find no more fitting method to celebrate its praises than to deny It every manner of Attribute.
> — `christian_mysticism/dionysius-divine-names-1/chunks/007.toml`

**Secondary citations:**
- Norman Russell, The Doctrine of Deification in the Greek Patristic Tradition (2004), ch. 1 - distinguishes Christian participatory deification by grace from Hellenistic and Hermetic self-deification through knowledge.
- A.-J. Festugiere, La Revelation d'Hermes Trismegiste, vol. IV (1954) - analysis of CH XIII rebirth as deifying gnosis (citation uncertain as to section).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-14 · proposed **false_friend** · borderline
**platonism / body_as_obstacle** (“the soul viewing existence through the bars of a prison”, n=92)  ↔  **gnosticism / body_as_obstacle** (“wealth dwelling in poverty; wretched body”, n=151)

**Claim:** Plato's body-as-prison and Thomas's wretched flesh read as the same somatic pessimism at translation level, but Plato's obstacle sits inside a good, ordered, divine cosmos, whereas the Gnostic body indexes an anticosmic verdict on the world itself.

**Rationale:** In the Phaedo the prison is a moral-epistemic condition remediable by philosophy, and the cosmos remains divine handiwork worth contemplating; the fault is in the soul's entanglement, not in being as such. In Thomas the spirit's residence in flesh is an ontological scandal ('a wonder of wonders') within a scheme that devalues the world as such. Jonas made this the canonical contrast between Greek cosmos-piety and Gnostic anticosmism - yet the practical overlap (asceticism, distrust of the senses, soma-sema imagery the Gnostics themselves borrowed) is strong enough that Plotinus's anti-Gnostic polemic had to fight for the distinction; genuinely contestable.

**Primary evidence:**
> The lovers of knowledge are conscious that their souls, when philosophy receives them, are simply fastened and glued to their bodies: the soul is only able to view existence through the bars of a prison, and not in her own nature; she is wallowing in the mire of all ignorance; and philosophy, […]
> — `platonism/plato-phaedo/chunks/019.toml`
> Jesus said, "If the flesh came into being because of spirit, it is a wonder. But if spirit came into being because of the body, it is a wonder of wonders. Indeed, I am amazed at how this great wealth has made its home in this poverty."
> — `gnosticism/gospel-of-thomas/chunks/029.toml`
> Jesus said, "Wretched is the body that is dependant upon a body, and wretched is the soul that is dependent on these two."
> — `gnosticism/gospel-of-thomas/chunks/087.toml`

**Secondary citations:**
- Hans Jonas, The Gnostic Religion (2nd ed. 1963), essay 'The Cosmos in Greek and Gnostic Evaluation' - contrasts Greek cosmos-piety with Gnostic anticosmic dualism even where body-negative imagery is shared.
- Plotinus, Ennead II.9.17-18 - primary-source insistence that despising the body must not become contempt for the beautiful cosmos, drawn against the Gnostics.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-15 · proposed **false_friend** · easy
**platonism / anamnesis** (“knowledge is recollection”, n=27)  ↔  **gnosticism / gnosis_direct_knowledge** (“gnosis as sobering from intoxication”, n=199)

**Claim:** Platonic anamnesis and Gnostic awakening share the surface schema 'saving knowledge = recovering what is already yours' with matching sleep/forgetting imagery, but recollection is elicited by dialectic from every rational soul, while the Gnostic must be sobered by an external revealer against a stupefying world.

**Rationale:** In the Phaedo recollection is a structural property of all learning, demonstrable from ordinary perception of equals; no elect, no call, no cosmic adversary - only questioning. In Thomas humanity is 'intoxicated' and 'blind in their hearts,' and the shaking-off of the wine becomes possible because the revealer took his place in the world; knowledge arrives as address, not maieutics. The shared forgetting/remembering and drunkenness/sobriety imagery is exactly what a translation-level matcher would seize on, while the mechanisms - innate latency activated by reason versus alienated origin disclosed by revelation - are held apart in the scholarship.

**Primary evidence:**
> I would ask you whether you may not agree with me when you look at the matter in another way; I mean, if you are still incredulous as to whether knowledge is recollection. ... We should agree, if I am not mistaken, that what a man recollects he must have known at some previous time.
> — `platonism/plato-phaedo/chunks/012.toml`
> I found all of them intoxicated; I found none of them thirsty. And my soul became afflicted for the sons of men, because they are blind in their hearts and do not have sight; for empty they came into the world, and empty too they seek to leave the world. But for the moment they are intoxicated. […]
> — `gnosticism/gospel-of-thomas/chunks/028.toml`

**Secondary citations:**
- Hans Jonas, The Gnostic Religion (1958), ch. 3 (symbolism of the call, sleep, intoxication, awakening) - gnosis comes from without through a messenger, distinguished from philosophic reminiscence.
- Kurt Rudolph, Gnosis: The Nature and History of Gnosticism (1983), section on the concept of gnosis - revealed saving knowledge for the gnostic versus rational recollection in the Platonic school.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### A-16 · proposed **false_friend** · borderline
**gnosticism / divine_hiddenness** (“the light of the father concealed in images”, n=98)  ↔  **christian_mysticism / divine_hiddenness** (“super-essential Darkness; the hidden Godhead”, n=183)

**Claim:** Thomas's concealed Father and Dionysius's super-essential Darkness both say God is hidden beyond all images and light, but Dionysian hiddenness belongs to the Cause of the very beings that veil him, while Gnostic hiddenness marks the Father's otherness from the world and its makers.

**Rationale:** For Dionysius the darkness is epistemic: the Cause exceeds every cognition, yet all things participate in and proportionally reveal it - hiddenness and manifestation are two sides of one causal relation. In the Gnostic frame concealment tends toward ontological alienation: the light in the images stays hidden because the imaged world is not the Father's workmanship in the full sense, and knowing him requires extraction from it. Borderline because Thomas is the least demiurgical of Gnostic texts - its hidden/manifest dialectic can be read as pure apophatic epistemology, and Williams's critique of blanket 'anticosmic' readings cuts in its favor; real arguments exist for both verdicts.

**Primary evidence:**
> Jesus said, "The images are manifest to man, but the light in them remains concealed in the image of the light of the father. He will become manifest, but his image will remain concealed by his light."
> — `gnosticism/gospel-of-thomas/chunks/083.toml`
> in order that we may attain a naked knowledge of that Unknowing which in all existent things is enwrapped by all objects of knowledge ... and that we may begin to see that super-essential Darkness which is hidden by all the light that is in existent things.
> — `christian_mysticism/dionysius-mystical-theology/chunks/004.toml`

**Secondary citations:**
- Hans Jonas, The Gnostic Religion (1958), ch. 2 - the hidden, alien God as constitutively other than the cosmos and its rulers.
- Michael A. Williams, Rethinking "Gnosticism": An Argument for Dismantling a Dubious Category (1996) - challenges blanket anticosmic readings, sustaining the borderline status of Thomas's hiddenness language.
- Bernard McGinn, The Foundations of Mysticism (1991), section on Dionysius - divine darkness as the excess of the Cause knowable through and beyond its participations.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 


## Lane B — East-West pairs

### B-01 · proposed **false_friend** · borderline
**taoism / wu_wei** (“wu-wei ('manages affairs without doing anything')”, n=109)  ↔  **christian_mysticism / detachment_gelassenheit** (“Gelassenheit / self-renunciation (Field renders Abgeschiedenheit as 'sanctification')”, n=74)

**Claim:** Both traditions prize an 'effortless letting-go' of striving, so a translation-level matcher merges wu-wei with Eckhart's Gelassenheit, but the release is aimed at different objects.

**Rationale:** Wu-wei is non-coercive alignment with the immanent spontaneity of the Dao: the sage acts without claiming ownership and results follow naturally, with no divine will anywhere in the picture. Eckhart's released man surrenders his own will into God's will — the letting-go is theocentric obedience culminating in God working in the soul, not a technique of frictionless efficacy in the natural order. The perennialist merge erases the difference between a naturalistic action-theory and a doctrine of grace; still borderline because serious scholarship has defended the structural parallel of non-willing.

**Primary evidence:**
> Therefore the sage manages affairs without doing anything, and conveys his instructions without the use of speech. All things spring up, and there is not one which declines to show itself; they grow, and there is no claim made for their ownership; they go through their processes, and there is no […]
> — `taoism/tao-te-ching-legge/chunks/002.toml`
> The man who abides in the will of God wills nothing else than what God is, and what He wills. If he were ill he would not wish to be well. If he really abides in God's will, all pain is to him a joy, all complication, simple: yea, even the pains of hell would be a joy to him. He is free and gone […]
> — `christian_mysticism/eckhart-sermons-field/chunks/012.toml`

**Secondary citations:**
- R.C. Zaehner, Mysticism Sacred and Profane (1957), chs. 8-9 — argues theistic surrender-of-will mysticism differs in kind from nature/monistic mysticism, against the perennialist merge
- Reiner Schürmann, Meister Eckhart: Mystic and Philosopher (1978), appendix comparing Eckhart's releasement with Zen/Eastern non-willing — defends a structural parallel of Gelassenheit with East Asian letting-be (citation uncertain)

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-02 · proposed **false_friend** · borderline
**taoism / monad** (“'The One' (Legge's rendering, TTC 14)”, n=21)  ↔  **neoplatonism / monad** (“the One / first principle”, n=373)

**Claim:** Legge's Victorian rendering literally capitalizes 'The One' for the Dao, so the shared tag looks like a homology with Plotinus's One, but it is largely a translation artifact.

**Rationale:** In TTC 14 'The One' names the blending of three failed perceptual designations — an admission that the Dao resists description — whereas Plotinus's One is a rigorous metaphysical first principle, absolutely simple, transcending its products, reached by dialectical ascent through the hypostases. The Dao is an immanent generative course ('Mother of all things') that things follow, not a hyperousios source of a graded emanation hierarchy; sinologists have argued dao is not a metaphysical absolute at all. Borderline because the generative-source language (TTC 42: 'The Tao produced One') gives the comparativist a real foothold.

**Primary evidence:**
> We look at it, and we do not see it, and we name it 'the Equable.' We listen to it, and we do not hear it, and we name it 'the Inaudible.' We try to grasp it, and do not get hold of it, and we name it 'the Subtle.' With these three qualities, it cannot be made the subject of description; and hence […]
> — `taoism/tao-te-ching-legge/chunks/014.toml`
> that higher therefore [as above the ordering of reason] is without part or interval [implied by reasoned arrangement], is a one- all Reason-Principle, one number, a One greater than its product, more powerful, having no higher or better. Thus the Supreme can derive neither its being nor the quality […]
> — `neoplatonism/plotinus-select-works-index/chunks/732.toml`

**Secondary citations:**
- Chad Hansen, A Daoist Theory of Chinese Thought (1992), ch. 6 — argues 'dao' is prescriptive discourse-guidance, not a monistic metaphysical entity, and that One-Absolute readings are Western impositions
- J.J. Clarke, The Tao of the West (2000), ch. 3 — documents how missionary and Victorian translators (Legge included) assimilated the Dao to Western metaphysical and theological absolutes

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-03 · proposed **false_friend** · borderline
**buddhism / sunyata_emptiness** (“emptiness (sunyata)”, n=42)  ↔  **christian_mysticism / apophatic_theology** (“the divine Darkness / via negativa”, n=173)

**Claim:** Both discourses negate every predicate ('no form, no perception...' / 'neither being nor understanding'), so a lexical matcher fuses sunyata with Dionysian negative theology, but one negates the self-nature of phenomena while the other safeguards a super-essential God.

**Rationale:** The Heart Sutra's negations deny independent self-nature to all dharmas, including the path and nirvana itself; there is no transcendent referent that the negations protect. Dionysius's negations are instrumental: they strip concepts precisely to drive the soul upward into union with a superabundant divine cause 'which exceedeth all existence' — negation in service of a positive transcendence. Perennialists read both as one 'nothingness'; the Katz line insists the negations do opposite jobs. Borderline because Abe, Suzuki and the kenosis-sunyata literature seriously defend convergence.

**Primary evidence:**
> 'O S âriputra,' he said, 'form here is emptiness, and emptiness indeed is form. Emptiness is not different from form, form is not different from emptiness. What is form that is emptiness, what is emptiness that is form.' ... 'There is no knowledge, no ignorance, no destruction of knowledge, no […]
> — `buddhism/heart-sutra-smaller/chunks/001.toml`
> thou strain (so far as thou mayest) towards an union with Him whom neither being nor understanding can contain. ... thou shalt in pureness cast all things aside, and be released from all, and so shalt be led upwards to the Ray of that divine Darkness which exceedeth all existence.
> — `christian_mysticism/dionysius-mystical-theology/chunks/001.toml`

**Secondary citations:**
- Steven T. Katz, 'Language, Epistemology, and Mysticism,' in Mysticism and Philosophical Analysis (1978) — argues mystical 'nothingness' claims are tradition-constituted and non-identical across Buddhist and Christian contexts
- Masao Abe, 'Kenotic God and Dynamic Sunyata,' in The Emptying God, ed. Cobb & Ives (1990) — the strongest modern defense that sunyata and Christian self-emptying/apophasis genuinely converge

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-04 · proposed **false_friend** · easy · ⚠ DUP-1
**buddhism / soul_migration** (“'a course of many births' (punabbhava)”, n=13)  ↔  **platonism / soul_migration** (“'imprisoned in another body' (metempsychosis)”, n=24)

**Claim:** Both texts describe moral character driving repeated embodiment, so the shared soul_migration tag looks like one doctrine, but Platonic metempsychosis moves an immortal soul-substance while Buddhist rebirth explicitly proceeds without any transmigrating self.

**Rationale:** In the Phaedo an imperishable psyche, weighed down by its habits, is literally 'imprisoned in another body' — the same entity persists across incarnations and can be purified into disembodied divinity. The Dhammapada's wanderer through many births culminates in seeing the 'maker of the tabernacle' and dismantling him: liberation is the ending of the constructive process, not the release of a soul, and the anatta doctrine denies exactly the substance Plato requires. This is the classic near-miss where translation by 'reincarnation/transmigration' wrongly merges opposite anthropologies.

**Primary evidence:**
> Looking for the maker of this tabernacle, I shall have to run through a course of many births, so long as I do not find (him); and painful is birth again and again.
> — `buddhism/dhammapada-chapter-11/chunks/001.toml`
> and they continue to wander until the desire which haunts them is satisfied and they are imprisoned in another body. And they may be supposed to be fixed in the same natures which they had in their former life. ... I mean to say that men who have followed after gluttony, and wantonness, and […]
> — `platonism/plato-phaedo/chunks/018.toml`

**Secondary citations:**
- Steven Collins, Selfless Persons: Imagery and Thought in Theravada Buddhism (1982), ch. on rebirth — shows how Buddhist rebirth is theorized through dependent origination precisely without a transmigrating self
- Thomas McEvilley, The Shape of Ancient Thought (2002), chs. on reincarnation — presses the Greek-Indian parallel, illustrating the surface trap a matcher would fall into

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-05 · proposed **homology** · borderline
**hinduism / unity_of_being** (“'sees the self abiding in all beings' (Brahman-atman)”, n=24)  ↔  **neoplatonism / mystical_union** (“'centre coincides with centre' (henosis)”, n=279)

**Claim:** The Gita's realization that the inmost self is identical with the one reality pervading all beings corresponds to Plotinus's henosis, where the purified self merges with the One — a correspondence seriously defended in comparative scholarship since the 19th century.

**Rationale:** Both describe a disciplined interiorization (yoga of abstraction / Plotinian withdrawal) that terminates in a state where subject-object duality lapses and the practitioner's deepest self is found continuous with the ultimate principle; the structural move — liberation as recognition of prior identity rather than acquisition — is the same. Borderline because Plotinus insists the One is beyond the self and even beyond being (the soul is 'merged', not eternally identical as in tat tvam asi), and the Gita frames the unity theistically through Krishna; Zaehner used exactly this pair to split monistic from theistic mysticism.

**Primary evidence:**
> He who has devoted his self to abstraction, by devotion, looking alike on everything, sees the self abiding in all beings, and all beings in the self. To him who sees me in everything, and everything in me, I am never lost, and he is not lost to me.
> — `hinduism/bhagavad-gita-chapter-06/chunks/002.toml`
> The man is changed, no longer himself nor self-belonging; he is merged with the Supreme, sunken into it, one with it: centre coincides with centre, for on this higher plane things that touch at all are one; only in separation is there duality; by our holding away, the Supreme is set outside.
> — `neoplatonism/plotinus-select-works-index/chunks/750.toml`

**Secondary citations:**
- J.F. Staal, Advaita and Neoplatonism: A Critical Study in Comparative Philosophy (Madras, 1961) — systematic defense and critique of the Vedanta-Plotinus correspondence
- A.H. Armstrong, 'Plotinus and India,' Classical Quarterly 30 (1936) — argues the resemblances do not require influence and flags the differences in the doctrine of self

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-06 · proposed **homology** · borderline · ⚠ CONFLICT-1
**sufism / fana_annihilation** (“'annihilated' (fana)”, n=23)  ↔  **christian_mysticism / fana_annihilation** (“'loses its own distinctiveness, and vanishes in God'”, n=37)

**Claim:** The shared fana_annihilation tag marks a genuine correspondence: both Rumi and Eckhart describe the ego extinguished in God under the same image — a lesser light lost in the sun — while the person persists as God's act.

**Rationale:** The conceptual move matches beyond vocabulary: in both, the separate self is not destroyed but out-shone, its agency replaced by divine agency (Rumi's star lost when the sun rises; Eckhart's dawn-glow vanishing in the sun), and both guard against reading this as simple substantial identity (baqa 'subsistence after annihilation'; Eckhart's soul remaining creature). Borderline because the metaphysical frames differ — Sufi fana operates inside a strict creator-creature theism, while Eckhart grounds union in an uncreated ground of the soul that Islamic orthodoxy would refuse — so a skeptic can still argue the moves diverge at the ontology.

**Primary evidence:**
> If you had been Zaid, you too would have been lost, As a star is lost when tho sun shines on it; For then you see no trace or sign of it, No place or track of it in tho milky way. Our senses and our endless discourses Are annihilated in the light of the knowledge of our King.
> — `sufism/masnavi-book-1/chunks/034.toml`
> When the soul gets to this point, it loses its own distinctiveness, and vanishes in God as the crimson of sunrise disappears in the sun. To this goal only pure sanctification can arrive.
> — `christian_mysticism/eckhart-sermons-field/chunks/019.toml`

**Secondary citations:**
- Reza Shah-Kazemi, Paths to Transcendence: According to Shankara, Ibn Arabi, and Meister Eckhart (2006) — sustained argument that Sufi fana and Eckhartian self-naughting are structurally the same transcendence of ego
- Michael Sells, Mystical Languages of Unsaying (1994) — treats Eckhart and Ibn Arabi within one grammar of apophatic self-effacement while cataloguing their doctrinal differences

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-07 · proposed **false_friend** · borderline
**taoism / divine_hiddenness** (“the nameless, enduring Tao”, n=38)  ↔  **jewish_mysticism / ein_sof** (“'Ain Soph, the infinite and limitless one'”, n=15)

**Claim:** Perennialist readers merge the nameless Tao with the kabbalistic Ein Sof as one 'hidden infinite Ground beyond names,' but the hiddenness works differently: namelessness of an immanent course versus concealment of a theistic infinite prior to emanation.

**Rationale:** The Tao's hiddenness is linguistic-pragmatic — any named dao fails to be the constant dao, yet the Tao itself is maximally present, the 'Mother of all things' operating in everything. Ein Sof's concealment is ontological and theistic: a limitless Deity in 'negative existence' who must proceed into positive manifestation through the sefirot, within a covenantal, Torah-bound frame where the hidden God is still the personal God of Israel. The trap is the shared 'unknowable absolute' register; the moves differ on whether the hidden is a God who reveals himself in stages or a way that was never a someone. Borderline because both do ground a cosmogony in the unnameable.

**Primary evidence:**
> The Tao that can be trodden is not the enduring and unchanging Tao. The name that can be named is not the enduring and unchanging name. (Conceived of as) having no name, it is the Originator of heaven and earth; (conceived of as) having a name, it is the Mother of all things.
> — `taoism/tao-te-ching-legge/chunks/001.toml`
> This and the immediately following sections are supposed to trace the gradual development of the Deity from negative into positive existence; the text is here describing the time when the Deity was just commencing His manifestation from His primal negative form. ... Until that head (which is […]
> — `jewish_mysticism/kabbalah-unveiled-intro/chunks/001.toml`

**Secondary citations:**
- Gershom Scholem, Major Trends in Jewish Mysticism (1941), First Lecture — insists Ein Sof belongs to a specifically theistic emanation-scheme inseparable from Torah and cannot be detached into a generic hidden absolute
- Aldous Huxley, The Perennial Philosophy (1945) — canonical example of the merge, treating Tao and the kabbalistic Godhead as names for one 'divine Ground' (citation uncertain)

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-08 · proposed **homology** · borderline
**taoism / return_to_source** (“'returning to their root' (fu/gui gen)”, n=34)  ↔  **neoplatonism / return_to_source** (“'flight to the beloved Fatherland' (epistrophe)”, n=278)

**Claim:** Both traditions make 'return' the fundamental soteriological vector — things and souls complete themselves by reverting to their source in stillness — a correspondence of conceptual move, not just shared metaphor.

**Rationale:** TTC 16 grounds practice (emptiness, stillness) in a cosmological law that all things return to their root, and knowing this return is the sage's wisdom; Plotinus grounds practice (closing the eyes, turning inward) in the soul's epistrophe to the Father it came from. In both, return is achieved by subtraction and quieting rather than acquisition, and the terminus is the unchanging origin. The FF argument is real — Taoist return is a rhythmic pattern all things undergo anyway, while Plotinian return is a vertical ascent only souls make against the pull of matter — which is what makes this borderline rather than easy.

**Primary evidence:**
> All things alike go through their processes of activity, and (then) we see them return (to their original state). When things (in the vegetable world) have displayed their luxuriant growth, we see each of them return to its root. This returning to their root is what we call the state of stillness; […]
> — `taoism/tao-te-ching-legge/chunks/016.toml`
> The Fatherland to us is There whence we have come, and There is The Father. What then is our course, what the manner of our flight? This is not a journey for the feet; the feet bring us only from land to land; nor need you think of coach or ship to carry you away; all this order of things you must […]
> — `neoplatonism/plotinus-select-works-index/chunks/063.toml`

**Secondary citations:**
- Harold D. Roth, Original Tao: Inward Training and the Foundations of Taoist Mysticism (1999) — reads early Daoist practice as an apophatic-contemplative return to the Way, explicitly comparable with Western mystical typologies
- J.J. Clarke, The Tao of the West (2000) — surveys scholarly comparisons of Daoist reversion with Neoplatonic procession-and-return schemes (citation uncertain as to specific chapter)

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-09 · proposed **false_friend** · easy
**buddhism / kingdom_within** (“'Self is the lord of self'”, n=32)  ↔  **gnosticism / kingdom_within** (“'the kingdom is inside of you'”, n=107)

**Claim:** Both texts relocate salvation inside the person and away from external authority, so the shared kingdom_within tag invites merging — but Thomas grounds interiority in a divine sonship the Dhammapada's anatta doctrine denies.

**Rationale:** Gospel of Thomas 3 makes self-knowledge the discovery of a substantial divine identity: knowing yourselves reveals you are 'sons of the living father', consubstantial with the hidden God. The Dhammapada's interiority is ethical-practical reflexivity — no one can purify another, the 'self' that is lord of self is a reflexive pronoun of self-mastery, and the tradition explicitly refuses any indwelling divine essence. The surface trap (Conze himself catalogued Thomas-Buddhist parallels) dissolves at the anthropology: divine spark versus no-self.

**Primary evidence:**
> Self is the lord of self, who else could be the lord? With self well subdued, a man finds a lord such as few can find. ... By oneself the evil is done, by oneself one suffers; by oneself evil is left undone, by oneself one is purified. Purity and impurity belong to oneself, no one can purify […]
> — `buddhism/dhammapada-chapter-12/chunks/001.toml`
> Rather, the kingdom is inside of you, and it is outside of you. When you come to know yourselves, then you will become known, and you will realize that it is you who are the sons of the living father. But if you will not know yourselves, you dwell in poverty and it is you who are that poverty.
> — `gnosticism/gospel-of-thomas/chunks/003.toml`

**Secondary citations:**
- Edward Conze, 'Buddhism and Gnosis,' in The Origins of Gnosticism, ed. U. Bianchi (1967) — catalogues the striking parallels while showing the gnostic pneuma/elect anthropology is incompatible with Buddhist anatta

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-10 · proposed **homology** · borderline
**buddhism / poverty_of_spirit** (“'who calls nothing his own... who is poor'”, n=29)  ↔  **christian_mysticism / poverty_of_spirit** (“'empty of all creature's love'”, n=42)

**Claim:** The shared poverty_of_spirit tag tracks a genuine correspondence: in both, perfection is defined privatively — owning nothing, wanting nothing — with the emptying itself constituting the attainment rather than preparing for it.

**Rationale:** Dhammapada 421's Brahmana calls nothing his own 'before, behind, or between' — dispossession extended to past, future and present identity, not merely goods; Eckhart's detachment likewise converts emptiness directly into plenitude ('to be empty of all creature's love is to be full of God'). The Kyoto-school reading (Ueda) defends this as the same movement of radical non-possession. Borderline because Eckhart's poverty is ordered to being filled by God — an ontological exchange with a divine terminus — while the Buddhist text's poverty terminates in extinction of craving with nothing arriving to fill the vacancy; a contextualist can argue the emptying serves opposite ends.

**Primary evidence:**
> Him I call indeed a Brâhma n a who calls nothing his own, whether it be before, behind, or between, who is poor, and free from the love of the world.
> — `buddhism/dhammapada-chapter-26/chunks/005.toml`
> real sanctification consists in this that the spirit remain as immovable and unaffected by all impact of love or hate, joy or sorrow, honour or shame, as a huge mountain is unstirred by a gentle breeze. ... And thou shouldest know that to be empty of all creature's love is to be full of God, and to […]
> — `christian_mysticism/eckhart-sermons-field/chunks/017.toml`

**Secondary citations:**
- Shizuteru Ueda, 'Nothingness in Meister Eckhart and Zen Buddhism,' in The Buddha Eye, ed. F. Franck (1982) — defends a deep structural correspondence between Eckhart's poverty/detachment and Buddhist non-attachment, while noting Zen radicalizes it beyond Eckhart's God
- D.T. Suzuki, Mysticism: Christian and Buddhist (1957) — the classic (perennialist-leaning) pairing of Eckhart's poverty of spirit with Buddhist emptiness

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-11 · proposed **homology** · easy
**hinduism / living_god** (“'those who worship me with devotion (dwell) in me' (bhakti)”, n=26)  ↔  **christian_mysticism / bhakti** (“'God, of Thy Goodness, give me Thyself'”, n=58)

**Claim:** The Gita's bhakti — loving self-surrender to a personal Lord as itself sufficient for salvation — genuinely corresponds to the devotional mysticism of Julian, where love of a personal, responsive God replaces ritual and merit as the effective path.

**Rationale:** Both texts make the same structural move: the value of any act is relocated from the act to the devotional intention ('whoever with devotion offers me leaf, flower, fruit, water... I accept'), the deity personally indwells and keeps the devotee ('dwell in me, and I too in them' / 'our clothing that for love wrappeth us'), and the relation is explicitly open to the unlearned and lowly. This is mutual-indwelling theistic mysticism preserving the lover-beloved distinction, on both sides — the case comparativists since Zaehner have treated as a real cross-tradition kind, contrasted with monistic union.

**Primary evidence:**
> Whoever with devotion offers me leaf, flower, fruit, water, that, presented with devotion, I accept from him whose self is pure. ... But those who worship me with devotion (dwell) in me , and I too in them.
> — `hinduism/bhagavad-gita-chapter-09/chunks/002.toml`
> I saw that He is to us everything that is good and comfortable for us: He is our clothing that for love wrappeth us, claspeth us, and all encloseth us for tender love, that He may never leave us; being to us all-thing that is good, as to mine understanding. ... God, of Thy Goodness, give me […]
> — `christian_mysticism/julian-revelations/chunks/007.toml`

**Secondary citations:**
- R.C. Zaehner, Mysticism Sacred and Profane (1957), ch. 8 ('Theism versus Monism') — argues the Gita's loving union that preserves the soul-God distinction is genuinely of the same type as Christian devotional mysticism
- R.C. Zaehner, The Bhagavad-Gita, with commentary (1969) — reads Gita bhakti in sustained comparison with Christian mystical theology

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-12 · proposed **false_friend** · easy
**taoism / childlike_innocence** (“'like an infant'”, n=12)  ↔  **christian_mysticism / childlike_innocence** (“'become like children'”, n=16)

**Claim:** Identical imagery — the perfected person as an infant — makes this pair irresistible to a surface matcher, but the Taoist infant is a figure of pre-social vitality and pliancy while the Christian child is a figure of trusting dependence on a Father.

**Rationale:** TTC 55's infant embodies concentrated de: physical invulnerability, soft sinews with firm grasp, harmony of vital breath — a physiological-cosmological ideal of unexpended natural potency, with no note of humility or obedience. Boehme's child 'knows nothing, but clings to the mother': the point is epistemic surrender and death of self-will so that regeneration in Christ can occur — dependence on a person, not conservation of vitality. Shared image, opposite vectors: self-sufficient spontaneity versus creaturely reliance on grace.

**Primary evidence:**
> He who has in himself abundantly the attributes (of the Tao) is like an infant. Poisonous insects will not sting him; fierce beasts will not seize him; birds of prey will not strike him. (The infant's) bones are weak and its sinews soft, but yet its grasp is firm.
> — `taoism/tao-te-ching-legge/chunks/055.toml`
> Christ said, 'Unless you become like children, you will not see the kingdom of God.' ... like a child that knows nothing, but clings (instinctively) to the mother who gave it birth. And thus the will of the Christian must die to its own self-willing and self-assertion, and become like a child in […]
> — `christian_mysticism/life-and-doctrines-boehme/chunks/133.toml`

**Secondary citations:**
- Roger T. Ames and David L. Hall, Dao De Jing: A Philosophical Translation (2003), commentary on ch. 55 — reads the infant as an image of consummate vitality (de) and unmediated responsiveness, not moral innocence or humility (citation uncertain as to exact locus)

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-13 · proposed **homology** · easy
**sufism / separation_from_source** (“the reed-flute torn from its osier bed”, n=13)  ↔  **neoplatonism / separation_from_source** (“'the beloved Fatherland' from which the soul is exiled”, n=96)

**Claim:** Rumi's reed lamenting its severance from the reed-bed and Plotinus's soul yearning for the Fatherland make the same conceptual move — the human condition as exile from a divine origin whose felt pain is itself the engine of return — and the correspondence is underwritten by documented historical transmission.

**Rationale:** In both, longing is diagnostic: the lament of the reed and the homesickness of Odysseus's soul reveal an origin the exile has not ceased to belong to, and the remedy is a non-spatial return ('not a journey for the feet'; the reed's music, not travel). This is homology, not coincidence — Plotinian exile-and-return themes reached Islamic mysticism through the Arabic Plotinus materials (the so-called Theology of Aristotle), so the shared move has an actual filiation as well as a structural match.

**Primary evidence:**
> HEARKEN to the reed-flute, how it complains, Lamenting its banishment from its home: "Ever since they tore me from my osier bed, My plaintive notes have moved men and women to tears. I burst my breast, striving to give vent to sighs, And to express the pangs of my yearning for my home. He who […]
> — `sufism/masnavi-book-1/chunks/001.toml`
> "Let us flee then to the beloved Fatherland": this is the soundest counsel. But what is this flight? How are we to gain the open sea? For Odysseus is surely a parable to us when he commands the flight from the sorceries of Circe or Calypso- not content to linger for all the pleasure offered to his […]
> — `neoplatonism/plotinus-select-works-index/chunks/063.toml`

**Secondary citations:**
- Peter Adamson, The Arabic Plotinus: A Philosophical Study of the Theology of Aristotle (2002) — documents the transmission of Plotinian doctrines of the soul's descent, exile and return into Arabic-Islamic thought, the milieu Sufi metaphysics drew on

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### B-14 · proposed **false_friend** · easy
**buddhism / self_knowledge** (“'never identifies himself with name and form'”, n=43)  ↔  **hermeticism / self_knowledge** (“'he who thus hath learned to know himself'”, n=17)

**Claim:** Both traditions make knowing yourself the hinge of liberation, so the shared self_knowledge tag looks like one soteriology of 'know thyself' — but Hermetic self-knowledge discovers you are essentially God, while Buddhist self-knowledge discovers there is no essential you.

**Rationale:** Corpus Hermeticum I ties salvation to recognizing oneself as constituted of divine Light and Life — 'learn that thou art thyself of Life and Light... thou shalt return again to Life' — an anthropology of consubstantiality with the Father in which knowing the self is knowing God. The Dhammapada's liberating self-knowledge is disidentification: the bhikshu is defined by refusing to identify with name-and-form at all. Same slogan, inverted content: apotheosis of the inner man versus dissolution of the very notion of an inner man. This is the strongest false-friend axis in the East-West cluster — shared 'gnosis of self' register, opposite anthropology.

**Primary evidence:**
> He who never identifies himself with name and form, and does not grieve over what is no more, he indeed is called a Bhikshu.
> — `buddhism/dhammapada-chapter-25/chunks/001.toml`
> And he who thus hath learned to know himself, hath reached that Good which doth transcend abundance; but he who through a love that leads astray, expends his love upon his body - he stays in Darkness wandering, and suffering through his senses things of Death.
> — `hermeticism/corpus-hermeticum-01/chunks/003.toml`
> If then thou learnest that thou art thyself of Life and Light, and that thou [happen'st] to be out of them, thou shalt return again to Life.
> — `hermeticism/corpus-hermeticum-01/chunks/004.toml`

**Secondary citations:**
- Garth Fowden, The Egyptian Hermes (1986), ch. on Hermetic piety — Hermetic gnosis is the recognition of one's essential divinity and consubstantiality with Nous, i.e. self-knowledge as self-deification
- Edward Conze, 'Buddhism and Gnosis,' in The Origins of Gnosticism, ed. U. Bianchi (1967) — contrasts gnostic/Hermetic divine-essence anthropology with the Buddhist denial of a self to be known

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 


## Lane C — Ancient / mythic cluster

### C-01 · proposed **homology** · borderline
**egyptian / funerary_navigation** (“coming forth by day (pert em hru)”, n=365)  ↔  **greek_mystery / funerary_navigation** (“Pluto, Terrestrial Jove, judge of the dead”, n=22)

**Claim:** Both traditions give the dead ritual knowledge/cultic provision that secures safe passage and a better lot in the underworld, a correspondence comparativists have seriously defended (and seriously attacked) since Herodotus equated Orphic and Egyptian rites.

**Rationale:** The Book of the Dead rubric makes possession of the written chapter itself the operative guarantee of free movement after death; the Orphic hymn cultivates the underworld sovereign whose 'decision dread' fixes the fate of the dead and asks him to be propitious to the mystic. The shared move is soteriological insurance for the afterlife acquired in life through esoteric means, not mere shared underworld imagery. Against: Zuntz argued the Greek afterlife-instruction complex is native Pythagorean-Greek and not derived from Egypt; Merkelbach and others revived the Egyptian-derivation case, which is why this is a genuine borderline.

**Primary evidence:**
> If this writing be (2) known [by the deceased] upon earth, and this chapter be done into writing upon [his] coffin, he shall come forth by (3) day in all the forms of existence which he desireth, and he shall enter into [his] place and shall not be rejected.
> — `egyptian/egyptian-book-of-the-dead-index/chunks/151.toml`
> O mighty dæmon, whose decision dread, The future fate determines of the dead,
> — `greek_mystery/orphic-hymns/chunks/057.toml`
> Propitious to thy mystic's works incline, Rejoicing come, for holy rites are thine.
> — `greek_mystery/orphic-hymns/chunks/057.toml`

**Secondary citations:**
- G. Zuntz, Persephone: Three Essays on Religion and Thought in Magna Graecia (1971), Part II — argues the Greek gold-leaf afterlife instructions are Pythagorean-Greek and rejects derivation from the Egyptian Book of the Dead.
- R. Merkelbach, 'Die goldenen Totenpässe: ägyptisch, orphisch, bakchisch', ZPE 128 (1999) — defends genuine Egyptian Totenpass parallels to the Orphic afterlife texts.
- F. Graf & S.I. Johnston, Ritual Texts for the Afterlife (2007), ch. 4 — analyzes Orphic afterlife instruction as initiation-secured navigation of the underworld (citation uncertain on chapter number).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-02 · proposed **homology** · borderline
**norse / world_tree_axis** (“Yggdrasil, the world-ash”, n=15)  ↔  **finnic / world_tree_axis** (“the great oak, 'tree of heaven'”, n=35)

**Claim:** The Norse world-ash and the Kalevala's cosmic oak are both giant trees articulating the vertical structure of the cosmos, a correspondence comparative mythology of the Baltic-Scandinavian contact zone genuinely defends.

**Rationale:** Yggdrasil is the sustaining axis watered from Urth's well, seat of the Norns who allot fate; the Kalevala oak is likewise a 'tree of heaven' whose crown reaches the celestial lights — Harva placed the Finnic great oak squarely within the Finno-Ugric world-tree/world-pillar complex, and Norse-Finnic contact makes shared structure plausible. The counter-argument is real: the Kalevala oak is a calamity that blots out sun and moon and must be felled, an anti-axis whose narrative function (removal of obstruction) inverts Yggdrasil's function (permanent sustaining center). A verdict either way is defensible, which is exactly why it belongs in the gold set.

**Primary evidence:**
> An ash I know, | Yggdrasil its name, With water white | is the great tree wet; Thence come the dews | that fall in the dales, Green by Urth's well | does it ever grow.
> — `norse/poetic-edda-voluspo/chunks/006.toml`
> Kape, daughter of the Ether, Ancient mother of my being, Luonnotar, my nurse and helper, Loan to me the water-forces, Great the powers of the waters; Loan to me the strength of oceans, To upset this mighty oak-tree, To uproot this tree of evil, That again may shine the sunlight, That the moon once […]
> — `finnic/kalevala/chunks/005.toml`

**Secondary citations:**
- Uno Holmberg (Harva), Finno-Ugric, Siberian Mythology (Mythology of All Races vol. IV, 1927), chapters on the World Tree — treats the Finnic great oak within the world-tree/world-pillar complex.
- E.O.G. Turville-Petre, Myth and Religion of the North (1964), ch. on cosmology — Yggdrasil as the axis binding the Norse cosmic levels.
- M. Eliade, Shamanism: Archaic Techniques of Ecstasy (1964), ch. 8 — the World Tree as pan-Eurasian axis mundi (framework now considered over-generalized, which fuels the borderline verdict).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-03 · proposed **homology** · easy
**egyptian / sacred_names** (“'I know thee, I know thy name'”, n=232)  ↔  **finnic / word_power_incantation** (“synty, the sung 'origin of iron'”, n=177)

**Claim:** Both traditions make efficacious power depend on knowing and uttering the true name/origin of the being confronted: the Egyptian dead passes gates by declaring the gatekeepers' names, the Finnish singer masters iron's wound by singing iron's origin.

**Rationale:** This is a correspondence of conceptual move, not vocabulary: in Chapter 145-146 the declared name is itself the credential that compels passage, and in Kalevala runo 9 the recited origin-history (synty) is itself the operative cure — in both, exhaustive knowledge of a thing's identity confers command over it, framed as recitation 'every word in perfect order'. The two are independent (no contact claim), which makes this a clean typological homology rather than a lexical echo, and scholarship on each side describes the mechanism identically. Note the pairing crosses two concept IDs by design.

**Primary evidence:**
> I have made the way, I know thee, I know thy name, I know the name of the goddess who guardeth thee: 'Sword that smiteth at the utterance of its [own] name, the unknown (?) goddess with back-turned face, the overthrower of those who draw nigh unto her flame' is her name.
> — `egyptian/egyptian-book-of-the-dead-index/chunks/172.toml`
> Then the ancient Wainamoinen Thus begins his incantations, Thus begins his magic singing, Of the origin of evil; Every word in perfect order, Makes no effort to remember, Sings the origin of iron, That a bolt he well may fashion, Thus prepare a look for surety, For the wounds the axe has given, […]
> — `finnic/kalevala/chunks/036.toml`

**Secondary citations:**
- E. Hornung, Conceptions of God in Ancient Egypt (1982), ch. on names — the name as an essential component of a being, knowledge of which confers power over it.
- Anna-Leena Siikala, Mythic Images and Shamanism: A Perspective on Kalevala Poetry (FFC 280, 2002) — the synty (origin-song) as the healer's means of mastering the agent that caused the harm.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-04 · proposed **false_friend** · borderline
**norse / cosmogony** (“Ginnungagap and Ymir; Bur's sons lift the land”, n=10)  ↔  **finnic / cosmogony** (“the world-egg on the water-mother's knee”, n=36)

**Claim:** Same concept ID, adjacent cultures, and a matcher will link 'Norse creation' to 'Finnish creation' — but the conceptual moves belong to two distinct cosmogonic types: craftsman-gods constructing a world out of primordial void/giant-matter versus spontaneous world-generation from a broken egg.

**Rationale:** In Voluspo creation is an act of deliberate divine workmanship upon inert pre-existing conditions (and in the wider Eddic corpus, upon Ymir's dismembered body — a type Lincoln treats as inherited Indo-European anthropogonic sacrifice); in the Kalevala the egg fragments transform themselves into heaven and earth with no divine artisan shaping them, a variant of the widespread southern-Eurasian world-egg type. The surface trap (neighboring Baltic cultures, same taxonomy cell, both 'primal waters') is strong, and real Norse-Finnic borrowing in other domains makes the equation tempting. Borderline because contact-influence arguments between Scandinavian and Finnic cosmological poetry do exist, so an adjudicator could defend a weak homology at the 'creation from primal water-chaos' level.

**Primary evidence:**
> Of old was the age | when Ymir lived; Sea nor cool waves | nor sand there were; Earth had not been, | nor heaven above, But a yawning gap, | and grass nowhere. 4. Then Bur's sons lifted | the level land, Mithgarth the mighty | there they made
> — `norse/poetic-edda-voluspo/chunks/003.toml`
> From one half the egg, the lower, Grows the nether vault of Terra: From the upper half remaining, Grows the upper vault of Heaven; From the white part come the moonbeams, From the yellow part the sunshine, From the motley part the starlight, From the dark part grows the cloudage
> — `finnic/kalevala/chunks/002.toml`

**Secondary citations:**
- B. Lincoln, Myth, Cosmos, and Society: Indo-European Themes of Creation and Destruction (1986) — dismemberment cosmogony as a distinct inherited Indo-European type.
- M. Kuusi, K. Bosley & M. Branch, Finnish Folk Poetry: Epic (1977), commentary on the creation songs — the world-egg cosmogony as a separate Eurasian type in the Finnic tradition (citation uncertain on exact pages).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-05 · proposed **false_friend** · easy
**egyptian / eschatological_judgment** (“the Great Balance (weighing of the heart)”, n=57)  ↔  **jewish_mysticism / eschatological_judgment** (“'He cometh with ten thousands of His holy ones to execute judgement'”, n=101)

**Claim:** 'Judgment of the dead' is the shared translation term, but the Egyptian weighing is an individual, immediate, endlessly repeated post-mortem verdict while Enoch's judgment is a one-time collective cosmic assize — the taxonomy's own definition of eschatological judgment ('distinct from personal judgment') splits them.

**Rationale:** Ani's heart is weighed at his own death, the verdict concerns his personal moral ledger, and the cosmos continues unchanged afterward; 1 Enoch 1:9 announces a future theophany in which all flesh is convicted at once and the world-order itself is terminated and restored. A lexical matcher (both scenes have a divine tribunal, accusers, and a registrar deity/scribe motif) will fuse the two, and this is precisely the species of tag-level error the production review flagged. Brandon's old diffusionist claim that Egyptian judgment imagery fed later apocalyptic is the only real counter, and it concerns imagery transmission, not identity of conceptual move.

**Primary evidence:**
> The heart of Osiris hath in very truth been weighed, and his soul hath stood as a witness for him; it hath been found true by trial in the Great Balance. There hath not been found any wickedness in him; he hath not wasted the offerings in the temples; he hath not done harm by his deeds; and he […]
> — `egyptian/egyptian-book-of-the-dead-index/chunks/136.toml`
> And behold! He cometh with ten thousands of ⌈ His ⌉ holy ones To execute judgement upon all, And to destroy ⌈ all ⌉ the ungodly: And to convict all flesh Of all the works ⌈ of their ungodliness ⌉ which they have ungodly committed
> — `jewish_mysticism/enoch-charles-1917/chunks/017.toml`

**Secondary citations:**
- J. Gwyn Griffiths, The Divine Verdict: A Study of Divine Judgement in the Ancient Religions (Brill, 1991) — distinguishes Egypt's immediate individual post-mortem judgment from collective final judgment in Jewish apocalyptic.
- S.G.F. Brandon, The Judgment of the Dead (1967) — the dated diffusionist counter-case that Egyptian judgment ideas influenced later eschatologies.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-06 · proposed **false_friend** · borderline
**greek_mystery / living_god** (“Jove (Zeus), 'first and last'”, n=157)  ↔  **mesopotamian / living_god** (“'Marduk is king!'”, n=48)

**Claim:** The deity-name equation 'supreme king of the gods' (Jove = Marduk) is exactly the interpretatio-style surface trap flagged in production review: the Orphic Zeus is a pantheistic totality containing the cosmos, while Marduk's supremacy is a political kingship conferred by the divine assembly as payment for combat service.

**Rationale:** In the Orphic verses Jove IS fire, night, day, earth, water and sky — divinity as the immanent body of the world, with all things flowing from his mind; in Enuma Elish the gods elect Marduk, hand him regalia, and his rule is contractual and won, an etiology of Babylonian kingship. 'King of the gods' is shared titulature, not a shared conceptual move. Borderline rather than easy because West has argued for genuine Near Eastern influence on Orphic theogonic material (Zeus's swallowing and re-creation of the world echoing Marduk traditions), so a scholar can mount a real transmission-based homology case one level below the name equation. (Note: the Orphic Jove verses are the famous Orphic fragment given in Taylor's translation in the volume's front matter — primary Orphic verse, though embedded in the introductory essay.)

**Primary evidence:**
> In Jove the male and female forms combine, For Jove's a man, and yet a maid divine; Jove the strong basis of the earth contains, And the deep splendour of the starry plains; Jove is the breath of all; Jove's wondrous frame Lives in the rage of ever restless flame; Jove is the sea's strong root, the […]
> — `greek_mystery/orphic-hymns/chunks/011.toml`
> When the gods, his fathers, beheld the fulfillment of his word, They rejoiced, and they did homage unto him, saying, " Marduk is king!" They bestowed upon him the scepter, and the throne, and the ring, They give him an invincible weapony which overwhelmeth the foe.
> — `mesopotamian/enuma-elish/chunks/007.toml`

**Secondary citations:**
- T. Jacobsen, The Treasures of Darkness (1976), ch. 6 — Marduk's kingship in Enuma Elish as assembly-conferred political sovereignty mirroring Mesopotamian institutions.
- M.L. West, The Orphic Poems (1983) — the Orphic Zeus hymn's pantheistic 'Zeus is all' theology, with discussion of possible Near Eastern (Marduk-tradition) antecedents; this is the counter-argument that makes the pair borderline.
- M.L. West, The East Face of Helicon (1997) — Near Eastern influence on Greek succession-myth narrative generally.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-07 · proposed **false_friend** · borderline · ⚠ DUP-2
**egyptian / theosis_deification** (“'I am Osiris, the Lord of eternity'”, n=87)  ↔  **christian_mysticism / theosis_deification** (“'that we also may be His Son'”, n=170)

**Claim:** The Frazerian equation of becoming-Osiris with Christian deification through the dying-and-rising Christ is the classic surface trap: both say 'the dead person is identified with the god who died and lives', but the conceptual moves diverge and the Frazerian category itself is largely rejected scholarship.

**Rationale:** The Egyptian move is ritual-funerary identification: by declaration and rite the deceased assumes Osiris's vindicated status, and Osiris himself remains dead, reconstituted as lord of the Duat, not returned to the living. The Eckhartian move is transformative filiation of the living person into the eternally begotten Son — an ongoing ontological participation, not a post-mortem role assumption. J.Z. Smith's demolition of the 'dying and rising gods' category makes this a canonical false friend; Mettinger's partial rehabilitation of the category (though he stays agnostic on Christian dependence) supplies the genuine argument for the other verdict, hence borderline.

**Primary evidence:**
> I have knit together my bones, I have made myself whole and sound; I have become young once more; I am Osiris, the Lord of eternity.
> — `egyptian/egyptian-book-of-the-dead-index/chunks/189.toml`
> All that the Eternal Father teaches and reveals is His being, His nature, and His Godhead, which He manifests to us in His Son, and teaches us that we are also His Son. All that God worketh and teacheth, He worketh in His Son. All His work is directed to this end that we also may be His Son.
> — `christian_mysticism/eckhart-sermons-field/chunks/011.toml`

**Secondary citations:**
- J.Z. Smith, 'Dying and Rising Gods', Encyclopedia of Religion (1987) — rejects the Frazerian category; Osiris remains among the dead and is not a 'risen' god in the Christian sense.
- J.G. Frazer, The Golden Bough, Part IV: Adonis Attis Osiris — the classic (now rejected) homology this false friend reproduces.
- T.N.D. Mettinger, The Riddle of Resurrection (2001) — partially rehabilitates dying-and-rising deities in the ancient Near East while remaining cautious about Christian dependence; the live counter-argument.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-08 · proposed **false_friend** · borderline
**egyptian / cosmic_dualism** (“the fiend Sebau/Apep held in bondage”, n=83)  ↔  **mesopotamian / cosmic_dualism** (“Tiamat”, n=12)

**Claim:** 'Serpent-combat against chaos' invites the Enuma Elish ↔ Book of the Dead chaoskampf equation flagged in production review, but the Egyptian combat is a cyclical liturgical maintenance performed nightly and forever, while Tiamat's defeat is a unique primordial event that produces the cosmos and Marduk's kingship.

**Rationale:** In the Papyrus of Ani the speaker joins the crew of the solar boat and helps hold the fiend 'in bondage' — the enemy is never finally destroyed, and the ritual participation of every deceased person in the recurring victory is the whole point. In Enuma Elish the combat happens once, ends in dismemberment, and its product is creation itself ('one half of her he stablished as a covering for heaven') plus a kingship etiology. Gunkel's founding comparison lumped these; Ballentine and others show the lumping obscures categorically different functions. Borderline because the shared dragon-combat morphology is real and some scholars still defend a common Near Eastern Chaoskampf complex at the motif level.

**Primary evidence:**
> I am the great god in the boat of the Sun; I have (6) fought for thee. I am one of the gods, those holy princes who make Osiris (7) to be victorious over his enemies on the day of weighing of words. (8) I am thy mediator, O Osiris. I am [one] of the gods (9) born of Nut, those who slay the foes of […]
> — `egyptian/egyptian-book-of-the-dead-index/chunks/147.toml`
> He seized the spear and burst her belly, He severed her inward parts, he pierced her heart. He overcame her and cut off her life; He cast down her body and stood upon it.
> — `mesopotamian/enuma-elish/chunks/008.toml`
> He split her up like a flat fish into two halves; One half of her he stablished as a covering for heaven.
> — `mesopotamian/enuma-elish/chunks/008.toml`

**Secondary citations:**
- H. Gunkel, Schöpfung und Chaos in Urzeit und Endzeit (1895) — the founding chaoskampf comparison this pair tests.
- D.S. Ballentine, The Conflict Myth and the Biblical Tradition (2015) — critiques indiscriminate chaoskampf lumping; conflict myths serve distinct political/theological functions per tradition.
- E. Hornung, Conceptions of God in Ancient Egypt (1982) — Apophis combat as perpetual cyclical maintenance of order, never a final cosmogonic victory.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-09 · proposed **homology** · borderline
**mesopotamian / cosmic_dualism** (“Tiamat and Marduk”, n=12)  ↔  **norse / cosmic_dualism** (“Thor and the Mithgarth serpent”, n=12)

**Claim:** God-versus-cosmic-serpent single combat that decides the fate of the ordered world is a genuine structural correspondence that comparative mythology defends — the storm/champion god meets the world-encircling chaos serpent in decisive battle.

**Rationale:** Both texts stage the same conceptual move: the pantheon's designated champion (not its sovereign father-figure) engages the chaos-serpent in single combat on which cosmic order depends, and the combat is mutually annihilating in tendency (Thor dies of the serpent's venom; Marduk must be armed with the totality of winds and storm to survive). Watkins reconstructs the dragon-slaying combat as an inherited formulaic structure, and Fontenrose explicitly aligned the Marduk-Tiamat and Thor-serpent combats within one combat-myth family. Borderline: the correspondence is typological/genetic-IE at best, chronology and transmission are unprovable, and the placement differs radically — cosmogonic past in Babylon, eschatological future (Ragnarok) in the Norse — which an adjudicator could reasonably treat as a decisive functional difference.

**Primary evidence:**
> Then advanced Tiamat and Marduk, the counselor of the gods; To the fight they came on, to the battle they drew nigh. The lord spread out his net and caught her, And the evil wind that was behind him he let loose in her face.
> — `mesopotamian/enuma-elish/chunks/008.toml`
> In anger smites | the warder of earth,-- Forth from their homes | must all men flee;- Nine paces fares | the son of Fjorgyn, And, slain by the serpent, | fearless he sinks.
> — `norse/poetic-edda-voluspo/chunks/014.toml`

**Secondary citations:**
- C. Watkins, How to Kill a Dragon: Aspects of Indo-European Poetics (1995) — the hero-slays-serpent formula as an inherited structural core of Indo-European myth.
- J. Fontenrose, Python: A Study of Delphic Myth and Its Origins (1959) — comparative combat-myth study aligning Marduk-Tiamat with other god-versus-dragon combats including Norse material (citation uncertain on the Thor discussion's locus).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-10 · proposed **false_friend** · borderline
**celtic / shapeshifting_transformation** (“Math's magic wand transformations”, n=47)  ↔  **native_american / shapeshifting_transformation** (“yânû (the Ani-Tsaguhi become bears)”, n=63)

**Claim:** Both cells read 'humans become animals', but the Mabinogion transformation is punitive sorcery imposed by a wronged magician-king within a juridical frame, while the Cherokee transformation is a voluntary ontological passage expressing human-animal kinship and founding a hunting covenant.

**Rationale:** Math transforms Gwydion and Gilfaethwy as sentence and shame — form is a prison term ('since now ye are in bonds'), reversed when the punishment is complete, and the animal nature is explicitly degradation. The Ani-Tsaguhi choose bear-form as abundance, retain speech and kinship, and institute the reciprocal bear-hunting songs — the move Hallowell-style ontology studies describe as metamorphosis among other-than-human persons. A concept-level matcher fuses them because the concept cell and the surface event (man-to-animal) are identical. Borderline because both narratives do share a real folkloric substrate of body-boundary fluidity, and Celtic material elsewhere (Taliesin, Tuan mac Cairill) has transformation-as-knowledge that is closer to the Cherokee pole, so a scholar could argue tradition-level homology even if these two episodes diverge.

**Primary evidence:**
> Then he took his magic wand, and struck Gilvaethwy, so that he became a deer, and he seized upon the other hastily lest he should escape from him. And he struck him with the same magic wand, and he became a deer also. "Since now ye are in bonds, I will that ye go forth together and be companions, […]
> — `celtic/mabinogion/chunks/160.toml`
> Hereafter we shall be called yânû (bears), and when you yourselves are hungry come into the woods and call us and we shall come to give you our own flesh. You need not be afraid to kill us, for we shall live always." Then they taught the messengers the songs with which to call them, and the bear […]
> — `native_american/mooney-cherokee-myths/chunks/110.toml`

**Secondary citations:**
- A.I. Hallowell, 'Ojibwa Ontology, Behavior, and World View' (1960) — metamorphosis as an attribute of other-than-human persons in Native North American ontologies (Ojibwa case, standard framework applied to Cherokee narrative).
- W.J. Gruffydd, Math vab Mathonwy (1928) — analysis of the punitive transformation sequence in the Fourth Branch (citation uncertain on section).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-11 · proposed **homology** · easy
**norse / word_power_incantation** (“the runes, won on the windy tree”, n=20)  ↔  **finnic / word_power_incantation** (“the lost-words of the Master (Wipunen)”, n=177)

**Claim:** Odin winning the runes through self-sacrificial ordeal on the tree and Väinämöinen extracting the lost words from the dead giant Wipunen are the same conceptual move: words of power must be seized from the otherworld through a deathlike ordeal, and comparativists of the Norse-Finnic contact zone defend the correspondence.

**Rationale:** Both heroes undergo a liminal death-experience (hanging wounded and unfed; entering the body of a dead primeval sage) precisely in order to acquire operative verbal knowledge — runes/charms, incantations — which then grounds their mastery as magicians. The knowledge is not doctrinal but performative: charm-lists and origin-songs. Eliade read Odin's hanging as initiatory-shamanic, DuBois and Siikala treat Norse and Finnic verbal magic as an interactive contact-zone complex; Fleck's anti-shamanic reading of Havamol 138-141 is the reservation an adjudicator should weigh, but the words-through-otherworld-ordeal structure holds regardless of the shamanism label.

**Primary evidence:**
> I ween that I hung | on the windy tree, Hung there for nights full nine; With the spear I was wounded, | and offered I was To Othin, myself to myself, On the tree that none | may ever know What root beneath it runs.
> — `norse/poetic-edda-hovamol/chunks/013.toml`
> None made me happy | with loaf or horn, And there below I looked; I took up the runes, | shrieking I took them, And forthwith back I fell.
> — `norse/poetic-edda-hovamol/chunks/013.toml`
> Till I learn thine incantations, Learn thy many wisdom-sayings, Learn the lost-words of the Master; Never must these words be bidden, Earth must never lose this wisdom, Though the wisdom-singers perish.
> — `finnic/kalevala/chunks/094.toml`

**Secondary citations:**
- T.A. DuBois, Nordic Religions in the Viking Age (1999), ch. on magic — Norse and Finnic verbal-magic traditions as an interpenetrating contact-zone complex.
- M. Eliade, Shamanism: Archaic Techniques of Ecstasy (1964), ch. on Indo-European shamanic ideologies — Odin's hanging as initiatory ordeal for numinous knowledge.
- J. Fleck, 'Odinn's Self-Sacrifice — A New Interpretation', Scandinavian Studies 43 (1971) — the counter-reading against the shamanic frame (does not touch the words-through-ordeal structure itself).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-12 · proposed **false_friend** · borderline
**jewish_mysticism / sephirot** (“the ten Sephiroth, 'as a flame to a burning coal'”, n=33)  ↔  **gnosticism / aeons** (“the aeons; Pistis Sophia's fall”, n=66)

**Claim:** Ten sefirot and thirty aeons both look like 'chains of divine emanations from a hidden God', the classic Scholem-era equation — but the sefirot are inseparable modalities of one God with no intra-divine catastrophe, while the aeon-world is a drama whose member can fall, forget, and generate the deficient cosmos.

**Rationale:** Sefer Yetzirah insists the Sephiroth have 'their end even as their beginning', bound to the divine unity as flame to coal, explicitly guarding against 'any second one'; Pistis Sophia's aeon falls out of her place, loses her light, forgets her mystery, and becomes matter — emanation as tragedy producing a world that must be escaped. The lexical trap ('emanations', numbered divine gradations, hidden source) is strong enough that Scholem himself built a genetic gnostic-origins thesis on it; Idel's counter that the sefirotic system is an inner-Jewish development with a fundamentally different theology of unity is now widely followed. Both verdicts have first-rank defenders, hence borderline; the pair also deliberately crosses two concept IDs.

**Primary evidence:**
> These ten Sephiroth which are, moreover, ineffable, have their end even as their beginning, conjoined, even as is a flame to a burning coal: for our God is superlative in his unity, and does not permit any second one.
> — `jewish_mysticism/sefer-yetzirah/chunks/001.toml`
> Because my time failed as a breath, and I became matter. They took away my light from me. And my power dried up. I forgot my mystery this which I was wont to do at first. From the shout of the fear with the power of the Self-willed my power failed in me—I became as a mere demon, dwelling in matter […]
> — `gnosticism/pistis-sophia/chunks/025.toml`

**Secondary citations:**
- G. Scholem, Origins of the Kabbalah (1962; Eng. 1987), ch. 1 — argues for gnostic elements behind early kabbalistic theosophy; the classic pro-equation case.
- M. Idel, Kabbalah: New Perspectives (1988), ch. on methodology/theosophy — rejects the genetic gnostic derivation and stresses the sefirot's inner-Jewish development and unity-theology.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-13 · proposed **homology** · easy
**egyptian / psychopomp_journey** (“the pylons and their doorkeepers' names”, n=259)  ↔  **gnosticism / psychopomp_journey** (“the mystery of the loosing of the seals”, n=36)

**Claim:** The soul's post-mortem passage past hostile gatekeepers by declaring the prescribed name/formula at each gate is a genuine structural homology between Egyptian funerary religion and Gnostic ascent, defended explicitly in the comparative literature.

**Rationale:** The conceptual move is identical and specific: the afterlife route is segmented into guarded checkpoints; each guardian releases the soul only upon correct utterance of a secret credential (the doorkeeper's name; the mystery loosing the seal) acquired ritually before death; passage is mechanical upon correct utterance, not a moral verdict. Pistis Sophia even retains the guardians' explicit instruction not to release the soul without the formula, mirroring the pylon speeches. Zandee's monograph draws the Egyptian-Gnostic comparison directly, and the Egyptian material is widely cited as background to Greco-Egyptian ascent schemes; the analogy is at the level of function, not shared names, so it survives the deity-name-matching critique.

**Primary evidence:**
> WORDS TO BE SPOKEN WHEN [ANI] COMETH UNTO THE TENTH PYLON. Saith Osiris Ani, [triumphant]: "Lo, she who is loud of voice, she who causeth those to cry who entreat her, the fearful one who terrifieth, who feareth none that are therein. The name of the doorkeeper is Sekhen-ur."
> — `egyptian/egyptian-book-of-the-dead-index/chunks/171.toml`
> And having not yet been distant from the Height, she is wont to say the mystery of the loosing of her seals, with all the bonds of the counterfeit spirit, these with which the Rulers bound it in unto the soul.
> — `gnosticism/pistis-sophia/chunks/115.toml`
> Release not this soul except she say unto thee the mystery of the loosing of every seal, these in which we bound thee in unto [262 ] the soul.
> — `gnosticism/pistis-sophia/chunks/115.toml`

**Secondary citations:**
- J. Zandee, Death as an Enemy according to Ancient Egyptian Conceptions (1960), concluding comparative section — parallels between Egyptian gate-passage formulas and Gnostic ascent passwords (citation uncertain on section number).
- H. Jonas, The Gnostic Religion (1958), ch. on the ascent of the soul — the password-ascent through archontic spheres as a defining Gnostic structure.
- G. Scholem, Jewish Gnosticism, Merkabah Mysticism, and Talmudic Tradition (1960) — the seals/passwords ascent complex across Gnostic and Hekhalot literature, establishing the comparativist legitimacy of the motif.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### C-14 · proposed **false_friend** · borderline
**native_american / living_god** (“the 'Great Mystery' (Wakan Tanka)”, n=24)  ↔  **christian_mysticism / living_god** (“'He is our clothing that for love wrappeth us'”, n=303)

**Claim:** The English rendering 'Great Spirit/Great Mystery = the living God' invites equating Wakan Tanka with the personal responsive God of Christian mysticism, but scholarship holds wakan to be a diffuse plural sacred potency, and the monotheistic framing in Eastman is itself an assimilation-era Christianizing translation.

**Rationale:** Julian's God is a personal lover who wraps, clasps, and can be petitioned — relational theism at maximum intensity. The Lakota material behind Eastman's 'Great Mystery' is, per Walker's Lakota sources, a collective of sixteen wakan aspects rather than one personal being, and Eastman (a Christian convert writing for a white audience in 1911) supplies the theistic vocabulary — 'ascended to God', 'sons of God' — that makes the lexical match fire; the corpus quote is thus the trap exhibited in a primary source. Borderline because Hultkrantz and others seriously defended a genuine Supreme Being concept in Native North America, so the adjudicator has a real scholarly argument on the homology side.

**Primary evidence:**
> The original attitude of the American Indian toward the Eternal, the "Great Mystery" that surrounds and embraces us, was as simple as it was exalted. To him it was the supreme conception, bringing with it the fullest measure of joy and satisfaction possible in this life. The worship of the "Great […]
> — `native_american/eastman-soul-of-indian/chunks/001.toml`
> I saw that He is to us everything that is good and comfortable for us: He is our clothing that for love wrappeth us, claspeth us, and all encloseth us for tender love, that He may never leave us; being to us all-thing that is good, as to mine understanding.
> — `christian_mysticism/julian-revelations/chunks/007.toml`

**Secondary citations:**
- J.R. Walker, Lakota Belief and Ritual (ed. R.J. DeMallie & E.A. Jahner, 1980) — Wakan Tanka as a sixteen-fold collective of wakan powers rather than a single personal deity.
- Å. Hultkrantz, The Religions of the American Indians (1979), ch. on the Supreme Being — defends a genuine high-god conception in Native North America; the counter-argument that keeps this pair borderline.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 


## Lane D — False-friend specialist (translation-vocabulary collisions)

### D-01 · proposed **false_friend** · easy
**buddhism / sunyata_emptiness** (“emptiness”, n=42)  ↔  **gnosticism / kenoma** (“deficiency / void (kenoma)”, n=15)

**Claim:** Both corpora speak of 'emptiness'/'deficiency' as a central metaphysical fact, so a lexical matcher links Buddhist śūnyatā to the Gnostic kenoma.

**Rationale:** In the Heart Sutra, emptiness is the true character of ALL phenomena — a liberating insight into lack of self-nature, applying equally to form and Nirvana, with no negative valuation. In Pistis Sophia, deficiency/emptiness is a cosmic REGION and privative condition — the lightless realm outside the pleroma into which Sophia falls, something to be escaped and filled with light. One is an epistemic corrective true of everything; the other is an ontological lack true of only the lower world. Identifying them inverts the Buddhist point, where emptiness is not a deficiency at all.

**Primary evidence:**
> 'O S âriputra,' he said, 'form here is emptiness, and emptiness indeed is form. Emptiness is not different from form, form is not different from emptiness. What is form that is emptiness, what is emptiness that is form.'
> — `buddhism/heart-sutra-smaller/chunks/001.toml`
> I shall manifest to thee, O Light, because thou deliveredst me, and (for) thy wonders in the race of [166 ] the mankind, I having become deficient of my power, thou gavest power to me, and I having become deficient of my light, thou filledst me with light being purified.
> — `gnosticism/pistis-sophia/chunks/071.toml`

**Secondary citations:**
- Jay L. Garfield, The Fundamental Wisdom of the Middle Way, commentary on ch. XXIV — emptiness is dependent origination itself, not a void, absence, or deficiency of being.
- Hans Jonas, The Gnostic Religion, ch. on the Valentinian speculation — the kenoma/hysterema is the privative realm of lack produced by Sophia's fall, ontologically opposed to the pleromatic fullness.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### D-02 · proposed **false_friend** · borderline
**taoism / sunyata_emptiness** (“emptiness / empty space”, n=13)  ↔  **buddhism / sunyata_emptiness** (“emptiness”, n=42)

**Claim:** The taxonomy itself tags Tao Te Ching 'emptiness' chapters with concept.sunyata_emptiness, reproducing the ancient geyi ('concept-matching') conflation of Daoist wu/xu with Buddhist śūnyatā.

**Rationale:** Laozi's emptiness is functional vacancy — the hollow of a vessel or wheel-hub whose usefulness lies in what is absent, and the Tao's own inexhaustible unfilledness. Madhyamaka emptiness is a second-order claim that no dharma possesses svabhāva, explicitly including the hollow and the hub alike. The Daoist hollow presupposes a real vessel with a real cavity; the Buddhist doctrine denies exactly that kind of intrinsic reality. Borderline because the Chinese Buddhist tradition itself long read them together, and some comparativists defend a deep affinity.

**Primary evidence:**
> The thirty spokes unite in the one nave; but it is on the empty space (for the axle), that the use of the wheel depends. Clay is fashioned into vessels; but it is on their empty hollowness, that their use depends.
> — `taoism/tao-te-ching-legge/chunks/011.toml`
> The Tao is (like) the emptiness of a vessel; and in our employment of it we must be on our guard against all fulness. How deep and unfathomable it is, as if it were the Honoured Ancestor of all things!
> — `taoism/tao-te-ching-legge/chunks/004.toml`
> 'Here, O S âriputra, all things have the character of emptiness, they have no beginning, no end, they are faultless and not faultless, they are not imperfect and not perfect. Therefore, O S âriputra, in this emptiness there is no form, no perception, no name, no concepts, no knowledge.'
> — `buddhism/heart-sutra-smaller/chunks/001.toml`

**Secondary citations:**
- Robert H. Sharf, Coming to Terms with Chinese Buddhism (2002), ch. 1 — on geyi: early Chinese translators rendered śūnyatā through indigenous Daoist wu/xu, producing a systematic conflation later Buddhists had to unwind.
- Livia Kohn, Daoism and Chinese Culture, section on Buddho-Daoist interaction — Daoist emptiness as cosmological vacancy vs Buddhist emptiness as absence of self-nature (citation uncertain).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### D-03 · proposed **false_friend** · borderline
**gnosticism / self_knowledge** (“know yourselves”, n=70)  ↔  **buddhism / self_knowledge** (“self is the lord of self”, n=43)

**Claim:** Both corpora make 'knowing/mastering the self' soteriologically central, inviting a merge of Thomas's gnosis of the divine self with the Dhammapada's self-discipline.

**Rationale:** In Thomas, to know yourself is to discover WHAT you are — a child of the living Father with a divine origin; self-knowledge reveals a metaphysical identity. In the Dhammapada, attā in 'self is the lord of self' is reflexive self-mastery and moral vigilance, within a tradition whose signature doctrine (anattā) denies precisely the substantial Self the Gnostic saying presupposes; Müller's own footnotes in this corpus warn that mind and body are 'not with the Buddhists âtman, or self.' The taxonomy definition ('recognition of one's own true divine nature') fits Thomas and contradicts the Buddhist material sharing the tag. Borderline because Upanishadically-inclined readers have long taken the Dhammapada attā verses as pointing to a true Self.

**Primary evidence:**
> When you come to know yourselves, then you will become known, and you will realize that it is you who are the sons of the living father. But if you will not know yourselves, you dwell in poverty and it is you who are that poverty.
> — `gnosticism/gospel-of-thomas/chunks/003.toml`
> 160. Self is the lord of self, who else could be the lord? With self well subdued, a man finds a lord such as few can find.
> — `buddhism/dhammapada-chapter-12/chunks/001.toml`
> Nâmarûpa is here used again in its technical sense of mind and body, neither of which, however, is with the Buddhists âtman, or 'self.'
> — `buddhism/dhammapada-chapter-25/chunks/002.toml`

**Secondary citations:**
- Steven Collins, Selfless Persons (1982) — the Dhammapada's attā passages are reflexive and conventional, not assertions of a metaphysical Self, against perennialist/Upanishadic readings.
- Elaine Pagels, Beyond Belief (2003), ch. on the Gospel of Thomas — logion 3's self-knowledge is discovery of one's divine origin and kinship with the Father.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### D-04 · proposed **false_friend** · borderline · ⚠ DUP-1
**platonism / soul_migration** (“living again / born from the dead”, n=24)  ↔  **buddhism / soul_migration** (“birth again and again”, n=13)

**Claim:** Both corpora teach that beings are 'born again' in a cycle, so translation-level matching merges Platonic metempsychosis with Buddhist rebirth.

**Rationale:** The Phaedo's argument requires a persisting substantial soul that exists between bodies ('the souls of the dead are in existence') and grounds recollection of prenatal knowledge — the cycle is evidence FOR the soul's immortality. The Dhammapada's round of births is driven by craving and the 'builder of the house,' with no transmigrating soul, and the goal is to END the cycle, not to prove an immortal substrate; rebirth is the problem, immortality of a soul is not the consolation. Borderline because scholars like McEvilley argue a genetic connection between Greek and Indian transmigration doctrines, and both do share the cyclical structure and ethical loading of rebirth.

**Primary evidence:**
> I am confident in the belief that there truly is such a thing as living again, and that the living spring from the dead, and that the souls of the dead are in existence, and that the good souls have a better portion than the evil.
> — `platonism/plato-phaedo/chunks/011.toml`
> Looking for the maker of this tabernacle, I shall have to run through a course of many births, so long as I do not find (him); and painful is birth again and again. But now, maker of the tabernacle, thou hast been seen
> — `buddhism/dhammapada-chapter-11/chunks/001.toml`

**Secondary citations:**
- Richard Gombrich, What the Buddha Thought (2009) — Buddhist rebirth is process without a transmigrating soul; the anattā doctrine makes it categorically unlike soul-migration models.
- Thomas McEvilley, The Shape of Ancient Thought (2002), chs. on reincarnation — argues for historical linkage between Greek and Indian transmigration (the identification a scholar could defend, making this pair borderline).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### D-05 · proposed **false_friend** · easy · ⚠ DUP-2
**egyptian / theosis_deification** (“I am Osiris (the deceased becomes a god)”, n=87)  ↔  **christian_mysticism / theosis_deification** (“Deification”, n=170)

**Claim:** Both corpora are tagged 'deification' — the dead Ani declares 'I am Osiris' and Dionysius defines Deification — so the shared English term merges ritual identification with participatory theosis.

**Rationale:** In the Book of the Dead, the deceased is ritually and verbally IDENTIFIED with Osiris and other gods: the formula performatively confers the god's status for post-mortem efficacy, effective at death through correct utterance, with no transformation of moral nature. Dionysian/patristic deification is a lifelong participatory assimilation 'so far as these things may be' — likeness and union by grace that explicitly preserves the creature/Creator distinction and never lets the soul BE God. Verbatim identity claim versus asymptotic participation are different conceptual moves under one English word.

**Primary evidence:**
> I am Osiris, the scribe Ani, triumphant in peace, triumphant! (8) I have drawn nigh to behold the great gods, and I feed upon the meals of sacrifice whereon their kas feed.
> — `egyptian/egyptian-book-of-the-dead-index/chunks/216.toml`
> D. defines Deification as “a process whereby we are made like unto God (ἀφομοίωσις) and are united unto Him (ἕνωσις) so far as these things may be.” (Eccl. Hier. I. 4. Migne, p. 376, A.)
> — `christian_mysticism/dionysius-divine-names-1/chunks/003.toml`

**Secondary citations:**
- Norman Russell, The Doctrine of Deification in the Greek Patristic Tradition (2004), Introduction — distinguishes 'realistic' and 'ethical' participatory theosis, always within the creature/Creator distinction.
- Jan Assmann, Death and Salvation in Ancient Egypt (2005) — the deceased's identification with Osiris is a ritual-performative transfiguration of the dead, not a moral or contemplative divinization of the living person.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### D-06 · proposed **false_friend** · easy
**egyptian / living_god** (“living god”, n=222)  ↔  **gnosticism / living_god** (“living father”, n=170)

**Claim:** The exact English phrase 'living god/living father' appears in both corpora, inviting a match between the regenerated Egyptian sun-god and the Gnostic eternal Father.

**Rationale:** In the Egyptian material 'living' is cyclical and precarious: Afu-Ra is a DEAD god who nightly regains his powers as a living god through union with Khepera — life here is renewable vitality that can be lost, maintained by cosmic process and cult. In Thomas, 'the living father' marks the eternally self-subsistent source whose life is the antithesis of the dead world; his children come from self-established light, and 'living' can never lapse. One tradition's 'living' presupposes divine mortality; the other's excludes it by definition.

**Primary evidence:**
> The pictures and texts which illustrate and describe this region are of peculiar interest, for they refer to the union of KHEPERA with RA, i.e., the introduction of the germ of new life into the body of the dead Sun-god, whereby AFU-RA. regains his powers as a living god, and becomes ready to […]
> — `egyptian/egyptian-heaven-and-hell/chunks/081.toml`
> If they say to you, 'Is it you?', say, 'We are its children, we are the elect of the living father.' If they ask you, 'What is the sign of your father in you?', say to them, 'It is movement and repose.'
> — `gnosticism/gospel-of-thomas/chunks/050.toml`

**Secondary citations:**
- Erik Hornung, Conceptions of God in Ancient Egypt: The One and the Many (1982) — Egyptian gods age, die, and are cyclically regenerated; their 'life' is maintained, not aseity.
- Bentley Layton, The Gnostic Scriptures (1987), introduction to the Gospel of Thomas — 'the living' (Jesus/Father) denotes the eternally existent, life-giving divine realm opposed to the dead cosmos.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### D-07 · proposed **false_friend** · borderline
**zoroastrianism / cosmic_dualism** (“two spirits (light vs the Lie)”, n=23)  ↔  **gnosticism / cosmic_dualism** (“Light vs the darkness of Chaos”, n=182)

**Claim:** Both corpora share the same concept tag and the same light-versus-darkness imagery, so Zoroastrian and Gnostic 'dualism' look like one doctrine.

**Rationale:** Gathic dualism is ethical and world-affirming: two primal spirits choose between truth and the Lie, but the material creation is Ahura Mazda's good handiwork and the arena where mortals must choose rightly. Pistis Sophia's dualism is anti-cosmic and vertical: darkness/Chaos is the lower material condition itself, entered by a FALL from one's Place, and salvation is extraction from matter, not victory within it. Borderline because a genetic relation between Iranian dualism and Gnosis has been seriously argued for a century (Reitzenstein through Widengren), and one branch of Gnosticism is standardly typed 'Iranian.'

**Primary evidence:**
> (Yea) when the two spirits came together at the first to make 1 life, and life's absence 2 , and to determine how the world at the last shall be (ordered), for the wicked (Hell) the worst life, for the holy (Heaven) the Best Mental State 3 ,
> — `zoroastrianism/yasna-30/chunks/001.toml`
> I became in the darkness with the shadow of the Chaos, being bound in the bonds being cruel of the Chaos, there being not light in me: because I exasperated the precept of the Light, I transgressed, I gave anger to the precept of the Light, because I came out of my Place: and I having come down, I […]
> — `gnosticism/pistis-sophia/chunks/071.toml`

**Secondary citations:**
- Hans Jonas, The Gnostic Religion — explicitly contrasts gnostic anti-cosmic dualism (matter as product of error, to be escaped) with Iranian dualism in which the good creation is the battlefield of the two spirits.
- Mary Boyce, Zoroastrians: Their Religious Beliefs and Practices (1979) — the material world is Ahura Mazda's good creation and the instrument for defeating evil, not the domain of evil itself.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### D-08 · proposed **false_friend** · easy
**christian_mysticism / meditation** (“meditation”, n=27)  ↔  **buddhism / meditation** (“meditation”, n=41)

**Claim:** The identical English word 'meditation' names a preparatory discursive exercise in the Christian corpus and the summit practice adjacent to Nirvana in the Buddhist corpus.

**Rationale:** In the Dionysian/Carmelite frame preserved in this corpus, 'meditation' is the LOWER rung — discursive, image-using rumination that one eventually abandons for imageless contemplation, and abandoning it prematurely is 'disastrous.' Müller's Dhammapada uses 'meditation' for jhāna/samādhi, the culminating discipline inseparable from liberating knowledge and 'near unto Nirvâna.' A lexical matcher aligns the bottom of one ladder with the top of the other; the conceptual roles are nearly inverted.

**Primary evidence:**
> St. John of the Cross and other spiritual writers insist that, though contemplation is a higher activity than meditation through images, yet not all are called to it, and that it is disastrous prematurely to abandon meditation.
> — `christian_mysticism/dionysius-divine-names-1/chunks/003.toml`
> 372. Without knowledge there is no meditation, without meditation there is no knowledge: he who has knowledge and meditation is near unto Nirvâ n a. 373. A Bhikshu who has entered his empty house, and whose mind is tranquil, feels a more than human delight when he sees the law clearly.
> — `buddhism/dhammapada-chapter-25/chunks/002.toml`

**Secondary citations:**
- Jean Leclercq, The Love of Learning and the Desire for God (1961), ch. on lectio divina — Christian meditatio is ruminative, discursive chewing of the scriptural text, propaedeutic to contemplatio.
- Rupert Gethin, The Foundations of Buddhism (1998), ch. 7 — dhyāna/bhāvanā as cultivation of absorption and insight, the core soteriological discipline rather than a preliminary.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### D-09 · proposed **false_friend** · borderline · ⚠ CONFLICT-1
**sufism / fana_annihilation** (“annihilate your sight in God's sight”, n=23)  ↔  **christian_mysticism / fana_annihilation** (“vanishes in God / reduces everything to nothingness”, n=37)

**Claim:** The taxonomy applies the Sufi tag fana_annihilation to Eckhart's corpus, ratifying the perennialist identification of fanā with Rhenish self-naughting.

**Rationale:** Rumi's fanā is the lover's exchange of his own attributes for God's within an uncompromisingly theistic devotional frame — sight annihilated INTO God's sight, with the servant recovered in baqā as God's act, never an identity of essence. Eckhart's soul 'loses its own distinctiveness and vanishes in God' in the ground where, on his metaphysic, God and soul were never ontologically two — an indistinct union rooted in Trinitarian emanation, not the erasure of a lover before the Beloved. The shared rhetoric of annihilation covers different theologies of what remains and why. Borderline: serious comparativists (e.g. Shah-Kazemi) argue the two are substantively convergent.

**Primary evidence:**
> Our eyes are subject to many infirmities; Go! annihilate your sight in God's sight. For our foresight His foresight is a fair exchange; In His sight is all that ye can desire.
> — `sufism/masnavi-book-1/chunks/011.toml`
> When the soul gets to this point, it loses its own distinctiveness, and vanishes in God as the crimson of sunrise disappears in the sun. To this goal only pure sanctification can arrive.
> — `christian_mysticism/eckhart-sermons-field/chunks/019.toml`

**Secondary citations:**
- Annemarie Schimmel, Mystical Dimensions of Islam (1975), ch. 2 — fanā is annihilation of attributes and will, not substantial union or deification; baqā restores the servant.
- Bernard McGinn, The Mystical Thought of Meister Eckhart (2001) — Eckhart's union is 'indistinct union' in the ground of the soul, grounded in the eternal birth of the Word, a different metaphysics from devotional annihilation.
- Reza Shah-Kazemi, Paths to Transcendence (2006) — argues the substantive convergence of Eckhart and Sufi annihilation (the identification a scholar could defend).

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### D-10 · proposed **false_friend** · easy
**finnic / word_power_incantation** (“words of magic / the lost-words”, n=177)  ↔  **christian_mysticism / birth_of_word_in_soul** (“the Word of God”, n=60)

**Claim:** Both corpora center on the salvific power of 'the Word,' tempting a link between Väinämöinen's quest for lost words and Eckhart's birth of the Word in the soul.

**Rationale:** Kalevala 'words' are discrete, ownable units of technical-magical knowledge — origin-charms that confer causal power over things (a boat cannot be finished for want of three words, and the hero raids a dead giant's mouth to get them). Eckhart's 'Word' is the second Person of the Trinity, eternally begotten in the soul's ground; it is not information, cannot be lost or fetched, and confers filiation rather than operative power. The shared English 'word(s)' papers over incantatory technology versus Trinitarian ontology.

**Primary evidence:**
> Wainamoinen, old and truthful, Did not learn the words of magic In Tuoni's gloomy regions, In the kingdom of Manala. Thereupon he long debated, Well considered, long reflected, Where to find the magic sayings; When a shepherd came to meet him, Speaking thus to Wainamoinen: "Thou canst find of words […]
> — `finnic/kalevala/chunks/089.toml`
> To which Christ answered, “Nay, rather blessed are they that hear the Word of God and keep it.” It is more worthy of God that He be born spiritually of every pure and virgin soul, than that He be born of Mary.
> — `christian_mysticism/eckhart-sermons-field/chunks/009.toml`

**Secondary citations:**
- Anna-Leena Siikala, Mythic Images and Shamanism: A Perspective on Kalevala Poetry (2002) — the tietäjä's power rests on knowing a thing's synty (origin-words); the charm operates causally on its object.
- Bernard McGinn, The Mystical Thought of Meister Eckhart (2001), ch. on the birth of the Word — the eternal begetting of the Son in the ground of the soul as Eckhart's central teaching.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### D-11 · proposed **false_friend** · easy
**egyptian / ritual_purity** (“I am pure / purified”, n=85)  ↔  **buddhism / ritual_purity** (“by oneself one is purified”, n=14)

**Claim:** Both corpora declare the subject 'pure/purified' under the same concept tag, though one purity is lustral-ritual and the other explicitly repudiates ritual purification.

**Rationale:** The Book of the Dead's purity is a ritual state achieved by bathing in sacred pools and declared formulaically to pass the gatekeepers of the judgment hall — external, transferable by rite, and instrumentally required for admission. Dhammapada 165 defines purity as strictly ethical and reflexive — 'no one can purify another' — a direct denial of the officiated, ritual purification the Egyptian text exemplifies. The shared tag merges a lustration system with its explicit ethical negation.

**Primary evidence:**
> I am pure, in my fore-parts have I been made clean, and in my hinder parts have I (19) been purified; my reins have been bathed in the Pool of right and truth, and no member of my body was wanting. I have been purified in the pool of the south.
> — `egyptian/egyptian-book-of-the-dead-index/chunks/224.toml`
> 165. By oneself the evil is done, by oneself one suffers; by oneself evil is left undone, by oneself one is purified. Purity and impurity belong to oneself, no one can purify another.
> — `buddhism/dhammapada-chapter-12/chunks/001.toml`

**Secondary citations:**
- Richard Gombrich, Theravada Buddhism: A Social History (1988), ch. 2 — the Buddha ethicized Brahmanical categories, redefining purity as moral rather than ritual.
- Jan Assmann, Death and Salvation in Ancient Egypt (2005) — purification rites and declarations of purity as preconditions for the deceased's passage and vindication before the tribunal.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 

### D-12 · proposed **false_friend** · borderline
**christian_mysticism / detachment_gelassenheit** (“sanctification [Field's rendering of Abgeschiedenheit] / empty of all creature's love”, n=74)  ↔  **buddhism / detachment_gelassenheit** (“free from all attachments”, n=68)

**Claim:** The taxonomy's single detachment/Gelassenheit tag merges Eckhart's God-directed letting-go with Buddhist non-attachment, the exact equation D.T. Suzuki made famous.

**Rationale:** Eckhart's detachment is a via: the heart is emptied of creatures PRECISELY SO THAT it 'draws God to itself' and God can write on the blank tablet — an ontological receptivity ordered to union and the birth of the Word. The Dhammapada's freedom from attachments is the extinction of craving that ends suffering and rebirth; nothing is emptied in order to be filled, and no divine indwelling completes the movement. Same negative gesture, opposite teleologies — one theocentric plenitude, one cessation. Borderline because Suzuki and others argued they are the same act, and Eckhart's 'wanting nothing' can be read non-teleologically.

**Primary evidence:**
> When the free spirit is stablished in true sanctification, it draws God to itself, and were it placed beyond the reach of contingencies, it would assume the properties of God. ... And thou shouldest know that to be empty of all creature’s love is to be full of God, and to be full of creature-love […]
> — `christian_mysticism/eckhart-sermons-field/chunks/017.toml`
> 396. I do not call a man a Brâhma n a because of his origin or of his mother. He is indeed arrogant, and he is wealthy: but the poor, who is free from all attachments, him I call indeed a Brâhma n a. 397. Him I call indeed a Brâhma n a who has cut all fetters, who never trembles, is independent and […]
> — `buddhism/dhammapada-chapter-26/chunks/002.toml`

**Secondary citations:**
- D.T. Suzuki, Mysticism: Christian and Buddhist (1957) — explicitly identifies Eckhart's detachment/nothingness with Buddhist emptiness and non-attachment (the identification under test).
- Shizuteru Ueda, 'Nothingness in Meister Eckhart and Zen Buddhism' (in The Buddha Eye, ed. Franck) — draws the distinction: Eckhart's letting-go terminates in the birth of God in the soul, where Zen non-attachment has no such theistic completion.
- Bernard McGinn, The Mystical Thought of Meister Eckhart (2001), ch. on detachment — Abgeschiedenheit as ordered to union with God, not cessation of craving.

**Verdict:** ☐ homology ☐ false_friend ☐ rejected — 
