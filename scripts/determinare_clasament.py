# Cât de determinat e clasamentul: pentru câte școli poziția e o poziție, și pentru câte
# e o zonă.
#
# Perechile se testează pe DIFERENȚĂ, nu pe suprapunerea intervalelor. Suprapunerea a două
# intervale de 95% e un criteriu mai sever decât testul diferenței — două intervale se pot
# suprapune iar diferența să fie totuși semnificativă. Ambele se calculează aici, ca să se
# vadă cât de mult conta alegerea criteriului.
#
#   z = |θ1 − θ2| / sqrt(se1² + se2²)   pe medianele ajustate și erorile lor posterioare
#
# Familia de comparații e mulțimea perechilor din interiorul unui an, la un oraș — de aceea
# se raportează și varianta cu Holm: cu ~30 de școli sunt ~435 de perechi, iar la 5% brut
# ar ieși vreo 20 de perechi „semnificative" din întâmplare.
import io, json, math, os, sys
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from statistici import norm_sf, holm

DATE = os.path.join(HERE, '..', 'date')
YEARS = [str(y) for y in range(2020, 2026)]
OUT = os.path.join(DATE, 'determinare_clasament.json')

shr = json.load(io.open(os.path.join(DATE, 'shrinkage_mediana.json'), encoding='utf-8'))
rez = {}
for an in YEARS:
    scoli = sorted(shr[an]['scoli'], key=lambda s: s['rang_shrink'])
    k = len(scoli)
    perechi = []
    for i in range(k):
        for j in range(i + 1, k):
            a, b = scoli[i], scoli[j]
            se = math.sqrt(a['se_shrink'] ** 2 + b['se_shrink'] ** 2)
            z = abs(a['mediana_shrink'] - b['mediana_shrink']) / se if se else 0.0
            perechi.append({'i': i, 'j': j, 'z': z, 'p_brut': 2 * norm_sf(z),
                            'suprapun': not (b['ci_low'] > a['ci_high'] or
                                             a['ci_low'] > b['ci_high'])})
    holm(perechi)

    def zone(cheie):
        """Pentru fiecare școală, câte altele nu se pot despărți de ea (ea inclusă)."""
        z = [1] * k
        for p in perechi:
            if not cheie(p):
                z[p['i']] += 1
                z[p['j']] += 1
        return z

    z_brut = zone(lambda p: p['p_brut'] < 0.05)
    z_holm = zone(lambda p: p['p_holm'] < 0.05)
    z_supr = zone(lambda p: not p['suprapun'])
    med = lambda v: sorted(v)[len(v) // 2]
    rez[an] = {
        'k': k,
        'perechi_total': len(perechi),
        'perechi_despartite_brut': sum(1 for p in perechi if p['p_brut'] < 0.05),
        'perechi_despartite_holm': sum(1 for p in perechi if p['p_holm'] < 0.05),
        'perechi_intervale_separate': sum(1 for p in perechi if not p['suprapun']),
        'pozitie_unica_brut': sum(1 for v in z_brut if v == 1),
        'pozitie_unica_holm': sum(1 for v in z_holm if v == 1),
        'pozitie_unica_suprapunere': sum(1 for v in z_supr if v == 1),
        'zona_tipica_brut': med(z_brut),
        'zona_tipica_holm': med(z_holm),
        'zona_tipica_suprapunere': med(z_supr),
        'zona_maxima_holm': max(z_holm),
    }

# Schimbarea NIVELULUI unei școli de la un an la altul. Familia de comparații e mulțimea
# școlilor comune celor doi ani. Atenție la citire: ce iese semnificativ aici include
# mișcarea comună a anului — de aceea vârful e la trecerea în anul pe care Friedman îl
# arată ca an slab în toate trei orașele, nu la școli anume.
schimbari = {}
for a, b_ in zip(YEARS, YEARS[1:]):
    da = {s['cod']: s for s in shr[a]['scoli']}
    db = {s['cod']: s for s in shr[b_]['scoli']}
    per = []
    for cod in set(da) & set(db):
        x, y = da[cod], db[cod]
        se = math.sqrt(x['se'] ** 2 + y['se'] ** 2)
        z = abs(x['mediana'] - y['mediana']) / se if se else 0.0
        per.append({'cod': cod, 'z': z, 'p_brut': 2 * norm_sf(z)})
    holm(per)
    schimbari[f'{a}->{b_}'] = {
        'scoli': len(per),
        'semnificative_brut': sum(1 for p in per if p['p_brut'] < 0.05),
        'semnificative_holm': sum(1 for p in per if p['p_holm'] < 0.05)}

json.dump({'oras': 'TIMIȘOARA', 'ani': rez, 'schimbari_an_la_an': schimbari},
          io.open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)

print()
print('Schimbarea nivelului unei școli de la un an la altul')
print(f"{'trecere':>14}{'școli':>7}{'brut':>7}{'Holm':>7}")
for k, v in schimbari.items():
    print(f"{k:>14}{v['scoli']:>7}{v['semnificative_brut']:>7}{v['semnificative_holm']:>7}")

print('Perechi despărțite, din toate perechile posibile ale anului')
print(f"{'an':>5}{'școli':>7}{'perechi':>9}{'pe diferență':>14}{'+ Holm':>10}"
      f"{'intervale separate':>20}")
for an in YEARS:
    r = rez[an]
    print(f"{an:>5}{r['k']:>7}{r['perechi_total']:>9}"
          f"{r['perechi_despartite_brut']:>9} {100 * r['perechi_despartite_brut'] / r['perechi_total']:>3.0f}%"
          f"{r['perechi_despartite_holm']:>6} {100 * r['perechi_despartite_holm'] / r['perechi_total']:>3.0f}%"
          f"{r['perechi_intervale_separate']:>15} {100 * r['perechi_intervale_separate'] / r['perechi_total']:>3.0f}%")
print()
print('Zona în care poate sta o școală (câte școli nu se pot despărți de ea)')
print(f"{'an':>5}{'poziție unică':>15}{'zonă tipică':>13}{'zonă maximă':>13}   (pe diferență, Holm)")
for an in YEARS:
    r = rez[an]
    print(f"{an:>5}{r['pozitie_unica_holm']:>15}{r['zona_tipica_holm']:>13}{r['zona_maxima_holm']:>13}")
print()
print('salvat:', os.path.normpath(OUT))
