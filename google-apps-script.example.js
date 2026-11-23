/** Google Apps Script — create as a standalone project under an account with access to the private Sheet.
 * Deploy as Web App: Execute as Me; Who has access: Anyone.
 * WARNING: the JSON endpoint is public. It publishes the fields below, including game notes and guide links.
 * Review and remove fields that should not be public before deployment.
 * This never changes the source spreadsheet's sharing permissions.
 */
const SHEET_ID='1fOrA8bzXKTT-aZgFpYD5t2w1DP9x8fAyobsf2GzaDYw';
const SOURCES=[
 ['График офлайн-игр 2026 год','current',0,1,2,3,4,8],
 ['График офлайн-игр 2025 год','archive',0,1,2,3,4,6],
 ['График офлайн-игр 2024 год','archive',0,1,2,3,4,6],
 ['График офлайн-игр 2023 год','archive',0,1,-1,2,3,4],
 ['График офлайн-игр 2022 год','archive',0,1,-1,2,3,4],
 ['График офлайн-игр 2021 год','archive',0,1,-1,2,3,-1],
 ['График всех офлайн-игр 2020 год (после карантина)','archive',0,1,-1,3,4,-1],
 ['График игр Квиз, плиз! [стрим] Москва','special',0,2,-1,6,4,-1],
 ['Все тематические офлайн-игры Квиз, плиз!','special',0,1,-1,2,3,-1]
];
function doGet(){
 const ss=SpreadsheetApp.openById(SHEET_ID), rows=[];
 for(const [name,group,dateCol,nameCol,ratingCol,guideCol,noteCol,scoreCol] of SOURCES){
  const sheet=ss.getSheetByName(name);if(!sheet)continue;
  const data=sheet.getDataRange().getValues();
  for(let i=2;i<data.length;i++){
   const row=data[i], game=String(row[nameCol]||'').trim();
   if(!game||/^(название|аббревиатура|расписание на неделю)/i.test(game))continue;
   const value=c=>c<0?'':row[c];
   const date=value(dateCol) instanceof Date?Utilities.formatDate(value(dateCol),'Europe/Minsk','dd.MM.yyyy'):String(value(dateCol)||'');
   const guide=String(value(guideCol)||'').match(/https?:\/\/[^\s]+/);
   rows.push({group,date,name:game,rating:String(value(ratingCol)||''),score:String(value(scoreCol)||''),annotation:String(value(noteCol)||'').slice(0,400),guide:guide?guide[0]:''});
  }
 }
 return ContentService.createTextOutput(JSON.stringify({updatedAt:new Date().toISOString(),rows})).setMimeType(ContentService.MimeType.JSON);
}
