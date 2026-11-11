/* What the enabled progress rules add to a learner's page.
   Every control is visible to the learner. Private answers go to the teacher only. Nothing is recorded in the background
   except the time of a saved change and the length of a long paste, and the page says so. */
const ciDraft={},ciBeat={};
const ciTools=()=>data?.progress?.instruments;
const ciLocked=()=>Boolean(data?.instructorReadOnly||document.querySelector('.offline-banner'));
const ciSandbox=()=>preview&&(params.has('forceFlow')||params.has('forceReview')||params.has('forceExchange'));
const ciPick=(name,value,options)=>'<div class="ci-choice">'+options.map(([v,label])=>'<label><input type="radio" name="'+name+'" value="'+v+'" '+(value===v?'checked':'')+'><span>'+label+'</span></label>').join('')+'</div>';

function ciAuthors(t){
 const a=t.authors;if(!a||!document.querySelector('.workflow-critique'))return '';
 return '<p class="ci-authors">'+(a.names.length>1?'Edited by '+esc(a.names.slice(0,-1).join(', ')+' and '+a.names.at(-1)):a.names.length?'Edited by '+esc(a.names[0])+' only so far':'No saved version yet')+'</p>';
}
function ciSignoff(t){
 const s=t.signoff;if(!s||!document.querySelector('.workflow-critique'))return '';
 const d=ciDraft.signoff??={agree:s.mine?(s.mine.agree?'yes':'no'):'',note:''},current=s.entries.filter(e=>e.current).length,signed=s.mine&&s.mine.version===s.version;
 const rows=s.entries.map(e=>'<li class="'+(e.current?'':'stale')+'"><b>'+esc(e.mine?'You':e.name)+'</b><span>'+(e.agree?'agrees':'would change something')+(e.current?'':' · earlier version')+'</span><p>'+esc(e.note)+'</p></li>').join('');
 const body=!s.saved?'<p class="ci-quiet">Save the shared critique first.</p>':!s.canSign?'<p class="ci-quiet">You saved this version. A teammate signs off.</p>':
  '<form data-ci-form="signoff">'+ciPick('ciAgree',d.agree,[['yes','I agree'],['no','I would change something']])+'<textarea data-ci-input="signoff" aria-label="Reason for your sign-off" placeholder="One reason. Point to a frame or a sentence.">'+esc(d.note)+'</textarea><div class="ci-row"><small>'+(signed?'Your sign-off is saved for this version.':s.mine?'The critique changed after your sign-off.':'Your teammates see your sign-off.')+'</small><button class="studio-primary" type="submit">'+(signed?'Update sign-off':'Sign off')+'</button></div></form>';
 return '<section class="ci-card" data-ci="signoff"><header><h3>Second sign-off</h3><span class="ci-count '+(current>=s.required?'done':'')+'">'+current+' of '+s.required+'</span></header><p>A teammate who did not save this version reads it and gives one reason.</p>'+(rows?'<ul class="ci-list">'+rows+'</ul>':'')+body+'</section>';
}
function ciWhyNot(t){
 const w=t.whyNot;if(!w||!document.querySelector('.workflow-critique'))return '';
 const text=ciDraft.whynot??w.text;
 return '<section class="ci-card" data-ci="whynot"><header><h3>A reading we rejected or left open</h3></header><p>Name the other reading. Say why your team rejected it, or what would settle it.</p><textarea data-ci-input="whynot" aria-label="A reading we rejected or left open">'+esc(text)+'</textarea><div class="ci-row"><small>'+(w.saved?'Saved'+(w.by?' by '+esc(w.by):''):'Shared with your team.')+'</small><button class="studio-secondary" data-ci-save="whynot">Save note</button></div></section>';
}
function ciExplainer(t){
 const x=t.explainer;if(!x||stage().purpose!=='critique')return '';
 if(!x.picked)return '<section class="ci-card ci-plain" data-ci="explainer"><header><h3>One member will explain</h3></header><p>When the critique is saved, one member is picked at random to explain the team’s answer to the teacher. Make sure everyone can.</p></section>';
 if(!x.mine)return '<section class="ci-card ci-plain" data-ci="explainer"><header><h3>'+esc(x.name)+' explains your team’s answer</h3></header><p>The pick was random. '+esc(x.name)+' writes a short private explanation for the teacher.'+(x.done?' It is saved.':'')+'</p></section>';
 const text=ciDraft.explain??x.text;
 return '<section class="ci-card ci-focus" data-ci="explainer"><span class="progress-kicker">PRIVATE TO YOU AND YOUR TEACHER</span><header><h3>You were picked to explain</h3></header><p>The pick was random. What did your team decide, and what is one reason?</p><textarea data-ci-input="explain" aria-label="Your explanation of the team’s answer">'+esc(text)+'</textarea><div class="ci-row"><small>'+(x.done?'Saved. You can update it.':'Use your own words.')+'</small><button class="studio-primary" data-ci-save="explain">'+(x.done?'Update explanation':'Save explanation')+'</button></div></section>';
}
function ciPulse(t){
 const p=t.pulse;if(!p||!p.open||stage().id!==p.phaseId)return '';
 const d=ciDraft.pulse??={contributed:p.mine?.contributed||'',used:p.mine?.used||'',change:p.mine?.change||''},options=[['yes','Yes'],['partly','Partly'],['no','No']];
 return '<section class="ci-card ci-focus" data-ci="pulse"><span class="progress-kicker">PRIVATE TO YOU AND YOUR TEACHER</span><header><h3>Before you finish</h3></header><form data-ci-form="pulse"><fieldset><legend>Did you contribute to the team’s answer?</legend>'+ciPick('ciContributed',d.contributed,options)+'</fieldset><fieldset><legend>Was your work used?</legend>'+ciPick('ciUsed',d.used,options)+'</fieldset><label>One thing to change next time<textarea data-ci-input="pulse" aria-label="One thing to change next time">'+esc(d.change)+'</textarea></label><div class="ci-row"><small>'+(p.mine?'Saved. Teammates do not see this.':'Teammates do not see this.')+'</small><button class="studio-primary" type="submit">'+(p.mine?'Update':'Save')+'</button></div></form></section>';
}
function ciStatus(t){
 const s=t.status;if(!s||stage().id!==s.phaseId)return '';
 return '<section class="ci-status" data-ci="status"><label>Team status<input data-ci-input="status" maxlength="200" value="'+esc(ciDraft.status??'')+'" placeholder="One line: what is your team doing now?"></label><button class="studio-secondary" data-ci-save="status">Post</button>'+(s.text?'<p><b>'+esc(s.by||'Your team')+'</b> '+esc(s.text)+'</p>':'')+'</section>';
}
function ciNote(t){
 if(!t.paste)return '';
 return '<p class="ci-note">'+(t.paste.block?'Paste is off in answer fields for this activity.':'Long pastes into answer fields are noted for your teacher by length. The text is not copied.')+'</p>';
}
async function ciSend(body,after){
 if(ciLocked())return notice('Class work · read only');
 if(ciSandbox())return notice('Preview only · this does not change the class.');
 try{await api('/api/collab',body);after?.();await refresh(true)}catch(e){notice(e.message)}
}
const ciRenderBase=render;
render=function(){
 const active=document.activeElement,key=active?.dataset?.ciInput,selection=active?.selectionStart;
 ciRenderBase();
 const t=ciTools(),column=document.querySelector('.progress-work-column');if(!t||!column||document.querySelector('.offline-banner'))return;
 document.querySelector('.workflow-critique .studio-action-row')?.insertAdjacentHTML('afterend',ciAuthors(t));
 const top=ciStatus(t)+ciNote(t),bottom=ciSignoff(t)+ciWhyNot(t)+ciExplainer(t)+ciPulse(t);
 if(top){const area=document.createElement('div');area.id='ciTop';area.innerHTML=top;column.prepend(area)}
 if(bottom){const area=document.createElement('div');area.id='ciArea';area.innerHTML=bottom;column.append(area)}
 if(t.unheard)document.querySelector('.adaptive-help [data-support-request="visit"]')?.insertAdjacentHTML('beforebegin','<button data-ci-request="unheard">My point was not discussed</button>');
 document.querySelectorAll('[data-ci-input]').forEach(el=>el.oninput=()=>{const k=el.dataset.ciInput;if(k==='signoff')ciDraft.signoff.note=el.value;else if(k==='pulse')ciDraft.pulse.change=el.value;else ciDraft[k]=el.value});
 document.querySelectorAll('[data-ci-form] input[type=radio]').forEach(el=>el.onchange=()=>{if(el.name==='ciAgree')ciDraft.signoff.agree=el.value;if(el.name==='ciContributed')ciDraft.pulse.contributed=el.value;if(el.name==='ciUsed')ciDraft.pulse.used=el.value});
 const signoff=document.querySelector('[data-ci-form="signoff"]');
 if(signoff)signoff.onsubmit=e=>{e.preventDefault();const d=ciDraft.signoff;if(!d.agree)return notice('Choose “I agree” or “I would change something”.');if(!d.note.trim())return notice('Give one reason.');ciSend({kind:'signoff',version:t.signoff.version,agree:d.agree==='yes',note:d.note},()=>{delete ciDraft.signoff;notice('Sign-off saved for your team.')})};
 const pulse=document.querySelector('[data-ci-form="pulse"]');
 if(pulse)pulse.onsubmit=e=>{e.preventDefault();const d=ciDraft.pulse;if(!d.contributed||!d.used)return notice('Answer both questions.');ciSend({kind:'pulse',contributed:d.contributed,used:d.used,change:d.change},()=>{delete ciDraft.pulse;notice('Saved privately for your teacher.')})};
 document.querySelectorAll('[data-ci-save]').forEach(b=>b.onclick=()=>{const k=b.dataset.ciSave,text=(document.querySelector('[data-ci-input="'+k+'"]')?.value||'').trim();
  if(k==='whynot')return ciSend({kind:'whynot',text},()=>{delete ciDraft.whynot;notice('Note saved for your team.')});
  if(!text)return notice(k==='status'?'Write one line first.':'Write your explanation first.');
  if(k==='status')return ciSend({kind:'status',text},()=>{delete ciDraft.status;notice('Status posted to your team.')});
  ciSend({kind:'explain',text},()=>{delete ciDraft.explain;notice('Saved privately for your teacher.')})});
 document.querySelector('[data-ci-request]')?.addEventListener('click',async e=>{const b=e.currentTarget;if(ciLocked())return;b.disabled=true;try{await api('/api/help',{requestKind:'unheard',text:'My point was not discussed by my team.'});await refresh(true);notice('Sent privately to your teacher.')}catch(error){notice(error.message);b.disabled=false}});
 if(ciLocked())document.querySelectorAll('#ciTop input,#ciTop button,#ciArea input,#ciArea textarea,#ciArea button,[data-ci-request]').forEach(el=>el.disabled=true);
 if(key){const el=document.querySelector('[data-ci-input="'+key+'"]');if(el){el.focus({preventScroll:true});try{el.setSelectionRange(selection,selection)}catch{}}}
};
/* Length of a long paste. The pasted text never leaves the page. */
document.addEventListener('paste',e=>{
 const t=ciTools()?.paste,el=e.target;if(!t||!el?.matches?.('#app textarea,#app input[type="text"],#app input:not([type])'))return;
 const text=e.clipboardData?.getData('text')||'';if(text.length<t.minChars)return;
 const field=(el.getAttribute('aria-label')||el.closest('label')?.innerText||el.placeholder||'an answer field').trim().split('\n')[0].slice(0,120);
 if(t.block){e.preventDefault();notice('Paste is off for answers in this activity. Type your answer.')}else notice('Long pastes are noted for your teacher by length. The text is not copied.');
 if(ciLocked()||ciSandbox())return;
 api('/api/collab',{kind:'paste',chars:text.length,field}).catch(()=>{});
},true);
/* Time of the last typed change, at most once every few seconds. No text is sent. */
document.addEventListener('input',e=>{
 const t=ciTools()?.heartbeat;if(!t||preview||ciLocked()||!e.target?.matches?.('#app textarea,#app input,#app select'))return;
 const scope=e.target.closest('.workflow-critique,.workflow-opening,[data-ci],#adaptiveStudentArea')?'shared':'own',now=Date.now();
 if(now-(ciBeat[scope]||0)<t.seconds*1000)return;ciBeat[scope]=now;
 api('/api/collab',{kind:'edit',scope}).catch(()=>{});
},true);
/* The first state can arrive while the later scripts are still loading. Draw once more so the page has everything above. */
if(data)render();
