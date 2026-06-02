#!/usr/bin/env python3
"""Build HTML pages for Agent开发 Part 3 knowledge base."""
import os
import re
import html

# Paths
BASE = "/home/pez/knowledge-base/AI大模型/05-Agent开发"
OUT = "/home/pez/projects/ai-knowledge-hub/display/kb/ai-core"

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def md_to_html(md_text, skip_first_h1=True):
    """Convert markdown to HTML with basic rendering."""
    lines = md_text.split('\n')
    html_parts = []
    in_code = False
    code_lang = ''
    code_buf = []
    in_table = False
    table_rows = []
    in_list = False
    list_items = []
    list_type = ''
    first_h1_skipped = False

    def flush_list():
        nonlocal in_list, list_items, list_type
        if in_list and list_items:
            tag = list_type
            items_html = ''.join(f'<li>{process_inline(item)}</li>' for item in list_items)
            html_parts.append(f'<{tag}>{items_html}</{tag}>')
            list_items = []
            in_list = False

    def flush_table():
        nonlocal in_table, table_rows
        if table_rows:
            html_parts.append(render_table(table_rows))
            table_rows = []
            in_table = False

    def process_inline(text):
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'<code class="inline">\1</code>', text)
        # Links
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        # Wikilinks
        text = re.sub(r'\[\[([^\]]+)\]\]', lambda m: f'<a class="wikilink" href="#{m.group(1).replace(" ", "-")}">{m.group(1)}</a>', text)
        return text

    def render_table(rows):
        if not rows:
            return ''
        header = rows[0]
        body = rows[1:] if len(rows) > 1 else []
        ths = ''.join(f'<th>{process_inline(c)}</th>' for c in header)
        trs = []
        for i, row in enumerate(body):
            cls = ' class="alt"' if i % 2 == 1 else ''
            tds = ''.join(f'<td>{process_inline(c)}</td>' for c in row)
            trs.append(f'<tr{cls}>{tds}</tr>')
        return f'<table><thead><tr>{ths}</tr></thead><tbody>{"".join(trs)}</tbody></table>'

    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code:
                code_text = html.escape('\n'.join(code_buf))
                lang_class = f' class="language-{code_lang}"' if code_lang else ''
                html_parts.append(f'<div class="code-block"><pre><code{lang_class}>{code_text}</code></pre></div>')
                code_buf = []
                in_code = False
                code_lang = ''
            else:
                flush_list()
                flush_table()
                in_code = True
                code_lang = line.strip()[3:].strip()
            continue

        if in_code:
            code_buf.append(line)
            continue

        # Tables
        if '|' in line and line.strip().startswith('|'):
            flush_list()
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(re.match(r'^[-:]+$', c) for c in cells):
                continue  # Skip separator row
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            continue
        else:
            if in_table:
                flush_table()

        # Headers
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            flush_list()
            level = len(m.group(1))
            text = process_inline(m.group(2))
            # Skip first H1 if requested (we add it in section header)
            if level == 1 and skip_first_h1 and not first_h1_skipped:
                first_h1_skipped = True
                continue
            html_parts.append(f'<h{level}>{text}</h{level}>')
            continue

        # List items
        m = re.match(r'^(\s*)[-*]\s+(.*)', line)
        if m:
            if not in_list:
                in_list = True
                list_type = 'ul'
                list_items = []
            list_items.append(m.group(2))
            continue

        m = re.match(r'^(\s*)\d+\.\s+(.*)', line)
        if m:
            if not in_list:
                in_list = True
                list_type = 'ol'
                list_items = []
            list_items.append(m.group(2))
            continue

        # Blockquotes
        if line.strip().startswith('>'):
            flush_list()
            text = process_inline(line.strip()[1:].strip())
            html_parts.append(f'<blockquote>{text}</blockquote>')
            continue

        # Empty line
        if not line.strip():
            flush_list()
            continue

        # Regular paragraph
        flush_list()
        html_parts.append(f'<p>{process_inline(line)}</p>')

    flush_list()
    if in_table:
        flush_table()

    return '\n'.join(html_parts)

def extract_title(md_text, fallback="Untitled"):
    """Extract the first H1 title."""
    m = re.search(r'^#\s+(.+)', md_text, re.MULTILINE)
    if m:
        title = m.group(1).strip()
        # Remove difficulty markers
        title = re.sub(r'\s*[⭐🔥]+\s*', ' ', title).strip()
        return title
    # Try H2 as fallback
    m = re.search(r'^##\s+(.+)', md_text, re.MULTILINE)
    if m:
        title = m.group(1).strip()
        title = re.sub(r'\s*[⭐🔥🔗🧭💡📊]+\s*', ' ', title).strip()
        return title
    return fallback

def extract_difficulty(md_text):
    """Extract difficulty level from markers."""
    if '⭐⭐⭐' in md_text[:200]:
        return ('高级', '#e74c3c')
    if '⭐⭐' in md_text[:200]:
        return ('进阶', '#f39c12')
    if '⭐' in md_text[:200]:
        return ('入门', '#27ae60')
    return ('基础', '#3498db')

def build_toc(html_text):
    """Build table of contents from H2/H3 headers."""
    toc = []
    for m in re.finditer(r'<h([2-3])>(.*?)</h\1>', html_text):
        level = int(m.group(1))
        text = re.sub(r'<[^>]+>', '', m.group(2))  # Strip HTML tags
        anchor = text.replace(' ', '-').replace('.', '-')
        indent = (level - 2) * 20
        toc.append(f'<div class="toc-item" style="padding-left:{indent}px"><a href="#{anchor}">{text}</a></div>')
    return ''.join(toc)

# ============================================================
# SVG Diagrams
# ============================================================

MEMORY_SVG = '''<svg viewBox="0 0 900 500" xmlns="http://www.w3.org/2000/svg" class="diagram-svg">
<style>
  .box { fill: #ffffff; stroke: #0075de; stroke-width: 2; rx: 8; }
  .box-inner { fill: #f0f7ff; stroke: #0075de; stroke-width: 1; rx: 4; }
  .arrow { stroke: #0075de; stroke-width: 2; fill: none; marker-end: url(#arrowhead); }
  .arrow-dash { stroke: #888; stroke-width: 1.5; fill: none; stroke-dasharray: 6,4; marker-end: url(#arrowhead-gray); }
  .label { font-family: Inter, sans-serif; font-size: 14px; fill: #1a1a1a; text-anchor: middle; }
  .label-sm { font-family: Inter, sans-serif; font-size: 11px; fill: #666; text-anchor: middle; }
  .title { font-family: Inter, sans-serif; font-size: 16px; fill: #0075de; font-weight: bold; text-anchor: middle; }
</style>
<defs>
  <marker id="arrowhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#0075de"/></marker>
  <marker id="arrowhead-gray" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#888"/></marker>
</defs>

<!-- Title -->
<text x="450" y="30" class="title">Agent 记忆架构：短期 → 工作 → 长期 记忆流</text>

<!-- Short-term Memory -->
<rect x="30" y="60" width="220" height="180" class="box"/>
<text x="140" y="85" class="label" font-weight="bold">短期记忆 (Short-Term)</text>
<rect x="50" y="100" width="180" height="35" class="box-inner"/>
<text x="140" y="122" class="label-sm">滑动窗口 Sliding Window</text>
<rect x="50" y="145" width="180" height="35" class="box-inner"/>
<text x="140" y="167" class="label-sm">对话摘要 Summary</text>
<rect x="50" y="190" width="180" height="35" class="box-inner"/>
<text x="140" y="212" class="label-sm">Token 管理 & 压缩</text>

<!-- Working Memory -->
<rect x="340" y="60" width="220" height="180" class="box"/>
<text x="450" y="85" class="label" font-weight="bold">工作记忆 (Working)</text>
<rect x="360" y="100" width="180" height="35" class="box-inner"/>
<text x="450" y="122" class="label-sm">In-Context Memory</text>
<rect x="360" y="145" width="180" height="35" class="box-inner"/>
<text x="450" y="167" class="label-sm">System Instructions</text>
<rect x="360" y="190" width="180" height="35" class="box-inner"/>
<text x="450" y="212" class="label-sm">用户画像 & 偏好</text>

<!-- Long-term Memory -->
<rect x="650" y="60" width="220" height="180" class="box"/>
<text x="760" y="85" class="label" font-weight="bold">长期记忆 (Long-Term)</text>
<rect x="670" y="100" width="180" height="35" class="box-inner"/>
<text x="760" y="122" class="label-sm">向量数据库 ChromaDB</text>
<rect x="670" y="145" width="180" height="35" class="box-inner"/>
<text x="760" y="167" class="label-sm">知识图谱 Neo4j</text>
<rect x="670" y="190" width="180" height="35" class="box-inner"/>
<text x="760" y="212" class="label-sm">SQLite / Redis 缓存</text>

<!-- Arrows -->
<path d="M250,150 L340,150" class="arrow"/>
<path d="M560,150 L650,150" class="arrow"/>
<text x="295" y="140" class="label-sm">Swap</text>
<text x="605" y="140" class="label-sm">Store</text>

<!-- Retrieval Pipeline -->
<rect x="100" y="280" width="700" height="80" class="box" fill="#f8f9fa"/>
<text x="450" y="305" class="label" font-weight="bold">记忆检索管线 (Memory Retrieval Pipeline)</text>
<text x="450" y="325" class="label-sm">BM25 + 向量检索 → 时间衰减 → 重要性加权 → Top-K</text>
<text x="450" y="345" class="label-sm">Score = α·Relevance + β·Temporal + γ·Importance + δ·Frequency</text>

<!-- Decay curve -->
<rect x="100" y="390" width="340" height="90" class="box" fill="#fff8f0"/>
<text x="270" y="415" class="label" font-weight="bold">时间衰减策略</text>
<text x="270" y="435" class="label-sm">指数衰减 e^(-λt) | 线性衰减 1-t/T</text>
<text x="270" y="455" class="label-sm">对数衰减 1/(1+ln(1+t)) | 阶梯衰减</text>

<!-- Memory Consolidation -->
<rect x="460" y="390" width="340" height="90" class="box" fill="#f0fff0"/>
<text x="630" y="415" class="label" font-weight="bold">记忆整合 (Consolidation)</text>
<text x="630" y="435" class="label-sm">去重合并 → 低重要性遗忘 → 更新权重</text>
<text x="630" y="455" class="label-sm">MemGPT: Agent 自主管理记忆</text>
</svg>'''

WORKFLOW_SVG = '''<svg viewBox="0 0 900 550" xmlns="http://www.w3.org/2000/svg" class="diagram-svg">
<style>
  .wf-trigger { fill: #fff3e0; stroke: #f39c12; stroke-width: 2; rx: 8; }
  .wf-llm { fill: #f0f7ff; stroke: #0075de; stroke-width: 2; rx: 8; }
  .wf-action { fill: #e8f5e9; stroke: #27ae60; stroke-width: 2; rx: 8; }
  .wf-cond { fill: #fce4ec; stroke: #e74c3c; stroke-width: 2; rx: 8; }
  .wf-kb { fill: #f3e5f5; stroke: #8e44ad; stroke-width: 2; rx: 8; }
  .wf-output { fill: #e0f2f1; stroke: #00897b; stroke-width: 2; rx: 8; }
  .wf-arrow { stroke: #555; stroke-width: 1.5; fill: none; marker-end: url(#wf-arrow); }
  .wf-label { font-family: Inter, sans-serif; font-size: 12px; fill: #1a1a1a; text-anchor: middle; }
  .wf-title { font-family: Coze/Dify, sans-serif; font-size: 16px; fill: #0075de; font-weight: bold; text-anchor: middle; }
  .wf-type { font-family: Inter, sans-serif; font-size: 10px; fill: #888; text-anchor: middle; }
</style>
<defs>
  <marker id="wf-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker>
</defs>

<text x="450" y="25" class="wf-title">Coze / Dify 工作流构建器：节点、边、触发器、动作</text>

<!-- Trigger -->
<rect x="50" y="50" width="140" height="50" class="wf-trigger"/>
<text x="120" y="72" class="wf-label" font-weight="bold">触发器 Trigger</text>
<text x="120" y="88" class="wf-type">用户输入 / API / 定时</text>

<path d="M190,75 L230,75" class="wf-arrow"/>

<!-- LLM Node -->
<rect x="230" y="50" width="140" height="50" class="wf-llm"/>
<text x="300" y="72" class="wf-label" font-weight="bold">LLM 节点</text>
<text x="300" y="88" class="wf-type">GPT / DeepSeek / Qwen</text>

<path d="M370,75 L410,75" class="wf-arrow"/>

<!-- Knowledge Base -->
<rect x="410" y="50" width="140" height="50" class="wf-kb"/>
<text x="480" y="72" class="wf-label" font-weight="bold">知识库 RAG</text>
<text x="480" y="88" class="wf-type">向量检索 / Embedding</text>

<path d="M550,75 L590,75" class="wf-arrow"/>

<!-- Condition -->
<rect x="590" y="50" width="140" height="50" class="wf-cond"/>
<text x="660" y="72" class="wf-label" font-weight="bold">条件分支</text>
<text x="660" y="88" class="wf-type">IF/ELSE / Switch</text>

<path d="M660,100 L660,140" class="wf-arrow"/>
<path d="M660,140 L300,140" class="wf-arrow"/>

<!-- Action 1 -->
<rect x="200" y="120" width="120" height="45" class="wf-action"/>
<text x="260" y="140" class="wf-label" font-weight="bold">工具调用</text>
<text x="260" y="155" class="wf-type">HTTP / Plugin</text>

<path d="M320,142 L380,142" class="wf-arrow"/>

<!-- Action 2 -->
<rect x="380" y="120" width="120" height="45" class="wf-action"/>
<text x="440" y="140" class="wf-label" font-weight="bold">代码执行</text>
<text x="440" y="155" class="wf-type">Python / JS</text>

<path d="M440,165 L440,195" class="wf-arrow"/>

<!-- Template -->
<rect x="370" y="195" width="140" height="50" class="wf-llm"/>
<text x="440" y="217" class="wf-label" font-weight="bold">模板 Template</text>
<text x="440" y="233" class="wf-type">Jinja2 / 变量替换</text>

<path d="M440,245 L440,275" class="wf-arrow"/>

<!-- Output -->
<rect x="370" y="275" width="140" height="50" class="wf-output"/>
<text x="440" y="297" class="wf-label" font-weight="bold">输出 Response</text>
<text x="440" y="313" class="wf-type">文本 / JSON / 文件</text>

<!-- Node Types Legend -->
<rect x="50" y="350" width="800" height="180" fill="none" stroke="#ddd" stroke-width="1" rx="8"/>
<text x="450" y="375" class="wf-title">节点类型与功能</text>

<rect x="70" y="390" width="160" height="40" class="wf-trigger"/>
<text x="150" y="415" class="wf-label">触发器节点</text>
<text x="150" y="425" class="wf-type">启动工作流</text>

<rect x="250" y="390" width="160" height="40" class="wf-llm"/>
<text x="330" y="415" class="wf-label">LLM 节点</text>
<text x="330" y="425" class="wf-type">AI 推理生成</text>

<rect x="430" y="390" width="160" height="40" class="wf-action"/>
<text x="510" y="415" class="wf-label">动作节点</text>
<text x="510" y="425" class="wf-type">工具/代码执行</text>

<rect x="610" y="390" width="160" height="40" class="wf-cond"/>
<text x="690" y="415" class="wf-label">条件节点</text>
<text x="690" y="425" class="wf-type">分支/循环逻辑</text>

<rect x="70" y="450" width="160" height="40" class="wf-kb"/>
<text x="150" y="475" class="wf-label">知识库节点</text>
<text x="150" y="485" class="wf-type">RAG 检索增强</text>

<rect x="250" y="450" width="160" height="40" class="wf-output"/>
<text x="330" y="475" class="wf-label">输出节点</text>
<text x="330" y="485" class="wf-type">返回结果</text>

<rect x="430" y="450" width="160" height="40" fill="#e8e8e8" stroke="#888" stroke-width="1" rx="8"/>
<text x="510" y="475" class="wf-label">变量系统</text>
<text x="510" y="485" class="wf-type">会话/环境变量</text>

<rect x="610" y="450" width="160" height="40" fill="#e8e8e8" stroke="#888" stroke-width="1" rx="8"/>
<text x="690" y="475" class="wf-label">API 集成</text>
<text x="690" y="485" class="wf-type">外部服务调用</text>
</svg>'''

# ============================================================
# HTML Template
# ============================================================

def build_html(title, sections, sidebar_items, svg_diagram=None):
    """Build a complete HTML page."""

    # Build sidebar
    sidebar_html = '<nav class="sidebar">\n'
    sidebar_html += f'<div class="sidebar-title">{title}</div>\n'
    for section in sidebar_items:
        sidebar_html += f'<div class="sidebar-section">\n'
        sidebar_html += f'<div class="sidebar-section-title">{section["title"]}</div>\n'
        for item in section["items"]:
            sidebar_html += f'<a href="#{item["id"]}" class="sidebar-link">{item["text"]}</a>\n'
        sidebar_html += '</div>\n'
    sidebar_html += '</nav>\n'

    # Build main content
    main_html = '<main class="content">\n'

    # SVG diagram if provided
    if svg_diagram:
        main_html += f'<div class="diagram-container">\n{svg_diagram}\n</div>\n'

    # Sections
    for section in sections:
        main_html += f'<section id="{section["id"]}" class="doc-section">\n'
        main_html += f'<h1>{section["title"]}</h1>\n'

        # Difficulty badge
        if "difficulty" in section:
            label, color = section["difficulty"]
            main_html += f'<span class="difficulty-badge" style="background:{color}20;color:{color};border:1px solid {color}40">{label}</span>\n'

        # TOC
        toc = build_toc(section["html"])
        if toc:
            main_html += f'<div class="toc-container">\n<div class="toc-title">目录</div>\n{toc}\n</div>\n'

        main_html += section["html"]
        main_html += '\n</section>\n'

    main_html += '</main>\n'

    # Complete HTML
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: 'Inter', 'Noto Sans SC', -apple-system, sans-serif;
  font-size: 16px;
  line-height: 1.7;
  color: #1a1a1a;
  background: #ffffff;
}}

/* Sidebar */
.sidebar {{
  position: fixed;
  top: 0;
  left: 0;
  width: 280px;
  height: 100vh;
  background: #f7f7f5;
  border-right: 1px solid rgba(0,0,0,0.1);
  overflow-y: auto;
  padding: 20px 0;
  z-index: 100;
}}
.sidebar-title {{
  font-size: 14px;
  font-weight: 700;
  color: #0075de;
  padding: 0 16px 12px;
  border-bottom: 1px solid rgba(0,0,0,0.1);
  margin-bottom: 8px;
}}
.sidebar-section {{
  padding: 8px 0;
}}
.sidebar-section-title {{
  font-size: 11px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 16px 2px;
}}
.sidebar-link {{
  display: block;
  padding: 4px 16px 4px 24px;
  font-size: 13px;
  color: #333;
  text-decoration: none;
  transition: background 0.15s;
}}
.sidebar-link:hover {{
  background: rgba(0,117,222,0.08);
  color: #0075de;
}}

/* Main Content */
.content {{
  margin-left: 280px;
  padding: 40px 60px;
  max-width: 900px;
}}

/* Typography */
h1 {{
  font-size: 44px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 16px;
  color: #1a1a1a;
}}
h2 {{
  font-size: 28px;
  font-weight: 600;
  margin-top: 40px;
  margin-bottom: 12px;
  color: #1a1a1a;
  border-bottom: 1px solid rgba(0,0,0,0.1);
  padding-bottom: 8px;
}}
h3 {{
  font-size: 22px;
  font-weight: 600;
  margin-top: 32px;
  margin-bottom: 8px;
}}
h4 {{
  font-size: 18px;
  font-weight: 600;
  margin-top: 24px;
  margin-bottom: 8px;
}}

/* Paragraphs */
p {{
  margin-bottom: 12px;
  line-height: 1.7;
}}

/* Links */
a {{
  color: #0075de;
  text-decoration: none;
}}
a:hover {{
  text-decoration: underline;
}}
.wikilink {{
  color: #0075de;
  background: rgba(0,117,222,0.08);
  padding: 1px 4px;
  border-radius: 3px;
}}

/* Code */
code.inline {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  background: #f6f5f4;
  padding: 2px 6px;
  border-radius: 3px;
}}
.code-block {{
  background: #f6f5f4;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 6px;
  margin: 16px 0;
  overflow: hidden;
}}
.code-block pre {{
  padding: 16px;
  overflow-x: auto;
  margin: 0;
}}
.code-block code {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
}}

/* Tables */
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 14px;
}}
th {{
  background: #f7f7f5;
  font-weight: 600;
  text-align: left;
  padding: 10px 12px;
  border-bottom: 2px solid rgba(0,0,0,0.1);
}}
td {{
  padding: 10px 12px;
  border-bottom: 1px solid rgba(0,0,0,0.1);
}}
tr.alt {{
  background: #fafafa;
}}

/* Blockquotes */
blockquote {{
  border-left: 3px solid #0075de;
  padding: 8px 16px;
  margin: 12px 0;
  background: #f0f7ff;
  color: #333;
}}

/* Lists */
ul, ol {{
  margin: 8px 0 12px 24px;
}}
li {{
  margin-bottom: 4px;
}}

/* Diagram */
.diagram-container {{
  margin: 24px 0;
  padding: 20px;
  background: #fafafa;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 8px;
}}
.diagram-svg {{
  width: 100%;
  height: auto;
}}

/* Difficulty Badge */
.difficulty-badge {{
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 16px;
}}

/* TOC */
.toc-container {{
  background: #f7f7f5;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 6px;
  padding: 16px;
  margin: 16px 0 24px;
}}
.toc-title {{
  font-size: 14px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}}
.toc-item {{
  padding: 2px 0;
}}
.toc-item a {{
  font-size: 13px;
  color: #555;
}}
.toc-item a:hover {{
  color: #0075de;
}}

/* Section */
.doc-section {{
  margin-bottom: 60px;
  padding-bottom: 40px;
  border-bottom: 1px solid rgba(0,0,0,0.1);
}}
.doc-section:last-child {{
  border-bottom: none;
}}
</style>
</head>
<body>
{sidebar_html}
{main_html}
</body>
</html>'''

# ============================================================
# Build Page 1: Agent Memory System
# ============================================================
print("Building agent-memory.html...")

memory_files = [
    (f"{BASE}/12-Agent记忆系统/01-短期记忆与对话管理.md", "短期记忆与对话管理"),
    (f"{BASE}/12-Agent记忆系统/02-长期记忆与向量存储.md", "长期记忆与向量存储"),
    (f"{BASE}/12-Agent记忆系统/03-MemGPT与记忆架构.md", "MemGPT与记忆架构"),
    (f"{BASE}/12-Agent记忆系统/04-记忆检索与衰减策略.md", "记忆检索与衰减策略"),
]

memory_sections = []
memory_sidebar = [{"title": "Agent 记忆系统", "items": []}]

for path, name in memory_files:
    content = read_file(path)
    title = extract_title(content)
    difficulty = extract_difficulty(content)
    section_id = name.replace(" ", "-")
    html_content = md_to_html(content)

    memory_sections.append({
        "id": section_id,
        "title": title,
        "html": html_content,
        "difficulty": difficulty,
    })
    memory_sidebar[0]["items"].append({"id": section_id, "text": title})

with open(f"{OUT}/agent-memory.html", 'w', encoding='utf-8') as f:
    f.write(build_html("Agent 记忆系统", memory_sections, memory_sidebar, MEMORY_SVG))

print("Done: agent-memory.html")

# ============================================================
# Build Page 2: Agent Evaluation
# ============================================================
print("Building agent-eval.html...")

eval_files = [
    (f"{BASE}/13-Agent评估与基准/01-评估维度与指标体系.md", "评估维度与指标体系"),
    (f"{BASE}/13-Agent评估与基准/02-基准测试GAIA-AgentBench.md", "基准测试GAIA-AgentBench"),
    (f"{BASE}/13-Agent评估与基准/03-LLM-as-Judge评估方法.md", "LLM-as-Judge评估方法"),
]

eval_sections = []
eval_sidebar = [{"title": "Agent 评估与基准", "items": []}]

for path, name in eval_files:
    content = read_file(path)
    title = extract_title(content)
    difficulty = extract_difficulty(content)
    section_id = name.replace(" ", "-")
    html_content = md_to_html(content)

    eval_sections.append({
        "id": section_id,
        "title": title,
        "html": html_content,
        "difficulty": difficulty,
    })
    eval_sidebar[0]["items"].append({"id": section_id, "text": title})

with open(f"{OUT}/agent-eval.html", 'w', encoding='utf-8') as f:
    f.write(build_html("Agent 评估与基准", eval_sections, eval_sidebar))

print("Done: agent-eval.html")

# ============================================================
# Build Page 3: Advanced Prompt Patterns
# ============================================================
print("Building agent-advanced-prompt.html...")

prompt_files = [
    (f"{BASE}/14-高级Prompt模式/01-ReAct推理行动循环.md", "ReAct推理行动循环"),
    (f"{BASE}/14-高级Prompt模式/02-Plan-and-Execute模式.md", "Plan-and-Execute模式"),
    (f"{BASE}/14-高级Prompt模式/03-Reflexion自我反思.md", "Reflexion自我反思"),
    (f"{BASE}/14-高级Prompt模式/04-Tree-of-Thoughts思维树.md", "Tree-of-Thoughts思维树"),
    (f"{BASE}/14-高级Prompt模式/05-LATS语言Agent树搜索.md", "LATS语言Agent树搜索"),
]

prompt_sections = []
prompt_sidebar = [{"title": "高级 Prompt 模式", "items": []}]

for path, name in prompt_files:
    content = read_file(path)
    title = extract_title(content)
    difficulty = extract_difficulty(content)
    section_id = name.replace(" ", "-")
    html_content = md_to_html(content)

    prompt_sections.append({
        "id": section_id,
        "title": title,
        "html": html_content,
        "difficulty": difficulty,
    })
    prompt_sidebar[0]["items"].append({"id": section_id, "text": title})

with open(f"{OUT}/agent-advanced-prompt.html", 'w', encoding='utf-8') as f:
    f.write(build_html("高级 Prompt 模式", prompt_sections, prompt_sidebar))

print("Done: agent-advanced-prompt.html")

# ============================================================
# Build Page 4: Coze-Dify + ByteDance Practice
# ============================================================
print("Building coze-dify.html...")

coze_files = [
    (f"{BASE}/Coze-Dify/1.1 Coze平台介绍.md", "Coze平台介绍"),
    (f"{BASE}/Coze-Dify/1.2 Coze平台入门实战.md", "Coze平台入门实战"),
    (f"{BASE}/Coze-Dify/1.1 Dify平台介绍.md", "Dify平台介绍"),
    (f"{BASE}/Coze-Dify/1.2Dify的入门实战.md", "Dify入门实战"),
    (f"{BASE}/Coze-Dify/2.1 Docker的原理和基本使用.md", "Docker原理和基本使用"),
    (f"{BASE}/Coze-Dify/2.1 私有数据访问.md", "私有数据访问"),
    (f"{BASE}/Coze-Dify/2.2-dify接入知识库.md", "Dify接入知识库"),
    (f"{BASE}/Coze-Dify/2.3-dify接入外部知识库ragflow.md", "Dify接入外部知识库RAGFlow"),
    (f"{BASE}/Coze-Dify/2.4 Coze API调用.md", "Coze API调用"),
    (f"{BASE}/Coze-Dify/DeepSeek+Dify搭建工作流.md", "DeepSeek+Dify搭建工作流"),
    (f"{BASE}/Coze-Dify/README.md", "RAGFlow SDK"),
    (f"{BASE}/Coze-Dify/README_CN.md", "Model Runtime"),
    (f"{BASE}/Coze-Dify/02-简历.md", "简历优化建议", "简历优化建议"),
    (f"{BASE}/Coze-Dify/杰-两年-本科-大模型开发.md", "简历优化案例", "简历优化案例"),
    (f"{BASE}/字节跳动实践/字节跳动Agent实践手册.md", "字节跳动Agent实践手册"),
]

coze_sections = []
coze_sidebar = [
    {"title": "Coze 平台", "items": []},
    {"title": "Dify 平台", "items": []},
    {"title": "进阶功能", "items": []},
    {"title": "参考文档", "items": []},
]

for i, item in enumerate(coze_files):
    if len(item) == 3:
        path, name, fallback_title = item
    else:
        path, name = item
        fallback_title = name
    content = read_file(path)
    title = extract_title(content, fallback=fallback_title)
    difficulty = extract_difficulty(content)
    section_id = name.replace(" ", "-").replace("+", "-")
    html_content = md_to_html(content)

    coze_sections.append({
        "id": section_id,
        "title": title,
        "html": html_content,
        "difficulty": difficulty,
    })

    # Assign to sidebar section
    if i < 2:
        coze_sidebar[0]["items"].append({"id": section_id, "text": title})
    elif i < 4:
        coze_sidebar[1]["items"].append({"id": section_id, "text": title})
    elif i < 10:
        coze_sidebar[2]["items"].append({"id": section_id, "text": title})
    else:
        coze_sidebar[3]["items"].append({"id": section_id, "text": title})

with open(f"{OUT}/coze-dify.html", 'w', encoding='utf-8') as f:
    f.write(build_html("Coze / Dify 平台开发", coze_sections, coze_sidebar, WORKFLOW_SVG))

print("Done: coze-dify.html")
print("\n=== All pages built successfully! ===")
