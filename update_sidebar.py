import os
import glob
import re

TARGETS = ['dashboard.html', 'predict.html', 'history.html', 'diet.html', 'chat.html']
sidebar_template = """      <span class="sidebar-section-label">Main</span>
      <a href="/dashboard.html" class="sidebar-link{dash_active}">Dashboard</a>
      <a href="/predict.html" class="sidebar-link{pred_active}">Start Assessment</a>
      <a href="/diet.html" class="sidebar-link{diet_active}">Diet Plan</a>
      <a href="/history.html" class="sidebar-link{hist_active}">My History</a>
      <a href="/chat.html" class="sidebar-link{chat_active}">Chatbot</a>"""

for fpath in glob.glob('frontend/**/*.html', recursive=True):
    fname = os.path.basename(fpath)
    if fname not in TARGETS and ('login' not in fname and 'register' not in fname and 'index' not in fname):
        continue

    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Determine actives
    da = ' active' if fname == 'dashboard.html' else ''
    pa = ' active' if fname == 'predict.html' else ''
    dia = ' active' if fname == 'diet.html' else ''
    ha = ' active' if fname == 'history.html' else ''
    ca = ' active' if fname == 'chat.html' else ''
    
    rep = sidebar_template.format(dash_active=da, pred_active=pa, diet_active=dia, hist_active=ha, chat_active=ca)
    
    pattern = re.compile(r'<span class="sidebar-section-label">Main</span>(?:.*?)<div class="sidebar-foot">', re.DOTALL)
    
    if pattern.search(content):
        new_content = re.sub(pattern, rep + '\n    </nav>\n    <div class="sidebar-foot">', content)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    else:
        print(f"Pattern not found in {fname}")

print("Sidebars successfully updated!")
