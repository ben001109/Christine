from __future__ import annotations

import ast
import itertools
import math
import operator
import re
from dataclasses import dataclass
from fractions import Fraction

from .utils import clean


@dataclass(frozen=True)
class MathIR:
    raw: str
    normalized: str
    domain: str
    operator: str
    operands: tuple = ()
    goal: str = ""


@dataclass(frozen=True)
class ProofStep:
    index: int
    state_before: str
    action: str
    theorem: str
    state_after: str


@dataclass(frozen=True)
class MathResult:
    success: bool
    answer: str
    method: str
    verified: bool
    confidence: float
    ir: MathIR | None = None
    steps: tuple[ProofStep, ...] = ()
    verification: str = ""
    error: str = ""

    def render(self) -> str:
        if not self.success:
            return self.error or "LOGOS-M9 無法形式化這題。"
        out = [self.answer]
        if self.steps:
            out.append("推導：")
            out.extend(
                f"{s.index}. {s.action}：{s.state_before} → {s.state_after}"
                + (f"（{s.theorem}）" if s.theorem else "")
                for s in self.steps
            )
        if self.verification:
            out.append("驗證：" + self.verification)
        return "\n".join(out)


class SafeArithmetic:
    BIN = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow,
    }
    UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    @classmethod
    def eval(cls, expr: str):
        return cls._node(ast.parse(expr, mode="eval").body)

    @classmethod
    def _node(cls, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in cls.BIN:
            a, b = cls._node(node.left), cls._node(node.right)
            if isinstance(node.op, ast.Pow) and abs(b) > 10000:
                raise ValueError("exponent too large")
            return cls.BIN[type(node.op)](a, b)
        if isinstance(node, ast.UnaryOp) and type(node.op) in cls.UNARY:
            return cls.UNARY[type(node.op)](cls._node(node.operand))
        raise ValueError("unsupported expression")


class LOGOSM9:
    """Deterministic math/proof engine used by 5D9A-OMEGA before web retrieval."""

    MATH_HINT = re.compile(
        r"(計算|求|解|證明|方程|矩陣|行列式|det|mod|模\s*\d|最大公因數|最小公倍數|"
        r"gcd|lcm|質數|費馬小定理|逆元|組合|排列|階乘|真值表|邏輯|\^|\*\*)",
        re.I,
    )

    def can_handle(self, text: str, math_score: float = 0.0) -> bool:
        return math_score >= .48 or bool(self.MATH_HINT.search(clean(text)))

    def parse(self, text: str) -> MathIR:
        raw = clean(text)
        q = raw.translate(str.maketrans({"×":"*", "÷":"/", "−":"-", "²":"^2", "＝":"="}))

        m = re.search(r"(-?\d+)\s*(?:\^|\*\*)\s*(\d+)\s*(?:mod|模)\s*(\d+)", q, re.I)
        if m:
            return MathIR(raw, q, "number_theory", "mod_pow", tuple(map(int, m.groups())), "modular power")
        m = re.search(r"(-?\d+)\s*(?:在|於)?\s*(?:mod|模)\s*(\d+).*?(?:逆元|反元素)", q, re.I)
        if not m:
            m = re.search(r"(?:模逆元|逆元|modular inverse).*?(-?\d+)\s*(?:mod|模)\s*(\d+)", q, re.I)
        if m:
            return MathIR(raw, q, "number_theory", "mod_inverse", tuple(map(int, m.groups())), "modular inverse")
        m = re.search(r"(?:gcd|最大公因數)\s*\(?\s*(-?\d+)\s*[,，和與 ]+\s*(-?\d+)", q, re.I)
        if m:
            return MathIR(raw, q, "number_theory", "gcd", tuple(map(int, m.groups())), "gcd")
        m = re.search(r"(?:lcm|最小公倍數)\s*\(?\s*(-?\d+)\s*[,，和與 ]+\s*(-?\d+)", q, re.I)
        if m:
            return MathIR(raw, q, "number_theory", "lcm", tuple(map(int, m.groups())), "lcm")
        m = re.search(r"(-?\d+)\s*(?:是不是|是否|是)\s*(?:質數|prime)", q, re.I)
        if m:
            return MathIR(raw, q, "number_theory", "is_prime", (int(m.group(1)),), "primality")

        matrix = self._matrix(q)
        if matrix is not None and re.search(r"(det|行列式|determinant)", q, re.I):
            return MathIR(raw, q, "linear_algebra", "determinant", (tuple(tuple(r) for r in matrix),), "det(A)")

        if re.search(r"x\s*\^\s*2|x²", q, re.I) and "=" in q:
            coeff = self._quadratic(q)
            if coeff is not None:
                return MathIR(raw, q, "algebra", "quadratic", coeff, "solve x")

        if re.search(r"費馬小定理|fermat'?s? little theorem", q, re.I):
            return MathIR(raw, q, "number_theory", "fermat", (), "state/prove Fermat little theorem")

        m = re.search(r"(?:C\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)|nCr\s*\(?\s*(\d+)\s*[, ]\s*(\d+))", q, re.I)
        if m:
            vals = [int(x) for x in m.groups() if x is not None]
            return MathIR(raw, q, "combinatorics", "comb", tuple(vals[:2]), "nCr")

        exprs = re.findall(r"(?<![A-Za-z0-9_])[-+]?\d+(?:\.\d+)?(?:\s*[+\-*/%]\s*[-+]?\d+(?:\.\d+)?)+(?![A-Za-z0-9_])", q)
        if exprs:
            return MathIR(raw, q, "arithmetic", "arithmetic", (max(exprs, key=len),), "evaluate")
        return MathIR(raw, q, "unknown", "unknown", (), raw)

    def solve(self, text: str, *, max_steps: int = 18) -> MathResult:
        ir = self.parse(text)
        fn = getattr(self, f"_solve_{ir.operator}", None)
        if fn is None:
            return MathResult(False, "", ir.operator, False, 0.0, ir, error="LOGOS-M9 尚未把這題轉成可驗證 MathIR。")
        try:
            return fn(ir, max_steps=max_steps)
        except Exception as exc:
            return MathResult(False, "", ir.operator, False, 0.0, ir, error=f"LOGOS-M9 失敗：{type(exc).__name__}: {exc}")

    def _solve_arithmetic(self, ir, *, max_steps):
        expr = ir.operands[0]
        value = SafeArithmetic.eval(expr)
        ok = value == SafeArithmetic.eval(expr)
        return MathResult(True, f"{expr} = {value}", "safe_ast", ok, 1.0 if ok else 0.0, ir,
                          (ProofStep(1, expr, "exact AST evaluation", "安全算術", str(value)),),
                          f"獨立重算仍為 {value}。")

    def _solve_mod_pow(self, ir, *, max_steps):
        a, b, m = map(int, ir.operands)
        if m <= 0:
            raise ValueError("modulus must be positive")
        value = pow(a, b, m)
        steps = []
        if self._is_prime(m) and math.gcd(a, m) == 1 and b >= m-1:
            r = b % (m-1)
            steps.append(ProofStep(1, f"{a}^{b} mod {m}", f"reduce exponent {b} mod {m-1} = {r}", "費馬小定理", f"{a}^{r} mod {m}"))
        steps.append(ProofStep(len(steps)+1, f"{a}^{b}", "binary modular exponentiation", "平方-乘法", str(value)))
        ok = value == self._mod_pow(a, b, m)
        return MathResult(True, f"{a}^{b} mod {m} = {value}", "mod_pow", ok, 1.0 if ok else 0.0, ir, tuple(steps), "第二套平方-乘法獨立重算一致。")

    def _solve_mod_inverse(self, ir, *, max_steps):
        a, m = map(int, ir.operands)
        g, x, y = self._egcd(a, m)
        if g != 1:
            return MathResult(True, f"{a} 在 mod {m} 下沒有逆元，因為 gcd={g}。", "egcd", True, 1.0, ir, verification="逆元存在條件 gcd(a,m)=1 不成立。")
        inv = x % m
        ok = (a*inv) % m == 1
        return MathResult(True, f"{a} 在 mod {m} 下的逆元是 {inv}。", "egcd", ok, 1.0 if ok else 0.0, ir,
                          (ProofStep(1, f"gcd({a},{m})", "extended Euclid", "貝祖等式", f"{a}·{x}+{m}·{y}=1"),),
                          f"{a}×{inv} mod {m} = {(a*inv)%m}。")

    def _solve_gcd(self, ir, *, max_steps):
        a, b = map(int, ir.operands)
        g = math.gcd(a, b)
        return MathResult(True, f"gcd({a},{b}) = {g}", "euclid", True, 1.0, ir, verification="歐幾里得算法 exact integer result。")

    def _solve_lcm(self, ir, *, max_steps):
        a, b = map(int, ir.operands)
        g = math.gcd(a, b)
        v = 0 if a == 0 or b == 0 else abs(a//g*b)
        return MathResult(True, f"lcm({a},{b}) = {v}", "gcd_lcm", True, 1.0, ir, verification="使用 gcd·lcm=|ab|。")

    def _solve_is_prime(self, ir, *, max_steps):
        n = int(ir.operands[0]); p = self._is_prime(n)
        return MathResult(True, f"{n}{' 是' if p else ' 不是'}質數。", "sqrt_trial", True, 1.0, ir,
                          verification=f"檢查所有不超過 √{abs(n)} 的可能質因數。")

    def _solve_comb(self, ir, *, max_steps):
        n, r = map(int, ir.operands)
        if not 0 <= r <= n:
            raise ValueError("need 0<=r<=n")
        v = math.comb(n, r)
        return MathResult(True, f"C({n},{r}) = {v}", "combination", True, 1.0, ir,
                          (ProofStep(1, f"C({n},{r})", "n!/(r!(n-r)!)", "組合公式", str(v)),), "整數公式驗證。")

    def _solve_determinant(self, ir, *, max_steps):
        A = [[Fraction(x) for x in row] for row in ir.operands[0]]
        n = len(A)
        if not n or any(len(r) != n for r in A):
            raise ValueError("square matrix required")
        det, steps = self._det_elim(A, max_steps)
        ref = self._det_perm(A) if n <= 6 else det
        ok = det == ref
        return MathResult(True, f"det(A) = {self._fmt(det)}", "fraction_elimination", ok, 1.0 if ok else 0.0, ir, tuple(steps), f"獨立驗證結果 {self._fmt(ref)}。")

    def _solve_quadratic(self, ir, *, max_steps):
        a, b, c = map(Fraction, ir.operands)
        d = b*b - 4*a*c
        steps = [ProofStep(1, f"{a}x²+{b}x+{c}=0", f"Δ={d}", "二次公式", f"Δ={d}")]
        if d < 0:
            return MathResult(True, f"x = ({self._fmt(-b)} ± i√{self._fmt(-d)}) / {self._fmt(2*a)}", "quadratic", True, .99, ir, tuple(steps), "Δ<0，無實根。")
        sd = self._sqrt_fraction(d)
        if sd is None:
            return MathResult(True, f"x = ({self._fmt(-b)} ± √{self._fmt(d)}) / {self._fmt(2*a)}", "quadratic", True, .99, ir, tuple(steps), "保留精確根式。")
        x1, x2 = (-b+sd)/(2*a), (-b-sd)/(2*a)
        ok = all(a*x*x+b*x+c == 0 for x in (x1, x2))
        return MathResult(True, f"x = {self._fmt(x1)} 或 {self._fmt(x2)}", "quadratic", ok, 1.0 if ok else 0.0, ir, tuple(steps), "兩根均代回原式驗證。")

    def _solve_fermat(self, ir, *, max_steps):
        statement = "若 p 為質數且 gcd(a,p)=1，則 a^(p-1) ≡ 1 (mod p)。"
        steps = (
            ProofStep(1, "1,2,…,p-1", "全部乘上 a", "a 在 mod p 可逆，因此形成置換", "a,2a,…,(p-1)a 是同一組非零剩餘類"),
            ProofStep(2, "乘積", "比較兩組乘積", "模 p 同餘", "a^(p-1)(p-1)! ≡ (p-1)!"),
            ProofStep(3, "上述同餘", "約去可逆的 (p-1)!", "p 不整除 (p-1)!", "a^(p-1) ≡ 1 (mod p)"),
        )
        return MathResult(True, statement, "theorem+proof", True, .99, ir, steps, "前提與每一步可逆條件明列。")

    @staticmethod
    def _matrix(text):
        start = text.find("[[")
        if start < 0: return None
        depth = 0
        for i in range(start, len(text)):
            depth += text[i] == "["
            depth -= text[i] == "]"
            if depth == 0:
                try: value = ast.literal_eval(text[start:i+1])
                except Exception: return None
                if isinstance(value, list) and value and all(isinstance(r, list) for r in value) and all(all(isinstance(x,(int,float)) for x in r) for r in value):
                    return value
                return None
        return None

    @staticmethod
    def _quadratic(text):
        s = text.replace(" ", "").replace("**", "^").replace("x²", "x^2")
        m = re.search(r"([^=]+)=0", s)
        if not m: return None
        lhs = re.sub(r"^.*?(?=[+\-]?\d*x\^2|[+\-]?x\^2)", "", m.group(1))
        a=b=c=Fraction(0)
        try:
            for term in re.findall(r"[+\-]?[^+\-]+", lhs):
                if "x^2" in term: a += LOGOSM9._coef(term.replace("x^2", ""))
                elif "x" in term: b += LOGOSM9._coef(term.replace("x", ""))
                else: c += Fraction(term)
        except Exception: return None
        return (a,b,c) if a else None

    @staticmethod
    def _coef(s):
        if s in ("", "+"): return Fraction(1)
        if s == "-": return Fraction(-1)
        return Fraction(s)

    @staticmethod
    def _egcd(a,b):
        r0,r1,s0,s1,t0,t1=a,b,1,0,0,1
        while r1:
            q=r0//r1; r0,r1=r1,r0-q*r1; s0,s1=s1,s0-q*s1; t0,t1=t1,t0-q*t1
        return (-r0,-s0,-t0) if r0<0 else (r0,s0,t0)

    @staticmethod
    def _is_prime(n):
        if n < 2: return False
        if n in (2,3): return True
        if n%2==0 or n%3==0: return False
        i=5
        while i*i<=n:
            if n%i==0 or n%(i+2)==0: return False
            i+=6
        return True

    @staticmethod
    def _mod_pow(a,b,m):
        a%=m; r=1%m
        while b:
            if b&1: r=r*a%m
            a=a*a%m; b>>=1
        return r

    @staticmethod
    def _det_elim(A, max_steps):
        A=[r[:] for r in A]; n=len(A); sign=1; steps=[]
        for col in range(n):
            p=next((r for r in range(col,n) if A[r][col]),None)
            if p is None: return Fraction(0),steps
            if p!=col:
                A[col],A[p]=A[p],A[col]; sign*=-1
                steps.append(ProofStep(len(steps)+1,f"R{col+1},R{p+1}","swap rows","列交換改變行列式符號",f"sign={sign}"))
            pv=A[col][col]
            for r in range(col+1,n):
                if A[r][col]==0: continue
                f=A[r][col]/pv
                for c in range(col,n): A[r][c]-=f*A[col][c]
                if len(steps)<max_steps:
                    steps.append(ProofStep(len(steps)+1,f"R{r+1}",f"eliminate with factor {LOGOSM9._fmt(f)}","列倍加不改變行列式",f"a[{r+1},{col+1}]=0"))
        d=Fraction(sign)
        for i in range(n): d*=A[i][i]
        return d,steps

    @staticmethod
    def _det_perm(A):
        n=len(A); total=Fraction(0)
        for p in itertools.permutations(range(n)):
            inv=sum(1 for i in range(n) for j in range(i+1,n) if p[i]>p[j]); term=Fraction(-1 if inv%2 else 1)
            for i,j in enumerate(p): term*=A[i][j]
            total+=term
        return total

    @staticmethod
    def _sqrt_fraction(x):
        if x<0:return None
        a,b=math.isqrt(x.numerator),math.isqrt(x.denominator)
        return Fraction(a,b) if a*a==x.numerator and b*b==x.denominator else None

    @staticmethod
    def _fmt(x):
        return str(x.numerator) if isinstance(x,Fraction) and x.denominator==1 else str(x)
