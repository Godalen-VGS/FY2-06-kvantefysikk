"""Automatisk retting av FY2-06-kvantefysikk.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1', 'fotonenergi_ev(500e-9) skal gi ca. 2.48 eV', 'naer(fotonenergi_ev(500e-9), 6.626e-34 * 2.998e8 / 500e-9 / 1.602e-19) and naer(fotonenergi_ev(1240e-9), 1.0, rel=1e-3)'),
    ('2_h_eksakt', 'planck_fra_data skal finne h fra eksakte data', 'naer(planck_fra_data([5e14, 7e14, 9e14], [6.626e-34 / 1.602e-19 * f - 2 for f in [5e14, 7e14, 9e14]]), 6.626e-34, rel=1e-6)'),
    ('2_W_eksakt', 'utlosningsarbeid_ev skal gi 2 eV for de samme dataene', 'naer(utlosningsarbeid_ev([5e14, 7e14, 9e14], [6.626e-34 / 1.602e-19 * f - 2 for f in [5e14, 7e14, 9e14]]), 2, rel=1e-6)'),
    ('2_data', 'Plancks konstant fra fotoelektrisk.csv skal være ca. 6.6e-34 J·s', "naer(planck_fra_data(*__import__('numpy').loadtxt('fotoelektrisk.csv', delimiter=',', skiprows=1, unpack=True)), 6.626e-34, rel=0.05)"),
    ('3_halfa', 'bolgelengde_overgang(3, 2) skal gi ca. 656 nm (rød H-alfa)', 'naer(bolgelengde_overgang(3, 2), 6.626e-34 * 2.998e8 / (13.6 * 1.602e-19 * (1/4 - 1/9)) * 1e9, rel=1e-4)'),
    ('3_lyman', 'bolgelengde_overgang(2, 1) skal gi ca. 122 nm (UV)', 'naer(bolgelengde_overgang(2, 1), 6.626e-34 * 2.998e8 / (13.6 * 1.602e-19 * 0.75) * 1e9, rel=1e-4)'),
    ('4', 'de_broglie_elektron(100) skal gi ca. 1.23e-10 m', 'naer(de_broglie_elektron(100), 6.626e-34 / (2 * 9.109e-31 * 1.602e-19 * 100)**0.5, rel=1e-4)'),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
