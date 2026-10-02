import base64
import hmac
import html as html_lib
import io
import json
import os
import zipfile
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo
from email.message import EmailMessage
from email.utils import formatdate
from urllib.parse import parse_qs, quote, quote_plus, unquote, urljoin, urlparse

from bs4 import BeautifulSoup
from fpdf import FPDF
import pandas as pd
from pydantic import BaseModel, Field
import requests
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# DESIGN SYSTEM (theme, CSS & HTML components)
# ==========================================

APP_NAME = "Fortlox Prospector"
APP_TAGLINE = "Fortlox Security · free business finder"

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #0A0E1A;
  --surface: #111827;
  --surface-2: #161F33;
  --surface-3: #1C2740;
  --border: rgba(148, 163, 184, 0.14);
  --border-strong: rgba(148, 163, 184, 0.26);
  --text: #E7EAF3;
  --muted: #8C98B0;
  --faint: #5E6A82;
  --accent: #29A9E1;
  --accent-2: #5FD0FF;
  --accent-soft: rgba(41, 169, 225, 0.14);
  --good: #34D399;
  --warn: #FBBF24;
  --risk: #FB923C;
  --bad: #F87171;
  --radius: 14px;
  --grad: linear-gradient(135deg, #29A9E1 0%, #5FD0FF 100%);
}

html, body, [class*="css"], .stApp, button, input, textarea, select {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif !important;
}
.stApp {
  background:
    radial-gradient(1200px 500px at 85% -10%, rgba(56, 214, 245, 0.07), transparent 60%),
    radial-gradient(900px 500px at 10% -20%, rgba(41, 169, 225, 0.10), transparent 60%),
    var(--bg);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"] { display: none; }
footer { visibility: hidden; }
.block-container { padding-top: 1.6rem !important; padding-bottom: 3rem !important; max-width: 1500px; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0D1322 0%, #0A0E1A 100%);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarContent"] { padding-top: 0.6rem; }
[data-testid="stSidebarUserContent"] { padding-top: 1rem; }

/* ---------- Typography ---------- */
h1, h2, h3, h4 { color: var(--text); letter-spacing: -0.02em; }
p, li, label, .stMarkdown { color: var(--text); }
[data-testid="stCaptionContainer"], .stCaption { color: var(--muted) !important; }
[data-testid="stWidgetLabel"] p {
  font-size: 0.76rem !important; font-weight: 600 !important; color: var(--muted) !important;
  text-transform: uppercase; letter-spacing: 0.06em;
}

/* ---------- Cards (bordered containers) ---------- */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]),
div[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: var(--radius) !important;
}
.st-key-card-queue { margin-top: 18px; }
.st-key-card-left, .st-key-card-select, .st-key-card-right, .st-key-card-login, .st-key-card-queue {
  background: linear-gradient(180deg, rgba(22, 31, 51, 0.85) 0%, rgba(17, 24, 39, 0.85) 100%);
  border: 1px solid var(--border) !important;
  border-radius: var(--radius);
  padding: 22px 22px 18px 22px;
  box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset, 0 20px 40px -24px rgba(0,0,0,0.6);
}

/* ---------- Inputs ---------- */
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
  background: var(--surface) !important;
  border: 1px solid var(--border-strong) !important;
  border-radius: 10px !important;
  transition: border-color .15s ease, box-shadow .15s ease;
}
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within, [data-baseweb="textarea"]:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-soft) !important;
}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea { color: var(--text) !important; }
[data-baseweb="input"] > div, [data-baseweb="base-input"] { background: transparent !important; }
textarea { font-family: 'Inter', sans-serif !important; font-size: 0.9rem !important; line-height: 1.55 !important; }

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  border-radius: 10px !important; font-weight: 600 !important; padding: 0.55rem 1.1rem !important;
  border: 1px solid var(--border-strong) !important; background: var(--surface-2) !important;
  color: var(--text) !important; transition: all .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  border-color: var(--accent) !important; color: #fff !important; transform: translateY(-1px);
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"], .stFormSubmitButton > button,
[data-testid="stBaseButton-primary"] {
  background: var(--grad) !important; border: none !important; color: #0A0E1A !important;
  box-shadow: 0 8px 24px -10px rgba(41, 169, 225, 0.8);
}
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {
  filter: brightness(1.08); color: #0A0E1A !important;
}
.stButton > button[kind="primary"] p, [data-testid="stBaseButton-primary"] p, .stFormSubmitButton > button p { color: #0A0E1A !important; font-weight: 700 !important; }

.stLinkButton a, [data-testid^="stBaseLinkButton"] {
  border-radius: 10px !important; font-weight: 700 !important; padding: 0.55rem 1.1rem !important;
}
[data-testid="stBaseLinkButton-primary"], .stLinkButton a[kind="primary"] {
  background: var(--grad) !important; border: none !important; color: #0A0E1A !important;
  box-shadow: 0 8px 24px -10px rgba(41, 169, 225, 0.8);
}
[data-testid="stBaseLinkButton-primary"] p, .stLinkButton a[kind="primary"] p { color: #0A0E1A !important; font-weight: 700 !important; }
[data-testid="stBaseLinkButton-primary"]:hover { filter: brightness(1.08); }

/* ---------- Tabs ---------- */
[data-testid="stTabs"] [role="tablist"], [data-baseweb="tab-list"] {
  gap: 4px; background: var(--surface); padding: 4px; border-radius: 12px; border: 1px solid var(--border);
}
[data-testid="stTabs"] [role="tab"], [data-baseweb="tab"] {
  border-radius: 9px !important; padding: 8px 16px !important; height: auto !important;
  color: var(--muted) !important; background: transparent !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"], [data-baseweb="tab"][aria-selected="true"] { background: var(--surface-3) !important; color: var(--text) !important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"], [data-testid="stTabs"] .react-aria-SelectionIndicator { display: none !important; }
[data-testid="stTabs"] [role="tab"] p { font-weight: 600; font-size: 0.86rem; }
[data-testid="stTabs"] [role="tablist"] { width: fit-content; margin-bottom: 6px; }

/* ---------- Table, expanders, alerts ---------- */
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
[data-testid="stExpander"] details { background: var(--surface); border: 1px solid var(--border) !important; border-radius: 12px !important; }
[data-testid="stExpander"] summary p { font-size: 0.85rem; color: var(--muted); font-weight: 600; }
[data-testid="stAlert"] { border-radius: 12px !important; border: 1px solid var(--border) !important; }
[data-testid="stCode"] pre, .stCode pre { background: var(--surface) !important; border: 1px solid var(--border); border-radius: 12px; }
hr { border-color: var(--border) !important; }

/* ================= Custom components ================= */
.pe-hero { display: flex; align-items: center; justify-content: space-between; gap: 24px; flex-wrap: wrap;
  padding: 6px 2px 22px 2px; margin-bottom: 18px; border-bottom: 1px solid var(--border); }
.st-key-logo-card img { border-radius: 12px; background: #fff; padding: 6px; }
.pe-eyebrow { display: inline-flex; align-items: center; gap: 8px; font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--accent-2); margin-bottom: 8px; }
.pe-eyebrow .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--good); box-shadow: 0 0 0 4px rgba(52,211,153,.15); }
.pe-title { font-size: 2.05rem; font-weight: 800; letter-spacing: -0.035em; line-height: 1.1; margin: 0; color: var(--text); }
.pe-title span { background: var(--grad); -webkit-background-clip: text; background-clip: text; color: transparent; }
.pe-sub { color: var(--muted); font-size: 0.95rem; margin-top: 8px; max-width: 620px; }

.pe-stepper { display: flex; align-items: center; gap: 6px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 999px; padding: 6px; }
.pe-step { display: flex; align-items: center; gap: 8px; padding: 7px 14px 7px 7px; border-radius: 999px;
  font-size: 0.82rem; font-weight: 600; color: var(--faint); white-space: nowrap; }
.pe-step .num { width: 24px; height: 24px; border-radius: 50%; display: grid; place-items: center; font-size: 0.72rem;
  font-weight: 700; border: 1px solid var(--border-strong); color: var(--faint); }
.pe-step.done { color: var(--muted); }
.pe-step.done .num { background: rgba(52,211,153,.14); border-color: rgba(52,211,153,.45); color: var(--good); }
.pe-step.active { background: var(--surface-3); color: var(--text); }
.pe-step.active .num { background: var(--grad); border: none; color: #0A0E1A; }
.pe-step-sep { width: 14px; height: 1px; background: var(--border-strong); }

.pe-section { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.pe-section .badge { width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center;
  background: var(--accent-soft); color: var(--accent); font-weight: 800; font-size: 0.85rem; border: 1px solid rgba(41,169,225,.3); }
.pe-section .t { font-size: 1.08rem; font-weight: 700; color: var(--text); line-height: 1.2; }
.pe-section .s { font-size: 0.82rem; color: var(--muted); margin-top: 2px; }

.pe-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.pe-chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 0.76rem;
  font-weight: 600; background: var(--surface-3); color: var(--text); border: 1px solid var(--border); white-space: nowrap; }
.pe-chip.accent { background: var(--accent-soft); color: #A9DDF6; border-color: rgba(41,169,225,.3); }
.pe-chip.good { background: rgba(52,211,153,.12); color: var(--good); border-color: rgba(52,211,153,.3); }
.pe-chip.warn { background: rgba(251,191,36,.12); color: var(--warn); border-color: rgba(251,191,36,.3); }
.pe-chip.risk { background: rgba(251,146,60,.12); color: var(--risk); border-color: rgba(251,146,60,.3); }
.pe-chip.bad { background: rgba(248,113,113,.12); color: var(--bad); border-color: rgba(248,113,113,.3); }
.pe-chip.muted { background: transparent; color: var(--muted); }

.pe-vertical { display: flex; gap: 14px; align-items: flex-start; background: var(--surface); border: 1px dashed var(--border-strong);
  border-radius: 12px; padding: 12px 14px; margin: 2px 0 14px 0; }
.pe-vertical .lbl { font-size: 0.7rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--faint); margin-bottom: 6px; }

.pe-kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 4px 0 14px 0; }
.pe-kpi { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px; }
.pe-kpi .v { font-size: 1.35rem; font-weight: 800; color: var(--text); letter-spacing: -0.02em; }
.pe-kpi .l { font-size: 0.72rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }

.pe-selected { display: flex; align-items: center; justify-content: space-between; gap: 12px; background: var(--accent-soft);
  border: 1px solid rgba(41,169,225,.35); border-radius: 12px; padding: 12px 14px; margin: 14px 0 10px 0; }
.pe-selected .n { font-weight: 700; color: var(--text); }
.pe-selected .m { font-size: 0.8rem; color: var(--muted); margin-top: 2px; }
.pe-hint { display: flex; align-items: center; gap: 10px; color: var(--muted); font-size: 0.86rem; background: var(--surface);
  border: 1px dashed var(--border-strong); border-radius: 12px; padding: 12px 14px; margin-top: 12px; }

.pe-empty { text-align: center; padding: 48px 24px 40px 24px; }
.pe-empty .t { font-size: 1.1rem; font-weight: 700; color: var(--text); margin-top: 14px; }
.pe-empty .s { font-size: 0.88rem; color: var(--muted); margin: 6px auto 20px auto; max-width: 360px; line-height: 1.5; }
.pe-empty ol { text-align: left; display: inline-block; margin: 0 auto; padding: 0; list-style: none; counter-reset: s; }
.pe-empty li { counter-increment: s; color: var(--muted); font-size: 0.86rem; margin: 8px 0; display: flex; align-items: center; gap: 10px; }
.pe-empty li::before { content: counter(s); width: 22px; height: 22px; border-radius: 50%; display: grid; place-items: center;
  background: var(--surface-3); border: 1px solid var(--border-strong); font-size: 0.72rem; font-weight: 700; color: var(--text); }

.pe-firm { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 14px; }
.pe-firm .name { font-size: 1.35rem; font-weight: 800; letter-spacing: -0.025em; color: var(--text); line-height: 1.2; }
.pe-firm .meta { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.pe-firm .blurb { color: var(--muted); font-size: 0.86rem; line-height: 1.5; margin-top: 10px; font-style: italic; }

.pe-grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
@media (max-width: 1100px) { .pe-grid2 { grid-template-columns: 1fr; } .pe-kpis { grid-template-columns: 1fr 1fr 1fr; } }
.pe-panel { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 14px; margin-bottom: 10px; }
.pe-cols { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 0 18px; }
@media (max-width: 1250px) { .pe-cols { grid-template-columns: 1fr; } }
.pe-hook { margin-bottom: 10px; }
.pe-panel .h { font-size: 0.7rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--faint); margin-bottom: 10px; }

.pe-contact { display: flex; align-items: center; gap: 12px; }
.pe-avatar { width: 44px; height: 44px; border-radius: 12px; display: grid; place-items: center; font-weight: 800; font-size: 0.95rem;
  background: var(--grad); color: #0A0E1A; flex-shrink: 0; }
.pe-contact .n { font-weight: 700; font-size: 1.02rem; color: var(--text); }
.pe-contact .r { font-size: 0.8rem; color: var(--muted); margin-top: 2px; }

.pe-row { display: flex; align-items: center; gap: 10px; padding: 7px 0; border-top: 1px solid var(--border); font-size: 0.86rem; }
.pe-row:first-of-type { border-top: none; }
.pe-row svg { color: var(--accent-2); flex-shrink: 0; }
.pe-row a, .pe-row span { color: var(--text) !important; text-decoration: none; overflow-wrap: anywhere; }
.pe-row .tag { color: var(--faint) !important; white-space: nowrap; }
.pe-row a.trunc { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; overflow-wrap: normal; }
.pe-row a:hover { color: var(--accent-2) !important; }
.pe-row .tag { margin-left: auto; font-size: 0.68rem; color: var(--faint); font-weight: 600; text-transform: uppercase; letter-spacing: .05em; }
.pe-none { color: var(--faint); font-size: 0.84rem; font-style: italic; }

.pe-officer { display: flex; justify-content: space-between; gap: 8px; padding: 6px 0; border-top: 1px solid var(--border); font-size: 0.84rem; }
.pe-officer:first-of-type { border-top: none; }
.pe-officer .who { color: var(--text); font-weight: 600; }
.pe-officer .since { color: var(--faint); font-size: 0.76rem; white-space: nowrap; }

.pe-hook { background: linear-gradient(135deg, rgba(41,169,225,.12), rgba(95,208,255,.06)); border: 1px solid rgba(41,169,225,.28);
  border-radius: 12px; padding: 14px 16px; }
.pe-hook .h { font-size: 0.7rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #A9DDF6; }
.pe-hook .t { font-weight: 700; color: var(--text); margin: 4px 0 10px 0; }
.pe-hook ul { margin: 0; padding-left: 0; list-style: none; }
.pe-hook li { font-size: 0.85rem; color: var(--text); padding: 4px 0 4px 24px; position: relative; }
.pe-hook li::before { content: ""; position: absolute; left: 4px; top: 10px; width: 8px; height: 8px; border-radius: 50%; background: var(--grad); }

/* Workspace switch in sidebar */
[data-testid="stSidebar"] [role="radiogroup"] { gap: 6px; margin-bottom: 6px; }
[data-testid="stSidebar"] [role="radiogroup"] label { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 9px 12px !important; margin: 0 !important; width: 100%; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { border-color: rgba(41,169,225,.55); background: var(--accent-soft); }
[data-testid="stSidebar"] [role="radiogroup"] label p { font-weight: 600 !important; font-size: .88rem !important; color: var(--text) !important;
  text-transform: none !important; letter-spacing: 0 !important; }
/* LinkedIn panel */
.st-key-card-linkedin { background: var(--surface); border: 1px solid rgba(10,102,194,.45) !important; border-radius: 12px;
  padding: 14px 14px 10px 14px; margin-bottom: 10px; }
.li-head { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; }
.li-head .t { font-weight: 700; color: var(--text); font-size: .95rem; }
.li-head .s { font-size: .8rem; color: var(--muted); margin-top: 1px; }
.li-badge { width: 30px; height: 30px; border-radius: 7px; background: #0A66C2; color: #fff; font-weight: 800; font-size: .95rem;
  display: grid; place-items: center; flex-shrink: 0; font-family: Arial, sans-serif; }
.li-mini { width: 15px; height: 15px; border-radius: 3px; background: #0A66C2; color: #fff; font-weight: 800; font-size: .62rem;
  display: grid; place-items: center; flex-shrink: 0; font-family: Arial, sans-serif; }
/* Sidebar components */
.pe-brand { display: flex; align-items: center; gap: 12px; padding: 4px 0 18px 0; border-bottom: 1px solid var(--border); margin-bottom: 16px; }
.pe-logo { width: 40px; height: 40px; border-radius: 12px; background: var(--grad); display: grid; place-items: center; color: #0A0E1A;
  box-shadow: 0 10px 24px -10px rgba(41,169,225,.9); }
.pe-brand .n { font-weight: 800; font-size: 1.05rem; color: var(--text); letter-spacing: -0.02em; }
.pe-brand .s { font-size: 0.75rem; color: var(--muted); }
.pe-side-h { font-size: 0.68rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--faint); margin: 18px 0 8px 0; }
.pe-status { display: flex; align-items: center; justify-content: space-between; font-size: 0.84rem; color: var(--text); padding: 7px 0; }
.pe-status .st { display: inline-flex; align-items: center; gap: 6px; font-size: 0.76rem; font-weight: 600; }
.pe-status .st.ok { color: var(--good); } .pe-status .st.off { color: var(--bad); } .pe-status .st.idle { color: var(--muted); }
.pe-status .st::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.pe-stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
.pe-stat { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 10px; text-align: center; }
.pe-stat .v { font-weight: 800; font-size: 1.1rem; color: var(--text); }
.pe-stat .l { font-size: 0.64rem; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; font-weight: 600; margin-top: 2px; }

/* Login */
.pe-login-head { text-align: center; margin: 8vh 0 22px 0; }
.pe-login-head .pe-logo { width: 54px; height: 54px; margin: 0 auto 16px auto; border-radius: 16px; }
.pe-login-head .t { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.03em; color: var(--text); }
.pe-login-head .s { color: var(--muted); font-size: 0.92rem; margin-top: 6px; }
</style>
"""

_ICON_PATHS = {
    "mail": '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "pin": '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "pointer": '<path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/>',
}


def _full_width_kwargs() -> Dict[str, Any]:
    """Full-width buttons: 'width' on Streamlit 1.46+, 'use_container_width' before that."""
    import inspect
    try:
        if "width" in inspect.signature(st.button).parameters:
            return {"width": "stretch"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": True}


FULL_WIDTH = _full_width_kwargs()


def icon(name: str, size: int = 16, stroke: float = 2) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        f' stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{_ICON_PATHS[name]}</svg>'
    )


def esc(value: Any) -> str:
    """Escapes scraped/registry text before it goes into HTML."""
    return html_lib.escape(str(value if value is not None else ""), quote=True)


def render_html(markup: str, target=None) -> None:
    """Renders HTML via markdown. Lines are flattened so markdown never treats indentation as code."""
    flat = "".join(line.strip() for line in markup.splitlines())
    (target or st).markdown(flat, unsafe_allow_html=True)


def inject_css() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def chip(text: str, tone: str = "") -> str:
    return f'<span class="pe-chip {tone}">{esc(text)}</span>'


def section_header(num: str, title: str, subtitle: str = "") -> None:
    render_html(
        f'<div class="pe-section"><div class="badge">{num}</div><div>'
        f'<div class="t">{esc(title)}</div>'
        + (f'<div class="s">{esc(subtitle)}</div>' if subtitle else "")
        + "</div></div>"
    )


def hero_html(active_step: int) -> str:
    steps = ["Target", "Select", "Enrich", "Pitch"]
    parts = []
    for i, label in enumerate(steps, start=1):
        state = "done" if i < active_step else "active" if i == active_step else ""
        num = icon("check", 12, 3) if state == "done" else str(i)
        parts.append(f'<div class="pe-step {state}"><span class="num">{num}</span>{label}</div>')
    stepper = '<div class="pe-step-sep"></div>'.join(parts)
    return (
        '<div class="pe-hero"><div>'
        '<div class="pe-eyebrow"><span class="dot"></span>Fortlox Security · Free, no-key business finder</div>'
        '<div class="pe-title">Fortlox <span>Prospector</span></div>'
        '<div class="pe-sub">Find local businesses by sector, pull their contact details from the open web,'
        ' then send a Fortlox-branded pitch and one-page overview.</div>'
        f'</div><div class="pe-stepper">{stepper}</div></div>'
    )


def confidence_chip(confidence: Optional[str]) -> str:
    tones = {
        "High": ("good", "High-confidence match"),
        "Medium": ("warn", "Medium-confidence match"),
        "Low": ("risk", "Low-confidence match"),
        "Manual": ("accent", "Website entered manually"),
    }
    tone, label = tones.get(confidence or "", ("bad", "Website not found"))
    return chip(label, tone)


def display_officer_name(raw: str) -> str:
    """'BYWATER, Paul James' -> 'Paul James Bywater'; company officers are just title-cased."""
    if "," in raw:
        surname, forenames = raw.split(",", 1)
        return f"{forenames.strip().title()} {surname.strip().title()}".strip()
    return raw.title()


def initials(name: str) -> str:
    words = [w for w in re.split(r"[\s&/]+", name or "") if w and w[0].isalpha()]
    return ("".join(w[0] for w in words[:2]) or "?").upper()


# ==========================================
# 0. PASSWORD GATEWAY (STREAMLIT SECRETS)
# ==========================================


def check_password() -> bool:
    # Fail CLOSED: if the secret is missing or misconfigured, nobody gets in.
    try:
        configured_password = st.secrets["APP_PASSWORD"]
    except Exception:
        configured_password = None
    if not configured_password:
        st.set_page_config(page_title=f"{APP_NAME} · Locked", page_icon="🎯", layout="centered")
        inject_css()
        render_html(
            f'<div class="pe-login-head"><div class="pe-logo">{icon("lock", 24, 2.2)}</div>'
            '<div class="t">App locked</div>'
            '<div class="s">APP_PASSWORD isn\'t set in Streamlit Secrets, so access is blocked.</div></div>'
        )
        st.error("Add APP_PASSWORD under App settings → Secrets, then reload.")
        return False

    def password_entered():
        if hmac.compare_digest(
            st.session_state.get("password", "").encode("utf-8"),
            str(configured_password).encode("utf-8"),
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.set_page_config(page_title=f"{APP_NAME} · Sign in", page_icon="🎯", layout="centered")
    inject_css()
    _, mid, _ = st.columns([1, 2.2, 1])
    with mid:
        render_html(
            f'<div class="pe-login-head"><div class="pe-logo">{icon("target", 26, 2.2)}</div>'
            f'<div class="t">{APP_NAME}</div>'
            f'<div class="s">{APP_TAGLINE} · Authorised users only</div></div>'
        )
        with st.container(key="card-login"):
            with st.form("Credentials", border=False):
                st.text_input("Access password", type="password", key="password",
                              placeholder="Enter your password")
                st.form_submit_button("Sign in", on_click=password_entered,
                                      type="primary", **FULL_WIDTH)
            if (
                "password_correct" in st.session_state
                and not st.session_state["password_correct"]
            ):
                st.error("Incorrect password. Please try again.")

    return False


TPS_DISCLAIMER = (
    "Contact details shown in this app come from public sources and have <b>not</b> been checked "
    "against the Telephone Preference Service (TPS) or Corporate TPS (CTPS) registers."
)


def check_disclaimer() -> bool:
    """Shown once per sign-in: the user must accept the TPS disclaimer before using the app."""
    if st.session_state.get("tps_ack"):
        return True
    st.set_page_config(page_title=f"{APP_NAME} · Before you start", page_icon="🎯", layout="centered")
    inject_css()
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        render_html(
            f'<div class="pe-login-head"><div class="pe-logo">{icon("shield", 26, 2.2)}</div>'
            '<div class="t">Before you start</div>'
            '<div class="s">Please read and accept the disclaimer below</div></div>'
        )
        with st.container(key="card-login"):
            render_html(
                f'<div style="font-size:14px;line-height:1.6">{TPS_DISCLAIMER}<br><br>'
                "By using this application you understand that it is <b>your sole responsibility</b> "
                "to check every number against the TPS and CTPS registers (and to follow any other "
                "marketing rules that apply) <b>before contacting any business or person</b> found "
                "through it. The app developer accepts no liability for contact made without these checks.</div>"
            )
            render_html(
                "<style>.st-key-card-login [data-testid='stCheckbox']{margin:14px 0 6px}"
                ".st-key-card-login [data-testid='stCheckbox'] p{text-transform:none!important;letter-spacing:0!important;"
                "font-size:14px!important;font-weight:600!important;color:var(--text,#E6EDF7)!important}"
                ".st-key-card-login button:disabled{opacity:.4;filter:grayscale(.6);box-shadow:none!important;cursor:not-allowed}</style>"
            )
            agreed = st.checkbox("I understand and accept responsibility for TPS/CTPS checks", key="tps_tick")
            if st.button("Accept and continue", type="primary", disabled=not agreed, **FULL_WIDTH):
                st.session_state["tps_ack"] = True
                st.session_state["tps_ack_at"] = datetime.now().strftime("%d %b %Y, %H:%M")
                st.rerun()
    return False


if not check_password():
    st.stop()
if not check_disclaimer():
    st.stop()

# ==========================================
# 1. VERTICALS, CRMS & PITCH PLAYBOOKS
# ==========================================

VERTICAL_PRESETS = {
    "Estate & Lettings Agents": {
        "sic_codes": ["68310"],
        "description": "Real estate agencies & letting operations",
        "search_hint": "Estate Agents",
        "crms": ["Street", "Alto", "Reapit", "Dezrez", "Jupix"],
        "primary_hook": "CRM Integration (Street / Alto / Reapit)",
        "fallback_greeting": "Lettings & Sales Team",
        "pitch_bullets": [
            "Screen pop-up of every client or landlord record the moment they call",
            "Automatic voice recording syncing directly to the property file",
            "Click to dial directly inside your CRM / property portal",
            "Every lead, missed call & call note tracked automatically",
        ],
        "default_cta": "Let me know how many phones or softphone users you have, and I'll send over a quote.",
    },
    "Dental Practices": {
        "sic_codes": ["86230"],
        "description": "Dental practice activities",
        "search_hint": "Dental Practice",
        "crms": ["Dentally", "EXACT", "Carestream R4"],
        "primary_hook": "PMS Integration (Dentally / EXACT / R4)",
        "fallback_greeting": "Practice Manager",
        "pitch_bullets": [
            "Patient records pop up on reception screens when the phone rings",
            "Calls log automatically against the right patient chart",
            "Missed calls are flagged instantly for follow up and recall retention",
            "Call recordings are stored compliantly against the patient file",
        ],
        "default_cta": "How many handsets does the practice currently use? I can send over a no obligation quote.",
    },
    "Solicitors & Legal Practices": {
        "sic_codes": ["69102"],
        "description": "Solicitors & legal service providers",
        "search_hint": "Solicitors",
        "crms": ["Clio", "LEAP", "Proclaim", "Actionstep"],
        "primary_hook": "Matter Management Integration (Clio / LEAP)",
        "fallback_greeting": "Practice Manager",
        "pitch_bullets": [
            "Dial straight from the active client or matter record",
            "Mobile & desktop softphone app so fee earners can take calls securely anywhere",
            "One unified system across reception, every fee earner and all branch offices",
            "Call recordings & billable duration synced back to the matter file",
        ],
        "default_cta": "Let me know which system you run and roughly how many users you have, and I'll send over a quote.",
    },
    "Accountants & Auditors": {
        "sic_codes": ["69201"],
        "description": "Accounting, bookkeeping & tax consultancy",
        "search_hint": "Accountants",
        "crms": ["Iris", "CCH", "TaxCalc", "Xero Practice Manager"],
        "primary_hook": "Client Portal & Time Tracking Integration",
        "fallback_greeting": "Practice Partner",
        "pitch_bullets": [
            "Client identification card pops on screen the moment they call",
            "Automatic call logging against client tax and year-end audit folders",
            "Seamless transfer between desk phones and laptop softphones for hybrid staff",
            "Consolidated line rental and cloud voice to reduce fixed telecom overheads",
        ],
        "default_cta": "Let me know your approximate team size and I can send over an indicative quote.",
    },
    "General Medical Clinics": {
        "sic_codes": ["86210"],
        "description": "General medical practice activities",
        "search_hint": "Clinic",
        "crms": ["EMIS Web", "SystmOne", "Semble", "Heydoc"],
        "primary_hook": "Clinical System Integration & Triage Routing",
        "fallback_greeting": "Clinic Manager",
        "pitch_bullets": [
            "Patient record screen-pop to accelerate inbound triage",
            "Automated call queueing & peak-time patient callback features",
            "Encrypted, compliant voice recordings stored per patient file",
            "Direct transfer lines between triage staff, clinicians, and administration",
        ],
        "default_cta": "How many lines or handsets do you operate? I can send over a no obligation overview.",
    },
}


class OfficerInfo(BaseModel):
    name: str
    role: str  # Friendly label, e.g. "Director"
    raw_role: str = ""  # Companies House value, e.g. "llp-designated-member"
    appointed_on: Optional[str] = None
    is_owner: bool = False  # Also a Person with Significant Control


class ScrapedLead(BaseModel):
    company_name: str
    company_number: Optional[str] = None
    source_id: Optional[str] = None  # e.g. OSM-n123 when found on OpenStreetMap
    sic_codes: List[str] = Field(default_factory=list)
    sector_guess: str = "General B2B"
    registered_address: Optional[str] = None
    website_url: Optional[str] = None
    phones_found: List[str] = Field(default_factory=list)
    emails_found: List[str] = Field(default_factory=list)
    officers: List[OfficerInfo] = Field(default_factory=list)
    site_meta_description: Optional[str] = None
    trading_name: Optional[str] = None  # From Google Maps, e.g. "J Dent Dental Care"
    contact_name: Optional[str] = None  # Added by a person after checking LinkedIn etc.
    contact_role: Optional[str] = None
    contact_email: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_confidence: Optional[str] = None  # High / Medium / Low / Manual
    website_reasons: List[str] = Field(default_factory=list)
    discovery_notes: List[str] = Field(default_factory=list)
    other_emails: List[str] = Field(default_factory=list)  # Third-party addresses (agencies, regulators)
    pages_checked: List[str] = Field(default_factory=list)


# ==========================================
# 2. ENRICHMENT & SCRAPING ENGINE
# ==========================================


# ------------------------------------------------------------------
# Web discovery & extraction helpers
# ------------------------------------------------------------------

LEGAL_SUFFIX_WORDS = {
    "LTD", "LIMITED", "PLC", "LLP", "LP", "GROUP", "HOLDINGS", "UK", "(UK)",
    "CO", "COMPANY", "THE", "T/A", "INTERNATIONAL",
}

# Words too common to identify a firm on their own (kept for the full-name match)
GENERIC_NAME_WORDS = {
    "and", "the", "of", "dental", "dentist", "dentists", "practice", "practices",
    "surgery", "clinic", "clinics", "medical", "health", "healthcare", "care",
    "solicitors", "solicitor", "law", "legal", "lawyers", "partners", "partnership",
    "accountants", "accountancy", "accounting", "tax", "bookkeeping", "associates",
    "estate", "estates", "agents", "agency", "lettings", "letting", "property",
    "properties", "residential", "sales", "services", "consultants", "consultancy",
    "management", "uk", "ltd", "limited", "llp", "plc", "group", "holdings", "co",
}

# Directories, portals, social media, regulators and review sites — never a firm's own site.
BLOCKED_DOMAINS = {
    "company-information.service.gov.uk", "gov.uk", "companieshouse.gov.uk",
    "endole.co.uk", "duedil.com", "opencorporates.com", "companycheck.co.uk",
    "checkcompany.co.uk", "companiesintheuk.co.uk", "bizdb.co.uk", "companieslist.co.uk",
    "company-data.co.uk", "ukcompanieslist.com", "find-and-update.company-information.service.gov.uk",
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "youtube.com", "tiktok.com", "pinterest.com", "wikipedia.org",
    "yell.com", "thomsonlocal.com", "scoot.co.uk", "192.com", "cylex-uk.co.uk",
    "freeindex.co.uk", "hotfrog.co.uk", "yelp.co.uk", "yelp.com", "trustpilot.com",
    "google.com", "google.co.uk", "bing.com", "duckduckgo.com", "maps.apple.com",
    "rightmove.co.uk", "zoopla.co.uk", "onthemarket.com", "primelocation.com",
    "allagents.co.uk", "getagent.co.uk", "homipi.co.uk", "propertymark.co.uk",
    "whatclinic.com", "doctify.com", "topdoctors.co.uk", "cqc.org.uk", "gdc-uk.org",
    "lawsociety.org.uk", "solicitors.lawsociety.org.uk", "sra.org.uk",
    "reviewsolicitors.co.uk", "solicitors.guru", "icaew.com", "accaglobal.com",
    "checkatrade.com", "ratedpeople.com", "bark.com", "mybuilder.com",
    "indeed.com", "indeed.co.uk", "glassdoor.co.uk", "reed.co.uk", "totaljobs.com",
    "zoominfo.com", "rocketreach.co", "apollo.io", "dnb.com", "kompass.com",
    "crunchbase.com", "bloomberg.com", "misterwhat.co.uk", "brownbook.net",
    "fyple.co.uk", "opendi.co.uk", "tuugo.co.uk", "infobel.com", "cybo.com",
    "n49.com", "businessmagnet.co.uk", "streetcheck.co.uk", "amazon.co.uk",
    "ebay.co.uk", "gumtree.com", "tripadvisor.co.uk", "118118.com", "ukphonebook.com",
}
# Blocked only as the exact domain (their subdomains can be real practice sites, e.g. xyzsurgery.nhs.uk)
BLOCKED_EXACT_ONLY = {"nhs.uk"}

FREE_MAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "hotmail.com", "hotmail.co.uk", "outlook.com",
    "live.co.uk", "live.com", "yahoo.com", "yahoo.co.uk", "btinternet.com",
    "btconnect.com", "icloud.com", "me.com", "aol.com", "sky.com", "virginmedia.com",
    "talktalk.net", "nhs.net",
}

# Link hints for pages worth scraping, most useful first
CONTACT_PAGE_HINTS = [
    "contact", "get-in-touch", "get in touch", "getintouch", "find-us", "find us",
    "our-team", "our team", "meet-the-team", "meet the team", "team", "our-people",
    "people", "branches", "offices", "about",
]

JUNK_EMAIL_MARKERS = (
    "example.", "sentry", "wixpress", "domain.com", "yourname", "youremail",
    "email.com", "@2x", "noreply", "no-reply", "donotreply", "u003e", "godaddy",
    "wordpress", "schema.org", "@sentry", "@ingest", "test@",
)
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+'-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,24}")
PHONE_TEXT_RE = re.compile(
    r"(?:\+\s?44\s?(?:\(0\)\s?)?|0044\s?|\(?0)\d[\d \-\(\)]{7,14}\d"
)


def domain_of(url: str) -> Optional[str]:
    if not url:
        return None
    if "://" not in url:
        url = "https://" + url
    host = (urlparse(url).hostname or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host or None


FOREIGN_OK_TLDS = {"uk", "co", "io", "me", "ai", "tv", "eu", "ly", "fm", "cc"}
BLOCKED_DOMAINS |= {
    "zhihu.com", "baidu.com", "quora.com", "reddit.com", "medium.com", "weibo.com", "bilibili.com", "vk.com",
    "naver.com", "yahoo.com", "msn.com", "imdb.com", "booking.com", "expedia.co.uk", "trivago.co.uk",
    "github.com", "apple.com", "microsoft.com", "wikimedia.org", "wiktionary.org", "britannica.com",
    "find-open.co.uk", "yably.co.uk", "locallife.co.uk", "companieshousedata.co.uk", "ukbusinessforums.co.uk",
    "bizstats.co.uk", "companydatashop.com", "checkcompany.uk", "find-and-update.company-information.service.gov.uk",
}


def is_blocked_domain(domain: str) -> bool:
    domain = domain.lower()
    if domain in BLOCKED_EXACT_ONLY:
        return True
    tld = domain.rsplit(".", 1)[-1]
    if len(tld) == 2 and tld not in FOREIGN_OK_TLDS:
        return True  # Another country's site (.cn, .de, .ru…): never a UK firm's own website
    return any(domain == b or domain.endswith("." + b) for b in BLOCKED_DOMAINS)


def domain_label(domain: str) -> str:
    """'www.hart-new-homes.co.uk' -> 'hartnewhomes'"""
    parts = domain.lower().split(".")
    for suffix_len in (3, 2, 1):  # handles .co.uk, .org.uk, .com etc
        tail = ".".join(parts[-suffix_len:])
        if tail in {"co.uk", "org.uk", "me.uk", "ltd.uk", "plc.uk", "nhs.uk", "net.uk"} and len(parts) > 2:
            return re.sub(r"[^a-z0-9]", "", parts[-3])
    return re.sub(r"[^a-z0-9]", "", parts[-2] if len(parts) >= 2 else parts[0])


def distinctive_name_tokens(company_name: str) -> List[str]:
    """'HART NEW HOMES (WALSALL) LIMITED' -> ['hart', 'new', 'homes', 'walsall']"""
    words = re.sub(r"[^a-z0-9 ]", " ", company_name.lower().replace("&", " and ")).split()
    words = [w for w in words if w.upper() not in LEGAL_SUFFIX_WORDS]
    distinct = [w for w in words if w not in GENERIC_NAME_WORDS]
    return distinct or words


def guess_domains(company_name: str) -> List[str]:
    """Likely domains straight from the name — a fallback when search engines block us."""
    words = [w for w in re.sub(r"[^a-z0-9& ]", " ", company_name.lower()).split()
             if w.upper() not in LEGAL_SUFFIX_WORDS and w != "&"]
    if not words:
        return []
    joined, hyphen = "".join(words), "-".join(words)
    distinct = [w for w in words if w not in GENERIC_NAME_WORDS]
    guesses = [f"{joined}.co.uk", f"{joined}.com", f"{hyphen}.co.uk", f"{joined}.uk"]
    if distinct and distinct != words:
        short = "".join(distinct)
        if len(short) >= 5:
            guesses.append(f"{short}.co.uk")
    return [g for g in dict.fromkeys(guesses) if len(g) <= 70]


def decode_cfemail(hex_string: str) -> Optional[str]:
    """Decodes Cloudflare's 'email protection' obfuscation."""
    try:
        data = bytes.fromhex(hex_string)
        key = data[0]
        return "".join(chr(b ^ key) for b in data[1:])
    except (ValueError, IndexError):
        return None


def clean_email(raw: str) -> Optional[str]:
    em = unquote(raw or "").strip().strip(".,;:()<>[]'\"").lower()
    em = em.split("?")[0]
    m = EMAIL_RE.fullmatch(em)
    if not m or len(em) > 80:
        return None
    if em.endswith(IMAGE_EXTS) or any(j in em for j in JUNK_EMAIL_MARKERS):
        return None
    return em


def extract_emails(soup: BeautifulSoup, html: str) -> Set[str]:
    found: Set[str] = set()
    # 1. mailto: links
    for a in soup.select('a[href^="mailto:" i]'):
        em = clean_email(a["href"].split(":", 1)[1])
        if em:
            found.add(em)
    # 2. Cloudflare-protected emails
    for el in soup.select("[data-cfemail]"):
        em = clean_email(decode_cfemail(el.get("data-cfemail", "")) or "")
        if em:
            found.add(em)
    for a in soup.select('a[href*="/cdn-cgi/l/email-protection#"]'):
        em = clean_email(decode_cfemail(a["href"].split("#", 1)[1]) or "")
        if em:
            found.add(em)
    # 3. Visible text, including "name [at] firm [dot] co.uk" style
    text = soup.get_text(" ")
    text = re.sub(r"\s*[\[\(\{]\s*at\s*[\]\)\}]\s*", "@", text, flags=re.I)
    text = re.sub(r"\s*[\[\(\{]\s*dot\s*[\]\)\}]\s*", ".", text, flags=re.I)
    # 4. Structured data (JSON-LD "email": "...")
    for script in soup.find_all("script", type="application/ld+json"):
        text += " " + (script.string or "")
    for raw in EMAIL_RE.findall(text):
        em = clean_email(raw)
        if em:
            found.add(em)
    return found


def normalise_uk_phone(raw: str) -> Optional[str]:
    """Any UK format -> standard display format, e.g. '+44 (0)1922 123456' -> '01922 123456'."""
    if not raw:
        return None
    raw = unquote(raw).replace("(0)", "")
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("0044"):
        digits = "0" + digits[4:]
    elif digits.startswith("44") and len(digits) == 12:
        digits = "0" + digits[2:]
    if not digits.startswith("0") or len(digits) not in (10, 11) or digits[1] not in "123578":
        return None
    d = digits
    if len(d) == 10:
        return f"{d[:5]} {d[5:]}"
    if d.startswith("02"):
        return f"{d[:3]} {d[3:7]} {d[7:]}"            # 020 7946 0000
    if d.startswith(("03", "08")):
        return f"{d[:4]} {d[4:7]} {d[7:]}"            # 0800 123 4567
    if d.startswith("07"):
        return f"{d[:5]} {d[5:]}"                     # 07700 900123
    if d[2] == "1" or d[3] == "1":
        return f"{d[:4]} {d[4:7]} {d[7:]}"            # 0121 234 5678
    return f"{d[:5]} {d[5:]}"                         # 01922 123456


def extract_phones(soup: BeautifulSoup, html: str) -> List[Tuple[str, int]]:
    """Returns (phone, weight). Clickable tel: links count more than plain text."""
    out: List[Tuple[str, int]] = []
    for a in soup.select('a[href^="tel:" i], a[href^="callto:" i]'):
        ph = normalise_uk_phone(a["href"].split(":", 1)[1])
        if ph:
            out.append((ph, 3))
    for script in soup(["script", "style", "noscript"]):
        script.decompose()
    for raw in PHONE_TEXT_RE.findall(soup.get_text(" ")):
        ph = normalise_uk_phone(raw)
        if ph:
            out.append((ph, 1))
    return out


def _describe_ch_error(resp: requests.Response) -> str:
    """Turns a Companies House HTTP error into a plain-English message."""
    code = resp.status_code
    if code == 401:
        return "Companies House rejected the API key (401). Check COMPANIES_HOUSE_KEY in Secrets."
    if code == 403:
        return "Companies House refused access (403). The key may not be a REST API key."
    if code == 404:
        return "No matching companies found (404)."
    if code == 416:
        return "Too many results requested. Narrow the search and try again."
    if code == 429:
        return "Companies House rate limit hit (600 requests / 5 mins). Wait a few minutes and retry."
    if code >= 500:
        return f"Companies House is having problems right now ({code}). Try again shortly."
    return f"Companies House returned an unexpected error ({code})."



# What each sector looks like on Google Maps (place types) and in business names
SECTOR_PLACE_RULES: Dict[str, Dict[str, Any]] = {
    "Estate & Lettings Agents": {
        "types": {"real_estate_agency"},
        "words": ("estate", "letting", "lettings", "lets", "property", "properties", "homes",
                  "residential", "realty", "agents", "sales"),
    },
    "Dental Practices": {
        "types": {"dentist", "dental_clinic"},
        "words": ("dental", "dentist", "dentistry", "orthodont", "smile", "teeth", "implant"),
    },
    "Solicitors & Legal Practices": {
        "types": {"lawyer"},
        "words": ("solicitor", "solicitors", "law", "legal", "lawyers", "conveyancing", "notary"),
    },
    "Accountants & Auditors": {
        "types": {"accounting"},
        "words": ("accountant", "accountants", "accounting", "accountancy", "tax", "bookkeeping",
                  "audit", "payroll", "chartered"),
    },
    "General Medical Clinics": {
        "types": {"doctor", "medical_clinic", "medical_center", "hospital", "general_hospital",
                  "physiotherapist", "health"},
        "words": ("clinic", "medical", "health", "surgery", "doctor", "gp", "physio", "practice"),
    },
}
GENERIC_PLACE_TYPES = {"point_of_interest", "establishment", "store", "service", "business"}


def sector_fit(place: Dict[str, Any], rules: Dict[str, Any]) -> Optional[bool]:
    """True = Google lists it as this sector; False = clearly a different business
    (e.g. a locksmith when we want estate agents); None = can't tell."""
    if not rules:
        return None
    types = set(place.get("types") or [])
    if place.get("primaryType"):
        types.add(place["primaryType"])
    if types & rules["types"]:
        return True
    specific = types - GENERIC_PLACE_TYPES
    if not specific:
        return None  # Google only says "business", so don't judge
    name = ((place.get("displayName") or {}).get("text") or "").lower()
    if any(w in name for w in rules["words"]):
        return None  # Name says it's in the sector even if Google's category differs
    return False


class LeadEnricher:

    def __init__(self, ch_api_key: Optional[str] = None):
        self.ch_api_key = ch_api_key.strip() if ch_api_key else None
        self.base_url = "https://api.company-information.service.gov.uk"
        self.headers = self._get_auth_headers()
        self.web_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
        }
        self.session = requests.Session()
        self.session.headers.update(self.web_headers)

    def _get_auth_headers(self) -> Dict[str, str]:
        if not self.ch_api_key:
            return {}
        token = base64.b64encode(f"{self.ch_api_key}:".encode("utf-8")).decode(
            "utf-8"
        )
        return {"Authorization": f"Basic {token}"}

    def browse_vertical(
        self,
        sic_codes: List[str],
        location_keyword: Optional[str] = None,
        company_name_includes: Optional[str] = None,
        limit: int = 25,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Returns (results, error_message). error_message is None on success."""
        if not self.ch_api_key:
            return [], "No Companies House API key configured."

        url = f"{self.base_url}/advanced-search/companies"
        params: Dict[str, Any] = {
            "sic_codes": ",".join(sic_codes),
            "company_status": "active",
            "size": limit,
        }

        if location_keyword and location_keyword.strip():
            params["location"] = location_keyword.strip()

        if company_name_includes and company_name_includes.strip():
            params["company_name_includes"] = company_name_includes.strip()

        try:
            resp = requests.get(
                url, headers=self.headers, params=params, timeout=12
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                results = []
                for item in items:
                    addr = item.get("registered_office_address", {})
                    loc_parts = [
                        addr.get("locality"),
                        addr.get("postal_code"),
                    ]
                    location_str = ", ".join([p for p in loc_parts if p])
                    results.append(
                        {
                            "Company Name": item.get("company_name", ""),
                            "Company Number": item.get("company_number", ""),
                            "Incorporated": item.get(
                                "date_of_creation", "N/A"
                            ),
                            "Town / Postcode": location_str or "UK",
                            "Status": item.get("company_status", "").title(),
                            "Companies House": (
                                "https://find-and-update.company-information.service.gov.uk/company/"
                                + item.get("company_number", "")
                            ),
                        }
                    )
                return results, None
            if resp.status_code == 404:
                # Advanced search answers 404 when nothing matches.
                return [], None
            return [], _describe_ch_error(resp)
        except requests.exceptions.Timeout:
            return [], "Companies House didn't respond in time. Please try again."
        except requests.exceptions.RequestException as exc:
            return [], f"Couldn't reach Companies House ({exc.__class__.__name__})."
        except ValueError:
            return [], "Companies House returned an unreadable response."

    def get_company_details(self, company_number: str) -> Dict[str, Any]:
        if not self.ch_api_key:
            return {}
        url = f"{self.base_url}/company/{company_number}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {}

    def get_officers(self, company_number: str) -> List[OfficerInfo]:
        if not self.ch_api_key:
            return []
        url = f"{self.base_url}/company/{company_number}/officers"
        officers = []
        self.last_officer_error = None
        try:
            # NB: don't send register_view=true. Companies House answers 400/404 for most firms,
            # which silently returned no directors. Resigned officers are filtered out below instead.
            resp = requests.get(
                url,
                headers=self.headers,
                params={"items_per_page": 100},
                timeout=10,
            )
            if resp.status_code == 429:  # Rate limited during a big batch: wait and retry once
                time.sleep(2)
                resp = requests.get(url, headers=self.headers, params={"items_per_page": 100}, timeout=10)
            if resp.status_code != 200:
                self.last_officer_error = f"Companies House officers lookup failed ({resp.status_code})"
            if resp.status_code == 200:
                for item in resp.json().get("items", []):
                    if not item.get("resigned_on"):
                        raw_role = (item.get("officer_role") or "").lower()
                        officers.append(
                            OfficerInfo(
                                name=item.get("name", "Unknown"),
                                role=format_role(raw_role),
                                raw_role=raw_role,
                                appointed_on=item.get("appointed_on"),
                            )
                        )
        except Exception as exc:
            self.last_officer_error = f"Companies House officers lookup failed ({exc.__class__.__name__})"
        return officers

    # ------------------------------------------------------------------
    # WEBSITE DISCOVERY (search results + domain guesses, verified & scored)
    # ------------------------------------------------------------------

    def _fetch_html(self, url: str, timeout: int = 7) -> Optional[Tuple[str, str]]:
        """GETs a page. Returns (final_url_after_redirects, html) or None."""
        try:
            resp = self.session.get(url, timeout=timeout, allow_redirects=True)
            ctype = resp.headers.get("Content-Type", "").lower()
            if resp.status_code == 200 and ("html" in ctype or not ctype):
                return resp.url, resp.text
        except requests.exceptions.RequestException:
            pass
        return None

    def _search_duckduckgo(self, query: str) -> Tuple[List[str], Optional[str]]:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            resp = self.session.get(url, timeout=7)
        except requests.exceptions.RequestException:
            return [], "DuckDuckGo unreachable"
        if resp.status_code != 200 or "anomaly" in resp.text.lower()[:5000]:
            return [], "DuckDuckGo blocked the request"
        soup = BeautifulSoup(resp.text, "html.parser")
        urls: List[str] = []
        for a in soup.select("a.result__a[href]"):
            href = a["href"]
            if "uddg=" in href:
                href = unquote(parse_qs(urlparse(href).query).get("uddg", [""])[0])
            if href.startswith("//"):
                href = "https:" + href
            urls.append(href)
        if not urls:  # Older markup: display URL only
            for span in soup.select(".result__url"):
                urls.append("https://" + span.get_text().strip())
        return urls, None

    def _search_bing(self, query: str) -> Tuple[List[str], Optional[str]]:
        url = f"https://www.bing.com/search?q={quote_plus(query)}&setlang=en-GB&cc=GB"
        try:
            resp = self.session.get(url, timeout=7)
        except requests.exceptions.RequestException:
            return [], "Bing unreachable"
        if resp.status_code != 200:
            return [], "Bing blocked the request"
        soup = BeautifulSoup(resp.text, "html.parser")
        urls: List[str] = []
        for a in soup.select("li.b_algo h2 a[href]"):
            href = a["href"]
            if "bing.com/ck/a" in href:  # Bing tracking wrapper: u=a1<base64url>
                u = parse_qs(urlparse(href).query).get("u", [""])[0]
                if u.startswith("a1"):
                    try:
                        b64 = u[2:] + "=" * (-len(u[2:]) % 4)
                        href = base64.urlsafe_b64decode(b64).decode("utf-8", "ignore")
                    except Exception:
                        continue
            urls.append(href)
        return urls, None

    def _score_candidate(
        self, domain: str, html: str, company_name: str,
        company_number: Optional[str], postcode: Optional[str], town: Optional[str],
    ) -> Tuple[int, List[str]]:
        """Scores how likely a site belongs to this company. Returns (score, reasons)."""
        score, reasons = 0, []
        tokens = distinctive_name_tokens(company_name)
        compact = "".join(tokens)
        label = domain_label(domain)

        # 1. Domain vs company name
        if compact and len(compact) >= 4 and (compact in label or (len(label) >= 5 and label in compact)):
            score += 45
            reasons.append("domain matches company name")
        else:
            hits = [t for t in tokens if len(t) >= 3 and t in label]
            if hits:
                score += min(15 * len(hits), 30)
                reasons.append(f"domain contains '{', '.join(hits)}'")

        soup = BeautifulSoup(html, "html.parser")
        title = (soup.title.get_text(" ", strip=True) if soup.title else "").lower()
        og = soup.find("meta", attrs={"property": "og:site_name"})
        if og and og.get("content"):
            title += " " + og["content"].lower()
        text = soup.get_text(" ", strip=True)
        text_l = text.lower()
        text_compact = re.sub(r"\s+", "", text_l)

        # 2. Page title / site name
        title_hits = [t for t in tokens if len(t) >= 3 and t in title]
        if title_hits:
            score += min(10 * len(title_hits), 20)
            reasons.append("name in page title")

        # 3. UK companies must show their registered number on their website
        if company_number:
            num = company_number.lstrip("0")
            if re.search(rf"(?<!\d)0*{re.escape(num)}(?!\d)", text_compact) and len(num) >= 5:
                score += 50
                reasons.append(f"company number {company_number} shown on site")

        # 4. Legal name / location on page
        legal = re.sub(r"\s+", " ", company_name.lower()).strip()
        if legal and legal in text_l:
            score += 20
            reasons.append("full legal name on site")
        if postcode and postcode.replace(" ", "").lower() in text_compact:
            score += 15
            reasons.append(f"registered postcode {postcode} on site")
        elif town and len(town) > 3 and town.lower() in text_l:
            score += 5
            reasons.append(f"mentions {town}")
        return score, reasons

    # ------------------------------------------------------------------
    # GOOGLE PLACES (trading name, real website & main phone number)
    # ------------------------------------------------------------------

    PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
    PLACES_FIELDS = (
        "places.displayName,places.websiteUri,places.nationalPhoneNumber,"
        "places.formattedAddress,places.businessStatus,"
        "places.types,places.primaryType,places.primaryTypeDisplayName"
    )

    def places_lookup(self, company_name: str, town: Optional[str],
                      vertical: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Finds the firm on Google Maps. Returns {name, website, phone, address} or None.
        Only runs when GOOGLE_PLACES_API_KEY is set in Secrets (1 billable lookup per firm)."""
        self.last_places_note = None
        key = _secret_value("GOOGLE_PLACES_API_KEY")
        if not key:
            return None
        clean = " ".join(w for w in re.sub(r"[^\w&' ]", " ", company_name).split()
                         if w.upper() not in LEGAL_SUFFIX_WORDS)
        body = {
            "textQuery": f"{clean} {town or ''}".strip(),
            "regionCode": "GB",
            "languageCode": "en-GB",
            "pageSize": 5,
        }
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": self.PLACES_FIELDS,
        }
        try:
            resp = requests.post(self.PLACES_URL, json=body, headers=headers, timeout=8)
        except requests.exceptions.RequestException as exc:
            self.last_places_note = f"Google Maps lookup failed ({exc.__class__.__name__})"
            return None
        if resp.status_code != 200:
            hint = {400: "check the request", 403: "API key not allowed. Enable Places API (New) and billing",
                    429: "quota reached"}.get(resp.status_code, "")
            self.last_places_note = f"Google Maps lookup failed ({resp.status_code}{': ' + hint if hint else ''})"
            return None

        tokens = distinctive_name_tokens(company_name)
        key_tokens = [t for t in tokens if len(t) >= 3] or tokens
        rules = SECTOR_PLACE_RULES.get(vertical or "", {})
        best, best_score = None, 0.0
        wrong_sector: List[str] = []
        for place in resp.json().get("places", []) or []:
            if place.get("businessStatus") == "CLOSED_PERMANENTLY":
                continue
            fit = sector_fit(place, rules)
            if fit is False:  # Google lists it as a different kind of business
                label = ((place.get("primaryTypeDisplayName") or {}).get("text")
                         or (place.get("primaryType") or "other business").replace("_", " "))
                wrong_sector.append(f"'{(place.get('displayName') or {}).get('text', '')}' ({label.lower()})")
                continue
            name = (place.get("displayName") or {}).get("text", "")
            words = re.sub(r"[^a-z0-9 ]", " ", name.lower().replace("&", " and ")).split()
            compact = "".join(words)
            hits = [t for t in key_tokens if t in words or (len(t) >= 4 and t in compact)]
            score = len(hits) / max(1, len(key_tokens))
            web_label = domain_label(domain_of(place.get("websiteUri", "")) or "")
            if web_label and any(len(t) >= 4 and t in web_label for t in key_tokens):
                score += 0.5
            if fit is True:
                score += 0.25  # Right kind of business: extra confidence
            if score > best_score:
                best, best_score = place, score
        if not best or best_score < 0.5:
            self.last_places_note = (
                "Google Maps: ignored " + ", ".join(wrong_sector[:2]) + " (wrong type of business)"
                if wrong_sector else "Google Maps: no listing confidently matched this company"
            )
            return None
        found = {
            "name": (best.get("displayName") or {}).get("text", ""),
            "website": best.get("websiteUri", ""),
            "phone": normalise_uk_phone(best.get("nationalPhoneNumber", "")) or "",
            "address": best.get("formattedAddress", ""),
        }
        self.last_places_note = f"Google Maps: matched '{found['name']}'"
        return found

    def auto_discover_website(
        self,
        company_name: str,
        location: Optional[str] = None,
        company_number: Optional[str] = None,
        postcode: Optional[str] = None,
        places_website: Optional[str] = None,
        trading_name: Optional[str] = None,
        listing_source: str = "Google Maps",
    ) -> Dict[str, Any]:
        """Finds the firm's own website. Returns url, confidence, reasons and notes."""
        places_domain = domain_of(places_website) if places_website else None
        notes: List[str] = []
        clean_name = " ".join(w for w in re.sub(r"[^\w&' ]", " ", company_name).split()
                              if w.upper() not in LEGAL_SUFFIX_WORDS)
        query = f"{clean_name} {location or ''}".strip()

        # A. Search engines (DuckDuckGo, then Bing as a fallback)
        search_urls: List[str] = []
        engines = () if places_domain else (self._search_duckduckgo, self._search_bing)  # Listed site: no need to search
        for engine in engines:
            urls, err = engine(query)
            if err:
                notes.append(err)
            search_urls.extend(urls)
            if urls:
                break

        candidates: List[str] = []
        for u in search_urls:
            d = domain_of(u)
            if d and not is_blocked_domain(d) and d not in candidates:
                candidates.append(d)
        candidates = candidates[:6]

        # B. Domain guesses (works even when search engines block us)
        guessed_only: Set[str] = set()
        for guess in guess_domains(company_name) + (guess_domains(trading_name) if trading_name else []):
            if guess not in candidates:
                candidates.append(guess)
                guessed_only.add(guess)
        # The Google Maps listing's own website goes first
        if places_domain and not is_blocked_domain(places_domain):
            candidates = [places_domain] + [c for c in candidates if c != places_domain]

        # C. Fetch & score candidates in parallel
        rejected_guesses: List[str] = []

        def check(domain: str):
            page = self._fetch_html(f"https://{domain}") or self._fetch_html(f"http://{domain}")
            if not page:
                return None
            final_url, html = page
            final_domain = domain_of(final_url) or domain
            if is_blocked_domain(final_domain):
                return None
            score, reasons = self._score_candidate(
                final_domain, html, company_name, company_number, postcode, location
            )
            if trading_name:
                t_score, t_reasons = self._score_candidate(
                    final_domain, html, trading_name, company_number, postcode, location
                )
                if t_score > score:
                    score, reasons = t_score, t_reasons
            on_listing = bool(places_domain and final_domain in (places_domain, "www." + places_domain))
            if on_listing:
                score += 35
                reasons = [f"website on the firm's {listing_source} listing"] + reasons
            elif domain in guessed_only:
                # A guessed address (e.g. elliott.com) must prove it's this firm: a matching name in the
                # web address or page title isn't enough, since big unrelated sites share common names.
                strong = ("company number", "full legal name", "registered postcode", "mentions ")
                if not any(r.startswith(strong) for r in reasons):
                    rejected_guesses.append(final_domain)
                    return None
            return final_url, final_domain, score, reasons

        results = []
        with ThreadPoolExecutor(max_workers=6) as pool:
            for res in pool.map(check, candidates):
                if res:
                    results.append(res)

        if not results:
            if places_website and places_domain and not is_blocked_domain(places_domain):
                notes.append(f"Website didn't respond to us, but it's on the firm's {listing_source} listing")
                parsed_p = urlparse(places_website if "://" in places_website else "https://" + places_website)
                return {"url": f"{parsed_p.scheme}://{parsed_p.netloc}", "confidence": "Medium",
                        "reasons": [f"website on the firm's {listing_source} listing"], "notes": notes}
            if rejected_guesses:
                notes.append("Ignored " + ", ".join(sorted(set(rejected_guesses))[:3])
                             + ": nothing on the site ties it to this company")
            else:
                notes.append("No candidate website responded")
            return {"url": None, "confidence": None, "reasons": [], "notes": notes}

        results.sort(key=lambda r: r[2], reverse=True)
        final_url, final_domain, score, reasons = results[0]
        if score < 35:
            notes.append(f"Best candidate {final_domain} scored too low to trust")
            return {"url": None, "confidence": None, "reasons": reasons, "notes": notes,
                    "rejected": final_domain}

        confidence = "High" if score >= 80 else "Medium" if score >= 55 else "Low"
        parsed = urlparse(final_url)
        return {
            "url": f"{parsed.scheme}://{parsed.netloc}",
            "confidence": confidence,
            "reasons": reasons,
            "notes": notes,
        }

    # ------------------------------------------------------------------
    # CONTACT SCRAPING (contact/about/team pages, hidden emails, clean phones)
    # ------------------------------------------------------------------

    def _find_contact_pages(self, soup: BeautifulSoup, root: str) -> List[str]:
        root_host = domain_of(root)
        ranked: List[Tuple[int, str]] = []
        for a in soup.find_all("a", href=True):
            href = urljoin(root + "/", a["href"].strip())
            if not href.startswith("http") or domain_of(href) != root_host:
                continue
            path_and_text = (urlparse(href).path + " " + a.get_text(" ", strip=True)).lower()
            for rank, hint in enumerate(CONTACT_PAGE_HINTS):
                if hint in path_and_text:
                    clean = href.split("#")[0].rstrip("/")
                    if clean != root.rstrip("/"):
                        ranked.append((rank, clean))
                    break
        seen, pages = set(), []
        for _, url in sorted(ranked):
            if url not in seen:
                seen.add(url)
                pages.append(url)
        return pages[:4]

    def scrape_contact_channels(self, base_url: str) -> Dict[str, Any]:
        empty = {"emails": [], "other_emails": [], "phones": [], "description": "",
                 "resolved_url": None, "pages_checked": []}
        if not base_url:
            return empty
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"

        home = self._fetch_html(base_url)
        if not home and base_url.startswith("https://"):
            home = self._fetch_html("http://" + base_url[len("https://"):])
        if not home:
            return {**empty, "resolved_url": base_url}

        final_url, home_html = home
        parsed = urlparse(final_url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        site_domain = domain_of(root)
        home_soup = BeautifulSoup(home_html, "html.parser")

        extra_pages = self._find_contact_pages(home_soup, root)
        if not extra_pages:
            extra_pages = [urljoin(root, p) for p in ("/contact", "/contact-us", "/about", "/about-us")]

        pages_html = [(final_url, home_html)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            for url, page in zip(extra_pages, pool.map(self._fetch_html, extra_pages)):
                if page:
                    pages_html.append((page[0], page[1]))

        email_hits: Dict[str, int] = {}
        phone_scores: Dict[str, int] = {}
        description = ""

        for _, html in pages_html:
            soup = BeautifulSoup(html, "html.parser")
            if not description:
                for attrs in ({"name": "description"}, {"property": "og:description"}):
                    tag = soup.find("meta", attrs=attrs)
                    if tag and tag.get("content"):
                        description = tag["content"].strip()
                        break
            for em in extract_emails(soup, html):
                email_hits[em] = email_hits.get(em, 0) + 1
            for ph, weight in extract_phones(soup, html):
                phone_scores[ph] = phone_scores.get(ph, 0) + weight

        own, freemail, other = [], [], []
        for em in email_hits:
            dom = em.split("@", 1)[1]
            if dom == site_domain or dom.endswith("." + site_domain) or site_domain.endswith("." + dom):
                own.append(em)
            elif dom in FREE_MAIL_DOMAINS:
                freemail.append(em)
            else:
                other.append(em)

        phones = sorted(phone_scores, key=lambda p: (-phone_scores[p], p))[:5]
        return {
            "emails": sorted(own) + sorted(freemail),
            "other_emails": sorted(other),
            "phones": phones,
            "description": description,
            "resolved_url": root,
            "pages_checked": [u for u, _ in pages_html],
        }

    def enrich_selected_company(
        self,
        company_number: str,
        sector_name: str,
        manual_website: Optional[str] = None,
    ) -> ScrapedLead:
        ch_data = self.get_company_details(company_number)
        company_name = ch_data.get("company_name", company_number)

        address_dict = ch_data.get("registered_office_address", {})
        address_parts = [
            address_dict.get(k)
            for k in [
                "premises",
                "address_line_1",
                "locality",
                "region",
                "postal_code",
            ]
            if address_dict.get(k)
        ]
        registered_address = (
            ", ".join(address_parts) if address_parts else None
        )
        town = address_dict.get("locality")
        postcode = address_dict.get("postal_code")

        officers = mark_owners(self.get_officers(company_number), psc_owner_names(self.ch_api_key, company_number))

        # Free sources first (sector register, then OpenStreetMap); Google Maps only if they leave gaps
        free, free_notes = free_intel(company_name, postcode or "", sector_name,
                                      sra_data=getattr(self, "sra_data", None))
        need_google = not (free and free.get("website") and free.get("phone"))
        places = self.places_lookup(company_name, town or postcode, sector_name) if need_google else None
        if not need_google:
            self.last_places_note = "Google Maps: not needed (free sources had the website and phone)"
        trading_name = (places["name"] if places and places.get("name") else None) or (
            free["name"] if free and free.get("name") and _sim(free["name"], company_name) < 1 else None)

        listed_site, listed_source = None, "Google Maps"
        if places and places.get("website"):
            listed_site = places["website"]
        elif free and free.get("website"):
            listed_site, listed_source = free["website"], free["source"]

        target_website = manual_website.strip() if manual_website else None
        discovery: Dict[str, Any] = {"confidence": "Manual", "reasons": ["entered by you"], "notes": []}
        if not target_website:
            discovery = self.auto_discover_website(
                company_name,
                location=town or postcode,
                company_number=company_number,
                postcode=postcode,
                places_website=listed_site,
                trading_name=trading_name,
                listing_source=listed_source,
            )
            target_website = discovery.get("url")

        site_contacts = (
            self.scrape_contact_channels(target_website)
            if target_website
            else {"emails": [], "other_emails": [], "phones": [], "description": "",
                  "resolved_url": None, "pages_checked": []}
        )
        notes = free_notes + list(discovery.get("notes", []))
        if getattr(self, "last_places_note", None):
            notes.insert(len(free_notes), self.last_places_note)
        phones = list(site_contacts["phones"])
        for listed in (free, places):  # Listed numbers are usually the main switchboard
            if listed and listed.get("phone"):
                phones = [listed["phone"]] + [p for p in phones if p != listed["phone"]]
        emails = list(site_contacts["emails"])
        if free and free.get("email") and free["email"] not in emails:
            emails.insert(0, free["email"])
        emails, dead = filter_deliverable(emails)
        if dead:
            notes.append("Dropped (domain can't receive email): " + ", ".join(dead[:3]))
        owners = [display_officer_name(o.name) for o in officers if getattr(o, "is_owner", False)]
        if owners:
            notes.append("Companies House: " + ", ".join(owners[:2]) + (" is" if len(owners) == 1 else " are")
                         + " a director and owner")
        if getattr(self, "last_officer_error", None):
            notes.append(self.last_officer_error)
        if target_website and not site_contacts.get("pages_checked"):
            notes.append("Website didn't respond when scraping contacts")

        return ScrapedLead(
            company_name=company_name,
            company_number=company_number,
            sic_codes=ch_data.get("sic_codes", []),
            sector_guess=sector_name,
            registered_address=registered_address,
            website_url=site_contacts.get("resolved_url") or target_website,
            phones_found=phones,
            emails_found=emails,
            trading_name=trading_name,
            officers=officers,
            site_meta_description=site_contacts["description"],
            website_confidence=discovery.get("confidence") if target_website else None,
            website_reasons=discovery.get("reasons", []),
            discovery_notes=notes,
            other_emails=site_contacts.get("other_emails", []),
            pages_checked=site_contacts.get("pages_checked", []),
        )


# ==========================================
# FREE INTELLIGENCE: no-cost sources tried before Google Maps
#   Companies House owners (PSC) · FCA & SRA registers · OpenStreetMap · DNS email checks
# ==========================================
FREE_HEADERS = {"User-Agent": "FortloxProspector/1.0 (+https://www.fortloxsecurity.com)"}
_FREE_CACHE: Dict[str, Any] = {}
FCA_SECTORS = {"Financial Advisers & Mortgage Brokers", "Insurance Brokers"}
SRA_SECTORS = {"Solicitors & Legal Practices"}
CQC_SECTORS = {"Care Homes & Home Care", "General Medical Clinics", "Dental Practices"}
# Where a person can double-check a firm by hand (registers without a usable free search API)
REGISTER_LINKS = {
    "Care Homes & Home Care": ("CQC register", "https://www.cqc.org.uk/search/all?query={q}"),
    "General Medical Clinics": ("CQC register", "https://www.cqc.org.uk/search/all?query={q}"),
    "Dental Practices": ("CQC register", "https://www.cqc.org.uk/search/all?query={q}"),
    "Financial Advisers & Mortgage Brokers": ("FCA register", "https://register.fca.org.uk/s/search?q={q}&type=Companies"),
    "Insurance Brokers": ("FCA register", "https://register.fca.org.uk/s/search?q={q}&type=Companies"),
    "Solicitors & Legal Practices": ("SRA register", "https://www.sra.org.uk/consumers/register/"),
    "Veterinary Practices": ("RCVS Find a Vet", "https://findavet.rcvs.org.uk/find-a-vet-practice/?filter-keyword={q}"),
}


def register_link(sector: str, company: str) -> Optional[Tuple[str, str]]:
    entry = REGISTER_LINKS.get(sector)
    if not entry:
        return None
    return entry[0], entry[1].format(q=quote_plus(friendly_company_name(company)))


def _sim(a: str, b: str) -> float:
    ta, tb = set(distinctive_name_tokens(a or "")), set(distinctive_name_tokens(b or ""))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _free_get_json(url: str, **kwargs) -> Optional[Any]:
    try:
        resp = requests.get(url, headers={**FREE_HEADERS, **kwargs.pop("headers", {})}, timeout=kwargs.pop("timeout", 10), **kwargs)
        if resp.status_code != 200:
            return None
        return resp.json()
    except (requests.exceptions.RequestException, ValueError):
        return None


def postcode_location(postcode: str) -> Optional[Tuple[float, float]]:
    """Latitude/longitude of a UK postcode (postcodes.io, free, no key)."""
    pc = (postcode or "").replace(" ", "").upper()
    if not pc:
        return None
    key = f"pc:{pc}"
    if key not in _FREE_CACHE:
        data = _free_get_json(f"https://api.postcodes.io/postcodes/{pc}")
        res = (data or {}).get("result") or {}
        _FREE_CACHE[key] = (res["latitude"], res["longitude"]) if res.get("latitude") else None
    return _FREE_CACHE[key]


def dns_has(domain: str, rtype: str) -> Optional[bool]:
    """True/False if the domain has records of this type (Google DNS-over-HTTPS, free). None if unknown."""
    key = f"dns:{domain}:{rtype}"
    if key not in _FREE_CACHE:
        data = _free_get_json("https://dns.google/resolve", params={"name": domain, "type": rtype}, timeout=6)
        if data is None:
            _FREE_CACHE[key] = None
        elif data.get("Status") == 3:  # NXDOMAIN: the domain doesn't exist
            _FREE_CACHE[key] = False
        else:
            _FREE_CACHE[key] = any(a.get("type") in (15 if rtype == "MX" else 1, 5) for a in (data.get("Answer") or []))
    return _FREE_CACHE[key]


def email_domain_ok(email: str) -> Optional[bool]:
    """Can this address receive mail? False only when DNS says the domain has no mail server at all."""
    domain = (email or "").rsplit("@", 1)[-1].lower()
    if not domain:
        return False
    mx = dns_has(domain, "MX")
    if mx is not False:
        return mx
    return dns_has(domain, "A")  # Mail can still be delivered to the domain's A record


def filter_deliverable(emails: List[str]) -> Tuple[List[str], List[str]]:
    """(kept, dropped): drops addresses whose domain can't receive email (typos, dead domains)."""
    kept, dropped = [], []
    for e in emails:
        (dropped if email_domain_ok(e) is False else kept).append(e)
    return kept, dropped


def osm_lookup(company: str, postcode: str, trading_name: str = "") -> Optional[Dict[str, Any]]:
    """The business on OpenStreetMap near its postcode (Overpass API, free, no key)."""
    loc = postcode_location(postcode)
    tokens = [t for t in distinctive_name_tokens(trading_name or company) if len(t) >= 4] or \
             distinctive_name_tokens(trading_name or company)
    if not loc or not tokens:
        return None
    token = re.escape(max(tokens, key=len))
    query = (f'[out:json][timeout:12];nwr(around:3000,{loc[0]},{loc[1]})["name"~"{token}",i];out tags 20;')
    key = f"osm:{query}"
    if key not in _FREE_CACHE:
        try:
            resp = requests.post("https://overpass-api.de/api/interpreter", data={"data": query},
                                 headers=FREE_HEADERS, timeout=15)
            _FREE_CACHE[key] = resp.json().get("elements", []) if resp.status_code == 200 else None
        except (requests.exceptions.RequestException, ValueError):
            _FREE_CACHE[key] = None
    elements = _FREE_CACHE[key]
    if not elements:
        return None
    best, best_score = None, 0.0
    for el in elements:
        tags = el.get("tags") or {}
        score = max(_sim(company, tags.get("name", "")), _sim(trading_name, tags.get("name", "")) if trading_name else 0)
        if score > best_score:
            best, best_score = tags, score
    if not best or best_score < 0.5:
        return None
    site = best.get("website") or best.get("contact:website") or best.get("url") or ""
    phone = best.get("phone") or best.get("contact:phone") or ""
    email = best.get("email") or best.get("contact:email") or ""
    if not (site or phone or email):
        return None
    return {"name": best.get("name", ""), "website": site, "phone": normalise_uk_phone(phone.split(";")[0]) or "",
            "email": clean_email(email.split(";")[0]) if email else None, "source": "OpenStreetMap"}


def _pick(d: Dict[str, Any], *words: str) -> str:
    """First non-empty value whose key contains any of the words (register APIs vary their field names)."""
    for k, v in (d or {}).items():
        if any(w in k.lower() for w in words) and isinstance(v, (str, int)) and str(v).strip():
            return str(v).strip()
    return ""


def fca_lookup(company: str, postcode: str) -> Optional[Dict[str, Any]]:
    """FCA Financial Services Register (free key: FCA_API_EMAIL + FCA_API_KEY in Secrets)."""
    email, key = _secret_value("FCA_API_EMAIL"), _secret_value("FCA_API_KEY")
    if not (email and key):
        return None
    hdr = {"X-Auth-Email": email, "X-Auth-Key": key, "Content-Type": "application/json"}
    base = "https://register.fca.org.uk/services/V0.1"
    data = _free_get_json(f"{base}/Search", params={"q": friendly_company_name(company), "type": "firm"}, headers=hdr)
    rows = (data or {}).get("Data") or []
    ranked = sorted(
        [r for r in rows if "authorised" in _pick(r, "status").lower() or not _pick(r, "status")],
        key=lambda r: -_sim(company, _pick(r, "name")))
    for r in ranked[:3]:
        if _sim(company, _pick(r, "name")) < 0.6:
            break
        frn = _pick(r, "reference number", "frn")
        addr = _free_get_json(f"{base}/Firm/{frn}/Address", headers=hdr) if frn else None
        offices = (addr or {}).get("Data") or []
        pc = (postcode or "").replace(" ", "").upper()
        office = next((o for o in offices if pc and _pick(o, "postcode").replace(" ", "").upper() == pc), None) \
            or (offices[0] if offices else {})
        site, phone = _pick(office, "website"), _pick(office, "phone")
        if site or phone:
            return {"name": _pick(r, "name"), "website": site, "phone": normalise_uk_phone(phone) or phone,
                    "email": None, "source": f"FCA register (FRN {frn})"}
    return None


@st.cache_resource(ttl=86400, show_spinner="Downloading the SRA register (once a day)…")
def sra_register() -> List[Dict[str, Any]]:
    """Every SRA-regulated firm with its offices (free key: SRA_API_KEY in Secrets). Cached for a day."""
    key = _secret_value("SRA_API_KEY")
    if not key:
        return []
    try:
        resp = requests.get("https://sra-prod-apim.azure-api.net/datashare/api/V1/organisation/GetAll",
                            headers={"Ocp-Apim-Subscription-Key": key, **FREE_HEADERS}, timeout=90)
        body = resp.json() if resp.status_code == 200 else {}
    except (requests.exceptions.RequestException, ValueError):
        body = {}
    orgs = body.get("Organisations") or body.get("organisations") or (body if isinstance(body, list) else [])
    return [o for o in orgs if isinstance(o, dict)]


def sra_lookup(company: str, postcode: str, register: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not register:
        return None
    pc = (postcode or "").replace(" ", "").upper()
    best, best_score, best_office = None, 0.0, {}
    for org in register:
        name = _pick(org, "practicename", "name")
        score = _sim(company, name)
        if score < 0.6:
            continue
        offices = org.get("Offices") or org.get("offices") or []
        office = next((o for o in offices if pc and _pick(o, "postcode").replace(" ", "").upper() == pc), None)
        if office:
            score += 0.3
        if score > best_score:
            best, best_score, best_office = org, score, office or (offices[0] if offices else {})
    if not best:
        return None
    site, phone, email = _pick(best_office, "website"), _pick(best_office, "phone"), _pick(best_office, "email")
    if not (site or phone or email):
        return None
    return {"name": _pick(best, "practicename", "name"), "website": site, "phone": normalise_uk_phone(phone) or phone,
            "email": clean_email(email) if email else None, "source": f"SRA register (SRA {_pick(best, 'sranumber')})"}


def free_intel(company: str, postcode: str, sector: str, trading_name: str = "",
               sra_data: Optional[List[Dict[str, Any]]] = None) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Tries the free sources in order: the sector's register, then OpenStreetMap. Returns (found, notes)."""
    notes: List[str] = []
    found = None
    if sector in FCA_SECTORS and _secret_value("FCA_API_KEY"):
        found = fca_lookup(company, postcode)
        notes.append(f"FCA register: matched '{found['name']}'" if found else "FCA register: no confident match")
    elif sector in SRA_SECTORS and sra_data:
        found = sra_lookup(company, postcode, sra_data)
        notes.append(f"SRA register: matched '{found['name']}'" if found else "SRA register: no confident match")
    if not found:
        found = osm_lookup(company, postcode, trading_name)
        if found:
            notes.append(f"OpenStreetMap: matched '{found['name']}'")
    if found and found.get("website") and not found["website"].startswith("http"):
        found["website"] = "https://" + found["website"]
    return found, notes


def psc_owner_names(ch_api_key: str, company_number: str) -> List[str]:
    """Active individual owners (People with Significant Control) from Companies House, as 'forename surname'."""
    if not ch_api_key or not company_number:
        return []
    try:
        resp = requests.get(
            f"https://api.company-information.service.gov.uk/company/{company_number}/persons-with-significant-control",
            auth=(ch_api_key, ""), timeout=10)
        items = resp.json().get("items", []) if resp.status_code == 200 else []
    except (requests.exceptions.RequestException, ValueError):
        return []
    out = []
    for it in items:
        if it.get("ceased_on") or "individual" not in (it.get("kind") or ""):
            continue
        ne = it.get("name_elements") or {}
        name = " ".join(x for x in [ne.get("forename"), ne.get("surname")] if x) or it.get("name", "")
        if name:
            out.append(name.lower())
    return out


def mark_owners(officers: List[Any], owners: List[str]) -> List[Any]:
    """Flags directors who are also owners, so the pitch goes to the person who signs things off."""
    if not owners:
        return officers
    for o in officers:
        disp = display_officer_name(o.name).lower().split()
        if disp and any(disp[0] in own.split() and disp[-1] in own.split() for own in owners):
            o.is_owner = True
            if "owner" not in (o.role or "").lower():
                o.role = f"{o.role} & owner"
    return officers


# ==========================================
# FREE BUSINESS FINDER: OpenStreetMap (no key) + optional Companies House (free key)
# ==========================================
# OpenStreetMap tags for each sector (what the business is listed as on the map)
OSM_SECTOR_TAGS: Dict[str, List[str]] = {
    "Estate & Lettings Agents": ['["office"="estate_agent"]', '["shop"="estate_agent"]'],
    "Dental Practices": ['["amenity"="dentist"]', '["healthcare"="dentist"]'],
    "Solicitors & Legal Practices": ['["office"="lawyer"]'],
    "Accountants & Auditors": ['["office"="accountant"]', '["office"="tax_advisor"]'],
    "General Medical Clinics": ['["amenity"="clinic"]', '["amenity"="doctors"]', '["healthcare"="physiotherapist"]'],
    "Recruitment Agencies": ['["office"="employment_agency"]'],
    "Financial Advisers & Mortgage Brokers": ['["office"="financial_advisor"]', '["office"="financial"]'],
    "Insurance Brokers": ['["office"="insurance"]'],
    "Car Dealers & Garages": ['["shop"="car"]', '["shop"="car_repair"]', '["shop"="tyres"]'],
    "Veterinary Practices": ['["amenity"="veterinary"]'],
    "Opticians": ['["shop"="optician"]', '["healthcare"="optometrist"]'],
    "Property & Block Management": ['["office"="property_management"]'],
    "Hotels & Hospitality": ['["tourism"="hotel"]', '["tourism"="guest_house"]', '["amenity"="restaurant"]', '["amenity"="pub"]'],
    "Care Homes & Home Care": ['["social_facility"="nursing_home"]', '["social_facility"="assisted_living"]', '["amenity"="nursing_home"]'],
    "Trades & Building Services": ['["craft"="plumber"]', '["craft"="electrician"]', '["craft"="hvac"]', '["trade"="plumbing"]'],
    "Contact Centres & Customer Service": ['["office"="telecommunication"]', '["office"="company"]["name"~"contact|call centre|customer",i]'],
}
UK_POSTCODE_FULL = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$", re.I)


def locate_area(place: str) -> Optional[Tuple[float, float, str]]:
    """(lat, lon, label) for a UK town or postcode. postcodes.io first, then OpenStreetMap Nominatim. Free, no key."""
    q = (place or "").strip()
    if not q:
        return None
    if UK_POSTCODE_FULL.match(q):
        data = _free_get_json(f"https://api.postcodes.io/postcodes/{q.replace(' ', '')}")
        r = (data or {}).get("result") or {}
        if r.get("latitude"):
            return r["latitude"], r["longitude"], r.get("postcode", q.upper())
    data = _free_get_json("https://api.postcodes.io/places", params={"q": q, "limit": 5})
    for r in (data or {}).get("result") or []:
        if r.get("latitude") and (r.get("name_1") or "").lower() == q.lower():
            return r["latitude"], r["longitude"], r.get("name_1", q)
    for r in (data or {}).get("result") or []:
        if r.get("latitude"):
            return r["latitude"], r["longitude"], r.get("name_1", q)
    data = _free_get_json("https://nominatim.openstreetmap.org/search",
                          params={"q": q, "countrycodes": "gb", "format": "json", "limit": 1})
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", q).split(",")[0]
    return None


# The same free OpenStreetMap data is served by several public servers. If one is busy (429)
# or times out (504), the next is tried automatically.
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


@st.cache_data(ttl=6 * 3600, show_spinner=False, max_entries=200)
def _overpass_cached(query: str) -> List[Dict[str, Any]]:
    """Successful answers are remembered for 6 hours, so repeat searches don't hit the servers at all."""
    last = ""
    for attempt in range(2):  # Two rounds through every server, with a short pause between rounds
        for url in OVERPASS_MIRRORS:
            try:
                resp = requests.post(url, data={"data": query}, headers=FREE_HEADERS, timeout=35)
            except requests.exceptions.RequestException as exc:
                last = exc.__class__.__name__
                continue
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except ValueError:
                    last = "bad reply"
                    continue
                if "runtime error" in (data.get("remark") or "").lower() and not data.get("elements"):
                    last = "server timeout"
                    continue
                return data.get("elements", [])
            last = str(resp.status_code)
        if attempt == 0:
            time.sleep(3)
    raise RuntimeError(last or "no answer")


def overpass_query(query: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    try:
        return _overpass_cached(query), None
    except RuntimeError as exc:
        return [], (f"All the free map servers are busy right now ({exc}). Wait a minute and try again,"
                    " or try a smaller 'Within km' distance.")


def osm_browse(sector: str, lat: float, lon: float, radius_km: int, keyword: str, limit: int) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Businesses of this sector within radius_km, from OpenStreetMap. Returns (rows, error)."""
    tags = OSM_SECTOR_TAGS.get(sector) or []
    if not tags:
        return [], "This sector can't be searched on the map yet."
    r = int(radius_km * 1000)
    parts = "".join(f"nwr{t}(around:{r},{lat},{lon});" for t in tags)
    query = f"[out:json][timeout:25];({parts});out center tags 400;"
    elements, err = overpass_query(query)
    if err:
        return [], err
    rows, seen = [], set()
    kw = (keyword or "").strip().lower()
    for el in elements:
        t = el.get("tags") or {}
        name = (t.get("name") or "").strip()
        if not name or (kw and kw not in name.lower()):
            continue
        pc = (t.get("addr:postcode") or "").upper()
        town = t.get("addr:city") or t.get("addr:town") or t.get("addr:village") or t.get("addr:suburb") or ""
        key = (name.lower(), pc)
        if key in seen:
            continue
        seen.add(key)
        site = t.get("website") or t.get("contact:website") or t.get("url") or ""
        phone = t.get("phone") or t.get("contact:phone") or ""
        email = t.get("email") or t.get("contact:email") or ""
        street = " ".join(x for x in [t.get("addr:housenumber"), t.get("addr:street")] if x)
        osm_id = f"OSM-{el.get('type', 'n')[0]}{el.get('id')}"
        rows.append({
            "Company Name": name,
            "Company Number": osm_id,
            "Town / Postcode": ", ".join(x for x in [town, pc] if x) or "—",
            "Has": " ".join(x for x in ["🌐" if site else "", "📞" if phone else "", "✉️" if email else ""] if x) or "—",
            "Map": f"https://www.openstreetmap.org/{el.get('type', 'node')}/{el.get('id')}",
            "_website": site, "_phone": phone.split(";")[0].strip(), "_email": email.split(";")[0].strip(),
            "_postcode": pc, "_town": town, "_address": ", ".join(x for x in [street, town, pc] if x),
        })
    # Businesses with contact details first, then A–Z
    rows.sort(key=lambda x: (x["Has"] == "—", x["Company Name"].lower()))
    return rows[:limit], None


def ch_match(ch_key: str, company: str, postcode: str) -> Optional[Dict[str, Any]]:
    """Optional: the business on Companies House (needs the free key). Active companies, close name match only."""
    if not ch_key:
        return None
    try:
        resp = requests.get("https://api.company-information.service.gov.uk/search/companies",
                            params={"q": company, "items_per_page": 10}, auth=(ch_key, ""), timeout=10)
        items = resp.json().get("items", []) if resp.status_code == 200 else []
    except (requests.exceptions.RequestException, ValueError):
        return None
    best, best_score = None, 0.0
    for it in items:
        if (it.get("company_status") or "").lower() != "active":
            continue
        score = _sim(company, it.get("title", ""))
        if postcode and postcode.replace(" ", "").lower() in (it.get("address_snippet") or "").replace(" ", "").lower():
            score += 0.3
        if score > best_score:
            best, best_score = it, score
    return best if best and best_score >= 0.75 else None


def enrich_osm_business(row: Dict[str, Any], sector: str, ch_key: str, manual_website: Optional[str] = None) -> "ScrapedLead":
    """Finds the website, emails, phones (and, with the free key, directors) for a business found on the map."""
    e = LeadEnricher(ch_api_key=ch_key)
    name, pc, town = row["Company Name"], row.get("_postcode", ""), row.get("_town", "")
    notes = ["Found on OpenStreetMap" + (f" ({row['Town / Postcode']})" if row.get("Town / Postcode") else "")]
    officers, company_number, sic = [], None, []
    ch = ch_match(ch_key, name, pc) if ch_key else None
    if ch:
        company_number = ch.get("company_number")
        officers = mark_owners(e.get_officers(company_number), psc_owner_names(ch_key, company_number))
        try:
            sic = list(e.get_company_details(company_number).get("sic_codes") or [])
        except Exception:
            sic = []
        notes.append(f"Companies House: matched {ch.get('title')} (#{company_number})")
    elif ch_key:
        notes.append("Companies House: no confident match")

    listed = (row.get("_website") or "").strip()
    if listed and not listed.startswith("http"):
        listed = "https://" + listed
    if manual_website:
        target, confidence, reasons = manual_website.strip(), "Manual", ["entered by you"]
        if not target.startswith("http"):
            target = "https://" + target
    else:
        d = e.auto_discover_website(name, location=town or pc, company_number=company_number, postcode=pc,
                                    places_website=listed or None, listing_source="OpenStreetMap")
        target, confidence, reasons = d.get("url"), d.get("confidence"), d.get("reasons", [])
        notes += d.get("notes", [])
    site = e.scrape_contact_channels(target) if target else {
        "emails": [], "other_emails": [], "phones": [], "description": "", "resolved_url": None, "pages_checked": []}
    phones = []
    for raw in [row.get("_phone")] + site["phones"]:
        ph = normalise_uk_phone(raw or "")
        if ph and ph not in phones:
            phones.append(ph)
    emails = [x for x in [clean_email(row.get("_email") or "") if row.get("_email") else None] + site["emails"] if x]
    emails, dead = filter_deliverable(list(dict.fromkeys(emails)))
    if dead:
        notes.append("Dropped (domain can't receive email): " + ", ".join(dead[:3]))
    owners = [display_officer_name(o.name) for o in officers if getattr(o, "is_owner", False)]
    if owners:
        notes.append("Companies House: " + ", ".join(owners[:2]) + " is a director and owner")
    return ScrapedLead(
        company_name=name, company_number=company_number, source_id=row["Company Number"],
        sic_codes=sic, sector_guess=sector,
        registered_address=(ch.get("address_snippet") if ch else None) or row.get("_address") or None,
        website_url=site.get("resolved_url") or target, phones_found=phones[:5], emails_found=emails,
        officers=officers, site_meta_description=site.get("description"), trading_name=None,
        website_confidence=confidence if target else None, website_reasons=reasons, discovery_notes=notes,
        other_emails=site.get("other_emails", []), pages_checked=site.get("pages_checked", []),
    )


# ==========================================
# 3. PITCH SYNTHESIZER & PDF BUILDER
# ==========================================


def sanitize_pdf_text(text: str) -> str:
    """Replaces Unicode bullets, smart quotes, and dashes with Latin-1 equivalents for FPDF."""
    if not text:
        return ""
    replacements = {
        "\u2022": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00a0": " ",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "—": "-",
        "–": "-",
        "•": "-",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", errors="replace").decode("latin-1")


# Companies House officer_role values, best decision-maker first.
# Secretaries and all "corporate-*" roles (companies, not people) are excluded.
DECISION_MAKER_ROLES = [
    "director",
    "llp-designated-member",
    "llp-member",
    "managing-officer",
    "member",
]

ROLE_LABELS = {
    "director": "Director",
    "llp-designated-member": "Designated Member (LLP)",
    "llp-member": "Member (LLP)",
    "managing-officer": "Managing Officer",
    "member": "Member",
    "secretary": "Company Secretary",
    "nominee-director": "Nominee Director",
}

NAME_TITLES = {"mr", "mrs", "ms", "miss", "dr", "sir", "dame", "prof", "professor", "lord", "lady", "rev"}


def format_role(raw_role: str) -> str:
    raw_role = (raw_role or "").strip().lower()
    return ROLE_LABELS.get(raw_role, raw_role.replace("-", " ").title() or "Officer")


def first_name_from_officer(raw_name: str) -> Optional[str]:
    """Companies House lists people as 'SURNAME, Forename Middle'.
    Returns the forename, e.g. 'BYWATER, Paul James' -> 'Paul'."""
    if not raw_name:
        return None
    if "," in raw_name:
        forenames = raw_name.split(",", 1)[1]
    else:
        forenames = raw_name  # Rare 'Paul BYWATER' style: first word is the forename
    for token in forenames.replace(".", " ").split():
        clean = re.sub(r"[^A-Za-z'\-]", "", token)
        if clean and clean.lower() not in NAME_TITLES and len(clean) > 1:
            return "-".join(p[:1].upper() + p[1:].lower() for p in clean.split("-"))
    return None


def pick_decision_maker(officers: List["OfficerInfo"]) -> Optional["OfficerInfo"]:
    """Chooses the most senior active person (directors first, longest-serving first)."""
    for wanted in DECISION_MAKER_ROLES:
        matches = [o for o in officers if o.raw_role == wanted]
        if matches:
            return sorted(matches, key=lambda o: (not getattr(o, "is_owner", False), o.appointed_on or "9999"))[0]
    return None


GENERIC_EMAIL_PREFIXES = {
    "info", "information", "enquiries", "enquiry", "enq", "sales", "lettings", "letting",
    "rentals", "lets", "office", "admin", "administration", "contact", "contactus",
    "mail", "post", "reception", "frontdesk", "support", "help", "hello", "hi", "team",
    "accounts", "account", "finance", "billing", "invoices", "payments", "bookings",
    "booking", "appointments", "appts", "careers", "jobs", "recruitment", "hr",
    "marketing", "newsletter", "news", "press", "media", "privacy", "dpo", "data",
    "gdpr", "complaints", "feedback", "service", "services", "customerservice",
    "customerservices", "general", "manager", "management", "partners", "property",
    "properties", "valuations", "valuation", "maintenance", "repairs", "lettingsteam",
    "salesteam", "dental", "dentist", "surgery", "practice", "practicemanager",
    "clinic", "patients", "patient", "law", "legal", "conveyancing", "probate",
    "family", "tax", "payroll", "bookkeeping", "audit", "web", "webmaster", "website",
    "it", "tech", "office1", "branch", "new", "newbusiness", "referrals", "clients",
}


def first_name_from_email(email: str) -> Optional[str]:
    """'david.mann@x.co.uk' -> 'David'. Returns None for inboxes like info@ or accounts@."""
    prefix = email.split("@", 1)[0].lower()
    compact = re.sub(r"[^a-z]", "", prefix)
    if not compact or compact in GENERIC_EMAIL_PREFIXES:
        return None
    first = re.split(r"[._\-]", prefix)[0]
    first = re.sub(r"[^a-z]", "", first)
    # Must look like a first name: letters only, 3-12 chars, not a generic word
    if 3 <= len(first) <= 12 and first not in GENERIC_EMAIL_PREFIXES and first.isalpha():
        # 'dmann' style (initial + surname) can't be trusted as a first name
        has_separator = any(sep in prefix for sep in "._-")
        if not has_separator:
            if len(first) > 8:
                return None
            # Two leading consonants that rarely start a first name = initial + surname ('dmann', 'pbywater')
            vowels = set("aeiouy")
            ok_clusters = {"br", "ch", "cl", "cr", "dr", "fl", "fr", "gl", "gr", "kr",
                           "ph", "pr", "sc", "sh", "st", "th", "tr", "bl", "chr", "sk"}
            if first[0] not in vowels and first[1] not in vowels and first[:2] not in ok_clusters:
                return None
        return first.capitalize()
    return None


def pick_primary_email(lead: "ScrapedLead", first_name: Optional[str] = None) -> Optional[str]:
    """The best single email for the dossier: the contact's own inbox, else the main inbox."""
    if getattr(lead, "contact_email", None):
        return lead.contact_email
    if not lead.emails_found:
        return None
    if first_name:
        for em in lead.emails_found:
            if em.split("@", 1)[0].lower().startswith(first_name.lower()):
                return em
    for preferred in ("info", "enquiries", "hello", "contact", "office", "reception"):
        for em in lead.emails_found:
            if em.split("@", 1)[0].lower() == preferred:
                return em
    return lead.emails_found[0]


def infer_contact_name_and_role(
    lead: ScrapedLead, vertical_key: str
) -> Tuple[str, str]:
    """Smart contact resolver: extracts personal names from officers or email prefixes."""
    vert_cfg = VERTICAL_PRESETS.get(
        vertical_key, VERTICAL_PRESETS["Estate & Lettings Agents"]
    )

    # 0. A contact a person has confirmed (e.g. via LinkedIn) always wins
    manual = (getattr(lead, "contact_name", None) or "").strip()
    if manual:
        first = re.sub(r"[^A-Za-z'\-]", "", manual.split()[0]) if manual.split() else ""
        if first:
            return first[:1].upper() + first[1:], (getattr(lead, "contact_role", None) or "Confirmed contact")

    # 1. Primary Officer match — only real people in decision-making roles
    officer = pick_decision_maker(lead.officers)
    if officer:
        first_name = first_name_from_officer(officer.name)
        if first_name:
            return first_name, officer.role

    # 2. Email Prefix Extraction (e.g. sarah@firm.co.uk or david.mann@firm.co.uk -> Sarah / David)
    for em in lead.emails_found:
        name_candidate = first_name_from_email(em)
        if name_candidate:
            return name_candidate, f"Direct Contact ({em})"

    # 3. Fallback to vertical-specific role
    return vert_cfg["fallback_greeting"], "Team / Branch Management"


# ------------------------------------------------------------------
# SY Communications brand & sector copy (email + overview PDF)
# ------------------------------------------------------------------

SENDER_COMPANY = "Fortlox Security"
# Fortlox logo built into the app, so the PDFs always have it (even if logo.png goes missing)
_LOGO_JPG_B64 = (
    "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"
    "uNym4mhosF//2Q=="
)


def logo_image() -> io.BytesIO:
    """logo.png next to app.py if present, otherwise the built-in copy."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    try:
        with open(path, "rb") as fh:
            return io.BytesIO(fh.read())
    except OSError:
        return io.BytesIO(base64.b64decode(_LOGO_JPG_B64))
SENDER_DEFAULTS = {
    "name": "Ky Thomas",
    "title": "Managing Director",
    "phone": "01453 702502",
    "email": "sales@fortloxsecurity.com",
    "website": "www.fortloxsecurity.com",
    "address": "2 Taits Hill Barn, Taits Hill, Stinchcombe GL11 6BN",
}
BRAND_PURPLE = (16, 42, 67)       # #102A43 navy
BRAND_PURPLE_2 = (27, 64, 98)    # #2d1f6e
BRAND_TEAL = (30, 154, 214)       # #1E9AD6 Fortlox cyan
SWITCHOVER_LINE = (
    "With BT's analogue phone network switching off by January 2027, it's a good moment to"
    " move to a system that actually works with your software."
)

# Per-sector copy. Keys match VERTICAL_PRESETS.
SECTOR_COPY: Dict[str, Dict[str, Any]] = {
    "Estate & Lettings Agents": {
        "sector_plural": "estate and lettings agents",
        "subject": "Stop missing applicant calls at {company}",
        "pain": "Most agencies still ask who's calling, then search {crms} while the caller waits. And calls missed during viewings often go to the agent down the road.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which system you use and how many staff take calls, and I'll send an indicative quote.",
        "challenges": [
            ("Calls missed during viewings", "Applicants who can't get through rarely leave a message; they ring the next agent."),
            ("No caller context", "Staff answer blind, then search the CRM while the landlord or tenant waits."),
            ("No record of what was agreed", "Call notes live in people's heads, not on the property or tenancy file."),
        ],
        "outcomes": [
            ("Screen-pop on every call", "The landlord, vendor or applicant record opens the moment the phone rings."),
            ("Click-to-dial from your CRM", "Call straight from the property, applicant or tenancy record. No retyping numbers."),
            ("Calls logged automatically", "Every call, duration and recording saved against the right record for compliance and disputes."),
            ("Missed-call recovery", "Missed calls are flagged instantly with the caller's record, so no lead goes cold."),
        ],
    },
    "Dental Practices": {
        "sector_plural": "dental practices",
        "subject": "Fewer missed patient calls at {company}",
        "pain": "Reception gets swamped at 8.30am, patients who can't get through don't always call back, and staff search {crms} on every call.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which system you use and how many handsets you have, and I'll send a no-obligation quote.",
        "challenges": [
            ("Morning call peaks", "Reception is overwhelmed at opening and patients give up or go elsewhere."),
            ("Lost recalls and bookings", "Missed calls mean missed appointments and gaps in the diary."),
            ("Searching while the patient waits", "Staff look up records manually on every call."),
        ],
        "outcomes": [
            ("Patient screen-pop", "The patient's record appears on the reception screen as the phone rings."),
            ("Call queueing & callbacks", "Smart queues and messages manage the morning rush without losing callers."),
            ("Missed-call follow-up", "Every missed call is flagged so reception can ring back and protect recalls."),
            ("Compliant call recording", "Recordings stored securely and linked to the patient record."),
        ],
    },
    "Solicitors & Legal Practices": {
        "sector_plural": "law firms",
        "subject": "Calls logged straight to the matter at {company}",
        "pain": "Fee earners are rarely at their desk, clients expect to reach the right person first time, and phone time often never reaches the matter in {crms}.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which system you run and roughly how many users, and I'll send an indicative quote.",
        "challenges": [
            ("Fee earners away from the desk", "Calls bounce around the office or go to voicemail."),
            ("Unrecorded billable time", "Phone time isn't captured against the matter, so it's never billed."),
            ("Multiple offices, multiple systems", "Branches that can't transfer calls between each other easily."),
        ],
        "outcomes": [
            ("Dial from the matter", "Click-to-call from the client or matter record in your case management system."),
            ("Softphone anywhere", "Fee earners take calls on laptop or mobile securely, on the firm's number."),
            ("Duration & recordings on file", "Call time and recordings logged against the matter for billing and compliance."),
            ("One system, every office", "Reception, fee earners and branches on one platform with simple transfers."),
        ],
    },
    "Accountants & Auditors": {
        "sector_plural": "accountancy practices",
        "subject": "Client calls logged automatically at {company}",
        "pain": "Around deadlines the phones don't stop, clients expect you to know who they are, and call time rarely gets captured in {crms}.",
        "cta": "Worth a quick 15-minute demo? Or just reply with your team size and practice software, and I'll send an indicative quote.",
        "challenges": [
            ("Deadline call surges", "January and year-end bring call spikes the team can't keep up with."),
            ("Unbilled advice time", "Quick calls add up but rarely make it onto a timesheet."),
            ("Hybrid teams", "Staff split between home and office struggle to transfer calls smoothly."),
        ],
        "outcomes": [
            ("Client identified on arrival", "The client's details pop up before you say hello."),
            ("Automatic call logging", "Calls logged against the client record, with duration for time tracking."),
            ("Desk to laptop in one tap", "Seamless transfers between desk phones and softphones for hybrid staff."),
            ("Lower fixed costs", "Line rental and call costs consolidated onto one cloud platform."),
        ],
    },
    "General Medical Clinics": {
        "sector_plural": "clinics",
        "subject": "Shorter phone queues for patients at {company}",
        "pain": "Peak-hour queues put pressure on the front desk, and staff often have to search {crms} before they can help.",
        "cta": "Worth a quick 15-minute demo? Or just reply with how many lines or handsets you run, and I'll send a no-obligation overview.",
        "challenges": [
            ("Peak-hour queues", "The phones spike at opening and patients abandon the call."),
            ("Triage without context", "Staff answer without the patient's details in front of them."),
            ("Sensitive conversations", "Calls need to be recorded and stored securely."),
        ],
        "outcomes": [
            ("Patient screen-pop", "The patient's record appears as the call arrives to speed up triage."),
            ("Queueing & callbacks", "Patients hear their queue position or get a callback instead of an engaged tone."),
            ("Secure call recording", "Encrypted recordings stored against the patient record."),
            ("Easy internal transfers", "Direct routes between reception, clinicians and admin."),
        ],
    },
}

# ---- Extra sectors (added Oct 2026) ----
NEW_PRESETS = {
    "Recruitment Agencies": {
        "sic_codes": ["78100", "78200", "78300"],
        "description": "Employment placement & temporary staffing agencies",
        "search_hint": "Recruitment",
        "crms": ["Bullhorn", "Vincere", "Firefish", "Mercury"],
        "primary_hook": "ATS / CRM Integration (Bullhorn / Vincere / Firefish)",
        "fallback_greeting": "Recruitment Team",
        "pitch_bullets": [
            "Candidate and client records pop up the moment they call",
            "Click-to-dial from your ATS, with every call logged automatically",
            "Call recording for compliance, coaching and disputes",
            "Call stats per consultant, ready for your KPI boards",
        ],
        "default_cta": "Let me know which ATS you use and how many consultants you have, and I'll send an indicative quote.",
    },
    "Financial Advisers & Mortgage Brokers": {
        "sic_codes": ["66190"],
        "description": "Financial advice, mortgage & wealth management activities",
        "search_hint": "Financial",
        "crms": ["Intelliflo", "Iress Xplan", "Mortgage Brain", "Salesforce"],
        "primary_hook": "Back-office Integration (Intelliflo / Xplan) & FCA-ready recording",
        "fallback_greeting": "Advice Team",
        "pitch_bullets": [
            "Secure call recording to support FCA record-keeping",
            "Client record screen-pop from your back-office system",
            "Click-to-dial and automatic call logging against the client file",
            "Calls routed to the right adviser, wherever they're working",
        ],
        "default_cta": "Let me know which back-office system you use and how many advisers you have, and I'll send an indicative quote.",
    },
    "Insurance Brokers": {
        "sic_codes": ["66220"],
        "description": "Activities of insurance agents & brokers",
        "search_hint": "Insurance",
        "crms": ["Acturis", "Applied Epic", "OpenGI", "SSP"],
        "primary_hook": "Broking Platform Integration (Acturis / Applied Epic / OpenGI)",
        "fallback_greeting": "Broking Team",
        "pitch_bullets": [
            "Policyholder record pops up before you answer",
            "Recorded calls stored for compliance and claims disputes",
            "Renewal and claims calls queued to the right team",
            "Missed calls flagged so renewals don't slip away",
        ],
        "default_cta": "Let me know which broking platform you use and roughly how many staff take calls, and I'll send a quote.",
    },
    "Car Dealers & Garages": {
        "sic_codes": ["45111", "45112", "45200"],
        "description": "Motor vehicle sales, servicing & repair",
        "search_hint": "Motors",
        "crms": ["Keyloop", "Pinewood", "MAM Autowork", "GarageHive"],
        "primary_hook": "DMS Integration (Keyloop / Pinewood / MAM)",
        "fallback_greeting": "Sales & Service Team",
        "pitch_bullets": [
            "Customer and vehicle record on screen as the phone rings",
            "Sales, service and parts calls routed to the right desk",
            "Missed-call alerts so no sales enquiry goes cold",
            "Call recording to settle disputes and coach the team",
        ],
        "default_cta": "Let me know which DMS you use and how many handsets you run, and I'll send an indicative quote.",
    },
    "Veterinary Practices": {
        "sic_codes": ["75000"],
        "description": "Veterinary activities",
        "search_hint": "Vets",
        "crms": ["RxWorks", "Provet Cloud", "Robovet", "VetIT"],
        "primary_hook": "Practice System Integration (RxWorks / Provet / Robovet)",
        "fallback_greeting": "Practice Team",
        "pitch_bullets": [
            "Client and pet record pops up the moment they call",
            "Smart queues for the morning rush and emergency calls",
            "Out-of-hours routing to your on-call vet or partner service",
            "Missed calls flagged so every booking is followed up",
        ],
        "default_cta": "Let me know which practice system you use and how many handsets you have, and I'll send a no-obligation quote.",
    },
    "Opticians": {
        "sic_codes": ["47782"],
        "description": "Retail sale by opticians",
        "search_hint": "Opticians",
        "crms": ["Optix", "Ocuco Acuitas", "Opticabase", "Optisoft"],
        "primary_hook": "Practice System Integration (Optix / Acuitas / Opticabase)",
        "fallback_greeting": "Practice Team",
        "pitch_bullets": [
            "Patient record on screen before you answer",
            "Recall and appointment calls queued, not lost",
            "Missed calls flagged so bookings are always returned",
            "One number across branches, routed to whoever's free",
        ],
        "default_cta": "Let me know which practice system you use and how many branches you have, and I'll send an indicative quote.",
    },
    "Property & Block Management": {
        "sic_codes": ["68320"],
        "description": "Management of real estate on a fee or contract basis",
        "search_hint": "Property Management",
        "crms": ["Qube", "Fixflo", "PropertyFile", "Arthur Online"],
        "primary_hook": "Property System Integration (Qube / Fixflo / Arthur)",
        "fallback_greeting": "Property Management Team",
        "pitch_bullets": [
            "Resident, landlord or block record pops up on every call",
            "Out-of-hours and emergency repair calls routed correctly",
            "Every call logged against the property for an audit trail",
            "Peak-time queues so residents aren't left on hold",
        ],
        "default_cta": "Let me know which system you manage your portfolio in and how many staff take calls, and I'll send a quote.",
    },
    "Hotels & Hospitality": {
        "sic_codes": ["55100", "56101", "56302"],
        "description": "Hotels, restaurants, pubs & bars",
        "search_hint": "Hotel",
        "crms": ["Guestline", "Mews", "ResDiary", "OpenTable"],
        "primary_hook": "Booking System Integration (Guestline / Mews / ResDiary)",
        "fallback_greeting": "Reservations Team",
        "pitch_bullets": [
            "Guest booking details on screen as the phone rings",
            "Reservation calls answered even when the team is busy",
            "Room-to-reception and kitchen extensions that just work",
            "Missed booking calls flagged so revenue isn't lost",
        ],
        "default_cta": "Let me know which booking system you use and how many handsets you need, and I'll send an indicative quote.",
    },
    "Care Homes & Home Care": {
        "sic_codes": ["87100", "87300", "88100"],
        "description": "Residential care, nursing homes & domiciliary care",
        "search_hint": "Care",
        "crms": ["Person Centred Software", "Birdie", "CareDocs", "Access Care Planning"],
        "primary_hook": "Care System Integration & Reliable Family Contact",
        "fallback_greeting": "Care Team",
        "pitch_bullets": [
            "Families reach the right person first time, day or night",
            "Calls routed to carers' mobiles when they're on the floor",
            "Recorded calls for safeguarding and complaints",
            "Reliable lines ahead of the January 2027 analogue switch-off",
        ],
        "default_cta": "Let me know how many sites and handsets you run, and I'll send a no-obligation quote.",
    },
    "Trades & Building Services": {
        "sic_codes": ["43220", "43210"],
        "description": "Plumbing, heating & electrical installation",
        "search_hint": "Heating",
        "crms": ["simPRO", "Commusoft", "Joblogic", "ServiceM8"],
        "primary_hook": "Job Management Integration (simPRO / Commusoft / Joblogic)",
        "fallback_greeting": "Office Team",
        "pitch_bullets": [
            "Customer and job history on screen as they call",
            "Calls follow engineers to their mobiles on site",
            "Every missed call flagged, because a missed call is a missed job",
            "Call recording to settle quote and booking disputes",
        ],
        "default_cta": "Let me know which job management system you use and how many engineers and office staff you have, and I'll send a quote.",
    },
    "Contact Centres & Customer Service": {
        "sic_codes": ["82200"],
        "description": "Activities of call centres",
        "search_hint": "Contact Centre",
        "crms": ["Salesforce", "Zendesk", "Freshdesk", "HubSpot"],
        "primary_hook": "Contact Centre Platform (queues, wallboards, CRM integration)",
        "fallback_greeting": "Operations Team",
        "pitch_bullets": [
            "Live wallboards and real-time queue stats",
            "Skills-based routing to the right agent first time",
            "Call recording and quality scoring with Call Scope",
            "Screen-pop and logging into Salesforce, Zendesk or HubSpot",
        ],
        "default_cta": "Let me know how many agents you run and which CRM you use, and I'll send an indicative quote.",
    },
}

NEW_COPY = {
    "Recruitment Agencies": {
        "sector_plural": "recruitment agencies",
        "subject": "Every candidate call logged in your ATS, {company}",
        "pain": "Consultants live on the phone, but calls rarely make it into {crms}, and a missed call from a candidate or client often goes to a competitor.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which ATS you use and how many consultants you have, and I'll send an indicative quote.",
        "challenges": [
            ("Calls missing from the ATS", "Consultants forget to log calls, so the record is never complete."),
            ("Missed candidate calls", "Candidates who can't get through accept the next agency's offer."),
            ("No view of activity", "Managers can't see call volumes per consultant without chasing spreadsheets."),
        ],
        "outcomes": [
            ("Screen-pop from your ATS", "The candidate or client record opens the moment the phone rings."),
            ("Automatic call logging", "Every call, duration and recording saved against the right record."),
            ("Consultant call stats", "Live call activity per consultant for KPIs and coaching."),
            ("Missed-call recovery", "Missed calls flagged instantly so no placement slips away."),
        ],
    },
    "Financial Advisers & Mortgage Brokers": {
        "sector_plural": "financial advisers and mortgage brokers",
        "subject": "FCA-ready call recording for {company}",
        "pain": "Advisers move between the office, home and client meetings, calls need to be recorded for compliance, and client notes still end up typed into {crms} by hand.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which back-office system you use and how many advisers you have, and I'll send an indicative quote.",
        "challenges": [
            ("Recording obligations", "Calls need to be recorded and easy to find when compliance asks."),
            ("Advisers on the move", "Clients struggle to reach the right adviser away from the office."),
            ("Manual file notes", "Call details are retyped into the back-office system after the fact."),
        ],
        "outcomes": [
            ("Secure call recording", "Every call recorded, stored securely and easy to retrieve."),
            ("Client screen-pop", "The client file opens from your back-office system as the phone rings."),
            ("Calls on any device", "Advisers take calls on the business number from desk, laptop or mobile."),
            ("Automatic call logging", "Calls saved against the client record, ready for reviews."),
        ],
    },
    "Insurance Brokers": {
        "sector_plural": "insurance brokers",
        "subject": "Faster renewals and claims calls at {company}",
        "pain": "Renewal season brings call peaks, claims callers are often stressed, and staff still search {crms} while the client waits.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which broking platform you use and how many staff take calls, and I'll send a quote.",
        "challenges": [
            ("Renewal peaks", "Clients who can't get through at renewal time shop around."),
            ("Searching while clients wait", "Staff look up policies manually on every call."),
            ("Evidence for disputes", "Without recordings, it's your word against theirs."),
        ],
        "outcomes": [
            ("Policyholder screen-pop", "The client and policy record opens as the phone rings."),
            ("Renewal & claims routing", "Calls go straight to the right team, with queues for busy times."),
            ("Compliant call recording", "Recordings stored securely and linked to the client."),
            ("Missed-call follow-up", "Every missed call is flagged so renewals aren't lost."),
        ],
    },
    "Car Dealers & Garages": {
        "sector_plural": "car dealers and garages",
        "subject": "No more missed sales calls at {company}",
        "pain": "Sales, service and parts calls all land on the same lines, enquiries get missed when the team is with customers, and nobody can see the caller's history in {crms}.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which DMS you use and how many handsets you run, and I'll send an indicative quote.",
        "challenges": [
            ("Missed sales enquiries", "A buyer who can't get through rings the next dealer on the list."),
            ("Calls to the wrong desk", "Service and parts calls bounce around before reaching the right person."),
            ("No caller history", "Staff can't see the customer's vehicle or last visit when they answer."),
        ],
        "outcomes": [
            ("Customer & vehicle screen-pop", "Their record from your DMS appears as the phone rings."),
            ("Department routing", "Sales, service and parts calls reach the right team first time."),
            ("Missed-call alerts", "Every missed enquiry is flagged for a quick call back."),
            ("Call recording", "Settle disputes and coach the team with recorded calls."),
        ],
    },
    "Veterinary Practices": {
        "sector_plural": "veterinary practices",
        "subject": "Fewer missed client calls at {company}",
        "pain": "Mornings are a scramble, urgent calls need to reach a vet fast, and reception searches {crms} on every call.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which practice system you use and how many handsets you have, and I'll send a no-obligation quote.",
        "challenges": [
            ("Morning call peaks", "Clients wait on hold or give up while reception is busy."),
            ("Urgent calls", "Emergencies need to reach the right person immediately."),
            ("Searching while the client waits", "Staff look up client and pet records on every call."),
        ],
        "outcomes": [
            ("Client & pet screen-pop", "The record appears on screen as the phone rings."),
            ("Smart queues & priority routing", "Urgent calls jump the queue and reach a vet quickly."),
            ("Out-of-hours routing", "Calls go to your on-call vet or partner service automatically."),
            ("Missed-call follow-up", "Every missed call is flagged so bookings are returned."),
        ],
    },
    "Opticians": {
        "sector_plural": "opticians",
        "subject": "Every recall call answered at {company}",
        "pain": "Recall and appointment calls come in while staff are with patients, missed calls rarely leave a message, and records sit in {crms} rather than on screen.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which practice system you use and how many branches you have, and I'll send an indicative quote.",
        "challenges": [
            ("Calls while staff are with patients", "The phone rings out during testing and dispensing."),
            ("Lost recall bookings", "Patients who can't get through put their eye test off."),
            ("Multi-branch juggling", "Calls don't reach the branch or colleague who's free."),
        ],
        "outcomes": [
            ("Patient screen-pop", "The patient record appears as the phone rings."),
            ("Call queueing", "Callers hold briefly instead of ringing out."),
            ("Missed-call follow-up", "Every missed call is flagged so bookings are returned."),
            ("One number, every branch", "Calls routed to whichever branch or colleague is free."),
        ],
    },
    "Property & Block Management": {
        "sector_plural": "property and block managers",
        "subject": "Every resident call logged at {company}",
        "pain": "Residents call about repairs at all hours, landlords expect quick answers, and call details rarely reach {crms}.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which system you manage your portfolio in and how many staff take calls, and I'll send a quote.",
        "challenges": [
            ("Out-of-hours emergencies", "Urgent repair calls need to reach someone, whatever the time."),
            ("No audit trail", "Disputes are hard to settle without a record of who said what."),
            ("Answering blind", "Staff search for the block or resident while the caller waits."),
        ],
        "outcomes": [
            ("Resident & property screen-pop", "The block, unit or landlord record appears as the phone rings."),
            ("Emergency routing", "Out-of-hours calls go straight to the on-call team."),
            ("Calls logged to the property", "Every call and recording saved for a clear audit trail."),
            ("Queues for busy periods", "Residents hold briefly instead of ringing out."),
        ],
    },
    "Hotels & Hospitality": {
        "sector_plural": "hotels and hospitality businesses",
        "subject": "Never miss a booking call at {company}",
        "pain": "Reservation calls come in while the team is busy with guests, missed calls are lost bookings, and guest details sit in {crms} rather than on screen.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which booking system you use and how many handsets you need, and I'll send an indicative quote.",
        "challenges": [
            ("Missed reservation calls", "Guests who can't get through book somewhere else."),
            ("Busy front desk", "Reception juggles guests in person and on the phone."),
            ("Outdated room phones", "Old internal systems are costly and unreliable."),
        ],
        "outcomes": [
            ("Guest screen-pop", "Booking details appear as the phone rings."),
            ("Overflow & queueing", "Busy calls overflow to another team instead of ringing out."),
            ("Modern extensions", "Reception, rooms, kitchen and office on one simple system."),
            ("Missed-call alerts", "Every missed booking call is flagged for a call back."),
        ],
    },
    "Care Homes & Home Care": {
        "sector_plural": "care providers",
        "subject": "Families reach the right carer at {company}",
        "pain": "Families want reassurance, carers are rarely near a desk phone, and many homes still rely on lines affected by the analogue switch-off.",
        "cta": "Worth a quick 15-minute demo? Or just reply with how many sites and handsets you run, and I'll send a no-obligation quote.",
        "challenges": [
            ("Calls ringing out", "Carers are with residents, so the phone goes unanswered."),
            ("Night and weekend cover", "Calls need to reach whoever is on shift."),
            ("Analogue lines", "Alarms and lines need to be ready for the January 2027 switch-off."),
        ],
        "outcomes": [
            ("Calls on carers' mobiles", "The care line rings on mobiles or cordless handsets around the home."),
            ("Shift-based routing", "Calls follow your rota, day and night."),
            ("Call recording", "Recordings support safeguarding and complaint handling."),
            ("Future-proof lines", "Digital phones ready for the analogue switch-off."),
        ],
    },
    "Trades & Building Services": {
        "sector_plural": "trade and building services firms",
        "subject": "A missed call is a missed job, {company}",
        "pain": "Engineers are on site, the office is stretched, and customers who can't get through call the next firm on Google. Job details stay locked in {crms}.",
        "cta": "Worth a quick 15-minute demo? Or just reply with which job management system you use and how many engineers and office staff you have, and I'll send a quote.",
        "challenges": [
            ("Missed new-job calls", "Customers ring the next firm if nobody answers."),
            ("Engineers away from the office", "Calls can't reach the right person on site."),
            ("No job history to hand", "The office searches for the customer while they wait."),
        ],
        "outcomes": [
            ("Customer & job screen-pop", "Their history from your job system appears as the phone rings."),
            ("Calls on engineers' mobiles", "The business number follows the team on site."),
            ("Missed-call alerts", "Every missed call is flagged so no job is lost."),
            ("Call recording", "Settle quote and booking disputes with recorded calls."),
        ],
    },
    "Contact Centres & Customer Service": {
        "sector_plural": "contact centres",
        "subject": "Live queue insight for {company}",
        "pain": "Queues build without warning, supervisors can't see who's free, and agents switch between the phone and {crms} on every call.",
        "cta": "Worth a quick 15-minute demo? Or just reply with how many agents you run and which CRM you use, and I'll send an indicative quote.",
        "challenges": [
            ("Queues you can't see", "Supervisors only find out about waits when customers complain."),
            ("Calls to the wrong agent", "Callers are transferred around before they reach the right skill."),
            ("Quality checks by hand", "Listening back and scoring calls takes hours."),
        ],
        "outcomes": [
            ("Live wallboards", "Calls waiting, wait times and agent status in real time."),
            ("Skills-based routing", "Callers reach the right agent first time."),
            ("Call Scope quality scoring", "Recordings, analytics and QC in one place."),
            ("CRM screen-pop", "Customer records open automatically, with every call logged."),
        ],
    },
}

NEW_PLACE_RULES = {
    "Recruitment Agencies": {"types": {"employment_agency"},
                             "words": ("recruitment", "recruit", "staffing", "personnel", "resourcing", "talent", "careers")},
    "Financial Advisers & Mortgage Brokers": {"types": {"finance"},
                                              "words": ("financial", "wealth", "mortgage", "mortgages", "advisers", "advisors", "ifa", "planning", "finance")},
    "Insurance Brokers": {"types": {"insurance_agency"}, "words": ("insurance", "brokers", "broker", "insure")},
    "Car Dealers & Garages": {"types": {"car_dealer", "car_repair"},
                              "words": ("motors", "motor", "garage", "autos", "auto", "cars", "car", "vehicle", "vehicles", "tyres", "mot")},
    "Veterinary Practices": {"types": {"veterinary_care"}, "words": ("vet", "vets", "veterinary", "animal", "pet")},
    "Opticians": {"types": {"optician"}, "words": ("optician", "opticians", "eyecare", "optometrist", "optometrists", "eyewear", "vision", "eye")},
    "Property & Block Management": {"types": {"real_estate_agency"},
                                    "words": ("property", "properties", "management", "block", "estates", "residential", "lettings")},
    "Hotels & Hospitality": {"types": {"lodging", "hotel", "restaurant", "bar", "pub"},
                             "words": ("hotel", "inn", "restaurant", "bar", "kitchen", "lodge", "arms", "tavern", "bistro")},
    "Care Homes & Home Care": {"types": {"nursing_home"},
                               "words": ("care", "nursing", "healthcare", "residential", "homecare", "living", "carers")},
    "Trades & Building Services": {"types": {"plumber", "electrician", "general_contractor"},
                                   "words": ("plumbing", "heating", "electrical", "electrics", "gas", "building", "services", "installations", "boilers")},
    "Contact Centres & Customer Service": {"types": set(),
                                           "words": ("contact", "centre", "call", "customer", "service", "communications", "telemarketing", "support")},
}

# Lead Revival: words that point a CRM lead at each sector pitch
NEW_KEYWORDS = {
    "Recruitment Agencies": ("recruit", "staffing", "personnel", "resourcing", "employment agency"),
    "Financial Advisers & Mortgage Brokers": ("financial advi", "wealth", "mortgage", "ifa ", "financial planning"),
    "Insurance Brokers": ("insurance",),
    "Car Dealers & Garages": ("motors", "garage", "car sales", "autos", "vehicle", "tyres", "automotive"),
    "Veterinary Practices": ("veterinar", " vets", "vet group", "animal hospital"),
    "Opticians": ("optician", "optometr", "eyecare", "eye care"),
    "Property & Block Management": ("block management", "property management", "residential management"),
    "Hotels & Hospitality": ("hotel", "restaurant", "hospitality", " inn", "tavern"),
    "Care Homes & Home Care": ("care home", "nursing home", "home care", "homecare", "domiciliary", "care services"),
    "Trades & Building Services": ("plumbing", "heating", "electrical", "electrician", "gas services", "boiler"),
    "Contact Centres & Customer Service": ("contact centre", "call centre", "telemarketing", "customer service"),
}

VERTICAL_PRESETS.update(NEW_PRESETS)
# Fortlox: the same four headline benefits for every sector
for _sector, _copy in SECTOR_COPY.items():
    _crms = VERTICAL_PRESETS.get(_sector, {}).get("crms", ["your CRM"])
    _copy["outcomes"] = [
        ("Smarter call handling", "Queues, hunt groups and out-of-hours routing, so every call reaches the right person."),
        ("Voicemail to email", "Messages land straight in your inbox, so you can reply from anywhere."),
        ("Call recording", "Every call recorded for training, quality and peace of mind."),
        ("CRM integration", f"Works with {', '.join(_crms[:3])}: caller details pop up and every call is logged."),
    ]
SECTOR_PLACE_RULES.update(NEW_PLACE_RULES)
SECTOR_COPY.update(NEW_COPY)

EVERYTHING_WE_DO = [
    "Cloud phone systems & softphones",
    "Desk, DECT & headset hardware",
    "Business broadband & connectivity",
    "Business mobiles",
    "Networking & Wi-Fi",
    "CCTV, security & access control",
]


def friendly_company_name(legal_name: str) -> str:
    """'HART NEW HOMES (WALSALL) LIMITED' -> 'Hart New Homes (Walsall)'."""
    name = re.sub(r"\b(LIMITED|LTD\.?|PLC|LLP|L\.L\.P\.)\s*$", "", legal_name.strip(), flags=re.I).strip(" ,.")
    if name.isupper():
        name = " ".join(
            w if (w in {"&", "UK"} or (len(w) <= 3 and not any(c in "AEIOU" for c in w) and w.isalpha()))
            else w.title()
            for w in name.split()
        )
    return name.replace(" And ", " and ").replace(" Of ", " of ").replace(" The ", " the ")


def lead_display_name(lead: "ScrapedLead") -> str:
    """The name the firm actually trades under (Google Maps) if known, else a tidied legal name."""
    trading = (getattr(lead, "trading_name", None) or "").strip()
    if trading and len(trading) <= 60:
        return trading
    return friendly_company_name(lead.company_name)


def looks_like_company_name(name: str) -> bool:
    """True if someone typed the company (e.g. 'SYComms', 'SY Comms') where their own name goes."""
    flat = re.sub(r"[^a-z]", "", (name or "").lower())
    return bool(flat) and (flat.startswith("fortlox") or flat in ("fortloxsecurity", "fortlox"))


def get_sender() -> Dict[str, str]:
    sender = dict(SENDER_DEFAULTS)
    sender.update({k: v for k, v in st.session_state.get("sender_profile", {}).items() if v})
    if looks_like_company_name(sender.get("name", "")):
        sender["name"] = ""  # Sign as the company, never "I'm SYComms from SY Communications"
    return sender


def build_signature(sender: Dict[str, str]) -> str:
    lines = ["Kind regards,"]
    if sender.get("name"):
        lines.append("")
        lines.append(sender["name"])
        if sender.get("title"):
            lines.append(sender["title"])
    lines.append(SENDER_COMPANY)
    contact = " | ".join(x for x in (sender.get("phone"), sender.get("email")) if x)
    if contact:
        lines.append(contact)
    if sender.get("website"):
        lines.append(sender["website"])
    return "\n".join(lines)


def build_email_subject(lead: ScrapedLead, vertical_key: str) -> str:
    copy = SECTOR_COPY.get(vertical_key, SECTOR_COPY["Estate & Lettings Agents"])
    crms = VERTICAL_PRESETS.get(vertical_key, VERTICAL_PRESETS["Estate & Lettings Agents"])["crms"]
    return copy["subject"].format(company=lead_display_name(lead), crm1=crms[0])


def build_email_pitch(
    lead: ScrapedLead,
    vertical_key: str,
    include_attachment_line: bool = True,
    include_switchover: bool = True,
) -> str:
    config = VERTICAL_PRESETS.get(vertical_key, VERTICAL_PRESETS["Estate & Lettings Agents"])
    copy = SECTOR_COPY.get(vertical_key, SECTOR_COPY["Estate & Lettings Agents"])
    sender = get_sender()
    first_name, _ = infer_contact_name_and_role(lead, vertical_key)
    greeting_name = first_name if first_name != config["fallback_greeting"] else "there"
    company = lead_display_name(lead)
    crms = config["crms"]
    crms_str = ", ".join(crms[:2]) + f" or {crms[2]}" if len(crms) >= 3 else " or ".join(crms)

    who = f"I'm {sender['name']} from {SENDER_COMPANY}" if sender.get("name") else f"It's {SENDER_COMPANY} here"
    bullets = "\n".join(f"- {title}" for title, _ in copy["outcomes"][:4])

    parts = [
        f"Hi {greeting_name},",
        f"{who}. We help {copy['sector_plural']} like {company} connect their phones to the software they already use.",
        copy["pain"].format(crms=crms_str),
        "We connect your phones to whichever system you use, so you get:",
        bullets,
    ]
    if include_switchover:
        parts.append(SWITCHOVER_LINE)
    if include_attachment_line:
        parts.append(
            "I've attached a one-page overview of how it works."
        )
    parts.append(copy["cta"])
    parts.append(build_signature(sender))
    parts.append(
        "P.S. If this isn't relevant, just reply \"no thanks\" and I won't get in touch again."
    )
    return "\n\n".join(parts)


def _email_plain_html(body: str) -> str:
    """Plain look: the email as simple paragraphs, bullets and signature (like a personal email)."""
    blocks, out = [b for b in body.replace("\r\n", "\n").split("\n\n")], []
    for block in blocks:
        lines = [l for l in block.split("\n") if l.strip() != ""] or [""]
        if all(l.lstrip().startswith("- ") for l in lines):
            items = "".join(f"<li>{html_lib.escape(l.lstrip()[2:])}</li>" for l in lines)
            out.append(f'<ul style="margin:0 0 14px 0;padding-left:20px">{items}</ul>')
        else:
            text = "<br>".join(html_lib.escape(l) for l in block.split("\n"))
            style = "margin:0 0 14px 0"
            if block.startswith("P.S."):
                style += ";color:#6b7280;font-size:12px"
            out.append(f'<p style="{style}">{text}</p>')
    return (
        '<html><body style="font-family:Calibri,Arial,sans-serif;font-size:14px;line-height:1.45;color:#1f2937">'
        + "".join(out) + "</body></html>"
    )


def _hex(rgb: Tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def _email_branded_html(body: str, subject: str = "") -> str:
    """Branded look: SY Communications header, feature tiles, switch-off callout, a demo button and a
    proper signature. Built from the (editable) plain-text email, using tables and inline styles only,
    so it renders in Outlook, Gmail, Apple Mail and Zoho alike. No images, so nothing is blocked."""
    purple, purple2, teal = _hex(BRAND_PURPLE), _hex(BRAND_PURPLE_2), _hex(BRAND_TEAL)
    font = "font-family:'Segoe UI',Calibri,Arial,Helvetica,sans-serif"
    sender = get_sender()
    e = html_lib.escape
    blocks = [b.strip("\n") for b in body.replace("\r\n", "\n").split("\n\n")]
    rows: List[str] = []
    sig_lines: List[str] = []
    ps = ""
    in_sig = False

    def para(text: str, extra: str = "") -> str:
        inner = "<br>".join(e(l) for l in text.split("\n"))
        return (f'<tr><td style="padding:0 36px 16px 36px;{font};font-size:15px;line-height:1.6;color:#1f2937;{extra}">'
                f"{inner}</td></tr>")

    for block in blocks:
        if not block.strip():
            continue
        first = block.lstrip()
        if first.startswith("P.S."):
            ps = block
            continue
        if in_sig or first.lower().startswith(("kind regards", "best regards", "many thanks", "regards")):
            in_sig = True
            sig_lines += [l for l in block.split("\n") if l.strip()]
            continue
        lines = [l for l in block.split("\n") if l.strip()]
        if lines and all(l.lstrip().startswith("- ") for l in lines):
            items = [l.lstrip()[2:] for l in lines]
            cells = ""
            for i in range(0, len(items), 2):
                pair = items[i:i + 2]
                tds = "".join(
                    f'<td width="50%" valign="top" style="padding:5px">'
                    f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
                    f'<td style="background:#f4f2fb;border-left:4px solid {teal};border-radius:6px;padding:12px 14px;'
                    f'{font};font-size:14px;font-weight:600;color:{purple}">'
                    f'<span style="color:{teal};font-weight:700">&#10003;</span>&nbsp; {e(it)}</td></tr></table></td>'
                    for it in pair)
                if len(pair) == 1:
                    tds += '<td width="50%"></td>'
                cells += f"<tr>{tds}</tr>"
            rows.append(f'<tr><td style="padding:0 31px 14px 31px"><table role="presentation" width="100%" '
                        f'cellpadding="0" cellspacing="0" border="0">{cells}</table></td></tr>')
            continue
        low = first.lower()
        if "analogue" in low and "2027" in low:
            rows.append(
                f'<tr><td style="padding:2px 36px 18px 36px"><table role="presentation" width="100%" cellpadding="0" '
                f'cellspacing="0" border="0"><tr><td style="background:#fff7e8;border:1px solid #f5c26b;border-radius:8px;'
                f'padding:14px 16px;{font};font-size:14px;line-height:1.55;color:#7a4b00">'
                f'<strong style="color:#b45309">&#9200; BT switch-off: January 2027</strong><br>{e(block)}</td></tr></table></td></tr>')
            continue
        if low.startswith("worth a quick") or ("demo" in low and "?" in first and len(first) < 260):
            head, _, rest = first.partition("?")
            href = _secret_value("DEMO_BOOKING_URL") or (
                f"mailto:{sender.get('email', '')}?subject={quote('Demo request: ' + (subject or 'phone system'))}")
            label = "Book a 15-minute demo" if "15" in head else "Book a quick demo"
            rows.append(
                f'<tr><td align="center" style="padding:8px 36px 6px 36px">'
                f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
                f'<td align="center" bgcolor="{teal}" style="border-radius:8px">'
                f'<a href="{e(href)}" style="display:inline-block;padding:13px 30px;{font};font-size:15px;font-weight:700;'
                f'color:#ffffff;text-decoration:none;border-radius:8px">{label} &rarr;</a></td></tr></table></td></tr>')
            if rest.strip():
                rows.append(para(rest.strip(), "text-align:center;font-size:14px;color:#4b5563;padding-top:10px"))
            continue
        if low.startswith("i've attached"):
            rows.append(para("\U0001F4CE " + block, "font-size:14px;color:#4b5563"))
            continue
        rows.append(para(block))

    # Signature block
    sig_html = ""
    if sig_lines:
        closing, rest_lines = sig_lines[0], sig_lines[1:]
        name_lines = [l for l in rest_lines if l.strip() != SENDER_COMPANY and "|" not in l and "www." not in l]
        contact = next((l for l in rest_lines if "|" in l), "")
        site = next((l for l in rest_lines if "www." in l), "")
        who = "".join(
            f'<div style="{font};font-size:{15 if i == 0 else 13}px;font-weight:{700 if i == 0 else 400};'
            f'color:{purple if i == 0 else "#4b5563"}">{e(l)}</div>' for i, l in enumerate(name_lines))
        site_html = (f'<a href="https://{e(site.strip().replace("https://", "").replace("http://", ""))}" '
                     f'style="color:{teal};text-decoration:none;font-weight:600">{e(site.strip())}</a>' if site else "")
        sig_html = (
            f'<tr><td style="padding:10px 36px 26px 36px">'
            f'<div style="{font};font-size:15px;color:#1f2937;margin-bottom:12px">{e(closing)}</div>'
            f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td style="border-left:3px solid {teal};padding:2px 0 2px 14px">{who}'
            f'<div style="{font};font-size:14px;font-weight:700;color:{purple};margin-top:{4 if who else 0}px">{e(SENDER_COMPANY)}</div>'
            f'<div style="{font};font-size:13px;color:#4b5563;margin-top:2px">{e(contact)}</div>'
            f'<div style="{font};font-size:13px;margin-top:2px">{site_html}</div>'
            f"</td></tr></table></td></tr>")

    header = (
        f'<tr><td bgcolor="{purple}" style="background:{purple};padding:22px 36px;border-radius:12px 12px 0 0">'
        f'<div style="{font};font-size:20px;font-weight:800;color:#ffffff;letter-spacing:.2px">'
        f'<span style="color:{teal};letter-spacing:1px">FORTLOX</span> SECURITY</div>'
        f'<div style="{font};font-size:12px;color:#c9c3ec;margin-top:3px">Telecoms, connectivity &amp; security, all from one local team</div>'
        f'</td></tr>'
        f'<tr><td height="4" bgcolor="{teal}" style="background:{teal};font-size:0;line-height:0">&nbsp;</td></tr>'
        f'<tr><td style="padding:28px 0 0 0;font-size:0;line-height:0">&nbsp;</td></tr>'
    )
    footer = (
        f'<tr><td style="padding:14px 36px 0 36px;{font};font-size:12px;line-height:1.5;color:#8a8fa3">{e(ps)}</td></tr>'
        if ps else "")
    address = SENDER_DEFAULTS.get("address", "")
    return (
        '<html><body style="margin:0;padding:0;background:#f1f0f7">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f1f0f7" '
        'style="background:#f1f0f7"><tr><td align="center" style="padding:24px 12px">'
        '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" '
        'style="width:100%;max-width:600px">'
        '<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" '
        f'style="background:#ffffff;border-radius:12px;border:1px solid #e4e1f0">{header}{"".join(rows)}{sig_html}</table></td></tr>'
        f"{footer}"
        + (f'<tr><td style="padding:6px 36px 0 36px;{font};font-size:11px;color:#a3a7b8">{e(SENDER_COMPANY)} · {e(address)}</td></tr>'
           if address else "")
        + "</table></td></tr></table></body></html>"
    )


def _email_body_html(body: str, subject: str = "") -> str:
    """The HTML version of an email: branded (default) or plain, per the 'Branded email design' switch."""
    try:
        branded = st.session_state.get("opt_branded", True)
    except Exception:
        branded = True
    return _email_branded_html(body, subject) if branded else _email_plain_html(body)


def build_eml_draft(
    to: str,
    subject: str,
    body: str,
    attachments: Optional[List[Tuple[str, bytes]]] = None,
) -> bytes:
    """A ready-to-send email draft (.eml) with attachments.

    Outlook for Windows opens it as an unsent draft (thanks to the X-Unsent header),
    with the To, Subject, formatted body and PDF already in place.
    """
    msg = EmailMessage()
    if to:
        msg["To"] = to
    msg["Subject"] = subject or ""
    msg["Date"] = formatdate(localtime=True)
    msg["X-Unsent"] = "1"  # Tells Outlook to open this as a new draft, not a received email
    msg.set_content(body.replace("\r\n", "\n"))
    msg.add_alternative(_email_body_html(body, subject or ""), subtype="html")
    for filename, data in attachments or []:
        msg.add_attachment(data, maintype="application", subtype="pdf", filename=filename)
    return msg.as_bytes()


def build_mailto(to: str, subject: str, body: str) -> str:
    """mailto: link that opens the user's default email app with everything filled in."""
    body_crlf = body.replace("\r\n", "\n").replace("\n", "\r\n")
    return (
        f"mailto:{quote(to or '', safe='@.+-_')}"
        f"?subject={quote(subject or '', safe='')}"
        f"&body={quote(body_crlf, safe='')}"
    )



# ------------------------------------------------------------------
# SY Communications sector overview (the "About us" email attachment)
# ------------------------------------------------------------------


def _box(pdf: FPDF, x: float, y: float, w: float, h: float, style: str = "F", radius: float = 2.5) -> None:
    try:
        pdf.rect(x, y, w, h, style=style, round_corners=True, corner_radius=radius)
    except TypeError:  # Older fpdf2 without rounded corners
        pdf.rect(x, y, w, h, style=style)


def create_sector_overview_pdf(lead: Optional[ScrapedLead], vertical_key: str) -> bytes:
    """One-page, branded Fortlox Security solutions overview, personalised to the prospect."""
    copy = SECTOR_COPY.get(vertical_key, SECTOR_COPY["Estate & Lettings Agents"])
    cfg = VERTICAL_PRESETS.get(vertical_key, VERTICAL_PRESETS["Estate & Lettings Agents"])
    sender = get_sender()
    T = sanitize_pdf_text
    purple, purple2, teal = BRAND_PURPLE, BRAND_PURPLE_2, BRAND_TEAL
    ink, grey, light = (30, 30, 46), (95, 100, 120), (244, 243, 250)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()
    W = 210
    L, R = 14, 196
    CW = R - L

    # ---------- Header band: white, with the Fortlox logo ----------
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 0, W, 50, "F")
    pdf.set_fill_color(*purple)
    pdf.rect(0, 46, W, 4, "F")
    pdf.set_fill_color(*teal)
    pdf.rect(0, 50, W, 1.2, "F")
    try:
        pdf.image(logo_image(), x=L, y=5, h=24)
    except Exception:
        pdf.set_xy(L, 13)
        pdf.set_font("Helvetica", "B", 17)
        pdf.set_text_color(*teal)
        pdf.cell(100, 8, "FORTLOX SECURITY")
    pdf.set_xy(L, 31)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*purple)
    pdf.multi_cell(108, 6, T(f"Phone systems built for {copy['sector_plural']}"), align="L")
    # Prepared-for panel
    if lead:
        pdf.set_fill_color(*purple2)
        _box(pdf, 128, 11, 68, 26)
        pdf.set_xy(132, 14)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(*teal)
        pdf.cell(60, 4, "PREPARED FOR")
        pdf.set_xy(132, 19)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(255, 255, 255)
        pdf.multi_cell(61, 4.6, T(lead_display_name(lead)[:60]), align="L")
        pdf.set_xy(132, 30.5)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(190, 184, 230)
        pdf.cell(60, 4, T(pd.Timestamp.now().strftime("%B %Y")))

    # ---------- Intro ----------
    crms = cfg["crms"]
    y = 58
    pdf.set_xy(L, y)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*ink)
    pdf.multi_cell(
        CW, 5.2,
        T(
            f"We connect your phone system directly to {', '.join(crms[:-1])} and {crms[-1]}, so every call"
            " arrives with context, gets logged automatically and never slips through the cracks."
        ),
        align="L",
    )

    def heading(text: str, yy: float) -> float:
        pdf.set_xy(L, yy)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*teal)
        pdf.cell(CW, 4, text.upper())
        pdf.set_draw_color(*teal)
        pdf.set_line_width(0.5)
        pdf.line(L, yy + 5.2, L + 10, yy + 5.2)
        return yy + 8

    # ---------- The challenge (3 cards) ----------
    y = heading("The challenge", pdf.get_y() + 4)
    gap = 4
    cw3 = (CW - 2 * gap) / 3
    for i, (title, desc) in enumerate(copy["challenges"][:3]):
        x = L + i * (cw3 + gap)
        pdf.set_fill_color(*light)
        _box(pdf, x, y, cw3, 24)
        pdf.set_xy(x + 4, y + 3.5)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*purple)
        pdf.multi_cell(cw3 - 8, 4.4, T(title), align="L")
        pdf.set_xy(x + 4, pdf.get_y() + 1)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*grey)
        pdf.multi_cell(cw3 - 8, 3.9, T(desc), align="L")
    y += 24 + 5

    # ---------- How we solve it ----------
    y = heading("How we solve it", y)
    pdf.set_xy(L, y)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*grey)
    pdf.cell(22, 6, "Integrates with:")
    x = L + 23
    pdf.set_font("Helvetica", "B", 8)
    for crm in crms:
        w = pdf.get_string_width(T(crm)) + 7
        pdf.set_draw_color(*teal)
        pdf.set_line_width(0.35)
        pdf.set_text_color(*purple)
        _box(pdf, x, y + 0.5, w, 5.2, style="D", radius=2.6)
        pdf.set_xy(x, y + 0.5)
        pdf.cell(w, 5.2, T(crm), align="C")
        x += w + 2.5
    y += 10
    cw2 = (CW - gap) / 2
    for i, (title, desc) in enumerate(copy["outcomes"][:4]):
        col, row = i % 2, i // 2
        x = L + col * (cw2 + gap)
        yy = y + row * 17
        pdf.set_fill_color(*teal)
        pdf.ellipse(x, yy + 0.5, 7, 7, "F")
        pdf.set_xy(x, yy + 1.8)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(7, 4.4, str(i + 1), align="C")
        pdf.set_xy(x + 10, yy)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*ink)
        pdf.cell(cw2 - 10, 5, T(title))
        pdf.set_xy(x + 10, yy + 5.5)
        pdf.set_font("Helvetica", "", 8.2)
        pdf.set_text_color(*grey)
        pdf.multi_cell(cw2 - 12, 4, T(desc), align="L")
    y += 2 * 17 + 1

    # ---------- Switchover callout ----------
    pdf.set_fill_color(230, 247, 245)
    _box(pdf, L, y, CW, 19)
    pdf.set_fill_color(*teal)
    pdf.rect(L, y, 1.6, 19, "F")
    pdf.set_xy(L + 6, y + 3)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(*purple)
    pdf.cell(CW - 10, 5, "The analogue switch-off is coming: January 2027")
    pdf.set_xy(L + 6, y + 8.5)
    pdf.set_font("Helvetica", "", 8.2)
    pdf.set_text_color(*grey)
    pdf.multi_cell(
        CW - 12, 4,
        "BT is retiring the traditional phone network. If you still rely on analogue or ISDN lines, moving now"
        " means you choose the timing, and you upgrade to a system that works with your software.",
        align="L",
    )
    y += 19 + 5

    # ---------- One partner + Why us (two columns) ----------
    y0 = y
    heading("One partner for your technology", y)
    yy = y + 8
    for i, item in enumerate(EVERYTHING_WE_DO):
        pdf.set_fill_color(*teal)
        pdf.ellipse(L, yy + i * 6 + 1.6, 2, 2, "F")
        pdf.set_xy(L + 4, yy + i * 6)
        pdf.set_font("Helvetica", "", 8.3)
        pdf.set_text_color(*ink)
        pdf.cell(80, 5, T(item))

    xw = L + CW / 2 + 4
    pdf.set_xy(xw, y0)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*teal)
    pdf.cell(80, 4, "WHY FORTLOX SECURITY")
    pdf.set_draw_color(*teal)
    pdf.line(xw, y0 + 5.2, xw + 10, y0 + 5.2)
    why = [
        ("Local to you", "A Gloucestershire team you can actually speak to."),
        ("One stop shop", "Phones, connectivity, mobiles and security from one supplier."),
        ("Built around your software", "We set up the integration around how your team works."),
        ("Clear, no-obligation quotes", "Straightforward pricing before you commit to anything."),
    ]
    yy = y0 + 8
    for title, desc in why:
        pdf.set_xy(xw, yy)
        pdf.set_font("Helvetica", "B", 8.3)
        pdf.set_text_color(*ink)
        pdf.cell(80, 4.2, T(title))
        pdf.set_xy(xw, yy + 4.2)
        pdf.set_font("Helvetica", "", 7.8)
        pdf.set_text_color(*grey)
        pdf.cell(80, 4, T(desc))
        yy += 9
    y = max(yy, y0 + 8 + 6 * 6) + 3

    # ---------- Next steps ----------
    if y > 250:  # Safety: never collide with the footer
        y = 250
    y = heading("Next steps", y)
    steps = [
        ("15-minute call", "A quick chat about your team, lines and software."),
        ("Free review", "We look at your current setup and contracts."),
        ("Tailored quote", "A clear, no-obligation proposal."),
    ]
    for i, (title, desc) in enumerate(steps):
        x = L + i * (cw3 + gap)
        pdf.set_fill_color(*light)
        _box(pdf, x, y, cw3, 16)
        pdf.set_xy(x + 4, y + 3)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*purple)
        pdf.cell(cw3 - 8, 4.5, T(f"{i + 1}. {title}"))
        pdf.set_xy(x + 4, y + 8.3)
        pdf.set_font("Helvetica", "", 7.6)
        pdf.set_text_color(*grey)
        pdf.multi_cell(cw3 - 8, 3.6, T(desc), align="L")

    # ---------- Footer band ----------
    pdf.set_fill_color(*purple)
    pdf.rect(0, 272, W, 25, "F")
    pdf.set_fill_color(*teal)
    pdf.rect(0, 272, W, 1.2, "F")
    pdf.set_xy(L, 277)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(255, 255, 255)
    contact_name = sender.get("name") or "Talk to our team"
    pdf.cell(90, 5, T(contact_name + (f"  |  {sender['title']}" if sender.get("name") and sender.get("title") else "")))
    pdf.set_xy(L, 283)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(190, 184, 230)
    pdf.cell(
        CW, 5,
        T("  |  ".join(x for x in (sender.get("phone"), sender.get("email"), sender.get("website")) if x)),
    )
    pdf.set_xy(L, 288.5)
    pdf.set_font("Helvetica", "", 7.2)
    pdf.cell(CW, 4, T(sender.get("address", "")))

    out = pdf.output()
    return bytes(out) if not isinstance(out, str) else out.encode("latin-1", errors="replace")


class LeadDossierPDF(FPDF):

    def header(self):
        self.set_fill_color(30, 41, 59)  # Dark slate header bar
        self.rect(0, 0, 210, 14, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 9)
        self.set_xy(12, 3)
        self.cell(
            0,
            8,
            "FORTLOX SECURITY | CONFIDENTIAL LEAD RECORD",
            ln=0,
        )
        self.ln(14)

    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(148, 163, 184)
        self.cell(
            0,
            6,
            "Confidential lead record - Generated for internal sales review",
            0,
            0,
            "C",
        )


def create_pdf_dossier(
    lead: ScrapedLead,
    vertical_name: str,
    pitch_text: str,
    target_crms: List[str],
) -> bytes:
    pdf = LeadDossierPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    contact_name, contact_role = infer_contact_name_and_role(
        lead, vertical_name
    )

    # 1. PRIMARY CONTACT CARD
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 4, "PRIMARY CONTACT", ln=True)

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, sanitize_pdf_text(contact_name), ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(71, 85, 105)
    primary_email = pick_primary_email(lead, contact_name) or "Email TBD"
    primary_phone = (
        lead.phones_found[0] if lead.phones_found else "Phone TBD"
    )
    contact_sub = f"{contact_role} - {primary_email} - {primary_phone}"
    pdf.cell(0, 5, sanitize_pdf_text(contact_sub), ln=True)

    pdf.ln(3)

    # 2. FIRM CARD
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 4, "TARGET FIRM", ln=True)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, sanitize_pdf_text(lead.company_name[:55]), ln=True)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(71, 85, 105)
    addr_line = lead.registered_address or "Address not listed"
    site_line = lead.website_url or "Website not specified"
    pdf.cell(
        0,
        5,
        sanitize_pdf_text(
            f"{vertical_name} - {addr_line[:65]}" + (" - Company" if lead.company_number else "")
            + (f" #{lead.company_number}" if lead.company_number else "")
        ),
        ln=True,
    )
    pdf.cell(0, 5, sanitize_pdf_text(f"Domain: {site_line}"), ln=True)

    if lead.site_meta_description:
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.multi_cell(
            190, 4, sanitize_pdf_text(f'"{lead.site_meta_description[:200]}"')
        )

    pdf.ln(2)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # 3. CORE INTEGRATION HOOK
    vert_cfg = VERTICAL_PRESETS.get(
        vertical_name, VERTICAL_PRESETS["Estate & Lettings Agents"]
    )
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 4, "SYSTEM INTEGRATION HOOK", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(2, 132, 199)  # Highlighted blue
    crms_headline = f"{vert_cfg['primary_hook']} (confirm which)"
    pdf.cell(0, 5, sanitize_pdf_text(crms_headline), ln=True)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(51, 65, 85)
    for bullet in vert_cfg["pitch_bullets"]:
        pdf.cell(0, 4.5, sanitize_pdf_text(f"- {bullet}"), ln=True)

    pdf.ln(3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # 4. TAILORED OUTREACH EMAIL DRAFT
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 4, "READY-TO-SEND OUTREACH EMAIL COPY", ln=True)

    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(15, 23, 42)

    clean_pitch = sanitize_pdf_text(pitch_text)
    pdf.multi_cell(190, 4.2, clean_pitch, border=1, fill=True)

    output = pdf.output()
    if isinstance(output, str):
        return output.encode("latin-1", errors="replace")
    elif isinstance(output, bytearray):
        return bytes(output)
    return output


# ==========================================
# 3b. SENT LOG (remembers who's been emailed, across sessions)
# ==========================================


def _secret_value(key: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(key, default) or default)
    except Exception:
        return default


class SentLog:
    """Stores {company_number: record} of firms that have been emailed.

    Permanent: a JSON file in a private GitHub repo (set GITHUB_TOKEN + GITHUB_REPO in Secrets).
    Fallback: a local file, which Streamlit Cloud wipes whenever the app restarts or redeploys.
    """

    def __init__(self, path_secret: str = "GITHUB_LOG_PATH", default_path: str = "sent_log.json",
                 local_name: str = ".sent_log.json", compact: bool = False) -> None:
        self.compact = compact  # Smaller file for big stores (saved firms)
        self.token = _secret_value("GITHUB_TOKEN")
        self.repo = _secret_value("GITHUB_REPO")  # e.g. "sammyatt2010-hub/prospect-engine-data"
        self.branch = _secret_value("GITHUB_BRANCH", "main")
        self.path = _secret_value(path_secret, default_path)
        self.backend = "github" if (self.token and self.repo) else "local"
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base_dir = os.getcwd()
        self.local_path = os.path.join(base_dir, local_name)
        self.last_error: Optional[str] = None

    # ---------- GitHub backend ----------
    def _url(self) -> str:
        return f"https://api.github.com/repos/{self.repo}/contents/{self.path}"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _gh_read(self) -> Tuple[Dict[str, Any], Optional[str]]:
        resp = requests.get(self._url(), headers=self._headers(), params={"ref": self.branch}, timeout=10)
        if resp.status_code == 404:
            return {}, None  # File doesn't exist yet; first write creates it
        if resp.status_code != 200:
            raise RuntimeError(self._describe(resp.status_code))
        payload = resp.json()
        if payload.get("encoding") == "none" or (not payload.get("content") and payload.get("size", 0) > 0):
            # Files over 1 MB: GitHub leaves the content out, so fetch the raw file
            raw = requests.get(self._url(), headers={**self._headers(), "Accept": "application/vnd.github.raw+json"},
                               params={"ref": self.branch}, timeout=20)
            if raw.status_code != 200:
                raise RuntimeError(self._describe(raw.status_code))
            payload = {**payload, "content": base64.b64encode(raw.content).decode("ascii")}
        content = base64.b64decode(payload.get("content", "") or b"").decode("utf-8-sig").strip()
        if not content or content in ("[]", "null"):
            return {}, payload.get("sha")  # Emptied by hand on GitHub: treat as a fresh start
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            raise RuntimeError(f"{self.path} on GitHub isn't valid JSON. Replace its contents with {{}} to start fresh.")
        return (data if isinstance(data, dict) else {}), payload.get("sha")

    def _gh_write(self, data: Dict[str, Any], sha: Optional[str], message: str) -> int:
        body: Dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(json.dumps(data, indent=None if self.compact else 2, sort_keys=True,
                                                   separators=(",", ":") if self.compact else None
                                                   ).encode("utf-8")).decode("ascii"),
            "branch": self.branch,
        }
        if sha:
            body["sha"] = sha
        resp = requests.put(self._url(), headers=self._headers(), json=body, timeout=25)
        return resp.status_code

    @staticmethod
    def _describe(code: int) -> str:
        return {
            401: "GitHub rejected the token (401). Check GITHUB_TOKEN in Secrets.",
            403: "GitHub token lacks permission (403). It needs Contents: Read and write on the repo.",
            404: "GitHub repo not found (404). Check GITHUB_REPO in Secrets.",
        }.get(code, f"GitHub returned an error ({code}).")

    # ---------- Local backend ----------
    def _local_read(self) -> Dict[str, Any]:
        try:
            with open(self.local_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _local_write(self, data: Dict[str, Any]) -> None:
        tmp = self.local_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
        os.replace(tmp, self.local_path)

    # ---------- Public API ----------
    def load(self) -> Dict[str, Any]:
        self.last_error = None
        try:
            return self._gh_read()[0] if self.backend == "github" else self._local_read()
        except Exception as exc:  # Never let the log break the app
            self.last_error = str(exc) if isinstance(exc, RuntimeError) else f"Couldn't load sent log ({exc.__class__.__name__})."
            return {}

    def apply(self, changes: Dict[str, Optional[Dict[str, Any]]], message: str) -> Dict[str, Any]:
        """Applies {company_number: record or None (= un-mark)} and returns the latest full log.
        Re-reads before writing, so two people using the app at once don't overwrite each other."""
        self.last_error = None

        def merge(data: Dict[str, Any]) -> Dict[str, Any]:
            for key, record in changes.items():
                if record is None:
                    data.pop(key, None)
                else:
                    data[key] = record
            return data

        if self.backend == "local":
            data = merge(self._local_read())
            self._local_write(data)
            return data

        for _attempt in range(3):
            data, sha = self._gh_read()
            data = merge(data)
            status = self._gh_write(data, sha, message)
            if status in (200, 201):
                return data
            if status not in (409, 422):  # 409/422 = someone else saved first; re-read and retry
                raise RuntimeError(self._describe(status))
        raise RuntimeError("GitHub was busy saving the sent log. Please try again.")


def now_uk() -> datetime:
    try:
        return datetime.now(ZoneInfo("Europe/London"))
    except Exception:
        return datetime.now()


def sent_label(record: Optional[Dict[str, Any]]) -> str:
    """'✓ 25 Sep' for the tables."""
    if not record:
        return ""
    try:
        return "✓ " + datetime.fromisoformat(record.get("sent_at", "")).strftime("%d %b").lstrip("0")
    except ValueError:
        return "✓ Sent"


# ------------------------------------------------------------------
# Batch export: a zip of ready-to-send Outlook drafts
# ------------------------------------------------------------------


def draft_filename_part(company_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", friendly_company_name(company_name)).strip("_") or "firm"


def build_lead_list_csv(items: List[Dict[str, Any]], log: Dict[str, Any]) -> bytes:
    """Spreadsheet of every selected firm, including those with no email (for phoning)."""
    rows = []
    for item in items:
        lead: ScrapedLead = item["lead"]
        cn = lead.company_number or ""
        contact, role = infer_contact_name_and_role(lead, item["vertical"])
        directors = [display_officer_name(o.name) for o in lead.officers if o.raw_role in DECISION_MAKER_ROLES]
        rec = log.get(cn)
        rows.append({
            "Status": (f"{rec.get('status') or 'Emailed'} {sent_label(rec)[2:]}" if rec
                       else "Ready to email" if item.get("to") else "No email"),
            "Firm": lead.company_name,
            "Trading name": getattr(lead, "trading_name", None) or "",
            "Company number": cn,
            "Sector": item["vertical"],
            "Contact": contact,
            "Contact role": role,
            "Email": item.get("to", ""),
            "Other emails": "; ".join(e for e in lead.emails_found if e != item.get("to")),
            "Phone": (lead.phones_found or [""])[0],
            "Other phones": "; ".join(lead.phones_found[1:]),
            "TPS/CTPS checked (you)": "",
            "Directors": "; ".join(directors),
            "Website": lead.website_url or "",
            "Website match": (lead.website_confidence or "") if lead.website_url else "Not found",
            "Registered office": lead.registered_address or "",
            "Email subject": item.get("subject", "") if item.get("to") else "",
        })
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")  # utf-8-sig = opens cleanly in Excel


def build_drafts_zip(items: List[Dict[str, Any]], attach_overview: bool) -> Tuple[bytes, int, List[str]]:
    """items: queue items with lead/vertical/to/subject/body. Returns (zip_bytes, drafts_written, skipped_names)."""
    buf = io.BytesIO()
    written, skipped = 0, []
    summary = io.StringIO()
    summary.write("Firm,Company number,To,Contact,Subject,Website,Website match\n")
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in items:
            lead: ScrapedLead = item["lead"]
            if not item.get("to"):
                skipped.append(lead_display_name(lead))
                continue
            written += 1
            part = draft_filename_part(lead.company_name)
            attachments = None
            if attach_overview:
                sector_slug = re.sub(
                    r"[^A-Za-z0-9]+", "_",
                    SECTOR_COPY.get(item["vertical"], {}).get("sector_plural", "sector"),
                ).strip("_")
                attachments = [(
                    f"Fortlox_Security_{sector_slug}_overview_{part}.pdf",
                    create_sector_overview_pdf(lead, item["vertical"]),
                )]
            eml = build_eml_draft(item["to"], item["subject"], item["body"], attachments=attachments)
            zf.writestr(f"{written:02d}_{part}.eml", eml)
            contact, _ = infer_contact_name_and_role(lead, item["vertical"])
            row = [lead.company_name, lead.company_number or "", item["to"], contact,
                   item["subject"], lead.website_url or "", lead.website_confidence or "Not found"]
            summary.write(",".join('"' + str(v).replace('"', '""') + '"' for v in row) + "\n")
        zf.writestr("_summary.csv", summary.getvalue())
        zf.writestr("_READ_ME_FIRST_TPS.txt",
                    "These contact details come from public sources and have NOT been checked against the\r\n"
                    "TPS or Corporate TPS (CTPS) registers. It is your sole responsibility to carry out these\r\n"
                    "checks before contacting any business or person in these drafts.\r\n")
    return buf.getvalue(), written, skipped


# ==========================================
# 4. STREAMLIT APPLICATION
# ==========================================

# ==========================================
# ZOHO CRM: every enriched firm becomes a Zoho Lead (duplicate-checked), then Send via Zoho
# ==========================================
ZOHO_SEND_LIMIT = 100  # Zoho's Send Mail API allows 100 emails a day
ZOHO_SCOPE = ("ZohoCRM.modules.leads.ALL,ZohoCRM.modules.accounts.READ,ZohoCRM.modules.contacts.READ,"
              "ZohoCRM.modules.notes.CREATE,ZohoCRM.coql.READ,ZohoCRM.settings.fields.READ,ZohoCRM.org.READ,"
              "ZohoCRM.send_mail.leads.CREATE,ZohoCRM.Files.CREATE,ZohoCRM.settings.emails.READ")

class ZohoError(RuntimeError):
    pass


class ZohoCRM:
    """Minimal Zoho CRM v8 client using a Self Client refresh token (EU data centre by default)."""

    def __init__(self) -> None:
        self.client_id = _secret_value("ZOHO_CLIENT_ID")
        self.client_secret = _secret_value("ZOHO_CLIENT_SECRET")
        self.refresh_token = _secret_value("ZOHO_REFRESH_TOKEN")
        self.accounts_url = _secret_value("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.eu").rstrip("/")
        self.api_domain = _secret_value("ZOHO_API_DOMAIN", "https://www.zohoapis.eu").rstrip("/")
        self.crm_url = _secret_value("ZOHO_CRM_URL", "https://crm.zoho.eu").rstrip("/")
        self.configured = bool(self.client_id and self.client_secret and self.refresh_token)
        # Client ID + secret in Secrets but no refresh token yet: the app can do the one-off swap itself
        self.can_setup = bool(self.client_id and self.client_secret) and not self.refresh_token

    # ---------- one-off setup: swap a Self Client code for a refresh token ----------
    def exchange_code(self, code: str) -> Dict[str, str]:
        """Returns {'refresh_token': ...} or {'error': plain-English reason}."""
        try:
            resp = requests.post(
                f"{self.accounts_url}/oauth/v2/token",
                data={"grant_type": "authorization_code", "client_id": self.client_id,
                      "client_secret": self.client_secret, "code": code.strip()},
                timeout=15,
            )
            data = resp.json()
        except requests.exceptions.RequestException as exc:
            return {"error": f"Couldn't reach Zoho ({exc.__class__.__name__}). Try again in a moment."}
        except ValueError:
            return {"error": f"Zoho sent an unreadable reply (HTTP {resp.status_code}). Check the Self Client is on api-console.zoho.eu."}
        if data.get("refresh_token"):
            return {"refresh_token": data["refresh_token"]}
        if data.get("access_token"):
            return {"error": "Zoho gave a short-lived token but no refresh token. Generate a new code and try again."}
        err = str(data.get("error") or f"HTTP {resp.status_code}")
        hints = {
            "invalid_code": "The code has expired or was already used. Codes last only a few minutes and work once, so generate a fresh one and paste it straight in.",
            "invalid_client": "Zoho doesn't recognise ZOHO_CLIENT_ID. Copy it again from the Self Client's Client Secret tab. If the Self Client was made on api-console.zoho.com (not .eu), make a new one on api-console.zoho.eu.",
            "invalid_client_secret": "ZOHO_CLIENT_SECRET doesn't match the client ID. Copy it again from the Self Client's Client Secret tab (watch for stray spaces).",
        }
        return {"error": f"Zoho said: {err}. " + hints.get(err, "Generate a fresh code and try again. If it keeps failing, check the client ID and secret in Secrets.")}

    # ---------- auth ----------
    def _token(self, force: bool = False) -> str:
        cached = st.session_state.get("zoho_token")
        if cached and not force and cached[1] > time.time() + 60:
            return cached[0]
        try:
            resp = requests.post(
                f"{self.accounts_url}/oauth/v2/token",
                params={"refresh_token": self.refresh_token, "client_id": self.client_id,
                        "client_secret": self.client_secret, "grant_type": "refresh_token"},
                timeout=12,
            )
            data = resp.json()
        except requests.exceptions.RequestException as exc:
            raise ZohoError(f"Couldn't reach Zoho to sign in ({exc.__class__.__name__}).")
        except ValueError:
            raise ZohoError("Zoho sent an unreadable sign-in response.")
        if "access_token" not in data:
            err = data.get("error", "unknown error")
            hint = {
                "invalid_code": "The refresh token is invalid or was revoked. Generate a new one in api-console.zoho.eu.",
                "invalid_client": "ZOHO_CLIENT_ID / ZOHO_CLIENT_SECRET don't match. Check them in Secrets.",
            }.get(err, "Check the Zoho secrets and that the Self Client is in the EU data centre.")
            raise ZohoError(f"Zoho sign-in failed ({err}). {hint}")
        if data.get("api_domain"):
            self.api_domain = data["api_domain"].rstrip("/")
        st.session_state["zoho_token"] = (data["access_token"], time.time() + int(data.get("expires_in", 3600)))
        return data["access_token"]

    def _request(self, method: str, path: str, **kwargs) -> Optional[Dict[str, Any]]:
        for attempt in (0, 1):
            headers = {"Authorization": f"Zoho-oauthtoken {self._token(force=attempt == 1)}"}
            try:
                resp = requests.request(method, f"{self.api_domain}{path}", headers=headers, timeout=20, **kwargs)
            except requests.exceptions.RequestException as exc:
                raise ZohoError(f"Couldn't reach Zoho CRM ({exc.__class__.__name__}).")
            if resp.status_code == 204:
                return None  # No records
            try:
                body = resp.json()
            except ValueError:
                body = {}
            code = str(body.get("code", ""))
            if resp.status_code == 401 and code in ("INVALID_TOKEN", "AUTHENTICATION_FAILURE") and attempt == 0:
                continue  # Token expired early: refresh once and retry
            if resp.status_code >= 400:
                row = (body.get("data") or [{}])[0] if isinstance(body.get("data"), list) else {}
                code = code or str(row.get("code", ""))
                msg = body.get("message") or row.get("message") or code or f"HTTP {resp.status_code}"
                if code == "OAUTH_SCOPE_MISMATCH":
                    msg = "The Zoho token is missing a permission. Regenerate it with the scopes listed in the setup notes."
                raise ZohoError(f"Zoho CRM error: {msg}")
            return body
        raise ZohoError("Zoho CRM rejected the sign-in.")

    # ---------- reads ----------
    def fields(self, module: str) -> Dict[str, Dict[str, Any]]:
        body = self._request("GET", "/crm/v8/settings/fields", params={"module": module}) or {}
        return {f["api_name"]: f for f in body.get("fields", [])}

    @staticmethod
    def picklist(fields: Dict[str, Dict[str, Any]], api_name: str) -> List[str]:
        values = (fields.get(api_name) or {}).get("pick_list_values") or []
        out = []
        for v in values:
            for k in ("display_value", "actual_value"):
                if v.get(k) and v[k] != "-None-":
                    out.append(v[k])
        return out

    def org_domain(self) -> Optional[str]:
        try:
            body = self._request("GET", "/crm/v8/org") or {}
            org = (body.get("org") or [{}])[0]
            return org.get("domain_name")
        except ZohoError:
            return None

    def coql(self, query: str) -> List[Dict[str, Any]]:
        body = self._request("POST", "/crm/v8/coql", json={"select_query": query})
        return (body or {}).get("data") or []

    def create_lead(self, fields: Dict[str, Any]) -> str:
        body = self._request("POST", "/crm/v8/Leads", json={"data": [fields], "trigger": ["workflow"]})
        return str(self._row_result(body).get("id", ""))

    # ---------- writes (phase 2): send, fill blanks, notes ----------
    @staticmethod
    def _row_result(body: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        row = ((body or {}).get("data") or [{}])[0]
        if row.get("status") != "success":
            msg = row.get("message") or row.get("code") or "unknown error"
            raise ZohoError(f"Zoho CRM error: {msg}")
        return row.get("details") or {}

    def from_addresses(self) -> List[Dict[str, Any]]:
        body = self._request("GET", "/crm/v8/settings/emails/actions/from_addresses") or {}
        return [a for a in body.get("from_addresses", []) if a.get("email")]

    def upload_file(self, filename: str, data: bytes) -> str:
        body = self._request("POST", "/crm/v8/files", files={"file": (filename, data, "application/pdf")})
        return self._row_result(body)["id"]

    def send_mail(self, record_id: str, sender: Dict[str, Any], to_email: str, to_name: str,
                  subject: str, html: str, attachment_ids: Optional[List[str]] = None) -> str:
        mail: Dict[str, Any] = {
            "from": {"user_name": sender.get("user_name") or "", "email": sender["email"]},
            "to": [{"user_name": to_name or "", "email": to_email}],
            "subject": subject, "content": html, "mail_format": "html",
        }
        if sender.get("type") == "org_email":
            mail["org_email"] = True
        if attachment_ids:
            mail["attachments"] = [{"id": a} for a in attachment_ids]
        body = self._request("POST", f"/crm/v8/Leads/{record_id}/actions/send_mail", json={"data": [mail]})
        return self._row_result(body).get("message_id", "")

    def update_lead(self, record_id: str, fields: Dict[str, Any]) -> None:
        if fields:
            self._row_result(self._request("PUT", "/crm/v8/Leads", json={"data": [dict(fields, id=record_id)]}))

    def add_note(self, record_id: str, title: str, content: str) -> None:
        note = {"Note_Title": title, "Note_Content": content,
                "Parent_Id": {"module": {"api_name": "Leads"}, "id": record_id}}
        self._row_result(self._request("POST", f"/crm/v8/Leads/{record_id}/Notes", json={"data": [note]}))

    def record_url(self, record_id: str, module: str = "Leads") -> str:
        dom = st.session_state.get("zoho_org_domain")
        base = f"{self.crm_url}/crm/{dom}" if dom else f"{self.crm_url}/crm"
        return f"{base}/tab/{module}/{record_id}"

ZOHO = ZohoCRM()
ZOHO_STORE = SentLog("GITHUB_ZOHO_LEADS_PATH", "zoho_leads.json", ".zoho_leads.json")
UK_POSTCODE_RE = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$", re.I)


def zoho_lead_source() -> str:
    return _secret_value("ZOHO_LEAD_SOURCE", "Prospect Engine")


def get_zoho_store() -> Dict[str, Any]:
    if "zoho_store_data" not in st.session_state:
        st.session_state["zoho_store_data"] = ZOHO_STORE.load()
    return st.session_state["zoho_store_data"]


def save_zoho_store(changes: Dict[str, Dict[str, Any]]) -> None:
    try:
        st.session_state["zoho_store_data"] = ZOHO_STORE.apply(changes, f"Prospect Engine: {len(changes)} firms to Zoho")
    except Exception:
        st.session_state.setdefault("zoho_store_data", {}).update(changes)


def load_zoho_meta() -> Optional[str]:
    """Lead fields (for picklist checks) and the org's URL name, once per session."""
    if "pe_lead_fields" in st.session_state:
        return None
    try:
        st.session_state["pe_lead_fields"] = ZOHO.fields("Leads")
    except ZohoError as exc:
        return str(exc)
    st.session_state["zoho_org_domain"] = ZOHO.org_domain()
    return None


def zoho_on() -> bool:
    return ZOHO.configured and "pe_lead_fields" in st.session_state


def lead_source_ok() -> bool:
    return zoho_lead_source() in ZOHO.picklist(st.session_state.get("pe_lead_fields") or {}, "Lead_Source")


def _q(v: str) -> str:
    return "'" + (v or "").replace("\\", "").replace("'", "\\'") + "'"


def _either(conds: List[str]) -> str:
    """COQL wants OR conditions nested in pairs: ((a or b) or c)."""
    out = conds[0]
    for c in conds[1:]:
        out = f"({out} or {c})"
    return out


def _name_variants(lead: ScrapedLead) -> List[str]:
    names = [lead.company_name, friendly_company_name(lead.company_name), getattr(lead, "trading_name", None) or ""]
    base = friendly_company_name(lead.company_name)
    names += [f"{base} Ltd", f"{base} Limited", base.upper(), lead.company_name.title()]
    return list(dict.fromkeys(n.strip() for n in names if n and n.strip()))[:8]


def find_in_zoho(lead: ScrapedLead, email: str, phone: str) -> Optional[Dict[str, Any]]:
    """An existing Lead, or an existing customer (Account / Contact email), for this firm."""
    names = ", ".join(_q(n) for n in _name_variants(lead))
    conds = [f"Company in ({names})"]
    if email:
        conds.append(f"Email = {_q(email)}")
    if phone:
        variants = list(dict.fromkeys([phone, phone.replace(" ", "")]))
        conds.append(f"Phone in ({', '.join(_q(p) for p in variants)})")
    rows = ZOHO.coql(f"select Company, Lead_Status from Leads where {_either(conds)} limit 0, 5")
    if rows:
        return {"status": "existing", "id": str(rows[0].get("id")), "zoho_status": rows[0].get("Lead_Status") or ""}
    rows = ZOHO.coql(f"select Account_Name from Accounts where Account_Name in ({names}) limit 0, 5")
    if rows:
        return {"status": "customer", "id": str(rows[0].get("id")), "name": rows[0].get("Account_Name") or ""}
    if email:
        rows = ZOHO.coql(f"select Email, Account_Name from Contacts where Email = {_q(email)} limit 0, 5")
        acc = (rows[0].get("Account_Name") or {}) if rows else {}
        if rows and isinstance(acc, dict) and acc.get("id"):
            return {"status": "customer", "id": str(acc["id"]), "name": acc.get("name") or ""}
    return None


def _split_address(addr: str) -> Dict[str, str]:
    parts = [p.strip() for p in (addr or "").split(",") if p.strip()]
    out: Dict[str, str] = {}
    if parts and UK_POSTCODE_RE.match(parts[-1]):
        out["Zip_Code"] = parts.pop().upper()
    county = re.compile(r"(shire|^(west|east|north|south|greater) |midlands|merseyside|cornwall|devon|kent|essex|"
                        r"surrey|norfolk|suffolk|cumbria|durham|tyne and wear|london|wales|scotland|county)", re.I)
    if len(parts) >= 3 and county.search(parts[-1]):
        out["State"] = parts.pop()
    if len(parts) >= 2:
        out["City"] = parts.pop()
    if parts:
        if len(parts) > 1 and re.fullmatch(r"[\dA-Za-z\-/]{1,6}", parts[0]) and any(ch.isdigit() for ch in parts[0]):
            parts = [f"{parts[0]} {parts[1]}"] + parts[2:]  # "14, Bridge Street" -> "14 Bridge Street"
        out["Street"] = ", ".join(parts)
    return out


def zoho_lead_fields(item: Dict[str, Any], cn: str) -> Dict[str, Any]:
    lead: ScrapedLead = item["lead"]
    lf = st.session_state.get("pe_lead_fields") or {}
    contact, role = infer_contact_name_and_role(lead, item["vertical"])
    person = (getattr(lead, "contact_name", None) or "").strip()
    if not person:
        officer = pick_decision_maker(lead.officers)
        person = display_officer_name(officer.name) if officer else ""
        role = officer.role if officer else ""
    fields: Dict[str, Any] = {"Company": lead_display_name(lead)}
    if person and len(person.split()) >= 2:
        fields["First_Name"], fields["Last_Name"] = person.split()[0], person.split()[-1]
        if role:
            fields["Designation"] = role
    else:
        fields["Last_Name"] = lead_display_name(lead)  # Zoho needs a Last Name
    email = (item.get("to") or (lead.emails_found[0] if lead.emails_found else "")).strip()
    if email:
        fields["Email"] = email
    if lead.phones_found:
        fields["Phone"] = lead.phones_found[0]
    if lead.website_url and lead.website_confidence in VERIFIED_WEBSITE:
        fields["Website"] = lead.website_url
    fields.update(_split_address(lead.registered_address or ""))
    industries = ZOHO.picklist(lf, "Industry")
    match = next((v for v in industries if v.lower() == item["vertical"].lower()), None)
    if match:
        fields["Industry"] = match
    if lead_source_ok():
        fields["Lead_Source"] = zoho_lead_source()
    statuses = ZOHO.picklist(lf, "Lead_Status")
    emailed = cn in get_sent_log()
    want = "Attempted to Contact" if emailed else "Not Contacted"
    if want in statuses:
        fields["Lead_Status"] = want
    directors = [display_officer_name(o.name) for o in lead.officers if o.raw_role in DECISION_MAKER_ROLES][:4]
    desc = [
        f"Found by Prospect Engine on {now_uk().strftime('%d %b %Y')} (source: {zoho_lead_source()}).",
        f"Legal name: {lead.company_name}" + (f" · Company number: {lead.company_number}" if lead.company_number else ""),
        f"Sector pitched: {item['vertical']}" + (f" · SIC: {', '.join(lead.sic_codes[:3])}" if lead.sic_codes else ""),
    ]
    if directors:
        desc.append("Directors: " + ", ".join(directors))
    if lead.website_url:
        desc.append(f"Website: {lead.website_url} ({lead.website_confidence or 'unverified'} match)")
    others = [e for e in lead.emails_found if e != email][:4]
    if others:
        desc.append("Other emails found: " + ", ".join(others))
    if len(lead.phones_found) > 1:
        desc.append("Other numbers: " + ", ".join(lead.phones_found[1:4]))
    if getattr(lead, "linkedin_url", None):
        desc.append(f"LinkedIn: {lead.linkedin_url}")
    desc.append("Details from Companies House, the firm's own website and Google Maps.")
    fields["Description"] = "\n".join(desc)
    return fields


def push_to_zoho_leads(cns: List[str]) -> Dict[str, List[str]]:
    """Adds each firm to Zoho as a Lead unless it's already there (as a lead or a customer)."""
    queue = st.session_state.get("queue", {})
    store = get_zoho_store()
    todo = [cn for cn in cns if cn in queue and cn not in store]
    summary: Dict[str, List[str]] = {"created": [], "existing": [], "customer": [], "error": []}
    if not todo:
        return summary
    stamp = now_uk().isoformat(timespec="seconds")
    who = get_sender().get("name", "")

    def _one(cn: str) -> Tuple[str, Dict[str, Any]]:
        item = queue[cn]
        lead: ScrapedLead = item["lead"]
        email = (item.get("to") or (lead.emails_found[0] if lead.emails_found else "")).strip()
        phone = lead.phones_found[0] if lead.phones_found else ""
        try:
            hit = find_in_zoho(lead, email, phone)
            if hit:
                return cn, dict(hit, at=stamp, by=who, firm=lead_display_name(lead))
            lid = ZOHO.create_lead(zoho_lead_fields(item, cn))
            rec = get_sent_log().get(cn)
            if rec:  # Already emailed from here (Outlook draft): put that on the lead's history
                ZOHO.add_note(lid, "Prospect Engine: pitch emailed",
                              f"Pitch emailed on {fmt_when(rec.get('sent_at', ''))} by {rec.get('sent_by') or 'the team'}"
                              f" to {rec.get('to') or 'unknown'}.\nSubject: {rec.get('subject', '')}")
            return cn, {"status": "created", "id": lid, "at": stamp, "by": who, "firm": lead_display_name(lead)}
        except ZohoError as exc:
            return cn, {"status": "error", "error": str(exc), "firm": lead_display_name(lead)}

    changes: Dict[str, Dict[str, Any]] = {}
    progress = st.progress(0.0, text="Checking Zoho for duplicates…")
    for n, cn_ in enumerate(todo, start=1):
        progress.progress(n / len(todo), text=f"Adding to Zoho {n} of {len(todo)} · {lead_display_name(queue[cn_]['lead'])}")
        cn, rec = _one(cn_)
        if rec["status"] == "error" and "permission" in rec["error"].lower():
            st.session_state["zoho_needs_scope"] = True  # Same for every firm, so stop and ask to reconnect
            summary["error"].append("permission")
            break
        summary[rec["status"]].append(rec.get("firm", cn) if rec["status"] != "error" else f"{rec['firm']}: {rec['error']}")
        if rec["status"] != "error":
            changes[cn] = rec
    progress.empty()
    if changes:
        save_zoho_store(changes)
    bump_queue_editor()
    return summary


def zoho_summary_text(s: Dict[str, List[str]]) -> Optional[str]:
    bits = []
    if s["created"]:
        bits.append(f"{len(s['created'])} added as new leads")
    if s["existing"]:
        bits.append(f"{len(s['existing'])} already in Zoho, so not duplicated")
    if s["customer"]:
        bits.append(f"{len(s['customer'])} already a customer: " + ", ".join(s["customer"][:3]))
    return ("Zoho: " + " · ".join(bits) + ".") if bits else None


def zoho_label(cn: str) -> str:
    rec = get_zoho_store().get(cn)
    if not rec:
        return ""
    return {"created": "✓ New lead", "existing": "• Already a lead", "customer": "⚠ Customer"}.get(rec.get("status"), "")


def zoho_sent_today(log: Dict[str, Any]) -> int:
    today = now_uk().date().isoformat()
    return sum(1 for r in log.values() if r.get("via") == "zoho" and str(r.get("sent_at", "")).startswith(today))


def zoho_senders() -> Tuple[List[Dict[str, Any]], Optional[str]]:
    if "zoho_from" not in st.session_state:
        try:
            st.session_state["zoho_from"] = ZOHO.from_addresses()
        except ZohoError as exc:
            return [], str(exc)
    return st.session_state["zoho_from"], None


def send_via_zoho(cns: List[str], sender: Optional[Dict[str, Any]], origin: str = "panel") -> None:
    """Makes sure each firm is a Zoho lead, then sends its pitch from Zoho, moves the status on and adds a note."""
    queue = st.session_state.get("queue", {})
    push_to_zoho_leads(cns)
    store = get_zoho_store()
    done, problems = [], []
    sent_changes: Dict[str, Dict[str, Any]] = {}
    who = get_sender().get("name") or "Prospect Engine"
    stamp = now_uk().strftime("%d %b %Y %H:%M")
    statuses = ZOHO.picklist(st.session_state.get("pe_lead_fields") or {}, "Lead_Status")
    progress = st.progress(0.0, text="Sending through Zoho…")
    for n, cn in enumerate(cns, start=1):
        item = queue.get(cn)
        if not item:
            continue
        lead: ScrapedLead = item["lead"]
        name = lead_display_name(lead)
        progress.progress(n / len(cns), text=f"Sending {n} of {len(cns)} · {name}")
        rec = store.get(cn) or {}
        if rec.get("status") == "customer":
            problems.append(f"{name}: already a customer in Zoho, so no new-business pitch was sent")
            continue
        if not rec.get("id"):
            problems.append(f"{name}: couldn't add it to Zoho, so it wasn't sent")
            continue
        ensure_draft(item)
        to = (item.get("to") or "").strip()
        if not to or not clean_email(to) or not sender:
            problems.append(f"{name}: no valid email address" if sender else f"{name}: no From address in Zoho")
            continue
        contact = infer_contact_name_and_role(lead, item["vertical"])[0]
        try:
            att = []
            if st.session_state["opt_attach"]:
                pdf = create_sector_overview_pdf(lead, item["vertical"])
                att = [ZOHO.upload_file(f"Fortlox_Security_overview_{draft_filename_part(lead.company_name)}.pdf", pdf)]
            ZOHO.send_mail(rec["id"], sender, to, "" if contact in ("Team", "there") else contact,
                           item["subject"], _email_body_html(item["body"], item["subject"]), att)
        except ZohoError as exc:
            problems.append(f"{name}: not sent. {exc}")
            continue
        try:
            if "Attempted to Contact" in statuses:
                ZOHO.update_lead(rec["id"], {"Lead_Status": "Attempted to Contact"})
            ZOHO.add_note(rec["id"], "Prospect Engine: pitch emailed",
                          f"Emailed by {who} via Prospect Engine on {stamp}.\nTo: {to}\nSubject: {item['subject']}\n"
                          f"Pitch: {item['vertical']}" + (" (overview PDF attached)" if st.session_state["opt_attach"] else ""))
        except ZohoError as exc:
            problems.append(f"{name}: sent, but the lead wasn't updated. {exc}")
        sent_changes[cn] = dict(sent_record(item), via="zoho", status="Emailed via Zoho",
                                from_address=sender.get("email", ""))
        done.append(name)
    progress.empty()
    if sent_changes:
        record_sent(sent_changes)
    st.session_state["zoho_push_result"] = {"done": done, "problems": problems, "origin": origin}


def show_zoho_push_result(origin: str) -> None:
    res = st.session_state.get("zoho_push_result")
    if not res or res.get("origin") != origin:
        return
    st.session_state.pop("zoho_push_result", None)
    if res["done"]:
        st.success(f"{len(res['done'])} sent via Zoho: " + ", ".join(res["done"][:6]) + ("…" if len(res["done"]) > 6 else ""))
    for p_ in res["problems"]:
        st.warning(p_)


def render_zoho_setup() -> None:
    render_html(
        '<div class="pe-panel"><div class="h">One-off Zoho setup</div>'
        '<div style="font-size:.84rem;line-height:1.55;color:var(--muted)">'
        "<b>1.</b> In <b>api-console.zoho.eu</b>, open your Self Client and go to <b>Generate Code</b>.<br>"
        "<b>2.</b> Paste the scope below, pick <b>10 minutes</b> and click <b>Create</b>.<br>"
        "<b>3.</b> Paste the code here and click Connect. Be quick: codes expire.</div></div>"
    )
    st.code(ZOHO_SCOPE, language=None)
    with st.form("zoho_setup", border=False):
        setup_code = st.text_input("Code from Zoho", type="password", placeholder="1000.xxxxxxxx…")
        setup_go = st.form_submit_button("Connect Zoho", type="primary", **FULL_WIDTH)
    if setup_go:
        if not setup_code.strip():
            st.warning("Paste the code from Zoho first.")
        else:
            with st.spinner("Asking Zoho for a permanent key…"):
                st.session_state["zoho_setup_result"] = ZOHO.exchange_code(setup_code)
    result = st.session_state.get("zoho_setup_result") or {}
    if result.get("error"):
        st.error(result["error"])
    elif result.get("refresh_token"):
        st.success("Connected. Last step:")
        st.code(f'ZOHO_REFRESH_TOKEN = "{result["refresh_token"]}"', language=None)
        st.caption("Copy that line into this app's Streamlit Secrets, save, then reboot. Don't share it in emails or chats.")


def render_leads_table(df: pd.DataFrame, key: str):
    """Selectable company table with tidy columns. Works on old and new Streamlit versions."""
    column_config = {
        "Company Name": st.column_config.TextColumn("Company Name", width=200),
        "Contacted": st.column_config.TextColumn("Contacted", width=78, help="Already emailed (from the sent log)"),
        "Company Number": st.column_config.TextColumn("Co. #", width=74),
        "Incorporated": st.column_config.DateColumn("Since", format="MMM YYYY", width=78),
        "Town": st.column_config.TextColumn("Town", width=95),
        "Has": st.column_config.TextColumn("Listed", width=70, help="🌐 website · 📞 phone · ✉️ email on the map listing"),
        "Map": st.column_config.LinkColumn("Map", display_text="View ↗", width=58, help="Opens the listing on OpenStreetMap"),
        "Companies House": st.column_config.LinkColumn(
            "Registry", display_text="View ↗", width=62,
            help="Opens the company's Companies House page in a new tab",
        ),
    }
    column_order = [c for c in column_config if c in df.columns]
    if "Company Number" in df.columns and df["Company Number"].astype(str).str.startswith("OSM-").all():
        column_order = [c for c in column_order if c != "Company Number"]  # Map finds have no company number
    table_height = min(38 + 35 * len(df), 420)  # Grows with rows, scrolls after ~11
    common = dict(
        hide_index=True,
        selection_mode="multi-row",
        on_select="rerun",
        column_config=column_config,
        column_order=column_order,
        height=table_height,
        key=key,
    )
    try:
        return st.dataframe(df, width="stretch", **common)  # Streamlit 1.46+
    except Exception:
        return st.dataframe(df, use_container_width=True, **common)  # Older Streamlit


st.set_page_config(
    page_title=f"{APP_NAME} · Prospect Discovery & Dossiers",
    page_icon="🎯",
    layout="wide",
)
inject_css()

for _k, _v in {"stat_searches": 0, "stat_firms": 0, "stat_dossiers": 0}.items():
    st.session_state.setdefault(_k, 0)

hero_slot = st.empty()  # Filled at the end so the progress stepper reflects this run's actions
MAX_BATCH = 25
SENT_LOG = SentLog()
for _k, _v in {"opt_branded": True, "opt_attach": True, "opt_switch": True, "queue_editor_ver": 0, "sent_log_ver": 0}.items():
    st.session_state.setdefault(_k, _v)


def get_sent_log() -> Dict[str, Any]:
    """Loaded once per session; refreshed after every change (and by the sidebar Refresh button)."""
    if "sent_log_data" not in st.session_state:
        st.session_state["sent_log_data"] = SENT_LOG.load()
    return st.session_state["sent_log_data"]


def bump_queue_editor() -> None:
    st.session_state["queue_editor_ver"] = st.session_state.get("queue_editor_ver", 0) + 1


def record_sent(changes: Dict[str, Optional[Dict[str, Any]]]) -> None:
    """Saves sent ticks/unticks to the permanent log and refreshes every view of it."""
    local = dict(get_sent_log())
    try:
        n_on = sum(1 for v in changes.values() if v)
        latest = SENT_LOG.apply(changes, f"Fortlox: {n_on} marked sent, {len(changes) - n_on} unmarked")
        st.session_state["sent_log_data"] = latest
    except Exception as exc:
        for key, rec in changes.items():  # Keep this session correct even if saving failed
            if rec is None:
                local.pop(key, None)
            else:
                local[key] = rec
        st.session_state["sent_log_data"] = local
        st.session_state["sent_log_error"] = str(exc) if isinstance(exc, RuntimeError) else "Couldn't save the sent log."
    st.session_state["sent_log_ver"] = st.session_state.get("sent_log_ver", 0) + 1
    bump_queue_editor()


# ------------------------------------------------------------------
# CALL LIST (permanent, shared telemarketing database)
# ------------------------------------------------------------------
CALL_STORE = SentLog("GITHUB_CALLS_PATH", "call_list.json", ".call_list.json")

CALL_OPEN = ["New", "No answer", "Call back"]
CALL_DONE = ["Interested", "Not interested", "Wrong number", "Do not call"]
CALL_STATUSES = CALL_OPEN + CALL_DONE
CALL_STATUS_TONE = {"New": "accent", "No answer": "muted", "Call back": "warn", "Interested": "good",
                    "Not interested": "", "Wrong number": "bad", "Do not call": "bad"}
VERIFIED_WEBSITE = ("High", "Medium", "Manual")


def get_call_list() -> Dict[str, Any]:
    if "call_list_data" not in st.session_state:
        st.session_state["call_list_data"] = CALL_STORE.load()
    return st.session_state["call_list_data"]


def save_calls(changes: Dict[str, Optional[Dict[str, Any]]], message: str) -> None:
    """Writes call-list changes to the permanent store (re-reads first so colleagues' edits survive)."""
    local = dict(get_call_list())
    try:
        st.session_state["call_list_data"] = CALL_STORE.apply(changes, f"Fortlox calls: {message}")
    except Exception as exc:
        for key, rec in changes.items():
            if rec is None:
                local.pop(key, None)
            else:
                local[key] = rec
        st.session_state["call_list_data"] = local
        st.session_state["call_list_error"] = str(exc) if isinstance(exc, RuntimeError) else "Couldn't save the call list."
    st.session_state["call_ver"] = st.session_state.get("call_ver", 0) + 1


def call_record_from_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Only what a caller needs: who, which number, and the website if we've verified it."""
    lead: ScrapedLead = item["lead"]
    contact, role = infer_contact_name_and_role(lead, item["vertical"])
    website = lead.website_url if (lead.website_url and lead.website_confidence in VERIFIED_WEBSITE) else ""
    return {
        "company_number": lead.company_number or "",
        "firm": lead_display_name(lead),
        "legal_name": lead.company_name,
        "contact": contact,
        "role": role,
        "directors": [display_officer_name(o.name) for o in lead.officers if o.raw_role in DECISION_MAKER_ROLES][:3],
        "phone": (lead.phones_found or [""])[0],
        "other_phones": lead.phones_found[1:3],
        "website": website,
        "linkedin": getattr(lead, "linkedin_url", None) or "",
        "sector": item["vertical"],
        "address": lead.registered_address or "",
        "added_at": now_uk().isoformat(timespec="seconds"),
        "added_by": get_sender().get("name", ""),
        "status": "New",
        "notes": "",
        "callback": "",
        "attempts": 0,
        "last_called": "",
        "last_called_by": "",
        "history": [],
    }


def call_queue(calls: Dict[str, Any]) -> List[str]:
    """Order to work through: callbacks that are due, then new firms, then retries (least recent first)."""
    now = now_uk().replace(tzinfo=None)
    due, new, retry = [], [], []
    for cn, r in calls.items():
        status = r.get("status", "New")
        if status == "Call back":
            try:
                when = datetime.fromisoformat(r.get("callback") or "")
                when = when.replace(tzinfo=None)
            except ValueError:
                when = now
            if when <= now:
                due.append((when, cn))
        elif status == "New":
            new.append((r.get("added_at", ""), cn))
        elif status == "No answer":
            retry.append((r.get("last_called", ""), cn))
    return [c for _, c in sorted(due)] + [c for _, c in sorted(new)] + [c for _, c in sorted(retry)]


def fmt_when(iso: str, with_time: bool = True) -> str:
    try:
        d = datetime.fromisoformat(iso)
    except (TypeError, ValueError):
        return ""
    return d.strftime("%d %b %H:%M" if with_time else "%d %b").lstrip("0")


# ------------------------------------------------------------------
# CONFIRMED CONTACTS (found by a person, e.g. on LinkedIn; saved permanently)
# ------------------------------------------------------------------
CONTACTS_STORE = SentLog("GITHUB_CONTACTS_PATH", "contacts.json", ".contacts.json")


def get_contacts() -> Dict[str, Any]:
    if "contacts_data" not in st.session_state:
        st.session_state["contacts_data"] = CONTACTS_STORE.load()
    return st.session_state["contacts_data"]


def apply_contact(item: Dict[str, Any], rec: Dict[str, Any]) -> None:
    """Puts a confirmed contact onto a queued firm: greeting, role, LinkedIn and (if given) email."""
    lead: ScrapedLead = item["lead"]
    lead.contact_name = (rec.get("name") or "").strip() or None
    lead.contact_role = (rec.get("role") or "").strip() or None
    lead.linkedin_url = (rec.get("linkedin") or "").strip() or None
    email = clean_email(rec.get("email") or "") if rec.get("email") else None
    lead.contact_email = email
    if email:
        if email not in lead.emails_found:
            lead.emails_found = [email] + list(lead.emails_found)
        if item.get("to") != email:
            item["to"] = email
            item["to_ver"] = item.get("to_ver", 0) + 1
    item["sig"] = None  # Rebuild the draft with the new greeting


def save_contact(cn: str, name: str = "", role: str = "", linkedin: str = "", email: str = "") -> Optional[str]:
    """Saves a confirmed contact permanently and applies it. Returns an error message or None."""
    email = (email or "").strip()
    if email and not clean_email(email):
        return f"'{email}' doesn't look like a valid email address."
    current = dict(get_contacts().get(cn) or {})
    rec = {
        "name": (name or "").strip() or current.get("name", ""),
        "role": (role or "").strip() or current.get("role", ""),
        "linkedin": (linkedin or "").strip() or current.get("linkedin", ""),
        "email": clean_email(email) if email else current.get("email", ""),
        "updated_at": now_uk().isoformat(timespec="seconds"),
        "updated_by": get_sender().get("name", ""),
    }
    item = st.session_state.get("queue", {}).get(cn)
    if item:
        rec["firm"] = item["lead"].company_name
    try:
        st.session_state["contacts_data"] = CONTACTS_STORE.apply({cn: rec}, "contact updated")
    except Exception:
        st.session_state.setdefault("contacts_data", {})[cn] = rec
    if item:
        apply_contact(item, rec)
    bump_queue_editor()
    return None


def linkedin_people_url(lead: ScrapedLead) -> str:
    officer = pick_decision_maker(lead.officers)
    person = display_officer_name(officer.name) if officer else "director"
    return "https://www.linkedin.com/search/results/people/?keywords=" + quote(f"{person} {lead_display_name(lead)}")


def linkedin_company_url(lead: ScrapedLead) -> str:
    return "https://www.linkedin.com/search/results/companies/?keywords=" + quote(lead_display_name(lead))


def suggest_email(full_name: str, lead: ScrapedLead) -> Optional[str]:
    """If the firm's own website shows how staff emails are formed, apply that to a new name.
    e.g. site lists sarah.jones@firm.co.uk -> 'Mark Hughes' becomes mark.hughes@firm.co.uk. Unverified."""
    words = [re.sub(r"[^a-z]", "", w.lower()) for w in (full_name or "").split()]
    words = [w for w in words if w]
    if not words or not lead.website_url or lead.website_confidence not in ("High", "Medium", "Manual"):
        return None
    site = domain_of(lead.website_url) or ""
    own = [e for e in lead.emails_found if e.split("@", 1)[1] == site or e.split("@", 1)[1].endswith("." + site)]
    first, last = words[0], (words[-1] if len(words) > 1 else "")
    for e in own:
        local, dom = e.split("@", 1)
        if re.fullmatch(r"[a-z]+\.[a-z]+", local) and last:
            return f"{first}.{last}@{dom}"
    for e in own:
        local, dom = e.split("@", 1)
        if first_name_from_email(e) and re.fullmatch(r"[a-z]+", local):
            return f"{first}@{dom}"
    return None


def sent_record(item: Dict[str, Any]) -> Dict[str, Any]:
    lead: ScrapedLead = item["lead"]
    return {
        "company_name": lead.company_name,
        "to": item.get("to", ""),
        "contact": infer_contact_name_and_role(lead, item["vertical"])[0],
        "vertical": item["vertical"],
        "subject": item.get("subject", ""),
        "sent_at": now_uk().isoformat(timespec="seconds"),
        "sent_by": get_sender().get("name", ""),
        "status": "Emailed" if item.get("to") else "Handled",
    }


# ------------------------------------------------------------------
# SAVED FIRMS (every enriched firm, kept permanently in the GitHub repo)
# ------------------------------------------------------------------
SAVED_STORE = SentLog("GITHUB_SAVED_PATH", "saved_firms.json", ".saved_firms.json", compact=True)
_SAVED_FIELDS = ("company_name", "company_number", "source_id", "sic_codes", "sector_guess", "registered_address",
                 "website_url", "phones_found", "emails_found", "trading_name", "website_confidence",
                 "site_meta_description", "discovery_notes", "other_emails")


def get_saved() -> Dict[str, Any]:
    if "saved_data" not in st.session_state:
        st.session_state["saved_data"] = SAVED_STORE.load()
    return st.session_state["saved_data"]


def lead_key(lead: ScrapedLead) -> str:
    return lead.source_id or lead.company_number or lead.company_name


def _lead_to_saved(lead: ScrapedLead) -> Dict[str, Any]:
    """Just what's needed to rebuild the firm later (keeps the GitHub file small)."""
    d = lead.model_dump() if hasattr(lead, "model_dump") else lead.dict()
    out = {k: d.get(k) for k in _SAVED_FIELDS}
    out["phones_found"] = list(out.get("phones_found") or [])[:5]
    out["emails_found"] = list(out.get("emails_found") or [])[:6]
    out["other_emails"] = list(out.get("other_emails") or [])[:3]
    out["discovery_notes"] = list(out.get("discovery_notes") or [])[:6]
    out["site_meta_description"] = (out.get("site_meta_description") or "")[:300] or None
    out["officers"] = [{k: o.get(k) for k in ("name", "role", "raw_role", "appointed_on", "is_owner")}
                       for o in (d.get("officers") or [])[:8]]
    return out


def lead_from_saved(rec: Dict[str, Any]) -> ScrapedLead:
    data = dict(rec.get("lead") or {})
    data.setdefault("company_name", rec.get("firm") or "Unknown firm")
    return ScrapedLead(**{k: v for k, v in data.items() if v is not None})


def save_enriched(leads: List[ScrapedLead], vertical: str) -> None:
    """Saves (or refreshes) enriched firms in the permanent store. One GitHub commit per batch."""
    if not leads:
        return
    existing = get_saved()
    who = get_sender().get("name", "")
    stamp = now_uk().isoformat(timespec="seconds")
    changes: Dict[str, Optional[Dict[str, Any]]] = {}
    for lead in leads:
        cn = lead_key(lead)
        prev = existing.get(cn) or {}
        changes[cn] = {
            "firm": lead_display_name(lead), "vertical": vertical, "lead": _lead_to_saved(lead),
            "saved_at": prev.get("saved_at") or stamp, "saved_by": prev.get("saved_by") or who,
            "updated_at": stamp,
        }
    update_saved(changes, f"{len(changes)} firm{'s' if len(changes) != 1 else ''} saved")


def update_saved(changes: Dict[str, Optional[Dict[str, Any]]], message: str) -> None:
    local = dict(get_saved())
    try:
        st.session_state["saved_data"] = SAVED_STORE.apply(changes, f"Fortlox saved firms: {message}")
    except Exception as exc:
        for key, rec in changes.items():
            if rec is None:
                local.pop(key, None)
            else:
                local[key] = rec
        st.session_state["saved_data"] = local
        st.session_state["saved_error"] = str(exc) if isinstance(exc, RuntimeError) else "Couldn't save the firms."
    st.session_state["saved_ver"] = st.session_state.get("saved_ver", 0) + 1


def add_to_queue(lead: ScrapedLead, vertical: str) -> None:
    queue = st.session_state.setdefault("queue", {})
    order = st.session_state.setdefault("queue_order", [])
    cn = lead.source_id or lead.company_number or lead.company_name
    contact, _ = infer_contact_name_and_role(lead, vertical)
    queue[cn] = {
        "lead": lead,
        "vertical": vertical,
        "include": True,
        "to": pick_primary_email(lead, contact) or "",
        "to_ver": queue.get(cn, {}).get("to_ver", 0) + 1,
        "subject": None,
        "body": None,
        "sig": None,
    }
    if cn not in order:
        order.append(cn)
    stored = get_contacts().get(cn)
    if stored:
        apply_contact(queue[cn], stored)
    bump_queue_editor()


def run_enrichment(
    rows: List[Dict[str, Any]],
    vertical: str,
    manual_websites: Optional[Dict[str, str]] = None,
) -> None:
    """Enriches firms 4 at a time with a progress bar and adds them to the review queue.
    rows need 'Company Number' and 'Company Name'. manual_websites: {company_number: url}."""
    manual_websites = manual_websites or {}
    progress = st.progress(0.0, text="Starting enrichment…")

    sra_data = sra_register() if vertical in SRA_SECTORS and _secret_value("SRA_API_KEY") else []

    def _enrich(row: Dict[str, Any]) -> ScrapedLead:
        if str(row.get("Company Number", "")).startswith("OSM-"):
            return enrich_osm_business(row, vertical, ch_api_key,
                                       manual_website=manual_websites.get(row["Company Number"]) or None)
        enricher = LeadEnricher(ch_api_key=ch_api_key)
        enricher.sra_data = sra_data
        return enricher.enrich_selected_company(
            company_number=row["Company Number"],
            sector_name=vertical,
            manual_website=manual_websites.get(row["Company Number"]) or None,
        )

    results: Dict[str, ScrapedLead] = {}
    failures: List[str] = []
    with ThreadPoolExecutor(max_workers=min(4, len(rows))) as pool:
        futures = {pool.submit(_enrich, row): row for row in rows}
        for done, fut in enumerate(as_completed(futures), start=1):
            row = futures[fut]
            try:
                results[row["Company Number"]] = fut.result()
            except Exception:
                failures.append(friendly_company_name(row["Company Name"]))
            progress.progress(
                done / len(rows),
                text=f"Enriched {done} of {len(rows)} · {friendly_company_name(row['Company Name'])}",
            )
    progress.empty()

    first_cn = None
    for row in rows:  # Keep the table's order in the queue
        cn = row["Company Number"]
        if cn in results:
            add_to_queue(results[cn], vertical)
            first_cn = first_cn or cn
    if first_cn:
        st.session_state["current_cn"] = first_cn
        st.session_state["current_cn_select"] = first_cn
    st.session_state["stat_dossiers"] += len(results)
    save_enriched(list(results.values()), vertical)  # Kept permanently under Saved firms
    if results and zoho_on() and st.session_state.get("zoho_auto", True):
        summary = push_to_zoho_leads(list(results))
        if zoho_summary_text(summary):
            st.info(zoho_summary_text(summary))
        if "permission" in summary["error"]:
            st.warning("Zoho: the key in Secrets doesn't have all the permissions this app needs, so no firms were added."
                       " Open **Reconnect Zoho** in the sidebar to get this app its own key, then use **Add firms not yet in Zoho**"
                       " under Review & send.")
        else:
            for err in summary["error"]:
                st.warning("Zoho: couldn't add " + err)
    if failures:
        st.warning("Couldn't enrich: " + ", ".join(failures))
    if len(rows) > 1 and results:
        with_email = sum(1 for cn in results if results[cn].emails_found)
        st.success(
            f"{len(results)} firms enriched: {with_email} with an email address,"
            f" {len(results) - with_email} without. See Review & send below."
        )


def ensure_draft(item: Dict[str, Any]) -> None:
    """(Re)builds a firm's subject/body when first needed or when options/signature change."""
    sig = (item["vertical"], st.session_state["opt_attach"], st.session_state["opt_switch"],
           tuple(sorted(get_sender().items())),
           getattr(item["lead"], "contact_name", None), getattr(item["lead"], "contact_role", None))
    if item.get("sig") != sig or item.get("body") is None:
        item["subject"] = build_email_subject(item["lead"], item["vertical"])
        item["body"] = build_email_pitch(
            item["lead"], item["vertical"],
            include_attachment_line=st.session_state["opt_attach"],
            include_switchover=st.session_state["opt_switch"],
        )
        item["sig"] = sig



try:
    secret_ch_key = st.secrets.get("COMPANIES_HOUSE_KEY", "")
except Exception:
    secret_ch_key = ""


def columns(spec, **kwargs):
    """st.columns with bottom alignment where supported (Streamlit 1.36+)."""
    try:
        return st.columns(spec, vertical_alignment="bottom", **kwargs)
    except TypeError:
        return st.columns(spec, **kwargs)


# ---------------- Sidebar ----------------
with st.sidebar:
    render_html(
        f'<div class="pe-brand"><div class="pe-logo">{icon("target", 22, 2.2)}</div>'
        f'<div><div class="n">{APP_NAME}</div><div class="s">{APP_TAGLINE}</div></div></div>'
    )
    # ---- Workspace switch (bookmarkable: ?view=calls) ----
    _VIEWS = {"prospect": "🎯  Prospecting", "saved": "🗂️  Saved firms", "calls": "📞  Call list & callbacks"}
    if "w_view" not in st.session_state:
        st.session_state["w_view"] = st.query_params.get("view") if st.query_params.get("view") in _VIEWS else "prospect"
    if st.session_state.get("goto_view") in _VIEWS:  # Set by buttons on other pages (before the switch is drawn)
        st.session_state["w_view"] = st.session_state.pop("goto_view")
    _calls_side = get_call_list()
    _order_side = call_queue(_calls_side)
    _n_to_call = len(_order_side)
    _n_due = sum(1 for c in _order_side if _calls_side[c].get("status") == "Call back")
    st.session_state["view"] = st.radio(
        "Workspace", list(_VIEWS), key="w_view", label_visibility="collapsed", format_func=_VIEWS.get,
    )  # Labels stay fixed: a changing label would make Streamlit reset the switch
    _side_notes = []
    if _n_due:
        _side_notes.append(f'<b style="color:#FBBF24">{_n_due} callback{"s" if _n_due != 1 else ""} due now</b>')
    if _n_to_call:
        _side_notes.append(f'{_n_to_call} {"firm" if _n_to_call == 1 else "firms"} waiting on the call list')
    if get_saved():
        _side_notes.append(f'{len(get_saved())} firms saved')
    if _side_notes:
        render_html('<div style="font-size:.76rem;color:var(--muted);margin:-2px 0 6px 4px;line-height:1.6">'
                    + "<br>".join(_side_notes) + "</div>")
    if st.query_params.get("view", "prospect") != st.session_state["view"]:
        st.query_params["view"] = st.session_state["view"]
    if True:
        with st.container(key="logo-card"):
            st.image(logo_image(), **({"width": "stretch"} if "width" in FULL_WIDTH else {"use_container_width": True}))
    render_html('<div class="pe-side-h">Sources (all free)</div>')
    ch_api_key = secret_ch_key  # Optional: a free Companies House key in Secrets adds registered companies & directors
    get_sent_log()
    log_state = ('off">Error' if (SENT_LOG.last_error or st.session_state.get("sent_log_error"))
                 else 'ok">Saved' if SENT_LOG.backend == "github" else 'idle">This session')
    render_html(
        '<div class="pe-status">OpenStreetMap finder<span class="st ok">Ready</span></div>'
        '<div class="pe-status">Website &amp; email finder<span class="st ok">Ready</span></div>'
        '<div class="pe-status">Email domain checks<span class="st ok">Ready</span></div>'
        '<div class="pe-status">Pitch PDFs<span class="st ok">Ready</span></div>'
        f'<div class="pe-status">Companies House<span class="st {"ok" if ch_api_key else "idle"}">{"Connected" if ch_api_key else "Optional"}</span></div>'
        f'<div class="pe-status">Saved firms &amp; call list<span class="st {log_state}</span></div>'
    )
    if SENT_LOG.last_error or st.session_state.get("sent_log_error"):
        st.caption("⚠️ " + (st.session_state.pop("sent_log_error", None) or SENT_LOG.last_error or ""))
    elif SENT_LOG.backend == "local":
        st.caption("Saved firms, call list and ticks last until the app restarts. Add GITHUB_TOKEN and GITHUB_REPO"
                   " in Secrets to keep them permanently.")
    st.caption(f"🛡️ TPS disclaimer accepted {st.session_state.get('tps_ack_at', '')}. "
               "Check every number against TPS/CTPS before contacting.")
    if st.button("↻ Refresh shared data", **FULL_WIDTH, help="Pick up ticks made by colleagues since you opened the app."):
        st.session_state.pop("sent_log_data", None)
        st.session_state.pop("call_list_data", None)
        st.session_state.pop("contacts_data", None)
        st.session_state.pop("saved_data", None)
        for _k in ("zoho_store_data", "zoho_from", "pe_lead_fields"):
            st.session_state.pop(_k, None)
        st.session_state["call_ver"] = st.session_state.get("call_ver", 0) + 1
        st.session_state["sent_log_ver"] = st.session_state.get("sent_log_ver", 0) + 1
        bump_queue_editor()
        st.rerun()
    render_html('<div class="pe-side-h">This session</div>')
    sidebar_stats_slot = st.empty()
    render_html('<div class="pe-side-h">Your email signature</div>')
    with st.expander("Signature details", expanded=not st.session_state.get("sender_profile", {}).get("name")):
        def _secret(key: str, default: str) -> str:
            try:
                return str(st.secrets.get(key, default))
            except Exception:
                return default
        prof = st.session_state.setdefault("sender_profile", {
            "name": _secret("SENDER_NAME", SENDER_DEFAULTS["name"]),
            "title": _secret("SENDER_TITLE", SENDER_DEFAULTS["title"]),
            "phone": _secret("SENDER_PHONE", SENDER_DEFAULTS["phone"]),
            "email": _secret("SENDER_EMAIL", SENDER_DEFAULTS["email"]),
        })
        prof["name"] = st.text_input("Your name", value=prof.get("name", ""), placeholder="e.g. Ky Thomas",
                                     help="Leave blank to send as the company: \"Hi Mike, it's Fortlox Security here.\"")
        if not get_sender().get("name"):
            st.caption("No name set: emails open \"It's Fortlox Security here\" and are signed by the company.")
        prof["title"] = st.text_input("Job title", value=prof.get("title", ""))
        prof["phone"] = st.text_input("Direct phone", value=prof.get("phone", ""))
        prof["email"] = st.text_input("Your email", value=prof.get("email", ""))
        st.session_state["sender_profile"] = prof
    render_html('<div class="pe-side-h">Account</div>')
    if st.button("Log out", **FULL_WIDTH):
        st.session_state["password_correct"] = False
        st.rerun()

# ---------------- CALL LIST PAGE ----------------
CALL_CSS = """
<style>
.st-key-card-call-now, .st-key-card-call-list, .st-key-card-call-empty, .st-key-card-call-upcoming, .st-key-card-saved, .st-key-card-saved-empty {
  background: linear-gradient(180deg, rgba(22, 31, 51, 0.85) 0%, rgba(17, 24, 39, 0.85) 100%);
  border: 1px solid var(--border) !important; border-radius: var(--radius); padding: 22px 22px 18px 22px;
  box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset, 0 20px 40px -24px rgba(0,0,0,0.6); }
.st-key-card-call-now { border-color: rgba(95,208,255,.35) !important; }
.st-key-card-call-upcoming { margin-top: 18px; }
.cl-kpis { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 18px; }
@media (max-width: 1100px) { .cl-kpis { grid-template-columns: repeat(3, 1fr); } }
.cl-kpi { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px; border-top: 2px solid var(--c, var(--accent)); }
.cl-kpi .v { font-size: 1.45rem; font-weight: 800; color: var(--text); letter-spacing: -0.02em; }
.cl-kpi .l { font-size: 0.7rem; color: var(--muted); font-weight: 700; text-transform: uppercase; letter-spacing: .07em; }
.cl-firm { font-size: 1.45rem; font-weight: 800; letter-spacing: -0.025em; color: var(--text); line-height: 1.2; }
.cl-legal { font-size: 0.78rem; color: var(--faint); margin-top: 2px; }
.cl-phone { display: flex; align-items: center; gap: 12px; margin: 14px 0 10px 0; padding: 14px 16px; border-radius: 14px;
  background: linear-gradient(135deg, rgba(95,208,255,.14), rgba(41,169,225,.10)); border: 1px solid rgba(95,208,255,.35); }
.cl-phone .ic { width: 40px; height: 40px; border-radius: 12px; background: var(--grad); color: #0A0E1A; display: grid; place-items: center; flex-shrink: 0; }
.cl-phone a { font-size: 1.55rem; font-weight: 800; letter-spacing: -0.01em; color: var(--text) !important; text-decoration: none; }
.cl-phone .alt { font-size: 0.78rem; color: var(--muted); margin-top: 2px; }
.cl-hist { margin-top: 6px; }
.cl-hist .row { display: flex; gap: 10px; font-size: 0.8rem; padding: 6px 0; border-top: 1px solid var(--border); color: var(--muted); }
.cl-hist .row b { color: var(--text); font-weight: 600; }
.cl-hist .row .when { color: var(--faint); white-space: nowrap; min-width: 88px; }
.cl-flash { margin-bottom: 12px; }
.st-key-card-call-now .stButton button { min-height: 44px; }
</style>
"""


def call_hero_html(to_call: int, due: int, interested: int) -> str:
    pills = [
        (str(to_call), "To call", "active"),
        (str(due), "Callbacks due", "done" if due == 0 else ""),
        (str(interested), "Interested", "done"),
    ]
    parts = [f'<div class="pe-step {cls}"><span class="num">{n}</span>{label}</div>' for n, label, cls in pills]
    return (
        '<div class="pe-hero"><div>'
        '<div class="pe-eyebrow"><span class="dot"></span>Shared call list · saved permanently</div>'
        '<div class="pe-title">Call list <span>&amp; dialler</span></div>'
        '<div class="pe-sub">Firms ready to phone, with callbacks served up when they\'re due. Work top to bottom:'
        ' every outcome is saved and shows as contacted in future searches.</div>'
        f'</div><div class="pe-stepper">{"<div class=pe-step-sep></div>".join(parts)}</div></div>'
    )


def log_call(cn: str, outcome: str, notes: str, callback_at: Optional[datetime]) -> None:
    calls = get_call_list()
    if cn not in calls:
        return
    caller = get_sender().get("name", "")
    r = dict(calls[cn])
    stamp = now_uk().isoformat(timespec="seconds")
    entry = {"at": stamp, "by": caller, "outcome": outcome, "note": (notes or "").strip()}
    r["history"] = list(r.get("history") or []) + [entry]
    r.update(status=outcome, notes=notes or "", attempts=int(r.get("attempts") or 0) + 1,
             last_called=stamp, last_called_by=caller,
             callback=callback_at.isoformat(timespec="minutes") if (outcome == "Call back" and callback_at) else "")
    save_calls({cn: r}, f"{r.get('firm', cn)} -> {outcome}")
    if outcome in CALL_DONE:  # Finished with: show as contacted in future prospecting searches
        record_sent({cn: {
            "company_name": r.get("legal_name", r.get("firm", "")), "to": "", "contact": r.get("contact", ""),
            "vertical": r.get("sector", ""), "subject": "", "sent_at": stamp, "sent_by": caller,
            "status": f"Called · {outcome}",
        }})
    st.session_state["call_current"] = None
    st.session_state["call_flash"] = f"{r.get('firm', 'Firm')} logged as {outcome}."


def render_call_page() -> None:
    st.markdown(CALL_CSS, unsafe_allow_html=True)
    calls = get_call_list()
    ver = st.session_state.get("call_ver", 0)
    order = call_queue(calls)
    caller = get_sender().get("name", "")
    today = now_uk().date().isoformat()
    status_counts = {s: sum(1 for r in calls.values() if r.get("status") == s) for s in CALL_STATUSES}
    due_now = sum(1 for cn in order if calls[cn].get("status") == "Call back")
    calls_today = sum(1 for r in calls.values() for h in (r.get("history") or []) if str(h.get("at", "")).startswith(today))

    render_html(
        '<div class="cl-kpis">'
        f'<div class="cl-kpi" style="--c:#5FD0FF"><div class="l">To call now</div><div class="v">{len(order)}</div></div>'
        f'<div class="cl-kpi" style="--c:#FBBF24"><div class="l">Callbacks due</div><div class="v">{due_now}</div></div>'
        f'<div class="cl-kpi" style="--c:#29A9E1"><div class="l">Calls today</div><div class="v">{calls_today}</div></div>'
        f'<div class="cl-kpi" style="--c:#34D399"><div class="l">Interested</div><div class="v">{status_counts["Interested"]}</div></div>'
        f'<div class="cl-kpi" style="--c:#5E6A82"><div class="l">On the list</div><div class="v">{len(calls)}</div></div>'
        "</div>"
    )
    if st.session_state.get("call_list_error"):
        st.error(st.session_state.pop("call_list_error"))

    if not calls:
        with st.container(key="card-call-empty"):
            render_html(
                f'<div class="pe-empty"><div style="color:var(--accent-2);display:inline-block;padding:18px;border-radius:20px;'
                f'background:rgba(95,208,255,.1);border:1px solid rgba(95,208,255,.3)">{icon("phone", 40, 1.6)}</div>'
                '<div class="t">The call list is empty</div>'
                '<div class="s">Firms we can phone but not email land here, saved for the whole team.</div>'
                "<ol><li>In Prospecting, enrich a batch of firms</li><li>Tick firms under <b>&nbsp;No email found</b></li>"
                "<li>Hit <b>&nbsp;Add to the call list</b></li></ol></div>"
            )
        return

    left, right = st.columns([1, 1.35], gap="large")

    # ===== Now calling =====
    with left:
        with st.container(key="card-call-now"):
            section_header("▶", "Now calling", f"{len(order)} in the queue · callbacks first, then new, then retries")
            if st.session_state.get("call_flash"):
                st.success(st.session_state.pop("call_flash"))
            if not caller:
                st.caption("💡 Add your name under **Your email signature** in the sidebar so calls are logged against you.")
            if not order:
                render_html('<div class="pe-hint">Queue clear. Every firm has an outcome or a callback booked for later.</div>')
            else:
                current = st.session_state.get("call_current")
                if current not in order:
                    current = order[0]
                pick = st.selectbox(
                    "Up next", order, index=order.index(current), key=f"call_pick_{ver}",
                    format_func=lambda c: f"{calls[c].get('firm', c)} · {calls[c].get('status', 'New')}"
                    + (f" · {fmt_when(calls[c].get('callback', ''))}" if calls[c].get("status") == "Call back" else ""),
                )
                st.session_state["call_current"] = pick
                r = calls[pick]
                cfg = VERTICAL_PRESETS.get(r.get("sector", ""), VERTICAL_PRESETS["Estate & Lettings Agents"])
                meta = [chip(r.get("status", "New"), CALL_STATUS_TONE.get(r.get("status", "New"), "")),
                        chip(r.get("sector", ""), "accent")]
                if r.get("attempts"):
                    meta.append(chip(f"{r['attempts']} previous call{'s' if r['attempts'] != 1 else ''}", "muted"))
                phone = r.get("phone", "")
                alt = " · ".join(r.get("other_phones") or [])
                site = r.get("website", "")
                directors = ", ".join(r.get("directors") or [])
                render_html(
                    f'<div class="cl-firm">{esc(r.get("firm", ""))}</div>'
                    f'<div class="cl-legal">{esc(r.get("legal_name", ""))}'
                    + ("" if str(pick).startswith("OSM-") else f" · #{esc(pick)}") + "</div>"
                    f'<div class="pe-chips" style="margin-top:10px">{"".join(meta)}</div>'
                    f'<div class="cl-phone"><div class="ic">{icon("phone", 20, 2.2)}</div><div>'
                    f'<a href="tel:{esc(phone.replace(" ", ""))}">{esc(phone or "No number")}</a>'
                    + (f'<div class="alt">Also: {esc(alt)}</div>' if alt else "")
                    + "</div></div>"
                    '<div class="pe-panel"><div class="h">Ask for</div>'
                    f'<div class="pe-contact"><div class="pe-avatar">{esc(initials(r.get("contact", "?")))}</div>'
                    f'<div><div class="n">{esc(r.get("contact", ""))}</div><div class="r">{esc(r.get("role", ""))}'
                    + (f" · directors: {esc(directors)}" if directors else "")
                    + "</div></div></div>"
                    + (f'<div class="pe-row" style="margin-top:10px">{icon("globe", 15)}<a href="{esc(site)}" target="_blank">'
                       f'{esc(site.replace("https://", "").replace("http://", ""))}</a></div>' if site else "")
                    + (f'<div class="pe-row">{icon("pin", 15)}<span>{esc(r.get("address", ""))}</span></div>' if r.get("address") else "")
                    + "</div>"
                    f'<div class="pe-hook"><div class="h">Talking points</div><div class="t">{esc(cfg["primary_hook"])}</div>'
                    "<ul>" + "".join(f"<li>{esc(b)}</li>" for b in cfg["pitch_bullets"][:3])
                    + "<li>BT's analogue lines switch off by January 2027, so now is the time to move</li></ul></div>"
                )
                li_q = f"{(r.get('directors') or [r.get('contact', '')])[0]} {r.get('firm', '')}"
                st.link_button("🔎  Find on LinkedIn", r.get("linkedin") or
                               "https://www.linkedin.com/search/results/people/?keywords=" + quote(li_q),
                               **FULL_WIDTH, help="Check who you're calling before you dial")
                hist = list(reversed(r.get("history") or []))[:3]
                if hist:
                    render_html(
                        '<div class="nl-lines-h" style="font-size:.7rem;font-weight:700;letter-spacing:.08em;'
                        'text-transform:uppercase;color:var(--faint);margin:10px 0 2px 0">Previous calls</div><div class="cl-hist">'
                        + "".join(
                            f'<div class="row"><span class="when">{esc(fmt_when(h.get("at", "")))}</span>'
                            f'<span><b>{esc(h.get("outcome", ""))}</b>{" · " + esc(h.get("by")) if h.get("by") else ""}'
                            f'{" · " + esc(h.get("note")) if h.get("note") else ""}</span></div>'
                            for h in hist)
                        + "</div>"
                    )
                notes = st.text_area("Call notes", value=r.get("notes", ""), key=f"call_note_{pick}_{ver}", height=90,
                                     placeholder="Who you spoke to, current provider, contract end date, number of users…")
                d1, d2 = st.columns(2)
                with d1:
                    cb_day = st.date_input("Call back on", value=now_uk().date() + timedelta(days=1),
                                           key=f"cb_day_{pick}_{ver}", format="DD/MM/YYYY")
                with d2:
                    slots = [dt_time(h, m) for h in range(8, 19) for m in (0, 30) if not (h == 18 and m == 30)]
                    cb_time = st.selectbox("at", slots, index=slots.index(dt_time(10, 0)), key=f"cb_time_{pick}_{ver}",
                                           format_func=lambda t: t.strftime("%H:%M"))
                outcome = None
                buttons = [
                    ("✅  Interested", "Interested", "primary", None),
                    ("📅  Call back", "Call back", "secondary", "Books the date & time above"),
                    ("📵  No answer", "No answer", "secondary", None),
                    ("✋  Not interested", "Not interested", "secondary", None),
                    ("⚠️  Wrong number", "Wrong number", "secondary", None),
                    ("🚫  Do not call", "Do not call", "secondary", "Never offered again. Use when someone asks not to be contacted."),
                ]
                for row_start in range(0, len(buttons), 2):
                    bcols = st.columns(2)
                    for bcol, (label, value, kind, tip) in zip(bcols, buttons[row_start:row_start + 2]):
                        with bcol:
                            if st.button(label, type=kind, key=f"o_{value.replace(' ', '_').lower()}_{pick}",
                                         help=tip, **FULL_WIDTH):
                                outcome = value
                if outcome:
                    log_call(pick, outcome, notes, datetime.combine(cb_day, cb_time) if outcome == "Call back" else None)
                    st.rerun()

        render_upcoming_callbacks(calls, order)

    # ===== The whole list =====
    with right:
        with st.container(key="card-call-list"):
            section_header("≡", "The list", "Filter, tweak statuses or notes, then save. Shared with everyone using the app.")
            f1, f2, f3 = st.columns([1.3, 1.2, 1])
            with f1:
                show = st.multiselect("Status", CALL_STATUSES, default=CALL_OPEN, key="call_f_status")
            with f2:
                sectors = sorted({r.get("sector", "") for r in calls.values() if r.get("sector")})
                pick_sec = st.multiselect("Sector", sectors, default=[], key="call_f_sector", placeholder="All sectors")
            with f3:
                q = st.text_input("Search", key="call_f_q", placeholder="Firm, contact or phone").strip().lower()
            rows = []
            for cn, r in calls.items():
                if show and r.get("status", "New") not in show:
                    continue
                if pick_sec and r.get("sector") not in pick_sec:
                    continue
                hay = " ".join([r.get("firm", ""), r.get("contact", ""), r.get("phone", ""), r.get("legal_name", "")]).lower()
                if q and q not in hay:
                    continue
                rows.append({
                    "cn": cn, "Status": r.get("status", "New"), "Firm": r.get("firm", ""), "Contact": r.get("contact", ""),
                    "Phone": r.get("phone", ""), "Website": r.get("website", ""),
                    "Callback": fmt_when(r.get("callback", "")) if r.get("status") == "Call back" else "",
                    "Calls": int(r.get("attempts") or 0), "Last called": fmt_when(r.get("last_called", "")),
                    "Notes": r.get("notes", ""),
                })
            if not rows:
                st.caption("No firms match these filters.")
            else:
                df = pd.DataFrame(rows)
                kwargs = dict(
                    hide_index=True, num_rows="fixed", key=f"call_table_{ver}",
                    height=min(38 + 35 * len(df), 560),
                    column_order=["Status", "Firm", "Contact", "Phone", "Website", "Callback", "Calls", "Last called", "Notes"],
                    disabled=["Firm", "Contact", "Phone", "Website", "Callback", "Calls", "Last called"],
                    column_config={
                        "Status": st.column_config.SelectboxColumn("Status", options=CALL_STATUSES, required=True, width="small"),
                        "Firm": st.column_config.TextColumn("Firm", width="medium"),
                        "Contact": st.column_config.TextColumn("Contact", width="small"),
                        "Phone": st.column_config.TextColumn("Phone", width="small"),
                        "Website": st.column_config.LinkColumn("Website", width="small", display_text="Open ↗"),
                        "Callback": st.column_config.TextColumn("Callback", width="small"),
                        "Calls": st.column_config.NumberColumn("Calls", width="small"),
                        "Last called": st.column_config.TextColumn("Last called", width="small"),
                        "Notes": st.column_config.TextColumn("Notes (editable)", width="large"),
                    },
                )
                try:
                    edited = st.data_editor(df, width="stretch", **kwargs)
                except Exception:
                    edited = st.data_editor(df, use_container_width=True, **kwargs)
                changes: Dict[str, Dict[str, Any]] = {}
                for _, row in edited.iterrows():
                    orig = calls.get(row["cn"])
                    if not orig:
                        continue
                    if row["Status"] != orig.get("status", "New") or (row["Notes"] or "") != (orig.get("notes") or ""):
                        changes[row["cn"]] = {"status": row["Status"], "notes": row["Notes"] or ""}
                s1, s2 = st.columns([1.2, 1])
                with s1:
                    if st.button(f"💾  Save {len(changes)} change{'s' if len(changes) != 1 else ''}" if changes else "💾  No changes to save",
                                 type="primary", disabled=not changes, key="call_save", **FULL_WIDTH):
                        caller_now = get_sender().get("name", "")
                        stamp = now_uk().isoformat(timespec="seconds")
                        updates, handled = {}, {}
                        for cn, ch in changes.items():
                            r = dict(calls[cn])
                            if ch["status"] != r.get("status"):
                                r["history"] = list(r.get("history") or []) + [
                                    {"at": stamp, "by": caller_now, "outcome": f"Set to {ch['status']}", "note": ""}]
                                if ch["status"] in CALL_DONE:
                                    handled[cn] = {"company_name": r.get("legal_name", ""), "to": "", "contact": r.get("contact", ""),
                                                   "vertical": r.get("sector", ""), "subject": "", "sent_at": stamp,
                                                   "sent_by": caller_now, "status": f"Called · {ch['status']}"}
                            r.update(ch)
                            updates[cn] = r
                        save_calls(updates, f"{len(updates)} edited")
                        if handled:
                            record_sent(handled)
                        st.rerun()
                with s2:
                    export = pd.DataFrame([{
                        "Status": r.get("status", ""), "Firm": r.get("firm", ""), "Legal name": r.get("legal_name", ""),
                        "Company number": cn, "Contact": r.get("contact", ""), "Role": r.get("role", ""),
                        "Phone": r.get("phone", ""), "Other phones": "; ".join(r.get("other_phones") or []),
                        "Website": r.get("website", ""), "Sector": r.get("sector", ""), "Address": r.get("address", ""),
                        "Callback": r.get("callback", ""), "Calls": r.get("attempts", 0),
                        "Last called": r.get("last_called", ""), "Last called by": r.get("last_called_by", ""),
                        "Notes": r.get("notes", ""),
                    } for cn, r in calls.items()])
                    st.download_button("⬇  Export call list (.csv)", data=export.to_csv(index=False).encode("utf-8-sig"),
                                       file_name=f"Fortlox_Security_call_list_{now_uk().strftime('%Y-%m-%d')}.csv",
                                       mime="text/csv", key="call_export", **FULL_WIDTH)


def saved_hero_html(total: int, with_email: int, fresh: int) -> str:
    pills = [(str(total), "Saved", "active"), (str(with_email), "With email", "done"), (str(fresh), "Not contacted", "")]
    parts = [f'<div class="pe-step {cls}"><span class="num">{n}</span>{label}</div>' for n, label, cls in pills]
    return (
        '<div class="pe-hero"><div>'
        '<div class="pe-eyebrow"><span class="dot"></span>Every enriched firm · saved permanently</div>'
        '<div class="pe-title">Saved <span>firms</span></div>'
        '<div class="pe-sub">Every business you enrich is kept here, so you never have to search for it again.'
        ' Reopen firms to email them, or send them to the call list.</div>'
        f'</div><div class="pe-stepper">{"<div class=pe-step-sep></div>".join(parts)}</div></div>'
    )


def _saved_status(cn: str, log: Dict[str, Any], calls: Dict[str, Any]) -> str:
    if cn in calls:
        return "📞 " + (calls[cn].get("status") or "New")
    if cn in log:
        return "✓ " + (log[cn].get("status") or "Emailed")
    return "Not contacted"


def _saved_item(cn: str, rec: Dict[str, Any]) -> Dict[str, Any]:
    """A queue-style item for a saved firm (with any confirmed contact applied)."""
    item = {"lead": lead_from_saved(rec), "vertical": rec.get("vertical") or "Estate & Lettings Agents",
            "to": "", "to_ver": 0, "sig": None}
    stored = get_contacts().get(cn)
    if stored:
        apply_contact(item, stored)
    return item


def render_saved_page() -> None:
    st.markdown(CALL_CSS, unsafe_allow_html=True)
    saved = get_saved()
    log, calls = get_sent_log(), get_call_list()
    ver = st.session_state.get("saved_ver", 0)
    if st.session_state.get("saved_error"):
        st.error(st.session_state.pop("saved_error"))
    if st.session_state.get("saved_flash"):
        st.success(st.session_state.pop("saved_flash"))

    n_email = sum(1 for r in saved.values() if (r.get("lead") or {}).get("emails_found"))
    n_phone = sum(1 for r in saved.values() if (r.get("lead") or {}).get("phones_found"))
    n_fresh = sum(1 for cn in saved if cn not in log and cn not in calls)
    render_html(
        '<div class="cl-kpis">'
        f'<div class="cl-kpi" style="--c:#5FD0FF"><div class="l">Saved firms</div><div class="v">{len(saved)}</div></div>'
        f'<div class="cl-kpi" style="--c:#34D399"><div class="l">With email</div><div class="v">{n_email}</div></div>'
        f'<div class="cl-kpi" style="--c:#29A9E1"><div class="l">With phone</div><div class="v">{n_phone}</div></div>'
        f'<div class="cl-kpi" style="--c:#FBBF24"><div class="l">Not contacted</div><div class="v">{n_fresh}</div></div>'
        f'<div class="cl-kpi" style="--c:#5E6A82"><div class="l">On call list</div><div class="v">{sum(1 for c in saved if c in calls)}</div></div>'
        "</div>"
    )
    if not saved:
        with st.container(key="card-saved-empty"):
            render_html(
                f'<div class="pe-empty"><div style="color:var(--accent-2);display:inline-block;padding:18px;border-radius:20px;'
                f'background:rgba(95,208,255,.1);border:1px solid rgba(95,208,255,.3)">{icon("target", 40, 1.6)}</div>'
                '<div class="t">No saved firms yet</div>'
                '<div class="s">Every firm you enrich in Prospecting is saved here automatically.</div>'
                "<ol><li>Open <b>&nbsp;Prospecting</b></li><li>Find businesses in an area</li>"
                "<li>Enrich them, and they appear here</li></ol></div>"
            )
        return

    with st.container(key="card-saved"):
        section_header("≡", "Your saved firms", "Search, filter, then tick firms to reopen, call or export them.")
        f1, f2, f3 = st.columns([1.2, 1.3, 1])
        with f1:
            q = st.text_input("Search", key="sv_q", placeholder="Firm, contact, town, email or phone").strip().lower()
        with f2:
            sectors = sorted({r.get("vertical", "") for r in saved.values() if r.get("vertical")})
            pick_sec = st.multiselect("Sector", sectors, default=[], key="sv_sector", placeholder="All sectors")
        with f3:
            show = st.selectbox("Show", ["All", "Not contacted", "Has email", "Phone only", "On call list", "Emailed / handled"],
                                key="sv_show")
        rows = []
        for cn, r in sorted(saved.items(), key=lambda kv: kv[1].get("updated_at", ""), reverse=True):
            L = r.get("lead") or {}
            emails, phones = L.get("emails_found") or [], L.get("phones_found") or []
            if pick_sec and r.get("vertical") not in pick_sec:
                continue
            if show == "Not contacted" and (cn in log or cn in calls):
                continue
            if show == "Has email" and not emails:
                continue
            if show == "Phone only" and (emails or not phones):
                continue
            if show == "On call list" and cn not in calls:
                continue
            if show == "Emailed / handled" and cn not in log:
                continue
            contact = (get_contacts().get(cn) or {}).get("name") or ""
            if not contact:
                owners = [o for o in (L.get("officers") or []) if o.get("is_owner")] or (L.get("officers") or [])
                contact = display_officer_name(owners[0]["name"]) if owners else ""
            area = L.get("registered_address") or ""
            hay = " ".join([r.get("firm", ""), L.get("company_name", ""), contact, area, " ".join(emails), " ".join(phones)]).lower()
            if q and q not in hay:
                continue
            try:
                saved_on = datetime.fromisoformat(r.get("saved_at", "")).strftime("%d %b %Y").lstrip("0")
            except ValueError:
                saved_on = ""
            rows.append({
                "cn": cn, "Select": False, "Firm": r.get("firm") or L.get("company_name", ""),
                "Sector": r.get("vertical", ""), "Status": _saved_status(cn, log, calls), "Contact": contact,
                "Email": (emails or [""])[0], "Phone": (phones or [""])[0], "Website": L.get("website_url") or "",
                "Address": area, "Saved": saved_on,
            })
        st.caption(f"Showing {len(rows)} of {len(saved)} saved firms.")
        if not rows:
            st.info("No saved firms match these filters.")
            return
        df = pd.DataFrame(rows)
        kwargs = dict(
            hide_index=True, num_rows="fixed", key=f"saved_table_{ver}_{len(rows)}",
            height=min(38 + 35 * len(df), 520),
            column_order=["Select", "Firm", "Sector", "Status", "Contact", "Email", "Phone", "Website", "Address", "Saved"],
            disabled=["Firm", "Sector", "Status", "Contact", "Email", "Phone", "Website", "Address", "Saved"],
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", width="small"),
                "Firm": st.column_config.TextColumn("Firm", width="medium"),
                "Sector": st.column_config.TextColumn("Sector", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Contact": st.column_config.TextColumn("Contact", width="small"),
                "Email": st.column_config.TextColumn("Email", width="medium"),
                "Phone": st.column_config.TextColumn("Phone", width="small"),
                "Website": st.column_config.LinkColumn("Website", width="small", display_text="Open ↗"),
                "Address": st.column_config.TextColumn("Address", width="medium"),
                "Saved": st.column_config.TextColumn("Saved", width="small"),
            },
        )
        try:
            edited = st.data_editor(df, width="stretch", **kwargs)
        except Exception:
            edited = st.data_editor(df, use_container_width=True, **kwargs)
        picked = [row["cn"] for _, row in edited.iterrows() if row["Select"]]
        can_call = [c for c in picked if c not in calls and (saved[c].get("lead") or {}).get("phones_found")]

        a1, a2, a3, a4 = st.columns(4)
        with a1:
            if st.button(f"✉️  Reopen {len(picked)} to email" if picked else "✉️  Reopen to email", type="primary",
                         disabled=not picked, key="sv_open", **FULL_WIDTH,
                         help="Loads the ticked firms into Review & send under Prospecting, with fresh email drafts."):
                for c in picked:
                    add_to_queue(lead_from_saved(saved[c]), saved[c].get("vertical") or "Estate & Lettings Agents")
                st.session_state["current_cn"] = picked[0]
                st.session_state["current_cn_select"] = picked[0]
                st.session_state["goto_view"] = "prospect"
                st.session_state["saved_ver"] = ver + 1
                st.rerun()
        with a2:
            if st.button(f"📞  Add {len(can_call)} to call list" if can_call else "📞  Add to call list",
                         disabled=not can_call, key="sv_call", **FULL_WIDTH,
                         help="Firms with a phone number that aren't already on the call list."):
                save_calls({c: call_record_from_item(_saved_item(c, saved[c])) for c in can_call}, f"{len(can_call)} added")
                st.session_state["saved_ver"] = ver + 1  # Clear the ticks
                st.session_state["saved_flash"] = (f"{len(can_call)} firms added to the call list."
                                                   " Open Call list & callbacks in the sidebar to start calling.")
                st.rerun()
        with a3:
            export = df.drop(columns=["cn", "Select"])
            if picked:
                export = export[df["cn"].isin(picked)]
            st.download_button(f"⬇  Export {len(export)} (.csv)", data=export.to_csv(index=False).encode("utf-8-sig"),
                               file_name=f"Fortlox_Security_saved_firms_{now_uk().strftime('%Y-%m-%d')}.csv",
                               mime="text/csv", key="sv_export", **FULL_WIDTH,
                               help="Ticked firms, or everything shown if none are ticked.")
        with a4:
            with st.popover(f"🗑️  Remove {len(picked)}" if picked else "🗑️  Remove", disabled=not picked, **FULL_WIDTH):
                st.caption("Removes the ticked firms from Saved firms. Call list entries and ticks stay.")
                if st.button(f"Yes, remove {len(picked)}", key=f"sv_del_{ver}", type="primary"):
                    update_saved({c: None for c in picked}, f"{len(picked)} removed")
                    st.session_state["saved_flash"] = f"{len(picked)} firms removed."
                    st.rerun()
        if len(picked) > 1 and len(can_call) < len(picked):
            st.caption(f"💡 {len(picked) - len(can_call)} ticked firms are already on the call list or have no phone number.")


def render_upcoming_callbacks(calls: Dict[str, Any], due_order: List[str]) -> None:
    """Callbacks booked for later, soonest first."""
    upcoming = []
    for cn, r in calls.items():
        if r.get("status") == "Call back" and cn not in due_order and r.get("callback"):
            upcoming.append((r.get("callback"), cn))
    upcoming.sort()
    with st.container(key="card-call-upcoming"):
        section_header("📅", "Booked callbacks", f"{len(upcoming)} coming up · each one joins the queue when it's due")
        if not upcoming:
            render_html('<div class="pe-hint">No callbacks booked. Use <b>Call back</b> on a call to book one.</div>')
            return
        today = now_uk().date()
        html_rows = []
        for when, cn in upcoming[:15]:
            r = calls[cn]
            try:
                d = datetime.fromisoformat(when)
                day = "Today" if d.date() == today else "Tomorrow" if d.date() == today + timedelta(days=1) else d.strftime("%a %d %b")
                label = f"{day} {d.strftime('%H:%M')}"
            except ValueError:
                label = when
            phone = r.get("phone", "")
            html_rows.append(
                f'<div class="row"><span class="when" style="min-width:110px">{esc(label)}</span>'
                f'<span><b>{esc(r.get("firm", ""))}</b>'
                + (f' · <a href="tel:{esc(phone.replace(" ", ""))}">{esc(phone)}</a>' if phone else "")
                + (f' · {esc(r.get("notes", "")[:80])}' if r.get("notes") else "")
                + "</span></div>"
            )
        render_html('<div class="cl-hist">' + "".join(html_rows) + "</div>")
        if len(upcoming) > 15:
            st.caption(f"+ {len(upcoming) - 15} more. Filter the list by 'Call back' to see them all.")
        ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Fortlox Prospector//EN"]
        for when, cn in upcoming:
            try:
                d = datetime.fromisoformat(when)
            except ValueError:
                continue
            r = calls[cn]
            ics += ["BEGIN:VEVENT", f"UID:{re.sub(r'[^A-Za-z0-9]', '', cn)}-{d.strftime('%Y%m%dT%H%M')}@fortlox",
                    f"DTSTART;TZID=Europe/London:{d.strftime('%Y%m%dT%H%M%S')}",
                    f"DTEND;TZID=Europe/London:{(d + timedelta(minutes=15)).strftime('%Y%m%dT%H%M%S')}",
                    f"SUMMARY:Call back {r.get('firm', '')} ({r.get('phone', '')})".replace(",", "\\,"),
                    "DESCRIPTION:" + (f"Ask for {r.get('contact', '')}. {r.get('notes', '')}").replace("\n", " ").replace(",", "\\,"),
                    "END:VEVENT"]
        ics.append("END:VCALENDAR")
        st.download_button("🗓️  Add callbacks to my calendar (.ics)", data="\r\n".join(ics).encode("utf-8"),
                           file_name="Fortlox_callbacks.ics", mime="text/calendar", key="cb_ics", **FULL_WIDTH,
                           help="Opens in Outlook, Google Calendar or Apple Calendar.")


if st.session_state.get("view") == "saved":
    render_saved_page()
    _sv = get_saved()
    _lg = get_sent_log()
    _cl = get_call_list()
    render_html(saved_hero_html(len(_sv), sum(1 for r in _sv.values() if (r.get("lead") or {}).get("emails_found")),
                                sum(1 for c in _sv if c not in _lg and c not in _cl)), target=hero_slot)
    render_html(
        '<div class="pe-stats">'
        f'<div class="pe-stat"><div class="v">{len(_sv)}</div><div class="l">Saved</div></div>'
        f'<div class="pe-stat"><div class="v">{len(call_queue(_cl))}</div><div class="l">To call</div></div>'
        f'<div class="pe-stat"><div class="v">{len(_lg)}</div><div class="l">Handled</div></div>'
        "</div>",
        target=sidebar_stats_slot,
    )
    st.stop()

if st.session_state.get("view") == "calls":
    render_call_page()
    _calls = get_call_list()
    _order = call_queue(_calls)
    render_html(call_hero_html(len(_order), sum(1 for c in _order if _calls[c].get("status") == "Call back"),
                               sum(1 for r in _calls.values() if r.get("status") == "Interested")), target=hero_slot)
    render_html(
        '<div class="pe-stats">'
        f'<div class="pe-stat"><div class="v">{len(_calls)}</div><div class="l">On list</div></div>'
        f'<div class="pe-stat"><div class="v">{len(_order)}</div><div class="l">To call</div></div>'
        f'<div class="pe-stat"><div class="v">{len(get_sent_log())}</div><div class="l">Handled</div></div>'
        "</div>",
        target=sidebar_stats_slot,
    )
    st.stop()



col_left, col_right = st.columns([1.08, 0.92], gap="large")

# ---------------- Left: Target & Select ----------------
with col_left:
    with st.container(key="card-left"):
        section_header("01", "Target market", "Pick a sector and an area to find local businesses (free, no sign-up).")

        selected_vertical_name = st.selectbox(
            "Industry",
            options=sorted(VERTICAL_PRESETS.keys()),
            index=sorted(VERTICAL_PRESETS.keys()).index("Estate & Lettings Agents"),
            help="Each sector has its own pitch, systems and one-page overview PDF.",
        )
        vertical_config = VERTICAL_PRESETS[selected_vertical_name]
        render_html(
            '<div class="pe-vertical"><div style="flex:1">'
            '<div class="lbl">Systems we integrate with</div><div class="pe-chips">'
            + "".join(chip(c, "accent") for c in vertical_config["crms"])
            + "</div></div></div>"
        )
        sources = ["OpenStreetMap (free)"] + (["Companies House (free key)"] if ch_api_key else [])
        source = st.radio("Find businesses from", sources, horizontal=True, key="find_source",
                          help="OpenStreetMap needs no sign-up. Companies House lists every registered company,"
                               " and appears here once a free COMPANIES_HOUSE_KEY is added to Secrets.") \
            if len(sources) > 1 else sources[0]

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            location_input = st.text_input(
                "Town or postcode",
                placeholder="e.g. Stroud or GL5 1AA" if source.startswith("Open") else "e.g. Gloucester or Gloucestershire",
            )
        with f_col2:
            keyword_filter = st.text_input(
                "Name keyword (optional)",
                placeholder=f"e.g. {vertical_config['search_hint']}",
            )

        r_col1, r_col2, r_col3 = columns([1, 1, 1.6])
        with r_col1:
            result_limit = st.selectbox("Results", [25, 50, 100], index=1)
        with r_col2:
            radius_km = st.selectbox("Within", [3, 5, 10, 20, 30], index=2, format_func=lambda k: f"{k} km",
                                     disabled=not source.startswith("Open"))
        with r_col3:
            browse_btn = st.button("Find businesses", type="primary", **FULL_WIDTH)

        if browse_btn:
            leads_list, search_error = [], None
            if not location_input.strip():
                search_error = "Type a town or postcode first."
            elif source.startswith("Open"):
                with st.spinner("Searching the map…"):
                    loc = locate_area(location_input)
                    if not loc:
                        search_error = f"Couldn't find '{location_input}'. Try a nearby town or a full postcode."
                    else:
                        leads_list, search_error = osm_browse(selected_vertical_name, loc[0], loc[1], radius_km,
                                                              keyword_filter, result_limit)
            else:
                with st.spinner("Querying the Companies House register…"):
                    enricher = LeadEnricher(ch_api_key=ch_api_key)
                    leads_list, search_error = enricher.browse_vertical(
                        sic_codes=vertical_config["sic_codes"],
                        location_keyword=location_input,
                        company_name_includes=keyword_filter,
                        limit=result_limit,
                    )
            st.session_state["discovered_leads"] = leads_list
            st.session_state["active_vertical_name"] = selected_vertical_name
            st.session_state["search_location"] = location_input.strip()
            st.session_state["selected_lead_row"] = None
            st.session_state["search_version"] = st.session_state.get("search_version", 0) + 1
            if not search_error:
                st.session_state["stat_searches"] += 1
                st.session_state["stat_firms"] += len(leads_list)
            if search_error:
                st.error(search_error)
            elif not leads_list:
                st.warning("Nothing found. Try a bigger distance, a nearby bigger town, or remove the keyword."
                           + (" The map only shows businesses someone has added, so Companies House (free key)"
                              " finds more." if source.startswith("Open") else ""))

    if st.session_state.get("discovered_leads"):
        with st.container(key="card-select"):
            leads_data = st.session_state["discovered_leads"]
            where = st.session_state.get("search_location") or "the UK"
            log_now = get_sent_log()
            already = sum(1 for r in leads_data if r.get("Company Number") in log_now)
            section_header(
                "02", "Select firms",
                f"{len(leads_data)} active {'firm' if len(leads_data) == 1 else 'firms'} in {where}"
                f" · {st.session_state.get('active_vertical_name', '')}"
                + (f" · {already} already contacted" if already else ""),
            )

            df = pd.DataFrame(leads_data)
            df["Contacted"] = [sent_label(log_now.get(cn)) for cn in df["Company Number"]]
            if "Town / Postcode" in df.columns:
                df["Town"] = df["Town / Postcode"].astype(str).str.split(",").str[0]
            if "Incorporated" in df.columns:
                df["Incorporated"] = pd.to_datetime(df["Incorporated"], errors="coerce")

            table_event = render_leads_table(
                df, key=f"leads_table_{st.session_state.get('search_version', 0)}"
            )
            selected_rows = [i for i in (table_event.selection.rows if table_event else []) if i < len(leads_data)]
            selected = [leads_data[i] for i in selected_rows]
            st.session_state["selected_rows_data"] = selected

            batch_to_run: List[Dict[str, Any]] = []
            website_override = ""
            if not selected:
                render_html(
                    f'<div class="pe-hint">{icon("pointer", 16)}'
                    "Tick one firm, or several to build a batch. Or enrich every result in one go.</div>"
                )
                n_all = min(len(leads_data), MAX_BATCH)
                fresh = [r for r in leads_data if r["Company Number"] not in log_now and r["Company Number"] not in st.session_state.get("queue", {})]
                if st.button(
                    f"⚡ Enrich all {min(len(fresh), MAX_BATCH)} new results"
                    + (f" (skips {len(leads_data) - len(fresh)} already contacted or queued)" if len(fresh) < len(leads_data) else ""),
                    type="primary", disabled=not fresh, **FULL_WIDTH,
                    help=f"Finds contacts for every firm in the list (up to {MAX_BATCH} at a time), then sorts them into Ready to email / No email below.",
                ):
                    batch_to_run = fresh[:MAX_BATCH]
                if len(fresh) > MAX_BATCH:
                    st.caption(f"The first {MAX_BATCH} will be enriched. Run it again for the next {MAX_BATCH}.")
            else:
                n_sel = len(selected)
                names = ", ".join(esc(friendly_company_name(r["Company Name"])) for r in selected[:3])
                more = f" + {n_sel - 3} more" if n_sel > 3 else ""
                contacted_sel = [r for r in selected if r["Company Number"] in log_now]
                meta = (("" if str(selected[0]["Company Number"]).startswith("OSM-") else f'#{esc(selected[0]["Company Number"])} · ') + esc(selected[0]["Town / Postcode"])
                        if n_sel == 1 else f"{names}{more}")
                render_html(
                    f'<div class="pe-selected"><div><div class="n">'
                    f'{esc(selected[0]["Company Name"]) if n_sel == 1 else f"{n_sel} firms selected"}</div>'
                    f'<div class="m">{meta}</div></div>'
                    f'{chip(f"{n_sel} selected", "accent")}</div>'
                )
                if contacted_sel:
                    st.caption(
                        f"⚠️ {len(contacted_sel)} of these already contacted: "
                        + ", ".join(friendly_company_name(r["Company Name"]) for r in contacted_sel[:4])
                        + ("…" if len(contacted_sel) > 4 else "")
                    )
                if n_sel > MAX_BATCH:
                    st.warning(f"Batches are capped at {MAX_BATCH} firms. Only the first {MAX_BATCH} will be enriched.")

                if n_sel == 1:
                    e_col1, e_col2 = columns([1.6, 1])
                    with e_col1:
                        website_override = st.text_input(
                            "Website (optional)", placeholder="Leave blank to auto-discover",
                        )
                    with e_col2:
                        if st.button("Enrich & build dossier", type="primary", **FULL_WIDTH):
                            batch_to_run = selected[:1]
                else:
                    if st.button(f"Enrich {min(n_sel, MAX_BATCH)} firms & add to review", type="primary", **FULL_WIDTH):
                        batch_to_run = selected[:MAX_BATCH]

            if batch_to_run:
                vertical_now = st.session_state.get("active_vertical_name", "Estate & Lettings Agents")
                run_enrichment(
                    batch_to_run, vertical_now,
                    manual_websites={batch_to_run[0]["Company Number"]: website_override} if website_override else None,
                )


# ---------------- Right: Dossier ----------------
queue: Dict[str, Dict[str, Any]] = st.session_state.setdefault("queue", {})
queue_order: List[str] = [cn for cn in st.session_state.setdefault("queue_order", []) if cn in queue]

with col_right:
    with st.container(key="card-right"):
        if not queue:
            render_html(
                f'<div class="pe-empty"><div style="color:var(--accent);display:inline-block;'
                f'padding:18px;border-radius:20px;background:var(--accent-soft);border:1px solid rgba(41,169,225,.3)">'
                f'{icon("target", 40, 1.6)}</div>'
                '<div class="t">Your dossier will appear here</div>'
                '<div class="s">Every enriched firm gets a contact card, verified channels,'
                ' a sector integration pitch and a one-page PDF.</div>'
                "<ol><li>Choose a sector &amp; territory</li><li>Tick one or more firms</li>"
                "<li>Hit <b>&nbsp;Enrich</b></li></ol></div>"
            )
        else:
            log_now = get_sent_log()
            if st.session_state.get("current_cn") not in queue:
                st.session_state["current_cn"] = queue_order[0]
            if len(queue_order) > 1:
                if st.session_state.get("current_cn_select") not in queue:
                    st.session_state["current_cn_select"] = st.session_state["current_cn"]
                st.selectbox(
                    f"Viewing firm ({len(queue_order)} in queue)",
                    options=queue_order,
                    key="current_cn_select",
                    format_func=lambda c: ("✓ " if c in log_now else "") + lead_display_name(queue[c]["lead"]),
                )
                st.session_state["current_cn"] = st.session_state["current_cn_select"]
            cn = st.session_state["current_cn"]
            item = queue[cn]
            lead: ScrapedLead = item["lead"]
            current_vert_name = item["vertical"]
            vert_cfg = VERTICAL_PRESETS[current_vert_name]
            contact_name, contact_role = infer_contact_name_and_role(lead, current_vert_name)
            primary_email = pick_primary_email(lead, contact_name)
            is_sent = cn in log_now

            section_header("03", "Lead dossier", "Review, tailor the pitch and send.")

            # Firm header
            meta = [chip(f"#{lead.company_number}" if lead.company_number else "Found on map"), chip(current_vert_name, "accent")]
            meta += [chip(f"SIC {c}", "muted") for c in lead.sic_codes[:2]]
            meta.append(confidence_chip(lead.website_confidence if lead.website_url else None))
            if is_sent:
                meta.append(chip(f"Sent {sent_label(log_now[cn])[2:]}", "good"))
            zrec = get_zoho_store().get(cn) or {}
            if zrec:
                meta.append(chip({"created": "In Zoho: new lead", "existing": "In Zoho: existing lead",
                                  "customer": "Existing customer!"}.get(zrec.get("status"), "In Zoho"),
                                 "risk" if zrec.get("status") == "customer" else "accent"))
            blurb = (
                f'<div class="blurb">“{esc(lead.site_meta_description[:220])}'
                f'{"…" if len(lead.site_meta_description) > 220 else ""}”</div>'
                if lead.site_meta_description else ""
            )
            render_html(
                f'<div class="pe-firm"><div><div class="name">{esc(lead.company_name)}</div>'
                f'<div class="meta">{"".join(meta)}</div>{blurb}</div></div>'
            )
            if zrec.get("id"):
                st.link_button("Open in Zoho ↗", ZOHO.record_url(zrec["id"], "Accounts" if zrec.get("status") == "customer" else "Leads"))
            if zrec.get("status") == "customer":
                st.error(f"This firm is already a customer in Zoho ({zrec.get('name') or 'Accounts'}). Use Customer Growth for them,"
                         " not a new-business pitch.")

            if not lead.website_url and getattr(lead, "contact_email", None):
                pass  # A person has confirmed the contact, so the missing website no longer matters
            elif not lead.website_url:
                st.warning(
                    "Couldn't confidently find this firm's website. Tick just this firm on the left,"
                    " paste its website and re-run to pull contacts."
                )
            elif lead.website_confidence == "Low":
                st.warning(
                    "Weak website match. Check it's the right firm before sending, or tick just this"
                    " firm on the left, paste the correct website and re-run."
                )

            reg = register_link(current_vert_name, lead.company_name)
            if reg:
                st.link_button(f"🔎 Check on the {reg[0]} ↗", reg[1],
                               help="Official register: confirms the firm and often lists its website, phone and manager.")

            tab1, tab2 = st.tabs(["Overview", "Pitch & send"])

            with tab1:
                # Contact + channels
                email_rows = "".join(
                    f'<div class="pe-row">{icon("mail", 15)}<a class="trunc" title="{esc(e)}" href="mailto:{esc(e)}">{esc(e)}</a>'
                    + ('<span class="tag" title="Used in the email &amp; PDF">★ Primary</span>' if e == primary_email else "")
                    + "</div>"
                    for e in lead.emails_found[:5]
                ) or '<div class="pe-none">No emails found</div>'
                phone_rows = "".join(
                    f'<div class="pe-row">{icon("phone", 15)}'
                    f'<a href="tel:{esc(p.replace(" ", ""))}">{esc(p)}</a>'
                    + ('<span class="tag">Main</span>' if i == 0 else "")
                    + "</div>"
                    for i, p in enumerate(lead.phones_found[:4])
                ) or '<div class="pe-none">No phone numbers found</div>'
                site_row = (
                    f'<div class="pe-row">{icon("globe", 15)}<a href="{esc(lead.website_url)}" target="_blank">'
                    f'{esc(lead.website_url.replace("https://", "").replace("http://", ""))}</a></div>'
                    if lead.website_url else ""
                )
                addr_row = (
                    f'<div class="pe-row">{icon("pin", 15)}<span>{esc(lead.registered_address)}</span>'
                    '<span class="tag">Reg. office</span></div>'
                    if lead.registered_address else ""
                )
                li_row = (
                    f'<div class="pe-row"><span class="li-mini">in</span><a class="trunc" href="{esc(lead.linkedin_url)}" target="_blank">'
                    'LinkedIn profile</a></div>' if getattr(lead, "linkedin_url", None) else ""
                )
                render_html(
                    '<div class="pe-panel"><div class="h">Decision-maker</div>'
                    f'<div class="pe-contact"><div class="pe-avatar">{esc(initials(contact_name))}</div>'
                    f'<div><div class="n">{esc(contact_name)}</div><div class="r">{esc(contact_role)}</div></div></div>'
                    f'<div style="margin-top:12px">{site_row}{addr_row}{li_row}</div></div>'
                    '<div class="pe-panel"><div class="h">Channels</div><div class="pe-cols">'
                    f'<div>{email_rows}</div><div>{phone_rows}</div></div></div>'
                )

                # ---- LinkedIn: a person looks, then brings the right contact back ----
                with st.container(key="card-linkedin"):
                    have = bool(getattr(lead, "contact_name", None))
                    render_html(
                        '<div class="li-head"><span class="li-badge">in</span><div><div class="t">'
                        + ("Contact confirmed" if have else "Find the right person on LinkedIn")
                        + '</div><div class="s">'
                        + (f"{esc(lead.contact_name)}{' · ' + esc(lead.contact_role) if lead.contact_role else ''}"
                           f"{' · updated by ' + esc(get_contacts().get(cn, {}).get('updated_by')) if get_contacts().get(cn, {}).get('updated_by') else ''}"
                           if have else "Search in your own LinkedIn, then paste who you find below. The email and PDF update instantly.")
                        + "</div></div></div>"
                    )
                    lk1, lk2 = st.columns(2)
                    with lk1:
                        st.link_button("🔎  Find people on LinkedIn", linkedin_people_url(lead), **FULL_WIDTH,
                                       help="Opens LinkedIn in a new tab, searching for the director at this firm")
                    with lk2:
                        st.link_button("🏢  Company page", linkedin_company_url(lead), **FULL_WIDTH)
                    with st.form(key=f"li_form_{cn}", border=False):
                        a1, a2 = st.columns(2)
                        with a1:
                            f_name = st.text_input("Contact name", value=getattr(lead, "contact_name", None) or "",
                                                   placeholder="e.g. Sarah Jones")
                        with a2:
                            f_role = st.text_input("Job title", value=getattr(lead, "contact_role", None) or "",
                                                   placeholder="e.g. Practice Manager")
                        a3, a4 = st.columns(2)
                        with a3:
                            f_li = st.text_input("LinkedIn profile link", value=getattr(lead, "linkedin_url", None) or "",
                                                 placeholder="https://www.linkedin.com/in/…")
                        with a4:
                            hint = suggest_email(getattr(lead, "contact_name", None) or "", lead)
                            f_email = st.text_input("Business email (if known)", value=getattr(lead, "contact_email", None) or "",
                                                    placeholder=f"Likely: {hint}" if hint else "name@firm.co.uk")
                        saved = st.form_submit_button("Save contact", type="primary", **FULL_WIDTH)
                    if hint and not getattr(lead, "contact_email", None):
                        st.caption(f"💡 Their website uses addresses like this, so **{hint}** is likely, but unverified."
                                   " Only use it if you're comfortable it's right.")
                    elif getattr(lead, "contact_name", None) is None:
                        st.caption("Tip: type the name and save first. If their website shows how emails are formed,"
                                   " a likely address will be suggested.")
                    if saved:
                        err = save_contact(cn, f_name, f_role, f_li, f_email)
                        if err:
                            st.error(err)
                        else:
                            st.session_state["li_flash"] = "Contact saved" + (
                                ". This firm is now in Ready to email." if f_email.strip() else ".")
                            st.rerun()
                    if st.session_state.get("li_flash"):
                        st.success(st.session_state.pop("li_flash"))

                # Officers + integration hook
                officer_rows = "".join(
                    f'<div class="pe-officer"><span><span class="who">{esc(display_officer_name(o.name))}</span>'
                    f' <span style="color:var(--muted)">· {esc(o.role)}</span></span>'
                    f'<span class="since">since {esc((o.appointed_on or "N/A")[:4])}</span></div>'
                    for o in lead.officers[:6]
                ) or '<div class="pe-none">No active officers returned</div>'
                hook_items = "".join(f"<li>{esc(b)}</li>" for b in vert_cfg["pitch_bullets"])
                render_html(
                    f'<div class="pe-hook"><div class="h">Integration hook</div>'
                    f'<div class="t">{esc(vert_cfg["primary_hook"])}</div><ul>{hook_items}</ul></div>'
                    f'<div class="pe-panel"><div class="h">Registered officers ({len(lead.officers)})</div>{officer_rows}</div>'
                )

                if lead.website_reasons or lead.discovery_notes or lead.other_emails or lead.pages_checked:
                    with st.expander("How this was found"):
                        if lead.website_reasons:
                            st.markdown("**Website match:** " + "; ".join(lead.website_reasons))
                        for note in lead.discovery_notes:
                            st.markdown(f"- {note}")
                        if lead.other_emails:
                            st.markdown(
                                "**Third-party emails ignored** (agencies, regulators, portals): "
                                + ", ".join(f"`{e}`" for e in lead.other_emails)
                            )
                        if lead.pages_checked:
                            st.markdown("**Pages checked:** " + " · ".join(lead.pages_checked))

            with tab2:
                o1, o2 = st.columns(2)
                with o1:
                    st.session_state["opt_attach"] = st.toggle(
                        "Attach sector overview", value=st.session_state["opt_attach"], key="w_opt_attach",
                        help="Adds a line to the email and attaches the branded PDF to drafts.")
                with o2:
                    st.session_state["opt_switch"] = st.toggle(
                        "Mention Jan 2027 switch-off", value=st.session_state["opt_switch"], key="w_opt_switch")
                st.session_state["opt_branded"] = st.toggle(
                    "Branded email design", value=st.session_state["opt_branded"], key="w_opt_branded",
                    help="On: Fortlox Security header, feature tiles, switch-off callout and a demo button."
                         " Off: a plain, personal-looking email. Applies to drafts and Zoho sends.")
                attach_overview = st.session_state["opt_attach"]

                ensure_draft(item)
                # Push this firm's saved draft into the editor when switching firms or after a rebuild
                widget_sig = (cn, item["sig"], item.get("to_ver", 0))
                if st.session_state.get("email_widget_sig") != widget_sig:
                    st.session_state["email_to"] = item["to"]
                    st.session_state["email_subject"] = item["subject"]
                    st.session_state["email_body"] = item["body"]
                    st.session_state["email_widget_sig"] = widget_sig

                email_to = st.text_input("To", key="email_to", placeholder="name@firm.co.uk")
                email_subject = st.text_input("Subject", key="email_subject")
                edited_pitch = st.text_area("Email body", key="email_body", height=380)
                if email_to != item["to"]:
                    bump_queue_editor()  # Keep the review table in step with the To box
                item.update(to=email_to, subject=email_subject, body=edited_pitch)
                if lead.emails_found and len(lead.emails_found) > 1:
                    st.caption("Other addresses found: " + ", ".join(e for e in lead.emails_found if e != email_to))
                with st.expander("👀  Preview the email as they'll see it"):
                    components.html(_email_body_html(edited_pitch, email_subject), height=820, scrolling=True)

                mailto_url = build_mailto(email_to, email_subject, edited_pitch)
                friendly = draft_filename_part(lead.company_name)
                sector_slug = re.sub(r"[^A-Za-z0-9]+", "_", SECTOR_COPY.get(current_vert_name, {}).get("sector_plural", "sector")).strip("_")

                overview_name = f"Fortlox_Security_{sector_slug}_overview_{friendly}.pdf"
                overview_bytes = create_sector_overview_pdf(lead, current_vert_name) if attach_overview else None
                eml_bytes = build_eml_draft(
                    email_to, email_subject, edited_pitch,
                    attachments=[(overview_name, overview_bytes)] if overview_bytes else None,
                )
                st.download_button(
                    label=("📎  Email draft with PDF attached" if attach_overview else "📎  Email draft (.eml)"),
                    data=eml_bytes,
                    file_name=f"Email_to_{friendly}.eml",
                    mime="message/rfc822",
                    type="primary",
                    help="Downloads a ready-to-send draft. Click the downloaded file to open it in Outlook with the PDF attached.",
                    **FULL_WIDTH,
                )
                st.caption(
                    "Click the downloaded file to open it in Outlook as a new draft with the PDF attached,"
                    " then check it and hit Send. (Apple Mail: open it, then Message → Send Again.)"
                )
                b1, b2, b3 = st.columns(3)
                with b1:
                    st.link_button("✉️ Email only", mailto_url, **FULL_WIDTH,
                                   help="Opens your email app with the text filled in (no attachment). Handy for Gmail.")
                with b2:
                    if overview_bytes:
                        st.download_button(
                            label="⬇ Overview PDF",
                            data=overview_bytes,
                            file_name=overview_name,
                            mime="application/pdf",
                            **FULL_WIDTH,
                        )
                with b3:
                    st.download_button(
                        label="⬇ Lead dossier",
                        data=bytes(create_pdf_dossier(
                            lead=lead,
                            vertical_name=current_vert_name,
                            pitch_text=edited_pitch,
                            target_crms=vert_cfg["crms"],
                        )),
                        file_name=f"dossier_{friendly.lower()}.pdf",
                        mime="application/pdf",
                        **FULL_WIDTH,
                    )

                # Send this one firm through Zoho (adds it as a lead first if needed)
                if zoho_on() and not is_sent and zrec.get("status") != "customer":
                    try:
                        zpop = st.popover("🚀  Send this email via Zoho", key=f"zs1_{cn}_{st.session_state.get('sent_log_ver', 0)}",
                                          disabled=not email_to, **FULL_WIDTH)
                    except TypeError:
                        zpop = st.popover("🚀  Send this email via Zoho", disabled=not email_to, **FULL_WIDTH)
                    with zpop:
                        senders_, s_err_ = zoho_senders()
                        if s_err_:
                            st.caption(s_err_)
                        elif senders_:
                            idx_ = st.session_state.get("zs_from", 0)
                            frm_ = senders_[idx_] if 0 <= idx_ < len(senders_) else senders_[0]
                            st.markdown(f"Send to **{esc(email_to)}** from **{esc(frm_['email'])}**?")
                            st.caption("Logged on the Zoho lead with a note, and the status moves to Attempted to Contact.")
                            if st.button("Yes, send it now", type="primary", key=f"zs1_go_{cn}", **FULL_WIDTH):
                                send_via_zoho([cn], frm_, origin="dossier")
                                st.rerun()
                show_zoho_push_result("dossier")

                # Sent tick: saved to the permanent log, so it's there next time anyone opens the app
                sent_now = st.checkbox(
                    "✅  Handled: tick once this email has gone",
                    value=is_sent,
                    key=f"sent_chk_{cn}_{st.session_state.get('sent_log_ver', 0)}",
                    help="Saved permanently, and shows as Contacted in future searches.",
                )
                if sent_now != is_sent:
                    record_sent({cn: sent_record(item) if sent_now else None})
                    st.rerun()
                if is_sent:
                    rec = log_now[cn]
                    who = f" by {rec['sent_by']}" if rec.get("sent_by") else ""
                    st.caption(f"Marked sent{who} on {sent_label(rec)[2:]} to {rec.get('to') or 'unknown address'}.")

                tips = []
                if len(mailto_url) > 1900:
                    tips.append("This email is long, so the 'Email only' button may cut it short in some apps. The draft file isn't affected.")
                if not email_to:
                    tips.append("No email address found. Add one in the To box first.")
                for tip in tips:
                    st.caption("💡 " + tip)

                if st.toggle("Show copy-ready email", value=False, key="opt_copy"):
                    st.caption("Use the copy icon at the top-right of each box.")
                    st.code(email_subject, language=None)
                    st.code(edited_pitch, language=None)


# ---------------- Review queue (full width) ----------------
def _data_editor(df: pd.DataFrame, **kwargs):
    try:
        return st.data_editor(df, width="stretch", **kwargs)
    except Exception:
        return st.data_editor(df, use_container_width=True, **kwargs)


def _website_label(lead: ScrapedLead) -> str:
    return (lead.website_confidence or "Not found") if lead.website_url else "Not found"


def _mark_handled_popover(ids: List[str], label_noun: str, key: str) -> None:
    pop_kwargs = dict(disabled=not ids, **FULL_WIDTH)
    label = f"✅  Mark {len(ids)} as handled"
    try:  # A fresh key after each save closes the pop-up
        pop = st.popover(label, key=f"{key}_{st.session_state.get('sent_log_ver', 0)}", **pop_kwargs)
    except TypeError:
        pop = st.popover(label, **pop_kwargs)
    with pop:
        st.markdown(f"Mark **{len(ids)} selected {label_noun}** as handled?")
        st.caption("They'll show as contacted in future searches. You can untick any of them afterwards.")
        if st.button("Yes, mark as handled", type="primary", key=f"{key}_confirm", **FULL_WIDTH):
            record_sent({c: sent_record(queue[c]) for c in ids})
            st.rerun()


def _apply_editor(edited: pd.DataFrame, log_now: Dict[str, Any]) -> None:
    """Writes table edits back to the queue (selection, email, website, handled tick)."""
    sent_changes: Dict[str, Optional[Dict[str, Any]]] = {}
    moved = False
    for _, row in edited.iterrows():
        c = row["cn"]
        if c not in queue:
            continue
        if "Select" in row:
            queue[c]["include"] = bool(row["Select"])
        if "Contact" in row:
            shown = infer_contact_name_and_role(queue[c]["lead"], queue[c]["vertical"])[0]
            new_name = str(row["Contact"] or "").strip()
            if new_name and new_name != shown:
                save_contact(c, name=new_name)
                moved = True
        if "Email" in row:
            new_to = str(row["Email"] or "").strip()
            if new_to != queue[c]["to"]:
                if bool(new_to) != bool(queue[c]["to"]):
                    moved = True  # Firm changes group: redraw straight away
                if new_to:
                    err = save_contact(c, email=new_to)  # Saved permanently, like LinkedIn finds
                    if err:
                        st.session_state["table_error"] = err
                        moved = True
                        continue
                moved = moved or (bool(new_to) != bool(queue[c]["to"]))
                queue[c]["to"] = new_to
                queue[c]["to_ver"] = queue[c].get("to_ver", 0) + 1
        if "Website" in row:
            queue[c]["website_input"] = str(row["Website"] or "").strip()
        if bool(row["Handled"]) != (c in log_now):
            sent_changes[c] = sent_record(queue[c]) if row["Handled"] else None
    if sent_changes:
        record_sent(sent_changes)
        st.rerun()
    if moved:  # An email was added/removed, so the firm changes group
        bump_queue_editor()
        st.rerun()



def render_zoho_send_panel(ready_sel: List[str], log_now: Dict[str, Any]) -> None:
    with st.container(key="card-zoho-send"):
        render_html(
            '<div style="display:flex;align-items:center;gap:10px;margin:6px 0 2px 0">'
            f'<span style="font-weight:700;color:var(--text)">🚀 Send via Zoho</span>{chip("Logged on each lead", "accent")}</div>'
            '<div style="font-size:.8rem;color:var(--muted);margin-bottom:6px">Sends each pitch from Zoho with its PDF,'
            " logs it on the firm's Zoho lead, adds a note and sets the status to Attempted to Contact.</div>")
        show_zoho_push_result("panel")
        store = get_zoho_store()
        missing = [c for c in st.session_state.get("queue_order", []) if c in st.session_state.get("queue", {}) and c not in store]
        if missing and st.button(f"➕  Add {len(missing)} firm(s) not yet in Zoho", key="zoho_add_missing"):
            s_ = push_to_zoho_leads(missing)
            st.session_state["zoho_add_msg"] = (
                "Zoho needs a new key first: open Connect Zoho in the sidebar." if "permission" in s_["error"]
                else zoho_summary_text(s_) or ("Couldn't add: " + "; ".join(s_["error"][:3]) if s_["error"] else "Nothing new to add."))
            st.rerun()
        if st.session_state.get("zoho_add_msg"):
            st.info(st.session_state.pop("zoho_add_msg"))
        senders, err = zoho_senders()
        if err:
            if "permission" in err.lower() or "scope" in err.lower():
                st.info("Sending needs the full Zoho permissions: open Connect Zoho in the sidebar and connect again.")
            else:
                st.error(err)
            return
        if not senders:
            st.warning("Zoho didn't return any address to send from.")
            return
        st.selectbox("Send from", list(range(len(senders))), key="zs_from",
                     format_func=lambda i: f"{senders[i].get('user_name') or ''} <{senders[i]['email']}>".strip()
                     + (" · org address" if senders[i].get("type") == "org_email" else ""))
        ids = [c for c in ready_sel if (store.get(c) or {}).get("status") != "customer"]
        customers = len(ready_sel) - len(ids)
        if customers:
            st.caption(f"⚠️ {customers} selected firm(s) are already customers in Zoho, so they're left out.")
        sent_today = zoho_sent_today(log_now)
        left = max(0, ZOHO_SEND_LIMIT - sent_today)
        if len(ids) > left:
            st.warning(f"Zoho allows {ZOHO_SEND_LIMIT} emails a day and {sent_today} have gone today, so only the first {left} will be sent.")
            ids = ids[:left]
        label = f"🚀  Send {len(ids)} {'email' if len(ids) == 1 else 'emails'} via Zoho"
        try:
            pop = st.popover(label, key=f"zs_pop_{st.session_state.get('sent_log_ver', 0)}", disabled=not ids, **FULL_WIDTH)
        except TypeError:
            pop = st.popover(label, disabled=not ids, **FULL_WIDTH)
        with pop:
            idx = st.session_state.get("zs_from", 0)
            frm = senders[idx] if 0 <= idx < len(senders) else senders[0]
            st.markdown(f"Send **{len(ids)} emails** now from **{esc(frm['email'])}**?")
            st.caption("This can't be undone. Each is logged on its Zoho lead.")
            if st.button("Yes, send them now", type="primary", key="zs_confirm", **FULL_WIDTH):
                send_via_zoho(ids, frm)
                st.rerun()
        st.caption(f"Sent via Zoho today: {sent_today} of {ZOHO_SEND_LIMIT}.")


def _group_title(emoji: str, title: str, count: int, tone: str) -> None:
    render_html(
        f'<div style="display:flex;align-items:center;gap:10px;margin:18px 0 8px 0">'
        f'<span style="font-size:1.05rem">{emoji}</span>'
        f'<span style="font-weight:700;color:var(--text)">{esc(title)}</span>{chip(str(count), tone)}</div>'
    )


if queue:
    with st.container(key="card-queue"):
        log_now = get_sent_log()
        for c in queue_order:
            ensure_draft(queue[c])
        ready_all = [c for c in queue_order if c not in log_now and queue[c]["to"]]
        noemail_all = [c for c in queue_order if c not in log_now and not queue[c]["to"]]
        handled_all = [c for c in queue_order if c in log_now]
        ver = st.session_state.get("queue_editor_ver", 0)
        stamp = now_uk().strftime("%Y-%m-%d_%H%M")

        section_header(
            "04", "Review & send",
            f"{len(queue_order)} enriched · {len(ready_all)} ready to email · {len(noemail_all)} no email found"
            f" · {len(handled_all)} handled",
        )

        # ===== 1. Ready to email =====
        _group_title("✉️", "Ready to email", len(ready_all), "good")
        if not ready_all:
            st.caption("No firms with an email address yet. Check the No email found list below.")
        else:
            st.caption("These firms have an email address. Untick any you don't want, fix addresses inline, then export.")
            rdf = pd.DataFrame([{
                "cn": c,
                "Select": bool(queue[c]["include"]),
                "Handled": False,
                "Firm": lead_display_name(queue[c]["lead"]),
                "Contact": infer_contact_name_and_role(queue[c]["lead"], queue[c]["vertical"])[0],
                "Email": queue[c]["to"],
                "Phone": (queue[c]["lead"].phones_found or [""])[0],
                "LinkedIn": getattr(queue[c]["lead"], "linkedin_url", None) or linkedin_people_url(queue[c]["lead"]),
                "Website match": _website_label(queue[c]["lead"]),
                "Zoho": zoho_label(c),
            } for c in ready_all])
            edited = _data_editor(
                rdf, hide_index=True, num_rows="fixed", key=f"q_ready_{ver}",
                height=min(38 + 35 * len(rdf), 390),
                column_order=["Select", "Handled", "Firm", "Contact", "Email", "LinkedIn", "Phone", "Website match"],
                disabled=["Firm", "Phone", "LinkedIn", "Website match", "Zoho"],
                column_config={
                    "Select": st.column_config.CheckboxColumn("Select", width="small"),
                    "Handled": st.column_config.CheckboxColumn("Handled ✓", width="small", help="Tick once emailed. Saved permanently."),
                    "Firm": st.column_config.TextColumn("Firm", width="medium"),
                    "Contact": st.column_config.TextColumn("Contact ✎", width="small", help="Type the right first name or full name. Saved permanently."),
                    "Email": st.column_config.TextColumn("Email ✎", width="medium", help="Clear it to move the firm to No email found"),
                    "LinkedIn": st.column_config.LinkColumn("LinkedIn", width="small", display_text="Find ↗"),
                    "Phone": st.column_config.TextColumn("Phone", width="small"),
                    "Website match": st.column_config.TextColumn("Website", width="small"),
                },
            )
            _apply_editor(edited, log_now)
            ready_sel = [c for c in ready_all if queue[c]["include"]]
            st.caption("🛡️ Not checked against TPS/CTPS. Screen these contacts yourself before sending or calling.")
            r1, r2 = st.columns([1.4, 1])
            with r1:
                if ready_sel:
                    zip_bytes, n_written, _ = build_drafts_zip([queue[c] for c in ready_sel], st.session_state["opt_attach"])
                    st.download_button(
                        f"📦  Download {n_written} email {'draft' if n_written == 1 else 'drafts'} (.zip)",
                        data=zip_bytes,
                        file_name=f"Fortlox_Security_drafts_{stamp}.zip",
                        mime="application/zip", type="primary",
                        help="One ready-to-send Outlook draft per selected firm, each with its PDF attached.",
                        **FULL_WIDTH,
                    )
                else:
                    st.button("📦  Select firms to export", disabled=True, **FULL_WIDTH)
            with r2:
                _mark_handled_popover(ready_sel, "firms", "pop_ready")
            if zoho_on():
                render_zoho_send_panel(ready_sel, log_now)

        # ===== 2. No email found =====
        _group_title("📞", "No email found", len(noemail_all), "warn")
        if not noemail_all:
            st.caption("Every enriched firm has an email address.")
        else:
            st.caption(
                "Click **Find ↗** to look the firm up on LinkedIn, then type the right contact and business email"
                " straight into the row: the firm moves up to Ready to email with a personalised draft. Or send them"
                " to the shared call list, or paste their real website and hit Retry."
            )
            if st.session_state.get("table_error"):
                st.error(st.session_state.pop("table_error"))
            calls_now = get_call_list()
            ndf = pd.DataFrame([{
                "cn": c,
                "Select": bool(queue[c]["include"]),
                "Handled": False,
                "Firm": lead_display_name(queue[c]["lead"]),
                "Contact": infer_contact_name_and_role(queue[c]["lead"], queue[c]["vertical"])[0],
                "Phone": (queue[c]["lead"].phones_found or [""])[0],
                "LinkedIn": getattr(queue[c]["lead"], "linkedin_url", None) or linkedin_people_url(queue[c]["lead"]),
                "Email": "",
                "Website": queue[c].get("website_input") or (queue[c]["lead"].website_url or ""),
                "Zoho": zoho_label(c),
                "Why": ("📞 In call list" if c in calls_now else "No website" if not queue[c]["lead"].website_url
                        else "No email on site"),
            } for c in noemail_all])
            edited = _data_editor(
                ndf, hide_index=True, num_rows="fixed", key=f"q_noemail_{ver}",
                height=min(38 + 35 * len(ndf), 390),
                column_order=["Select", "Handled", "Firm", "LinkedIn", "Contact", "Email", "Phone", "Website", "Why"],
                disabled=["Firm", "Phone", "LinkedIn", "Why", "Zoho"],
                column_config={
                    "Select": st.column_config.CheckboxColumn("Select", width="small"),
                    "Handled": st.column_config.CheckboxColumn("Handled ✓", width="small", help="Tick once called or dealt with."),
                    "Firm": st.column_config.TextColumn("Firm", width="medium"),
                    "LinkedIn": st.column_config.LinkColumn("LinkedIn", width="small", display_text="Find ↗",
                                                            help="Opens a LinkedIn search for this firm's director in a new tab"),
                    "Contact": st.column_config.TextColumn("Contact ✎", width="small", help="Type the name you found. Saved permanently."),
                    "Phone": st.column_config.TextColumn("Phone", width="small"),
                    "Email": st.column_config.TextColumn("Add email ✎", width="medium", help="Type an address to move this firm to Ready to email"),
                    "Website": st.column_config.TextColumn("Website (editable)", width="medium", help="Paste the right website, then Retry"),
                    "Why": st.column_config.TextColumn("Why", width="small"),
                },
            )
            _apply_editor(edited, log_now)
            noemail_sel = [c for c in noemail_all if queue[c]["include"]]
            retry_ids = [
                c for c in noemail_sel
                if queue[c].get("website_input") and domain_of(queue[c]["website_input"]) != domain_of(queue[c]["lead"].website_url or "")
            ]
            to_call = [c for c in noemail_sel if c not in calls_now and queue[c]["lead"].phones_found]
            no_phone = [c for c in noemail_sel if c not in calls_now and not queue[c]["lead"].phones_found]
            if st.button(
                f"📞  Add {len(to_call)} to the call list" if to_call else "📞  Nothing new to add to the call list",
                type="primary", disabled=not to_call, key="add_to_calls", **FULL_WIDTH,
                help="Saves the selected firms (contact, phone and verified website) to the shared call list page.",
            ):
                save_calls({c: call_record_from_item(queue[c]) for c in to_call}, f"{len(to_call)} added")
                for c in to_call:
                    queue[c]["include"] = False
                bump_queue_editor()
                st.session_state["calls_flash"] = f"{len(to_call)} firms added to the call list."
                st.rerun()
            if st.session_state.get("calls_flash"):
                st.success(st.session_state.pop("calls_flash") + " Open **Call list** in the sidebar to start calling.")
            if no_phone:
                st.caption(f"💡 {len(no_phone)} selected {'firm has' if len(no_phone) == 1 else 'firms have'} no phone number,"
                           " so can't go on the call list. Paste their website and hit Retry to look again.")
            n1, n2, n3 = st.columns(3)
            with n1:
                if st.button(f"🔁  Retry {len(retry_ids)} with new website", disabled=not retry_ids, **FULL_WIDTH,
                             help="Re-scrapes the selected firms whose website you've changed."):
                    run_enrichment(
                        [{"Company Number": c, "Company Name": queue[c]["lead"].company_name} for c in retry_ids],
                        queue[retry_ids[0]]["vertical"],
                        manual_websites={c: queue[c]["website_input"] for c in retry_ids},
                    )
                    st.rerun()
            with n2:
                st.download_button(
                    f"📋  Call list: {len(noemail_sel)} (.csv)",
                    data=build_lead_list_csv([queue[c] for c in noemail_sel], log_now),
                    file_name=f"Fortlox_Security_call_list_{stamp}.csv",
                    mime="text/csv", disabled=not noemail_sel,
                    help="Selected firms with phone numbers, directors and websites. Opens in Excel.",
                    **FULL_WIDTH,
                )
            with n3:
                _mark_handled_popover(noemail_sel, "firms", "pop_noemail")

        # ===== 3. Handled =====
        if handled_all:
            with st.expander(f"✓ Handled ({len(handled_all)})"):
                hdf = pd.DataFrame([{
                    "cn": c,
                    "Handled": True,
                    "Status": f"{log_now[c].get('status') or 'Emailed'} {sent_label(log_now[c])[2:]}",
                    "Firm": lead_display_name(queue[c]["lead"]),
                    "Sent to": log_now[c].get("to") or "",
                    "By": log_now[c].get("sent_by") or "",
                } for c in handled_all])
                edited = _data_editor(
                    hdf, hide_index=True, num_rows="fixed", key=f"q_handled_{ver}",
                    column_order=["Handled", "Status", "Firm", "Sent to", "By"],
                    disabled=["Status", "Firm", "Sent to", "By"],
                    column_config={"Handled": st.column_config.CheckboxColumn("Handled ✓", width="small", help="Untick to move it back")},
                )
                _apply_editor(edited, log_now)

        # ===== Footer =====
        st.write("")
        f1, f2, _ = st.columns([1.3, 0.8, 1.4])
        with f1:
            st.download_button(
                f"📋  Full lead list: {len(queue_order)} firms (.csv)",
                data=build_lead_list_csv([queue[c] for c in queue_order], log_now),
                file_name=f"Fortlox_Security_lead_list_{stamp}.csv",
                mime="text/csv", **FULL_WIDTH,
            )
        with f2:
            if st.button("Clear queue", **FULL_WIDTH, help="Empty the review queue (handled ticks are kept)."):
                st.session_state["queue"] = {}
                st.session_state["queue_order"] = []
                bump_queue_editor()
                st.rerun()


# ---------------- Late-rendered pieces (reflect this run's state) ----------------
if queue:
    active_step = 4
elif st.session_state.get("selected_rows_data"):
    active_step = 3
elif st.session_state.get("discovered_leads"):
    active_step = 2
else:
    active_step = 1
render_html(hero_html(active_step), target=hero_slot)
render_html(
    '<div class="pe-stats">'
    f'<div class="pe-stat"><div class="v">{st.session_state["stat_firms"]}</div><div class="l">Firms</div></div>'
    f'<div class="pe-stat"><div class="v">{len(queue)}</div><div class="l">Enriched</div></div>'
    f'<div class="pe-stat"><div class="v">{len(get_sent_log())}</div><div class="l">Handled</div></div>'
    "</div>",
    target=sidebar_stats_slot,
)
