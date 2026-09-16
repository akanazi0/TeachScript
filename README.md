# TeachScript

TeachScript is a small educational programming language and compiler pipeline written in Python. It turns TeachScript source into Python, showing each stage along the way:

```text
source code -> lexical analysis -> parsing -> semantic analysis -> Python -> execution
```

The project is designed to make compiler concepts visible and approachable. Errors are reported before code generation, and successful runs print the generated Python code before executing it.

## Features

- Scanner with token, symbol-table, comment, and lexical-error handling
- Predictive parser that builds a parse tree
- Semantic analysis with scoped symbols, declarations, type checks, and function checks
- Python code generation for statements and expressions
- Built-in execution through Python's `compile()` and `exec()`
- Optional PyQt5 interface for inspecting scanner output

## Requirements

- Python 3.6 or newer
- PyQt5 is optional and only needed for `gui.py`

The command-line compiler uses only Python's standard library.

## Quick Start

Run the compiler's built-in example:

```bash
python3 main.py
```

Compile a TeachScript file:

```bash
python3 main.py path/to/program.ts
```

For example:

```bash
python3 main.py examples/hello.ts
```

The compiler stops at the first unsuccessful stage and prints the relevant errors. On success, it displays the generated Python source and then runs it.

## Example Program

Save this as `hello.ts`:

```teachscript
START
	int count = 3;
	var message = "Hello from TeachScript";

	print message;
	while (count > 0) {
		print count;
		count = count - 1;
	}
FINISH
```

Run it with:

```bash
python3 main.py hello.ts
```

`START` and `FINISH` delimit a program. Keywords are case-insensitive, although uppercase delimiters make programs easy to scan.

## Language Overview

### Declarations and assignment

```teachscript
int age = 21;
float temperature = 18.5;
string name = "Ada";
bool ready = true;
var total = age + 1;

age = age + 1;
```

Typed declarations support `int`, `float`, `string`, and `bool`. `var` infers its type from the expression on the right-hand side.

### Control flow

```teachscript
if (age >= 18) then {
	print "Adult";
} else {
	print "Minor";
}

while (ready) {
	print "Working";
	ready = false;
}

repeat {
	print age;
	age = age - 1;
} while (age > 0)
```

### Functions

```teachscript
func greet(person) {
	print person;
	return person;
}

greet("Ada");
```

### Expressions and comments

Arithmetic operators: `+`, `-`, `*`, `/`, `%`, `^`

Comparison operators: `==`, `!=`, `<`, `>`, `<=`, `>=`

Logical operators: `and`, `or`, `not`

TeachScript supports both line and block comments:

```teachscript
// A line comment
/* A block comment */
```

## Optional Scanner GUI

Install PyQt5 in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install PyQt5
```

Launch the scanner interface:

```bash
python3 gui.py
```

The GUI accepts source text and displays the token list, symbol table, and lexical errors in separate tabs.

## Project Structure

| File | Purpose |
| --- | --- |
| `main.py` | Runs the complete compiler pipeline and executes generated Python |
| `parser.py` | Defines tokens, the lexical scanner, parse tree nodes, and parser |
| `semantic_analyzer.py` | Performs scope and type validation |
| `code_generator.py` | Converts the parse tree into Python source |
| `gui.py` | Optional PyQt5 scanner interface |
| `TeachScript(Scanner).py` | Standalone scanner demonstration |

## Pipeline Output

When you run `main.py`, the stages are reported in order:

1. Lexical analysis
2. Syntax analysis
3. Semantic analysis
4. Code generation and execution

This makes the project useful as a compact reference for experimenting with the front end of a compiler and tracing a program from source text to executable output.
