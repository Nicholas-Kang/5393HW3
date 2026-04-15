#!/usr/bin/env python3
"""
Stochastic Circuit Synthesizer — Binary Probability Edition
============================================================
EE 5393 (Circuits, Computation and Biology) — HW #1 Problem 2(b)

Source: S = {0.5} only.
Gates:  AND (p·q),  NOT (1−p),  OR via De Morgan: NOT(AND(NOT(a),NOT(b)))

KEY INSIGHT — the COMPARATOR METHOD
-------------------------------------
Any n-bit binary fraction  T = 0.b₁b₂...bₙ  (base 2)  =  B / 2ⁿ
can be implemented EXACTLY using n independent 0.5 streams X₁…Xₙ.

Treat the n streams as a random integer X ~ Uniform{0, 1, …, 2ⁿ−1}.
Build the Boolean comparator:  output = 1  iff  X < B.

Then:  P(output = 1) = B / 2ⁿ = T   ✓  (exact, by construction)

Comparator circuit  less(X[i..n], b[i..n]):
  b[i] == '1':  NOT(X[i])  OR  (X[i] AND less(X[i+1..n], b[i+1..n]))
  b[i] == '0':  NOT(X[i])  AND  less(X[i+1..n], b[i+1..n])
  base case  :  constant 0  (X == B → not strictly less)

OR(a,b) = NOT(AND(NOT(a), NOT(b)))  — only AND + NOT needed.

IMPORTANT: signals can share input bits, so probabilities are computed
using TRUTH TABLES (exhaustive evaluation over all 2ⁿ inputs), NOT the
independence formula p·q.
"""

from fractions import Fraction
from typing    import List, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Wire: Boolean function stored as a truth table
# ─────────────────────────────────────────────────────────────────────────────

class Wire:
    """
    A signal in the circuit.
    truth_table[i] = output bit when the n inputs have the binary
    representation of i (i.e. input pattern i).
    """
    _ctr = 0

    def __init__(self, name: str, table: List[int], op: str = "",
                 inputs: list = None):
        self.name   = name
        self.table  = table                                # list of 0/1
        self.op     = op
        self.inputs = inputs or []
        self.prob   = Fraction(sum(table), len(table))

    def __repr__(self):
        return f"{self.name}(p={float(self.prob):.7f})"


def input_wire(idx: int, n: int) -> Wire:
    """
    The i-th input (0-indexed) for an n-input circuit.
    Bit i of the pattern number determines its value.
    Bit 0 is the MOST significant (first stream = highest-order bit).
    """
    Wire._ctr += 1
    table = [(pattern >> (n - 1 - idx)) & 1 for pattern in range(2**n)]
    return Wire(f"X{idx+1}", table, "INPUT")


def const_zero(n: int) -> Wire:
    return Wire("ZERO", [0] * 2**n, "CONST0")

def make_not(w: Wire, ctr: list) -> Wire:
    ctr[0] += 1
    table = [1 - b for b in w.table]
    return Wire(f"w{ctr[0]}", table, "NOT", [w])

def make_and(a: Wire, b: Wire, ctr: list) -> Wire:
    ctr[0] += 1
    table = [x & y for x, y in zip(a.table, b.table)]
    return Wire(f"w{ctr[0]}", table, "AND", [a, b])

def make_or(a: Wire, b: Wire, ctr: list) -> Wire:
    """OR via De Morgan: NOT(AND(NOT(a), NOT(b)))."""
    na   = make_not(a, ctr)
    nb   = make_not(b, ctr)
    nand = make_and(na, nb, ctr)
    return make_not(nand, ctr)


# ─────────────────────────────────────────────────────────────────────────────
# Comparator builder
# ─────────────────────────────────────────────────────────────────────────────

def build_comparator(bits: str) -> Tuple[Wire, List[Wire], int]:
    """
    Build output = 1 iff (X₁X₂…Xₙ)₂ < int(bits, 2).
    Returns (output_wire, input_wires, total_gate_count).
    """
    n   = len(bits)
    ctr = [0]
    X   = [input_wire(i, n) for i in range(n)]

    def less(i: int) -> Wire:
        if i == n:
            return const_zero(n)
        bit    = bits[i]
        rest   = less(i + 1)
        xi     = X[i]
        not_xi = make_not(xi, ctr)

        if bit == "0":
            if rest.op == "CONST0":
                return const_zero(n)
            return make_and(not_xi, rest, ctr)
        else:  # bit == "1"
            if rest.op == "CONST0":
                return not_xi
            xi_and_rest = make_and(xi, rest, ctr)
            return make_or(not_xi, xi_and_rest, ctr)

    output = less(0)
    return output, X, ctr[0]


# ─────────────────────────────────────────────────────────────────────────────
# Topological sort (for printing in order)
# ─────────────────────────────────────────────────────────────────────────────

def topo_sort(root: Wire) -> List[Wire]:
    order, visited = [], set()
    def visit(w):
        if id(w) in visited: return
        visited.add(id(w))
        for inp in w.inputs: visit(inp)
        order.append(w)
    visit(root)
    return order


# ─────────────────────────────────────────────────────────────────────────────
# Pretty printer
# ─────────────────────────────────────────────────────────────────────────────

LINE = 74

def print_circuit(bits: str) -> None:
    n        = len(bits)
    B        = int(bits, 2)
    target   = Fraction(B, 2**n)
    target_f = float(target)

    print(f"\n{'='*LINE}")
    print(f"  TARGET (binary)  :  0.{bits}_2")
    print(f"  TARGET (decimal) :  {target_f:.10f}  =  {target}")
    print(f"  SOURCE           :  {{ 0.5 }}  ({n} independent streams)")
    print(f"{'─'*LINE}")

    output, inputs, n_gates = build_comparator(bits)

    assert output.prob == target, \
        f"BUG: got {output.prob} expected {target}"

    # Gate breakdown
    all_wires = topo_sort(output)
    and_gates = [w for w in all_wires if w.op == "AND"]
    not_gates = [w for w in all_wires if w.op == "NOT"]

    print(f"  METHOD           :  Comparator  (X < {B},  X ~ Uniform{{0..{2**n-1}}})")
    print(f"  RESULT           :  P(output=1) = {output.prob} = {target_f:.10f}  ✓ EXACT")
    print(f"  GATES            :  {len(and_gates)} AND  +  {len(not_gates)} NOT  "
          f"(OR = NOT·AND·NOT·NOT  each = 3 gates)")

    # Binary decomposition
    one_pos = [i+1 for i,b in enumerate(bits) if b=='1']
    terms   = [f"1/2^{p}" for p in one_pos]
    print(f"\n  Binary decomp    :  0.{bits}_2")
    print(f"                    = " + " + ".join(terms))
    print(f"                    = " + " + ".join(str(Fraction(1,2**p)) for p in one_pos))

    # Comparator logic explanation
    print(f"\n  Comparator logic :  output = 1  iff  X₁X₂...X{n} (as integer) < {B}")
    for i, b in enumerate(bits):
        indent = "  " * i
        if b == "1":
            print(f"    Bit {i+1} (b={b}):  NOT(X{i+1}) OR  (X{i+1} AND [recurse on bits {i+2}..{n}])")
        else:
            print(f"    Bit {i+1} (b={b}):  NOT(X{i+1}) AND [recurse on bits {i+2}..{n}]")

    # Circuit equations
    print(f"\n{'─'*LINE}")
    print(f"  CIRCUIT EQUATIONS  (inputs X1..X{n}, each p=0.5, independent)")
    print(f"{'─'*LINE}")
    seen_names = set()
    for w in all_wires:
        if w.name in seen_names or w.op == "CONST0":
            continue
        seen_names.add(w.name)
        p_str = f"p={float(w.prob):.7f}"
        if w.op == "INPUT":
            print(f"  {w.name:<8} INPUT                     {p_str}")
        elif w.op == "NOT":
            print(f"  {w.name:<8} NOT  {w.inputs[0].name:<8}              {p_str}")
        elif w.op == "AND":
            print(f"  {w.name:<8} AND  {w.inputs[0].name:<6} , {w.inputs[1].name:<6}      {p_str}")
    print(f"{'─'*LINE}")
    print(f"  OUTPUT = {output.name}   =>   P(output=1) = {float(output.prob):.10f}")

    # Verification table (boundary rows)
    print(f"\n{'─'*LINE}")
    print(f"  VERIFICATION TABLE  (patterns near boundary B={B})")
    print(f"  {'X':>5}  {'bits':>{n+2}}  {'out':>4}  {'< B?':>5}")
    print(f"  {'─'*5}  {'─'*(n+2)}  {'─'*4}  {'─'*5}")
    show = (list(range(min(3, B))) +
            list(range(max(0,B-2), min(B+2, 2**n))) +
            list(range(max(2**n-2, B+1), 2**n)))
    show = sorted(set(show))
    prev = -1
    for x in show:
        if x > prev + 1 and prev >= 0:
            print(f"  {'...':>5}  {'...':>{n+2}}  {'...':>4}  {'...':>5}")
        bstr = format(x, f'0{n}b')
        out  = output.table[x]
        lt   = "YES" if x < B else "no"
        mark = " <-- boundary" if abs(x - B) <= 1 else ""
        print(f"  {x:>5}  {bstr:>{n+2}}  {out:>4}  {lt:>5}{mark}")
        prev = x

    total_ones = sum(output.table)
    print(f"{'─'*LINE}")
    print(f"  Total 1-outputs: {total_ones} / {2**n} = {Fraction(total_ones,2**n)} = {float(Fraction(total_ones,2**n)):.7f}  ✓")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * LINE)
    print("  Stochastic Circuit Synthesizer  --  EE 5393 HW #1 Problem 2(b)")
    print("  Method : COMPARATOR (X < B using n fair-coin streams)")
    print("  Gates  : AND and NOT only  (OR via De Morgan)")
    print("  Source : {0.5} only  |  All results EXACT by construction")
    print("=" * LINE)

    hw_targets = [
        ("i",   "1011111"),
        ("ii",  "1101111"),
        ("iii", "1010111"),
    ]

    for label, b in hw_targets:
        print(f"\n{'─'*LINE}")
        print(f"  PROBLEM 2(b)-{label}:  0.{b}_2")
        print_circuit(b)

    # Interactive mode
    print(f"\n{'='*LINE}")
    print("  Interactive — enter a binary fraction (e.g. '1011' or '0.1011')")
    print("  Type 'quit' to exit.")
    print("=" * LINE)
    while True:
        try:
            raw = input("\n  Binary string: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if raw.lower() in ("quit", "exit", "q", ""):
            break
        bits = raw.lstrip("0").lstrip(".").strip()
        if not bits or not all(c in "01" for c in bits):
            print("  Please enter only 0s and 1s")
            continue
        try:
            print_circuit(bits)
        except AssertionError as e:
            print(f"  Internal error: {e}")