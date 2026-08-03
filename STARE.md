# STARE — raport-timisoara (handoff · 2026-07-16)

---

# BAC Timișoara — stare la 2026-07-17 (sfârșit de zi)

Analiza EN VIII de mai jos e **încheiată și livrată** — nu se atinge. Firul activ e replicarea pe Bacalaureat.

**Livrabil: `bac.html`** — comis și publicat (commit `a51f051`, 2026-07-17).
- **[pro-vio.github.io/raport-timisoara/bac.html](https://pro-vio.github.io/raport-timisoara/bac.html)** — linkul public, verificat live. Se reconstruiește la fiecare `git push` pe `main` (build Pages ~1 min; verifică cu `gh api repos/pro-vio/raport-timisoara/pages/builds/latest`).
- [Artifact](https://claude.ai/code/artifact/c1a11bbf-3384-4038-bc9b-7fd10e339d45) — aceeași pagină, pt iterare din chat. Republicare: `python scripts/build_bac_html.py`, apoi Artifact pe același `file_path` (păstrează URL-ul).
- În repo: 7,6 MB (bac.html + 5 JSON-uri derivate + 11 scripturi). Cele 281 MB de surse brute sunt în `.gitignore` — se redescarcă cu `download_bac.py`.

Pași: 1. descărcare ✅ · 2. inventar ✅ · 3. extracție ✅ · 4. distribuții ✅ · 5. teste structurale ✅ ·
6. shrinkage ✅ · 7. raport ✅. **Fereastra: 2017-2025, 9 ani.**

Raportul are **4 taburi**, fiecare cu grafic + casetele care îi dau funcție (lectură, teste, sinteză,
cum-se-citește, notă metodologică — modelate după EN, unde graficele nu stăteau singure):
1. **Datele și definițiile** — proză + arborele profil→filieră.
2. **Variația structurală: trei orașe** — grafic Friedman, tabelul medianelor, caseta *Compoziția
   orașelor* (singurul loc unde orașul apare întreg), *Testele efectuate*, *Ce spune imaginea completă*.
3. **Evoluția medianelor** — tab propriu (ca la EN), cu comutator brut/reziduu.
4. **Liceele din Timișoara** — graficul de intervale (+ liniuța medianei brute), tabelul, *Cum se citește*
   (schemă SVG), *Notă metodologică*.
Toate graficele SVG inline, toate cu selector de filieră, hover pe toate. Cifrele din casete se CALCULEAZĂ
din JSON-uri la fiecare build. Linia groasă la evoluție = mediana FILIEREI. Ancora shrinkage = celula oraș×filieră×an.

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
2. **Mediană, nu medie.** Decis pe datele BAC (nu prin analogie cu EN), pe celulele liceu×filieră×an:
   969 de celule, 82% asimetrice la stânga, 44% semnificativ, diferență −0,12, corelată −0,53 cu nivelul liceului.
   Pe clasament: Spearman medie-vs-mediană per celulă are minimul 0,70 și tipicul 0,98 — în celulele mici
   alegerea chiar mută ranguri (vechiul „0,99" venea dintr-un clasament care amesteca filierele).
3. **Doar promoția curentă** (89% din candidați).
4. **Filierele sunt trei lumi sociale distincte** — prezumție de bază, nu ipoteză testată. Consecința tare:
   **MULȚIMEA DE REFERINȚĂ E ÎNTOTDEAUNA ORAȘ×FILIERĂ — orașul singur nu apare nicăieri.** Nimic nu se
   compară între filiere; rangurile se calculează în interiorul filierei. Încălcări găsite și eliminate
   (audit 2026-07-17, la cererea userului): KW pe an care grupa toate celulele unui oraș (șters din
   teste_bac.py; varianta corectă e în filiera_bac.py), distribuțiile pasului 4 pe celule școală×an
   (rekey liceu×filieră×an), Spearman-ul „0,99" din text. Un KW omnibus peste
   cele 9 entități a fost ÎNCERCAT ȘI ABANDONAT: ieșea p<1e-8, ε²=0,4-0,6, dar aia era prezumția apărând în
   rezultat, iar rangurile lui clasau teoretice față de tehnologice. Corecția a schimbat răspunsul: de la
   1 comparație semnificativă din 81, la 4.
5. **Neprezentații intră în mediană, așezați jos, fără notă** (`statistici.mediana_cu_neprezentati`; redenumită
   3 august 2026 din `mediana_cenzurata` — cenzurate sunt cazurile, nu statistica). Mediana e o
   poziție, nu o medie. Santinela `SUB=0.0` — valoarea ei e irelevantă prin construcție (4,5 și 1,0 dau
   identic); de aceea nu trebuie inventată. Asumpție asumată: neprezentatul stă sub oricine s-a prezentat.
   Miza e inegală: <1% la teoretic/vocațional, 4% la tehnologic.
6. **IRIS (liceu special) RĂMÂNE** în clasament (userul s-a răzgândit) — cu notă în text.
7. **Liceele cu două filiere** apar pe două taburi, marcate „— teoretic" / „— vocațional".

## Rezultate

- **Fără pooling temporal.** Friedman pe fiecare din cele 9 entități oraș×filieră: respinge
  interschimbabilitatea anilor în 8 din 9; excepția e vocaționalul din Iași (5 licee, p=0,72) — fără putere.
  W între 0,14 și 0,59. Tiparul anilor DIFERĂ între filiere (la TM: cel mai bun an e 2024 la teoretic,
  2023 la tehnologic, 2017 la vocațional) — graficul urmează selectorul de filieră. Deci nici anii nu se
  adună, nici filierele nu se amestecă.
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

## Terminologie (decizii de vocabular, 2026-07-17)

- **variația** = fenomenul (cât din ce vedem se împarte între grupuri) · **dispersia** = parametrul (τ²).
  „Varianța" e calc — Reisz [R m.71]: termenii sunt „abaterea standard" și „dispersia". Userul: „perechea
  variație-dispersie îmi place, mă ajută să îmi structurez vocabularul".
- **„peste X" e calc după *across*** → „între" (inter) / „în interiorul" (intra); pentru agregare, „pe"
  sau „la nivelul". Termenii userului pentru despărțirea variației: **intra-grup / inter-grup**, folosiți
  de el într-un articol. Reisz NU are vocabular inter/intra-grup (zero apariții) — nu e autoritate acolo.
- **„referent" e fals prieten** → „referință" (în română referentul e persoana care referă).
- **„interschimbabili"**, nu „schimbabili între ei" (despre ani, la Friedman).
- **„gap" → „diferență"** (3 august 2026, userul). Mărimea e percentila la care cade media
  minus 50, deci o diferență cu semn — valorile sunt negative. „Distanță" e greșit tocmai
  fiindcă o distanță nu poate fi negativă. Glosarul `statistica-ro` n-are intrare pentru ea,
  nici Reisz; cuvântul comun e cel corect. În text: „diferența medie–mediană", „media
  diferențelor (pp)". Cheile din JSON și variabilele din scripturi rămân `gap` (identificatori,
  nu text).

## Lecție de proces (2026-07-17)

De DOUĂ ori userul a văzut „graficul Friedman e per oraș, nu oraș×filieră” — și avea dreptate,
deși DATELE erau corecte (statisticile se schimbau la comutarea filierei). Greșeala era în PREZENTARE:
titlul rămăsese „pe orașe” (o înlocuire de șir eșuase în tăcere), iar selectorul stătea SUB grafic, nu deasupra.
Verificările mele prin JS măsurau numere, nu titluri/layout. **Regulă: după orice schimbare, verifică și
ce SPUNE pagina — titlu, etichetă de control, aria-label — nu doar ce calculează.** Un assert care pică
într-un patch lasă fișierul nescris: verifică mereu că build-ul chiar a rulat.

## FIRUL VALOARE ADĂUGATĂ (explorat 2026-07-21, BLOCAT PE DATE)

Scop: delta = nota BAC − nota de intrare (media de admitere), per liceu. „Valoare adăugată contextuală"
(CVA): judeci liceul după rezultatul lui FAȚĂ DE ce prezicea intrarea, nu brut.

### Sursa de intrare — GĂSITĂ și verificată
Repartizarea computerizată de la `static.admitere.edu.ro/{an}/repartizare/{JUDET}/data/candidate`
(2024-2025 fără `.json`; anii vechi cu `.json` + `?_=timestamp`). JSON per candidat repartizat, cheile:
`madm`=media de admitere (NOTA DE INTRARE), `mev`=media EN, `mabs`=media claselor V-VIII, `nro`/`nmate`=
note RO/mate, `h`=liceul unde a ajuns (nume în HTML), `sp`=specializarea, `sc`=codul gimnaziului.
**Joinul cu BAC merge pe COD SIIIR** (nume→cod prin endpoint-ul `highschool`): 30/37 licee TM se potrivesc;
cei 7 lipsă = vocaționalele (sport/artă), admitere separată pe aptitudini. Specializarea→filieră: real/uman
→ teoretic, servicii/tehnic/resurse → tehnologic. Din 2025 admiterea e 100% EN, deci `madm`==`mev`; la anii
vechi diferă (amestec EN + media gimnaziu). Am în `date/admitere/` (gitignore): TM 2025 (test) + TM 2023 (Wayback).

### ZIDUL: nu există pereche cohortă-corectă pentru orașele noastre
Intrare an E → BAC an E+4. Ne trebuie E≤2021 (BAC-ul nostru ≤2025). DAR datele de intrare pentru TM/CJ/IS
supraviețuiesc doar din 2023 (Wayback; live are doar 2024-2025). Intrarea 2013-2021 pt orașele noastre:
ștearsă de pe live, iar crawler-ul Wayback n-a rulat JS-ul care încarcă `candidate.json` → a salvat doar
paginile index. Ce s-a prins din anii vechi = județe la întâmplare (BC/CT 2017, CS/SJ 2019, B 2021), niciodată
TM/CJ/IS. Gol structural de 2 ani: intrarea începe 2023 (→BAC 2027), BAC-ul se termină 2025 (→intrare 2021).
Extracția de pe Wayback FUNCȚIONEAZĂ (TM 2023 = 3985 candidați, complet) — dar perechea lui e în viitor.

### Decizii metodologice stabilite în discuție (de reținut, sunt corecte)
- **Media diferențelor = diferența mediilor**, fără join individual — ADEVĂRAT, dar DOAR pentru MEDIE. Pentru
  DISTRIBUȚIA delta trebuie covarianța = împerecherea individului, pe care n-o avem (codul candidatului admitere
  ≠ „Cod unic candidat" BAC). Deci delta individuală e în afara datelor.
- **Mediana nu se compune** (mediana(δ) ≠ mediana(BAC)−mediana(intrare)); doar media. Deci pt delta e mai bună
  MEDIA, cu prețul că neprezentații cer o notă (nu-i mai poți cenzura ca la mediană). Nivelul rămâne pe mediană.
- **Comonoton (împerechere după rang)** = diferența cuantilelor δ(p)=Q_BAC(p)−Q_intrare(p), un Q-Q. Face vizibilă
  regresia spre medie (coada de jos „urcă", vârful plat), DAR interzice încrucișările → NU se agregă pe școală
  (media lui pe școală = diferența mediilor oricum; forța zero valoarea adăugată dacă imputezi note). Bun pt
  DESCRIEREA distribuției, inutil pt clasament.
- **Panta din perechi comonotone = „linia SD"** (σ_BAC/σ_intrare), nu linia de regresie (ρ·σ_BAC/σ_intrare).
  Comonoton presupune ρ=1 (rang perfect păstrat), deci panta MAXIMĂ; injectează regresia spre medie prin pantă.
- **Banda comonoton↔countermonoton** mărginește valoarea adăugată peste ρ∈[−1,+1], DAR capătul de jos (ρ=−1,
  cei mai buni la intrare iau cele mai mici note) e SUBSTANȚIAL IMPOSIBIL → banda conține adevărul trivial, prea
  largă. Nu importa ρ național/internațional: restricția de amplitudine (intrare comprimată la colegii, diferită
  pe școală) îl face netransferabil.
- **CONCLUZIA CURATĂ:** pt valoare adăugată la nivel de LICEU (unitatea proiectului) NU e nevoie de ρ individual.
  Relația de care e nevoie — media BAC vs media intrare ÎNTRE școli — e direct estimabilă pe datele noastre
  (reziduu din regresia mediilor de școală, cu shrinkage pt școlile mici, ca la BAC). Ruta individuală (Fréchet/
  comonoton) ne-a servit doar ca să înțelegem limita; livrabilul onest nu trece de școală.

### Demo cross-cohortă (2025 intrare vs 2025 BAC, cohorte DIFERITE — doar forma)
Reziduul din regresie BAC~intrare, în interiorul filierei: la teoretic vârful adaugă valoare (Bănățean +0,46,
Loga +0,44), teologicele subperformează (Antim −1,00, Baptist −0,73); la tehnologic, unele licee cu intrare
slabă duc elevii peste predicție (Silvicultură +1,54). Clasamentul de valoare adăugată e ALTUL decât cel brut.
Cifrele sunt de aruncat (cohorte nepotrivite), forma e reală.

### Opțiuni la reluare
A. Aștepți BAC 2027+ pt cohorta 2023 (capturabilă acum). B. Alt arhiv pt intrarea istorică TM (ISJ Timiș,
mirror-uri) — incert. C. Proxy pe PRAG: „ultima medie de intrare" din planul de școlarizare e disponibilă
istoric, cohortă-corectă, dar slabă/părtinitoare (pragul, nu distribuția). D. Demo cross-cohortă (forma metodei).
Firul e AMBIȚIOS și se lovește de o limită de DATE, nu de metodă. Proiectul BAC în sine e livrat și solid.

## Deschis

- **Următorul fir (userul, 2026-07-17): contribuția netă a liceului** — puncte adăugate față de nota de
  intrare, cu normalizare. E exact ce lipsește acum: raportul spune la limite că măsoară selecția la intrare,
  nu valoarea adăugată. **Dar prima verificare nu e normalizarea, ci dacă legătura se poate face deloc:**
  admiterea la liceu e alt set de date decât BAC-ul, joinul e pe ELEV, nu pe școală, iar noi nu avem un
  identificator de elev între cele două. `Cod unic candidat` din BAC nu e evident același lucru cu ce apare
  în datele de admitere — de verificat înainte de orice altceva. Userul a zis: după ce ne lămurim cu BAC-ul.
- **Rămase din structura aprobată, deliberat neînceput e:** (a) tabul *Distribuțiile notelor* — beeswarm
  pe licee (fiecare candidat un punct, neprezentații sub axă) + distanța medie–mediană ca argument empiric
  al medianei; singurul cu muncă reală — cere mediile brute per candidat (~68k valori, ~300KB) și percentila
  mediei calculată în distributii_bac.py (nu există acum). (b) tabul *Clasament (evoluție)* cu săgeți ↑↓ pe
  ani, pe filieră — userul a zis explicit să NU-l fac încă.
- Restul casetelor din structura EN sunt acum toate prezente; textul e scris și actualizat.
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
1. **Efecte structurale** — grafic rang mediu Friedman (3 orașe) + teste efectuate + concluzia că Timișoara stă ultima în toți cei 6 ani, deci ordinea orașelor nu depinde de an.
2. **Distribuții note pe școală** — strip-plot (fiecare candidat = un punct, jitter, canvas), linii mediană (alb)/media celor prezenți (roșu) mereu vizibile pe grafic, slider de an; + cardul „Diferența medie–mediană" (diferență în puncte procentuale + concluzia: mediana pt clasament).
3. **Mediane cu bootstrap** — caterpillar plot shrinkage empirical-Bayes (bootstrap 2000 reeșantionări pt SE mediană), slider de an, schemă „Cum se citește", notă metodologică (mu_hat = **media** medianelor școlilor, nu mediana lor — impus de formula de shrinkage).
4. **Evoluția medianelor** — traiectorii pe școală, toggle Valori brute/Reziduu (text explicativ se schimbă cu butonul), linie groasă mereu vizibilă = mediana orașului.
5. **Clasament** — tabel cu INTERVALE DE RANG („locul 4-12"), fără săgeți. Vezi mai jos de ce.

Design: pagină editorială proprie (serif Georgia pt titluri, sans pt corp, paletă warm-paper/ledger), token-uri light+dark, verificat live cu preview server (`.claude/launch.json` din `analiza-patrimven`, config `evaluare-nationala-preview` → acum servește `Documents/raport-timisoara`, port 8769).

## Date
- `date/` — 6× xlsx per-candidat de pe data.gov.ro (2020-2025; identificator școală = `COD SIIIR`).
  - ⚠️ **Fișierul 2020 are metadata de dimensiuni ruptă** → citește DOAR cu `openpyxl.load_workbook(path, read_only=False)`.
- `date/Unitati de invatamant acreditate  i autorizate.xls` — registrul SIIIR→denumire/localitate/județ (`.xls` vechi → `xlrd`, nu `openpyxl`; normalizează Ş/Ţ→Ș/Ț la join).
- Derivate cheie în `date/`: `shrinkage_mediana.json` (medie/mediană/shrink/CI per școală per an), `candidati_raw_timisoara.json` (note brute per candidat, Timișoara, toți anii — folosit direct în raport pt strip-plot), `medie_vs_mediana_percentil.json`, `dinamica_ranguri.json`, `kw_pe_ani.json`, `friedman_mediane.json` (**cel curent** — Friedman pe mediane școală-an + benzi min/max + exemplu pt text), `friedman_pe_orase.json` (⚠️ istoric, calculat pe MEDII școală-an — nu-l mai folosi), `skew_kurt_2020_2025.json` (⚠️ pe ani cumulați, doar explorare).

## Scripturi (`scripts/`)
Pe lângă cele din sesiunea trecută: `shrinkage_mediana.py` (empirical-Bayes + bootstrap), `extract_candidati_raw.py`, `dinamica_ranguri.py`, `medie_vs_mediana_percentil.py`.

### `index.html` are generator (3 august 2026, decizia userului: „nicio cifră hardcodată")
`build_index_html.py` construiește pagina din `index_template.html` + JSON-urile din `date/`.
**Nicio cifră nu mai e scrisă de mână** — nici în grafice, nici în proză. Cele 51 de jetoane
`{{...}}` se calculează la fiecare rulare; build-ul cade dacă un jeton n-are valoare sau dacă
o valoare se calculează degeaba.

**De ce nu e de ajuns generatorul.** Interpolarea protejează cifra, nu afirmația: „2020 e cel
mai mare peste tot" poate avea cifra corectă și fi falsă — s-a întâmplat de două ori pe 3
august, prinse abia la citire. De aceea build-ul rulează la final `verifica_text.py`, care
testează **afirmațiile** (Timișoara ultima în toți anii, un singur contrast Dunn semnificativ,
anul de vârf pe fiecare oraș, echilibrul tagurilor, formulările scoase la audit) și **întoarce
exit 1**, cu pagina nescrisă, dacă una pică. Verificat prin stricarea deliberată a unei valori.

Singurul lucru din blocurile de date care NU vine din fișiere e `nume_scurte.json` —
prescurtările denumirilor pentru lizibilitatea graficului. E editorial, de aceea stă separat
și la vedere. Ordinea liniilor din „Evoluția medianelor" e acum o regulă declarată (rangul din
primul an, apoi restul), nu una accidentală.

Căile absolute către fostul folder `evaluare-nationala/date` au fost înlocuite peste tot cu
căi relative la script (19 locuri, 9 scripturi) — până atunci niciun script EN nu mai rula.
**pandas/scipy NU sunt instalate** — tot manual în Python pur (numpy/openpyxl/xlrd). `xlrd` instalat separat pt `.xls` vechi.

## Decizii metodologice (nu redeschide fără motiv)
- **Unitatea de analiză = școala**, nu candidatul individual.
- **Fără prezumție de omogenitate temporală** — Friedman izolează efectul anului de efectul grupului (KW pe fiecare an separat).
- **Mediană, nu medie** — diferența medie–mediană corelată cu nivelul școlii (r=−0,64: media penalizează sistematic școlile de elită). Mediană folosită peste tot pt statistica per școală; media apare doar ca ancoră de shrinkage (impusă matematic) și ca linie de comparație pe strip-plot. ⚠️ **Regula a fost încălcată tăcut până pe 3 august 2026**: KW pe an intra cu MEDIA școlii (`kw_pe_ani.py`), la fel cum fusese și Friedman înainte de 15 iulie. Reparat; efectul e mai mic pe mediane, vezi rezultatele.
- **Shrinkage empirical-Bayes cu bootstrap**: mediana școlii + SE prin bootstrap (2000 reeșantionări) → shrink spre media medianelor orașului (`mu_hat`), pondere `w=τ²/(τ²+SE²)`. Vezi explicația completă în tab „Mediane cu bootstrap" → „Notă metodologică".
- **Neprezentații intră în mediană și la EN** (3 august 2026; decizia luată la BAC pe 17 iulie, extinsă acum). Pragul rămâne pe candidații CU NOTĂ, ca setul de școli să nu se schimbe odată cu statistica. Efect: 5-8 mediane și 4-8 ranguri mutate pe an, din ~30 de școli; cea mai mare mișcare Șc.19 „Avram Iancu" 2025 (13 neprezentați, mediana 8,570→8,400, rangul 6→9).
  **Verificat că poziția Timișoarei NU ține de ei** (`neprezentati.py` → `date/neprezentati.json`): ponderea se încrucișează între orașe de la an la an, iar mediana orașului se mișcă cu ≤0,07, cu semne diferite. Ce ține: la școlile ale căror elevi iau note mai mici se prezintă mai puțini — corelație −0,49, iar **nu e circulară**: iese −0,50 pe medie și −0,55 pe `MEDIA V-VIII`, care nu vine din examen.
- **Două praguri, deliberat** (aprobat de user, 3 august 2026): 8 la teste (Friedman, KW), 15 la graficele care numesc școli. Un test adună peste zeci de școli și suportă unități mai zgomotoase; un grafic numește o școală anume, unde o mediană șubredă devine o afirmație despre ea. La TM diferența e de 4-8 școli pe an.

## Clasamentul e o hartă de zone, nu o ordine (3 august 2026)

Userul: „mediane cu bootstrap și clasament ar trebui să spună o poveste consistentă statistic".
Erau contradictorii — un tab arăta zone largi, celălalt o ordine fermă cu săgeți. Măsurat:

- **Intervale de rang** (`ranguri_bootstrap.py` → `ranguri_bootstrap.json`): se bootstrapează
  clasamentul ÎNTREG, 2000 de replici, fiindcă rangul e o mărime a mulțimii, nu a școlii.
  Lățime tipică **9-11 locuri**, maxim 22. „Locul 6" e de fapt „locul 4-12".
- **Săgețile: 1 din 124 se susține.** De aceea au fost scoase. Rangul elimină din construcție
  mișcarea comună a anului, deci ce rămâne e partea specifică școlii — și aia e zgomot.
  (Pe NIVEL, 22% din schimbările an-la-an sunt semnificative brut și 6% cu Holm, dar se
  strâng la trecerea 2020→2021, exact anul pe care Friedman îl arată ca mișcare națională.)
- **Perechi despărțite** (`determinare_clasament.py`): pe diferență 55-63%, cu Holm pe familia
  anului **29-35%**; prin suprapunerea intervalelor 41-52%. Suprapunerea e prea severă, Holm
  e obligatoriu dacă afirmația e „acesta e clasamentul". Poziții unice: 0-1 pe an.
- **Ce rezistă**: primul loc e neambiguu (1-1) în toți cei 6 ani; ultima școală se desparte de
  mijloc; între ele doar 4-12 școli din ~30 se despart de școala din mijloc.

**Pragurile n-au bază empirică** (`prag_incertitudine.py`). Curba lățimii intervalului în
funcție de numărul de candidați **nu are cot** — scade neted de la ~2,7 puncte la n=5 la ~0,9
la n=55. Deci pragul e o alegere de precizie, nu o descoperire. Traduceri: sub 2,5 puncte → 9
candidați; sub 2,0 → 13; sub 1,5 → 18; sub 1,2 → 23. Pragurile actuale (8 la teste, 15 la
grafice) au intrat pe 14-15 iulie fără justificare și corespund cu ~2,65 și ~1,72 puncte.
⚠️ Prima variantă a criteriului — „cât din câmpul orașului acoperă intervalul" — a fost
ABANDONATĂ: e circulară, fiindcă ridicarea pragului îngustează câmpul, care ridică pragul
(bază 15 → praguri 9/17; bază 17 → 10/18). Lățimea absolută n-are bucla asta.
**ALES de user (3 august 2026): 2,5 puncte la teste, 1,5 la grafice.** De acolo ies pragurile
**9 și 18**, calculate la fiecare rulare. `MIN_N` nu mai e literal în niciun script EN — se
citește prin `praguri.py` din `prag_incertitudine.json`. Lanțul: `prag_incertitudine.py`
rulează PRIMUL, nu depinde de niciun prag, deci n-are ciclu.

⚠️ **Pragurile din lanțul BAC au rămas literale** (`teste_bac.py` 8, `filiera_bac.py` 8,
`shrinkage_bac.py` 10), iar comentariul „ca la EN" din `teste_bac.py` **nu mai e adevărat**.
Userul: „de bac nu ne ocupăm" — deci se lasă așa, dar cine reia BAC-ul să știe că referința e
depășită; celulele acolo sunt liceu×filieră×an, deci preciziile s-ar recalcula pe datele lor.

## Rezultate cheie (TM+CJ+IS)
1. **KW pe fiecare an** (recalculat 2026-08-03 pe MEDIANE școală-an; înainte intra media școlii): Timișoara ultima în toți cei 6 ani, deci ordinea nu depinde de an; deasupra, Cluj primul 2020-2024 și Iași în 2025. Efect mic, ε²=0,002-0,051, minimul în 2023. Singurul contrast Dunn semnificativ e Cluj-Timișoara (2020, 2021, 2022, 2024); în 2023 și 2025 omnibusul nu respinge. În 2024, omnibus p=0,054 dar Dunn CJ-TM p=0,047 — perechea iese sub un omnibus care nu respinge. Variația domină *între școli în același oraș*.
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
