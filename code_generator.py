import re

class CodeGenerator:
    def __init__(self, root_node):
        self.root = root_node
        self.python_code = ""
        self.indent_level = 0

    def generate(self):
        self.python_code = self.visit(self.root)
        return self.python_code

    def indent(self):
        return "    " * self.indent_level

    def visit(self, node):
        if node is None:
            return ""
        
        clean_name = node.name.split(' ')[0].replace("'", "_prime")
        method_name = f"visit_{clean_name}"
        
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        res = ""
        for child in node.children:
            res += self.visit(child)
        return res

    # --- VISITOR METHODS ---

    def visit_Program(self, node):
        # Program: start Statements finish
        # We ignore start/finish in Python output
        return self.visit(node.children[1])

    def visit_Statements(self, node):
        res = ""
        for child in node.children:
            if child.name != 'ε':
                res += self.visit(child)
        return res

    def visit_Statement(self, node):
        first_child = node.children[0].name.split(' ')[0]
        
        if first_child in ['int', 'float', 'string', 'bool']:
            # type id DeclTailer
            var_name = self.extract_value(node.children[1])
            # Handle DeclTailer
            return self.visit_DeclTailer(node.children[2], var_name)
            
        elif first_child == 'var':
            # var id = Expression ;
            var_name = self.extract_value(node.children[1])
            expr = self.visit(node.children[3])
            return f"{self.indent()}{var_name} = {expr}\n"

        elif first_child == 'id':
            # id AssignOrCall
            var_name = self.extract_value(node.children[0])
            return self.visit_AssignOrCall(node.children[1], var_name)

        elif first_child == 'if':
            # if ( Expression ) then { Statements } Else
            expr = self.visit(node.children[2])
            res = f"{self.indent()}if {expr}:\n"
            self.indent_level += 1
            statements = self.visit(node.children[6])
            if not statements.strip(): res += f"{self.indent()}pass\n"
            else: res += statements
            self.indent_level -= 1
            res += self.visit(node.children[8]) # Else
            return res

        elif first_child == 'while':
            # while ( Expression ) { Statements }
            expr = self.visit(node.children[2])
            res = f"{self.indent()}while {expr}:\n"
            self.indent_level += 1
            statements = self.visit(node.children[5])
            if not statements.strip(): res += f"{self.indent()}pass\n"
            else: res += statements
            self.indent_level -= 1
            return res

        elif first_child == 'repeat':
            # repeat { Statements } while ( Expression )
            # Translates to: while True: ... if not cond: break
            res = f"{self.indent()}while True:\n"
            self.indent_level += 1
            statements = self.visit(node.children[2])
            if not statements.strip(): res += f"{self.indent()}pass\n"
            else: res += statements
            expr = self.visit(node.children[6])
            res += f"{self.indent()}if not ({expr}): break\n"
            self.indent_level -= 1
            return res

        elif first_child == 'read':
            # read id ;
            var_name = self.extract_value(node.children[1])
            # We use input() and assume type from usage or just keep as string/float
            return f"{self.indent()}{var_name} = input()\n"

        elif first_child == 'print':
            # print Expression ;
            expr = self.visit(node.children[1])
            return f"{self.indent()}print({expr})\n"

        elif first_child == 'func':
            # func id ( Params ) { Statements }
            func_name = self.extract_value(node.children[1])
            params = self.visit(node.children[3])
            res = f"{self.indent()}def {func_name}({params}):\n"
            self.indent_level += 1
            statements = self.visit(node.children[6])
            if not statements.strip(): res += f"{self.indent()}pass\n"
            else: res += statements
            self.indent_level -= 1
            return res

        elif first_child == 'return':
            # return Expression ;
            expr = self.visit(node.children[1])
            return f"{self.indent()}return {expr}\n"

        return ""

    def visit_DeclTailer(self, node, var_name):
        # ; | = Expression ;
        if len(node.children) == 1:
            # Just a declaration, in Python we can initialize to None or 0
            return f"{self.indent()}{var_name} = None\n"
        else:
            expr = self.visit(node.children[1])
            return f"{self.indent()}{var_name} = {expr}\n"

    def visit_AssignOrCall(self, node, name):
        # = Expression ; | ( Args ) ;
        first_child = node.children[0].name.split(' ')[0]
        if first_child == '=':
            expr = self.visit(node.children[1])
            return f"{self.indent()}{name} = {expr}\n"
        elif first_child == '(':
            args = self.visit(node.children[1])
            return f"{self.indent()}{name}({args})\n"
        return ""

    def visit_Params(self, node):
        if not node.children or node.children[0].name == 'ε':
            return ""
        p_id = self.extract_value(node.children[0])
        more = self.visit(node.children[1])
        return p_id + more

    def visit_MoreParams(self, node):
        if not node.children or node.children[0].name == 'ε':
            return ""
        p_id = self.extract_value(node.children[1])
        more = self.visit(node.children[2])
        return ", " + p_id + more

    def visit_Args(self, node):
        if not node.children or node.children[0].name == 'ε':
            return ""
        expr = self.visit(node.children[0])
        more = self.visit(node.children[1])
        return expr + more

    def visit_MoreArgs(self, node):
        if not node.children or node.children[0].name == 'ε':
            return ""
        expr = self.visit(node.children[1])
        more = self.visit(node.children[2])
        return ", " + expr + more

    def visit_Expression(self, node):
        t1 = self.visit(node.children[0])
        return self.visit_Expression_prime(node.children[1], t1)

    def visit_Expression_prime(self, node, left):
        if not node.children or node.children[0].name == 'ε':
            return left
        right = self.visit(node.children[1])
        res = f"({left} or {right})"
        return self.visit_Expression_prime(node.children[2], res)

    def visit_L_And(self, node):
        t1 = self.visit(node.children[0])
        return self.visit_L_And_prime(node.children[1], t1)

    def visit_L_And_prime(self, node, left):
        if not node.children or node.children[0].name == 'ε':
            return left
        right = self.visit(node.children[1])
        res = f"({left} and {right})"
        return self.visit_L_And_prime(node.children[2], res)

    def visit_L_Rel(self, node):
        t1 = self.visit(node.children[0])
        return self.visit_L_Rel_prime(node.children[1], t1)

    def visit_L_Rel_prime(self, node, left):
        if not node.children or node.children[0].name == 'ε':
            return left
        op = self.extract_value(node.children[0])
        right = self.visit(node.children[1])
        return f"({left} {op} {right})"

    def visit_L_Add(self, node):
        t1 = self.visit(node.children[0])
        return self.visit_L_Add_prime(node.children[1], t1)

    def visit_L_Add_prime(self, node, left):
        if not node.children or node.children[0].name == 'ε':
            return left
        op = self.extract_value(node.children[0])
        right = self.visit(node.children[1])
        res = f"({left} {op} {right})"
        return self.visit_L_Add_prime(node.children[2], res)

    def visit_L_Mul(self, node):
        t1 = self.visit(node.children[0])
        return self.visit_L_Mul_prime(node.children[1], t1)

    def visit_L_Mul_prime(self, node, left):
        if not node.children or node.children[0].name == 'ε':
            return left
        op = self.extract_value(node.children[0])
        right = self.visit(node.children[1])
        res = f"({left} {op} {right})"
        return self.visit_L_Mul_prime(node.children[2], res)

    def visit_L_Pow(self, node):
        t1 = self.visit(node.children[0])
        return self.visit_L_Pow_prime(node.children[1], t1)

    def visit_L_Pow_prime(self, node, left):
        if not node.children or node.children[0].name == 'ε':
            return left
        # ^ is ** in Python
        right = self.visit(node.children[1])
        return f"({left} ** {right})"

    def visit_L_Unary(self, node):
        first = node.children[0].name.split(' ')[0]
        if first in ['+', '-']:
            inner = self.visit(node.children[1])
            return f"({first}{inner})"
        elif first == 'not':
            inner = self.visit(node.children[1])
            return f"(not {inner})"
        else:
            return self.visit(node.children[0])

    def visit_Primary(self, node):
        type_name = node.children[0].name.split(' ')[0]
        if type_name == '(':
            return f"({self.visit(node.children[1])})"
        elif type_name in ['num', 'string_lit', 'bool_lit']:
            return self.extract_value(node.children[0])
        elif type_name == 'id':
            name = self.extract_value(node.children[0])
            rest = self.visit_IdRest(node.children[1])
            return f"{name}{rest}"
        return ""

    def visit_IdRest(self, node):
        if not node.children or node.children[0].name == 'ε':
            return ""
        args = self.visit(node.children[1])
        return f"({args})"

    def visit_Else(self, node):
        if not node.children or node.children[0].name == 'ε':
            return ""
        res = f"{self.indent()}else:\n"
        self.indent_level += 1
        statements = self.visit(node.children[2])
        if not statements.strip(): res += f"{self.indent()}pass\n"
        else: res += statements
        self.indent_level -= 1
        return res

    def extract_value(self, node):
        # Handle cases like "id (x)", "num (5)", "RelOp (==)"
        if '(' in node.name and ')' in node.name:
            return node.name[node.name.find("(")+1:node.name.rfind(")")]
        return node.name

    def execute(self, code):
        print("\n--- EXECUTING GENERATED PYTHON CODE ---")
        try:
            compiled = compile(code, '<string>', 'exec')
            exec(compiled)
        except Exception as e:
            print(f"Execution Error: {e}")
