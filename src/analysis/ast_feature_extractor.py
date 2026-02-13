from parser.grammar.TSqlParserVisitor import TSqlParserVisitor


class ASTFeatureExtractor(TSqlParserVisitor):

    def __init__(self):
        self.features = {
            "select_star": False,
            "join_count": 0,
            "where_clauses": [],
            "functions_in_where": []
        }

    # Detect SELECT *
    def visitSelect_list(self, ctx):
        if "*" in ctx.getText():
            self.features["select_star"] = True
        return self.visitChildren(ctx)

    # Count JOINs
    def visitJoin_part(self, ctx):
        self.features["join_count"] += 1
        return self.visitChildren(ctx)

    # Capture WHERE clause text
    def visitSearch_condition(self, ctx):
        text = ctx.getText()
        self.features["where_clauses"].append(text)

        # crude function detection for now
        if "(" in text and ")" in text:
            self.features["functions_in_where"].append(text)

        return self.visitChildren(ctx)


def extract_features(tree):
    visitor = ASTFeatureExtractor()
    visitor.visit(tree)
    return visitor.features
