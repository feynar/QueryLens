"""
Extracts structural SQL features from the ANTLR parse tree.

These features are later consumed by the static rule engine to detect
anti-patterns such as SELECT *, non-sargable predicates, EXISTS/NOT EXISTS,
derived tables, window functions, HAVING clauses, and correlated subqueries.
"""

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
        
        
        # Stores raw subquery text so correlated-subquery classification
        # can be finalized after the full tree traversal is complete.
        self.subquery_texts = []
        
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

        # Tracks aliases from the outer query so subqueries can later be checked
        # for references back to the outer scope.
        self.outer_tables = set()
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

        # Detect join predicates and store a simple text form of the ON clause
        # for later missing-index heuristics.
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
        text = ctx.getText().upper()
        compact = "".join(text.split())

        # Detect EXISTS / NOT EXISTS predicates.
        # NOT may appear outside the predicate text in the parent context,
        # so both the predicate and its parent are inspected.
        if "EXISTS" in compact:
            # Check if parent has NOT
            parent_text = ctx.parentCtx.getText().upper() if ctx.parentCtx else ""

            if "NOT" in parent_text:
                self.features["has_not_exists"] = True
            else:
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

        # Store subquery text so correlated-subquery detection can be finalized
        # later, after aliases and EXISTS / NOT EXISTS flags are fully known.
        self.subquery_texts.append(ctx.getText().upper())

        self.visitChildren(ctx)

        self.current_depth -= 1

        if self.current_depth == 0:
            self.in_subquery = False

        return None

    # ---------------------------------
    def visitTable_source_item(self, ctx):
        text = ctx.getText().upper()

        if text.startswith("(") and "SELECT" in text:
            self.features["has_derived_table"] = True

        alias = None
        as_alias_ctx = ctx.as_table_alias() if hasattr(ctx, "as_table_alias") else None

        if as_alias_ctx:
            alias = as_alias_ctx.getText().upper()
            
        # Only aliases from the outer query are tracked here.
        # Subquery-local aliases should not be treated as outer references.
        if alias and not self.in_subquery:
            self.outer_tables.add(alias)

        return self.visitChildren(ctx)

    # ---------------------------------
    def visitFull_column_name(self, ctx):
        text = ctx.getText().upper()


        # Track qualified column references for later missing-index heuristics.
        if "." in text:
            self.features["where_columns"].append(text)
            
            alias = text.split(".")[0].strip()

            # Early correlated-reference detection inside subqueries.
            # Final correlated-subquery classification is decided in extract().
            if self.in_subquery and alias in self.outer_tables:
                self.correlated_detected = True
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

        # Fallback for HAVING in case the grammar path does not trigger
        # visitHaving_clause() reliably for some query forms.
        if "HAVING" in self.sql_text:
            self.features["has_having"] = True

        # Correlated-subquery detection is finalized after traversal so that
        # outer aliases and EXISTS / NOT EXISTS flags are fully known.
        # EXISTS / NOT EXISTS are tracked separately and should not also be
        # labeled as correlated_subquery.
        if self.features["has_exists"] or self.features["has_not_exists"]:
            self.correlated_detected = False
        elif self.features["has_subquery"]:
            for subquery_text in self.subquery_texts:
                for outer_alias in self.outer_tables:
                    if f"{outer_alias}." in subquery_text:
                        self.correlated_detected = True
                        break
                if self.correlated_detected:
                    break

        self.features["has_correlated_subquery"] = self.correlated_detected
        return self.features