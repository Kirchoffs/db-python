class CatalogForm:
    pass

class CatalogBasic:
    def __init__(self, name):
        self.name = name
        self.rows = []
    
    def insert(self, row: CatalogForm):
        self.rows.append(row)
        
    def delete(self, condition):
        i = 0
        while i < len(self.rows):
            if condition(self.rows[i]):
                self.rows.pop(i)
                i -= 1
            i += 1
    
    def select(self, condition):
        return list(filter(condition, self.rows))

    def update(self, condition, update):
        pass