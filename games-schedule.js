/* Section 04 — Games schedule. Public JSON endpoint configured after Apps Script deployment. */
window.GAMES_SCHEDULE_ENDPOINT = window.GAMES_SCHEDULE_ENDPOINT || '';
window.GamesSchedule = (() => {
 const SOURCE='https://docs.google.com/spreadsheets/d/1fOrA8bzXKTT-aZgFpYD5t2w1DP9x8fAyobsf2GzaDYw/edit';
 const tabs=[['current','График 2026'],['archive','Архив 2020–2025'],['special','Стримы и тематические']];
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const link=u=>{try{const p=new URL(u);return ['https:','http:'].includes(p.protocol)?p.href:''}catch{return ''}};
 let rows=[], tab='current', query='', status='loading', error='';
 const root=()=>document.getElementById('games-schedule-root');
 function render(){
  const el=root();if(!el)return;
  const filtered=rows.filter(r=>r.group===tab&&[r.date,r.name,r.rating,r.score,r.annotation].some(v=>String(v||'').toLowerCase().includes(query.toLowerCase())));
  el.innerHTML='<div class="games-controls"><div class="games-tabs" role="tablist">'+tabs.map(([id,name])=>'<button type="button" role="tab" aria-selected="'+(id===tab)+'" data-games-tab="'+id+'">'+name+'</button>').join('')+'</div><input id="games-search" type="search" placeholder="Поиск по названию, номеру, дате" aria-label="Поиск игр" value="'+esc(query)+'"></div>'+
   (status==='loading'?'<p class="games-message">Загружаю расписание…</p>':status==='error'?'<div class="games-message">Автоматическая загрузка пока не настроена. '+esc(error)+' <a href="'+SOURCE+'" target="_blank" rel="noopener noreferrer">Открыть исходную таблицу</a> (потребуется доступ).</div>':
   '<p class="games-count">Найдено игр: '+filtered.length+'</p><div class="games-table-wrap"><table class="games-table"><thead><tr><th>Дата</th><th>Игра</th><th>Рейтинг</th><th>Средний балл</th><th>Гайдлайн</th></tr></thead><tbody>'+filtered.map(r=>'<tr><td>'+esc(r.date)+'</td><td><strong>'+esc(r.name)+'</strong>'+(r.annotation?'<div class="games-note">'+esc(r.annotation)+'</div>':'')+'</td><td>'+esc(r.rating)+'</td><td>'+esc(r.score)+'</td><td>'+(link(r.guide)?'<a target="_blank" rel="noopener noreferrer" href="'+esc(link(r.guide))+'">Открыть ↗</a>':'—')+'</td></tr>').join('')+'</tbody></table></div>'+(filtered.length?'':'<p class="games-message">По этому запросу игр нет.</p>'));
  el.querySelectorAll('[data-games-tab]').forEach(b=>b.addEventListener('click',()=>{tab=b.dataset.gamesTab;render()}));
  const input=el.querySelector('#games-search');if(input){input.addEventListener('input',e=>{query=e.target.value;const pos=e.target.selectionStart;render();const next=root()?.querySelector('#games-search');if(next){next.focus();next.setSelectionRange(pos,pos)}})}
 }
 async function load(){
  const endpoint=window.GAMES_SCHEDULE_ENDPOINT;
  if(!endpoint){status='error';error='Адрес безопасной выгрузки будет добавлен после настройки Google Apps Script.';render();return}
  try{const r=await fetch(endpoint,{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();if(!Array.isArray(d.rows))throw Error('Неверный формат данных');rows=d.rows;status='ready'}
  catch(e){status='error';error='Не удалось получить данные: '+e.message}render();
 }
 function mount(){if(!root())return;render();if(status==='loading')load()}
 return {mount};
})();