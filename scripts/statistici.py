# Funcții statistice fără scipy (nu e instalat), folosite de teste_bac.py și
# filiera_bac.py. Extrase într-un modul comun ca să nu existe două copii ale
# aceleiași matematici.
import math
from collections import Counter

def median_of(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2

# --- mediana cu neprezentații așezați jos (decizia userului, 2026-07-17) ---
#
# Neprezentații nu primesc notă, dar intră în calcul, așezați sub toți cei care s-au
# prezentat. Se poate, fiindcă mediana e o poziție, nu o medie: ca să afli cine e la
# mijloc îți trebuie doar CÂȚI sunt sub el, nu CÂT au luat. Un liceu cu mulți
# neprezentați e astfel penalizat chiar în cifra de performanță, fără să inventăm note.
#
# Asumpția, mai slabă decât a imputării dar tot o asumpție: un neprezentat stă sub
# oricine s-a prezentat. Cei mai mulți sunt elevi care s-au ferit de examen, dar unii
# au plecat în străinătate sau au fost bolnavi — pe toți îi punem sub cel cu 1,00.
#
# Implementare: îi reprezentăm cu o santinelă sub scala de note. VALOAREA SANTINELEI E
# IRELEVANTĂ prin construcție — orice număr sub mediană dă aceleași poziții, deci aceeași
# mediană (0,0 sau 4,5 dau identic). Tocmai de aceea nu trebuie inventată una. Santinela
# există doar ca lista să poată fi sortată și reeșantionată la bootstrap ca oricare alta.
# Singurul caz în care iese la iveală e cel patologic, cu peste jumătate neprezentați:
# atunci mediana chiar cade în blocul lor și nu e definită — o semnalăm cu None.
SUB = 0.0        # sub 1,00, adică sub orice notă posibilă

def cu_neprezentati(note, n_fara_rezultat):
    """Lista pe care se calculează mediana liceului: notele, plus neprezentații dedesubt."""
    return [SUB] * n_fara_rezultat + list(note)

def mediana_cenzurata(note, n_fara_rezultat):
    """Mediana liceului, cu neprezentații jos. None dacă mediana cade în blocul lor."""
    if not note and not n_fara_rezultat:
        return None
    m = median_of(cu_neprezentati(note, n_fara_rezultat))
    return None if m <= SUB else m

def rank_all(values):
    """Ranguri cu medierea ex-aequo-urilor."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for kk in range(i, j + 1):
            ranks[order[kk]] = avg
        i = j + 1
    return ranks

def chi2_sf(x, df):
    """Coada superioară a lui chi-pătrat, prin gamma incompletă regularizată."""
    a, x2 = df / 2.0, x / 2.0
    if x2 <= 0:
        return 1.0
    if x2 < a + 1:
        term = 1.0 / a
        s = term
        n = 0
        while True:
            n += 1
            term *= x2 / (a + n)
            s += term
            if term < s * 1e-14 or n > 1000:
                break
        return 1.0 - s * math.exp(-x2 + a * math.log(x2) - math.lgamma(a))
    tiny = 1e-300
    b = x2 + 1 - a
    c = 1 / tiny
    d = 1 / b
    h = d
    for i in range(1, 300):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny: d = tiny
        c = b + an / c
        if abs(c) < tiny: c = tiny
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return h * math.exp(-x2 + a * math.log(x2) - math.lgamma(a))

def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))

def kruskal(glist):
    """H corectat pentru ex-aequo, N total, sumele de ranguri pe grup."""
    all_v = [v for g in glist for v in g]
    N = len(all_v)
    ranks = rank_all(all_v)
    H, pos, rank_sums = 0.0, 0, []
    for g in glist:
        rs = sum(ranks[pos:pos + len(g)])
        rank_sums.append(rs)
        H += rs * rs / len(g)
        pos += len(g)
    H = 12.0 / (N * (N + 1)) * H - 3 * (N + 1)
    cnt = Counter(all_v)
    corr = 1 - sum(t ** 3 - t for t in cnt.values()) / (N ** 3 - N)
    if corr > 0:
        H /= corr
    return H, N, rank_sums

def dunn_raw(etichete, glist, rank_sums, N, perechi=None):
    """Z și p brut pentru perechile Dunn, FĂRĂ corecție. Rangurile sunt cele primite,
    deci apelantul decide în ce univers se clasează (vezi filiera_bac.py: rangurile se
    calculează în interiorul filierei, nu între filiere)."""
    k = len(glist)
    sizes = [len(g) for g in glist]
    mean_ranks = [rs / n for rs, n in zip(rank_sums, sizes)]
    all_v = [v for g in glist for v in g]
    cnt = Counter(all_v)
    tie_term = sum(t ** 3 - t for t in cnt.values()) / (12 * (N - 1))
    if perechi is None:
        perechi = [(i, j) for i in range(k) for j in range(i + 1, k)]
    out = []
    for i, j in perechi:
        se = math.sqrt((N * (N + 1) / 12 - tie_term) * (1 / sizes[i] + 1 / sizes[j]))
        if se == 0:
            continue
        z = (mean_ranks[i] - mean_ranks[j]) / se
        out.append({'pereche': f'{etichete[i]} vs {etichete[j]}', 'z': round(z, 3),
                    'p_brut': 2 * norm_sf(abs(z))})
    return out, mean_ranks

def holm(items, cheie='p_brut'):
    """Corecție Holm peste o familie de comparații declarată de apelant."""
    items = sorted(items, key=lambda d: d[cheie])
    n, prev = len(items), 0.0
    for i, d in enumerate(items):
        padj = min(1.0, max(prev, (n - i) * d[cheie]))
        prev = padj
        d['p_holm'] = round(padj, 5)
    return items

def dunn_holm(etichete, glist, rank_sums, N, perechi=None):
    """Post-hoc Dunn, cu corecție Holm.

    `perechi` = listă de (i, j) pentru o familie de comparații PRE-SPECIFICATĂ. Când e
    dată, Holm se aplică doar pe ea, nu pe toate perechile. Asta contează la multe
    grupuri: cu 9 grupuri, toate perechile înseamnă 36 de comparații, iar Holm peste 36
    taie puterea plătind pentru comparații fără interes. Rangurile rămân cele din testul
    omnibus (așa lucrează Dunn) — se restrânge doar familia, nu clasarea.
    """
    k = len(glist)
    sizes = [len(g) for g in glist]
    mean_ranks = [rs / n for rs, n in zip(rank_sums, sizes)]
    all_v = [v for g in glist for v in g]
    cnt = Counter(all_v)
    tie_term = sum(t ** 3 - t for t in cnt.values()) / (12 * (N - 1))
    if perechi is None:
        perechi = [(i, j) for i in range(k) for j in range(i + 1, k)]
    rez = []
    for i, j in perechi:
        se = math.sqrt((N * (N + 1) / 12 - tie_term) * (1 / sizes[i] + 1 / sizes[j]))
        if se == 0:
            continue
        z = (mean_ranks[i] - mean_ranks[j]) / se
        rez.append([etichete[i], etichete[j], z, 2 * norm_sf(abs(z))])
    rez.sort(key=lambda t: t[3])
    prev, out = 0.0, []
    n_p = len(rez)
    for pi, (a, b, z, praw) in enumerate(rez):
        padj = min(1.0, max(prev, (n_p - pi) * praw))
        prev = padj
        out.append({'pereche': f'{a} vs {b}', 'z': round(z, 3), 'p_holm': round(padj, 5)})
    return out, mean_ranks
