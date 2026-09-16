class SymbolTable:
    def __init__(self):
        # Stack of scopes, each scope is a dictionary: { name: { 'type': ..., 'kind': ..., 'params': ..., 'return_type': ..., 'line': ... } }
        self.scopes = [{}]

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name, symbol_info):
        # Declare in current (innermost) scope
        current_scope = self.scopes[-1]
        if name in current_scope:
            return False # Already declared in this scope
        current_scope[name] = symbol_info
        return True

    def lookup(self, name):
        # Look up from innermost to outermost scope
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def is_in_current_scope(self, name):
        return name in self.scopes[-1]

class SemanticAnalyzer:
    def __init__(self, root_node):
        self.root = root_node
        self.symbol_table = SymbolTable()
        self.errors = []
        self.current_function_return_type = None

    def analyze(self):
        # Entry Point Check
        if self.root and self.root.children:
            first_child_name = self.root.children[0].name.split(' ')[0].lower()
            if first_child_name != 'start':
                self.errors.append("Semantic Error: Program entry point 'START' not found.")
        else:
            self.errors.append("Semantic Error: Program entry point 'START' not found.")

        self.visit(self.root)
        return self.errors

    def error(self, message, line):
        self.errors.append(f"Semantic Error at line {line}: {message}")

    def visit(self, node):
        if node is None:
            return None
        
        method_name = f"visit_{node.name.split(' ')[0]}"
        # If node name is 'id (x)', we want 'visit_id'
        # Clean up node name for visitor mapping
        clean_name = node.name.split(' ')[0].replace("'", "_prime")
        method_name = f"visit_{clean_name}"
        
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for child in node.children:
            self.visit(child)
        return None

    # --- VISITOR METHODS ---

    def visit_Program(self, node):
        # Program: start Statements finish
        # (start/finish are tokens, Statements is non-terminal)
        for child in node.children:
            self.visit(child)

    def visit_Statements(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Statement(self, node):
        # Can be declaration, assignment, if, while, etc.
        first_child = node.children[0].name.split(' ')[0]
        
        if first_child in ['int', 'float', 'string', 'bool']:
            # Variable Declaration: type id DeclTailer
            var_type = first_child
            var_id_node = node.children[1]
            var_name = self.extract_value(var_id_node)
            line = self.extract_line(var_id_node)
            
            if not self.symbol_table.declare(var_name, {'type': var_type, 'kind': 'var', 'line': line}):
                self.error(f"Variable '{var_name}' already declared in this scope.", line)
            
            # Handle DeclTailer (init or just ;)
            self.visit_DeclTailer(node.children[2], var_name, var_type)
            
        elif first_child == 'var':
            # Assignment/Declaration: var id = Expression ;
            var_id_node = node.children[1]
            var_name = self.extract_value(var_id_node)
            line = self.extract_line(var_id_node)
            
            # For 'var' keyword, we infer type from Expression
            expr_type = self.visit(node.children[3])
            
            if not self.symbol_table.declare(var_name, {'type': expr_type, 'kind': 'var', 'line': line}):
                self.error(f"Variable '{var_name}' already declared in this scope.", line)

        elif first_child == 'id':
            # AssignOrCall: id AssignOrCall
            var_name = self.extract_value(node.children[0])
            line = self.extract_line(node.children[0])
            symbol = self.symbol_table.lookup(var_name)
            
            if not symbol:
                self.error(f"Identifier '{var_name}' used before declaration.", line)
                return
            
            self.visit_AssignOrCall(node.children[1], var_name, symbol, line)

        elif first_child == 'func':
            # func id ( Params ) { Statements }
            func_id_node = node.children[1]
            func_name = self.extract_value(func_id_node)
            line = self.extract_line(func_id_node)
            
            self.symbol_table.enter_scope()
            params = self.visit(node.children[3]) # Returns list of (name, type)
            self.symbol_table.exit_scope()
            
            # Use 'any' as default return type until return statement is found
            func_info = {
                'type': 'any', 
                'kind': 'func', 
                'params': params, 
                'return_type': 'any',
                'line': line
            }
            if not self.symbol_table.declare(func_name, func_info):
                self.error(f"Function '{func_name}' already declared.", line)
                
            # Now analyze body
            self.symbol_table.enter_scope()
            # Declare params in function scope
            if params:
                for p_name, p_type in params:
                    self.symbol_table.declare(p_name, {'type': p_type, 'kind': 'var', 'line': line})
            
            old_func_ret = self.current_function_return_type
            self.current_function_return_type = 'any'
            self.visit(node.children[6]) # Statements
            self.current_function_return_type = old_func_ret
            self.symbol_table.exit_scope()

        elif first_child == 'return':
            # return Expression ;
            expr_type = self.visit(node.children[1])
            # Return Type Correctness
            if self.current_function_return_type is not None:
                if not self.types_match(self.current_function_return_type, expr_type):
                    line = self.extract_line(node.children[0])
                    self.error(f"Type Error: Return type '{expr_type}' does not match expected return type '{self.current_function_return_type}'.", line)
            return expr_type

        else:
            # if, while, repeat, read, print
            self.generic_visit(node)

    def visit_DeclTailer(self, node, var_name, var_type):
        # DeclTailer: ; | = Expression ;
        if len(node.children) > 1: # = Expression ;
            expr_type = self.visit(node.children[1])
            if not self.types_match(var_type, expr_type):
                line = self.extract_line(node.children[0])
                self.error(f"Type mismatch: cannot assign '{expr_type}' to '{var_type}'.", line)

    def visit_AssignOrCall(self, node, name, symbol, line):
        # AssignOrCall: = Expression ; | ( Args ) ;
        first_child = node.children[0].name.split(' ')[0]
        if first_child == '=':
            if symbol['kind'] != 'var':
                self.error(f"Cannot assign to '{name}', it is a {symbol['kind']}.", line)
            expr_type = self.visit(node.children[1])
            if not self.types_match(symbol['type'], expr_type):
                self.error(f"Type mismatch: cannot assign '{expr_type}' to '{symbol['type']}'.", line)
        elif first_child == '(':
            if symbol['kind'] != 'func':
                self.error(f"'{name}' is not a function and cannot be called.", line)
            else:
                # Rule 9: Function Argument Match
                args = self.visit(node.children[1]) if len(node.children) > 1 else []
                if args is None:
                    args = []
                expected_count = len(symbol['params']) if symbol.get('params') else 0
                actual_count = len(args) if isinstance(args, list) else 0
                if actual_count != expected_count:
                    self.error(f"Function '{name}' expected {expected_count} params, found {actual_count}.", line)

    def visit_Params(self, node):
        # Params: id MoreParams | ε
        if not node.children or node.children[0].name == 'ε':
            return []
        
        params = []
        p_id = self.extract_value(node.children[0])
        # For our simple grammar, params might need types. 
        # If grammar doesn't specify param types, we might assume generic or 'any'.
        # Looking at grammar 23: Params -> id MoreParams. 
        # This language seems to have untyped params? Or types are elsewhere.
        params.append((p_id, 'any')) 
        params.extend(self.visit(node.children[1]))
        return params

    def visit_MoreParams(self, node):
        # MoreParams: , id MoreParams | ε
        if not node.children or node.children[0].name == 'ε':
            return []
        params = []
        p_id = self.extract_value(node.children[1])
        params.append((p_id, 'any'))
        params.extend(self.visit(node.children[2]))
        return params

    def visit_Expression(self, node):
        # Expression -> L_And Expression'
        t1 = self.visit(node.children[0])
        return self.visit_Expression_prime(node.children[1], t1)

    def visit_Expression_prime(self, node, left_type):
        # Expression' -> or L_And Expression' | ε
        if not node.children or node.children[0].name == 'ε':
            return left_type
        right_type = self.visit(node.children[1])
        if left_type != 'bool' or right_type != 'bool':
            self.error("Logical 'or' requires boolean operands.", -1) # Line tracking needs improvement
            return 'error'
        return self.visit_Expression_prime(node.children[2], 'bool')

    # ... and so on for L_And, L_Rel, L_Add, L_Mul, L_Pow, L_Unary, Primary ...
    # For brevity in this initial implementation, I'll focus on the core logic.

    def visit_Primary(self, node):
        # Primary: ( Expression ) | num | string_lit | bool_lit | id IdRest
        type_name = node.children[0].name.split(' ')[0]
        if type_name == '(':
            return self.visit(node.children[1])
        elif type_name == 'num':
            val = self.extract_value(node.children[0])
            return 'float' if '.' in val else 'int'
        elif type_name == 'string_lit':
            return 'string'
        elif type_name == 'bool_lit':
            return 'bool'
        elif type_name == 'id':
            name = self.extract_value(node.children[0])
            symbol = self.symbol_table.lookup(name)
            if not symbol:
                # We need to know the line. extract_line is not implemented properly yet.
                self.error(f"Identifier '{name}' used before declaration.", -1)
                return 'error'
            # IdRest handles function calls
            return self.visit_IdRest(node.children[1], symbol)
        return 'error'

    def visit_IdRest(self, node, symbol):
        # IdRest: ( Args ) | ε
        if not node.children or node.children[0].name == 'ε':
            return symbol['type']
        # Function call
        return symbol['return_type']

    def visit_L_And(self, node):
        t1 = self.visit(node.children[0])
        return self.visit_L_And_prime(node.children[1], t1)

    def visit_L_And_prime(self, node, left_type):
        if not node.children or node.children[0].name == 'ε':
            return left_type
        right_type = self.visit(node.children[1])
        if left_type != 'bool' or right_type != 'bool':
            self.error("Logical 'and' requires boolean operands.", -1)
            return 'error'
        return self.visit_L_And_prime(node.children[2], 'bool')

    def visit_L_Rel(self, node):
        t1 = self.visit(node.children[0])
        return self.visit_L_Rel_prime(node.children[1], t1)

    def visit_L_Rel_prime(self, node, left_type):
        if not node.children or node.children[0].name == 'ε':
            return left_type
        # RelOp L_Add
        op = self.extract_value(node.children[0])
        right_type = self.visit(node.children[1])
        # Comparison usually results in bool
        if not self.check_comparison(left_type, right_type, op):
            self.error(f"Cannot compare {left_type} and {right_type} with {op}.", -1)
            return 'error'
        return 'bool'

    def visit_L_Add(self, node):
        t1 = self.visit(node.children[0])
        return self.visit_L_Add_prime(node.children[1], t1)

    def visit_L_Add_prime(self, node, left_type):
        if not node.children or node.children[0].name == 'ε':
            return left_type
        op = self.extract_value(node.children[0])
        right_type = self.visit(node.children[1])
        res_type = self.check_arithmetic(left_type, right_type, op)
        return self.visit_L_Add_prime(node.children[2], res_type)

    def visit_L_Mul(self, node):
        t1 = self.visit(node.children[0])
        return self.visit_L_Mul_prime(node.children[1], t1)

    def visit_L_Mul_prime(self, node, left_type):
        if not node.children or node.children[0].name == 'ε':
            return left_type
        op = self.extract_value(node.children[0])
        right_type = self.visit(node.children[1])
        # Division by Zero
        if op == '/':
            right_value = self.extract_value(node.children[1])
            if right_value == '0':
                line = self.extract_line(node.children[0])
                self.error("Division by zero is not allowed.", line)
        res_type = self.check_arithmetic(left_type, right_type, op)
        return self.visit_L_Mul_prime(node.children[2], res_type)

    def visit_L_Pow(self, node):
        t1 = self.visit(node.children[0])
        return self.visit_L_Pow_prime(node.children[1], t1)

    def visit_L_Pow_prime(self, node, left_type):
        if not node.children or node.children[0].name == 'ε':
            return left_type
        right_type = self.visit(node.children[1])
        res_type = self.check_arithmetic(left_type, right_type, '^')
        return res_type

    def visit_L_Unary(self, node):
        # L_Unary: + L_Unary | - L_Unary | not L_Unary | Primary
        type_name = node.children[0].name.split(' ')[0]
        if type_name in ['+', '-']:
            t = self.visit(node.children[1])
            if t not in ['int', 'float']:
                self.error(f"Unary {type_name} requires numeric operand.", -1)
                return 'error'
            return t
        elif type_name == 'not':
            t = self.visit(node.children[1])
            if t != 'bool':
                self.error("Unary 'not' requires boolean operand.", -1)
                return 'error'
            return 'bool'
        else:
            return self.visit(node.children[0])

    def check_comparison(self, t1, t2, op):
        if t1 == 'error' or t2 == 'error': return True # Already reported
        if t1 in ['int', 'float'] and t2 in ['int', 'float']: return True
        if t1 == t2: return True
        return False

    # Helper methods
    def extract_value(self, node):
        # Node name is often "type (value)"
        match = re.search(r'\((.*)\)', node.name)
        return match.group(1) if match else node.name

    def extract_line(self, node):
        # This is tricky if parser didn't store line in node.
        # I'll need to modify the Parser or estimate.
        # For now, let's assume -1 or try to find it.
        return -1 

    def types_match(self, t1, t2):
        if t1 == t2: return True
        if t1 == 'float' and t2 == 'int': return True # Implicit cast
        if t1 == 'any' or t2 == 'any': return True
        return False

    def check_arithmetic(self, t1, t2, op):
        if t1 == 'error' or t2 == 'error': return 'error'
        if t1 == 'any' or t2 == 'any': return 'any'
        if t1 in ['int', 'float'] and t2 in ['int', 'float']:
            return 'float' if (t1 == 'float' or t2 == 'float') else 'int'
        self.error(f"Invalid operands for {op}: {t1} and {t2}", -1)
        return 'error'

    def check_comparison(self, t1, t2, op):
        if t1 == 'error' or t2 == 'error': return True 
        if t1 == 'any' or t2 == 'any': return True
        if t1 in ['int', 'float'] and t2 in ['int', 'float']: return True
        if t1 == t2: return True
        return False

import re
