from sql.parser.ast import Select, Identifier, Join, Star, FunctionOperation, JoinType
from sql.logical_operator import Query, ScanOperator, FilterOperator, JoinOperator, GroupOperator, SortOperator, Condition
from catalog import catalog_table
from errors import SQLLogicalPlanError
from common.fabric import TableColumn
from sql.utils import table_exists, column_exists

class SelectTransformer:
    @staticmethod
    def transform(ast: Select):
        query = Query(None)
        SelectTransformer.transform_clause_from(query, ast)
        SelectTransformer.transform_target_list(query, ast)
        SelectTransformer.transform_clause_where(query, ast)
        SelectTransformer.transform_clause_join(query, ast)
        SelectTransformer.transform_clause_order(query, ast)
        SelectTransformer.transform_clause_group(query, ast)
        
        SelectTransformer.rewrite(query, ast)
        return query
    
    @staticmethod
    def transform_clause_from(ast, query):
        unchecked_tables = []
        if isinstance(ast.from_table, Identifier):
            unchecked_tables.append(ast.from_table.parts)
        elif isinstance(ast.from_table, Join):
            unchecked_tables.append(ast.from_table.left.parts)
            unchecked_tables.append(ast.from_table.right.parts)
        else:
            raise
        
        checked_tables = []
        for table_name in unchecked_tables:
            results = catalog_table.select(lambda table: table.name == table_name)
            if len(results) != 1:
                raise SQLLogicalPlanError(f'Table {table_name} not found')
            checked_tables.append(table_name)
                
        for table_name in checked_tables:
            query.scan_operators.append(ScanOperator(table_name))
    
    @staticmethod
    def transform_target_list(ast, query):
        target_list = []
        for target in ast.targets:
            if isinstance(target, Star):
                for scan_operator in query.scan_operators:
                    table_name = scan_operator.table_name
                    results = catalog_table.select(lambda table: table.name == table_name)
                    for column_name in next(iter(results)).columns:
                        target_list.append(TableColumn(table_name, column_name))
                query.projection_columns.append(target.parts)
            elif isinstance(target, Identifier):
                full_name = target.parts
                if '.' not in full_name:
                    raise SQLLogicalPlanError('Column name must be fully qualified')
                table_name, column_name = full_name.split('.')
                target_list.append(TableColumn(table_name, column_name))
            elif isinstance(target, FunctionOperation):
                pass
            else:
                raise
        
        query.projection_columns.extend(target_list)
    
    @staticmethod
    def transform_clause_where(ast, query):
        if not ast.where:
            return
        query.where_condition = FilterOperator(Condition(ast.where))
    
    @staticmethod
    def transform_clause_join(ast, query):
        if not isinstance(ast.from_table, Join):
            return
        join_ast = ast.from_table
        
        left_table_name = join_ast.left.parts
        right_table_name = join_ast.right.parts
        if not table_exists(left_table_name):
            raise SQLLogicalPlanError(f'Table {left_table_name} not found')
        if not table_exists(right_table_name):
            raise SQLLogicalPlanError(f'Table {right_table_name} not found')
        
        join_condition = Condition(join_ast.condition)
        if isinstance(join_condition.left, TableColumn) and column_exists(join_condition.left.table_name, join_condition.left.column_name):
            raise SQLLogicalPlanError(f'Column {join_condition.left} not found')
        if isinstance(join_condition.right, TableColumn) and column_exists(join_condition.right.table_name, join_condition.right.column_name):
            raise SQLLogicalPlanError(f'Column {join_condition.right} not found')
        
        join_operator = JoinOperator(
            join_type = join_ast.join_type,
            left_table_name = left_table_name,
            right_table_name = right_table_name,
            join_condition = join_condition
        )
        
        query.join_operator = join_operator
        
        for scan_operator in query.scan_operators:
            if scan_operator.table_name == join_operator.left_table_name:
                join_operator.add_child(scan_operator)
            if scan_operator.table_name == join_operator.right_table_name:
                join_operator.add_child(scan_operator)
 
    @staticmethod
    def transform_clause_order(ast, query):
        if not ast.order_by:
            return
        
        full_name = ast.order_by.column
        if '.' not in full_name:
            raise SQLLogicalPlanError('Column name must be fully qualified')
        table_name, column_name = full_name.split('.')
        
        if not column_exists(table_name, column_name):
            raise SQLLogicalPlanError(f'Column {full_name} not found')
        
        query.sort_operator = SortOperator(
            sort_column = TableColumn(table_name, column_name),
            asc = ast.order_by.direction == 'ASC'
        )
        
        pass
    
    @staticmethod
    def transform_clause_group(ast, query):
        if not ast.group_by:
            return
        
        full_name = ast.group_by.column
        if '.' not in full_name:
            raise SQLLogicalPlanError('Column name must be fully qualified')
        table_name, column_name = full_name.split('.')
        
        if not column_exists(table_name, column_name):
            raise SQLLogicalPlanError(f'Column {full_name} not found')
        query.group_by_column = TableColumn(table_name, column_name)
        
        raise NotImplementedError
    
    @staticmethod
    def rewrite(query):
        building_node = query
        if query.group_by_column:
            operator = GroupOperator(
                group_by_column = query.group_by_column,
                aggregate_function_name = None,
                aggregate_column = None
            )

            building_node = building_node.add_child(operator)
        
        if query.sort_operator:
            building_node = building_node.add_child(query.sort_operator)
        
        if query.join_operator:
            building_node = building_node.add_child(query.join_operator)
        
        if query.where_condition:
            filter_operator = query.where_condition
            
            if isinstance(filter_operator.condition.left, TableColumn) and isinstance(filter_operator.condition.right, TableColumn):
                table_names = (query.join_operator.left_table_name, query.join_operator.right_table_name)
                
                if not (query.join_operator and filter_operator.condition.left.table_name in table_names and filter_operator.condition.right.table_name in table_names):
                    raise SQLLogicalPlanError('Table in where clause should be all seen in the join clause')
                
                if query.join_operator.join_type != JoinType.CROSS_JOIN:
                    raise NotImplementedError('Not support join condition in where clause')
            
                query.join_operator.join_type = JoinType.INNER_JOIN
                query.join_operator.condition = filter_operator.condition
            else:
                table_column = None
                if isinstance(filter_operator.condition.left, TableColumn):
                    table_column = filter_operator.condition.left
                elif isinstance(filter_operator.condition.right, TableColumn):
                    table_column = filter_operator.condition.right
                else:
                    pass
                
                if table_column:
                    for scan_operator in query.scan_operators:
                        if scan_operator.table_name == table_column.table_name:
                            scan_operator.condition = filter_operator.condition
    