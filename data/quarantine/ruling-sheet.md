# Tag-quarantine dossiers — batch 1 ruling sheet

10 cells, 564 tags, from `suspect-ranking.csv` (164 suspect cells / 3,158 tags total).
Agent-assembled evidence, quotes machine-verified verbatim against the corpus
(one chunk-id misattribution found and corrected during validation). Rule each cell:
**keep / reassign / mixed (needs per-chunk pass) / reject** — nothing applies without you.

| # | cell | n | proposer says | est. keep/reassign/reject | conf |
|---|---|---:|---|---|---|
| 1 | living_god × finnic | 191 | mixed → concept.prayer, concept.word_power_incantation, concept.animism | 20%/25%/55% | high |
| 2 | theurgy × finnic | 85 | reassign → word_power_incantation | 0%/70%/30% | high |
| 3 | living_god × celtic | 80 | reject → concept.shapeshifting_transformation, concept.word_power_incantation (case-by-case for enchantment chunks); keep only the Taliesin hymn chunks | 6%/6%/88% | high |
| 4 | cosmic_dualism × finnic | 59 | reject | 5%/5%/90% | high |
| 5 | kingdom_within × buddhism | 32 | reject → self_knowledge / sunyata_emptiness (only where not already co-tagged) | 5%/10%/85% | high |
| 6 | living_god × mandaean | 30 | keep | 85%/5%/10% | high |
| 7 | ritual_purity × native_american | 26 | mixed → fasting_and_prayer; cosmic_sympathy (per-chunk) | 30%/25%/45% | medium |
| 8 | detachment_gelassenheit × hinduism | 26 | keep | 77%/4%/19% | medium |
| 9 | soul_migration × hinduism | 18 | keep | 90%/0%/10% | high |
| 10 | self_knowledge × hinduism | 17 | keep | 90%/0%/10% | high |


## 1. living_god × finnic (n=191) — proposed: **mixed**

*The divine conceived as active, present, and dynamic—not an abstract principle but a personal responsive reality.* (family `theology.divine_attributes_and_acts`)

**Home move:**
> Now, therefore, O Pepi, he that hath given unto thee life and all power and eternity and the power of speech and thy body is Ra. ... Hail, Pepi, thou placest thyself upon the throne of Him that dwelleth among the living.
> — `egyptian.egyptian-book-of-the-dead-index.062`
> O Powerful Victory, by men desir'd ... Thee I invoke, whose might alone can quell Contending rage, and molestation fell ... Come, mighty Goddess, and thy suppliant bless, With sparkling eye, elated with success.
> — `greek_mystery.orphic-hymns.074`

**What the cell actually contains:**
> Fair Annikki, lovely sister, Bring me now my silken raiment, Bring my best and richest vesture ... Brought a fur-coat made of seal-skin, Fastened with a thousand bottons, And adorned with countless jewels.
> — `finnic.kalevala.100` · Wholly secular dressing/courtship scene; no divine content of any kind. Representative of the 109/191 tagged chunks containing no deity term (no Ukko, God, jumala, or creator).
> O thou wise and worthy minstrel, Thou the only true, magician, Cease I pray thee thine enchantment, Only turn away thy magic.
> — `finnic.kalevala.013` · Supplication addressed to Wainamoinen, a human singer-magician, in a song-contest — the move is magical word-power between humans (word_power_incantation), not a responsive god.
> Paths of hope that God has fashioned, Have ye seen my Lemminkainen ... Sad, the many pathways answer: We ourselves have cares sufficient, Cannot watch thy son and hero.
> — `finnic.kalevala.076` · The mother interrogates personified pathways (and elsewhere moon, trees, rivers) which answer — the animism move: plural, local, embodied spirits in landscape; the single 'God' reference is incidental.
> Ukko, thou O God above me, Thou that rulest all the storm-clouds ... Let the icy rain come falling ... Ukko, the benign Creator, Heard the prayer of Lemminkainen, Broke apart the dome of heaven, Rent the heights of heaven asunder.
> — `finnic.kalevala.071` · Genuine home-move match: Ukko petitioned in second person and responding with immediate action — a personal, responsive, active god.
> Ukko, thou O God above me, Thou Creator of the heavens, Put my snow-shoes well in order, And endow them both with swiftness.
> — `finnic.kalevala.068` · Petition to Ukko as active helper; matches the home move, though it is also a straightforward prayer instance — the tag and concept.prayer overlap here.

**Analysis:** The tag has been applied as a blanket across the Kalevala: 191 of 275 chunks are tagged, and 109 of the 191 contain no deity term whatsoever (no Ukko, God, jumala, or creator) — pure heroic narrative, courtship, feasting, battle. Of the 82 that do mention a deity, many are incidental formula ('God has fashioned') inside scenes whose real move is animist nature-spirit address or human runo-magic (word_power_incantation, shamanic_journey). A genuine minority — the recurring 'Ukko, thou O God above me' petitions, several of which show Ukko responding with action — does make the home move of a personal responsive divine reality. The cell is therefore not a false friend at the concept level but a catastrophic over-application at the chunk level: living_god became a proxy for 'this is the Kalevala'.

**Reassign to:** concept.prayer, concept.word_power_incantation, concept.animism

**Citations:** Kalevala, trans. John Martin Crawford — Ukko is the sky-god/'Creator' petitioned in formulaic invocations throughout ('Ukko, thou O God above me') · Lonnrot, Kalevala — the epic is predominantly heroic-magical narrative in which sung word-power, not deity petition, is the operative supernatural mechanism (citation uncertain)

**Ruling:** ☐ keep ☐ reassign ☐ mixed ☐ reject — 


## 2. theurgy × finnic (n=85) — proposed: **reassign**

*Iamblichean ritual practice that engages the gods directly through consecrated material symbols and actions, on the premise that divine power descends into properly prepared matter — distinct from philosophical contemplation alone.* (family `praxis.ritual_and_symbolic`)

**Home move:**
> in the worship of the Gods, they offered animals, and other substances congruous to their nature; and received in the first place the powers of daemons as proximate to natural substances and operations... Afterwards they proceeded from daemons to the powers and energies of the Gods... aptly interpreting symbols, and ascending to a proper intelligence of the Gods.
> — `greek_mystery.orphic-hymns.023`
> Thou art purified with natron, and Horus is purified with natron... Hail, Unas, thy two jaws are unlocked. Hail, Unas, the two gods have opened thy mouth. O Unas, the Eye of Horus hath been given unto thee, and Horus cometh thereunto; it is brought unto thee, and placed in thy mouth.
> — `egyptian.egyptian-book-of-the-dead-index.111`

**What the cell actually contains:**
> Greater things have been accomplished, Much more wondrous things effected, Through but three words of the master; Through the telling of the causes, Streams and oceans have been tempered, River cataracts been lessened.
> — `finnic.kalevala.037` · Blood-stopping charm: efficacy lies in speaking the origin-words ('telling of the causes'), the paradigm word_power_incantation move; no consecrated matter, no descending divine power.
> I have learned of words a hundred, Learned a thousand incantations... Thus the ancient Wainamoinen Built the boat with magic only, And with magic launched his vessel, Using not the hand to touch it.
> — `finnic.kalevala.095` · The Wipunen lost-words episode: sung words alone build and launch the boat — verbal-causal magic, explicitly bypassing material operation rather than working through it.
> Quick began his incantations, Straightway sang the songs of witchcraft... Sang the very best of singers To the very worst of minstrels, Filled their mouths with dust and ashes, Piled the rocks upon their shoulders.
> — `finnic.kalevala.062` · Competitive song-combat between human sorcerers; coercive singing against rivals, not engagement of gods through symbols.
> He will charm thee with his singing Will bewitch thee in his anger... By my songs shall I transform him, That his feet shall be as flint-stone, And as oak his nether raiment.
> — `finnic.kalevala.009` · Singing-duel challenge: transformation by song. Same magic-song register; nothing Iamblichean.
> Now he tries his silken fish-net, Angles long, and angles longer... Till at last, one sunny morning, Strikes a fish of magic powers.
> — `finnic.kalevala.024` · Plain narrative (fishing for the Aino-fish); no ritual act at all — pure tagger noise, neither theurgy nor word_power.

**Analysis:** Twelve sampled chunks across the Kalevala show one consistent register: runo-song and origin-word magic wielded by human singers against nature, rivals, and wounds — the causal engine is always the sung/spoken word, never divine power drawn down into consecrated material symbols, and the gods (Ukko) appear only as addressees of prayer. This is exactly the surface-only Iamblichean-theurgy↔operative-magic collapse the gold-set adjudication flagged, and it is the contamination vector for the theurgy F1 drop. 75 of the 85 chunks already carry word_power_incantation (whose taxonomy definition names Vainamoinen's runo-songs as an exemplar), so for those the fix is simply dropping theurgy; the 10 chunks lacking it (e.g. 024, 048, 116) are mostly plain narrative or craft-forging episodes where neither concept applies. Nothing sampled satisfies the theurgy definition's premise of divine descent into prepared matter.

**Reassign to:** word_power_incantation

**Citations:** Iamblichus, De Mysteriis (II.11) — theurgic union effected by divine symbols/sunthemata, not by human thought or coercive craft · Proclus apud Thomas Taylor, Dissertation on Orphic Hymns — ascent through material substances congruous to divine natures · Lonnrot/Crawford, The Kalevala — Vainamoinen's power is knowledge of origin-words and song, characteristic of Finnic tietaja practice (citation uncertain)

**Ruling:** ☐ keep ☐ reassign ☐ mixed ☐ reject — 


## 3. living_god × celtic (n=80) — proposed: **reject**

*The divine conceived as active, present, and dynamic—not an abstract principle but a personal responsive reality.* (family `theology.divine_attributes_and_acts`)

**Home move:**
> Now, therefore, O Pepi, he that hath given unto thee life and all power and eternity and the power of speech and thy body is Ra. ... Hail, Pepi, thou placest thyself upon the throne of Him that dwelleth among the living.
> — `egyptian.egyptian-book-of-the-dead-index.062`
> O Powerful Victory, by men desir'd ... Thee I invoke, whose might alone can quell Contending rage, and molestation fell ... Come, mighty Goddess, and thy suppliant bless, With sparkling eye, elated with success.
> — `greek_mystery.orphic-hymns.074`

**What the cell actually contains:**
> And Owain asked the pages in which troop the Earl was. ... So they returned, and Owain pressed forward until he met the Earl. And Owain drew him completely out of his saddle, and turned his horse's head towards the Castle.
> — `celtic.mabinogion.019` · Secular chivalric combat narrative; no divine reference at all. 24 of the 80 tagged chunks have no god-term of any kind.
> Heaven knows, Lady, said Owain, it is no more possible for me to...
> — `celtic.mabinogion.011` · Representative of the dominant pattern in the 56 chunks that do mention God/Heaven: courtly oath and politeness formulas ('Heaven knows', 'I declare to Heaven', 'Heaven prosper thee') — conversational convention in Guest's translation, not a theological claim.
> Lady, he said, wilt thou tell me aught concerning thy purpose? I will tell thee, said she. My chief quest was to seek thee.
> — `celtic.mabinogion.128` · Pwyll and Rhiannon courtship dialogue — otherworld romance narrative, no divine-presence move.
> And she took hold of the bowl with him; and as she did so her hands became fast to the bowl, and her feet to the slab ... there came thunder upon them, and a fall of mist, and thereupon the castle vanished, and they with it.
> — `celtic.mabinogion.151` · Enchantment-marvel narrative (Manawyddan); the supernatural here is magic and otherworld enchantment, not a responsive god.
> I adore the Supreme, Lord of all animation,— Him that supports the heavens, Ruler of every extreme, Him that made the water good for all, Him who has bestowed each gift, and blesses it.
> — `celtic.mabinogion.188` · The one genuine match in the cell: Taliesin's hymn praising an active, sustaining, gift-bestowing God — the home move, via the Christian overlay of the Hanes Taliesin section.

**Analysis:** The Mabinogion cell is almost entirely secular narrative: quests, combats, courtships, enchantments. 24/80 tagged chunks contain no god-term at all, and in the 56 that do, 'God/Heaven' occurs overwhelmingly as courtly oath formula ('Heaven knows, Lady', 'I declare to Heaven') — speech decoration, not theology. Nothing in the Four Branches or the romances presents a deity as an active responsive presence; the operative supernatural is enchantment, otherworld beings, and shapeshifting, which have their own concepts (shapeshifting_transformation, animism). The only genuine expressions are 3-5 chunks in the Taliesin section (roughly 186-190), where Taliesin sings praise of 'the Supreme, Lord of all animation' who actively sustains and bestows — a real living-god move, though Christian rather than Celtic-pagan. This cell looks like a classic false friend: the tagger keyed on surface 'God/Heaven' tokens in a text whose religiosity is formulaic.

**Reassign to:** concept.shapeshifting_transformation, concept.word_power_incantation (case-by-case for enchantment chunks); keep only the Taliesin hymn chunks

**Citations:** The Mabinogion, trans. Lady Charlotte Guest — 'Heaven knows'/'I declare to Heaven' oath formulas pervade the courtly dialogue · Hanes Taliesin (in Guest's Mabinogion) — Taliesin's songs contain explicit praise of an active sustaining God ('I adore the Supreme, Lord of all animation')

**Ruling:** ☐ keep ☐ reassign ☐ mixed ☐ reject — 


## 4. cosmic_dualism × finnic (n=59) — proposed: **reject**

*Ontological opposition between two primal principles (light/darkness, truth/lie, spirit/matter) as the fundamental structure of reality.* (family `theology.ontological_structure`)

**Home move:**
> Thus are the primeval spirits who as a pair (combining their opposite strivings), and (yet each) independent in his action, have been famed (of old). (They are) a better thing, they two, and a worse, as to thought, as to word, and as to deed. And between these two let the wisely acting choose aright.
> — `zoroastrianism.yasna-30.001`
> Matter becomes mistress of what is manifested through it: it corrupts and destroys the incomer, it substitutes its own opposite character and kind... No, if body is the cause of Evil, then there is no escape; the cause of Evil is Matter.
> — `neoplatonism.plotinus-select-works-index.076`

**What the cell actually contains:**
> Louhi, hostess of Pohyola, Northland's old and toothless wizard, Makes the Sun and Moon her captives... When the golden Moon had vanished, And the silver Sun had hidden In the iron-banded caverns, Louhi stole the fire from Northland... Night was king and reigned unbroken, Darkness ruled in Kalevala.
> — `finnic.kalevala.252` · The strongest-looking light/dark passage is a theft narrative: a sorceress steals and hides the luminaries, Ukko strikes new fire, and the plot restores them. Darkness is a reversible event inside one creation, not a coeternal principle.
> How unborn to live and flourish In the spaces wrapped in darkness, In uncomfortable limits, Where he had not seen the moonlight, Had not seen the silver sunshine... Thus the wonderful enchanter Was delivered from his mother, Ilmatar, the Ether's daughter.
> — `finnic.kalevala.003` · Womb-darkness in the birth of Vainamoinen — gestation imagery, not an ontological dark principle.
> Never while the moonlight glimmers, Shall I go to dreary Pohya, To the plains of Sariola, Where the people eat each other, Sink their heroes in the ocean.
> — `finnic.kalevala.046` · Pohjola as dismal, dangerous otherworld-north — mythic geography and inter-community hostility, not a metaphysical anti-principle.
> Then Untamo sorely threatened To annihilate the people Of his brother, Kalerwoinen, To exterminate his tribe-folk... Warriors of Untamoinen Came equipped with spears and arrows, Killed the people of Kalervo.
> — `finnic.kalevala.184` · The Kullervo cycle's kin-feud — purely social antagonism tagged apparently on 'Son of Evil' lexicon.
> Now my mind is filled with sorrow... Till my life is filled with darkness, And my spirit white with anguish.
> — `finnic.kalevala.019` · Aino's lament: darkness as emotional metaphor for grief.

**Analysis:** The Yasna 30 reference move posits two primeval spirits, each independent, jointly determining the structure and eschatological outcome of reality, with human existence framed as a choice between them; Plotinus argues an ontological thesis about Matter as the ground of evil. Thirteen sampled Kalevala chunks contain nothing of this shape: the oppositions are narrative (hero vs rival singer, Kalevala vs Pohjola raids, Untamo vs Kalervo feud, Louhi's theft of sun and moon) or affective (grief-darkness), and every darkness is local, personified in a mortal antagonist, and reversed within the plot under a single creator (Ukko) who is never opposed by a rival principle. Pohjola is a hostile otherworld region, not an anti-cosmos; Louhi is a sorceress, not an Angra Mainyu. The tagger appears to have keyed on light/dark and North-vs-Kaleva lexical surface. This is narrative antagonism, and there is no better existing concept that fits the antagonism itself (individual chunks' real content — shamanic_journey, word_power_incantation, animism — is already co-tagged).

**Citations:** Yasna 30.3-5, Mills tr. (SBE 31) — the two primal spirits as ontological-ethical pair · Mary Boyce, Zoroastrians: Their Religious Beliefs and Practices — dualism of two uncreated spirits as doctrine (citation uncertain) · Juha Pentikainen, Kalevala Mythology — Pohjola as the mythic north/otherworld of the epic's conflict, not a metaphysical evil principle (citation uncertain)

**Ruling:** ☐ keep ☐ reassign ☐ mixed ☐ reject — 


## 5. kingdom_within × buddhism (n=32) — proposed: **reject**

*The claim that the divine realm is present inside the individual, accessible without external mediation.* (family `anthropology.divine_indwelling`)

**Home move:**
> The only way in which this matter can be settled for once and for ever is that those who have doubts about the divinity of Christ succeed in raising Him from His tomb within their own souls, when He will become revealed to them.
> — `christian_mysticism.life-and-doctrines-boehme.118`
> In the life of man there are three states to be distinguished from each other—first, the innermost, that is to say, God being eternally hidden within the fire; secondly, the middle part, which from eternity has stood as an image or likeness in the wonders of God.
> — `christian_mysticism.life-and-doctrines-boehme.055`

**What the cell actually contains:**
> Self is the lord of self, who else could be the lord? With self well subdued, a man finds a lord such as few can find... By oneself the evil is done, by oneself one suffers... Purity and impurity belong to oneself, no one can purify another.
> — `buddhism.dhammapada-chapter-12.001` · Self-mastery and moral self-reliance: the trained self is the only 'lord' — precisely the anatta-shaped move the gold set rated a false friend (B-09), with no indwelling divine posited.
> You yourself must make an effort. The Tathagatas (Buddhas) are only preachers. The thoughtful who enter the way are freed from the bondage of Mara.
> — `buddhism.dhammapada-chapter-20.001` · Interiorized responsibility for the path — effort and insight, not access to a divine realm within.
> All that we are is the result of what we have thought: it is founded on our thoughts, it is made up of our thoughts. If a man speaks or acts with an evil thought, pain follows him, as the wheel follows the foot of the ox that draws the carriage.
> — `buddhism.dhammapada-chapter-01.001` · Mind-primacy in ethical causation — a claim about karmic construction of experience, not about a divine presence inside the person.
> He who takes refuge with Buddha, the Law, and the Church; he who, with clear understanding, sees the four holy truths... That is the safe refuge, that is the best refuge; having gone to that refuge, a man is delivered from all pain.
> — `buddhism.dhammapada-chapter-14.003` · Refuge is the external triple gem plus insight into the truths — directly against the 'without external mediation' clause; the tagger seemingly read 'inner refuge' into it. (Quote splices the verse across an editorial footnote present in the chunk file.)
> form here is emptiness, and emptiness indeed is form... in this emptiness there is no form, no perception, no name, no concepts, no knowledge.
> — `buddhism.heart-sutra-smaller.001` · Sunyata denies the substantial interior locus that a kingdom-within would occupy; already served by sunyata_emptiness.

**Analysis:** The reference move (Boehme, and Plotinine interiority generally) presupposes an indwelling divine reality — God or Christ already present in the soul's ground, to be uncovered without external mediation. The Buddhist cell is Dhammapada and Heart Sutra material whose interiority is of a different kind: mind as the karmic engine, self-subduing as the only lordship, personal effort with the Buddha demoted to 'only a preacher,' and, in the Heart Sutra, an explicit emptying of any inner substantial locus. Chapter 14 even makes refuge external (Buddha, Dharma, Sangha), contradicting the definition's no-external-mediation clause. This maps one-to-one onto gold-set B-09 (anatta-shaped self-mastery, rated 1): interiorized liberation without an indwelling divine is a false friend of kingdom_within. The genuinely parallel Buddhist doctrine (tathagatagarbha/luminous mind) does not appear in these chunks. The real content is already covered by co-tags (detachment_gelassenheit 29, self_knowledge 22, sunyata_emptiness 15, meditation 19), so wholesale rejection loses little.

**Reassign to:** self_knowledge / sunyata_emptiness (only where not already co-tagged)

**Citations:** Dhammapada vv. 160, 165, 276 (Muller tr., SBE 10) — self as only lord; self-purification; Tathagatas only preachers · Gold-set adjudication B-09 — anatta-shaped self-mastery vs kingdom_within rated 1 (false friend) · Steven Collins, Selfless Persons — anatta doctrine excludes an indwelling-self/divine-ground reading of Pali interiority (citation uncertain)

**Ruling:** ☐ keep ☐ reassign ☐ mixed ☐ reject — 


## 6. living_god × mandaean (n=30) — proposed: **keep**

*The divine conceived as active, present, and dynamic—not an abstract principle but a personal responsive reality.* (family `theology.divine_attributes_and_acts`)

**Home move:**
> Now, therefore, O Pepi, he that hath given unto thee life and all power and eternity and the power of speech and thy body is Ra. ... Hail, Pepi, thou placest thyself upon the throne of Him that dwelleth among the living.
> — `egyptian.egyptian-book-of-the-dead-index.062`
> O Powerful Victory, by men desir'd ... Thee I invoke, whose might alone can quell Contending rage, and molestation fell ... Come, mighty Goddess, and thy suppliant bless, With sparkling eye, elated with success.
> — `greek_mystery.orphic-hymns.074`

**What the cell actually contains:**
> Through my Father's discourses I give light and through the praise of the Man, my creator, I have freed my soul from the world.
> — `mandaean.gnostic-john-baptizer-1.004` · The divine as 'Life' is the axis of the passage: the hostile powers are defined precisely as 'the Dead who have not seen Life' — divinity equated with living reality itself. (The companion phrase 'the Dead who have not seen Life' appears in chunk 008.)
> Thou hast won the victory, Gnosis of Life, and helped all thy friends to victory. And Life is victorious. In the Name of Great Life, may hallowed Light be glorified.
> — `mandaean.gnostic-john-baptizer-2.003` · 'In the Name of Great Life' (Hayyi Rabbi) is the standard liturgical opening across these texts; Life is portrayed as an acting, victorious agent — the home move in its strongest form.
> I have come unto thee, O Soul, whom Life has sent into this world. In robes of the Eight went I into the world. I went in the vesture of Life and came into the world.
> — `mandaean.gnostic-john-baptizer-1.008` · Life actively sends the messenger and the soul into the world — the divine as dynamic, initiating, personal agent, not abstract principle.
> The Treasury am I, Life's Treasury. ... Day in and day out they sing praise to Great [Life], and through me they mount upward and behold the Light's region.
> — `mandaean.gnostic-john-baptizer-3.013` · Great Life as the continuously praised, presently active source of ascent — praise-relationship with a living supreme being.
> Who told Yeshu Messiah, son of Miryam, who told Yeshu, so that he went to the shore of the Jordan and said [unto Yahya]: Yahya, baptize me with thy baptizing and utter o'er me also the Name thy wont is to utter.
> — `mandaean.gnostic-john-baptizer-1.009` · One of the minority narrative-polemic chunks: baptism dispute where the operative move is the uttered Name (sacred_names) rather than the living-god theme itself, though the Great Life frame surrounds the section.

**Analysis:** This cell is close to maximally legitimate. The Mandaean supreme being is Hayyi Rabbi, 'The Great Life / The Living One', and these texts (Mead's Gnostic John the Baptizer, from the Book of John) invoke it constantly: 23 of 30 tagged chunks contain explicit Life-language, including the recurring liturgical formula 'In the Name of Great Life, may hallowed Light be glorified' and refrains like 'Life is exalted and is victorious'. Life acts — it sends messengers, wins victories, receives daily praise, and its opponents are 'the Dead who have not seen Life' — which is exactly the home move: the divine as active, personal, responsive reality rather than abstract principle, here elevated to the tradition's very theonym. The handful of chunks without explicit Life-refs are narrative or polemic sections (John/Jesus baptism dispute, the fisher allegory) embedded in the same hymn cycles, where a stricter chunk-level read might prefer sacred_names or divine_hiddenness, but the tag is defensible even there. This is legitimate new coverage, not a false friend.

**Citations:** G.R.S. Mead, Gnostic John the Baptizer: Selections from the Mandaean John-Book — the 'In the Name of Great Life, may hallowed Light be glorified' opening formula and 'Life is victorious' refrains · Jorunn J. Buckley, The Mandaeans: Ancient Texts and Modern People — Hayyi Rabbi ('The Great Life') as the Mandaean supreme being (citation uncertain) · Mark Lidzbarski, Das Johannesbuch der Mandaer — source translation underlying Mead's selections (citation uncertain)

**Ruling:** ☐ keep ☐ reassign ☐ mixed ☐ reject — 


## 7. ritual_purity × native_american (n=26) — proposed: **mixed**

*The maintenance of a state of cleanliness—physical, moral, or spiritual—required for encounter with the divine.* (family `praxis.ascetic_discipline`)

**Home move:**
> The Purifications are divided into two parts, one concerning itself with the physical body, and the other with the 'luminous body.'... All three Purifications must be accomplished if man would become free, and Godlike.
> — `greek_mystery.pythagorean-golden-verses.008`
> thou art purified with natron, and Horus is purified with natron... and thy mouth is [as pure] as the mouth of a sucking calf on the day of its birth. Thou art stablished among the gods thy brethren, thy head is purified for thee with natron.
> — `egyptian.egyptian-book-of-the-dead-index.111`

**What the cell actually contains:**
> This story gives the traditional origin of the 'eneepee,' which has ever since been deemed essential to the Indian's effort to purify and recreate his spirit. It is used both by the doctor and by his patient. Every man must enter the cleansing bath and take the cold plunge which follows, when preparing for any spiritual crisis.
> — `native_american.eastman-soul-of-indian.014` · Vapor-bath as purification before spiritual encounter — a genuine purity move, though its charter myth (dead bones revived by steam) frames it as renewal/re-creation as much as cleansing.
> He wakes at daybreak, puts on his moccasins and steps down to the water's edge. Here he throws handfuls of clear, cold water into his face, or plunges in bodily. After the bath, he stands erect before the advancing dawn, facing the sun as it dances upon the horizon, and offers his unspoken orison.
> — `native_american.eastman-soul-of-indian.008` · Morning ablution immediately preceding prayer — the closest match to the lustral reference move.
> For baptism we substitute the 'eneepee,' the purification by vapor, and in our holy communion we partake of the soothing incense of tobacco in the stead of bread and wine.
> — `native_american.eastman-soul-of-indian.015` · Explicitly a purification sacrament, though in Eastman's deliberately Christianized comparative framing.
> a person under treatment for rheumatism is forbidden to eat the meat, touch the skin, or use a spoon made from the horn of the buffalo, upon the ground of an occult connection between the habitual cramped attitude of a rheumatic and the natural 'hump' of that animal.
> — `native_american.mooney-cherokee-myths.028` · Medical food-tabu grounded in sympathetic correspondence — avoidance of harmful likeness, not cleanliness for divine encounter; the frame is cosmic_sympathy.
> if your people will live with us let them fast seven days, and we shall come then to take them... 'I came with them, but you did not obey my word, but broke the fast and raised the war cry.'
> — `native_american.mooney-cherokee-myths.126` · Seven-day fast as preparation/qualification for crossing into the spirit town — fasting_and_prayer, with the emphasis on obedience and readiness rather than cleanness.
> The robin is called tsiskwa'gwa, a name which can not be analyzed, while the little sparrow is called tsiskwa'ya (the real or principal bird).
> — `native_american.mooney-cherokee-myths.054` · Bird nomenclature ethnography — no purity content at all; tag noise.

**Analysis:** The cell splits cleanly by source. The Eastman (Lakota) chunks describe real purification practice — morning water rite before prayer, the inipi vapor-bath required 'when preparing for any spiritual crisis' — which does satisfy the definition's letter, though the indigenous frame is renewal/re-creation (the eneepee's origin myth is a resurrection) and preparation rather than removal of pollution as a formulaic precondition of the Egyptian/Pythagorean type. The Mooney (Cherokee) chunks, the bulk of the cell, are mostly tabu and sympathetic-magic ethnography (food tabus keyed to occult resemblance, fuel tabus, insect rites) or plain myth narrative; their governing logic is correspondence/avoidance, not lustral cleanliness for divine encounter, and several chunks (054, 113) have no purity content whatsoever. A minority of Mooney passages involve fasting-vigils (eagle killer, Kanasta) better served by the already-present fasting_and_prayer tag. Recommend cell-by-cell: keep the Eastman sweat-lodge/ablution cluster, reassign fast-vigil chunks to fasting_and_prayer and resemblance-tabu chunks to cosmic_sympathy, reject the rest.

**Reassign to:** fasting_and_prayer; cosmic_sympathy (per-chunk)

**Citations:** Charles Eastman, The Soul of the Indian — the eneepee (vapor-bath) as purification and re-creation of the spirit before spiritual crisis · James Mooney, Myths of the Cherokee — tabus operate 'upon the ground of an occult connection' (sympathetic resemblance), not pollution-removal · Joseph Epes Brown, The Sacred Pipe — Inipi as rite of purification among the Lakota (citation uncertain)

**Ruling:** ☐ keep ☐ reassign ☐ mixed ☐ reject — 


## 8. detachment_gelassenheit × hinduism (n=26) — proposed: **keep**

*Eckhart's Abgeschiedenheit/Gelassenheit — radical letting-go of will, image, and grasping that opens the soul to God; distinct from inner_silence (quietness) and from material renunciation, and adjacent to Sufi tark and Buddhist non-grasping as a practice rather than a metaphysical claim.* (family `praxis.contemplative_practice`)

**Home move:**
> real sanctification consists in this that the spirit remain as immovable and unaffected by all impact of love or hate, joy or sorrow, honour or shame, as a huge mountain is unstirred by a gentle breeze... to be empty of all creature's love is to be full of God, and to be full of creature-love is to be empty of God.
> — `christian_mysticism.eckhart-sermons-field.017`
> Death and life, preservation and ruin, failure and success, poverty and wealth, superiority and inferiority, blame and praise, hunger and thirst, cold and heat;--these are the changes of circumstances... They are not sufficient therefore to disturb the harmony (of the nature), and are not allowed to enter into the treasury of intelligence.
> — `taoism.zhuangzi-inner-chapters-index.036`

**What the cell actually contains:**
> Your business is with action alone; not by any means with fruit. Let not the fruit of action be your motive (to action)... perform actions, casting off (all) attachment, and being equable in success or ill-success; (such) equability is called devotion.
> — `hinduism.bhagavad-gita-chapter-02.003` · The signature nishkama-karma move: detachment from the fruits of action while continuing to act — detachment inside obligation, not withdrawal from it.
> The man who, casting off all desires, lives free from attachments, who is free from egoism, and from (the feeling that this or that is) mine, obtains tranquillity. This, O son of Pritha! is the Brahmic state.
> — `hinduism.bhagavad-gita-chapter-02.004` · Letting-go of desire, egoism, and 'mine' as the gate to the divine state — maps nearly clause-for-clause onto Eckhart's emptiness-of-creatures that fills with God.
> Dedicating all actions to me with a mind knowing the relation of the supreme and individual self, engage in battle without desire, without (any feeling that this or that is) mine, and without any mental trouble.
> — `hinduism.bhagavad-gita-chapter-03.002` · God-directed releasement of will — the structurally closest match to Gelassenheit proper: the will is surrendered upward, not merely stilled.
> who sitting like one unconcerned is never perturbed by the qualities... to whom a sod and a stone and gold are alike; to whom what is agreeable and what is disagreeable are alike... who is alike in honour and dishonour.
> — `hinduism.bhagavad-gita-chapter-14.002` · Equanimity portrait almost identical to the Eckhart mountain simile and Zhuangzi's undisturbed harmony — same phenomenology of the detached agent.
> This threefold penance, practised with perfect faith, by men who do not wish for the fruit, and who are possessed of devotion is called good.
> — `hinduism.bhagavad-gita-chapter-17.001` · Thin tag: detachment appears only as a classificatory criterion inside the guna-typology of penance/food/gifts — chapter-level spillover rather than a passage about the practice itself.

**Analysis:** The tagged passages genuinely make the family move: radical letting-go of desire, fruit, and 'mine', producing an unmoved equanimity that matches the Eckhart and Zhuangzi exemplars almost line for line, and the theistic strand (dedicating all action to Krishna) is closer to Gelassenheit's God-directed surrender of will than to wu-wei's effortlessness. The concept already functions corpus-wide as the generic detachment slot — the definition explicitly folds in Buddhist non-grasping, and buddhism carries dozens of these tags — so hinduism's inclusion is consistent practice, not a false friend. The Gita's distinctive contribution is detachment exercised in the midst of obligatory action with fruits renounced (and ch. 18's tyaga-vs-sannyasa distinction even mirrors the definition's 'distinct from material renunciation' clause). A minority of the 26 tags are thin chapter-level spillover (11.004, 17.001, 17.002, 8.001, 6.003) where detachment surfaces only as a passing epithet or criterion. Keep the cell; if the curator wants finer grain a nishkama_karma split is defensible, but it would fragment a concept that is already deliberately pan-traditional.

**Split option:** `nishkama_karma` — The Gita's karma-yoga: action performed as duty or offering with renunciation of its fruits — detachment exercised within action rather than by withdrawal from it.

**Citations:** Bhagavad Gita 2.47 (Telang trans., SBE 8) — 'Your business is with action alone; not by any means with fruit' as the core karma-yoga formula · Bhagavad Gita 18.4-11 — tyaga defined as abandonment of fruit, not of prescribed action · Meister Eckhart, On Detachment (Field, Sermons) — the detached spirit unmoved as a mountain by a breeze (citation uncertain: Field collection sermon numbering) · Zhuangzi ch. 5, 'The Seal of Virtue Complete' (Legge trans., SBE 39) — changes of circumstance insufficient to disturb the harmony of the nature

**Ruling:** ☐ keep ☐ reassign ☐ mixed ☐ reject — 


## 9. soul_migration × hinduism (n=18) — proposed: **keep**

*The transmigration of the soul across lives.* (family `cosmology.soul_cosmology`)

**Home move:**
> on the other, we hear of its sin, its purification, its expiation; it is doomed to the lower world, it passes from body to body... The retreat and sundering, then, must be not from this body only, but from every alien accruement.
> — `neoplatonism.plotinus-select-works-index.012`
> If there be in them, as the opinion goes, human Souls that have sinned, then the Animating-Principle in its separable phase does not enter directly into the brute; it is there but not there to them.
> — `neoplatonism.plotinus-select-works-index.011`

**What the cell actually contains:**
> As a man, casting off old clothes, puts on others and new ones, so the embodied (self) casting off old bodies, goes to others and new ones... For to one that is born, death is certain; and to one that dies, birth is certain.
> — `hinduism.bhagavad-gita-chapter-02.002` · The canonical transmigration image, with an explicit persistent substrate: the unborn, everlasting embodied self changes bodies like clothes — the same soul-substrate model as the Plotinian home, not the Buddhist no-self rebirth.
> An eternal portion of me it is, which, becoming an individual soul in the mortal world, draws (to itself) the senses with the mind as the sixth. Whenever the ruler (of the bodily frame) obtains or quits a body, he goes taking these (with him) as the wind (takes) perfumes from (their) seats.
> — `hinduism.bhagavad-gita-chapter-15.001` · Explicit mechanics of the migrating soul carrying mind and senses between bodies — the closest structural parallel to the Platonic soul-vehicle model.
> When an embodied (self) encounters death, while goodness is developed, then he reaches the untainted worlds of those who know the highest... Likewise, dying during (the prevalence of) darkness, he is born in the wombs of the ignorant.
> — `hinduism.bhagavad-gita-chapter-14.001` · Moral quality at death determines the womb of rebirth — karmic steering of transmigration, matching Plotinus's sinful souls entering brutes.
> He who is fallen from devotion attains the worlds of those who perform meritorious acts, dwells (there) for many a year, and is afterwards born into a family of holy and illustrious men... There he comes into contact with the knowledge which belonged to him in his former body.
> — `hinduism.bhagavad-gita-chapter-06.003` · Cross-life continuity of one individual's acquired dispositions — personal identity persisting through rebirth.
> And having enjoyed that great heavenly world, they enter the mortal world when (their) merit is exhausted.
> — `hinduism.bhagavad-gita-chapter-09.001` · Cyclical return even from heaven — samsara encompassing celestial destinations, the full transmigration cosmology.

**Analysis:** This cell is not a false friend; it is the doctrine's historical source arriving late to the corpus. The tagged chunks contain the clothes simile, the born-must-die-must-be-born axiom, guna-at-death determining the womb of rebirth, personal continuity across births (6.003), and 15.001's explicit subtle-body mechanics of the soul carrying mind and senses between bodies. The substrate model is emphatically atman-based ('unborn, everlasting, unchangeable... not killed when the body is killed'), which is the same persistent-soul move as the neoplatonic home exemplars — if anything the Platonic tradition inherited the family resemblance, not the reverse. Chunk-level accuracy is high across all 18: only 12.001 is thin ('ocean of this world of death' with no actual transmigration claim) and 5.002 rests on 'for ever released from birth and death,' which still presupposes the doctrine. Keep.

**Citations:** Bhagavad Gita 2.22 (Telang trans., SBE 8) — the cast-off-clothes simile for the self taking new bodies · Bhagavad Gita 8.16 — 'All worlds up to the world of Brahman are destined to return; after attaining to me there is no birth again' · Plotinus, Enneads I.1.12 (MacKenna trans.) — the compound soul 'passes from body to body' and pays penalty · Plato, Phaedo 81e-82b — souls entering animal bodies according to character, the Greek metempsychosis parallel (citation uncertain)

**Ruling:** ☐ keep ☐ reassign ☐ mixed ☐ reject — 


## 10. self_knowledge × hinduism (n=17) — proposed: **keep**

*The recognition of one's own true divine nature as the primary path to liberation; 'know thyself' as soteriology.* (family `soteriology.knowledge_path`)

**Home move:**
> Withdraw into yourself and look... never can the soul have vision of the First Beauty unless itself be beautiful. Therefore, first let each become godlike and each beautiful who cares to see God and Beauty.
> — `neoplatonism.plotinus-select-works-index.064`
> Only he in whom is light can see the light... only the divinity in man can know God in and through man... by the awakening of that which is divine in him attains the self-consciousness of his own immortality.
> — `christian_mysticism.life-and-doctrines-boehme.058`

**What the cell actually contains:**
> nor has he who is not self-restrained perseverance in the pursuit of self-knowledge; there is no tranquillity for him who does not persevere in the pursuit of self-knowledge; and whence can there be happiness for one who is not tranquil?
> — `hinduism.bhagavad-gita-chapter-02.004` · The Telang translation uses the term 'self-knowledge' verbatim, as the pivot between discipline and liberation.
> But to those who have destroyed that ignorance by knowledge of the self, (such) knowledge, like the sun, shows forth that supreme (principle). And those whose mind is (centred) on it... go never to return, having their sins destroyed by knowledge.
> — `hinduism.bhagavad-gita-chapter-05.001` · Knowledge of the self destroys ignorance and directly ends rebirth — knowledge-path soteriology in its pure form.
> in which too, one seeing the self by the self, is pleased in the self... he who has devoted his self to abstraction, by devotion, looking alike on everything, sees the self abiding in all beings, and all beings in the self.
> — `hinduism.bhagavad-gita-chapter-06.002` · The reflexive vision — atman knowing atman — matching Plotinus's 'withdraw into yourself and look' move exactly.
> He who thus knows nature and spirit, together with the qualities, is not born again, however living. Some by concentration see the self in the self by the self.
> — `hinduism.bhagavad-gita-chapter-13.002` · Knowing the knower (Kshetrajna) terminates rebirth: recognition itself is the liberating act, which is the taxonomy definition almost word for word.
> An eternal portion of me it is, which, becoming an individual soul in the mortal world... Devotees making efforts perceive him abiding within their selfs.
> — `hinduism.bhagavad-gita-chapter-15.001` · Supplies the 'true divine nature' clause: the self to be known is an eternal portion of the Lord, so self-knowledge is literally recognition of one's own divinity.

**Analysis:** This is legitimate coverage, and plausibly the concept's best instantiation in the corpus: the taxonomy's formula — recognition of one's true divine nature as the primary path to liberation — is historically an Upanishadic/Vedantic doctrine (atma-jnana) that the neoplatonic and mystical homes echo, not the reverse. The tagged chunks carry every element of the definition: the literal term 'self-knowledge' (2.004), ignorance destroyed by knowledge of the self with cessation of rebirth as the direct result (5.001, 13.002), the reflexive seeing of the self by the self (6.002, 13.002), and the divinity of the known self as an eternal portion of Krishna (15.001, 13.001's Kshetrajna 'in all Kshetras'). The structure is identical to the home exemplars — Plotinus's withdraw-and-sculpt-yourself-godlike and Boehme's divinity-in-man knowing God — with the Gita stating the identity claim more strongly than either. Chunk-level accuracy is high across all 17; the thinnest are 18.004 (Arjuna's 'I now recollect myself' plus the 'sacrifice of knowledge') and 14.001 (knowing what is above the qualities), both still defensible. Keep with high confidence; if anything this cell strengthens the concept's cross-tradition definition.

**Citations:** Bhagavad Gita 2.64-66 (Telang trans., SBE 8) — tranquillity impossible without 'perseverance in the pursuit of self-knowledge' · Bhagavad Gita 13.23 — he who knows spirit and nature 'is not born again, however living' · Chandogya Upanishad 6.8.7 — tat tvam asi, the self identified with Brahman; the doctrinal root, though the corpus's hinduism holdings are currently Gita-only (citation uncertain as corpus evidence, standard as scholarship) · Plotinus, Enneads I.6.9 (MacKenna trans.) — 'Withdraw into yourself and look'; become godlike to see God · Franz Hartmann, Life and Doctrines of Jacob Boehme — only the divinity in man can know God

**Ruling:** ☐ keep ☐ reassign ☐ mixed ☐ reject — 
