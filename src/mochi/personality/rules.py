def format_rules(rules: list[str]) -> str:
    if not rules:
        return "- none"

    return "\n".join(f"- {rule}" for rule in rules)
