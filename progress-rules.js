/* Teacher-authored checks. Only implemented signals run automatically. */
let ruleDraft=[],ruleSelected='',ruleReturn='canvas';
function rulePhaseName(id){return data.plan.phases.find(p=>p.id===id)?.title||id}
function ruleCollect(){
 const r=ruleDraft.find(r=>r.id===ruleSelected);if(!r)return;
 $$('[data-rule-field]').forEach(el=>{r[el.dataset.ruleField]=el.type==='number'?+el.value:el.value});
}
progressRulesModal=function(){
 if(!data.progress)return toast('This pilot supports progress rules for the voting-story role play.');
 ruleReturn=progressScreen==='teams'||progressScreen==='detail'?'teams':'canvas';progressScreen='rules';
 ruleDraft=clone(data.progress.rules);for(const suggestion of data.progress.suggestions||[])if(!ruleDraft.some(r=>r.id===suggestion.id))ruleDraft.push({...clone(suggestion),enabled:false});ruleSelected=ruleDraft.find(r=>r.enabled)?.id||ruleDraft[0]?.id;
 drawRulePlanner();
};
function drawRulePlanner(){
 showModal(modalHead('Progress rules','')+
 '<div class="rule-planner-top"><div><span class="progress-kicker">BASED ON THIS ACTIVITY</span><p>'+esc(data.plan.structure)+' · '+data.plan.groupSize+' roles · '+data.plan.phases.length+' stages</p></div><button id="ruleSuggest">Refresh suggestions</button></div>'+
 '<div class="rule-planner"><aside class="rule-list"><h3>Suggested checks</h3><div class="rule-list-options">'+ruleDraft.map(r=>'<div class="rule-list-row '+(ruleSelected===r.id?'selected':'')+'"><input type="checkbox" data-rule-enabled="'+esc(r.id)+'" aria-label="Enable '+esc(r.title)+'" '+(r.enabled?'checked':'')+'><button data-rule-select="'+esc(r.id)+'"><strong>'+esc(r.title)+'</strong></button></div>').join('')+'</div><button id="ruleAdd" class="rule-add">+ Write my own rule</button></aside><section id="ruleEditor" class="rule-editor"></section></div>'+
 '<div class="rule-planner-footer"><p id="ruleFeedback" role="status"></p><details><summary>About these suggestions</summary><p>Prepared checks derived from instructor feedback and common collaboration concerns: participation, individual understanding, role clarity, workload, conflict and feedback quality. <a href="https://en.wikipedia.org/wiki/Cooperative_learning#Limitations_and_problems" target="_blank" rel="noopener">Background</a>. Automatic signals and teacher observations are distinguished. Free text does not program a detector.</p></details></div><div class="progress-modal-actions"><button id="ruleCancel">Cancel</button><button id="progressRulesSave" class="primary">Save rules & update interfaces</button></div>','progress-rules-modal rule-planner-modal');
 $$('[data-rule-select]').forEach(b=>b.onclick=()=>{ruleCollect();ruleSelected=b.dataset.ruleSelect;drawRulePlanner()});
 $$('[data-rule-enabled]').forEach(c=>c.onchange=()=>{ruleDraft.find(r=>r.id===c.dataset.ruleEnabled).enabled=c.checked;drawRuleCount()});
 $('#ruleAdd').onclick=()=>{ruleCollect();const id='custom-'+Date.now().toString(36);ruleDraft.push({id,origin:'custom',enabled:true,title:'My progress rule',condition:'teacher_review',phaseId:data.plan.phases.at(-1).id,expectation:'',evidence:'',response:'',remainingMinutes:0});ruleSelected=id;drawRulePlanner();$('#ruleTitle').focus()};
 $('#ruleSuggest').onclick=async()=>{ruleCollect();const b=$('#ruleSuggest');b.disabled=true;b.textContent='Checking activity…';try{const result=await api('/api/host/progress-analyze',{});if(result.planRev!==data.planRev)throw Error('The plan changed. Reopen Progress rules to use the latest stages.');for(const r of result.rules)if(!ruleDraft.some(x=>x.id===r.id))ruleDraft.push(r);drawRulePlanner();$('#ruleFeedback').textContent='Suggestions refreshed. Your selections and edits are kept.'}catch(e){$('#ruleFeedback').textContent=e.message;b.disabled=false;b.textContent='Refresh suggestions'}};
 $('#ruleCancel').onclick=()=>ruleReturn==='teams'?teamModal():closeModal();
 $('#progressRulesSave').onclick=saveRulePlanner;drawRuleEditor();drawRuleCount();
 const selected=$('[data-rule-select="'+ruleSelected+'"]')?.closest('.rule-list-row'),list=$('.rule-list-options');if(selected&&list)list.scrollTop+=selected.getBoundingClientRect().top-list.getBoundingClientRect().top-10;
}
function drawRuleCount(){const n=ruleDraft.filter(r=>r.enabled).length;$('#progressRulesSave').textContent='Save '+n+' rule'+(n===1?'':'s')}
function drawRuleEditor(){
 const r=ruleDraft.find(r=>r.id===ruleSelected);if(!r)return;
 const manual=r.condition==='teacher_review',phases=r.condition==='submission'?data.plan.phases.filter(p=>p.kind==='individual'):data.plan.phases;
 $('#ruleEditor').innerHTML='<span class="progress-kicker">'+(manual?'TEACHER CHECK':'OBSERVABLE SIGNAL')+'</span><label>Rule name<input id="ruleTitle" data-rule-field="title" value="'+esc(r.title)+'" maxlength="160"></label><label>When<select data-rule-field="phaseId">'+phases.map(p=>option(p.id,p.title,r.phaseId)).join('')+'</select></label>'+(r.condition==='submission'?'<label>Remind me with this many minutes left<input type="number" min="0" max="120" step="0.5" data-rule-field="remainingMinutes" value="'+r.remainingMinutes+'"></label>':'')+
 '<label>What should happen?<textarea data-rule-field="expectation" placeholder="Describe the progress you expect.">'+esc(r.expectation)+'</textarea></label><label>What evidence will you check?<textarea data-rule-field="evidence" placeholder="Name a saved contribution or something you will observe.">'+esc(r.evidence)+'</textarea></label><label>If it needs attention<textarea data-rule-field="response" placeholder="What would you ask, change, or offer?">'+esc(r.response)+'</textarea></label>'+
 '<div class="rule-detection-note">'+(manual?'Teacher review. Save an observation in Teams; this rule does not infer speech or grade a rubric.':r.condition==='private_check'?'Automatic signal: a saved incorrect MCQ answer. The teacher reviews the reason; changing the wording here does not change the answer key.':r.condition==='submission'?'Automatic signal: a missing role submission at the chosen reminder time, or after this stage. No alert before the live stage runs.':'Recorded signal: '+(data.progress.library?.seeds[r.id]?.trigger||r.evidence).replace(/\{(\w+)\}/g,(_,k)=>r.params?.[k]??'').replace(/(\d+) ([\w-]+)\(s\)/g,(_,n,w)=>n+' '+w+(Number(n)===1?'':'s')))+'</div>'+
 '<button id="ruleStudentPreview">What changes for students?</button>'+(r.origin==='custom'?'<button id="ruleDelete" class="rule-delete">Delete this rule</button>':'');
 $('#ruleStudentPreview').onclick=()=>{ruleCollect();showRuleStudentPreview(r)};
 $('#ruleDelete')?.addEventListener('click',()=>{ruleDraft=ruleDraft.filter(x=>x.id!==r.id);ruleSelected=ruleDraft[0]?.id;drawRulePlanner()});
}
function showRuleStudentPreview(r){
 const q=data.progress.questions.initial,collected=data.progress.config.privateCheck;
 const content=r.condition==='private_check'?(collected?'<span class="progress-kicker">ALREADY COLLECTED · PRIVATE TO THE LEARNER AND TEACHER</span><h2>'+esc(q.prompt)+'</h2>'+q.options.map(([,label])=>'<div class="rule-preview-option"><span>○</span>'+esc(label)+'</div>').join('')+'<label>Your reason<textarea disabled placeholder="Use a label or unit from the story."></textarea></label><p>This rule reads the existing answer and reason. Turning the rule off stops the reminder; collection continues.</p>':'<h2>No individual check in this activity.</h2><p>Add the check to the activity before using this detector. Existing role work is still saved.</p>'):r.condition==='submission'?'<h2>Uses existing role submissions.</h2><p>No new student task. The rule adds a teacher reminder at the selected time.</p>':'<h2>Teacher observation.</h2><p>No new student task. Inspect the saved work or ask the group, then record specific evidence in Teams.</p>';
 showModal(modalHead('Data used by this rule',rulePhaseName(r.phaseId))+'<div class="rule-student-preview">'+content+'</div><div class="progress-modal-actions"><button id="rulePreviewBack">← Back to rules</button></div>','progress-rules-modal');
 $('#rulePreviewBack').onclick=drawRulePlanner;
}
async function saveRulePlanner(){
 ruleCollect();const b=$('#progressRulesSave');b.disabled=true;$('#ruleFeedback').textContent='Saving rules and updating connected interfaces…';
 try{
  const next=clone(data.plan);next.progress={...next.progress,rules:clone(ruleDraft),rulesReviewedAt:Date.now()};
  await api('/api/host/plan',{plan:next,planRev:data.planRev});history.push(clone(data.plan));await reload(true);refreshPreviewPages();
  window.dispatchEvent(new Event('progress-rules-saved'));if(ruleReturn==='teams')teamModal();else closeModal();toast('Rules saved. Check the updated student interfaces on the canvas.');
 }catch(e){$('#ruleFeedback').textContent=e.message;b.disabled=false}
}
const ruleTeamDetailBase=teamDetail;
teamDetail=function(group){
 ruleTeamDetailBase(group);if(!currentProgress())return;
 const e=currentProgress().teams[group],container=$('.progress-detail-bottom');if(!container)return;
 if(data.plan.progress?.rules){container.querySelector('.progress-observation')?.remove();container.classList.add('rule-planned-intervention')}
 container.insertAdjacentHTML('beforebegin','<section class="rule-signals"><div class="progress-evidence-header"><h3>Progress rules</h3><button id="ruleEditFromTeam">Edit rules</button></div>'+e.signals.map(s=>'<article class="rule-signal '+s.status+'"><div><span class="rule-signal-label">'+esc(s.condition==='teacher_review'?'Teacher review':rulePhaseName(s.phaseId))+' · '+esc({'attention':'Needs attention','checked':'Checked','addressed':'Addressed','waiting':'Waiting','collecting':'Collecting','needs-review':'Not reviewed','review':'Evidence to read','inactive':'Not triggered'}[s.status]||s.status)+'</span><h4>'+esc(s.title)+'</h4><p>'+esc(s.detail)+'</p>'+(s.status==='attention'&&s.response?'<p class="rule-response">Next step: '+esc(s.response)+'</p>':'')+'</div>'+(s.condition==='teacher_review'?'<button data-rule-review="'+esc(s.id)+'">Record observation</button>':s.id==='reading-check'&&s.status==='attention'&&!e.support?'<button data-rule-support>Preview support</button>':'')+'</article>').join('')+'</section>');
 if(e.support){$('.progress-detail-toolbar>div').insertAdjacentHTML('afterbegin','<button id="inspectSupportedTeam">Inspect updated interfaces</button>');$('#inspectSupportedTeam').onclick=()=>{canvasClassWork=!progressPreview;previewGroup=group;closeModal();previewPhase=data.plan.live.phaseId;render();fit();toast('Open a learner card on the canvas to inspect this team’s updated interface.');};}
 $('#ruleEditFromTeam').onclick=()=>progressRulesModal();$$('[data-rule-review]').forEach(b=>b.onclick=()=>ruleObservation(group,b.dataset.ruleReview));$('[data-rule-support]')?.addEventListener('click',()=>supportPreview(group));
};
function ruleObservation(group,id){
 const r=currentProgress().rules.find(r=>r.id===id),s=currentProgress().teams[group].signals.find(r=>r.id===id);
 showModal(modalHead(r.title,'Team '+(group+1)+' · Instructor observation')+'<div class="rule-editor"><p>'+esc(r.expectation)+'</p><label>Finding<select id="ruleFinding">'+option('attention','Needs attention',s.status)+option('checked','Checked',s.status)+'</select></label><label>Evidence you observed<textarea id="ruleEvidenceNote" placeholder="Record a specific contribution or interaction.">'+esc(['checked','attention'].includes(s.status)?s.detail:'')+'</textarea></label><p class="progress-footnote">This is your judgment; the system has not recorded or analyzed speech.</p><p id="ruleReviewFeedback" role="status"></p></div><div class="progress-modal-actions"><button id="ruleReviewBack">Back</button><button id="ruleReviewSave" class="primary">Save observation</button></div>','progress-rules-modal');
 $('#ruleReviewBack').onclick=()=>teamDetail(group);$('#ruleReviewSave').onclick=async()=>{if(progressPreview)return $('#ruleReviewFeedback').textContent='Use Class work to save a teacher observation.';try{await api('/api/host/progress-support',{kind:'rule-review',group,ruleId:id,status:$('#ruleFinding').value,note:$('#ruleEvidenceNote').value});await reload(true);teamDetail(group)}catch(e){$('#ruleReviewFeedback').textContent=e.message}};
}
