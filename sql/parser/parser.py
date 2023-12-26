import re
import sly

from sly import Lexer, Parser
from .ast import Select, Update, Delete, Insert
from .ast import Identifier, Star, Operation, FunctionOperation, OrderBy, Join, JoinType, BinaryOperation, Constant

class SQLLexer(Lexer):
    ignore = '\t\n\r '
    reflags = re.IGNORECASE
    
    tokens = {
        # DDL
        CREATE, DROP, DATABASE, TABLE, INDEX, EXPLAIN,
        
        # select
        SELECT, STAR, FROM, WHERE, GROUP_BY, ORDER_BY, ASC, DESC,
        
        JOIN, FULL, INNER, OUTER, LEFT, RIGHT, ON,
        
        # DML
        INSERT, DELETE, INTO, VALUES, UPDATE, SET,
        
        # punctuation
        DOT, COMMA, LPAREN, RPAREN,
        
        # operators
        EQ, NE, GT, GEQ, LT, LEQ,
        AND, OR, NOT,
        
        # data types
        ID, INTEGER, QUOTE_STRING, DQUOTE_STRING, FLOAT, BOOLEAN, NULL,
    }
    
    CREATE = 'CREATE'
    DROP = 'DROP'
    DATABASE = 'DATABASE'
    TABLE = 'TABLE'
    INDEX = 'INDEX'
    
    EXPLAIN = 'EXPLAIN'
    
    SELECT = 'SELECT'
    STAR = r'\*'
    FROM = 'FROM'
    WHERE = 'WHERE'
    GROUP_BY = 'GROUP BY'
    ORDER_BY = 'ORDER BY'
    ASC = 'ASC'
    DESC = 'DESC'
    
    JOIN = 'JOIN'
    FULL = 'FULL'
    INNER = 'INNER'
    OUTER = 'OUTER'
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'
    ON = 'ON'
    
    INSERT = 'INSERT'
    DELETE = 'DELETE'
    INTO = 'INTO'
    VALUES = 'VALUES'
    UPDATE = 'UPDATE'
    SET = 'SET'
    
    DOT = r'\.'
    COMMA = r','
    LPAREN = r'\('
    RPAREN = r'\)'
    
    EQ = r'='
    NE = r'!='
    GT = r'>'
    GEQ = r'>='
    LT = r'<'
    LEQ = r'<='
    AND = r'AND'
    OR = r'OR'
    NOT = r'NOT'
    
    INTEGER = r'\d+'
    
    @_(r'([a-zA-Z_][a-zA-Z0-9_]*)')
    def ID(self, t):
        return t
    
    DQUOTE_STRING = r'"[^"]*"'
    QUOTE_STRING = r"'[^']*'"

class SQLParser(Parser):
    tokens = SQLLexer.tokens
    
    precedence = (
        ('left', OR, AND),
        ('left', EQ, NE, GT, GEQ, LT, LEQ),
    )
    
    @_(
        "select",
        "update",
        "insert",
        "delete"
    )
    def query(self, p):
        return p[0]
    
    # select
    @_('SELECT target_columns')
    def select(self, p):
        return Select(targets = p.target_columns)
    
    @_('target_columns COMMA target_column')
    def target_columns(self, p):
        p.target_columns.append(p.target_column)
        return p.target_columns

    @_('target_column')
    def target_columns(self, p):
        return [p.target_column]
    
    @_('star')
    def target_column(self, p):
        return p.star
    
    @_('expr', 'function')
    def target_column(self, p):
        return p[0]
    
    @_('STAR')
    def star(self, p):
        return Star()
    
    @_('id LPAREN expr_list_or_nothing RPAREN')
    def function(self, p):
        args = p.expr_list_or_nothing
        if not args:
            args = []
        return FunctionOperation(op = p.id, args = args)
    
    @_('expr_list')
    def expr_list_or_nothing(self, p):
        return p.expr_list
    
    # from
    @_(
        'select FROM from_table', 
        'select FROM cross_join_tables', 
        'select FROM join_tables'
    )
    def select(self, p):
        select = p.select
        if select.from_table:
            raise SyntaxError('FROM clause already specified')

        select.from_table = p.from_table
        return select
    
    @_('identifier')
    def from_table(self, p):
        return p.identifier
    
    # where
    @_('select WHERE expr')
    def select(self, p):
        select = p.select
        if select.where:
            raise SyntaxError('WHERE clause already specified')
        if not select.from_table:
            raise SyntaxError('FROM clause not specified')
        
        where_expr = p.expr
        if not isinstance(where_expr, Operation):
            raise SyntaxError('WHERE clause must be an operation')
        select.where = where_expr
        return select
    
    # order by
    @_('select ORDER_BY ordering_term')
    def select(self, p):
        select = p.select
        if select.order_by:
            raise SyntaxError('ORDER BY clause already specified')
        if not select.from_table:
            raise SyntaxError('FROM clause not specified')
        select.order_by = p.ordering_term
        return select
    
    @_('identifier', 'identifier ASC')
    def ordering_term(self, p):
        return OrderBy(column = p.identifier, direction = 'ASC')
    
    @_('identifier DESC')
    def ordering_term(self, p):
        return OrderBy(column = p.identifier, direction = 'DESC')
    
    # group by
    @_('select GROUP_BY expr_list')
    def select(self, p):
        select = p.select
        if select.group_by:
            raise SyntaxError('GROUP BY clause already specified')
        if not select.from_table:
            raise SyntaxError('FROM clause not specified')
        
        group_by = p.expr_list
        if not isinstance(group_by, list):
            group_by = [group_by]
            
        select.group_by = group_by
        return select
    
    @_('from_table join_clause from_table ON expr')
    def join_tables(self, p):
        return Join(left = p[0], right = p[2], join_type = p.join_clause, condition = p.expr)
    
    @_(
        JoinType.LEFT_JOIN,
        JoinType.RIGHT_JOIN,
        JoinType.INNER_JOIN,
        JoinType.FULL_JOIN,
    )
    def join_clause(self, p):
        return ' '.join(p)
    
    @_('from_table COMMA from_table')
    def cross_join_tables(self, p):
        return Join(left = p[0], right = p[2], join_type = JoinType.CROSS_JOIN)
    
    @_(
        'expr EQ expr',
        'expr NE expr',
        'expr GEQ expr',
        'expr GT expr',
        'expr LEQ expr',
        'expr LT expr',
        'expr AND expr',
        'expr OR expr',
    )
    def expr(self, p):
        return BinaryOperation(op = p[1], args = (p.expr0, p.expr1))
    
    @_('expr')
    def expr_list(self, p):
        return [p.expr]
    
    @_('enum')
    def expr_list(self, p):
        return p.enum
    
    @_('enum COMMA expr')
    def enum(self, p):
        return p.enum + [p.expr]
    
    @_('expr COMMA expr')
    def enum(self, p):
        return [p.expr0, p.expr1]
    
    @_('identifier')
    def expr(self, p):
        return p.identifier

    @_('constant')
    def expr(self, p):
        return p.constant
    
    @_('NULL')
    def constant(self, p):
        return Constant(value = None)
    
    @_('integer')
    def constant(self, p):
        return Constant(value = int(p.integer))

    @_('string')
    def constant(self, p):
        return Constant(value = str(p.string))
        
    @_('identifier DOT identifier')
    def identifier(self, p):
        p.identifier0.parts += p.identifier1.parts
        return p.identifier0

    @_('id')
    def identifier(self, p):
        return Identifier(p.id)
    
    @_('ID')
    def id(self, p):
        return p.ID
    
    @_('quote_string', 'dquote_string')
    def string(self, p):
        return p[0]
    
    @_('INTEGER')
    def integer(self, p):
        return int(p[0])

    @_('QUOTE_STRING')
    def quote_string(self, p):
        return p[0].strip('\'')

    @_('DQUOTE_STRING')
    def dquote_string(self, p):
        return p[0].strip('\"')
    
    @_(
        'UPDATE identifier SET update_parameter_list',
        'UPDATE identifier SET update_parameter_list WHERE expr'
    )
    def update(self, p):
        where = getattr(p, 'expr', None)
        return Update(table = p.identifier, columns = p.update_parameter_list, where = where)
    
    @_(
        'update_parameter',
        'update_parameter_list COMMA update_parameter'
    )
    def update_parameter_list(self, p):
        params = getattr(p, 'update_parameter_list', {})
        params.update(p.update_parameter)
        return params
    
    @_('id EQ expr')
    def update_parameter(self, p):
        return {p.id: p.expr}
    
    @_(
        'DELETE FROM from_table WHERE expr',
        'DELETE FROM from_table'
    )
    def delete(self, p):
        where = getattr(p, 'expr', None)
        
        if where and not isinstance(where, Operation):
            raise SyntaxError('WHERE clause must be an operation')

        return Delete(table = p.from_table, where = where)
    
    @_(
        'INSERT INTO from_table LPAREN target_columns RPAREN VALUES expr_list_set',
        'INSERT INTO from_table VALUES expr_list_set'
    )
    def insert(self, p):
        columns = getattr(p, 'target_columns', None)
        return Insert(table = p.from_table, columns = columns, values = p.expr_list_set)
    
    @_('expr_list_set COMMA expr_list_set')
    def expr_list_set(self, p):
        return p.expr_list_set0 + p.expr_list_set1
    
    @_('LPAREN expr_list RPAREN')
    def expr_list_set(self, p):
        return [p.expr_list]
        
def query_parse(sql_stmt):
    lexer = SQLLexer()
    parser = SQLParser()
    tokens = lexer.tokenize(sql_stmt)
    return parser.parse(tokens)
