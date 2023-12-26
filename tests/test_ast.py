import unittest
from sql.parser.ast import ASTNode

class TestASTNode(ASTNode):
    def __init__(self, name, age):
        super().__init__()
        self.name = name
        self.age = age

class TestAST(unittest.TestCase):
    def test_ast(self):
        ast = TestASTNode('John', '35')
        self.assertEqual(ast.name, 'John')
        self.assertEqual(ast.age, '35')
        self.assertEqual(str(ast), '<TestASTNode> { name=John age=35 }')

if __name__ == '__main__':
    unittest.main()
