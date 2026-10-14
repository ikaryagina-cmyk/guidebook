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
-- Кто редактирует базу (отдел франшиз)
create table if not exists public.editors (
  email text primary key,
  added_at timestamptz not null default now()
);

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
-- Редакторы входят по почте и паролю (аккаунт заводится в Authentication → Users).
create or replace function public.my_email() returns text
language sql stable set search_path = public as $$
  select lower(coalesce(auth.jwt() ->> 'email', ''))
$$;

create or replace function public.is_editor() returns boolean
language sql stable security definer set search_path = public as $$
  select public.my_email() <> '' and exists (select 1 from public.editors e where lower(e.email) = public.my_email())
$$;

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

-- Как пускать эту почту: editor — спросить пароль, city — пустить, closed — город закрыт, none — почты нет в списке
create or replace function public.login_kind(addr text) returns text
language sql stable security definer set search_path = public as $$
  select case
    when coalesce(trim(addr), '') = '' then 'none'
    when exists (select 1 from public.editors e where lower(e.email) = lower(trim(addr))) then 'editor'
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
