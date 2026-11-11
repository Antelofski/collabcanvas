/* A bounded UI testing agent. It drives real controls against an isolated fixture. */
let activityTestRunning=false;
function activityTestModal(){
 if(activityTestRunning)return;
 const report=data.studio?.activityTest,current=report?.planRev===data.planRev;
 showModal(modalHead('Test activity','Check every student interface.')+'<div class="activity-test-toolbar"><span id="testRunStatus">'+(current?report.passed+' checks passed'+(report.failed?' · '+report.failed+' need attention':''):'Ready to test all '+data.plan.groupSize+' roles')+'</span><button id="runActivityTest" class="primary">'+(current?'Run tests again':'Run tests')+'</button></div><div class="activity-test-layout"><div id="testResults" class="activity-test-results" aria-live="polite">'+(current?report.checks.map(testResultHTML).join(''):'<p class="activity-test-intro">Saving · reload · peer access · handoffs</p>')+'</div><div class="activity-test-preview"><span id="testPreviewLabel">Student journey preview</span><iframe id="activityTestFrame" title="Testing agent student journey"></iframe></div></div><p class="studio-local-note">Scripted browser tests · isolated data</p>','activity-test-modal');
 $('#runActivityTest').onclick=runActivityTest;
}
function testResultHTML(c){return '<article class="activity-test-result '+c.status+'"><span>'+({passed:'✓',failed:'!',skipped:'–'}[c.status])+'</span><details><summary>'+esc(c.name)+'</summary><p>'+esc(c.detail||'')+'</p></details></article>'}
async function runActivityTest(){
 activityTestRunning=true;const button=$('#runActivityTest'),results=$('#testResults'),status=$('#testRunStatus'),frame=$('#activityTestFrame');button.disabled=true;button.textContent='Testing…';results.innerHTML='';let run,checks=[];
 const check=(name,detail,status='passed')=>{const c={name,detail,status};checks.push(c);results.insertAdjacentHTML('beforeend',testResultHTML(c));results.scrollTop=results.scrollHeight;$('#testRunStatus').textContent=checks.filter(x=>x.status==='passed').length+' checks passed'+(checks.some(x=>x.status==='failed')?' · needs attention':'');};
 const assert=(condition,message)=>{if(!condition)throw Error(message)};
 const wait=async(fn,label,limit=9000)=>{const start=Date.now();while(Date.now()-start<limit){try{const value=await fn();if(value)return value}catch{}await new Promise(r=>setTimeout(r,100))}throw Error(label+' timed out.');};
 const doc=()=>frame.contentDocument;
 const field=(selector,value)=>{const el=doc()?.querySelector(selector);assert(el,'Missing input: '+selector);el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));};
 const click=selector=>{const el=doc()?.querySelector(selector);assert(el&&!el.disabled,'Unavailable control: '+selector);el.click();};
 const qa=async(person,path='/api/state',body)=>{const r=await fetch('/api/test/'+run.id+'?action='+encodeURIComponent(path)+'&admin='+encodeURIComponent(admin)+'&person='+person.id,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});const j=await r.json();if(!r.ok)throw Error(j.error);return j};
 const load=async(person,phase)=>{const role=data.plan.tasks.find(t=>t.assignees.includes(person.slot));$('#testPreviewLabel').textContent=role.title+' · '+(data.plan.phases.find(s=>s.id===phase)?.title||phase);await new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(Error('Student interface did not load.')),9000);frame.onload=()=>{clearTimeout(timeout);resolve()};frame.src='/student.html?preview=1&admin='+encodeURIComponent(admin)+'&person='+person.id+'&phase='+phase+'&testRun='+run.id});await wait(()=>doc()?.querySelector('.editorial-page h1')&&!doc().body.textContent.includes('undefined'),'Load '+role.title);await wait(()=>[...doc().querySelectorAll('.studio-source img')].every(i=>i.complete&&i.naturalWidth>0),'Source images');if(document.body.classList.contains('guided-active'))await new Promise(resolve=>setTimeout(resolve,650));};
 try{
  run=await api('/api/host/test-start',{});const people=run.people.filter(p=>p.group===0),work=run.plan.phases.find(s=>s.kind==='individual'),flow=run.plan.studio?.flow==='group-first';
  assert(run.plan.materialId==='81'&&run.plan.structure==='Role Play','The browser pilot currently tests the voting-story role-play interfaces.');
  assert(work,'No individual role-work stage was found.');
  const roles=people.map(p=>({person:p,task:run.plan.tasks.find(t=>t.assignees.includes(p.slot))}));assert(roles.every(r=>r.task),'A learner has no assigned role.');check('Role assignments',people.length+' learners have a task and a dedicated interface.');
  const checkReading=async person=>{if((await qa(person)).progress?.answers?.initial)return;click('input[name="initialAnswer"][value="filter"]');field('#initialReason','The frame labels count narrower population groups, not later dates.');click('[data-check-form="initial"] button[type="submit"]');await wait(async()=>Boolean((await qa(person)).progress?.answers?.initial),'Save individual check');check(person.name+' · individual check','The answer and reason are saved for this learner only.');};
  if(run.plan.progress?.beforeDiscussion){for(const {person} of roles){await load(person,'read');await checkReading(person)}}
  if(flow){
   const first=people[0];await load(first,'read');field('#initialReading','The maps get smaller because each frame filters who is included. Area represents people, not land.');click('#saveInitialReading');await wait(async()=>Boolean((await qa(first)).studioGroup?.opening?.text),'Save starting reading');check('Shared starting discussion','Saved through the group-reading control.');
   await load(people[1],work.id);assert(doc().querySelector('.workflow-start-context')?.textContent.includes('filters who is included'),'The role task did not receive the group reading.');check('Discussion → role-task handoff','A second learner receives the saved starting reading.');
  }
  for(const {person,task} of roles){
   try{
    await load(person,work.id);const progressView=await qa(person);if(progressView.progress?.config.privateCheck&&progressView.progress.phase===work.id)await checkReading(person);const before=doc().querySelectorAll('.studio-source-images figure').length;click('#toggleCompare');assert(doc().querySelectorAll('.studio-source-images figure').length!==before,'Compare did not change the source view.');click('[data-studio-frame="6"]');assert(doc().querySelector('.studio-source-images figcaption')?.textContent==='Comparison with Florida','Frame selection did not update the image.');check(task.title+' · source controls','Frame selection and comparison change the visual material.');
    if(task.roleId==='author'){field('textarea[data-beat][data-field="text"]','Area represents population size, not geographic size.');field('textarea[data-beat][data-field="reason"]','The legend assigns one million people to each square.');}
    else if(task.roleId==='reader'){field('#newReadingNote','The shrinking maps could look like a population decline over time.');click('#addReadingNote');assert(doc().querySelectorAll('.studio-reading-log article').length>0,'The reading note was not added.');}
    else if(task.roleId==='checker'){field('#evidenceStatement','The population is falling over time.');field('#evidenceReason','Each frame applies a filter to the population; it is not a time series.');field('#evidenceStatus','correct');click('#addEvidenceCheck');assert(doc().querySelectorAll('.workflow-evidence-list article').length>0,'The evidence check was not added.');}
    else field('[data-studio-field="reflection"]','Keep the claim about a narrowing electorate. Clarify that map area counts people, not land.');
    click('#submitStudio');await wait(async()=>Boolean((await qa(person)).studioArtifacts?.[person.id]?.submitted?.[work.id]),'Save '+task.title);check(task.title+' · save and submit','Role work reaches its own saved record.');
    await load(person,work.id);const own=(await qa(person)).studioArtifacts[person.id];assert(own?.version>0,'Saved role work was lost on reload.');const observed=task.roleId==='author'?doc().querySelector('textarea[data-beat][data-field="text"]')?.value:task.roleId==='reader'?doc().querySelector('.studio-reading-log')?.textContent:task.roleId==='checker'?doc().querySelector('.workflow-evidence-list')?.textContent:doc().querySelector('[data-studio-field="reflection"]')?.value;assert(observed?.trim(),'The saved response did not return to its interface.');check(task.title+' · reload','The saved response is restored in the generated interface.');
    if(task.roleId==='author'&&roles.length>1){const other=await qa(people[1]);assert(!other.studioArtifacts[person.id],'An unfinished peer received the author’s answer.');check('Independent role work','Peer answers stay hidden before the team submits.');assert(!other.progress?.answers?.initial,'Another learner received the author’s private check.');check('Private check separation','A peer does not receive another learner’s private answer.');}
   }catch(e){check(task.title+' · journey',e.message,'failed')}
  }
  const first=people[0],view=await qa(first);assert(view.peerVisible,'Peer work did not open after all role submissions.');check('Role-work sharing gate','Peer work opens only after the whole group submits.');
  const outsider=run.people.find(p=>p.group!==0);if(outsider){const outside=await qa(outsider);assert(!outside.studioArtifacts[first.id]&&outside.peers.every(p=>p.group===outsider.group),'Another group received this group’s work.');check('Group separation','A learner in another group cannot receive these contributions.');}
  if(flow){
   const editor=roles.find(r=>r.task.roleId==='editor')?.person||first;await load(editor,'revise');assert(doc().querySelectorAll('[data-contribution]').length===roles.length,'The shared critique is missing a role contribution.');for(const b of [...doc().querySelectorAll('[data-contribution]')]){const id=b.dataset.contribution;click('[data-contribution="'+id+'"]');const contribution=doc().querySelector('.workflow-contribution-content')?.textContent;assert(contribution?.trim()&&!contribution.includes('No assessment shared yet.'),'A role contribution is empty.');}check('Four contributions → shared critique','The writing interface exposes every role’s saved findings.');
   field('[data-group-field="message"]','Area shows how many people remain after each voting filter.');field('[data-group-field="misreading"]','Shrinking area could be mistaken for a population decline over time.');field('[data-group-field="change"]','Label each retained population at the transition.');click('#saveSharedCritique');await wait(async()=>Boolean((await qa(editor)).studioGroup?.critique?.message),'Save shared critique');await load(people[1],'revise');assert(doc().querySelector('[data-group-field="message"]')?.value.includes('voting filter'),'A teammate did not receive the shared critique.');check('Shared critique · save and handoff','A teammate opens the same saved group response.');
   /* What the enabled progress rules add to the student page is driven through its real controls as well. */
   const tools=async p=>(await qa(p)).progress?.instruments||{},other=p=>people.find(x=>x.id!==p.id),signer=other(editor),control=selector=>wait(()=>doc().querySelector(selector),'Control '+selector);
   const rule=async(name,detail,steps)=>{try{await steps();check(name,detail)}catch(e){check(name,e.message,'failed')}};
   if(signer&&(await tools(signer)).signoff)await rule('Rule · second sign-off','A teammate who did not save the critique signs off with a reason. The writer cannot sign their own version.',async()=>{
    await load(signer,'revise');await control('[data-ci-form="signoff"]');click('input[name="ciAgree"][value="yes"]');field('[data-ci-input="signoff"]','The legend supports this reading: one square counts one million people.');click('[data-ci-form="signoff"] button[type="submit"]');
    await wait(async()=>Boolean((await tools(signer)).signoff.mine),'Save sign-off');const writer=(await tools(editor)).signoff;
    assert(!writer.canSign,'The member who saved the critique could sign off their own version.');assert(writer.entries.some(e=>e.current&&!e.mine),'The writer did not receive the teammate’s sign-off.')});
   if(signer&&(await tools(signer)).whyNot)await rule('Rule · a rejected reading is recorded','The team writes down the other reading and why it was rejected. Teammates see the same note.',async()=>{
    await load(signer,'revise');await control('[data-ci-input="whynot"]');field('[data-ci-input="whynot"]','Some of us read the shrinking maps as a fall over time. The frame labels name filters, not dates.');click('[data-ci-save="whynot"]');
    await wait(async()=>(await tools(editor)).whyNot.text.includes('frame labels'),'Save the rejected reading')});
   let picked=null;for(const p of people)if((await tools(p)).explainer?.mine)picked=p;
   if(picked)await rule('Rule · one member explains','One member is picked at random. The explanation stays private to that member and the teacher.',async()=>{
    await load(picked,'revise');await control('[data-ci-input="explain"]');field('[data-ci-input="explain"]','We decided the area counts people, because the legend sets one square to one million people.');click('[data-ci-save="explain"]');
    await wait(async()=>Boolean((await tools(picked)).explainer.done),'Save explanation');const seen=(await tools(other(picked))).explainer;
    assert(seen&&!seen.mine&&!seen.text,'A teammate received the private explanation.')});
   const pulse=(await tools(first)).pulse;
   if(pulse?.open)await rule('Rule · private closing check','Each learner answers privately. A teammate does not receive the answer.',async()=>{
    await load(first,pulse.phaseId);await control('[data-ci-form="pulse"]');click('input[name="ciContributed"][value="yes"]');click('input[name="ciUsed"][value="partly"]');field('[data-ci-input="pulse"]','Give the reader more time before the shared critique.');click('[data-ci-form="pulse"] button[type="submit"]');
    await wait(async()=>Boolean((await tools(first)).pulse.mine),'Save closing check');assert(!(await tools(other(first))).pulse.mine,'A teammate received the private closing check.')});
   const line=(await tools(first)).status;
   if(line)await rule('Rule · team status line','A one-line status reaches the whole team.',async()=>{
    await load(first,line.phaseId);await control('[data-ci-input="status"]');field('[data-ci-input="status"]','Comparing frames 1 and 7.');click('[data-ci-save="status"]');
    await wait(async()=>(await tools(other(first))).status.text==='Comparing frames 1 and 7.','Post team status')});
   if((await tools(first)).paste)await rule('Rule · paste notice','The page tells learners that long pastes are noted by length.',async()=>{await load(first,work.id);await control('.ci-note')});
  }
 }catch(e){check('Activity journey',e.message,'failed')}
 finally{
  try{if(run){const result=await api('/api/host/test-report',{id:run.id,checks});data.studio??={};data.studio.activityTest=result.report;status.textContent=result.report.failed?result.report.failed+' checks need attention':result.report.passed+' checks passed';}}
  catch(e){check('Save test report',e.message,'failed');status.textContent='The report could not be saved.'}
  activityTestRunning=false;button.disabled=false;button.textContent='Run tests again';
 }
}
const testToolbarBase=renderGuideToolbar;
renderGuideToolbar=function(){testToolbarBase();if(!$('#testActivityButton')){$('#teamsButton').insertAdjacentHTML('beforebegin','<button id="testActivityButton" class="quiet">Test activity</button>');$('#testActivityButton').onclick=activityTestModal;}$('#testActivityButton').hidden=!data.plan.planned;};
const testRenderBase=render;
render=function(inspect=true){testRenderBase(inspect);if(!data?.plan.planned)$('#testActivityButton')?.setAttribute('hidden','');};
