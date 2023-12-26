from catalog import catalog_table

def table_exists(table_name):
    return bool(catalog_table.select(lambda r: r.table_name == table_name))

def column_exists(table_name, column_name):
    tables = catalog_table.select(lambda r: r.table_name == table_name)
    if len(tables) == 1 and column_name in next(iter(tables)).columns:
        return True
    return False