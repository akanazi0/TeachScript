import sys
import os
import re

# For importing the scanner from Phase 1 folder if needed
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Phase 1')))

class Token:
    """Stores the structure for each identified lexeme."""
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
        self.symbol_table = {} 
        self.keywords = {
            'start', 'finish', 'if', 'then', 'else', 'repeat', 'while', 
            'var', 'int', 'float', 'string', 'bool', 'do', 'read', 
            'print', 'void', 'return', 'func', 'and', 'or', 'not'
        }

    def scan(self):
        token_specification = [
            ('BLOCK_COMMENT', r'/\*[\s\S]*?\*/'),
            ('LINE_COMMENT',  r'//.*'),
            ('NUMBER',        r'-?\d+(\.\d+)?'),
            ('STRING',        r'"[^"]*"'),
            ('ID',            r'[A-Za-z][A-Za-z0-9]*'),
            ('REL_OP',        r'==|!=|<=|>=|<|>'),
            ('ARITH_OP',      r'[=+\-*/%^]'),
            ('DELIMITER',     r'[.\(\),\{\};:]'),
            ('NEWLINE',       r'\n'),
            ('SKIP',          r'[ \t]+'),
            ('MISMATCH',      r'.'),
        ]
        
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
            
            if kind == 'ID':
                val_lower = value.lower()
                if val_lower in self.keywords:
                    kind = 'KEYWORD'
                elif val_lower in ['true', 'false']:
                    kind = 'BOOL_LIT'
                elif len(value) > 8:
                    self.errors.append(f"Lexical Error at line {line_num}: Identifier '{value}' exceeds 8 chars.")
                    continue
                else:
                    if value not in self.symbol_table:
                        self.symbol_table[value] = line_num

            elif kind == 'NUMBER':
                parts = value.split('.')
                int_part = parts[0].replace('-', '')
                if len(int_part) > 8:
                    self.errors.append(f"Lexical Error at line {line_num}: Number '{value}' exceeds 8 digits.")
                    continue

            elif kind == 'MISMATCH':
                self.errors.append(f"Lexical Error at line {line_num}: Invalid symbol '{value}'.")
                continue

            self.tokens.append(Token(kind, value, line_num))

        return self.tokens, self.symbol_table, self.errors

class Node:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def display(self, level=0):
        print("  " * level + self.name)
        for child in self.children:
            child.display(level + 1)

    def to_string(self, level=0):
        ret = "  " * level + self.name + "\n"
        for child in self.children:
            ret += child.to_string(level + 1)
        return ret

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens + [Token('$', '$', -1)]
        self.current_token_idx = 0
        self.stack = []
        self.root = None
        
        # Productions mapping
        self.productions = {
            1: ['start', 'Statements', 'finish'],
            2: ['Statement', 'Statements'],
            3: [], # epsilon
            4: ['int', 'id', 'DeclTailer'],
            5: ['float', 'id', 'DeclTailer'],
            6: ['string', 'id', 'DeclTailer'],
            7: ['bool', 'id', 'DeclTailer'],
            8: ['var', 'id', '=', 'Expression', ';'],
            9: ['id', 'AssignOrCall'],
            10: ['if', '(', 'Expression', ')', 'then', '{', 'Statements', '}', 'Else'],
            11: ['while', '(', 'Expression', ')', '{', 'Statements', '}'],
            12: ['repeat', '{', 'Statements', '}', 'while', '(', 'Expression', ')'],
            13: ['read', 'id', ';'],
            14: ['print', 'Expression', ';'],
            15: ['func', 'id', '(', 'Params', ')', '{', 'Statements', '}'],
            16: ['return', 'Expression', ';'],
            17: [';'],
            18: ['=', 'Expression', ';'],
            19: ['=', 'Expression', ';'],
            20: ['(', 'Args', ')', ';'],
            21: ['else', '{', 'Statements', '}'],
            22: [], # epsilon
            23: ['id', 'MoreParams'],
            24: [], # epsilon
            25: [',', 'id', 'MoreParams'],
            26: [], # epsilon
            27: ['Expression', 'MoreArgs'],
            28: [], # epsilon
            29: [',', 'Expression', 'MoreArgs'],
            30: [], # epsilon
            31: ['L_And', "Expression'"],
            32: ['or', 'L_And', "Expression'"],
            33: [], # epsilon
            34: ['L_Rel', "L_And'"],
            35: ['and', 'L_Rel', "L_And'"],
            36: [], # epsilon
            37: ['L_Add', "L_Rel'"],
            38: ['RelOp', 'L_Add'],
            39: [], # epsilon
            40: ['L_Mul', "L_Add'"],
            41: ['+', 'L_Mul', "L_Add'"],
            42: ['-', 'L_Mul', "L_Add'"],
            43: [], # epsilon
            44: ['L_Pow', "L_Mul'"],
            45: ['*', 'L_Pow', "L_Mul'"],
            46: ['/', 'L_Pow', "L_Mul'"],
            47: ['%', 'L_Pow', "L_Mul'"],
            48: [], # epsilon
            49: ['L_Unary', "L_Pow'"],
            50: ['^', 'L_Pow'],
            51: [], # epsilon
            52: ['+', 'L_Unary'],
            53: ['-', 'L_Unary'],
            54: ['not', 'L_Unary'],
            55: ['Primary'],
            56: ['(', 'Expression', ')'],
            57: ['num'],
            58: ['string_lit'],
            59: ['bool_lit'],
            60: ['id', 'IdRest'],
            61: ['(', 'Args', ')'],
            62: [] # epsilon
        }

        # Parsing Table
        # Row: Non-terminal, Column: Terminal
        self.table = {
            'Program': {'start': 1},
            'Statements': {
                'int': 2, 'float': 2, 'string': 2, 'bool': 2, 'var': 2, 'id': 2, 
                'if': 2, 'while': 2, 'repeat': 2, 'read': 2, 'print': 2, 'func': 2, 'return': 2,
                'finish': 3, '}': 3
            },
            'Statement': {
                'int': 4, 'float': 5, 'string': 6, 'bool': 7, 'var': 8, 'id': 9,
                'if': 10, 'while': 11, 'repeat': 12, 'read': 13, 'print': 14, 'func': 15, 'return': 16
            },
            'DeclTailer': {';': 17, '=': 18},
            'AssignOrCall': {'=': 19, '(': 20},
            'Else': {
                'else': 21,
                'int': 22, 'float': 22, 'string': 22, 'bool': 22, 'var': 22, 'id': 22,
                'if': 22, 'while': 22, 'repeat': 22, 'read': 22, 'print': 22, 'func': 22, 'return': 22,
                'finish': 22, '}': 22
            },
            'Params': {'id': 23, ')': 24},
            'MoreParams': {',': 25, ')': 26},
            'Args': {
                '+': 27, '-': 27, 'not': 27, '(': 27, 'num': 27, 'string_lit': 27, 'bool_lit': 27, 'id': 27,
                ')': 28
            },
            'MoreArgs': {',': 29, ')': 30},
            'Expression': {'+': 31, '-': 31, 'not': 31, '(': 31, 'num': 31, 'string_lit': 31, 'bool_lit': 31, 'id': 31},
            "Expression'": {
                'or': 32,
                ';': 33, ')': 33, ',': 33, 'then': 33, '}': 33
            },
            'L_And': {'+': 34, '-': 34, 'not': 34, '(': 34, 'num': 34, 'string_lit': 34, 'bool_lit': 34, 'id': 34},
            "L_And'": {
                'and': 35,
                'or': 36, ';': 36, ')': 36, ',': 36, 'then': 36, '}': 36
            },
            'L_Rel': {'+': 37, '-': 37, 'not': 37, '(': 37, 'num': 37, 'string_lit': 37, 'bool_lit': 37, 'id': 37},
            "L_Rel'": {
                'RelOp': 38,
                'and': 39, 'or': 39, ';': 39, ')': 39, ',': 39, 'then': 39, '}': 39
            },
            'L_Add': {'+': 40, '-': 40, 'not': 40, '(': 40, 'num': 40, 'string_lit': 40, 'bool_lit': 40, 'id': 40},
            "L_Add'": {
                '+': 41, '-': 42,
                'RelOp': 43, 'and': 43, 'or': 43, ';': 43, ')': 43, ',': 43, 'then': 43, '}': 43
            },
            'L_Mul': {'+': 44, '-': 44, 'not': 44, '(': 44, 'num': 44, 'string_lit': 44, 'bool_lit': 44, 'id': 44},
            "L_Mul'": {
                '*': 45, '/': 46, '%': 47,
                '+': 48, '-': 48, 'RelOp': 48, 'and': 48, 'or': 48, ';': 48, ')': 48, ',': 48, 'then': 48, '}': 48
            },
            'L_Pow': {'+': 49, '-': 49, 'not': 49, '(': 49, 'num': 49, 'string_lit': 49, 'bool_lit': 49, 'id': 49},
            "L_Pow'": {
                '^': 50,
                '*': 51, '/': 51, '%': 51, '+': 51, '-': 51, 'RelOp': 51, 'and': 51, 'or': 51, ';': 51, ')': 51, ',': 51, 'then': 51, '}': 51
            },
            'L_Unary': {'+': 52, '-': 53, 'not': 54, '(': 55, 'num': 55, 'string_lit': 55, 'bool_lit': 55, 'id': 55},
            'Primary': {'(': 56, 'num': 57, 'string_lit': 58, 'bool_lit': 59, 'id': 60},
            'IdRest': {
                '(': 61,
                '^': 62, '*': 62, '/': 62, '%': 62, '+': 62, '-': 62, 'RelOp': 62, 'and': 62, 'or': 62, ';': 62, ')': 62, ',': 62, 'then': 62, '}': 62
            }
        }

    def get_terminal(self, token):
        if token.type == 'KEYWORD':
            return token.value.lower()
        if token.type == 'ID':
            return 'id'
        if token.type == 'BOOL_LIT':
            return 'bool_lit'
        if token.type == 'NUMBER':
            return 'num'
        if token.type == 'STRING':
            return 'string_lit'
        if token.type == 'REL_OP':
            return 'RelOp'
        if token.type == 'ARITH_OP' or token.type == 'DELIMITER':
            return token.value
        if token.type == '$':
            return '$'
        return None

    def parse(self):
        self.stack = [('$', None), ('Program', Node('Program'))]
        self.root = self.stack[1][1]
        
        while len(self.stack) > 0:
            top, node = self.stack.pop()
            current_token = self.tokens[self.current_token_idx]
            terminal = self.get_terminal(current_token)
            
            if top == '$':
                if terminal == '$':
                    return True, "Parsing successful", self.root
                else:
                    return False, f"Syntax Error: Expected end of program at line {current_token.line}, found '{current_token.value}'", None
            
            if top in self.table: # Non-terminal
                if terminal in self.table[top]:
                    prod_num = self.table[top][terminal]
                    rhs = self.productions[prod_num]
                    
                    # Create children nodes and push to stack in reverse
                    children_nodes = []
                    for symbol in rhs:
                        child_node = Node(symbol)
                        node.add_child(child_node)
                        children_nodes.append((symbol, child_node))
                    
                    for child in reversed(children_nodes):
                        self.stack.append(child)
                    
                    if not rhs: # ε production
                        node.add_child(Node("ε"))
                else:
                    expected = list(self.table[top].keys())
                    return False, f"Syntax Error at line {current_token.line}: Expected one of {expected}, but found '{current_token.value}'", None
            else: # Terminal
                if top == terminal:
                    if node:
                        node.name = f"{top} ({current_token.value})"
                    self.current_token_idx += 1
                else:
                    return False, f"Syntax Error at line {current_token.line}: Expected '{top}', but found '{current_token.value}'", None
        
        return True, "Parsing successful", self.root

def run_parser(source_code):
    scanner = LexicalScanner(source_code)
    tokens, symbols, lex_errors = scanner.scan()
    
    if lex_errors:
        return False, "Lexical errors found:\n" + "\n".join(lex_errors), None
    
    parser = Parser(tokens)
    success, message, tree = parser.parse()
    return success, message, tree

if __name__ == "__main__":
    test_code = """
START
    var count = 0;
    repeat {
        print "Count is: ";
        print count;
        count = count + 1;
    } while (count < 5)
FINISH
"""
    success, message, tree = run_parser(test_code)
    print(message)
    if success:
        tree.display()
