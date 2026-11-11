/* Inspect the same saved work in read-only before/after snapshots before applying. */
let supportComparison=null,supportComparisonSerial=0;
function interfaceChangeStory(pattern){return {
 'scaffold':{title:'Break the role task into smaller steps',change:'Keep the role tools. Add three prompts: read the unit, identify who is counted, then explain the changing area.',why:'Gives a learner who asked for help a concrete starting point. Their shared findings still feed the team critique.',recheck:'Read the three answers and the resulting role contribution. Check the interpretation, not just completion.'},
 'written-exchange':{title:'Bring the unanswered question into the critique',change:'Place the Reader’s original question beside shared writing. Add a direct answer and an evidence field.',why:'Makes the overlooked question visible where the team is working and records which response addresses it.',recheck:'Compare the response with the original question and cited evidence. Check whether it changes the critique.'},
 'reason-check':{title:'Test the reasoning behind agreement',change:'Add a counterfactual: could a map shrink while total residents stay the same? Ask for an explanation and a linked peer reply.',why:'Reveals reasons behind matching choices. The team tests its interpretation without being forced to disagree.',recheck:'Read the explanation and the peer reply. Check whether they distinguish a smaller subset from falling population.'},
 'comparison':{title:'Compare who the frames count',change:'Add first-and-last-frame comparison for this team and a new individual check for learners needing support.',why:'Makes the population filter explicit before checking whether each learner can interpret another example.',recheck:'Read the new individual answers and reasons; keep the original answers visible.'}
 }[pattern]||{title:'Review the proposed change',change:'Inspect the revised task and connected handoff.',why:'Check that the change responds to the evidence.',recheck:'Review the resulting student work.'}}
const legacyComparisonPreview=supportPreview,legacyAdaptiveComparison=adaptivePreview;
function comparisonRole(p){return data.plan.tasks.find(t=>t.assignees.includes(p.slot))?.title||p.name}
function comparisonFinding(e){const groups={};for(const r of e.rows.filter(r=>r.initial&&!r.initial.correct)){const choice=frameworkChoice(r.initial.answer);(groups[choice]??=[]).push(r.name.replace(' (example)',''))}return Object.entries(groups).map(([choice,names])=>names.join(' and ')+' chose “'+choice+'”').join(' ')}
function comparisonURL(side){const c=supportComparison;return '/student.html?preview=1&admin='+encodeURIComponent(admin)+'&person='+encodeURIComponent(c.person)+'&testRun='+encodeURIComponent(c.run[side])+'&phase='+encodeURIComponent(c.phase)}
function comparisonScroll(frame,side){
 let attempts=0;const timer=setInterval(()=>{
  const c=supportComparison;if(!frame.isConnected||!c){clearInterval(timer);return}
  const selector=side==='after'?(c.pattern==='comparison'?'.progress-support':'[data-adaptive-card="'+c.run.additionId+'"]'):'.workflow-role-work';
  const el=frame.contentDocument?.querySelector(selector);
  if(el){const doc=frame.contentDocument;doc.scrollingElement.scrollTop=Math.max(0,el.getBoundingClientRect().top+doc.scrollingElement.scrollTop-12);clearInterval(timer)}else if(++attempts>50)clearInterval(timer);
 },60);
}
function drawSupportComparison(){
 const c=supportComparison;if(!c)return;progressScreen='support-comparison';
 const e=data.progress.teams[c.group],person=c.run.people.find(p=>p.id===c.person),names=c.run.targets.map(id=>c.run.people.find(p=>p.id===id)?.name||comparisonRole(c.run.people.find(p=>p.id===id))).join(', ');
 const description=c.pattern==='scaffold'?'Only '+names.replaceAll(' (example)','')+' receives the smaller-step task.':'Applies to Team '+(c.group+1)+'.';
 showModal(modalHead('Preview change','Team '+(c.group+1)+' · not applied')+'<div class="support-compare-context"><div><span class="progress-kicker">WHY THIS CHANGE</span><p>'+esc(c.reason)+'</p></div><label>Student interface<select id="supportComparePerson">'+c.run.people.map(p=>option(p.id,comparisonRole(p)+' · '+(p.name||'Learner'),c.person)).join('')+'</select></label></div><div class="support-compare-grid">'+['before','after'].map(side=>'<section class="support-compare-card '+side+'"><header><div><span class="progress-kicker">'+side.toUpperCase()+'</span><h3>'+(side==='before'?'Current interface':'Proposed interface')+'</h3></div><button id="supportOpen'+(side==='before'?'Before':'After')+'">Open '+side+' ↗</button></header><iframe id="support'+(side==='before'?'Before':'After')+'Frame" title="'+(side==='before'?'Before':'After')+' student interface" src="'+comparisonURL(side)+'"></iframe></section>').join('')+'</div><div class="support-compare-scope"><p>'+esc(description)+'</p><details><summary>Recipients and saved work</summary><p>'+(c.pattern==='comparison'?'All four role interfaces in this team receive the comparison. Private follow-ups: ':'Assigned: ')+esc(names)+'. Original answers and role work are retained.</p></details></div><p id="supportCompareFeedback" role="status"></p><div class="progress-modal-actions"><button id="progressSupportBack">Back to evidence</button><button id="progressApplySupport" class="primary">'+(c.pattern==='scaffold'&&c.run.targets.length===1?'Apply to '+names.replace(' (example)',''):'Apply to Team '+(c.group+1))+'</button></div>','support-comparison-modal');
 const story=interfaceChangeStory(c.pattern);$('.support-compare-context').insertAdjacentHTML('beforebegin','<section class="support-change-explanation"><div><b>What changes</b><p>'+esc(story.change)+'</p></div><div><b>How this responds</b><p>'+esc(story.why)+'</p></div></section>');
 $('#supportComparePerson').onchange=ev=>{c.person=ev.target.value;drawSupportComparison()};
 for(const side of ['before','after']){const frame=$('#support'+(side==='before'?'Before':'After')+'Frame');frame.onload=()=>comparisonScroll(frame,side);$('#supportOpen'+(side==='before'?'Before':'After')).onclick=()=>openSupportComparison(side)}
 $('#progressSupportBack').onclick=()=>teamDetail(c.group);
 $('#progressApplySupport').onclick=async()=>{const button=$('#progressApplySupport');button.disabled=true;try{
  if(c.pattern==='comparison')await api('/api/host/progress-support',{kind:'support',group:c.group,expectedTargets:c.run.targets,expectedPlanRev:c.run.planRev});
  else await api('/api/host/adaptive-apply',{...c.run.proposal,note:c.reason});
  await reload(true);teamDetail(c.group);toast('Applied to Team '+(c.group+1)+'. Existing work is retained.');
 }catch(error){$('#supportCompareFeedback').textContent=error.message;button.disabled=false}};
}
function openSupportComparison(side){
 const c=supportComparison,person=c.run.people.find(p=>p.id===c.person);progressScreen='support-full-'+side;
 showModal(modalHead((side==='before'?'Before':'After')+' · '+comparisonRole(person),'Same student and saved work · preview only')+'<div class="support-full-toolbar"><button id="supportCompareBack">← Back to comparison</button><span>'+esc(person.name||comparisonRole(person))+'</span></div><iframe id="supportFullFrame" title="'+(side==='before'?'Before':'After')+' full student interface" src="'+comparisonURL(side)+'"></iframe>','support-full-modal');
 $('#supportCompareBack').onclick=drawSupportComparison;$('#supportFullFrame').onload=()=>comparisonScroll($('#supportFullFrame'),side);
}
async function prepareSupportComparison(group,pattern,targets,note){
 if(progressPreview)return toast('Use Class work to preview a live change.');
 const serial=++supportComparisonSerial,e=data.progress.teams[group],people=activePeople().filter(p=>p.group===group),requests=e.adaptive?.requests||[];
 const requested=requests.filter(r=>r.requestKind==='difficulty').map(r=>r.person);
 const chosen=targets||(pattern==='comparison'?e.rows.filter(r=>r.initial&&!r.initial.correct).map(r=>r.person):pattern==='scaffold'?(requested.length?[...new Set(requested)]:[people[0].id]):people.map(p=>p.id));
 const reason=note||(pattern==='comparison'?comparisonFinding(e):pattern==='scaffold'?(requests.find(r=>r.requestKind==='difficulty')?.text||'The instructor wants a smaller first step while retaining the role task.'):pattern==='written-exchange'?(requests.find(r=>r.requestKind==='participation')?.text||'The instructor wants each contribution to receive a direct response.'):'All learners chose the same answer. Check their reasoning before deciding whether more discussion is useful.');
 showModal(modalHead('Preparing comparison','Preserving the same student work')+'<div class="support-compare-loading" role="status">Opening before and after interfaces…</div>','support-comparison-modal');
 try{const run=await api('/api/host/support-comparison',{group,pattern,targets:chosen,note:reason});if(serial!==supportComparisonSerial)return;supportComparison={group,pattern,run,reason,person:chosen[0]||run.people[0].id,phase:data.plan.live.phaseId};drawSupportComparison()}catch(error){if(serial===supportComparisonSerial){$('#overlay .modal').innerHTML=modalHead('Could not preview',error.message)+'<button id="supportErrorBack">Back to evidence</button>';$('#supportErrorBack').onclick=()=>teamDetail(group)}}
}
supportPreview=function(group){return fullActivityTour?legacyComparisonPreview(group):prepareSupportComparison(group,'comparison')};
adaptivePreview=function(group,pattern,targets,note){return fullActivityTour?legacyAdaptiveComparison(group,pattern,targets,note):prepareSupportComparison(group,pattern,targets,note)};
