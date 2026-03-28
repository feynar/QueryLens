"""
QueryLens — AST Feature Extractor (Week 8)

Feature Extraction Strategy:

Hybrid approach:
- AST traversal → structural detection
- Regex fallback → semantic detection not exposed in AST

Outputs normalized feature dictionary used by rule engine.

Important:
Some SQL constructs (e.g., EXISTS, HAVING, WINDOW) are detected
via regex because they are not consistently exposed in the AST.
"""

from src.parser.grammar.TSqlParserVisitor import TSqlParserVisitor
import re


class FeatureExtractor(TSqlParserVisitor):

    NON_SARGABLE_FUNCTIONS = {
        "YEAR", "MONTH", "DAY",
        "UPPER", "LOWER",
        "LTRIM", "RTRIM",
        "CONVERT", "CAST"
    }

    AGGREGATE_FUNCTIONS = {
        "SUM", "COUNT", "AVG", "MIN", "MAX",
    }
    
    COLUMN_PATTERN = re.compile(r"[A-Z_]+\.[A-Z_]+|[A-Z_]+")

    def __init__(self, sql_text=None):

        self.sql_text = sql_text.upper() if sql_text else ""

        self.features = {
            "has_select_star": False,
            "join_count": 0,
            "non_sargable_functions": [],

            # extended rule detection
            "has_exists": False,
            "has_not_exists": False,
            "has_having": False,
            "has_window_function": False,
            "has_cross_join": False,
            "has_cartesian_join": False,
            "has_order_by": False,
            "has_distinct": False,
            "has_subquery": False,
            "has_group_by": False,
            "has_aggregation": False,
            "has_derived_table": False,
            "has_where": False,
            "has_correlated_subquery": False
        }

    # ---------------------------------
    # SELECT *
    # ---------------------------------

    def visitSelect_list_elem(self, ctx):
        if ctx.getText() == "*":
            self.features["has_select_star"] = True
        return self.visitChildren(ctx)

    # ---------------------------------
    # JOIN COUNT
    # ---------------------------------

    def visitJoin_part(self, ctx):
        self.features["join_count"] += 1
        return self.visitChildren(ctx)

    # ---------------------------------
    # NON-SARGABLE DETECTION
    # ---------------------------------

    def visitSearch_condition(self, ctx):

            text = ctx.getText().upper()
            pattern = r"([A-Z_]+)\(([^)]+)\)"

            matches = re.findall(pattern, text)

            for func, arg in matches:

                if func in self.NON_SARGABLE_FUNCTIONS and "." in arg:
                    self.features["non_sargable_functions"].append(func)

            return self.visitChildren(ctx)

    # ---------------------------------
    # TABLE SOURCE (no join counting)
    # ---------------------------------

    def visitTable_source_item(self, ctx):
        return self.visitChildren(ctx)

    # ---------------------------------
    # FEATURE EXTRACTION FINAL PASS
    # ---------------------------------

    def extract(self, tree):

        # run AST visitor
        self.visit(tree)

        text = self.sql_text.upper()

        # EXISTS
        if re.search(r"\bEXISTS\s*\(", text):
            self.features["has_exists"] = True
    
        # NOT EXISTS
        if re.search(r"\bNOT\s+EXISTS\s*\(", text):
            self.features["has_not_exists"] = True

        # HAVING
        if re.search(r"\bHAVING\b", text):
            self.features["has_having"] = True

        # WINDOW FUNCTION
        if re.search(r"\bOVER\s*\(", text):
            self.features["has_window_function"] = True

        # CROSS JOIN
        if re.search(r"\bCROSS\s+JOIN\b", text):
            self.features["has_cross_join"] = True

        # CARTESIAN JOIN (comma joins)
        if re.search(r"\bFROM\b\s+[A-Z_]+(\s+[A-Z_]+)?\s*,", text):
            self.features["has_cartesian_join"] = True
            
        # ORDER BY
        if re.search(r"\bORDER\s+BY\b", text):
            self.features["has_order_by"] = True

        # DISTINCT
        if re.search(r"\bSELECT\s+DISTINCT\b", text):
            self.features["has_distinct"] = True

        # ANY SUBQUERY
        if re.search(r"\(\s*SELECT", text):
            self.features["has_subquery"] = True
            
        # GROUP BY
        if re.search(r"\bGROUP\s+BY\b", text):
            self.features["has_group_by"] = True

        # DERIVED TABLE
        if re.search(r"FROM\s*\(", text):
            self.features["has_derived_table"] = True

        # AGGREGATE FUNCTIONS
        if re.search(r"\b(SUM|COUNT|AVG|MIN|MAX)\s*\(", text):
            self.features["has_aggregation"] = True
            
        # WHERE
        if re.search(r"\bWHERE\b", text):
            self.features["has_where"] = True
    
        # CORRELATED SUBQUERY
        if re.search(r"\bSELECT\b.*\bWHERE\b.*\bSELECT\b", text):
            outer_columns = re.findall(self.COLUMN_PATTERN, text)

            for col in outer_columns:
                pattern = r"\bSELECT\b.*\bWHERE\b.*" + col
                if re.search(pattern, text):
                    self.features["has_correlated_subquery"] = True
                    break
                    
        # ---------------------------------
        # DEBUG: Print detected features
        # ---------------------------------

        #debug_features = {k: v for k, v in self.features.items() if v}

        #if debug_features:
        #    print("\n[FeatureExtractor DEBUG]")
        #    print(debug_features)
    
        return self.features