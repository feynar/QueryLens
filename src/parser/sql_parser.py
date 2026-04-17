"""
QueryLens — SQL Parser Utilities

Provides helper functions for parsing SQL text and SQL files using
the ANTLR-generated T-SQL lexer and parser.

Used by:
    - static analyzer
    - feature extractor
    - other AST-based analysis components
"""
from antlr4 import InputStream, CommonTokenStream
from src.parser.grammar.TSqlLexer import TSqlLexer
from src.parser.grammar.TSqlParser import TSqlParser


def parse_sql(sql_text: str):
    """
    Parses a SQL string into an ANTLR parse tree and parser instance.

    Returns:
        tuple: (parse_tree, parser)
    """    
    input_stream = InputStream(sql_text)
    lexer = TSqlLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = TSqlParser(token_stream)
    tree = parser.tsql_file()
    return tree, parser


def parse_sql_file(path: str):
    """
    Reads a SQL file from disk and parses it into an ANTLR parse tree.

    Attempts UTF-8 first, then falls back to cp1252 for compatibility
    with Windows-encoded files.
    """    
    try:
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="cp1252") as f:
            sql = f.read()

    return parse_sql(sql)