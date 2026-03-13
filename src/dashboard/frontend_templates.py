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


def build_drag_drop_script() -> str:
    return """
    <script>
    (function () {
      const DBG = '[drag-schedule-debug]';
      const log = (...args) => console.log(DBG, ...args);
      log('script init');
      const parentDoc = window.parent.document;
      const board = parentDoc.querySelector('.board-root');
      if (!board) {
        log('board-root not found');
        return;
      }
      const scheduleDropCol = board.querySelector('.board-col-col2');
      if (!scheduleDropCol) {
        log('schedule drop column not found');
        return;
      }
      const dropTargets = [
        scheduleDropCol.querySelector('.board-col-head'),
        scheduleDropCol.querySelector('.post-stack'),
        scheduleDropCol
      ].filter(Boolean);
      log('dropTargets count =', dropTargets.length);
      let draggingItemId = '';

      const scheduleByItem = (itemId) => {
        if (!itemId) {
          log('scheduleByItem blocked: empty itemId');
          return;
        }
        log('scheduleByItem start', { itemId });
        const pwin = window.parent;
        const url = new URL(pwin.location.href);
        url.searchParams.set('schedule_pick', itemId);
        pwin.history.replaceState({}, "", url.toString());
        log('query param set via history.replaceState', url.toString());
        const commitBtn = parentDoc.querySelector('.st-key-drag_drop_commit button');
        if (commitBtn) {
          commitBtn.click();
          log('clicked hidden drag_drop_commit button to trigger rerun');
        } else {
          log('hidden drag_drop_commit button not found; waiting manual rerun');
        }
      };

      const clearHighlight = () => dropTargets.forEach((el) => el.classList.remove('dropzone-active'));
      const setHighlight = () => dropTargets.forEach((el) => el.classList.add('dropzone-active'));

      const bindCard = (card) => {
        if (!card || card.dataset.scheduleBound === '1') return;
        card.dataset.scheduleBound = '1';
        const itemId = card.dataset.itemId || '';
        if (!itemId) {
          log('skip bind: missing data-item-id', card);
          return;
        }
        log('bind card', itemId);

        card.addEventListener('dragstart', (ev) => {
          draggingItemId = itemId;
          if (ev.dataTransfer) {
            ev.dataTransfer.effectAllowed = 'copyMove';
            ev.dataTransfer.setData('text/plain', itemId);
            ev.dataTransfer.setData('application/x-item-id', itemId);
          }
          card.dataset.dragging = '1';
          log('dragstart', {
            itemId,
            hasDataTransfer: !!ev.dataTransfer,
          });
          setHighlight();
        });
        card.addEventListener('dragend', () => {
          card.dataset.dragging = '0';
          log('dragend', { itemId });
          draggingItemId = '';
          clearHighlight();
        });

        let touchTimer = null;
        let touchDragging = false;
        let touchOverDrop = false;

        card.addEventListener('touchstart', () => {
          touchDragging = false;
          touchOverDrop = false;
          log('touchstart', { itemId });
          touchTimer = window.setTimeout(() => {
            touchDragging = true;
            log('touch long press armed', { itemId });
            setHighlight();
          }, 360);
        }, { passive: true });

        card.addEventListener('touchmove', (ev) => {
          if (!touchDragging) return;
          const touch = ev.touches && ev.touches[0];
          if (!touch) return;
          const hit = parentDoc.elementFromPoint(touch.clientX, touch.clientY);
          touchOverDrop = !!(hit && hit.closest && hit.closest('.board-col-col2'));
        }, { passive: true });

        card.addEventListener('touchend', () => {
          if (touchTimer) {
            clearTimeout(touchTimer);
            touchTimer = null;
          }
          log('touchend', { itemId, touchDragging, touchOverDrop });
          if (touchDragging && touchOverDrop) {
            scheduleByItem(itemId);
          }
          touchDragging = false;
          touchOverDrop = false;
          clearHighlight();
        });
      };

      dropTargets.forEach((target) => {
        target.addEventListener('dragover', (ev) => {
          ev.preventDefault();
          if (ev.dataTransfer) ev.dataTransfer.dropEffect = 'copy';
          setHighlight();
        });
        target.addEventListener('dragleave', clearHighlight);
        target.addEventListener('drop', (ev) => {
          ev.preventDefault();
          ev.stopPropagation();
          let itemId = '';
          if (ev.dataTransfer) {
            itemId = ev.dataTransfer.getData('application/x-item-id') || ev.dataTransfer.getData('text/plain') || '';
          }
          if (!itemId) itemId = draggingItemId;
          log('drop', {
            itemIdFromTransfer: ev.dataTransfer ? (ev.dataTransfer.getData('application/x-item-id') || ev.dataTransfer.getData('text/plain') || '') : '',
            fallbackDraggingItemId: draggingItemId,
            finalItemId: itemId,
          });
          clearHighlight();
          scheduleByItem(itemId);
        });
      });

      const bindAll = () => {
        const cards = board.querySelectorAll('.post-card-draggable[data-item-id]');
        log('bindAll cards=', cards.length);
        cards.forEach(bindCard);
      };
      bindAll();
      const mo = new MutationObserver(() => bindAll());
      mo.observe(board, { childList: true, subtree: true });
      log('mutation observer attached');
    })();
    </script>
    """
