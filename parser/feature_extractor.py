from parser.grammar.TSqlVisitor import TSqlVisitor

class SQLFeatureExtractor(TSqlVisitor):

    def __init__(self):
        self.features = {
            "select_star": False,
            "join_count": 0,
            "where_functions": []
        }

    def visitSelect_list(self, ctx):
        if "*" in ctx.getText():
            self.features["select_star"] = True
        return self.visitChildren(ctx)

    def visitJoin_part(self, ctx):
        self.features["join_count"] += 1
        return self.visitChildren(ctx)

    def visitFunction_call(self, ctx):
        function_name = ctx.getText().split("(")[0]
        self.features["where_functions"].append(function_name.upper())
        return self.visitChildren(ctx)
