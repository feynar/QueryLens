from src.parser.grammar.TSqlParserVisitor import TSqlParserVisitor


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

    def __init__(self, sql_text=None):
        self.sql_text = sql_text.upper() if sql_text else ""

        self.features = {
            "has_select_star": False,
            "join_count": 0,
            "join_types": set(),

            "non_sargable_functions": [],

            "has_exists": False,
            "has_not_exists": False,
            "has_having": False,
            "has_window_function": False,
            "has_cross_join": False,

            "has_order_by": False,
            "has_distinct": False,
            "has_subquery": False,
            "subquery_depth": 0,

            "has_group_by": False,
            "has_aggregation": False,
            "has_derived_table": False,
            "has_where": False,
            "has_correlated_subquery": False,
            
            "has_join_predicate": False,
            "join_columns": [],
            "where_columns": [],
            "has_selective_predicate": False,
            "has_range_predicate": False
        }

        self.current_depth = 0

        # Correlation tracking
        self.outer_tables = set()
        self.current_tables = set()
        self.in_subquery = False
        self.correlated_detected = False

    # ---------------------------------
    def visitSelect_list_elem(self, ctx):
        if ctx.getText() == "*":
            self.features["has_select_star"] = True
        return self.visitChildren(ctx)

    # ---------------------------------
    def visitQuery_specification(self, ctx):
        if ctx.DISTINCT():
            self.features["has_distinct"] = True
        return self.visitChildren(ctx)

    # ---------------------------------
    def visitSearch_condition(self, ctx):
        self.features["has_where"] = True

        text = ctx.getText().upper()

        # Detect non-sargable functions
        for func in self.NON_SARGABLE_FUNCTIONS:
            if f"{func}(" in text:
                self.features["non_sargable_functions"].append(func)

        # TRUE filtering predicates (WHERE only)
        if "=" in text or " IN " in text:
            self.features["has_selective_predicate"] = True

        if ">" in text or "<" in text or "BETWEEN" in text:
            self.features["has_range_predicate"] = True

        return self.visitChildren(ctx)

    # ---------------------------------
    def visitJoin_part(self, ctx):
        self.features["join_count"] += 1

        text = ctx.getText().upper()

        if "LEFT" in text:
            self.features["join_types"].add("LEFT")
        elif "RIGHT" in text:
            self.features["join_types"].add("RIGHT")
        elif "FULL" in text:
            self.features["join_types"].add("FULL")
        elif "CROSS" in text:
            self.features["has_cross_join"] = True
            self.features["join_types"].add("CROSS")
        else:
            self.features["join_types"].add("INNER")

        # detect join predicates
        if " ON " in text:
            self.features["has_join_predicate"] = True

            # crude extraction of join columns
            parts = text.split("ON")
            if len(parts) > 1:
                condition = parts[1]
                self.features["join_columns"].append(condition.strip())
                
        return self.visitChildren(ctx)

    # ---------------------------------
    def visitGroup_by_clause(self, ctx):
        self.features["has_group_by"] = True
        return self.visitChildren(ctx)

    def visitHaving_clause(self, ctx):
        self.features["has_having"] = True
        return self.visitChildren(ctx)

    def visitOrder_by_clause(self, ctx):
        self.features["has_order_by"] = True
        return self.visitChildren(ctx)

    # ---------------------------------
    def visitFunction_call(self, ctx):
        func_name = ctx.getText().split("(")[0].upper()

        if func_name in self.AGGREGATE_FUNCTIONS:
            self.features["has_aggregation"] = True

        return self.visitChildren(ctx)

    # ---------------------------------
    def visitPredicate(self, ctx):
        text = f" {ctx.getText().upper()} "

        if "NOT EXISTS" in text:
            self.features["has_not_exists"] = True
        elif "EXISTS" in text:
            self.features["has_exists"] = True

        return self.visitChildren(ctx)
    
    # ---------------------------------
    def visitSubquery(self, ctx):
        self.features["has_subquery"] = True

        self.current_depth += 1
        self.in_subquery = True

        self.features["subquery_depth"] = max(
            self.features["subquery_depth"],
            self.current_depth
        )

        self.visitChildren(ctx)

        self.current_depth -= 1

        if self.current_depth == 0:
            self.in_subquery = False

        return None

    # ---------------------------------
    def visitTable_source_item(self, ctx):
        text = ctx.getText().upper()

        parts = text.split()
        if len(parts) >= 2:
            alias = parts[-1]
            self.current_tables.add(alias)

            if not self.in_subquery:
                self.outer_tables.add(alias)

        if text.startswith("(") and "SELECT" in text:
            self.features["has_derived_table"] = True

        return self.visitChildren(ctx)

    # ---------------------------------
    def visitFull_column_name(self, ctx):
        text = ctx.getText().upper()


        # track WHERE columns
        if "." in text:
            self.features["where_columns"].append(text)
            
            alias = text.split(".")[0].strip()

            # PRIMARY detection
            if self.in_subquery and alias in self.outer_tables:
                self.correlated_detected = True
            
            # FALLBACK detection (robust to alias issues)
            elif self.in_subquery:
                for outer in self.outer_tables:
                    if outer in text:
                        self.correlated_detected = True
                        break

        return self.visitChildren(ctx)

    # ---------------------------------
    def visitOver_clause(self, ctx):
        self.features["has_window_function"] = True
        return self.visitChildren(ctx)

    # ---------------------------------
    def extract(self, tree):

        self.visit(tree)

        self.features["join_types"] = list(self.features["join_types"])

        # FINAL correlated assignment
        self.features["has_correlated_subquery"] = self.correlated_detected

        return self.features