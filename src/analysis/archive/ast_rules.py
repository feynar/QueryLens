import os
from parser.grammar.TSqlParserVisitor import TSqlParserVisitor
from src.analysis.sql_parser import parse_sql_file


class SelectStarVisitor(TSqlParserVisitor):

    def __init__(self):
        self.found = False

    def visitSelect_list(self, ctx):
        text = ctx.getText()
        if "*" in text:
            self.found = True
        return self.visitChildren(ctx)


def analyze_with_ast(file_path):
    tree, parser = parse_sql_file(file_path)

    visitor = SelectStarVisitor()
    visitor.visit(tree)

    findings = []
    query_id = os.path.splitext(os.path.basename(file_path))[0]

    if visitor.found:
        findings.append({
            "query_id": query_id,
            "issue_type": "SELECT_STAR"
        })

    return findings
