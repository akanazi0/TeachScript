import sys
import os

# Add Phase 1 and Phase 2 directories to sys.path for importing
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, 'Phase 1'))
sys.path.append(os.path.join(parent_dir, 'Phase 2'))

# Now we can import the classes
# Note: Phase 1 file is 'TeachScript(Scanner).py' which is not a valid python module name for import
# I will use importlib to import it or assume it's copied. 
# Better: the Phase 2 parser.py ALREADY contains a copy of LexicalScanner.
from parser import LexicalScanner, Parser, Node
from semantic_analyzer import SemanticAnalyzer
from code_generator import CodeGenerator

def run_compiler(source_code):
    print("--- PHASE 1: LEXICAL ANALYSIS ---")
    scanner = LexicalScanner(source_code)
    tokens, symbols, lex_errors = scanner.scan()
    
    if lex_errors:
        print("Lexical Errors Found:")
        for err in lex_errors: print(err)
        return

    print("Lexical Analysis Successful.\n")

    print("--- PHASE 2: SYNTAX ANALYSIS ---")
    parser = Parser(tokens)
    success, message, tree = parser.parse()
    
    if not success:
        print(message)
        return

    print("Syntax Analysis Successful. Parse Tree generated.\n")

    print("--- PHASE 3A: SEMANTIC ANALYSIS ---")
    analyzer = SemanticAnalyzer(tree)
    sem_errors = analyzer.analyze()
    
    if sem_errors:
        print("Semantic Errors Found:")
        for err in sem_errors: print(err)
        return

    print("Semantic Analysis Successful.\n")

    print("--- PHASE 3B: CODE GENERATION & EXECUTION ---")
    generator = CodeGenerator(tree)
    python_code = generator.generate()
    
    print("Generated Python Code:")
    print("-" * 30)
    print(python_code)
    print("-" * 30)
    
    generator.execute(python_code)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            code = f.read()
            run_compiler(code)
    else:
        # Default test program
        test_program = """
START
    int x = 10;
    int y = 20;
    int result = x + y * 2;
    print "The result is: ";
    print result;
    
    if (result > 40) then {
        print "Result is large";
    } else {
        print "Result is small";
    }
FINISH
"""
        run_compiler(test_program)
