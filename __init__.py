from aqt import mw
from aqt import gui_hooks
from aqt.utils import tooltip
from anki.cards import Card

FIELD_NAME = "LearningHistory"
SYMBOLS = ['✕', '△', '◯', '◎']

last_clicked_card_id = None

def log_symbol(sym: str):
    """シンボルをノートに追加する共通処理"""
    global last_clicked_card_id
    
    if not mw.reviewer or not mw.reviewer.card:
        return
        
    card = mw.reviewer.card
    note = card.note()
    
    # 解答面（裏面）が表示されている時のみ実行
    if mw.reviewer.state != "answer":
        return
        
    if FIELD_NAME in note and card.id != last_clicked_card_id:
        last_clicked_card_id = card.id
        note[FIELD_NAME] += sym
        mw.col.update_note(note)
        mw.reviewer._redraw_current_card()
        tooltip(f"Logged '{sym}' to {FIELD_NAME}", period=1200)

def on_show_question(card: Card):
    """質問面が表示されたらコンテナを削除"""
    js_code = """
    var oldDiv = document.getElementById('lh-buttons-container');
    if (oldDiv) oldDiv.remove();
    """
    if mw.reviewer:
        mw.reviewer.web.eval(js_code)

def on_show_answer(card: Card):
    """解答面が表示されたらボタンを表示"""
    global last_clicked_card_id
    note = card.note()
    
    if FIELD_NAME not in note:
        return

    already_clicked = "true" if (card.id == last_clicked_card_id) else "false"

    js_code = f"""
    (function() {{
        var oldDiv = document.getElementById('lh-buttons-container');
        if (oldDiv) oldDiv.remove();

        var div = document.createElement('div');
        div.id = 'lh-buttons-container';
        
        div.style.display = 'flex';
        div.style.flexDirection = 'row';
        div.style.flexWrap = 'nowrap';
        div.style.justifyContent = 'center';
        div.style.alignItems = 'center';
        div.style.gap = '8px';
        div.style.padding = '4px 0 0 0';
        div.style.margin = '4px auto 0 auto';
        div.style.borderTop = '1px solid var(--border, #e0e0e0)';
        div.style.maxWidth = '100%';
        div.style.boxSizing = 'border-box';

        var symbols = {str(SYMBOLS)};
        var alreadyClicked = {already_clicked};

        symbols.forEach(function(sym) {{
            var btn = document.createElement('button');
            btn.className = 'lh-btn';
            btn.innerText = sym;
            
            btn.style.display = 'flex';
            btn.style.alignItems = 'center';
            btn.style.justifyContent = 'center';
            btn.style.width = '44px';
            btn.style.height = '30px';
            btn.style.flexShrink = '0';
            btn.style.fontSize = '16px';
            btn.style.borderRadius = '4px';
            btn.style.border = '1px solid #bbb';
            btn.style.backgroundColor = 'var(--canvas, #f5f5f5)';
            btn.style.color = 'var(--text-main, #000)';

            if (alreadyClicked) {{
                btn.disabled = true; 
                btn.style.opacity = '0.4';
                btn.style.cursor = 'not-allowed';
            }} else {{
                btn.style.cursor = 'pointer';
                btn.onclick = function() {{
                    var btns = document.querySelectorAll('.lh-btn');
                    btns.forEach(function(b) {{ 
                        b.disabled = true; 
                        b.style.opacity = '0.4';
                        b.style.cursor = 'not-allowed';
                    }});
                    pycmd('lh_add_symbol:' + sym);
                }};
            }}
            div.appendChild(btn);
        }});

        var target = null;
        var walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
        var node = walk.nextNode();
        
        while (node) {{
            if (node.nodeValue.includes('学習履歴')) {{
                target = node.parentElement;
                break;
            }}
            node = walk.nextNode();
        }}

        if (target) {{
            var container = target;
            while (container && container.parentElement && 
                   container.parentElement !== document.body && 
                   container.parentElement.id !== 'qa' &&
                   window.getComputedStyle(container).display === 'inline') {{
                container = container.parentElement;
            }}
            container.parentNode.insertBefore(div, container.nextSibling);
        }} else {{
            var cardContainer = document.getElementById('qa') || document.body;
            cardContainer.appendChild(div);
        }}

        document.body.style.paddingBottom = "0px";
        document.body.style.marginBottom = "0px";
        document.documentElement.style.paddingBottom = "0px";
        document.documentElement.style.marginBottom = "0px";
        
        var qa = document.getElementById('qa');
        if (qa) {{
            qa.style.paddingBottom = "0px";
            qa.style.marginBottom = "0px";
        }}
        
        var cardFrame = document.querySelector('.card');
        if (cardFrame) {{
            cardFrame.style.paddingBottom = "8px";
            cardFrame.style.marginBottom = "4px";
        }}
    }})();
    """
    
    if mw.reviewer:
        mw.reviewer.web.eval(js_code)

def on_js_message(handled, message, context):
    """JavaScriptからのボタンクリック通知を処理"""
    if not message.startswith("lh_add_symbol:"):
        return handled
    
    sym = message.split(":", 1)[1]
    log_symbol(sym)
    return (True, None)

# Ankiの_shortcutKeysメソッドを拡張して独自キーを追加
def extended_shortcut_keys(reviewer):
    original_keys = reviewer._old_shortcutKeys() if hasattr(reviewer, "_old_shortcutKeys") else []
    
    # Macにおける "Meta" は 物理 Control キー (^) を指します
    custom_keys = [
        ("Meta+1", lambda: log_symbol(SYMBOLS[0])),
        ("Meta+2", lambda: log_symbol(SYMBOLS[1])),
        ("Meta+3", lambda: log_symbol(SYMBOLS[2])),
        ("Meta+4", lambda: log_symbol(SYMBOLS[3])),
    ]
    return original_keys + custom_keys

# レビュアーの_shortcutKeysを動的に置き換え
from aqt.reviewer import Reviewer

if not hasattr(Reviewer, "_lh_patched"):
    Reviewer._old_shortcutKeys = Reviewer._shortcutKeys
    Reviewer._shortcutKeys = extended_shortcut_keys
    Reviewer._lh_patched = True

# Hook登録
gui_hooks.reviewer_did_show_question.append(on_show_question)
gui_hooks.reviewer_did_show_answer.append(on_show_answer)
gui_hooks.webview_did_receive_js_message.append(on_js_message)