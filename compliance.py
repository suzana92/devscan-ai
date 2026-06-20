def check_compliance(code_content, filename, rules_text):
    """
    Compliance Guardrails — checks code against YOUR company's
    specific coding standards.
    
    Simple explanation:
    Imagine your company has a rulebook:
    - "Always use double quotes for strings"
    - "Every function must have a docstring"
    - "Never use global variables"
    
    This function reads that rulebook and checks if the code follows it.
    This is impossible for CodeRabbit because it doesn't know YOUR rules.
    """
    
    if not rules_text or not rules_text.strip():
        return []
    
    violations = []
    rules = [r.strip() for r in rules_text.split("\n") if r.strip()]
    lines = code_content.split("\n")
    
    for rule in rules:
        rule_lower = rule.lower()
        
        # Rule: Must have docstrings
        if "docstring" in rule_lower or "documentation" in rule_lower:
            func_lines = [i+1 for i, l in enumerate(lines) if "def " in l]
            for func_line in func_lines:
                # Check if line after function has a docstring
                if func_line < len(lines):
                    next_line = lines[func_line].strip() if func_line < len(lines) else ""
                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                        violations.append({
                            "rule": rule,
                            "severity": "MEDIUM",
                            "issue": f"Line {func_line}: Function missing docstring — violates your coding standards",
                            "line": func_line
                        })
                        break
        
        # Rule: No global variables
        if "no global" in rule_lower or "global variable" in rule_lower:
            for line_num, line in enumerate(lines, 1):
                if line.strip().startswith("global "):
                    violations.append({
                        "rule": rule,
                        "severity": "MEDIUM",
                        "issue": f"Line {line_num}: Global variable used — violates your no-globals policy",
                        "line": line_num
                    })
        
        # Rule: Single quotes only
        if "single quote" in rule_lower:
            double_quote_lines = [i+1 for i, l in enumerate(lines) if '"' in l and "import" not in l]
            if double_quote_lines:
                violations.append({
                    "rule": rule,
                    "severity": "LOW",
                    "issue": f"Double quotes found on {len(double_quote_lines)} lines — your standard requires single quotes",
                    "line": double_quote_lines[0]
                })
        
        # Rule: No print statements
        if "no print" in rule_lower or "no debug" in rule_lower:
            print_lines = [i+1 for i, l in enumerate(lines) if "print(" in l]
            if print_lines:
                violations.append({
                    "rule": rule,
                    "severity": "LOW",
                    "issue": f"print() statements found — your standards prohibit debug prints in production",
                    "line": print_lines[0]
                })
        
        # Rule: Max line length
        if "line length" in rule_lower or "max length" in rule_lower:
            try:
                max_len = int(''.join(filter(str.isdigit, rule)))
                long_lines = [i+1 for i, l in enumerate(lines) if len(l) > max_len]
                if long_lines:
                    violations.append({
                        "rule": rule,
                        "severity": "LOW",
                        "issue": f"{len(long_lines)} lines exceed your {max_len} character limit",
                        "line": long_lines[0]
                    })
            except:
                pass
    
    return violations