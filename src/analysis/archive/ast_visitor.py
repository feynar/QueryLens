from parser.grammar.TSqlParserVisitor import TSqlParserVisitor


class QueryLensASTVisitor(TSqlParserVisitor):

    def __init__(self, query_id):
        self.query_id = query_id
        self.findings = []

    # Detect functions like YEAR(), MONTH(), DAY()
    def visitScalar_expression(self, ctx):
        text = ctx.getText().lower()

        if "year(" in text or "month(" in text or "day(" in text:
            self.findings.append({
                "query_id": self.query_id,
                "issue_type": "NON_SARGABLE_PREDICATE"
            })

        return self.visitChildren(ctx)
