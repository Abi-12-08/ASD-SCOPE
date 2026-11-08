import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart

# ============================================================
# ASD-SCOPE | Awareness, Reflection and Support
# Educational demonstration - NOT a diagnostic tool
# ============================================================

st.set_page_config(
    page_title="ASD-SCOPE | Awareness & Reflection",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded",
)

QUESTIONS = [
    ("Communication", "I sometimes find it difficult to tell when someone is being sarcastic.",
     "Think about how you understand jokes, irony, and indirect language."),
    ("Social situations", "After spending time in a group, I sometimes need quiet time to recharge.",
     "Consider how social activities affect your energy and comfort."),
    ("Sensory preferences", "Certain everyday sounds, lights, or textures can feel overwhelming to me.",
     "Think about your personal reactions to sensory environments."),
    ("Routines", "I feel more comfortable when I know what to expect from my day.",
     "Consider whether a predictable routine helps you feel comfortable."),
    ("Communication", "I sometimes need extra time to work out what someone means.",
     "Think about conversations, hints, and implied meanings."),
    ("Social situations", "I sometimes find busy social environments tiring or difficult to navigate.",
     "Consider how crowded or unfamiliar social settings feel."),
    ("Sensory preferences", "I notice small environmental details that other people may not mention.",
     "Think about background sounds, patterns, and changes around you."),
    ("Routines", "Unexpected changes to a plan can take me some time to adjust to.",
     "Consider how you respond when familiar plans change."),
    ("Interests", "I enjoy spending a lot of time learning about topics that interest me.",
     "Think about how you explore hobbies and subjects you enjoy."),
    ("Personal preferences", "I sometimes prefer communicating in a way that differs from the people around me.",
     "Consider your preferences for speaking, writing, or messaging."),
]

ANSWER_OPTIONS = ["Not answered", "Not at all", "A little", "Quite a bit", "Very much"]
VALID_ANSWERS = ANSWER_OPTIONS[1:]

IMPACT_OPTIONS = [
    "No meaningful impact reported",
    "Some impact or distress",
    "Significant impact or persistent concern",
    "Unsure / prefer not to say",
]

CATEGORY_ORDER = [
    "Communication",
    "Social situations",
    "Sensory preferences",
    "Routines",
    "Interests",
    "Personal preferences",
]

PAGES = [
    "Home",
    "Reflection Questionnaire",
    "My Responses & Next Steps",
    "Comfort & Accessibility",
    "Support & Resources",
]

DEFAULTS = {
    "page": "Home",
    "answers": {},
    "impact": IMPACT_OPTIONS[-1],
    "age_range": "Prefer not to say",
    "dark": False,
    "contrast": False,
    "font": "Standard",
    "reduce_motion": False,
    "reflection_topics": [],
    "personal_notes": "",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ------------------ Visual settings ------------------

if st.session_state.contrast:
    theme = dict(
        bg="#FFFFFF",
        surface="#FFFFFF",
        text="#111111",
        muted="#333333",
        border="#777777",
        accent="#0037CC",
        notice="#FFF2CC",
        notice_text="#3B2A00",
        input="#FFFFFF",
        input_text="#111111",
    )
elif st.session_state.dark:
    theme = dict(
        bg="#111827",
        surface="#1F2937",
        text="#F9FAFB",
        muted="#D1D5DB",
        border="#475569",
        accent="#93C5FD",
        notice="#3B3425",
        notice_text="#FDE68A",
        input="#273449",
        input_text="#F9FAFB",
    )
else:
    theme = dict(
        bg="#FFFFFF",
        surface="#F5F7FB",
        text="#172033",
        muted="#536176",
        border="#DCE3ED",
        accent="#246BFD",
        notice="#FFF7E6",
        notice_text="#513800",
        input="#FFFFFF",
        input_text="#172033",
    )

# Button colors are explicitly paired so labels remain readable in every theme.
button_bg = theme["surface"]
button_text = theme["text"]
button_border = theme["border"]
primary_button_bg = theme["accent"]
primary_button_text = "#FFFFFF" if (st.session_state.contrast or not st.session_state.dark) else "#111827"

font_px = {
    "Standard": "16px",
    "Large": "19px",
    "Extra large": "22px",
}[st.session_state.font]

# Animated background colors remain subtle so both light and dark modes stay readable.
# High-contrast mode and the Reduce Motion setting disable the background animation.
if st.session_state.contrast or st.session_state.reduce_motion:
    background_animation_css = """
    [data-testid="stAppViewContainer"]::before,
    [data-testid="stAppViewContainer"]::after {
        animation: none !important;
        opacity: 0 !important;
    }
    """
else:
    if st.session_state.dark:
        blob_opacity = "0.24"
    else:
        blob_opacity = "0.34"

    background_animation_css = f"""
    [data-testid="stAppViewContainer"] {{
        position: relative;
        isolation: isolate;
        overflow: hidden;
        background: {theme["bg"]} !important;
    }}

    [data-testid="stAppViewContainer"]::before,
    [data-testid="stAppViewContainer"]::after {{
        content: "";
        position: fixed;
        inset: -18%;
        z-index: -1;
        pointer-events: none;
        border-radius: 50%;
        filter: blur(58px);
        opacity: {blob_opacity};
        will-change: transform, background-position;
    }}

    [data-testid="stAppViewContainer"]::before {{
        background:
            radial-gradient(ellipse at 18% 24%, #56C8F5 0%, transparent 34%),
            radial-gradient(ellipse at 74% 20%, #9B7BFF 0%, transparent 31%),
            radial-gradient(ellipse at 55% 78%, #47E0C1 0%, transparent 34%);
        animation: asdScopeFloatOne 24s ease-in-out infinite alternate;
    }}

    [data-testid="stAppViewContainer"]::after {{
        background:
            radial-gradient(ellipse at 82% 62%, #FF8BCB 0%, transparent 30%),
            radial-gradient(ellipse at 28% 78%, #7EA6FF 0%, transparent 32%);
        animation: asdScopeFloatTwo 30s ease-in-out infinite alternate;
    }}

    @keyframes asdScopeFloatOne {{
        0%   {{ transform: translate3d(-2%, -1%, 0) scale(1); }}
        50%  {{ transform: translate3d(3%, 2%, 0) scale(1.06); }}
        100% {{ transform: translate3d(-1%, 4%, 0) scale(0.98); }}
    }}

    @keyframes asdScopeFloatTwo {{
        0%   {{ transform: translate3d(2%, 3%, 0) scale(1.02); }}
        50%  {{ transform: translate3d(-3%, -2%, 0) scale(0.96); }}
        100% {{ transform: translate3d(2%, -4%, 0) scale(1.07); }}
    }}
    """

st.markdown(f"""
<style>
:root {{ color-scheme: {"dark" if st.session_state.dark and not st.session_state.contrast else "light"}; }}
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="stMainBlockContainer"], .block-container {{
    background:{theme["bg"]} !important;
    color:{theme["text"]} !important;
    font-size:{font_px} !important;
}}
/* Let the softly animated color layer show through the main canvas. */
[data-testid="stMain"], [data-testid="stMainBlockContainer"], .block-container {{
    background: transparent !important;
}}
[data-testid="stHeader"] {{ background:transparent !important; }}
h1,h2,h3,h4,p,li,label,[data-testid="stMarkdownContainer"] {{
    color:{theme["text"]} !important;
}}
[data-testid="stCaptionContainer"] {{ color:{theme["muted"]} !important; }}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div,
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
    background:#101827 !important;
}}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
    color:#F8FAFC !important;
}}
[data-testid="stSidebar"] .stButton > button {{
    width:100%;
    text-align:left;
    border-radius:8px;
    margin-bottom:3px;
}}
.card {{
    background:{theme["surface"]};
    border:1px solid {theme["border"]};
    border-radius:14px;
    padding:20px;
    margin-bottom:14px;
}}
.card h3,.card p {{ color:{theme["text"]} !important; }}
.hero {{
    background:linear-gradient(120deg,#102447,#234F91);
    padding:30px;
    border-radius:18px;
    margin-bottom:22px;
}}
.hero h1,.hero p,.hero div {{ color:white !important; }}
.notice {{
    background:{theme["notice"]};
    border-left:5px solid #D99000;
    padding:15px;
    border-radius:8px;
    margin:14px 0;
}}
.notice strong,.notice p {{ color:{theme["notice_text"]} !important; }}
/* Consistent, accessible button styling: secondary buttons use theme surfaces;
   primary actions use the accent with a deliberately contrasting label. */
.stButton > button,
.stFormSubmitButton > button,
[data-testid="stBaseButton-secondary"] {{
    background:{button_bg} !important;
    color:{button_text} !important;
    border:1px solid {button_border} !important;
    border-radius:9px;
    min-height:42px;
    font-weight:600;
}}
.stButton > button p,
.stFormSubmitButton > button p,
[data-testid="stBaseButton-secondary"] p {{
    color:{button_text} !important;
}}
.stButton > button:hover,
.stFormSubmitButton > button:hover,
[data-testid="stBaseButton-secondary"]:hover {{
    background:{theme["input"]} !important;
    color:{button_text} !important;
    border-color:{theme["accent"]} !important;
}}
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {{
    background:{primary_button_bg} !important;
    color:{primary_button_text} !important;
    border:1px solid {primary_button_bg} !important;
    border-radius:9px;
    min-height:42px;
    font-weight:700;
}}
.stButton > button[kind="primary"] p,
.stFormSubmitButton > button[kind="primary"] p,
[data-testid="stBaseButton-primary"] p {{
    color:{primary_button_text} !important;
}}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {{
    filter:brightness(0.94);
}}
.stButton > button:focus-visible,
.stFormSubmitButton > button:focus-visible {{
    outline:3px solid {theme["accent"]} !important;
    outline-offset:2px !important;
}}
[data-testid="stApp"] input,[data-testid="stApp"] textarea,[data-baseweb="select"] > div {{
    background:{theme["input"]} !important;
    color:{theme["input_text"]} !important;
    border-color:{theme["border"]} !important;
}}
{background_animation_css}
</style>
""", unsafe_allow_html=True)

# ------------------ Helpers ------------------

def answered_count():
    return sum(
        st.session_state.answers.get(i) in VALID_ANSWERS
        for i in range(len(QUESTIONS))
    )


def clear_responses():
    st.session_state.answers = {}
    st.session_state.impact = IMPACT_OPTIONS[-1]
    st.session_state.reflection_topics = []
    st.session_state.personal_notes = ""

    for i in range(len(QUESTIONS)):
        st.session_state.pop(f"q_{i}", None)

    st.session_state.pop("impact_input", None)


def disclaimer():
    st.markdown("""
    <div class="notice">
        <strong>Important educational disclaimer</strong>
        <p>These are original illustrative reflection questions. This demonstration is not a validated
        screening instrument, diagnostic test, or substitute for professional assessment. Responses
        cannot establish or rule out autism.</p>
    </div>
    """, unsafe_allow_html=True)


def guidance():
    impact = st.session_state.impact

    if impact == IMPACT_OPTIONS[2]:
        return (
            "Consider discussing your concerns with a qualified healthcare professional. "
            "Specific examples of how these experiences affect daily life may be useful."
        )

    if impact == IMPACT_OPTIONS[1]:
        return (
            "If these experiences continue to cause distress or interfere with everyday activities, "
            "consider discussing them with a qualified healthcare professional."
        )

    if impact == IMPACT_OPTIONS[0]:
        return (
            "You have not reported a meaningful impact in this response. This is a reflection only; "
            "it does not rule autism in or out."
        )

    return (
        "If you are unsure, observe when these experiences occur and whether they affect daily life. "
        "You can seek professional guidance if you have ongoing concerns."
    )


def response_frame():
    rows = []

    for i, (category, question, explanation) in enumerate(QUESTIONS):
        answer = st.session_state.answers.get(i)

        if answer in VALID_ANSWERS:
            rows.append({
                "Category": category,
                "Response": answer,
                "Question": question,
                "Explanation": explanation,
                "Question number": i + 1,
            })

    return pd.DataFrame(
        rows,
        columns=[
            "Category",
            "Response",
            "Question",
            "Explanation",
            "Question number",
        ],
    )


def submit_answers():
    for i in range(len(QUESTIONS)):
        answer = st.session_state.get(f"q_{i}", "Not answered")

        if answer in VALID_ANSWERS:
            st.session_state.answers[i] = answer
        else:
            st.session_state.answers.pop(i, None)

    st.session_state.impact = st.session_state.get(
        "impact_input",
        IMPACT_OPTIONS[-1],
    )

    st.session_state.page = "My Responses & Next Steps"


def report_text(value):
    replacements = {
        "—": "-",
        "–": "-",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "•": "-",
        "…": "...",
    }

    value = str(value or "")

    for old, new in replacements.items():
        value = value.replace(old, new)

    return escape(value)


def build_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="ASD-SCOPE Reflection Report",
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ASDTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=27,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#17345E"),
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="ASDSub",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#536176"),
        spaceAfter=14,
    ))

    styles.add(ParagraphStyle(
        name="ASDSection",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#17345E"),
        spaceBefore=12,
        spaceAfter=7,
    ))

    styles.add(ParagraphStyle(
        name="ASDQ",
        parent=styles["Heading3"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#17345E"),
        spaceBefore=8,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="ASDBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="ASDSmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#536176"),
        spaceAfter=5,
    ))

    styles.add(ParagraphStyle(
        name="ASDCallout",
        parent=styles["BodyText"],
        fontSize=9,
        leading=14,
        borderColor=colors.HexColor("#B7CBE8"),
        borderWidth=0.8,
        borderPadding=9,
        backColor=colors.HexColor("#F3F7FC"),
        spaceBefore=5,
        spaceAfter=8,
    ))

    story = []
    data = response_frame()
    count = answered_count()

    story += [
        Spacer(1, 8 * mm),
        Paragraph("ASD-SCOPE", styles["ASDTitle"]),
        Paragraph(
            "Awareness, Reflection and Support",
            styles["ASDSub"],
        ),
        Paragraph(
            "PERSONAL REFLECTION REPORT",
            styles["Heading1"],
        ),
        Paragraph(
            f"Report generated: {date.today().strftime('%d %B %Y')}",
            styles["ASDBody"],
        ),
        Paragraph(
            "This report organizes your own responses and may be used as a conversation aid.",
            styles["ASDBody"],
        ),
        Paragraph(
            "<b>Important:</b> Original illustrative questions only. "
            "This is not a validated screening instrument or diagnostic test "
            "and cannot establish or rule out autism.",
            styles["ASDCallout"],
        ),
        Paragraph(
            "1. Response overview",
            styles["ASDSection"],
        ),
    ]

    overview = [
        ["Measure", "Summary"],
        ["Questions answered", f"{count} of {len(QUESTIONS)}"],
        ["Questions unanswered", str(len(QUESTIONS) - count)],
        [
            "Categories represented",
            str(data["Category"].nunique() if not data.empty else 0),
        ],
        ["Age range", report_text(st.session_state.age_range)],
        [
            "Reported everyday impact",
            report_text(st.session_state.impact),
        ],
    ]

    table = Table(
        overview,
        colWidths=[65 * mm, 98 * mm],
        repeatRows=1,
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17345E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#EAF0F8")),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#172033")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    story += [
        table,
        Spacer(1, 4 * mm),
        Paragraph(
            "2. Response graphs",
            styles["ASDSection"],
        ),
        Paragraph(
            "These graphs summarize selections only; "
            "they are not clinical scores or severity measures.",
            styles["ASDSmall"],
        ),
    ]

    if not data.empty:
        category_counts = (
            data.groupby("Category")
            .size()
            .reindex(CATEGORY_ORDER, fill_value=0)
        )
    else:
        category_counts = pd.Series(
            0,
            index=CATEGORY_ORDER,
        )

    drawing = Drawing(480, 210)

    chart = HorizontalBarChart()
    chart.x = 155
    chart.y = 18
    chart.width = 285
    chart.height = 165
    chart.data = [list(category_counts.values)]
    chart.categoryAxis.categoryNames = CATEGORY_ORDER
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(
        1,
        int(category_counts.max()),
    )
    chart.valueAxis.valueStep = 1
    chart.valueAxis.labels.fontSize = 7
    chart.bars[0].fillColor = colors.HexColor("#356FE0")
    chart.bars[0].strokeColor = colors.HexColor("#356FE0")
    chart.barWidth = 13
    chart.groupSpacing = 7

    drawing.add(chart)

    drawing.add(String(
        155,
        194,
        "Answered questions by category",
        fontName="Helvetica-Bold",
        fontSize=9,
        fillColor=colors.HexColor("#17345E"),
    ))

    story += [
        drawing,
        Paragraph(
            "Selected response options by category",
            styles["ASDQ"],
        ),
    ]

    matrix = [
        [
            int(
                (
                    (data["Category"] == category)
                    & (data["Response"] == answer)
                ).sum()
            ) if not data.empty else 0
            for category in CATEGORY_ORDER
        ]
        for answer in VALID_ANSWERS
    ]

    drawing2 = Drawing(480, 225)

    chart2 = VerticalBarChart()
    chart2.x = 45
    chart2.y = 45
    chart2.width = 405
    chart2.height = 145
    chart2.data = matrix
    chart2.categoryAxis.categoryNames = CATEGORY_ORDER
    chart2.categoryAxis.labels.fontName = "Helvetica"
    chart2.categoryAxis.labels.fontSize = 6.5
    chart2.categoryAxis.labels.angle = 20
    chart2.categoryAxis.labels.dy = -4
    chart2.valueAxis.valueMin = 0
    chart2.valueAxis.valueMax = max(
        1,
        max((sum(row) for row in matrix), default=0),
    )
    chart2.valueAxis.valueStep = 1
    chart2.valueAxis.labels.fontSize = 7
    chart2.valueAxis.visibleGrid = True
    chart2.groupSpacing = 8
    chart2.barWidth = 10

    palette = [
        "#64748B",
        "#60A5FA",
        "#2563EB",
        "#17345E",
    ]

    for index, color in enumerate(palette):
        chart2.bars[index].fillColor = colors.HexColor(color)
        chart2.bars[index].strokeColor = colors.HexColor(color)

    drawing2.add(chart2)

    lx = 25
    ly = 16

    for index, answer in enumerate(VALID_ANSWERS):
        drawing2.add(Rect(
            lx,
            ly,
            7,
            7,
            fillColor=colors.HexColor(palette[index]),
            strokeColor=colors.HexColor(palette[index]),
        ))

        drawing2.add(String(
            lx + 10,
            ly - 1,
            answer,
            fontName="Helvetica",
            fontSize=7,
            fillColor=colors.HexColor("#172033"),
        ))

        lx += [82, 80, 95, 105][index]

    story += [
        drawing2,
        PageBreak(),
        Paragraph(
            "3. Complete questionnaire record",
            styles["ASDSection"],
        ),
        Paragraph(
            "Each question includes all response choices and the selection saved in this session.",
            styles["ASDBody"],
        ),
    ]

    for i, (category, question, explanation) in enumerate(QUESTIONS):
        selected = st.session_state.answers.get(
            i,
            "Not answered",
        )

        rows = [
            ["Available option", "Selection"],
        ]

        rows.extend([
            [
                option,
                "SELECTED" if option == selected else "Not selected",
            ]
            for option in ANSWER_OPTIONS
        ])

        t = Table(
            rows,
            colWidths=[95 * mm, 68 * mm],
            repeatRows=1,
        )

        selected_row = ANSWER_OPTIONS.index(selected) + 1

        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17345E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#172033")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            (
                "BACKGROUND",
                (0, selected_row),
                (-1, selected_row),
                colors.HexColor("#DCEBFF"),
            ),
            (
                "FONTNAME",
                (0, selected_row),
                (-1, selected_row),
                "Helvetica-Bold",
            ),
        ]))

        story.append(KeepTogether([
            Paragraph(
                f"Question {i + 1} - {report_text(category)}",
                styles["ASDQ"],
            ),
            Paragraph(
                report_text(question),
                styles["ASDBody"],
            ),
            Paragraph(
                f"Explanation: {report_text(explanation)}",
                styles["ASDSmall"],
            ),
            t,
            Spacer(1, 4 * mm),
        ]))

    story += [
        Paragraph(
            "4. Reflection topics",
            styles["ASDSection"],
        ),
    ]

    if st.session_state.reflection_topics:
        story.extend(
            Paragraph(
                f"- {report_text(topic)}",
                styles["ASDBody"],
            )
            for topic in st.session_state.reflection_topics
        )
    else:
        story.append(Paragraph(
            "No optional reflection topics selected.",
            styles["ASDBody"],
        ))

    story += [
        Paragraph(
            "5. Reported impact and next steps",
            styles["ASDSection"],
        ),
        Paragraph(
            f"<b>Impact response:</b> {report_text(st.session_state.impact)}",
            styles["ASDBody"],
        ),
        Paragraph(
            report_text(guidance()),
            styles["ASDBody"],
        ),
        Paragraph(
            "You may note specific examples, when an experience occurs, and whether it affects everyday "
            "activities. If you have ongoing concerns, consider speaking with a qualified professional "
            "experienced in the relevant area. You may bring this report as a conversation aid.",
            styles["ASDBody"],
        ),
    ]

    if st.session_state.personal_notes.strip():
        story += [
            Paragraph(
                "Personal notes",
                styles["ASDSection"],
            ),
            Paragraph(
                report_text(st.session_state.personal_notes).replace("\n", "<br/>"),
                styles["ASDBody"],
            ),
        ]

    story += [
        Paragraph(
            "6. A message from ASD-SCOPE",
            styles["ASDSection"],
        ),
        Paragraph(
            "Your responses are a starting point for reflection, not a label or conclusion about who you are. "
            "Everyone has their own ways of communicating and navigating everyday life. You deserve to have "
            "your experiences heard and taken seriously.",
            styles["ASDCallout"],
        ),
        Paragraph(
            "Report limitations",
            styles["ASDSection"],
        ),
        Paragraph(
            "ASD-SCOPE uses original illustrative questions and descriptive summaries. It does not use a "
            "validated clinical scoring system, diagnose, or determine whether an assessment is indicated.",
            styles["ASDBody"],
        ),
    ]

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(
            18 * mm,
            10 * mm,
            "ASD-SCOPE - Personal Reflection Report",
        )
        canvas.drawRightString(
            A4[0] - 18 * mm,
            10 * mm,
            f"Page {document.page}",
        )
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    pdf = buffer.getvalue()
    buffer.close()

    return pdf
# ------------------ Sidebar ------------------

with st.sidebar:
    st.markdown(
        "<div style='padding:8px 0 18px'>"
        "<div style='font-size:2rem;font-weight:700'>🧩 ASD-SCOPE</div>"
        "<div style='color:#C5D9FF'>Awareness • Reflection • Support</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### Navigation")

    for item in PAGES:
        if st.button(
            ("● " if st.session_state.page == item else "○ ") + item,
            key=f"nav_{item}",
            use_container_width=True,
        ):
            st.session_state.page = item
            st.rerun()

    st.markdown("---")
    st.markdown("### Your progress")
    st.progress(answered_count() / len(QUESTIONS))
    st.caption(f"{answered_count()} of {len(QUESTIONS)} questions answered")
    st.caption("Educational demonstration — not a clinical tool.")


# ------------------ Page routing ------------------

page = st.session_state.page


# ============================================================
# HOME
# ============================================================

if page == "Home":

    st.markdown(
        "<div class='hero'>"
        "<div style='text-transform:uppercase;letter-spacing:1.5px;font-size:.8rem'>"
        "An educational demonstration</div>"
        "<h1>Welcome to ASD-SCOPE</h1>"
        "<p>Explore everyday communication, routines, sensory experiences, "
        "and personal preferences in a respectful, accessible environment.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    with left:
        st.markdown(
            "<div class='card'><h3>📝 Reflection questionnaire</h3>"
            "<p>Ten illustrative questions; edit answers at any time.</p></div>",
            unsafe_allow_html=True,
        )

        if st.button("Start questionnaire", type="primary", use_container_width=True):
            st.session_state.page = "Reflection Questionnaire"
            st.rerun()

    with right:
        st.markdown(
            "<div class='card'><h3>🌿 Comfort & accessibility</h3>"
            "<p>Adjust theme, text size, contrast, and motion.</p></div>",
            unsafe_allow_html=True,
        )

        if st.button("Personalize experience", use_container_width=True):
            st.session_state.page = "Comfort & Accessibility"
            st.rerun()

    left, right = st.columns(2)

    with left:
        st.markdown(
            "<div class='card'><h3>📋 Responses & report</h3>"
            "<p>Review descriptive summaries and export a PDF.</p></div>",
            unsafe_allow_html=True,
        )

        if st.button("Review responses", use_container_width=True):
            st.session_state.page = "My Responses & Next Steps"
            st.rerun()

    with right:
        st.markdown(
            "<div class='card'><h3>🤝 Support & resources</h3>"
            "<p>Find general information and professional support guidance.</p></div>",
            unsafe_allow_html=True,
        )

        if st.button("Explore resources", use_container_width=True):
            st.session_state.page = "Support & Resources"
            st.rerun()

    st.markdown("### What ASD-SCOPE offers")

    st.markdown(
        "<div class='card'><p>Interactive reflection, descriptive category summaries, "
        "a printable personal report, next-step guidance, and comfort settings. "
        "It does not predict or diagnose.</p></div>",
        unsafe_allow_html=True,
    )

    disclaimer()


# ============================================================
# REFLECTION QUESTIONNAIRE
# ============================================================

elif page == "Reflection Questionnaire":

    st.title("Reflection Questionnaire")

    st.write(
        "Consider each statement and choose the response that best reflects "
        "your experience. There are no right or wrong answers."
    )

    disclaimer()

    # Age range is a separate introductory question.
    # It is not included in the 10 reflection questions or charts.

    st.markdown("### Before you begin")

    st.selectbox(
        "Which age range do you belong to?",
        [
            "20–29",
            "30–39",
            "40–49",
            "50+",
            "Prefer not to say",
        ],
        key="age_range",
        help="This is background information only and is not included in reflection summaries.",
    )

    st.progress(answered_count() / len(QUESTIONS))
    st.caption(f"{answered_count()} of {len(QUESTIONS)} responses saved")

    with st.form("reflection_form"):

        for i, (category, question, explanation) in enumerate(QUESTIONS):

            st.caption(
                f"QUESTION {i + 1} OF {len(QUESTIONS)} · {category.upper()}"
            )

            st.markdown(f"**{question}**")
            st.caption(explanation)

            previous = st.session_state.answers.get(
                i,
                "Not answered",
            )

            st.radio(
                f"Response to question {i + 1}",
                ANSWER_OPTIONS,
                index=ANSWER_OPTIONS.index(previous),
                key=f"q_{i}",
                horizontal=True,
                label_visibility="collapsed",
            )

            st.markdown("---")

        st.markdown("### Everyday impact and support")

        st.write(
            "Do these experiences cause distress or make everyday activities "
            "more difficult? This is used only for general guidance."
        )

        st.radio(
            "How would you describe the impact?",
            IMPACT_OPTIONS,
            index=IMPACT_OPTIONS.index(st.session_state.impact),
            key="impact_input",
            label_visibility="collapsed",
        )

        st.form_submit_button(
            "Save responses and review",
            use_container_width=True,
            type="primary",
            on_click=submit_answers,
        )

    st.caption(
        "You may submit partially completed responses and return while this session remains active."
    )


# ============================================================
# MY RESPONSES & NEXT STEPS
# ============================================================

elif page == "My Responses & Next Steps":

    st.title("My Responses & Next Steps")

    st.write(
        "Review answers, explore descriptive insights, "
        "and create a printable reflection report."
    )

    disclaimer()

    data = response_frame()
    count = answered_count()

    a, b, c = st.columns(3)

    a.metric("Questions answered", f"{count}/{len(QUESTIONS)}")
    b.metric("Questions remaining", len(QUESTIONS) - count)
    c.metric(
        "Categories explored",
        data["Category"].nunique() if not data.empty else 0,
    )

    st.progress(count / len(QUESTIONS))

    if data.empty:

        st.info("No saved responses yet.")

        if st.button("Open questionnaire", type="primary"):
            st.session_state.page = "Reflection Questionnaire"
            st.rerun()

    else:

        st.markdown("## Your descriptive insights")

        st.write(
            "Charts summarize your selections only. "
            "They are not clinical scores or predictions."
        )

        counts = (
            data.groupby("Category")
            .size()
            .reindex(CATEGORY_ORDER, fill_value=0)
        )

        st.bar_chart(
            counts[counts > 0],
            horizontal=True,
            x_label="Answered questions",
            y_label="Category",
        )

        matrix = (
            data.groupby(["Category", "Response"])
            .size()
            .unstack(fill_value=0)
            .reindex(
                index=CATEGORY_ORDER,
                columns=VALID_ANSWERS,
                fill_value=0,
            )
        )

        matrix = matrix.loc[matrix.sum(axis=1) > 0]

        if not matrix.empty:
            st.bar_chart(
                matrix,
                x_label="Category",
                y_label="Responses",
                stack=True,
            )

        st.caption(
            "Categories contain different numbers of questions; "
            "response patterns must not be interpreted as severity."
        )

        st.markdown("### Category overview")

        for category in CATEGORY_ORDER:

            subset = data[data.Category == category]

            if not subset.empty:

                with st.expander(
                    f"{category} · {len(subset)} answered"
                ):

                    for _, row in subset.iterrows():

                        st.markdown(
                            f"**Question {row['Question number']}:** "
                            f"{row['Question']}"
                        )

                        st.markdown(
                            f"**Your response:** {row['Response']}"
                        )

                        st.caption(row["Explanation"])

        st.markdown("### Topics you choose to reflect on")

        st.multiselect(
            "Select optional topics",
            CATEGORY_ORDER,
            key="reflection_topics",
        )

        st.markdown("### Personal notes (optional)")

        st.text_area(
            "Notes for yourself or a future conversation",
            key="personal_notes",
            placeholder=(
                "You can write examples, contexts, "
                "or questions you would like to discuss."
            ),
        )

        st.markdown("### Reported impact and general guidance")

        st.markdown(
            f"<div class='card'><h3>{escape(st.session_state.impact)}</h3>"
            f"<p>{escape(guidance())}</p></div>",
            unsafe_allow_html=True,
        )

        st.markdown("### General next steps")

        st.markdown(
            "- Note specific experiences and their effect on daily activities.\n"
            "- If concerns persist, consider speaking with a qualified healthcare professional.\n"
            "- You may bring the PDF report to help explain your experiences.\n"
            "- This demonstration cannot establish or rule out autism."
        )

        st.markdown("---")
        st.markdown("### Printable reflection report")

        try:

            pdf_bytes = build_pdf()

            st.download_button(
                "Download Reflection Report (PDF)",
                data=pdf_bytes,
                file_name="ASD-SCOPE_Reflection_Report.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

        except Exception as error:

            st.error(
                "PDF generation failed. Confirm ReportLab is installed."
            )

            st.caption(f"Technical detail: {error}")

        left, right = st.columns(2)

        with left:

            if st.button("Edit responses", use_container_width=True):
                st.session_state.page = "Reflection Questionnaire"
                st.rerun()

        with right:

            if st.button("Clear all responses", use_container_width=True):
                clear_responses()
                st.rerun()

    st.caption(
        "Responses are held in Streamlit session state. This demo does not deliberately "
        "write them to a file/database; this is not a guarantee of server-level privacy."
    )


# ============================================================
# COMFORT & ACCESSIBILITY
# ============================================================

elif page == "Comfort & Accessibility":

    st.title("Comfort & Accessibility")

    st.write("Personalize how ASD-SCOPE looks and feels.")

    dark = st.toggle(
        "🌙 Use dark mode",
        value=st.session_state.dark,
        key="dark_setting",
    )

    contrast = st.toggle(
        "◐ Use higher contrast",
        value=st.session_state.contrast,
        key="contrast_setting",
    )

    font = st.radio(
        "Text size",
        ["Standard", "Large", "Extra large"],
        index=["Standard", "Large", "Extra large"].index(
            st.session_state.font
        ),
        horizontal=True,
        key="font_setting",
    )

    reduce = st.toggle(
        "Reduce animations and transitions",
        value=st.session_state.reduce_motion,
        key="motion_setting",
    )

    if (
        dark,
        contrast,
        font,
        reduce,
    ) != (
        st.session_state.dark,
        st.session_state.contrast,
        st.session_state.font,
        st.session_state.reduce_motion,
    ):

        st.session_state.dark = dark
        st.session_state.contrast = contrast
        st.session_state.font = font
        st.session_state.reduce_motion = reduce

        st.rerun()

    st.markdown(
        "<div class='card'><h3>Your comfort matters.</h3>"
        "<p>Choose the settings that make the app easiest to read.</p></div>",
        unsafe_allow_html=True,
    )

    if contrast:
        st.info("High-contrast mode takes priority over dark mode.")
    elif dark:
        st.info("Dark mode is active.")
    else:
        st.info("Light mode is active.")

    st.caption(
        "Preferences are held for the active session and may reset when it ends."
    )


# ============================================================
# SUPPORT & RESOURCES
# ============================================================

elif page == "Support & Resources":

    st.title("Support & Resources")

    st.write(
        "Learning about autism and finding appropriate support can take time. "
        "You do not need to draw conclusions from this demonstration."
    )

    st.markdown(
        "<div class='card'><h3>When professional guidance may help</h3>"
        "<p>If you have ongoing questions about communication, sensory experiences, "
        "routines, development, or daily functioning, a qualified healthcare professional "
        "can help explore concerns and discuss whether an assessment is appropriate.</p></div>",
        unsafe_allow_html=True,
    )

    st.markdown("### Finding appropriate support")

    st.markdown(
        "1. Write down experiences or questions you would like to discuss.\n"
        "2. Look for a suitably qualified professional experienced in autism assessment "
        "for the relevant age group.\n"
        "3. Ask about qualifications, assessment process, accessibility, fees, "
        "and available support.\n"
        "4. In India, you may ask a registered healthcare provider or recognized "
        "hospital for a referral."
    )

    st.markdown("### General information")

    st.markdown(
        "- [World Health Organization — Autism](https://www.who.int/health-topics/autism)\n"
        "- [NICE — Autism in adults](https://www.nice.org.uk/guidance/cg142)\n"
        "- [National Institute of Mental Health and Neurosciences (NIMHANS)]"
        "(https://nimhans.ac.in/)"
    )

    st.markdown("### Preparing for a conversation")

    st.markdown(
        "- Describe concrete examples and when they happen.\n"
        "- Note what helps and what makes things harder.\n"
        "- Bring relevant questions or this reflection report if you choose.\n"
        "- You can ask about the professional's experience and the process."
    )

    disclaimer()


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    f"<div style='text-align:center;padding:10px 0 18px'>"
    f"<p style='color:{theme['muted']} !important'><b>ASD-SCOPE</b> · "
    f"Educational project demonstration</p>"
    f"<p style='color:{theme['muted']} !important;font-size:.85rem'>"
    f"Promoting understanding, accessibility, and respectful reflection. "
    f"Not a validated screening or diagnostic tool.</p></div>",
    unsafe_allow_html=True,
)