from __future__ import annotations


def build_chip_color_script(color_payload_json: str) -> str:
    return f"""
    <script>
    (function() {{
      const colorMap = {color_payload_json};
      const normalize = (txt) => String(txt || '').replace('×', '').trim();
      const applyColors = () => {{
        try {{
          const doc = window.parent.document;
          const tags = doc.querySelectorAll('div[data-baseweb="tag"]');
          tags.forEach((tag) => {{
            const key = normalize(tag.textContent);
            const color = colorMap[key];
            if (!color) return;
            tag.style.background = color;
            tag.style.borderColor = color;
            tag.style.color = '#1c2033';
            const closeBtn = tag.querySelector('button');
            if (closeBtn) closeBtn.style.color = '#1c2033';
          }});
        }} catch (e) {{
          // no-op
        }}
      }};
      applyColors();
      const obs = new MutationObserver(() => applyColors());
      obs.observe(window.parent.document.body, {{ childList: true, subtree: true }});
    }})();
    </script>
    """


def build_schedule_pick_script() -> str:
    return """
    <script>
    (function () {
      const MAX_ATTEMPTS = 40;
      let attempts = 0;

      const tryBind = () => {
        attempts += 1;
        const doc = window.parent.document;
        const board = doc.querySelector('.board-root');
        const commitBtn = doc.querySelector('.st-key-schedule_pick_commit button');
        if (!board || !commitBtn) {
          if (attempts < MAX_ATTEMPTS) {
            window.setTimeout(tryBind, 120);
          }
          return;
        }

        const bindAll = () => {
          const buttons = board.querySelectorAll('.post-card-schedule-btn[data-item-id]');
          buttons.forEach((btn) => {
            if (btn.dataset.bound === '1') return;
            btn.dataset.bound = '1';
            btn.addEventListener('click', (ev) => {
              ev.preventDefault();
              ev.stopPropagation();
              if (typeof ev.stopImmediatePropagation === 'function') {
                ev.stopImmediatePropagation();
              }
              const itemId = String(btn.dataset.itemId || '').trim();
              if (!itemId) return;
              const pwin = window.parent;
              const url = new URL(pwin.location.href);
              url.searchParams.set('schedule_pick', itemId);
              pwin.history.replaceState({}, '', url.toString());
              btn.blur();
              // Delay rerun slightly so current click sequence fully ends,
              // avoiding accidental click-through to the dialog date input.
              window.setTimeout(() => commitBtn.click(), 90);
            });
          });
        };

        bindAll();
        const mo = new MutationObserver(() => bindAll());
        mo.observe(board, { childList: true, subtree: true });
      };

      tryBind();
    })();
    </script>
    """
