---
name: python-pep8-style
description: Guidelines for enforcing strict PEP-8 formatting rules, syntax conventions, and code layouts for Python code in Palmiche J.A.R.V.I.S.
---

# Python Code Style and Formatting Conventions (PEP-8)

This skill governs the visual styling, formatting, and structural constraints of all Python (`.py`) code files in the Palmiche J.A.R.V.I.S project. AI assistants must adhere strictly to these rules, which are based on PEP-8, when creating or editing files.

## Formatting Rules

1. **Indentation**:
   * Use exactly **4 spaces** per indentation level. Never use tabs.

2. **Maximum Line Length**:
   * Limit all lines to a maximum of **79 characters**.
   * For flowing long blocks of text with fewer structural restrictions (docstrings or comments), the line length should be limited to 72 characters.

3. **Blank Lines**:
   * Surround top-level function and class definitions with **two blank lines**.
   * Method definitions inside a class are surrounded by a **single blank line**.
   * Extra blank lines may be used (sparingly) to separate groups of related functions.

4. **Imports**:
   * Imports should usually be on separate lines.
   * Imports are always put at the top of the file, just after any module comments and docstrings, and before module globals and constants.
   * Imports should be grouped in the following order:
     1. Standard library imports.
     2. Related third party imports.
     3. Local application/library specific imports.
   * You should put a blank line between each group of imports.

5. **String Quotes**:
   * In Python, single-quoted strings and double-quoted strings are the same. Pick a rule and stick to it (double quotes `"` are recommended). For triple-quoted strings, always use double quote characters (`"""`) to be consistent with the docstring convention in PEP 257.

6. **Whitespace in Expressions and Statements**:
   * Avoid extraneous whitespace in the following situations:
     * Immediately inside parentheses, brackets or braces.
     * Between a trailing comma and a following close parenthesis.
     * Immediately before a comma, semicolon, or colon.
     * Immediately before the open parenthesis that starts the argument list of a function call.

7. **Comments and Docstrings**:
   * Write docstrings for all public modules, functions, classes, and methods according to PEP-257.
   * Inline comments should be used sparingly and should be separated by at least two spaces from the statement. They should start with a `#` and a single space.

8. **Naming Conventions**:
   * **Variables and Functions**: Use `lowercase_with_underscores`.
   * **Classes**: Use `CapWords` (CamelCase).
   * **Constants**: Use `ALL_CAPS_WITH_UNDERSCORES`.
   * **Modules**: Use `short_lowercase_names`.

9. **Trailing Commas**:
   * Trailing commas are typically optional, but they are useful when a version control system is used, when a list of values, arguments or imported items is expected to be extended over time. The pattern is to put each value on a line by itself, always adding a trailing comma.

10. **End of File**:
    * Every file must end with exactly **one trailing empty line**.
