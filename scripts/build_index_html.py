# Construiește index.html din scripts/index_template.html.
#
# Regula: NICIO cifră scrisă de mână în pagină. Fiecare valoare — și din grafice, și din
# proză — se calculează aici, din JSON-urile din date/, la fiecare rulare.
#
# Interpolarea protejează cifra, nu afirmația. „2020 e cel mai mare peste tot" poate avea
# cifra corectă și fi falsă. De aceea build-ul rulează la final verifica_text.py, care
# testează afirmațiile, și NU scrie pagina dacă o aserțiune pică.
import io, json, os, re, subprocess, sys
NL = chr(10)
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from praguri import criteriu, prag

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
npz = J('neprezentati.json')
rng_ = J('ranguri_bootstrap.json')
det = J('determinare_clasament.json')
sm = J('scoli_mici.json')
rc = J('restrictie_clasament.json')
pr = J('predictie_scoala.json')


def d(x, n=2):
    """Zecimale cu virgulă — separatorul zecimal în română."""
    return f'{x:.{n}f}'.replace('.', ',')


def enumera(xs, si='și'):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else f"{', '.join(xs[:-1])} {si} {xs[-1]}"


_CUVINTE_F = {1: 'O', 2: 'Două', 3: 'Trei', 4: 'Patru', 5: 'Cinci', 6: 'Șase',
              7: 'Șapte', 8: 'Opt', 9: 'Nouă', 10: 'Zece'}


def cuvant_f(n):
    """Numeralul în litere, feminin, pentru titluri. Peste zece rămâne cifra."""
    return _CUVINTE_F.get(n, str(n))


_MICI = {'De', 'Din', 'Cu', 'La', 'Și', 'Pentru', 'Al', 'A', 'Pe'}


def titlu_ro(s):
    """Majuscule inițiale, dar prepozițiile rămân mici: „Liceul de Arte Plastice"."""
    return ' '.join(w.lower() if i and w in _MICI else w
                    for i, w in enumerate(s.title().split()))


def numar(n, substantiv):
    """Numeralul cu „de" acolo unde româna îl cere: 9 situații, dar 21 de situații."""
    return f'{n} de {substantiv}' if n % 100 == 0 or n % 100 > 19 else f'{n} {substantiv}'


def semn(x, n=2):
    """Cifră cu semn tipografic corect: minusul e &minus;, nu cratimă."""
    return ('&minus;' if x < 0 else '') + d(abs(x), n)


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


MIN_N = prag('prag_grafice')
MIN_N_TESTE = prag('prag_teste')
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


# ------------------------------------------------- tabul cu decalajul școală-examen
AN_DEC = YEARS[-1]
_CUL = {'IAȘI': ('#2a78d6', '#3987e5'), 'CLUJ-NAPOCA': ('#1baf7a', '#199e70'),
        'TIMIȘOARA': ('#eda100', '#c98500')}
_ID = {'IAȘI': 'is', 'CLUJ-NAPOCA': 'cj', 'TIMIȘOARA': 'tm'}
# Limitele se calculează peste TOȚI anii, ca norul să nu sară când se schimbă anul.
_val = [v for c in pr['celule'] for v in (c['v8_mediana'], c['en_mediana'])]
_LIM = [round(min(_val) - 0.3, 1), round(max(_val) + 0.2, 1)]


def _oglinda(oras):
    """Cât de mult e tiparul anilor la decalaj oglinda celui de la examen."""
    a = [fr[oras]['rang_mediu'][y] for y in YEARS]
    b = [pr['friedman_delta'][oras]['rang_mediu'][y] for y in YEARS]
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    sa = (sum((x - ma) ** 2 for x in a) / n) ** .5
    sb = (sum((x - mb) ** 2 for x in b) / n) ** .5
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (n * sa * sb)


# Timișoara prima: raportul e despre ea, celelalte două stau ca termen de comparație.
_ORD_DEC = ['TIMIȘOARA', 'CLUJ-NAPOCA', 'IAȘI']
_orase_js, _carduri = [], []
for oras in _ORD_DEC:
    ro = ORASE[oras]
    ani = {}
    for an in YEARS:
        pts = [c for c in pr['celule'] if c['oras'] == oras and c['an'] == an]
        st = pr['intre_scoli'][oras][an]
        assert st['toate_sub_diagonala'], f'{oras} {an}: nu mai stau toate școlile sub linie'
        ani[an] = {'puncte': [[c['v8_mediana'], c['en_mediana'], c['denumire']] for c in pts],
                   'n_scoli': st['n_scoli'], 'pearson': st['pearson'],
                   'decalaj_median': st['decalaj_median'],
                   'decalaj_min': st['decalaj_min'], 'decalaj_max': st['decalaj_max']}
    _orase_js.append({'id': _ID[oras], 'nume': ro, 'culoare': _CUL[oras][0],
                      'culoare_dark': _CUL[oras][1], 'ani': ani})
    _carduri.append(f"""    <div class="card">
      <h2>{ro}</h2>
      <p class="note">Fiecare punct e o școală. Pe orizontală mediana notelor pe care le dă școala în clasele V&ndash;VIII, pe verticală mediana notelor pe care le iau aceiași elevi la examen.</p>
      <div class="modenav" id="ani-{_ID[oras]}" role="group" aria-label="Anul"></div>
      <div class="duo">
        <div class="plot"><canvas id="scatter-{_ID[oras]}" role="img" aria-label="Nor de puncte, {ro}: fiecare punct e o școală, notele date de școală față de notele de la examen. Toate punctele stau sub linia notei egale."></canvas></div>
        <div class="say" id="say-{_ID[oras]}"></div>
      </div>
    </div>""")

# tabelul cu coeficienții de corelație, ani × orașe
_rand = []
for an in YEARS:
    celule_ = ''.join(
        f"<td>{d(pr['intre_scoli'][o][an]['pearson'])}</td>" for o in _ORD_DEC)
    _rand.append(f'          <tr><td class="school">{an}</td>{celule_}</tr>')
_TABEL_DEC = NL.join([
    '    <div class="card">',
    '      <h2>Corelația dintre notele de la clasă și cele de la examen</h2>',
    '      <p class="note">Calculată între școli, în fiecare an: cât de bine anticipează'
    ' mediana notelor date de o școală mediana notelor pe care le iau elevii ei la examen.'
    ' Valoarea 1 ar însemna că ordinea școlilor e aceeași după ambele.</p>',
    '      <div class="table-scroll">',
    '        <table>',
    '          <thead><tr><th>An</th>'
    + ''.join(f'<th>{ORASE[o]}</th>' for o in _ORD_DEC) + '</tr></thead>',
    '          <tbody>',
] + _rand + [
    '          </tbody>',
    '        </table>',
    '      </div>',
    '    </div>',
])

# --- decalajul pe școlile Timișoarei: mediana și împrăștierea, plus elevii fiecărei școli
NOTE_TM = J('note_en.json')
_DTM = {}
for an in YEARS:
    scoli = []
    for cod, r in NOTE_TM['ani'][an]['scoli'].items():
        if NOTE_TM['orase'].get(cod) != 'TIMIȘOARA':
            continue
        per = r.get('v8_en') or []
        if len(per) < MIN_N:
            continue
        dif = sorted(a - b for a, b in per)
        n = len(dif)
        med = dif[n // 2] if n % 2 else (dif[n // 2 - 1] + dif[n // 2]) / 2
        scoli.append({'cod': cod, 'nume': NUME_SCURT.get(cod, NOTE_TM['denumiri'][cod]),
                      'n': n, 'med': round(med, 3),
                      'q1': round(dif[n // 4], 3), 'q3': round(dif[(3 * n) // 4], 3),
                      'elevi': [[a, b] for a, b in per]})
    # cel mai mic decalaj sus: școala a cărei notă anticipă cel mai bine examenul
    scoli.sort(key=lambda x: x['med'])
    _DTM[an] = scoli
assert all(_DTM[a] for a in YEARS), 'nu mai există școli peste prag la Timișoara'


# elevii care iau la examen peste media de la clasă
_dep = pr['depasiri']
_dtm = _dep['TIMIȘOARA']
assert _dtm['celule_cu_mediana_negativa'] == 0, 'există acum școli cu mediana decalajului negativă'
_q1n = [x for x in _dtm['primele'] if x['q1'] < 0]
_top = _dtm['primele'][:4]
# afirmația din text: excepțiile se strâng la școlile de sus
assert _top[0]['pondere'] > 3 * _dtm['pondere'], 'excepțiile nu se mai strâng nicăieri'
_DEP_TOP = ' '.join(
    f"La {titlu_ro(NUME_SCURT.get(x['cod'], x['denumire']))}, în {x['an']}, "
    f"{x['peste']} din {x['n']} de elevi ({d(100 * x['pondere'], 0)}%)."
    for x in _top[:3])
_cel_q1 = [c for c in pr['celule']
           if c['oras'] == 'TIMIȘOARA' and any(y['cod'] == c['cod'] and y['an'] == c['an']
                                               for y in _q1n)]


# extremele și mijlocul listei, pentru caseta „Cum se citește"
_prz = _DTM[AN_DEC]
_prz_med = _prz[len(_prz) // 2]
assert _prz[0]['med'] < _prz[-1]['med'], 'lista nu mai e ordonată crescător după decalaj'

_tm = pr['intre_scoli']['TIMIȘOARA'][AN_DEC]
_tmk = pr['kw_delta']['TIMIȘOARA']['la_gramada']
_tmf = pr['friedman_delta']['TIMIȘOARA']
_ogl = _oglinda('TIMIȘOARA')
assert _ogl < -0.7, f'tiparul decalajului nu mai e oglinda celui de la examen ({_ogl:.2f})'
assert _tmk['epsilon2'] > max(v['epsilon2'] for v in kw['ani'].values()),     'școlile nu mai diferă între ele mai mult decât orașele'
# afirmația din text: Timișoara are corelația cea mai mică dintre cele trei orașe
_cor_dec = {o: [pr['intre_scoli'][o][a]['pearson'] for a in YEARS] for o in _ORD_DEC}
# afirmația din text: Timișoara are corelația cea mai mică în FIECARE an
for _i, _a in enumerate(YEARS):
    assert _cor_dec['TIMIȘOARA'][_i] < min(_cor_dec['CLUJ-NAPOCA'][_i], _cor_dec['IAȘI'][_i]),         f'{_a}: Timișoara nu mai are corelația cea mai mică'
assert _cor_dec['TIMIȘOARA'][-1] < _cor_dec['TIMIȘOARA'][0], 'corelația la Timișoara nu mai scade'
_cor_an = {o: pr['intre_scoli'][o][AN_DEC]['pearson'] for o in _ORD_DEC}
assert min(_cor_an, key=_cor_an.get) == 'TIMIȘOARA', f'nu mai e Timișoara cea mai mică: {_cor_an}'

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

# intervalele de rang și săgețile pe care le-au înlocuit
_lat_an = {an: sorted(v['latime'] for v in sc.values()) for an, sc in rng_['ani'].items()}
_lat_tip = [l[len(l) // 2] for l in _lat_an.values()]
_sag_tot = sum(v['sageti_afisate'] for v in rng_['sageti'].values())
_sag_sus = sum(v['sustinute'] for v in rng_['sageti'].values())
assert _sag_sus * 10 < _sag_tot, \
    f'săgețile au devenit susținute ({_sag_sus}/{_sag_tot}) — fraza din text nu mai ține'
_NUME_SAG = {0: 'niciuna nu se susține', 1: 'una singură se susține'}
FRAZA_SAG = _NUME_SAG.get(_sag_sus, f'{_sag_sus} se susțin')

# restrângerea clasamentului la școli tot mai mari nu-l face determinat
_rc = rc['pe_prag']
_rc_lat = [v['latime_tipica'] for v in _rc.values()]
_rc_pct = [v['latime_pct_din_camp'] for v in _rc.values()]
_rc_ies = [v['miscari_sustinute_pct'] for v in _rc.values() if v['miscari_sustinute_pct'] is not None]
assert max(_rc_ies) < 15, f'restrângerea începe să determine clasamentul ({max(_rc_ies)}%)'
assert max(_rc_pct) - min(_rc_pct) < 20, \
    f'incertitudinea raportată la câmp nu mai e stabilă ({min(_rc_pct)}-{max(_rc_pct)}%)'

# mărimea școlilor, înainte și după tăietură
_ms_i = sm['marimea_scolilor']['inainte']
_ms_d = sm['marimea_scolilor']['dupa']
# afirmația din text: tăietura abia apropie distribuțiile, deci cele cinci sunt o coadă,
# nu vârful unei diferențe de mărime
_dks = _ms_i['ks']['CLUJ-NAPOCA vs TIMIȘOARA'] - _ms_d['ks']['CLUJ-NAPOCA vs TIMIȘOARA']
assert 0 <= _dks < 0.05, f'tăietura mută acum mult distribuțiile de mărime ({_dks:.3f})'

# școlile pe care pragul testelor le scoate — toate dintr-un singur oraș
_sm_cel = sm['celule_sub_prag']
assert all(v == 0 for c, v in _sm_cel.items() if c != 'TIMIȘOARA'), \
    f'nu mai sunt toate la Timișoara: {_sm_cel}'
assert sm['oras_mereu_ultimul'] == ['TIMIȘOARA'], \
    f'direcția depinde acum de prag: {sm["oras_mereu_ultimul"]}'
assert len(sm['mediane_nedefinite']) >= 1, 'nu mai există mediana nedefinită din text'
_nd = sm['mediane_nedefinite'][0]
# denumirea din registru e cu majuscule și lipită („ȘCOALA GIMNAZIALĂ NR.15 TIMIȘOARA")
_SM_NEDEF = re.sub(r'\bNr\.\s*(\d)', r'nr. \1', titlu_ro(_nd['denumire'])) + f" în {_nd['an']}"

# schimbările de nivel de la un an la altul, și unde se strâng
_sch = det['schimbari_an_la_an']
_sch_t = sum(v['scoli'] for v in _sch.values())
_sch_b = sum(v['semnificative_brut'] for v in _sch.values())
_sch_h = sum(v['semnificative_holm'] for v in _sch.values())
_varf = max(_sch, key=lambda k: _sch[k]['semnificative_brut'])
_sch_varf = _varf.replace('->', '&rarr;')
# afirmația din text: vârful cade pe anul pe care Friedman îl arată jos în toate orașele
assert _varf.split('->')[1] in ANI_JOS, \
    f'vârful schimbărilor ({_varf}) nu mai cade pe un an slab la Friedman ({ANI_JOS})'

# cât de determinat e clasamentul: primul loc, și câte școli se despart de cea din mijloc
_dist, _k = [], []
for an, sc in rng_['ani'].items():
    v = sorted(sc.values(), key=lambda x: x['rang_publicat'])
    mij = v[len(v) // 2]
    _dist.append(sum(1 for x in v
                     if x['rang_hi'] < mij['rang_lo'] or x['rang_lo'] > mij['rang_hi']))
    _k.append(len(v))
    assert round(v[0]['rang_lo']) == round(v[0]['rang_hi']) == 1, \
        f'{an}: primul loc nu mai e neambiguu ({v[0]["rang_lo"]}-{v[0]["rang_hi"]})'
    # Afirmația despre coadă se raportează la treimea de jos, nu la școala din mijloc:
    # aceea e o școală anume, iar în 2021 chiar ea are un interval de 10-26, aproape cât
    # tot clasamentul, deci nimic nu se desparte de ea. Treimea nu depinde de o școală.
    assert v[-1]['rang_lo'] > 2 * len(v) / 3, \
        f'{an}: ultima școală nu mai stă în treimea de jos ({v[-1]["rang_lo"]} din {len(v)})'

# neprezentații
_pond = [v for o in npz['pondere_neprezentati_pct'].values() for v in o.values()]
_cor = npz['corelatie_nivel_vs_pondere']['TOATE']
# afirmația din text: niciun oraș nu stă constant deasupra celorlalte
_top_pond = {max(npz['pondere_neprezentati_pct'], key=lambda o: npz['pondere_neprezentati_pct'][o][a])
             for a in YEARS}
assert len(_top_pond) > 1, f'un singur oraș are mereu cea mai mare pondere: {_top_pond}'
assert _cor['mediana_en'] < 0 and _cor['media_en'] < 0 and _cor['mediana_viii'] < 0, \
    f'corelațiile nu mai sunt toate negative: {_cor}'

# Kruskal-Wallis
eps = {a: kw['ani'][a]['epsilon2'] for a in YEARS}
AN_EPS_MIN = min(eps, key=eps.get)
sig = {a: [x['pereche'] for x in kw['ani'][a]['dunn_holm'] if x['p_holm'] < 0.05] for a in YEARS}
perechi_sig = {p for ps in sig.values() for p in ps}
assert len(perechi_sig) == 1, f'nu mai e un singur contrast semnificativ: {perechi_sig}'
PERECHE = '&ndash;'.join(ORASE[x.strip()] for x in list(perechi_sig)[0].split(' vs '))
ANI_SIG = [a for a in YEARS if sig[a]]
ANI_NESIG = [a for a in YEARS if not sig[a]]
# Anii de graniță: omnibusul nu respinge, dar o pereche iese sub prag. Fraza apare doar
# dacă fenomenul există — a existat pe 3 august, a dispărut după includerea neprezentaților.
granita = [a for a in YEARS if kw['ani'][a]['p'] >= 0.05 and sig[a]]
FRAZA_GRANITA = ''
for a in granita:
    pd_ = [x['p_holm'] for x in kw['ani'][a]['dunn_holm'] if x['p_holm'] < 0.05][0]
    FRAZA_GRANITA += (f" În {a} testul pe ansamblu dă p={d(kw['ani'][a]['p'], 3)}, iar "
                      f"post-hoc-ul pentru {{PERECHE}} p={d(pd_, 3)}: perechea iese sub un "
                      f"test de ansamblu care nu respinge.")

# ε² poate ieși negativ când grupurile nu se separă deloc: H scade sub k−1. Se raportează
# ca atare, cu citirea lui (decizia userului, 3 august 2026: „ambele").
ani_neg = [a for a in YEARS if eps[a] < 0]
FRAZA_EPS_NEG = ''
if ani_neg:
    val = ', '.join(f'{d(eps[a], 3)} în {a}' for a in ani_neg)
    FRAZA_EPS_NEG = (f' Valoarea iese negativă ({val}) &mdash; formula coboară sub zero când '
                     f'orașele nu se separă deloc, deci acolo efectul e nul.')

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
    'KW_EPS_MIN': d(min(eps.values()), 3), 'KW_EPS_MAX': d(max(eps.values()), 3),
    'KW_PERECHE': PERECHE, 'KW_ANI_SIG': enumera(ANI_SIG), 'KW_ANI_NESIG': enumera(ANI_NESIG),
    'KW_FRAZA_GRANITA': FRAZA_GRANITA.replace('{PERECHE}', PERECHE),
    'KW_FRAZA_EPS_NEG': FRAZA_EPS_NEG,

    'JS_RANGURI': json.dumps(rng_['ani'], ensure_ascii=False),
    'JS_DECALAJ_TM': json.dumps(_DTM, ensure_ascii=False),
    'JS_DECALAJ': json.dumps({'limite': _LIM, 'orase': _orase_js}, ensure_ascii=False),
    'CARDURI_DECALAJ': (NL + NL).join(_carduri),
    'TABEL_DECALAJ': _TABEL_DEC,
    'DEC_COR_TM_MIN': d(min(_cor_dec['TIMIȘOARA'])), 'DEC_COR_TM_MAX': d(max(_cor_dec['TIMIȘOARA'])),
    'DEC_COR_CJ_MIN': d(min(_cor_dec['CLUJ-NAPOCA'])), 'DEC_COR_CJ_MAX': d(max(_cor_dec['CLUJ-NAPOCA'])),
    'DEC_COR_IS_MIN': d(min(_cor_dec['IAȘI'])), 'DEC_COR_IS_MAX': d(max(_cor_dec['IAȘI'])),
    'DEC_COR_TM_PRIM': d(_cor_dec['TIMIȘOARA'][0]), 'DEC_COR_TM_ULT': d(_cor_dec['TIMIȘOARA'][-1]),
    'AN_PRIM': YEARS[0],
    'DEC_TM_ELEVI': f"{_tmk['n_elevi']:,}".replace(',', '.'),
    'DEC_TM_SPEARMAN': d(pr['pe_oras']['TIMIȘOARA']['spearman'], 3),
    'DEC_TM_EPS': d(_tmk['epsilon2'], 2),
    'DEC_TM_MIN': d(_tmk['delta_median_min']['delta']),
    'DEC_TM_MAX': d(_tmk['delta_median_max']['delta']),
    'DEC_TM_SCOLI_FR': str(_tmf['n_scoli']),
    'DEC_TM_W': d(_tmf['kendall_W'], 2),
    'DEC_TM_OGLINDA': semn(_ogl, 2),
    'TH_ANI': '\n            '.join(f'<th>{a}</th>' for a in YEARS),
    'AN_ULTIM': YEARS[-1],
    'RANG_LAT_MIN': str(int(min(_lat_tip))), 'RANG_LAT_MAX': str(int(max(_lat_tip))),
    'RANG_LAT_MAXIM': str(int(max(l[-1] for l in _lat_an.values()))),
    'SAGETI_TOTAL': str(_sag_tot), 'SAGETI_SUSTINUTE': FRAZA_SAG,
    'RANG_DIST_MIN': str(min(_dist)), 'RANG_DIST_MAX': str(max(_dist)),
    'RANG_K': str(round(sum(_k) / len(_k))),
    'PRZ_PRIMA': titlu_ro(_prz[0]['nume']), 'PRZ_PRIMA_VAL': d(_prz[0]['med']),
    'PRZ_ULTIMA': titlu_ro(_prz[-1]['nume']), 'PRZ_ULTIMA_VAL': d(_prz[-1]['med']),
    'PRZ_MEDIANA': d(_prz_med['med']),
    'DEP_TM_N': str(_dtm['elevi_peste']),
    'DEP_TM_TOT': f"{_dtm['elevi']:,}".replace(',', '.'),
    'DEP_TM_PCT': d(100 * _dtm['pondere'], 1) + '%',
    'DEP_CJ_PCT': d(100 * _dep['CLUJ-NAPOCA']['pondere'], 1) + '%',
    'DEP_IS_PCT': d(100 * _dep['IAȘI']['pondere'], 1) + '%',
    'DEP_TM_CELULE': str(_dtm['celule']),
    'DEP_TM_Q1NEG': (titlu_ro(NUME_SCURT.get(_q1n[0]['cod'], _q1n[0]['denumire']))
                     + f", în {_q1n[0]['an']}") if _q1n else 'niciuna',
    'DEP_TM_TOP': _DEP_TOP,
    'SM_SITUATII': numar(_sm_cel['TIMIȘOARA'], 'situații'),
    'SM_SCOLI_CUVANT': cuvant_f(sm['scoli_distincte_sub_prag']['TIMIȘOARA']),
    'SM_SCOLI': str(sm['scoli_distincte_sub_prag']['TIMIȘOARA']),
    'SM_ANI_CU': enumera(sm['ani_semnificativi_cu_pragul']),
    'SM_ANI_FARA': enumera(sm['ani_semnificativi_fara_pragul']),
    'SM_NEDEF': _SM_NEDEF,
    'RC_PRAG_MAX': str(max(rc['praguri_testate'])),
    'RC_LAT_MAX': numar(round(max(_rc_lat)), 'locuri'),
    'RC_LAT_MIN': numar(round(min(_rc_lat)), 'locuri'),
    'RC_PCT_MIN': str(round(min(_rc_pct))), 'RC_PCT_MAX': str(round(max(_rc_pct))),
    'RC_IES_MIN': str(round(min(_rc_ies))), 'RC_IES_MAX': str(round(max(_rc_ies))),

    'MS_KS_INAINTE': d(_ms_i['ks']['CLUJ-NAPOCA vs TIMIȘOARA'], 3),
    'MS_KS_DUPA': d(_ms_d['ks']['CLUJ-NAPOCA vs TIMIȘOARA'], 3),
    'MS_IS': str(round(_ms_d['marime_mediana']['IAȘI'])),
    'MS_CJ': str(round(_ms_d['marime_mediana']['CLUJ-NAPOCA'])),
    'MS_TM': str(round(_ms_d['marime_mediana']['TIMIȘOARA'])),

    'SM_N_CU': str(len(sm['ani_semnificativi_cu_pragul'])),
    'SM_N_FARA': str(len(sm['ani_semnificativi_fara_pragul'])),
    'MIN_N_TESTE_VECHI': str(sm['prag_curent'] - 1),

    'SCHIMB_TOTAL': str(_sch_t), 'SCHIMB_BRUT': str(_sch_b), 'SCHIMB_HOLM': str(_sch_h),
    'SCHIMB_AN_VARF': _sch_varf,

    'NEPZ_MIN': d(min(_pond), 1) + '%', 'NEPZ_MAX': d(max(_pond), 1) + '%',
    'NEPZ_MISCARE': zecimale(max(abs(v) for o in npz['miscarea_medianei_orasului'].values()
                                 for v in o.values())),
    'NEPZ_COR_MEDIANA': semn(_cor['mediana_en']),
    'NEPZ_COR_MEDIE': semn(_cor['media_en']),
    'NEPZ_COR_VIII': semn(_cor['mediana_viii']),

    'R_DIF': '&minus;' + d(abs(mv['corelatie_medie_vs_gap'])),
    'N_BOOT': str(N_BOOT), 'MIN_N': str(MIN_N), 'MIN_N_TESTE': str(MIN_N_TESTE),
    'CRIT_TESTE': d(criteriu('prag_teste'), 1),
    'CRIT_GRAFICE': d(criteriu('prag_grafice'), 1),
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

# Pagina se scrie într-un fișier alături, se verifică acolo, și abia apoi ia locul celei
# vechi. Altfel un build căzut ar lăsa pe disc exact pagina pe care verificarea a respins-o.
TMP = OUT + '.nou'
io.open(TMP, 'w', encoding='utf-8', newline='\n').write(s)
r = subprocess.run([sys.executable, os.path.join(HERE, 'verifica_text.py'), TMP])
if r.returncode:
    os.remove(TMP)
    print('\nBUILD CĂZUT: o afirmație din text nu mai e susținută de date. '
          'index.html a rămas neatins.')
    sys.exit(r.returncode)
os.replace(TMP, OUT)
print(f'\nscris {os.path.normpath(OUT)}  ({len(s):,} caractere)'.replace(',', ' '))
