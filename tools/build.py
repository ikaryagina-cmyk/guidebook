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
    } else {
      loginShell('Вход для отдела', '<form class="panel login-box" id="pwForm" novalidate><h2 class="h2">Пароль редактора</h2>' +
        '<p>Почта <b>' + esc(L.email) + '</b> есть в списке редакторов, поэтому нужен пароль.</p>' +
        '<input type="email" name="username" autocomplete="username" value="' + esc(L.email) + '" hidden>' +
        '<div class="field"><label for="lg-pw">Пароль</label><input class="inp" id="lg-pw" type="password" autocomplete="current-password"></div>' +
        err + '<button class="btn" type="submit"' + (L.busy ? ' disabled' : '') + '>' + (L.busy ? 'Проверяю…' : 'Войти') + '</button>' +
        '<div class="login-links"><button class="linkbtn" type="button" id="lgOther">Другая почта</button></div></form>');
      const i = $('#lg-pw'); if (i) i.focus();
    }
  }
  function loginError(e) {
    const c = e && e.code, b = e && e.body, ec = b && (b.error_code || b.code);
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
      if (kind === 'city') { storeCity(v); boot(); return; }
      LOGIN.err = kind === 'closed' ? CLOSED : NO_EMAIL; renderLogin();
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
rep("  /* ---------- start ---------- */\n", LOGIN_JS + "\n  /* ---------- start ---------- */\n")

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

open(dst, 'w', encoding='utf-8').write(s)
print('ok', len(s))
