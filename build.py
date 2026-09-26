#!/usr/bin/env python3
"""
PiTheory website builder.

Source of truth (edit these through pitheory.in/admin, or by hand):
  content/questions/*.json   one file per question
  data/chapters.json         the 28 NCERT chapters
  data/site.json             phone, WhatsApp, fees, videos, testimonials...
  static/                    images, logo and question diagrams

Output: the complete website in site/  (upload this folder, or let GitHub build it)

  python3 build.py            normal build
  python3 build.py --inline   preview build: CSS, JS and images embedded in each page
"""
import base64, datetime, html, json, mimetypes, re, shutil, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "site"
INLINE = "--inline" in sys.argv
TODAY = datetime.date.today()

SITE = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))
CHAPTERS = json.loads((ROOT / "data/chapters.json").read_text(encoding="utf-8"))["chapters"]
URL = SITE["site_url"].rstrip("/")
e = lambda s: html.escape(str(s if s is not None else ""), quote=True)
WARN = []

# ----------------------------------------------------------------- helpers
GREEK = {"alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "Delta": "Δ", "theta": "θ", "lambda": "λ",
         "mu": "μ", "pi": "π", "rho": "ρ", "sigma": "σ", "omega": "ω", "Omega": "Ω", "varepsilon": "ε",
         "epsilon": "ε", "phi": "φ", "tau": "τ", "eta": "η", "nu": "ν", "times": "×", "cdot": "·",
         "circ": "°", "approx": "≈", "le": "≤", "ge": "≥", "infty": "∞", "propto": "∝", "to": "→"}


def plain(tex):
    """LaTeX text to readable plain text (titles, descriptions, share text)."""
    s = str(tex or "")
    for _ in range(3):
        s = re.sub(r"\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\[dt]?frac(\d)(\d)", r"\1/\2", s)
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"√(\1)", s)
    s = re.sub(r"\^\{?\\circ\}?", "°", s)
    s = re.sub(r"\\([A-Za-z]+)", lambda m: GREEK.get(m.group(1), ""), s)
    s = s.replace("\\ ", " ").replace("\\,", " ").replace("\\;", " ").replace("$", "")
    s = re.sub(r"\^\{([^{}]*)\}", r"^\1", s).replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def clip(s, n):
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def asset(path):
    """Public path, or an embedded data URI in --inline preview builds."""
    if not path or not INLINE or not path.startswith("/"):
        return path
    for base in (ROOT / "static", ROOT):
        f = base / path.lstrip("/")
        if f.is_file():
            mime = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
            if f.suffix == ".webp":
                mime = "image/webp"
            return f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()
    return path


def paras(text):
    parts = [p.strip() for p in re.split(r"\n\s*\n", str(text or "")) if p.strip()]
    return "".join(f"<p>{e(p).replace(chr(10), '<br>')}</p>" for p in parts)


def wa(msg="Hi Sir, I'd like to know about PiTheory physics classes."):
    return f"https://wa.me/{SITE['whatsapp']}?text=" + urllib.parse.quote(msg)


ICON = {
    "sol": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>',
    "save": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M19 21l-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2Z"/></svg>',
    "share": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/></svg>',
    "flag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 22V4a1 1 0 0 1 1-1h12l-2 5 2 5H5"/></svg>',
}
WA_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.9c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6a2.7 2.7 0 0 0 1.8-1.3 2.2 2.2 0 0 0 .1-1.3c0-.1-.2-.2-.4-.3Z"/></svg>'

# -------------------------------------------------------------- load data
def load_questions():
    by_slug = {c["slug"]: c for c in CHAPTERS}
    qs, seen = [], {}
    for f in sorted((ROOT / "content/questions").glob("*.json")):
        try:
            q = json.loads(f.read_text(encoding="utf-8"))
        except Exception as ex:
            WARN.append(f"{f.name}: not valid JSON ({ex}), skipped"); continue
        qid = str(q.get("id", "")).strip()
        where = qid or f.name
        if str(q.get("status", "published")).lower() != "published":
            continue
        if not re.fullmatch(r"(11|12)-\d{2}-\d{3}", qid):
            WARN.append(f"{where}: ID must look like 11-03-017, skipped"); continue
        if qid in seen:
            WARN.append(f"{where}: duplicate ID (also in {seen[qid]}), skipped"); continue
        c = by_slug.get(q.get("chapter"))
        if not c:
            WARN.append(f"{where}: unknown chapter '{q.get('chapter')}', skipped"); continue
        if not qid.startswith(c["code"] + "-"):
            WARN.append(f"{where}: ID should start with {c['code']} for {c['name']}, skipped"); continue
        if not str(q.get("question", "")).strip() or not str(q.get("solution", "")).strip():
            WARN.append(f"{where}: question or solution is empty, skipped"); continue
        qtype = q.get("type", "mcq")
        if qtype == "mcq":
            opts = [o for o in (q.get("options") or []) if (o.get("text") or o.get("image"))]
            if len(opts) != 4:
                WARN.append(f"{where}: MCQ needs exactly 4 options (has {len(opts)}), skipped"); continue
            if q.get("answer") not in ("A", "B", "C", "D"):
                WARN.append(f"{where}: MCQ answer must be A, B, C or D, skipped"); continue
            q["options"] = opts
        else:
            try:
                float(q.get("numerical_answer"))
            except (TypeError, ValueError):
                WARN.append(f"{where}: numerical answer must be a number, skipped"); continue
            if "NEET" in (q.get("exams") or []):
                WARN.append(f"{where}: note, NEET has no numerical-type questions (tag kept)")
        for key in ("diagram", "solution_diagram"):
            p = q.get(key) or ""
            if p.startswith("/") and not (ROOT / "static" / p.lstrip("/")).is_file():
                WARN.append(f"{where}: {key} file {p} not found (image hidden)"); q[key] = ""
        for o in q.get("options", []):
            p = o.get("image") or ""
            if p.startswith("/") and not (ROOT / "static" / p.lstrip("/")).is_file():
                WARN.append(f"{where}: option image {p} not found"); o["image"] = ""
        seen[qid] = f.name
        src = str(q.get("source") or "")
        q.update({
            "id": qid, "type": qtype, "c": c, "cls": c["class"], "exams": q.get("exams") or [],
            "difficulty": (q.get("difficulty") or "").capitalize(),
            "important": bool(q.get("important")),
            "pyq": bool(re.search(r"(NEET|JEE|AIPMT|AIEEE|AIIMS|EAMCET|KCET|MHT[- ]?CET|BITSAT|WBJEE|COMEDK).*\b(19|20)\d\d\b", src, re.I)),
            "plain": plain(q["question"]),
            "path": f"/physics/{c['slug']}/{qid}/",
        })
        q["url"] = URL + q["path"]
        qs.append(q)
    qs.sort(key=lambda x: x["id"])
    for c in CHAPTERS:
        c["items"] = [q for q in qs if q["c"] is c]
        c["path"] = f"/physics/{c['slug']}/"
    return qs


# ---------------------------------------------------------------- layout
def layout(title, desc, path, body, schema=(), current="", noindex=False):
    ver = TODAY.strftime("%Y%m%d")
    if INLINE:
        css = f"<style>{(ROOT / 'assets/style.css').read_text()}</style>"
        js = f"<script>{(ROOT / 'assets/app.js').read_text()}</script>"
    else:
        css = f'<link rel="stylesheet" href="/assets/style.css?v={ver}">'
        js = f'<script defer src="/assets/app.js?v={ver}"></script>'
    ga = ""
    if SITE.get("ga_id") and not INLINE:
        g = e(SITE["ga_id"])
        ga = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={g}"></script>'
              f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{g}');</script>")
    verify = f'<meta name="google-site-verification" content="{e(SITE["google_site_verification"])}">' if SITE.get("google_site_verification") and path == "/" else ""
    ld = "".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schema)
    pt = json.dumps({"whatsapp": SITE["whatsapp"], "leadForm": {"action": SITE.get("lead_form_action", ""), "fields": SITE.get("lead_form_fields", {})}})

    def nav(href, label, cls=""):
        cur = ' aria-current="page"' if current == href else ""
        return f'<a href="{href}" class="{cls}"{cur}>{label}</a>'

    social = "".join(f'<li><a href="{e(SITE[k])}" rel="noopener">{n}</a></li>' for k, n in (("youtube_channel", "YouTube"), ("instagram", "Instagram")) if SITE.get(k))
    phones = "".join(f'<li><a href="tel:{p.replace(" ", "")}">{e(p)}</a></li>' for p in SITE["phones"])
    return f"""<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{'<meta name="robots" content="noindex">' if noindex else f'<link rel="canonical" href="{e(URL + path)}">'}
{verify}
<meta property="og:type" content="website">
<meta property="og:site_name" content="PiTheory Learning">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(URL + path)}">
<meta property="og:image" content="{URL}/img/og.png">
<meta property="og:locale" content="en_IN">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#182084">
<link rel="icon" href="{asset('/img/mark.svg')}" type="image/svg+xml">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"></script>
{css}
{ld}
{ga}
<script>window.PT={pt};</script>
{js}
</head>
<body>
<header class="top">
  <div class="wrap">
    <a class="brand" href="/" aria-label="PiTheory Learning home">
      <img class="logo-light" src="{asset('/img/logo-navy.png')}" alt="PiTheory" width="669" height="158">
      <img class="logo-dark" src="{asset('/img/logo-white.png')}" alt="" width="669" height="158">
    </a>
    <nav class="nav" aria-label="Main">
      {nav("/physics/", "Chapters")}
      {nav("/questions/", "Search", "hide-sm")}
      {nav("/#classes", "Classes", "hide-sm")}
      {nav("/#faculty", "About", "hide-sm")}
      <a class="cta" href="/#demo">Free demo<span class="long"> class</span></a>
    </nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <div class="cols">
      <div>
        <img src="{asset('/img/logo-green.png')}" alt="PiTheory" width="669" height="158" loading="lazy">
        <p style="margin:0;max-width:34ch">NCERT chapter-wise NEET and JEE physics questions with step-by-step solutions, and online physics coaching.</p>
      </div>
      <div><h4>Practice</h4><ul><li><a href="/physics/">All chapters</a></li><li><a href="/questions/">Search questions</a></li><li><a href="/#faq">FAQ</a></li></ul></div>
      <div><h4>Contact</h4><ul>{phones}<li><a href="mailto:{e(SITE['email'])}">{e(SITE['email'])}</a></li>{social}</ul></div>
      <div><h4>PiTheory</h4><ul><li><a href="/#classes">Classes and fees</a></li><li><a href="/#faculty">About the faculty</a></li><li><a href="/privacy/">Privacy policy</a></li></ul></div>
    </div>
    <div class="legal"><span>© {TODAY.year} PiTheory Learning, Bangalore</span><span>All solutions written and checked by Sreeraj P</span></div>
  </div>
</footer>
<a class="wa-float" href="{e(wa())}" target="_blank" rel="noopener" aria-label="Chat on WhatsApp">{WA_SVG}</a>
</body>
</html>"""


# ---------------------------------------------------------------- pieces
def card(q, link=True):
    c = q["c"]
    tags = "".join(f'<span class="tag">{e(x)}</span>' for x in q["exams"])
    if q["pyq"]:
        tags += f'<span class="tag pyq">{e(q["source"])}</span>'
    if q["important"]:
        tags += '<span class="tag top">Top question</span>'
    if q["difficulty"]:
        tags += f'<span class="tag {e(q["difficulty"].lower())}">{e(q["difficulty"])}</span>'
    fig = ""
    if q.get("diagram"):
        fig = f'<figure class="q-fig"><img src="{e(asset(q["diagram"]))}" alt="{e(q.get("diagram_alt") or "Diagram for question " + q["id"])}" loading="lazy"></figure>'
    if q["type"] == "numerical":
        body = ('<p class="q-type">Numerical value type. Enter your answer.</p><div class="num"><input type="text" inputmode="decimal" '
                f'placeholder="Your answer" aria-label="Your answer for question {e(q["id"])}"><button class="btn" type="button" data-act="check">Check</button></div>')
        ans, ans_text = q["numerical_answer"], str(q["numerical_answer"])
    else:
        items = ""
        for i, o in enumerate(q["options"]):
            k = "ABCD"[i]
            img = f'<img class="opt-img" src="{e(asset(o["image"]))}" alt="Option {k}" loading="lazy">' if o.get("image") else ""
            txt = f'<span>{e(o.get("text", ""))}</span>' if o.get("text") else ""
            items += f'<li><button class="opt" type="button" data-k="{k}"><span class="bubble" aria-hidden="true">{k}</span><span class="opt-body">{txt}{img}</span><span class="sr">Option {k}</span></button></li>'
        body = f'<ol class="opts">{items}</ol>'
        ans = q["answer"]
        o = q["options"]["ABCD".index(ans)]
        ans_text = f"({ans}) {o.get('text') or 'see figure'}"
    sol_fig = f'<figure class="q-fig"><img src="{e(asset(q["solution_diagram"]))}" alt="Solution diagram for {e(q["id"])}" loading="lazy"></figure>' if q.get("solution_diagram") else ""
    open_link = f'<a class="link-btn primary" href="{q["path"]}">Open</a>' if link else ""
    return f"""<article class="q" id="q-{q['id']}" data-id="{q['id']}" data-answer="{e(ans)}" data-tol="{e(q.get('tolerance') or 0)}" data-type="{q['type']}" data-diff="{e(q['difficulty'])}" data-top="{int(q['important'])}" data-pyq="{int(q['pyq'])}" data-exams="{e('|'.join(q['exams']))}" data-chapter="{e(c['name'])}" data-plain="{e(clip(q['plain'], 180))}" data-url="{e(q['url'])}">
  <div class="q-head"><span class="q-id">Q {q['id']}</span>{tags}<span class="q-status" aria-live="polite"></span></div>
  <div class="q-text">{paras(q['question'])}</div>
  {fig}
  {body}
  <p class="feedback" aria-live="polite"></p>
  <div class="q-foot">
    <button class="link-btn primary" type="button" data-act="sol" aria-expanded="false">{ICON['sol']}<span>Show solution</span></button>
    <button class="link-btn" type="button" data-act="save" aria-pressed="false">{ICON['save']}<span>Save</span></button>
    <button class="link-btn" type="button" data-act="share">{ICON['share']}<span>Share</span></button>
    <button class="link-btn" type="button" data-act="report" title="Report a mistake in this question">{ICON['flag']}<span>Report</span></button>
    <span class="spacer"></span>{open_link}
  </div>
  <div class="solution" hidden>
    <p class="ans">Answer: <mark>{e(ans_text)}</mark></p>
    {paras(q['solution'])}{sol_fig}
    <p class="by"><img src="{asset('/img/sreeraj.webp')}" alt="" loading="lazy" width="30" height="30">Solution by Sreeraj P, M.Sc Physics</p>
  </div>
</article>"""


def help_box(chapter=None):
    head = f"Stuck on {chapter}?" if chapter else "Want a teacher to guide you?"
    msg = f"Hi Sir, I need help with {chapter}. I'd like a free demo class." if chapter else "Hi Sir, I'd like a free demo class."
    return f"""<aside class="help"><p><b>{e(head)}</b>Book a free demo class with Sreeraj Sir. Private and batch classes online, in English or Malayalam.</p>
<a class="btn green" href="{e(wa(msg))}" target="_blank" rel="noopener">Book on WhatsApp</a></aside>"""


def chapter_tile(c):
    n = len(c["items"])
    head = f'<span class="no">Chapter {c["number"]}</span><span class="nm">{e(c["name"])}</span>'
    if not n:
        return f'<li><div class="chap soon">{head}<span class="ct">Questions coming soon</span></div></li>'
    return (f'<li><a class="chap" href="{c["path"]}" data-progress="{c["code"]}" data-total="{n}">{head}'
            f'<span class="ct">{n} question{"s" if n != 1 else ""} · <span class="plabel">Not started yet</span></span>'
            f'<span class="bar"><i></i></span></a></li>')


def chapter_panels(tabs=True):
    out = ""
    for cls in ("11", "12"):
        tiles = "".join(chapter_tile(c) for c in CHAPTERS if c["class"] == cls)
        if tabs:
            out += f'<ul class="chap-grid" data-panel="{cls}" {"hidden" if cls == "12" else ""}>{tiles}</ul>'
        else:
            out += f'<h2 style="font-size:1.3rem;margin:28px 0 14px">Class {cls} Physics</h2><ul class="chap-grid">{tiles}</ul>'
    if tabs:
        out = ('<div class="tabs" role="tablist"><button type="button" role="tab" data-tab="11" aria-selected="true">Class 11 (+1)</button>'
               '<button type="button" role="tab" data-tab="12" aria-selected="false">Class 12 (+2)</button></div>') + out
    return out


def crumbs(items):
    parts = [f'<a href="{p}">{e(n)}</a>' if p else e(n) for n, p in items]
    return f'<nav class="crumbs" aria-label="Breadcrumb">{" › ".join(parts)}</nav>'


def crumb_schema(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": URL + p} for i, (n, p) in enumerate(items)]}


# ------------------------------------------------------------------ pages
FAQ = [
    ("What is PiTheory Learning?", "PiTheory Learning is a physics platform for NEET and JEE aspirants: a free NCERT chapter-wise question bank with step-by-step solutions, plus online classes with concept-based teaching, problem solving, doubt clearing and tests."),
    ("Who writes the solutions?", "Every solution is written and checked by Sreeraj P (M.Sc Physics, 10+ years teaching JEE and NEET). If you spot a mistake, tap Report on the question and it will be corrected."),
    ("Are these questions from previous years?", "Many are previous year questions from NEET, JEE Main and JEE Advanced, marked with the exam and year. Others are original practice questions written for the same pattern."),
    ("Is it suitable for both NEET and JEE?", "Yes. Each question is tagged NEET, JEE Main or JEE Advanced. Numerical value questions follow the JEE Main pattern."),
    ("Do you teach from the basics?", "Yes. Every chapter starts from fundamentals, then moves to exam-level problems."),
    ("Are there separate batches for Class 11, Class 12 and repeaters?", "Yes, for both NEET and JEE."),
    ("Is NCERT enough for NEET physics?", "NCERT is essential, but high scores also need extra conceptual practice and numerical problem solving. The question bank follows NCERT chapters so you can do both together."),
    ("How many physics questions should I solve daily?", "Regular daily practice matters more than long occasional sessions. Aim for 30 to 40 questions a day, including revision questions."),
    ("Do you teach students in the Gulf and abroad?", "Yes. Flexible timings for students in the UAE, Qatar, Kuwait, Oman, Bahrain and Saudi Arabia, and also Singapore, Malaysia, the USA, UK, Canada and Australia."),
    ("How do I join a class?", "Book a free demo class with the form on this page or message on WhatsApp. You get up to three trial classes before deciding."),
]


def page_home(qs):
    top = [q for q in qs if q["important"]] or qs
    qotd = top[TODAY.toordinal() % len(top)] if top else None
    live = sum(1 for c in CHAPTERS if c["items"])
    trust = [
        ('<path d="M12 2 4 5v6c0 5 3.4 9.5 8 11 4.6-1.5 8-6 8-11V5Z"/><path d="m9 12 2 2 4-4"/>', "Checked by a teacher", "Every solution is written and verified by Sreeraj P, not copied from forums."),
        ('<path d="M4 19.5V5a2 2 0 0 1 2-2h14v16H6.5A2.5 2.5 0 0 0 4 21.5Z"/>', "NCERT chapter-wise", "All 28 chapters of Class 11 and 12, in the order you study them."),
        ('<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>', "Attempt, then learn", "Pick an option or enter a value, get marked instantly, then read the method."),
        ('<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>', "Track your progress", "Your attempts and saved questions stay on your device, chapter by chapter."),
    ]
    trust_html = "".join(f'<div><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg><b>{t}</b><p>{d}</p></div>' for p, t, d in trust)
    quotes = ""
    if SITE.get("testimonials"):
        items = "".join(f'<figure class="quote"><p>“{e(t.get("text"))}”</p><footer><b>{e(t.get("name"))}</b>{" · " + e(t.get("detail")) if t.get("detail") else ""}</footer></figure>' for t in SITE["testimonials"])
        quotes = f'<section class="section"><div class="wrap"><p class="eyebrow">Students</p><h2>What students say</h2><div class="quotes">{items}</div></div></section>'
    vids = "".join(f'<button class="yt" type="button" data-id="{e(v)}" aria-label="Play PiTheory video {i + 1}" style="background-image:url(https://i.ytimg.com/vi/{e(v)}/hqdefault.jpg)"></button>' for i, v in enumerate(SITE.get("videos", [])))
    faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in FAQ)
    phones = "".join(f'<li><span>Call or WhatsApp</span><a href="tel:{p.replace(" ", "")}">{e(p)}</a></li>' for p in SITE["phones"])
    body = f"""
<section class="hero" style="--chalk:url('{asset('/img/chalkboard.webp')}')">
  <div class="wrap">
    <div>
      <h1>NEET and JEE physics questions, <em>solved the right way</em></h1>
      <p class="lede">NCERT chapter-wise questions with step-by-step solutions you can trust. Attempt each one, check your answer, then learn the method.</p>
      <form class="search" action="/questions/" method="get" role="search">
        <input type="search" name="s" placeholder="Search a topic, e.g. projectile" aria-label="Search questions">
        <button class="btn green" type="submit">Search</button>
      </form>
      <div class="actions">
        <a class="btn light" href="/physics/">Browse chapters</a>
        <a class="btn outline-light" href="#demo">Book a free demo class</a>
      </div>
      <ul class="stats">
        <li><b>{len(qs)}</b><span>solved questions</span></li>
        <li><b>{live}/28</b><span>NCERT chapters live</span></li>
        <li><b>{e(SITE['students_taught'])}</b><span>students taught</span></li>
      </ul>
    </div>
    <div>
      <p class="qotd-label">Question of the day</p>
      {card(qotd) if qotd else ''}
    </div>
  </div>
</section>

<section class="section" id="chapters">
  <div class="wrap">
    <p class="eyebrow">Question bank</p>
    <h2>Choose your chapter</h2>
    <p class="sub">MCQs in NEET and JEE format, and numerical value questions in the JEE pattern. Every question comes with a full worked solution.</p>
    {chapter_panels()}
  </div>
</section>

<section class="section alt">
  <div class="wrap">
    <p class="eyebrow">Why PiTheory</p>
    <h2>A physics source you can rely on</h2>
    <p class="sub">Built by a physics teacher for students who want correct answers and the reasoning behind them.</p>
    <div class="trust">{trust_html}</div>
  </div>
</section>

<section class="section" id="classes">
  <div class="wrap split">
    <div>
      <p class="eyebrow">Online classes</p>
      <h2>Private tuition and batch classes</h2>
      <p class="sub">Online physics coaching for NEET and JEE, planned around the student.</p>
      <ul class="facts">
        <li>Up to three trial classes before you decide</li>
        <li>Complete syllabus with PYQs, chapter tests and full mock exams</li>
        <li>Separate batches for Class 11, Class 12 and repeaters</li>
        <li>Classes in English and Malayalam</li>
        <li>Flexible timings for students in the UAE, Qatar, Kuwait, Saudi Arabia, Oman and Bahrain</li>
      </ul>
      <div class="prices">
        <div class="price"><span>Private tuition</span><b>{e(SITE['fee_private'])}</b> <small>{e(SITE['fee_private_unit'])}</small></div>
        <div class="price"><span>Batch classes</span><b>{e(SITE['fee_batch'])}</b> <small>{e(SITE['fee_batch_unit'])}</small></div>
      </div>
      <a class="btn" href="#demo">Book a free demo class</a>
    </div>
    <img class="photo" src="{asset('/img/student-model.webp')}" alt="Student building a wind turbine model" loading="lazy" width="1200" height="530">
  </div>
</section>

<section class="section alt" id="faculty">
  <div class="wrap split">
    <div class="faculty-photo"><img src="{asset('/img/sreeraj.webp')}" alt="Sreeraj P, physics faculty and founder of PiTheory Learning" loading="lazy" width="600" height="800"></div>
    <div>
      <p class="eyebrow">Your teacher</p>
      <h2>Sreeraj P</h2>
      <p class="sub" style="margin-bottom:18px">M.Sc Physics, University of Calicut. {e(SITE['years_experience'])} years teaching NEET and JEE physics.</p>
      <ul class="tags"><li>Narayana Group</li><li>Sri Chaitanya</li><li>Presidency Group</li><li>{e(SITE['students_taught'])} students taught</li></ul>
      <p>Has worked through all major study materials and previous year papers, and teaches every chapter from the concept up, so students can handle new problem types and not just familiar ones.</p>
      <a class="btn" href="{e(wa())}" target="_blank" rel="noopener">Talk to Sreeraj Sir</a>
    </div>
  </div>
</section>

{quotes}

<section class="section" id="videos">
  <div class="wrap">
    <p class="eyebrow">Free lessons</p>
    <h2>Watch a class</h2>
    <p class="sub">See how concepts are explained before you book.</p>
    <div class="videos">{vids}</div>
  </div>
</section>

<section class="section faq" id="faq">
  <div class="wrap narrow">
    <p class="eyebrow">FAQ</p>
    <h2>Frequently asked questions</h2>
    {faq}
  </div>
</section>

<section class="section" id="demo" style="padding-top:0">
  <div class="wrap">
    <div class="demo" style="--demo-img:url('{asset('/img/student-smiling.webp')}')">
      <div class="copy">
        <h2>Book a free demo class</h2>
        <p>Tell us about the student and we'll fix a time on WhatsApp.</p>
        <form class="form" id="demoForm" novalidate>
          <label for="dName">Student name</label>
          <input id="dName" name="name" autocomplete="name" required>
          <label for="dPhone">WhatsApp number</label>
          <input id="dPhone" name="phone" inputmode="tel" autocomplete="tel" placeholder="With country code if outside India" required>
          <p class="err" hidden>Add the student's name and a phone number.</p>
          <div class="row">
            <div><label for="dExam">Preparing for</label><select id="dExam" name="exam"><option>NEET</option><option>JEE</option><option>Both</option></select></div>
            <div><label for="dClass">Class</label><select id="dClass" name="cls"><option>11</option><option>12</option><option>Repeater</option><option>Class 10 or below</option></select></div>
          </div>
          <label for="dCountry">Where are you studying?</label>
          <select id="dCountry" name="country"><option>India</option><option>UAE</option><option>Saudi Arabia</option><option>Qatar</option><option>Kuwait</option><option>Oman</option><option>Bahrain</option><option>Other country</option></select>
          <button class="btn green" type="submit">Book on WhatsApp</button>
          <p class="done" hidden>WhatsApp is opening with your details. Press send and we'll reply with a time.</p>
          <p class="fine">We only use your number to arrange classes. <a href="/privacy/">Privacy policy</a></p>
        </form>
        <ul class="contact-lines">{phones}<li><span>Email</span><a href="mailto:{e(SITE['email'])}">{e(SITE['email'])}</a></li></ul>
      </div>
      <div class="pic" role="img" aria-label="Smiling student with books"></div>
    </div>
  </div>
</section>"""
    org = {"@context": "https://schema.org", "@type": "EducationalOrganization", "name": "PiTheory Learning", "url": URL + "/",
           "logo": URL + "/img/icon-512.png", "email": SITE["email"], "telephone": SITE["phones"][0].replace(" ", ""),
           "address": {"@type": "PostalAddress", "addressLocality": "Bangalore", "addressRegion": "Karnataka", "addressCountry": "IN"},
           "founder": {"@type": "Person", "name": "Sreeraj P", "jobTitle": "Physics Faculty", "image": URL + "/img/sreeraj.webp"}}
    web = {"@context": "https://schema.org", "@type": "WebSite", "name": "PiTheory Learning", "url": URL + "/",
           "potentialAction": {"@type": "SearchAction", "target": URL + "/questions/?s={search_term_string}", "query-input": "required name=search_term_string"}}
    faqs = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
    return layout("PiTheory Learning | NEET & JEE Physics Questions with Solutions, Chapter-wise",
                  "Free NCERT chapter-wise NEET and JEE physics questions with step-by-step solutions checked by a physics teacher. MCQs and JEE numerical questions for Class 11 and 12. Online physics tuition.",
                  "/", body, [org, web, faqs])


def page_hub():
    body = f"""
<div class="page-head"><div class="wrap">{crumbs([("Home", "/"), ("Chapters", "")])}
<h1>NEET and JEE physics, all 28 NCERT chapters</h1>
<p>Pick a chapter to practise its questions. Your progress in each chapter is saved on this device.</p></div></div>
<div class="wrap" style="padding-bottom:20px">{chapter_panels(tabs=False)}{help_box()}</div>"""
    return layout("Class 11 and 12 Physics Chapter-wise Questions for NEET & JEE | PiTheory",
                  "All 28 NCERT physics chapters for Class 11 and 12 with NEET and JEE questions and step-by-step solutions.",
                  "/physics/", body, [crumb_schema([("Home", "/"), ("Chapters", "/physics/")])], current="/physics/")


def page_chapter(c):
    items = c["items"]
    n_mcq = sum(1 for q in items if q["type"] == "mcq")
    n_num = len(items) - n_mcq
    exams = sorted({x for q in items for x in q["exams"]})
    intro = c.get("intro") or f"Class {c['class']} physics, NCERT chapter {c['number']}. Attempt each question, check your answer, then open the step-by-step solution."
    chips = [("all", "All"), ("todo", "Not attempted"), ("wrong", "Got wrong"), ("saved", "Saved"), ("top", "Top questions"), ("pyq", "PYQs")]
    if n_mcq and n_num:
        chips += [("mcq", "MCQ"), ("numerical", "Numerical")]
    chips += [(x, x) for x in exams]
    chip_html = "".join(f'<button class="chipbtn" type="button" data-filter="{e(k)}" aria-pressed="{"true" if k == "all" else "false"}">{e(l)}</button>' for k, l in chips)
    body = f"""
<div class="page-head" data-progress="{c['code']}" data-total="{len(items)}"><div class="wrap narrow">
  {crumbs([("Home", "/"), ("Chapters", "/physics/"), (c["name"], "")])}
  <h1>{e(c['name'])}: NEET and JEE questions with solutions</h1>
  <p>{e(intro)}</p>
  <div class="meta"><span><b>{len(items)}</b> questions</span><span><b>{n_mcq}</b> MCQ</span><span><b>{n_num}</b> numerical</span><span>Class {c['class']} · Chapter {c['number']}</span></div>
  <div class="progress"><span class="bar"><i></i></span><span class="plabel">Not started yet</span></div>
</div></div>
<div class="toolbar"><div class="wrap narrow">{chip_html}
  <select id="fDiff" aria-label="Difficulty"><option value="">Any level</option><option>Easy</option><option>Medium</option><option>Hard</option></select>
  <span class="count" id="qcount" aria-live="polite"></span></div></div>
<div class="wrap narrow" style="padding-top:24px">
  <div class="stack" id="qlist">{''.join(card(q) for q in items)}</div>
  <p class="empty" id="qempty" hidden>No questions match this filter.</p>
  <div class="more"><button class="btn ghost" id="moreBtn" type="button" hidden>Show more questions</button></div>
  {help_box(c['name'])}
</div>"""
    return layout(f"{c['name']} Questions for NEET & JEE with Solutions | Class {c['class']} Physics | PiTheory",
                  clip(f"{len(items)} {c['name']} physics questions for {' and '.join(exams) or 'NEET and JEE'} with step-by-step solutions. NCERT Class {c['class']}, chapter {c['number']}. MCQ and numerical, free.", 158),
                  c["path"], body, [crumb_schema([("Home", "/"), ("Chapters", "/physics/"), (c["name"], c["path"])])])


def page_question(q):
    c = q["c"]; items = c["items"]; i = items.index(q)
    prev_q = items[i - 1] if i > 0 else None
    next_q = items[i + 1] if i + 1 < len(items) else None
    related = [x for x in items if x is not q]
    related = (related[i:] + related[:i])[:6]
    rel = ""
    if related:
        rel = f'<section class="related"><h2>More {e(c["name"])} questions</h2><ul class="rows">' + "".join(
            f'<li><a href="{x["path"]}"><span class="rq">{e(clip(x["plain"], 150))}</span><span class="rm"><span>Q {x["id"]}</span><span>{e(", ".join(x["exams"]))}</span><span>{e(x["difficulty"])}</span></span></a></li>'
            for x in related) + "</ul></section>"
    pn = '<div class="pn">' + (f'<a class="link-btn" href="{prev_q["path"]}">← Previous</a>' if prev_q else "<span></span>") + \
         (f'<a class="link-btn primary" href="{next_q["path"]}">Next question →</a>' if next_q else "") + "</div>"
    exam_txt = " / ".join(q["exams"]) or "NEET / JEE"
    body = f"""
<div class="wrap narrow" style="padding-top:26px">
  {crumbs([("Home", "/"), (c["name"], c["path"]), ("Q " + q["id"], "")])}
  <h1 style="font-size:clamp(1.3rem,3vw,1.7rem);margin:10px 0 18px">{e(c['name'])} question for {e(exam_txt)}{' (' + e(q['source']) + ')' if q['pyq'] else ''}, with solution</h1>
  {card(q, link=False)}
  {pn}
  {help_box(c['name'])}
  {rel}
</div>"""
    if q["type"] == "mcq":
        k = "ABCD".index(q["answer"]); ans = f"({q['answer']}) {plain(q['options'][k].get('text', ''))}"
    else:
        ans = str(q["numerical_answer"])
    quiz = {"@context": "https://schema.org", "@type": "Quiz", "name": f"{c['name']} question {q['id']}",
            "educationalLevel": exam_txt, "about": {"@type": "Thing", "name": c["name"]},
            "author": {"@type": "Person", "name": "Sreeraj P"},
            "hasPart": [{"@type": "Question", "eduQuestionType": "Multiple choice" if q["type"] == "mcq" else "Short answer",
                         "text": q["plain"], "acceptedAnswer": {"@type": "Answer", "text": clip(f"{ans}. {plain(q['solution'])}", 500)}}]}
    title = f"{clip(q['plain'], 60)} | {c['name']} | PiTheory"
    desc = clip(f"{exam_txt} physics, {c['name']}: {q['plain']} Step-by-step solution.", 158)
    return layout(title, desc, q["path"], body, [quiz, crumb_schema([("Home", "/"), (c["name"], c["path"]), ("Q " + q["id"], q["path"])])])


def page_search(qs):
    live = [c for c in CHAPTERS if c["items"]]
    exams = sorted({x for q in qs for x in q["exams"]})
    rows = "".join(
        f'<li data-cls="{q["cls"]}" data-chapter="{e(q["c"]["slug"])}" data-type="{q["type"]}" data-exams="{e("|".join(q["exams"]))}" data-diff="{e(q["difficulty"])}" '
        f'data-text="{e((q["plain"] + " " + q["c"]["name"] + " " + q["id"] + " " + str(q.get("source") or "")).lower())}"><a href="{q["path"]}">'
        f'<span class="rq">{e(clip(q["plain"], 170))}</span><span class="rm"><span>Q {q["id"]}</span><span>{e(q["c"]["name"])}</span>'
        f'<span>{e(", ".join(q["exams"]))}</span><span>{"Numerical" if q["type"] == "numerical" else "MCQ"}</span><span>{e(q["difficulty"])}</span></span></a></li>'
        for q in qs)
    body = f"""
<div class="page-head"><div class="wrap">{crumbs([("Home", "/"), ("Search", "")])}
<h1>Search NEET and JEE physics questions</h1><p>{len(qs)} questions with step-by-step solutions.</p></div></div>
<div class="wrap" style="padding-top:24px">
  <div class="filters">
    <input id="fText" class="full" type="search" placeholder="Search by topic, words in the question, exam year or ID" aria-label="Search questions">
    <select id="fClass" aria-label="Class"><option value="">Class 11 and 12</option><option value="11">Class 11</option><option value="12">Class 12</option></select>
    <select id="fChapter" aria-label="Chapter"><option value="">All chapters</option>{''.join(f'<option value="{c["slug"]}">{e(c["name"])}</option>' for c in live)}</select>
    <select id="fType" aria-label="Question type"><option value="">MCQ and numerical</option><option value="mcq">MCQ</option><option value="numerical">Numerical</option></select>
    <select id="fExam" aria-label="Exam"><option value="">All exams</option>{''.join(f'<option>{e(x)}</option>' for x in exams)}</select>
    <select id="fDiff2" aria-label="Difficulty"><option value="">Any level</option><option>Easy</option><option>Medium</option><option>Hard</option></select>
  </div>
  <p class="count" id="count" style="color:var(--muted)" aria-live="polite">{len(qs)} questions</p>
  <ul class="rows" id="rows">{rows}</ul>
  <p class="empty" id="empty" hidden>No questions match. Try another chapter or clear the search.</p>
  {help_box()}
</div>"""
    return layout("Search NEET & JEE Physics Questions with Solutions | PiTheory",
                  f"Search {len(qs)} NEET and JEE physics questions by chapter, exam, type and difficulty. Step-by-step solutions.",
                  "/questions/", body, [crumb_schema([("Home", "/"), ("Search", "/questions/")])], current="/questions/")


def page_privacy():
    body = f"""<div class="wrap narrow prose">
<h1 class="page-h1">Privacy policy</h1>
<p>Last updated {TODAY.strftime('%d %B %Y')}.</p>
<h2>What we collect</h2><p>When you book a demo class, we receive the name, phone number, class, exam and location you enter, through WhatsApp{' and a form linked to our records' if SITE.get('lead_form_action') else ''}. We use these only to arrange classes and share course information. We do not sell or share them with anyone.</p>
<h2>Your practice data</h2><p>Your answers, progress and saved questions are stored only in your own browser. We cannot see them. Clearing your browser data removes them.</p>
<h2>Analytics</h2><p>We may use Google Analytics to count visits and see which pages are useful. It does not tell us who you are.</p>
<h2>Contact</h2><p>To ask about or delete your details, email <a href="mailto:{e(SITE['email'])}">{e(SITE['email'])}</a>.</p></div>"""
    return layout("Privacy policy | PiTheory Learning", "How PiTheory Learning handles your information.", "/privacy/", body)


def page_404():
    body = """<div class="wrap narrow prose"><h1 class="page-h1">This page isn't here</h1>
<p>The question may have moved. Search the question bank or pick a chapter.</p>
<p><a class="btn" href="/physics/">See all chapters</a></p></div>"""
    return layout("Page not found | PiTheory", "Page not found.", "/404.html", body, noindex=True)


# ------------------------------------------------------------------ build
def write(path, text):
    p = OUT / path.lstrip("/")
    if path.endswith("/"):
        p = p / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    qs = load_questions()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    if not INLINE:
        shutil.copytree(ROOT / "assets", OUT / "assets")
        shutil.copytree(ROOT / "static", OUT, dirs_exist_ok=True)
        shutil.copytree(ROOT / "admin", OUT / "admin")
    write("/", page_home(qs))
    write("/physics/", page_hub())
    write("/questions/", page_search(qs))
    write("/privacy/", page_privacy())
    write("/404.html", page_404())
    live = [c for c in CHAPTERS if c["items"]]
    for c in live:
        write(c["path"], page_chapter(c))
        for q in c["items"]:
            write(q["path"], page_question(q))
    urls = ["/", "/physics/", "/questions/"] + [c["path"] for c in live] + [q["path"] for q in qs] + ["/privacy/"]
    sm = "".join(f"<url><loc>{e(URL + u)}</loc><lastmod>{e(next((q.get('updated') for q in qs if q['path'] == u), None) or TODAY.isoformat())[:10]}</lastmod></url>" for u in urls)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n', encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {URL}/sitemap.xml\n", encoding="utf-8")
    (OUT / "CNAME").write_text(URL.split("//", 1)[1] + "\n", encoding="utf-8")
    print(f"Built {len(urls)} pages: {len(qs)} questions in {len(live)} of 28 chapters.")
    for c in CHAPTERS:
        print(f"  {c['code']}  {len(c['items']):>3}  {c['name']}")
    if WARN:
        print(f"\n{len(WARN)} note(s) to check:")
        for w in WARN:
            print("  - " + w)


if __name__ == "__main__":
    main()
