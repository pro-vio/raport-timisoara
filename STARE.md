# STARE — raport-timisoara (handoff · 2026-07-16)

---

# BAC Timișoara — stare la 2026-07-17 (sfârșit de zi)

Analiza EN VIII de mai jos e **încheiată și livrată** — nu se atinge. Firul activ e replicarea pe Bacalaureat.

**Livrabil: `bac.html`** — comis și publicat (commit `a51f051`, 2026-07-17).
- **[pro-vio.github.io/raport-timisoara/bac.html](https://pro-vio.github.io/raport-timisoara/bac.html)** — linkul public, verificat live. Se reconstruiește la fiecare `git push` pe `main` (build Pages ~1 min; verifică cu `gh api repos/pro-vio/raport-timisoara/pages/builds/latest`).
- [Artifact](https://claude.ai/code/artifact/c1a11bbf-3384-4038-bc9b-7fd10e339d45) — aceeași pagină, pt iterare din chat. Republicare: `python scripts/build_bac_html.py`, apoi Artifact pe același `file_path` (păstrează URL-ul).
- În repo: 7,6 MB (bac.html + 5 JSON-uri derivate + 11 scripturi). Cele 281 MB de surse brute sunt în `.gitignore` — se redescarcă cu `download_bac.py`.

Pași: 1. descărcare ✅ · 2. inventar ✅ · 3. extracție ✅ · 4. distribuții ✅ · 5. teste structurale ✅ ·
6. shrinkage ✅ · 7. raport ✅ (3 taburi). **Fereastra: 2017-2025, 9 ani.**

## Regula #1: NU CITI CSV-urile ministerului

Greșeala zilei, și merită scrisă mare. Prima versiune prefera CSV-ul „ca să nu depindem de ODS" și
pierdea 1,8% din rânduri în 2017 și 2019: separatorul zecimal e virgulă ne-quotată, „6,31" devine două
câmpuri, iar nota **nu se poate reconstrui** — „5,6 · 9" și „5 · 6,9" sunt amândouă valide și dau medii
diferite. Am construit un solver combinatoric cu ancore ca să compensez. Degeaba: aceleași seturi de pe
data.gov.ro conțin **ODS (2017)** și **XLSX (2019)**, cu valorile ca numere.
**Verifică toate resursele setului (`package_show`), nu doar prima.** Acum: pierdere zero (1 rând în 9 ani),
validare 100% în toți anii, iar solverul, ancorele, `regula_contestatie.py` și `diagnostic_bac.py` sunt șterse.
2017 e ODS, citit în flux cu `ods_reader.py` (odfpy ar încărca sute de MB în memorie). 2019 și 2020 au
metadata XLSX ruptă → `read_only=False`. 2022 are schemă proprie, 74 col.

## Deciziile metodologice (toate ale userului, toate confirmate)

1. **Media se recalculează.** Coloana `Medie` există doar pentru cei cu ≥5 la fiecare probă (78% în 2025) —
   e survivorship bias, iar selecția e mai dură la liceele slabe. Formula: media aritmetică a notelor finale,
   **trunchiată** la 2 zecimale (nu rotunjită — ar greși în 33%). Nota finală = cea de la contestație,
   necondiționat (2016 făcea excepție, cu prag ≥0,5 — de aceea e scos). Verificat: reproduce media publicată
   în 100% din cazuri, toți anii. Acoperire 95,5-98,7% vs 83-90%.
2. **Mediană, nu medie.** Decis pe datele BAC (nu prin analogie cu EN): 848 celule, 84% asimetrice la stânga,
   50% semnificativ, gap −0,13, corelat −0,55 cu nivelul școlii. Efectul pe clasament e mic (Spearman 0,99).
3. **Doar promoția curentă** (89% din candidați).
4. **Filierele sunt trei lumi sociale distincte** — prezumție de bază, nu ipoteză testată. Consecințe:
   nimic nu se compară peste filiere; **rangurile se calculează în interiorul filierei**. Un KW omnibus peste
   cele 9 entități a fost ÎNCERCAT ȘI ABANDONAT: ieșea p<1e-8, ε²=0,4-0,6, dar aia era prezumția apărând în
   rezultat, iar rangurile lui clasau teoretice față de tehnologice. Corecția a schimbat răspunsul: de la
   1 comparație semnificativă din 81, la 4.
5. **Neprezentații intră în mediană, așezați jos, fără notă** (`statistici.mediana_cenzurata`). Mediana e o
   poziție, nu o medie. Santinela `SUB=0.0` — valoarea ei e irelevantă prin construcție (4,5 și 1,0 dau
   identic); de aceea nu trebuie inventată. Asumpție asumată: neprezentatul stă sub oricine s-a prezentat.
   Miza e inegală: <1% la teoretic/vocațional, 4% la tehnologic.
6. **IRIS (liceu special) RĂMÂNE** în clasament (userul s-a răzgândit) — cu notă în text.
7. **Liceele cu două filiere** apar pe două taburi, marcate „— teoretic" / „— vocațional".

## Rezultate

- **Fără pooling temporal.** Friedman: p max 4,3×10⁻⁸, W 0,22-0,26. 2018 cel mai slab an, 2024 cel mai bun.
- **Timișoara e ultima din trei** la teoretic 9/9 ani și la tehnologic 9/9; la vocațional doar 2/9 — acolo
  nu are o problemă. Semnificativ: teoretic vs Iași (2024, 2025), tehnologic vs Cluj (2020, 2025). Decalajul
  se lărgește: ε² sare la ~0,28 în 2025.
- **Nu e (doar) compoziție.** Cluj are 17-25% tehnologice, TM 27-34% — dar Iași are aceeași compoziție ca TM
  și stă deasupra, în ambele filiere, în toți anii. (Retras: afirmasem pe tipul dedus din DENUMIRE că vârful
  e în regulă — fals, teoreticele TM sunt sub cele clujene în fiecare an.)
- **Shrinkage-ul aproape nu mișcă nimic**: τ² e mare față de zgomot, w=0,80-1,00, Δrang max 0-2. Liceele chiar
  se disting: 13/17 la teoretic 2025. Doar vocaționalul e indistinct (3/8) — și acolo τ² chiar e mic.

## Scripturi (`scripts/`, lanț în ordine)

`download_bac.py` → `extract_bac.py` (+`ods_reader.py`) → `distributii_bac.py` → `teste_bac.py` →
`filiera_bac.py` → `shrinkage_bac.py` → `build_bac_html.py` (+`operationalizare.py`).
`statistici.py` = funcțiile comune (fără scipy; numpy există).
**Cifrele din raport se calculează din JSON-uri la fiecare build** — au rămas o dată în urmă, nu se mai repetă.
Arborele de operaționalizare la fel: `operationalizare.py` e sursa care aplică regula ȘI desenează figura,
cu assert că partiția profil→filieră ține (verificat: 9 profiluri, 1 filieră fiecare, zero excepții).

## Deschis

- **`bac.html` e o pagină ORFANĂ.** Planul cerea link reciproc cu `index.html` (raportul EN); nu s-a făcut.
  Cine intră pe site nu are cum să afle că există raportul BAC, și invers. Câteva minute de lucru.
- **Următorul fir (userul, 2026-07-17): contribuția netă a liceului** — puncte adăugate față de nota de
  intrare, cu normalizare. E exact ce lipsește acum: raportul spune la limite că măsoară selecția la intrare,
  nu valoarea adăugată. **Dar prima verificare nu e normalizarea, ci dacă legătura se poate face deloc:**
  admiterea la liceu e alt set de date decât BAC-ul, joinul e pe ELEV, nu pe școală, iar noi nu avem un
  identificator de elev între cele două. `Cod unic candidat` din BAC nu e evident același lucru cu ce apare
  în datele de admitere — de verificat înainte de orice altceva. Userul a zis: după ce ne lămurim cu BAC-ul.
- Textul raportului e scris și actualizat; niciun pas din cei 7 nu mai e în lucru.
- Glosarul `statistica-ro`: 93 intrări; `cazuri cenzurate` [R m.181] adăugat. 18 termeni rămân nepropuși
  (asimetrie-ca-formă, bootstrap, mărimea efectului, Friedman, comparații multiple, boltire ș.a.) — **nu sunt
  în Reisz**, iar suporturile lui Hatos sunt pe ResearchGate, care cere verificare anti-bot. Userul: lasă-le.
- Atenție la un fals pozitiv găsit: `asimetr` apare de 6× în Reisz, dar TOATE sunt „asimetria temporală a
  cauzalității" — alt concept. Căutarea pe rădăcini fără citirea contextului umple glosarul cu potriviri false.

# Analiza EN VIII (încheiată · handoff 2026-07-15)

Analiză a rezultatelor Evaluării Naționale (clasa a VIII-a) pe școli, date deschise data.gov.ro, 2020-2025. **Un singur folder, un singur repo** — consolidat pe 2026-07-14 din foste 2 locații (`Documents/evaluare-nationala/` + `Documents/raport-timisoara/`), decizie user („am lucrat prost până acum, totul într-un singur folder").

## ✅ Livrabil gata: `index.html`
- **[pro-vio.github.io/raport-timisoara](https://pro-vio.github.io/raport-timisoara/)** — **linkul public de trimis** (GitHub Pages, verificat live 2026-07-15). Se actualizează automat la fiecare `git push` pe `main`.
- **[Artifact claude.ai](https://claude.ai/code/artifact/84c74049-6070-4d70-9fd4-798190532f1c)** — aceeași pagină, util pt iterare rapidă din chat (artifactele sunt private by default; linkul Pages e cel de distribuit).
- fișier local `index.html` (rădăcina proiectului), **~160 KB — trimis fără probleme pe mail/WhatsApp**.

⚠️ Toate încarcă Chart.js de pe CDN extern (cdnjs.cloudflare.com) → cine deschide are nevoie de internet în acel moment, altfel graficele nu se randează (restul e self-contained, date inline).

### Structură GitHub (1 repo, PUBLIC — decizie user 2026-07-15)
- **`pro-vio/raport-timisoara`** (PUBLIC) — tot proiectul: scripturi, JSON-uri derivate, STARE.md, `index.html` la rădăcină. `.gitignore` exclude xlsx-urile brute (97MB, redescărcabile de pe data.gov.ro).
- **GitHub Pages activat** pe branch `main`, root `/` → servește `index.html`.
- ⚠️ **Istoric al deciziei** (ca să nu se reia dezbaterea): schema a oscilat de 3 ori — (1) 2 repo-uri: privat + public-doar-raport; (2) 2026-07-14: consolidare într-un singur repo PRIVAT, Pages dezactivat, link = artifact; (3) 2026-07-15: userul a vrut înapoi linkul Pages → repo făcut PUBLIC din nou. **Constrângerea de fond: pe cont gratuit, Pages nu servește din repo privat.** Privat + link public GitHub = incompatibile fără GitHub Pro. Datele fiind deschise/anonimizate, public e OK.
- Fostul repo `pro-vio/evaluare-nationala-timisoara` — **șters de user, verificat 2026-07-14**. Nu mai există; `raport-timisoara` e singurul repo al proiectului.
- Autentificare `gh` cont `pro-vio` (HTTPS, keyring) — deja configurată pe această mașină. ⚠️ Tokenul NU are scope `delete_repo` (ștergerile de repo le face userul din browser).

Raport pentru audiență politică, scop restrâns la **Timișoara** (din cele 3 orașe analizate: Timișoara, Cluj-Napoca, Iași), 5 tab-uri:
1. **Efecte structurale** — grafic rang mediu Friedman (3 orașe) + teste efectuate + concluzia „nu există interacțiune între efectul de oraș și efectul de an" (finalizată lingvistic).
2. **Distribuții note pe școală** — strip-plot (fiecare candidat = un punct, jitter, canvas), linii mediană (alb)/medie (roșu) mereu vizibile pe grafic, slider de an; + cardul „Distanța medie-mediană" (gap procentual + concluzia: mediana, nu media, pt clasament).
3. **Mediane cu bootstrap** — caterpillar plot shrinkage empirical-Bayes (bootstrap 2000 reeșantionări pt SE mediană), slider de an, schemă „Cum se citește", notă metodologică (mu_hat = **media** medianelor școlilor, nu mediana lor — impus de formula de shrinkage).
4. **Evoluția medianelor** — traiectorii pe școală, toggle Valori brute/Reziduu (text explicativ se schimbă cu butonul), linie groasă mereu vizibilă = mediana orașului.
5. **Clasament (evoluție)** — tabel cu săgeți ▲▼= (font îngroșat) pt mișcarea în clasament an-cu-an.

Design: pagină editorială proprie (serif Georgia pt titluri, sans pt corp, paletă warm-paper/ledger), token-uri light+dark, verificat live cu preview server (`.claude/launch.json` din `analiza-patrimven`, config `evaluare-nationala-preview` → acum servește `Documents/raport-timisoara`, port 8769).

## Date
- `date/` — 6× xlsx per-candidat de pe data.gov.ro (2020-2025; identificator școală = `COD SIIIR`).
  - ⚠️ **Fișierul 2020 are metadata de dimensiuni ruptă** → citește DOAR cu `openpyxl.load_workbook(path, read_only=False)`.
- `date/Unitati de invatamant acreditate  i autorizate.xls` — registrul SIIIR→denumire/localitate/județ (`.xls` vechi → `xlrd`, nu `openpyxl`; normalizează Ş/Ţ→Ș/Ț la join).
- Derivate cheie în `date/`: `shrinkage_mediana.json` (medie/mediană/shrink/CI per școală per an), `candidati_raw_timisoara.json` (note brute per candidat, Timișoara, toți anii — folosit direct în raport pt strip-plot), `medie_vs_mediana_percentil.json`, `dinamica_ranguri.json`, `kw_pe_ani.json`, `friedman_mediane.json` (**cel curent** — Friedman pe mediane școală-an + benzi min/max + exemplu pt text), `friedman_pe_orase.json` (⚠️ istoric, calculat pe MEDII școală-an — nu-l mai folosi), `skew_kurt_2020_2025.json` (⚠️ pe ani cumulați, doar explorare).

## Scripturi (`scripts/`)
Pe lângă cele din sesiunea trecută: `shrinkage_mediana.py` (empirical-Bayes + bootstrap), `extract_candidati_raw.py`, `dinamica_ranguri.py`, `medie_vs_mediana_percentil.py`.
**pandas/scipy NU sunt instalate** — tot manual în Python pur (numpy/openpyxl/xlrd). `xlrd` instalat separat pt `.xls` vechi.

## Decizii metodologice (nu redeschide fără motiv)
- **Unitatea de analiză = școala**, nu candidatul individual.
- **Fără prezumție de omogenitate temporală** — Friedman izolează efectul anului de efectul grupului (KW pe fiecare an separat).
- **Mediană, nu medie** — gap medie-mediană corelat cu nivelul școlii (r=−0,64: media penalizează sistematic școlile de elită). Mediană folosită peste tot pt statistica per școală; media apare doar ca ancoră de shrinkage (impusă matematic) și ca linie de comparație pe strip-plot.
- **Shrinkage empirical-Bayes cu bootstrap**: mediana școlii + SE prin bootstrap (2000 reeșantionări) → shrink spre media medianelor orașului (`mu_hat`), pondere `w=τ²/(τ²+SE²)`. Vezi explicația completă în tab „Mediane cu bootstrap" → „Notă metodologică".

## Rezultate cheie (TM+CJ+IS)
1. **KW pe fiecare an**: Cluj ≥ Iași > Timișoara stabil în toți anii; efect mic (ε²=0,02-0,06) — variația domină *între școli în același oraș*.
2. **Friedman per oraș** (recalculat 2026-07-15 pe MEDIANE școală-an, `friedman_mediane.py` — inițial fusese pe medii, inconsistent cu restul raportului): omogenitate temporală respinsă decisiv (p≤1,1·10⁻⁴); același tipar în toate 3 orașele (2021+2024 slabi, 2020+2025 buni) → efect de examen la nivel național, nu dinamică specifică orașului. **Nu există interacțiune oraș×an.** Kendall W pe mediane: Iași 0,37 / Timișoara 0,36 / Cluj 0,12. Graficul din raport are acum și benzi min-max per oraș (extremele rangurilor între școli — aproape mereu 1-6; excepție notabilă: TM 2021/2024 max=5, nicio școală nu a avut atunci anul ei cel mai bun) + explicație pe înțeles comun, cu exemplul real Șc. Nr.16 „Take Ionescu" (cerută de user, dictată ca structură).
3. **Skew/kurtosis pe medii cumulate**: urmăresc mecanic media școlii (efect de plafon la 10) — doar explorare, invalidat de Friedman pt comparații riguroase.
4. **Shrinkage 2025**: clasament aproape identic cu cel brut pt școli mari (w≈0,95-0,995); diferă vizibil la școli mici (ex. Vlad Țepeș n=19, w=0,476, interval foarte larg).
5. **Dinamică ranguri**: Șc. Nr.6 și Lic. Teologic Baptist urcă constant; Lic. Ortodox „Antim Ivireanu" — urcare 2020-2024 urmată de cădere bruscă 2025 (posibil an atipic, n=40, de verificat).

## Pas următor (neînceput, opțional)
Standardizare pe an (z-score în interiorul anului) pt orice analiză longitudinală riguroasă — discutat, nu implementat (relevant mai ales dacă se reia skew/kurtosis).

## Fire deschise (de reluat)

### 1. Date EN VIII 2026 — nu există încă pe data.gov.ro
Verificat 2026-07-08: rezultatele finale (după contestații) au fost publicate azi de minister (edu.ro, comunicat/sinteză), dar **fișierul brut per-candidat pt 2026 NU e încă pe data.gov.ro**. Tiparul anilor anteriori arată o întârziere de câteva luni (2025: examen iunie, fișier publicat octombrie). Recheck recomandat: toamna 2026.

### 2. Extindere la BAC — ✅ aprobată și începută pe 2026-07-16
Vezi secțiunea „FIRUL CURENT" din capul fișierului. Față de propunerea inițială de aici, userul a extins fereastra la **10 ani (2016-2025)** și a cerut un **pas de verificare a distribuțiilor** înainte de alegerea medianei.
