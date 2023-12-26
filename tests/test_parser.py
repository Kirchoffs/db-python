import unittest

from sql.parser.parser import query_parse

class TestParser(unittest.TestCase):
    def test_select_parser(self):
        ast = query_parse('SELECT a, b FROM t')
        print(ast)

        ast = query_parse('SELECT a, b FROM t WHERE a > b')
        print(ast)

        ast = query_parse('SELECT a, b, c FROM t WHERE a > b ORDER BY c')
        print(ast)

        ast = query_parse('SELECT a, b, c FROM t WHERE a > b GROUP BY c ORDER BY c DESC')
        print(ast)

        ast = query_parse('SELECT a, b, c FROM t WHERE a > b AND c > 42')
        print(ast)

        ast = query_parse('SELECT a, b, c FROM t WHERE a > b AND c = "answer"')
        print(ast)

        ast = query_parse('select a, b from t where a > b')
        print(ast)
        
    def test_update_parser(self):
        ast = query_parse('UPDATE t SET a = 1 WHERE b > 42')
        print(ast)
        
    def test_insert_parser(self):
        ast = query_parse('INSERT INTO t (a, b) VALUES (1, 2)')
        print(ast)
    
    def test_delete_parser(self):
        ast = query_parse('DELETE FROM t WHERE a > 42')
        print(ast)

if __name__ == '__main__':
    unittest.main()
