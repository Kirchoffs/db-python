# Notes
## Open Source Parser Generator
- For C/C++, Bison / Flex is a good choice for parser generator.
- For Python, SLY / PLY is a good choice for parser generator. We use SLY in this project.

## BNF
```
select: SELECT target_columns
      | select FROM from_table
      | select FROM cross_join_tables
      | select FROM joint_tables
      | select WHERE expr

target_columns: target_column
              | target_columns ',' target_column

target_column: star
             | expr
             | function

star: STAR

function: id LPARAM expr_list_or_nothing RPARAM

expr_list_or_nothing: expr_list

from_table: identifier

expr_list: expr
         | enum

enum: expr COMMA expr
    | enum COMMA expr

expr: expr EQ expr,
    | expr NE expr,
    | expr GEQ expr,
    | expr GT expr,
    | expr LEQ expr,
    | expr LT expr,
    | expr AND expr,
    | expr OR expr,

expr: identifier
    | constant

identifier: identifier DOT identifier
          | id

constant: NULL
        | integer
        | string

integer: INTEGER

string: quote_string
      | dquote_string

quote_string: QUOTE_STRING

dquote_string: DQUOTE_STRING

id: ID
```
