async page => {
  // Flow B — bằng chứng hình học THẬT: hội thoại nằm trong bubble của node,
  // các nút thao tác bấm được, không tràn ngang. Desktop 1440x900 + mobile 390x844.
  const measure = async () => page.evaluate(() => {
    const collect = (root, acc = []) => {
      root.querySelectorAll('[data-testid]').forEach(el => acc.push(el));
      root.querySelectorAll('*').forEach(el => { if (el.shadowRoot) collect(el.shadowRoot, acc); });
      return acc;
    };
    const all = collect(document);
    const pick = (id) => all.find(el => el.getAttribute('data-testid') === id);
    const rect = (el) => {
      if (!el) return null;
      const b = el.getBoundingClientRect();
      const root = el.getRootNode();
      const cx = Math.min(window.innerWidth - 2, Math.max(1, b.x + b.width / 2));
      const cy = Math.min(window.innerHeight - 2, Math.max(1, b.y + b.height / 2));
      const hit = (root.elementFromPoint ? root.elementFromPoint(cx, cy) : null)
        || document.elementFromPoint(cx, cy);
      return {
        x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height),
        inViewportX: b.x >= 0 && b.right <= window.innerWidth + 1,
        inViewportY: b.y >= 0 && b.bottom <= window.innerHeight + 1,
        hitOk: !!hit && (hit === el || el.contains(hit)),
      };
    };
    const bubbleEl = pick('journey-bubble');
    const main = document.querySelector('[data-testid="stMain"]');
    const bb = bubbleEl ? bubbleEl.getBoundingClientRect() : null;
    const composer = pick('journey-discussion-body');
    let inBubble = false;
    for (let n = composer; n; n = n.parentElement) {
      if (n === bubbleEl) { inBubble = true; break; }
    }
    return {
      viewport: { w: window.innerWidth, h: window.innerHeight },
      mainScrollWidth: main ? main.scrollWidth : null,
      mainClientWidth: main ? main.clientWidth : null,
      horizontalOverflow: main ? main.scrollWidth > main.clientWidth + 1 : null,
      bubble: bb ? { x: Math.round(bb.x), y: Math.round(bb.y), w: Math.round(bb.width), h: Math.round(bb.height) } : null,
      discussionInsideBubble: inBubble,
      threadHeader: (pick('journey-discussion') || {}).textContent
        ? pick('journey-discussion').textContent.trim().slice(0, 40) : null,
      controls: {
        close: rect(pick('journey-bubble-close')),
        composer: rect(pick('journey-discussion-body')),
        attach: rect(pick('journey-discussion-attach')),
        send: rect(pick('journey-discussion-send')),
      },
      noteCount: all.filter(el => /^journey-discussion-note-/.test(el.getAttribute('data-testid') || '')).length,
    };
  });

  const out = {};
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(1500);
  await page.getByTestId('journey-discussion-send').scrollIntoViewIfNeeded();
  await page.waitForTimeout(800);
  out.desktop = await measure();
  await page.screenshot({ path: '/home/user/logistics-work-desk-arena/evidence/logi-journey-send-20261030/02-customer-discussion-desktop-1440x900.png' });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(2000);
  await page.getByTestId('journey-discussion-send').scrollIntoViewIfNeeded();
  await page.waitForTimeout(800);
  out.mobile = await measure();
  await page.screenshot({ path: '/home/user/logistics-work-desk-arena/evidence/logi-journey-send-20261030/03-customer-discussion-mobile-390x844.png' });

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(800);
  return out;
}
