# Varianța structurală: cele 9 entități oraș × filieră.
#
# PREZUMȚIA DE BAZĂ (decizia userului, 2026-07-17): în același oraș, cele trei filiere
# sunt trei lumi sociale diferite. De aici, două consecințe care structurează tot:
#  1. Nu se compară nimic între filiere. Un clasament al liceelor care amestecă filierele
#     ar fi, în fapt, un clasament al filierelor: primele ar fi teoreticele, ultimele
#     tehnologicele, iar cititorul ar crede că citește despre școli când citește despre
#     tipuri de școli. Condiție de face validity, nu de statistică.
#  2. RANGURILE SE CALCULEAZĂ ÎN INTERIORUL FILIEREI. O versiune anterioară făcea un
#     Kruskal-Wallis omnibus pe toate cele 9 entități deodată: ieșea p<1e-8 și ε²=0,4-0,6
#     în fiecare an, dar aia nu era o descoperire — era prezumția de mai sus apărând în
#     rezultat. Testul măsura că filiera contează, adică exact ce luăm ca dat, iar rangurile
#     lui clasau licee teoretice față de tehnologice. Ambele, greșit.
#
# Ce face scriptul: descrie cele 9 entități și verifică varianța structurală ÎNTRE ORAȘE,
# în interiorul fiecărei filiere. Rolul celor 3 orașe e să ne spună cât din variație e
# structurală; ce rămâne — diferența dintre licee în aceeași filieră și același oraș — e
# subiectul raportului.
#
# MULTIPLICITATE: o familie pe an, declarată dinainte — aceeași filieră, între orașe:
# 3 filiere × 3 perechi de orașe = 9 comparații, Holm pe familia asta.
#
# Unitatea de observație = celula liceu × filieră (un colegiu tehnic poate avea și clase
# teoretice, și tehnologice — filiera e proprietate a clasei, nu a școlii; deci un liceu
# poate apărea în două filiere, cu celule diferite).
# Statistica = mediana mediilor recalculate, promoția curentă. Fără pooling temporal
# (Friedman l-a exclus: p < 1e-6 în toate orașele), deci totul se face pe fiecare an.
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
from collections import defaultdict, Counter
from statistici import median_of, kruskal, chi2_sf, dunn_raw, holm, mediana_cenzurata

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..', 'date', 'bac')
MIN_N = 8            # candidați minimi pe celulă liceu×filieră×an
MIN_LICEE = 3        # licee minime pe oraș ca filiera să intre în test într-un an
YEARS = list(range(2017, 2026))
CITIES = ['CLUJ-NAPOCA', 'IAȘI', 'TIMIȘOARA']
FILIERE = ['teoretica', 'tehnologica', 'vocationala']
SCURT = {'CLUJ-NAPOCA': 'CJ', 'IAȘI': 'IS', 'TIMIȘOARA': 'TM'}

with open(os.path.join(BASE, 'candidati_bac.json'), encoding='utf-8') as f:
    data = json.load(f)
orase = data['orase']

# Celula = TOȚI candidații promoției curente din liceul respectiv, în filiera respectivă.
# Cei cu notă intră cu ea; cei fără rezultat (absenți, eliminați) intră fără notă, așezați
# jos — vezi mediana_cenzurata() în statistici.py.
cell = defaultdict(list)     # (siiir, an, filiera) -> [medii]
fara = Counter()             # (siiir, an, filiera) -> câți fără rezultat
cand = Counter()             # (oras, an, filiera) -> nr. candidați
for (an, siiir, forma, filiera, profil, promo, status,
     medie_pub, medie_calc) in data['candidati']:
    if promo != 1 or filiera not in FILIERE:
        continue
    cand[(orase[siiir], an, filiera)] += 1
    if medie_calc is not None:
        cell[(siiir, an, filiera)].append(medie_calc)
    else:
        fara[(siiir, an, filiera)] += 1

def n_total(k):
    return len(cell[k]) + fara[k]

def mediana_celulei(k):
    return mediana_cenzurata(cell[k], fara[k])

# ---------- 1. compoziția ----------
print('1. COMPOZIȚIA — ponderea candidaților pe filieră (promoția curentă)')
print(f'{"an":>5}   ' + '   '.join(f'{c:^24}' for c in CITIES))
print(f'{"":>5}   ' + '   '.join(' teor  tehn   voc      n' for _ in CITIES))
comp = {}
for an in YEARS:
    linie = f'{an:>5}   '
    for c in CITIES:
        tot = sum(cand[(c, an, f)] for f in FILIERE)
        pon = {f: cand[(c, an, f)] / tot for f in FILIERE}
        comp[f'{c}|{an}'] = {**{f: round(pon[f], 3) for f in FILIERE}, 'n': tot}
        linie += (f'{pon["teoretica"]:>5.0%} {pon["tehnologica"]:>5.0%} '
                  f'{pon["vocationala"]:>5.0%} {tot:>6,}   ')
    print(linie)

# ---------- 2. cele 9 entități: mediana pe an ----------
print('\n2. CELE 9 ENTITĂȚI — mediana medianelor de liceu (n = licee în entitate)')
print(f'{"an":>5}  ' + '  '.join(f'{SCURT[c]+"-"+f[:4]:>12}' for f in FILIERE for c in CITIES))
entit = defaultdict(dict)
for an in YEARS:
    groups = defaultdict(list)
    for k in list(cell) + [x for x in fara if x not in cell]:
        siiir, a, f = k
        if a == an and n_total(k) >= MIN_N:
            m = mediana_celulei(k)
            if m is not None:
                groups[(orase[siiir], f)].append(m)
    linie = f'{an:>5}  '
    for f in FILIERE:
        for c in CITIES:
            g = groups[(c, f)]
            if g:
                m = median_of(g)
                entit[str(an)][f'{SCURT[c]}-{f}'] = {'mediana': round(m, 3), 'n_licee': len(g)}
                linie += f'{m:>7.2f}({len(g):>2})'
            else:
                linie += f'{"—":>12}'
    print(linie)

# ---------- 3. varianța structurală între orașe, ÎN INTERIORUL fiecărei filiere ----------
print('\n3. ÎNTRE ORAȘE, ÎN INTERIORUL FILIEREI — există varianță structurală?')
print('   Kruskal-Wallis pe cele 3 orașe, cu ranguri calculate DOAR în interiorul')
print('   filierei. Familia pre-specificată: 9 comparații pe an (3 filiere × 3 perechi),')
print('   Holm pe familia asta.\n')
rez = {}
scor = defaultdict(lambda: {'ani': 0, 'tm_ultima': 0, 'tm_sub_cj_semnif': 0})
for an in YEARS:
    brute, per_fil = [], {}
    for fil in FILIERE:
        groups = defaultdict(list)
        for k in list(cell) + [x for x in fara if x not in cell]:
            siiir, a, f = k
            if a == an and f == fil and n_total(k) >= MIN_N:
                m = mediana_celulei(k)
                if m is not None:
                    groups[orase[siiir]].append(m)
        glist = [groups[c] for c in CITIES]
        sizes = [len(g) for g in glist]
        if min(sizes) < MIN_LICEE:
            per_fil[fil] = {'n_licee': dict(zip(CITIES, sizes)), 'test': 'nefăcut'}
            continue
        H, N, rank_sums = kruskal(glist)          # ranguri DOAR în interiorul filierei
        p = chi2_sf(H, len(CITIES) - 1)
        eps2 = (H - len(CITIES) + 1) / (N - len(CITIES))
        pairs, _ = dunn_raw([SCURT[c] for c in CITIES], glist, rank_sums, N)
        for d in pairs:
            d['filiera'] = fil
        brute += pairs
        meds = {c: round(median_of(groups[c]), 3) for c in CITIES}
        per_fil[fil] = {'n_licee': dict(zip(CITIES, sizes)), 'mediane': meds,
                        'H': round(H, 3), 'p': float(f'{p:.4g}'), 'epsilon2': round(eps2, 4)}
        s = scor[fil]
        s['ani'] += 1
        if meds['TIMIȘOARA'] == min(meds.values()):
            s['tm_ultima'] += 1
    holm(brute)                                    # o singură familie pe an
    for d in brute:
        per_fil[d['filiera']].setdefault('dunn', []).append(
            {'pereche': d['pereche'], 'z': d['z'], 'p_holm': d['p_holm']})
        if d['pereche'] == 'CJ vs TM' and d['p_holm'] < 0.05:
            m = per_fil[d['filiera']]['mediane']
            if m['TIMIȘOARA'] < m['CLUJ-NAPOCA']:
                scor[d['filiera']]['tm_sub_cj_semnif'] += 1
    rez[str(an)] = per_fil
    print(f'  ── {an}')
    for fil in FILIERE:
        pf = per_fil[fil]
        if pf.get('test') == 'nefăcut':
            print(f'     {fil:<12} n={list(pf["n_licee"].values())} — prea puține licee')
            continue
        semn = '***' if pf['p'] < 0.001 else '**' if pf['p'] < 0.01 else '*' if pf['p'] < 0.05 else 'ns'
        m = pf['mediane']
        print(f'     {fil:<12} n={list(pf["n_licee"].values())} H={pf["H"]:5.2f} '
              f'p={pf["p"]:8.4g} {semn:>3} ε²={pf["epsilon2"]:6.3f} | '
              f'CJ={m["CLUJ-NAPOCA"]:5.2f} IS={m["IAȘI"]:5.2f} TM={m["TIMIȘOARA"]:5.2f} | '
              + ' '.join(f'{d["pereche"]}:{d["p_holm"]:.3g}{"*" if d["p_holm"]<0.05 else ""}'
                         for d in pf['dunn']))

print('\n4. REZUMAT — în interiorul aceleiași filiere, unde stă Timișoara?')
for fil in FILIERE:
    s = scor[fil]
    if s['ani']:
        print(f'  {fil:<12}: ultima din 3 în {s["tm_ultima"]}/{s["ani"]} ani | '
              f'sub Cluj semnificativ în {s["tm_sub_cj_semnif"]}/{s["ani"]} ani')

op = os.path.join(BASE, 'filiera_bac.json')
with open(op, 'w', encoding='utf-8') as f:
    json.dump({'prezumtie': 'filierele sunt lumi sociale distincte; ranguri și comparații '
                            'doar în interiorul filierei',
               'min_candidati_celula': MIN_N, 'min_licee_entitate': MIN_LICEE,
               'familia_dunn': 'aceeași filieră, între orașe — 9 comparații/an, Holm',
               'compozitie': comp, 'entitati': dict(entit), 'pe_ani': rez,
               'rezumat': {k: dict(v) for k, v in scor.items()}},
              f, ensure_ascii=False, indent=2)
print(f'\nsalvat: {op}')
