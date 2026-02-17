"""
QueryLens — AST Feature Extractor (Week 8)

Extracts structural SQL features from ANTLR parse tree.
No rule decisions are made here.
"""

from parser.grammar.TSqlParserVisitor import TSqlParserVisitor
import re


class FeatureExtractor(TSqlParserVisitor):

    NON_SARGABLE_FUNCTIONS = {
        "YEAR", "MONTH", "DAY",
        "UPPER", "LOWER",
        "LTRIM", "RTRIM",
        "CONVERT", "CAST"
    }

    def __init__(self):
        self.features = {
            "has_select_star": False,
            "join_count": 0,
            "non_sargable_functions": []
        }

    # ---------- SELECT * ----------
    def visitSelect_list_elem(self, ctx):
        if ctx.getText() == "*":
            self.features["has_select_star"] = True
        return self.visitChildren(ctx)

    # ---------- JOIN COUNT ----------
    def visitJoin_part(self, ctx):
        self.features["join_count"] += 1
        return self.visitChildren(ctx)

    # ---------- WHERE ANALYSIS ----------
    def visitSearch_condition(self, ctx):
        text = ctx.getText().upper()

        pattern = r"([A-Z_]+)\(([^)]+)\)"

        for func, arg in re.findall(pattern, text):
            if func in self.NON_SARGABLE_FUNCTIONS:

                # argument must look like a column reference
                # reject constants and built-ins like GETDATE()
                if re.match(r"[A-Z_]+\.[A-Z_]+|[A-Z_]+", arg) and not arg.endswith("()"):
                    self.features["non_sargable_functions"].append(func)

        return self.visitChildren(ctx)

    def visitTable_source_item(self, ctx):
        text = ctx.getText().upper()

        JOIN_KEYWORDS = [
            "JOIN",
            "INNERJOIN",
            "LEFTJOIN",
            "RIGHTJOIN",
            "FULLJOIN",
            "CROSSJOIN"
        ]

        for keyword in JOIN_KEYWORDS:
            if keyword in text:
                self.features["join_count"] += 1

        return self.visitChildren(ctx)
    
    def extract(self, tree):
        self.visit(tree)
        return self.features
