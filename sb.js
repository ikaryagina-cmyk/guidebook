/* Гайдбук: маленький клиент Supabase (вход редакторов по паролю, таблицы, картинки) и прослойка
   под интерфейс базы, с которым работает страница. Без внешних библиотек. */
(function () {
  'use strict';
  const AUTH_KEY = 'gb.auth';
  const ls = {
    get(k) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : null; } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } },
    del(k) { try { localStorage.removeItem(k); } catch (e) { } }
  };
  function fail(code, message, status) { const e = new Error(message || code); e.code = code; e.status = status || 0; return e; }
  function codeFor(status, body) {
    const pg = body && (body.code || body.error_code);
    if (status === 401 || status === 403 || pg === '42501') return 'not_granted';
    if (status === 429) return 'rate_limited';
    if (status === 413) return 'too_large';
    if (status === 400 || status === 422 || status === 409) return 'invalid_argument';
    if (status === 507) return 'quota_exceeded';
    return 'unavailable';
  }

  function create(cfg) {
    const base = String(cfg.url || '').replace(/\/+$/, '');
    const key = cfg.key;
    let session = ls.get(AUTH_KEY);
    let refreshing = null;

    function saveSession(s) {
      if (!s || !s.access_token) { session = null; ls.del(AUTH_KEY); return null; }
      const now = Math.floor(Date.now() / 1000);
      session = {
        access_token: s.access_token,
        refresh_token: s.refresh_token,
        expires_at: Number(s.expires_at) || (now + (Number(s.expires_in) || 3600)),
        email: (s.user && s.user.email) || s.email || (session && session.email) || ''
      };
      ls.set(AUTH_KEY, session);
      return session;
    }

    async function raw(path, opts) {
      opts = opts || {};
      const headers = Object.assign({ apikey: key }, opts.headers || {});
      if (opts.auth !== false && session && session.access_token) headers.Authorization = 'Bearer ' + session.access_token;
      let body = opts.body;
      if (body !== undefined && !(body instanceof Blob) && typeof body !== 'string') { body = JSON.stringify(body); headers['Content-Type'] = 'application/json'; }
      let res;
      try { res = await fetch(base + path, { method: opts.method || 'GET', headers, body, cache: 'no-store' }); }
      catch (e) { throw fail('unavailable', 'Нет связи с базой'); }
      const text = await res.text();
      let data = null; if (text) { try { data = JSON.parse(text); } catch (e) { data = text; } }
      if (!res.ok) {
        const msg = data && (data.msg || data.message || data.error_description || data.error);
        const err = fail(codeFor(res.status, data), msg || ('HTTP ' + res.status), res.status);
        err.body = data; throw err;
      }
      return data;
    }

    async function refresh() {
      if (!session || !session.refresh_token) return null;
      if (!refreshing) {
        refreshing = raw('/auth/v1/token?grant_type=refresh_token', { method: 'POST', auth: false, body: { refresh_token: session.refresh_token } })
          .then(saveSession)
          .catch(e => { if (e.status === 400 || e.status === 401 || e.status === 403) saveSession(null); throw e; })
          .finally(() => { refreshing = null; });
      }
      return refreshing;
    }
    async function fresh() {
      if (session && session.expires_at - 90 < Date.now() / 1000) { try { await refresh(); } catch (e) { if (!session) throw e; } }
    }
    // Запрос с токеном: если токен истёк, обновляем и повторяем один раз
    async function call(path, opts) {
      await fresh();
      try { return await raw(path, opts); }
      catch (e) {
        if (e.status === 401 && session && session.refresh_token) { await refresh(); return raw(path, opts); }
        throw e;
      }
    }

    const auth = {
      get email() { return session ? session.email : ''; },
      // Сессия редактора, если он уже входил на этом устройстве
      async restore() {
        if (!session) return null;
        try { await fresh(); } catch (e) { return session ? session : null; }
        return session;
      },
      // editor | city | closed | none
      async kind(email) { return raw('/rest/v1/rpc/login_kind', { method: 'POST', auth: false, body: { addr: email } }); },
      async signInPassword(email, password) {
        const s = await raw('/auth/v1/token?grant_type=password', { method: 'POST', auth: false, body: { email, password } });
        return saveSession(s);
      },
      // Новый редактор создаёт себе пароль. Если в Supabase включено подтверждение почты, сессии не будет.
      async signUp(email, password) {
        const s = await raw('/auth/v1/signup', { method: 'POST', auth: false, body: { email, password, data: {} } });
        return s && s.access_token ? saveSession(s) : null;
      },
      async updatePassword(password) { return call('/auth/v1/user', { method: 'PUT', body: { password } }); },
      async signOut() {
        try { if (session) await raw('/auth/v1/logout', { method: 'POST' }); } catch (e) { }
        saveSession(null);
      }
    };

    const enc = encodeURIComponent;
    return {
      auth,
      select: (table, cols) => call('/rest/v1/' + table + '?select=' + enc(cols || 'id,data') + '&order=id'),
      rows: (table, query) => call('/rest/v1/' + table + '?' + query),
      rpc: (fn, args) => call('/rest/v1/rpc/' + fn, { method: 'POST', body: args || {} }),
      upsert: (table, rows) => call('/rest/v1/' + table + '?on_conflict=id', { method: 'POST', body: rows, headers: { Prefer: 'resolution=merge-duplicates,return=minimal' } }),
      remove: (table, id) => call('/rest/v1/' + table + '?id=eq.' + enc(id), { method: 'DELETE', headers: { Prefer: 'return=minimal' } }),
      upload: (bucket, name, blob, type) => call('/storage/v1/object/' + bucket + '/' + name, { method: 'POST', body: blob, headers: { 'Content-Type': type || 'application/octet-stream', 'x-upsert': 'false', 'cache-control': '31536000' } }),
      listFiles: bucket => call('/storage/v1/object/list/' + bucket, { method: 'POST', body: { prefix: '', limit: 1000, offset: 0 } }),
      publicUrl: (bucket, name) => base + '/storage/v1/object/public/' + bucket + '/' + name
    };
  }

  // Прослойка: db / user / assets / downloads в том виде, в каком их ждёт страница
  function runtime(sb, who) {
    const editor = !!who.editor;
    const watchers = [];
    let lastFull = 0;

    const toDocs = rows => (Array.isArray(rows) ? rows : []).map(r => ({ id: r.id, data: () => r.data }));
    async function fetchTable(name) {
      if (editor) return sb.select(name);
      if (name === 'guides') return sb.rpc('guides_for', { addr: who.email });
      if (name === 'config') { const d = await sb.rpc('config_for', { addr: who.email }); return d ? [{ id: 'app', data: d }] : []; }
      return [];
    }
    async function stampOf(name) {
      const rows = await sb.select(name, 'id,updated_at');
      return (rows || []).map(r => r.id + '@' + r.updated_at).join('|');
    }
    function makeWatcher(name, emit, onErr) {
      const w = { name, emit, onErr, stamp: null };
      w.load = async () => {
        try {
          if (editor) w.stamp = await stampOf(name);
          emit(await fetchTable(name));
        } catch (e) { if (onErr) onErr(e); }
      };
      w.check = async () => {
        try {
          if (editor) {
            const s = await stampOf(name);
            if (s === w.stamp) return;
            w.stamp = s;
          }
          emit(await fetchTable(name));
        } catch (e) { }
      };
      watchers.push(w); w.load(); lastFull = Date.now();
      return () => { const i = watchers.indexOf(w); if (i >= 0) watchers.splice(i, 1); };
    }
    // Свежие данные: у редакторов проверка раз в 40 секунд, у городов — когда вкладку открыли снова
    function poll(force) {
      if (document.visibilityState === 'hidden') return;
      if (!editor && !force && Date.now() - lastFull < 5 * 60 * 1000) return;
      lastFull = Date.now();
      watchers.forEach(w => w.check());
    }
    if (editor) setInterval(() => poll(true), 40000);
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') poll(editor); });

    function ref(table, id) {
      return {
        set: data => sb.upsert(table, [{ id, data }]).then(() => { watchers.forEach(w => { if (w.name === table) w.stamp = null; }); }),
        delete: () => sb.remove(table, id),
        onSnapshot(cb, onErr) {
          return makeWatcher(table, rows => {
            const r = (rows || []).find(x => x.id === id);
            cb({ exists: !!r, id, data: () => (r ? r.data : undefined) });
          }, onErr);
        }
      };
    }
    const db = {
      collection(name) {
        return {
          doc: id => ref(name, id),
          onSnapshot: (cb, onErr) => makeWatcher(name, rows => cb({ docs: toDocs(rows) }), onErr),
          async setMany(list) {
            for (let i = 0; i < list.length; i += 40) await sb.upsert(name, list.slice(i, i + 40).map(x => ({ id: x[0], data: x[1] })));
          }
        };
      },
      doc(path) { const p = String(path).split('/'); return ref(p[0], p[1]); },
      refresh: () => poll(true)
    };
    const user = {
      id: async () => who.email,
      me: async () => ({ name: '', email: who.email }),
      can: async () => editor,
      canEdit: async () => editor,
      isOwner: async () => false,
      profiles: async ids => {
        const out = {};
        if (editor) (ids || []).forEach(i => { if (/@/.test(i)) out[i] = { name: i }; });
        return out;
      }
    };
    const EXT = { 'image/png': 'png', 'image/jpeg': 'jpg', 'image/gif': 'gif', 'image/webp': 'webp' };
    const assets = editor ? {
      async upload(blob, opts) {
        const type = (opts && opts.type) || blob.type || 'image/png';
        if (blob.size > 20 * 1048576) throw fail('too_large');
        const d = new Date();
        const name = d.getFullYear() + String(d.getMonth() + 1).padStart(2, '0') + '-' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8) + '.' + (EXT[type] || 'bin');
        await sb.upload('images', name, blob, type);
        return { id: name, url: sb.publicUrl('images', name) };
      },
      async list() {
        let files = 0, bytes = 0;
        const top = await sb.listFiles('images');
        (top || []).forEach(f => { if (f && f.id) { files++; bytes += (f.metadata && f.metadata.size) || 0; } });
        return { usage: { files, bytes } };
      }
    } : null;
    const downloads = {
      async save(o) {
        const blob = o.data instanceof Blob ? o.data : new Blob([o.data], { type: /\.csv$/i.test(o.filename) ? 'text/csv;charset=utf-8' : 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob); a.download = o.filename || 'file';
        document.body.appendChild(a); a.click();
        setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
      }
    };
    return { db, user, assets, downloads };
  }

  window.GBSupabase = { create, runtime };
})();
