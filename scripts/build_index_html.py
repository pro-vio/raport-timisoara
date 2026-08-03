# Construiește index.html din scripts/index_template.html.
#
# Regula: NICIO cifră scrisă de mână în pagină. Fiecare valoare — și din grafice, și din
# proză — se calculează aici, din JSON-urile din date/, la fiecare rulare.
#
# Interpolarea protejează cifra, nu afirmația. „2020 e cel mai mare peste tot" poate avea
# cifra corectă și fi falsă. De aceea build-ul rulează la final verifica_text.py, care
# testează afirmațiile, și NU scrie pagina dacă o aserțiune pică.
import io, json, os, re, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
DATE = os.path.join(HERE, '..', 'date')
SABLON = os.path.join(HERE, 'index_template.html')
OUT = os.path.join(HERE, '..', 'index.html')
YEARS = [str(y) for y in range(2020, 2026)]
ORASE = {'CLUJ-NAPOCA': 'Cluj', 'IAȘI': 'Iași', 'TIMIȘOARA': 'Timișoara'}

J = lambda n: json.load(io.open(os.path.join(DATE, n), encoding='utf-8'))
fr = J('friedman_mediane.json')
kw = J('kw_pe_ani.json')
shr = J('shrinkage_mediana.json')
raw = J('candidati_raw_timisoara.json')
mv = J('medie_vs_mediana_percentil.json')


def d(x, n=2):
    """Zecimale cu virgulă — separatorul zecimal în română."""
    return f'{x:.{n}f}'.replace('.', ',')


def enumera(xs, si='și'):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else f"{', '.join(xs[:-1])} {si} {xs[-1]}"


def zecimale(x, minim=2):
    """Cât de multe zecimale cere valoarea ca să fie exactă, dar nu mai puțin de `minim`."""
    for n in range(minim, 7):
        if abs(round(x, n) - x) < 1e-12:
            return d(x, n)
    return d(x, 6)


def constanta(fisier, nume):
    """Citește o constantă din scriptul care o aplică, ca să nu fie scrisă de mână aici."""
    src = io.open(os.path.join(HERE, fisier), encoding='utf-8').read()
    m = re.search(rf'^{nume}\s*=\s*(\d+)', src, re.M)
    assert m, f'{nume} negăsit în {fisier}'
    return int(m.group(1))


MIN_N = constanta('extract_candidati_raw.py', 'MIN_N')
N_BOOT = constanta('shrinkage_mediana.py', 'B')

# --- numele scurte de școli: EDITORIAL, pentru lizibilitatea graficului. Singura parte a
# blocurilor de date care nu vine din fișiere; de aceea stă aici, la vedere. ---
NUME_SCURT = {c: raw['names'][c] for c in raw['order']}
_S = json.loads(io.open(os.path.join(HERE, 'nume_scurte.json'), encoding='utf-8').read()) \
    if os.path.exists(os.path.join(HERE, 'nume_scurte.json')) else {}
NUME_SCURT.update(_S)

# ---------------------------------------------------------------- blocuri de date (JS)
med_pe_an = {an: {r['cod']: r for r in shr[an]['scoli']} for an in YEARS}
# Ordinea liniilor din graficul „Evoluția medianelor": rangul din primul an, apoi școlile
# care lipsesc din el. Nu are efect asupra citirii — doar asupra ordinii de desenare.
_r0 = {c: r['rang_shrink'] for c, r in med_pe_an[YEARS[0]].items()}
ORDINE = sorted(raw['order'], key=lambda c: (c not in _r0, _r0.get(c, 10 ** 6)))
SCHOOLS = []
for cod in ORDINE:
    ani = {an: {'rank': med_pe_an[an][cod]['rang_shrink'], 'med': med_pe_an[an][cod]['mediana']}
           for an in YEARS if cod in med_pe_an[an]}
    SCHOOLS.append({'cod': cod, 'nume': NUME_SCURT[cod], 'ani': ani})

SHRINK_DATA = {an: {'mu': shr[an]['mu_hat'],
                    'scoli': [{'c': r['cod'], 'n': r['denumire'], 'nn': r['n'],
                               'raw': r['mediana'], 'sh': r['mediana_shrink'],
                               'lo': r['ci_low'], 'hi': r['ci_high'],
                               'w': r['w_shrink'], 'r': r['rang_shrink']}
                              for r in sorted(shr[an]['scoli'], key=lambda r: r['rang_shrink'])]}
               for an in YEARS}

MU_HAT = {an: shr[an]['mu_hat'] for an in YEARS}
GAP_ANI = [int(a) for a in YEARS]
GAP_MEDIU = [mv['per_an'][a]['gap_mediu'] for a in YEARS]
GAP_MEDIAN = [mv['per_an'][a]['gap_median'] for a in YEARS]
SERII = {c: [fr[c]['rang_mediu'][a] for a in YEARS] for c in ORASE}

# ------------------------------------------------------------------- cifrele din proză
W = {c: fr[c]['kendall_W'] for c in ORASE}
RM = {c: fr[c]['rang_mediu'] for c in ORASE}

# cei doi ani cu rangul cel mai mic — ceruți să fie aceiași în toate trei orașele
jos_pe_oras = [set(sorted(RM[c], key=lambda a: RM[c][a])[:2]) for c in ORASE]
assert jos_pe_oras[0] == jos_pe_oras[1] == jos_pe_oras[2], \
    f'anii de jos diferă între orașe: {jos_pe_oras}'
ANI_JOS = sorted(jos_pe_oras[0])
val_jos = [RM[c][a] for c in ORASE for a in ANI_JOS]

TOP = {c: max(RM[c], key=RM[c].get) for c in ORASE}
assert TOP['CLUJ-NAPOCA'] == TOP['TIMIȘOARA'], 'Cluj și Timișoara nu mai au același an de vârf'
AN_TOP_CJTM, AN_TOP_IS = TOP['CLUJ-NAPOCA'], TOP['IAȘI']
# vecinii anului de vârf al Iașului, în clasamentul Clujului
cj = RM['CLUJ-NAPOCA']
vecini = sorted((a for a in YEARS if a != AN_TOP_IS),
                key=lambda a: abs(cj[a] - cj[AN_TOP_IS]))[:2]

# exemplul didactic: perechea de ani cu cea mai mică diferență de mediană
ex = fr['_exemplu']
assert 'TAKE IONESCU' in ex['denumire'].upper(), f"exemplul s-a schimbat: {ex['denumire']}"
perechi = [(abs(ex['mediane'][a] - ex['mediane'][b]), a, b)
           for i, a in enumerate(YEARS) for b in YEARS[i + 1:]]
dif_min, EX_A, EX_B = min(perechi)

n_sc_fr = [fr[c]['n_scoli'] for c in ORASE]
n_sc_shr = [shr[an]['n_scoli'] for an in YEARS]

# Kruskal-Wallis
eps = {a: kw['ani'][a]['epsilon2'] for a in YEARS}
AN_EPS_MIN = min(eps, key=eps.get)
sig = {a: [x['pereche'] for x in kw['ani'][a]['dunn_holm'] if x['p_holm'] < 0.05] for a in YEARS}
perechi_sig = {p for ps in sig.values() for p in ps}
assert len(perechi_sig) == 1, f'nu mai e un singur contrast semnificativ: {perechi_sig}'
PERECHE = '&ndash;'.join(ORASE[x.strip()] for x in list(perechi_sig)[0].split(' vs '))
ANI_SIG = [a for a in YEARS if sig[a]]
ANI_NESIG = [a for a in YEARS if not sig[a]]
# anul de graniță: omnibus peste prag, dar o pereche sub prag
granita = [a for a in YEARS if kw['ani'][a]['p'] >= 0.05 and sig[a]]
assert len(granita) == 1, f'cazuri de graniță: {granita}'
AN_GR = granita[0]
P_DUNN_GR = [x['p_holm'] for x in kw['ani'][AN_GR]['dunn_holm'] if x['p_holm'] < 0.05][0]

prim = {a: max(kw['ani'][a]['rang_mediu'], key=kw['ani'][a]['rang_mediu'].get) for a in YEARS}
ani_cj = [a for a in YEARS if prim[a] == 'CLUJ-NAPOCA']
ani_is = [a for a in YEARS if prim[a] == 'IAȘI']
ultim = {min(kw['ani'][a]['rang_mediu'], key=kw['ani'][a]['rang_mediu'].get) for a in YEARS}
assert ultim == {'TIMIȘOARA'}, f'Timișoara nu mai e ultima în toți anii: {ultim}'

JETOANE = {
    'JS_SCHOOLS': json.dumps(SCHOOLS, ensure_ascii=False),
    'JS_SHRINK_DATA': json.dumps(SHRINK_DATA, ensure_ascii=False),
    'JS_CANDIDATI_RAW': json.dumps(raw, ensure_ascii=False),
    'JS_MU_HAT': json.dumps(MU_HAT, ensure_ascii=False),
    'JS_YEARS': json.dumps(YEARS, ensure_ascii=False),
    'JS_SHRINK_YEARS': json.dumps(YEARS, ensure_ascii=False),
    'JS_GAP_YEARS': json.dumps(GAP_ANI),
    'JS_GAP_MEDIU': json.dumps(GAP_MEDIU),
    'JS_GAP_MEDIAN': json.dumps(GAP_MEDIAN),
    'JS_FR_IS': json.dumps(SERII['IAȘI']),
    'JS_FR_CJ': json.dumps(SERII['CLUJ-NAPOCA']),
    'JS_FR_TM': json.dumps(SERII['TIMIȘOARA']),

    'EX_NUME': 'Școala Gimnazială nr. 16 „Take Ionescu" din Timișoara',
    'EX_SCURT': '„Take Ionescu"',
    'EX_MEDIANE': enumera(f"{zecimale(ex['mediane'][a])} ({a})" for a in YEARS),
    'EX_POZITII': ', '.join(str(int(ex['ranguri'][a])) for a in YEARS),
    'EX_AN_A': EX_A, 'EX_AN_B': EX_B, 'EX_DIF': d(dif_min, 3),

    'W_IS': d(W['IAȘI']), 'W_TM': d(W['TIMIȘOARA']), 'W_CJ': d(W['CLUJ-NAPOCA']),
    'FR_ANI_JOS': enumera(ANI_JOS),
    'FR_JOS_MIN': d(min(val_jos), 1), 'FR_JOS_MAX': d(max(val_jos), 1),
    'FR_AN_TOP_CJTM': AN_TOP_CJTM, 'FR_AN_TOP_IS': AN_TOP_IS,
    'FR_TOP_CJ': d(RM['CLUJ-NAPOCA'][AN_TOP_CJTM], 1),
    'FR_TOP_TM': d(RM['TIMIȘOARA'][AN_TOP_CJTM], 1),
    'FR_TOP_IS': d(RM['IAȘI'][AN_TOP_IS], 1),
    'FR_TM_LA_TOPIS': d(RM['TIMIȘOARA'][AN_TOP_IS], 1),
    'FR_CJ_LA_TOPIS': d(RM['CLUJ-NAPOCA'][AN_TOP_IS], 1),
    'FR_CJ_VECINI': enumera(sorted(vecini)),
    'FR_N_SCOLI': f'{min(n_sc_fr)}-{max(n_sc_fr)}',

    'KW_CJ_PRIM': f'{ani_cj[0]} și {ani_cj[-1]}' if len(ani_cj) > 2 else enumera(ani_cj),
    'KW_IS_PRIM': enumera(ani_is),
    'KW_EPS_MIN': d(min(eps.values()), 2), 'KW_EPS_MAX': d(max(eps.values()), 2),
    'KW_AN_EPS_MIN': AN_EPS_MIN, 'KW_EPS_MIN_EXACT': d(eps[AN_EPS_MIN], 3),
    'KW_PERECHE': PERECHE, 'KW_ANI_SIG': enumera(ANI_SIG), 'KW_ANI_NESIG': enumera(ANI_NESIG),
    'KW_AN_GRANITA': AN_GR, 'KW_P_GRANITA': d(kw['ani'][AN_GR]['p'], 3),
    'KW_PDUNN_GRANITA': d(P_DUNN_GR, 3),

    'R_DIF': '&minus;' + d(abs(mv['corelatie_medie_vs_gap'])),
    'N_BOOT': str(N_BOOT), 'MIN_N': str(MIN_N),
    'N_SCOLI_GRAFIC': str(len(SCHOOLS)),
    'N_SCOLI_ANCORA': f'{min(n_sc_shr)}-{max(n_sc_shr)}',
}

s = io.open(SABLON, encoding='utf-8').read()
lipsa = sorted(set(re.findall(r'\{\{(\w+)\}\}', s)) - set(JETOANE))
assert not lipsa, f'jetoane fără valoare: {lipsa}'
nefolosite = sorted(set(JETOANE) - set(re.findall(r'\{\{(\w+)\}\}', s)))
assert not nefolosite, f'valori calculate degeaba: {nefolosite}'
for k, v in JETOANE.items():
    s = s.replace('{{' + k + '}}', v)

io.open(OUT, 'w', encoding='utf-8', newline='\n').write(s)
print(f'scris {os.path.normpath(OUT)}  ({len(s):,} caractere)'.replace(',', ' '))

# Afirmațiile, nu doar cifrele. Dacă una pică, build-ul cade și pagina rămâne de refăcut.
print()
r = subprocess.run([sys.executable, os.path.join(HERE, 'verifica_text.py')])
if r.returncode:
    print('\nBUILD CĂZUT: o afirmație din text nu mai e susținută de date.')
sys.exit(r.returncode)
