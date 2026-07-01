---
name: code-style-enforcement
description: Guidelines for enforcing strict formatting rules, syntax conventions, and code layouts for Palmiche J.A.R.V.I.S (TypeScript, JavaScript, Vue, HTML, CSS/SCSS).
---

# Code Style and Formatting Conventions

This skill governs the visual styling, formatting, and structural constraints of all code files in the Palmiche J.A.R.V.I.S project. AI assistants must adhere strictly to these rules when creating or editing files.

## Formatting Rules

1. **Indentation**:
   * Use exactly **2 spaces** for indentation. Never use tabs.
   * This applies to all code blocks in all file types (`.ts`, `.js`, `.vue`, `.html`, `.css`, `.scss`, `.json`, `.md`), including inside `<template>` and `<style>` blocks of Vue components.

2. **Semicolons**:
   * **Never** use semicolons (`;`) at the end of statements in JavaScript and TypeScript, unless they are syntax-critical (such as separating two statements on a single line, which should be avoided anyway).

3. **Quotes**:
   * Use single quotes (`'`) for string literals in JavaScript, TypeScript, and CSS/SCSS, unless double quotes are required (e.g., in JSON or HTML/Vue template attribute values).

4. **Braces for Control Structures**:
   * All control structures (such as `if`, `else`, `for`, `while`, `switch`) **must** use block braces `{}`.
   * Single-line control statements without braces are strictly prohibited.
   * Don't set a blank line between the control structure condition and the opening brace or closing brace.
   * Example:

     ```typescript
     // Correct
     if (condition) {
       doSomething()
     }

     for (let i = 0; i <= 10; i++) {
      if (condition) {
         doSomething()
      }

      if (otheCondition) {
         doSomething()
      }
     }

     // Incorrect
     if (condition) doSomething()

     for (let i = 0;;) {

      if (condition) {
        doSomething()
      }
      if (otheCondition) {
        doSomething()
      }

     }
     ```

5. **Spacing Around Control Structures and Variables**:
   * Always leave **one empty line before and after** each control structure (`if`, `for`, `while`, `switch`, etc.) and variable declaration block (`const`, `let`, `var`).
   * Example:

     ```typescript
     const stepX = toPixels(cellWidth.value, unit)

     if (gridType.value === GRID_TYPE_SQUARE) {
       stepY = stepX
     }

     const freq = Number(masterLinesEach.value)
     ```

6. **Object Literal Spacing**:
   * Always leave blank spaces inside the braces for inline object declarations.
   * Example:

     ```typescript
     // Correct
     const options = { some: 'thing' }

     // Incorrect
     const options = {some:'thing'}
     ```

7. **End of File**:
   * Every file must end with exactly **one trailing empty line**.

8. For functions with more than 2 params, set a object as params, e.g:

   ```javascript
   // Correct
   function getData({ data, pagination, meta }){}

   // Incorrect
   function getData(data, pagination, meta){}
   ```

9. **Object Literal many fields**:
   * If a object literal has more than 2 fields, set a new line for each field, and put the braces in the same line as the object name.
   * Example:

     ```typescript
     // Correct
     const options = {
       field1: 'value1',
       field2: 'value2',
       field3: 'value3',
     }

     // Incorrect
     const options = { field1: 'value1', field2: 'value2', field3: 'value3' }
     ```

10. **Avoid lines with black spaces at the end of the file**
    * Example:

     ```typescript
     // Correct
     let 1;

     // Incorrect
     let 1 ;
       
      let b = 7;   
     ```

11. **Limit columns to 80 characters**
