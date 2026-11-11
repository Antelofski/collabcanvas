/* Rule library for the instructor.
   Plan: rules grouped by the collaboration problem they watch, each as alert → students see → respond now → next time.
   Class: open alerts on top of the classroom map, each read as expected → observed → why, closed with a note.
   After: decisions saved for the next activity. Review: a stage × role storyboard of every student page.
   The earlier views stay in place for ?tour=activity and for servers without the rule library. */
let rhClassRule='',rhSeenSig='',rhContext='',rhFilter='all',rhWording=false,rhStoryRule='',rhMatches=null;
const rhLogged=new Set();
const rhOn=()=>!fullActivityTour&&Boolean(data?.progress?.library);
const rhLib=()=>data.progress.library;
const rhCustomFamily={id:'custom',name:'Your own rules',problem:'A concern you described yourself.',caution:'Free text does not create a detector. A rule you write uses your own observation or a ready-made signal.'};
const rhSeedOf=r=>rhLib().seeds[r.id]||(r.condition&&r.condition!=='teacher_review'?Object.values(rhLib().seeds).find(s=>s.condition===r.condition):null)||null;
const rhGroupOf=r=>r.origin==='custom'?'custom':rhSeedOf(r)?.family||'custom';
const rhFamily=id=>rhLib().families.find(f=>f.id===id)||rhCustomFamily;
const rhShort=c=>monitorShort[c.id]||c.short||c.title;
const rhPlural=(n,one,many)=>n+' '+(n===1?one:many||one+'s');
const rhDetect={auto:'Recorded by the interface','auto+teacher':'Recorded by the interface, then read by you',self:'Reported by the learner',teacher:'Observed by you'};
const rhIndividualOnly=['submission','stalled_learner','workload_balance'],rhCheckpoint=['submission','shared_blocker','workload_balance'];
const rhPersonal=['stalled_learner','random_explainer','closing_pulse','pasted_text','feedback_specific','support_request'];
const rhTimed=['submission','stalled_learner','quiet_team','co_sign','shared_blocker','workload_balance'];
const rhSpot={co_sign:'[data-ci="signoff"]',contribution_balance:'.ci-authors',random_explainer:'[data-ci="explainer"]',unresolved_difference:'[data-ci="whynot"]',closing_pulse:'[data-ci="pulse"]',quiet_team:'[data-ci="status"]',pasted_text:'.ci-note',support_request:'.adaptive-help',private_check:'[data-check-form]'};
/* Wording for a ready-made change when it answers a rule other than the one it was first written for. */
const rhStories={
 'stalled-learner':{pattern:'scaffold',title:'Break the role task into smaller steps',change:'Keep the role tools. Add three short prompts for this learner only: read the unit, name who is counted, explain the changing area.',why:'Gives a concrete place to start without changing the goal. Teammates are not told.',recheck:'Read the three answers and the role contribution that follows.'},
 'quiet-team':{pattern:'written-exchange',title:'Add one round of written turns',change:'Each member gets a short field for one idea and its evidence, and can reply to a teammate.',why:'Gives a quiet team a low-pressure way to start. It does not assume why the team is quiet.',recheck:'Read whether the replies answer each other, not only how many were sent.'},
 'resolve-disagreement':{pattern:'written-exchange',title:'Put both readings side by side',change:'Each member writes their reading with its evidence, then replies to one teammate.',why:'Keeps the minority reading visible in writing before the team decides.',recheck:'Check that the critique says why one reading was rejected, or that it stays open.'},
 'shared-misconception':{pattern:'comparison',title:'Compare who the frames count',change:'Add a first-and-last-frame comparison for this team, then a new private question for each learner.',why:'Brings in information from outside the team. More peer discussion would repeat the same wrong answer.',recheck:'Read the new private answers and reasons. The first answers stay visible.'}};
/* A drafted question for the team. The teacher edits it before sending. */
const rhAsk={
 'co-sign':'Before you finish: one teammate who did not save the critique reads it and signs off with one reason.',
 'contribution-balance':'Take one round of turns. Each member adds one point to the critique before you finish.',
 'random-explainer':'Explain your answer to each other once more. Any member may be asked to explain it.',
 'quiet-team':'What is your team working on right now? Post one line in the team status.',
 'early-finish':'You finished early. Which other reading did you rule out, and what evidence ruled it out?',
 'resolve-disagreement':'Write three lines: reading A, reading B, and the evidence that would decide between them.',
 'specific-feedback':'Point to the sentence or frame your feedback is about, and give one reason.',
 'shared-misconception':'Look at the labels on frames 1 and 7. Who does each frame count?'};
const rhInterfaceStoryBase=interfaceChangeStory;
interfaceChangeStory=function(pattern){const story=rhOn()&&rhStories[rhStoryRule];return story&&story.pattern===pattern?story:rhInterfaceStoryBase(pattern)};

/* ------------------------------------------------------------------ planner */
const rhLegacy={modal:progressRulesModal,planner:drawRulePlanner,editor:drawRuleEditor,preview:showRuleStudentPreview,collect:ruleCollect};
function rhParams(r){return rhSeedOf(r)?.params||[]}
function rhFill(text,r){const specs=rhParams(r);return (text||'').replace(/\{(\w+)\}/g,(_,key)=>{const spec=specs.find(s=>s.key===key);return String(r.params?.[key]??spec?.default??'')}).replace(/(\d+) ([\w-]+)\(s\)/g,(_,n,word)=>n+' '+word+(Number(n)===1?'':'s'))}
function rhTrigger(r){const seed=rhSeedOf(r);if(r.condition==='teacher_review'&&r.origin==='custom')return 'You record what you observed for a team.';return rhFill(seed?.trigger||r.expectation,r)}
function rhAdds(r){return r.condition==='teacher_review'&&r.origin==='custom'?'':rhSeedOf(r)?.adds||''}
function rhDetection(r){const seed=rhSeedOf(r);return rhDetect[r.origin==='custom'?(r.condition==='teacher_review'?'teacher':'auto'):seed?.detection||'teacher']}
function rhCarried(r){const lib=rhLib();return r.carried||lib.carry.find(c=>c.ruleId===r.id&&c.fromRun!==lib.runId)||null}
function rhRuleRow(r){
 const lib=rhLib(),seed=rhSeedOf(r),off=lib.unavailable[r.id],tags=[];
 if(off)tags.push('Not available');else{if(seed?.scope==='class')tags.push('Whole class');if(rhAdds(r))tags.push('Student page');if(rhCarried(r))tags.push('From last time')}
 return '<div class="rh-rule '+(ruleSelected===r.id?'selected ':'')+(r.enabled?'':'off ')+(off?'unavailable':'')+'"><input type="checkbox" data-rule-enabled="'+esc(r.id)+'" aria-label="Turn on '+esc(r.title)+'" '+(r.enabled?'checked ':'')+(off?'disabled':'')+'><button data-rule-select="'+esc(r.id)+'"><strong>'+esc(r.title||'Untitled rule')+'</strong>'+(tags.length?'<span class="rh-tags">'+tags.map(t=>'<i>'+t+'</i>').join('')+'</span>':'')+'</button></div>';
}
function rhCount(){
 const on=ruleDraft.filter(r=>r.enabled),adds=on.filter(r=>rhAdds(r)).length,save=$('#progressRulesSave'),summary=$('#rhPlannerSummary');
 if(save)save.textContent='Save '+rhPlural(on.length,'rule');
 if(summary)summary.textContent=rhPlural(on.length,'rule')+' on · '+(adds?adds+' add something to the student page':'none change the student page');
}
ruleCollect=function(){
 if(!rhOn())return rhLegacy.collect();
 const r=ruleDraft.find(r=>r.id===ruleSelected);if(!r||!$('#ruleEditor'))return;
 $$('#ruleEditor [data-rule-field]').forEach(el=>{r[el.dataset.ruleField]=el.type==='number'?+el.value:el.value});
 $$('#ruleEditor [data-rule-param]').forEach(el=>{(r.params??={})[el.dataset.ruleParam]=el.type==='checkbox'?el.checked:+el.value});
};
progressRulesModal=function(){
 if(!rhOn())return rhLegacy.modal();
 ruleReturn=progressScreen==='teams'||progressScreen==='detail'?'teams':'canvas';progressScreen='rules';
 ruleDraft=clone(data.progress.rules);
 for(const s of data.progress.suggestions||[])if(!ruleDraft.some(r=>r.id===s.id))ruleDraft.push({...clone(s),enabled:false});
 ruleSelected=ruleDraft.find(r=>r.enabled)?.id||ruleDraft[0]?.id;rhFilter='all';rhWording=false;rhMatches=null;
 drawRulePlanner();
};
drawRulePlanner=function(){
 if(!rhOn())return rhLegacy.planner();
 if(!ruleDraft.some(r=>r.id===ruleSelected))ruleSelected=ruleDraft.find(r=>r.enabled)?.id||ruleDraft[0]?.id;
 const families=[...rhLib().families,rhCustomFamily],shown=r=>rhFilter==='all'||r.enabled||r.id===ruleSelected,keep=$('.rule-library-modal .rule-list-options')?.scrollTop;
 const list=families.map(f=>{const rows=ruleDraft.filter(r=>rhGroupOf(r)===f.id&&shown(r));return rows.length?'<section class="rh-family"><header><h4>'+esc(f.name)+'</h4><p>'+esc(f.problem)+'</p></header>'+rows.map(rhRuleRow).join('')+'</section>':''}).join('');
 showModal(modalHead('Progress rules','')+
  '<div class="rh-planner-top"><p id="rhPlannerSummary"></p><div class="rh-segment" role="group" aria-label="Rules shown">'+[['all','All rules'],['on','On only']].map(([id,label])=>'<button data-rh-filter="'+id+'" class="'+(rhFilter===id?'active':'')+'" aria-pressed="'+(rhFilter===id)+'">'+label+'</button>').join('')+'</div></div>'+
  '<div class="rh-planner"><aside class="rule-list"><div class="rule-list-options">'+(list||'<p class="rh-empty">No rule is on.</p>')+'</div><button id="ruleAdd" class="rh-add">+ Write my own rule</button></aside><section id="ruleEditor" class="rh-editor"></section></div>'+
  '<div class="rh-planner-footer"><p id="ruleFeedback" role="status"></p><div><button id="ruleCancel">Cancel</button><button id="progressRulesSave" class="primary">Save rules</button></div></div>','rule-library-modal');
 const options=$('.rule-list-options');
 $$('[data-rh-filter]').forEach(b=>b.onclick=()=>{ruleCollect();rhFilter=b.dataset.rhFilter;drawRulePlanner()});
 $$('[data-rule-select]').forEach(b=>b.onclick=()=>{ruleCollect();ruleSelected=b.dataset.ruleSelect;rhWording=false;rhMatches=null;drawRulePlanner()});
 $$('[data-rule-enabled]').forEach(c=>c.onchange=()=>{const r=ruleDraft.find(r=>r.id===c.dataset.ruleEnabled);r.enabled=c.checked;c.closest('.rh-rule').classList.toggle('off',!c.checked);if(r.id===ruleSelected&&$('#rhEnabled'))$('#rhEnabled').checked=c.checked;rhCount()});
 $('#ruleAdd').onclick=()=>{ruleCollect();const id='custom-'+Date.now().toString(36);ruleDraft.push({id,origin:'custom',enabled:true,title:'',condition:'teacher_review',phaseId:data.plan.phases.at(-1).id,expectation:'',evidence:'',response:'',nextTime:'',remainingMinutes:0,params:{}});ruleSelected=id;rhWording=true;rhMatches=null;drawRulePlanner();$('#ruleTitle')?.focus()};
 $('#ruleCancel').onclick=()=>ruleReturn==='teams'?teamModal():closeModal();
 $('#progressRulesSave').onclick=saveRulePlanner;
 drawRuleEditor();rhCount();
 const selected=$('[data-rule-select="'+ruleSelected+'"]')?.closest('.rh-rule');
 if(keep!==undefined)options.scrollTop=keep;
 if(selected){const a=selected.getBoundingClientRect(),b=options.getBoundingClientRect();if(a.top<b.top||a.bottom>b.bottom)options.scrollTop+=a.top-b.top-70}
};
function rhParamInput(r,spec){
 const value=r.params?.[spec.key]??spec.default;
 if(spec.type==='flag')return '<label class="rh-flag"><input type="checkbox" data-rule-param="'+spec.key+'" '+(value?'checked':'')+'>'+esc(spec.label)+'</label>';
 return '<label class="rh-param"><span>'+esc(spec.label)+'</span><span><input type="number" data-rule-param="'+spec.key+'" min="'+spec.min+'" max="'+spec.max+'" step="'+spec.step+'" value="'+value+'">'+(spec.unit?'<em>'+esc(spec.unit)+'</em>':'')+'</span></label>';
}
drawRuleEditor=function(){
 if(!rhOn())return rhLegacy.editor();
 const r=ruleDraft.find(r=>r.id===ruleSelected),root=$('#ruleEditor');if(!r||!root)return;
 const lib=rhLib(),seed=rhSeedOf(r),custom=r.origin==='custom',family=rhFamily(rhGroupOf(r)),off=lib.unavailable[r.id],carried=rhCarried(r),stats=lib.stats[r.id],adds=rhAdds(r);
 const phases=rhIndividualOnly.includes(r.condition)?data.plan.phases.filter(p=>p.kind==='individual'):data.plan.phases,phase=data.plan.phases.find(p=>p.id===r.phaseId);
 const story=seed?.pattern&&!custom?(rhStories[r.id]?.pattern===seed.pattern?rhStories[r.id]:rhInterfaceStoryBase(seed.pattern)):null;
 const settings=rhParams(r).map(spec=>rhParamInput(r,spec)).join('')+
  '<label class="rh-param"><span>Checked during</span><select data-rule-field="phaseId">'+phases.map(p=>option(p.id,p.title,r.phaseId)).join('')+'</select></label>'+
  (rhCheckpoint.includes(r.condition)?'<label class="rh-param"><span>Checkpoint before the stage ends</span><span><input type="number" min="0" max="'+(phase?.minutes||120)+'" step="0.5" data-rule-field="remainingMinutes" value="'+(r.remainingMinutes||0)+'"><em>min</em></span></label>':'');
 const signal=custom?'<label class="rh-field">How is it checked?<select id="rhCondition">'+option('teacher_review','I observe it and record what I saw',r.condition)+lib.customDetectors.map(d=>option(d.condition,'Ready-made signal: '+d.title,r.condition)).join('')+'</select></label><div class="rh-compile"><label class="rh-field">Or describe the concern in your own words<input id="rhCompileText" maxlength="300" placeholder="For example: one learner is stuck and nothing changes"></label><button id="rhCompile">Find in library</button></div><div id="rhMatches">'+rhMatchList()+'</div>':'';
 root.innerHTML='<header class="rh-editor-head"><div><p class="rh-problem"><b>'+esc(family.name)+'</b>'+esc(family.problem)+'</p><h3 id="rhRuleHeading">'+esc(r.title||'New rule')+'</h3></div><label class="rh-switch"><input type="checkbox" id="rhEnabled" '+(r.enabled?'checked ':'')+(off?'disabled':'')+'><span>Use this rule</span></label></header>'+
  (off?'<p class="rh-note warn">'+esc(off)+'</p>':'')+
  (carried?'<p class="rh-note carried"><b>From last time'+(carried.title?' · '+esc(carried.title):'')+'</b>'+esc(carried.note||'Turned on by an earlier decision.')+'</p>':'')+
  (r.remembered?'<p class="rh-note carried"><b>You wrote this rule earlier</b>It is off until you turn it on for this activity.</p>':'')+signal+
  '<div class="rh-loop"><section><h4>Alert when</h4><p id="rhTriggerText">'+esc(rhTrigger(r))+'</p><div class="rh-settings">'+settings+'</div><p class="rh-how">'+esc(rhDetection(r))+'</p></section>'+
  '<section><h4>Students see</h4><p>'+esc(adds||'Nothing new. This rule reads work the activity already saves.')+'</p><button id="ruleStudentPreview">Preview the student page</button></section>'+
  '<section><h4>Respond now</h4><p id="rhRespondText">'+esc(r.response||'Decide after you read the evidence.')+'</p>'+(story?'<p class="rh-how">Ready-made change: '+esc(story.title)+'</p>':'')+'</section>'+
  '<section><h4>Next time</h4><p id="rhNextText">'+esc(r.nextTime||'Nothing suggested yet.')+'</p>'+(stats?.runs?'<p class="rh-how">On in '+rhPlural(stats.runs,'earlier activity','earlier activities')+' · '+rhPlural(stats.alerts,'alert')+', '+stats.handled+' handled</p>':'')+'</section></div>'+
  (family.caution?'<p class="rh-caution"><b>Read with care</b>'+esc(family.caution)+'</p>':'')+
  '<details class="rh-wording" '+(rhWording||custom&&!r.expectation?'open':'')+'><summary>'+(custom?'Wording':'Edit wording')+'</summary><label class="rh-field">Rule name<input id="ruleTitle" data-rule-field="title" maxlength="160" value="'+esc(r.title)+'" placeholder="Name the behaviour you expect"></label><label class="rh-field">What should happen?<textarea data-rule-field="expectation" placeholder="Describe the progress you expect.">'+esc(r.expectation)+'</textarea></label><label class="rh-field">Evidence you will check<textarea data-rule-field="evidence" placeholder="Name saved work, or what you will observe.">'+esc(r.evidence)+'</textarea></label><label class="rh-field">Respond now<textarea data-rule-field="response" placeholder="What would you ask, change or offer?">'+esc(r.response)+'</textarea></label><label class="rh-field">Next time<textarea data-rule-field="nextTime" placeholder="What would you change in the design?">'+esc(r.nextTime||'')+'</textarea></label></details>'+
  (custom?'<div class="rh-editor-actions"><button id="ruleDelete">'+(r.remembered?'Forget this rule':'Delete this rule')+'</button></div>':'');
 $('#rhEnabled').onchange=e=>{r.enabled=e.target.checked;const box=$('[data-rule-enabled="'+r.id+'"]');if(box){box.checked=r.enabled;box.closest('.rh-rule').classList.toggle('off',!r.enabled)}rhCount()};
 $$('#ruleEditor [data-rule-param]').forEach(el=>el.oninput=()=>{ruleCollect();$('#rhTriggerText').textContent=rhTrigger(r)});
 const live=(field,target,empty)=>{const el=$('#ruleEditor [data-rule-field="'+field+'"]');if(el)el.oninput=()=>{$(target).textContent=el.value.trim()||empty}};
 live('response','#rhRespondText','Decide after you read the evidence.');live('nextTime','#rhNextText','Nothing suggested yet.');
 $('.rh-wording').ontoggle=e=>{rhWording=e.target.open};
 $('#ruleTitle').oninput=e=>{const text=e.target.value.trim()||'Untitled rule';$('#rhRuleHeading').textContent=text;const row=$('[data-rule-select="'+r.id+'"] strong');if(row)row.textContent=text};
 $('#ruleStudentPreview').onclick=()=>showRuleStudentPreview(r);
 $('#rhCondition')?.addEventListener('change',e=>{ruleCollect();rhUseSignal(r,e.target.value);rhWording=true;drawRulePlanner()});
 $('#rhCompile')?.addEventListener('click',async()=>{const text=$('#rhCompileText').value.trim()||[r.title,r.expectation].join(' ');ruleCollect();try{rhMatches=(await api('/api/host/rule-compile',{text})).matches}catch(e){rhMatches=[];toast(e.message,true)}$('#rhMatches').innerHTML=rhMatchList();rhBindMatches(r)});
 rhBindMatches(r);
 $('#ruleDelete')?.addEventListener('click',async()=>{if(r.remembered){try{await api('/api/host/rule-action',{kind:'forget-custom',id:r.id});await reload(true)}catch(e){return toast(e.message,true)}}ruleDraft=ruleDraft.filter(x=>x.id!==r.id);ruleSelected=ruleDraft.find(x=>x.enabled)?.id||ruleDraft[0]?.id;rhWording=false;drawRulePlanner()});
};
function rhMatchList(){
 if(!rhMatches)return '';
 if(!rhMatches.length)return '<p class="rh-how">Nothing in the library matches these words. Keep it as your own observation: you record what you see.</p>';
 const lib=rhLib();
 return rhMatches.map(m=>{const off=lib.unavailable[m.ruleId],on=ruleDraft.find(r=>r.id===m.ruleId)?.enabled;
  return '<article class="rh-match"><div><strong>'+esc(m.title)+'</strong><span>'+esc(rhFill(m.trigger,{id:m.ruleId,condition:m.condition,params:m.params}))+'</span>'+(off?'<span class="rh-match-off">'+esc(off)+'</span>':'')+'</div><div class="rh-match-actions">'+(off?'':'<button data-rh-match-rule="'+esc(m.ruleId)+'">'+(on?'Open this rule':'Turn on this rule')+'</button>')+(m.custom?'<button data-rh-match="'+esc(m.condition)+'">Use its signal in my rule</button>':'')+'</div></article>'}).join('')+'<p class="rh-how">Matched by keywords, not by a model.</p>';
}
function rhBindMatches(r){
 $$('[data-rh-match]').forEach(b=>b.onclick=()=>{ruleCollect();rhUseSignal(r,b.dataset.rhMatch);rhMatches=null;rhWording=true;drawRulePlanner()});
 /* The library already has this rule: turn it on there, and drop the empty draft. */
 $$('[data-rh-match-rule]').forEach(b=>b.onclick=()=>{ruleCollect();const target=ruleDraft.find(x=>x.id===b.dataset.rhMatchRule);if(!target)return;
  if(!r.remembered&&!(r.title||'').trim()&&!(r.expectation||'').trim()&&!(r.evidence||'').trim())ruleDraft=ruleDraft.filter(x=>x.id!==r.id);
  target.enabled=true;ruleSelected=target.id;rhMatches=null;rhWording=false;drawRulePlanner()});
}
function rhUseSignal(r,condition){
 const d=rhLib().customDetectors.find(d=>d.condition===condition);r.condition=condition;
 r.params=d?Object.fromEntries(d.params.map(p=>[p.key,p.default])):{};
 if(d){const seed=Object.values(rhLib().seeds).find(s=>s.condition===condition);if(!r.title.trim())r.title=d.title;if(!r.expectation.trim())r.expectation=seed.expectation;if(!r.evidence.trim())r.evidence=d.evidence;if(!r.response.trim())r.response=seed.response;if(!(r.nextTime||'').trim())r.nextTime=seed.nextTime;
  const fits=rhIndividualOnly.includes(condition)?data.plan.phases.filter(p=>p.kind==='individual'):data.plan.phases;if(!fits.some(p=>p.id===r.phaseId))r.phaseId=fits[0]?.id||r.phaseId}
}
function rhScrollTo(frame,selector){
 if(!selector)return;let tries=0;const timer=setInterval(()=>{
  if(!frame.isConnected)return clearInterval(timer);
  const doc=frame.contentDocument,el=doc?.querySelector(selector);
  if(el){doc.scrollingElement.scrollTop=Math.max(0,el.getBoundingClientRect().top+doc.scrollingElement.scrollTop-16);clearInterval(timer)}else if(++tries>70)clearInterval(timer);
 },70);
}
showRuleStudentPreview=async function(r){
 if(!rhOn())return rhLegacy.preview(r);
 if(!r)return;ruleCollect();progressScreen='rule-preview';
 const adds=rhAdds(r),role=p=>data.plan.tasks.find(t=>t.assignees.includes(p.slot))?.title||'Learner';
 showModal(modalHead('What students see',r.title)+'<div class="rh-preview-bar"><button id="rulePreviewBack">← Back to rules</button><p>'+esc(adds||'This rule adds nothing to the student page. It reads work the activity already saves.')+'</p><label>View as<select id="rhPreviewPerson" disabled></select></label></div><div class="rh-preview-stage"><p role="status">Opening an example student page…</p></div>','rh-preview-modal');
 $('#rulePreviewBack').onclick=()=>{progressScreen='rules';drawRulePlanner()};
 try{
  const run=await api('/api/host/rule-preview',{ruleId:r.id,rules:ruleDraft});if(!$('#overlay .rh-preview-modal'))return;
  const open=id=>{$('.rh-preview-stage').innerHTML='<iframe id="rhPreviewFrame" title="Example student page" src="/student.html?preview=1&admin='+encodeURIComponent(admin)+'&person='+encodeURIComponent(id)+'&testRun='+encodeURIComponent(run.id)+'&phase='+encodeURIComponent(run.phase)+'"></iframe>';const frame=$('#rhPreviewFrame');frame.onload=()=>rhScrollTo(frame,rhSpot[r.condition])};
  const picker=$('#rhPreviewPerson');picker.innerHTML=run.people.map(p=>option(p.id,role(p)+' · '+cleanName(p.name),run.person)).join('');picker.disabled=false;picker.onchange=e=>open(e.target.value);open(run.person);
 }catch(e){if($('.rh-preview-stage'))$('.rh-preview-stage').innerHTML='<p role="status">'+esc(e.message)+'</p>'}
};
const rhSaveBase=saveRulePlanner;
saveRulePlanner=async function(){
 if(rhOn()){
  ruleCollect();const complete=r=>r.title?.trim()&&r.expectation?.trim()&&r.evidence?.trim();
  ruleDraft=ruleDraft.filter(r=>r.enabled||r.origin!=='custom'||complete(r));
  const bad=ruleDraft.find(r=>!complete(r));
  if(bad){ruleSelected=bad.id;rhWording=true;drawRulePlanner();$('#ruleFeedback').textContent='“'+((bad.title||'').trim()||'Your rule')+'” needs a name, what should happen, and the evidence you will check.';return}
 }
 return rhSaveBase();
};

/* ------------------------------------------------------------------ class dashboard */
function rhSync(){for(const s of Object.values(rhLib().seeds))if(!monitorShort[s.id])monitorShort[s.id]=s.short}
function rhRank(rows){const order={attention:0,review:1,pending:2,reviewed:3,checked:4,collecting:5};return rows.map((c,i)=>[c,i]).sort((a,b)=>(order[monitorStatus(a[0])[0]]??9)-(order[monitorStatus(b[0])[0]]??9)||a[1]-b[1]).map(x=>x[0])}
function rhClassSignals(){return currentProgress()?.classSignals||[]}
function rhSignature(){const p=currentProgress();if(!p)return '';return JSON.stringify([progressPreview,(p.classSignals||[]).map(s=>[s.id,s.status,s.key]),p.teams.map(e=>(e.signals||[]).map(s=>[s.id,s.status,s.key])),p.library.carry.length,(p.log||[]).length,data.plan.live.phaseId,Boolean(data.plan.live.paused)])}
const rhChecksBase=monitorChecks;
monitorChecks=function(e){
 const rows=rhChecksBase(e);if(!rhOn())return rows;
 for(const c of rows){
  const s=(e.signals||[]).find(s=>s.id===c.id);
  if(s&&!c.change&&['addressed','inactive'].includes(s.status))Object.assign(c,{status:s.status,observed:s.observed,why:s.why,handled:s.handled});
  if(!c.targets&&c.people?.length&&c.pattern&&c.pattern!=='comparison')c.targets=c.people;
 }
 return rows;
};
const rhStatusBase=monitorStatus;
monitorStatus=function(c){
 if(rhOn()&&!c.change){
  if(c.status==='addressed')return ['reviewed','Handled'];
  if(c.status==='review')return ['review','Evidence to read'];
  if(c.status==='waiting')return ['collecting','Waiting'];
  if(c.status==='needs-review')return ['collecting','Your observation'];
 }
 return rhStatusBase(c);
};
const rhNavBase=monitorNav;
monitorNav=function(active){
 if(!rhOn())return rhNavBase(active);
 const lib=rhLib(),saved=lib.carry.filter(c=>c.fromRun===lib.runId).length,tab=(id,label)=>'<button data-monitor-view="'+id+'" class="'+(active===id?'active':'')+'">'+label+'</button>';
 return '<nav class="monitor-tabs" aria-label="Dashboard views">'+tab('progress','Progress')+tab('followup','Follow-up')+tab('next','Next time'+(saved?'<b class="rh-tab-count">'+saved+'</b>':''))+'<button id="knowledgeReportButton" class="'+(active==='knowledge'?'active':'')+'">Knowledge</button></nav>';
};
const rhBindNavBase=monitorBindNav;
monitorBindNav=function(){rhBindNavBase();if(rhOn())$$('[data-monitor-view]').forEach(b=>{const base=b.onclick;b.onclick=()=>{rhClassRule='';base()}})};
const rhMapBase=monitorMapPeople;
monitorMapPeople=function(){
 const rows=rhMapBase();if(!rhOn())return rows;
 for(const person of rows){
  const e=currentProgress().teams.find(e=>e.group===person.group);
  for(const c of monitorChecks(e)){
   if(c.change||!rhPersonal.includes(c.condition)||!(c.people||[]).includes(person.id))continue;
   if(c.status==='attention'){person.state='attention';person.stateLabel=rhShort(c)+' needs attention';break}
   if(c.status==='review'&&person.state!=='attention'){person.state='review';person.stateLabel=rhShort(c)+' · evidence to read'}
  }
 }
 return rows;
};
const rhPersonBase=monitorPersonPanel;
monitorPersonPanel=function(person){
 if(!rhOn())return rhPersonBase(person);
 const e=currentProgress().teams.find(e=>e.group===person.group),p=activePeople().find(p=>p.id===person.id),checks=rhRank(monitorChecks(e)),a=(progressPreview?data.studio?.previewArtifacts:data.studio?.artifacts)?.[p.id]||{},request=e.adaptive?.requests?.find(r=>r.person===p.id),support=checks.find(c=>c.id==='role-work');
 const saved=[...(a.observations||[]).map(r=>r.text),...(a.beats||[]).map(r=>r.text),...(a.checks||[]).map(r=>r.statement),a.reflection].filter(Boolean).slice(0,2);
 const row=c=>'<button data-monitor-issue="'+p.group+':'+esc(c.id)+'"><span>'+esc(rhShort(c))+'</span><i class="monitor-dot '+monitorStatus(c)[0]+'" aria-label="'+monitorStatus(c)[1]+'"></i></button>';
 const open=checks.filter(c=>['attention','review','pending'].includes(monitorStatus(c)[0])),rest=checks.filter(c=>!open.includes(c));
 return '<aside class="classroom-inspect" id="classroomPerson"><header><div><h2>'+esc(person.name)+'</h2><p>'+esc(person.role)+'</p></div><button id="monitorPersonClose" aria-label="Close student details">'+icon('close')+'</button></header><div class="classroom-person-state"><i class="classroom-symbol '+person.state+'" aria-hidden="true">'+classroomSymbols[person.state]+'</i>'+esc(person.stateLabel)+'</div>'+(request?'<blockquote>'+esc(request.text)+'</blockquote>':'')+saved.map(text=>'<p class="classroom-saved-text">'+esc(text)+'</p>').join('')+(request&&!support?.change?'<button id="monitorPersonSupport" class="primary">Preview smaller steps</button>':'')+'<button id="monitorPersonOpen">Open interface</button><div class="classroom-person-rules">'+open.map(row).join('')+(rest.length?'<details class="rh-person-rest"><summary>'+(open.length?rhPlural(rest.length,'other rule')+' for this team':'All '+rhPlural(rest.length,'rule')+' for this team')+'</summary>'+rest.map(row).join('')+'</details>':'')+'</div></aside>';
};
function rhClock(){
 const live=data.plan.live,phase=data.plan.phases.find(p=>p.id===live.phaseId)||data.plan.phases[0];
 if(!live.started)return {phase,started:false};
 const total=phase.minutes*60,left=live.paused?(live.remaining??total):total-(Date.now()/1000-(live.startedAt||Date.now()/1000));
 return {phase,started:true,paused:Boolean(live.paused),left};
}
function rhClockText(t){if(!t.started)return 'Class not started';const s=Math.round(Math.abs(t.left)),text=Math.floor(s/60)+':'+String(s%60).padStart(2,'0');return t.left<0?text+' over':text+' left'}
function rhStageBar(){
 if(progressPreview)return '<div class="rh-stage"><strong>Rehearsal data</strong><span>Time-based rules run on class work only.</span></div>';
 const t=rhClock();
 return '<div class="rh-stage"><strong>'+esc(t.started?t.phase.title:'Before class')+'</strong><span data-rh-clock>'+rhClockText(t)+'</span>'+(t.paused?'<span class="rh-paused">Paused</span>':'')+(t.started?'<button id="rhExtend" title="Add two minutes to this stage for the whole class">+2 min</button>':'')+'</div>';
}
function rhOpenAlerts(){
 const p=currentProgress(),rows=[];
 for(const c of p.classSignals||[]){const [state,label]=monitorStatus(c);if(state==='attention'||state==='review')rows.push({group:'class',c,state,label})}
 for(const e of p.teams)for(const c of monitorChecks(e)){const [state,label]=monitorStatus(c);if(state==='attention'||state==='review')rows.push({group:e.group,c,state,label})}
 return rows.sort((a,b)=>(a.state==='attention'?0:1)-(b.state==='attention'?0:1)||(a.group==='class'?-1:0)-(b.group==='class'?-1:0));
}
function rhAlertStrip(){
 const rows=rhOpenAlerts();if(!rows.length)return '';
 const row=r=>'<button class="rh-alert '+r.state+'" data-rh-alert="'+r.group+'|'+esc(r.c.id)+'"><span class="rh-alert-where">'+(r.group==='class'?'Whole class':'Team '+(r.group+1))+'</span><strong>'+esc(rhShort(r.c))+'</strong><p>'+esc(r.c.change?'New work to review after the change.':r.c.observed||r.c.detail||'')+'</p><span class="monitor-status '+r.state+'">'+r.label+'</span></button>';
 const first=rows.slice(0,4),rest=rows.slice(4);
 return '<section class="rh-alerts" aria-label="Open alerts">'+first.map(row).join('')+(rest.length?'<details><summary>'+rhPlural(rest.length,'more alert')+'</summary>'+rest.map(row).join('')+'</details>':'')+'</section>';
}
const rhRespondText=c=>c.status==='review'&&c.why?c.why:c.response||'Decide after you read the evidence.';
function rhRecords(c){return (c.records||[]).map(r=>'<div class="monitor-evidence-record"><b>'+esc(cleanName(r.name))+'</b><p>'+esc(r.text)+'</p></div>').join('')}
function rhReading(e){return e.rows.filter(r=>r.initial&&!r.initial.correct).map(r=>'<div class="monitor-evidence-record"><b>'+esc(cleanName(r.name))+' chose</b><blockquote>'+esc(frameworkChoice(r.initial.answer))+'</blockquote>'+(r.initial.reason?'<p>'+esc(r.initial.reason)+'</p>':'')+'</div>').join('')}
const rhEvidenceBase=monitorEvidence;
monitorEvidence=function(e,c){
 if(!rhOn())return rhEvidenceBase(e,c);
 if(c.id==='reading-check')return rhReading(e);
 if(['role-work','peer-use','answer-pattern'].includes(c.id)&&e.collaboration?.[c.id])return c.id==='answer-pattern'&&!['attention','checked','addressed'].includes(c.status)?'':rhEvidenceBase(e,c);
 return rhRecords(c);
};
function rhEvidenceGrid(c,evidence){
 const state=monitorStatus(c)[0],calm=state!=='attention',why=!c.why||state==='review'?'':'<p class="rh-why">'+(calm?'':'<b>Why now</b>')+esc(c.why)+'</p>';
 return '<div class="monitor-evidence-grid"><article id="frameworkRuleExpected"><h3>Expected</h3><p>'+esc(c.expected||c.expectation||'Review this rule with the team.')+'</p></article><article id="frameworkRuleObserved" class="monitor-observed '+(calm?'calm':'')+'"><h3>Observed</h3><p class="monitor-observation">'+esc(c.observed||c.detail||'Waiting for evidence.')+'</p>'+evidence+why+'</article></div>';
}
function rhHandledNote(c){return c.handled?'<section class="rh-handled"><div><h3>Handled</h3><p>'+esc(c.handled.note||'No note saved.')+'</p></div><button id="rhReopen">Reopen</button></section>':''}
function rhCloseOut(c,blocked){
 if(progressPreview||blocked||c.change||!['attention','review'].includes(c.status))return '';
 return '<section class="rh-close"><label for="rhHandleNote">What did you do or check?</label><textarea id="rhHandleNote" placeholder="One line is enough. The alert returns if the evidence changes."></textarea><button id="rhHandle" class="primary">Mark handled</button></section>';
}
function rhNextBlock(c){
 if(progressPreview)return '';
 const lib=rhLib(),saved=lib.carry.find(x=>x.ruleId===c.id&&x.fromRun===lib.runId);
 if(saved)return '<section class="rh-next-inline saved"><div><h3>Saved for next time</h3><p>'+esc(saved.note)+'</p></div><button data-rh-carry-remove="'+esc(saved.id)+'">Remove</button></section>';
 const open=c.change||['attention','review','addressed'].includes(c.status);
 return '<details class="rh-next-inline" '+(open?'open':'')+'><summary>Next time</summary><p>A design decision for the next activity. This class does not change.</p><textarea id="rhNextNote" aria-label="What to do next time">'+esc(c.nextTime||'')+'</textarea><button id="rhNextSave">Save for next time</button></details>';
}
function rhSupportBlock(e){
 const s=e.support,story=rhStories[rhStoryRule]?.pattern==='comparison'?rhStories[rhStoryRule]:rhInterfaceStoryBase('comparison'),ready=e.followupCount>=s.targets.length&&e.followupCorrect>=s.targets.length;
 return '<section class="monitor-proposal"><div><h3>'+esc(story.title)+'</h3><p>'+(s.resolved?'Reviewed. '+esc(s.note||''):'Applied to this team. '+e.followupCount+' of '+s.targets.length+' follow-up answers saved, '+e.followupCorrect+' match the key.')+'</p></div><div class="monitor-proposal-why"><b>'+(s.resolved?'After the change':'Before you close it')+'</b><p>'+esc(story.recheck)+'</p>'+(s.resolved?'':'<textarea id="progressResolveNote" aria-label="What did you verify?" placeholder="What did you verify?"></textarea><button id="progressResolve" class="primary" '+(ready?'':'disabled')+'>Mark addressed</button><button id="frameworkInPerson">Record an in-person check</button>')+'<button id="rhSupportOpen">Open updated interface</button></div></section>';
}
function rhRespond(e,c,story){
 const change=c.change,open=['attention','review'].includes(c.status),actions=[];
 if(change)return '<section class="monitor-proposal"><div><h3>'+esc(story.title)+'</h3><p>'+esc(story.change)+'</p></div><div class="monitor-proposal-why"><b>Applied. Read what learners did next.</b><p>'+esc(story.recheck||story.why)+'</p><button class="primary" id="collabReview">Review subsequent work</button><button id="frameworkInspect">Open updated interface</button></div></section>';
 if(c.pattern==='comparison'&&e.support)return rhSupportBlock(e);
 if(story&&c.status==='attention')return '<section class="monitor-proposal"><div><h3>'+esc(story.title)+'</h3><p>'+esc(story.change)+'</p></div><div class="monitor-proposal-why"><b>How this responds</b><p>'+esc(story.why)+'</p><button class="primary" id="frameworkSuggested">Preview change</button></div></section>';
 if(c.condition==='random_explainer'&&!progressPreview&&open)actions.push('<button id="rhPick">Pick another member</button>');
 if(rhTimed.includes(c.condition)&&!progressPreview&&c.status==='attention'&&data.plan.live.started)actions.push('<button id="rhExtendHere">Add 2 min for the class</button>');
 if(c.condition==='teacher_review'&&!c.pattern)actions.push('<button id="monitorObserve">Record observation</button>');
 if(story&&c.status==='collecting'&&!progressPreview)actions.push('<button id="frameworkSuggested">Preview change</button>');
 if(!open&&!actions.length)return '';
 return '<section class="rh-respond"><div><h3>Respond now</h3><p>'+esc(rhRespondText(c))+'</p></div>'+(actions.length?'<div class="rh-respond-actions">'+actions.join('')+'</div>':'')+'</section>';
}
const rhDetailBase=monitorDetail;
monitorDetail=function(e,c){
 if(!rhOn())return rhDetailBase(e,c);
 rhStoryRule=c.id;
 const [state,label]=monitorStatus(c),family=rhFamily(c.family),story=c.pattern?interfaceChangeStory(c.pattern):null,team=c.condition!=='closing_pulse';
 const tabs=rhRank(monitorChecks(e)).map(x=>'<button data-monitor-rule="'+esc(x.id)+'" class="'+(c.id===x.id?'active':'')+'"><i class="monitor-dot '+monitorStatus(x)[0]+'"></i>'+esc(rhShort(x))+'</button>').join('');
 return '<header class="monitor-heading"><div><button class="monitor-back" id="monitorBack">← Classroom</button><h2 id="frameworkRuleTitle">Team '+(e.group+1)+' · '+esc(rhShort(c))+'</h2><p>'+esc(family.name)+' · '+esc(family.problem)+'</p></div><span class="monitor-status framework-state '+state+'">'+label+'</span></header><nav class="monitor-rule-nav">'+tabs+'</nav><section id="adaptiveTeam">'+rhEvidenceGrid(c,monitorEvidence(e,c))+rhHandledNote(c)+rhRespond(e,c,story)+rhCloseOut(c,c.pattern==='comparison'&&Boolean(e.support))+rhNextBlock(c)+
  '<div class="monitor-detail-actions">'+(team?'<button id="frameworkMessage">Send a question</button>':'')+(c.id==='answer-pattern'?'<button id="monitorKeep">Keep current activity</button>':'')+'<div><button id="progressNext">Draft the next activity</button><button id="progressNextRun">Draft the next run</button></div></div></section>';
};
function rhClassDetail(c){
 rhStoryRule=c.id;
 const [state,label]=monitorStatus(c),family=rhFamily(c.family),teams=(c.groups||[]).map(g=>'<button data-rh-team="'+g+'">Open Team '+(g+1)+'</button>').join('');
 const others=rhClassSignals().length>1?'<nav class="monitor-rule-nav">'+rhRank(rhClassSignals()).map(x=>'<button data-rh-class-rule="'+esc(x.id)+'" class="'+(c.id===x.id?'active':'')+'"><i class="monitor-dot '+monitorStatus(x)[0]+'"></i>'+esc(rhShort(x))+'</button>').join('')+'</nav>':'';
 return '<header class="monitor-heading"><div><button class="monitor-back" id="rhClassBack">← Classroom</button><h2 id="frameworkRuleTitle">Whole class · '+esc(rhShort(c))+'</h2><p>'+esc(family.name)+' · '+esc(family.problem)+'</p></div><span class="monitor-status framework-state '+state+'">'+label+'</span></header>'+others+'<section id="adaptiveTeam">'+rhEvidenceGrid(c,rhRecords(c))+rhHandledNote(c)+
  '<section class="rh-respond"><div><h3>Respond now</h3><p>'+esc(rhRespondText(c))+'</p></div><div class="rh-respond-actions">'+(c.status==='attention'&&!progressPreview&&data.plan.live.started&&c.condition!=='rotation'?'<button id="rhExtendHere">Add 2 min for the class</button>':'')+teams+'</div></section>'+rhCloseOut(c)+rhNextBlock(c)+'</section>';
}
function rhNextView(){
 const lib=rhLib(),p=data.progress,mine=lib.carry.filter(c=>c.fromRun===lib.runId),earlier=lib.carry.filter(c=>c.fromRun!==lib.runId),byRule={};
 for(const i of p.log||[]){const r=byRule[i.ruleId]??={id:i.ruleId,title:i.title,alerts:0,handled:0,teams:new Set()};r.alerts++;if(i.outcome==='handled')r.handled++;r.teams.add(i.group)}
 const name=id=>monitorShort[id]||lib.seeds[id]?.short||p.rules.find(r=>r.id===id)?.title||id;
 const ideas=Object.values(byRule).map(r=>({...r,next:p.rules.find(x=>x.id===r.id)?.nextTime||lib.seeds[r.id]?.nextTime||''})).filter(r=>r.next&&!mine.some(c=>c.ruleId===r.id));
 const openNow=id=>rhOpenAlerts().filter(a=>a.c.id===id).length;
 const where=r=>{const teams=[...r.teams].filter(g=>g!=='class').length,open=openNow(r.id);return rhPlural(r.alerts,'alert')+(teams?' in '+rhPlural(teams,'team'):' for the whole class')+' · '+(open?open+' still open':'none open now')};
 const savedRow=c=>'<article class="rh-next-row"><div><strong>'+esc(name(c.ruleId))+'</strong><p>'+esc(c.note)+'</p>'+(c.observed?'<p class="rh-how">Seen in this class: '+esc(c.observed)+'</p>':'')+'</div><button data-rh-carry-remove="'+esc(c.id)+'">Remove</button></article>';
 const ideaRow=r=>'<article class="rh-next-row"><div><strong>'+esc(name(r.id))+'</strong><p>'+esc(r.next)+'</p><p class="rh-how">'+where(r)+'</p></div><button data-rh-carry-add="'+esc(r.id)+'">Save for next time</button></article>';
 const earlierRow=c=>'<article class="rh-next-row"><div><strong>'+esc(name(c.ruleId))+'</strong><p>'+esc(c.note)+'</p><p class="rh-how">From '+esc(c.title||'an earlier activity')+'</p></div></article>';
 return '<div class="rh-next"><header class="monitor-heading"><div><h2>Next time</h2><p>Design decisions from this class. They apply when you start the next activity. This class does not change.</p></div><button id="rhDrafts">Saved drafts</button></header>'+
  '<section><h3>Saved from this class</h3>'+(mine.length?mine.map(savedRow).join(''):'<p class="rh-empty">Nothing saved yet. Open an alert and use “Next time” to keep a decision.</p>')+'</section>'+
  (ideas.length?'<section><h3>Suggested by the alerts in this class</h3>'+ideas.map(ideaRow).join('')+'</section>':'')+
  (earlier.length?'<section><h3>Carried into this activity</h3>'+earlier.map(earlierRow).join('')+'</section>':'')+'</div>';
}
const rhOverviewBase=monitorOverview;
monitorOverview=function(){
 if(!rhOn())return rhOverviewBase();
 if(monitorView==='next')return rhNextView();
 const signal=rhClassRule&&rhClassSignals().find(s=>s.id===rhClassRule);if(signal)return rhClassDetail(signal);
 rhClassRule='';rhStoryRule='';
 const people=monitorMapPeople(),selected=people.find(p=>p.id===monitorPerson);
 const groups=currentProgress().teams.map(e=>{const checks=monitorChecks(e);return {group:e.group,attention:checks.filter(c=>monitorStatus(c)[0]==='attention').length,review:checks.filter(c=>monitorStatus(c)[0]==='review').length,footer:'<span>'+e.submitted+' / '+e.total+' shared</span>'}});
 return '<div class="rh-overview-top">'+rhStageBar()+classroomLegend()+'</div>'+rhAlertStrip()+'<div class="classroom-space '+(selected?'with-inspector':'')+'">'+classroomMapHTML(people,groups,monitorPerson)+(selected?monitorPersonPanel(selected):'')+'</div>';
};
async function rhAct(body,message){
 if(progressPreview)return toast('Switch to Class work to do this.');
 try{await api('/api/host/rule-action',body);await reload(true);drawMonitor();if(message)toast(message)}catch(e){toast(e.message,true)}
}
async function rhExtend(){
 try{await api('/api/host/live',{command:'extend',minutes:2});await reload(true);drawMonitor();toast('2 minutes added to “'+rhClock().phase.title+'”.')}catch(e){toast(e.message,true)}
}
function rhBind(){
 const p=currentProgress(),e=p.teams.find(e=>e.group===monitorTeam),c=e&&monitorView==='progress'?monitorChecks(e).find(c=>c.id===monitorRule):null;
 const classSignal=!c&&monitorView==='progress'&&rhClassRule?rhClassSignals().find(s=>s.id===rhClassRule):null,signal=c||classSignal,scope=c?e.group:'class';
 $$('[data-rh-alert]').forEach(b=>b.onclick=()=>{const [g,id]=b.dataset.rhAlert.split('|');if(g==='class'){rhClassRule=id;monitorTeam=null;monitorRule='';monitorPerson='';drawMonitor()}else teamDetail(+g,id)});
 $('#rhExtend')?.addEventListener('click',rhExtend);$('#rhExtendHere')?.addEventListener('click',rhExtend);
 $('#rhClassBack')?.addEventListener('click',()=>{rhClassRule='';drawMonitor()});
 $$('[data-rh-class-rule]').forEach(b=>b.onclick=()=>{rhClassRule=b.dataset.rhClassRule;drawMonitor()});
 $$('[data-rh-team]').forEach(b=>b.onclick=()=>teamDetail(+b.dataset.rhTeam));
 $$('[data-rh-carry-remove]').forEach(b=>b.onclick=()=>rhAct({kind:'carry-remove',id:b.dataset.rhCarryRemove},'Removed from next time.'));
 $$('[data-rh-carry-add]').forEach(b=>b.onclick=()=>{const id=b.dataset.rhCarryAdd,rule=p.rules.find(r=>r.id===id);rhAct({kind:'carry',ruleId:id,note:rule?.nextTime||rhLib().seeds[id]?.nextTime||'',enable:true},'Saved for next time.')});
 $('#rhDrafts')?.addEventListener('click',savedProgressDrafts);
 if(signal){
  $('#rhHandle')?.addEventListener('click',()=>rhAct({kind:'handle',group:scope,ruleId:signal.id,key:signal.key,note:$('#rhHandleNote').value},'Marked as handled. The alert returns if the evidence changes.'));
  $('#rhReopen')?.addEventListener('click',()=>rhAct({kind:'reopen',group:scope,ruleId:signal.id},'Alert reopened.'));
  $('#rhNextSave')?.addEventListener('click',()=>rhAct({kind:'carry',ruleId:signal.id,note:$('#rhNextNote').value,observed:signal.observed||'',group:scope==='class'?null:scope,enable:true},'Saved for next time. This class is unchanged.'));
  $('#rhPick')?.addEventListener('click',()=>rhAct({kind:'explainer-pick',group:scope},'Another member was picked to explain.'));
 }
 if(c&&e.support&&c.pattern==='comparison'){
  const resolve=async inPerson=>{if(progressPreview)return toast('Use Class work to record a review.');try{await api('/api/host/progress-support',{kind:'resolve',group:e.group,inPerson,note:$('#progressResolveNote').value});await reload(true);drawMonitor();toast('Review recorded. The first answers are kept.')}catch(err){toast(err.message,true)}};
  $('#progressResolve')?.addEventListener('click',()=>resolve(false));$('#frameworkInPerson')?.addEventListener('click',()=>resolve(true));
  $('#rhSupportOpen')?.addEventListener('click',()=>frameworkInspect(e.group,e.support.targets[0]));
 }
}
const rhDrawBase=drawMonitor;
drawMonitor=function(){
 if(!currentProgress()||!rhOn())return rhDrawBase();
 const context=[progressPreview,monitorView,monitorTeam,monitorRule,monitorChange,rhClassRule].join('|'),kept={};
 if($('#overlay .monitor-modal')&&context===rhContext)for(const el of $$('#monitorMain textarea[id]'))if(!el.disabled)kept[el.id]=el.value;
 rhSync();rhDrawBase();rhBind();
 rhContext=[progressPreview,monitorView,monitorTeam,monitorRule,monitorChange,rhClassRule].join('|');rhSeenSig=rhSignature();
 if(rhContext===context)for(const [id,value] of Object.entries(kept)){const el=document.getElementById(id);if(el&&!el.disabled&&value&&el.value!==value)el.value=value}
};
const rhTeamModalBase=teamModal;
teamModal=function(){rhClassRule='';return rhTeamModalBase()};
const rhTeamDetailBase=teamDetail;
teamDetail=function(group,id){
 if(rhOn()&&currentProgress()){
  rhClassRule='';
  /* Coming back from a preview or a message returns to the rule that was open. */
  if(!id&&monitorTeam===group&&monitorRule&&currentProgress().teams.find(e=>e.group===group)?.signals.some(s=>s.id===monitorRule))id=monitorRule;
 }
 return rhTeamDetailBase(group,id);
};
const rhMessageBase=frameworkMessage;
frameworkMessage=function(group){
 rhMessageBase(group);if(!rhOn())return;
 const rule=monitorTeam===group?monitorRule:'',draft=rhAsk[rule],box=$('#frameworkMessageText');
 if(draft&&box)box.value=draft;
 const back=$('#frameworkMessageBack');if(back)back.onclick=()=>teamDetail(group,rule||undefined);
};
/* Badge on the Dashboard button, a record of each new alert, and a redraw when an alert changes without a save. */
function rhAttention(){const p=data.progress;return (p.classSignals||[]).filter(s=>s.status==='attention').length+p.teams.reduce((n,e)=>n+monitorChecks(e).filter(c=>monitorStatus(c)[0]==='attention').length,0)}
function rhLogSeen(){
 const p=data.progress,items=[],known=new Set((p.log||[]).map(i=>i.group+'|'+i.ruleId+'|'+i.key));
 const add=(group,s)=>{const k=group+'|'+s.id+'|'+s.key;if(s.status==='attention'&&s.key&&!known.has(k)&&!rhLogged.has(k)){rhLogged.add(k);items.push({group,ruleId:s.id,key:s.key})}};
 for(const s of p.classSignals||[])add('class',s);
 for(const e of p.teams)for(const s of e.signals||[])add(e.group,s);
 if(items.length)api('/api/host/rule-action',{kind:'seen',items}).catch(()=>{});
}
setInterval(()=>{
 if(!data?.progress||!rhOn())return;
 const button=$('#teamsButton');if(button){const n=rhAttention();if(n)button.dataset.alerts=n;else delete button.dataset.alerts}
 rhLogSeen();
 const clock=$('[data-rh-clock]');if(clock)clock.textContent=rhClockText(rhClock());
 if(!$('#overlay .monitor-modal')||document.activeElement?.matches('textarea,input,select')||rhSignature()===rhSeenSig)return;
 const scroll=$('#monitorMain')?.scrollTop;drawMonitor();if($('#monitorMain'))$('#monitorMain').scrollTop=scroll;
},1000);

/* ------------------------------------------------------------------ storyboard */
/* Every stage of every role on one fixed grid. The canvas stays the place to arrange and edit. */
let rhStoryObserver=null;
function rhStoryURL(person,phase){return '/student.html?preview=1&admin='+encodeURIComponent(admin)+'&person='+encodeURIComponent(person)+'&phase='+encodeURIComponent(phase)+(canvasClassWork?'&inspect=1':'')+'&focusWork=1'}
function rhStoryboard(){
 if(!data.plan.planned)return toast('Generate the activity first.');
 const group=canvasClassWork?previewGroup:0,people=activePeople().filter(p=>p.group===group),phases=data.plan.phases,rules=(data.progress?.rules||[]).filter(r=>r.enabled),lib=data.progress?.library;
 const role=p=>data.plan.tasks.find(t=>t.assignees.includes(p.slot))?.title||'Learner '+String.fromCharCode(65+p.slot);
 const chips=phase=>rules.filter(r=>r.phaseId===phase.id).map(r=>{const seed=lib?.seeds[r.id]||(lib&&Object.values(lib.seeds).find(s=>s.condition===r.condition&&r.condition!=='teacher_review'));return '<i class="'+(seed?.adds?'adds':'')+'" title="'+esc(r.title)+'">'+esc(seed?.short||r.title)+'</i>'}).join('');
 const head='<div class="rh-story-corner"></div>'+phases.map((phase,i)=>'<header class="rh-story-stage"><span>'+(i+1)+'</span><div><h3>'+esc(phase.title)+'</h3><p>'+(phase.kind==='individual'?'On their own':'Together')+' · '+phase.minutes+' min</p></div>'+(rules.length?'<div class="rh-story-rules">'+(chips(phase)||'<em>No rule watches this stage</em>')+'</div>':'')+'</header>').join('');
 const rows=people.map(p=>'<div class="rh-story-role"><span class="avatar">'+String.fromCharCode(65+p.slot)+'</span><strong>'+esc(role(p))+'</strong></div>'+phases.map(phase=>'<div class="rh-cell"><iframe loading="lazy" tabindex="-1" aria-hidden="true" title="'+esc(role(p)+' · '+phase.title)+'" src="'+rhStoryURL(p.id,phase.id)+'"></iframe><button data-rh-cell="'+esc(p.id)+'|'+esc(phase.id)+'" aria-label="Open '+esc(role(p)+' · '+phase.title)+'"></button></div>').join('')).join('');
 showModal(modalHead('Storyboard',(canvasClassWork?'Class work · Team '+(group+1)+' · read only':'Rehearsal previews')+' · every role at every stage')+'<div class="rh-story-legend"><span><i class="adds"></i>Rule adds something to the student page</span><span><i></i>Rule reads saved work only</span></div><div class="rh-story-scroll"><div class="rh-story-grid" style="--rh-stages:'+phases.length+'">'+head+rows+'</div></div>','rh-story-modal');
 const fit=()=>$$('.rh-cell').forEach(cell=>cell.style.setProperty('--rh-scale',cell.clientWidth/1180));
 rhStoryObserver?.disconnect();rhStoryObserver=new ResizeObserver(fit);const grid=$('.rh-story-grid');if(grid)rhStoryObserver.observe(grid);fit();
 $$('[data-rh-cell]').forEach(b=>b.onclick=()=>{const [id,phase]=b.dataset.rhCell.split('|'),p=people.find(p=>p.id===id),stage=phases.find(s=>s.id===phase);
  showModal(modalHead(role(p)+' · '+stage.title,canvasClassWork?'Class work · read only':'Rehearsal preview')+'<div class="rh-story-back"><button id="rhStoryBack">← Storyboard</button></div><iframe class="studio-full-preview" title="Full-size learner preview" src="'+rhStoryURL(id,phase).replace('&focusWork=1','')+'"></iframe>','studio-page-modal');
  $('#rhStoryBack').onclick=rhStoryboard});
}
const rhToolbarBase=renderGuideToolbar;
renderGuideToolbar=function(){
 rhToolbarBase();
 if(data.plan.planned&&!$('#rhStoryboardButton')){$('#openPlanDetails')?.insertAdjacentHTML('afterend','<button id="rhStoryboardButton">Storyboard</button>');$('#rhStoryboardButton')?.addEventListener('click',rhStoryboard)}
};
