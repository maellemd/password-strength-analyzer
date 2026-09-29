# Password Strength Analyzer

A small Python command-line project for learning about password-strength heuristics.

This is a cleaned-up version of an early project. It deliberately stays simple: standard-library Python, functions, one small `dataclass`, and `unittest`.

## Improvements

- Hides password input with `getpass`
- Gives length more weight than arbitrary composition rules
- Detects a small set of common password terms
- Detects common numeric, alphabetic, QWERTY, and AZERTY sequences
- Detects repeated characters
- Renames the old "entropy" value to **theoretical search-space estimate**
- Separates analysis from terminal output
- Adds type hints, docstrings, constants, and tests
- Does not store or transmit the entered password

## Run

Requires Python 3.10+.

```bash
python password_analyzer.py
```

Run the tests:

```bash
python -m unittest -v
```

No third-party packages are required.

## Important limitation

The score is educational. The search-space calculation assumes characters are selected from broad character sets and does **not** measure the true entropy of a human-created password. A high score is not a guarantee that a password will resist every guessing or cracking strategy.

For real accounts, use unique passwords or passphrases and a reputable password manager. Multi-factor authentication should be enabled where available.

## Possible later review

This project is intentionally not overengineered. A future review could expand the pattern list, improve passphrase handling, add parameterized tests, or optionally explore privacy-preserving breached-password checks without sending a full password to a service.
