#!/usr/bin/env python3
"""Build HTML pages for the Foundation section of the AI knowledge base."""

import os
import re
import html as html_module
from pathlib import Path

KB_ROOT = Path("/home/pez/knowledge-base")
OUT_DIR = Path("/home/pez/projects/ai-knowledge-hub/display/kb/foundation")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Markdown to HTML converter ──────────────────────────────────────────

def md_to_html(md_text, page_id=""):
    """Convert markdown text to HTML with all required features."""
    lines = md_text.split('\n')
    html_parts = []
    in_code_block = False
    code_lang = ""
    code_lines = []
    in_table = False
    table_rows = []
    
    def flush_code():
        nonlocal code_lines, in_code_block, code_lang
        if code_lines:
            code_text = html_module.escape('\n'.join(code_lines))
            lang_class = f' class="language-{code_lang}"' if code_lang else ''
            html_parts.append(f'<div class="code-block"><div class="code-header"><span class="code-lang">{code_lang if code_lang else "code"}</span></div><pre><code{lang_class}>{code_text}</code></pre></div>')
            code_lines = []
            in_code_block = False
            code_lang = ""
    
    def flush_table():
        nonlocal table_rows, in_table
        if not table_rows:
            in_table = False
            return
        # Parse table
        header = table_rows[0]
        data_rows = table_rows[2:]  # skip separator row
        headers = [c.strip() for c in header.strip('|').split('|')]
        
        html_parts.append('<div class="table-wrapper"><table>')
        html_parts.append('<thead><tr>')
        for h in headers:
            html_parts.append(f'<th>{process_inline(h)}</th>')
        html_parts.append('</tr></thead><tbody>')
        for i, row in enumerate(data_rows):
            cls = ' class="alt-row"' if i % 2 == 1 else ''
            cells = [c.strip() for c in row.strip('|').split('|')]
            html_parts.append(f'<tr{cls}>')
            for c in cells:
                html_parts.append(f'<td>{process_inline(c)}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody></table></div>')
        table_rows = []
        in_table = False
    
    def process_inline(text):
        """Process inline markdown: bold, italic, code, links, wikilinks."""
        # Wikilinks [[...]] -> anchor
        text = re.sub(r'\[\[([^|\]]+?)(?:\|([^\]]+?))?\]\]', lambda m: f'<a href="#{wikilink_to_anchor(m.group(1))}" class="wikilink">{m.group(2) if m.group(2) else m.group(1)}</a>', text)
        # Images ![[...]] -> skip (we don't have images)
        text = re.sub(r'!\[\[.*?\]\]', '[image]', text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', text)
        # Bold **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic *text*
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # Links [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        # Math formulas $$...$$ or $...$
        text = re.sub(r'\$\$(.+?)\$\$', r'<span class="math-formula">\1</span>', text)
        text = re.sub(r'\$([^$]+?)\$', r'<span class="math-formula">\1</span>', text)
        return text
    
    def wikilink_to_anchor(wikilink):
        """Convert wikilink text to a URL-friendly anchor."""
        # Extract just the filename part
        parts = wikilink.split('/')
        name = parts[-1].replace(' ', '-')
        return re.sub(r'[^\w\u4e00-\u9fff-]', '', name).lower()
    
    def process_line(line):
        nonlocal in_code_block, code_lang, in_table, table_rows
        
        stripped = line.strip()
        
        # Code block start/end
        if stripped.startswith('```'):
            if in_code_block:
                flush_code()
                return
            else:
                if in_table:
                    flush_table()
                in_code_block = True
                code_lang = stripped[3:].strip()
                return
        
        if in_code_block:
            code_lines.append(line)
            return
        
        # Table detection
        if '|' in stripped and stripped.startswith('|'):
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(stripped)
            return
        elif in_table:
            flush_table()
        
        # Empty line
        if not stripped:
            html_parts.append('')
            return
        
        # Headings
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            anchor = re.sub(r'[^\w\u4e00-\u9fff-]', '', text.replace(' ', '-')).lower()
            html_parts.append(f'<h{level} id="{anchor}">{process_inline(text)}</h{level}>')
            return
        
        # Blockquote
        if stripped.startswith('>'):
            content = stripped[1:].strip()
            # Collect multi-line blockquotes
            html_parts.append(f'<blockquote>{process_inline(content)}</blockquote>')
            return
        
        # Horizontal rule
        if stripped in ('---', '***', '___'):
            html_parts.append('<hr>')
            return
        
        # Unordered list
        if re.match(r'^[-*]\s+', stripped):
            content = re.sub(r'^[-*]\s+', '', stripped)
            html_parts.append(f'<ul><li>{process_inline(content)}</li></ul>')
            return
        
        # Ordered list
        ol_match = re.match(r'^(\d+)[.)]\s+(.+)', stripped)
        if ol_match:
            content = ol_match.group(2)
            html_parts.append(f'<ol><li>{process_inline(content)}</li></ol>')
            return
        
        # Math block
        if stripped.startswith('$$'):
            html_parts.append(f'<div class="math-block">{process_inline(stripped)}</div>')
            return
        
        # Regular paragraph
        html_parts.append(f'<p>{process_inline(stripped)}</p>')
    
    for line in lines:
        process_line(line)
    
    if in_code_block:
        flush_code()
    if in_table:
        flush_table()
    
    # Merge consecutive blockquotes
    result = '\n'.join(html_parts)
    result = re.sub(r'</blockquote>\n<blockquote>', '\n', result)
    # Merge consecutive list items
    result = re.sub(r'</ul>\n<ul>', '\n', result)
    result = re.sub(r'</ol>\n<ol>', '\n', result)
    
    return result


def extract_toc(md_text):
    """Extract table of contents from markdown headings."""
    toc = []
    for line in md_text.split('\n'):
        m = re.match(r'^(#{2,4})\s+(.+)$', line.strip())
        if m:
            level = len(m.group(1))
            text = m.group(2)
            anchor = re.sub(r'[^\w\u4e00-\u9fff-]', '', text.replace(' ', '-')).lower()
            toc.append((level, text, anchor))
    return toc


def extract_difficulty(md_text):
    """Extract difficulty badge from markdown."""
    if '🟢' in md_text or '入门' in md_text:
        return ('beginner', '入门')
    elif '🟡' in md_text or '中级' in md_text or '中等' in md_text:
        return ('intermediate', '基础')
    elif '🔴' in md_text or '高级' in md_text:
        return ('advanced', '高级')
    return ('beginner', '入门')


def read_md_files(directory, recursive=False):
    """Read all .md files from a directory."""
    files = []
    base = KB_ROOT / directory
    if not base.exists():
        return files
    pattern = '*.md'
    md_files = sorted(base.rglob(pattern) if recursive else base.glob(pattern))
    for md_file in md_files:
        rel = md_file.relative_to(base)
        content = md_file.read_text(encoding='utf-8', errors='replace')
        files.append({
            'path': str(rel),
            'name': md_file.stem,
            'content': content,
            'difficulty': extract_difficulty(content),
        })
    return files


# ── Common HTML template ────────────────────────────────────────────────

def get_sidebar_tree(files_by_dir):
    """Generate sidebar HTML from files grouped by directory."""
    html = '<nav class="sidebar"><div class="sidebar-header"><h3>目录导航</h3></div><div class="sidebar-content">'
    for dir_name, files in files_by_dir.items():
        html += f'<div class="sidebar-section"><div class="sidebar-dir">{dir_name}</div><ul>'
        for f in files:
            anchor = re.sub(r'[^\w\u4e00-\u9fff-]', '', f["name"].replace(' ', '-')).lower()
            diff = f['difficulty']
            badge_cls = diff[0]
            html += f'<li><a href="#{anchor}"><span class="badge badge-{badge_cls}">{diff[1]}</span>{f["name"]}</a></li>'
        html += '</ul></div>'
    html += '</div></nav>'
    return html


def get_svg_ml_comparison():
    """SVG: ML algorithm comparison chart."""
    return '''
<svg viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" class="diagram-svg">
  <style>
    .chart-text { font-family: 'Inter', sans-serif; font-size: 12px; fill: #37352f; }
    .chart-title { font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600; fill: #37352f; }
    .chart-axis { stroke: #37352f; stroke-width: 1; }
    .chart-grid { stroke: #e0e0e0; stroke-width: 0.5; stroke-dasharray: 4 4; }
    .bar-svm { fill: #0075de; }
    .bar-rf { fill: #2ecc71; }
    .bar-xgb { fill: #e74c3c; }
    .bar-knn { fill: #f39c12; }
    .bar-lr { fill: #9b59b6; }
    .bar-dt { fill: #1abc9c; }
  </style>
  <text x="400" y="30" text-anchor="middle" class="chart-title">机器学习算法特性对比</text>
  <!-- Axes -->
  <line x1="80" y1="60" x2="80" y2="420" class="chart-axis"/>
  <line x1="80" y1="420" x2="760" y2="420" class="chart-axis"/>
  <!-- Y-axis labels -->
  <text x="70" y="80" text-anchor="end" class="chart-text">100%</text>
  <text x="70" y="150" text-anchor="end" class="chart-text">80%</text>
  <text x="70" y="220" text-anchor="end" class="chart-text">60%</text>
  <text x="70" y="290" text-anchor="end" class="chart-text">40%</text>
  <text x="70" y="360" text-anchor="end" class="chart-text">20%</text>
  <text x="70" y="425" text-anchor="end" class="chart-text">0%</text>
  <!-- Grid lines -->
  <line x1="80" y1="80" x2="760" y2="80" class="chart-grid"/>
  <line x1="80" y1="150" x2="760" y2="150" class="chart-grid"/>
  <line x1="80" y1="220" x2="760" y2="220" class="chart-grid"/>
  <line x1="80" y1="290" x2="760" y2="290" class="chart-grid"/>
  <line x1="80" y1="360" x2="760" y2="360" class="chart-grid"/>
  <!-- Accuracy bars (grouped by algorithm) -->
  <!-- KNN -->
  <rect x="110" y="170" width="40" height="250" class="bar-knn" rx="3"/>
  <text x="130" y="440" text-anchor="middle" class="chart-text">KNN</text>
  <text x="130" y="165" text-anchor="middle" class="chart-text">55%</text>
  <!-- Linear Regression -->
  <rect x="210" y="150" width="40" height="270" class="bar-lr" rx="3"/>
  <text x="230" y="440" text-anchor="middle" class="chart-text">线性回归</text>
  <text x="230" y="145" text-anchor="middle" class="chart-text">60%</text>
  <!-- Decision Tree -->
  <rect x="310" y="120" width="40" height="300" class="bar-dt" rx="3"/>
  <text x="330" y="440" text-anchor="middle" class="chart-text">决策树</text>
  <text x="330" y="115" text-anchor="middle" class="chart-text">68%</text>
  <!-- SVM -->
  <rect x="410" y="90" width="40" height="330" class="bar-svm" rx="3"/>
  <text x="430" y="440" text-anchor="middle" class="chart-text">SVM</text>
  <text x="430" y="85" text-anchor="middle" class="chart-text">78%</text>
  <!-- Random Forest -->
  <rect x="510" y="70" width="40" height="350" class="bar-rf" rx="3"/>
  <text x="530" y="440" text-anchor="middle" class="chart-text">随机森林</text>
  <text x="530" y="65" text-anchor="middle" class="chart-text">85%</text>
  <!-- XGBoost -->
  <rect x="610" y="55" width="40" height="365" class="bar-xgb" rx="3"/>
  <text x="630" y="440" text-anchor="middle" class="chart-text">XGBoost</text>
  <text x="630" y="50" text-anchor="middle" class="chart-text">90%</text>
  <!-- Legend -->
  <text x="400" y="475" text-anchor="middle" class="chart-text">算法准确率对比（典型分类任务）</text>
</svg>'''


def get_svg_neural_network():
    """SVG: Neural network architecture."""
    return '''
<svg viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" class="diagram-svg">
  <style>
    .nn-node { fill: #ffffff; stroke: #0075de; stroke-width: 2; }
    .nn-node-hl { fill: #0075de; stroke: #0075de; stroke-width: 2; }
    .nn-line { stroke: rgba(0,117,222,0.3); stroke-width: 1; }
    .nn-text { font-family: 'Inter', sans-serif; font-size: 11px; fill: #37352f; }
    .nn-label { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; fill: #37352f; }
  </style>
  <text x="400" y="25" text-anchor="middle" class="nn-label">全连接神经网络架构</text>
  <!-- Input layer -->
  <text x="100" y="55" text-anchor="middle" class="nn-label">输入层</text>
  <circle cx="100" cy="100" r="18" class="nn-node"/><text x="100" y="104" text-anchor="middle" class="nn-text">x1</text>
  <circle cx="100" cy="160" r="18" class="nn-node"/><text x="100" y="164" text-anchor="middle" class="nn-text">x2</text>
  <circle cx="100" cy="220" r="18" class="nn-node"/><text x="100" y="224" text-anchor="middle" class="nn-text">x3</text>
  <circle cx="100" cy="280" r="18" class="nn-node"/><text x="100" y="284" text-anchor="middle" class="nn-text">x4</text>
  <!-- Hidden layer 1 -->
  <text x="300" y="55" text-anchor="middle" class="nn-label">隐藏层 1</text>
  <circle cx="300" cy="80" r="18" class="nn-node"/><text x="300" y="84" text-anchor="middle" class="nn-text">h1</text>
  <circle cx="300" cy="140" r="18" class="nn-node"/><text x="300" y="144" text-anchor="middle" class="nn-text">h2</text>
  <circle cx="300" cy="200" r="18" class="nn-node"/><text x="300" y="204" text-anchor="middle" class="nn-text">h3</text>
  <circle cx="300" cy="260" r="18" class="nn-node"/><text x="300" y="264" text-anchor="middle" class="nn-text">h4</text>
  <circle cx="300" cy="320" r="18" class="nn-node"/><text x="300" y="324" text-anchor="middle" class="nn-text">h5</text>
  <!-- Hidden layer 2 -->
  <text x="500" y="55" text-anchor="middle" class="nn-label">隐藏层 2</text>
  <circle cx="500" cy="110" r="18" class="nn-node"/><text x="500" y="114" text-anchor="middle" class="nn-text">h6</text>
  <circle cx="500" cy="180" r="18" class="nn-node"/><text x="500" y="184" text-anchor="middle" class="nn-text">h7</text>
  <circle cx="500" cy="250" r="18" class="nn-node"/><text x="500" y="254" text-anchor="middle" class="nn-text">h8</text>
  <!-- Output layer -->
  <text x="700" y="55" text-anchor="middle" class="nn-label">输出层</text>
  <circle cx="700" cy="150" r="18" class="nn-node-hl"/><text x="700" y="154" text-anchor="middle" style="fill:#fff;font-size:11px;">y1</text>
  <circle cx="700" cy="220" r="18" class="nn-node-hl"/><text x="700" y="224" text-anchor="middle" style="fill:#fff;font-size:11px;">y2</text>
  <!-- Connections input->hidden1 -->
  <line x1="118" y1="100" x2="282" y2="80" class="nn-line"/>
  <line x1="118" y1="100" x2="282" y2="140" class="nn-line"/>
  <line x1="118" y1="100" x2="282" y2="200" class="nn-line"/>
  <line x1="118" y1="100" x2="282" y2="260" class="nn-line"/>
  <line x1="118" y1="100" x2="282" y2="320" class="nn-line"/>
  <line x1="118" y1="160" x2="282" y2="80" class="nn-line"/>
  <line x1="118" y1="160" x2="282" y2="140" class="nn-line"/>
  <line x1="118" y1="160" x2="282" y2="200" class="nn-line"/>
  <line x1="118" y1="160" x2="282" y2="260" class="nn-line"/>
  <line x1="118" y1="160" x2="282" y2="320" class="nn-line"/>
  <line x1="118" y1="220" x2="282" y2="80" class="nn-line"/>
  <line x1="118" y1="220" x2="282" y2="140" class="nn-line"/>
  <line x1="118" y1="220" x2="282" y2="200" class="nn-line"/>
  <line x1="118" y1="220" x2="282" y2="260" class="nn-line"/>
  <line x1="118" y1="220" x2="282" y2="320" class="nn-line"/>
  <line x1="118" y1="280" x2="282" y2="80" class="nn-line"/>
  <line x1="118" y1="280" x2="282" y2="140" class="nn-line"/>
  <line x1="118" y1="280" x2="282" y2="200" class="nn-line"/>
  <line x1="118" y1="280" x2="282" y2="260" class="nn-line"/>
  <line x1="118" y1="280" x2="282" y2="320" class="nn-line"/>
  <!-- Connections hidden1->hidden2 -->
  <line x1="318" y1="80" x2="482" y2="110" class="nn-line"/>
  <line x1="318" y1="80" x2="482" y2="180" class="nn-line"/>
  <line x1="318" y1="80" x2="482" y2="250" class="nn-line"/>
  <line x1="318" y1="140" x2="482" y2="110" class="nn-line"/>
  <line x1="318" y1="140" x2="482" y2="180" class="nn-line"/>
  <line x1="318" y1="140" x2="482" y2="250" class="nn-line"/>
  <line x1="318" y1="200" x2="482" y2="110" class="nn-line"/>
  <line x1="318" y1="200" x2="482" y2="180" class="nn-line"/>
  <line x1="318" y1="200" x2="482" y2="250" class="nn-line"/>
  <line x1="318" y1="260" x2="482" y2="110" class="nn-line"/>
  <line x1="318" y1="260" x2="482" y2="180" class="nn-line"/>
  <line x1="318" y1="260" x2="482" y2="250" class="nn-line"/>
  <line x1="318" y1="320" x2="482" y2="110" class="nn-line"/>
  <line x1="318" y1="320" x2="482" y2="180" class="nn-line"/>
  <line x1="318" y1="320" x2="482" y2="250" class="nn-line"/>
  <!-- Connections hidden2->output -->
  <line x1="518" y1="110" x2="682" y2="150" class="nn-line"/>
  <line x1="518" y1="110" x2="682" y2="220" class="nn-line"/>
  <line x1="518" y1="180" x2="682" y2="150" class="nn-line"/>
  <line x1="518" y1="180" x2="682" y2="220" class="nn-line"/>
  <line x1="518" y1="250" x2="682" y2="150" class="nn-line"/>
  <line x1="518" y1="250" x2="682" y2="220" class="nn-line"/>
  <!-- Labels -->
  <text x="400" y="375" text-anchor="middle" class="nn-text" style="font-size:12px;">前向传播方向 → | 每层神经元全连接到下一层 | 激活函数引入非线性</text>
</svg>'''


def get_svg_cnn():
    """SVG: CNN layer visualization."""
    return '''
<svg viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg" class="diagram-svg">
  <style>
    .cnn-rect { fill: #0075de; opacity: 0.15; stroke: #0075de; stroke-width: 1.5; }
    .cnn-conv { fill: #e74c3c; opacity: 0.2; stroke: #e74c3c; stroke-width: 1.5; }
    .cnn-pool { fill: #2ecc71; opacity: 0.2; stroke: #2ecc71; stroke-width: 1.5; }
    .cnn-fc { fill: #f39c12; opacity: 0.2; stroke: #f39c12; stroke-width: 1.5; }
    .cnn-text { font-family: 'Inter', sans-serif; font-size: 11px; fill: #37352f; }
    .cnn-label { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; fill: #37352f; }
    .cnn-arrow { stroke: #37352f; stroke-width: 1.5; fill: none; marker-end: url(#arrowhead); }
  </style>
  <defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#37352f"/></marker></defs>
  <text x="400" y="25" text-anchor="middle" class="cnn-label">卷积神经网络（CNN）层级结构</text>
  <!-- Input image -->
  <rect x="30" y="60" width="60" height="80" class="cnn-rect" rx="4"/>
  <text x="60" y="105" text-anchor="middle" class="cnn-text">输入</text>
  <text x="60" y="118" text-anchor="middle" class="cnn-text">224x224x3</text>
  <!-- Conv1 -->
  <rect x="140" y="65" width="55" height="70" class="cnn-conv" rx="4"/>
  <text x="167" y="105" text-anchor="middle" class="cnn-text">卷积</text>
  <text x="167" y="118" text-anchor="middle" class="cnn-text">3x3</text>
  <line x1="90" y1="100" x2="140" y2="100" class="cnn-arrow"/>
  <!-- Pool1 -->
  <rect x="240" y="70" width="45" height="60" class="cnn-pool" rx="4"/>
  <text x="262" y="105" text-anchor="middle" class="cnn-text">池化</text>
  <text x="262" y="118" text-anchor="middle" class="cnn-text">2x2</text>
  <line x1="195" y1="100" x2="240" y2="100" class="cnn-arrow"/>
  <!-- Conv2 -->
  <rect x="330" y="75" width="50" height="55" class="cnn-conv" rx="4"/>
  <text x="355" y="105" text-anchor="middle" class="cnn-text">卷积</text>
  <text x="355" y="118" text-anchor="middle" class="cnn-text">3x3</text>
  <line x1="285" y1="100" x2="330" y2="100" class="cnn-arrow"/>
  <!-- Pool2 -->
  <rect x="425" y="80" width="40" height="45" class="cnn-pool" rx="4"/>
  <text x="445" y="105" text-anchor="middle" class="cnn-text">池化</text>
  <text x="445" y="118" text-anchor="middle" class="cnn-text">2x2</text>
  <line x1="380" y1="100" x2="425" y2="100" class="cnn-arrow"/>
  <!-- Flatten -->
  <rect x="510" y="85" width="40" height="35" class="cnn-rect" rx="4"/>
  <text x="530" y="105" text-anchor="middle" class="cnn-text">展平</text>
  <line x1="465" y1="100" x2="510" y2="100" class="cnn-arrow"/>
  <!-- FC -->
  <rect x="595" y="80" width="50" height="45" class="cnn-fc" rx="4"/>
  <text x="620" y="105" text-anchor="middle" class="cnn-text">全连接</text>
  <line x1="550" y1="100" x2="595" y2="100" class="cnn-arrow"/>
  <!-- Output -->
  <rect x="690" y="85" width="50" height="35" fill="#0075de" opacity="0.3" stroke="#0075de" stroke-width="1.5" rx="4"/>
  <text x="715" y="105" text-anchor="middle" class="cnn-text">输出</text>
  <line x1="645" y1="100" x2="690" y2="100" class="cnn-arrow"/>
  <!-- Feature map visualization -->
  <text x="400" y="180" text-anchor="middle" class="cnn-label">特征图提取过程</text>
  <!-- Input grid -->
  <g transform="translate(80, 200)">
    <rect width="60" height="60" fill="#f6f5f4" stroke="#ccc" stroke-width="0.5"/>
    <rect x="0" y="0" width="10" height="10" fill="rgba(0,117,222,0.3)"/><rect x="10" y="0" width="10" height="10" fill="rgba(0,117,222,0.5)"/><rect x="20" y="0" width="10" height="10" fill="rgba(0,117,222,0.1)"/>
    <rect x="0" y="10" width="10" height="10" fill="rgba(0,117,222,0.5)"/><rect x="10" y="10" width="10" height="10" fill="rgba(0,117,222,0.8)"/><rect x="20" y="10" width="10" height="10" fill="rgba(0,117,222,0.4)"/>
    <rect x="0" y="20" width="10" height="10" fill="rgba(0,117,222,0.2)"/><rect x="10" y="20" width="10" height="10" fill="rgba(0,117,222,0.4)"/><rect x="20" y="20" width="10" height="10" fill="rgba(0,117,222,0.6)"/>
    <text x="30" y="45" text-anchor="middle" class="cnn-text">原始输入</text>
  </g>
  <!-- Kernel -->
  <g transform="translate(220, 210)">
    <rect width="30" height="30" fill="rgba(231,76,60,0.3)" stroke="#e74c3c"/>
    <text x="15" y="50" text-anchor="middle" class="cnn-text">卷积核</text>
  </g>
  <!-- Feature map -->
  <g transform="translate(350, 200)">
    <rect width="50" height="50" fill="#f6f5f4" stroke="#ccc" stroke-width="0.5"/>
    <rect x="0" y="0" width="10" height="10" fill="rgba(46,204,113,0.6)"/><rect x="10" y="0" width="10" height="10" fill="rgba(46,204,113,0.3)"/><rect x="20" y="0" width="10" height="10" fill="rgba(46,204,113,0.5)"/>
    <rect x="0" y="10" width="10" height="10" fill="rgba(46,204,113,0.4)"/><rect x="10" y="10" width="10" height="10" fill="rgba(46,204,113,0.7)"/><rect x="20" y="10" width="10" height="10" fill="rgba(46,204,113,0.2)"/>
    <rect x="0" y="20" width="10" height="10" fill="rgba(46,204,113,0.5)"/><rect x="10" y="20" width="10" height="10" fill="rgba(46,204,113,0.3)"/><rect x="20" y="20" width="10" height="10" fill="rgba(46,204,113,0.6)"/>
    <text x="25" y="40" text-anchor="middle" class="cnn-text">特征图</text>
  </g>
  <line x1="140" y1="230" x2="218" y2="230" class="cnn-arrow"/>
  <line x1="252" y1="230" x2="348" y2="230" class="cnn-arrow"/>
  <text x="285" y="220" text-anchor="middle" class="cnn-text">卷积运算</text>
</svg>'''


def get_svg_rnn_lstm():
    """SVG: RNN/LSTM data flow."""
    return '''
<svg viewBox="0 0 800 350" xmlns="http://www.w3.org/2000/svg" class="diagram-svg">
  <style>
    .rnn-cell { fill: #0075de; opacity: 0.15; stroke: #0075de; stroke-width: 2; }
    .rnn-gate { fill: #e74c3c; opacity: 0.15; stroke: #e74c3c; stroke-width: 2; }
    .rnn-line { stroke: #37352f; stroke-width: 1.5; fill: none; marker-end: url(#arr2); }
    .rnn-rec { stroke: #0075de; stroke-width: 1.5; fill: none; marker-end: url(#arr2); }
    .rnn-text { font-family: 'Inter', sans-serif; font-size: 11px; fill: #37352f; }
    .rnn-label { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; fill: #37352f; }
  </style>
  <defs><marker id="arr2" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#37352f"/></marker></defs>
  <text x="400" y="25" text-anchor="middle" class="rnn-label">RNN 循环神经网络数据流</text>
  <!-- RNN cells -->
  <rect x="80" y="70" width="70" height="50" class="rnn-cell" rx="8"/>
  <text x="115" y="100" text-anchor="middle" class="rnn-text">h1</text>
  <rect x="250" y="70" width="70" height="50" class="rnn-cell" rx="8"/>
  <text x="285" y="100" text-anchor="middle" class="rnn-text">h2</text>
  <rect x="420" y="70" width="70" height="50" class="rnn-cell" rx="8"/>
  <text x="455" y="100" text-anchor="middle" class="rnn-text">h3</text>
  <rect x="590" y="70" width="70" height="50" class="rnn-cell" rx="8"/>
  <text x="625" y="100" text-anchor="middle" class="rnn-text">ht</text>
  <!-- Input arrows -->
  <line x1="115" y1="180" x2="115" y2="120" class="rnn-line"/>
  <text x="115" y="195" text-anchor="middle" class="rnn-text">x1</text>
  <line x1="285" y1="180" x2="285" y2="120" class="rnn-line"/>
  <text x="285" y="195" text-anchor="middle" class="rnn-text">x2</text>
  <line x1="455" y1="180" x2="455" y2="120" class="rnn-line"/>
  <text x="455" y="195" text-anchor="middle" class="rnn-text">x3</text>
  <line x1="625" y1="180" x2="625" y2="120" class="rnn-line"/>
  <text x="625" y="195" text-anchor="middle" class="rnn-text">xt</text>
  <!-- Hidden state connections -->
  <line x1="150" y1="95" x2="250" y2="95" class="rnn-rec"/>
  <line x1="320" y1="95" x2="420" y2="95" class="rnn-rec"/>
  <line x1="490" y1="95" x2="590" y2="95" class="rnn-rec"/>
  <!-- Output arrows -->
  <line x1="115" y1="70" x2="115" y2="45" class="rnn-line"/>
  <text x="115" y="40" text-anchor="middle" class="rnn-text">y1</text>
  <line x1="285" y1="70" x2="285" y2="45" class="rnn-line"/>
  <text x="285" y="40" text-anchor="middle" class="rnn-text">y2</text>
  <line x1="455" y1="70" x2="455" y2="45" class="rnn-line"/>
  <text x="455" y="40" text-anchor="middle" class="rnn-text">y3</text>
  <line x1="625" y1="70" x2="625" y2="45" class="rnn-line"/>
  <text x="625" y="40" text-anchor="middle" class="rnn-text">yt</text>
  <!-- LSTM section -->
  <text x="400" y="240" text-anchor="middle" class="rnn-label">LSTM 门控机制</text>
  <rect x="200" y="260" width="400" height="70" fill="none" stroke="#e74c3c" stroke-width="1" stroke-dasharray="4 4" rx="8"/>
  <text x="400" y="280" text-anchor="middle" class="rnn-text">遗忘门 f = sigmoid(W_f · [h_{t-1}, x_t] + b_f)</text>
  <text x="400" y="300" text-anchor="middle" class="rnn-text">输入门 i = sigmoid(W_i · [h_{t-1}, x_t] + b_i)</text>
  <text x="400" y="320" text-anchor="middle" class="rnn-text">输出门 o = sigmoid(W_o · [h_{t-1}, x_t] + b_o)</text>
</svg>'''


def get_svg_attention():
    """SVG: Attention mechanism."""
    return '''
<svg viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" class="diagram-svg">
  <style>
    .att-box { fill: #0075de; opacity: 0.12; stroke: #0075de; stroke-width: 1.5; }
    .att-q { fill: #e74c3c; opacity: 0.12; stroke: #e74c3c; stroke-width: 1.5; }
    .att-k { fill: #2ecc71; opacity: 0.12; stroke: #2ecc71; stroke-width: 1.5; }
    .att-v { fill: #f39c12; opacity: 0.12; stroke: #f39c12; stroke-width: 1.5; }
    .att-line { stroke: #37352f; stroke-width: 1.5; fill: none; marker-end: url(#arr3); }
    .att-text { font-family: 'Inter', sans-serif; font-size: 11px; fill: #37352f; }
    .att-label { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; fill: #37352f; }
  </style>
  <defs><marker id="arr3" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#37352f"/></marker></defs>
  <text x="400" y="25" text-anchor="middle" class="att-label">Transformer 注意力机制 (Scaled Dot-Product Attention)</text>
  <!-- Input embeddings -->
  <rect x="50" y="60" width="80" height="35" class="att-box" rx="4"/>
  <text x="90" y="82" text-anchor="middle" class="att-text">输入序列</text>
  <!-- Linear projections -->
  <rect x="200" y="50" width="70" height="30" class="att-q" rx="4"/>
  <text x="235" y="70" text-anchor="middle" class="att-text">W_Q</text>
  <rect x="200" y="90" width="70" height="30" class="att-k" rx="4"/>
  <text x="235" y="110" text-anchor="middle" class="att-text">W_K</text>
  <rect x="200" y="130" width="70" height="30" class="att-v" rx="4"/>
  <text x="235" y="150" text-anchor="middle" class="att-text">W_V</text>
  <!-- Q K V labels -->
  <rect x="340" y="50" width="60" height="30" class="att-q" rx="4"/>
  <text x="370" y="70" text-anchor="middle" class="att-text">Q</text>
  <rect x="340" y="90" width="60" height="30" class="att-k" rx="4"/>
  <text x="370" y="110" text-anchor="middle" class="att-text">K</text>
  <rect x="340" y="130" width="60" height="30" class="att-v" rx="4"/>
  <text x="370" y="150" text-anchor="middle" class="att-text">V</text>
  <!-- Arrows from input to projections -->
  <line x1="130" y1="77" x2="200" y2="65" class="att-line"/>
  <line x1="130" y1="77" x2="200" y2="105" class="att-line"/>
  <line x1="130" y1="77" x2="200" y2="145" class="att-line"/>
  <!-- Q*K^T -->
  <rect x="460" y="55" width="100" height="35" fill="rgba(231,76,60,0.15)" stroke="#e74c3c" stroke-width="1.5" rx="4"/>
  <text x="510" y="77" text-anchor="middle" class="att-text">Q * K^T</text>
  <line x1="400" y1="65" x2="460" y2="70" class="att-line"/>
  <line x1="400" y1="105" x2="460" y2="75" class="att-line"/>
  <!-- Scale + Softmax -->
  <rect x="610" y="55" width="110" height="35" fill="rgba(155,89,182,0.15)" stroke="#9b59b6" stroke-width="1.5" rx="4"/>
  <text x="665" y="77" text-anchor="middle" class="att-text">/sqrt(d_k) + Softmax</text>
  <line x1="560" y1="72" x2="610" y2="72" class="att-line"/>
  <!-- Attention weights -->
  <rect x="610" y="130" width="110" height="35" fill="rgba(0,117,222,0.15)" stroke="#0075de" stroke-width="1.5" rx="4"/>
  <text x="665" y="152" text-anchor="middle" class="att-text">注意力权重</text>
  <line x1="665" y1="90" x2="665" y2="130" class="att-line"/>
  <!-- Multiply with V -->
  <rect x="460" y="130" width="100" height="35" fill="rgba(243,156,18,0.15)" stroke="#f39c12" stroke-width="1.5" rx="4"/>
  <text x="510" y="152" text-anchor="middle" class="att-text">* V</text>
  <line x1="610" y1="147" x2="560" y2="147" class="att-line"/>
  <line x1="400" y1="145" x2="460" y2="147" class="att-line"/>
  <!-- Output -->
  <rect x="460" y="210" width="100" height="35" class="att-box" rx="4"/>
  <text x="510" y="232" text-anchor="middle" class="att-text">输出</text>
  <line x1="510" y1="165" x2="510" y2="210" class="att-line"/>
  <!-- Formula -->
  <text x="400" y="290" text-anchor="middle" class="att-label">Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V</text>
  <!-- Multi-head note -->
  <rect x="150" y="310" width="500" height="70" fill="#f6f5f4" stroke="rgba(0,0,0,0.1)" rx="6"/>
  <text x="400" y="335" text-anchor="middle" class="att-label">Multi-Head Attention</text>
  <text x="400" y="355" text-anchor="middle" class="att-text">将 Q, K, V 分别投影到 h 个不同的子空间，独立计算注意力后拼接</text>
  <text x="400" y="370" text-anchor="middle" class="att-text">MultiHead(Q,K,V) = Concat(head_1, ..., head_h) * W_O</text>
</svg>'''


# ── CSS styles ──────────────────────────────────────────────────────────

COMMON_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: 'Inter', 'Noto Sans SC', 'PingFang SC', -apple-system, sans-serif;
  font-size: 16px; line-height: 1.7; color: #37352f; background: #ffffff;
  display: flex; min-height: 100vh;
}
/* Sidebar */
.sidebar {
  position: sticky; top: 0; left: 0; width: 280px; height: 100vh;
  overflow-y: auto; background: #f6f5f4; border-right: 1px solid rgba(0,0,0,0.1);
  flex-shrink: 0; padding: 0; z-index: 10;
}
.sidebar-header { padding: 24px 20px 16px; border-bottom: 1px solid rgba(0,0,0,0.1); }
.sidebar-header h3 { font-size: 16px; font-weight: 600; color: #37352f; }
.sidebar-content { padding: 12px 0; }
.sidebar-section { margin-bottom: 8px; }
.sidebar-dir { padding: 6px 20px; font-size: 13px; font-weight: 600; color: #6b6b6b; text-transform: uppercase; letter-spacing: 0.5px; }
.sidebar-section ul { list-style: none; }
.sidebar-section li a {
  display: flex; align-items: center; gap: 8px; padding: 6px 20px 6px 28px;
  font-size: 14px; color: #37352f; text-decoration: none; transition: background 0.15s;
}
.sidebar-section li a:hover { background: rgba(0,117,222,0.08); }
/* Main content */
.main-content { flex: 1; max-width: 900px; margin: 0 auto; padding: 40px 60px 80px; }
/* Headings */
h1 { font-size: 44px; font-weight: 700; margin: 0 0 16px; color: #37352f; letter-spacing: -0.5px; }
h2 { font-size: 28px; font-weight: 600; margin: 48px 0 16px; color: #37352f; padding-bottom: 8px; border-bottom: 1px solid rgba(0,0,0,0.1); }
h3 { font-size: 22px; font-weight: 600; margin: 32px 0 12px; color: #37352f; }
h4 { font-size: 18px; font-weight: 600; margin: 24px 0 8px; color: #37352f; }
h5 { font-size: 16px; font-weight: 600; margin: 20px 0 8px; color: #37352f; }
/* Paragraphs & text */
p { margin: 0 0 16px; }
strong { font-weight: 600; }
em { font-style: italic; }
a { color: #0075de; text-decoration: none; }
a:hover { text-decoration: underline; }
.wikilink { color: #0075de; border-bottom: 1px dotted #0075de; }
/* Lists */
ul, ol { margin: 0 0 16px; padding-left: 24px; }
li { margin-bottom: 4px; }
/* Blockquotes */
blockquote {
  margin: 16px 0; padding: 12px 16px; border-left: 3px solid #0075de;
  background: #f6f5f4; border-radius: 0 4px 4px 0; font-size: 14px; color: #4a4a4a;
}
blockquote p { margin: 0 0 4px; }
/* Code */
.inline-code {
  font-family: 'JetBrains Mono', monospace; font-size: 0.9em;
  background: #f6f5f4; padding: 2px 6px; border-radius: 3px; color: #e74c3c;
}
.code-block { margin: 16px 0; border-radius: 6px; overflow: hidden; border: 1px solid rgba(0,0,0,0.1); }
.code-header { background: #f6f5f4; padding: 6px 12px; border-bottom: 1px solid rgba(0,0,0,0.1); }
.code-lang { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #6b6b6b; }
.code-block pre { margin: 0; padding: 16px; overflow-x: auto; background: #ffffff; }
.code-block code {
  font-family: 'JetBrains Mono', monospace; font-size: 13.5px; line-height: 1.6; color: #37352f;
}
/* Tables */
.table-wrapper { margin: 16px 0; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { background: #f6f5f4; font-weight: 600; text-align: left; padding: 10px 12px; border: 1px solid rgba(0,0,0,0.1); }
td { padding: 8px 12px; border: 1px solid rgba(0,0,0,0.1); }
tr.alt-row { background: #f6f5f4; }
/* Badges */
.badge {
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 11px; font-weight: 600; line-height: 1.4; flex-shrink: 0;
}
.badge-beginner { background: #e6f7e6; color: #1a7a1a; }
.badge-intermediate { background: #fff7e6; color: #b37700; }
.badge-advanced { background: #ffe6e6; color: #b30000; }
/* Math */
.math-formula { font-family: 'Times New Roman', serif; font-style: italic; color: #37352f; }
.math-block { margin: 16px 0; padding: 12px 16px; background: #f6f5f4; border-radius: 4px; text-align: center; font-family: 'Times New Roman', serif; font-size: 16px; }
/* Diagrams */
.diagram-svg { width: 100%; max-width: 800px; margin: 24px auto; display: block; }
.diagram-container { margin: 24px 0; padding: 16px; background: #ffffff; border: 1px solid rgba(0,0,0,0.1); border-radius: 8px; }
.diagram-title { font-size: 16px; font-weight: 600; color: #37352f; margin-bottom: 12px; text-align: center; }
/* HR */
hr { margin: 32px 0; border: none; border-top: 1px solid rgba(0,0,0,0.1); }
/* Section cards */
.section-card {
  margin: 24px 0; padding: 24px; background: #ffffff; border: 1px solid rgba(0,0,0,0.1);
  border-radius: 8px; transition: box-shadow 0.2s;
}
.section-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.section-card h2 { margin-top: 0; border: none; padding: 0; }
/* Page header */
.page-header { margin-bottom: 40px; padding-bottom: 24px; border-bottom: 1px solid rgba(0,0,0,0.1); }
.page-subtitle { font-size: 18px; color: #6b6b6b; margin-top: 8px; }
/* TOC */
.toc { margin: 24px 0; padding: 20px 24px; background: #f6f5f4; border-radius: 8px; }
.toc h3 { font-size: 16px; margin: 0 0 12px; }
.toc ul { list-style: none; padding: 0; margin: 0; }
.toc li { margin: 4px 0; }
.toc a { font-size: 14px; color: #37352f; }
.toc a:hover { color: #0075de; }
.toc .toc-h3 { padding-left: 16px; }
.toc .toc-h4 { padding-left: 32px; }
/* Landing page */
.landing-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin: 32px 0; }
.landing-card {
  padding: 24px; background: #ffffff; border: 1px solid rgba(0,0,0,0.1);
  border-radius: 8px; transition: box-shadow 0.2s, transform 0.2s; text-decoration: none; color: #37352f;
}
.landing-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); transform: translateY(-2px); text-decoration: none; }
.landing-card h3 { margin: 0 0 8px; font-size: 20px; }
.landing-card p { margin: 0; font-size: 14px; color: #6b6b6b; }
/* Footer */
.page-footer { margin-top: 60px; padding-top: 20px; border-top: 1px solid rgba(0,0,0,0.1); font-size: 13px; color: #999; text-align: center; }
/* Responsive */
@media (max-width: 768px) {
  body { flex-direction: column; }
  .sidebar { width: 100%; height: auto; position: relative; }
  .main-content { padding: 20px; }
  h1 { font-size: 32px; }
}
/* Syntax highlighting (basic) */
.code-block code .kw { color: #d73a49; }
.code-block code .str { color: #032f62; }
.code-block code .cm { color: #6a737d; }
.code-block code .fn { color: #6f42c1; }
.code-block code .num { color: #005cc5; }
"""


def generate_page(title, sidebar_html, content_html, page_toc_html="", extra_css=""):
    """Generate a complete HTML page."""
    toc_section = ""
    if page_toc_html:
        toc_section = f'<div class="toc"><h3>目录</h3>{page_toc_html}</div>'
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - AI 知识库</title>
<style>{COMMON_CSS}{extra_css}</style>
</head>
<body>
{sidebar_html}
<main class="main-content">
<div class="page-header">
<h1>{title}</h1>
</div>
{toc_section}
{content_html}
<div class="page-footer">AI 知识库 - Foundation</div>
</main>
</body>
</html>"""


def build_toc_html(md_text):
    """Build HTML for table of contents from markdown."""
    toc = extract_toc(md_text)
    if not toc:
        return ""
    html = '<ul>'
    for level, text, anchor in toc:
        cls = f' class="toc-h{level}"' if level > 2 else ''
        html += f'<li{cls}><a href="#{anchor}">{text}</a></li>'
    html += '</ul>'
    return html


# ── Build each page ─────────────────────────────────────────────────────

def build_index():
    """Build the landing page."""
    content = """
<div class="section-card">
<h2>基础理论</h2>
<p>从机器学习到大语言模型，系统构建 AI 知识体系的基础理论部分。涵盖数据分析、经典算法、深度学习、自然语言处理、大语言模型及 RAG 高级模式。</p>
</div>
<div class="landing-grid">
<a href="machine-learning.html" class="landing-card">
<h3>机器学习</h3>
<p>数据分析工具链 (NumPy/Pandas/Matplotlib)、经典 ML 算法 (KNN/线性回归/逻辑回归/决策树/集成算法/贝叶斯/SVM/聚类/降维)、实战案例</p>
</a>
<a href="deep-learning.html" class="landing-card">
<h3>深度学习</h3>
<p>神经网络基础、全连接神经网络、CNN 卷积神经网络、反向传播、正则化、优化器、PyTorch 框架</p>
</a>
<a href="nlp.html" class="landing-card">
<h3>自然语言处理</h3>
<p>NLP 基础、RNN 循环神经网络、序列模型、文本分类项目实战、BERT 模型开发</p>
</a>
<a href="llm.html" class="landing-card">
<h3>大语言模型 (LLM)</h3>
<p>Transformer 注意力机制、Embedding 与 Rerank、RAG 技术、提示词工程、LangChain、模型解码策略、模型量化</p>
</a>
<a href="rag-advanced.html" class="landing-card">
<h3>RAG 高级模式</h3>
<p>Self-RAG 自适应检索、Corrective-RAG 纠错检索、生产级 RAG 架构、监控与质量漂移、成本优化策略</p>
</a>
</div>
"""
    sidebar = '<nav class="sidebar"><div class="sidebar-header"><h3>Foundation</h3></div><div class="sidebar-content"><div class="sidebar-section"><ul>'
    pages = [
        ("machine-learning.html", "机器学习"),
        ("deep-learning.html", "深度学习"),
        ("nlp.html", "自然语言处理"),
        ("llm.html", "大语言模型"),
        ("rag-advanced.html", "RAG 高级模式"),
    ]
    for href, name in pages:
        sidebar += f'<li><a href="{href}">{name}</a></li>'
    sidebar += '</ul></div></div></nav>'
    
    html = generate_page("AI 基础理论", sidebar, content)
    (OUT_DIR / "index.html").write_text(html, encoding='utf-8')
    print("Created index.html")


def build_page(filename, title, dirs_with_labels, extra_svgs=""):
    """Build a content page from markdown directories."""
    all_files_by_dir = {}
    all_md = ""
    
    for dir_name, label in dirs_with_labels:
        files = read_md_files(dir_name)
        if files:
            all_files_by_dir[label] = files
            for f in files:
                all_md += f['content'] + "\n\n"
    
    sidebar = get_sidebar_tree(all_files_by_dir)
    
    content = ""
    if extra_svgs:
        content += f'<div class="diagram-container">{extra_svgs}</div>'
    
    for dir_name, label in dirs_with_labels:
        files = all_files_by_dir.get(label, [])
        for f in files:
            anchor = re.sub(r'[^\w\u4e00-\u9fff-]', '', f["name"].replace(' ', '-')).lower()
            diff = f['difficulty']
            badge_cls = diff[0]
            
            # Build per-file TOC
            file_toc = build_toc_html(f['content'])
            toc_html = ""
            if file_toc:
                toc_html = f'<div class="toc"><h3>本节目录</h3>{file_toc}</div>'
            
            content += f'<div class="section-card" id="{anchor}">'
            content += f'<h2><span class="badge badge-{badge_cls}">{diff[1]}</span> {f["name"]}</h2>'
            content += toc_html
            content += md_to_html(f['content'], anchor)
            content += '</div>'
    
    page_toc = ""
    for dir_name, label in dirs_with_labels:
        files = all_files_by_dir.get(label, [])
        if files:
            page_toc += f'<ul><li style="font-weight:600;margin-top:8px;">{label}</li>'
            for f in files:
                anchor = re.sub(r'[^\w\u4e00-\u9fff-]', '', f["name"].replace(' ', '-')).lower()
                page_toc += f'<li class="toc-h3"><a href="#{anchor}">{f["name"]}</a></li>'
            page_toc += '</ul>'
    
    html = generate_page(title, sidebar, content, page_toc)
    (OUT_DIR / filename).write_text(html, encoding='utf-8')
    print(f"Created {filename}")


# ── Main ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Building Foundation HTML pages...")
    
    build_index()
    
    build_page(
        "machine-learning.html",
        "机器学习",
        [
            ("机器学习/1.数据分析", "数据分析"),
            ("机器学习/2.机器学习", "机器学习算法"),
            ("机器学习/3.案例", "实战案例"),
        ],
        extra_svgs=get_svg_ml_comparison()
    )
    
    build_page(
        "deep-learning.html",
        "深度学习",
        [
            ("深度学习", "深度学习基础"),
            ("深度学习/全连接神经网络", "全连接神经网络"),
            ("深度学习/卷积神经网络", "卷积神经网络"),
        ],
        extra_svgs=get_svg_neural_network() + get_svg_cnn()
    )
    
    build_page(
        "nlp.html",
        "自然语言处理",
        [
            ("NLP", "NLP 基础"),
            ("NLP项目实践", "NLP 项目实践"),
        ],
        extra_svgs=get_svg_rnn_lstm()
    )
    
    build_page(
        "llm.html",
        "大语言模型 (LLM)",
        [
            ("LLM", "大语言模型"),
        ],
        extra_svgs=get_svg_attention()
    )
    
    build_page(
        "rag-advanced.html",
        "RAG 高级模式",
        [
            ("RAG高级模式", "RAG 高级模式"),
        ],
    )
    
    print("Done! All pages created.")
