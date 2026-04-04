import re
import math


def analyze_characters(password: str) -> dict:
    return {
        "has_lowercase": bool(re.search(r"[a-z]", password)),
        "has_uppercase": bool(re.search(r"[A-Z]", password)),
        "has_digit":     bool(re.search(r"\d", password)),
        "has_symbol":    bool(re.search(r"[^a-zA-Z0-9]", password)),
        "length":        len(password),
    }


def calculate_entropy(password: str, char_analysis: dict) -> float:
    alphabet_size = 0

    if char_analysis["has_lowercase"]: alphabet_size += 26
    if char_analysis["has_uppercase"]: alphabet_size += 26
    if char_analysis["has_digit"]:     alphabet_size += 10
    if char_analysis["has_symbol"]:    alphabet_size += 32

    if alphabet_size == 0 or char_analysis["length"] == 0:
        return 0.0

    return round(char_analysis["length"] * math.log2(alphabet_size), 2)


def calculate_score(password: str, char_analysis: dict, entropy: float) -> int:
    score = 0
    length = char_analysis["length"]

    if length >= 20:   score += 40
    elif length >= 16: score += 35
    elif length >= 12: score += 25
    elif length >= 8:  score += 15
    elif length >= 6:  score += 5

    if char_analysis["has_lowercase"]: score += 10
    if char_analysis["has_uppercase"]: score += 10
    if char_analysis["has_digit"]:     score += 10
    if char_analysis["has_symbol"]:    score += 10

    if entropy >= 128:  score += 20
    elif entropy >= 60: score += 15
    elif entropy >= 36: score += 10
    elif entropy >= 28: score += 5

    return min(score, 100)


def get_strength_level(score: int) -> tuple[str, str]:
    if score >= 80:   return ("VERY STRONG", "\033[92m")
    elif score >= 60: return ("STRONG",      "\033[93m")
    elif score >= 40: return ("MODERATE",    "\033[33m")
    elif score >= 20: return ("WEAK",        "\033[91m")
    else:             return ("VERY WEAK",   "\033[31m")


def build_progress_bar(score: int, width: int = 20) -> str:
    filled = int((score / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {score}/100"


def generate_suggestions(password: str, char_analysis: dict, score: int) -> list[str]:
    suggestions = []

    if char_analysis["length"] < 12:
        suggestions.append("Use at least 12 characters.")
    if not char_analysis["has_uppercase"]:
        suggestions.append("Add uppercase letters (A-Z).")
    if not char_analysis["has_lowercase"]:
        suggestions.append("Add lowercase letters (a-z).")
    if not char_analysis["has_digit"]:
        suggestions.append("Add digits (0-9).")
    if not char_analysis["has_symbol"]:
        suggestions.append("Add symbols (!@#$%^&*...).")
    if re.search(r"(.)\1{2,}", password):
        suggestions.append("Avoid repeated characters (e.g. 'aaa', '111').")
    if re.search(r"(012|123|234|345|456|567|678|789|890)", password):
        suggestions.append("Avoid sequential digits (e.g. '1234').")
    if re.search(r"(abc|bcd|cde|qwerty|azerty)", password.lower()):
        suggestions.append("Avoid keyboard sequences (e.g. 'qwerty', 'azerty').")

    return suggestions


def analyze_password(password: str) -> None:
    RESET = "\033[0m"

    char_analysis = analyze_characters(password)
    entropy       = calculate_entropy(password, char_analysis)
    score         = calculate_score(password, char_analysis, entropy)
    level, color  = get_strength_level(score)
    bar           = build_progress_bar(score)
    suggestions   = generate_suggestions(password, char_analysis, score)

    print("\n" + "─" * 50)
    print(f"  Password : {'*' * char_analysis['length']}  ({char_analysis['length']} chars)")
    print(f"  Strength : {color}{level}{RESET}")
    print(f"  Score    : {color}{bar}{RESET}")
    print(f"  Entropy  : {entropy} bits")
    print("─" * 50)

    print("\n  Composition")
    print(f"    Lowercase  {'✓' if char_analysis['has_lowercase'] else '✗'}")
    print(f"    Uppercase  {'✓' if char_analysis['has_uppercase'] else '✗'}")
    print(f"    Digits     {'✓' if char_analysis['has_digit']     else '✗'}")
    print(f"    Symbols    {'✓' if char_analysis['has_symbol']    else '✗'}")

    if suggestions:
        print("\n  Suggestions")
        for s in suggestions:
            print(f"    → {s}")

    print("\n" + "─" * 50 + "\n")


def main():
    print("\n  Password Strength Analyzer")
    print("  Type 'quit' to exit.\n")

    while True:
        password = input("  Enter a password: ")

        if password.lower() == "quit":
            print("  Goodbye.\n")
            break

        if not password:
            print("  Password cannot be empty.\n")
            continue

        analyze_password(password)


if __name__ == "__main__":
    main()