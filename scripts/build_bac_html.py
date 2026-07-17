# Construiește raportul BAC ca pagină autonomă (date inline; CSP-ul blochează CDN-uri).
# Sursele: candidati_bac.json, filiera_bac.json, shrinkage_bac.json, plus arborele de
# operaționalizare generat din operationalizare.py — aceeași sursă care aplică regula.
import sys, os, json, html
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from operationalizare import construieste, layout

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..', 'date', 'bac')
OUT = os.path.join(HERE, '..', 'bac.html')
FILIERE = ['teoretica', 'tehnologica', 'vocationala']
NUME = {'teoretica': 'Teoretică', 'tehnologica': 'Tehnologică', 'vocationala': 'Vocațională'}
YEARS = list(range(2017, 2026))

cand = json.load(open(os.path.join(BASE, 'candidati_bac.json'), encoding='utf-8'))
dist = json.load(open(os.path.join(BASE, 'distributii_bac.json'), encoding='utf-8'))
teste = json.load(open(os.path.join(BASE, 'teste_bac.json'), encoding='utf-8'))

# Cifrele din text se CALCULEAZĂ din aceleași fișiere pe care le descriu. Prima versiune
# le avea scrise de mână și au rămas în urmă după re-rularea pe surse curate.
def ro(x, z=0):
    return f'{x:,.{z}f}'.replace(',', ' ').replace('.', ',')
def d(x, n=2):
    """Zecimale cu virgulă — separatorul zecimal în română."""
    return f'{x:.{n}f}'.replace('.', ',')
def pct(x, n=0):
    return f'{x*100:.{n}f}'.replace('.', ',') + '%'
def putere(x):
    """p mic, ca putere a lui zece: 4,3×10⁻⁸."""
    e = 0
    while x < 1:
        x *= 10; e -= 1
    sup = str(-e).translate(str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹'))
    return f'{d(x,1)}×10⁻{sup}'
cel = dist['scoala_an']
N_CEL = len(cel)
N_NEG = sum(1 for r in cel if r['skew_g1'] < 0)
N_SIG = sum(1 for r in cel if r['p_skew'] is not None and r['p_skew'] < 0.05)
R_GAP = abs(dist['r_gap_mediana'])
GAP_MED = abs(sorted(r['gap'] for r in cel)[len(cel) // 2])
PLAFON = sum(1 for r in cel if r['pond_plafon_950'] >= 0.10)
fr = teste['friedman_pe_orase']
W_MIN, W_MAX = min(v['kendall_W'] for v in fr.values()), max(v['kendall_W'] for v in fr.values())
P_MAX_FR = max(v['p'] for v in fr.values())
pc = [r for r in cand['candidati'] if r[5] == 1]
ACOP = {}
for an in YEARS:
    a = [r for r in pc if r[0] == an]
    ACOP[an] = (sum(1 for r in a if r[8] is not None) / len(a),
                sum(1 for r in a if r[7] is not None) / len(a),
                sum(1 for r in a if r[8] is not None) - sum(1 for r in a if r[7] is not None))
AC_MIN, AC_MAX = min(v[0] for v in ACOP.values()), max(v[0] for v in ACOP.values())
PUB_MIN, PUB_MAX = min(v[1] for v in ACOP.values()), max(v[1] for v in ACOP.values())
G_MIN, G_MAX = min(v[2] for v in ACOP.values()), max(v[2] for v in ACOP.values())
PROMO_PCT = len(pc) / len(cand['candidati'])
N_ARB = None  # completat după construirea arborelui

fil = json.load(open(os.path.join(BASE, 'filiera_bac.json'), encoding='utf-8'))
shr = json.load(open(os.path.join(BASE, 'shrinkage_bac.json'), encoding='utf-8'))

# ---- arborele de operaționalizare, ca SVG static (layout calculat aici) ----
arbore = construieste(cand['candidati'])
N_ARB = arbore['n']
noduri, muchii = layout(arbore, dx=34, dy=250)
W = 2 * 250 + 330
H = max(n['_x'] for n in noduri) + 68
def curba(a, b):
    x0, y0, x1, y1 = a['_y'], a['_x'], b['_y'], b['_x']
    mx = (x0 + x1) / 2
    return f'M{x0},{y0}C{mx},{y0} {mx},{y1} {x1},{y1}'
p = [f'<svg viewBox="0 0 {W} {H}" class="tree" role="img" '
     f'aria-label="Arborele profil–filieră, generat din date">']
p.append('<g transform="translate(16,34)">')
for a, b in muchii:
    p.append(f'<path d="{curba(a,b)}" fill="none" stroke="var(--tree-link)" stroke-width="1.4"/>')
for n in noduri:
    adanc = 0 if n is arbore else (1 if n.get('children') else 2)
    cls = ['n-root', 'n-branch', 'n-leaf'][adanc]
    p.append(f'<circle cx="{n["_y"]}" cy="{n["_x"]}" r="4.5" class="{cls}"/>')
    et = html.escape(n['name'])
    nr = f'{n["n"]:,}'.replace(',', '.')      # doar numărul primește punct de mie;
    p.append(f'<text x="{n["_y"]+10}" y="{n["_x"]}" dy="0.32em" class="{cls}">{et}'
             f'<tspan class="n-count"> · {nr}</tspan></text>')
p.append('</g></svg>')
TREE_SVG = ''.join(p)

# ---- date pentru taburile de analiză ----
TM = {}
for f in FILIERE:
    for an in YEARS:
        k = f'TIMIȘOARA|{f}|{an}'
        if k in shr['celule']:
            c = shr['celule'][k]
            TM[f'{f}|{an}'] = {
                'mu': c['mu_hat'], 'tau2': c['tau2'], 'k': c['k'],
                'dist': c['licee_distincte_de_medie'], 'dmax': c['delta_rang_max'],
                'scoli': [{'d': s['denumire'], 'n': s['n'], 'br': s['mediana'],
                           'rb': s['rang_naiv'], 'sh': s['mediana_shrink'],
                           'lo': s['ci_low'], 'hi': s['ci_high'], 'w': s['w_shrink']}
                          for s in c['scoli']]}
ORASE = {}
for an in YEARS:
    for f in FILIERE:
        pf = fil['pe_ani'][str(an)][f]
        if pf.get('test') == 'nefăcut':
            continue
        ORASE[f'{f}|{an}'] = {'med': pf['mediane'], 'n': pf['n_licee'], 'p': pf['p'],
                              'eps2': pf['epsilon2'], 'dunn': pf['dunn']}
# Evoluția medianelor: pentru fiecare filieră, mediana BRUTĂ a fiecărui liceu pe ani, plus
# mediana filierei în anul respectiv. Linia groasă e a filierei, nu a orașului: mediana unui
# oraș calculată între filiere n-ar avea referință.
def median_of(v):
    q=sorted(v); n=len(q)
    return q[n//2] if n%2 else (q[n//2-1]+q[n//2])/2
EVO = {}
for f in FILIERE:
    scoli, linia = {}, {}
    for an in YEARS:
        c = shr['celule'].get(f'TIMIȘOARA|{f}|{an}')
        if not c:
            continue
        linia[an] = round(median_of([x['mediana'] for x in c['scoli']]), 3)
        for x in c['scoli']:
            nume = x['denumire'].split(' — ')[0]
            scoli.setdefault(nume, {})[an] = x['mediana']
    EVO[f] = {'scoli': scoli, 'filiera': linia}

FRIED = {k: {'rang': [v['rang_mediu_pe_an'][str(a)] for a in YEARS], 'W': v['kendall_W'],
             'p': v['p'], 'n': v['n_celule_balansate'], 'Q': v['Q'], 'df': v['df']}
         for k, v in teste['friedman_pe_orase'].items()}
DATA = {'tm': TM, 'orase': ORASE, 'comp': fil['compozitie'], 'ani': YEARS,
        'filiere': FILIERE, 'nume': NUME, 'fried': FRIED, 'evo': EVO}

CSS = '''
:root{
  --paper:#f2f4f6; --surface:#ffffff; --ink:#16202b; --muted:#5a6b7b; --line:#dfe4e9;
  --accent:#0f6f9e; --f-teoretica:#0f6f9e; --f-tehnologica:#b35c00; --f-vocationala:#6b4bb8;
  --tree-link:#c3ccd4; --grid:#e9edf1; --chip:#eef1f4;
  --serif:Georgia,"Iowan Old Style","Times New Roman",serif;
  --sans:"Segoe UI",system-ui,-apple-system,"Helvetica Neue",sans-serif;
}
@media (prefers-color-scheme:dark){:root{
  --paper:#10161d; --surface:#182029; --ink:#e3e9ef; --muted:#93a2b1; --line:#2a3542;
  --accent:#3d93c4; --f-teoretica:#3d93c4; --f-tehnologica:#cf7d1f; --f-vocationala:#8f76d4;
  --tree-link:#3a4654; --grid:#232e3a; --chip:#212b36;
}}
:root[data-theme="dark"]{
  --paper:#10161d; --surface:#182029; --ink:#e3e9ef; --muted:#93a2b1; --line:#2a3542;
  --accent:#3d93c4; --f-teoretica:#3d93c4; --f-tehnologica:#cf7d1f; --f-vocationala:#8f76d4;
  --tree-link:#3a4654; --grid:#232e3a; --chip:#212b36;
}
:root[data-theme="light"]{
  --paper:#f2f4f6; --surface:#ffffff; --ink:#16202b; --muted:#5a6b7b; --line:#dfe4e9;
  --accent:#0f6f9e; --f-teoretica:#0f6f9e; --f-tehnologica:#b35c00; --f-vocationala:#6b4bb8;
  --tree-link:#c3ccd4; --grid:#e9edf1; --chip:#eef1f4;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:32px 20px 80px}
header{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:4px}
h1{font-family:var(--serif);font-size:30px;line-height:1.25;margin:0 0 6px;
  font-weight:600;text-wrap:balance;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:14px;margin:0}
.sub a{color:var(--accent);text-decoration:none;border-bottom:1px solid transparent}
.sub a:hover{border-bottom-color:var(--accent)}
.sub a:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:2px}
nav{display:flex;gap:2px;margin:22px 0 26px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.tab{appearance:none;background:none;border:0;border-bottom:2px solid transparent;
  color:var(--muted);font:inherit;font-size:14px;padding:10px 14px;cursor:pointer;
  margin-bottom:-1px;white-space:nowrap}
.tab:hover{color:var(--ink)}
.tab[aria-selected="true"]{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
.tab:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px}
.panel[hidden]{display:none}
.prose{font-family:var(--serif);max-width:65ch;font-size:16.5px;line-height:1.7}
.prose p{margin:0 0 15px}
.prose h2{font-family:var(--serif);font-size:21px;margin:34px 0 12px;font-weight:600}
.prose h3{font-family:var(--sans);font-size:13px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--muted);margin:28px 0 8px;font-weight:600}
.prose ul{margin:0 0 15px;padding-left:20px}
.prose li{margin-bottom:7px}
.prose code{font-family:ui-monospace,"Cascadia Mono",Consolas,monospace;font-size:.86em;
  background:var(--chip);padding:1px 5px;border-radius:3px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:6px;
  padding:18px;margin:20px 0}
.card-h{font-family:var(--sans);font-size:13px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--muted);margin:0 0 4px;font-weight:600}
.card-i{font-size:13.5px;color:var(--muted);margin:0 0 14px;max-width:70ch}
.scroll{overflow-x:auto}
svg.tree{min-width:820px;height:auto;font-family:var(--sans);font-size:13px}
.tree text.n-root{fill:var(--accent);font-weight:700}
.tree text.n-branch{fill:var(--ink);font-weight:700}
.tree text.n-leaf{fill:var(--muted)}
.tree circle.n-root{fill:var(--accent)}
.tree circle.n-branch{fill:var(--muted)}
.tree circle.n-leaf{fill:none;stroke:var(--muted);stroke-width:1.5}
.tree .n-count{fill:var(--muted);font-weight:400;font-variant-numeric:tabular-nums}
.ctrls{display:flex;gap:18px;align-items:center;flex-wrap:wrap;margin:0 0 18px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:5px;overflow:hidden;
  background:var(--surface)}
.seg button{appearance:none;background:none;border:0;border-right:1px solid var(--line);
  font:inherit;font-size:13.5px;padding:7px 14px;color:var(--muted);cursor:pointer;
  display:flex;align-items:center;gap:7px}
.seg button:last-child{border-right:0}
.seg button:hover{color:var(--ink)}
.seg button[aria-pressed="true"]{background:var(--chip);color:var(--ink);font-weight:600}
.seg button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.dot{width:9px;height:9px;border-radius:50%;flex:none}
label.lbl{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  font-weight:600;margin-right:8px}
select{font:inherit;font-size:13.5px;padding:6px 10px;border:1px solid var(--line);
  border-radius:5px;background:var(--surface);color:var(--ink)}
select:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.stats{display:flex;gap:26px;flex-wrap:wrap;margin:0 0 6px;padding:14px 0;
  border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.stat{min-width:96px}
.stat .v{font-size:22px;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.2}
.stat .l{font-size:12px;color:var(--muted);letter-spacing:.04em}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}
th{text-align:right;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--muted);font-weight:600;padding:8px 9px;border-bottom:1px solid var(--line);
  white-space:nowrap}
th.l,td.l{text-align:left}
td{padding:7px 9px;border-bottom:1px solid var(--grid);white-space:nowrap}
tbody tr:hover{background:var(--chip)}
.note{font-size:13px;color:var(--muted);margin:12px 0 0;max-width:72ch}
.chart{width:100%;height:auto;font-family:var(--sans);font-size:12px;min-width:900px}
.chart .grid{stroke:var(--grid);stroke-width:1}
.chart .ax{fill:var(--muted);font-size:11px}
.chart .nm{fill:var(--ink);font-size:12.5px}
.chart .ci{stroke-width:2;stroke-linecap:round;opacity:.55}
.chart .pt{stroke:var(--surface);stroke-width:2}
.chart .ref{stroke:var(--muted);stroke-dasharray:3 3;stroke-width:1}
.chart .reflbl{fill:var(--muted);font-size:10.5px}
.fr-line{fill:none;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.ev-sc{fill:none;stroke-width:1.2;opacity:.42}
.ev-sc:hover{opacity:1;stroke-width:2.4}
.ev-fil{fill:none;stroke-width:3;stroke-linejoin:round}
.modenav{display:inline-flex;border:1px solid var(--line);border-radius:5px;overflow:hidden;background:var(--surface);margin:0 0 12px}
.modenav button{appearance:none;background:none;border:0;border-right:1px solid var(--line);font:inherit;font-size:13px;padding:6px 12px;color:var(--muted);cursor:pointer}
.modenav button:last-child{border-right:0}
.modenav button[aria-pressed="true"]{background:var(--chip);color:var(--ink);font-weight:600}
.modenav button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.fr-lbl{font-size:12px;font-weight:600}
.leg{display:flex;gap:18px;flex-wrap:wrap;margin:10px 0 0;font-size:12.5px;color:var(--muted)}
.leg span{display:inline-flex;align-items:center;gap:7px}
.leg svg{flex:none}
.chart .row:hover rect.hit{fill:var(--chip);opacity:1}
.tip{position:fixed;pointer-events:none;background:var(--surface);border:1px solid var(--line);
  border-radius:5px;padding:8px 10px;font-size:12.5px;box-shadow:0 4px 14px rgba(0,0,0,.14);
  opacity:0;transition:opacity .1s;max-width:280px;z-index:9}
.tip b{display:block;margin-bottom:3px;font-size:12.5px}
.tip .r{color:var(--muted);font-variant-numeric:tabular-nums}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
'''

BODY = f'''<div class="wrap">
<header>
  <h1>Bacalaureatul în liceele din Timișoara, 2017–2025</h1>
  <p class="sub">Sesiunea de vară · promoția curentă · trei filiere tratate separat · <a href="index.html">Evaluarea Națională, 2020–2025 →</a></p>
</header>

<nav role="tablist">
  <button class="tab" role="tab" id="t-date" aria-controls="p-date" aria-selected="true">Datele și definițiile</button>
  <button class="tab" role="tab" id="t-orase" aria-controls="p-orase" aria-selected="false">Variația structurală: trei orașe</button>
  <button class="tab" role="tab" id="t-evo" aria-controls="p-evo" aria-selected="false">Evoluția medianelor</button>
  <button class="tab" role="tab" id="t-tm" aria-controls="p-tm" aria-selected="false">Liceele din Timișoara</button>
</nav>

<section class="panel" id="p-date" role="tabpanel" aria-labelledby="t-date">
<div class="prose">
<p>Raportul răspunde la o singură întrebare: <em>cât de mult diferă liceele din Timișoara între ele la bacalaureat, și cât din ce vedem e diferență reală, iar nu zgomot?</em> Datele sunt cele publicate de minister pe data.gov.ro, sesiunea de vară, nouă ani.</p>
<p>Voi arăta, în prima parte, ce am numărat și cum; în a doua, cât de mult diferă cele trei orașe între ele, ceea ce fixează scara pe care se citește restul; în a treia, unde stă fiecare liceu timișorean în lumea lui.</p>

<h2>Prezumția care structurează tot</h2>
<p>Asum că, în același oraș, cele trei filiere sunt trei lumi sociale diferite. Un liceu teoretic și unul tehnologic nu recrutează aceiași elevi, nu-i pregătesc pentru aceleași examene și nu răspund acelorași așteptări. De aceea nimic nu se compară între filiere: un clasament care le-ar amesteca ar fi, în fapt, un clasament al filierelor — primele locuri ar fi teoretice, ultimele tehnologice, iar cititorul ar crede că citește despre școli când citește despre tipuri de școli.</p>
<p>Prezumția nu e o ipoteză pe care o testăm, ci lentila prin care privim. Or, tocmai de aceea trebuie spusă deschis: cine nu o acceptă va citi altfel toate cifrele de mai jos.</p>

<h3>Maparea profil → filieră</h3>
<p>Filiera nu e un câmp completat de mână, ci o recodificare a profilului. Arborele coboară de la populația de candidați (rădăcina) la profiluri (frunzele), iar figura se generează din aceeași funcție care aplică regula în analiză — deci nu poate diverge de ea. Partiția e verificată la fiecare rulare: dacă un profil ar apărea în două filiere, arborele nu s-ar mai desena. Pe cei {ro(N_ARB)} de candidați din promoția curentă a celor trei orașe, nu apare nicio excepție.</p>
</div>
<div class="card"><div class="scroll">{TREE_SVG}</div></div>
<div class="prose">

<h2>Ce am numărat</h2>
<h3>Media, recalculată</h3>
<p>Coloana <code>Medie</code> din datele ministerului există doar pentru candidații care au luat cel puțin 5 la fiecare probă. În 2025, din 107.961 de candidați la nivel național, doar 84.464 — 78% — au o medie publicată; ceilalți 23.420 s-au prezentat, au dat toate probele, au picat una și nu au nicio medie. Nu există nicio excepție de la regula asta.</p>
<p>Or, a lucra cu coloana publicată ar însemna să calculăm mediana <em>supraviețuitorilor</em>. Întrebarea de pus oricărui set de date e cine lipsește din el și dacă absența lor schimbă concluzia; aici răspunsul e că da. Cum selecția e cu atât mai dură cu cât liceul e mai slab, statistica fiecărei școli s-ar calcula pe un subeșantion cu atât mai favorabil ei cu cât școala are mai multe eșecuri. Efectul ar merge exact invers decât trebuie.</p>
<p>De aceea recalculăm media pentru toți cei prezenți la toate probele, cu formula oficială: media aritmetică a notelor finale, trunchiată la două zecimale, fără rotunjire. Nota finală pe probă e cea de la contestație, acolo unde s-a contestat. Formula a fost verificată pe candidații care <em>au</em> medie publicată: o reproduce exact în 100% din cazuri, în fiecare din cei nouă ani. Rotunjirea, în locul trunchierii, ar greși într-o treime din cazuri.</p>
<p>Câștigul e substanțial: acoperirea urcă de la {pct(PUB_MIN)}–{pct(PUB_MAX)} la {pct(AC_MIN,1)}–{pct(AC_MAX,1)} din candidați, adică între {ro(G_MIN)} și {ro(G_MAX)} de oameni recuperați în fiecare an, în cele trei orașe. Cei recuperați sunt, prin construcție, coada de jos — exact partea pe care coloana publicată o ascundea.</p>

<h3>Mediana, nu media</h3>
<p>Statistica fiecărui liceu e mediana mediilor candidaților lui. Alegerea nu e preluată din analiza anterioară, ci decisă pe datele acestea: din {ro(N_CEL)} de celule școală–an, {pct(N_NEG/N_CEL)} au distribuția asimetrică la stânga, iar {pct(N_SIG/N_CEL)} semnificativ. Media stă sub mediană cu {d(GAP_MED)} puncte în mod tipic, dar abaterea nu e neutră — corelează −{d(R_GAP)} cu nivelul școlii, deci media penalizează exact liceele bune. Cauza e plafonul: la {PLAFON} dintre celule, peste o zecime dintre candidați au medii de 9,50 sau peste. Desigur, în clasament diferența e mică: ordonarea după medie și cea după mediană dau un coeficient Spearman de 0,99. Dar corectitudinea unei alegeri nu se măsoară prin cât de mult schimbă rezultatul.</p>

<h3>Neprezentații</h3>
<p>Cine se înscrie și nu se prezintă intră în calculul liceului, dar fără notă: e așezat sub toți cei care s-au prezentat. Se poate, fiindcă mediana e o poziție, nu o medie — ca să afli cine e la mijloc îți trebuie doar câți sunt sub el, nu cât au luat. În analiza de supraviețuire, cazurile despre care știi doar că valoarea lor cade dincolo de o limită se numesc <em>cazuri cenzurate</em>; aici limita e nota cea mai mică.</p>
<p>Un liceu cu mulți neprezentați e astfel penalizat chiar în cifra de performanță, fără să inventăm note. Iar o notă inventată nici n-ar schimba ceva: orice valoare sub mediană ocupă aceleași poziții, deci 4,50 și 1,00 dau rezultate identice. Tocmai de aceea nu trebuie aleasă una.</p>
<p>Asum totuși, și o spun deschis, că un neprezentat stă sub oricine s-a prezentat. Cei mai mulți sunt elevi care s-au ferit de examen, dar unii au plecat la o facultate în străinătate sau au fost bolnavi — pe toți îi punem sub cel cu 1,00. Miza e inegală: la Timișoara, în 2025, neprezentații sunt sub 1% la teoretic și la vocațional, dar 4% la tehnologic. Acolo unde asumpția contează, contează mult.</p>

<h3>Promoția curentă</h3>
<p>Intră doar candidații care au terminat clasa a XII-a în anul examenului — {pct(PROMO_PCT)} din total. Ceilalți vin din promoții anterioare și rămân atașați în date liceului absolvit atunci; în fișierul din 2025 există candidați din promoția 2013–2014. A-i include ar însemna să atribuim unei școli rezultatul unei cohorte pe care a predat-o acum un deceniu, iar cum cei care revin sunt disproporționat cei care au eșuat, liceele cu multe picări ar fi penalizate de două ori.</p>

<h3>Fără însumarea anilor</h3>
<p>Anii nu se adună. Testul Friedman, pe liceele prezente în toți cei nouă ani, respinge ipoteza că anii ar fi interschimbabili, în toate cele trei orașe: cea mai mare valoare p din cele trei e {putere(P_MAX_FR)}, iar coeficientul de concordanță Kendall stă între {d(W_MIN)} și {d(W_MAX)}. Tiparul e consecvent — 2018 e cel mai slab an aproape pretutindeni, 2024 cel mai bun. De aceea fiecare an se citește separat.</p>

<h2>Limitele</h2>
<ul>
<li><strong>Măsurăm selecția la intrare, nu valoarea adăugată.</strong> Un colegiu care alege primii 5% dintre absolvenții de gimnaziu va avea medii mari orice ar face la clasă. Nimic din datele acestea nu separă ce aduce școala de ce aduce elevul.</li>
<li><strong>Pragul de 10 candidați</strong> pe celulă liceu–filieră. Sub el, mediana nu e folosită. Consecința e vizibilă: un liceu cu o clasă mică și constantă apare pe tabul filierei respective doar în anii în care clasa trece pragul — „Bartók Béla" are o clasă de servicii aproape în fiecare an, dar apare la tehnologic o singură dată în nouă.</li>
<li><strong>Liceele cu două filiere apar de două ori</strong>, cu celule și mediane diferite, marcate ca atare. Nu e o dublare: sunt clase diferite. „Carmen Sylva" are 82 de candidați la teoretic și 46 la vocațional în 2025.</li>
<li><strong>Învățământul special rămâne în clasament.</strong> „IRIS" e liceu teoretic special; mediana lui măsoară altceva decât a celorlalte, iar cititorul trebuie să știe asta când îl vede pe ultimul loc.</li>
<li><strong>2016 e exclus.</strong> Era singurul an cu regula veche de contestație — nota contestată conta doar dacă diferea cu cel puțin 0,5 puncte — și singurul care nu se validează perfect nici așa (95,5%, față de 100% în ceilalți).</li>
<li><strong>Pierdere de date: practic zero.</strong> Din cei nouă ani cade un singur rând, cu un cod de școală invalid. O versiune anterioară a analizei citea, pentru 2017 și 2019, fișierele CSV ale ministerului, unde separatorul zecimal e virgulă ne-quotată: acolo o notă ruptă în două câmpuri nu se mai poate reconstrui — „5,6 · 9" și „5 · 6,9" sunt amândouă plauzibile și dau medii diferite — și se pierdeau 1,8% dintre rânduri. Aceleași seturi de pe data.gov.ro conțin însă și un fișier ODS (2017), și unul XLSX (2019), cu valorile ca numere. Analiza citește acum doar formatele tipate.</li>
</ul>
</div>
</section>

<section class="panel" id="p-orase" role="tabpanel" aria-labelledby="t-orase" hidden>
<div class="prose"><p>Cele trei orașe nu sunt subiectul raportului; ele fixează scara. Dacă liceele din Timișoara ar semăna cu cele din Cluj și Iași, diferențele dintre ele ar trebui citite ca variație locală. Comparația se face <strong>în interiorul fiecărei filiere</strong>, cu rangurile calculate tot acolo.</p></div>
<div id="v-fried"></div>
<div class="ctrls" id="c-orase"></div>
<div id="v-orase"></div>
</section>

<section class="panel" id="p-evo" role="tabpanel" aria-labelledby="t-evo" hidden>
<div class="prose"><p>Cum s-a mișcat fiecare liceu de la an la an, în interiorul lumii lui. Linia groasă e mediana filierei — o mediană a orașului, calculată între filiere, n-ar avea referință.</p></div>
<div class="ctrls" id="c-evo"></div>
<div id="v-evo"></div>
</section>

<section class="panel" id="p-tm" role="tabpanel" aria-labelledby="t-tm" hidden>
<div class="prose"><p>Fiecare liceu e arătat cu mediana lui ajustată și cu intervalul în care datele o pot localiza. Ajustarea trage medianele nesigure spre media lumii lor, cu atât mai tare cu cât liceul are mai puțini candidați: un clasament naiv le-ar da un loc pe care datele nu-l susțin. Linia punctată e media filierei în anul respectiv.</p></div>
<div class="ctrls" id="c-tm"></div>
<div id="v-tm"></div>
</section>
</div>
<div class="tip" id="tip"></div>
'''

JS = '''
const D = %%DATA%%;
const FCOL = {teoretica:'var(--f-teoretica)', tehnologica:'var(--f-tehnologica)', vocationala:'var(--f-vocationala)'};
const nf = (x,d=2)=> x==null ? '—' : x.toFixed(d).replace('.',',');
const esc = s => s.replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const state = {orase:{f:'teoretica'}, evo:{f:'teoretica'}, tm:{f:'teoretica', an:2025}};

// ---- taburi ----
const tabs=[...document.querySelectorAll('.tab')];
tabs.forEach(t=>t.addEventListener('click',()=>{
  tabs.forEach(x=>{x.setAttribute('aria-selected', x===t);
    document.getElementById(x.getAttribute('aria-controls')).hidden = x!==t;});
}));

// ---- tooltip ----
const tip=document.getElementById('tip');
function showTip(e,h){tip.innerHTML=h;tip.style.opacity=1;
  const r=tip.getBoundingClientRect();
  tip.style.left=Math.min(e.clientX+14, innerWidth-r.width-10)+'px';
  tip.style.top=Math.max(8, e.clientY-r.height-10)+'px';}
function hideTip(){tip.style.opacity=0;}

// ---- selector de filieră ----
function segFiliera(sel, cur, cb){
  const s=document.createElement('div'); s.className='seg';
  D.filiere.forEach(f=>{
    const b=document.createElement('button'); b.setAttribute('aria-pressed', f===cur);
    b.innerHTML=`<span class="dot" style="background:${FCOL[f]}"></span>${D.nume[f]}`;
    b.onclick=()=>cb(f); s.appendChild(b);
  });
  const l=document.createElement('label'); l.className='lbl'; l.textContent='Filiera';
  sel.appendChild(l); sel.appendChild(s);
}

// ============ Friedman: rangul mediu al anilor, per oraș ============
// Replică graficul din raportul EN. Identitatea orașului e purtată de culoare ȘI de
// formă (linie plină/întreruptă + marcaj), ca să nu depindă de culoare singură.
const FR_STIL = {
  'IAȘI':        {col:'var(--f-teoretica)',   dash:'',      marc:'cerc'},
  'CLUJ-NAPOCA': {col:'var(--f-tehnologica)', dash:'6 3',   marc:'triunghi'},
  'TIMIȘOARA':   {col:'var(--f-vocationala)', dash:'2 2',   marc:'patrat'},
};
function marcaj(tip, x, y, col){
  if(tip==='cerc')     return `<circle cx="${x}" cy="${y}" r="4" fill="${col}" stroke="var(--surface)" stroke-width="1.5"/>`;
  if(tip==='triunghi') return `<path d="M${x},${y-4.6} L${x+4.2},${y+3.2} L${x-4.2},${y+3.2} Z" fill="${col}" stroke="var(--surface)" stroke-width="1.5"/>`;
  return `<rect x="${x-3.6}" y="${y-3.6}" width="7.2" height="7.2" fill="${col}" stroke="var(--surface)" stroke-width="1.5"/>`;
}
function renderFriedman(){
  const fl=state.orase.f, F={}, ORD=[];
  ['IAȘI','CLUJ-NAPOCA','TIMIȘOARA'].forEach(c=>{ const k=c+'|'+fl; if(D.fried[k]){F[c]=D.fried[k]; ORD.push(c);} });
  if(!ORD.length) return;
  const K=D.ani.length, W=980, HH=330, PL=54, PR=22, PT=22, PB=42;
  const X=i=>PL+i*(W-PL-PR)/(K-1), Y=r=>PT+(K-r)/(K-1)*(HH-PT-PB);
  let g=`<svg class="chart" viewBox="0 0 ${W} ${HH}" role="img" aria-label="Rangul mediu al anilor, pe orașe, în filiera selectată">`;
  for(let r=1;r<=K;r++) g+=`<line class="grid" x1="${PL}" y1="${Y(r)}" x2="${W-PR}" y2="${Y(r)}"/>`
    + (r%2===1?`<text class="ax" x="${PL-9}" y="${Y(r)}" dy="0.32em" text-anchor="end">${r}</text>`:'');
  D.ani.forEach((a,i)=>{ g+=`<text class="ax" x="${X(i)}" y="${HH-PB+20}" text-anchor="middle">${a}</text>`; });
  g+=`<text class="ax" x="${PL-40}" y="${(PT+HH-PB)/2}" transform="rotate(-90 ${PL-40},${(PT+HH-PB)/2})" text-anchor="middle">rangul mediu al anului (1 = cel mai slab)</text>`;
  ORD.forEach(c=>{ const st=FR_STIL[c], d=F[c].rang.map((r,i)=>`${i?'L':'M'}${X(i)},${Y(r)}`).join(' ');
    g+=`<path class="fr-line" d="${d}" stroke="${st.col}" stroke-dasharray="${st.dash}"/>`;
    F[c].rang.forEach((r,i)=>{ g+=marcaj(st.marc, X(i), Y(r), st.col); }); });
  g+='</svg>';
  const leg=ORD.map(c=>{const st=FR_STIL[c];
    return `<span><svg width="26" height="12"><line x1="1" y1="6" x2="25" y2="6" stroke="${st.col}" stroke-width="2" stroke-dasharray="${st.dash}"/>${marcaj(st.marc,13,6,st.col)}</svg>${c==='CLUJ-NAPOCA'?'Cluj-Napoca':c==='IAȘI'?'Iași':'Timișoara'}</span>`;}).join('');
  const t=ORD.map(c=>`${c==='CLUJ-NAPOCA'?'Cluj':c==='IAȘI'?'Iași':'Timișoara'}: Q=${nf(F[c].Q,1)}, p=${F[c].p<0.001?F[c].p.toExponential(1).replace('.',','):nf(F[c].p,3)}, W=${nf(F[c].W)}, ${F[c].n} celule`).join(' · ');
  document.getElementById('v-fried').innerHTML=
    `<div class="card"><div class="card-h">Rangul mediu al anilor, pe orașe (testul Friedman)</div>
     <p class="card-i">Pentru fiecare celulă liceu×filieră, cei nouă ani se ordonează după mediana din anul respectiv: anul cel mai slab primește poziția 1, cel mai bun poziția 9. Graficul arată media acestor poziții, la nivelul tuturor celulelor orașului. Dacă anii ar fi interschimbabili, liniile ar fi plate.</p>
     <div class="scroll">${g}</div><div class="leg">${leg}</div>
     <p class="note">${t}</p>
     <p class="note">Dacă cele trei linii coboară și urcă împreună, efectul de an e național — de examen și de cohortă — nu local. Comută filiera: tiparele nu sunt aceleași. De aceea anii nu se adună, iar filierele nu se amestecă.</p></div>`;
}

// ============ TAB: trei orașe ============
function renderOrase(){
  const c=document.getElementById('c-orase'); c.innerHTML='';
  segFiliera(c, state.orase.f, f=>{state.orase.f=f; renderOrase(); renderFriedman();});
  const f=state.orase.f, v=document.getElementById('v-orase');
  const rows=D.ani.map(an=>{
    const o=D.orase[f+'|'+an]; if(!o) return null;
    return {an, ...o};
  }).filter(Boolean);
  const tmLast=rows.filter(r=>r.med['TIMIȘOARA']<=Math.min(r.med['CLUJ-NAPOCA'],r.med['IAȘI'])).length;
  const semn=rows.filter(r=>r.dunn.some(d=>d.p_holm<0.05)).length;
  let h=`<div class="stats">
    <div class="stat"><div class="v">${tmLast}/${rows.length}</div><div class="l">ani în care Timișoara e ultima</div></div>
    <div class="stat"><div class="v">${semn}/${rows.length}</div><div class="l">ani cu vreo diferență semnificativă</div></div>
    <div class="stat"><div class="v">${nf(Math.min(...rows.map(r=>r.eps2)),2)}–${nf(Math.max(...rows.map(r=>r.eps2)),2)}</div><div class="l">mărimea efectului (ε²)</div></div>
  </div>`;
  h+=`<div class="card"><div class="card-h">Mediana medianelor de liceu, pe an</div>
  <p class="card-i">Fiecare celulă e mediana liceelor din orașul respectiv, în filiera ${D.nume[f].toLowerCase()}. Testul compară cele trei orașe cu Kruskal–Wallis, cu rangurile calculate doar în interiorul filierei; perechile sunt corectate Holm într-o familie de nouă comparații pe an.</p>
  <div class="scroll"><table><thead><tr><th class="l">An</th>
  <th>Cluj-Napoca</th><th>Iași</th><th>Timișoara</th><th>p</th><th>ε²</th><th class="l">Perechi sub 0,05 (Holm)</th></tr></thead><tbody>`;
  rows.forEach(r=>{
    const mn=Math.min(r.med['CLUJ-NAPOCA'],r.med['IAȘI'],r.med['TIMIȘOARA']);
    const cell=(c)=>`<td${r.med[c]===mn?' style="font-weight:600"':''}>${nf(r.med[c])} <span style="color:var(--muted);font-size:11.5px">(${r.n[c]})</span></td>`;
    const sig=r.dunn.filter(d=>d.p_holm<0.05).map(d=>`${d.pereche} · p=${nf(d.p_holm,4)}`).join('<br>')||'<span style="color:var(--muted)">—</span>';
    h+=`<tr><td class="l">${r.an}</td>${cell('CLUJ-NAPOCA')}${cell('IAȘI')}${cell('TIMIȘOARA')}
      <td>${r.p<0.001?r.p.toExponential(1).replace('.',','):nf(r.p,3)}</td><td>${nf(r.eps2)}</td><td class="l" style="white-space:normal">${sig}</td></tr>`;
  });
  h+=`</tbody></table></div>
  <p class="note">În paranteză, numărul de licee din care se calculează mediana. Îngroșat = cea mai mică mediană din anul respectiv.</p></div>`;
  v.innerHTML=h;
}

// ============ Evoluția medianelor, în interiorul filierei ============
let evoMod='brut';
function renderEvo(){
  const c=document.getElementById('c-evo'); c.innerHTML='';
  segFiliera(c, state.evo.f, x=>{state.evo.f=x; renderEvo();});
  const f=state.evo.f, E=D.evo[f], col=FCOL[f], host=document.getElementById('v-evo');
  const nume=Object.keys(E.scoli);
  if(!nume.length){host.innerHTML='';return;}
  const rez = evoMod==='reziduu';
  const val=(sc,a)=> (E.scoli[sc][a]==null||E.filiera[a]==null) ? null
                   : (rez ? E.scoli[sc][a]-E.filiera[a] : E.scoli[sc][a]);
  const toate=nume.flatMap(sc=>D.ani.map(a=>val(sc,a))).filter(v=>v!=null);
  let lo=Math.min(...toate), hi=Math.max(...toate);
  const pad=(hi-lo)*0.06||0.5; lo-=pad; hi+=pad;
  const W=980, HH=380, PL=52, PR=124, PT=18, PB=38;
  const X=i=>PL+i*(W-PL-PR)/(D.ani.length-1), Y=v=>PT+(hi-v)/(hi-lo)*(HH-PT-PB);
  const tick=(hi-lo)>6?2:((hi-lo)>2?1:0.5);
  let g='<svg class="chart" viewBox="0 0 '+W+' '+HH+'" role="img" aria-label="Evoluția medianelor liceelor din Timișoara, filiera '+D.nume[f]+', 2017-2025">';
  for(let t=Math.ceil(lo/tick)*tick; t<=hi; t+=tick){
    g+='<line class="grid" x1="'+PL+'" y1="'+Y(t)+'" x2="'+(W-PR)+'" y2="'+Y(t)+'"/>'
     + '<text class="ax" x="'+(PL-9)+'" y="'+Y(t)+'" dy="0.32em" text-anchor="end">'+nf(t, tick<1?1:0)+'</text>';}
  D.ani.forEach((a,i)=>{g+='<text class="ax" x="'+X(i)+'" y="'+(HH-PB+19)+'" text-anchor="middle">'+a+'</text>';});
  if(rez) g+='<line x1="'+PL+'" y1="'+Y(0)+'" x2="'+(W-PR)+'" y2="'+Y(0)+'" class="ref"/>';
  nume.forEach(sc=>{
    const pts=D.ani.map((a,i)=>[i,val(sc,a)]).filter(x=>x[1]!=null);
    if(pts.length<2) return;
    const dd=pts.map((pv,k)=>(k?'L':'M')+X(pv[0])+','+Y(pv[1])).join(' ');
    g+='<path class="ev-sc" d="'+dd+'" stroke="'+col+'"><title>'+esc(sc)+'</title></path>';});
  if(rez){
    g+='<text class="reflbl" x="'+(W-PR+8)+'" y="'+Y(0)+'" dy="0.32em">mediana filierei</text>';
  } else {
    const fp=D.ani.map((a,i)=>[i,E.filiera[a]]).filter(x=>x[1]!=null);
    if(fp.length>1){
      g+='<path class="ev-fil" d="'+fp.map((pv,k)=>(k?'L':'M')+X(pv[0])+','+Y(pv[1])).join(' ')+'" stroke="'+col+'"/>';
      g+='<text class="fr-lbl" x="'+(W-PR+8)+'" y="'+Y(fp[fp.length-1][1])+'" dy="0.32em" fill="'+col+'">mediana filierei</text>';}
  }
  g+='</svg>';
  const notaBrut='Valorile brute conțin o <strong>evoluție structurală</strong> comună tuturor liceelor — un an de examen mai greu sau mai ușor mișcă toate liniile deodată (vezi tabul „Variația structurală"). O urcare sau o coborâre de la un an la altul nu înseamnă neapărat o schimbare reală a liceului; urmăriți dacă linia groasă se mișcă la fel.';
  const notaRez='Reziduul arată poziția <em>relativă</em> a liceului: scade din mediana lui mediana filierei din același an, deci rămâne doar diferența față de restul filierei, fără evoluția structurală comună. Linia filierei devine o dreaptă la zero.';
  host.innerHTML='<div class="card"><div class="card-h">Evoluția medianelor · '+D.nume[f].toLowerCase()+'</div>'
   +'<p class="card-i">Fiecare linie subțire e un liceu (minimum 10 candidați în anul respectiv); linia groasă e mediana filierei. Treci cu mouse-ul peste o linie ca să-i vezi numele.</p>'
   +'<div class="modenav"><button data-m="brut" aria-pressed="'+(!rez)+'">Valori brute</button>'
   +'<button data-m="reziduu" aria-pressed="'+rez+'">Reziduu (față de mediana filierei)</button></div>'
   +'<p class="note" style="margin:0 0 10px">'+(rez?notaRez:notaBrut)+'</p>'
   +'<div class="scroll">'+g+'</div></div>';
  host.querySelectorAll('.modenav button').forEach(b=>b.onclick=()=>{evoMod=b.dataset.m; renderEvo();});
}

// ============ TAB: Timișoara ============
function renderTM(){
  const c=document.getElementById('c-tm'); c.innerHTML='';
  segFiliera(c, state.tm.f, f=>{state.tm.f=f; renderTM();});
  const wrap=document.createElement('div');
  wrap.innerHTML=`<label class="lbl" for="an-sel">Anul</label>`;
  const sel=document.createElement('select'); sel.id='an-sel';
  D.ani.forEach(a=>{const o=document.createElement('option');o.value=a;o.textContent=a;
    if(a===state.tm.an)o.selected=true;sel.appendChild(o);});
  sel.onchange=e=>{state.tm.an=+e.target.value; renderTM();};
  wrap.appendChild(sel); c.appendChild(wrap);

  const key=state.tm.f+'|'+state.tm.an, cel=D.tm[key], v=document.getElementById('v-tm');
  if(!cel){v.innerHTML='<div class="card"><p class="card-i">Prea puține licee peste prag în acest an — celula nu se raportează.</p></div>';return;}
  const col=FCOL[state.tm.f];
  let h=`<div class="stats">
    <div class="stat"><div class="v">${cel.k}</div><div class="l">licee peste prag</div></div>
    <div class="stat"><div class="v">${nf(cel.mu)}</div><div class="l">media filierei</div></div>
    <div class="stat"><div class="v">${cel.dist}/${cel.k}</div><div class="l">se disting de medie</div></div>
    <div class="stat"><div class="v">${cel.dmax}</div><div class="l">mutare maximă de rang</div></div>
  </div>`;

  // --- graficul de intervale ---
  // PL = culoarul de nume. Denumirile liceelor sunt lungi („TEOLOGIC ORTODOX «SFÂNTUL
  // ANTIM IVIREANU» — vocațional" măsoară 356px); măsurat pe toate filierele și anii,
  // maximul e sub 370, deci 390 lasă margine. Sub atât, numele se taie.
  const S=cel.scoli, RH=26, PT=26, PB=40, PL=390, PR=26;
  const W=1150, HH=PT+PB+S.length*RH;
  const lo=Math.min(1, ...S.map(s=>s.lo)), hi=Math.max(10, ...S.map(s=>s.hi));
  const x0=Math.max(1, Math.floor(lo*2)/2-0.25), x1=Math.min(10, Math.ceil(hi*2)/2+0.25);
  const X=v=>PL+(v-x0)/(x1-x0)*(W-PL-PR);
  let g=`<svg class="chart" viewBox="0 0 ${W} ${HH}" role="img" aria-label="Mediana ajustată și intervalul, pe liceu">`;
  for(let t=Math.ceil(x0); t<=x1; t++) g+=`<line class="grid" x1="${X(t)}" y1="${PT-8}" x2="${X(t)}" y2="${HH-PB+4}"/><text class="ax" x="${X(t)}" y="${HH-PB+20}" text-anchor="middle">${t}</text>`;
  g+=`<line class="ref" x1="${X(cel.mu)}" y1="${PT-14}" x2="${X(cel.mu)}" y2="${HH-PB+4}"/>
      <text class="reflbl" x="${X(cel.mu)}" y="${PT-19}" text-anchor="middle">media filierei ${nf(cel.mu)}</text>`;
  S.forEach((s,i)=>{
    const y=PT+i*RH+RH/2;
    g+=`<g class="row">
      <rect class="hit" x="0" y="${y-RH/2}" width="${W}" height="${RH}" fill="transparent"
        data-i="${i}"/>
      <text class="nm" x="${PL-12}" y="${y}" dy="0.32em" text-anchor="end">${esc(s.d.replace(/ TIMIȘOARA/,'').replace(/^(LICEUL|COLEGIUL) /,''))}</text>
      <line class="ci" x1="${X(s.lo)}" y1="${y}" x2="${X(s.hi)}" y2="${y}" stroke="${col}"/>
      <circle class="pt" cx="${X(s.sh)}" cy="${y}" r="5" fill="${col}"/></g>`;
  });
  g+='</svg>';
  h+=`<div class="card"><div class="card-h">Mediana ajustată și intervalul ei</div>
    <p class="card-i">Punctul e mediana după ajustare; bara e intervalul de 95% în care datele o pot localiza. Liceele ale căror bare se suprapun nu pot fi despărțite. Sortare după mediana ajustată.</p>
    <div class="scroll">${g}</div></div>`;

  // --- tabelul ---
  h+=`<div class="card"><div class="card-h">Cifrele</div>
   <p class="card-i">„Brut" e mediana neajustată, cu rangul ei; <em>w</em> arată cât de mult se crede liceului pe cuvânt — aproape de 1 înseamnă că are destui candidați cât să vorbească singur.</p>
   <div class="scroll"><table><thead><tr><th class="l">#</th><th class="l">Liceul</th><th>Candidați</th>
   <th>Brut</th><th>Rang brut</th><th>Ajustat</th><th>Interval 95%</th><th>w</th></tr></thead><tbody>`;
  S.forEach((s,i)=>{h+=`<tr><td class="l">${i+1}</td><td class="l">${esc(s.d)}</td>
    <td>${s.n}</td><td>${nf(s.br)}</td><td>${s.rb}</td><td style="font-weight:600">${nf(s.sh)}</td>
    <td>${nf(s.lo)} – ${nf(s.hi)}</td><td>${nf(s.w)}</td></tr>`;});
  h+=`</tbody></table></div></div>`;
  v.innerHTML=h;

  v.querySelectorAll('rect.hit').forEach(r=>{
    const s=S[+r.dataset.i];
    r.addEventListener('mousemove',e=>showTip(e,
      `<b>${esc(s.d)}</b><span class="r">${s.n} candidați · brut ${nf(s.br)} (rang ${s.rb})<br>
       ajustat <b style="display:inline">${nf(s.sh)}</b> · interval ${nf(s.lo)} – ${nf(s.hi)} · w=${nf(s.w)}</span>`));
    r.addEventListener('mouseleave',hideTip);
  });
}
renderFriedman(); renderOrase(); renderEvo(); renderTM();
'''.replace('%%DATA%%', json.dumps(DATA, ensure_ascii=False))

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(f'<title>Bacalaureatul în liceele din Timișoara, 2017–2025</title>\n'
            f'<style>{CSS}</style>\n{BODY}\n<script>{JS}</script>\n')
print(f'scris: {OUT} ({os.path.getsize(OUT):,} B)')
