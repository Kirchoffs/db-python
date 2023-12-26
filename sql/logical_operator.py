from typing import Any, str
from catalog.entry import catalog_table
from common.fabric import TableColumn
from .parser.ast import BinaryOperation, Identifier, Constant

class LogicalOperator:
    def __init__(self, name):
        self.name = name
        self.children = []
        self.parent = None
        
    def add_child(self, operator):
        assert operator is not None
        
        if self.name != 'Join':
            assert operator.parent 
        
        self.children.append(operator)
        operator.parent = self
        
        return operator
    
class ScanOperator(LogicalOperator):
    def __init__(self, table_name):
        super().__init__('Scan')
        self.table_name = table_name
        self.columns = next(iter(catalog_table.select(lambda table: table.name == table_name))).columns
        self.condition = None

class Query(LogicalOperator):
    def __init__(self, projection_columns: str):
        super().__init__('Query')
        self.projection_columns = projection_columns
        self.scan_operators = []

class Condition:
    def __init__(self, operations: BinaryOperation):
        self.sign = operations.op
        
        self.left = self._to_table_column(operations.args[0])
        self.right = self._to_table_column(operations.args[1])

    @staticmethod
    def _to_table_column(node):
        if not isinstance(node, Identifier):
            assert isinstance(node, Constant)
            return node.value
        
        full_name = node.parts
        if '.' not in full_name:
            raise SyntaxError('Column name must be fully qualified')
        
        table_name, column_name = full_name.split('.')
        return TableColumn(table_name, column_name)

class FilterOperator(LogicalOperator):
    """
        Filter operator comes from 'WHERE' clause.
    """

    def __init__(self, condition: Condition):
        super().__init__('Filter')
        self.condition = condition

class JoinOperator(LogicalOperator):
    def __init__(self, join_type: str, left_table_name: str, right_table_name: str, join_condition: Condition):
        super().__init__('Join')
        self.join_type = join_type
        self.left_table_name = left_table_name
        self.right_table_name = right_table_name
        self.join_condition = join_condition

class SortOperator(LogicalOperator):
    def __init__(self, sort_column, asc = True):
        super().__init__('Sort')
        self.sort_column = sort_column
        self.asc = asc
        
class GroupOperator(LogicalOperator):
    def __init__(self, group_by_column, aggregate_function_name, aggregate_column):
        super().__init__('Group')
        self.group_by_column = group_by_column
        self.aggregate_function_name = aggregate_function_name
        self.aggregate_column = aggregate_column
