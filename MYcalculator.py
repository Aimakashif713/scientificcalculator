"""
Scientific Calculator - Streamlit App
======================================
A scientific calculator that works with BOTH:
  - Keyboard: type directly into the expression box and press Enter
  - Mouse: click the on-screen buttons (digits, operators, functions)

Run with:
    streamlit run scientific_calculator.py
"""

import math
import streamlit as st

# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(page_title="Aima's calculator", page_icon="S🧮", layout="centered")

st.markdown(
    """
    <style>
    div.stButton > button {
        width: 100%;
        height: 3em;
        font-size: 18px;
        font-weight: 600;
        border-radius: 10px;
    }
    .calc-display input {
        font-size: 26px !important;
        text-align: right;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧮 Scientific Calculator")
st.caption("Type with your keyboard and press **Enter**, or click the buttons with your mouse.")

# ----------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------
if "expression" not in st.session_state:
    st.session_state.expression = ""
if "result" not in st.session_state:
    st.session_state.result = ""
if "angle_mode" not in st.session_state:
    st.session_state.angle_mode = "Radians"
if "history" not in st.session_state:
    st.session_state.history = []


# ----------------------------------------------------------------------
# Safe evaluation engine
# ----------------------------------------------------------------------
def build_safe_namespace(angle_mode: str) -> dict:
    """Build a restricted namespace exposing only safe math functions/constants."""

    def deg_wrap(fn):
        return lambda x: fn(math.radians(x))

    def deg_unwrap(fn):
        return lambda x: math.degrees(fn(x))

    if angle_mode == "Degrees":
        sin_, cos_, tan_ = deg_wrap(math.sin), deg_wrap(math.cos), deg_wrap(math.tan)
        asin_, acos_, atan_ = deg_unwrap(math.asin), deg_unwrap(math.acos), deg_unwrap(math.atan)
    else:
        sin_, cos_, tan_ = math.sin, math.cos, math.tan
        asin_, acos_, atan_ = math.asin, math.acos, math.atan

    safe_dict = {
        # trig
        "sin": sin_, "cos": cos_, "tan": tan_,
        "asin": asin_, "acos": acos_, "atan": atan_,
        # hyperbolic
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        # logs / exponent
        "log": math.log10, "ln": math.log, "exp": math.exp,
        "sqrt": math.sqrt, "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
        "pow": math.pow,
        # misc
        "abs": abs, "fabs": math.fabs, "factorial": math.factorial,
        "floor": math.floor, "ceil": math.ceil, "round": round,
        # constants
        "pi": math.pi, "e": math.e, "tau": math.tau,
    }
    # block builtins entirely
    safe_dict["__builtins__"] = {}
    return safe_dict


def preprocess(expr: str) -> str:
    """Translate calculator-friendly notation into valid Python syntax."""
    expr = expr.replace("×", "*").replace("÷", "/").replace("^", "**")
    expr = expr.replace("π", "pi").replace("√", "sqrt")
    expr = expr.replace("%", "/100")
    return expr


def evaluate_expression(expr: str, angle_mode: str):
    """Safely evaluate the expression string, returning (result, error)."""
    if not expr.strip():
        return None, None
    try:
        clean_expr = preprocess(expr)
        namespace = build_safe_namespace(angle_mode)
        value = eval(clean_expr, {"__builtins__": {}}, namespace)  # noqa: S307 (restricted namespace)
        return value, None
    except ZeroDivisionError:
        return None, "Error: Division by zero"
    except Exception as exc:  # noqa: BLE001
        return None, f"Error: {exc}"


# ----------------------------------------------------------------------
# Callbacks
# ----------------------------------------------------------------------
def calculate():
    """Triggered by pressing Enter in the text box OR clicking '='."""
    expr = st.session_state.expression
    value, error = evaluate_expression(expr, st.session_state.angle_mode)
    if error:
        st.session_state.result = error
    elif value is not None:
        st.session_state.result = str(value)
        st.session_state.history.insert(0, f"{expr} = {value}")
        st.session_state.history = st.session_state.history[:8]


def append_token(token: str):
    st.session_state.expression += token


def clear_all():
    st.session_state.expression = ""
    st.session_state.result = ""


def backspace():
    st.session_state.expression = st.session_state.expression[:-1]


def use_last_result():
    if st.session_state.result and not st.session_state.result.startswith("Error"):
        st.session_state.expression += st.session_state.result


# ----------------------------------------------------------------------
# Display: keyboard-enabled input box (press Enter to calculate)
# ----------------------------------------------------------------------
st.text_input(
    "Expression (type here and press Enter)",
    key="expression",
    on_change=calculate,
    placeholder="e.g. sin(30) + sqrt(16) * 2",
    label_visibility="collapsed",
)

if st.session_state.result:
    st.markdown(
        f"<div style='text-align:right; font-size:28px; font-weight:bold; "
        f"padding:8px; background:#f0f2f6; border-radius:8px;'>= {st.session_state.result}</div>",
        unsafe_allow_html=True,
    )

st.write("")

# ----------------------------------------------------------------------
# Options row: angle mode + explicit Enter/Calculate button
# ----------------------------------------------------------------------
opt1, opt2, opt3 = st.columns([1.3, 1, 1])
with opt1:
    st.selectbox("Angle mode", ["Radians", "Degrees"], key="angle_mode")
with opt2:
    st.button("↵ Enter / Calculate", on_click=calculate, use_container_width=True, type="primary")
with opt3:
    st.button("Use result (Ans)", on_click=use_last_result, use_container_width=True)

st.write("")

# ----------------------------------------------------------------------
# Mouse-clickable button grid
# ----------------------------------------------------------------------
# Each row: list of (label, token_to_append) -- token=None means special action
rows = [
    [("sin(", "sin("), ("cos(", "cos("), ("tan(", "tan("), ("π", "π"), ("e", "e")],
    [("asin(", "asin("), ("acos(", "acos("), ("atan(", "atan("), ("log(", "log("), ("ln(", "ln(")],
    [("(", "("), (")", ")"), ("√(", "√("), ("^", "^"), ("!", "factorial(")],
    [("7", "7"), ("8", "8"), ("9", "9"), ("÷", "÷"), ("C", "CLEAR")],
    [("4", "4"), ("5", "5"), ("6", "6"), ("×", "×"), ("⌫", "BACKSPACE")],
    [("1", "1"), ("2", "2"), ("3", "3"), ("-", "-"), ("%", "%")],
    [("0", "0"), (".", "."), ("Ans", "ANS"), ("+", "+"), ("=", "EQUALS")],
]

for row in rows:
    cols = st.columns(len(row))
    for col, (label, token) in zip(cols, row):
        with col:
            if token == "CLEAR":
                st.button(label, on_click=clear_all, key=f"btn_{label}_{id(row)}", use_container_width=True)
            elif token == "BACKSPACE":
                st.button(label, on_click=backspace, key=f"btn_{label}_{id(row)}", use_container_width=True)
            elif token == "EQUALS":
                st.button(label, on_click=calculate, key=f"btn_{label}_{id(row)}", use_container_width=True, type="primary")
            elif token == "ANS":
                st.button(label, on_click=use_last_result, key=f"btn_{label}_{id(row)}", use_container_width=True)
            else:
                st.button(
                    label,
                    on_click=append_token,
                    args=(token,),
                    key=f"btn_{label}_{id(row)}",
                    use_container_width=True,
                )

st.write("")

# ----------------------------------------------------------------------
# History
# ----------------------------------------------------------------------
with st.expander("🕘 History", expanded=False):
    if st.session_state.history:
        for item in st.session_state.history:
            st.write(item)
        st.button("Clear history", on_click=lambda: st.session_state.history.clear())
    else:
        st.write("No calculations yet.")

st.divider()
st.caption(
    "Tips: Use `^` for power, `√(` for square root, `!` for factorial, `π` and `e` for constants. "
    "Type directly in the box and hit **Enter**, or use the buttons below."
)
