/* A compact framework view: rule → evidence → teacher response → recheck. */
const fullActivityTour=new URLSearchParams(location.search).get('tour')==='activity';
const frameworkRuleNames={'role-work':'Each learner shares their work','reading-check':'Correctly identify why the maps shrink','peer-use':'Peer questions receive a response','participation':'Everyone can contribute','support-request':'Learners can request support','answer-pattern':'Review reasons behind agreement','role-clarity':'Each learner knows their next step','workload-balance':'Workload fits the roles and time','resolve-disagreement':'Disagreements receive a response','specific-feedback':'Feedback names a concrete example'};
const frameworkRuleCopy={
 'role-work':['Missing submission near the end of role work.','Clarify the task or offer smaller steps.','Read the new contribution.'],
 'reading-check':['Flag an initial MCQ choice that does not identify population filtering.','Compare who the frames count, then recheck flagged learners.','Review the follow-up choice and reason.'],
 'peer-use':['A peer question has no response.','Invite a response or open a written exchange.','Check how the team used the response.'],
 'participation':['A learner request or teacher observation.','Offer another way to contribute.','Ask whether the change helped.'],
 'support-request':['A private request for help.','Offer smaller steps or a written exchange.','Review subsequent work with the learner.'],
 'answer-pattern':['Everyone chose the same answer.','Inspect reasons before changing the activity.','Keep the task or check the reasoning.'],
 'role-clarity':['A learner cannot explain their role or next step.','Clarify the brief and the handoff.','Ask the learner to describe what they will do.'],
 'workload-balance':['Workload concerns in a learner report or teacher observation.','Reassign a part, reduce scope or adjust time.','Check whether each role can make progress.'],
 'resolve-disagreement':['A disputed claim remains unanswered.','Open a focused exchange or join the group.','Inspect the response or record the unresolved point.'],
 'specific-feedback':['Feedback gives a rating without a concrete example.','Ask for the contribution and reason behind the judgment.','Read the revised feedback.']
};
const compactRuleEditorBase=drawRuleEditor;
drawRuleEditor=function(){
 compactRuleEditorBase();const r=ruleDraft.find(x=>x.id===ruleSelected);if(!r)return;
 if(!fullActivityTour){
  const root=$('#ruleEditor'),heading=root.querySelector('h3');if(heading)heading.textContent=frameworkRuleNames[r.id]||r.title;
  const notes=frameworkRuleCopy[r.id];if(notes)root.querySelectorAll('.adaptive-rule-summary dd').forEach((el,i)=>el.textContent=notes[i]);
  const kicker=root.querySelector('.progress-kicker');if(kicker)kicker.textContent=r.condition==='teacher_review'?'Teacher review':'Automatic signal';
  $('.rule-planner-modal .adaptive-loop')?.remove();
  $('.rule-planner-modal .modal-header p')?.remove();
  $('.rule-planner-top .progress-kicker')?.remove();
  const refresh=$('#ruleSuggest'),about=$('.rule-planner-footer details');if(refresh&&about)about.appendChild(refresh);
  $$('[data-rule-select]').forEach(b=>{const n=frameworkRuleNames[b.dataset.ruleSelect];if(n)b.querySelector('strong').innerHTML=esc(n)});
 }
};
const detailedFrameworkTeam=teamDetail;
function frameworkMainSignal(e){
 if(e.support)return e.signals.find(s=>s.id==='reading-check');
 return e.signals.find(s=>s.status==='attention'&&s.id==='reading-check')||e.signals.find(s=>s.status==='attention')||e.signals.find(s=>s.status==='needs-review');
}
function frameworkChoice(answer,kind='initial'){return currentProgress().questions[kind].options.find(o=>o[0]===answer)?.[1]||'Not saved'}
function frameworkRuleCode(id){const rows=currentProgress()?.rules||data.progress?.rules||[];const i=rows.findIndex(r=>r.id===id);return i<0?'':('R'+(i+1))}
function frameworkReadingEvidence(e){
 const q=currentProgress().questions.initial,correct=q.options.find(o=>o[0]===q.answer)?.[1]||'Each frame keeps a smaller group of people.';
 const groups=new Map();for(const row of e.rows.filter(r=>r.initial&&!r.initial.correct)){const key=row.initial.answer;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(row)}
 return '<div class="rule-expectation" id="frameworkRuleExpected"><h3>Expected · '+e.total+' of '+e.total+' correct</h3><strong>“'+esc(correct)+'”</strong></div><div class="rule-observed" id="frameworkRuleObserved"><h3>Observed · '+(e.answered-e.wrong)+' of '+e.answered+' correct</h3>'+[...groups].map(([answer,rows])=>{
 const why=answer==='time'?'The frames count different population groups, not the same population at later dates.':answer==='land'?'Area represents the number of people, not geographic land area.':'This choice does not match the population group shown by the frame labels.';
 return '<article><p class="rule-learner-names">'+esc(rows.map(r=>r.name.replace(' (example)','')).join(' and '))+' chose:</p><blockquote>“'+esc(frameworkChoice(answer))+'”</blockquote><div class="rule-failure-reason"><p><b>Not met because:</b> '+esc(why)+'</p></div><details><summary>Read student reasons</summary>'+rows.map(r=>'<p><b>'+esc(r.name)+'</b>: '+esc(r.initial.reason)+'</p>').join('')+'</details></article>'}).join('')+(e.answered<e.total?'<p class="rule-pending">'+(e.total-e.answered)+' answers are still pending; they are not counted as incorrect.</p>':'')+'</div>';
}
teamDetail=function(group){
 if(fullActivityTour||!currentProgress())return detailedFrameworkTeam(group);
 progressScreen='detail';progressGroup=group;
 const e=currentProgress().teams[group],signal=frameworkMainSignal(e),support=e.support,rows=e.rows.filter(r=>r.initial&&!r.initial.correct),requests=e.adaptive?.requests||[],ruleTitle=frameworkRuleNames[signal?.id]||signal?.title||'Activity progress';
 const resolved=Boolean(support?.resolved),reading=Boolean(signal?.id==='reading-check'||support),same=signal?.id==='answer-pattern',needs=signal?.status==='attention';
 let status=resolved?'Reviewed':support?'Recheck in progress':same?'Review reasons':needs?'Rule not met':'Needs review';
 const headline=resolved?'Support reviewed':support?e.followupCount+' / '+support.targets.length+' follow-ups saved':reading?'Identify population filtering':same?'Everyone chose the same answer':requests.length?requests.length+' support request'+(requests.length===1?'':'s'):'Check the activity';
 const evidence=reading&&!support?frameworkReadingEvidence(e):reading?'<div class="framework-answer-list">'+rows.map(r=>'<article><header><strong>'+esc(r.name)+'</strong><span>'+esc(r.role)+'</span></header><div><p><b>Initial</b>'+esc(frameworkChoice(r.initial.answer))+'</p>'+(support?'<p><b>After support</b>'+esc(r.followup?frameworkChoice(r.followup.answer,'followup'):'Waiting for a follow-up')+'</p>':'')+'</div><details><summary>Reason</summary><p>'+esc(r.initial.reason)+'</p>'+(r.followup?'<p>'+esc(r.followup.reason)+'</p>':'')+'</details></article>').join('')+'</div>':requests.length?requests.map(r=>'<p class="framework-request">'+esc(r.text)+'</p>').join(''):'<p class="framework-summary">'+esc(signal?.detail||'Open the saved work or record an observation.')+'</p>';
 const finding='';
 const suggestion=reading?'Make the population filters clear':requests.some(r=>r.requestKind==='difficulty')?'Offer smaller steps':requests.some(r=>r.requestKind==='participation')?'Open a written exchange':same?'Inspect their reasons':'Check with this team';
 const suggestionText=reading?'Show who frames 1 and 7 count. Then ask '+e.rows.filter(r=>r.initial&&!r.initial.correct).map(r=>r.name.replace(' (example)','')).join(' and ')+' to answer a new question independently.':same?'Agreement can be appropriate. Review explanations first.':(signal?.response||'Choose a response after checking the context.');
 showModal(modalHead('Team '+(group+1),'')+'<div class="framework-detail-toolbar"><button id="progressBack">← Teams</button><div><button id="progressWork">Open interfaces</button><button id="ruleEditFromTeam">Edit rules</button></div></div><div class="framework-progress-layout"><section class="framework-evidence"><span class="framework-state '+(resolved?'resolved':'')+'">'+esc(frameworkRuleCode(signal?.id||'reading-check'))+' · '+status+'</span><h2 id="frameworkRuleTitle">'+headline+'</h2><p class="framework-rule-label">'+(reading&&!support?'':esc(ruleTitle))+'</p>'+finding+evidence+'</section><section class="framework-response"><span class="progress-kicker">'+(support?'AFTER INTERVENTION':'SYSTEM SUGGESTS')+'</span><h2>'+(support?'Review the follow-up':suggestion)+'</h2>'+(support?(resolved?'<p class="framework-summary">'+esc(support.note)+'</p>':'<p class="framework-summary">'+e.followupCorrect+' of '+support.targets.length+' answered correctly.</p><label>Teacher review<textarea id="progressResolveNote" placeholder="What did you verify?"></textarea></label><button id="progressResolve" class="primary" '+(e.followupCount<support.targets.length||e.followupCorrect<support.targets.length?'disabled':'')+'>Mark addressed</button><button id="frameworkInPerson">Record an in-person check</button>')+'<button id="frameworkInspect">Open updated interface</button>':'<p class="framework-summary">'+suggestionText+'</p><button id="frameworkSuggested" class="primary">'+(reading?'Preview support':same?'Review reasons':requests.length?'Preview change':'Ask this team')+'</button><button id="frameworkMessage">Send a question</button>')+'<details class="framework-more"><summary>Other responses</summary><button data-framework-pattern="scaffold">Smaller steps</button><button data-framework-pattern="written-exchange">Written exchange</button><button data-framework-pattern="reason-check">Test the reasoning</button><button id="adaptiveKeep">Keep the activity</button><button id="frameworkDetailed">All evidence & controls</button></details></section></div><details class="framework-all-rules"><summary>All '+e.signals.length+' checks · '+e.signals.filter(s=>s.status==='attention').length+' need attention</summary>'+(e.signals||[]).map(s=>'<div><span>'+esc(frameworkRuleCode(s.id)+' · '+(frameworkRuleNames[s.id]||s.title))+'</span><b>'+esc({attention:s.id==='answer-pattern'?'Review reasons':'Needs attention',checked:'Checked',addressed:'Reviewed',collecting:'Collecting',waiting:'Waiting','needs-review':'Teacher review',review:'Evidence to read',inactive:'Not triggered'}[s.status]||s.status)+'</b>'+(s.condition==='teacher_review'?'<button data-framework-observe="'+esc(s.id)+'">Record observation</button>':'')+'</div>').join('')+'</details><div class="framework-future"><button id="progressNext">Save for next activity</button><button id="progressNextRun">Save for next run</button></div>','framework-detail-modal');
 $('#progressBack').onclick=teamModal;$('#progressWork').onclick=()=>frameworkInspect(group);$('#frameworkInspect')?.addEventListener('click',()=>frameworkInspect(group,rows[0]?.person));
 $$('[data-framework-observe]').forEach(b=>b.onclick=()=>ruleObservation(group,b.dataset.frameworkObserve));
 $('#ruleEditFromTeam').onclick=()=>progressRulesModal();$('#frameworkDetailed').onclick=()=>detailedFrameworkTeam(group);
 $('#frameworkSuggested')?.addEventListener('click',()=>{if(reading)return supportPreview(group);if(same){$('.framework-all-rules').open=true;return detailedFrameworkTeam(group)}if(requests.length)return adaptivePreview(group,requests.some(r=>r.requestKind==='difficulty')?'scaffold':'written-exchange');frameworkMessage(group)});
 $('#frameworkMessage')?.addEventListener('click',()=>frameworkMessage(group));$('#adaptiveKeep').onclick=()=>adaptiveKeep(group);
 $$('[data-framework-pattern]').forEach(b=>b.onclick=()=>adaptivePreview(group,b.dataset.frameworkPattern));
 const resolve=async inPerson=>{if(progressPreview)return toast('Use Class work to record a review.');try{await api('/api/host/progress-support',{kind:'resolve',group,inPerson,note:$('#progressResolveNote').value});await reload(true);teamDetail(group)}catch(err){toast(err.message,true)}};
 $('#progressResolve')?.addEventListener('click',()=>resolve(false));$('#frameworkInPerson')?.addEventListener('click',()=>resolve(true));
 $('#progressNext').onclick=()=>prepareProgressDraft('next-activity',group);$('#progressNextRun').onclick=()=>prepareProgressDraft('next-run',group);
};
function frameworkInspect(group,personId){
 canvasClassWork=!progressPreview;previewGroup=group;previewPhase=data.plan.live.phaseId;closeModal();setInspector(false);render();fit();
 const p=activePeople().find(p=>p.id===personId)||activePeople().find(p=>p.group===group);focusWindow(p.id);
}
function frameworkMessage(group){
 showModal(modalHead('Message Team '+(group+1),'')+'<label>Your question<textarea id="frameworkMessageText" placeholder="What would you like them to check?"></textarea></label><div class="progress-modal-actions"><button id="frameworkMessageBack">Back</button><button id="frameworkMessageSend" class="primary">Send</button></div>','framework-message-modal');
 $('#frameworkMessageBack').onclick=()=>teamDetail(group);$('#frameworkMessageSend').onclick=async()=>{const text=$('#frameworkMessageText').value.trim();if(!text)return toast('Write a question first.');if(progressPreview)return toast('Switch to Class work to send.');await api('/api/host/feedback',{group,text});await reload(true);teamDetail(group);toast('Sent to Team '+(group+1))};
}
