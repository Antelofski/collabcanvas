/* Instructor-only, task-scoped evidence and saved judgments. */
let knowledgeData=null,knowledgePerson='',knowledgeSnapshot='';
const knowledgeLabels={'demonstrated':'Demonstrated','needs-support':'Needs support','needs-check':'To review','not-observed':'No record'};
const knowledgeTeamsBase=teamModal;
teamModal=function(){knowledgeTeamsBase();const controls=$('#progressRules')?.parentElement;if(controls&&!$('#knowledgeReportButton')){const b=document.createElement('button');b.id='knowledgeReportButton';b.textContent='Knowledge state';b.onclick=()=>openKnowledgeReport();controls.prepend(b)}};
async function openKnowledgeReport(person,snapshot=''){
 progressScreen='knowledge';knowledgeSnapshot=snapshot;
 if(person)knowledgePerson=person;
 showModal(modalHead('Knowledge state','')+'<p role="status">Preparing task evidence…</p>','knowledge-modal');
 try{knowledgeData=await api('/api/host/knowledge-report'+(snapshot?'?snapshot='+encodeURIComponent(snapshot):''));drawKnowledgeReport()}catch(err){$('#overlay .modal').innerHTML=modalHead('Could not open report',err.message)}
}
function knowledgeEvidence(e){return '<article class="knowledge-evidence"><header>'+esc(e.source)+(e.scope==='review'?' · instructor observation':e.scope==='context'?' · task context':'')+'</header><p>'+esc(e.text)+'</p>'+(e.reason?'<p class="knowledge-reason">Reason: '+esc(e.reason)+'</p>':'')+'</article>'}
function knowledgeMapPeople(){return knowledgeData.learners.map(p=>{const needs=p.counts['needs-support'],review=p.counts['needs-check'],known=p.counts.demonstrated;return {id:p.person,name:cleanName(p.name),role:p.role,group:p.group,state:needs?'attention':review?'review':known?'recorded':'empty',stateLabel:needs?needs+' task'+(needs===1?' needs':'s need')+' support':review?review+' task'+(review===1?' needs':'s need')+' review':known?'Individual task evidence saved':'No individual record'}})}
function knowledgeTaskHTML(t,readOnly){
 const evidence=t.evidence.filter(e=>!t.review||e.scope!=='review');
 return '<details class="knowledge-task" data-knowledge-task="'+esc(t.id)+'"><summary><h3>'+esc(t.title)+'</h3><span class="knowledge-badge '+t.status+'">'+knowledgeLabels[t.status]+'</span></summary><div class="knowledge-task-detail">'+evidence.map(e=>'<blockquote><p>'+esc(e.text)+'</p>'+(e.reason?'<p class="knowledge-reason">'+esc(e.reason.replace(/^Example: /,''))+'</p>':'')+'</blockquote>').join('')+(!evidence.length?'<p>No saved answer.</p>':'')+(t.review?'<div class="knowledge-flat-note"><b>'+(t.reviewStale?'Review needs updating':'Teacher note')+'</b><p>'+esc(t.review.note)+'</p></div>':'')+'<div class="knowledge-flat-next"><b>Next</b><p>'+esc(t.nextCheck)+'</p></div>'+(!readOnly?'<button data-knowledge-review="'+esc(t.id)+'">Review</button>':'')+'</div></details>';
}
function drawKnowledgeReport(){
 const d=knowledgeData,person=d.learners.find(p=>p.person===knowledgePerson),people=knowledgeMapPeople(),groups=[...new Set(people.map(p=>p.group))].map(group=>({group,attention:people.filter(p=>p.group===group&&p.state==='attention').length,review:people.filter(p=>p.group===group&&p.state==='review').length,footer:''}));
 progressScreen='knowledge';
 const toolbar='<div class="knowledge-map-tools">'+(d.learners.some(p=>p.name.includes('(example)'))?'<span class="monitor-example">Example</span>':'')+(d.snapshots.length?'<select id="knowledgeSnapshot" aria-label="Report version">'+option('','Current',knowledgeSnapshot)+d.snapshots.slice().reverse().map(s=>option(s.id,new Date(s.created*1000).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}),knowledgeSnapshot)).join('')+'</select>':'')+'<button id="knowledgeDownload">Export</button><button id="knowledgeSave" class="primary" '+(d.readOnly?'disabled':'')+'>Save report</button></div>';
 const panel=person?'<aside class="knowledge-student classroom-inspect" id="knowledgeStudent"><header><div><h2>'+esc(cleanName(person.name))+'</h2><p>'+esc(person.role)+'</p></div><button id="knowledgeClose" aria-label="Close student record">'+icon('close')+'</button></header><div id="knowledgeTasks">'+person.tasks.map(t=>knowledgeTaskHTML(t,d.readOnly)).join('')+'</div></aside>':'<aside id="knowledgeStudent" hidden></aside>';
 showModal(modalHead('Class dashboard','')+'<div class="monitor-top">'+monitorNav('knowledge')+toolbar+'</div>'+classroomLegend(true)+'<div class="classroom-space knowledge-map-space '+(person?'with-inspector':'')+'">'+classroomMapHTML(people,groups,knowledgePerson,true)+panel+'</div><p id="knowledgeSaved" role="status">'+''+'</p>','knowledge-modal spatial-dashboard');
 monitorBindNav();$('#knowledgeReportButton').onclick=()=>{knowledgePerson='';drawKnowledgeReport()};
 $$('[data-knowledge-person]').forEach(b=>b.onclick=()=>{knowledgePerson=b.dataset.knowledgePerson;drawKnowledgeReport()});
 $$('[data-progress-team]').forEach(b=>b.onclick=()=>{const p=d.learners.find(p=>p.group===+b.dataset.progressTeam&&p.counts['needs-support'])||d.learners.find(p=>p.group===+b.dataset.progressTeam);knowledgePerson=p?.person||'';drawKnowledgeReport()});
 $('#knowledgeClose')?.addEventListener('click',()=>{knowledgePerson='';drawKnowledgeReport()});
 $$('[data-knowledge-review]').forEach(b=>b.onclick=()=>knowledgeReview(person.person,b.dataset.knowledgeReview));
 $('#knowledgeSnapshot')?.addEventListener('change',e=>openKnowledgeReport(knowledgePerson,e.target.value));
 $('#knowledgeDownload').onclick=downloadKnowledgeReport;
 $('#knowledgeSave').onclick=async()=>{const b=$('#knowledgeSave');b.disabled=true;try{const r=await api('/api/host/knowledge-snapshot',{});await openKnowledgeReport(knowledgePerson,r.snapshot.id)}catch(error){$('#knowledgeSaved').textContent=error.message;b.disabled=false}};
 if(person){const t=person.tasks.find(t=>t.status==='needs-support')||person.tasks.find(t=>t.review&&!t.reviewStale)||person.tasks[0];if(t)$('[data-knowledge-task="'+t.id+'"]').open=true}
}
function knowledgeReview(person,taskId){
 const p=knowledgeData.learners.find(p=>p.person===person),t=p.tasks.find(t=>t.id===taskId);
 showModal(modalHead('Review this task',p.name.replace(' (example)','')+' · '+t.title)+'<div class="knowledge-review-layout"><section><h3>Saved evidence</h3>'+t.evidence.filter(e=>!t.review||e.scope!=='review').map(knowledgeEvidence).join('')+(!t.evidence.length?'<p>No individual evidence is saved yet.</p>':'')+'</section><section><label>Task judgment<select id="knowledgeJudgment">'+Object.entries(knowledgeLabels).map(([v,label])=>option(v,label,t.status)).join('')+'</select></label><label>What did you verify?<textarea id="knowledgeNote" placeholder="Record what the learner showed on this task.">'+esc(t.review?.note||'')+'</textarea></label><label>What should be checked next?<textarea id="knowledgeNextCheck">'+esc(t.nextCheck)+'</textarea></label></section></div><p id="knowledgeReviewFeedback" role="status"></p><div class="progress-modal-actions"><button id="knowledgeReviewBack">Back to report</button><button id="knowledgeReviewSave" class="primary">Save judgment</button></div>','knowledge-review-modal');
 $('#knowledgeReviewBack').onclick=drawKnowledgeReport;$('#knowledgeReviewSave').onclick=async()=>{const b=$('#knowledgeReviewSave');b.disabled=true;try{await api('/api/host/knowledge-review',{person,task:taskId,evidenceKey:t.evidenceKey,version:t.review?.version||0,status:$('#knowledgeJudgment').value,note:$('#knowledgeNote').value,nextCheck:$('#knowledgeNextCheck').value});await openKnowledgeReport(person);const item=$('[data-knowledge-task="'+taskId+'"]');if(item)item.open=true;toast('Task judgment saved.')}catch(e){$('#knowledgeReviewFeedback').textContent=e.message;b.disabled=false}};
}
function downloadKnowledgeReport(){
 const d=knowledgeData,html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Knowledge state · '+esc(d.activity)+'</title><style>body{font:16px/1.6 system-ui;color:#25334a;max-width:1000px;margin:40px auto;padding:0 24px}h1{font-size:30px}section{margin:40px 0}article{padding:18px 0;border-top:1px solid #dde3ec}blockquote{border-left:3px solid #a8b9ce;padding-left:16px}small{color:#61738b}.badge{font-weight:650}button{padding:10px 16px}@media print{button{display:none}section{break-before:page}}</style><h1>Knowledge state</h1><p>'+esc(d.activity)+'</p><p>'+esc(d.basis)+'</p><button onclick="print()">Print / Save PDF</button>'+d.learners.map(p=>'<section><h2>'+esc(p.name)+' · Team '+(p.group+1)+'</h2><small>'+esc(p.role)+'</small>'+p.tasks.map(t=>'<article><h3>'+esc(t.title)+'</h3><span class="badge">'+esc(t.statusLabel)+'</span><p>'+esc(t.knowledge)+'</p>'+t.evidence.map(e=>'<blockquote><small>'+esc(e.source)+'</small><p>'+esc(e.text)+'</p>'+(e.reason?'<p>Reason: '+esc(e.reason)+'</p>':'')+'</blockquote>').join('')+(t.review?'<p><b>Teacher judgment:</b> '+esc(t.review.note)+'</p>':'')+'<p><b>Next check:</b> '+esc(t.nextCheck)+'</p></article>').join('')+'</section>').join('')+'</html>';
 const url=URL.createObjectURL(new Blob([html],{type:'text/html'})),a=document.createElement('a');a.href=url;a.download='CollabCanvas-Knowledge-State.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);toast('Report downloaded.');
}
const knowledgePlainExport=downloadKnowledgeReport;
downloadKnowledgeReport=async function(){
 const report=clone(knowledgeData),button=$('#knowledgeDownload');button.disabled=true;
 try{const response=await fetch('/knowledge-report-template.html');if(!response.ok)throw Error('Report layout unavailable');const template=await response.text();
  const payload=JSON.stringify(report).replaceAll('<','\\u003c'),html=template.replace('"__COLLABCANVAS_REPORT__"',payload);
  const url=URL.createObjectURL(new Blob([html],{type:'text/html'})),a=document.createElement('a');a.href=url;a.download='CollabCanvas-Knowledge-Report.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);toast('Report downloaded.');
 }catch(error){knowledgePlainExport()}finally{if(button.isConnected)button.disabled=false}
};

if(new URLSearchParams(location.search).get('demo')==='knowledge'){let tries=0;const launch=setInterval(()=>{if(data?.progress){clearInterval(launch);openKnowledgeReport()}else if(++tries>100)clearInterval(launch)},150)}
