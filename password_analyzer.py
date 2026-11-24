# I kept this project in one Python file because the logic is small enough
# to follow without a framework or extra modules of my own. All imports
# below are from the standard library, so users do not need pip.
import math
import re
import string
import sys
import warnings
from getpass import getpass, GetPassWarning


# I use a small local set to catch obvious passwords without sending anything
# over the internet. It is only a sample, not a complete breach database.
COMMON_PASSWORDS = {
    "password", "password123", "password123!", "123456", "12345678",
    "123456789", "qwerty", "azerty", "admin", "letmein", "welcome",
    "iloveyou", "abc123", "1234567890", "000000", "correcthorsebatterystaple",
}
# I use 15 as a length recommendation inspired by single-factor password
# guidance, not as a rule that proves a password is secure. A constant
# keeps the scoring and advice consistent.
MIN_LENGTH = 15
RESET = "\033[0m"


def analyze_characters(password: str) -> dict:
    # I use Python's string methods instead of ASCII-only regex ranges so that
    # accented letters and non-ASCII decimal digits are recognized. Spaces
    # are reported separately because they can be useful in passphrases.
    # A dictionary lets me group named results and pass them to other
    # functions without needing a class for this small project. any()
    # stops searching as soon as it finds a matching character.
    return {
        "length": len(password),
        "has_lowercase": any(c.islower() for c in password),
        "has_uppercase": any(c.isupper() for c in password),
        "has_digit": any(c.isdecimal() for c in password),
        "has_symbol": any(not c.isalnum() and not c.isspace() for c in password),
        "has_space": any(c.isspace() for c in password),
    }


def calculate_entropy(password: str) -> float | None:
    # I keep the entropy formula (length * log2(pool size)) to illustrate
    # how the size of a random search space grows. It assumes independent,
    # uniform character selection, so it is not a measure of human choices.
    # For non-ASCII input, I return None rather than assume a pool size.
    if any(c not in string.ascii_letters + string.digits + string.punctuation + " "
           for c in password):
        return None

    # Count each available character group once, not each individual character.
    pool = 0
    for group in (string.ascii_lowercase, string.ascii_uppercase,
                  string.digits, string.punctuation, " "):
        if any(c in group for c in password):
            pool += len(group)

    # An empty input gives a pool of zero; log2(0) is undefined. I handle
    # that case explicitly and round only for readability.
    return round(len(password) * math.log2(pool), 2) if pool else 0.0


def detect_patterns(password: str) -> dict:
    # Case folding catches variations such as Password and PASSWORD.
    normalized = password.casefold()
    # I also check a version without punctuation or spaces to catch simple
    # variations of common passwords. The original input stays unchanged.
    compact = re.sub(r"[\W_]+", "", normalized)
    common = normalized in COMMON_PASSWORDS or compact in COMMON_PASSWORDS
    # Exact matches alone miss simple variations such as Password2026.
    # A short substring check catches some of these, but can also flag
    # an innocent word inside a longer password.
    common_word = any(word in normalized for word in
                      ("password", "letmein", "iloveyou", "qwerty", "azerty"))

    # The regex captures a character and uses a backreference to find it
    # at least twice more in a row, for example aaa.
    repeated = bool(re.search(r"(.)\1{2,}", normalized, re.DOTALL))
    # Repetition is not always a single character. For example, Ab1!Ab1!
    # repeats a four-character block. I compare possible block lengths
    # directly because this is easier to follow than a more complex regex.
    # A block can only fill the whole string if its length divides the
    # password length evenly. This check does not catch partial repeats.
    repeated_block = any(
        len(normalized) % size == 0
        and normalized == normalized[:size] * (len(normalized) // size)
        for size in range(1, len(normalized) // 2 + 1)
    )
    # Include both QWERTY and AZERTY layouts, as well as alphabet and digits.
    sequences = (string.digits, string.ascii_lowercase,
                 "qwertyuiop", "asdfghjkl", "zxcvbnm",
                 "azertyuiop", "qsdfghjklm", "wxcvbn")
    # Check three-character windows in both directions (e.g. 123 and 321).
    # This is a simple pattern check and can also flag accidental matches.
    sequential = any(
        sequence[i:i + 3] in normalized
        or sequence[i:i + 3][::-1] in normalized
        for sequence in sequences for i in range(len(sequence) - 2)
    )
    return {
        "common": common,
        "common_word": common_word,
        "repeated": repeated,
        "repeated_block": repeated_block,
        "sequential": sequential,
    }


def calculate_score(char_analysis: dict, patterns: dict) -> int:
    length = char_analysis["length"]
    # I give length more weight than character variety so a long passphrase
    # does not need uppercase letters or symbols just to score well.
    score = min(length * 4, 100)
    # Each True value counts as one category in Python. The bonus is only
    # three points per extra category, so variety cannot dominate length.
    # I leave spaces out of the bonus rather than reward adding a space.
    diversity = sum(char_analysis[key] for key in (
        "has_lowercase", "has_uppercase", "has_digit", "has_symbol"))
    score += max(0, diversity - 1) * 3

    # A long password can still be predictable. I use score limits for
    # short passwords and known patterns, then apply additional penalties
    # for repeated characters and sequences.
    # I chose these caps to stop short or obvious passwords from reaching
    # the higher ratings. They are subjective cutoffs for this exercise.
    if length < 8:
        score = min(score, 19)
    elif length < MIN_LENGTH:
        score = min(score, 59)
    if patterns["common"] or patterns["repeated_block"]:
        score = min(score, 19)
    if patterns["common_word"]:
        score = min(score, 39)
    # Subtract points for these patterns and cap the remaining score.
    # More than one weakness can reduce the score further.
    if patterns["repeated"]:
        score = min(score - 15, 59)
    if patterns["sequential"]:
        score = min(score - 15, 59)

    # Keep the result within the range used by the progress bar. The weights
    # and thresholds are custom educational rules, not validated security metrics.
    return max(0, min(score, 100))


def get_strength_level(score: int) -> tuple[str, str]:
    # Keep the rating and its terminal color together so the display logic
    # does not need to repeat the score thresholds.
    if score >= 80:
        return "VERY STRONG", "\033[92m"
    if score >= 60:
        return "STRONG", "\033[93m"
    if score >= 40:
        return "MODERATE", "\033[33m"
    if score >= 20:
        return "WEAK", "\033[91m"
    return "VERY WEAK", "\033[31m"


def build_progress_bar(score: int, width: int = 20) -> str:
    # I keep the bar at a fixed width so results are easy to compare.
    # Integer division avoids fractional blocks; the number beside the bar
    # still shows the exact score.
    filled = score * width // 100
    return f"[{'█' * filled}{'░' * (width - filled)}] {score}/100"


def generate_suggestions(char_analysis: dict, patterns: dict) -> list[str]:
    # Base advice on the weaknesses actually detected instead of requiring
    # every character category. Account uniqueness matters regardless of score.
    suggestions = []
    if char_analysis["length"] < MIN_LENGTH:
        suggestions.append("Aim for at least 15 characters, especially for single-factor login.")
    if patterns["common"] or patterns["common_word"]:
        suggestions.append("Avoid common passwords and predictable words.")
    if patterns["repeated"] or patterns["repeated_block"]:
        suggestions.append("Avoid repeating characters or whole blocks.")
    if patterns["sequential"]:
        suggestions.append("Avoid alphabetic, numeric and keyboard sequences.")
    suggestions.append("Use a unique password for each account and consider a password manager.")
    return suggestions


def analyze_password(password: str) -> dict:
    # I return a dictionary instead of printing here so tests can check the
    # results directly. The raw password is not included in that dictionary.
    chars = analyze_characters(password)
    patterns = detect_patterns(password)
    score = calculate_score(chars, patterns)
    return {
        "characters": chars,
        "patterns": patterns,
        "entropy": calculate_entropy(password),
        "score": score,
        "suggestions": generate_suggestions(chars, patterns),
    }


def display_results(result: dict) -> None:
    chars = result["characters"]
    score = result["score"]
    level, color = get_strength_level(score)
    # ANSI colors are useful in a terminal but can clutter redirected output.
    # isatty() lets me disable them when stdout is not a terminal.
    color, reset = (color, RESET) if sys.stdout.isatty() else ("", "")
    # None means the ASCII model does not apply, not that entropy is zero.
    entropy = result["entropy"]
    entropy_text = "N/A (outside ASCII model)" if entropy is None else f"{entropy:.2f} bits"
    print("\n" + "─" * 50)
    print(f"  Length   : {chars['length']} characters")
    print(f"  Strength : {color}{level}{reset}")
    print(f"  Score    : {color}{build_progress_bar(score)}{reset}")
    print(f"  Random-model entropy: {entropy_text}")
    print("  Educational heuristic, not a guarantee of security.")
    # Show character types for learning purposes, not as mandatory rules.
    print("\n  Composition (not requirements)")
    for label, key in (("Lowercase", "has_lowercase"), ("Uppercase", "has_uppercase"),
                       ("Digits", "has_digit"), ("Symbols", "has_symbol"),
                       ("Spaces", "has_space")):
        print(f"    {label:10} {'Yes' if chars[key] else 'No'}")
    print("\n  Suggestions")
    for suggestion in result["suggestions"]:
        print(f"    → {suggestion}")
    print("─" * 50 + "\n")


def main() -> None:
    print("\n  Password Strength Analyzer")
    print("  Use fictional passwords. Press Ctrl+C to exit.\n")
    # I keep the prompt in a loop so several examples can be compared
    # without restarting Python. Ctrl+C exits without reserving a word
    # such as quit that someone might want to analyze.
    while True:
        try:
            # getpass normally hides typing. Some environments fall back to visible
            # input, so I turn that warning into an exception and stop instead.
            with warnings.catch_warnings():
                warnings.simplefilter("error", GetPassWarning)
                password = getpass("  Enter a password: ")
        except GetPassWarning:
            print("\n  Hidden input unavailable. Run this in a terminal.")
            break
        # Allow Ctrl+C or end-of-input to close the prompt without a traceback.
        except (KeyboardInterrupt, EOFError):
            print("\n  Goodbye.")
            break
        # Reject empty input, but do not strip whitespace: spaces may be
        # intentional characters in a password or passphrase.
        if not password:
            print("  Password cannot be empty.\n")
            continue
        display_results(analyze_password(password))
        # Drop this reference once the analysis is displayed. Python does not
        # guarantee that deleting a string securely clears it from memory.
        del password


# The tests import functions from this file. This guard prevents the
# interactive prompt from running during an import.
if __name__ == "__main__":
    main()
