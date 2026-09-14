import re

VALID_PREDICATES = {
    "Assign": 2,
    "Busy": 2,
    "Overlap": 2,
    "AtCampus": 2,
    "Prefer": 2
}

VALID_DOMAINS = {
    'i': 'I', 
    'j': 'J', 
    'k': 'J', 
    'c': 'C'
}

class PredicateValidator:
    QUANTIFIERS = {'forall', 'exists', r'\forall', r'\exists', '∀', '∃'}
    BINARY_OPERATORS = {
        'AND', 'OR', '->', '<->', '!=', '=',
        r'\land', r'\lor', r'\rightarrow', r'\leftrightarrow', r'\neq', r'\bigwedge', r'\bigvee',
        '∧', '∨', '→', '↔'
    }
    UNARY_OPERATORS = {'NOT', r'\neg', '¬'}
    OPERATORS = BINARY_OPERATORS | UNARY_OPERATORS

    def __init__(self, check_unbound_vars=False):
        self.check_unbound_vars = check_unbound_vars

    def _get_domain_for_var(self, var_name):
        """Maps standard and indexed variables (e.g., i_1, j_k) to their domain."""
        if var_name in VALID_DOMAINS:
            return VALID_DOMAINS[var_name]
        prefix = var_name.split('_')[0]
        if prefix in VALID_DOMAINS:
            return VALID_DOMAINS[prefix]
        return None

    def _tokenize(self, formula):
        """Tokenizes formula and verifies bracket balance and basic character syntax."""
        errors = []
        tokens = []
        
        token_pattern = re.compile(
            r'(?P<QUANTIFIER>\\forall|\\exists|forall|exists|[∀∃])|'
            r'(?P<OPERATOR>->|<->|\\rightarrow|\\leftrightarrow|\\land|\\lor|\\neg|\\neq|\\bigwedge|\\bigvee|AND|OR|NOT|!=|=|[→↔∧∨¬])|'
            r'(?P<LPAREN>[\(\[\{])|'
            r'(?P<RPAREN>[\)\]\}])|'
            r'(?P<COMMA>,)|'
            r'(?P<IN>\\in|in|[∈])|'
            r'(?P<WORD>[a-zA-Z_][a-zA-Z0-9_]*)|'
            r'(?P<SKIP>\s+)|'
            r'(?P<MISMATCH>.)'
        )
        
        paren_stack = []
        
        for mo in token_pattern.finditer(formula):
            kind = mo.lastgroup
            value = mo.group()
            pos = mo.start()
            
            if kind == 'SKIP':
                continue
            elif kind == 'MISMATCH':
                errors.append(f"Syntax Error at position {pos}: Unexpected character '{value}'")
            elif kind == 'LPAREN':
                paren_stack.append((value, pos))
                tokens.append(('LPAREN', value, pos))
            elif kind == 'RPAREN':
                if not paren_stack:
                    errors.append(f"Syntax Error at position {pos}: Unmatched closing bracket '{value}'")
                else:
                    last_paren, _ = paren_stack.pop()
                    matches = {')': '(', ']': '[', '}': '{'}
                    if matches.get(value) != last_paren:
                        errors.append(f"Syntax Error at position {pos}: Mismatched bracket '{value}' for '{last_paren}'")
                tokens.append(('RPAREN', value, pos))
            elif kind == 'WORD':
                if value in self.QUANTIFIERS:
                    tokens.append(('QUANTIFIER', value, pos))
                elif value in self.OPERATORS:
                    tokens.append(('OPERATOR', value, pos))
                else:
                    tokens.append(('WORD', value, pos))
            else:
                tokens.append((kind, value, pos))
                
        if paren_stack:
            for unclosed_paren, unclosed_pos in paren_stack:
                errors.append(f"Syntax Error at position {unclosed_pos}: Unclosed opening bracket '{unclosed_paren}'")
                
        return tokens, errors

    def _validate_operator_grammar(self, tokens):
        errors = []
        n = len(tokens)

        for i, (kind, val, pos) in enumerate(tokens):
            if val in self.BINARY_OPERATORS:
                # Must be preceded by a term, predicate closing, or right bracket
                if i == 0:
                    errors.append(f"Grammar Error at position {pos}: Leading binary operator '{val}'")
                else:
                    prev_kind, prev_val, _ = tokens[i - 1]
                    if prev_kind in ('LPAREN', 'COMMA', 'IN') or prev_val in self.OPERATORS or prev_val in self.QUANTIFIERS:
                        errors.append(f"Grammar Error at position {pos}: Operator '{val}' missing valid left operand")

                # Must be followed by a term, predicate, left bracket, or unary operator
                if i == n - 1:
                    errors.append(f"Grammar Error at position {pos}: Dangling binary operator '{val}'")
                else:
                    next_kind, next_val, _ = tokens[i + 1]
                    if next_kind in ('RPAREN', 'COMMA', 'IN') or next_val in self.BINARY_OPERATORS:
                        errors.append(f"Grammar Error at position {pos}: Operator '{val}' missing valid right operand")

            elif val in self.UNARY_OPERATORS:
                if i == n - 1:
                    errors.append(f"Grammar Error at position {pos}: Dangling unary operator '{val}'")
                else:
                    next_kind, next_val, _ = tokens[i + 1]
                    if next_val in self.BINARY_OPERATORS or next_kind in ('RPAREN', 'COMMA'):
                        errors.append(f"Grammar Error at position {pos}: Unary operator '{val}' followed by invalid token '{next_val}'")

            elif kind == 'RPAREN' and i + 1 < n:
                next_kind, next_val, next_pos = tokens[i + 1]
                if next_kind in ('WORD', 'LPAREN', 'QUANTIFIER'):
                    errors.append(f"Grammar Error at position {next_pos}: Missing connective operator before '{next_val}'")

            elif kind == 'LPAREN' and i + 1 < n:
                if tokens[i + 1][0] == 'RPAREN':
                    errors.append(f"Syntax Error at position {pos}: Empty expression '()'")

        return errors

    def validate(self, formula):
        print(f"Testing: {formula}")
        
        tokens, lex_errors = self._tokenize(formula)
        errors = list(lex_errors)
        
        if not lex_errors:
            grammar_errors = self._validate_operator_grammar(tokens)
            errors.extend(grammar_errors)

            quantified_vars = set()
            i = 0
            n = len(tokens)
            
            while i < n:
                token_type, value, pos = tokens[i]
                
                if token_type == 'QUANTIFIER':
                    i += 1
                    q_vars = []
                    while i < n:
                        t_kind, t_val, t_pos = tokens[i]
                        if t_kind == 'WORD' and t_val not in self.OPERATORS:
                            expected_domain = self._get_domain_for_var(t_val)
                            if not expected_domain:
                                errors.append(f"Domain Error at position {t_pos}: Quantified variable '{t_val}' has no valid domain defined")
                            
                            q_vars.append(t_val)
                            quantified_vars.add(t_val)
                            i += 1

                            if i < n and tokens[i][0] in ('COMMA', 'IN'):
                                if tokens[i][0] == 'IN':
                                    i += 1
                                    if i < n and tokens[i][0] == 'WORD':
                                        specified_domain = tokens[i][1]
                                        if expected_domain and specified_domain != expected_domain:
                                            errors.append(f"Domain Error at position {tokens[i][2]}: Variable '{t_val}' belongs to domain '{expected_domain}', but got '{specified_domain}'")
                                        i += 1
                                elif tokens[i][0] == 'COMMA':
                                    i += 1
                        elif t_kind == 'COMMA':
                            i += 1
                        else:
                            break
                            
                    if not q_vars:
                        errors.append(f"Syntax Error at position {pos}: Quantifier '{value}' missing target variable(s)")
                    continue

                elif token_type == 'WORD':
                    if i + 1 < n and tokens[i+1][0] == 'LPAREN':
                        pred_name = value
                        pred_pos = pos
                        
                        if pred_name not in VALID_PREDICATES:
                            errors.append(f"Semantic Error at position {pred_pos}: Unknown predicate '{pred_name}'")
                        
                        i += 2  # Skip predicate name and '('
                        args = []
                        depth = 1
                        arg_tokens = []
                        
                        while i < n and depth > 0:
                            t_type, t_val, t_pos = tokens[i]
                            if t_type == 'LPAREN':
                                depth += 1
                                arg_tokens.append(t_val)
                            elif t_type == 'RPAREN':
                                depth -= 1
                                if depth == 0:
                                    break
                                arg_tokens.append(t_val)
                            elif t_type == 'COMMA' and depth == 1:
                                arg_str = "".join(arg_tokens).strip()
                                if not arg_str:
                                    errors.append(f"Syntax Error at position {t_pos}: Empty argument in predicate '{pred_name}'")
                                else:
                                    args.append((arg_str, t_pos))
                                arg_tokens = []
                            else:
                                arg_tokens.append(t_val)
                            i += 1
                            
                        if depth == 0:
                            last_arg = "".join(arg_tokens).strip()
                            if last_arg:
                                args.append((last_arg, pos))
                            elif args:
                                errors.append(f"Syntax Error at position {pos}: Trailing comma or empty argument in predicate '{pred_name}'")
                                
                        if pred_name in VALID_PREDICATES:
                            expected_arity = VALID_PREDICATES[pred_name]
                            if len(args) != expected_arity:
                                errors.append(f"Semantic Error at position {pred_pos}: Predicate '{pred_name}' expects {expected_arity} arguments, but received {len(args)}")
                                
                        for arg_val, arg_pos in args:
                            domain = self._get_domain_for_var(arg_val)
                            if not domain:
                                errors.append(f"Domain Error in predicate '{pred_name}': Variable '{arg_val}' has no valid domain defined")
                            elif self.check_unbound_vars and arg_val not in quantified_vars:
                                errors.append(f"Scope Error in predicate '{pred_name}': Variable '{arg_val}' is unbound")
                    else:
                        var_name = value
                        if var_name not in self.OPERATORS and var_name not in self.QUANTIFIERS and var_name not in {'I', 'J', 'C'}:
                            domain = self._get_domain_for_var(var_name)
                            if not domain and var_name not in quantified_vars:
                                errors.append(f"Syntax Error at position {pos}: Unrecognized identifier '{var_name}'")

                i += 1

        if errors:
            for err in errors:
                print(f"  [X] {err}")
            return False
        else:
            print("  [OK] Formula format valid!")
            return True


def validate_formula(formula, check_unbound_vars=False):
    validator = PredicateValidator(check_unbound_vars=check_unbound_vars)
    return validator.validate(formula)


if __name__ == "__main__":
    test_formulas = [
        "forall j forall k (Overlap(j, k) AND Assign(i, j) -> NOT Assign(i, k))",
        "Assign(i, j) -> -> Busy(i, j)",                                   
        "Assign(i, j) ->",                                                
        "Assign(i, j) Busy(i, j)",                                            
        "forall x (Assign(i, j))",                                          
        "forall j in I (Assign(i, j))",                                         
        "()"                                                                 
    ]

    for f in test_formulas:
        validate_formula(f)
        print("-" * 50)
