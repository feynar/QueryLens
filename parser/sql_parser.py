from antlr4 import InputStream, CommonTokenStream
from parser.grammar.TSqlLexer import TSqlLexer
from parser.grammar.TSqlParser import TSqlParser

def parse_sql(sql_text: str):
    input_stream = InputStream(sql_text)
    lexer = TSqlLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = TSqlParser(token_stream)

    tree = parser.tsql_file()  # entry rule in TSql grammar
    return tree
