from .basic import CatalogForm, CatalogBasic

class CatalogTableForm(CatalogForm):
    def __init__(self, table_name, column_names, types):
        self.table_name = table_name
        self.column_names = column_names
        self.types = types
        assert len(column_names) == len(types)

class CatalogTable(CatalogBasic):
    def __init__(self):
        super().__init__('table_information')
        