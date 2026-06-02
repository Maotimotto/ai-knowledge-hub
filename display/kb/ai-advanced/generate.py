#!/usr/bin/env python3
"""Generate AI Advanced knowledge base HTML pages."""
import re, os, html as h

OUT = "/home/pez/projects/ai-knowledge-hub/display/kb/ai-advanced"

# ── Sidebar tree ──────────────────────────────────────────────
SIDEBAR = """
<nav class="sidebar">
<div class="sidebar-title">AI Advanced</div>
<a href="index.html" class="sidebar-link{0}">总览</a>
<a href="cv.html" class="sidebar-link{1}">08 计算机视觉基础</a>
<a href="interview.html" class="sidebar-link{2}">09 面试宝典</a>
<a href="projects.html" class="sidebar-link{3}">10 项目实战</a>
<a href="multimodal.html" class="sidebar-link{4}">11 多模态开发</a>
<a href="inference.html" class="sidebar-link{5}">12 LLM推理部署</a>
<a href="vectordb.html" class="sidebar-link{6}">13 向量数据库</a>
<a href="observability.html" class="sidebar-link{7}">14 LLM可观测性</a>
<a href="safety.html" class="sidebar-link{8}">15 AI安全与护栏</a>
<a href="serving.html" class="sidebar-link{9}">16 模型服务与部署</a>
</nav>
"""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter','Noto Sans SC',sans-serif;font-size:16px;color:#1a1a1a;background:#fff;line-height:1.7;display:flex;min-height:100vh}
.sidebar{width:260px;min-width:260px;background:#f9f9f8;border-right:1px solid rgba(0,0,0,0.1);padding:24px 16px;position:sticky;top:0;height:100vh;overflow-y:auto}
.sidebar-title{font-size:18px;font-weight:700;margin-bottom:20px;color:#0075de}
.sidebar-link{display:block;padding:8px 12px;border-radius:6px;color:#37352f;text-decoration:none;font-size:14px;margin-bottom:2px;transition:background .15s}
.sidebar-link:hover{background:rgba(0,117,222,0.08)}
.sidebar-link.active{background:rgba(0,117,222,0.12);color:#0075de;font-weight:600}
.main{flex:1;padding:40px 60px 80px;max-width:900px;margin:0 auto}
h1{font-size:44px;font-weight:700;margin-bottom:16px;color:#1a1a1a}
h2{font-size:28px;font-weight:700;margin:32px 0 16px;padding-bottom:8px;border-bottom:1px solid rgba(0,0,0,0.1)}
h3{font-size:22px;font-weight:600;margin:24px 0 12px}
h4{font-size:18px;font-weight:600;margin:20px 0 8px}
p{margin-bottom:12px}
ul,ol{margin:0 0 16px 24px}
li{margin-bottom:4px}
a{color:#0075de;text-decoration:none}
a:hover{text-decoration:underline}
code{font-family:'SF Mono','Fira Code',monospace;background:#f6f5f4;padding:2px 6px;border-radius:4px;font-size:14px}
pre{background:#f6f5f4;padding:20px;border-radius:8px;overflow-x:auto;margin-bottom:16px;border:1px solid rgba(0,0,0,0.06)}
pre code{background:none;padding:0;font-size:13.5px;line-height:1.6}
table{width:100%;border-collapse:collapse;margin-bottom:16px;font-size:14.5px}
th{background:#f6f5f4;font-weight:600;text-align:left;padding:10px 12px;border:1px solid rgba(0,0,0,0.1)}
td{padding:8px 12px;border:1px solid rgba(0,0,0,0.1)}
tr:nth-child(even){background:#fafafa}
blockquote{border-left:4px solid #0075de;padding:12px 16px;margin:0 0 16px;background:#f0f7ff;border-radius:0 8px 8px 0}
.badge{display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;margin-right:6px}
.badge-green{background:#dbeddb;color:#2d6a2e}
.badge-yellow{background:#fdecc8;color:#8a6a00}
.badge-orange{background:#fadec9;color:#935400}
.badge-red{background:#ffe2dd;color:#c43b3b}
.toc{background:#f9f9f8;border:1px solid rgba(0,0,0,0.1);border-radius:8px;padding:16px 20px;margin-bottom:24px}
.toc-title{font-weight:600;margin-bottom:8px;font-size:15px}
.toc a{font-size:14px;display:block;padding:3px 0;color:#37352f}
.card{border:1px solid rgba(0,0,0,0.1);border-radius:12px;padding:24px;margin-bottom:16px;transition:box-shadow .2s}
.card:hover{box-shadow:0 4px 12px rgba(0,0,0,0.08)}
.card-title{font-size:20px;font-weight:600;margin-bottom:8px}
.card-desc{color:#6b7280;font-size:14px}
.svg-diagram{margin:20px 0;text-align:center}
.svg-diagram svg{max-width:100%;height:auto}
.cross-ref{background:#f0f7ff;border:1px solid rgba(0,117,222,0.2);border-radius:8px;padding:12px 16px;margin:12px 0;font-size:14px}
.cross-ref strong{color:#0075de}
@media(max-width:900px){body{flex-direction:column}.sidebar{width:100%;min-width:auto;height:auto;position:relative}.main{padding:20px}}
"""

def md_to_html(text):
    """Convert markdown text to HTML."""
    lines = text.split('\n')
    out = []
    in_code = False
    code_lang = ''
    in_table = False
    table_rows = []
    
    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code:
                out.append('</code></pre>')
                in_code = False
                continue
            else:
                in_code = True
                code_lang = line.strip()[3:].strip()
                cls = f' class="language-{code_lang}"' if code_lang else ''
                out.append(f'<pre><code{cls}>')
                continue
        if in_code:
            out.append(h.escape(line))
            continue
        
        # Tables
        if '|' in line and line.strip().startswith('|'):
            cells = [c.strip() for c in line.strip().split('|')[1:-1]]
            if all(re.match(r'^[-:]+$', c) for c in cells):
                continue  # separator row
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            continue
        elif in_table:
            # Flush table
            out.append(_render_table(table_rows))
            in_table = False
            table_rows = []
        
        # Headings
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            txt = m.group(2).strip()
            anchor = re.sub(r'[^\w\u4e00-\u9fff-]', '', txt.replace(' ', '-'))[:60]
            out.append(f'<h{level} id="{anchor}">{_inline(txt)}</h{level}>')
            continue
        
        # Blockquote
        if line.strip().startswith('>'):
            content = line.strip().lstrip('>').strip()
            out.append(f'<blockquote><p>{_inline(content)}</p></blockquote>')
            continue
        
        # HR
        if re.match(r'^---+\s*$', line.strip()):
            out.append('<hr style="border:none;border-top:1px solid rgba(0,0,0,0.1);margin:24px 0">')
            continue
        
        # Unordered list
        m2 = re.match(r'^(\s*)[-*]\s+(.*)', line)
        if m2:
            indent = len(m2.group(1))
            content = m2.group(2)
            out.append(f'<li style="margin-left:{indent}px">{_inline(content)}</li>')
            continue
        
        # Ordered list
        m3 = re.match(r'^(\s*)\d+\.\s+(.*)', line)
        if m3:
            indent = len(m3.group(1))
            content = m3.group(2)
            out.append(f'<li style="margin-left:{indent}px">{_inline(content)}</li>')
            continue
        
        # Empty line
        if not line.strip():
            continue
        
        # Regular paragraph
        out.append(f'<p>{_inline(line)}</p>')
    
    if in_table:
        out.append(_render_table(table_rows))
    
    return '\n'.join(out)

def _inline(text):
    """Process inline markdown."""
    # wikilinks
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'<a href="#\2">\2</a>', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'<a href="#\1">\1</a>', text)
    # bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text

def _render_table(rows):
    if not rows:
        return ''
    out = ['<table>']
    # First row as header
    out.append('<thead><tr>')
    for cell in rows[0]:
        out.append(f'<th>{_inline(cell)}</th>')
    out.append('</tr></thead><tbody>')
    for row in rows[1:]:
        out.append('<tr>')
        for cell in row:
            out.append(f'<td>{_inline(cell)}</td>')
        out.append('</tr>')
    out.append('</tbody></table>')
    return '\n'.join(out)

def wrap_page(title, active_idx, body_html, toc_html=""):
    """Wrap content in full HTML page."""
    sidebar_items = [str(1 if i == active_idx else 0) for i in range(10)]
    sidebar = SIDEBAR.format(*sidebar_items)
    toc_section = f'<div class="toc"><div class="toc-title">目录</div>{toc_html}</div>' if toc_html else ''
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} - AI Advanced</title>
<style>{CSS}</style>
</head>
<body>
{sidebar}
<main class="main">
<h1>{title}</h1>
{toc_section}
{body_html}
</main>
</body>
</html>"""

def make_toc(sections):
    """Generate TOC from list of (title, anchor) tuples."""
    return ''.join(f'<a href="#{a}">{t}</a>' for t, a in sections)

def badge(level):
    colors = {'入门':'green','中级':'yellow','高级':'orange','面试':'red'}
    return f'<span class="badge badge-{colors.get(level,"yellow")}">{level}</span>'

def svg_vector_db_flow():
    return '''<svg viewBox="0 0 800 300" xmlns="http://www.w3.org/2000/svg" style="max-width:700px">
<defs><marker id="ah" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#0075de"/></marker></defs>
<rect x="10" y="110" width="140" height="60" rx="8" fill="#f0f7ff" stroke="#0075de"/>
<text x="80" y="145" text-anchor="middle" font-size="14" fill="#1a1a1a">原始文档</text>
<line x1="150" y1="140" x2="190" y2="140" stroke="#0075de" marker-end="url(#ah)"/>
<rect x="190" y="110" width="140" height="60" rx="8" fill="#f0f7ff" stroke="#0075de"/>
<text x="260" y="135" text-anchor="middle" font-size="13" fill="#1a1a1a">Embedding</text>
<text x="260" y="155" text-anchor="middle" font-size="12" fill="#6b7280">向量化模型</text>
<line x1="330" y1="140" x2="370" y2="140" stroke="#0075de" marker-end="url(#ah)"/>
<rect x="370" y="110" width="140" height="60" rx="8" fill="#dbeddb" stroke="#2d6a2e"/>
<text x="440" y="135" text-anchor="middle" font-size="13" fill="#1a1a1a">索引构建</text>
<text x="440" y="155" text-anchor="middle" font-size="12" fill="#6b7280">HNSW/IVF/PQ</text>
<line x1="510" y1="140" x2="550" y2="140" stroke="#0075de" marker-end="url(#ah)"/>
<rect x="550" y="110" width="140" height="60" rx="8" fill="#fdecc8" stroke="#8a6a00"/>
<text x="620" y="135" text-anchor="middle" font-size="13" fill="#1a1a1a">向量数据库</text>
<text x="620" y="155" text-anchor="middle" font-size="12" fill="#6b7280">Milvus/Qdrant/...</text>
<rect x="10" y="220" width="140" height="60" rx="8" fill="#f0f7ff" stroke="#0075de"/>
<text x="80" y="245" text-anchor="middle" font-size="14" fill="#1a1a1a">查询文本</text>
<text x="80" y="265" text-anchor="middle" font-size="12" fill="#6b7280">用户输入</text>
<line x1="150" y1="250" x2="190" y2="250" stroke="#0075de" marker-end="url(#ah)"/>
<line x1="260" y1="170" x2="260" y2="220" stroke="#0075de" stroke-dasharray="4" marker-end="url(#ah)"/>
<rect x="190" y="220" width="140" height="60" rx="8" fill="#f0f7ff" stroke="#0075de"/>
<text x="260" y="245" text-anchor="middle" font-size="13" fill="#1a1a1a">Query Embedding</text>
<text x="260" y="265" text-anchor="middle" font-size="12" fill="#6b7280">同一模型</text>
<line x1="330" y1="250" x2="550" y2="175" stroke="#0075de" marker-end="url(#ah)"/>
<text x="440" y="200" text-anchor="middle" font-size="12" fill="#0075de">相似度搜索</text>
<rect x="550" y="220" width="140" height="60" rx="8" fill="#fadec9" stroke="#935400"/>
<text x="620" y="245" text-anchor="middle" font-size="13" fill="#1a1a1a">Top-K 结果</text>
<text x="620" y="265" text-anchor="middle" font-size="12" fill="#6b7280">相关文档</text>
</svg>'''

def svg_safety_pipeline():
    return '''<svg viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg" style="max-width:700px">
<defs><marker id="ah2" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#0075de"/></marker></defs>
<rect x="10" y="70" width="120" height="60" rx="8" fill="#ffe2dd" stroke="#c43b3b"/>
<text x="70" y="95" text-anchor="middle" font-size="12" fill="#1a1a1a">用户输入</text>
<text x="70" y="115" text-anchor="middle" font-size="11" fill="#6b7280">Raw Input</text>
<line x1="130" y1="100" x2="155" y2="100" stroke="#0075de" marker-end="url(#ah2)"/>
<rect x="155" y="70" width="100" height="60" rx="8" fill="#fdecc8" stroke="#8a6a00"/>
<text x="205" y="95" text-anchor="middle" font-size="11" fill="#1a1a1a">注入检测</text>
<text x="205" y="110" text-anchor="middle" font-size="10" fill="#6b7280">Prompt</text>
<text x="205" y="123" text-anchor="middle" font-size="10" fill="#6b7280">Injection</text>
<line x1="255" y1="100" x2="280" y2="100" stroke="#0075de" marker-end="url(#ah2)"/>
<rect x="280" y="70" width="100" height="60" rx="8" fill="#fdecc8" stroke="#8a6a00"/>
<text x="330" y="95" text-anchor="middle" font-size="11" fill="#1a1a1a">PII过滤</text>
<text x="330" y="110" text-anchor="middle" font-size="10" fill="#6b7280">Personal</text>
<text x="330" y="123" text-anchor="middle" font-size="10" fill="#6b7280">Data</text>
<line x1="380" y1="100" x2="405" y2="100" stroke="#0075de" marker-end="url(#ah2)"/>
<rect x="405" y="70" width="120" height="60" rx="8" fill="#f0f7ff" stroke="#0075de"/>
<text x="465" y="95" text-anchor="middle" font-size="12" fill="#1a1a1a">LLM 推理</text>
<text x="465" y="115" text-anchor="middle" font-size="11" fill="#6b7280">Guarded Model</text>
<line x1="525" y1="100" x2="550" y2="100" stroke="#0075de" marker-end="url(#ah2)"/>
<rect x="550" y="70" width="100" height="60" rx="8" fill="#fdecc8" stroke="#8a6a00"/>
<text x="600" y="95" text-anchor="middle" font-size="11" fill="#1a1a1a">内容审核</text>
<text x="600" y="110" text-anchor="middle" font-size="10" fill="#6b7280">Moderation</text>
<line x1="650" y1="100" x2="675" y2="100" stroke="#0075de" marker-end="url(#ah2)"/>
<rect x="675" y="70" width="100" height="60" rx="8" fill="#dbeddb" stroke="#2d6a2e"/>
<text x="725" y="95" text-anchor="middle" font-size="11" fill="#1a1a1a">安全输出</text>
<text x="725" y="115" text-anchor="middle" font-size="11" fill="#6b7280">Safe Output</text>
</svg>'''

def svg_deployment_arch():
    return '''<svg viewBox="0 0 800 350" xmlns="http://www.w3.org/2000/svg" style="max-width:700px">
<defs><marker id="ah3" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#0075de"/></marker></defs>
<rect x="300" y="10" width="200" height="50" rx="8" fill="#f0f7ff" stroke="#0075de"/>
<text x="400" y="40" text-anchor="middle" font-size="14" fill="#1a1a1a">客户端 / SDK</text>
<line x1="400" y1="60" x2="400" y2="90" stroke="#0075de" marker-end="url(#ah3)"/>
<rect x="250" y="90" width="300" height="50" rx="8" fill="#fdecc8" stroke="#8a6a00"/>
<text x="400" y="115" text-anchor="middle" font-size="13" fill="#1a1a1a">Nginx / HAProxy 负载均衡</text>
<text x="400" y="130" text-anchor="middle" font-size="11" fill="#6b7280">SSL终止 + 限流 + 路由</text>
<line x1="300" y1="140" x2="150" y2="180" stroke="#0075de" marker-end="url(#ah3)"/>
<line x1="400" y1="140" x2="400" y2="180" stroke="#0075de" marker-end="url(#ah3)"/>
<line x1="500" y1="140" x2="650" y2="180" stroke="#0075de" marker-end="url(#ah3)"/>
<rect x="80" y="180" width="150" height="50" rx="8" fill="#dbeddb" stroke="#2d6a2e"/>
<text x="155" y="200" text-anchor="middle" font-size="12" fill="#1a1a1a">vLLM Instance 1</text>
<text x="155" y="220" text-anchor="middle" font-size="11" fill="#6b7280">GPU: A100</text>
<rect x="325" y="180" width="150" height="50" rx="8" fill="#dbeddb" stroke="#2d6a2e"/>
<text x="400" y="200" text-anchor="middle" font-size="12" fill="#1a1a1a">vLLM Instance 2</text>
<text x="400" y="220" text-anchor="middle" font-size="11" fill="#6b7280">GPU: A100</text>
<rect x="575" y="180" width="150" height="50" rx="8" fill="#dbeddb" stroke="#2d6a2e"/>
<text x="650" y="200" text-anchor="middle" font-size="12" fill="#1a1a1a">TGI Instance</text>
<text x="650" y="220" text-anchor="middle" font-size="11" fill="#6b7280">GPU: A10</text>
<line x1="155" y1="230" x2="155" y2="260" stroke="#0075de" marker-end="url(#ah3)"/>
<line x1="400" y1="230" x2="400" y2="260" stroke="#0075de" marker-end="url(#ah3)"/>
<line x1="650" y1="230" x2="650" y2="260" stroke="#0075de" marker-end="url(#ah3)"/>
<rect x="100" y="260" width="600" height="50" rx="8" fill="#fadec9" stroke="#935400"/>
<text x="400" y="280" text-anchor="middle" font-size="13" fill="#1a1a1a">Prometheus + Grafana 监控</text>
<text x="400" y="300" text-anchor="middle" font-size="11" fill="#6b7280">延迟 / 吞吐 / 错误率 / GPU使用率</text>
<rect x="100" y="320" width="280" height="30" rx="6" fill="#f6f5f4" stroke="rgba(0,0,0,0.1)"/>
<text x="240" y="340" text-anchor="middle" font-size="11" fill="#6b7280">HPA 自动扩缩容 (K8s)</text>
<rect x="420" y="320" width="280" height="30" rx="6" fill="#f6f5f4" stroke="rgba(0,0,0,0.1)"/>
<text x="560" y="340" text-anchor="middle" font-size="11" fill="#6b7280">金丝雀发布 / A/B测试</text>
</svg>'''

def svg_observability():
    return '''<svg viewBox="0 0 800 280" xmlns="http://www.w3.org/2000/svg" style="max-width:700px">
<rect x="10" y="10" width="780" height="50" rx="8" fill="#f0f7ff" stroke="#0075de"/>
<text x="400" y="40" text-anchor="middle" font-size="14" fill="#1a1a1a">LLM Application (FastAPI / LangChain / Hermes Agent)</text>
<rect x="10" y="80" width="780" height="40" rx="6" fill="#f6f5f4" stroke="rgba(0,0,0,0.1)"/>
<text x="200" y="105" text-anchor="middle" font-size="12" fill="#1a1a1a">OpenTelemetry SDK</text>
<text x="400" y="105" text-anchor="middle" font-size="12" fill="#6b7280">|</text>
<text x="400" y="105" text-anchor="middle" font-size="12" fill="#1a1a1a">LangSmith / Langfuse</text>
<text x="600" y="105" text-anchor="middle" font-size="12" fill="#6b7280">|</text>
<text x="650" y="105" text-anchor="middle" font-size="12" fill="#1a1a1a">Prometheus</text>
<line x1="400" y1="120" x2="400" y2="145" stroke="#0075de" stroke-width="2" marker-end="url(#ah)"/>
<rect x="100" y="145" width="600" height="40" rx="6" fill="#fdecc8" stroke="#8a6a00"/>
<text x="400" y="170" text-anchor="middle" font-size="13" fill="#1a1a1a">OTel Collector / Langfuse Server / Prometheus Server</text>
<line x1="200" y1="185" x2="130" y2="215" stroke="#0075de" marker-end="url(#ah)"/>
<line x1="400" y1="185" x2="400" y2="215" stroke="#0075de" marker-end="url(#ah)"/>
<line x1="600" y1="185" x2="670" y2="215" stroke="#0075de" marker-end="url(#ah)"/>
<rect x="50" y="215" width="160" height="50" rx="8" fill="#dbeddb" stroke="#2d6a2e"/>
<text x="130" y="235" text-anchor="middle" font-size="12" fill="#1a1a1a">Grafana Tempo</text>
<text x="130" y="253" text-anchor="middle" font-size="11" fill="#6b7280">Trace 可视化</text>
<rect x="320" y="215" width="160" height="50" rx="8" fill="#dbeddb" stroke="#2d6a2e"/>
<text x="400" y="235" text-anchor="middle" font-size="12" fill="#1a1a1a">Langfuse Dashboard</text>
<text x="400" y="253" text-anchor="middle" font-size="11" fill="#6b7280">成本/质量/评估</text>
<rect x="590" y="215" width="160" height="50" rx="8" fill="#dbeddb" stroke="#2d6a2e"/>
<text x="670" y="235" text-anchor="middle" font-size="12" fill="#1a1a1a">Grafana Dashboard</text>
<text x="670" y="253" text-anchor="middle" font-size="11" fill="#6b7280">Metrics / 告警</text>
</svg>'''

# ── Page definitions ──────────────────────────────────────────

def page_index():
    body = """
<p style="font-size:18px;color:#6b7280;margin-bottom:32px">AI 大模型进阶知识体系 -- 从推理部署到安全护栏的完整技术栈</p>

<div class="card"><a href="cv.html"><div class="card-title">08 计算机视觉基础</div></a><div class="card-desc">经典CNN网络 (LeNet/AlexNet/GoogLeNet)、卷积与池化、目标检测技术、ROI Pooling/Align</div></div>

<div class="card"><a href="interview.html"><div class="card-title">09 面试宝典</div></a><div class="card-desc">深度学习面试题、计算机视觉面试题、数据处理、机器学习、NLP、大语言模型、数据结构与算法</div></div>

<div class="card"><a href="projects.html"><div class="card-title">10 项目实战</div></a><div class="card-desc">RAG与Agent智能体、DeepSeek-RAG、智图寻宝、AI医疗、AI智教、智能商品发布、智选新闻等11个实战项目</div></div>

<div class="card"><a href="multimodal.html"><div class="card-title">11 多模态开发</div></a><div class="card-desc">腾讯云AI绘画API、文生图/图生图、SaaS平台、小程序端集成</div></div>

<div class="card"><a href="inference.html"><div class="card-title">12 LLM推理部署</div></a><div class="card-desc">vLLM PagedAttention、llama.cpp GGUF量化、TGI推理服务、推测解码、批处理调度、性能基准测试</div></div>

<div class="card"><a href="vectordb.html"><div class="card-title">13 向量数据库</div></a><div class="card-desc">Milvus分布式向量DB、Pinecone云原生、Qdrant与pgvector、Weaviate多模态搜索、选型对比矩阵</div></div>

<div class="card"><a href="observability.html"><div class="card-title">14 LLM可观测性</div></a><div class="card-desc">LangSmith追踪评估、Langfuse开源可观测性、OpenTelemetry for LLM、监控最佳实践</div></div>

<div class="card"><a href="safety.html"><div class="card-title">15 AI安全与护栏</div></a><div class="card-desc">Prompt注入与越狱防护、输出内容安全、Guardrails框架、红队测试方法论</div></div>

<div class="card"><a href="serving.html"><div class="card-title">16 模型服务与部署</div></a><div class="card-desc">API服务封装、负载均衡与扩展、模型灰度发布、成本管理与优化</div></div>

<div class="cross-ref"><strong>关联项目:</strong> <a href="inference.html">llm-api-gateway</a> (推理网关) | <a href="safety.html">ai-safety-guardrails</a> (安全护栏) | <a href="observability.html">observability-dashboard</a> (可观测性面板)</div>

<div class="svg-diagram"><h3>部署架构总览</h3>""" + svg_deployment_arch() + """</div>
"""
    return wrap_page("AI Advanced 总览", 0, body)


def page_cv():
    from pathlib import Path
    md = Path("/home/pez/knowledge-base/AI大模型/08-计算机视觉基础/经典网络与技术图解.md").read_text()
    body = md_to_html(md)
    toc = make_toc([("经典CNN网络","1-经典CNN网络"),("卷积与池化","2-卷积与池化"),("目标检测技术","3-目标检测技术"),("数据集","4-数据集"),("AI三剑客","5-AI三剑客")])
    return wrap_page("计算机视觉基础", 1, body, toc)


def page_interview():
    from pathlib import Path
    md1 = Path("/home/pez/knowledge-base/AI大模型/09-面试宝典/深度学习与计算机视觉面试题.md").read_text()
    md2 = Path("/home/pez/knowledge-base/AI大模型/09-面试宝典/人工智能面试宝典-V6.6.md").read_text()
    # Truncate md2 to first 500 lines for manageability
    md2_lines = md2.split('\n')[:500]
    md2 = '\n'.join(md2_lines)
    body = f'<h2>深度学习与计算机视觉面试题</h2>\n{md_to_html(md1)}\n<h2>人工智能面试宝典 V6.6 (精选)</h2>\n{md_to_html(md2)}\n<p style="color:#6b7280;font-size:14px">完整版包含 Python语言、数据处理、机器学习、深度学习、NLP、大语言模型、数据结构与算法、计算机视觉等章节。</p>'
    return wrap_page("面试宝典", 2, body)


def page_projects():
    from pathlib import Path
    base = Path("/home/pez/knowledge-base/AI大模型/10-项目实战")
    readme = (base / "README.md").read_text()
    
    projects = [
        ("RAG与Agent智能体", "黑马RAG-Agent项目", ["01-提示词工程.md","02-大模型RAG开发.md","03-RAG项目实战.md","04-项目数据资料.md"]),
        ("DeepSeek-RAG", "DeepSeek-RAG", ["README.md","CLAUDE.md"]),
        ("智图寻宝", "智图寻宝", ["智图寻宝.md"]),
        ("智能商品发布", "智能商品发布", ["智能商品发布.md"]),
        ("地址对齐", "地址对齐", ["地址对齐.md"]),
        ("智选新闻", "智选新闻", ["智选新闻.md"]),
        ("智荐图谱-电商图谱", "智荐图谱", ["电商图谱.md","Neo4j.md"]),
        ("AI智教", "AI智教", ["AI智教.md"]),
        ("智医助手", "智医助手", ["智医助手.md"]),
        ("AI学情", "AI学情", ["AI学情.md"]),
        ("AI医疗", "AI医疗", ["AI医疗.md"]),
    ]
    
    cards = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px;margin-bottom:32px">'
    for name, folder, _ in projects:
        cards += f'<div class="card"><div class="card-title">{name}</div><div class="card-desc">项目目录: {folder}/</div></div>'
    cards += '</div>'
    
    body = md_to_html(readme) + cards + '<h2>项目详细文档</h2>'
    for name, folder, files in projects:
        body += f'<h3>{name}</h3>'
        for fname in files:
            fpath = base / folder / fname
            if fpath.exists():
                md = fpath.read_text()
                body += md_to_html(md)
    
    return wrap_page("项目实战", 3, body)


def page_multimodal():
    from pathlib import Path
    base = Path("/home/pez/knowledge-base/AI大模型/11-多模态开发")
    readme = (base / "README.md").read_text()
    art = (base / "01-腾讯云AI绘画.md").read_text()
    body = md_to_html(readme) + md_to_html(art)
    return wrap_page("多模态开发", 4, body)


def page_inference():
    from pathlib import Path
    base = Path("/home/pez/knowledge-base/AI大模型/12-LLM推理部署")
    files = ["01-vLLM部署与配置.md","02-llama.cpp与GGUF.md","03-TGI推理服务.md","04-推测解码技术.md","05-批处理与调度策略.md","06-推理性能基准测试.md"]
    body = '<div class="cross-ref"><strong>关联项目:</strong> <a href="../projects/llm-api-gateway.html">llm-api-gateway</a> -- LLM推理网关，集成限流、监控、安全过滤</div>'
    for f in files:
        md = (base / f).read_text()
        body += md_to_html(md)
    toc = make_toc([("vLLM部署与配置","vLLM-部署与配置"),("llama.cpp与GGUF","llamacpp-与-GGUF"),("TGI推理服务","TGI-Text-Generation-Inference-推理服务"),("推测解码技术","推测解码技术-Speculative-Decoding"),("批处理与调度策略","批处理与调度策略"),("推理性能基准测试","推理性能基准测试")])
    return wrap_page("LLM推理部署", 5, body, toc)


def page_vectordb():
    from pathlib import Path
    base = Path("/home/pez/knowledge-base/AI大模型/13-向量数据库")
    files = ["01-Milvus分布式向量DB.md","02-Pinecone云原生向量DB.md","03-Qdrant与pgvector.md","04-Weaviate多模态搜索.md","05-向量DB选型对比矩阵.md"]
    body = '<div class="svg-diagram"><h3>向量数据库索引流程</h3>' + svg_vector_db_flow() + '</div>'
    for f in files:
        md = (base / f).read_text()
        body += md_to_html(md)
    toc = make_toc([("Milvus分布式向量DB","Milvus-分布式向量数据库"),("Pinecone云原生向量DB","Pinecone-云原生向量数据库"),("Qdrant与pgvector","Qdrant-与-pgvector"),("Weaviate多模态搜索","Weaviate-多模态向量搜索"),("向量DB选型对比矩阵","向量数据库选型对比矩阵")])
    return wrap_page("向量数据库", 6, body, toc)


def page_observability():
    from pathlib import Path
    base = Path("/home/pez/knowledge-base/AI大模型/14-LLM可观测性")
    files = ["01-LangSmith追踪与评估.md","02-Langfuse开源可观测性.md","03-OpenTelemetry-for-LLM.md","04-LLM监控最佳实践.md"]
    body = '<div class="cross-ref"><strong>关联项目:</strong> <a href="../projects/observability-dashboard.html">observability-dashboard</a> -- LLM可观测性监控面板</div>'
    body += '<div class="svg-diagram"><h3>可观测性技术栈</h3>' + svg_observability() + '</div>'
    for f in files:
        md = (base / f).read_text()
        body += md_to_html(md)
    toc = make_toc([("LangSmith追踪与评估","LangSmith-追踪与评估"),("Langfuse开源可观测性","Langfuse-开源可观测性"),("OpenTelemetry for LLM","OpenTelemetry-for-LLM"),("LLM监控最佳实践","LLM-监控最佳实践")])
    return wrap_page("LLM可观测性", 7, body, toc)


def page_safety():
    from pathlib import Path
    base = Path("/home/pez/knowledge-base/AI大模型/15-AI安全与护栏")
    files = ["01-Prompt注入与越狱防护.md","02-输出内容安全防护.md","03-Guardrails框架实战.md","04-红队测试方法论.md"]
    body = '<div class="cross-ref"><strong>关联项目:</strong> <a href="../projects/ai-safety-guardrails.html">ai-safety-guardrails</a> -- AI安全护栏系统，集成注入检测、内容审核、PII过滤</div>'
    body += '<div class="svg-diagram"><h3>安全防护管线</h3>' + svg_safety_pipeline() + '</div>'
    for f in files:
        md = (base / f).read_text()
        body += md_to_html(md)
    toc = make_toc([("Prompt注入与越狱防护","Prompt-注入与越狱防护"),("输出内容安全防护","输出内容安全防护"),("Guardrails框架实战","Guardrails-框架实战"),("红队测试方法论","红队测试方法论")])
    return wrap_page("AI安全与护栏", 8, body, toc)


def page_serving():
    from pathlib import Path
    base = Path("/home/pez/knowledge-base/AI大模型/16-模型服务与部署")
    files = ["01-API服务封装.md","02-负载均衡与扩展.md","03-模型灰度发布.md","04-成本管理与优化.md"]
    body = '<div class="cross-ref"><strong>关联项目:</strong> <a href="../projects/llm-api-gateway.html">llm-api-gateway</a> -- LLM API网关，集成负载均衡、灰度发布、成本管控</div>'
    body += '<div class="svg-diagram"><h3>部署架构</h3>' + svg_deployment_arch() + '</div>'
    for f in files:
        md = (base / f).read_text()
        body += md_to_html(md)
    toc = make_toc([("API服务封装","API-服务封装"),("负载均衡与扩展","负载均衡与扩展"),("模型灰度发布","模型灰度发布"),("成本管理与优化","成本管理与优化")])
    return wrap_page("模型服务与部署", 9, body, toc)


# ── Generate all pages ────────────────────────────────────────
if __name__ == "__main__":
    pages = [
        ("index.html", page_index),
        ("cv.html", page_cv),
        ("interview.html", page_interview),
        ("projects.html", page_projects),
        ("multimodal.html", page_multimodal),
        ("inference.html", page_inference),
        ("vectordb.html", page_vectordb),
        ("observability.html", page_observability),
        ("safety.html", page_safety),
        ("serving.html", page_serving),
    ]
    for fname, func in pages:
        print(f"Generating {fname}...")
        html = func()
        with open(os.path.join(OUT, fname), 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  -> {fname} ({len(html)} bytes)")
    print("Done!")
