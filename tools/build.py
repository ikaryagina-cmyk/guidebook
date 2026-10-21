#!/usr/bin/env python3
"""Собирает index.html для GitHub Pages из исходника артефакта (gaidbook.html).

python3 tools/build.py <gaidbook.html> index.html
"""
import sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        raise SystemExit('ожидалось %d вхождений, найдено %d: %r' % (count, n, old[:90]))
    s = s.replace(old, new)


# ---------- документ ----------
cut = s.index('<div class="readbar"')
head, body = s[:cut], s[cut:]
LOGIN_CSS = '''<style>
[hidden]{display:none!important}
html,body{margin:0}
.login-box{display:grid;gap:14px}
.login-box .btn{justify-self:start}
.login-code{font:800 28px/1 var(--font);letter-spacing:.18em;max-width:260px}
.login-links{display:flex;flex-wrap:wrap;gap:8px 18px}
.linkbtn{background:none;border:0;padding:0;font:inherit;color:var(--link);text-decoration:underline;text-underline-offset:3px;cursor:pointer}
.linkbtn:disabled{color:var(--fg3);text-decoration:none;cursor:default}
.foot .linkbtn{font-size:inherit}
.invite-box{background:var(--soft);border-radius:18px;padding:14px 16px;margin-top:16px;display:grid;gap:8px}
.invite-box p{margin:0}
.invite-text{font-weight:600;user-select:all;overflow-wrap:anywhere}
</style>
'''
s = ('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
     '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
     '<meta name="robots" content="noindex, nofollow">\n'
     '<meta name="referrer" content="strict-origin-when-cross-origin">\n'
     + head + LOGIN_CSS + '</head>\n<body>\n' + body.rstrip() + '\n</body>\n</html>\n')

# ---------- библиотеки и настройки ----------
rep('<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>',
    '<script src="vendor/marked.umd.js"></script>')
rep('<script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.1.6/purify.min.js"></script>',
    '<script src="vendor/purify.min.js"></script>\n<script src="config.js"></script>\n<script src="sb.js"></script>')

# ---------- состояние ----------
rep("  let db = null, user = null, downloads = null, assets = null, imgSeq = 0, uploading = 0;",
    "  let db = null, user = null, downloads = null, assets = null, imgSeq = 0, uploading = 0, sb = null;")

# ---------- картинки: ссылка на хранилище Supabase ----------
rep("cur.value = cur.value.replace(token, '![](/_blob/' + r.id + ')');",
    "cur.value = cur.value.replace(token, '![](' + (r.url || ('/_blob/' + r.id)) + ')');")

# ---------- выгрузка: вместе с городами и почтами ----------
rep("    return JSON.stringify({ format: 'gaidbook', version: 2, exportedAt: new Date().toISOString(), sections: cleanSections(state.sections), guides }, null, 2);",
    "    const out = { format: 'gaidbook', version: 2, exportedAt: new Date().toISOString(), sections: cleanSections(state.sections), guides };\n"
    "    if (state.canWrite && state.access.length) out.access = state.access.map(c => Object.assign({ id: c.id }, cityBody(c)));\n"
    "    return JSON.stringify(out, null, 2);")

# ---------- загрузка: города и почты, пачками ----------
rep("    const sections = (j && Array.isArray(j.sections)) ? cleanSections(j.sections) : [];\n    return { guides, sections };",
    "    const sections = (j && Array.isArray(j.sections)) ? cleanSections(j.sections) : [];\n"
    "    const access = (j && Array.isArray(j.access)) ? j.access.filter(c => c && c.name).map(c => ({ id: ID_RE.test(String(c.id || '')) ? String(c.id) : newCityId(), name: String(c.name), people: peopleOf(c), active: c.active !== false, createdAt: c.createdAt || null })) : [];\n"
    "    return { guides, sections, access };")
rep("    if (!guides.length) return { error: 'В файле не нашлось ни одного гайда.' };",
    "    if (!guides.length && !(j && Array.isArray(j.access) && j.access.length)) return { error: 'В файле не нашлось ни одного гайда.' };")
rep("    return '<div class=\"btn-row\"><span>В файле ' + nGuides(d.guides.length) + (d.sections.length ? ' и ' + d.sections.length + ' ' + plural(d.sections.length, 'раздел', 'раздела', 'разделов') : '') + '.</span>' +",
    "    const acc = d.access && d.access.length ? ', ' + d.access.length + ' ' + plural(d.access.length, 'город', 'города', 'городов') + ' с доступами' : '';\n"
    "    return '<div class=\"btn-row\"><span>В файле ' + nGuides(d.guides.length) + (d.sections.length ? ', ' + d.sections.length + ' ' + plural(d.sections.length, 'раздел', 'раздела', 'разделов') : '') + acc + '.</span>' +")
rep("        const body = { title: g.title, sectionId: resolve(g), summary: g.summary, todo: g.todo, source: g.source, tags: g.tags, status: g.status, body: g.body, videos: g.videos, createdAt: g.createdAt, updatedAt: g.updatedAt, example: g.example };",
    "        const body = { title: g.title, sectionId: resolve(g), summary: g.summary, todo: g.todo, source: g.source, tags: g.tags, status: g.status, body: g.body, videos: g.videos, createdAt: g.createdAt, updatedAt: g.updatedAt, example: g.example };\n"
    "        if (g.updatedBy) body.updatedBy = g.updatedBy;")
rep("      createdAt: g.createdAt || new Date().toISOString(), updatedAt: g.updatedAt || new Date().toISOString(), example: !!g.example\n    }));",
    "      createdAt: g.createdAt || new Date().toISOString(), updatedAt: g.updatedAt || new Date().toISOString(), example: !!g.example,\n"
    "      updatedBy: typeof g.updatedBy === 'string' ? g.updatedBy : ''\n    }));")
rep("      for (const [id, body] of prepared) await store.saveGuide(id, body);\n      toast('Загружено: ' + nGuides(d.guides.length));",
    "      if (state.mode === 'shared' && db.collection('guides').setMany) {\n"
    "        if (btn) btn.textContent = 'Загружаю гайды…';\n"
    "        await db.collection('guides').setMany(prepared);\n"
    "        prepared.forEach(([id, body]) => upsertLocal(Object.assign({ id }, body)));\n"
    "      } else for (const [id, body] of prepared) await store.saveGuide(id, body);\n"
    "      const cities = d.access || [];\n"
    "      if (cities.length) {\n"
    "        if (btn) btn.textContent = 'Загружаю города…';\n"
    "        for (const c of cities) await store.saveCity(c.id, cityBody(c, c.people));\n"
    "      }\n"
    "      toast('Загружено: ' + nGuides(d.guides.length) + (cities.length ? ' и ' + cities.length + ' ' + plural(cities.length, 'город', 'города', 'городов') : ''));")

# ---------- тексты раздела «Данные» ----------
rep("      ? 'Гайды хранятся в общей базе этой страницы: правки сразу видят все, кому открыт доступ.'",
    "      ? 'Гайды хранятся в общей базе: правки видят все, кому открыт доступ.'")
rep("<p>Все разделы и гайды одним файлом guides.json, сейчас в нём ' + nGuides(n) + '. Файл понадобится при публикации сайта на GitHub и годится как резервная копия.</p>",
    "<p>Все разделы, гайды, города и почты одним файлом guides.json, сейчас в нём ' + nGuides(n) + '. Годится как резервная копия.</p>")
rep("<h2 class=\"h2\">Загрузить из файла</h2><p>Добавит гайды и разделы из guides.json. Если гайд с таким же идентификатором уже есть, он заменится.</p>",
    "<h2 class=\"h2\">Загрузить из файла</h2><p>Добавит гайды, разделы, города и почты из guides.json. Если гайд или город с таким же идентификатором уже есть, он заменится.</p>")

EDITORS_JS = r'''
  /* ---------- редакторы ---------- */
  const ED = { list: null, loading: false, err: '', invite: null, confirm: null };
  const siteUrl = () => location.origin + location.pathname;
  const inviteText = (email, code) => 'Вас добавили в редакторы Гайдбука «Квиз, плиз!». Откройте ' + siteUrl() + ', войдите с почтой ' + email + ', введите код приглашения ' + code + ' и придумайте пароль.';
  function edErr(e) {
    const m = String((e && e.body && (e.body.message || e.body.msg)) || (e && e.message) || '');
    if (/bad_email/.test(m)) return 'Не похоже на почту.';
    if (/\bself\b/.test(m)) return 'Себя убрать или сбросить нельзя.';
    if (/not_editor/.test(m) || (e && e.code === 'not_granted')) return 'Это может только редактор. Обновите страницу и войдите снова.';
    if (e && e.code === 'unavailable') return 'Нет связи с базой. Проверьте интернет и попробуйте ещё раз.';
    return 'Не получилось. Попробуйте ещё раз.';
  }
  function viewEditors() {
    if (!editorMode()) return notFound('Раздел для отдела', 'Редакторами управляют только редакторы.');
    if (!sb) return notFound('Редакторы', 'Управлять редакторами можно на опубликованном сайте.');
    return '<div class="page narrow">' + topbar('dept', 'Отдел франшиз') +
      '<div class="g-head"><h1 class="display sm">Редакторы</h1><p class="lede">Редакторы правят гайды, разделы и доступы городов. Добавьте почту коллеги, и сайт выдаст код приглашения. Коллега откроет сайт, войдёт с этой почтой, введёт код и сам придумает пароль.</p></div>' +
      '<section class="panel"><h2 class="h2">Добавить редактора</h2><form class="login-box" id="edAddForm" novalidate>' +
      '<div class="field"><label for="ed-email">Почта</label><input class="inp" id="ed-email" type="email" inputmode="email" autocomplete="off" placeholder="name@quizplease.ru"></div>' +
      '<p class="err" id="ed-err" hidden></p><button class="btn small" type="submit" id="edAddBtn">Добавить и получить код</button></form>' +
      '<div id="edInvite">' + inviteHTML() + '</div></section>' +
      '<section class="panel"><h2 class="h2">Кто редактирует</h2><div id="edList">' + edListHTML() + '</div></section>' +
      '<section class="panel"><h2 class="h2">Сменить свой пароль</h2><form class="login-box" id="edPwForm" novalidate>' +
      '<input type="email" name="username" autocomplete="username" value="' + esc(loginEmail) + '" hidden>' +
      '<div class="field"><label for="ed-pw1">Новый пароль</label><input class="inp" id="ed-pw1" type="password" autocomplete="new-password" placeholder="Не короче 6 символов"></div>' +
      '<div class="field"><label for="ed-pw2">Пароль ещё раз</label><input class="inp" id="ed-pw2" type="password" autocomplete="new-password"></div>' +
      '<p class="err" id="ed-pw-err" hidden></p><button class="btn small ghost" type="submit">Сохранить пароль</button></form></section></div>';
  }
  function inviteHTML() {
    const iv = ED.invite; if (!iv) return '';
    return '<div class="invite-box"><p><b>' + esc(iv.title) + '</b></p>' + (iv.note ? '<p class="err">' + esc(iv.note) + '</p>' : '') +
      '<p class="invite-text" id="edInviteText">' + esc(inviteText(iv.email, iv.code)) + '</p>' +
      '<div class="btn-row"><button class="btn small" type="button" data-ed="copyinvite">Скопировать приглашение</button></div></div>';
  }
  function edListHTML() {
    if (ED.err) return '<p class="err">' + esc(ED.err) + '</p>';
    if (!ED.list) return '<p class="muted">Загружаю…</p>';
    if (!ED.list.length) return '<p class="muted">Редакторов пока нет.</p>';
    const meMail = String(loginEmail || '').toLowerCase();
    return ED.list.map(e => {
      const me = e.email === meMail, active = !!e.user_id;
      const pill = active ? '<span class="pill ok">Входит по паролю</span>' : '<span class="pill warn">Ждёт первого входа</span>';
      const conf = ED.confirm && ED.confirm.email === e.email ? ED.confirm.kind : '';
      let actions;
      if (me) actions = '<span class="muted">Это вы</span>';
      else if (conf === 'del') actions = '<span class="confirm">Убрать ' + esc(e.email) + ' из редакторов? <button class="btn danger small" type="button" data-ed="delyes">Да, убрать</button><button class="btn ghost small" type="button" data-ed="no">Нет</button></span>';
      else if (conf === 'reset') actions = '<span class="confirm">' + (active ? 'Старый пароль перестанет работать, коллега создаст новый по коду. ' : '') + 'Выдать новый код? <button class="btn small" type="button" data-ed="resetyes">Да, выдать</button><button class="btn ghost small" type="button" data-ed="no">Нет</button></span>';
      else actions = (!active && e.invite_code ? '<button class="btn small" type="button" data-ed="showinvite">Приглашение</button>' : '') +
        '<button class="btn ghost small" type="button" data-ed="reset">' + (active ? 'Сбросить пароль' : 'Новый код') + '</button>' +
        '<button class="btn danger small" type="button" data-ed="del">Убрать</button>';
      return '<div class="acc-card" data-edmail="' + esc(e.email) + '"><div class="acc-head"><span class="acc-name">' + esc(e.email) + '</span>' + pill + '</div>' +
        (!active && e.invite_code ? '<span class="muted acc-meta">Код приглашения: <b>' + esc(e.invite_code) + '</b></span>' : '') +
        '<div class="btn-row">' + actions + '</div></div>';
    }).join('');
  }
  function renderEdList() { const b = $('#edList'); if (b) b.innerHTML = edListHTML(); }
  function renderInvite() { const b = $('#edInvite'); if (b) b.innerHTML = inviteHTML(); }
  async function loadEditors() {
    if (!sb || ED.loading) return;
    ED.loading = true;
    try { ED.list = await sb.rows('editors', 'select=email,user_id,invite_code,added_at&order=added_at.asc'); ED.err = ''; }
    catch (e) { ED.err = edErr(e); ED.list = null; }
    ED.loading = false; renderEdList();
  }
  document.addEventListener('submit', async ev => {
    const f = ev.target;
    if (f.id === 'edAddForm') {
      ev.preventDefault();
      const inp = $('#ed-email'), er = $('#ed-err'), btn = $('#edAddBtn');
      const showErr = m => { er.textContent = m; er.hidden = !m; };
      const v = String(inp.value || '').trim().toLowerCase();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) { showErr('Похоже, в почте опечатка.'); inp.focus(); return; }
      showErr(''); btn.disabled = true;
      try {
        const r = await sb.rpc('add_editor', { addr: v });
        if (r && r.status === 'active') showErr('Эта почта уже в редакторах и входит по паролю.');
        else { ED.invite = { email: v, code: r.code, title: 'Готово. Отправьте коллеге это приглашение:' }; inp.value = ''; renderInvite(); loadEditors(); }
      } catch (e) { showErr(edErr(e)); }
      btn.disabled = false;
    } else if (f.id === 'edPwForm') {
      ev.preventDefault();
      const p1 = String($('#ed-pw1').value || ''), p2 = String($('#ed-pw2').value || ''), er = $('#ed-pw-err');
      const showErr = m => { er.textContent = m; er.hidden = !m; };
      if (p1.length < 6) return showErr('Пароль должен быть не короче 6 символов.');
      if (p1 !== p2) return showErr('Пароли не совпадают.');
      showErr('');
      try { await sb.auth.updatePassword(p1); $('#ed-pw1').value = ''; $('#ed-pw2').value = ''; toast('Пароль сохранён'); }
      catch (e) {
        const ec = e && e.body && (e.body.error_code || e.body.code);
        showErr(ec === 'same_password' ? 'Это ваш текущий пароль. Придумайте другой.' : ec === 'weak_password' ? 'Пароль слишком простой.' : edErr(e));
      }
    }
  });
  document.addEventListener('click', async ev => {
    const b = ev.target.closest && ev.target.closest('[data-ed]'); if (!b) return;
    const card = b.closest('[data-edmail]'), email = card ? card.dataset.edmail : '', act = b.dataset.ed;
    if (act === 'copyinvite') { const t = $('#edInviteText'); copyText(t ? t.textContent : '').then(ok => toast(ok ? 'Приглашение скопировано' : 'Не получилось скопировать')); return; }
    if (act === 'showinvite') {
      const e = (ED.list || []).find(x => x.email === email);
      if (e && e.invite_code) { ED.invite = { email, code: e.invite_code, title: 'Приглашение для ' + email + ':' }; renderInvite(); const box = $('#edInvite'); if (box) box.scrollIntoView({ block: 'center', behavior: reduceMotion ? 'auto' : 'smooth' }); }
      return;
    }
    if (act === 'del' || act === 'reset') { ED.confirm = { email, kind: act }; renderEdList(); return; }
    if (act === 'no') { ED.confirm = null; renderEdList(); return; }
    if (act === 'delyes') {
      b.disabled = true;
      try { await sb.rpc('remove_editor', { addr: email }); toast(email + ' больше не редактор'); if (ED.invite && ED.invite.email === email) { ED.invite = null; renderInvite(); } }
      catch (e) { toast(edErr(e)); }
      ED.confirm = null; loadEditors(); return;
    }
    if (act === 'resetyes') {
      b.disabled = true;
      try {
        const r = await sb.rpc('reset_editor', { addr: email });
        ED.invite = { email, code: r.code, title: 'Новый код готов. Отправьте коллеге это приглашение:', note: r.deleted ? '' : 'Старый аккаунт не удалился сам. Откройте в Supabase Authentication → Users, удалите ' + email + ' и только потом отправляйте приглашение.' };
        renderInvite();
      } catch (e) { toast(edErr(e)); }
      ED.confirm = null; loadEditors(); return;
    }
  });
'''

# ---------- маршрут «Редакторы» ----------
rep("      navA('data', '<span class=\"eyebrow\">Файлы</span>",
    "      navA('editors', '<span class=\"eyebrow\">Команда</span><span class=\"dcard-title\">Редакторы</span><p>Кто правит гайды: приглашения, коды и пароли.</p>', 'dcard press') +\n      navA('data', '<span class=\"eyebrow\">Файлы</span>")
rep("'structure', 'access'].indexOf(t)", "'structure', 'access', 'editors'].indexOf(t)")
rep("(v === 'dept' || v === 'attention' || v === 'data' || v === 'access') ? 'dept'", "(v === 'dept' || v === 'attention' || v === 'data' || v === 'access' || v === 'editors') ? 'dept'")
rep("      case 'data': html = viewData(); break;", "      case 'data': html = viewData(); break;\n      case 'editors': html = viewEditors(); break;")
rep("    if (r.view === 'data') { bindData(); fillAssetUsage(); }", "    if (r.view === 'data') { bindData(); fillAssetUsage(); }\n    if (r.view === 'editors') loadEditors();")
rep("(v === 'access' && $('#accList'))) {", "(v === 'access' && $('#accList')) || (v === 'editors' && $('#edList'))) {")

# ---------- текст на странице доступов ----------
rep("В опубликованной версии они будут входить по коду из письма, а город с закрытым доступом сразу перестанет видеть гайды. Сейчас это прототип: список хранится здесь, сам вход заработает после публикации.",
    "Сотрудник входит по своей почте из этого списка и видит только выбранные разделы. Если закрыть доступ городу, его сотрудники перестанут видеть гайды при следующем входе или обновлении страницы.")

# ---------- подвал: кто вошёл и выход ----------
rep("    if (state.mode === 'shared') { cls = 'shared'; text = state.canWrite ? 'Общая база: правки сразу видят все, кому открыта страница.' : 'Режим чтения.'; }",
    "    if (state.mode === 'shared') { cls = 'shared'; text = state.canWrite ? 'Общая база: правки видят все, кому открыт доступ.' : 'Режим чтения.'; }")
rep("    f.innerHTML = '<span class=\"dot ' + cls + '\"></span><span>' + esc(text) + '</span><span>Избранное и прогресс хранятся в этом браузере.</span>';",
    "    f.innerHTML = '<span class=\"dot ' + cls + '\"></span><span>' + esc(text) + '</span><span>Избранное и прогресс хранятся в этом браузере.</span>' +\n"
    "      (loginEmail ? '<span>' + esc(loginEmail) + ' · <button class=\"linkbtn\" type=\"button\" id=\"logoutBtn\">Выйти</button></span>' : '');")

# ---------- вход по почте ----------
LOGIN_JS = r'''
  /* ---------- вход: города по почте, редакторы по почте и паролю ---------- */
  const CITY_KEY = 'gb.city';
  const LOGIN = { step: 'email', email: '', err: '', busy: false };
  let loginEmail = '';
  function loginShell(title, inner) {
    $('#tabbar').hidden = true; $('#modebar').hidden = true; $('#readbar').hidden = true; $('#foot').innerHTML = '';
    $('#main').innerHTML = '<div class="page narrow"><div class="home-top">' + LOGO + '<div class="home-hi"><span class="eyebrow">Гайдбук «Квиз, плиз!»</span><b>' + esc(title) + '</b></div></div>' + inner + '</div>';
  }
  function renderLogin() {
    const L = LOGIN;
    const err = L.err ? '<p class="err">' + esc(L.err) + '</p>' : '';
    if (L.step === 'email') {
      loginShell('Вход', '<form class="panel login-box" id="loginForm" novalidate><h2 class="h2">Войдите по рабочей почте</h2>' +
        '<p>Подойдёт почта, которую ваш город передал в отдел франшиз.</p>' +
        '<div class="field"><label for="lg-email">Почта</label><input class="inp" id="lg-email" type="email" inputmode="email" autocomplete="email" placeholder="name@example.ru" value="' + esc(L.email) + '"></div>' +
        err + '<button class="btn" type="submit"' + (L.busy ? ' disabled' : '') + '>' + (L.busy ? 'Проверяю…' : 'Войти') + '</button></form>');
      const i = $('#lg-email'); if (i) i.focus();
    } else if (L.step === 'invite') {
      loginShell('Вход для отдела', '<form class="panel login-box" id="inviteForm" novalidate><h2 class="h2">Вас пригласили в редакторы</h2>' +
        '<p>Почта <b>' + esc(L.email) + '</b> добавлена в редакторы. Введите код приглашения, который вам прислали, и придумайте пароль. Дальше будете входить с этой почтой и паролем.</p>' +
        '<input type="email" name="username" autocomplete="username" value="' + esc(L.email) + '" hidden>' +
        '<div class="field"><label for="lg-code">Код приглашения</label><input class="inp" id="lg-code" type="text" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="16" placeholder="Например: 7F3A9C21"></div>' +
        '<div class="field"><label for="lg-new">Новый пароль</label><input class="inp" id="lg-new" type="password" autocomplete="new-password" placeholder="Не короче 6 символов"></div>' +
        '<div class="field"><label for="lg-new2">Пароль ещё раз</label><input class="inp" id="lg-new2" type="password" autocomplete="new-password"></div>' +
        err + '<button class="btn" type="submit"' + (L.busy ? ' disabled' : '') + '>' + (L.busy ? 'Сохраняю…' : 'Создать пароль и войти') + '</button>' +
        '<div class="login-links"><button class="linkbtn" type="button" id="lgOther">Другая почта</button></div></form>');
      const i = $('#lg-code'); if (i) i.focus();
    } else {
      loginShell('Вход для отдела', '<form class="panel login-box" id="pwForm" novalidate><h2 class="h2">Пароль редактора</h2>' +
        '<p>Почта <b>' + esc(L.email) + '</b> есть в списке редакторов, поэтому нужен пароль.</p>' +
        '<input type="email" name="username" autocomplete="username" value="' + esc(L.email) + '" hidden>' +
        '<div class="field"><label for="lg-pw">Пароль</label><input class="inp" id="lg-pw" type="password" autocomplete="current-password"></div>' +
        err + '<button class="btn" type="submit"' + (L.busy ? ' disabled' : '') + '>' + (L.busy ? 'Проверяю…' : 'Войти') + '</button>' +
        '<p class="muted">Забыли пароль? Попросите другого редактора выдать вам новый код в разделе Отдел → Редакторы.</p>' +
        '<div class="login-links"><button class="linkbtn" type="button" id="lgOther">Другая почта</button></div></form>');
      const i = $('#lg-pw'); if (i) i.focus();
    }
  }
  function loginError(e) {
    const c = e && e.code, b = e && e.body, ec = b && (b.error_code || b.code);
    if (ec === 'email_not_confirmed') return 'Аккаунт не подтверждён. В настройках входа Supabase выключите Confirm email или попросите редактора выдать вам новый код.';
    if (ec === 'weak_password') return 'Пароль слишком простой. Нужно не меньше 6 символов.';
    if (ec === 'signup_disabled') return 'В Supabase выключена регистрация. В настройках входа включите Allow new users to sign up.';
    if (ec === 'invalid_credentials' || (e && e.status === 400)) return 'Пароль не подошёл.';
    if (c === 'rate_limited') return 'Слишком много попыток. Подождите минуту и попробуйте снова.';
    if (c === 'unavailable') return 'Нет связи с базой. Проверьте интернет и попробуйте ещё раз.';
    return 'Не получилось войти. Попробуйте ещё раз через минуту.';
  }
  const NO_EMAIL = 'Этой почты нет в списке доступа. Напишите своему менеджеру в отделе франшиз.';
  const CLOSED = 'Доступ для вашего города сейчас закрыт. Если это ошибка, напишите своему менеджеру в отделе франшиз.';
  function storeCity(v) { try { if (v) localStorage.setItem(CITY_KEY, v); else localStorage.removeItem(CITY_KEY); } catch (e) { } }
  function storedCity() { try { return localStorage.getItem(CITY_KEY) || ''; } catch (e) { return ''; } }
  document.addEventListener('submit', async ev => {
    const f = ev.target;
    if (f.id === 'loginForm') {
      ev.preventDefault(); if (LOGIN.busy) return;
      const v = String($('#lg-email').value || '').trim().toLowerCase();
      LOGIN.email = v;
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) { LOGIN.err = 'Похоже, в почте опечатка.'; renderLogin(); return; }
      LOGIN.err = ''; LOGIN.busy = true; renderLogin();
      let kind;
      try { kind = await sb.auth.kind(v); } catch (e) { LOGIN.busy = false; LOGIN.err = loginError(e); renderLogin(); return; }
      LOGIN.busy = false;
      if (kind === 'editor') { LOGIN.step = 'password'; renderLogin(); return; }
      if (kind === 'editor_new') { LOGIN.step = 'invite'; renderLogin(); return; }
      if (kind === 'city') { storeCity(v); boot(); return; }
      LOGIN.err = kind === 'closed' ? CLOSED : NO_EMAIL; renderLogin();
    } else if (f.id === 'inviteForm') {
      ev.preventDefault(); if (LOGIN.busy) return;
      const code = String($('#lg-code').value || '').replace(/\s+/g, '').toUpperCase();
      const p1 = String($('#lg-new').value || ''), p2 = String($('#lg-new2').value || '');
      const stop = m => { LOGIN.busy = false; LOGIN.err = m; renderLogin(); };
      if (!code) return stop('Введите код приглашения.');
      if (p1.length < 6) return stop('Пароль должен быть не короче 6 символов.');
      if (p1 !== p2) return stop('Пароли не совпадают.');
      LOGIN.err = ''; LOGIN.busy = true; renderLogin();
      try {
        const ok = await sb.rpc('check_invite', { addr: LOGIN.email, code });
        if (!ok) return stop('Код не подошёл. Проверьте его или попросите редактора выдать новый.');
        let sess = null;
        try { sess = await sb.auth.signUp(LOGIN.email, p1); }
        catch (e) {
          const ec = e && e.body && (e.body.error_code || e.body.code);
          if (ec !== 'user_already_exists' && ec !== 'email_exists') throw e;
          try { sess = await sb.auth.signInPassword(LOGIN.email, p1); }
          catch (e2) { return stop('Для этой почты уже есть аккаунт со старым паролем. Попросите редактора нажать «Новый код» в разделе Отдел → Редакторы.'); }
        }
        if (!sess) return stop('Пароль создан, но Supabase ждёт подтверждения почты. В настройках входа Supabase выключите Confirm email, потом попросите новый код.');
        const claimed = await sb.rpc('claim_editor', { code });
        if (!claimed) { await sb.auth.signOut(); return stop('Не получилось подтвердить приглашение. Попросите редактора выдать новый код.'); }
        LOGIN.busy = false; storeCity(''); boot();
      } catch (e) { stop(loginError(e)); }
    } else if (f.id === 'pwForm') {
      ev.preventDefault(); if (LOGIN.busy) return;
      const pw = String($('#lg-pw').value || '');
      if (!pw) { LOGIN.err = 'Введите пароль.'; renderLogin(); return; }
      LOGIN.err = ''; LOGIN.busy = true; renderLogin();
      try { await sb.auth.signInPassword(LOGIN.email, pw); LOGIN.busy = false; storeCity(''); boot(); }
      catch (e) { LOGIN.busy = false; LOGIN.err = loginError(e); renderLogin(); }
    }
  });
  document.addEventListener('click', async ev => {
    const b = ev.target.closest && ev.target.closest('button'); if (!b) return;
    if (b.id === 'lgOther') { LOGIN.step = 'email'; LOGIN.err = ''; renderLogin(); }
    else if (b.id === 'logoutBtn') { b.disabled = true; storeCity(''); await sb.auth.signOut(); location.hash = ''; location.reload(); }
    else if (b.id === 'lgRetry') { boot(); }
  });
  function renderOffline() {
    loginShell('Нет связи', '<div class="empty"><h2 class="h2">Не получилось связаться с базой гайдов</h2>' +
      '<p>Проверьте интернет и попробуйте ещё раз. Если не помогает, напишите в отдел франшиз.</p>' +
      '<div class="btn-row"><button class="btn small" type="button" id="lgRetry">Попробовать снова</button><button class="btn ghost small" type="button" id="logoutBtn">Выйти</button></div></div>');
  }
  function launch(who) {
    loginEmail = who.email;
    const rt = window.GBSupabase.runtime(sb, who);
    db = rt.db; user = rt.user; downloads = rt.downloads; assets = rt.assets;
    state.route = parseToken(location.hash);
    render();
    startShared();
  }
  async function boot() {
    const cfg = window.GB_CONFIG || {};
    if (!sb) sb = window.GBSupabase.create(cfg);
    const sess = await sb.auth.restore();
    if (sess) {
      let who;
      try { who = await sb.rpc('whoami'); }
      catch (e) {
        if (e && e.code === 'not_granted') { await sb.auth.signOut(); LOGIN.step = 'email'; LOGIN.err = 'Вход устарел. Войдите снова.'; renderLogin(); return; }
        renderOffline(); return;
      }
      if (who && who.editor) { launch({ email: who.email, editor: true }); return; }
      await sb.auth.signOut();
      LOGIN.step = 'email'; LOGIN.email = (who && who.email) || ''; LOGIN.err = 'Эту почту убрали из списка редакторов.'; renderLogin(); return;
    }
    const city = storedCity();
    if (city) {
      let kind;
      try { kind = await sb.auth.kind(city); } catch (e) { renderOffline(); return; }
      if (kind === 'city') { launch({ email: city, editor: false }); return; }
      storeCity('');
      LOGIN.email = city;
      if (kind === 'editor') { LOGIN.step = 'password'; renderLogin(); return; }
      LOGIN.err = kind === 'closed' ? CLOSED : NO_EMAIL;
    }
    LOGIN.step = 'email'; renderLogin();
  }
'''
rep("  /* ---------- start ---------- */\n", LOGIN_JS + EDITORS_JS + "\n  /* ---------- start ---------- */\n")

rep('''  async function init() {
    state.route = parseToken(location.hash);
    render();
    const c = window.claude;''', '''  async function init() {
    state.route = parseToken(location.hash);
    if (window.GB_CONFIG && window.GB_CONFIG.url && window.GBSupabase) {
      $('#main').innerHTML = '<div class="page"><div class="empty"><p>Загружаю…</p></div></div>';
      return boot();
    }
    render();
    const c = window.claude;''')

# ---------- тема: светлая и тёмная ----------
rep('<meta name="referrer" content="strict-origin-when-cross-origin">\n',
    '<meta name="referrer" content="strict-origin-when-cross-origin">\n'
    "<script>try{var t=localStorage.getItem('gb-theme');if(t==='dark'||t==='light')document.documentElement.setAttribute('data-theme',t)}catch(e){}</script>\n")

TOC_CSS = """<style>
/* тема */
.home-theme{margin-left:auto}
:root[data-theme="dark"] .hero{background-position:center 12%}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .hero{background-position:center 12%}}
/* содержание гайда */
.g-col{display:grid;gap:28px;min-width:0}
.gtoc{display:grid;align-content:start;gap:4px}
.gtoc-head{display:flex;align-items:center;justify-content:space-between;gap:8px;min-height:48px;padding-left:10px}
.gtoc-list,.gtoc-sub{list-style:none;margin:0;padding:0;display:grid;gap:2px}
.gtoc-sub{margin:2px 0 8px 22px;padding-left:12px;border-left:1.5px solid var(--line)}
.gtoc-a{display:flex;gap:10px;align-items:flex-start;width:100%;text-align:left;border:0;background:transparent;color:var(--fg2);font:700 15px/1.3 var(--font);padding:8px 10px;border-radius:14px;cursor:pointer}
.gtoc-a:hover{color:var(--fg);background:var(--soft)}
.gtoc-a.on{color:var(--fg);background:var(--card)}
.gtoc-a.sub{font:600 14px/1.3 var(--font);padding:6px 10px}
.gtoc-a.sub.on{color:var(--link);background:transparent}
.gtoc-n{flex:none;min-width:22px;height:22px;margin-top:-1px;border-radius:999px;display:inline-grid;place-items:center;font:800 12px/1 var(--font);background:var(--soft);color:var(--fg2)}
.gtoc-a.on .gtoc-n{background:var(--pink);color:var(--on-pink)}
.gtoc-top{display:inline-flex;align-items:center;gap:8px;justify-self:start;margin-top:10px;padding:8px 10px;border:0;background:transparent;color:var(--fg2);font:700 14px/1 var(--font);cursor:pointer;border-radius:12px}
.gtoc-top:hover{color:var(--fg)}
.gtoc-top svg.i{width:18px;height:18px}
.toc-fab{position:fixed;right:16px;bottom:calc(env(safe-area-inset-bottom,0px) + 92px);z-index:41;display:inline-flex;align-items:center;gap:8px;height:46px;padding:0 18px 0 14px;border-radius:999px;border:0;background:var(--card);color:var(--fg);font:800 14px/1 var(--font);box-shadow:var(--shadow-md);cursor:pointer}
.toc-fab svg.i{width:20px;height:20px}
.gtoc-back{position:fixed;inset:0;z-index:65;background:rgba(0,0,0,.45)}
html.toc-lock{overflow:hidden}
@media (max-width:1179.98px){
  .gtoc{position:fixed;z-index:70;top:0;bottom:0;left:0;width:min(360px,88vw);overflow-y:auto;overscroll-behavior:contain;background:var(--bg);padding:calc(env(safe-area-inset-top,0px) + 12px) 12px calc(env(safe-area-inset-bottom,0px) + 28px) 12px;box-shadow:var(--shadow-md);border-radius:0 24px 24px 0;transform:translateX(-104%);visibility:hidden;transition:transform .28s var(--ease),visibility 0s linear .28s}
  .gtoc.open{transform:none;visibility:visible;transition:transform .28s var(--ease)}
}
@media (min-width:1180px){
  .page.narrow.has-toc{max-width:1144px;grid-template-columns:260px minmax(0,760px);column-gap:60px;justify-content:center;align-items:start}
  .gtoc{position:sticky;top:20px;max-height:calc(100vh - 40px);overflow-y:auto;overscroll-behavior:contain;scrollbar-width:thin;padding-bottom:16px}
  .gtoc-x,.toc-fab,.gtoc-back{display:none!important}
  .has-toc nav.toc{display:none}
  .gtoc-list > li:not(.open) > .gtoc-sub{display:none}
}
@media print{.gtoc,.toc-fab,.gtoc-back{display:none!important}}
</style>
"""
rep('</head>', TOC_CSS + '</head>')

rep("    eye: ic(",
    "    sun: ic('<circle cx=\"12\" cy=\"12\" r=\"4\"/><path d=\"M12 2.5v2M12 19.5v2M4.6 4.6 6 6M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4\"/>'),\n"
    "    moon: ic('<path d=\"M20.5 14.1A8.5 8.5 0 1 1 9.9 3.5a6.6 6.6 0 0 0 10.6 10.6z\"/>'),\n"
    "    list: ic('<path d=\"M9 6h11M9 12h11M9 18h11\"/><path d=\"M4.5 6h.01M4.5 12h.01M4.5 18h.01\" stroke-width=\"3\"/>'),\n"
    "    eye: ic(")

# заголовки второго и третьего уровня для содержания
rep("if (h.tagName === 'H2') toc.push({ id, text: h.textContent }); });",
    "toc.push({ id, text: h.textContent, lvl: h.tagName === 'H2' ? 2 : 3 }); });")

TOC_JS = r"""  /* ---------- тема ---------- */
  function themeNow() {
    const a = document.documentElement.getAttribute('data-theme');
    if (a === 'dark' || a === 'light') return a;
    return window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function themeLabel() { return themeNow() === 'dark' ? 'Включить светлую тему' : 'Включить тёмную тему'; }
  function themeBtn(cls) {
    return '<button class="circle press' + (cls ? ' ' + cls : '') + '" type="button" data-theme-toggle aria-label="' + themeLabel() + '" title="' + themeLabel() + '">' + (themeNow() === 'dark' ? ICON.sun : ICON.moon) + '</button>';
  }
  function syncThemeBtns() {
    $$('[data-theme-toggle]').forEach(b => { b.innerHTML = themeNow() === 'dark' ? ICON.sun : ICON.moon; b.setAttribute('aria-label', themeLabel()); b.title = themeLabel(); });
  }
  function toggleTheme() {
    const t = themeNow() === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', t);
    try { localStorage.setItem('gb-theme', t); } catch (e) { }
    syncThemeBtns();
  }
  try { matchMedia('(prefers-color-scheme: dark)').addEventListener('change', syncThemeBtns); } catch (e) { }

  /* ---------- содержание гайда ---------- */
  function tocTree(flat) {
    const out = []; const hasH2 = flat.some(t => t.lvl === 2);
    flat.forEach(t => {
      if (!hasH2 || t.lvl === 2) out.push({ id: t.id, text: t.text, subs: [] });
      else if (out.length) out[out.length - 1].subs.push({ id: t.id, text: t.text });
    });
    return out;
  }
  function tocAside(items) {
    return '<aside class="gtoc" id="gtoc" aria-label="Содержание гайда"><div class="gtoc-head"><span class="eyebrow">Содержание</span>' +
      '<button class="icon-btn gtoc-x" type="button" data-toc-close aria-label="Закрыть содержание">' + ICON.x + '</button></div><ol class="gtoc-list">' +
      items.map((t, i) => '<li><button type="button" class="gtoc-a" data-toc="' + t.id + '"><span class="gtoc-n">' + (i + 1) + '</span><span>' + esc(t.text) + '</span></button>' +
        (t.subs.length ? '<ol class="gtoc-sub">' + t.subs.map(x => '<li><button type="button" class="gtoc-a sub" data-toc="' + x.id + '">' + esc(x.text) + '</button></li>').join('') + '</ol>' : '') + '</li>').join('') +
      '</ol><button type="button" class="gtoc-top" data-toc="top">' + ICON.up + 'К началу гайда</button></aside>';
  }
  function tocIsOpen() { const a = $('#gtoc'); return !!(a && a.classList.contains('open')); }
  function openToc() {
    const a = $('#gtoc'); if (!a) return;
    a.classList.add('open'); document.documentElement.classList.add('toc-lock');
    const bk = $('.gtoc-back'); if (bk) bk.hidden = false;
    const f = $('[data-toc-open]'); if (f) f.setAttribute('aria-expanded', 'true');
    const cur = a.querySelector('.gtoc-a.on') || a.querySelector('.gtoc-a');
    setTimeout(() => { if (cur) { cur.focus({ preventScroll: true }); scrollTocTo(cur); } }, 40);
  }
  function closeToc(refocus) {
    document.documentElement.classList.remove('toc-lock');
    const bk = $('.gtoc-back'); if (bk) bk.hidden = true;
    const a = $('#gtoc'); if (!a || !a.classList.contains('open')) return;
    a.classList.remove('open');
    const f = $('[data-toc-open]'); if (f) { f.setAttribute('aria-expanded', 'false'); if (refocus) f.focus({ preventScroll: true }); }
  }
  function scrollTocTo(b) {
    const a = $('#gtoc'); if (!a || !b || a.scrollHeight <= a.clientHeight + 2) return;
    const top = b.offsetTop - a.clientHeight / 3;
    a.scrollTo({ top: Math.max(0, top) });
  }
  let tocPin = null, tocRaf = 0, tocLast = null;
  function updateToc() {
    tocRaf = 0;
    const a = $('#gtoc'); if (!a || state.route.view !== 'guide') return;
    const btns = $$('.gtoc-a', a); if (!btns.length) return;
    const atBottom = scrollY + innerHeight >= document.documentElement.scrollHeight - 4;
    let cur = null;
    if (tocPin && (Date.now() - tocPin.t < 1200 || atBottom)) cur = tocPin.id;
    else {
      tocPin = null;
      for (const b of btns) { const h = document.getElementById(b.dataset.toc); if (h && h.getBoundingClientRect().top <= 120) cur = b.dataset.toc; }
    }
    btns.forEach(b => { const on = b.dataset.toc === cur; b.classList.toggle('on', on); if (on) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current'); });
    $$('.gtoc-list > li', a).forEach(li => li.classList.toggle('open', !!li.querySelector('.gtoc-a.on')));
    const onb = a.querySelector('.gtoc-a.on');
    if (onb && onb !== tocLast && !tocIsOpen()) scrollTocTo(onb);
    tocLast = onb;
  }
  const queueToc = () => { if (!tocRaf) tocRaf = requestAnimationFrame(updateToc); };
  window.addEventListener('scroll', queueToc, { passive: true });
  window.addEventListener('resize', () => { if (tocIsOpen() && innerWidth >= 1180) closeToc(); queueToc(); });

"""
rep("  function viewGuide(id) {", TOC_JS + "  function viewGuide(id) {")

# кнопка темы и страница гайда с содержанием
rep("    const right = (ed ? navA('e-' + g.id, ICON.pen, 'circle press', ' aria-label=\"Редактировать гайд\"') : '') +",
    "    const right = (ed ? navA('e-' + g.id, ICON.pen, 'circle press', ' aria-label=\"Редактировать гайд\"') : '') + themeBtn() +")
rep("    let h = '<div class=\"page narrow\">' + topbar(s ? 's-' + s.id : 'sections', s ? esc(s.num + ' · ' + s.name) : '', right);",
    "    const tocItems = tocTree(pr.toc); const hasToc = tocItems.length >= 2;\n"
    "    let h = '<div class=\"page narrow' + (hasToc ? ' has-toc' : '') + '\">' + (hasToc ? tocAside(tocItems) : '') + '<div class=\"g-col\">' + topbar(s ? 's-' + s.id : 'sections', s ? esc(s.num + ' · ' + s.name) : '', right);")
rep("    if (pr.toc.length >= 2) h += '<nav class=\"toc\" aria-label=\"Содержание\">' + pr.toc.map(",
    "    if (hasToc) h += '<nav class=\"toc\" aria-label=\"Содержание\">' + tocItems.map(")
rep("    return h + '</div>';\n  }\n  function viewSearch() {",
    "    return h + '</div>' + (hasToc ? '<button class=\"toc-fab press\" type=\"button\" data-toc-open aria-controls=\"gtoc\" aria-expanded=\"false\">' + ICON.list + '<span>Содержание</span></button>' +\n"
    "      '<div class=\"gtoc-back\" data-toc-close hidden></div>' : '') + '</div>';\n  }\n  function viewSearch() {")

rep("<span class=\"eyebrow\">Гайдбук «Квиз, плиз!»</span><b>' + (name ? 'Привет, ' + esc(name) : 'Привет!') + '</b></div></div>'",
    "<span class=\"eyebrow\">Гайдбук «Квиз, плиз!»</span><b>' + (name ? 'Привет, ' + esc(name) : 'Привет!') + '</b></div>' + themeBtn('home-theme') + '</div>'")
rep("<span class=\"eyebrow\">Гайдбук «Квиз, плиз!»</span><b>' + esc(title) + '</b></div></div>'",
    "<span class=\"eyebrow\">Гайдбук «Квиз, плиз!»</span><b>' + esc(title) + '</b></div>' + themeBtn('home-theme') + '</div>'")

rep("    $('#main').innerHTML = html;\n    $('#readbar').hidden = r.view !== 'guide';",
    "    document.documentElement.classList.remove('toc-lock'); tocLast = null;\n    $('#main').innerHTML = html;\n    $('#readbar').hidden = r.view !== 'guide';")
rep("        updateReadbar();\n      }\n      if (state.highlight) {",
    "        updateReadbar();\n      }\n      updateToc();\n      if (state.highlight) {")

rep("  document.addEventListener('keydown', e => {\n",
    "  document.addEventListener('keydown', e => {\n    if (e.key === 'Escape' && tocIsOpen()) { closeToc(true); return; }\n")
rep("    const toc = t.closest('[data-toc]');\n    if (toc) { e.preventDefault(); const el = document.getElementById(toc.dataset.toc); if (el) el.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' }); return; }",
    "    if (t.closest('[data-theme-toggle]')) { toggleTheme(); return; }\n"
    "    if (t.closest('[data-toc-open]')) { openToc(); return; }\n"
    "    if (t.closest('[data-toc-close]')) { closeToc(true); return; }\n"
    "    const toc = t.closest('[data-toc]');\n"
    "    if (toc) {\n"
    "      e.preventDefault(); const id = toc.dataset.toc; const smooth = reduceMotion ? 'auto' : 'smooth';\n"
    "      closeToc();\n"
    "      if (id === 'top') { tocPin = null; window.scrollTo({ top: 0, behavior: smooth }); return; }\n"
    "      const el = document.getElementById(id);\n"
    "      if (el) { tocPin = { id, t: Date.now() }; el.scrollIntoView({ behavior: smooth, block: 'start' }); updateToc(); }\n"
    "      return;\n"
    "    }")

open(dst, 'w', encoding='utf-8').write(s)
print('ok', len(s))
