/* Shared discussion → role work → shared critique, with saved handoffs. */
let groupDrafts={},selectedContribution='author',workflowOpeningShown=false;
function studioDisplayPhases(){
 if(preview&&params.get('forceFlow')==='group-first'){
  const n=data.plan.budget,a=Math.max(1,Math.round(n*2/9)),b=Math.max(1,Math.round(n*4/9));
  return [{id:'read',title:'Discuss together',kind:'discussion',purpose:'opening',minutes:a},{id:'discuss',title:'Work by role',kind:'individual',purpose:'rolework',minutes:b},{id:'revise',title:'Write together',kind:'revision',purpose:'critique',minutes:n-a-b}];
 }
 return data.plan.phases;
}
const workflowBaseStage=stage;
stage=function(){const s=workflowBaseStage();return studioDisplayPhases().find(p=>p.id===s.id)||s};
function workflowRoleTool(){const role=studioRole();return role==='author'?authorBuilder():role==='reader'?readerLog():role==='checker'?checkerWorkbench():role==='host'?hostWorkbench():editorPrepare()}
function groupDraft(section){
 const fresh=data.studioGroup?.[section]||{version:0};
 if(!groupDrafts[section]||!groupDrafts[section]._dirty&&fresh.version>(groupDrafts[section].version||0))groupDrafts[section]={...fresh};
 return groupDrafts[section];
}
function initialReadingContext(){const value=data.studioGroup?.opening?.text;return '<aside class="workflow-start-context"><span>YOUR GROUP’S STARTING READING</span><p>'+esc(value||'Your group has not saved a starting reading yet.')+'</p>'+(!value?'<button id="goToOpening" class="studio-secondary">Open the group discussion</button>':'')+'</aside>'}
function openingDiscussion(){
 const draft=groupDraft('opening'),task=assignedTasks()[0];
 return '<section class="studio-work workflow-opening" data-region="opening-discussion">'+regionHead('Start with one group reading','opening-discussion')+'<div class="workflow-group-badge">Group '+(data.person.group+1)+' · shared discussion</div><p class="studio-section-copy">Compare the first and last frames. What changes in the map, and who is still included?</p><label class="studio-full-label">Our initial reading<textarea id="initialReading" data-group-field="text" data-group-section="opening" placeholder="Record one interpretation your group wants to check.">'+esc(draft.text||'')+'</textarea></label><div class="studio-action-row"><span id="groupSaveState">'+(draft.updated?'Shared reading saved':'One shared response')+'</span><button id="saveInitialReading" class="studio-primary">Save group reading</button></div><button id="reloadSharedOpening" class="workflow-reload" hidden>Reload the shared copy</button><div class="workflow-next-role"><span>NEXT · YOUR ROLE</span><strong>'+esc(task?.title||roleName())+'</strong><p>'+esc(task?.prompt||'Bring your perspective back to the group.')+'</p></div></section>';
}
function checkerWorkbench(){
 const checks=studioDoc.checks||[];
 return '<section class="studio-work" data-region="evidence-checks">'+regionHead('Check what the map supports','evidence-checks')+'<p class="studio-section-copy">Check a statement against the units, labels, and population groups.</p><div class="workflow-check-composer"><label>Statement to check<textarea id="evidenceStatement" aria-label="Statement to check" placeholder="What claim needs checking?"></textarea></label><div class="workflow-check-row"><label>Check against<select id="evidenceFrame">'+frameOptions(studioSourceIndex)+'</select></label><label>Your judgment<select id="evidenceStatus"><option value="supported">Supported</option><option value="correct">Needs correction</option><option value="notshown">Not shown</option></select></label></div><label>Explain the check<textarea id="evidenceReason" aria-label="Explain the check" placeholder="Use the frame’s unit or label to explain your judgment."></textarea></label><button id="addEvidenceCheck" class="studio-secondary">Add evidence check</button></div><div class="workflow-evidence-list">'+checks.map(c=>'<article><div><button data-jump-frame="'+c.frame+'">FRAME '+(c.frame+1)+'</button><span>'+esc({supported:'Supported',correct:'Needs correction',notshown:'Not shown'}[c.status])+'</span><button data-remove-check="'+esc(c.id)+'" aria-label="Remove evidence check">×</button></div><h3>'+esc(c.statement)+'</h3><p>'+esc(c.reason)+'</p></article>').join('')+'</div>'+studioAction(studioDoc.submitted[stage().id]?'Update evidence checks':'Share evidence checks')+'</section>';
}
function hostWorkbench(){return '<section class="studio-work" data-region="discussion-host">'+regionHead('Connect the group’s readings','discussion-host')+'<p class="studio-section-copy">Prepare one question that connects two interpretations. Keep an unresolved point visible.</p><label>Discussion question<textarea data-studio-field="reflection" aria-label="Discussion host question">'+esc(studioDoc.reflection||'')+'</textarea></label>'+studioAction('Share discussion question')+'</section>'}
function contributionMarkup(role){
 const a=studioRole()===role?studioDoc:studioWork(role);
 if(role==='author')return (a.beats||[]).filter(x=>x.text?.trim()||x.reason?.trim()).map(x=>'<article><span>FRAME '+(x.frame+1)+'</span><p><b>'+esc(x.text)+'</b></p><p>'+esc(x.reason)+'</p></article>').join('');
 if(role==='reader')return (a.observations||[]).map(x=>'<article><span>FRAME '+(x.frame+1)+' · '+esc(x.kind)+'</span><p>'+esc(x.text)+'</p></article>').join('');
 if(role==='checker')return (a.checks||[]).map(x=>'<article><span>FRAME '+(x.frame+1)+' · '+esc({supported:'Supported',correct:'Needs correction',notshown:'Not shown'}[x.status])+'</span><p><b>'+esc(x.statement)+'</b></p><p>'+esc(x.reason)+'</p></article>').join('');
 return '<article><span>'+(role==='host'?'DISCUSSION QUESTION':'EDITORIAL ASSESSMENT')+'</span><p>'+esc(a.reflection||a.decision?.keep||'No assessment shared yet.')+'</p><p>'+esc((a.criteria||[]).join(' · '))+'</p></article>';
}
function collectiveCritique(){
 if(!data.groupRolesReady)return '<section class="studio-work workflow-wait" data-region="shared-critique">'+regionHead('Bring every contribution together','shared-critique')+'<p class="studio-section-copy">Everyone needs to share their role work before the team’s findings open here.</p><button id="goToRoleWork" class="studio-secondary">Return to role work</button></section>';
 const draft=groupDraft('critique'),roles=data.plan.tasks.map(t=>({id:t.roleId,title:t.title})).filter((x,i,a)=>a.findIndex(y=>y.id===x.id)===i);
 if(!roles.some(r=>r.id===selectedContribution))selectedContribution=roles[0].id;
 return '<section class="studio-work workflow-critique" data-region="shared-critique">'+regionHead('Write one shared critique','shared-critique')+'<p class="studio-section-copy">Use each role’s findings to agree on what the story shows and what needs work.</p><div class="workflow-contribution-tabs" aria-label="Role contributions">'+roles.map(r=>'<button data-contribution="'+r.id+'" aria-pressed="'+(r.id===selectedContribution)+'">'+esc(r.title)+'</button>').join('')+'</div><div class="workflow-contribution-content">'+contributionMarkup(selectedContribution)+'</div><div class="workflow-shared-fields">'+[['message','What does the story show?'],['misreading','What could readers misread?'],['change','What would you change?']].map(([k,label])=>'<label>'+label+'<textarea data-group-field="'+k+'" data-group-section="critique" aria-label="'+label+'">'+esc(draft[k]||'')+'</textarea></label>').join('')+'</div><div class="studio-action-row"><span id="groupSaveState">'+(draft.updated?'Shared critique saved':'One response for your group')+'</span><button id="saveSharedCritique" class="studio-primary">Save shared critique</button></div><button id="reloadSharedCritique" class="workflow-reload" hidden>Reload the shared copy</button></section>';
}
async function saveWorkflowGroup(section){
 const draft=groupDraft(section),button=$(section==='opening'?'#saveInitialReading':'#saveSharedCritique');
 if(preview&&(params.has('forceFlow')||params.has('forceReview')||params.has('forceExchange'))){notice('Preview only · this does not change the class.');return}
 button.disabled=true;
 try{const result=await api('/api/studio/group',{section,phaseId:stage().id,version:draft.version||0,record:draft});groupDrafts[section]={...result.record};data.studioGroup??={};data.studioGroup[section]=result.record;notice(section==='opening'?'Your group reading is saved for the role tasks.':'Shared critique saved for your group.');render()}
 catch(e){notice(e.message);$(section==='opening'?'#reloadSharedOpening':'#reloadSharedCritique').hidden=false}
 finally{if(button.isConnected)button.disabled=false}
}
const workflowOriginalBind=bindStudio;
bindStudio=function(){
 workflowOriginalBind();
 document.querySelectorAll('[data-group-field]').forEach(el=>el.oninput=()=>{const d=groupDraft(el.dataset.groupSection);d[el.dataset.groupField]=el.value;d._dirty=true;$('#groupSaveState').textContent='Unsaved group response'});
 $('#saveInitialReading')?.addEventListener('click',()=>saveWorkflowGroup('opening'));$('#saveSharedCritique')?.addEventListener('click',()=>saveWorkflowGroup('critique'));
 for(const [id,section] of [['reloadSharedOpening','opening'],['reloadSharedCritique','critique']])$('#'+id)?.addEventListener('click',async()=>{delete groupDrafts[section];await refresh(true);render()});
 const jump=id=>{if(preview)previewPhase=id;else selfPhase=id;render()};$('#goToOpening')?.addEventListener('click',()=>jump('read'));$('#goToRoleWork')?.addEventListener('click',()=>jump('discuss'));
 $('#addEvidenceCheck')?.addEventListener('click',()=>{const statement=$('#evidenceStatement').value.trim(),reason=$('#evidenceReason').value.trim();if(!statement||!reason)return notice('Write the statement and explain your check.');studioDoc.checks??=[];studioDoc.checks.push({id:'check-'+Date.now(),frame:+$('#evidenceFrame').value,status:$('#evidenceStatus').value,statement,reason});$('#evidenceStatement').value='';$('#evidenceReason').value='';studioPersist();render()});
 document.querySelectorAll('[data-remove-check]').forEach(b=>b.onclick=()=>{studioDoc.checks=studioDoc.checks.filter(c=>c.id!==b.dataset.removeCheck);studioPersist();render()});
 document.querySelectorAll('[data-contribution]').forEach(b=>b.onclick=()=>{selectedContribution=b.dataset.contribution;render()});
};

// Startup is owned by progress-student.js.
