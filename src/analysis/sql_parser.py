from antlr4 import *
from parser.grammar.TSqlLexer import TSqlLexer
from parser.grammar.TSqlParser import TSqlParser


def parse_sql_text(sql_text):
    input_stream = InputStream(sql_text)
    lexer = TSqlLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = TSqlParser(token_stream)
    tree = parser.tsql_file()
    return tree, parser


def parse_sql_file(path):
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    return parse_sql_text(sql)
