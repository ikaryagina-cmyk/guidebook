/* Section 04 — Games schedule. Reads pre-generated public JSON from same origin. */
window.GamesSchedule = (() => {
 const SOURCE='https://docs.google.com/spreadsheets/d/1fOrA8bzXKTT-aZgFpYD5t2w1DP9x8fAyobsf2GzaDYw/edit';
 const tabs=[['current','График 2026'],['archive','Архив 2020–2025'],['special','Стримы и тематические']];
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const link=u=>{try{const p=new URL(u);return ['https:','http:'].includes(p.protocol)?p.href:''}catch{return ''}};
 let rows=[], tab='current', query='', status='loading', error='';
 const root=()=>document.getElementById('games-schedule-root');
 const months=['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];
 const monthIndex={'январь':0,'февраль':1,'март':2,'апрель':3,'май':4,'июнь':5,'июль':6,'август':7,'сентябрь':8,'октябрь':9,'ноябрь':10,'декабрь':11};
 function dateInfo(value){
  const raw=String(value||'').trim();
  const full=raw.match(/^(\d{1,2})\.(\d{1,2})\.(20\d{2})/);
  if(full){
   const day=Number(full[1]),month=Number(full[2])-1,year=Number(full[3]);
   const date=new Date(Date.UTC(year,month,day));
   if(date.getUTCFullYear()===year&&date.getUTCMonth()===month&&date.getUTCDate()===day)return {date,monthOnly:false};
  }
  const monthly=raw.toLowerCase().match(/([а-яё]+)\s*,?\s*(20\d{2})/);
  if(monthly&&monthIndex[monthly[1]]!==undefined){
   return {date:new Date(Date.UTC(Number(monthly[2]),monthIndex[monthly[1]],1)),monthOnly:true};
  }
  return null;
 }
 const formatDay=d=>String(d.getUTCDate()).padStart(2,'0');
 function weekLabel(date){
  const start=new Date(date.getTime());
  const day=(start.getUTCDay()+6)%7;
  start.setUTCDate(start.getUTCDate()-day);
  const end=new Date(start.getTime());end.setUTCDate(end.getUTCDate()+6);
  const label=start.getUTCMonth()===end.getUTCMonth()
   ?formatDay(start)+'–'+formatDay(end)+' '+months[end.getUTCMonth()]
   :formatDay(start)+' '+months[start.getUTCMonth()]+' – '+formatDay(end)+' '+months[end.getUTCMonth()];
  return {key:'w'+start.toISOString().slice(0,10),label:label+' '+end.getUTCFullYear()};
 }
 function groupedRows(items){
  const enriched=items.map((row,index)=>({row,index,info:dateInfo(row.date)}));
  enriched.sort((a,b)=>(a.info?.date.getTime()??Infinity)-(b.info?.date.getTime()??Infinity)||a.index-b.index);
  let lastKey='',html='';
  enriched.forEach(({row,info})=>{
   const group=info?(info.monthOnly
    ?{key:'m'+info.date.toISOString().slice(0,7),label:'Тематические · '+months[info.date.getUTCMonth()]+' '+info.date.getUTCFullYear()}
    :weekLabel(info.date)):{key:'unknown',label:'Без даты'};
   if(group.key!==lastKey){
    html+='<tr class="games-week-row"><th colspan="5" scope="rowgroup">'+esc(group.label)+'</th></tr>';
    lastKey=group.key;
   }
   html+='<tr><td>'+esc(row.date)+'</td><td><strong>'+esc(row.name)+'</strong>'+(row.annotation?'<div class="games-note">'+esc(row.annotation)+'</div>':'')+'</td><td>'+esc(row.rating)+'</td><td>'+esc(row.score)+'</td><td>'+(link(row.guide)?'<a target="_blank" rel="noopener noreferrer" href="'+esc(link(row.guide))+'">Открыть ↗</a>':'—')+'</td></tr>';
  });
  return html;
 }
 function render(){
  const el=root();if(!el)return;
  const filtered=rows.filter(r=>r.group===tab&&[r.date,r.name,r.rating,r.score,r.annotation].some(v=>String(v||'').toLowerCase().includes(query.toLowerCase())));
  el.innerHTML='<div class="games-controls"><div class="games-tabs" role="tablist">'+tabs.map(([id,name])=>'<button type="button" role="tab" aria-selected="'+(id===tab)+'" data-games-tab="'+id+'">'+name+'</button>').join('')+'</div><input id="games-search" type="search" placeholder="Поиск по названию, номеру, дате" aria-label="Поиск игр" value="'+esc(query)+'"></div>'+
   (status==='loading'?'<p class="games-message">Загружаю расписание…</p>':status==='error'?'<div class="games-message">Автоматическая загрузка пока не настроена. '+esc(error)+' <a href="'+SOURCE+'" target="_blank" rel="noopener noreferrer">Открыть исходную таблицу</a> (потребуется доступ).</div>':
   '<p class="games-count">Найдено игр: '+filtered.length+'</p><div class="games-table-wrap"><table class="games-table"><thead><tr><th>Дата</th><th>Игра</th><th>Рейтинг</th><th>Средний балл</th><th>Гайдлайн</th></tr></thead><tbody>'+groupedRows(filtered)+'</tbody></table></div>'+(filtered.length?'':'<p class="games-message">По этому запросу игр нет.</p>'));
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