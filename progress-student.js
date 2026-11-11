/* Private checks, scoped support, and visible handoffs. No speech is inferred. */
let progressDraft={initial:{},followup:{}},progressPageKey='';
function progressQuestion(kind){
 const p=data.progress,q=p.questions[kind],saved=p.answers[kind],draft=progressDraft[kind];
 if(saved)return '<div class="progress-check-saved"><span class="progress-check-icon">✓</span><div><strong>'+(kind==='initial'?'Your individual check is saved.':'Your follow-up answer is saved.')+'</strong><p>'+esc(q.options.find(x=>x[0]===saved.answer)?.[1]||'')+'</p><small>Your teacher can review your answer and reason.</small></div></div>';
 return '<form class="progress-check-form" data-check-form="'+kind+'"><span class="progress-kicker">'+(kind==='initial'?'INDIVIDUAL CHECK':'PRIVATE FOLLOW-UP')+'</span><h2>'+esc(q.prompt)+'</h2><div class="progress-options">'+q.options.map(([value,label])=>'<label><input type="radio" name="'+kind+'Answer" value="'+value+'" '+(draft.answer===value?'checked':'')+' required><span>'+esc(label)+'</span></label>').join('')+'</div><label class="progress-reason-label">Your reason<textarea id="'+kind+'Reason" data-progress-reason="'+kind+'" placeholder="Use a label or unit from the story." required>'+esc(draft.reason||'')+'</textarea></label><div class="progress-submit"><small>Private to you and your teacher.</small><button class="studio-primary" type="submit">'+(kind==='initial'?'Save individual check':'Save follow-up answer')+'</button></div></form>';
}
function progressStudentHTML(){
 const p=data.progress;if(!p)return '';
 let h='';if(p.config.privateCheck&&stage().id===p.phase)h+=progressQuestion('initial');
 if(p.support?.resolved)h+='<div class="progress-check-saved"><span class="progress-check-icon">✓</span><div><strong>Your teacher has reviewed the follow-up.</strong><p>Continue with your role work. Your original notes are kept.</p></div></div>';
 else if(p.support){const m=data.materials.find(m=>m.id===data.plan.materialId),s=p.support;h+='<section class="progress-support"><div class="progress-support-heading"><span class="progress-kicker">FROM YOUR TEACHER · TEAM '+(data.person.group+1)+'</span><strong>'+esc(s.title)+'</strong></div><p>'+esc(s.prompt)+'</p><div class="progress-compare">'+[0,6].map(i=>'<figure><img src="'+esc(m.images?.[i]||m.image)+'" alt="Voting story frame '+(i+1)+'"><figcaption>Frame '+(i+1)+' · '+esc(m.frameLabels?.[i]||'')+'</figcaption></figure>').join('')+'</div>'+(s.resolved?'<p class="progress-addressed">Your teacher has reviewed the follow-up. Continue with your role work.</p>':s.needsFollowup?progressQuestion('followup'):'<p class="progress-support-note">Discuss which people each frame counts. Continue with your role work.</p>')+'</section>'}
 return h?'<div class="progress-student-area">'+h+'</div>':'';
}
const progressBaseRender=render;
render=function(){
 if(data?.progress&&preview&&params.get('forceFlow')==='group-first'&&!data.progress.config.checkPhase)data.progress.phase='discuss';
 const key=data?data.person.id+':'+stage().id:'';if(key!==progressPageKey){progressDraft={initial:{},followup:{}};progressPageKey=key}
 const active=document.activeElement,focused=active?.id,selection=active?.selectionStart;
 progressBaseRender();if(!data?.progress||!document.querySelector('.editorial-page'))return;
 const p=data.progress,workspace=document.querySelector('.studio-workspace');
 const roleColumn=workspace.lastElementChild,column=document.createElement('div');column.className='progress-work-column';workspace.insertBefore(column,roleColumn);column.innerHTML=progressStudentHTML();column.appendChild(roleColumn);
 if(p.config.beforeDiscussion&&stage().id===p.phase&&!p.answers.initial){const opening=document.querySelector('.workflow-opening');if(opening)opening.innerHTML='<span class="progress-kicker">BEFORE THE DISCUSSION</span><h2>Start with your own reading.</h2><p>Save the private check above. Then open your group’s shared reading.</p>'}
 if(data.plan.studio?.adaptedBriefs){const task=assignedTasks()[0],roleWork=document.querySelector('.workflow-role-work');if(task&&roleWork)roleWork.insertAdjacentHTML('afterbegin','<aside class="progress-role-brief"><strong>Your role brief</strong><p>'+esc(task.prompt)+'</p></aside>')}
 document.querySelectorAll('[data-check-form]').forEach(form=>{
  const kind=form.dataset.checkForm;
  form.addEventListener('input',()=>{progressDraft[kind]={answer:form.querySelector('input:checked')?.value||'',reason:form.querySelector('textarea').value}});
  form.onsubmit=async e=>{e.preventDefault();const button=form.querySelector('button');button.disabled=true;try{const result=await api('/api/progress/answer',{kind,...progressDraft[kind],phaseId:stage().id});data.progress.answers[kind]=result.answer;progressDraft[kind]={};notice(document.querySelector('.offline-banner')?'Saved on this device only.':'Saved privately for your teacher.');render()}catch(e){notice(e.message);button.disabled=false}};
 });
 if(focused&&/^(initial|followup)Reason$/.test(focused)){const el=document.getElementById(focused);if(el){el.focus({preventScroll:true});el.setSelectionRange(selection,selection)}}
};
if(!document.querySelector('.offline-banner'))refresh();
/* Notify only the instructor tutorial frame; send no answer contents. */
const coachProgressRenderBase=render;
render=function(){coachProgressRenderBase();if(parent!==window&&/^https?:$/.test(location.protocol))parent.postMessage({type:'coach-student-progress'},location.origin)};

/* Live instructor inspection cannot submit or change a learner’s work. */
const inspectedProgressRender=render;
render=function(){
 inspectedProgressRender();if(!data?.instructorReadOnly)return;
 document.querySelectorAll('input,textarea,select').forEach(el=>{if(el.id!=='compareFrame')el.disabled=true});
 document.querySelectorAll('#app button').forEach(b=>{if(!b.matches('[data-studio-stage],[data-studio-frame],[data-stage],#toggleCompare,#expandStory,#returnPrepare,#goToOpening,#goToRoleWork'))b.disabled=true});
 const label=document.querySelector('.preview-label');if(label)label.textContent='Class work · read only';
};
