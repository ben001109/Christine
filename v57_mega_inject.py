"""
V57 COMPRESSED_KB MEGA INJECTION - All Batches (2+3+4+5) in ONE script
Target: 77 -> 300+ entries
"""
import re, os

FILE = r"F:\christine\christine_final.py"
OUT_LOG = r"F:\christine\kb_inject_log.txt"

ALL_NEW_ENTRIES = [
    # ============================================================
    # BATCH 2: World History, Geography, Economics, etc. (+73)
    # ============================================================
    ("world history,history,ancient,civilization,human",
     "world history|ancient|civilization|human",
     "human history spans ~300,000 years. Key periods: Stone Age (tools/fire), Agricultural Revolution (~10,000 BC, farming→settlements), Bronze Age (3300 BC, metalwork/writing), Iron Age (1200 BC), Classical Antiquity (Greece/Rome), Middle Ages (476-1453), Renaissance (14-17th C), Age of Exploration (15-17th C), Scientific Revolution (16-17th C), Industrial Revolution (18-19th C), Modern Era (20th C+). Writing invented ~3400 BC in Sumer. Agriculture enabled population growth and complex societies."),

    ("ancient greece,greek,philosophy,democracy,athens,sparta",
     "ancient greece|greek|philosophy|democracy|athens|sparta",
     "Ancient Greece (800-146 BC) foundations of Western civilization. Athens: birthplace of democracy (direct democracy, male citizens voted). Sparta: military state. Philosophy: Socrates (questioning method), Plato (Republic, Forms), Aristotle (logic, empiricism). Homer's Iliad/Odyssey. Olympic Games began 776 BC. Alexander the Great conquered from Greece to India. Greek contributions: geometry (Euclid), physics (Archimedes), medicine (Hippocrates), theater (tragedy/comedy), architecture (Parthenon)."),

    ("roman empire,rome,roman,republic,caesar,colosseum",
     "roman empire|rome|roman|republic|caesar",
     "Roman civilization: Kingdom (753-509 BC)→Republic (509-27 BC)→Empire (27 BC-476 AD). Julius Caesar crossed Rubicon, became dictator, assassinated 44 BC. Augustus first Emperor. Peak: controlled Mediterranean, Western Europe, Middle East, North Africa. Engineering: roads, aqueducts, concrete, Colosseum. Latin→Romance languages. Roman law influenced modern legal systems. Fall of Western Rome 476 AD (barbarian invasions, economic decline, overexpansion). Eastern Roman (Byzantine) Empire lasted until 1453."),

    ("renaissance,rebirth,humanism,art,science revolution",
     "renaissance|rebirth|humanism",
     "Renaissance (14th-17th century) 'rebirth' of classical learning, originated in Florence, Italy. Humanism placed humans at center. Key figures: Leonardo da Vinci (polymath), Michelangelo (Sistine Chapel, David), Raphael, Machiavelli (The Prince). Gutenberg printing press (1440) revolutionized knowledge spread. Scientific Revolution: Copernicus (heliocentrism), Galileo (telescope observations), Kepler (planetary motion), Newton (gravity, calculus). Protestant Reformation: Martin Luther's 95 Theses (1517) split Christianity."),

    ("industrial revolution,steam engine,factory,urbanization",
     "industrial revolution|steam engine|factory|urbanization",
     "Industrial Revolution (1760-1840, Britain first) transformed agrarian societies into industrial ones. Key inventions: steam engine (Watt), spinning jenny, power loom, locomotive (Stephenson). Coal and iron drove growth. Factory system replaced cottage industry. Urbanization: mass migration to cities. Social impacts: child labor, pollution, wealth inequality, rise of middle class. Second Industrial Revolution (1870-1914): electricity, steel, chemicals, internal combustion engine. Led to labor movements, unions, and eventually welfare states."),

    ("world war 1,WWI,great war,trench warfare,versailles",
     "world war 1|WWI|great war|trench|versailles",
     "World War I (1914-1918): Allied Powers (Britain, France, Russia, USA) vs Central Powers (Germany, Austria-Hungary, Ottoman Empire). Triggered by assassination of Archduke Franz Ferdinand. Trench warfare on Western Front. New weapons: machine guns, poison gas, tanks, aircraft. ~17 million dead, ~20 million wounded. Russian Revolution 1917. Treaty of Versailles (1919) imposed harsh terms on Germany. League of Nations created. Ottoman Empire dissolved. Redrew European/Middle East borders. Seeds of WWII sown."),

    ("world war 2,WWII,nazi,holocaust,atomic bomb,normandy",
     "world war 2|WWII|nazi|holocaust|atomic|normandy",
     "World War II (1939-1945): Allies (UK, USSR, USA, China, France) vs Axis (Germany, Japan, Italy). Nazi Germany invaded Poland Sept 1, 1939. Holocaust: systematic murder of 6 million Jews + millions others. Key battles: Stalingrad, Midway, D-Day (Normandy, June 6 1944). Atomic bombs on Hiroshima and Nagasaki (Aug 1945). ~70-85 million dead (deadliest conflict in history). Led to United Nations, Cold War, decolonization, European integration."),

    ("cold war,iron curtain,space race,nuclear,USSR,USA",
     "cold war|iron curtain|space race|nuclear|USSR",
     "Cold War (1947-1991): geopolitical tension between USA (capitalism/democracy) and USSR (communism). Never direct military conflict but proxy wars (Korea, Vietnam, Afghanistan). Nuclear arms race: MAD (Mutually Assured Destruction). Space Race: Sputnik (1957), Gagarin first in space (1961), Apollo 11 Moon landing (1969). Berlin Wall built 1961, fell 1989. Cuban Missile Crisis (1962) closest to nuclear war. USSR dissolved Dec 25, 1991. NATO vs Warsaw Pact."),

    ("mongol empire,genghis khan,silk road,conquest",
     "mongol empire|genghis khan|silk road|conquest",
     "Mongol Empire (1206-1368): largest contiguous land empire in history (~24 million km2). Founded by Genghis Khan (Temujin), united nomadic tribes. Military innovations: cavalry tactics, composite bow, psychological warfare. Conquered China, Central Asia, Persia, Russia, Eastern Europe. Pax Mongolica enabled Silk Road trade. Kublai Khan founded Yuan Dynasty in China. Empire eventually split into four khanates. Facilitated cultural exchange but also devastation (estimated 40 million deaths)."),

    ("meiji restoration,japan modernization,emperor,samurai",
     "meiji restoration|japan|modernization|emperor|samurai",
     "Meiji Restoration (1868): overthrew Tokugawa shogunate, restored Emperor Meiji. Rapid modernization: abolished feudal system, created conscript army, built railroads, established parliament (Diet). Studied Western technology and institutions. Slogan: 'Rich Country, Strong Military'. Japan became first non-Western industrialized nation. Won Sino-Japanese War (1895), Russo-Japanese War (1905). Annexed Korea (1910). Samurai class abolished, replaced by modern military. Foundation for Japan as world power."),

    ("ancient egypt,pharaoh,pyramid,nile,hieroglyph",
     "ancient egypt|pharaoh|pyramid|nile|hieroglyph",
     "Ancient Egypt civilization (~3100-30 BC) along Nile River. Pharaohs were god-kings. Great Pyramid of Giza (built ~2560 BC for Khufu) is last surviving Ancient Wonder. Hieroglyphic writing decoded via Rosetta Stone (1822, Champollion). Mummification preserved bodies for afterlife. Innovations: 365-day calendar, papyrus, basic surgery, geometry for land surveying. New Kingdom peaked under Ramesses II. Cleopatra VII was last pharaoh before Roman conquest (30 BC). Nile's annual flooding enabled agriculture."),

    # ===== Geography =====
    ("continent,asia,europe,africa,americas,oceania,antarctic",
     "continent|asia|europe|africa|americas|oceania|antarctic",
     "Earth has 7 continents: Asia (largest, 4.7B people), Africa (2nd largest, Sahara desert), North America, South America (Amazon rainforest), Antarctica (coldest, no permanent residents), Europe, Oceania/Australia (smallest). Highest point: Mt Everest 8849m (Asia). Lowest: Dead Sea -430m. Longest river: Nile 6650km (debated with Amazon). Largest lake: Caspian Sea. Deepest ocean point: Mariana Trench 10994m."),

    ("ocean,pacific,atlantic,indian,arctic,marine",
     "ocean|pacific|atlantic|indian|arctic|marine",
     "Five oceans: Pacific (largest, deepest), Atlantic, Indian, Southern, Arctic. Oceans cover ~71% of Earth's surface. Ocean currents regulate global climate (Gulf Stream warms NW Europe). Tsunamis caused by underwater earthquakes, waves up to 800km/h. Mariana Trench deepest at 10994m. Coral reefs support 25% of marine species despite covering <1% of ocean floor. Ocean absorbs ~30% of human CO2 emissions (causing acidification)."),

    ("climate zone,tropical,temperate,polar,monsoon,weather",
     "climate zone|tropical|temperate|polar|monsoon|weather",
     "Koppen climate classification: Tropical(A), Dry(B), Temperate(C), Continental(D), Polar(E). Taiwan: subtropical monsoon (north) to tropical monsoon (south). Monsoons caused by land-sea temperature differences, crucial for Asian agriculture. El Nino (ENSO): Pacific sea temperature anomaly affecting global weather patterns. Jet streams guide weather systems at high altitude. Climate vs weather: climate is long-term average, weather is day-to-day."),

    ("plate tectonics,earthquake,volcano,ring of fire",
     "plate tectonics|earthquake|volcano|ring of fire",
     "Plate tectonics: Earth's crust divided into ~15 major plates floating on asthenosphere. Plate boundaries: convergent (mountains/trenches), divergent (rifts/mid-ocean ridges), transform (faults). Ring of Fire around Pacific has 75% of world's volcanoes, 90% of earthquakes. Taiwan sits on Eurasian and Philippine Sea Plate convergence zone, frequent earthquakes. Richter scale logarithmic: each number = 10x more ground motion. Tsunami early warning systems can save lives."),

    # ===== Economics =====
    ("macroeconomics,GDP,inflation,unemployment,fiscal",
     "macroeconomics|GDP|inflation|unemployment|fiscal",
     "Macroeconomics studies overall economy. GDP (Gross Domestic Product) measures total economic output. Inflation: sustained price increase, central banks target ~2%. Unemployment types: frictional (between jobs), structural (skills mismatch), cyclical (recession). Keynesian: government spending stabilizes economy. Monetarist: money supply matters most. Phillips curve: short-run inflation-unemployment tradeoff. Fiscal policy (government spending/taxes) vs monetary policy (interest rates/money supply)."),

    ("microeconomics,supply demand,market,utility,price",
     "microeconomics|supply|demand|market|utility|price",
     "Microeconomics studies individual/firm decisions. Supply and demand: price rises→supply up, demand down. Equilibrium where curves cross. Diminishing marginal utility: more consumption→less additional satisfaction. Market structures: perfect competition, monopoly, oligopoly, monopolistic competition. Elasticity measures sensitivity to price changes. Game theory analyzes strategic interactions (Nash equilibrium). Consumer surplus = willingness to pay minus actual price."),

    ("monetary policy,central bank,interest rate,QE,fed",
     "monetary policy|central bank|interest rate|QE|fed",
     "Monetary policy set by central banks. Lower interest rates stimulate borrowing/spending; higher rates curb inflation. Quantitative Easing (QE): central bank buys government bonds to inject liquidity. US Federal Reserve (Fed), ECB, BOJ policies affect global economy. Inflation targeting: most central banks aim for ~2%. Tools: open market operations, reserve requirements, discount rate. Zero lower bound problem led to negative interest rate policies in some countries."),

    ("international trade,tariff,free trade,comparative advantage,WTO",
     "international trade|tariff|free trade|comparative advantage|WTO",
     "Comparative advantage (Ricardo): even if one country is less efficient at everything, specialization and trade benefit both. WTO promotes global trade liberalization. Tariffs protect domestic industries but raise consumer costs. Regional trade agreements: RCEP, CPTPP reduce barriers among members. Balance of trade: exports minus imports. Exchange rates affect competitiveness. Globalization increased interconnection but also inequality debates."),

    # ===== Law =====
    ("constitutional law,constitution,rights,judicial review",
     "constitutional law|constitution|rights|judicial review",
     "Constitution is supreme law, defines government structure and citizen rights. Separation of powers (executive, legislative, judicial) provides checks and balances. Fundamental rights: free speech, religion, equality, privacy. Judicial review allows courts to invalidate unconstitutional laws. Taiwan's Constitutional Court (formerly Council of Grand Justices) safeguards constitutional supremacy. Rule of law: everyone subject to law, including government."),

    ("criminal law,crime,punishment,presumption of innocence",
     "criminal law|crime|punishment|presumption of innocence",
     "Criminal law defines offenses and penalties. Principles: no crime without law (nullum crimen sine lege), presumption of innocence (burden on prosecution). Elements: actus reus (guilty act) + mens rea (guilty mind). Punishments: imprisonment, fines, probation, death penalty (abolished in many countries). Due process protections: right to counsel, fair trial, protection against self-incrimination, double jeopardy."),

    ("civil law,contract,tort,property,obligation",
     "civil law|contract|tort|property|obligation",
     "Civil law governs private relationships. Contract law requires mutual agreement (offer and acceptance). Tort law handles non-contractual damages, requires proving negligence and causation. Property law defines ownership, mortgages, easements. Freedom of contract principle respects party autonomy. Statute of limitations sets time limits for legal claims. Civil vs common law systems: civil law (codified, most of world) vs common law (precedent-based, UK/US tradition)."),

    # ===== Medicine =====
    ("human body,anatomy,organ,system,physiology",
     "human body|anatomy|organ|system|physiology",
     "Human body has 11 organ systems: skeletal (206 bones), muscular (600+ muscles), cardiovascular (heart pumps ~7500L/day), respiratory (lungs, gas exchange), digestive (9m tract), nervous (86B neurons), endocrine (hormones), immune (defense), urinary (filtration), reproductive, integumentary (skin, largest organ). Homeostasis maintains internal balance. Average adult: 60% water, 37 trillion cells. DNA in each cell ~2m long if stretched."),

    ("immune system,immunity,vaccine,antibody,pathogen",
     "immune system|immunity|vaccine|antibody|pathogen",
     "Immune system: innate (barriers, inflammation, NK cells) and adaptive (T cells, B cells, antibodies). Antibodies are Y-shaped proteins that bind specific antigens. Vaccines train immune memory without causing disease. Types: mRNA (Pfizer/Moderna COVID), viral vector (AZ), inactivated, subunit. Autoimmune diseases: immune system attacks own body (lupus, rheumatoid arthritis, Type 1 diabetes). Immunotherapy revolutionized cancer treatment (checkpoint inhibitors, CAR-T)."),

    ("genetics,DNA,gene,chromosome,heredity,mutation",
     "genetics|DNA|gene|chromosome|heredity|mutation",
     "DNA double helix carries genetic information using 4 bases: A-T, C-G. Human genome: ~3.2 billion base pairs, ~20,000 protein-coding genes, 23 chromosome pairs. Mendel's laws: dominant/recessive inheritance. Mutations can be beneficial, neutral, or harmful. CRISPR-Cas9 enables precise gene editing. Epigenetics: gene expression changes without DNA sequence changes. Genetic disorders: sickle cell, cystic fibrosis, Down syndrome (trisomy 21). Human Genome Project completed 2003."),

    ("neuroscience,brain,neuron,synapse,cognition",
     "neuroscience|brain|neuron|synapse|cognition",
     "Human brain: ~86 billion neurons, ~100 trillion synapses. Weighs ~1.4kg, uses 20% of body's energy. Major regions: frontal lobe (planning, personality), temporal (language, memory), parietal (sensory), occipital (vision), cerebellum (coordination), brainstem (vital functions). Neurons communicate via electrical impulses and chemical neurotransmitters (dopamine, serotonin, GABA, glutamate). Neuroplasticity: brain rewires throughout life. fMRI and EEG are key imaging tools."),

    ("pharmacology,drug,medicine,dosage,side effect",
     "pharmacology|drug|medicine|dosage|side effect",
     "Pharmacology studies drug effects on the body. Pharmacokinetics (ADME): Absorption, Distribution, Metabolism, Excretion. Pharmacodynamics: how drugs affect the body (receptor binding, enzyme inhibition). Drug development: preclinical→Phase I-III trials→approval (10-15 years, ~$2.6B average). Side effects result from off-target actions. Drug interactions can be dangerous. Antibiotics fight bacteria (not viruses). Antibiotic resistance is a global health crisis (overuse)."),

    ("mental health,depression,anxiety,therapy,psychology",
     "mental health|depression|anxiety|therapy|psychology",
     "Mental health disorders affect 1 in 4 people globally. Depression: persistent sadness, loss of interest, fatigue, affects 280M people. Anxiety disorders: excessive worry, panic attacks. PTSD: after traumatic events. Treatments: psychotherapy (CBT most evidence-based), medication (SSRIs, SNRIs), exercise, mindfulness. Stigma remains barrier to seeking help. Suicide prevention: listening, asking directly, crisis hotlines. Brain chemistry (serotonin, dopamine) and life circumstances both contribute."),

    ("epidemiology,public health,pandemic,disease,prevention",
     "epidemiology|public health|pandemic|disease|prevention",
     "Epidemiology studies disease patterns in populations. Key measures: incidence (new cases), prevalence (total cases), mortality rate. R0 (basic reproduction number): average infections from one case. Pandemic: global disease spread. Historical pandemics: Black Death (1347-1351, ~50M dead), 1918 Spanish Flu (~50M), COVID-19 (2020+, ~7M+ confirmed dead). Public health tools: vaccination, sanitation, quarantine, contact tracing, surveillance. Preventive medicine saves more lives than curative."),

    ("nutrition,vitamin,mineral,diet,calorie,macronutrient",
     "nutrition|vitamin|mineral|diet|calorie|macronutrient",
     "Macronutrients: carbohydrates (4 cal/g, energy), proteins (4 cal/g, building blocks), fats (9 cal/g, hormones/insulation). Essential vitamins: A (vision), B-complex (energy metabolism), C (immunity/collagen), D (bones, from sunlight), E (antioxidant), K (blood clotting). Key minerals: calcium (bones), iron (blood), zinc (immunity), magnesium (300+ reactions). Recommended daily calories: ~2000-2500 (varies). Balanced diet: varied, moderate, nutrient-dense."),

    # ===== Technology =====
    ("semiconductor,chip,transistor,TSMC,Moore law",
     "semiconductor|chip|transistor|TSMC|Moore",
     "Semiconductors are materials with conductivity between conductors and insulators (silicon most common). Transistors are tiny switches, basis of all digital electronics. Moore's Law: transistor count doubles every ~2 years (slowing but continuing). Modern chips have billions of transistors at nanometer scale. TSMC (Taiwan) leads advanced manufacturing (3nm, 2nm coming). Process: design (EDA tools)→photolithography (ASML EUV)→etching→doping→packaging. Chips are in everything: phones, cars, appliances, medical devices."),

    ("5G,6G,wireless,mobile network,spectrum,latency",
     "5G|6G|wireless|mobile|spectrum|latency",
     "5G: 5th generation mobile network. Speed up to 20 Gbps (100x 4G), latency <1ms, 1M devices/km2. Uses mmWave (high speed, short range), sub-6GHz (balance), low-band (coverage). Enables IoT, autonomous vehicles, remote surgery, AR/VR. Network slicing provides virtual dedicated networks. 6G research for 2030s: THz frequencies, AI-native, sensing+communication, speeds up to 1 Tbps. Challenges: infrastructure cost, coverage gaps, health concerns (unfounded for current tech)."),

    ("IoT,internet of things,smart home,sensor,connected",
     "IoT|internet of things|smart home|sensor|connected",
     "Internet of Things: physical devices connected to internet. Applications: smart home (thermostat, lights, locks), industrial IoT (predictive maintenance), wearables (health monitoring), smart cities (traffic, energy), agriculture (soil sensors, drones). Estimated 75+ billion IoT devices by 2025. Protocols: MQTT, CoAP, Zigbee, Z-Wave, LoRaWAN. Challenges: security vulnerabilities, privacy, interoperability, power management. Edge computing processes data locally to reduce latency."),

    ("cloud computing,AWS,Azure,SaaS,PaaS,IaaS",
     "cloud computing|AWS|Azure|SaaS|PaaS|IaaS",
     "Cloud computing delivers computing services over internet. Models: IaaS (virtual machines - AWS EC2), PaaS (development platform - Heroku), SaaS (software - Gmail/Office365). Deployment: public, private, hybrid, multi-cloud. Major providers: AWS (32%), Azure (22%), GCP (11%). Benefits: scalability, pay-as-you-go, global reach, reduced maintenance. Serverless computing (Lambda) executes code without managing servers. Kubernetes orchestrates containers. Cloud enables startups to scale without upfront hardware investment."),

    ("VR,AR,virtual reality,augmented reality,metaverse,XR",
     "VR|AR|virtual reality|augmented reality|metaverse|XR",
     "VR (Virtual Reality): fully immersive digital environment via headset (Meta Quest, Apple Vision Pro). AR (Augmented Reality): digital overlays on real world (Pokemon Go, HoloLens). MR/XR: spectrum of real-virtual blending. Applications: gaming, training (medical/military), education, remote collaboration, therapy (PTSD/phobia treatment), architecture visualization. Challenges: motion sickness, resolution, field of view, social isolation. Apple Vision Pro (2024) introduced 'spatial computing' concept."),

    ("autonomous driving,self driving,ADAS,lidar,Tesla",
     "autonomous driving|self driving|ADAS|lidar|Tesla",
     "Autonomous driving levels (SAE): L0 (no automation)→L5 (full automation). Current: mostly L2-L3 (Tesla Autopilot/FSD, Waymo L4 in limited areas). Sensors: cameras, LiDAR (laser ranging), radar, ultrasonic. AI processes sensor fusion, path planning, decision making. Tesla camera-only approach vs Waymo LiDAR approach. Challenges: edge cases, weather, regulation, liability, ethical decisions (trolley problem). Potential: reduce 94% of accidents (human error), mobility for elderly/disabled."),

    ("renewable energy,solar,wind,hydropower,green energy",
     "renewable energy|solar|wind|hydropower|green",
     "Renewable energy from naturally replenishing sources. Solar: photovoltaic cells convert sunlight to electricity, cost dropped 90% since 2010. Wind: turbines convert kinetic energy, offshore wind growing rapidly. Hydropower: largest renewable source, dams generate electricity. Geothermal: Earth's internal heat. Biomass: organic material. Solar+wind now cheapest new electricity in most of world. Challenges: intermittency (need storage), grid integration, land use, materials (rare earths). Global target: net-zero emissions by 2050."),

    ("battery technology,lithium,solid state,energy storage",
     "battery|lithium|solid state|energy storage",
     "Lithium-ion batteries dominate (phones, EVs, grid storage). Energy density ~250-300 Wh/kg. Solid-state batteries promise 2-3x density, safer (no liquid electrolyte), target 2027-2030 mass production (Toyota, Samsung SDI). Sodium-ion batteries: cheaper, abundant materials, lower density. Flow batteries for grid-scale storage. Battery degradation: ~2-3% capacity loss per year. Recycling critical for sustainability (lithium, cobalt, nickel recovery). Global battery market: $100B+ by 2025."),

    ("3D printing,additive manufacturing,prototype,material",
     "3D printing|additive manufacturing|prototype",
     "3D printing builds objects layer by layer from digital models. Technologies: FDM (plastic filament, most common), SLA (resin, high detail), SLS (powder sintering, strong parts), metal printing (DMLS/EBM). Materials: plastics, metals (titanium, steel), ceramics, concrete, bio-materials. Applications: rapid prototyping, custom medical implants, aerospace parts, dental, fashion, construction (3D-printed houses). Advantages: complexity is free, customization, reduced waste. Limitations: speed, size, material properties vs traditional manufacturing."),

    ("biotechnology,biotech,genetic engineering,CRISPR,GMO",
     "biotechnology|biotech|genetic engineering|CRISPR|GMO",
     "Biotechnology uses biological systems for products/processes. CRISPR-Cas9 (2012): revolutionary gene editing tool, precise DNA modification. Applications: gene therapy (sickle cell cure approved 2023), GMO crops (pest resistant, nutrient enhanced), biofuels, bioplastics, synthetic biology (designing new organisms). mRNA technology (COVID vaccines) opened new medical frontiers. Ethical debates: designer babies, gene drives, biosecurity. Global biotech market: $1.5T+ by 2030."),

    ("nanotechnology,nanotech,nanometer,nanomaterial",
     "nanotechnology|nanotech|nanometer|nanomaterial",
     "Nanotechnology operates at 1-100 nanometer scale (1nm = 10^-9 m, DNA ~2.5nm wide). Nanomaterials have unique properties due to quantum effects and high surface area. Carbon nanotubes: 100x stronger than steel at 1/6 weight. Graphene: single atom thick carbon sheet, excellent conductor. Applications: targeted drug delivery, water purification, solar cells, electronics, coatings. Nanoparticles in sunscreen (zinc oxide), stain-resistant fabrics. Concerns: potential toxicity, environmental impact of nanomaterials."),

    ("space exploration,NASA,SpaceX,Mars,ISS,rocket",
     "space exploration|NASA|SpaceX|Mars|ISS|rocket",
     "Space milestones: Sputnik (1957), Gagarin in space (1961), Moon landing (1969), Space Shuttle (1981-2011), ISS (1998-present), Mars rovers (Spirit/Opportunity/Curiosity/Perseverance). SpaceX revolutionized with reusable rockets (Falcon 9), Starship (largest ever rocket). NASA Artemis program aims to return humans to Moon. Mars colonization: SpaceX target 2030s, challenges include radiation, 7-month travel, thin atmosphere. James Webb Space Telescope (2021) peers to early universe. Commercial space tourism beginning (Blue Origin, Virgin Galactic)."),

    # ===== Chemistry =====
    ("chemistry,element,periodic table,chemical reaction,bond",
     "chemistry|element|periodic table|chemical|bond",
     "Chemistry studies matter and its transformations. 118 known elements organized in periodic table by atomic number. Chemical bonds: ionic (electron transfer, NaCl), covalent (electron sharing, H2O), metallic (electron sea, metals). Reactions: synthesis, decomposition, combustion, acid-base, redox. Mole: 6.022x10^23 particles (Avogadro's number). pH scale 0-14: <7 acidic, 7 neutral, >7 basic. Organic chemistry: carbon-based compounds (life chemistry). Catalysts speed reactions without being consumed."),

    ("organic chemistry,carbon,polymer,plastic,hydrocarbon",
     "organic chemistry|carbon|polymer|plastic|hydrocarbon",
     "Organic chemistry studies carbon compounds (carbon forms 4 bonds, enabling complex molecules). Hydrocarbons: alkanes (single bonds), alkenes (double), alkynes (triple). Functional groups determine properties: -OH (alcohol), -COOH (carboxylic acid), -NH2 (amine). Polymers: long chain molecules. Plastics are synthetic polymers (polyethylene, PET, nylon). Proteins, DNA, carbohydrates are biological polymers. Petrochemistry converts crude oil into fuels and chemicals. Green chemistry aims to reduce environmental impact."),

    # ===== Astronomy =====
    ("astronomy,star,galaxy,universe,Big Bang,cosmic",
     "astronomy|star|galaxy|universe|Big Bang|cosmic",
     "Universe began with Big Bang ~13.8 billion years ago. Observable universe: ~93 billion light-years diameter, ~2 trillion galaxies. Milky Way: ~200-400 billion stars, ~100,000 light-years across. Stellar evolution: nebula→protostar→main sequence→red giant→white dwarf/neutron star/black hole (depending on mass). Sun is a medium G-type star, ~4.6 billion years old, ~5 billion years left. Dark matter (~27%) and dark energy (~68%) make up 95% of universe (ordinary matter only ~5%)."),

    ("solar system,planet,Mars,Jupiter,Saturn,moon",
     "solar system|planet|Mars|Jupiter|Saturn|moon",
     "Solar system: Sun + 8 planets + dwarf planets + asteroids + comets. Inner rocky planets: Mercury, Venus, Earth, Mars. Outer gas/ice giants: Jupiter (largest, Great Red Spot), Saturn (rings), Uranus, Neptune. Pluto reclassified as dwarf planet (2006). Earth's Moon: only natural satellite, formed from giant impact ~4.5 BYA. Mars: thin CO2 atmosphere, evidence of past water, target for human colonization. Jupiter's Europa and Saturn's Enceladus may have subsurface oceans (possible life)."),

    ("dark energy,dark matter,expansion,cosmology,multiverse",
     "dark energy|dark matter|expansion|cosmology|multiverse",
     "Dark matter: invisible mass that doesn't emit light but has gravitational effects. Evidence: galaxy rotation curves, gravitational lensing, cosmic microwave background. Makes up ~27% of universe. Candidates: WIMPs, axions (not yet detected). Dark energy: mysterious force accelerating universe expansion. Discovered 1998 (Nobel 2011). Makes up ~68% of universe. Cosmological constant or quintessence. Multiverse theory: our universe may be one of many. String theory suggests 10^500 possible universes."),

    # ===== Linguistics =====
    ("linguistics,language,grammar,syntax,phonology",
     "linguistics|language|grammar|syntax|phonology",
     "Linguistics studies human language scientifically. Subfields: phonology (sound systems), morphology (word structure), syntax (sentence structure), semantics (meaning), pragmatics (context-dependent meaning). Chomsky's Universal Grammar: innate language faculty. ~7000 languages worldwide, many endangered. Language families: Indo-European (most speakers), Sino-Tibetan, Afro-Asiatic, Niger-Congo. Sapir-Whorf hypothesis: language influences thought. Sign languages are full natural languages with grammar."),

    # ===== Architecture =====
    ("architecture,building,design,skyscraper,style",
     "architecture|building|design|skyscraper|style",
     "Architectural styles through history: Ancient (pyramids, temples), Classical (Greek columns, Roman arches), Gothic (pointed arches, flying buttresses, cathedrals), Renaissance (symmetry, domes), Baroque (ornate), Neoclassical, Art Nouveau, Art Deco, Modernism (Bauhaus, less is more), Postmodern, Contemporary. Tallest building: Burj Khalifa 828m (Dubai). Sustainable architecture: green roofs, passive heating/cooling, LEED certification. Famous architects: Frank Lloyd Wright, Le Corbusier, Zaha Hadid, Tadao Ando."),

    # ===== Agriculture =====
    ("agriculture,farming,crop,soil,irrigation,food security",
     "agriculture|farming|crop|soil|irrigation|food security",
     "Agriculture feeds 8 billion people. Green Revolution (1960s): high-yield varieties, fertilizers, irrigation dramatically increased production. Major crops: rice, wheat, corn, soybeans. Modern techniques: precision agriculture (GPS/sensors), vertical farming, hydroponics (soilless), aquaponics (fish+plants). Challenges: climate change, soil degradation, water scarcity, biodiversity loss, pesticide resistance. Organic farming avoids synthetic chemicals. GMOs increase yield but controversial. ~30% of food globally is wasted."),

    # ===== Sociology =====
    ("sociology,society,social,inequality,culture,class",
     "sociology|society|social|inequality|culture|class",
     "Sociology studies human society and social behavior. Key thinkers: Marx (class conflict, capitalism), Durkheim (social solidarity, anomie), Weber (bureaucracy, social action). Social stratification: class, race, gender create unequal access to resources. Socialization: how individuals learn cultural norms. Institutions: family, education, religion, economy, government. Globalization connects but also creates tensions. Social media transforms communication, creates echo chambers, affects mental health."),

    # ===== Music =====
    ("music theory,note,chord,scale,rhythm,harmony",
     "music theory|note|chord|scale|rhythm|harmony",
     "Music theory: language for understanding music. Notes: C D E F G A B (12 semitones in octave). Scales: major (happy), minor (sad), pentatonic (5-note, universal). Chords: 3+ notes played together (major, minor, diminished, augmented, 7th). Time signatures: 4/4 (common), 3/4 (waltz), 6/8. Key: tonal center of a piece. Circle of fifths organizes key relationships. Intervals: distance between notes. Counterpoint: multiple independent melodies. Harmony = vertical (chords), melody = horizontal (sequence)."),

    ("classical music,baroque,romantic,symphony,composer",
     "classical music|baroque|romantic|symphony|composer",
     "Western classical music periods: Medieval (chant)→Renaissance (polyphony)→Baroque (1600-1750: Bach, Handel, Vivaldi)→Classical (1750-1820: Mozart, Haydn, Beethoven early)→Romantic (1820-1900: Beethoven late, Chopin, Tchaikovsky, Wagner)→Modern (1900+: Debussy, Stravinsky, Schoenberg). Symphony: large orchestral work. Concerto: soloist + orchestra. Sonata form: exposition-development-recapitulation. Opera combines music + drama + staging."),

    # ===== Sports =====
    ("sports science,exercise,training,physiology,performance",
     "sports science|exercise|training|physiology|performance",
     "Exercise physiology: aerobic (cardio, uses oxygen) vs anaerobic (short intense bursts, without oxygen). VO2max measures cardiovascular fitness. Progressive overload principle: gradually increase training stress. Periodization: planned training variation. Recovery: sleep, nutrition, active recovery essential. Common injuries: ACL tear, stress fractures, tendinitis. Sports nutrition: carb loading, protein timing, hydration. Doping: prohibited performance-enhancing substances. Heart rate zones for training intensity."),

    # ===== Cooking =====
    ("cooking technique,culinary,sear,braise,saute,bake",
     "cooking technique|culinary|sear|braise|saute|bake",
     "Fundamental techniques: sauteing (high heat, little fat, quick), braising (sear then slow cook in liquid), roasting (dry heat in oven), grilling (direct heat), steaming (gentle, retains nutrients), poaching (gentle simmer in liquid), deep frying (submerge in hot oil). Maillard reaction (browning at 140-165C) creates flavor in seared meat, toast, coffee. Caramelization: sugars break down at high heat. Five mother sauces (Escoffier): bechamel, veloute, espagnole, hollandaise, tomato. Mise en place: prep everything before cooking."),

    # ===== Materials Science =====
    ("materials science,metal,ceramic,polymer,composite",
     "materials science|metal|ceramic|polymer|composite",
     "Materials science studies structure-property relationships. Metals: strong, conductive, ductile (steel, aluminum, titanium). Ceramics: hard, heat-resistant, brittle (glass, porcelain, silicon carbide). Polymers: lightweight, flexible (plastics, rubber, fiber). Composites: combine materials for superior properties (carbon fiber reinforced polymer, fiberglass, concrete). Smart materials: shape memory alloys, piezoelectrics, self-healing materials. Biomaterials for medical implants. Metamaterials: engineered structures with properties not found in nature."),

    # ===== Oceanography =====
    ("oceanography,marine biology,deep sea,coral reef,fishery",
     "oceanography|marine biology|deep sea|coral reef|fishery",
     "Oceanography: physical (currents, waves), chemical (salinity, pH), biological (marine life), geological (seafloor). Deep sea (>200m) is largest habitat on Earth, >80% unexplored. Hydrothermal vents support chemosynthetic life. Coral reefs: biodiversity hotspots, threatened by warming (bleaching) and acidification. Overfishing depletes stocks; sustainable fishing crucial. Plastic pollution: 8M tons enter oceans yearly, microplastics in food chain. Marine protected areas (MPAs) help conservation."),

    # ============================================================
    # BATCH 3: Advanced Science, Technology, Health (+47)
    # ============================================================
    ("quantum computing advanced,qubit,superposition,entanglement,error correction",
     "quantum computing advanced|qubit|superposition|entanglement|error correction",
     "Quantum computing uses quantum mechanics for computation. Qubit: quantum bit existing in superposition (0 and 1 simultaneously). Entanglement: qubits share state regardless of distance. Quantum gates manipulate qubits. Error correction is key challenge (Google Willow chip 2024 milestone). Algorithms: Shor's (factoring, breaks RSA), Grover's (search speedup). Current: NISQ era (Noisy Intermediate-Scale Quantum), 1000+ qubits but high error rates. Applications: drug discovery, cryptography, optimization, materials simulation."),

    ("nuclear energy,fission,fusion,reactor,radiation",
     "nuclear energy|fission|fusion|reactor|radiation",
     "Nuclear fission: splitting heavy atoms (uranium-235/plutonium-239) releases enormous energy. Commercial reactors generate ~10% of world electricity. Advantages: low carbon, reliable baseload. Risks: meltdown (Chernobyl 1986, Fukushima 2011), radioactive waste (half-life thousands of years), proliferation. Nuclear fusion: combining light atoms (hydrogen isotopes), powers the Sun. Fusion promises near-limitless clean energy but achieving sustained net-positive energy is extremely difficult. ITER experiment under construction in France."),

    ("hydrogen energy,fuel cell,green hydrogen,electrolysis",
     "hydrogen energy|fuel cell|green hydrogen|electrolysis",
     "Hydrogen as clean energy carrier: burns to produce only water. Green hydrogen: produced by electrolysis using renewable electricity. Grey hydrogen: from natural gas (most current production, creates CO2). Blue hydrogen: grey with carbon capture. Fuel cells convert hydrogen to electricity (used in Toyota Mirai, Hyundai Nexo). Challenges: storage (high pressure/cryogenic), infrastructure, efficiency losses in production-storage-use chain. Potential for heavy industry, shipping, aviation decarbonization."),

    ("carbon capture,CCS,CCUS,direct air capture,carbon removal",
     "carbon capture|CCS|CCUS|direct air capture|carbon removal",
     "Carbon capture and storage (CCS): capture CO2 from industrial sources, transport and store underground. Direct Air Capture (DAC): removes CO2 directly from atmosphere (Climeworks, Carbon Engineering). CCUS adds utilization (CO2→fuels, building materials, chemicals). Currently captures ~45 Mt CO2/year (need 6000+ Mt by 2050 for net-zero). Enhanced weathering: spreading crusite minerals to absorb CO2. Biochar: charcoal from biomass locks carbon in soil. Trees and oceans are natural carbon sinks."),

    ("stem cells,regenerative medicine,cell therapy,iPSC",
     "stem cells|regenerative medicine|cell therapy|iPSC",
     "Stem cells can self-renew and differentiate into specialized cells. Types: embryonic (pluripotent, any cell type), adult (limited, tissue-specific), iPSC (induced pluripotent, reprogrammed adult cells, Yamanaka 2006 Nobel 2012). Applications: regenerating damaged tissues, disease modeling, drug testing. Clinical uses: bone marrow transplants (leukemia), skin grafts. Research frontiers: growing organoids (mini-organs), 3D bioprinting organs, treating Parkinson's, spinal cord injuries, diabetes."),

    ("traditional Chinese medicine,TCM,acupuncture,herbal,qi",
     "traditional Chinese medicine|TCM|acupuncture|herbal|qi",
     "Traditional Chinese Medicine (TCM): 2000+ year system based on qi (vital energy), yin-yang balance, five elements. Diagnosis: pulse taking, tongue observation, questioning. Treatments: herbal medicine (thousands of formulas), acupuncture (inserting needles at meridian points), cupping, moxibustion, tui na massage, qigong. Tu Youyou won 2015 Nobel Prize for extracting artemisinin (malaria drug) from traditional herb. Modern research examines TCM through clinical trials. Integration with Western medicine growing."),

    ("microbiome,gut bacteria,probiotics,flora,microbiota",
     "microbiome|gut bacteria|probiotics|flora|microbiota",
     "Human microbiome: ~38 trillion microorganisms (mostly bacteria) living in/on body, majority in gut. Gut-brain axis: bidirectional communication between gut bacteria and brain, affects mood, cognition. Functions: digest fiber, produce vitamins (K, B12), train immune system, protect against pathogens. Dysbiosis (imbalance) linked to obesity, diabetes, autoimmune diseases, depression. Probiotics add beneficial bacteria; prebiotics feed them (fiber-rich foods). Each person's microbiome is unique, shaped by diet, birth method, environment."),

    ("aging research,longevity,senescence,telomere,anti-aging",
     "aging research|longevity|senescence|telomere|anti-aging",
     "Aging: progressive decline in function. Hallmarks of aging (Lopez-Otin 2013/2023): genomic instability, telomere attrition, epigenetic alterations, loss of proteostasis, deregulated nutrient sensing, mitochondrial dysfunction, cellular senescence, stem cell exhaustion, altered intercellular communication, disabled macroautophagy, chronic inflammation, dysbiosis. Telomeres shorten with each cell division. Senolytics: drugs that kill senescent cells. Caloric restriction extends lifespan in animal models. Rapamycin, metformin, NAD+ boosters under study. Average human lifespan doubled in last 200 years."),

    ("addiction science,dopamine,reward,substance,behavioral",
     "addiction science|dopamine|reward|substance|behavioral",
     "Addiction: chronic brain disorder involving compulsive substance use or behavior despite harm. Dopamine reward pathway (ventral tegmental area→nucleus accumbens) hijacked by addictive substances/behaviors. Tolerance: need more for same effect. Dependence: withdrawal symptoms without substance. Substance addictions: alcohol, opioids, nicotine, cocaine, methamphetamine. Behavioral addictions: gambling, gaming, social media. Treatment: detox, CBT, motivational interviewing, medication-assisted (methadone, naltrexone, buprenorphine), support groups (12-step)."),

    ("exercise science,fitness,cardio,strength,flexibility",
     "exercise science|fitness|cardio|strength|flexibility",
     "WHO recommends: 150-300 min/week moderate or 75-150 min vigorous aerobic activity + 2 days strength training. Benefits: reduced cardiovascular disease, diabetes, cancer, depression, dementia risk. Cardio improves heart health and VO2max. Strength training builds muscle, increases metabolism, improves bone density. Flexibility and mobility prevent injury. HIIT (High-Intensity Interval Training): time-efficient, boosts metabolism. Exercise releases endorphins, BDNF (brain growth factor). Even 10 min walking has measurable health benefits."),

    ("sports psychology,mental game,flow state,visualization",
     "sports psychology|mental game|flow state|visualization",
     "Sports psychology optimizes mental performance. Flow state (Csikszentmihalyi): optimal performance zone, challenge matches skill level. Visualization/mental rehearsal: athletes mentally practice movements, activates same neural pathways as physical practice. Self-talk: positive internal dialogue improves performance. Goal setting: SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound). Pre-performance routines reduce anxiety. Growth mindset (Dweck): ability can be developed through effort. Choking under pressure: overthinking automated skills."),

    # ============================================================
    # BATCH 4: Brain Science, Taiwan, Chinese Culture (+35)
    # ============================================================
    ("brain plasticity,neuroplasticity,learning,rewiring",
     "brain plasticity|neuroplasticity|learning|rewiring",
     "Neuroplasticity: brain's ability to reorganize neural connections throughout life. Types: structural (physical changes in brain structure), functional (shifting functions to different regions). London taxi drivers have enlarged hippocampi from spatial navigation. Learning new skills creates new synaptic connections. Critical periods: windows of heightened plasticity in early development (language acquisition). Adult neuroplasticity enables recovery after stroke, learning new languages/instruments at any age. Meditation physically changes brain structure (increased grey matter in prefrontal cortex)."),

    ("consciousness,awareness,qualia,hard problem,mind",
     "consciousness|awareness|qualia|hard problem|mind",
     "Consciousness: subjective experience of awareness. Hard problem of consciousness (Chalmers 1995): why does physical brain processing give rise to subjective experience (qualia)? Easy problems: explaining cognitive functions. Major theories: Global Workspace Theory (Baars: consciousness as broadcasting), Integrated Information Theory (Tononi: phi measure of consciousness), Higher-Order Theories (consciousness requires self-awareness). Neural correlates of consciousness (NCC) studied via fMRI/EEG. Consciousness in AI: Chinese Room argument (Searle) vs functionalism."),

    ("memory mechanism,hippocampus,long term,short term,encoding",
     "memory mechanism|hippocampus|long term|short term|encoding",
     "Memory types: sensory (<1s), short-term/working memory (7 plus/minus 2 items, seconds-minutes), long-term (unlimited capacity). Long-term: declarative (explicit: episodic events + semantic facts) and procedural (implicit: skills, habits). Hippocampus crucial for encoding new declarative memories (Patient H.M. lost ability after removal). Consolidation: memories stabilize during sleep (replay). Retrieval: context-dependent, mood-congruent. Forgetting curve (Ebbinghaus): 70% lost within 24 hours without review. Spaced repetition optimizes retention."),

    ("placebo effect,nocebo,mind body,expectation,healing",
     "placebo effect|nocebo|mind body|expectation|healing",
     "Placebo effect: improvement from inert treatment due to expectation of benefit. Neurologically real: releases endorphins, dopamine, changes brain activity. Nocebo: negative effects from negative expectations. Placebo surgeries sometimes as effective as real ones for pain. Open-label placebos (patient knows it is placebo) still work in some cases. Stronger placebo effects: larger pills, injections over pills, branded over generic, more expensive, doctor confidence matters. Clinical trials use double-blind randomized controlled design to account for placebo."),

    ("circadian rhythm advanced,melatonin,SCN,jet lag,chronotype",
     "circadian rhythm advanced|melatonin|SCN|jet lag|chronotype",
     "Circadian rhythm: ~24-hour internal clock regulated by suprachiasmatic nucleus (SCN) in hypothalamus. Light→SCN→pineal gland suppresses melatonin (wakefulness); darkness→melatonin release (sleepiness). Chronotypes: morning larks vs night owls (partially genetic, shifts with age). Jet lag: circadian desynchronization from rapid time zone crossing. Social jet lag: mismatch between social schedule and biological clock. Disrupted circadian rhythm linked to cancer, metabolic disorders, depression. Light therapy helps SAD (Seasonal Affective Disorder) and circadian disorders."),

    ("dream science,REM,lucid dream,interpretation,sleep cycle",
     "dream science|REM|lucid dream|interpretation|sleep cycle",
     "Dreams primarily occur during REM sleep (rapid eye movement). Brain highly active during REM, body paralyzed (atonia prevents acting out dreams). Dream content: often incorporates recent experiences (day residue), emotional processing. Lucid dreaming: awareness of dreaming during dream, can sometimes control dream content. Techniques: reality testing, MILD (Mnemonic Induction). Theories: threat simulation (practice), memory consolidation, emotional regulation, random neural firing (activation-synthesis). Average person dreams 3-5 times per night but forgets most."),

    ("gut brain axis,enteric nervous system,serotonin,vagus",
     "gut brain axis|enteric nervous system|serotonin|vagus",
     "Gut-brain axis: bidirectional communication between gut and brain via vagus nerve, hormones, immune system, and microbiome metabolites. Enteric nervous system: 500 million neurons in gut (second brain). 95% of body's serotonin produced in gut. Gut bacteria produce neurotransmitters (GABA, dopamine, serotonin). Stress affects gut (IBS, inflammation); gut health affects mood (anxiety, depression). Vagus nerve stimulation being studied for depression treatment. Diet directly influences mental health through microbiome."),

    # ===== Taiwan History & Culture =====
    ("taiwan history,formosa,aboriginal,dutch,qing,japanese",
     "taiwan history|formosa|aboriginal|dutch|qing|japanese",
     "Taiwan history: indigenous peoples (16+ tribes, 6000+ years). Portuguese named it Formosa (beautiful island, 1542). Dutch colonial period (1624-1662), Koxinga (Zheng Chenggong) expelled Dutch. Qing Dynasty rule (1683-1895). Treaty of Shimonoseki: ceded to Japan (1895). Japanese colonial period (1895-1945): modernization, infrastructure, but cultural suppression. ROC took control 1945. 228 Incident (1947): uprising and massacre. Martial law (1949-1987, longest in world). Democratization in 1980s-90s. First direct presidential election 1996."),

    ("228 incident,white terror,martial law,taiwan democracy",
     "228 incident|white terror|martial law|taiwan democracy",
     "228 Incident (February 28, 1947): anti-government uprising in Taiwan after KMT monopoly agent beat tobacco vendor. Escalated to island-wide protests against KMT corruption and misrule. Military crackdown killed estimated 18,000-28,000 people. Followed by White Terror period (1949-1987): political persecution, estimated 140,000 imprisoned, 3,000-4,000 executed. Martial law lifted 1987 by President Chiang Ching-kuo. Democratization: opposition DPP founded 1986, first direct presidential election 1996, first peaceful power transfer 2000 (Chen Shui-bian)."),

    ("taiwan indigenous,aboriginal,austronesian,tribe,culture",
     "taiwan indigenous|aboriginal|austronesian|tribe|culture",
     "Taiwan indigenous peoples: 16 officially recognized tribes (~580,000 people, ~2.4% population). Austronesian language family origin: Taiwan is likely Austronesian homeland (6000+ years), languages spread to Philippines, Indonesia, Polynesia, Madagascar. Major tribes: Amis (largest), Atayal, Paiwan, Bunun, Tsou, Rukai, Puyuma, Saisiyat, Yami/Tao, Thao, Kavalan, Truku, Sakizaya, Sediq, Hla'alua, Kanakanavu. Rich oral traditions, weaving, carving, music. Harvest festivals are important cultural events."),

    ("hakka culture,hakka,hakka people,tung blossom,lei tea",
     "hakka culture|hakka|hakka people|tung blossom|lei tea",
     "Hakka people: Han Chinese subgroup, migrated south over centuries, maintain distinct culture and language. Taiwan Hakka: ~4.7 million (20% population), concentrated in Hsinchu, Miaoli, Taoyuan, Pingtung. Hakka cuisine: lei cha (ground tea), ban tiao (rice noodle strips), stir-fried dried squid, preserved vegetables (suan cai, mei gan cai). Cultural traits: emphasis on education, frugality, community solidarity. Tung Blossom Festival (April-May, Hakka villages). Hakka language preservation efforts in schools and media."),

    ("taiwan temple culture,mazu,folk religion,pilgrimage",
     "taiwan temple|mazu|folk religion|pilgrimage",
     "Taiwan has 12,000+ temples, one of highest densities in world. Folk religion blends Buddhism, Taoism, and local beliefs. Mazu (goddess of sea): most popular deity, Dajia Mazu pilgrimage is world's 3rd largest religious event (millions participate). Temple architecture: ornate wood/stone carvings, dragon columns, curved roofs. Activities: divination (throwing moon blocks, drawing fortune sticks), ghost month ceremonies, lantern festivals, temple fairs. Important deities: Mazu, Guan Gong, Earth God, Wang Ye, Avalokitesvara (Guanyin)."),

    ("taiwan night market,street food,bubble tea,cuisine",
     "taiwan night market|street food|bubble tea|cuisine",
     "Taiwan night markets are iconic cultural attractions. Famous markets: Shilin (Taipei), Fengjia (Taichung), Liuhe (Kaohsiung), Raohe (Taipei). Popular foods: stinky tofu (chou doufu), oyster omelette (o-a-jian), beef noodle soup, gua bao (pork belly bun), scallion pancake (cong you bing), pepper bun, braised pork rice (lu rou fan). Bubble tea (boba): invented in Taiwan 1980s (Chun Shui Tang or Hanlin Tea Room), now global phenomenon. Shaved ice (tsua-ping) with toppings. Night markets also have games, clothing, accessories."),

    ("TSMC semiconductor,taiwan chip,silicon shield",
     "TSMC semiconductor|taiwan chip|silicon shield",
     "TSMC (Taiwan Semiconductor Manufacturing Company): world's most advanced chip foundry. Founded 1987 by Morris Chang, pioneered pure-play foundry model. Global market share: ~55%+ of foundry revenue, 90%+ of advanced chips (<7nm). Key customers: Apple, NVIDIA, AMD, Qualcomm, MediaTek. Process technology: 3nm mass production, 2nm (N2) planned 2025-2026, A16 (1.6nm) in development. Silicon Shield: Taiwan's semiconductor dominance deters military conflict. Overseas fabs: Arizona (USA), Kumamoto (Japan), Dresden (Germany). Revenue ~$70B+."),

    ("taiwan earthquake preparedness,seismic,921,disaster",
     "taiwan earthquake|seismic|921|disaster",
     "Taiwan: highly seismic, sits on Eurasian/Philippine Sea Plate boundary. 921 Earthquake (Chi-Chi, Sept 21, 1999): magnitude 7.3, 2,415 dead, 11,305 injured, deadliest in modern Taiwan history. Preparedness: earthquake early warning system (seconds of alert), strict building codes (updated post-921), earthquake drills in schools. Drop-Cover-Hold On during quake. Emergency kit: water, food, flashlight, first aid, documents. Taiwan Seismological Center monitors 24/7. Buildings designed for seismic resistance (base isolation, dampers, Taipei 101's tuned mass damper)."),

    ("typhoon preparedness,storm,warning,taiwan weather",
     "typhoon preparedness|storm|warning|taiwan weather",
     "Taiwan averages 3-4 direct typhoon hits per year (season: June-November). Saffir-Simpson equivalent: tropical depression→tropical storm→severe typhoon→super typhoon. CWA (Central Weather Administration) issues sea/land warnings. Preparations: secure windows, stock water/food, charge devices, avoid mountains/rivers. Typhoon days: schools and offices close. Risks: flooding, landslides (especially in mountain areas), storm surge. Historical: Typhoon Morakot (2009) caused catastrophic mudslides in southern Taiwan (681 dead). Reservoir management critical during typhoon season."),

    # ===== Chinese Language & Culture =====
    ("mandarin linguistics,tones,pinyin,traditional chinese",
     "mandarin linguistics|tones|pinyin|traditional chinese",
     "Mandarin Chinese: 4 tones + neutral tone. Pinyin romanization system. Characters: traditional (Taiwan/HK) vs simplified (China). ~3000 characters for basic literacy, ~6000 for newspaper reading. Character types: pictographs (sun, moon, mountain), ideographs, compound ideographs, phono-semantic compounds (90%+). Stroke order matters for handwriting. Measure words required before nouns. No conjugation, no articles, minimal inflection. Topic-prominent language (topic-comment structure). ~1.1 billion native speakers, most spoken language by native speakers."),

    ("taiwanese hokkien,minnan,southern min,台語",
     "taiwanese hokkien|minnan|southern min",
     "Taiwanese Hokkien (Minnan/Southern Min): spoken by ~70% of Taiwan population. Originated from Fujian province (Quanzhou/Zhangzhou dialects). 7 tones (vs Mandarin 4). Has literary and colloquial readings for same character. Rich vocabulary for daily life, agriculture, food. Romanization: Pe-oh-ji (POJ), Tai-lo. Important cultural medium: Taiwanese opera (gezaixi), folk songs, proverbs. Language revitalization: Taiwanese classes in schools since 2001, public TV station (PTS Taiwan Minnan channel). UNESCO classifies as vulnerable language."),

    ("chinese calligraphy,brush,script,kaishu,xingshu",
     "chinese calligraphy|brush|script|kaishu",
     "Chinese calligraphy: art of writing Chinese characters with brush and ink. Five major scripts: seal script (zhuanshu, oldest), clerical script (lishu), regular script (kaishu, standard), running script (xingshu, semi-cursive), cursive/grass script (caoshu). Four Treasures of Study: brush, ink, paper (xuan paper), inkstone. Famous calligraphers: Wang Xizhi (Sage of Calligraphy), Yan Zhenqing, Su Shi, Zhao Mengfu. Calligraphy cultivates patience, discipline, aesthetic sense. UNESCO Intangible Cultural Heritage."),

    ("chinese poetry,tang dynasty,li bai,du fu,shi,ci",
     "chinese poetry|tang dynasty|li bai|du fu|shi|ci",
     "Chinese poetry peak during Tang Dynasty (618-907). Shi poetry: regulated verse with strict tonal patterns and parallelism. Li Bai (Li Po): Romantic poet, moonlight/wine/freedom themes. Du Fu: Realist poet, social conscience, called Poet Sage. Wang Wei: nature poet, Buddhist influence. Tang: ~49,000 poems by 2,200+ poets preserved. Song Dynasty ci: lyric poetry set to music, Li Qingzhao (greatest female poet), Su Shi. Classical Chinese poetry influences all East Asian literature. Forms: jueju (4 lines), lushi (8 lines), ci (irregular), qu."),

    ("chinese idioms,chengyu,proverb,wisdom,four character",
     "chinese idioms|chengyu|proverb|wisdom|four character",
     "Chengyu: four-character idioms, mostly from classical literature/history. Examples: 守株待兔 (wait by tree stump for rabbit = expect gains without effort), 画蛇添足 (draw snake add feet = ruin by overdoing), 对牛弹琴 (play lute to cow = cast pearls before swine), 卧薪尝胆 (sleep on brush, taste gall = endure hardship for revenge), 塞翁失马 (old man loses horse = blessing in disguise). Over 5,000 commonly used chengyu. Often contain historical allusions and condensed wisdom. Essential for literary Chinese proficiency."),

    ("chinese zodiac,shengxiao,twelve animals,lunar year",
     "chinese zodiac|shengxiao|twelve animals|lunar year",
     "Chinese Zodiac: 12-year cycle, each year represented by an animal. Order: Rat, Ox, Tiger, Rabbit, Dragon, Snake, Horse, Goat, Monkey, Rooster, Dog, Pig. Legend: order determined by race across river (rat rode on ox, jumped off to win). Combined with Five Elements (Wood/Fire/Earth/Metal/Water) for 60-year cycle. Personality associations: Dragon (ambitious, charismatic), Monkey (clever, curious), Tiger (brave, confident). Ben Ming Nian: your zodiac year considered unlucky (wear red for protection)."),

    ("24 solar terms,jieqi,seasons,agriculture calendar",
     "24 solar terms|jieqi|seasons|agriculture calendar",
     "24 Solar Terms (Jieqi): traditional Chinese calendar dividing year into 24 periods based on Sun's position. Spring: Lichun (start), Yushui (rain water), Jingzhe (awakening of insects), Chunfen (equinox), Qingming (tomb sweeping), Guyu (grain rain). Summer: Lixia, Xiaoman, Mangzhong, Xiazhi (solstice), Xiaoshu, Dashu. Autumn: Liqiu, Chushu, Bailu, Qiufen (equinox), Hanlu, Shuangjiang. Winter: Lidong, Xiaoxue, Daxue, Dongzhi (solstice), Xiaohan, Dahan. UNESCO Intangible Cultural Heritage 2016. Guides agriculture and daily life."),

    ("tea culture,gongfu tea,oolong,green tea,ceremony",
     "tea culture|gongfu tea|oolong|green tea|ceremony",
     "Tea originated in China (~2737 BC legend, Shennong). Six types: green (unoxidized), white (minimal), yellow (slight), oolong (partial, 10-80%), black/red (full), dark/puerh (fermented). Taiwan famous for: high mountain oolong (Ali Shan, Li Shan), Oriental Beauty, Dong Ding, Sun Moon Lake black tea. Gongfu tea ceremony: small Yixing clay teapot, multiple short infusions, appreciation of aroma/taste/appearance. Tea culture emphasizes patience, mindfulness, social bonding. Global tea production: ~6 million tons/year, China largest producer."),

    ("mahjong,tiles,strategy,social game",
     "mahjong|tiles|strategy|social game",
     "Mahjong: tile-based game for 4 players, originated in China ~19th century. 144 tiles: suits (bamboo/circles/characters 1-9), honors (winds/dragons), bonus (flowers/seasons). Goal: complete a winning hand (usually 4 sets + 1 pair). Taiwanese mahjong: 16 tiles per player, unique scoring rules. Strategies: reading discards, defensive play, choosing when to declare riichi/ready. Social importance in Chinese culture: family gatherings, festivals, social bonding. Variants: Japanese Riichi, Hong Kong, American. Cognitive benefits: memory, strategy, social engagement."),

    ("wuxia novels,martial arts fiction,jin yong,fantasy",
     "wuxia novels|martial arts fiction|jin yong|fantasy",
     "Wuxia: martial arts fiction genre, heroes with extraordinary fighting skills in historical settings. Jin Yong (Louis Cha): greatest wuxia author, works include Legend of the Condor Heroes, The Smiling Proud Wanderer, Demi-Gods and Semi-Devils. Gu Long: atmospheric, mystery-oriented style. Themes: loyalty, justice, honor, love, sacrifice, jianghu (martial arts world outside law). Influenced Chinese-language culture enormously: films, TV dramas, games, idioms. Wuxia values: righteousness (yi), martial virtue (wude), chivalry. New wuxia: modern adaptations with fantasy elements."),

    ("chinese opera,peking opera,kunqu,face painting",
     "chinese opera|peking opera|kunqu|face painting",
     "Chinese opera: traditional theater combining music, singing, dialogue, acrobatics, martial arts. Peking opera (jingju): most famous form, originated 18th century. Role types: sheng (male), dan (female), jing (painted face), chou (clown). Face paint (lianpu) colors indicate character: red (loyal), black (honest/fierce), white (treacherous), blue (cunning). Kunqu: oldest surviving form (600+ years), UNESCO Masterpiece. Other forms: Cantonese opera, Sichuan opera (face changing), Taiwanese gezaixi. Elaborate costumes, stylized movements, distinctive vocal techniques."),

    # ============================================================
    # BATCH 5: Math, CS, Economics, Law, Religion, Art, Environment,
    #          Politics, Philosophy, Physics, Psychology (+50)
    # ============================================================
    ("calculus,derivative,integral,limit,newton,leibniz",
     "calculus|derivative|integral|limit",
     "Calculus studies continuous change. Differentiation (derivatives) measures instantaneous rate of change. Integration calculates area under curves. Newton and Leibniz independently invented calculus. Fundamental theorem: differentiation and integration are inverse operations. Applications span physics, engineering, economics, and virtually all sciences. Chain rule, product rule, quotient rule for derivatives. Techniques of integration: substitution, integration by parts, partial fractions."),

    ("linear algebra,matrix,vector,eigenvalue,transformation",
     "linear algebra|matrix|vector|eigenvalue",
     "Linear algebra studies vector spaces and linear maps. Core concepts: matrices, determinants, eigenvalues and eigenvectors. Matrix multiplication represents composition of linear transformations. In machine learning, neural networks are essentially massive matrix operations. SVD (Singular Value Decomposition) widely used in data dimensionality reduction and recommendation systems. Basis vectors span a vector space. Linear independence, rank, null space are fundamental concepts."),

    ("statistics,probability,Bayes,distribution,hypothesis",
     "statistics|probability|Bayes|distribution|hypothesis",
     "Statistics analyzes data to infer patterns. Descriptive: mean, median, standard deviation summarize data. Inferential: draw conclusions about populations from samples. Bayes theorem: P(A|B)=P(B|A)P(A)/P(B), foundation of machine learning. Central limit theorem: sum of many independent random variables tends toward normal distribution. Hypothesis testing: null hypothesis, p-value, significance level. Distributions: normal, binomial, Poisson, exponential. Regression analysis models relationships between variables."),

    ("number theory,prime,Riemann,Fermat,cryptography math",
     "number theory|prime|Riemann|Fermat",
     "Number theory studies integer properties. Primes: numbers divisible only by 1 and themselves. Distribution of primes remains mysterious. Riemann Hypothesis (about prime distribution) is one of Millennium Prize Problems ($1M). Fermat's Last Theorem (x^n+y^n=z^n has no positive integer solutions for n>2) proved by Andrew Wiles in 1995. RSA encryption relies on difficulty of factoring large numbers into prime factors. Goldbach Conjecture: every even number >2 is sum of two primes (unproven)."),

    ("data structures,array,linked list,tree,stack,queue,hash",
     "data structures|array|linked list|tree|stack|queue|hash",
     "Data structures organize and store data. Array: O(1) random access. Linked List: O(1) insertion/deletion. Stack: Last-In-First-Out (LIFO). Queue: First-In-First-Out (FIFO). Tree: hierarchical structure, binary search tree averages O(log n) lookup. Hash Table: average O(1) lookup but worst case O(n). Heap: priority queue. Graph: nodes and edges for network/relationship modeling. Choosing right data structure is fundamental to efficient algorithms."),

    ("algorithms,sorting,complexity,big O,dynamic programming",
     "algorithms|sorting|complexity|big O|dynamic programming",
     "Algorithm: finite sequence of steps to solve a problem. Time complexity via Big O: O(1) constant, O(log n) logarithmic, O(n) linear, O(n log n) linearithmic, O(n^2) quadratic. Quicksort averages O(n log n), worst O(n^2). Dynamic programming: break problem into overlapping subproblems (memoization). Greedy: choose locally optimal at each step. Divide and conquer: split, solve, merge. Graph algorithms: BFS, DFS, Dijkstra shortest path, A* search."),

    ("operating system,OS,process,thread,memory management",
     "operating system|OS|process|thread|memory management",
     "OS manages hardware resources and provides application runtime environment. Core functions: process management (scheduling, synchronization), memory management (virtual memory, paging), file systems, I/O management. Linux kernel by Linus Torvalds, open source, dominates servers. Windows dominates desktop. Modern OS supports multitasking, multi-user, virtualization. Context switching between processes. Deadlock: circular dependency of resources. Containers (Docker) provide lightweight OS-level virtualization."),

    ("computer network,TCP,IP,HTTP,DNS,protocol,internet",
     "computer network|TCP|IP|HTTP|DNS|protocol|internet",
     "Computer networks use OSI 7-layer or TCP/IP 4-layer model. IP handles addressing and routing. TCP provides reliable end-to-end transport. HTTP is web application protocol; HTTPS adds TLS encryption. DNS translates domain names to IP addresses. Routers forward packets at network layer; switches forward frames at data link layer. WiFi uses IEEE 802.11 standard. IPv4 (32-bit, ~4.3B addresses) being replaced by IPv6 (128-bit). CDNs cache content closer to users for faster delivery."),

    ("database,SQL,NoSQL,relational,index,ACID",
     "database|SQL|NoSQL|relational|index|ACID",
     "Relational databases (RDBMS) store data in tables; SQL is query language. ACID properties ensure transaction reliability (Atomicity, Consistency, Isolation, Durability). Indexes speed queries but use space. NoSQL: document (MongoDB), key-value (Redis), column-family (Cassandra), graph (Neo4j). CAP theorem: consistency, availability, partition tolerance - can only have 2 of 3. ORM (Object-Relational Mapping) bridges objects and tables. Database sharding distributes data across servers."),

    ("compiler,interpreter,lexer,parser,AST,JIT",
     "compiler|interpreter|lexer|parser|AST|JIT",
     "Compiler transforms high-level language to machine code: lexical analysis, parsing, semantic analysis, optimization, code generation. Interpreter executes source code line by line (Python). JIT (Just-In-Time) compilation combines both (Java JVM, JavaScript V8). LLVM: modular compiler infrastructure supporting multiple language frontends. AST (Abstract Syntax Tree) represents program structure. Garbage collection automatically manages memory (Java, Python, Go). Compiled languages (C/C++/Rust) generally faster; interpreted (Python/JS) more flexible."),

    ("cryptography,encryption,RSA,AES,hash,blockchain,security",
     "cryptography|encryption|RSA|AES|hash|blockchain",
     "Cryptography protects information security. Symmetric encryption (AES): same key for encrypt/decrypt, fast. Asymmetric (RSA): public key encrypts, private key decrypts, good for key exchange. Hash functions (SHA-256): map arbitrary data to fixed-length digest, irreversible. Digital signatures verify identity and data integrity. Blockchain uses cryptography for decentralized trust. TLS/SSL secures web communications. Post-quantum cryptography: preparing for quantum computers that could break RSA."),

    ("software engineering,agile,CI CD,design patterns,SOLID",
     "software engineering|agile|CI CD|design patterns|SOLID",
     "Software engineering applies engineering principles to software development. Agile methods (Scrum, Kanban) emphasize iterative development and rapid feedback. CI/CD (Continuous Integration/Deployment) automates build, test, and release. Design patterns (GoF): Singleton, Factory, Observer, Strategy solve common problems. Version control (Git) tracks code changes. SOLID principles guide OOP design: Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion. Code review, testing (unit/integration/e2e), documentation are essential practices."),

    ("democracy,election,representative,separation of powers",
     "democracy|election|representative|separation of powers",
     "Democracy: citizens participate in political decisions. Direct democracy (Swiss referendums) vs representative democracy (elected officials). Presidential system (USA) vs parliamentary system (UK). Democratic elements: free and fair elections, rule of law, separation of powers, press freedom, minority rights protection. Taiwan achieved full democratization since 1996 direct presidential election. Electoral systems: first-past-the-post, proportional representation, mixed systems. Challenges: populism, misinformation, voter apathy, gerrymandering."),

    ("international relations,geopolitics,diplomacy,world order",
     "international relations|geopolitics|diplomacy|world order",
     "International relations studies state interactions. Realism emphasizes power and national interest. Liberalism values international institutions and cooperation. Constructivism focuses on ideas and identity. Post-Cold War US unipolarity shifting to multipolar world. US-China competition, Russia-Ukraine conflict, Indo-Pacific strategy reshape geopolitics. UN, G7, G20 are important multilateral platforms. Diplomacy, sanctions, alliances, and deterrence are key tools. Nuclear non-proliferation remains critical challenge."),

    ("education theory,pedagogy,constructivism,Montessori",
     "education theory|pedagogy|constructivism|Montessori",
     "Constructivism (Piaget, Vygotsky): learners actively construct knowledge rather than passively receive. Montessori education emphasizes self-directed learning and prepared environment. Bloom's taxonomy: remember, understand, apply, analyze, evaluate, create. Zone of Proximal Development (ZPD): level achievable with guidance. Flipped classroom: students self-study first, class time for discussion and practice. Multiple intelligences (Gardner): linguistic, logical, spatial, musical, bodily, interpersonal, intrapersonal, naturalist."),

    ("food science,processing,fermentation,Maillard,preservation",
     "food science|processing|fermentation|Maillard|preservation",
     "Food science studies food production, processing, preservation, and safety. Fermentation uses microorganisms for beneficial changes (wine, vinegar, yogurt, soy sauce). Pasteurization uses gentle heat to extend shelf life. Freeze-drying (lyophilization) preserves nutrition and flavor. Food additives: preservatives, emulsifiers, thickeners. Maillard reaction produces flavors and brown color in seared meat and baked goods. HACCP (Hazard Analysis Critical Control Points) ensures food safety."),

    ("existentialism,Sartre,Camus,Kierkegaard,freedom,absurd",
     "existentialism|Sartre|Camus|Kierkegaard|freedom|absurd",
     "Existentialism emphasizes individual existence precedes essence; humans must define themselves through choices. Kierkegaard: precursor, subjective truth and leap of faith. Sartre: 'condemned to be free,' bad faith is escaping freedom. Camus' absurdism: face meaningless universe yet rebel, like Sisyphus endlessly pushing boulder uphill. Heidegger: Dasein (being-there), authenticity vs they-self. Beauvoir: existentialist feminism, The Second Sex. Key theme: anxiety of radical freedom and responsibility."),

    ("ethics,utilitarianism,deontology,virtue ethics,moral",
     "ethics|utilitarianism|deontology|virtue ethics|moral",
     "Ethics studies morality. Utilitarianism (Bentham, Mill): actions judged by consequences, maximize overall happiness. Deontology (Kant): some actions inherently right or wrong regardless of outcome, categorical imperative. Virtue ethics (Aristotle): focus on character cultivation, golden mean. Trolley problem classic debate between utilitarian (pull lever) vs deontological (don't use person as means). Care ethics (Gilligan): emphasizes relationships and context. Applied ethics: bioethics, business ethics, environmental ethics, AI ethics."),

    ("epistemology,knowledge,truth,skepticism,rationalism",
     "epistemology|knowledge|truth|skepticism|rationalism",
     "Epistemology studies nature, sources, and limits of knowledge. Traditional definition: knowledge is justified true belief (JTB), challenged by Gettier problems. Empiricism (Locke, Hume): knowledge from sensory experience. Rationalism (Descartes, Leibniz): knowledge from reason. Kant synthesized both: knowledge requires sensory intuition and intellectual categories. Skepticism questions whether certain knowledge is possible. Scientific method: observation→hypothesis→experiment→theory. Paradigm shifts (Kuhn): revolutionary changes in scientific frameworks."),

    ("thermodynamics,entropy,energy conservation,heat engine",
     "thermodynamics|entropy|energy conservation|heat engine",
     "Four laws of thermodynamics: 0th establishes temperature concept. 1st (energy conservation): energy cannot be created or destroyed. 2nd: entropy (disorder) of isolated system always increases; heat flows from hot to cold spontaneously. 3rd: absolute zero cannot be reached. Carnot engine sets efficiency upper limit. Entropy increase explains arrow of time direction. Applications: engines, refrigerators, power plants, chemical reactions, black hole thermodynamics."),

    ("electromagnetism,Maxwell,electric field,magnetic,EM wave",
     "electromagnetism|Maxwell|electric field|magnetic|EM wave",
     "Maxwell's equations unified electricity and magnetism, predicted electromagnetic waves travel at speed of light. Electric fields created by charges (Coulomb's law). Magnetic fields created by currents (Ampere's law). Faraday's law: changing magnetic field induces electric field (electromagnetic induction, basis of generators). EM spectrum: radio waves→microwaves→infrared→visible light (380-700nm)→ultraviolet→X-rays→gamma rays. Light is visible portion of EM spectrum."),

    ("fluid mechanics,Bernoulli,viscosity,laminar,turbulent",
     "fluid mechanics|Bernoulli|viscosity|laminar|turbulent",
     "Fluid mechanics studies liquid and gas motion. Bernoulli principle: increased flow speed correlates with decreased pressure (airplane lift principle). Reynolds number determines flow regime: low = laminar (smooth), high = turbulent (chaotic). Navier-Stokes equations describe viscous fluid motion; existence and smoothness of solutions is a Millennium Prize Problem. Applications: aerodynamics, weather prediction, blood flow, pipe design, ocean currents."),

    ("reinforcement learning,RL,reward,Q-learning,policy,agent",
     "reinforcement learning|RL|reward|Q-learning|policy|agent",
     "Reinforcement learning: agent learns optimal policy through environment interaction and reward signals. Core concepts: state, action, reward, policy, value function. Q-learning estimates state-action pair values. Deep RL (DQN, PPO, SAC) combines deep learning for high-dimensional inputs. AlphaGo and AlphaFold demonstrated RL breakthrough capabilities. Applications: game playing, robotics, recommendation systems, autonomous driving, resource optimization."),

    ("computer vision,CNN,image recognition,object detection,YOLO",
     "computer vision|CNN|image recognition|object detection|YOLO",
     "Computer vision enables machines to understand visual information. CNN (Convolutional Neural Network) is core architecture: conv layers extract features, pooling layers reduce dimensions, FC layers classify. Milestones: AlexNet (2012), VGGNet, ResNet (residual connections). Object detection: YOLO (real-time), Faster R-CNN. Semantic segmentation: per-pixel classification. Vision Transformer (ViT) brings transformer architecture to vision tasks. Applications: autonomous driving, medical imaging, surveillance, AR."),

    ("generative AI,GPT,diffusion,Stable Diffusion,DALL-E,LLM",
     "generative AI|GPT|diffusion|Stable Diffusion|DALL-E|LLM",
     "Generative AI creates new content rather than just analyzing. Large Language Models (GPT series, Claude, LLaMA) based on transformer and large-scale pretraining. Diffusion models (Stable Diffusion, DALL-E, Midjourney) generate images from noise. GAN (Generative Adversarial Network): generator vs discriminator adversarial training. Multimodal models (GPT-4V) handle text and images simultaneously. Applications: writing, coding, art, music, video, design, drug discovery."),

    ("cognitive psychology,memory,attention,decision,bias",
     "cognitive psychology|memory|attention|decision|bias",
     "Cognitive psychology studies mental processes. Working memory capacity ~7 plus/minus 2 items (Miller's law). Attention is selective (cocktail party effect) and divisible. Kahneman dual-system theory: System 1 fast/intuitive, System 2 slow/analytical. Cognitive biases: confirmation bias, anchoring effect, availability heuristic, framing effect, Dunning-Kruger effect. These biases systematically affect judgment and decision-making. Understanding biases improves critical thinking."),

    ("social psychology,conformity,obedience,attribution,bystander",
     "social psychology|conformity|obedience|attribution|bystander",
     "Social psychology studies how social context affects behavior. Asch conformity experiment: group pressure changes judgment. Milgram obedience experiment: 65% administered maximum shock. Fundamental attribution error: overestimate personal factors, underestimate situational factors. Stanford prison experiment revealed role influence on behavior. Bystander effect: more people present, less likely anyone helps. Cognitive dissonance: discomfort from holding contradictory beliefs."),

    ("developmental psychology,Piaget,attachment,adolescence",
     "developmental psychology|Piaget|attachment|adolescence",
     "Developmental psychology studies psychological changes across lifespan. Piaget's four stages: sensorimotor, preoperational, concrete operational, formal operational. Attachment theory (Bowlby): securely attached infants develop healthier relationships. Erikson's eight stages span trust-vs-mistrust to integrity-vs-despair. Vygotsky: social interaction drives cognitive development. Adolescence: identity exploration (Erikson's identity vs role confusion). Moral development (Kohlberg): pre-conventional, conventional, post-conventional stages."),

    # ===== World Religions =====
    ("buddhism,Buddha,four noble truths,eightfold path,nirvana",
     "buddhism|Buddha|four noble truths|eightfold path|nirvana",
     "Buddhism founded by Siddhartha Gautama (~5th century BC, India). Core teachings: Four Noble Truths (suffering, origin of suffering, cessation, path), Eightfold Path, Twelve Links of Dependent Origination, Three Marks (impermanence, suffering, non-self). Major branches: Theravada (Southeast Asia), Mahayana (East Asia), Vajrayana/Tibetan. Goal: nirvana (liberation from cycle of rebirth). Emphasizes meditation, mindfulness, compassion. ~500 million followers globally."),

    ("christianity,Jesus,Bible,Catholic,Protestant,church",
     "christianity|Jesus|Bible|Catholic|Protestant|church",
     "Christianity: faith in Jesus Christ as Son of God and savior. Bible: Old Testament + New Testament. Three major branches: Catholic (Pope as leader), Eastern Orthodox, Protestant (from Luther's Reformation, 16th century). Core beliefs: Trinity (Father, Son, Holy Spirit), original sin and redemption, resurrection and eternal life. ~2.4 billion followers, largest religion. Christmas celebrates birth of Jesus, Easter celebrates resurrection. Sacraments: baptism, communion/Eucharist."),

    ("islam,Muhammad,Quran,five pillars,mosque,muslim",
     "islam|Muhammad|Quran|five pillars|mosque|muslim",
     "Islam founded by Prophet Muhammad in 7th century Arabia. Quran is supreme scripture. Five Pillars: Shahada (declaration of faith), Salat (5 daily prayers), Zakat (charity tax), Sawm (Ramadan fasting), Hajj (Mecca pilgrimage). Two major sects: Sunni (~85%) and Shia. Mosque is place of worship. Sharia: Islamic law covering all aspects of life. ~1.9 billion followers, second largest religion. Islam means 'submission to God' (Allah). Rich contributions to mathematics, astronomy, medicine, architecture."),

    ("hinduism,Veda,karma,dharma,brahman,reincarnation",
     "hinduism|Veda|karma|dharma|brahman|reincarnation",
     "Hinduism: world's oldest major religion, no single founder. Core texts: Vedas, Upanishads, Bhagavad Gita. Brahman: ultimate reality. Karma (actions determine future), Dharma (duty/righteousness), Samsara (cycle of rebirth), Moksha (liberation). Major deities: Brahma (creator), Vishnu (preserver), Shiva (destroyer). ~1.2 billion followers, primarily in India. Caste system historically influential but increasingly challenged. Festivals: Diwali (lights), Holi (colors). Yoga originated from Hindu spiritual practices."),

    ("taoism,Laozi,Dao De Jing,yin yang,wu wei,nature",
     "taoism|Laozi|Dao De Jing|yin yang|wu wei|nature",
     "Taoism rooted in Chinese philosophy and folk religion. Laozi's Dao De Jing: Dao (Way) as universal source, advocates wu wei (non-action, going with natural flow). Zhuangzi developed free-spirited and relativistic thought. Religious Taoism incorporates alchemy, longevity practices, talismans. Yin-Yang and Five Elements theory influenced Chinese medicine, feng shui, divination. Taoism profoundly shaped Chinese culture, art, literature, martial arts (Tai Chi). Concept of harmony with nature resonates with modern environmentalism."),

    # ===== Art History =====
    ("renaissance art,Leonardo,Michelangelo,Raphael,perspective",
     "renaissance art|Leonardo|Michelangelo|Raphael|perspective",
     "Renaissance art (14th-17th century) revived classical Greek-Roman aesthetics, emphasized humanism. Leonardo da Vinci: Mona Lisa, Last Supper, pioneered sfumato technique and anatomical accuracy. Michelangelo: Sistine Chapel ceiling, David sculpture. Raphael: School of Athens, perfect composition. Revolutionary techniques: linear perspective, chiaroscuro (light-shadow contrast). Patronage system (Medici family). Oil painting developed. Art shifted from purely religious to celebrating human form and achievement."),

    ("impressionism,Monet,Renoir,light,plein air,brushwork",
     "impressionism|Monet|Renoir|light|plein air",
     "Impressionism (1860s-1880s) revolutionized painting. Characteristics: plein air (outdoor) painting, capturing light changes, visible brushstrokes, bright colors. Monet's Impression Sunrise named the movement. Monet's water lilies series, Renoir's figures, Degas' dancers each distinctive. Post-Impressionism (Cezanne, Van Gogh, Gauguin) pushed further, laying foundation for modern art. Impressionists initially rejected by Salon, organized independent exhibitions. Changed art from depicting reality to capturing perception."),

    ("modern art,Picasso,cubism,abstract,surrealism,Duchamp",
     "modern art|Picasso|cubism|abstract|surrealism|Duchamp",
     "Modern art (late 19th-mid 20th century) broke traditions. Cubism (Picasso, Braque): multi-perspective fragmented forms. Abstract Expressionism (Pollock, de Kooning): spontaneous emotion. Surrealism (Dali, Magritte): dreams and subconscious. Duchamp's Fountain (urinal) challenged 'what is art.' Bauhaus unified art and industrial design. Pop Art (Warhol): commercial culture as art. Minimalism: stripped to essentials. Each movement reacted against predecessors, constantly expanding art's boundaries."),

    # ===== Environmental Science =====
    ("climate change,global warming,greenhouse,carbon emission",
     "climate change|global warming|greenhouse|carbon emission",
     "Climate change primarily caused by human greenhouse gas emissions (CO2, CH4). Global average temperature risen ~1.1C since pre-industrial era. Impacts: sea level rise, extreme weather increase, glacier melting, ecosystem destruction. Paris Agreement targets limiting warming to 1.5-2C. Carbon neutrality (net-zero emissions) is national target for many countries. Solutions: renewable energy transition, electric vehicles, carbon capture, improved energy efficiency, reforestation, carbon trading markets."),

    ("ecology,ecosystem,food chain,biodiversity,habitat",
     "ecology|ecosystem|food chain|biodiversity|habitat",
     "Ecology studies organism-environment interactions. Ecosystem = biotic community + abiotic environment. Food chain: producers→primary consumers→secondary consumers→apex predators. Biodiversity includes genetic, species, and ecosystem diversity. Current species extinction rate 100-1000x natural background (6th mass extinction). Keystone species have disproportionate ecosystem impact. Ecosystem services: pollination, water purification, carbon sequestration, soil formation. Conservation strategies: protected areas, habitat restoration, species reintroduction."),

    ("sustainability,SDGs,circular economy,ESG,green",
     "sustainability|SDGs|circular economy|ESG|green",
     "Sustainable development meets present needs without compromising future generations (Brundtland definition). UN 17 Sustainable Development Goals (SDGs) cover poverty elimination, quality education, climate action. Circular economy shifts from take-make-dispose to reduce-reuse-recycle. ESG (Environmental, Social, Governance) increasingly important for corporate evaluation and investment. Carbon footprint measurement. Life cycle assessment evaluates environmental impact from cradle to grave. Green finance channels capital toward sustainable projects."),

    # ===== Music Advanced =====
    ("music theory advanced,harmony,counterpoint,form,key,modulation",
     "music theory advanced|harmony|counterpoint|form|key|modulation",
     "Harmony studies chord structure and progression rules. Main chord functions: tonic (I), dominant (V), subdominant (IV). Counterpoint: technique of combining independent melodies (Bach's fugues are pinnacle). Sonata form: exposition, development, recapitulation. Twelve-tone technique (Schoenberg) broke tonal system, each pitch used equally. Jazz harmony: extended chords (9th, 11th, 13th), chord substitutions, improvisation over changes."),

    ("world cuisine,french,japanese,chinese,italian,cooking",
     "world cuisine|french|japanese|chinese|italian",
     "French cuisine: famous for sauces (bechamel, hollandaise), emphasizes technique. Japanese cuisine: fresh ingredients and seasonality, sushi, sashimi, tempura, ramen. Chinese cuisine: eight regional styles each distinctive (Sichuan spicy, Cantonese delicate). Italian cuisine: simple quality ingredients, pizza and pasta beloved worldwide. Thai cuisine: balance of sweet, sour, salty, spicy. Indian cuisine: complex spice blends (masala), regional diversity. Mexican cuisine: corn, beans, chili peppers foundation."),
]

print(f"Reading {FILE}...")
with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

print(f"File size: {len(content)} characters, {content.count(chr(10))+1} lines")

# Find the closing bracket of COMPRESSED_KB - search for the exact last entry
marker = "non-violent communication|NVC"
if marker not in content:
    marker = "nonviolent communication"
if marker not in content:
    # Try Chinese
    marker = "\u975e\u66b4\u529b\u6e9d\u901a"  # 非暴力溝通
if marker not in content:
    # Ultimate fallback: find the ] that closes COMPRESSED_KB before __init__
    print("WARNING: Could not find marker, using structural search")
    # Find COMPRESSED_KB = [
    kb_start = content.find("COMPRESSED_KB = [")
    if kb_start == -1:
        with open(OUT_LOG, "w", encoding="utf-8") as f:
            f.write("FATAL: COMPRESSED_KB not found!")
        print("FATAL: COMPRESSED_KB not found!")
        exit(1)
    # Find the corresponding ] - count brackets
    depth = 0
    kb_end = -1
    in_string = False
    escape = False
    for i in range(kb_start, min(kb_start + 200000, len(content))):
        ch = content[i]
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"' and not in_string:
            in_string = True
            continue
        if ch == '"' and in_string:
            in_string = False
            continue
        if in_string:
            continue
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                kb_end = i
                break
    if kb_end == -1:
        with open(OUT_LOG, "w", encoding="utf-8") as f:
            f.write("FATAL: Could not find closing ] of COMPRESSED_KB!")
        print("FATAL: Could not find closing ] of COMPRESSED_KB!")
        exit(1)
    bracket_pos = kb_end
else:
    pos = content.find(marker)
    # Find the next ']' that closes the list after this marker
    # First find the end of this tuple entry
    search_from = pos
    # Find '),\n' after marker (end of tuple)
    tuple_end = content.find("),", search_from)
    if tuple_end == -1:
        tuple_end = content.find(")\n", search_from)
    # Now find the ']' after the tuple end
    bracket_pos = content.find("]", tuple_end + 1)
    # Make sure this ] is the one closing COMPRESSED_KB (should be on a line with just whitespace + ])
    # Verify by checking what comes after
    after_bracket = content[bracket_pos:bracket_pos+50].strip()
    if not after_bracket.startswith("]"):
        with open(OUT_LOG, "w", encoding="utf-8") as f:
            f.write(f"WARNING: bracket verification issue. After bracket: {after_bracket[:50]}")

# Build the new entries string
new_entries_str = "\n    # ===== V57 Mega Knowledge Injection (Batch 2-5, auto-generated) =====\n"
for tags, patterns, answer in ALL_NEW_ENTRIES:
    # Escape any quotes in the strings
    tags_e = tags.replace('"', '\\"')
    patterns_e = patterns.replace('"', '\\"')
    answer_e = answer.replace('"', '\\"')
    new_entries_str += f'    ("{tags_e}",\n     "{patterns_e}",\n     "{answer_e}"),\n\n'

# Insert before the closing bracket
new_content = content[:bracket_pos] + new_entries_str + content[bracket_pos:]

print(f"Writing updated file...")
with open(FILE, "w", encoding="utf-8") as f:
    f.write(new_content)

# Count total entries
count_pattern = r'\(\s*[\[\("]'
# Better: count lines that start tuples in COMPRESSED_KB section
kb_start_new = new_content.find("COMPRESSED_KB = [")
kb_class = new_content.find("def __init__(self):", kb_start_new)
kb_section = new_content[kb_start_new:kb_class]

# Count tuple entries: lines starting with ( or containing ("
import re
entry_count = len(re.findall(r'^\s+\([\["]', kb_section, re.MULTILINE))
# Also count ([ style entries  
entry_count2 = len(re.findall(r'\(\s*\[', kb_section))
entry_count3 = len(re.findall(r'\(\s*"[^"]+",\s*$', kb_section, re.MULTILINE))

# Most reliable: count answer strings (3rd element of each tuple)
# Each entry has a pattern like: "answer text"),
entry_count_reliable = kb_section.count('"),')

log_msg = f"""=== V57 MEGA INJECTION COMPLETE ===
Entries added: {len(ALL_NEW_ENTRIES)}
Entry count methods: pattern1={entry_count}, pattern2={entry_count2}, pattern3={entry_count3}, reliable={entry_count_reliable}
New file size: {len(new_content)} characters
"""

with open(OUT_LOG, "w", encoding="utf-8") as f:
    f.write(log_msg)

print(f"SUCCESS! Added {len(ALL_NEW_ENTRIES)} new knowledge entries.")
print(f"Entry count (reliable): {entry_count_reliable}")
print(f"New file size: {len(new_content)} chars")
print(f"Log written to {OUT_LOG}")
