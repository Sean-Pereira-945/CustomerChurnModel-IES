"""Generate Meridian_Retention.pptx from all three tracks' outputs (16:9, python-pptx).

- Main-slide numbers are injected from metrics.json / eda_findings.json via the same placeholder
  filling as fill_report.py — nobody hand-copies numbers.
- Appendix slides are built by reading each `## heading` from the approach_*.md files.
- A missing image or file becomes a labelled grey box instead of crashing, so the deck can be
  dry-run before integration.

Run: python build_deck.py            # defaults to ../out, writes ../out/C/Meridian_Retention.pptx
"""
import csv
import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

from fill_report import build_lookup, fill_text, resolve_base

RED = RGBColor(0xC8, 0x10, 0x2E)
INK = RGBColor(0x1F, 0x23, 0x28)
BLUE = RGBColor(0x2F, 0x6D, 0xB5)
MUTED = RGBColor(0x6B, 0x72, 0x80)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
LIGHT = RGBColor(0xF3, 0xF4, 0xF6)
GREY = RGBColor(0xD1, 0xD5, 0xDB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SW, SH = Inches(13.333), Inches(7.5)
TEAM = "Team Meridian — Person A (Data) · Person B (Model) · Person C (Strategy)"


# ---------------------------------------------------------------- helpers
def _set(run, size, color, bold=False, italic=False):
    run.font.size = Pt(size); run.font.color.rgb = color
    run.font.bold = bold; run.font.italic = italic
    run.font.name = "Calibri"


def textbox(slide, l, t, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(l, t, w, h); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    return tf


def title_bar(slide, text, kicker=None):
    tf = textbox(slide, Inches(0.6), Inches(0.35), Inches(12.1), Inches(1.1))
    if kicker:
        p = tf.paragraphs[0]; r = p.add_run(); r.text = kicker.upper()
        _set(r, 11, RED, bold=True)
        p2 = tf.add_paragraph()
    else:
        p2 = tf.paragraphs[0]
    r = p2.add_run(); r.text = text; _set(r, 26, INK, bold=True)
    # accent rule
    ln = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.62), Inches(1.5), Inches(1.4), Pt(3))
    ln.fill.solid(); ln.fill.fore_color.rgb = RED; ln.line.fill.background()


def page_no(slide, n):
    tf = textbox(slide, Inches(12.5), Inches(7.05), Inches(0.7), Inches(0.35))
    r = tf.paragraphs[0].add_run(); r.text = str(n); _set(r, 10, MUTED)


def source_line(slide, text):
    tf = textbox(slide, Inches(0.6), Inches(7.02), Inches(11.5), Inches(0.4))
    r = tf.paragraphs[0].add_run(); r.text = "Source: " + text; _set(r, 9, MUTED, italic=True)


def bullets(slide, items, l, t, w, h, size=15, gap=6):
    tf = textbox(slide, l, t, w, h)
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        r = p.add_run(); r.text = "•  " + it; _set(r, size, INK)
    return tf


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def image_or_placeholder(slide, path, l, t, w, h, label=None):
    p = Path(path)
    if p.exists():
        try:
            from PIL import Image  # pillow ships with matplotlib envs; fall back if absent
            iw, ih = Image.open(p).size; ar = iw / ih
        except Exception:
            ar = w / h
        box_ar = w / h
        if ar > box_ar:
            nw, nh = w, int(w / ar)
        else:
            nh, nw = h, int(h * ar)
        slide.shapes.add_picture(str(p), l + (w - nw) // 2, t + (h - nh) // 2, nw, nh)
    else:
        box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
        box.fill.solid(); box.fill.fore_color.rgb = LIGHT
        box.line.color.rgb = GREY; box.line.dash_style = 2
        tf = box.text_frame; tf.word_wrap = True
        r = tf.paragraphs[0].add_run()
        r.text = f"[missing: {label or p.name}]"; _set(r, 12, MUTED, italic=True)
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


# ---------------------------------------------------------------- approach parsing
def parse_sections(md_path):
    text = Path(md_path).read_text(encoding="utf-8") if Path(md_path).exists() else ""
    sections, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*)", line)
        if m:
            cur = m.group(1).strip(); sections[cur] = []
        elif cur is not None and line.strip().startswith("-"):
            sections[cur].append(line.strip()[1:].strip())
    return sections


def section_bullets(sections, *headings, limit=8):
    out = []
    for h in headings:
        out += sections.get(h, [f"(missing section: {h})"])
    return out[:limit]


# ---------------------------------------------------------------- main slides
def main(base=None):
    base = resolve_base(base)
    A, B, C = base / "A", base / "B", base / "C"
    lookup = build_lookup(B / "metrics.json", C / "eda_findings.json")
    def F(t): return fill_text(t, lookup)
    aA, aB, aC = parse_sections(A / "approach_A.md"), parse_sections(B / "approach_B.md"), parse_sections(C / "approach_C.md")

    prs = Presentation(); prs.slide_width, prs.slide_height = SW, SH
    pg = [1]
    def num(s): page_no(s, pg[0]); pg[0] += 1

    # --- 1 title -----------------------------------------------------------
    s = blank(prs)
    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(2.4), SW, Inches(2.0))
    band.fill.solid(); band.fill.fore_color.rgb = RED; band.line.fill.background()
    tf = textbox(s, Inches(0.8), Inches(2.5), Inches(11.7), Inches(1.8), MSO_ANCHOR.MIDDLE)
    r = tf.paragraphs[0].add_run(); r.text = "Predict. Prioritise. Retain."; _set(r, 44, WHITE, bold=True)
    p = tf.add_paragraph(); r = p.add_run()
    r.text = "A customer-retention decision engine for Meridian Trust Bank"; _set(r, 20, WHITE)
    tf2 = textbox(s, Inches(0.8), Inches(4.7), Inches(11.7), Inches(0.6))
    r = tf2.paragraphs[0].add_run(); r.text = TEAM; _set(r, 14, MUTED)
    num(s)

    # --- 2 our approach (pipeline diagram) ---------------------------------
    s = blank(prs); title_bar(s, "A four-stage pipeline, each step defensible", "Our approach")
    stages = [("DATA", "Clean · checksum · scale to 50k"),
              ("UNDERSTANDING", "EDA with 95% CIs · driver ranking"),
              ("PREDICTION", "Calibrated model · holdout-tested"),
              ("RECOMMENDATION", "Tiers · playbook · measured pilot")]
    bw, bh, top, gap = Inches(2.7), Inches(1.5), Inches(2.9), Inches(0.37)
    x = Inches(0.6)
    for i, (name, line) in enumerate(stages):
        box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, top, bw, bh)
        box.fill.solid(); box.fill.fore_color.rgb = BLUE if i % 2 == 0 else INK
        box.line.fill.background()
        tf = box.text_frame; tf.word_wrap = True
        r = tf.paragraphs[0].add_run(); r.text = name; _set(r, 15, WHITE, bold=True)
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        cap = textbox(s, x, top + bh + Inches(0.1), bw, Inches(0.9))
        rr = cap.paragraphs[0].add_run(); rr.text = line; _set(rr, 12, MUTED)
        cap.paragraphs[0].alignment = PP_ALIGN.CENTER
        if i < 3:
            ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x + bw + Inches(0.02), top + Inches(0.55), gap, Inches(0.4))
            ar.fill.solid(); ar.fill.fore_color.rgb = RED; ar.line.fill.background()
        x = x + bw + gap
    bullets(s, ["Raw data kept read-only; one shared loader; fixed seed 42 — every number reproducible.",
                "Split before synthesising, holdout touched once — no leakage into evaluation."],
            Inches(0.6), Inches(5.3), Inches(12.1), Inches(1.2), size=14)
    notes(s, "Our method mirrors how a bank would deploy this. We clean and checksum the data, "
             "understand churn with confidence intervals, predict with a calibrated and holdout-tested "
             "model, and turn that into prioritised action proven by a pilot. Every step is reproducible "
             "from code with a fixed seed.")
    num(s)

    # --- 3 the problem in AED ---------------------------------------------
    s = blank(prs); title_bar(s, F("AED {{C.aed_balance_lost_total|aed_m}} of balances sit with churned customers"), "The problem in AED")
    bullets(s, [F("{{C.churned|int}} of {{C.customers|int}} customers have churned — {{C.base_churn_rate|pct1}} of the base."),
                F("That is AED {{C.aed_balance_lost_total|aed_m}} in average monthly balances ({{C.pct_balance_lost|pct1}} of deposits)."),
                F("Mass Market = {{C.share_churners_mass_market_pct}}% of churners, but value concentrates at the top:"),
                F("Affluent + Private Banking = {{C.share_balance_lost_top2_segments|pct}} of the balance lost.")],
            Inches(0.6), Inches(1.8), Inches(5.6), Inches(4.5), size=16, gap=14)
    image_or_placeholder(s, C / "figures" / "08_segment_volume_vs_value.png",
                         Inches(6.4), Inches(1.8), Inches(6.3), Inches(4.4), "chart 8")
    source_line(s, "eda_findings.json; chart 08_segment_volume_vs_value. Real customers, n=10,000.")
    notes(s, "Churn is 15.8% of customers but the money is what matters. Roughly AED 22 million in "
             "balances sits with customers who have left. Mass Market drives the count of churners, but "
             "the Affluent and Private Banking segments drive half the balance lost. That split is why we "
             "prioritise by balance at risk, not by probability alone.")
    num(s)

    # --- 4 why customers leave --------------------------------------------
    s = blank(prs); title_bar(s, F("New, single-product and inactive customers leave hardest"), "Why customers leave — descriptive")
    for i, (img, lbl) in enumerate([("02_products.png", "chart 2"), ("03_recency.png", "chart 3"),
                                    ("07_tenure_x_products.png", "chart 7")]):
        image_or_placeholder(s, C / "figures" / img, Inches(0.5 + i * 4.15), Inches(1.9),
                             Inches(4.0), Inches(3.4), lbl)
    bullets(s, [F("Single-product customers churn at {{C.churn_products_1|pct1}} vs {{C.churn_products_2|pct1}} for two products."),
                F("90+ days inactive: {{C.churn_recency_90plus|pct1}} churn. New customers: {{C.churn_tenure_lt1|pct1}} vs {{C.churn_tenure_15plus|pct1}} at 15+ yrs ({{C.tenure_lt1_vs_15plus_ratio|x2}})."),
                "Association, not causation — bars show 95% Wilson intervals with sample sizes."],
            Inches(0.6), Inches(5.5), Inches(12.1), Inches(1.6), size=13, gap=5)
    source_line(s, "eda_findings.json; charts 02, 03, 07. Real customers, n=10,000.")
    notes(s, "These are the strongest patterns. Customers with one product churn at over triple the rate "
             "of those with two. Ninety days of inactivity is a near-50% churn signal. And the first year "
             "is decisive — new customers churn more than five times as often as 15-year customers. Every "
             "bar carries a confidence interval, and we are careful to call these associations, not causes.")
    num(s)

    # --- 5 predicting ------------------------------------------------------
    s = blank(prs); title_bar(s, F("A {{B.chosen_model}} that beats the naive rule {{B.pr_auc|f3}} vs {{B.baseline_pr_auc|f3}} PR-AUC"), "Predicting who will leave — predictive")
    # model comparison mini-table
    rows = list(csv.reader((B / "model_comparison.csv").read_text(encoding="utf-8").splitlines()))
    tbl = s.shapes.add_table(len(rows), 4, Inches(0.6), Inches(1.9), Inches(6.0), Inches(2.4)).table
    for ci in range(4):
        tbl.columns[ci].width = Inches(1.5) if ci else Inches(2.7)
    for ri, row in enumerate(rows):
        for cj in range(4):
            cell = tbl.cell(ri, cj); cell.text = row[cj] if cj < len(row) else ""
            para = cell.text_frame.paragraphs[0]
            for rn in para.runs:
                _set(rn, 10.5, WHITE if ri == 0 else INK, bold=(ri == 0))
            cell.fill.solid(); cell.fill.fore_color.rgb = RED if ri == 0 else (LIGHT if ri % 2 else WHITE)
    bullets(s, [F("Holdout PR-AUC {{B.pr_auc|f3}} (95% CI {{B.pr_auc_ci_low|f3}}–{{B.pr_auc_ci_high|f3}}), ROC-AUC {{B.roc_auc|f3}}."),
                F("Top decile of scores captures {{B.top_decile_capture|pct}} of all leavers."),
                F("Isotonic-calibrated; leakage tested (drop {{B.leakage_pr_auc_drop|f3}} without recency).")],
            Inches(0.6), Inches(4.5), Inches(6.0), Inches(2.2), size=13, gap=6)
    image_or_placeholder(s, B / "figures" / "shap_bar.png", Inches(6.9), Inches(1.9), Inches(5.8), Inches(4.6), "SHAP bar")
    source_line(s, "model_comparison.csv, metrics.json, SHAP figure. Trained on real data only.")
    notes(s, "We trained on real data only, with a held-out 2,000 customers touched once. The model — a "
             "logistic regression chosen on cross-validated PR-AUC — far outperforms the naive new-customer "
             "rule. Its top decile catches almost 40% of all leavers. Probabilities are calibrated so that "
             "probability times balance is real money, and SHAP gives every customer a plain-English reason.")
    num(s)

    # --- 6 who to save first ----------------------------------------------
    s = blank(prs); title_bar(s, F("Ranking by balance-at-risk protects AED {{B.aed_protected_value_weighted|aed_m}} vs {{B.aed_protected_prob_only|aed_m}}"), "Who to save first")
    tc = lookup["B"]
    matrix = [("T1 Save now", "High risk · High value", tc.get("tier_counts.T1 Save now", "?"), RED),
              ("T2 Protect", "Low risk · High value", tc.get("tier_counts.T2 Protect", "?"), BLUE),
              ("T3 Automated save", "High risk · Low value", tc.get("tier_counts.T3 Automated save", "?"), GREEN),
              ("T4 Monitor", "Low risk · Low value", tc.get("tier_counts.T4 Monitor", "?"), MUTED)]
    for i, (name, desc, cnt, col) in enumerate(matrix):
        r_, c_ = divmod(i, 2)
        box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(0.6 + c_ * 3.1), Inches(2.0 + r_ * 1.7), Inches(2.95), Inches(1.55))
        box.fill.solid(); box.fill.fore_color.rgb = col; box.line.fill.background()
        tf = box.text_frame; tf.word_wrap = True
        rr = tf.paragraphs[0].add_run(); rr.text = name; _set(rr, 15, WHITE, bold=True)
        p = tf.add_paragraph(); rr = p.add_run(); rr.text = desc; _set(rr, 11, WHITE)
        p = tf.add_paragraph(); rr = p.add_run()
        rr.text = f"{int(cnt):,} customers" if str(cnt).isdigit() else str(cnt); _set(rr, 13, WHITE, bold=True)
    image_or_placeholder(s, B / "figures" / "value_capture.png", Inches(6.9), Inches(1.9), Inches(5.8), Inches(4.3), "value-capture chart")
    source_line(s, F("metrics.json tier_counts; value-capture chart. Capacity {{B.capacity_n|int}} contacts/month."))
    notes(s, "We sort customers into four tiers on risk and value. High value means a balance in the top "
             "quartile. With only 500 RM contacts a month, how we rank matters enormously: ranking by "
             "expected balance at risk protects several times the money that ranking by probability alone "
             "would, and far more than random outreach. Same effort, much more deposit base retained.")
    num(s)

    # --- 7 recommendations -------------------------------------------------
    s = blank(prs); title_bar(s, "From prediction to measured action", "Recommendations")
    bullets(s, ["Playbook by tier: onboarding journey (new/disengaged); priority complaint resolution + RM call;",
                "   RM assignment / priority upgrade (high-balance, no RM); cross-sell bundle (single product); reactivation offer (dormant).",
                "Pilot: randomised controlled trial on T1 & T3, treatment vs BAU control, stratified by tier and segment.",
                "Power calc (40%→32% churn, α=0.05, power 0.8) sizes each arm; 90-day treatment, read at 90 & 180 days.",
                "KPIs: churn-rate uplift (primary); AED retained, ROI, products/customer, NPS (secondary).",
                "Decision rule: scale if uplift significant AND ROI>1; otherwise retire or redesign.",
                "The ask: approve the 90-day T1/T3 pilot and the RM capacity to contact the top-ranked customers."],
            Inches(0.6), Inches(1.9), Inches(12.1), Inches(4.8), size=15, gap=10)
    notes(s, "Each risk signal maps to a concrete intervention. Crucially, we do not claim these will work "
             "— we propose to prove it. A randomised controlled trial on the high-risk tiers, sized by a "
             "power calculation, will measure churn uplift and ROI. We scale only what works. The ask is "
             "approval for a 90-day pilot and the RM capacity to run it.")
    num(s)

    # --- appendix divider --------------------------------------------------
    s = blank(prs)
    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(3.0), SW, Inches(1.5))
    band.fill.solid(); band.fill.fore_color.rgb = INK; band.line.fill.background()
    tf = textbox(s, Inches(0.8), Inches(3.1), Inches(11.7), Inches(1.3), MSO_ANCHOR.MIDDLE)
    r = tf.paragraphs[0].add_run(); r.text = "Appendix — methodology & practices"; _set(r, 30, WHITE, bold=True)
    p = tf.add_paragraph(); r = p.add_run()
    r.text = "For technical Q&A: how we did each step."; _set(r, 16, WHITE)
    num(s)

    # --- appendix content slides ------------------------------------------
    def appx(code, title_txt, items, img=None, img_lbl=None):
        s = blank(prs); title_bar(s, title_txt, code)
        w = Inches(6.2) if img else Inches(12.1)
        bullets(s, [F(x) for x in items], Inches(0.6), Inches(1.9), w, Inches(4.8), size=13, gap=7)
        if img:
            image_or_placeholder(s, img, Inches(7.0), Inches(1.9), Inches(5.7), Inches(4.4), img_lbl)
        num(s)

    appx("A1", "Data understanding & cleaning", section_bullets(aA, "Data understanding", "Cleaning steps"))
    appx("A2", "Validation, checksums & data quality", section_bullets(aA, "Validation & checksums", "Data-processing best practices"))
    appx("A3", "Synthetic data: method & fidelity", section_bullets(aA, "Synthetic data method", "Synthetic data fidelity"),
         img=A / "figures" / "synthetic_vs_real.png", img_lbl="synthetic_vs_real.png")
    appx("A4", "EDA method", section_bullets(aC, "EDA method"))
    appx("A5", "Feature engineering & models compared", section_bullets(aB, "Feature engineering", "Models compared"))
    appx("A6", "Validation design, leakage & robustness", section_bullets(aB, "Validation design", "Leakage & robustness checks"))
    appx("A7", "Explainability, fairness & responsible AI", section_bullets(aB, "Explainability", "Fairness & responsible AI"))
    appx("A8", "Prioritisation logic & unseen-data demo", section_bullets(aB, "Prioritisation logic", "Unseen-data demo"))
    appx("A9", "Power BI model design + dashboard", section_bullets(aA, "Power BI model design"),
         img=A / "screens" / "page1.png", img_lbl="page1.png (Power BI screenshot)")
    appx("A10", "Pilot design & power calculation", section_bullets(aC, "Pilot design method"))

    # A11: AI disclosure (read whole file as bullets)
    s = blank(prs); title_bar(s, "Limitations, next steps & AI disclosure", "A11")
    disc = (C / "ai_disclosure.md")
    items = [l.strip()[1:].strip() for l in (disc.read_text(encoding="utf-8").splitlines() if disc.exists() else [])
             if l.strip().startswith("-")][:10]
    bullets(s, items or ["(ai_disclosure.md missing)"], Inches(0.6), Inches(1.9), Inches(12.1), Inches(4.8), size=12.5, gap=6)
    num(s)

    out_path = C / "Meridian_Retention.pptx"
    prs.save(out_path)
    print(f"Deck -> {out_path}  ({len(prs.slides._sldIdLst)} slides)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
