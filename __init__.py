from aqt import mw
from aqt import gui_hooks
from aqt.utils import tooltip
from anki.cards import Card

FIELD_NAME = "LearningHistory"
SYMBOLS = ['✕', '△', '◯', '◎']

# Tracks the clicked state across redraws
last_clicked_card_id = None

def on_show_question(card: Card):
    """Triggered when the front/question side of the card is shown.
    Guarantees the buttons are completely removed on the front view.
    """
    js_code = """
    var oldDiv = document.getElementById('lh-buttons-container');
    if (oldDiv) oldDiv.remove();
    """
    if mw.reviewer:
        mw.reviewer.web.eval(js_code)

def on_show_answer(card: Card):
    """Triggered when the back/answer side of the card is shown."""
    global last_clicked_card_id
    note = card.note()
    
    # Only inject buttons if the specific field exists in this note type
    if FIELD_NAME not in note:
        return

    # Pass down the clicked state so we know whether to render them locked
    already_clicked = "true" if (card.id == last_clicked_card_id) else "false"

    # JavaScript to inject buttons inside the white card container and strip excess margins
    js_code = f"""
    (function() {{
        // Prevent duplicate containers if the view re-renders
        var oldDiv = document.getElementById('lh-buttons-container');
        if (oldDiv) oldDiv.remove();

        var div = document.createElement('div');
        div.id = 'lh-buttons-container';
        
        // Strict row Flexbox configuration
        div.style.display = 'flex';
        div.style.flexDirection = 'row';
        div.style.flexWrap = 'nowrap';
        div.style.justifyContent = 'center';
        div.style.alignItems = 'center';
        div.style.gap = '8px';               // Gap between buttons
        
        // Aggressively stripped margins and padding
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
            
            // Tight button footprint
            btn.style.width = '44px';
            btn.style.height = '30px';
            btn.style.flexShrink = '0';
            btn.style.fontSize = '16px';
            
            btn.style.borderRadius = '4px';
            btn.style.border = '1px solid #bbb';
            btn.style.backgroundColor = 'var(--canvas, #f5f5f5)';
            btn.style.color = 'var(--text-main, #000)';

            // Set state based on whether this card has already logged a symbol
            if (alreadyClicked) {{
                btn.disabled = true; 
                btn.style.opacity = '0.4';
                btn.style.cursor = 'not-allowed';
            }} else {{
                btn.style.cursor = 'pointer';
                btn.onclick = function() {{
                    // Immediately disable all buttons to prevent double-clicks
                    var btns = document.querySelectorAll('.lh-btn');
                    btns.forEach(function(b) {{ 
                        b.disabled = true; 
                        b.style.opacity = '0.4';
                        b.style.cursor = 'not-allowed';
                    }});
                    // Send the selected symbol back to the Python backend
                    pycmd('lh_add_symbol:' + sym);
                }};
            }}
            div.appendChild(btn);
        }});

        // --- SAFE DOM INSERTION ---
        // Find the element containing "学習履歴" safely. All braces are properly escaped here.
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
            // Find the closest block-level parent so we don't break inline elements
            var container = target;
            while (container && container.parentElement && 
                   container.parentElement !== document.body && 
                   container.parentElement.id !== 'qa' &&
                   window.getComputedStyle(container).display === 'inline') {{
                container = container.parentElement;
            }}
            container.parentNode.insertBefore(div, container.nextSibling);
        }} else {{
            // Fallback if "学習履歴" text is somehow not found
            var cardContainer = document.getElementById('qa') || document.body;
            cardContainer.appendChild(div);
        }}

        // --- EXTRA SPACE CLEANUP ---
        // Force-strip massive margins from the document body and Anki wrapper
        document.body.style.paddingBottom = "0px";
        document.body.style.marginBottom = "0px";
        document.documentElement.style.paddingBottom = "0px";
        document.documentElement.style.marginBottom = "0px";
        
        var qa = document.getElementById('qa');
        if (qa) {{
            qa.style.paddingBottom = "0px";
            qa.style.marginBottom = "0px";
        }}
        
        // Tighten the custom card container itself
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
    """Handles the communication from the JavaScript button click to Python."""
    global last_clicked_card_id
    if not message.startswith("lh_add_symbol:"):
        return handled
    
    # Extract the clicked symbol
    sym = message.split(":", 1)[1]
    
    if mw.reviewer and mw.reviewer.card:
        card = mw.reviewer.card
        note = card.note()
        if FIELD_NAME in note:
            # Log this card ID to ensure buttons stay disabled after redraw
            last_clicked_card_id = card.id
            
            # Append the symbol to the end of the existing field text
            note[FIELD_NAME] += sym
            mw.col.update_note(note)
            
            # Force Anki to instantly refresh/redraw the current card view
            mw.reviewer._redraw_current_card()
            
            # Subtle confirmation toast
            tooltip(f"Logged '{sym}' to {FIELD_NAME}", period=1200)
            
    return (True, None)

# Register hooks into Anki's review lifecycle
gui_hooks.reviewer_did_show_question.append(on_show_question)
gui_hooks.reviewer_did_show_answer.append(on_show_answer)
gui_hooks.webview_did_receive_js_message.append(on_js_message)