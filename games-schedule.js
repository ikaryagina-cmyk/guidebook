/* Section 04 — Games schedule. Public JSON endpoint configured after Apps Script deployment. */
window.GAMES_SCHEDULE_ENDPOINT = "https://script.google.com/macros/s/AKfycbzNf_s5PGYDLs01nuQP4DJ_x0tUi074m2UP0HftOzKMzCTWhlHjXVW7FYuOID1XUhOu/exec";
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
 function load(){
  const endpoint=window.GAMES_SCHEDULE_ENDPOINT;
  if(!endpoint){status='error';error='Адрес расписания не задан.';render();return}
  status='loading';render();
  const script=document.createElement('script');
  let finished=false;
  const previous=window.GamesScheduleReceive;
  const timeout=setTimeout(()=>finish(new Error('Превышено время ожидания')),25000);
  function finish(err,data){
   if(finished)return;
   finished=true;clearTimeout(timeout);script.remove();
   if(previous===undefined)delete window.GamesScheduleReceive;else window.GamesScheduleReceive=previous;
   if(err){status='error';error=err.message}
   else if(!data||!Array.isArray(data.rows)){status='error';error='Неверный формат данных'}
   else {rows=data.rows;status='ready'}
   render();
  }
  window.GamesScheduleReceive=data=>finish(null,data);
  script.onerror=()=>finish(new Error('Сервер расписания недоступен'));
  script.src=endpoint+'?callback=GamesScheduleReceive&_='+Date.now();
  document.head.appendChild(script);
 }
 function mount(){if(!root())return;render();if(status==='loading')load()}
 return {mount};
})();