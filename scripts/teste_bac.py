# Pasul 5 — testele structurale pe BAC, replicând metodologia EN VIII
# (kw_pe_ani.py + friedman_mediane.py), dar pe media recalculată și promoția curentă.
#
# Unitatea de analiză = liceul. Statistica per liceu-an = MEDIANA mediilor candidaților
# (decizie luată la pasul 4 pe distribuțiile BAC: 85% dintre celulele școală-an sunt
# asimetrice la stânga, 50% semnificativ, iar deviația medie-mediană corelează −0,53 cu
# nivelul școlii, deci media penalizează sistematic liceele bune).
#
# Două întrebări:
#  1. KRUSKAL-WALLIS pe fiecare an: diferă cele 3 orașe între ele? Observațiile sunt
#     medianele liceelor, grupate pe oraș. Post-hoc Dunn cu corecție Holm.
#  2. FRIEDMAN pe fiecare oraș: blocuri = liceele prezente în toți anii, tratament = anul.
#     Testează dacă anii sunt schimbabili între ei. Dacă ies diferiți, NU se face pooling
#     temporal — regula proiectului: fără pooling fără test.
import sys, os, json, math
sys.stdout.reconfigure(encoding='utf-8')
from collections import defaultdict, Counter
from statistici import median_of, rank_all, chi2_sf, norm_sf, kruskal, mediana_cenzurata

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..', 'date', 'bac')
MIN_N = 8            # ca la EN VIII: sub 8 candidați, mediana liceului-an nu e folosită
YEARS = list(range(2017, 2026))
CITIES = ['CLUJ-NAPOCA', 'IAȘI', 'TIMIȘOARA']

with open(os.path.join(BASE, 'candidati_bac.json'), encoding='utf-8') as f:
    data = json.load(f)
orase, den = data['orase'], data['denumiri']

# liceu-an -> mediana mediilor (promoția curentă, media recalculată)
# Celula = TOȚI candidații promoției curente; cei fără rezultat intră fără notă, jos.
# Unitatea e celula LICEU × FILIERĂ, nu liceul. Sub prezumția că filierele sunt lumi
# sociale distincte, o mediană a unui liceu calculată între filiere n-are referință — nici
# măcar în interiorul unui bloc Friedman, fiindcă valoarea comparată de la an la an ar
# rămâne o mediană între filiere. Deci blocul e celula, iar un colegiu tehnic cu clase
# teoretice și tehnologice contribuie cu două blocuri.
FILIERE = ('teoretica', 'tehnologica', 'vocationala')
acc = defaultdict(list)
fara = Counter()
for (an, siiir, forma, filiera, profil, promo, status,
     medie_pub, medie_calc) in data['candidati']:
    if promo != 1 or filiera not in FILIERE:
        continue
    if medie_calc is not None:
        acc[(siiir, filiera, an)].append(medie_calc)
    else:
        fara[(siiir, filiera, an)] += 1
matrix = defaultdict(dict)          # (siiir, filiera) -> {an: mediana}
n_cand = defaultdict(dict)
for k in set(acc) | set(fara):
    siiir, filiera, an = k
    n = len(acc[k]) + fara[k]
    if n >= MIN_N:
        m = mediana_cenzurata(acc[k], fara[k])
        if m is not None:
            matrix[(siiir, filiera)][an] = m
            n_cand[(siiir, filiera)][an] = n

def rank_row(vals):
    return rank_all(vals)

# ---------- 1. Kruskal-Wallis pe fiecare an ----------
out = {'min_candidati_per_liceu_an': MIN_N, 'statistica': 'mediana medie_calc, promoția curentă',
       'kw_pe_ani': {}, 'friedman_pe_orase': {}}
print(f'Unitatea = liceul; statistica = mediana mediilor (promoția curentă, medie recalculată)')
print(f'Prag: minim {MIN_N} candidați pe liceu-an\n')
print('1. KRUSKAL-WALLIS pe fiecare an — diferă cele 3 orașe?')
for an in YEARS:
    groups = defaultdict(list)
    for (siiir, filiera), ys in matrix.items():
        if an in ys:
            groups[orase[siiir]].append(ys[an])
    glist = [groups[c] for c in CITIES]
    sizes = [len(g) for g in glist]
    if min(sizes) < 3:
        continue
    H, N, rank_sums = kruskal(glist)
    k = len(CITIES)
    p = chi2_sf(H, k - 1)
    eps2 = (H - k + 1) / (N - k)
    mean_ranks = [rs / n for rs, n in zip(rank_sums, sizes)]
    meds = {c: round(median_of(groups[c]), 3) for c in CITIES}
    # Dunn + Holm
    all_v = [v for g in glist for v in g]
    cnt = Counter(all_v)
    tie_term = sum(t ** 3 - t for t in cnt.values()) / (12 * (N - 1))
    pairs = []
    for i in range(k):
        for j in range(i + 1, k):
            se = math.sqrt((N * (N + 1) / 12 - tie_term) * (1 / sizes[i] + 1 / sizes[j]))
            z = abs(mean_ranks[i] - mean_ranks[j]) / se
            pairs.append([CITIES[i], CITIES[j], z, 2 * norm_sf(z)])
    pairs.sort(key=lambda t: t[3])
    prev, dunn = 0.0, []
    for pi, (a, b, z, praw) in enumerate(pairs):
        padj = min(1.0, max(prev, (k - pi) * praw))
        prev = padj
        dunn.append({'pereche': f'{a} vs {b}', 'z': round(z, 3), 'p_holm': round(padj, 5)})
    out['kw_pe_ani'][str(an)] = {
        'n_licee': dict(zip(CITIES, sizes)), 'mediana_pe_oras': meds,
        'rang_mediu': {c: round(mr, 1) for c, mr in zip(CITIES, mean_ranks)},
        'H': round(H, 3), 'p': float(f'{p:.4g}'), 'epsilon2': round(eps2, 4),
        'dunn_holm': dunn}
    semn = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    print(f'  {an}: n={sizes} H={H:6.2f} p={p:9.4g} {semn:>3} ε²={eps2:.3f} '
          f'mediane={[meds[c] for c in CITIES]}')
    for dd in dunn:
        mark = '*' if dd['p_holm'] < 0.05 else ' '
        print(f'        {mark} {dd["pereche"]:<28} z={dd["z"]:6.3f}  p_holm={dd["p_holm"]:.4g}')

# ---------- 2. Friedman pe fiecare oraș: sunt anii schimbabili? ----------
print(f'\n2. FRIEDMAN pe fiecare oraș — blocuri = celulele liceu×filieră prezente în toți cei {len(YEARS)} anii, '
      f'tratament = anul')
print('   (dacă anii diferă semnificativ, NU se face pooling temporal)')
# Câte un Friedman pe fiecare oraș ȘI filieră: filierele fiind lumi distincte, un rang
# mediu al anilor calculat între ele ar amesteca trei traiectorii care n-au de ce să
# semene. Așa se și vede dacă efectul de an e același în toate trei.
k = len(YEARS)
FILIERE_L = ('teoretica', 'tehnologica', 'vocationala')
for city in CITIES:
  for fil in FILIERE_L:
    blocks = []
    for (siiir, filiera), ys in matrix.items():
        if orase[siiir] == city and filiera == fil and all(y in ys for y in YEARS):
            blocks.append([ys[y] for y in YEARS])
    n = len(blocks)
    if n < 3:
        print(f'  {city} · {fil}: doar {n} celule balansate — test nefăcut')
        continue
    rank_sums = [0.0] * k
    tie_num = 0.0
    for b in blocks:
        rr = rank_row(b)
        for i, r in enumerate(rr):
            rank_sums[i] += r
        cnt = Counter(b)
        tie_num += sum(t ** 3 - t for t in cnt.values())
    Q = 12.0 / (n * k * (k + 1)) * sum(rs * rs for rs in rank_sums) - 3 * n * (k + 1)
    denom = 1 - tie_num / (n * k * (k * k - 1))
    if denom > 0:
        Q /= denom
    p = chi2_sf(Q, k - 1)
    W = Q / (n * (k - 1))
    mean_ranks = [round(rs / n, 2) for rs in rank_sums]
    out['friedman_pe_orase'][f'{city}|{fil}'] = {
        'n_celule_balansate': n, 'Q': round(Q, 3), 'df': k - 1,
        'p': float(f'{p:.4g}'), 'kendall_W': round(W, 4),
        'rang_mediu_pe_an': dict(zip(map(str, YEARS), mean_ranks))}
    semn = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    print(f'  {city:<12} {fil:<12} n={n:>3} Q={Q:6.2f} p={p:9.4g} {semn:<3} W={W:.3f}  ' + '  '.join(f'{y}:{r:.1f}' for y, r in zip(YEARS, mean_ranks)))

op = os.path.join(BASE, 'teste_bac.json')
with open(op, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f'\nsalvat: {op}')
