// The ticket window: click the station's ticket window (or the toy donation shop, or the Marines) and a painted
// paper card asks where you live, then prints a train ticket to your local toy drive's drop-off spots. From the map,
// "Ride the train there" hands the ticket to the map page, which carries you along the painted rails.
(function () {
  const TT = window.TT_CAMPAIGNS, esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const host = (() => { try { return window.parent !== window && window.parent.__ttRide ? window.parent : null; } catch (e) { return null; } })();
  const card = document.createElement('div'); card.className = 'tw'; card.hidden = true;
  card.setAttribute('role', 'dialog'); card.setAttribute('aria-modal', 'true'); card.setAttribute('aria-labelledby', 'tw-title');
  document.body.appendChild(card);
  let last = null, current = null;
  const tellHost = v => { try { window.parent !== window && window.parent.__ttCardOpen && window.parent.__ttCardOpen(v); } catch (e) {} };
  const NOTE = '<p class="tw-note">Demo: every toy drive, place and date here is invented.</p>';
  function open(html, focusSel) {
    card.innerHTML = '<button class="tw-x" aria-label="Close">&times;</button>' + html + NOTE; card.hidden = false; window.__busy = true; tellHost(true);
    card.querySelector('.tw-x').onclick = close;
    (card.querySelector(focusSel || 'button, input') || card).focus({ preventScroll: true });
  }
  function close() { card.hidden = true; window.__busy = false; tellHost(false); if (last && last.focus) last.focus({ preventScroll: true }); }
  addEventListener('keydown', e => { if (e.key === 'Escape' && !card.hidden) close(); });

  function ask(kind) {
    TT.log('ask');
    open(`<span class="tw-eyebrow">${kind === 'donate' ? 'Toy donation' : 'Toy Town Station · ticket window'}</span>
      <h2 id="tw-title">Drop off a toy near you</h2>
      <p>Every new, unwrapped toy you drop off goes to a child in your own community. Tell us where you live and we'll print your ticket to the nearest drop-off spots.</p>
      <form class="tw-form"><label for="tw-zip">Your ZIP code</label>
        <div class="tw-row"><input id="tw-zip" inputmode="numeric" autocomplete="postal-code" maxlength="5" placeholder="e.g. 55401" required>
        <button type="submit" class="tw-go">Print my ticket</button></div>
        <p class="tw-err" role="alert" hidden>Please enter a five-digit ZIP code.</p></form>`, '#tw-zip');
    const f = card.querySelector('form'), inp = card.querySelector('#tw-zip'), err = card.querySelector('.tw-err');
    inp.addEventListener('input', () => { inp.value = inp.value.replace(/\D/g, '').slice(0, 5); err.hidden = true; });
    f.onsubmit = e => { e.preventDefault(); const c = TT.find(inp.value); if (!c) { err.hidden = false; inp.focus(); return; } TT.log('ticket'); ticket(c); };
  }
  function spotsHtml(c) {
    return '<ol class="tw-spots">' + c.spots.map(([n, a, h]) => `<li><b>${esc(n)}</b><span>${esc(a)}, ${esc(c.town)}</span><span>${esc(h)}</span></li>`).join('') + '</ol>';
  }
  function ticket(c) {
    current = c;
    open(`<span class="tw-eyebrow">Your ticket</span>
      <div class="tw-ticket" aria-label="Train ticket from Toy Town to ${esc(c.town)}">
        <div class="tw-stub"><span>Admit</span><b>one toy</b></div>
        <div class="tw-body"><div class="tw-route"><span>Toy Town</span><i aria-hidden="true">&#10230;</i><span>${esc(c.town)}</span></div>
          <h2 id="tw-title">${esc(c.town)} Toy Drive</h2>
          <p>Drop off by <b>${esc(c.deadline)}</b> &middot; nearest spot: <b>${esc(c.spots[0][0])}</b></p></div>
      </div>
      <p class="tw-what">Bring a <b>new, unwrapped toy</b>. Any age from baby to teen; books and games count too.</p>
      <div class="tw-actions">
        <button class="tw-go tw-ride">${host ? 'Ride the train to ' + esc(c.town) : 'See the drop-off spots'}</button>
        ${host ? '<button class="tw-plain tw-list">Just show the drop-off spots</button>' : ''}
        <button class="tw-plain tw-again">Another ZIP code</button></div>
      <div class="tw-more" hidden>${spotsHtml(c)}</div>`, '.tw-ride');
    const more = card.querySelector('.tw-more');
    const show = () => { more.hidden = false; TT.log('spots'); more.scrollIntoView({ block: 'nearest' }); };
    card.querySelector('.tw-ride').onclick = () => { if (host) { TT.log('ride'); close(); host.__ttRide(c); } else show(); };
    const l = card.querySelector('.tw-list'); if (l) l.onclick = show;
    card.querySelector('.tw-again').onclick = () => ask('ticket');
  }
  function marines() {
    TT.log('marines');
    open(`<span class="tw-eyebrow">The Marines</span><h2 id="tw-title">How a toy reaches a child</h2>
      <ol class="tw-steps"><li>You drop off a new, unwrapped toy at a spot near you.</li><li>Marines and volunteers collect the toys from every spot in town.</li>
      <li>They sort them by age and hand them out in the same community, in time for the holidays.</li></ol>
      <div class="tw-actions"><button class="tw-go tw-find">Find a drop-off near me</button></div>`, '.tw-find');
    card.querySelector('.tw-find').onclick = () => ask('ticket');
  }
  addEventListener('tt-hotspot', e => { last = document.activeElement; TT.log('hotspot_' + e.detail); (e.detail === 'marines' ? marines : ask)(e.detail); });
  window.__ticket = { ask, ticket: z => ticket(TT.find(z)), marines, close };      // test hooks
})();
