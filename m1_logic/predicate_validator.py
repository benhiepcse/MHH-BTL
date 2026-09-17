from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

@dataclass
class Error:
    line: int
    column: int
    message: str

    def __str__(self) -> str:
        return f"line {self.line}, column {self.column}: {self.message}"

FORMAT_COMMANDS = {
    r"\left", r"\right", r"\displaystyle", r"\textstyle",
    r"\big", r"\Big", r"\bigg", r"\Bigg",
}

BINARY_COMMANDS = {
    r"\land": "∧",
    r"\lor": "∨",
    r"\rightarrow": "→",
    r"\to": "→",
    r"\leftrightarrow": "↔",
    r"\iff": "↔",
    r"\ne": "!=",
    r"\neq": "!=",
    r"\leq": "≤",
    r"\le": "≤",
    r"\geq": "≥",
    r"\ge": "≥",
    r"\in": "∈",
    r"\notin": "∉",
}

BINARY_SYMBOLS = {
    "∧": "AND (∧)",
    "∨": "OR (∨)",
    "→": "implication (→)",
    "↔": "equivalence (↔)",
    "=": "equality (=)",
    "!=": "inequality (!=)",
    "≠": "inequality (≠)",
    # These are relation operators used in domain/formula syntax.
    "∈": "membership (∈)",
    "∉": "non-membership (∉)",
    "<": "less-than (<)",
    ">": "greater-than (>)",
    "≤": "less-than-or-equal (≤)",
    "≥": "greater-than-or-equal (≥)",
}

UNARY_COMMANDS = {
    r"\neg": "NOT (¬)",
    r"\lnot": "NOT (¬)",
}

UNARY_SYMBOLS = {
    "¬": "NOT (¬)",
}

QUANTIFIER_COMMANDS = {
    r"\forall": "∀",
    r"\exists": "∃",
}

QUANTIFIER_SYMBOLS = {"∀", "∃"}

OTHER_RELATIONS = {"∈", "∉", "<", ">", "≤", "≥"}

KNOWN_CALL_ARITY = {
    "Assign": 2,
    "Busy": 2,
    "Overlap": 2,
    "AtCampus": 2,
    "Prefer": 2,
    "r": 1,
    "duration": 1,
    "start": 1,
    "date": 1,
}

IDENTIFIER_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*"
)


def is_identifier(value: str) -> bool:
    """Return True when value has a valid variable/identifier form."""
    return bool(IDENTIFIER_RE.fullmatch(value))


def extract_math(text: str) -> list[tuple[int, int, str]]:
    results: list[tuple[int, int, str]] = []

    display_pattern = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
    inline_pattern = re.compile(
        r"(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)", re.DOTALL
    )

    covered: list[tuple[int, int]] = []
    for match in display_pattern.finditer(text):
        covered.append(match.span())
        before = text[:match.start()]
        line = before.count("\n") + 1
        last_nl = before.rfind("\n")
        col = match.start() - last_nl
        results.append((line, col, match.group(1)))

    for match in inline_pattern.finditer(text):
        if any(a <= match.start() < b for a, b in covered):
            continue
        before = text[:match.start()]
        line = before.count("\n") + 1
        last_nl = before.rfind("\n")
        col = match.start() - last_nl
        results.append((line, col, match.group(1)))

    return sorted(results, key=lambda x: (x[0], x[1]))


def normalize_latex(formula: str) -> str:
    text = formula

    command_map = {
        r"\rightarrow": " → ",
        r"\leftrightarrow": " ↔ ",
        r"\forall": " ∀ ",
        r"\exists": " ∃ ",
        r"\land": " ∧ ",
        r"\lor": " ∨ ",
        r"\neg": " ¬ ",
        r"\lnot": " ¬ ",
        r"\neq": " != ",
        r"\ne": " != ",
        r"\leq": " ≤ ",
        r"\le": " ≤ ",
        r"\geq": " ≥ ",
        r"\ge": " ≥ ",
        r"\notin": " ∉ ",
        r"\in": " ∈ ",
        r"\to": " → ",
        r"\iff": " ↔ ",
    }

    def replace_command(match: re.Match[str]) -> str:
        command = match.group(0)
        return command_map.get(command, command)

    text = re.sub(r"\\[A-Za-z]+", replace_command, text)

    for command in FORMAT_COMMANDS:
        text = text.replace(command, "")

    text = re.sub(
        r"\\(?:,|;|:|!|quad|qquad|enspace|hspace)",
        " ",
        text,
    )

    text = re.sub(r"\\text\s*\{([^{}]*)\}", r" \1 ", text)
    text = re.sub(r"\\operatorname\s*\{([^{}]*)\}", r" \1 ", text)

    # LaTeX escaped delimiters such as \{ and \}. The uploaded predicates.md
    # uses doubled backslashes (\\{, \\}), so normalize one or more slashes.
    text = re.sub(r"\\+\{", " { ", text)
    text = re.sub(r"\\+\}", " } ", text)
    text = re.sub(r"\\+\[", " [ ", text)
    text = re.sub(r"\\+\]", " ] ", text)
    text = re.sub(r"\\+\(", " ( ", text)
    text = re.sub(r"\\+\)", " ) ", text)

    text = text.replace(r"\left", "").replace(r"\right", "")
    text = text.replace(r"\!=", " != ")

    return text


def tokenize(formula: str) -> list[tuple[str, str, int]]:
    tokens: list[tuple[str, str, int]] = []
    i = 0

    while i < len(formula):
        ch = formula[i]

        if ch.isspace():
            i += 1
            continue

        if formula.startswith("!=", i):
            tokens.append(("BINARY", "!=", i))
            i += 2
            continue

        if ch in BINARY_SYMBOLS or ch == "≠":
            tokens.append(("BINARY", "!=" if ch == "≠" else ch, i))
            i += 1
            continue

        if ch in UNARY_SYMBOLS:
            tokens.append(("UNARY", ch, i))
            i += 1
            continue

        if ch in QUANTIFIER_SYMBOLS:
            tokens.append(("QUANTIFIER", ch, i))
            i += 1
            continue

        if ch == "|":
            tokens.append(("CARDINALITY_BAR", ch, i))
            i += 1
            continue

        if ch in "()[]{}":
            tokens.append((ch, ch, i))
            i += 1
            continue

        if ch in ",;":
            tokens.append(("SEP", ch, i))
            i += 1
            continue

        if ch == ":":
            # Set-builder notation, e.g. {i ∈ I : Assign(i,j)}.
            tokens.append(("SET_BUILDER_COLON", ch, i))
            i += 1
            continue

        if ch in OTHER_RELATIONS:
            tokens.append(("BINARY", ch, i))
            i += 1
            continue

        if ch in "^_":
            tokens.append(("DECORATION", ch, i))
            i += 1
            continue

        if ch == "\\":
            match = re.match(r"\\[A-Za-z]+", formula[i:])
            if match:
                value = match.group(0)
                tokens.append(("COMMAND", value, i))
                i += len(value)
                continue
            tokens.append(("UNKNOWN", ch, i))
            i += 1
            continue

        match = re.match(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?", formula[i:])
        if match:
            value = match.group(0)
            tokens.append(("ATOM", value, i))
            i += len(value)
            continue

        if ch.isalnum():
            tokens.append(("ATOM", ch, i))
        else:
            tokens.append(("UNKNOWN", ch, i))

        i += 1

    return tokens


# ---------------------------------------------------------------------------
# Syntax helpers
# ---------------------------------------------------------------------------

def is_opening(kind: str) -> bool:
    return kind in {"(", "[", "{"}


def is_closing(kind: str) -> bool:
    return kind in {")", "]", "}"}


def is_operand_start(kind: str) -> bool:
    return kind in {
        "ATOM", "(", "[", "{",
        "UNARY", "QUANTIFIER",
        "COMMAND", "CARDINALITY_BAR",
    }


def is_operand_end(kind: str) -> bool:
    return kind in {
        "ATOM", ")", "]", "}",
        "COMMAND", "CARDINALITY_BAR",
    }


def matching_open(close: str) -> str:
    return {")": "(", "]": "[", "}": "{"}[close]


def find_matching_close(
    tokens: list[tuple[str, str, int]], start: int
) -> int | None:
    open_kind = tokens[start][0]
    close_kind = {"(": ")", "[": "]", "{": "}"}[open_kind]
    stack: list[str] = []

    for i in range(start, len(tokens)):
        kind = tokens[i][0]
        if is_opening(kind):
            stack.append(kind)
        elif is_closing(kind):
            if not stack:
                return None
            if kind != {"(": ")", "[": "]", "{": "}"}[stack[-1]]:
                return None
            stack.pop()
            if not stack:
                return i

    return None

def check_balanced_delimiters(
    tokens: list[tuple[str, str, int]],
    line: int,
    formula: str,
) -> list[Error]:
    errors: list[Error] = []
    stack: list[tuple[str, int]] = []

    for kind, value, pos in tokens:
        if is_opening(kind):
            stack.append((kind, pos))
        elif is_closing(kind):
            expected = matching_open(kind)
            if not stack:
                errors.append(
                    Error(line, pos + 1, f"unexpected closing delimiter '{value}'")
                )
            elif stack[-1][0] != expected:
                errors.append(
                    Error(
                        line,
                        pos + 1,
                        f"mismatched delimiter '{value}', expected closing "
                        f"delimiter for '{stack[-1][0]}'",
                    )
                )
                stack.pop()
            else:
                stack.pop()

    for opening, pos in stack:
        closing = {"(": ")", "[": "]", "{": "}"}[opening]
        errors.append(
            Error(
                line,
                pos + 1,
                f"unclosed delimiter '{opening}', expected '{closing}'",
            )
        )

    return errors


def check_binary_operators(
    tokens: list[tuple[str, str, int]],
    line: int,
) -> list[Error]:
    errors: list[Error] = []

    for i, (kind, value, pos) in enumerate(tokens):
        if kind != "BINARY":
            continue

        prev_kind = tokens[i - 1][0] if i > 0 else None
        next_kind = tokens[i + 1][0] if i + 1 < len(tokens) else None

        if i == 0 or not is_operand_end(prev_kind):
            errors.append(
                Error(
                    line,
                    pos + 1,
                    f"binary/relation operator '{value}' must be preceded by "
                    "an expression",
                )
            )

        if i + 1 >= len(tokens) or not is_operand_start(next_kind):
            errors.append(
                Error(
                    line,
                    pos + 1,
                    f"binary/relation operator '{value}' must be followed by "
                    "an expression",
                )
            )

    return errors


def check_unary_operators(
    tokens: list[tuple[str, str, int]],
    line: int,
) -> list[Error]:
    errors: list[Error] = []

    for i, (kind, value, pos) in enumerate(tokens):
        if kind != "UNARY":
            continue

        next_kind = tokens[i + 1][0] if i + 1 < len(tokens) else None

        if next_kind in {"BINARY", ")", "]", "}"}:
            errors.append(
                Error(
                    line,
                    pos + 1,
                    f"unary operator '{value}' cannot be followed immediately "
                    "by a binary/relation operator or closing delimiter",
                )
            )

        if i + 1 >= len(tokens):
            errors.append(
                Error(
                    line,
                    pos + 1,
                    f"unary operator '{value}' must be followed by an expression",
                )
            )
        elif not is_operand_start(next_kind):
            errors.append(
                Error(
                    line,
                    pos + 1,
                    f"unary operator '{value}' must be followed by an expression",
                )
            )

    return errors


def parse_quantifier_variables(
    tokens: list[tuple[str, str, int]],
    q_index: int,
) -> tuple[set[str], int | None, list[tuple[int, str]]]:
    variables: set[str] = set()
    local_errors: list[tuple[int, str]] = []
    i = q_index + 1

    if i >= len(tokens):
        return variables, None, [
            (tokens[q_index][2], "quantifier must be followed by a valid domain variable")
        ]

    if tokens[i][0] != "ATOM" or not is_identifier(tokens[i][1]):
        return variables, None, [
            (
                tokens[i][2],
                "quantifier must be followed by a valid domain variable",
            )
        ]

    while i < len(tokens):
        kind, value, pos = tokens[i]

        if kind != "ATOM" or not is_identifier(value):
            local_errors.append(
                (pos, "expected a valid variable name in the quantifier declaration")
            )
            return variables, None, local_errors

        variables.add(value)
        i += 1

        if i >= len(tokens):
            return variables, i, local_errors

        next_kind, next_value, next_pos = tokens[i]

        if next_kind == "SEP" and next_value == ",":
            comma_pos = next_pos
            i += 1
            if (
                i >= len(tokens)
                or tokens[i][0] != "ATOM"
                or not is_identifier(tokens[i][1])
            ):
                local_errors.append(
                    (
                        comma_pos,
                        "quantifier variable list has a comma without a following valid variable",
                    )
                )
                return variables, None, local_errors
            continue

        if next_kind == "BINARY" and next_value == "∈":
            i += 1
            if i >= len(tokens) or tokens[i][0] != "ATOM":
                relation_pos = next_pos
                local_errors.append(
                    (
                        relation_pos,
                        "membership operator '∈' in a quantifier must be followed by a domain",
                    )
                )
                return variables, None, local_errors

            i += 1
            return variables, i, local_errors

        if next_kind == "ATOM":
            if i + 1 < len(tokens) and tokens[i + 1][0] == "(":
                return variables, i, local_errors

            local_errors.append(
                (
                    next_pos,
                    "multiple quantifier variables must be separated by ',' or followed by '∈'",
                )
            )
            return variables, None, local_errors

        return variables, i, local_errors

    return variables, i, local_errors


def check_quantifiers(
    tokens: list[tuple[str, str, int]],
    line: int,
) -> list[Error]:
    errors: list[Error] = []

    for i, (kind, value, pos) in enumerate(tokens):
        if kind != "QUANTIFIER":
            continue

        variables, after, local_errors = parse_quantifier_variables(tokens, i)
        for error_pos, message in local_errors:
            errors.append(Error(line, error_pos + 1, message))

        if not variables or after is None:
            continue

        if after >= len(tokens):
            errors.append(
                Error(
                    line,
                    pos + 1,
                    f"quantifier '{value}' must be followed by a quantified expression",
                )
            )
            continue

        next_kind = tokens[after][0]
        if next_kind in {"BINARY", ")", "]", "}"}:
            errors.append(
                Error(
                    line,
                    tokens[after][2] + 1,
                    f"invalid token after quantifier '{value}' declaration",
                )
            )

    return errors


def is_function_call_start(
    tokens: list[tuple[str, str, int]], index: int
) -> bool:
    return (
        index + 1 < len(tokens)
        and tokens[index][0] == "ATOM"
        and tokens[index + 1][0] == "("
    )


def find_predicate_call_spans(
    tokens: list[tuple[str, str, int]],
) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for i in range(len(tokens) - 1):
        if not is_function_call_start(tokens, i):
            continue
        close = find_matching_close(tokens, i + 1)
        if close is not None:
            spans.append((i + 1, close))
    return spans


def check_operand_adjacency(
    tokens: list[tuple[str, str, int]],
    line: int,
) -> list[Error]:
    errors: list[Error] = []
    call_spans = find_predicate_call_spans(tokens)

    for i in range(len(tokens) - 1):
        kind1, value1, pos1 = tokens[i]
        kind2, value2, pos2 = tokens[i + 1]

        if any(open_i < i and i + 1 < close_i for open_i, close_i in call_spans):
            continue

        if not is_operand_end(kind1) or not is_operand_start(kind2):
            continue

        # ATOM followed by '(' is a function/predicate call, not missing op.
        if kind1 == "ATOM" and kind2 == "(":
            continue

        if (kind1 == "CARDINALITY_BAR" and kind2 == "{") or (kind1 == "}" and kind2 == "CARDINALITY_BAR"):
            continue

        errors.append(
            Error(
                line,
                pos2 + 1,
                f"missing operator between '{value1}' and '{value2}'",
            )
        )

    return errors


def split_top_level_arguments(
    tokens: list[tuple[str, str, int]],
) -> tuple[list[list[tuple[str, str, int]]], list[tuple[int, str]]]:
    args: list[list[tuple[str, str, int]]] = []
    errors: list[tuple[int, str]] = []
    current: list[tuple[str, str, int]] = []
    stack: list[str] = []

    for kind, value, pos in tokens:
        if is_opening(kind):
            stack.append(kind)
            current.append((kind, value, pos))
            continue

        if is_closing(kind):
            current.append((kind, value, pos))
            if stack:
                expected = {"(": ")", "[": "]", "{": "}"}[stack[-1]]
                if value == expected:
                    stack.pop()
            continue

        if kind == "SEP" and value == "," and not stack:
            if not current:
                errors.append(
                    (pos, "predicate/function argument list contains an empty argument")
                )
            else:
                args.append(current)
            current = []
            continue

        if kind == "SEP" and value == ";" and not stack:
            errors.append(
                (pos, "use ',' to separate predicate/function arguments, not ';'")
            )
            current.append((kind, value, pos))
            continue

        current.append((kind, value, pos))

    if current:
        args.append(current)
    elif tokens:
        last_pos = tokens[-1][2]
        errors.append(
            (last_pos, "predicate/function argument list ends with an empty argument")
        )

    return args, errors


def check_argument_tokens(
    arg_tokens: list[tuple[str, str, int]],
    line: int,
) -> list[Error]:
    errors: list[Error] = []

    if not arg_tokens:
        return errors

    for i in range(len(arg_tokens) - 1):
        kind1, value1, _ = arg_tokens[i]
        kind2, value2, pos2 = arg_tokens[i + 1]

        if kind1 == "SEP" and value1 == ";":
            errors.append(
                Error(
                    line,
                    pos2 + 1,
                    "semicolon is not a valid predicate/function argument separator",
                )
            )

        if not is_operand_end(kind1) or not is_operand_start(kind2):
            continue

        if kind1 == "ATOM" and kind2 == "(":
            continue

        if (kind1 == "CARDINALITY_BAR" and kind2 == "{") or (kind1 == "}" and kind2 == "CARDINALITY_BAR"):
            continue

        errors.append(
            Error(
                line,
                pos2 + 1,
                f"missing comma between argument terms '{value1}' and '{value2}'",
            )
        )

    return errors


def check_predicate_calls(
    tokens: list[tuple[str, str, int]],
    line: int,
) -> list[Error]:
    errors: list[Error] = []

    for i in range(len(tokens) - 1):
        if not is_function_call_start(tokens, i):
            continue

        name = tokens[i][1]
        pos = tokens[i][2]
        close = find_matching_close(tokens, i + 1)

        if close is None:
            continue

        inner = tokens[i + 2:close]

        if not inner:
            errors.append(
                Error(
                    line,
                    pos + 1,
                    f"predicate/function '{name}' has an empty argument list",
                )
            )
            continue

        args, structural_errors = split_top_level_arguments(inner)
        for error_pos, message in structural_errors:
            errors.append(Error(line, error_pos + 1, message))

        argument_errors_found = False
        for arg in args:
            if not arg:
                continue
            argument_errors = check_argument_tokens(arg, line)
            if argument_errors:
                argument_errors_found = True
                errors.extend(argument_errors)

        expected_arity = KNOWN_CALL_ARITY.get(name)
        if expected_arity is not None and not structural_errors and not argument_errors_found:
            nonempty_args = [arg for arg in args if arg]
            if len(nonempty_args) != expected_arity:
                errors.append(
                    Error(
                        line,
                        pos + 1,
                        f"predicate/function '{name}' expects {expected_arity} "
                        f"argument(s), but {len(nonempty_args)} were provided",
                    )
                )

    return errors


def check_unknown_tokens(
    tokens: list[tuple[str, str, int]],
    line: int,
) -> list[Error]:
    errors: list[Error] = []
    for kind, value, pos in tokens:
        if kind == "UNKNOWN":
            errors.append(
                Error(
                    line,
                    pos + 1,
                    f"unexpected character '{value}' in formula",
                )
            )
    return errors


def check_set_builder_colons(
    tokens: list[tuple[str, str, int]],
    line: int,
) -> list[Error]:
    errors: list[Error] = []

    for i, (kind, value, pos) in enumerate(tokens):
        if kind != "SET_BUILDER_COLON":
            continue

        prev_kind = tokens[i - 1][0] if i > 0 else None
        next_kind = tokens[i + 1][0] if i + 1 < len(tokens) else None

        if prev_kind is None or prev_kind in {"{", "SEP", "BINARY", "UNARY"}:
            errors.append(
                Error(line, pos + 1, "set-builder ':' must follow a set-builder term")
            )

        if next_kind is None or next_kind in {"}", "SEP", "BINARY", "UNARY"}:
            errors.append(
                Error(line, pos + 1, "set-builder ':' must be followed by a condition")
            )

    return errors

def validate_formula(formula: str, line: int) -> list[Error]:
    normalized = normalize_latex(formula)
    tokens = tokenize(normalized)

    errors: list[Error] = []
    errors.extend(check_balanced_delimiters(tokens, line, normalized))
    errors.extend(check_binary_operators(tokens, line))
    errors.extend(check_unary_operators(tokens, line))
    errors.extend(check_quantifiers(tokens, line))
    errors.extend(check_operand_adjacency(tokens, line))
    errors.extend(check_predicate_calls(tokens, line))
    errors.extend(check_unknown_tokens(tokens, line))
    errors.extend(check_set_builder_colons(tokens, line))

    bar_positions = [
        pos for kind, value, pos in tokens if kind == "CARDINALITY_BAR"
    ]
    if len(bar_positions) % 2 != 0:
        errors.append(
            Error(
                line,
                bar_positions[-1] + 1,
                "unmatched cardinality bar '|'"
            )
        )

    return errors


def should_validate_math(start_line: int, formula: str, text: str) -> bool:
    lines = text.splitlines()
    section = ""
    for number in range(min(start_line, len(lines)), 0, -1):
        candidate = lines[number - 1].strip()
        heading = re.match(r"^#{1,6}\s+(.+?)\s*$", candidate)
        if heading:
            section = heading.group(1).strip().lower()
            break

    if section == "operator and expression grammar":
        return False

    normalized = normalize_latex(formula)

    if re.search(r"\\(?:bigwedge|bigvee|dots|cdots)\b", formula):
        return False

    has_predicate_call = bool(
        re.search(r"\b[A-Za-z_][A-Za-z0-9_]*\s*\(", normalized)
    )
    has_quantifier = bool(re.search(r"[∀∃]", normalized))

    return has_predicate_call or has_quantifier


def validate_markdown(path: Path) -> list[Error]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [Error(1, 1, f"file not found: {path}")]
    except UnicodeDecodeError as exc:
        return [Error(1, 1, f"file is not valid UTF-8: {exc}")]

    math_blocks = extract_math(text)

    errors: list[Error] = []

    masked = list(text)
    for match in re.finditer(
        r"\$\$.*?\$\$|\$(?!\$).*?(?<!\$)\$",
        text,
        re.DOTALL,
    ):
        for i in range(match.start(), match.end()):
            if masked[i] != "\n":
                masked[i] = " "

    remaining = "".join(masked)
    single_dollars = re.findall(r"(?<!\$)\$(?!\$)", remaining)
    if len(single_dollars) % 2 != 0:
        errors.append(
            Error(1, 1, "unmatched '$' found in Markdown math delimiters")
        )

    for start_line, start_col, formula in math_blocks:
        if not should_validate_math(start_line, formula, text):
            continue

        formula_errors = validate_formula(formula, start_line)
        for error in formula_errors:
            if error.column == 1:
                error.column = start_col
            else:
                error.column += max(0, start_col - 1)
        errors.extend(formula_errors)

    return sorted(errors, key=lambda e: (e.line, e.column, e.message))

def print_report(path: Path, errors: Iterable[Error]) -> int:
    errors = list(errors)

    if not errors:
        print(f"PASS: no common predicate-format errors found in '{path}'.")
        return 0

    print(f"FAIL: found {len(errors)} error(s) in '{path}':")
    for index, error in enumerate(errors, 1):
        print(f"  {index}. {error}")

    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check common predicate-format errors in a Markdown file."
    )

    default_file = Path(__file__).resolve().parent / "predicates.md"

    parser.add_argument(
        "file",
        nargs="?",
        default=str(default_file),
        help="Markdown file to validate (default: predicates.md next to this script)",
    )

    args = parser.parse_args()
    path = Path(args.file)
    return print_report(path, validate_markdown(path))


if __name__ == "__main__":
    raise SystemExit(main())
    raise SystemExit(main())

