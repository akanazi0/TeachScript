import re

class Token:
    """Stores the structure for each identified lexeme"""
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line

    def __repr__(self):
        return f"<{self.type}, {self.line}, {self.value}>"

class LexicalScanner:
    def __init__(self, source_code):
        self.source = source_code
        self.tokens = []
        self.errors = []
        self.symbol_table = {} # Stores identifier: first_line 
        
        # KEYWORDS
        self.keywords = {
            'start', 'finish', 'if', 'then', 'else', 'repeat', 'while', 
            'var', 'int', 'float', 'string', 'bool', 'do', 'read', 
            'print', 'void', 'return', 'func', 'and', 'or', 'not'
        }

    def scan(self):
        # REGULAR EXPRESSIONS
        token_specification = [
            ('BLOCK_COMMENT', r'/\*[\s\S]*?\*/'), 
            ('LINE_COMMENT',  r'//.*'),           
            ('NUMBER',        r'-?\d+(\.\d+)?'),  # Logic below handles max 8 digits 
            ('STRING',        r'"[^"]*"'),        
            ('ID',            r'[A-Za-z][A-Za-z0-9]*'), # Logic below handles max 8 chars 
            ('REL_OP',        r'==|!=|<=|>=|<|>'), 
            ('ARITH_OP',      r'[=+\-*/%^]'),      
            ('DELIMITER',     r'[.\(\),\{\};:]'),  
            ('NEWLINE',       r'\n'),              # Used for line tracking
            ('SKIP',          r'[ \t]+'),          # Ignore whitespace
            ('MISMATCH',      r'.'),               # Catch-all for invalid symbols 
        ]
        
        # Combine patterns into a named group regex
        master_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
        line_num = 1
        
        for mo in re.finditer(master_regex, self.source):
            kind = mo.lastgroup
            value = mo.group()

            if kind == 'NEWLINE':
                line_num += 1
                continue
            elif kind in ('SKIP', 'LINE_COMMENT', 'BLOCK_COMMENT'):
                continue
            
            # --- MANDATORY LOGIC CHECKS ---
            
            # 1. Identifier Handling & Max Length (8 chars)
            if kind == 'ID':
                if value.lower() in self.keywords: # Case-insensitive check 
                    kind = 'KEYWORD'
                elif len(value) > 8:
                    self.errors.append(f"Lexical Error at line {line_num}: Identifier '{value}' exceeds 8 chars.")
                    continue
                else:
                    # Update Symbol Table with first occurrence 
                    if value not in self.symbol_table:
                        self.symbol_table[value] = line_num

            # 2. Number Handling & Max Digits (8 before decimal) 
            elif kind == 'NUMBER':
                parts = value.split('.')
                # Check integer part (handling negative sign)
                int_part = parts[0].replace('-', '')
                if len(int_part) > 8:
                    self.errors.append(f"Lexical Error at line {line_num}: Number '{value}' exceeds 8 digits.")
                    continue

            # 3. Error Reporting for Invalid Symbols 
            elif kind == 'MISMATCH':
                self.errors.append(f"Lexical Error at line {line_num}: Invalid symbol '{value}'.")
                continue

            self.tokens.append(Token(kind, value, line_num))

        return self.tokens, self.symbol_table, self.errors


# uses this block to connect the backend to the GUI.
def run_scanner(input_text):
    scanner = LexicalScanner(input_text)
    tokens, symbols, errors = scanner.scan()
    
    print(f"Total lexemes found: {len(tokens)}")
    print("\n--- TOKEN LIST ---")
    for t in tokens: print(t)
    
    print("\n--- SYMBOL TABLE ---")
    for name, line in symbols.items(): print(f"{name}: First seen at line {line}")
    
    if errors:
        print("\n--- ERRORS ---")
        for e in errors: print(e)

# Example Usage
sample_program = """
var count = 42;
if (count > 0) {
    print "Success";
} // This is a comment
"""

test = """
name = Khalid;
if (name > 5) {
then print "Hello Khalid";
}
// test for lexical analyzer """


run_scanner(test)