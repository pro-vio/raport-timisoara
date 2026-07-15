# STARE — raport-timisoara (handoff · 2026-07-15)

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
- Derivate cheie în `date/`: `shrinkage_mediana.json` (medie/mediană/shrink/CI per școală per an), `candidati_raw_timisoara.json` (note brute per candidat, Timișoara, toți anii — folosit direct în raport pt strip-plot), `medie_vs_mediana_percentil.json`, `dinamica_ranguri.json`, `kw_pe_ani.json`, `friedman_pe_orase.json`, `skew_kurt_2020_2025.json` (⚠️ pe ani cumulați, doar explorare).

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
2. **Friedman per oraș**: omogenitate temporală respinsă decisiv (p≤2,5·10⁻⁷); traiectorii aproape identice în toate 3 orașele (2021+2024 slabi, 2020+2025 buni) → efect de examen la nivel național, nu dinamică specifică orașului. **Nu există interacțiune oraș×an.**
3. **Skew/kurtosis pe medii cumulate**: urmăresc mecanic media școlii (efect de plafon la 10) — doar explorare, invalidat de Friedman pt comparații riguroase.
4. **Shrinkage 2025**: clasament aproape identic cu cel brut pt școli mari (w≈0,95-0,995); diferă vizibil la școli mici (ex. Vlad Țepeș n=19, w=0,476, interval foarte larg).
5. **Dinamică ranguri**: Șc. Nr.6 și Lic. Teologic Baptist urcă constant; Lic. Ortodox „Antim Ivireanu" — urcare 2020-2024 urmată de cădere bruscă 2025 (posibil an atipic, n=40, de verificat).

## Pas următor (neînceput, opțional)
Standardizare pe an (z-score în interiorul anului) pt orice analiză longitudinală riguroasă — discutat, nu implementat (relevant mai ales dacă se reia skew/kurtosis).

## Fire deschise (de reluat)

### 1. Date EN VIII 2026 — nu există încă pe data.gov.ro
Verificat 2026-07-08: rezultatele finale (după contestații) au fost publicate azi de minister (edu.ro, comunicat/sinteză), dar **fișierul brut per-candidat pt 2026 NU e încă pe data.gov.ro**. Tiparul anilor anteriori arată o întârziere de câteva luni (2025: examen iunie, fișier publicat octombrie). Recheck recomandat: toamna 2026.

### 2. Extindere la BAC — propunere discutată, neîncepută
Userul a cerut replicarea aceluiași tip de analiză pentru **Bacalaureat**. Date confirmate disponibile pe data.gov.ro (cel puțin din 2018+, sesiunea I și sesiunea II separat).
**Recomandarea mea (neconfirmată încă de user când s-a intrat în pauză):**
- Doar **sesiunea I** (vara) — sesiunea II e restanțieri/îmbunătățiri, populație auto-selectată, necomparabilă.
- Adaugă **rata de promovare** ca metrică nouă (prag: medie ≥6,00 ȘI ≥5,00 la fiecare probă) — probabil statistica-fanion la BAC, spre deosebire de EN VIII unde toți candidații au o medie.
- Universul de școli = **licee**, identificare nouă din registru (suprapunere parțială, dar nu identică, cu școlile EN VIII — ex. „C.D. Loga" are ambele cicluri, dar liceele tehnologice pot să nu aibă gimnaziu asociat în listă).
- Păstrează aceeași fereastră **2020-2025** și aceleași 3 orașe (Timișoara/Cluj/Iași), ca să fie comparabil direct cu raportul EN VIII.
- Restul pipeline-ului identic: mediană (nu medie), shrinkage empirical-Bayes+bootstrap, KW pe an + Friedman între orașe, aceeași structură de raport.

**La reluare: cere confirmarea userului pe schema de mai sus înainte de a începe descărcarea/scripturile.**
