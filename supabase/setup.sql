-- Гайдбук «Квиз, плиз!» — настройка базы Supabase.
-- Запускать целиком в SQL Editor. Повторный запуск безопасен: ничего не удаляет.

-- ---------- таблицы ----------
create table if not exists public.guides (
  id text primary key,
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
create table if not exists public.config (
  id text primary key,
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
-- Города и почты сотрудников: {name, active, people: [{email, sections|null}], emails: [...]}
create table if not exists public.access (
  id text primary key,
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
-- Кто редактирует базу (отдел франшиз). user_id — аккаунт, который принял приглашение;
-- invite_code — код приглашения, пока редактор ещё не входил.
create table if not exists public.editors (
  email text primary key,
  added_at timestamptz not null default now()
);
alter table public.editors add column if not exists user_id uuid;
alter table public.editors add column if not exists invite_code text;

-- Почты редакторов храним в нижнем регистре
update public.editors e set email = lower(trim(e.email))
  where e.email <> lower(trim(e.email))
    and not exists (select 1 from public.editors d where d.email = lower(trim(e.email)));

-- Редакторы, заведённые вручную до приглашений, привязываются к своим аккаунтам по почте
update public.editors e set user_id = u.id
  from auth.users u
  where e.user_id is null and e.invite_code is null and lower(u.email) = lower(e.email);

create or replace function public.touch_updated_at() returns trigger
language plpgsql as $$
begin new.updated_at := now(); return new; end $$;

drop trigger if exists guides_touch on public.guides;
create trigger guides_touch before update on public.guides for each row execute function public.touch_updated_at();
drop trigger if exists config_touch on public.config;
create trigger config_touch before update on public.config for each row execute function public.touch_updated_at();
drop trigger if exists access_touch on public.access;
create trigger access_touch before update on public.access for each row execute function public.touch_updated_at();

-- ---------- кто вошёл ----------
-- Редакторы входят по почте и паролю. Новый редактор сам создаёт пароль по коду приглашения.
create or replace function public.my_email() returns text
language sql stable set search_path = public as $$
  select lower(coalesce(auth.jwt() ->> 'email', ''))
$$;

create or replace function public.is_editor() returns boolean
language sql stable security definer set search_path = public as $$
  select auth.uid() is not null and public.my_email() <> '' and exists (
    select 1 from public.editors e where e.user_id = auth.uid() and lower(e.email) = public.my_email())
$$;

-- Статус редактора: active — входит по паролю, pending — ждёт первого входа, null — не редактор
create or replace function public.editor_status(addr text) returns text
language sql stable security definer set search_path = public as $$
  select case
    when e.user_id is not null and exists (select 1 from auth.users u where u.id = e.user_id) then 'active'
    else 'pending' end
  from public.editors e
  where lower(e.email) = lower(trim(coalesce(addr, '')))
  limit 1
$$;

create or replace function public.new_invite_code() returns text
language sql volatile set search_path = public as $$
  select upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 8))
$$;

-- Подходит ли код приглашения (проверяется до создания пароля)
create or replace function public.check_invite(addr text, code text) returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce(public.editor_status(addr) = 'pending', false) and exists (
    select 1 from public.editors e
    where lower(e.email) = lower(trim(addr)) and e.invite_code is not null
      and e.invite_code = upper(trim(coalesce(code, ''))))
$$;

-- Новый редактор после создания пароля привязывает аккаунт по коду
create or replace function public.claim_editor(code text) returns boolean
language plpgsql volatile security definer set search_path = public as $$
declare n int;
begin
  if auth.uid() is null then return false; end if;
  update public.editors e set user_id = auth.uid(), invite_code = null
   where lower(e.email) = public.my_email()
     and e.invite_code is not null and e.invite_code = upper(trim(coalesce(code, '')))
     and (e.user_id is null or not exists (select 1 from auth.users u where u.id = e.user_id));
  get diagnostics n = row_count;
  return n > 0;
end $$;

-- Добавить редактора: возвращает код приглашения
create or replace function public.add_editor(addr text) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare a text := lower(trim(coalesce(addr, ''))); c text;
begin
  if not public.is_editor() then raise exception 'not_editor' using errcode = '42501'; end if;
  if a !~ '^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$' then raise exception 'bad_email' using errcode = '22023'; end if;
  if public.editor_status(a) = 'active' then return jsonb_build_object('status', 'active'); end if;
  c := public.new_invite_code();
  insert into public.editors (email, invite_code) values (a, c)
    on conflict (email) do update set invite_code = excluded.invite_code, user_id = null;
  return jsonb_build_object('status', 'invited', 'code', c);
end $$;

-- Новый код для редактора (забыл пароль или код): старый аккаунт удаляется, чтобы создать пароль заново
create or replace function public.reset_editor(addr text) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare a text := lower(trim(coalesce(addr, ''))); c text; gone boolean := true;
begin
  if not public.is_editor() then raise exception 'not_editor' using errcode = '42501'; end if;
  if a = public.my_email() then raise exception 'self' using errcode = '22023'; end if;
  if not exists (select 1 from public.editors e where lower(e.email) = a) then raise exception 'not_found' using errcode = '22023'; end if;
  c := public.new_invite_code();
  update public.editors e set user_id = null, invite_code = c where lower(e.email) = a;
  begin
    delete from auth.users u where lower(u.email) = a;
  exception when others then
    gone := false;
  end;
  if gone then gone := not exists (select 1 from auth.users u where lower(u.email) = a); end if;
  return jsonb_build_object('code', c, 'deleted', gone);
end $$;

-- Убрать редактора (себя убрать нельзя)
create or replace function public.remove_editor(addr text) returns boolean
language plpgsql volatile security definer set search_path = public as $$
declare a text := lower(trim(coalesce(addr, '')));
begin
  if not public.is_editor() then raise exception 'not_editor' using errcode = '42501'; end if;
  if a = public.my_email() then raise exception 'self' using errcode = '22023'; end if;
  delete from public.editors e where lower(e.email) = a;
  return found;
end $$;

drop function if exists public.access_people(text);

-- Записи о сотруднике в списке городов: [{email, sections|null, active}, ...]
create or replace function public.access_people(target text, only_open boolean default true) returns setof jsonb
language sql stable security definer set search_path = public as $$
  select p || jsonb_build_object('active', coalesce((a.data ->> 'active')::boolean, true))
  from public.access a
  cross join lateral jsonb_array_elements(
    case
      when jsonb_typeof(a.data -> 'people') = 'array' then a.data -> 'people'
      when jsonb_typeof(a.data -> 'emails') = 'array' then
        (select coalesce(jsonb_agg(jsonb_build_object('email', e, 'sections', null)), '[]'::jsonb)
           from jsonb_array_elements_text(a.data -> 'emails') e)
      else '[]'::jsonb
    end) p
  where (not only_open or coalesce((a.data ->> 'active')::boolean, true))
    and coalesce(target, '') <> ''
    and lower(p ->> 'email') = lower(trim(target))
$$;

-- Доступ сотрудника города: null — доступа нет; {"all": true} — все разделы; {"all": false, "sections": [...]}
create or replace function public.access_of(addr text) returns jsonb
language sql stable security definer set search_path = public as $$
  with p as (select * from public.access_people(addr) x)
  select case
    when not exists (select 1 from p) then null
    else jsonb_build_object(
      'all', exists (select 1 from p where jsonb_typeof(p.x -> 'sections') is distinct from 'array'),
      'sections', coalesce((
        select jsonb_agg(distinct s)
        from p cross join lateral jsonb_array_elements_text(
          case when jsonb_typeof(p.x -> 'sections') = 'array' then p.x -> 'sections' else '[]'::jsonb end) s
      ), '[]'::jsonb))
  end
$$;

-- Как пускать эту почту: editor — спросить пароль, editor_new — код приглашения и новый пароль,
-- city — пустить, closed — город закрыт, none — почты нет в списке
create or replace function public.login_kind(addr text) returns text
language sql stable security definer set search_path = public as $$
  select case
    when coalesce(trim(addr), '') = '' then 'none'
    when public.editor_status(addr) = 'active' then 'editor'
    when public.editor_status(addr) = 'pending' then 'editor_new'
    when public.access_of(addr) is not null then 'city'
    when exists (select 1 from public.access_people(addr, false)) then 'closed'
    else 'none'
  end
$$;

-- Кто я (для редактора после входа по паролю)
create or replace function public.whoami() returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('email', public.my_email(), 'editor', public.is_editor())
$$;

-- Гайды для сотрудника города: без черновиков, только его разделы и подразделы, без заметок отдела
create or replace function public.guides_for(addr text) returns table (id text, data jsonb)
language plpgsql stable security definer set search_path = public as $$
declare
  acc jsonb;
  allowed text[];
begin
  acc := public.access_of(addr);
  if acc is null then return; end if;
  if (acc ->> 'all')::boolean then
    return query select g.id, g.data - 'todo' - 'updatedBy' from public.guides g
      where coalesce(g.data ->> 'status', '') <> 'draft';
    return;
  end if;
  select array_agg(distinct x) into allowed from (
    select jsonb_array_elements_text(acc -> 'sections') as x
    union
    select s ->> 'id'
      from public.config c
      cross join lateral jsonb_array_elements(coalesce(c.data -> 'sections', '[]'::jsonb)) s
      where c.id = 'app'
        and (s ->> 'parent') in (select jsonb_array_elements_text(acc -> 'sections'))
  ) t;
  return query select g.id, g.data - 'todo' - 'updatedBy' from public.guides g
    where coalesce(g.data ->> 'status', '') <> 'draft'
      and (g.data ->> 'sectionId') = any (coalesce(allowed, array[]::text[]));
end $$;

-- Структура разделов для сотрудника города (без заметок отдела)
create or replace function public.config_for(addr text) returns jsonb
language sql stable security definer set search_path = public as $$
  select case
    when public.access_of(addr) is null then null
    else (
      select jsonb_build_object('sections', coalesce(jsonb_agg(e.s - 'todo' order by e.o), '[]'::jsonb))
      from public.config c
      cross join lateral jsonb_array_elements(coalesce(c.data -> 'sections', '[]'::jsonb)) with ordinality as e(s, o)
      where c.id = 'app')
  end
$$;

-- ---------- права ----------
alter table public.guides enable row level security;
alter table public.config enable row level security;
alter table public.access enable row level security;
alter table public.editors enable row level security;

drop policy if exists "editors_all" on public.guides;
create policy "editors_all" on public.guides for all to authenticated using (public.is_editor()) with check (public.is_editor());
drop policy if exists "editors_all" on public.config;
create policy "editors_all" on public.config for all to authenticated using (public.is_editor()) with check (public.is_editor());
drop policy if exists "editors_all" on public.access;
create policy "editors_all" on public.access for all to authenticated using (public.is_editor()) with check (public.is_editor());
drop policy if exists "editors_all" on public.editors;
create policy "editors_all" on public.editors for all to authenticated using (public.is_editor()) with check (public.is_editor());

revoke all on public.guides, public.config, public.access, public.editors from anon;
grant select, insert, update, delete on public.guides, public.config, public.access, public.editors to authenticated;

revoke execute on function public.access_people(text, boolean) from public, anon, authenticated;
revoke execute on function public.access_of(text) from public, anon, authenticated;
revoke execute on function public.whoami() from public, anon;
revoke execute on function public.editor_status(text), public.new_invite_code() from public, anon, authenticated;
revoke execute on function public.claim_editor(text), public.add_editor(text), public.reset_editor(text), public.remove_editor(text) from public, anon;
grant execute on function public.check_invite(text, text) to anon, authenticated;
grant execute on function public.claim_editor(text), public.add_editor(text), public.reset_editor(text), public.remove_editor(text) to authenticated;
grant execute on function public.login_kind(text), public.guides_for(text), public.config_for(text) to anon, authenticated;
grant execute on function public.my_email(), public.is_editor(), public.whoami() to authenticated;

-- ---------- картинки ----------
insert into storage.buckets (id, name, public)
values ('images', 'images', true)
on conflict (id) do update set public = true;

drop policy if exists "gb_images_select" on storage.objects;
create policy "gb_images_select" on storage.objects for select to authenticated
  using (bucket_id = 'images');
drop policy if exists "gb_images_insert" on storage.objects;
create policy "gb_images_insert" on storage.objects for insert to authenticated
  with check (bucket_id = 'images' and public.is_editor());
drop policy if exists "gb_images_update" on storage.objects;
create policy "gb_images_update" on storage.objects for update to authenticated
  using (bucket_id = 'images' and public.is_editor());
drop policy if exists "gb_images_delete" on storage.objects;
create policy "gb_images_delete" on storage.objects for delete to authenticated
  using (bucket_id = 'images' and public.is_editor());

-- ---------- живое обновление у редакторов ----------
do $$
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    begin alter publication supabase_realtime add table public.guides; exception when duplicate_object then null; end;
    begin alter publication supabase_realtime add table public.config; exception when duplicate_object then null; end;
    begin alter publication supabase_realtime add table public.access; exception when duplicate_object then null; end;
  end if;
end $$;
