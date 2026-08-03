# Ontologie și măsurare — Evaluare Națională, școlile din Timișoara

Audit al paginii `index.html`, 3 august 2026. Treapta 1 e stabilită de autor; restul sunt
propuneri și goluri, nu decizii luate.

## Întrebarea de cercetare

Nescrisă până acum. Din raport se citește: *cum stau școlile din Timișoara la Evaluarea
Națională, între 2020 și 2025, față de ele însele în alți ani și față de școlile din Cluj și
Iași.* De confirmat sau reformulat de autor.

## 1. Entități

**Decizia autorului (3 august 2026): existență directă au elevii, notele, școlile și
orașele.** Restul sunt construcții peste ele.

**Relațiile dintre ele, tot de la autor:** elevul are note · școala are elevi — cei înscriși
la ea, care au făcut acea școală · școala e într-un oraș. Agregarea merge pe lanțul ăsta de
apartenență, și numai pe el: mediana unei școli e mediana notelor elevilor ei.

| Entitate | Statut | Ce e |
|---|---|---|
| elevul | existență directă | candidatul înscris la examen |
| nota | existență directă | valoarea din fișierul ministerului, per elev per probă, plus media lui |
| școala | existență directă | unitatea din registrul SIIIR; are elevii care au făcut-o |
| orașul | existență directă | localitatea din registru; conține școli |
| mediana școală×an | construcție | poziția din mijloc a notelor elevilor acelei școli, în acel an |
| rangul anului în școală | construcție | ordinea celor șase mediane ale școlii |
| rangul mediu al anului, pe oraș | construcție | media rangurilor peste școlile orașului |
| mediana ajustată (shrinkage) | construcție | mediana trasă spre ancora orașului |
| clasamentul | construcție | ordinea școlilor după mediană, într-un an |

### Ce nu e în inventar, dar textul se sprijină pe el

Trei lucruri apar în afirmațiile paginii fără să existe în inventar:

- **anul** — pagina spune „anul contează", „ordinea anilor". Anul e etichetă de timp sau
  entitate cu proprietăți proprii?
- **examenul / subiectele** — „ordinea anilor vine de la examen"; dificultatea subiectelor
  nu e măsurată nicăieri în date.
- **generația / cohorta** — „generația care a dat examenul"; nu există în date nicio
  proprietate a generației, doar notele elevilor ei.

Ultimele două sunt numite împreună în text („examen și cohortă") tocmai fiindcă datele nu le
pot despărți. **Întrebare pentru autor:** intră în inventar ca entități, cu observația că nu
sunt măsurate, sau ies din text?

## 2. Concepte

| Ce se măsoară | Concept declarat | Stare |
|---|---|---|
| mediana notelor unei școli | — | **gol** |
| rangul mediu al anilor | interschimbabilitatea anilor | declarat implicit, prin testul Friedman |
| Kendall W | concordanța dintre școli în privința ordinii anilor | declarat în text |
| diferența medie–mediană | asimetria distribuției notelor școlii | declarat implicit |

**Conceptul, stabilit de autor (3 august 2026): rezultatul cohortei.** Mediana unei școli
într-un an e poziția din mijloc a notelor elevilor ei din acel an. Atât spune cifra, și e
exact ce dă lanțul de apartenență de la treapta 1.

O consecință a aceluiași lanț: mulțimea de elevi a unei școli se schimbă complet în fiecare
an, deci construcția e a perechii **școală×an**, nu a școlii. Orice frază care spune „școala
a urcat" afirmă ceva despre o mulțime de elevi comparată cu alta.

**Selecția la intrare e o limită, nu o a doua citire a cifrei** (decizia autorului, aceeași
zi). Cum ajung elevii la o școală anume nu e în date — nu se măsoară nicăieri în fișierele
Evaluării Naționale. Deci rezultatul cohortei e confundat cu selecția, fără ca datele să
poată despărți cele două.

Pe pagină limita se enunță **fără trimitere la literatură** (decizia autorului, 3 august
2026). Prima formulare invoca literatura de specialitate pentru afirmația că selecția
contează; era singurul loc din raport sprijinit pe o sursă, iar sursa n-ar fi fost numită.
Formularea păstrată spune la fel de mult din date: cum ajung elevii la o școală nu se vede
aici, deci distanțele dintre școli nu se citesc ca distanțe între ce adaugă școlile.

**Contribuția școlii** — ce adaugă școala peste ce prezicea intrarea — e în afara datelor.
`STARE.md` consemnează firul valoare adăugată ca blocat pe date până în 2027.

**Ce lipsește de pe pagină.** Nici conceptul, nici limita nu apar în `index.html`. Textul
numește mediana, pe rând, „nivelul școlii", „școli bune", „școli de elită" și o folosește ca
bază de clasament. Un cititor politic va citi din asta contribuția școlii. Recomandarea mea:
o casetă de limite care spune în cuvinte ce măsoară cifra și ce nu se poate observa, iar
„școli bune" / „de elită" înlocuite cu formularea care ține de rezultatul cohortei.

Ce se agregă — media sau mediana notelor — rămâne o alegere între două construcții pe care
ontologia le permite deopotrivă. Proiectul a ales mediana pe temeiul distribuției (diferența
medie–mediană corelată r = −0,64 cu nivelul școlii); decizia e consemnată în `STARE.md`.

## 3. Operaționalizare

### Praguri — rezolvat pe 3 august 2026

Erau trei praguri diferite în același raport, declarat doar unul: 15 la graficele care numesc
școli, 8 la Kruskal-Wallis și Friedman, plus condiția de prezență în toți cei șase ani la
Friedman. Cele trei dădeau trei mulțimi de școli, prezentate una lângă alta ca despre același
oraș, iar valorile intraseră în cod fără justificare.

| Unde | Prag | Din ce criteriu | Declarat pe pagină |
|---|---|---|---|
| graficele care numesc o școală | 18 candidați | interval mai îngust de 1,5 puncte | da |
| Kruskal-Wallis și Friedman | 9 candidați | interval mai îngust de 2,5 puncte | da |
| Friedman, în plus | prezență în toți cei 6 ani | cere blocuri complete | da |

Pragurile sunt acum **calculate din precizia declarată**, la fiecare rulare
(`prag_incertitudine.py` → `praguri.py`), nu scrise în scripturi. Curba lățimii intervalului
în funcție de numărul de candidați **nu are cot**, deci datele nu pot da un prag — pot doar
traduce în număr de candidați o alegere de precizie, iar alegerea e a autorului.

O variantă anterioară a criteriului măsura ce fracțiune din câmpul orașului acoperă
intervalul. A fost abandonată fiindcă e circulară: ridicând pragul, școlile mici ies din câmp,
câmpul se îngustează, fiecare interval acoperă o fracțiune mai mare, deci pragul urcă din nou.

### Cazuri de graniță fără regulă scrisă

- **elevii neprezentați** — verificat azi în cod și în fișiere. Fișierul de rezultate îi
  înregistrează: are coloanele `STATUS ROMANA` și `STATUS MATEMATICA`, cu valorile PREZENT și
  ABSENT. În 2025, la nivel național, 6.994 din 159.229 de candidați (4,4%) n-au medie. La
  BAC decizia a fost luată explicit — neprezentații intră în mediană, așezați jos, fără notă.
  **La EN nu există decizie: `extract_candidati_raw.py` păstrează rândul numai dacă `MEDIA` e
  numerică, deci absenții cad tăcut**, iar coloanele de status nu sunt citite de niciun script
  al lanțului EN.

  **Miza, măsurată pe Timișoara (3 august 2026).** Absenții sunt 0,9–1,8% din candidații
  orașului, an de an — mult sub cei 4,4% naționali. Aplicând `mediana_cu_neprezentati` pe școlile
  cu minimum 15 candidați, mediana se mută la 5–8 școli din 29–32, în fiecare an. La cele mai
  multe mișcarea e sub 0,1 puncte, dar nu peste tot: Șc. nr. 21 „Vicențiu Babeș" 2022, cu 13
  absenți, trece de la 6,700 la 6,110; Șc. nr. 20 în 2022 de la 4,960 la 4,185 (6 absenți din
  22); Șc. nr. 19 „Avram Iancu" 2025, cu 13 absenți, de la 8,570 la 8,400. Nicio școală n-a
  ajuns în cazul în care mediana cade în blocul absenților.

  Tiparul e cel de la BAC: absenții se strâng la școlile mici și la cele cu mediană joasă,
  deci includerea lor coboară mai ales coada de jos a clasamentului. Ce s-a măsurat aici sunt
  medianele, nu rangurile.
- **școlile cu recrutare proprie** — Waldorf, liceele teologice, Lenau cu predare în germană.
  Intră în același clasament cu școlile de cartier. Cu ce justificare?
- **ordinea coloanelor din strip-plot** e rangul din 2025. Unde stau școlile care lipsesc din
  2025?
- **apartenența elevului la școală** — stabilită de autor: elevii care au făcut acea școală.
  Fișierul are o singură coloană de unitate (`COD SIIIR`), fără o a doua pentru centrul de
  examen, iar alături stă `MEDIA V-VIII` — media claselor V-VIII, pe care doar școala de
  proveniență o poate raporta. Asta susține citirea autorului, fără s-o dovedească; dovada ar
  fi în documentația setului de pe data.gov.ro.

## 4. Instrument

Partea solidă a lanțului. Valoarea se produce trasabil: fișierele per candidat de pe
data.gov.ro, identificator `COD SIIIR`, scripturile din `scripts/`, JSON-urile derivate din
`date/`. La orice cifră se poate arăta cu degetul unde se calculează.

Două lucruri lipsesc:

**Absența nu e codată, la două niveluri.**

La nivelul elevului, absentul e înregistrat în fișier (`STATUS`) și aruncat la extracție —
vezi treapta 3.

La nivelul școlii, când o școală lipsește dintr-un an, cheia pur și simplu nu există în
`medii_pe_ani`. Trei stări ale lumii ajung în același gol: școala n-a avut absolvenți în acel
an · a avut, dar sub pragul de 15 · codul ei SIIIR nu s-a găsit în registru
(`if code not in registry: continue`). Legenda paginii — „liniile întrerupte marchează anii în
care școala a avut sub 15 candidați" — afirmă că e a doua, fără ca datele s-o poată susține.

**Cifrele din text sunt scrise de mână.** `index.html` n-are generator, spre deosebire de
`bac.html`, unde `build_bac_html.py` recalculează casetele la fiecare rulare. Verificate azi
contra `friedman_mediane.json` și `medie_vs_mediana_percentil.json`, toate corespund. Dar
corespund azi; la prima recalculare rămân în urmă tăcut. La BAC lecția e deja consemnată în
`STARE.md`: „au rămas o dată în urmă, nu se mai repetă".

## 5. Relații așteptate

**Treapta a fost sărită.** Nu există, nici în repo nici în `STARE.md`, o listă de așteptări
scrisă înainte de a vedea datele.

Consecința e concretă, nu formală. Pagina afirmă: dacă traiectoriile orașelor ar fi fost
divergente, eterogenitatea ar fi fost locală; ele coboară și urcă împreună, deci efectul e
comun. Ambele rezultate erau povestibile după fapt, cu aceeași convingere. Nimic nu fusese
exclus dinainte, deci tiparul găsit nu se distinge de un artefact al măsurării.

Se consemnează că treapta s-a sărit. Nu se completează retroactiv.

## 6. Cine scrie interpretările

Nedecis. Până acum textele de pe pagină au fost propuse de mine și acceptate de autor, fără o
convenție scrisă despre ce propun, ce scrie el și ce trece prin el înainte de publicare.

## Ce a rămas nedecis (3 august 2026)

1. Anul, examenul și generația — intră în inventarul de entități sau ies din text?
2. Ce concept citește mediana unei școli: rezultatul cohortei, selecția la intrare, sau
   contribuția școlii?
3. Se scrie pe pagină limita pe care `STARE.md` o consemnează deja?
4. ~~Cele trei praguri~~ — **rezolvat 3 august 2026**: calculate din precizia declarată
   (1,5 puncte la grafice → 18, 2,5 la teste → 9) și scrise pe pagină.
5. Regula pentru elevii neprezentați la EN — azi cad tăcut; la BAC decizia a fost explicită.
6. Regula pentru școlile cu recrutare proprie.
7. Codarea absenței la nivel de școală: se distinge „fără absolvenți" de „sub prag" de
   „cod negăsit în registru"?
8. `index.html` capătă generator, ca `bac.html`?
9. Cine scrie textele de interpretare.
