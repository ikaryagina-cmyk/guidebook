/* Section 04 — Games schedule. Reads pre-generated public JSON from same origin. */
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
  status='loading';render();
  try{
   const response=await fetch('./games-schedule-data.json',{cache:'no-store'});
   if(!response.ok)throw new Error('HTTP '+response.status);
   const data=await response.json();
   if(!Array.isArray(data.rows))throw new Error('Неверный формат расписания');
   rows=data.rows;status='ready';error='';
  }catch(e){
   status='error';
   error='Публичная выгрузка ещё не создана. '+e.message;
  }
  render();
 }
 function mount(){if(!root())return;render();if(status==='loading')load()}
 return {mount};
})();