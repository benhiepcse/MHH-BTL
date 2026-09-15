#!/usr/bin/env python3
"""
predicate_validator.py

Validate common formatting/syntax errors in mathematical predicates written
inside a Markdown file.

The checks are based on the "Formal Syntax Rules" section of predicate.md:

1. Binary operators:
       AND, OR, implication, equivalence, equality, inequality
   must have a valid expression on both sides.

2. Unary operators:
       NOT / negation
   cannot be followed immediately by another binary operator or ')'.

3. Quantifiers:
       forall / exists
   must be followed by one or more valid domain variables, optionally followed
   by a domain constraint such as "in I".

4. Parentheses/braces:
   (), [] and {} must be balanced.

5. Predicate calls:
   A predicate/function call such as Assign(i, j) must have balanced
   parentheses and non-empty arguments.

The validator intentionally performs syntax/format checks only. It does not
attempt to prove that a formula is logically correct.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Iterable


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

@dataclass
class Error:
    line: int
    column: int
    message: str

    def __str__(self) -> str:
        return f"line {self.line}, column {self.column}: {self.message}"


# ---------------------------------------------------------------------------
# Token definitions
# ---------------------------------------------------------------------------
.
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
}

BINARY_SYMBOLS = {
    "∧": "AND (∧)",
    "∨": "OR (∨)",
    "→": "implication (→)",
    "↔": "equivalence (↔)",
    "=": "equality (=)",
    "!=": "inequality (!=)",
    "≠": "inequality (≠)",
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

# Identifier used for variables, set names, function/predicate names, etc.
IDENTIFIER_RE = re.compile(
    r"(?:"
    r"[A-Za-z_][A-Za-z0-9_]*"
    r"|[ivjkcprnmkta-zA-Z]_[A-Za-z0-9]+"
    r")"
)


# ---------------------------------------------------------------------------
# Markdown / LaTeX preprocessing
# ---------------------------------------------------------------------------

def extract_math(text: str) -> list[tuple[int, int, str]]:
    """
    Extract inline/display math.

    Returns tuples: (start_line, start_column, formula).
    """
    results: list[tuple[int, int, str]] = []

    display_pattern = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)

    inline_pattern = re.compile(r"(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)", re.DOTALL)

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
    """
    Convert common LaTeX operators to plain symbols while preserving
    meaningful characters.

    Command matching is token-based so that '\\ne' never accidentally matches
    the beginning of '\\neg'.
    """
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

    text = text.replace(r"\left", "").replace(r"\right", "")
    text = text.replace(r"\!=", " !=")

    return text



def tokenize(formula: str) -> list[tuple[str, str, int]]:
    """
    Tokenize a normalized formula.

    Token tuple:
        (kind, value, character_position)
    """
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
            if i > 0 and formula[i - 1] == "\\\\":
                tokens.append(("ATOM", ch, i))
            else:
                tokens.append((ch, ch, i))
            i += 1
            continue

        if ch in ",;":
            tokens.append(("SEP", ch, i))
            i += 1
            continue

        if ch in OTHER_RELATIONS:
            tokens.append(("RELATION", ch, i))
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
    """
    Tokens which can begin an expression under the assignment's simplified
    predicate grammar.
    """
    return kind in {
        "ATOM", "(", "[", "{",
        "UNARY", "QUANTIFIER",
        "COMMAND",
    }


def is_operand_end(kind: str) -> bool:
    """
    Tokens which can end an expression.
    """
    return kind in {
        "ATOM", ")",
        "COMMAND", "CARDINALITY_BAR",
    }


def matching_open(close: str) -> str:
    return {")": "(", "]": "[", "}": "{"}[close]


def find_matching_close(tokens: list[tuple[str, str, int]], start: int) -> int | None:
    open_kind = tokens[start][0]
    close_kind = {"(": ")", "[": "]", "{": "}"}[open_kind]
    depth = 0

    for i in range(start, len(tokens)):
        kind = tokens[i][0]
        if kind == open_kind:
            depth += 1
        elif kind == close_kind:
            depth -= 1
            if depth == 0:
                return i
    return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

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
                        f"mismatched delimiter '{value}', expected "
                        f"closing delimiter for '{stack[-1][0]}'",
                    )
                )
                stack.pop()
            else:
                stack.pop()

    for opening, pos in stack:
        closing = {"(": ")", "[": "]", "{": "}"}[opening]
        errors.append(
            Error(line, pos + 1, f"unclosed delimiter '{opening}', expected '{closing}'")
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
                    f"binary operator '{value}' must be preceded by a term, "
                    "predicate closing, or ')'",
                )
            )

        if i + 1 >= len(tokens) or not is_operand_start(next_kind):
            errors.append(
                Error(
                    line,
                    pos + 1,
                    f"binary operator '{value}' must be followed by a term, "
                    "predicate opening, '(', or a unary operator",
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
                    "by a binary operator or closing parenthesis",
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

    return errors


def parse_quantifier_variables(
    tokens: list[tuple[str, str, int]],
    q_index: int,
) -> tuple[set[str], int | None]:
    """
    Parse a simplified quantifier declaration.

    Examples accepted:
        ∀ i
        ∀ i ∈ I
        ∀ j, k ∈ J
        ∃ i_1, i_2, ..., i_n ∈ I

    Returns:
        (declared_variables, index_after_declaration)

    The parser stops before '(' because the quantified expression normally
    starts there.
    """
    variables: set[str] = set()
    i = q_index + 1

    if i >= len(tokens):
        return variables, None

    expecting_variable = True
    domain_seen = False

    while i < len(tokens):
        kind, value, _ = tokens[i]

        if kind == "ATOM":
            if expecting_variable:
                variables.add(value)
                expecting_variable = False
                i += 1
                continue

            if domain_seen:
                break

            break

        if kind == "SEP" and value == ",":
            if expecting_variable:
                break
            expecting_variable = True
            i += 1
            continue

        if kind == "RELATION" and value == "∈":
            if expecting_variable or domain_seen:
                break
            domain_seen = True
            i += 1

            if i < len(tokens) and tokens[i][0] == "ATOM":
                i += 1
                return variables, i

            return variables, None

        # Expression begins.
        break

    if expecting_variable:
        return variables, None

    return variables, i


def check_quantifiers(
    tokens: list[tuple[str, str, int]],
    line: int,
) -> list[Error]:
    errors: list[Error] = []

    for i, (kind, value, pos) in enumerate(tokens):
        if kind != "QUANTIFIER":
            continue

        variables, after = parse_quantifier_variables(tokens, i)

        if not variables or after is None:
            errors.append(
                Error(
                    line,
                    pos + 1,
                    f"quantifier '{value}' must be followed by a valid domain variable",
                )
            )
            continue

        if after < len(tokens):
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


def check_operand_adjacency(
    tokens: list[tuple[str, str, int]],
    line: int,
) -> list[Error]:
    """
    Catch especially common forms such as:
        Assign(i,j) Assign(k,j)
        (A)(B)
        ) (
        variable )
    without trying to become a full theorem prover/parser.
    """
    errors: list[Error] = []

    for i in range(len(tokens) - 1):
        kind1, value1, pos1 = tokens[i]
        kind2, value2, pos2 = tokens[i + 1]

        if (
            is_operand_end(kind1)
            and kind2 == "ATOM"
            and value1.isascii()
            and value2.isascii()
        ):
            errors.append(
                Error(
                    line,
                    pos2 + 1,
                    f"missing operator between '{value1}' and '{value2}'",
                )
            )

        if kind1 == ")" and kind2 == "(":
            errors.append(
                Error(
                    line,
                    pos2 + 1,
                    "missing operator between ')' and '('",
                )
            )

    return errors


def check_predicate_calls(
    formula: str,
    tokens: list[tuple[str, str, int]],
    line: int,
) -> list[Error]:
    """
    Validate simple calls such as Assign(i, j).

    A function/predicate name immediately followed by '(' must contain a
    closing ')'. Empty calls like Assign() are reported.
    """
    errors: list[Error] = []

    for i in range(len(tokens) - 1):
        kind, name, pos = tokens[i]
        next_kind, next_value, next_pos = tokens[i + 1]

        if kind != "ATOM" or next_kind != "(":
            continue

        close = find_matching_close(tokens, i + 1)
        if close is None:
            continue  

        if close == i + 2:
            errors.append(
                Error(
                    line,
                    pos + 1,
                    f"predicate/function '{name}' has empty argument list",
                )
            )

    return errors


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_formula(formula: str, line: int) -> list[Error]:
    normalized = normalize_latex(formula)
    tokens = tokenize(normalized)

    errors: list[Error] = []
    errors.extend(check_balanced_delimiters(tokens, line, normalized))
    errors.extend(check_binary_operators(tokens, line))
    errors.extend(check_unary_operators(tokens, line))
    errors.extend(check_quantifiers(tokens, line))
    errors.extend(check_operand_adjacency(tokens, line))
    errors.extend(check_predicate_calls(normalized, tokens, line))

    bar_positions = [pos for kind, value, pos in tokens if kind == "CARDINALITY_BAR"]
    if len(bar_positions) % 2 != 0:
        errors.append(
            Error(
                line,
                bar_positions[-1] + 1,
                "unmatched cardinality bar '|'",
            )
        )

    return errors


def should_validate_math(start_line: int, formula: str, text: str) -> bool:
    """
    Decide whether a math span is an actual predicate expression.

    The source document also contains mathematical notation in definitions,
    prose examples, and the syntax-rule reference section. The validator
    focuses on expressions that are intended to be parsed as predicates.
    """
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
    for match in re.finditer(r"\$\$.*?\$\$|\$(?!\$).*?(?<!\$)\$", text, re.DOTALL):
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

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
    parser.add_argument(
        "file",
        nargs="?",
        default="predicates.md",
        help="Markdown file to validate (default: predicates.md)",
    )
    args = parser.parse_args()

    path = Path(args.file)
    return print_report(path, validate_markdown(path))


if __name__ == "__main__":
    raise SystemExit(main())
