# Cât de bine prezic notele date de școală nota de la examen, la același elev.
#
# Întrebarea userului, 3 august 2026. Se pune la nivel de individ, fiindcă acolo există
# perechea: fiecare elev are o medie a claselor V-VIII, dată de școala lui, și o medie la
# Evaluarea Națională, dată de un examen din afara școlii. Ambele pe scala 1-10.
#
# Se măsoară două lucruri diferite, care se confundă ușor:
#   DECALAJUL   — cu cât notează școala peste examen. Mediana diferențelor per elev.
#   ORDONAREA   — dacă elevii pe care școala îi pune mai sus ies mai sus și la examen.
# O școală poate nota generos și totuși ordona perfect, dacă decalajul e același pentru toți.
#
# ⚠️ RESTRICȚIA DE AMPLITUDINE. Corelația din interiorul unei școli scade mecanic acolo unde
# notele școlii sunt înghesuite: dacă toți elevii au 9,8, nu mai e ce ordona, iar corelația
# iese mică fără ca școala să fi greșit ceva. De aceea se raportează și PANTA regresiei
# notei de examen pe nota școlii, care nu se comprimă la fel, și împrăștierea notelor școlii
# alături de corelație. Fără ele, clasamentul „cine prezice mai bine" ar fi în bună parte
# un clasament al școlilor cu elevi eterogeni.
import io, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from praguri import prag
from statistici import median_of, rank_all, kruskal, chi2_sf

DATE = os.path.join(HERE, '..', 'date')
YEARS = [str(y) for y in range(2020, 2026)]
ORASE = ['CLUJ-NAPOCA', 'IAȘI', 'TIMIȘOARA']
MIN_N = prag('prag_grafice')
OUT = os.path.join(DATE, 'predictie_scoala.json')

NOTE = json.load(io.open(os.path.join(DATE, 'note_en.json'), encoding='utf-8'))
reg, den = NOTE['orase'], NOTE['denumiri']


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sx = (sum((x - mx) ** 2 for x in xs) / n) ** .5
    sy = (sum((y - my) ** 2 for y in ys) / n) ** .5
    if sx == 0 or sy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (n * sx * sy)


def spearman(xs, ys):
    return pearson(rank_all(xs), rank_all(ys))


def panta(xs, ys):
    """Panta regresiei lui y pe x: cu cât crește nota de examen la un punct în plus la școală."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    return None if sxx == 0 else sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def cuartile(v):
    s = sorted(v)
    n = len(s)
    return s[n // 4], s[(3 * n) // 4]


celule = []
for an in YEARS:
    for cod, r in NOTE['ani'][an]['scoli'].items():
        oras = reg.get(cod)
        per = r.get('v8_en') or []
        if oras is None or len(per) < MIN_N:
            continue
        v8 = [p[0] for p in per]
        en = [p[1] for p in per]
        q1, q3 = cuartile(v8)
        celule.append({
            'an': an, 'oras': oras, 'cod': cod, 'denumire': den.get(cod, cod),
            'n': len(per),
            'decalaj': round(median_of([a - b for a, b in zip(v8, en)]), 3),
            'spearman': (lambda x: None if x is None else round(x, 3))(spearman(v8, en)),
            'pearson': (lambda x: None if x is None else round(x, 3))(pearson(v8, en)),
            'panta': (lambda x: None if x is None else round(x, 3))(panta(v8, en)),
            'v8_mediana': round(median_of(v8), 2),
            'v8_iqr': round(q3 - q1, 2),
            'en_mediana': round(median_of(en), 2),
        })
    print(f'{an}: {sum(1 for c in celule if c["an"] == an)} celule')

# la nivel de oraș, pe toți elevii deodată
pe_oras = {}
for oras in ORASE:
    v8, en = [], []
    for an in YEARS:
        for cod, r in NOTE['ani'][an]['scoli'].items():
            if reg.get(cod) == oras:
                for a, b in (r.get('v8_en') or []):
                    v8.append(a); en.append(b)
    q1, q3 = cuartile(v8)
    pe_oras[oras] = {'n_elevi': len(v8),
                     'decalaj_median': round(median_of([a - b for a, b in zip(v8, en)]), 3),
                     'spearman': round(spearman(v8, en), 3),
                     'panta': round(panta(v8, en), 3),
                     'v8_iqr': round(q3 - q1, 2)}

# Corelația ÎNTRE ȘCOLI, nu între elevi: exact ce arată norul de puncte, unde fiecare punct
# e o școală. Cea pe elevi e altă mărime și ar contrazice figura de lângă ea.
def corelatii_pe_scoli(oras, an):
    pts = [c for c in celule if c['oras'] == oras and c['an'] == an]
    if len(pts) < 5:
        return None
    x = [c['v8_mediana'] for c in pts]
    y = [c['en_mediana'] for c in pts]
    return {'n_scoli': len(pts),
            'pearson': round(pearson(x, y), 3),
            'spearman': round(spearman(x, y), 3),
            'panta': round(panta(x, y), 3),
            'decalaj_median': round(median_of([c['decalaj'] for c in pts]), 3),
            'decalaj_min': round(min(c['decalaj'] for c in pts), 3),
            'decalaj_max': round(max(c['decalaj'] for c in pts), 3),
            'toate_sub_diagonala': all(c['en_mediana'] <= c['v8_mediana'] for c in pts)}


intre_scoli = {o: {a: corelatii_pe_scoli(o, a) for a in YEARS} for o in ORASE}

print()
print(f'Corelația ÎNTRE ȘCOLI, {YEARS[-1]}')
print(f"{'oraș':>13}{'școli':>7}{'Pearson':>9}{'Spearman':>10}{'panta':>8}{'decalaj median':>16}")
for o in ORASE:
    v = intre_scoli[o][YEARS[-1]]
    print(f"{o:>13}{v['n_scoli']:>7}{v['pearson']:>9.3f}{v['spearman']:>10.3f}"
          f"{v['panta']:>8.3f}{v['decalaj_median']:>16.2f}")


# Diferă școlile între ele prin cât notează peste examen?
# Unitatea e ELEVUL, grupurile sunt școlile, mărimea testată e delta lui personal.
# Se rulează pe fiecare an separat și pe toți anii la grămadă — delta poartă și efectul de
# an (un examen mai greu ridică delta la toată lumea), care la grămadă intră ca zgomot.
def kw_delta(oras, ani):
    grupuri = {}
    for an in ani:
        for cod, r in NOTE['ani'][an]['scoli'].items():
            if reg.get(cod) != oras:
                continue
            per = r.get('v8_en') or []
            if len(per) < MIN_N:
                continue
            grupuri.setdefault(cod, []).extend(a - b for a, b in per)
    coduri = [c for c in grupuri if len(grupuri[c]) >= MIN_N]
    if len(coduri) < 3:
        return None
    glist = [grupuri[c] for c in coduri]
    H, N, rs = kruskal(glist)
    k = len(glist)
    med = {c: round(median_of(grupuri[c]), 3) for c in coduri}
    extrem = sorted(med, key=med.get)
    return {'n_scoli': k, 'n_elevi': N, 'H': round(H, 2), 'df': k - 1,
            'p': float(f'{chi2_sf(H, k - 1):.4g}'),
            'epsilon2': round((H - k + 1) / (N - k), 4),
            'delta_median_min': {'scoala': den.get(extrem[0], extrem[0]), 'delta': med[extrem[0]]},
            'delta_median_max': {'scoala': den.get(extrem[-1], extrem[-1]), 'delta': med[extrem[-1]]},
            'delta_median_pe_scoala': med}


# Sunt anii interschimbabili, în privința decalajului? Același design ca la orașe:
# blocuri = școlile prezente în toți anii, tratament = anul, valoarea = delta mediană a
# școlii în acel an. Dacă anii ies ordonați la fel la toate școlile, decalajul se mișcă
# în bloc — semn că vine de la examen, nu de la felul în care notează fiecare școală.
def friedman_delta(oras):
    matrice = {}
    for an in YEARS:
        for cod, r in NOTE['ani'][an]['scoli'].items():
            if reg.get(cod) != oras:
                continue
            per = r.get('v8_en') or []
            if len(per) >= MIN_N:
                matrice.setdefault(cod, {})[an] = median_of([a - b for a, b in per])
    blocuri = [[m[a] for a in YEARS] for m in matrice.values() if all(a in m for a in YEARS)]
    n, k = len(blocuri), len(YEARS)
    if n < 5:
        return None
    sume = [0.0] * k
    tie = 0.0
    for b in blocuri:
        rr = rank_all(b)
        for i, x in enumerate(rr):
            sume[i] += x
        from collections import Counter
        tie += sum(t ** 3 - t for t in Counter(b).values())
    Q = 12.0 / (n * k * (k + 1)) * sum(s * s for s in sume) - 3 * n * (k + 1)
    den_ = 1 - tie / (n * k * (k * k - 1))
    if den_ > 0:
        Q /= den_
    return {'n_scoli': n, 'Q': round(Q, 2), 'df': k - 1,
            'p': float(f'{chi2_sf(Q, k - 1):.4g}'),
            'kendall_W': round(Q / (n * (k - 1)), 4),
            'rang_mediu': {a: round(s / n, 2) for a, s in zip(YEARS, sume)}}


fr_delta = {o: friedman_delta(o) for o in ORASE}

kw_pe_oras = {o: {'la_gramada': kw_delta(o, YEARS),
                  'pe_an': {a: kw_delta(o, [a]) for a in YEARS}}
              for o in ORASE}

print()
print('Diferă școlile prin cât notează peste examen? (KW pe elevi, grupuri = școlile)')
print(f"{'oraș':>13}{'școli':>7}{'elevi':>8}{'p':>11}{'ε²':>9}   interval delta mediană")
for o, v in kw_pe_oras.items():
    g = v['la_gramada']
    print(f"{o:>13}{g['n_scoli']:>7}{g['n_elevi']:>8}{g['p']:>11.4g}{g['epsilon2']:>9.3f}"
          f"   {g['delta_median_min']['delta']:.2f} … {g['delta_median_max']['delta']:.2f}")
print()
print('pe ani separat, ε²:')
for o, v in kw_pe_oras.items():
    print(f"  {o:>13} " + '  '.join(f"{a}:{v['pe_an'][a]['epsilon2']:.3f}"
                                    for a in YEARS if v['pe_an'][a]))

print()
print('Sunt anii interschimbabili, în privința decalajului? (Friedman, blocuri = școlile)')
print(f"{'oraș':>13}{'școli':>7}{'p':>11}{'W':>8}   rang mediu pe an")
for o, v in fr_delta.items():
    if v:
        print(f"{o:>13}{v['n_scoli']:>7}{v['p']:>11.4g}{v['kendall_W']:>8.3f}   "
              + ' '.join(f"{a}:{v['rang_mediu'][a]:.1f}" for a in YEARS))

json.dump({'min_candidati': MIN_N, 'pe_oras': pe_oras, 'intre_scoli': intre_scoli,
           'kw_delta': kw_pe_oras, 'friedman_delta': fr_delta, 'celule': celule},
          io.open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)

print()
print('Pe oraș, toți elevii, toți anii')
print(f"{'oraș':>13}{'elevi':>8}{'decalaj':>9}{'Spearman':>10}{'panta':>8}{'IQR V-VIII':>12}")
for o, v in pe_oras.items():
    print(f"{o:>13}{v['n_elevi']:>8}{v['decalaj_median']:>9.2f}{v['spearman']:>10.3f}"
          f"{v['panta']:>8.3f}{v['v8_iqr']:>12.2f}")

tm = [c for c in celule if c['oras'] == 'TIMIȘOARA' and c['an'] == YEARS[-1]]
print()
print(f'Timișoara, {YEARS[-1]} — școlile după cât de bine ordonează')
print(f"{'școala':44s}{'n':>5}{'decalaj':>9}{'Spearman':>10}{'panta':>8}{'IQR V-VIII':>12}")
for c in sorted(tm, key=lambda c: -(c['spearman'] or -9)):
    print(f"{c['denumire'][:44]:44s}{c['n']:>5}{c['decalaj']:>9.2f}"
          f"{(c['spearman'] if c['spearman'] is not None else float('nan')):>10.3f}"
          f"{(c['panta'] if c['panta'] is not None else float('nan')):>8.3f}{c['v8_iqr']:>12.2f}")
print()
print('salvat:', os.path.normpath(OUT))
