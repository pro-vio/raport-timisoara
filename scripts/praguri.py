# Pragurile nu se scriu de mână în scripturi. Se calculează în prag_incertitudine.py, din
# precizia declarată acolo, și se citesc de aici.
#
# `prag_teste`   — pentru Friedman și Kruskal-Wallis, unde nicio școală nu e numită.
# `prag_grafice` — pentru tot ce arată o școală anume: shrinkage, dinamica medianelor,
#                  clasamentul, diferența medie-mediană.
#
# prag_incertitudine.py trebuie rulat înaintea celorlalte. El nu depinde de niciun prag,
# deci lanțul n-are ciclu.
import io, json, os

_FISIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'date',
                       'prag_incertitudine.json')


def prag(nume):
    with io.open(_FISIER, encoding='utf-8') as f:
        d = json.load(f)
    p = d['praguri'][nume]
    return p['valoare']


def criteriu(nume):
    """Precizia declarată din care iese pragul, în puncte de notă."""
    with io.open(_FISIER, encoding='utf-8') as f:
        return json.load(f)['praguri'][nume]['criteriu_puncte']
