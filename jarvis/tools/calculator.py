"""Safe math expression evaluator and unit converter for Jarvis.

Uses Python's ast module to evaluate expressions without calling eval() directly,
allowing only numeric literals, arithmetic operators, and a curated set of math
functions. No imports, attribute access, or function calls beyond the whitelist
are permitted.
"""
import ast
import math
import operator

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCS = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sqrt": math.sqrt, "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan, "atan2": math.atan2,
    "log": math.log, "log2": math.log2, "log10": math.log10,
    "exp": math.exp, "floor": math.floor, "ceil": math.ceil,
    "degrees": math.degrees, "radians": math.radians,
    "factorial": math.factorial, "gcd": math.gcd,
    "hypot": math.hypot,
}

_SAFE_CONSTS = {
    "pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf,
}


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, complex)):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in _SAFE_CONSTS:
            return _SAFE_CONSTS[node.id]
        raise ValueError(f"Variable no permitida: '{node.id}'")
    if isinstance(node, ast.BinOp):
        op = _SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Operador no soportado: {type(node.op).__name__}")
        return op(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Operador unario no soportado: {type(node.op).__name__}")
        return op(_eval_node(node.operand))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _SAFE_FUNCS:
            fname = getattr(node.func, "id", "?")
            raise ValueError(f"Función no permitida: '{fname}'")
        args = [_eval_node(a) for a in node.args]
        return _SAFE_FUNCS[node.func.id](*args)
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(e) for e in node.elts)
    raise ValueError(f"Expresión no soportada: {type(node).__name__}")


def calculate(expression: str) -> str:
    """Evaluate a math expression safely. Supports +−×÷^, functions like sqrt/sin/log, and constants pi/e."""
    expr = (expression or "").strip()
    # Normalise common alternatives
    expr = expr.replace("×", "*").replace("÷", "/").replace("^", "**")

    if not expr:
        return "Indica una expresión matemática. Ej: 2 + 3 * 4, sqrt(144), sin(pi/2)"

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        return f"Expresión inválida: {exc}"

    try:
        result = _eval_node(tree)
    except (ValueError, ZeroDivisionError, OverflowError, TypeError) as exc:
        return f"Error de cálculo: {exc}"

    # Pretty-print result
    if isinstance(result, complex):
        return f"{expr} = {result}"
    if isinstance(result, float):
        if result == int(result) and abs(result) < 1e15:
            return f"{expr} = {int(result)}"
        return f"{expr} = {result:.10g}"
    return f"{expr} = {result}"


# ---------------------------------------------------------------------------
# Unit converter
# ---------------------------------------------------------------------------

_UNITS: dict[str, dict[str, float]] = {
    # Length — base: metre
    "length": {
        "m": 1, "metro": 1, "metros": 1,
        "km": 1e3, "kilómetro": 1e3, "kilómetros": 1e3,
        "cm": 1e-2, "centímetro": 1e-2, "centímetros": 1e-2,
        "mm": 1e-3, "milímetro": 1e-3, "milímetros": 1e-3,
        "mi": 1609.344, "milla": 1609.344, "millas": 1609.344,
        "yd": 0.9144, "yarda": 0.9144, "yardas": 0.9144,
        "ft": 0.3048, "pie": 0.3048, "pies": 0.3048, "foot": 0.3048, "feet": 0.3048,
        "in": 0.0254, "pulgada": 0.0254, "pulgadas": 0.0254, "inch": 0.0254, "inches": 0.0254,
        "nm": 1852, "nmi": 1852,
    },
    # Mass — base: kilogram
    "mass": {
        "kg": 1, "kilogramo": 1, "kilogramos": 1,
        "g": 1e-3, "gramo": 1e-3, "gramos": 1e-3,
        "mg": 1e-6, "miligramo": 1e-6, "miligramos": 1e-6,
        "lb": 0.453592, "libra": 0.453592, "libras": 0.453592, "lbs": 0.453592,
        "oz": 0.0283495, "onza": 0.0283495, "onzas": 0.0283495,
        "t": 1e3, "tonelada": 1e3, "toneladas": 1e3,
    },
    # Temperature — handled separately via formulas
    # Speed — base: m/s
    "speed": {
        "m/s": 1, "metros/s": 1,
        "km/h": 1 / 3.6, "kmh": 1 / 3.6, "kph": 1 / 3.6,
        "mph": 0.44704, "millas/h": 0.44704,
        "kt": 0.514444, "nudo": 0.514444, "nudos": 0.514444, "knot": 0.514444, "knots": 0.514444,
    },
    # Area — base: m²
    "area": {
        "m2": 1, "m²": 1,
        "km2": 1e6, "km²": 1e6,
        "cm2": 1e-4, "cm²": 1e-4,
        "ha": 1e4, "hectárea": 1e4, "hectáreas": 1e4,
        "acre": 4046.86, "acres": 4046.86,
        "ft2": 0.092903, "ft²": 0.092903,
        "in2": 6.4516e-4, "in²": 6.4516e-4,
        "mi2": 2.59e6, "mi²": 2.59e6,
    },
    # Volume — base: litre
    "volume": {
        "l": 1, "litro": 1, "litros": 1, "L": 1,
        "ml": 1e-3, "mililitro": 1e-3, "mililitros": 1e-3,
        "m3": 1e3, "m³": 1e3,
        "gal": 3.78541, "galón": 3.78541, "galones": 3.78541, "gallon": 3.78541, "gallons": 3.78541,
        "qt": 0.946353, "cuarto": 0.946353,
        "pt": 0.473176, "pinta": 0.473176, "pintas": 0.473176,
        "cup": 0.236588, "taza": 0.236588, "tazas": 0.236588,
        "fl oz": 0.0295735, "fl_oz": 0.0295735,
    },
    # Digital storage — base: byte
    "storage": {
        "b": 1, "byte": 1, "bytes": 1,
        "kb": 1024, "kilobyte": 1024, "kilobytes": 1024,
        "mb": 1024**2, "megabyte": 1024**2, "megabytes": 1024**2,
        "gb": 1024**3, "gigabyte": 1024**3, "gigabytes": 1024**3,
        "tb": 1024**4, "terabyte": 1024**4, "terabytes": 1024**4,
        "pb": 1024**5, "petabyte": 1024**5, "petabytes": 1024**5,
        "kib": 1024, "mib": 1024**2, "gib": 1024**3, "tib": 1024**4,
    },
}


def _find_category(unit: str) -> tuple[str, dict]:
    u = unit.strip().lower()
    for cat, units in _UNITS.items():
        if u in units:
            return cat, units
    return "", {}


def _convert_temperature(value: float, from_u: str, to_u: str) -> str:
    _aliases = {
        "c": "c", "celsius": "c", "°c": "c",
        "f": "f", "fahrenheit": "f", "°f": "f",
        "k": "k", "kelvin": "k",
    }
    fu = _aliases.get(from_u.lower().strip())
    tu = _aliases.get(to_u.lower().strip())
    if fu is None or tu is None:
        return ""

    # Convert to Celsius first
    if fu == "c":
        c = value
    elif fu == "f":
        c = (value - 32) * 5 / 9
    else:  # kelvin
        c = value - 273.15

    # Convert from Celsius to target
    if tu == "c":
        result = c
    elif tu == "f":
        result = c * 9 / 5 + 32
    else:  # kelvin
        result = c + 273.15

    return f"{value} {from_u} = {result:.4g} {to_u}"


def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Convert *value* from *from_unit* to *to_unit*."""
    try:
        val = float(value)
    except (TypeError, ValueError):
        return f"Valor inválido: '{value}'."

    # Try temperature first (special formulas)
    temp_result = _convert_temperature(val, from_unit, to_unit)
    if temp_result:
        return temp_result

    cat_from, units_from = _find_category(from_unit)
    cat_to, units_to = _find_category(to_unit)

    if not cat_from:
        return f"Unidad no reconocida: '{from_unit}'."
    if not cat_to:
        return f"Unidad no reconocida: '{to_unit}'."
    if cat_from != cat_to:
        return f"No se puede convertir {cat_from} a {cat_to}."

    base = val * units_from[from_unit.strip().lower()]
    result = base / units_to[to_unit.strip().lower()]

    if result == int(result) and abs(result) < 1e12:
        result_str = str(int(result))
    else:
        result_str = f"{result:.6g}"

    return f"{val} {from_unit} = {result_str} {to_unit}"
