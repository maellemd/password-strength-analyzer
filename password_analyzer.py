"""Small, local password-strength analyzer.

The score is educational. It is not a prediction of how long a password
will take to crack and it does not measure true password entropy.
"""

from __future__ import annotations

from dataclasses import dataclass
from getpass import getpass
import math
import re
import string


MIN_RECOMMENDED_LENGTH = 12
GOOD_LENGTH = 16
MAX_SCORE = 100

COMMON_PASSWORD_TERMS = {
    "password",
    "passw0rd",
    "letmein",
    "welcome",
    "admin",
    "iloveyou",
    "monkey",
    "dragon",
    "football",
}

COMMON_SEQUENCES = (
    "0123456789",
    "9876543210",
    "abcdefghijklmnopqrstuvwxyz",
    "zyxwvutsrqponmlkjihgfedcba",
    "qwertyuiop",
    "poiuytrewq",
    "azertyuiop",
    "poiuytreza",
)


@dataclass(frozen=True)
class PasswordAnalysis:
    """Results returned by the analyzer."""

    length: int
    has_lowercase: bool
    has_uppercase: bool
    has_digit: bool
    has_symbol: bool
    search_space_bits: float
    score: int
    level: str
    warnings: tuple[str, ...]
    suggestions: tuple[str, ...]


def analyze_characters(password: str) -> dict[str, bool | int]:
    """Return simple character-class information."""
    return {
        "has_lowercase": any(char.islower() for char in password),
        "has_uppercase": any(char.isupper() for char in password),
        "has_digit": any(char.isdigit() for char in password),
        "has_symbol": any(not char.isalnum() for char in password),
        "length": len(password),
    }


def estimate_search_space_bits(password: str, analysis: dict[str, bool | int]) -> float:
    """Estimate theoretical search-space bits from length and character sets.

    This deliberately does not call the result "entropy": human-created
    passwords are not uniformly random.
    """
    alphabet_size = 0

    if analysis["has_lowercase"]:
        alphabet_size += len(string.ascii_lowercase)
    if analysis["has_uppercase"]:
        alphabet_size += len(string.ascii_uppercase)
    if analysis["has_digit"]:
        alphabet_size += len(string.digits)
    if analysis["has_symbol"]:
        alphabet_size += len(string.punctuation)

    length = int(analysis["length"])
    if alphabet_size == 0 or length == 0:
        return 0.0

    return round(length * math.log2(alphabet_size), 1)


def contains_common_term(password: str) -> bool:
    """Return True when a small built-in list appears in the password."""
    lowered = password.casefold()
    return any(term in lowered for term in COMMON_PASSWORD_TERMS)


def contains_sequence(password: str, minimum_length: int = 4) -> bool:
    """Detect common alphabetic, numeric, and keyboard sequences."""
    lowered = password.casefold()

    for sequence in COMMON_SEQUENCES:
        for start in range(len(sequence) - minimum_length + 1):
            fragment = sequence[start : start + minimum_length]
            if fragment in lowered:
                return True

    return False


def has_excessive_repetition(password: str) -> bool:
    """Detect three or more identical consecutive characters."""
    return bool(re.search(r"(.)\1{2,}", password))


def calculate_score(
    password: str,
    analysis: dict[str, bool | int],
    search_space_bits: float,
) -> int:
    """Calculate a simple educational score with length as the main factor."""
    length = int(analysis["length"])
    score = 0

    # Length carries most of the score.
    if length >= 20:
        score += 60
    elif length >= GOOD_LENGTH:
        score += 52
    elif length >= MIN_RECOMMENDED_LENGTH:
        score += 42
    elif length >= 10:
        score += 30
    elif length >= 8:
        score += 20
    elif length >= 6:
        score += 10

    # Diversity is useful, but should not dominate the score.
    classes_used = sum(
        bool(analysis[key])
        for key in ("has_lowercase", "has_uppercase", "has_digit", "has_symbol")
    )
    score += classes_used * 7

    # Theoretical search space is supporting information, not proof of strength.
    if search_space_bits >= 100:
        score += 12
    elif search_space_bits >= 70:
        score += 8
    elif search_space_bits >= 50:
        score += 4

    # Penalize easy-to-guess patterns.
    if contains_common_term(password):
        score -= 30
    if contains_sequence(password):
        score -= 15
    if has_excessive_repetition(password):
        score -= 10

    return max(0, min(score, MAX_SCORE))


def get_strength_level(score: int) -> str:
    if score >= 80:
        return "VERY STRONG"
    if score >= 60:
        return "STRONG"
    if score >= 40:
        return "MODERATE"
    if score >= 20:
        return "WEAK"
    return "VERY WEAK"


def build_warnings(password: str) -> list[str]:
    warnings = []

    if contains_common_term(password):
        warnings.append("Contains a common password word or term.")
    if contains_sequence(password):
        warnings.append("Contains a predictable sequence.")
    if has_excessive_repetition(password):
        warnings.append("Contains repeated consecutive characters.")

    return warnings


def build_suggestions(
    analysis: dict[str, bool | int],
    warnings: list[str],
) -> list[str]:
    suggestions = []
    length = int(analysis["length"])

    if length < MIN_RECOMMENDED_LENGTH:
        suggestions.append(f"Use at least {MIN_RECOMMENDED_LENGTH} characters.")
    elif length < GOOD_LENGTH:
        suggestions.append("Consider 16+ characters or a longer passphrase.")

    if sum(
        bool(analysis[key])
        for key in ("has_lowercase", "has_uppercase", "has_digit", "has_symbol")
    ) < 3:
        suggestions.append("Use a less predictable mix of characters.")

    if warnings:
        suggestions.append("Replace common words, sequences, or repeated patterns.")

    if not suggestions:
        suggestions.append("Keep it unique and do not reuse it on other accounts.")

    return suggestions


def analyze_password(password: str) -> PasswordAnalysis:
    """Analyze a password without printing or storing it."""
    analysis = analyze_characters(password)
    search_space_bits = estimate_search_space_bits(password, analysis)
    score = calculate_score(password, analysis, search_space_bits)
    warnings = build_warnings(password)
    suggestions = build_suggestions(analysis, warnings)

    return PasswordAnalysis(
        length=int(analysis["length"]),
        has_lowercase=bool(analysis["has_lowercase"]),
        has_uppercase=bool(analysis["has_uppercase"]),
        has_digit=bool(analysis["has_digit"]),
        has_symbol=bool(analysis["has_symbol"]),
        search_space_bits=search_space_bits,
        score=score,
        level=get_strength_level(score),
        warnings=tuple(warnings),
        suggestions=tuple(suggestions),
    )


def build_progress_bar(score: int, width: int = 20) -> str:
    filled = round((score / MAX_SCORE) * width)
    return f"[{'#' * filled}{'-' * (width - filled)}] {score}/{MAX_SCORE}"


def print_analysis(result: PasswordAnalysis) -> None:
    """Display results without echoing the password itself."""
    print("\n" + "-" * 58)
    print(f"  Length              {result.length} characters")
    print(f"  Strength            {result.level}")
    print(f"  Score               {build_progress_bar(result.score)}")
    print(f"  Search-space est.   ~{result.search_space_bits} bits (theoretical)")
    print("-" * 58)

    print("\n  Composition")
    print(f"    Lowercase   {'yes' if result.has_lowercase else 'no'}")
    print(f"    Uppercase   {'yes' if result.has_uppercase else 'no'}")
    print(f"    Digits      {'yes' if result.has_digit else 'no'}")
    print(f"    Symbols     {'yes' if result.has_symbol else 'no'}")

    if result.warnings:
        print("\n  Warnings")
        for warning in result.warnings:
            print(f"    ! {warning}")

    print("\n  Suggestions")
    for suggestion in result.suggestions:
        print(f"    -> {suggestion}")

    print(
        "\n  Note: This is an educational estimate, not a measurement of\n"
        "  true entropy or a guarantee of resistance to password cracking."
    )
    print("-" * 58 + "\n")


def main() -> None:
    print("\n  Password Strength Analyzer")
    print("  Passwords are analyzed locally and are not saved.")
    print("  Press Ctrl+C to exit.\n")

    try:
        while True:
            password = getpass("  Enter a password: ")

            if not password:
                print("  Password cannot be empty.\n")
                continue

            print_analysis(analyze_password(password))
    except (KeyboardInterrupt, EOFError):
        print("\n  Goodbye.\n")


if __name__ == "__main__":
    main()
