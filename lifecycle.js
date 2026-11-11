/* Draft pages stay private until the instructor deploys the local activity. */
function renderWorkspaceState(){
 const ready=Boolean(data.plan.planned),deployed=Boolean(data.deployment?.active);
 document.body.dataset.workspace=ready?'ready':'empty';
 document.body.dataset.planner=plannerWidgetOpen?'open':'closed';$('#planButton').setAttribute('aria-expanded',String(plannerWidgetOpen));$('#planButton').innerHTML=icon('roles')+'Planner';$('#emptyCanvas').hidden=ready||plannerWidgetOpen;$('#activityTitle').value=ready?data.plan.title:'Untitled activity';
 $('#newActivity').hidden=!ready;$('#restoreActivity').hidden=ready||!data.previousActivity;
 $('#deploymentState').hidden=!ready;$('#deploymentState').textContent=deployed?'Deployed':'Draft';
 $('#deploymentState').classList.toggle('deployed',deployed);
 ['studentsButton','shareButton','layoutButton','sampleButton','inspectorToggle','undo'].forEach(id=>$('#'+id).disabled=!ready);
 $('#shareButton').innerHTML=icon(deployed?'qr':'share')+(deployed?'Deployment':'Deploy');
 if(ready)return false;
 $('#saveState').textContent='New activity';if(plannerWidgetOpen)renderWindows();else $('#windows').replaceChildren();$('#connections').replaceChildren();$('#annotationLayer').replaceChildren();
 if(typeof teacherInk!=='undefined'){teacherInk.forEach(a=>a.remove());teacherInk=[]}
 setInspector(false);return true;
}

async function newActivity(){
 try{await queue;await api('/api/host/new',{});closeModal();resetPlannerWidget();history=[];changes=[];referenceOnCanvas=false;sample=false;focusedWindowId='';previewGroup=0;previewPhase='read';data=null;await reload(true);toast('Blank canvas ready. The previous activity is saved.');}
 catch(e){toast(e.message,true)}
}
async function restoreActivity(){
 try{await api('/api/host/restore',{});resetPlannerWidget();data=null;await reload(true);toast('Previous activity restored.');}catch(e){toast(e.message,true)}
}
function deploymentModal(){
 if(!data.plan.planned)return planModal();
 if(data.deployment?.active)return shareModal();
 const p=data.plan,issues=[],total=p.phases.reduce((n,s)=>n+s.minutes,0);if(total>p.budget)issues.push('The stages exceed your time budget.');for(let slot=0;slot<p.groupSize;slot++)if(!p.tasks.some(t=>t.assignees.includes(slot)&&t.prompt.trim()))issues.push('Assign a question to Learner '+String.fromCharCode(65+slot)+'.');
 showModal(modalHead('Deploy this activity','Open the learner entry when your pages are ready.')+
 '<div class="deploy-summary"><div><span>Activity</span><strong>'+esc(p.title)+'</strong></div><div><span>Learners</span><strong>'+p.groupCount+' groups × '+p.groupSize+'</strong></div><div><span>Timing</span><strong>'+total+' / '+p.budget+' min</strong></div></div>'+
 '<div class="deploy-phases">'+p.phases.map(s=>'<span>'+esc(s.title)+' <small>'+s.minutes+' min</small></span>').join('')+'</div>'+
 (issues.length?'<div class="warning">'+issues.map(esc).join('<br>')+'</div>':'<p class="deploy-ready">Every learner has an assigned role or task.</p>')+
 (data.studio?.activityTest?.planRev===data.planRev?'<p class="deploy-test-status">UI test: '+data.studio.activityTest.passed+' checks passed'+(data.studio.activityTest.failed?' · '+data.studio.activityTest.failed+' need attention':'')+'.</p>':'<p class="small-note">This plan version has not been tested yet.</p>')+'<p class="small-note">Deploys on this computer’s local server. Learners use the same Wi-Fi. The class timer stays stopped; preview answers are not student submissions.</p>'+
 '<div class="deploy-actions"><button class="quiet" id="backToCanvas">Back to canvas</button><button class="primary" id="confirmDeploy" '+(issues.length?'disabled':'')+'>Deploy activity '+icon('arrow')+'</button></div>','deployment-modal');
 $('#backToCanvas').onclick=closeModal;
 $('#confirmDeploy').onclick=async()=>{const b=$('#confirmDeploy');b.disabled=true;b.textContent='Deploying…';try{await queue;await api('/api/host/deploy',{planRev:data.planRev});await reload(true);shareModal();toast('Activity deployed. Learner entry is open.');}catch(e){b.disabled=false;b.textContent='Deploy activity';toast(e.message,true)}};
}
