# Școlile pe care pragul le scoate din teste — și cât cântăresc.
#
# Descoperit pe 3 august 2026, ridicând pragul testelor de la 8 la 9 candidați: dispăreau
# școli aproape numai din Timișoara, iar odată cu ele o bună parte din diferența dintre
# orașe. Nu e un detaliu de calibrare, e un rezultat: Cluj și Iași nu au deloc, în date,
# școli atât de mici.
#
# Scriptul rulează Kruskal-Wallis la pragul curent și la pragul imediat inferior, pe
# aceleași date, și numește școlile din diferență.
import io, json, math, os, sys
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from praguri import prag
from statistici import median_of, mediana_cu_neprezentati, kruskal, chi2_sf, dunn_holm

DATE = os.path.join(HERE, '..', 'date')
ORASE = ['CLUJ-NAPOCA', 'IAȘI', 'TIMIȘOARA']
YEARS = [str(y) for y in range(2020, 2026)]
PRAG = prag('prag_teste')
OUT = os.path.join(DATE, 'scoli_mici.json')

NOTE = json.load(io.open(os.path.join(DATE, 'note_en.json'), encoding='utf-8'))
reg, den = NOTE['orase'], NOTE['denumiri']


def kw_la_prag(p):
    """Kruskal-Wallis pe fiecare an, luând școlile cu cel puțin p candidați cu notă."""
    out = {}
    for an in YEARS:
        grupuri = {c: [] for c in ORASE}
        for cod, r in NOTE['ani'][an]['scoli'].items():
            oras = reg.get(cod)
            if oras is None or len(r['note']) < p:
                continue
            m = mediana_cu_neprezentati(r['note'], r['neprezentati'])
            if m is not None:
                grupuri[oras].append(m)
        glist = [grupuri[c] for c in ORASE]
        H, N, rs = kruskal(glist)
        dunn, rang = dunn_holm(ORASE, glist, rs, N)
        out[an] = {'n_scoli': {c: len(grupuri[c]) for c in ORASE},
                   'p': float(f'{chi2_sf(H, 2):.4g}'),
                   'epsilon2': round((H - 2) / (N - 3), 4),
                   'rang_mediu': {c: round(r_, 1) for c, r_ in zip(ORASE, rang)},
                   'perechi_semnificative': [d['pereche'] for d in dunn if d['p_holm'] < 0.05]}
    return out


cu = kw_la_prag(PRAG)          # pragul curent: școlile mici sunt AFARĂ
fara = kw_la_prag(PRAG - 1)    # un candidat mai jos: școlile mici sunt ÎNĂUNTRU

# școlile din diferență, pe oraș
diferenta = {c: [] for c in ORASE}
for an in YEARS:
    for cod, r in NOTE['ani'][an]['scoli'].items():
        oras = reg.get(cod)
        if oras and len(r['note']) == PRAG - 1:
            m = mediana_cu_neprezentati(r['note'], r['neprezentati'])
            diferenta[oras].append({
                'an': an, 'cod': cod, 'denumire': den[cod],
                'n_note': len(r['note']), 'neprezentati': r['neprezentati'],
                'mediana': None if m is None else round(m, 3),
                'mediana_orasului': round(median_of(
                    [x for x in (mediana_cu_neprezentati(rr['note'], rr['neprezentati'])
                                 for k, rr in NOTE['ani'][an]['scoli'].items()
                                 if reg.get(k) == oras and len(rr['note']) >= PRAG)
                     if x is not None]), 3)})

ani_sig_cu = [a for a in YEARS if cu[a]['perechi_semnificative']]
ani_sig_fara = [a for a in YEARS if fara[a]['perechi_semnificative']]
tm = diferenta['TIMIȘOARA']
scoli_tm = sorted({x['cod'] for x in tm})
nedefinite = [x for x in tm if x['mediana'] is None]

# Timișoara rămâne ultima în ambele variante? Direcția nu depinde de prag.
ultima = {min(v['rang_mediu'], key=v['rang_mediu'].get) for v in list(cu.values()) + list(fara.values())}

out = {
    'prag_curent': PRAG,
    'kw_cu_pragul': cu,
    'kw_fara_pragul': fara,
    'ani_semnificativi_cu_pragul': ani_sig_cu,
    'ani_semnificativi_fara_pragul': ani_sig_fara,
    'celule_sub_prag': {c: len(v) for c, v in diferenta.items()},
    'scoli_distincte_sub_prag': {c: len({x['cod'] for x in v}) for c, v in diferenta.items()},
    'scoli_timisoara': diferenta['TIMIȘOARA'],
    'oras_mereu_ultimul': sorted(ultima),
    'mediane_nedefinite': nedefinite,
}
json.dump(out, io.open(OUT, 'w', encoding='utf-8', newline='\n'),
          ensure_ascii=False, indent=1)

print(f'prag curent: {PRAG} candidați\n')
print(f"{'an':>5}{'cu pragul':>28}{'fără prag (>= ' + str(PRAG - 1) + ')':>30}")
for an in YEARS:
    f = lambda v: (f"ε²={v['epsilon2']:+.4f} p={v['p']:<8.4g} "
                   f"{len(v['perechi_semnificative'])} perechi")
    print(f'{an:>5}{f(cu[an]):>28}{f(fara[an]):>30}')
print()
print(f'ani semnificativi — cu pragul: {ani_sig_cu or "niciunul"}; fără: {ani_sig_fara or "niciunul"}')
print(f'celule sub prag: ' + ', '.join(f'{c} {len(v)}' for c, v in diferenta.items()))
print(f'școli distincte la Timișoara: {len(scoli_tm)}')
print(f'orașul mereu ultimul, în ambele variante: {sorted(ultima)}')
for x in nedefinite:
    print(f'mediană nedefinită: {x["denumire"]} în {x["an"]} '
          f'({x["neprezentati"]} neprezentați, {x["n_note"]} cu notă)')
print('\nsalvat:', os.path.normpath(OUT))
