from antlr4 import InputStream, CommonTokenStream
from src.parser.grammar.TSqlLexer import TSqlLexer
from src.parser.grammar.TSqlParser import TSqlParser


def parse_sql(sql_text: str):
    input_stream = InputStream(sql_text)
    lexer = TSqlLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = TSqlParser(token_stream)
    tree = parser.tsql_file()
    return tree, parser


def parse_sql_file(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="cp1252") as f:
            sql = f.read()

    return parse_sql(sql)