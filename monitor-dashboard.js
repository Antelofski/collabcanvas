/* One classroom view for progress, scoped changes and subsequent work. */
let monitorView='progress',monitorTeam=null,monitorRule='',monitorChange='',monitorSeen=0,monitorPerson='';
const monitorLegacyTeams=teamModal,monitorLegacyDetail=teamDetail,monitorLegacyReview=adaptiveReview;
const monitorShort={'role-work':'Contribution','peer-use':'Peer response','answer-pattern':'Reasoning check'};
const cleanName=n=>(n||'Learner').replace(' (example)','');
function monitorChecks(e){
 return (e.signals||[]).map(s=>{const c={...s,...(e.collaboration?.[s.id]||{}),id:s.id,title:frameworkRuleNames[s.id]||s.title};if(c.id==='answer-pattern'&&e.answered===e.total&&e.total>1&&new Set(e.rows.map(r=>r.initial?.answer)).size>1){c.status='inactive';c.observed='Initial answers differ; this conditional rule is not triggered.'}return c});
}
function monitorStatus(c){
 if(c.change?.reviewed)return ['reviewed','Reviewed'];
 if(c.change){const rows=Object.values(c.change.responses||{});return rows.some(r=>r.shared)?['review','Ready to review']:['pending','Awaiting work']}
 if(c.status==='inactive')return ['collecting','Not triggered'];
 return c.status==='attention'?['attention','Needs attention']:c.status==='checked'?['checked','Check recorded']:['collecting','Collecting'];
}
function monitorNav(active){return '<nav class="monitor-tabs" aria-label="Dashboard views"><button data-monitor-view="progress" class="'+(active==='progress'?'active':'')+'">Progress</button><button data-monitor-view="followup" class="'+(active==='followup'?'active':'')+'">Follow-up</button><button id="knowledgeReportButton" class="'+(active==='knowledge'?'active':'')+'">Knowledge</button></nav>'}
function monitorBindNav(){
 $$('[data-monitor-view]').forEach(b=>b.onclick=()=>{monitorView=b.dataset.monitorView;monitorTeam=null;monitorRule='';monitorChange='';monitorPerson='';drawMonitor()});
 $('#knowledgeReportButton').onclick=()=>openKnowledgeReport();
}
function monitorShell(content){
 const p=currentProgress(),example=p.teams.some(e=>e.rows.some(r=>/\(example\)/.test(r.name)));
 const tools='<details class="monitor-tools"><summary aria-label="Dashboard options">'+'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="19" cy="12" r="1.5"/></svg>'+'</summary><div><button id="progressRules">Progress rules</button><button id="progressDrafts">Saved drafts</button><label>Data<select id="monitorSource" aria-label="Data source">'+option('class','Class work',progressPreview?'rehearsal':'class')+option('rehearsal','Rehearsal',progressPreview?'rehearsal':'class')+'</select></label></div></details>';
 showModal(modalHead('Class dashboard','')+'<div class="monitor-top">'+monitorNav(monitorView)+'<div class="monitor-source">'+(example?'<span class="monitor-example">Example</span>':'')+'<button id="progressRefresh" aria-label="Refresh dashboard"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 7v5h-5M20 12a8 8 0 1 0-2 5M20 7v5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button>'+tools+'</div></div><main class="monitor-main" id="monitorMain">'+content+'</main>','monitor-modal spatial-dashboard');
 monitorSeen=data.rev;progressScreen=monitorTeam===null?'teams':'detail';progressGroup=monitorTeam??0;
 monitorBindNav();$('#progressRules').onclick=progressRulesModal;$('#progressDrafts').onclick=savedProgressDrafts;
 $('#monitorSource').onchange=e=>{progressPreview=e.target.value==='rehearsal';monitorRule='';monitorChange='';monitorPerson='';drawMonitor()};
 $('#progressRefresh').onclick=async()=>{await reload(true);drawMonitor()};
}
function monitorMapPeople(){
 const phases=data.plan.phases.filter(p=>p.kind==='individual'),records=(progressPreview?data.studio?.previewResponses:data.studio?.responses)||{};
 return activePeople().map(p=>{const e=currentProgress().teams.find(e=>e.group===p.group),checks=monitorChecks(e),task=data.plan.tasks.find(t=>t.assignees.includes(p.slot));
  const submitted=phases.length&&phases.every(phase=>records[p.id]?.[phase.id+':submitted']);
  let state=submitted?'recorded':'empty',stateLabel=submitted?'Role work shared':'No shared role work';
  const own=checks.find(c=>c.id==='role-work'&&c.status==='attention'&&c.targets?.includes(p.id));
  if(own){state='attention';stateLabel='Contribution needs attention'}
  if(checks.some(c=>c.id==='reading-check'&&c.status==='attention')&&e.rows.find(r=>r.person===p.id)?.initial?.correct===false){state='attention';stateLabel='Individual check needs review'}
  for(const c of checks.filter(c=>c.change?.targets.includes(p.id))){const change=c.change;if(change.reviewed){state=submitted?'recorded':state;stateLabel=submitted?'Role work shared; support reviewed':'Support reviewed'}else{state=change.responses?.[p.id]?.shared?'review':own?'attention':'review';stateLabel=change.responses?.[p.id]?.shared?'New work to review':'Support assigned; awaiting work'}}
  return {id:p.id,name:cleanName(p.name||'Learner '+String.fromCharCode(65+p.slot)),role:task?.title||'Learner',group:p.group,state,stateLabel,submitted};
 });
}
function monitorPersonPanel(person){
 const e=currentProgress().teams.find(e=>e.group===person.group),p=activePeople().find(p=>p.id===person.id),checks=monitorChecks(e),a=(progressPreview?data.studio?.previewArtifacts:data.studio?.artifacts)?.[p.id]||{},request=e.adaptive?.requests?.find(r=>r.person===p.id),support=checks.find(c=>c.id==='role-work');
 const saved=[...(a.observations||[]).map(r=>r.text),...(a.beats||[]).map(r=>r.text),...(a.checks||[]).map(r=>r.statement),a.reflection].filter(Boolean).slice(0,2);
 return '<aside class="classroom-inspect" id="classroomPerson"><header><div><h2>'+esc(person.name)+'</h2><p>'+esc(person.role)+'</p></div><button id="monitorPersonClose" aria-label="Close student details">'+icon('close')+'</button></header><div class="classroom-person-state"><i class="classroom-symbol '+person.state+'" aria-hidden="true">'+classroomSymbols[person.state]+'</i>'+esc(person.stateLabel)+'</div>'+(request?'<blockquote>'+esc(request.text)+'</blockquote>':'')+saved.map(text=>'<p class="classroom-saved-text">'+esc(text)+'</p>').join('')+(request&&!support?.change?'<button id="monitorPersonSupport" class="primary">Preview smaller steps</button>':'')+'<button id="monitorPersonOpen">Open interface</button><div class="classroom-person-rules">'+checks.map(c=>'<button data-monitor-issue="'+p.group+':'+c.id+'"><span>'+esc(monitorShort[c.id]||c.title)+'</span><i class="monitor-dot '+monitorStatus(c)[0]+'" aria-label="'+monitorStatus(c)[1]+'"></i></button>').join('')+'</div></aside>';
}
function monitorOverview(){
 const people=monitorMapPeople(),groups=currentProgress().teams.map(e=>({group:e.group,attention:monitorChecks(e).filter(c=>monitorStatus(c)[0]==='attention').length,review:monitorChecks(e).filter(c=>monitorStatus(c)[0]==='review').length,footer:'<span>'+e.submitted+' / '+e.total+' shared</span>'})),selected=people.find(p=>p.id===monitorPerson);
 return classroomLegend()+'<div class="classroom-space '+(selected?'with-inspector':'')+'">'+classroomMapHTML(people,groups,monitorPerson)+(selected?monitorPersonPanel(selected):'')+'</div>';
}
function monitorEvidence(e,c){
 if(c.id==='role-work')return (c.names||[]).map(n=>'<div class="monitor-evidence-record"><b>'+esc(cleanName(n))+'</b><p>No saved role contribution at the checkpoint.</p></div>').join('')+(c.requests||[]).map(text=>'<blockquote>'+esc(text)+'</blockquote>').join('');
 if(c.id==='peer-use')return c.question?'<div class="monitor-evidence-record"><b>'+esc(cleanName(c.question.name))+' asked</b><blockquote>'+esc(c.question.text)+'</blockquote>'+(c.linked||[]).map(r=>'<p><b>Linked response</b> '+esc(r.values.idea)+'</p>').join('')+'</div>':'';
 if(c.id==='answer-pattern')return '<div class="monitor-evidence-record"><b>'+e.rows.map(r=>esc(cleanName(r.name))).join(' · ')+'</b><blockquote>'+esc(frameworkChoice(e.rows[0]?.initial?.answer))+'</blockquote><p>Matching answers trigger a check of reasons, not an error judgment.</p></div>';
 if(c.id==='reading-check')return frameworkReadingEvidence(e);
 return '<div class="monitor-evidence-record"><p>'+esc(c.detail||c.evidence||'Inspect the saved work or record an observation.')+'</p></div>';
}
function monitorDetail(e,c){
 const [state,label]=monitorStatus(c),change=c.change,story=c.pattern?interfaceChangeStory(c.pattern):null;
 const tabs=monitorChecks(e).map(x=>'<button data-monitor-rule="'+x.id+'" class="'+(c.id===x.id?'active':'')+'"><i class="monitor-dot '+monitorStatus(x)[0]+'"></i>'+esc(monitorShort[x.id]||x.title)+'</button>').join('');
 return '<header class="monitor-heading"><div><button class="monitor-back" id="monitorBack">← Classroom</button><h2 id="frameworkRuleTitle">'+'Team '+(e.group+1)+' · '+esc(monitorShort[c.id]||c.title)+'</h2></div><span class="monitor-status framework-state '+state+'">'+label+'</span></header><nav class="monitor-rule-nav">'+tabs+'</nav><section id="adaptiveTeam"><div class="monitor-evidence-grid"><article id="frameworkRuleExpected"><h3>Expected</h3><p>'+esc(c.expected||c.expectation||'Review the selected rule with this team.')+'</p></article><article id="frameworkRuleObserved" class="monitor-observed"><h3>Observed</h3><p class="monitor-observation">'+esc(c.observed||c.detail||'Waiting for evidence.')+'</p>'+monitorEvidence(e,c)+'</article></div>'+(story?'<section class="monitor-proposal"><div><span>'+(change?'APPLIED CHANGE':'PROPOSED CHANGE')+'</span><h3>'+esc(story.title)+'</h3><p>'+esc(story.change)+'</p></div><div class="monitor-proposal-why"><b>How this responds</b><p>'+esc(story.why)+'</p>'+(change?'<button class="primary" id="collabReview">Review subsequent work</button><button id="frameworkInspect">Open updated interface</button>':'<button class="primary" id="frameworkSuggested">Preview change</button>')+'</div></section>':'<button id="monitorObserve">Record observation</button>')+'<div class="monitor-detail-actions"><button id="frameworkMessage">Send a question</button><button id="monitorKeep">Keep current activity</button><div><button id="progressNext">Save for next activity</button><button id="progressNextRun">Save for next run</button></div></div></section>';
}
function monitorFollowup(){
 const teams=currentProgress().teams.filter(e=>monitorTeam===null||e.group===monitorTeam),changes=teams.flatMap(e=>(e.adaptive?.changes||[]).map(c=>({e,c})));let selected=changes.find(({c})=>c.id===monitorChange);
 if(!selected&&changes.length===1)selected=changes[0];
 if(!selected)return '<header class="monitor-heading"><div><h2>Subsequent work</h2></div></header><div class="monitor-followup-list">'+(changes.length?changes.map(({e,c})=>'<button data-monitor-change="'+e.group+':'+c.id+'"><span>Team '+(e.group+1)+'</span><strong>'+esc(interfaceChangeStory(c.pattern).title)+'</strong><p>'+Object.values(c.responses||{}).filter(r=>r.shared).length+' shared contributions</p><b>'+ (c.reviewed?'Review recorded':'Open work →')+'</b></button>').join(''):'<div class="monitor-empty"><h3>No interface changes yet.</h3><p>After a change is applied, the resulting student work appears here.</p><button data-monitor-view="progress">View progress</button></div>')+'</div>';
 const {e,c}=selected,people=activePeople().filter(p=>p.group===e.group),story=interfaceChangeStory(c.pattern);monitorChange=c.id;
 const responses=c.targets.filter(pid=>c.responses?.[pid]),waiting=c.targets.length-responses.length;
 return '<header class="monitor-heading"><div><button class="monitor-back" id="monitorFollowupBack">← All subsequent work</button><h2>Team '+(e.group+1)+' · '+esc(story.title)+'</h2></div><span class="monitor-status '+(c.reviewed?'reviewed':'review')+'">'+(c.reviewed?'Reviewed':'Review the work')+'</span></header><div class="monitor-review-context"><b>Interface change</b><p>'+esc(story.change)+'</p></div><div class="monitor-review-grid"><section class="adaptive-review-work">'+responses.map(pid=>{const p=people.find(p=>p.id===pid),r=c.responses[pid];return '<article class="monitor-work-record"><header><strong>'+esc(cleanName(p?.name))+'</strong><span>'+esc(comparisonRole(p))+'</span></header>'+c.spec.fields.filter(([key])=>r.values[key]).map(([key,label])=>'<div><b>'+esc(label)+'</b><p>'+esc(r.values[key])+'</p></div>').join('')+(r.reply?'<div class="monitor-linked-reply"><b>Peer response'+(r.replyTo?' to '+esc(cleanName(people.find(p=>p.id===r.replyTo)?.name)):'')+'</b><p>'+esc(r.reply)+'</p></div>':'')+'</article>'}).join('')+(!responses.length?'<div class="monitor-empty"><h3>Waiting for student work.</h3><p>The interface change alone does not close this issue.</p></div>':'')+(waiting?'<p class="monitor-waiting">'+waiting+' assigned learner'+(waiting===1?' has':'s have')+' no saved response yet.</p>':'')+'</section><aside class="monitor-review-decision"><h3>Teacher review</h3><p>'+esc(story.recheck)+'</p><label for="adaptiveReviewNote">What did you verify?</label><textarea id="adaptiveReviewNote" '+(c.reviewed?'disabled':'')+' placeholder="Record what the work shows and what still needs checking.">'+esc(c.reviewNote||'')+'</textarea><p id="adaptiveReviewFeedback" role="status"></p>'+(!c.reviewed?'<button id="adaptiveReviewSave" class="primary">Record review</button>':'')+'<button id="frameworkInspect">Open updated interface</button></aside></div>';
}
function drawMonitor(){
 if(!currentProgress())return monitorLegacyTeams();
 const e=currentProgress().teams.find(e=>e.group===monitorTeam),c=e&&monitorChecks(e).find(c=>c.id===monitorRule);
 monitorShell(monitorView==='followup'?monitorFollowup():c?monitorDetail(e,c):monitorOverview());
 $$('[data-progress-team]').forEach(b=>b.onclick=()=>teamDetail(+b.dataset.progressTeam));
 $$('[data-map-person]').forEach(b=>b.onclick=()=>{monitorPerson=b.dataset.mapPerson;drawMonitor()});
 $('#monitorPersonClose')?.addEventListener('click',()=>{monitorPerson='';drawMonitor()});
 $('#monitorPersonOpen')?.addEventListener('click',()=>frameworkInspect(activePeople().find(p=>p.id===monitorPerson).group,monitorPerson));
 $('#monitorPersonSupport')?.addEventListener('click',()=>{const p=activePeople().find(p=>p.id===monitorPerson);adaptivePreview(p.group,'scaffold',[p.id])});
 $$('[data-monitor-issue]').forEach(b=>b.onclick=()=>{const [g,id]=b.dataset.monitorIssue.split(':');teamDetail(+g,id)});
 $$('[data-monitor-rule]').forEach(b=>b.onclick=()=>{monitorRule=b.dataset.monitorRule;drawMonitor()});
 $('#monitorBack')?.addEventListener('click',()=>{monitorTeam=null;monitorRule='';monitorPerson='';drawMonitor()});
 if(c){
  $('#frameworkSuggested')?.addEventListener('click',()=>adaptivePreview(e.group,c.pattern,c.targets,(c.observed||'')+' '+(c.why||'')));
  $('#frameworkInspect')?.addEventListener('click',()=>frameworkInspect(e.group,c.change.targets[0]));
  $('#collabReview')?.addEventListener('click',()=>adaptiveReview(e.group,c.change.id));
  $('#frameworkMessage')?.addEventListener('click',()=>frameworkMessage(e.group));$('#monitorKeep')?.addEventListener('click',()=>adaptiveKeep(e.group));
  $('#monitorObserve')?.addEventListener('click',()=>ruleObservation(e.group,c.id));
  $('#progressNext')?.addEventListener('click',()=>prepareProgressDraft('next-activity',e.group));$('#progressNextRun')?.addEventListener('click',()=>prepareProgressDraft('next-run',e.group));
 }
 $$('[data-monitor-change]').forEach(b=>b.onclick=()=>{const [g,id]=b.dataset.monitorChange.split(':');adaptiveReview(+g,id)});
 $('#monitorFollowupBack')?.addEventListener('click',()=>{monitorTeam=null;monitorChange='';drawMonitor()});
 if(monitorView==='followup'&&monitorChange){const team=currentProgress().teams.find(e=>(e.adaptive?.changes||[]).some(c=>c.id===monitorChange)),change=team?.adaptive.changes.find(c=>c.id===monitorChange);if(change){
  $('#frameworkInspect')?.addEventListener('click',()=>frameworkInspect(team.group,change.targets[0]));
  $('#adaptiveReviewSave')?.addEventListener('click',async()=>{const button=$('#adaptiveReviewSave');button.disabled=true;try{await api('/api/host/adaptive-review',{group:team.group,id:change.id,note:$('#adaptiveReviewNote').value});await reload(true);drawMonitor();toast('Review recorded. Student work is preserved.')}catch(error){$('#adaptiveReviewFeedback').textContent=error.message;button.disabled=false}});
 }}
}
teamModal=function(){if(fullActivityTour)return monitorLegacyTeams();monitorView='progress';monitorTeam=null;monitorRule='';monitorChange='';monitorPerson='';drawMonitor()};
teamDetail=function(group,id){if(fullActivityTour)return monitorLegacyDetail(group,id);monitorView='progress';monitorTeam=group;const e=currentProgress()?.teams.find(e=>e.group===group),checks=e?monitorChecks(e):[];monitorRule=id||checks.find(c=>monitorStatus(c)[0]==='attention')?.id||checks.find(c=>c.change)?.id||checks[0]?.id||'';drawMonitor()};
adaptiveReview=function(group,id){if(fullActivityTour)return monitorLegacyReview(group,id);monitorView='followup';monitorTeam=group;monitorRule='';monitorChange=id;drawMonitor()};
setInterval(()=>{if(!$('#overlay .monitor-modal')||monitorSeen===data?.rev||document.activeElement?.matches('textarea,input,select'))return;const scroll=$('#monitorMain')?.scrollTop;drawMonitor();if($('#monitorMain'))$('#monitorMain').scrollTop=scroll},1800);
