"""Generate a Power BI Project (PBIP) for the Meridian retention dashboard.

PBIP is the text-based Power BI format: a .pbip pointer, a TMSL semantic model (model.bim) and a
legacy report (report.json). Power BI Desktop (Windows) opens the .pbip and compiles it.

Because Claude Code cannot run Power BI Desktop, this file CANNOT be test-opened here; every JSON it
writes is validated as parseable, but opening/visual correctness must be confirmed in Desktop.

Builds under out/A/powerbi/:
  Meridian.pbip
  Meridian.SemanticModel/{.platform, definition.pbism, model.bim}
  Meridian.Report/{.platform, definition.pbir, report.json}
  Meridian_theme.json   (apply via View > Themes > Browse for the red/blue colour scheme)

Run: python build_pbip.py ../out/A/powerbi
"""
import json
import sys
import uuid
from pathlib import Path


def guid():
    return str(uuid.uuid4())


# ---------------------------------------------------------------- schema
# (column, tmsl_dtype, m_type, hidden, sort_by)
FACT = [
    ("customer_id", "string", "type text", False, None),
    ("data_scope", "string", "type text", False, None),
    ("data_split", "string", "type text", False, None),
    ("customer_segment", "string", "type text", True, None),   # hidden: use dim_segment
    ("tenure_band", "string", "type text", True, None),        # hidden: use dim_tenure
    ("tenure_years", "double", "type number", False, None),
    ("num_products", "int64", "Int64.Type", False, None),
    ("products_band", "string", "type text", False, "products_band_sort"),
    ("recency_band", "string", "type text", False, "recency_band_sort"),
    ("engagement_band", "string", "type text", False, "engagement_band_sort"),
    ("complaint_band", "string", "type text", False, "complaint_band_sort"),
    ("nps_band", "string", "type text", False, "nps_band_sort"),
    ("rm_status", "string", "type text", False, None),
    ("avg_monthly_balance", "double", "type number", False, None),
    ("churned", "int64", "Int64.Type", False, None),
    ("dq_products_lt_flags", "int64", "Int64.Type", False, None),
    ("dq_tenure_gt_adult_years", "int64", "Int64.Type", False, None),
    ("products_band_sort", "int64", "Int64.Type", True, None),
    ("recency_band_sort", "int64", "Int64.Type", True, None),
    ("engagement_band_sort", "int64", "Int64.Type", True, None),
    ("complaint_band_sort", "int64", "Int64.Type", True, None),
    ("nps_band_sort", "int64", "Int64.Type", True, None),
]
DIM_SEGMENT = [
    ("customer_segment", "string", "type text", False, "segment_sort"),
    ("segment_sort", "int64", "Int64.Type", True, None),
]
DIM_TENURE = [
    ("tenure_band", "string", "type text", True, None),
    ("tenure_sort", "int64", "Int64.Type", True, None),
    ("tenure_label", "string", "type text", False, "tenure_sort"),
]
PRIORITY = [
    ("customer_id", "string", "type text", False, None),
    ("churn_probability", "double", "type number", False, None),
    ("avg_monthly_balance", "double", "type number", False, None),
    ("expected_balance_at_risk", "double", "type number", False, None),
    ("priority_tier", "string", "type text", False, None),
    ("top_3_reasons", "string", "type text", False, None),
]

MEASURES = [
    ("Customers", "COUNTROWS ( fact_customers )", "#,0", "1 Volume"),
    ("Churned Customers", "CALCULATE ( COUNTROWS ( fact_customers ), fact_customers[churned] = 1 )", "#,0", "1 Volume"),
    ("Retained Customers", "[Customers] - [Churned Customers]", "#,0", "1 Volume"),
    ("Churn Rate", "DIVIDE ( [Churned Customers], [Customers] )", "0.0%", "2 Rates"),
    ("Base Churn Rate", "CALCULATE ( [Churn Rate], ALLEXCEPT ( fact_customers, fact_customers[data_scope] ) )", "0.0%", "2 Rates"),
    ("Churn Rate vs Base", "[Churn Rate] - [Base Churn Rate]", "+0.0%;-0.0%;0.0%", "2 Rates"),
    ("Churn Lift", "DIVIDE ( [Churn Rate], [Base Churn Rate] )", "0.00\"x\"", "2 Rates"),
    ("Churn Rate No RM", "CALCULATE ( [Churn Rate], fact_customers[rm_status] = \"No RM\" )", "0.0%", "2 Rates"),
    ("Churn Rate With RM", "CALCULATE ( [Churn Rate], fact_customers[rm_status] = \"RM assigned\" )", "0.0%", "2 Rates"),
    ("Total Balance AED", "SUM ( fact_customers[avg_monthly_balance] )", "#,0", "3 Money (AED)"),
    ("Balance Lost AED", "CALCULATE ( [Total Balance AED], fact_customers[churned] = 1 )", "#,0", "3 Money (AED)"),
    ("Pct Balance Lost", "DIVIDE ( [Balance Lost AED], [Total Balance AED] )", "0.0%", "3 Money (AED)"),
    ("Avg Balance Churned", "CALCULATE ( AVERAGE ( fact_customers[avg_monthly_balance] ), fact_customers[churned] = 1 )", "#,0", "3 Money (AED)"),
    ("Avg Balance Retained", "CALCULATE ( AVERAGE ( fact_customers[avg_monthly_balance] ), fact_customers[churned] = 0 )", "#,0", "3 Money (AED)"),
    ("Share of Customers", "DIVIDE ( [Customers], CALCULATE ( [Customers], ALLEXCEPT ( fact_customers, fact_customers[data_scope] ) ) )", "0.0%", "4 Mix"),
    ("Share of Churners", "DIVIDE ( [Churned Customers], CALCULATE ( [Churned Customers], ALLEXCEPT ( fact_customers, fact_customers[data_scope] ) ) )", "0.0%", "4 Mix"),
    ("Share of Balance Lost", "DIVIDE ( [Balance Lost AED], CALCULATE ( [Balance Lost AED], ALLEXCEPT ( fact_customers, fact_customers[data_scope] ) ) )", "0.0%", "4 Mix"),
    ("Pct With RM", "DIVIDE ( CALCULATE ( [Customers], fact_customers[rm_status] = \"RM assigned\" ), [Customers] )", "0.0%", "5 Behaviour"),
    ("Pct Single Product", "DIVIDE ( CALCULATE ( [Customers], fact_customers[products_band] = \"1\" ), [Customers] )", "0.0%", "5 Behaviour"),
    ("Avg Products", "AVERAGE ( fact_customers[num_products] )", "0.00", "5 Behaviour"),
    ("DQ Products Below Flags", "SUM ( fact_customers[dq_products_lt_flags] )", "#,0", "6 Data quality"),
    ("DQ Tenure Above Adult Years", "SUM ( fact_customers[dq_tenure_gt_adult_years] )", "#,0", "6 Data quality"),
    ("Priority Customers", "COUNTROWS ( priority_list )", "#,0", "7 Priority"),
    ("Expected Balance At Risk", "SUM ( priority_list[expected_balance_at_risk] )", "#,0", "7 Priority"),
]


# ---------------------------------------------------------------- semantic model (model.bim)
def m_expression(columns, csv_path):
    transforms = ", ".join(f'{{"{c}", {mt}}}' for c, _, mt, _, _ in columns)
    return [
        "let",
        f'    Source = Csv.Document(File.Contents("{csv_path}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f"    Typed = Table.TransformColumnTypes(Promoted, {{{transforms}}})",
        "in",
        "    Typed",
    ]


def tmsl_columns(columns):
    out = []
    for name, dtype, _, hidden, sort_by in columns:
        col = {"name": name, "dataType": dtype, "sourceColumn": name,
               "summarizeBy": "none", "lineageTag": guid()}
        if hidden:
            col["isHidden"] = True
        if sort_by:
            col["sortByColumn"] = sort_by
        out.append(col)
    return out


def data_table(name, columns, csv_path):
    return {"name": name, "lineageTag": guid(),
            "columns": tmsl_columns(columns),
            "partitions": [{"name": name, "mode": "import",
                            "source": {"type": "m", "expression": m_expression(columns, csv_path)}}]}


def measures_table():
    return {
        "name": "_Measures", "lineageTag": guid(),
        "columns": [{"name": "_", "dataType": "int64", "sourceColumn": "_",
                     "isHidden": True, "summarizeBy": "none", "lineageTag": guid()}],
        "partitions": [{"name": "_Measures", "mode": "import",
                        "source": {"type": "m",
                                   "expression": ["let", '    Source = #table(type table [_ = Int64.Type], {{1}})',
                                                  "in", "    Source"]}}],
        "measures": [{"name": n, "expression": e, "formatString": f, "displayFolder": d,
                      "lineageTag": guid()} for n, e, f, d in MEASURES],
    }


def build_model(data_dir: Path):
    def p(fn):
        return str((data_dir / fn).resolve())
    tables = [
        data_table("fact_customers", FACT, p("fact_customers.csv")),
        data_table("dim_segment", DIM_SEGMENT, p("dim_segment.csv")),
        data_table("dim_tenure", DIM_TENURE, p("dim_tenure.csv")),
        data_table("priority_list", PRIORITY, p("priority_list.csv")),
        measures_table(),
    ]
    relationships = [
        {"name": guid(), "fromTable": "fact_customers", "fromColumn": "customer_segment",
         "toTable": "dim_segment", "toColumn": "customer_segment", "crossFilteringBehavior": "oneDirection"},
        {"name": guid(), "fromTable": "fact_customers", "fromColumn": "tenure_band",
         "toTable": "dim_tenure", "toColumn": "tenure_band", "crossFilteringBehavior": "oneDirection"},
    ]
    return {
        "name": "Meridian", "compatibilityLevel": 1567,
        "model": {
            "culture": "en-US",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": tables,
            "relationships": relationships,
            "annotations": [{"name": "PBI_QueryOrder",
                             "value": '["fact_customers","dim_segment","dim_tenure","priority_list","_Measures"]'}],
        },
    }


# ---------------------------------------------------------------- report (legacy report.json)
def _alias(entity, used):
    a = entity[0].lower()
    i = 1
    while a in used:
        i += 1; a = f"{entity[0].lower()}{i}"
    used.add(a)
    return a


def visual(vtype, x, y, w, h, title=None, fields=None, z=0, text=None):
    """fields: list of (role, table, column, is_measure)."""
    sv = {"visualType": vtype, "drillFilterOtherVisuals": True}
    if text is not None:  # textbox has no query
        sv["objects"] = {"general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": text, "textStyle": {"fontSize": "11pt"}}],
             "horizontalTextAlignment": "left"}]}}]}
    if fields:
        projections, from_map, selects, used = {}, {}, [], set()
        for role, table, col, is_m in fields:
            if table not in from_map:
                from_map[table] = _alias(table, used)
            alias = from_map[table]
            qref = f"{table}.{col}"
            projections.setdefault(role, []).append({"queryRef": qref})
            ref = {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}
            sel = ({"Measure": ref} if is_m else {"Column": ref})
            sel["Name"] = qref
            sel["NativeReferenceName"] = col
            selects.append(sel)
        sv["projections"] = {r: [{**p, "active": True} if i == 0 else p for i, p in enumerate(v)]
                             for r, v in projections.items()}
        sv["prototypeQuery"] = {
            "Version": 2,
            "From": [{"Name": a, "Entity": t, "Type": 0} for t, a in from_map.items()],
            "Select": selects,
        }
    if title:
        sv.setdefault("vcObjects", {})["title"] = [{"properties": {
            "show": {"expr": {"Literal": {"Value": "true"}}},
            "text": {"expr": {"Literal": {"Value": "'" + title.replace("'", "''") + "'"}}}}}]
    config = {"name": guid(),
              "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z}}],
              "singleVisual": sv}
    return {"x": x, "y": y, "z": z, "width": w, "height": h,
            "config": json.dumps(config), "filters": "[]", "query": "", "dataTransforms": ""}


def section(name, visuals, ordinal):
    return {"name": guid(), "displayName": name, "filters": "[]", "ordinal": ordinal,
            "visualContainers": visuals, "config": "{}", "displayOption": 1,
            "width": 1280, "height": 720}


def build_report():
    FM, FC = "_Measures", "fact_customers"
    pages = []

    def scope_slicer():
        return visual("slicer", 1070, 15, 195, 95, "Data scope",
                      [("Values", FC, "data_scope", False)], z=0)

    # Page 1 — Executive overview
    v = [scope_slicer(),
         visual("card", 20, 15, 200, 95, "Customers", [("Values", FM, "Customers", True)], z=1),
         visual("card", 230, 15, 200, 95, "Churn Rate", [("Values", FM, "Churn Rate", True)], z=2),
         visual("card", 440, 15, 200, 95, "Balance Lost (AED)", [("Values", FM, "Balance Lost AED", True)], z=3),
         visual("card", 650, 15, 200, 95, "% Balance Lost", [("Values", FM, "Pct Balance Lost", True)], z=4),
         visual("columnChart", 20, 125, 600, 290, "Churn is highest in the first year",
                [("Category", "dim_tenure", "tenure_label", False), ("Y", FM, "Churn Rate", True)], z=5),
         visual("clusteredBarChart", 640, 125, 620, 290,
                "Mass Market drives volume; higher segments drive the money lost",
                [("Category", "dim_segment", "customer_segment", False),
                 ("Y", FM, "Share of Churners", True), ("Y", FM, "Share of Balance Lost", True)], z=6),
         visual("columnChart", 20, 425, 1240, 280, "Churn rate falls as segment value rises",
                [("Category", "dim_segment", "customer_segment", False), ("Y", FM, "Churn Rate", True)], z=7)]
    pages.append(section("1 Executive overview", v, 0))

    # Page 2 — Behavioural drivers
    v = [scope_slicer(),
         visual("columnChart", 20, 125, 405, 270, "Single-product customers churn at 2x+ the average",
                [("Category", FC, "products_band", False), ("Y", FM, "Churn Rate", True)], z=1),
         visual("columnChart", 435, 125, 405, 270, "90+ days idle: churn triples",
                [("Category", FC, "recency_band", False), ("Y", FM, "Churn Rate", True)], z=2),
         visual("columnChart", 850, 125, 410, 270, "Churn falls as digital engagement rises",
                [("Category", FC, "engagement_band", False), ("Y", FM, "Churn Rate", True)], z=3),
         visual("columnChart", 20, 410, 405, 295, "2+ complaints: churn doubles",
                [("Category", FC, "complaint_band", False), ("Y", FM, "Churn Rate", True)], z=4),
         visual("columnChart", 435, 410, 405, 295, "Negative NPS churns at 1.7x the average",
                [("Category", FC, "nps_band", False), ("Y", FM, "Churn Rate", True)], z=5),
         visual("pivotTable", 850, 410, 410, 295, "New + single product: more than half leave",
                [("Rows", "dim_tenure", "tenure_label", False),
                 ("Columns", FC, "products_band", False), ("Values", FM, "Churn Rate", True)], z=6)]
    pages.append(section("2 Behavioural drivers", v, 1))

    # Page 3 — Relationship & value at risk
    v = [scope_slicer(),
         visual("clusteredColumnChart", 20, 125, 620, 300,
                "Customers with an RM churn at about half the rate",
                [("Category", "dim_segment", "customer_segment", False),
                 ("Y", FM, "Churn Rate No RM", True), ("Y", FM, "Churn Rate With RM", True)], z=1),
         visual("pivotTable", 660, 125, 600, 300, "Where the lost balances sit (AED)",
                [("Rows", "dim_segment", "customer_segment", False),
                 ("Columns", "dim_tenure", "tenure_label", False), ("Values", FM, "Balance Lost AED", True)], z=2),
         visual("card", 20, 435, 300, 130, "% Mass Affluent with an RM",
                [("Values", FM, "Pct With RM", True)], z=3),
         visual("textbox", 340, 435, 920, 130, None, None, z=4,
                text="RM coverage is associated with lower churn, but RMs may be assigned to already-loyal "
                     "customers. This must be tested in the pilot before we claim it causes retention.")]
    pages.append(section("3 Relationship & value", v, 2))

    # Page 4 — Data quality & lineage
    v = [scope_slicer(),
         visual("card", 20, 125, 290, 120, "Products below flags", [("Values", FM, "DQ Products Below Flags", True)], z=1),
         visual("card", 320, 125, 290, 120, "Tenure above adult years", [("Values", FM, "DQ Tenure Above Adult Years", True)], z=2),
         visual("tableEx", 20, 255, 590, 200, "Scope: rows and churn",
                [("Values", FC, "data_scope", False), ("Values", FM, "Customers", True), ("Values", FM, "Churn Rate", True)], z=3),
         visual("clusteredColumnChart", 640, 125, 620, 330,
                "Synthetic rows reproduce real churn by segment",
                [("Category", "dim_segment", "customer_segment", False),
                 ("Series", FC, "data_scope", False), ("Y", FM, "Churn Rate", True)], z=4),
         visual("textbox", 20, 470, 1240, 235, None, None, z=5,
                text="10,000 real customers, cleaned and checksum-verified against the source summary. "
                     "40,000 synthetic rows generated with a stratified Gaussian copula fitted on 8,000 "
                     "training customers only. Data-quality issues are flagged, not removed. Headline "
                     "figures use real data only. Set the Data scope slicer to Real for headline numbers.")]
    pages.append(section("4 Data quality & lineage", v, 3))

    # Page 5 — Retention priority (from priority_list)
    PL = "priority_list"
    v = [visual("card", 20, 15, 240, 100, "Priority customers (real)", [("Values", FM, "Priority Customers", True)], z=0),
         visual("card", 270, 15, 240, 100, "Expected balance at risk (AED)", [("Values", FM, "Expected Balance At Risk", True)], z=1),
         visual("columnChart", 20, 125, 490, 300, "Expected balance at risk by tier",
                [("Category", PL, "priority_tier", False), ("Y", FM, "Expected Balance At Risk", True)], z=2),
         visual("columnChart", 20, 435, 490, 270, "Customers by tier",
                [("Category", PL, "priority_tier", False), ("Y", FM, "Priority Customers", True)], z=3),
         visual("tableEx", 530, 15, 730, 690, "Priority list (sort by expected balance at risk; apply Top 50)",
                [("Values", PL, "priority_tier", False), ("Values", PL, "customer_id", False),
                 ("Values", PL, "churn_probability", False), ("Values", PL, "expected_balance_at_risk", False),
                 ("Values", PL, "top_3_reasons", False)], z=4)]
    pages.append(section("5 Retention priority", v, 4))

    config = {"version": "5.43", "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True}
    return {"config": json.dumps(config), "layoutOptimization": 0,
            "resourcePackages": [], "sections": pages, "pods": [], "publicCustomVisuals": []}


# ---------------------------------------------------------------- theme
def theme():
    return {"name": "Meridian",
            "dataColors": ["#C8102E", "#2F6DB5", "#6B7280", "#1F2328", "#2E7D32", "#C8102E"],
            "background": "#FFFFFF", "foreground": "#1F2328", "tableAccent": "#C8102E"}


def platform(kind, name):
    return {"$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": kind, "displayName": name},
            "config": {"version": "2.0", "logicalId": guid()}}


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    json.loads(path.read_text(encoding="utf-8"))  # validate parseable


def main(root):
    root = Path(root)
    data_dir = root / "data"
    sm, rp = root / "Meridian.SemanticModel", root / "Meridian.Report"

    write_json(root / "Meridian.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/pbip/definitionProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": "Meridian.Report"}}],
        "settings": {"enableAutoRecovery": True}})

    write_json(sm / ".platform", platform("SemanticModel", "Meridian"))
    write_json(sm / "definition.pbism", {"version": "4.0", "settings": {}})
    write_json(sm / "model.bim", build_model(data_dir))

    write_json(rp / ".platform", platform("Report", "Meridian"))
    write_json(rp / "definition.pbir", {"version": "4.0",
                                        "datasetReference": {"byPath": {"path": "../Meridian.SemanticModel"}}})
    write_json(rp / "report.json", build_report())

    write_json(root / "Meridian_theme.json", theme())

    print(f"PBIP generated -> {root}")
    print(f"  model.bim: 5 tables, {len(MEASURES)} measures, 2 relationships")
    print(f"  report.json: 5 pages")
    print(f"  data path baked in: {data_dir.resolve()}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../out/A/powerbi")
