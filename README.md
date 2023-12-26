# Notes
## Project Notes
### Interface
- exec_query(sql_stmt: str) -> Result
- query_parser(sql_stmt: str) -> ASTNode
- query_plan(ast_node: ASTNode) -> PlanTree
- exec_plan(plan_tree: PlanTree) -> Result

## Database Notes
### Operator
SPJ Operator: Select-Project-Join Operator

## Python Notes
### Create New Environment
```
>> python -m venv .env
>> source .env/bin/activate
```

### Install Dependencies
```
>> python -m pip install sly
```

### Run
```
>> python -m tests.test_ast
```

```
>> python -m unittest discover
```

### General Project Setup
#### init.sh
```
if [ ! -d '.env' ]; then
    python -m venv .env
fi
```

#### start.sh
```
source .env/bin/activate
pip install -r requirements.txt
```

#### requirements.txt
```
sly
```

### Python Package
#### `__init__.py`
In Python projects, if you create a file called `__init__.py` in a directory then Python will treat that directory as a package. A package in Python is a collection of modules (individual .py files) that can be imported into other Python files.

Since Python version 3.3 and the implementation of PEP 420, Python will automatically create __Namespace Packages__ implicitly in many cases. This means that `__init__.py` is now often optional, but it’s still useful to structure your initialization code.
