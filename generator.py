"""Password generator: pure logic, uses the OS CSPRNG via `secrets`."""
import math, secrets

UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"
DIGITS = "0123456789"
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?"
AMBIGUOUS = set("O0Il1|")


def generate(length=20, upper=True, lower=True, digits=True, symbols=True,
             avoid_ambiguous=False) -> tuple[str, int]:
    """Return (password, entropy_bits). Guarantees one char from every enabled set."""
    pools = [p for p, on in ((UPPER, upper), (LOWER, lower), (DIGITS, digits), (SYMBOLS, symbols)) if on]
    if avoid_ambiguous:
        pools = ["".join(c for c in p if c not in AMBIGUOUS) for p in pools]
    if not pools:
        raise ValueError("Select at least one character type.")
    if not 8 <= length <= 128 or length < len(pools):
        raise ValueError("Invalid length.")
    alphabet = "".join(pools)
    chars = [secrets.choice(p) for p in pools]
    chars += [secrets.choice(alphabet) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars), int(length * math.log2(len(alphabet)))


def rate(bits: int) -> tuple[str, str]:
    if bits < 60:  return "Weak", "#dc2626"
    if bits < 80:  return "Fair", "#f59e0b"
    if bits < 110: return "Strong", "#16a34a"
    return "Excellent", "#16a34a"
