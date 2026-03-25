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
        const parentDoc = window.parent && window.parent.document ? window.parent.document : document;
        const board = document.querySelector('.board-root') || parentDoc.querySelector('.board-root');
        const commitBtn = parentDoc.querySelector('.st-key-schedule_pick_commit button');
        const lockCommitBtn = parentDoc.querySelector('.st-key-schedule_lock_commit button');
        const unscheduleCommitBtn = parentDoc.querySelector('.st-key-unschedule_commit button');
        const updateCommitBtn = parentDoc.querySelector('.st-key-update_pick_commit button');
        const deleteCommitBtn = parentDoc.querySelector('.st-key-delete_pick_commit button');
        if (!board || !commitBtn) {
          if (attempts < MAX_ATTEMPTS) {
            window.setTimeout(tryBind, 120);
          }
          return;
        }

        const bindAll = () => {
          const triggerCommit = (btn, commitAction) => {
            btn.classList.add('is-loading');
            btn.setAttribute('disabled', 'disabled');
            window.setTimeout(() => commitAction(), 90);
          };

          const scheduleButtons = board.querySelectorAll('.post-card-schedule-btn[data-item-id]');
          scheduleButtons.forEach((btn) => {
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
              triggerCommit(btn, () => commitBtn.click());
            });
          });

          const lockButtons = board.querySelectorAll('.post-card-lock-btn[data-schedule-key]');
          lockButtons.forEach((btn) => {
            if (btn.dataset.bound === '1') return;
            btn.dataset.bound = '1';
            btn.addEventListener('click', (ev) => {
              ev.preventDefault();
              ev.stopPropagation();
              if (typeof ev.stopImmediatePropagation === 'function') {
                ev.stopImmediatePropagation();
              }
              const scheduleKey = String(btn.dataset.scheduleKey || '').trim();
              if (!scheduleKey) return;
              const pwin = window.parent;
              const url = new URL(pwin.location.href);
              url.searchParams.set('lock_toggle', scheduleKey);
              pwin.history.replaceState({}, '', url.toString());
              btn.blur();
              triggerCommit(btn, () => {
                if (lockCommitBtn) lockCommitBtn.click();
              });
            });
          });

          const unscheduleButtons = board.querySelectorAll('.post-card-return-btn[data-unschedule-key]');
          unscheduleButtons.forEach((btn) => {
            if (btn.dataset.bound === '1') return;
            btn.dataset.bound = '1';
            btn.addEventListener('click', (ev) => {
              ev.preventDefault();
              ev.stopPropagation();
              if (typeof ev.stopImmediatePropagation === 'function') {
                ev.stopImmediatePropagation();
              }
              const unscheduleKey = String(btn.dataset.unscheduleKey || '').trim();
              if (!unscheduleKey) return;
              const pwin = window.parent;
              const url = new URL(pwin.location.href);
              url.searchParams.set('unschedule_pick', unscheduleKey);
              pwin.history.replaceState({}, '', url.toString());
              btn.blur();
              triggerCommit(btn, () => {
                if (unscheduleCommitBtn) unscheduleCommitBtn.click();
              });
            });
          });

          const editButtons = board.querySelectorAll('.post-card-edit-btn[data-edit-key]');
          editButtons.forEach((btn) => {
            if (btn.dataset.bound === '1') return;
            btn.dataset.bound = '1';
            btn.addEventListener('click', (ev) => {
              ev.preventDefault();
              ev.stopPropagation();
              if (typeof ev.stopImmediatePropagation === 'function') {
                ev.stopImmediatePropagation();
              }
              const editKey = String(btn.dataset.editKey || '').trim();
              if (!editKey) return;
              const pwin = window.parent;
              const url = new URL(pwin.location.href);
              url.searchParams.set('update_pick', editKey);
              pwin.history.replaceState({}, '', url.toString());
              btn.blur();
              triggerCommit(btn, () => {
                if (updateCommitBtn) updateCommitBtn.click();
              });
            });
          });

          const deleteButtons = board.querySelectorAll('.post-card-delete-btn[data-delete-key]');
          deleteButtons.forEach((btn) => {
            if (btn.dataset.bound === '1') return;
            btn.dataset.bound = '1';
            btn.addEventListener('click', (ev) => {
              ev.preventDefault();
              ev.stopPropagation();
              if (typeof ev.stopImmediatePropagation === 'function') {
                ev.stopImmediatePropagation();
              }
              const deleteKey = String(btn.dataset.deleteKey || '').trim();
              if (!deleteKey) return;
              const pwin = window.parent;
              const url = new URL(pwin.location.href);
              url.searchParams.set('delete_pick', `published:${deleteKey}`);
              pwin.history.replaceState({}, '', url.toString());
              btn.blur();
              triggerCommit(btn, () => {
                if (deleteCommitBtn) deleteCommitBtn.click();
              });
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
