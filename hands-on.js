const coachPreparedInputs={
 plan:[
  ['#planningMaterial','81'],['#planningMethod','Role Play'],['#planningSize','4'],['#planningGroups','3'],['#planningBudget','18'],
  ['#planningBrief','Create a role-play activity that simulates an editorial review meeting. Assign students as Story Author, First-time Reader, Evidence Checker, and Critical Editor. Have them examine how area, labels, and sequence convey the message, then write a shared critique.']
 ],
 edit:[['#teachingChange','Start with a group discussion of the first and last frames. Record one initial reading. Then let the four roles examine that reading on their own. Finally, bring their findings together to write one shared critique.']],
 claim:[['#name','Maya (practice)']],
 opening:[['#initialReading','The maps narrow the population to a small group of voters. Each step filters who is counted, rather than showing population falling over time.']],
 rolework:[
  ['input[name="initialAnswer"]','time'],['#initialReason','Tutorial example: I read the smaller maps as a population decline over time.'],
  ['.studio-beat:nth-child(1) textarea[data-field="text"]','Each square represents one million people, rather than an equal area of land.'],
  ['.studio-beat:nth-child(1) textarea[data-field="reason"]','The unit key labels the squares as people. State sizes therefore represent population, not geography.'],
  ['.studio-beat:nth-child(2) textarea[data-field="text"]','Only voters in competitive Senate states remain at this point in the story.'],
  ['.studio-beat:nth-child(2) textarea[data-field="reason"]','The population label changes as states are filtered. The smaller map shows a narrower group, not a later year.']
 ],
 critique:[
  ['[data-group-field="message"]','The story narrows the population through a sequence of voting filters.'],
  ['[data-group-field="misreading"]','Shrinking area may be mistaken for population declining over time.'],
  ['[data-group-field="change"]','Keep the population label visible at each transition and state that the sequence filters people, rather than years.']
 ],
 followup:[['input[name="followupAnswer"]','yes'],['#followupReason','A later frame counts a narrower population group. The map can shrink without a change in total population.']],
 support:[
  ['#progressMessage','Compare frames 1 and 7. Which label tells you who is counted? Explain why the map can shrink without population falling over time.'],
  ['#progressObservation','The private answers differ from the shared reading. Ask each learner to explain the population filter. Spoken participation has not been checked.']
 ],
 review:[['#progressResolveNote','I compared the initial and follow-up answers with the frame labels. The follow-up reasons distinguish population filters from change over time. I would check transfer with a new example.']],
 preview:[
  ['input[name="initialAnswer"]','filter'],['#initialReason','The frame labels name different population groups, not different years.'],
  ['.studio-beat:nth-child(1) textarea[data-field="text"]','Each square represents one million people, rather than an equal area of land.'],
  ['.studio-beat:nth-child(1) textarea[data-field="reason"]','The unit key says people. The shapes are scaled by population.'],
  ['.studio-beat:nth-child(2) textarea[data-field="text"]','The sequence filters the voters included in the comparison.'],
  ['.studio-beat:nth-child(2) textarea[data-field="reason"]','The frame labels name different population groups, not different years.'],
  ['#newReadingNote','The shrinking maps could look like a decline over time. Which label tells me this is a population filter?'],
  ['#evidenceStatement','The shrinking map shows the population declining over time.'],['#evidenceStatus','correct'],
  ['#evidenceReason','The labels change which people are counted. They do not show a sequence of years.'],
  ['[data-studio-field="reflection"]','Keep the population comparison, but clarify that the shrinking shapes filter voters rather than show a change over time.']
 ]
};
/* Next-driven demo. App text is English; explanations live only in the Chinese dock. */
tutorialActive=false;renderTutorial=function(){};document.body.classList.remove('tour-open');$('#tutorialDock').hidden=true;$('#tutorialSpotlight')?.remove();
let demoActive=false,demoBusy=false,demoIndex=0,demoReady=false,demoPart='',demoError='',demoStartup=false;
const demoKey=()=> (fullActivityTour?'collabcanvas-guided-v2-':'collabcanvas-knowledge-v6-')+admin;
const demoOwner=()=>activePeople().find(p=>p.group===0&&p.slot===0);
const demoTeam=()=>data.progress?.teams.find(t=>t.group===0);
function demoPersist(){try{localStorage.setItem(demoKey(),JSON.stringify({version:2,step:demoSteps[demoIndex].id,index:demoIndex,active:demoActive,part:demoPart,planner:plannerDraft}))}catch{}}
async function demoWait(fn,label='interface',timeout=18000){const began=Date.now();while(Date.now()-began<timeout){const result=await fn();if(result)return result;await new Promise(r=>setTimeout(r,60))}throw Error('Could not open '+label+'. Use Retry to continue.');}
async function demoHostUntil(fn,label){await demoWait(async()=>fn(await api('/api/host')),label);await reload(true)}
function demoFill(doc,selector,value){
 const fields=[...doc.querySelectorAll(selector)];if(!fields.length)throw Error('Missing prepared field: '+selector);
 const field=fields[0],E=doc.defaultView.Event;
 if(field.type==='radio'){const chosen=fields.find(f=>f.value===value);if(!chosen)throw Error('Missing answer option.');chosen.checked=true;chosen.dispatchEvent(new E('input',{bubbles:true}));chosen.dispatchEvent(new E('change',{bubbles:true}));return}
 if(field.type==='checkbox')field.checked=Boolean(value);else field.value=value;
 field.dispatchEvent(new E('input',{bubbles:true}));field.dispatchEvent(new E('change',{bubbles:true}));
}
function demoFillSet(doc,name){for(const [selector,value]of coachPreparedInputs[name]||[])if(doc.querySelector(selector))demoFill(doc,selector,value)}
function demoClick(selector,doc=document){const el=doc.querySelector(selector);if(!el||el.disabled)throw Error('Control is not ready: '+selector);el.classList.add('demo-action');el.click();}
function demoSetPlanner(part){demoPart=part;if(!$('#planningForm'))openPlannerWidget();demoPresentPlanner();}
function demoPresentPlanner(){
 if(!demoActive)return;const form=$('#planningForm');if(!form)return;
 const byPart={'class-count':['.planning-numbers'],'group-size':['.planning-numbers'],source:['.studio-upload'],visual:['#planningMaterial'],brief:['.studio-prompt-label','#planningBrief'],method:['#planningMethod'],groups:['.planning-numbers'],timing:['.planning-numbers'],generate:['#plannerArrangement','.studio-generate']};
 const allow=new Set((byPart[demoPart]||[]).map(s=>{const e=form.querySelector(s);return e?.parentElement?.tagName==='LABEL'?e.parentElement:e}));
 for(const el of form.children)el.classList.toggle('demo-hidden',!allow.has(el));
 const numberSelector={'class-count':'#planningGroups','group-size':'#planningSize',timing:'#planningBudget'}[demoPart];
 form.querySelectorAll('.planning-numbers>label').forEach(el=>el.classList.toggle('demo-hidden',numberSelector?!el.querySelector(numberSelector):demoPart==='groups'?Boolean(el.querySelector('#planningBudget')):false));
 const headings={'class-count':['Number of teams','Each team has separate saved work.'],'group-size':['Students per team','One connected interface per learner.'],source:['Source material','Upload lecture slides to start.'],visual:['Choose a visual','Use slide 81: the voting story.'],brief:['Describe the activity','An editorial review meeting, using the voting story.'],method:['Collaboration method','Role Play'],groups:['Arrange the class','Each team receives its own set of role interfaces.'],timing:['Activity time','Set the time budget.'],generate:['Ready to generate','3 teams · 4 learners per team · 18 minutes']};
 const [title,note]=headings[demoPart]||['Plan an activity','Start with the source material.'];
 let lead=$('#demoPlannerLead');if(!lead){lead=document.createElement('div');lead.id='demoPlannerLead';form.before(lead)}
 lead.innerHTML='<span>INSTRUCTOR PLANNER</span><h2>'+esc(title)+'</h2><p>'+esc(note)+'</p>';
 const node=$('#window-plan'),area=$('#canvasArea').getBoundingClientRect();if(!node)return;
 const width=Math.max(260,Math.min(540,area.width-48)),height=Math.max(230,Math.min(590,area.height-42));node.style.width=width+'px';node.style.height=height+'px';scale=1;tx=(area.width-width)/2-parseFloat(node.style.left);ty=18-parseFloat(node.style.top);transform();
}
const demoRenderBase=render;render=function(...args){demoRenderBase(...args);if(demoActive)demoPresentPlanner()};
async function demoStudent(join=false){
 const p=demoOwner(),url=join&&!p.claimed?'/join?code='+encodeURIComponent(data.code):'/s/'+p.token;
 showModal(modalHead(join?'Student entry':'Student interface','Demonstration classroom · simulated responses')+'<iframe class="demo-student-frame" title="Demonstration student interface" src="'+url+'"></iframe>','demo-student-modal');
 const frame=$('.demo-student-frame');await demoWait(()=>frame.contentDocument?.querySelector(join&&!p.claimed?'#places .task-choice':'.editorial-page'),'student interface');return frame.contentDocument;
}
async function demoFrame(){return demoWait(()=>$('#overlay iframe')?.contentDocument?.querySelector('.editorial-page')&&$('#overlay iframe').contentDocument,'student interface')}
async function demoRole(slot){closeModal();setInspector(false);previewPhase='read';const p=activePeople().find(p=>p.group===0&&p.slot===slot);focusWindow(p.id);await demoFrame();}
function demoAttribute(id){closeModal();tab=id;render();setInspector(true);}
async function demoFresh(){
 const r=await api('/api/host/tutorial-start',{reset:true});location.assign(r.url);
}

async function demoStudentFor(group,slot){
 const p=activePeople().find(p=>p.group===group&&p.slot===slot);
 showModal(modalHead('Student interface','Demonstration classroom · simulated responses')+'<iframe class="demo-student-frame" title="Demonstration student interface" src="/s/'+p.token+'"></iframe>','demo-student-modal');
 await demoFrame();return $('.demo-student-frame').contentDocument;
}
async function demoAdaptivePreview(group,pattern){await adaptivePreview(group,pattern);await demoWait(()=>$('#adaptiveApply')&&!$('#adaptiveApply').disabled,'adaptation preview');await demoWait(()=>$('#adaptivePreviewFrame')?.contentDocument?.querySelector('[data-adaptive-pattern="'+pattern+'"]'),'adapted student interface');}
async function demoApplyAdaptive(group,pattern){
 if(!data.progress.teams[group].adaptive?.changes?.some(c=>c.pattern===pattern)){
  demoClick('#adaptiveApply');await demoHostUntil(d=>d.progress.teams[group].adaptive?.changes?.some(c=>c.pattern===pattern),'applied interface change');
 }
}
function demoAdaptiveFill(doc,values){for(const [key,value]of Object.entries(values))demoFill(doc,'[data-adaptive-field="'+key+'"]',value);}

/* The rule set of the framework tour: three collaboration rules, then one more from the rule library. */
function demoRuleSet(cosign){ruleDraft.forEach(r=>r.enabled=Boolean(collaborationCodes[r.id])||Boolean(cosign&&r.id==='co-sign'))}
const demoSignal=(d,group,id)=>d.progress.teams[group].signals.find(s=>s.id===id);
async function demoRulePreview(id,selector){await showRuleStudentPreview(ruleDraft.find(r=>r.id===id));return demoWait(()=>$('#rhPreviewFrame')?.contentDocument?.querySelector(selector),'student page preview')}
async function demoStoryboard(){closeModal();setInspector(false);rhStoryboard();await demoWait(()=>$('.rh-cell iframe')?.contentDocument?.querySelector('.editorial-page'),'storyboard')}
const D=(id,title,text,run,focus)=>({id,title,text,run,focus});
const activityDemoSteps=[
 D('empty','从真正的空画布开始','这里还没有活动、阶段或学生界面。只需点击“下一步”，教程会替你打开 Planner。',async()=>{if(data.plan.planned)throw Error('This run is already planned. Start a new demo.');closeModal();resetPlannerWidget();setInspector(false);render();},'#planButton'),
 D('planner','打开 Planner','已自动打开画布上的配置组件。下一步会上传准备好的 InfoVis 课件。',()=>demoSetPlanner('source'),'#window-plan'),
 D('upload','上传课件','教程已上传真实的示例 PDF，并显示课件缩略图。系统界面仍是英文。',async()=>{demoSetPlanner('source');if(!studioLecture){const r=await fetch('/assets/lecture.pdf');if(!r.ok)throw Error('Example lecture is unavailable.');await uploadLecture(new File([await r.blob()],'SI649-Communicative-Visualization.pdf',{type:'application/pdf'}));if(!studioLecture)throw Error('The example upload did not finish.');}},'#uploadedSlides'),
 D('visual','选择投票图','已选中 slide 81 的七帧投票故事：面积表示人口，后续画面筛选人群，并非人口随时间下降。',()=>{demoSetPlanner('visual');demoFill(document,'#planningMaterial','81');rememberPlannerDraft();},'#planningMaterial'),
 D('brief','填入活动描述','已填入编辑评审会议的活动描述。四位学生分别扮演作者、读者、证据核查者和编辑。',()=>{demoSetPlanner('brief');demoFill(document,'#planningBrief',coachPreparedInputs.plan.find(x=>x[0]==='#planningBrief')[1]);rememberPlannerDraft();},'#planningBrief'),
 D('method','选择 Role Play','已自动选择协作方式。接下来设置小组人数，而不是提前生成学生页面。',()=>{demoSetPlanner('method');demoFill(document,'#planningMethod','Role Play');rememberPlannerDraft();},'#planningMethod'),
 D('groups','设置三组、每组四人','每组有四个不同任务，各组保存各自的学生作品。画布会预览其中一组。',()=>{demoSetPlanner('groups');demoFill(document,'#planningGroups','3');demoFill(document,'#planningSize','4');rememberPlannerDraft();},'.planning-numbers'),
 D('timing','设置十八分钟','已填入时间预算。下一步生成四个学生界面。',()=>{demoSetPlanner('timing');demoFill(document,'#planningBudget','18');rememberPlannerDraft();},'#planningBudget'),
 D('generate','生成四个学生界面','已自动执行 Generate activity。四个角色拥有不同工具，并通过共同任务相互连接。',async()=>{if(!data.plan.planned){demoSetPlanner('generate');await generateStudio({preventDefault(){}});await demoHostUntil(d=>d.plan.planned,'generated interfaces');}demoPart='';closeModal();setInspector(false);fit();},'#windows'),
 D('author','查看 Author 界面','作者用故事片段组织主张，并解释图中的变化如何支撑信息。下一步会自动打开 Reader。',()=>demoRole(0),'frame:.studio-workspace'),
 D('reader','查看 Reader 界面','读者记录困惑、定位对应画面，并提出需要同伴解释的问题。',()=>demoRole(1),'frame:.studio-workspace'),
 D('checker','查看 Checker 界面','核查者检查单位、标签与各帧统计的人群，辨别图表能支持什么。',()=>demoRole(2),'frame:.studio-workspace'),
 D('editor','查看 Editor 界面','编辑检查主张与理由，整理团队需要澄清的地方。四个学生界面都已自动打开过。',()=>demoRole(3),'frame:.studio-workspace'),
 D('edit','提出界面修改','已打开 Edit 并填入修改意图：先共同讨论，再分别按角色工作，最后共同写评论。',()=>{closeModal();editStudioRegion(demoOwner().id,'author-build','the opening activity');demoFillSet(document,'edit');},'#teachingChange'),
 D('preview','预览相互连接的修改','已自动生成修改预览。变化同时涉及四个界面的任务顺序与产物交接。',async()=>{await previewTeachingEdit();if(!studioCandidate)throw Error('The edit preview is unavailable.');},'#teachingPreview'),
 D('apply','应用到所有小组','已应用修改。现在流程变为共同讨论 → 按角色工作 → 共同写作，角色工具仍然保留。',async()=>{if(data.plan.studio?.flow!=='group-first'){demoClick('#applyTeachingChange');await demoHostUntil(d=>d.plan.studio?.flow==='group-first','revised activity');}closeModal();setInspector(false);previewPhase='read';render();fit();},'#phaseBar'),
 D('task-setting','查看任务设置','教程自动打开五项精确设置。Task 描述学生收到什么、做什么、产出什么。',()=>demoAttribute('task'),'.inspector'),
 D('group-setting','查看组队设置','Group 控制组数、人数和学生位置。这些设置决定要分发多少份个人界面。',()=>demoAttribute('group'),'.inspector'),
 D('roles-setting','查看分工设置','Roles 表明材料与认知任务分给谁，以及各角色如何使用同伴的工作。',()=>demoAttribute('distribution'),'.inspector'),
 D('interaction-setting','查看互动设置','Interaction 控制同步方式、交流媒介，以及同伴答案何时可见。',()=>demoAttribute('interaction'),'.inspector'),
 D('time-setting','查看时间设置','Time 展示各阶段时长和衔接。五项设置用于检查同一份活动安排。',()=>demoAttribute('timing'),'.inspector'),
 D('rules','计划进展规则','已自动打开候选规则。教师可以选用、修改或自写；自动信号与教师观察会明确区分。',()=>{setInspector(false);progressScreen='';progressRulesModal();ruleSelected='reading-check';drawRulePlanner();},'#overlay .modal'),
 D('rule-preview','查看规则如何改变学生界面','已打开学生端预览。个人读图检查会收集私密初答和理由，不向同伴公开。',()=>showRuleStudentPreview(ruleDraft.find(r=>r.id==='reading-check')),'#overlay .modal'),
 D('adaptive-rules','把规则连接到可执行的调整','已切到学生求助规则。Notice、Possible response、Recheck 分别说明可见证据、教师可选处理和后续复查。',()=>{drawRulePlanner();ruleSelected='support-request';drawRulePlanner();},'#ruleEditor'),
 D('adaptive-rule-preview','学生可以表达需要什么支持','新入口让学生请求较小步骤或先写出来。规则不会从无操作记录推断不参与，也不会自动给学生贴标签。',()=>showRuleStudentPreview(ruleDraft.find(r=>r.id==='support-request')),'#overlay .modal'),
 D('save-rules','保存规则并更新界面','已保存选中的规则。之后 Dashboard 能显示对应证据，原有学生任务保持连接。',async()=>{drawRulePlanner();await saveRulePlanner();if(!data.plan.progress?.rulesReviewedAt)throw Error('Rules were not saved.');closeModal();render();fit();},'#planProgressRules'),
 D('test','运行界面测试','教程正在替你执行浏览器操作，检查保存、答案权限和阶段交接。测试结束后才能继续。',async()=>{activityTestModal();await runActivityTest();if(data.studio.activityTest.failed)throw Error('Some activity tests need attention.');},'#testResults'),
 D('deploy-review','检查部署安排','已打开部署确认页，核对人数、时间与测试结果。此时学生入口尚未开放。',()=>{closeModal();deploymentModal();},'#overlay .modal'),
 D('deploy','部署一个班级二维码','已自动确认部署。所有小组扫同一个码，再领取自己的任务界面；计时尚未启动。',async()=>{if(!data.deployment.active){demoClick('#confirmDeploy');await demoHostUntil(d=>d.deployment.active,'class deployment');}shareModal();},'.studio-class-qr'),
 D('join','展示扫码后的领取入口','已打开与扫码相同的入口，并选好 Group 1、Author 和示例姓名。无需你手动选择。',async()=>{const doc=await demoStudent(true);if(!demoOwner().claimed){demoClick('[data-group="0"]',doc);demoClick('[data-place="'+demoOwner().id+'"]',doc);demoFill(doc,'#name','Maya (practice)');}},'frame:#places'),
 D('claim','领取学生界面','已自动领取 Author。系统将这一位学生连接到 Group 1 的同伴和共同作品。',async()=>{if(!demoOwner().claimed){const doc=$('.demo-student-frame').contentDocument;demoClick('#claim',doc);await demoHostUntil(d=>d.people.find(p=>p.id===demoOwner().id)?.claimed,'student claim');}await demoFrame();},'frame:.editorial-page'),
 D('opening','开始共同读图','已启动练习课堂，并填好小组初始解释。下一步会自动保存，然后进入角色任务。',async()=>{if(!data.plan.live.started)await live('start');await live('stage',{phaseId:'read'});const doc=await demoStudent();await demoWait(()=>doc.querySelector('#initialReading'),'starting reading');demoFillSet(doc,'opening');},'frame:#initialReading'),
 D('role-work','保存讨论并进入角色任务','小组初始解释已保存。教程已进入 Work by role，准备一份错误初答与作者贡献，演示如何发现问题。',async()=>{let doc=await demoFrame();if(!data.studio.groups?.['0']?.opening?.text){demoClick('#saveInitialReading',doc);await demoHostUntil(d=>Boolean(d.studio.groups?.['0']?.opening?.text),'group reading');}await live('stage',{phaseId:'discuss'});doc=await demoStudent();await demoWait(()=>doc.querySelector('#initialReason'),'private check');demoFillSet(doc,'rolework');doc.querySelector('[data-check-form]')?.scrollIntoView({block:'center'});},'frame:[data-check-form]'),
 D('share-role','自动提交初答与角色贡献','已保存示例初答和作者解释。初答故意把地图缩小理解为时间变化，用于后面的检测与支持。',async()=>{let doc=await demoFrame();if(!demoTeam().rows.find(r=>r.person===demoOwner().id).initial){demoClick('[data-check-form="initial"] button',doc);await demoHostUntil(d=>d.progress.teams[0].rows.find(r=>r.person===demoOwner().id).initial,'initial check');}doc=await demoFrame();demoClick('#submitStudio',doc);await demoHostUntil(d=>d.studio.responses[demoOwner().id]?.['discuss:submitted'],'role contribution');},'frame:#submitStudio'),
 D('shared-critique','汇合四个角色的贡献','已加入明确标注的示例同学，进入共同写作，并填好三项评论。其他小组的数据没有改变。',async()=>{if(!data.tutorialPeerExamples){await api('/api/host/tutorial-examples',{kind:'peers'});await reload(true);}await live('stage',{phaseId:'revise'});const doc=await demoStudent();await demoWait(()=>doc.querySelector('#saveSharedCritique'),'shared critique');demoFillSet(doc,'critique');},'frame:#saveSharedCritique'),
 D('evidence','查看团队进展证据','共同评论已经保存。Dashboard 同时显示正确的小组解释与两份错误个人初答，避免用“全组完成”掩盖误解。',async()=>{if(!data.studio.groups?.['0']?.critique?.message){demoClick('#saveSharedCritique',await demoFrame());await demoHostUntil(d=>Boolean(d.studio.groups?.['0']?.critique?.message),'shared critique');}progressPreview=false;teamDetail(0);},'.progress-answer-table'),
 D('support-preview','预览局部支持','已打开帧对比预览。整组会看到比较材料，只有两名初答需要复查的学生收到私密题目。',()=>supportPreview(0),'.progress-support-preview'),
 D('support','只给这个小组加任务','已应用局部支持，并打开这名学生的实际界面。帧对比、原始答案与原有角色工具都在。',async()=>{if(!demoTeam().support){demoClick('#progressApplySupport');await demoHostUntil(d=>Boolean(d.progress.teams[0].support),'team support');}const doc=await demoStudent();await demoWait(()=>doc.querySelector('#followupReason'),'follow-up');demoFillSet(doc,'followup');doc.querySelector('.progress-support').scrollIntoView({block:'start'});},'frame:.progress-support'),
 D('follow-up','提交独立复查','教程已自动提交这名学生的复查，并模拟另一位示例学生完成复查。初答没有被改写。',async()=>{const doc=await demoFrame();if(!demoTeam().rows.find(r=>r.person===demoOwner().id).followup){demoClick('[data-check-form="followup"] button',doc);await demoHostUntil(d=>d.progress.teams[0].rows.find(r=>r.person===demoOwner().id).followup,'follow-up answer');}await api('/api/host/tutorial-examples',{kind:'followups'});await reload(true);progressPreview=false;teamDetail(0);demoFillSet(document,'review');},'.progress-answer-table'),
 D('review','教师确认处理结果','已保存示例教师判断：两份复查理由能区分人群筛选与时间变化。系统保留初答、复查与教师说明。',async()=>{if(!demoTeam().support.resolved){demoClick('#progressResolve');await demoHostUntil(d=>d.progress.teams[0].support?.resolved,'teacher review');}},'.progress-reviewed'),
 D('adaptive-evidence','同一活动，不同学生需要不同支持','教程加入另外两组明确标注的示例学生。第二组答案相同，第三组仍需要帮助来读图并完成共同评论。',async()=>{await api('/api/host/tutorial-examples',{kind:'adaptive-teams'});await reload(true);teamModal();},'.progress-team-grid'),
 D('difficulty-request','学生主动说明任务太难','已打开第三组 Reader 的界面。学生可以私下请求较小步骤，不需要系统从沉默推断原因。',async()=>{const doc=await demoStudentFor(2,1);demoClick('.adaptive-help summary',doc);demoClick('[data-support-request="difficulty"]',doc);await demoHostUntil(d=>d.requests.some(r=>r.group===2&&r.requestKind==='difficulty'),'private difficulty request');},'frame:.adaptive-help'),
 D('difficulty-review','教师检查具体请求','教师看到的是“需要较小步骤”的私人请求。可以先问、到组旁查看，或预览局部界面调整。',()=>{progressPreview=false;teamDetail(2);$('#adaptiveTeam').scrollIntoView({block:'start'});},'#adaptiveTeam'),
 D('scaffold-preview','预览分步支架和交接','Reader 收到单位、人群、变化三个步骤；同伴只接收主动分享后的发现。原有角色工具与目标保留。',()=>demoAdaptivePreview(2,'scaffold'),'.adaptive-preview-layout'),
 D('scaffold-apply','应用并查看学生的新任务','只修改第三组。Reader 的新界面已出现三个步骤；教程已填好示例解释，下一步会主动分享。',async()=>{await demoApplyAdaptive(2,'scaffold');const doc=await demoStudentFor(2,1);await demoWait(()=>doc.querySelector('[data-adaptive-field="unit"]'),'scaffold');demoAdaptiveFill(doc,{unit:'Each square represents one million people.',population:'The first frame counts the US population. The last frame counts a much smaller group involved in deciding competitive Senate races.',interpretation:'The population category becomes narrower. The sequence is not a series of later years.'});doc.querySelector('#adaptiveStudentArea').scrollIntoView({block:'start'});},'frame:#adaptiveStudentArea'),
 D('scaffold-handoff','把支架成果交给同伴','Reader 已主动分享。现在打开同组 Editor：这份解释进入共同评论的材料，私人求助没有公开。',async()=>{let doc=await demoFrame();demoClick('[data-adaptive-form] button[type="submit"]',doc);await demoHostUntil(d=>Object.values(d.progress.teams[2].adaptive.changes.find(c=>c.pattern==='scaffold').responses).some(r=>r.shared),'shared scaffold');doc=await demoStudentFor(2,3);await demoWait(()=>doc.querySelector('.adaptive-shared article'),'shared scaffold handoff');doc.querySelector('#adaptiveStudentArea').scrollIntoView({block:'start'});},'frame:.adaptive-shared'),
 D('scaffold-recheck','教师复查后再关闭请求','已打开后续作品。保存动作本身不能证明理解，教师需要读解释、询问或再出一道题。',()=>{const c=data.progress.teams[2].adaptive.changes.find(c=>c.pattern==='scaffold');adaptiveReview(2,c.id);demoFill(document,'#adaptiveReviewNote','I checked the three explanations and asked the Reader to explain the population filter. The note gives the Editor evidence to use; a new example would check transfer.');},'.adaptive-review-work'),
 D('writing-request','提供不同的参与方式','教师已保存复查。第二组 Reader 现在私下请求先写出来。系统不会推断学生是否 neurodivergent。',async()=>{demoClick('#adaptiveReviewSave');await demoHostUntil(d=>d.progress.teams[2].adaptive.changes.find(c=>c.pattern==='scaffold').reviewed,'reviewed scaffold');const doc=await demoStudentFor(1,1);demoClick('.adaptive-help summary',doc);demoClick('[data-support-request="participation"]',doc);await demoHostUntil(d=>d.requests.some(r=>r.group===1&&r.requestKind==='participation'),'written participation request');},'frame:.adaptive-help'),
 D('writing-preview','预览整个小组的文字交换','四个界面加入可分享的解释与定向回应，给学生另一个交流入口。原有共同任务继续保留。',()=>demoAdaptivePreview(1,'written-exchange'),'.adaptive-preview-layout'),
 D('writing-share','主动分享一份解释','已应用到第二组，并打开 Reader。先写好一个具体解释和图中依据，再由学生分享给同伴。',async()=>{await demoApplyAdaptive(1,'written-exchange');const doc=await demoStudentFor(1,1);await demoWait(()=>doc.querySelector('[data-adaptive-field="idea"]'),'written exchange');demoAdaptiveFill(doc,{idea:'The smaller shapes filter the population; they do not show a decline across years.',evidence:'The titles name narrower voting groups, while the square key counts people.'});demoClick('[data-adaptive-form] button[type="submit"]',doc);await demoHostUntil(d=>Object.values(d.progress.teams[1].adaptive.changes.find(c=>c.pattern==='written-exchange').responses).some(r=>r.shared),'shared written contribution');},'frame:#adaptiveStudentArea'),
 D('writing-reply','同伴回应具体理由','现在 Author 看见 Reader 的解释，写出自己的理解，并回应这位同伴的依据。不是只统计发了几条消息。',async()=>{const doc=await demoStudentFor(1,0);await demoWait(()=>doc.querySelector('[data-adaptive-reply-to]'),'peer reply');demoAdaptiveFill(doc,{idea:'I agree that area counts people, but the transition needs to state which group remains.',evidence:'The frame labels identify the retained groups.'});demoFill(doc,'[data-adaptive-reply-to]',activePeople().find(p=>p.group===1&&p.slot===1).id);demoFill(doc,'[data-adaptive-reply]','Your explanation separates filtering from time. We should keep the population label visible in the final critique.');demoClick('[data-adaptive-form] button[type="submit"]',doc);await demoHostUntil(d=>Object.values(d.progress.teams[1].adaptive.changes.find(c=>c.pattern==='written-exchange').responses).some(r=>r.reply),'linked peer response');},'frame:.adaptive-shared'),
 D('writing-recheck','检查回应有没有推进任务','教师查看解释和回应关系。两份贡献并不等于所有人都参与，更不代表掌握；教师决定是否需要继续支持。',()=>{const c=data.progress.teams[1].adaptive.changes.find(c=>c.pattern==='written-exchange');adaptiveReview(1,c.id);demoFill(document,'#adaptiveReviewNote','The Reader shared a source-based explanation and the Author responded to that reason. I would check whether the other two learners also had a useful way to contribute.');},'.adaptive-review-work'),
 D('agreement-review','全组同答，不自动判成问题','教师保存了交流观察。第二组全选相同答案，系统提示检查理由，允许保持原活动。',async()=>{demoClick('#adaptiveReviewSave');await demoHostUntil(d=>d.progress.teams[1].adaptive.changes.find(c=>c.pattern==='written-exchange').reviewed,'reviewed exchange');teamDetail(1);},'.progress-answer-table'),
 D('agreement-preview','可以加推理检查，也可以不加','这是另一个局部选项：用反事实问题检验共识。这里仅预览，不自动分发任务或制造分歧。',()=>demoAdaptivePreview(1,'reason-check'),'.adaptive-preview-layout'),
 D('agreement-keep','教师决定无需额外任务','示例教师核对了理由后，认为当前任务足够，选择保持活动，并记录理由。规则用于辅助判断。',()=>{adaptiveKeep(1);demoFill(document,'#adaptiveKeepNote','All four initial reasons distinguish population filters from time, and the written exchange uses the labels. I will keep the current task and check a new example later.');},'#adaptiveKeepNote'),
 D('agreement-save','保留教师决策与原始证据','已记录保持活动的决定。没有额外任务被分发；此前的初答、支架和同伴交流记录都仍然可查。',async()=>{demoClick('#adaptiveKeepSave');await demoHostUntil(d=>d.progress.teams[1].signals.find(s=>s.id==='answer-pattern').status==='checked','reviewed agreement');teamDetail(1);$('#adaptiveTeam').scrollIntoView({block:'start'});},'#adaptiveTeam'),
 D('next-activity','调整接下来的活动','已另存一个下一活动草稿：先做个人检查，再进入讨论。当前课堂和学生作品不会被替换。',async()=>{await prepareProgressDraft('next-activity',0);await demoWait(()=>$('#progressDraftDone'),'next-activity draft');},'.progress-draft-layout'),
 D('next-run','改进下次设计','已另存一个下次使用的草稿，澄清角色任务。你已走过规划、界面生成、调整、部署和进展干预。',async()=>{closeModal();await prepareProgressDraft('next-run',0);await demoWait(()=>$('#progressDraftDone'),'next-run draft');},'.progress-draft-layout')
];

const activityStep=id=>activityDemoSteps.find(s=>s.id===id);
const frameworkSteps=[
 D('empty','从空画布开始','演示系统框架。下一步打开 Planner。',activityStep('empty').run,'#planButton'),
 D('planner','打开 Planner','先准备材料，再逐项配置。',activityStep('planner').run,'#window-plan'),
 D('upload','上传 slides','准备好的课件已上传。下一步选择其中的材料。',activityStep('upload').run,'#uploadedSlides'),
 D('visual','选择材料','选中 slide 81。这里仅用它演示系统流程。',activityStep('visual').run,'#planningMaterial'),
 D('brief','输入活动描述','教师描述希望组织的活动。',activityStep('brief').run,'#planningBrief'),
 D('method','选择协作方式','此处选择 Role Play。重点是系统如何组织与调整活动。',activityStep('method').run,'#planningMethod'),
 D('class-count','设置组数','已填入三组，各组的作品分开保存。',()=>{demoSetPlanner('class-count');demoFill(document,'#planningGroups','3');rememberPlannerDraft();},'#planningGroups'),
 D('group-size','设置每组人数','已填入四人，因此每组会获得四个相互连接的界面。',()=>{demoSetPlanner('group-size');demoFill(document,'#planningSize','4');rememberPlannerDraft();},'#planningSize'),
 D('timing','设置时间','已填入十八分钟。',()=>{demoSetPlanner('timing');demoFill(document,'#planningBudget','18');rememberPlannerDraft();},'#planningBudget'),
 D('generate-review','确认生成配置','核对材料、协作方式、人数与时间，再生成界面。',()=>demoSetPlanner('generate'),'.studio-generate'),
 D('generate','生成相互连接的界面','画布展示四份学生界面与活动安排。',activityStep('generate').run,'#windows'),
 D('inspect','在画布打开界面','这里只检查生成结果，不逐个讲解学生如何上课。',()=>demoRole(0),'frame:.studio-workspace'),
 D('edit','提出修改','用一句话调整任务顺序和同伴交接。',activityStep('edit').run,'#teachingChange'),
 D('preview','检查修改范围','预览同一修改对各个界面的影响。',activityStep('preview').run,'#teachingPreview'),
 D('apply','应用修改','应用到相关界面；精确配置仍可从 Plan details 打开。',activityStep('apply').run,'#phaseBar'),
 D('storyboard','用 Storyboard 一次检查全部界面','每行是一个角色，每列是一个阶段。固定网格便于横向比较角色、纵向检查交接；画布仍用于布局和编辑。',demoStoryboard,'.rh-story-grid'),
 D('rules','从规则库选择进展规则','规则按常见的协作问题分组。先启用三条：贡献、同伴回应、共同答案的推理检查。个人答题仍然保存，但不作为本次提醒。',()=>{setInspector(false);progressScreen='';progressRulesModal();demoRuleSet(false);ruleSelected='role-work';drawRulePlanner();},'.rule-list'),
 D('rule-peer','查看同伴回应规则','追踪已经分享的读者问题有没有关联回应；教师仍要检查回应质量。',()=>{ruleSelected='peer-use';drawRulePlanner();},'#ruleEditor'),
 D('rule-reason','查看共同答案的推理规则','全组初答相同时，检查是否留下对比主张和同伴回应。相同答案本身不是错误。',()=>{ruleSelected='answer-pattern';drawRulePlanner();},'#ruleEditor'),
 D('rule-library','再启用一条：第二人确认','针对“各做各的、互不检查”。每条规则写法相同：何时提醒、学生看到什么、当下怎么回应、下次怎么改。',()=>{demoRuleSet(true);ruleSelected='co-sign';drawRulePlanner();},'#ruleEditor'),
 D('rule-students-see','保存前先看学生界面','这条规则在共同评论下方加入确认入口：没有保存这一版的组员读完后，写一条理由。',()=>demoRulePreview('co-sign','[data-ci="signoff"]'),'frame:[data-ci="signoff"]'),
 D('save-rules','保存规则','保存后，Dashboard 会依据学生的实际记录显示状态。',activityStep('save-rules').run,'#testActivityButton'),
 D('test-open','打开 UI testing','测试会逐个运行学生界面，检查按钮、保存、可见性与交接。',()=>activityTestModal(),'#runActivityTest'),
 D('test','运行真实界面测试','正在操作隔离的测试界面。不是预设的通过动画。',async()=>{await runActivityTest();if(data.studio.activityTest.failed)throw Error('Some UI checks failed.');},'#testResults'),
 D('test-result','查看测试结果','保留逐项结果，教师可以修复后重新测试。教学质量仍需教师检查。',()=>{},'#testRunStatus'),
 D('deploy-review','检查部署','确认配置与测试结果后，再开放入口。',activityStep('deploy-review').run,'#confirmDeploy'),
 D('deploy','部署班级入口','一个二维码连接到选组、选任务、领取界面的入口。',activityStep('deploy').run,'.studio-class-qr'),
 D('join','展示领取入口','扫码后选择组别和任务。',activityStep('join').run,'frame:#places'),
 D('claim','领取一个界面','仅演示领取，不继续完整走学生学习活动。',activityStep('claim').run,'frame:.studio-page-heading'),
 D('monitor','查看三组的实际信号','载入明确标注的模拟记录：第一组有人求助，第二组有未回应问题，第三组初答相同。',async()=>{if(!data.plan.live.started)await live('start');await api('/api/host/tutorial-examples',{kind:'collaboration-evidence'});await reload(true);progressPreview=false;teamModal();},'[data-classroom-group="0"]'),
 D('rule-alert','贡献还未齐备','角色工作还剩两分钟，四人中三人已提交；Eli 尚未提交，并明确请求较小步骤。',()=>teamDetail(0,'role-work'),'#frameworkRuleObserved'),
 D('preview-action','点击建议，先看预览','高亮 Preview change。下一步实际打开原界面与修改后界面的对比。',()=>teamDetail(0,'role-work'),'#frameworkSuggested'),
 D('intervene-preview','先预览教师可做的调整','点击 Preview change。对比同一个学生原来的工具与新增的三个小步骤。',async()=>{demoClick('#frameworkSuggested');await demoWait(()=>$('#supportOpenBefore'),'before and after comparison');},'.support-compare-grid'),
 D('compare-before','打开完整的原界面','教师检查 Eli 原有的阅读记录工具和任务要求。',async()=>{demoClick('#supportOpenBefore');const doc=await demoFrame();await demoWait(()=>doc.querySelector('.workflow-role-work'),'original role tools');},'frame:.workflow-role-work'),
 D('compare-after','打开完整的拟修改界面','保留原任务，增加三个小步骤。只有 Eli 需要完成这份支持。',async()=>{demoClick('#supportCompareBack');demoClick('#supportOpenAfter');const doc=await demoFrame();await demoWait(()=>doc.querySelector('[data-adaptive-pattern="scaffold"]'),'smaller steps');},'frame:[data-adaptive-pattern="scaffold"]'),
 D('compare-review','确认只调整目标学生','返回对比，确认接收人和保留的作品，再应用。',()=>demoClick('#supportCompareBack'),'#progressApplySupport'),
 D('intervene-apply','应用较小步骤支持','Eli 收到较小步骤；同组其他人的任务和已有作品保留。',async()=>{demoClick('#progressApplySupport');await demoHostUntil(d=>d.progress.teams[0].adaptive.changes?.some(c=>c.pattern==='scaffold'),'applied smaller steps');},'#frameworkInspect'),
 D('updated-ui','查看真实更新后的界面','直接从画布打开 Eli 的界面，确认实际部署的变化。',async()=>{const c=data.progress.teams[0].adaptive.changes.find(c=>c.pattern==='scaffold');frameworkInspect(0,c.targets[0]);const doc=await demoFrame();await demoWait(()=>doc.querySelector('[data-adaptive-pattern="scaffold"]'),'live smaller steps');doc.querySelector('[data-adaptive-pattern="scaffold"]').scrollIntoView({block:'start'});},'frame:[data-adaptive-pattern="scaffold"]'),
 D('recheck','查看后续贡献','载入明确标注的示例后续作品。Eli 完成三个步骤并分享了角色贡献，教师读完后记录判断。',async()=>{await api('/api/host/tutorial-examples',{kind:'collaboration-followup',group:0});await reload(true);const c=data.progress.teams[0].adaptive.changes.find(c=>c.pattern==='scaffold');adaptiveReview(0,c.id);demoFill(document,'#adaptiveReviewNote','Eli completed the smaller steps and saved a role contribution. I checked the note and confirmed the team can use it.');},'.monitor-review-grid'),
 D('review','记录贡献检查的处理结果','保存教师检查，并关闭这次求助。提交记录本身不等于学习效果。',async()=>{demoClick('#adaptiveReviewSave');await demoHostUntil(d=>d.progress.teams[0].adaptive.changes.find(c=>c.pattern==='scaffold').reviewed,'reviewed contribution');teamDetail(0,'role-work');},'.framework-state'),
 D('peer-alert','同伴回应检查：问题在汇合时被遗漏','第二组已进入共同写作，Sam 的问题仍有零条关联回应。',async()=>{await live('stage',{phaseId:'revise'});teamDetail(1,'peer-use');},'#frameworkRuleObserved'),
 D('peer-preview-action','点击同伴回应的调整建议','高亮 Preview change。接下来查看原问题如何进入共同写作。',()=>teamDetail(1,'peer-use'),'#frameworkSuggested'),
 D('peer-preview','让遗漏的问题进入共同写作','系统建议把原问题放到评论旁，并增加直接回应入口；先查看实际拟修改界面。',async()=>{demoClick('#frameworkSuggested');await demoWait(()=>$('#supportOpenAfter'),'peer comparison');demoClick('#supportOpenAfter');const doc=await demoFrame();await demoWait(()=>doc.querySelector('[data-adaptive-pattern="written-exchange"]'),'question response interface');},'frame:[data-adaptive-pattern="written-exchange"]'),
 D('peer-apply','应用回应入口','教师确认后应用到第二组，原问题和已有评论保留。',async()=>{demoClick('#supportCompareBack');demoClick('#progressApplySupport');await demoHostUntil(d=>d.progress.teams[1].adaptive.changes?.some(c=>c.pattern==='written-exchange'),'peer response change');teamDetail(1,'peer-use');},'#frameworkInspect'),
 D('peer-recheck','查看问题与回应的关联','载入示例回应：Alex 回答了 Sam 的原问题，并引用图例。教师仍要核对回应质量。',async()=>{await api('/api/host/tutorial-examples',{kind:'collaboration-followup',group:1});await reload(true);const c=data.progress.teams[1].adaptive.changes.find(c=>c.pattern==='written-exchange');adaptiveReview(1,c.id);demoFill(document,'#adaptiveReviewNote','Alex answered Sam’s original question using the population legend. I checked that the critique does not infer equal political power.');},'.adaptive-review-work'),
 D('peer-review','记录对同伴回应的检查','教师保存对原问题、关联回应和证据的检查；不是自动把任意文字判为正确。',async()=>{demoClick('#adaptiveReviewSave');await demoHostUntil(d=>d.progress.teams[1].adaptive.changes.find(c=>c.pattern==='written-exchange').reviewed,'reviewed peer response');teamDetail(1,'peer-use');},'#frameworkRuleObserved'),
 D('reason-alert','推理检查：一致答案还没有推理检查','第三组四人选择相同答案，但尚未完成对比主张和同伴回应。不是把一致判为错误。',()=>teamDetail(2,'answer-pattern'),'#frameworkRuleObserved'),
 D('reason-preview-action','点击推理检查的调整建议','高亮 Preview change。接下来查看拟加入的反事实问题和回应入口。',()=>teamDetail(2,'answer-pattern'),'#frameworkSuggested'),
 D('reason-preview','加入一个对比主张','预览一个反事实情境，要求解释理由并回应同伴；现有个人答案保持私密。',async()=>{demoClick('#frameworkSuggested');await demoWait(()=>$('#supportOpenAfter'),'reason comparison');demoClick('#supportOpenAfter');const doc=await demoFrame();await demoWait(()=>doc.querySelector('[data-adaptive-pattern="reason-check"]'),'reasoning interface');},'frame:[data-adaptive-pattern="reason-check"]'),
 D('reason-apply','应用小组推理检查','只给第三组加入这次交流，保留原来的角色工具和初答。',async()=>{demoClick('#supportCompareBack');demoClick('#progressApplySupport');await demoHostUntil(d=>d.progress.teams[2].adaptive.changes?.some(c=>c.pattern==='reason-check'),'reason check change');teamDetail(2,'answer-pattern');},'#frameworkInspect'),
 D('reason-recheck','检查解释和同伴回应','载入示例交流。教师看到一份反事实解释，以及另一位同学对该解释的关联回应。',async()=>{await api('/api/host/tutorial-examples',{kind:'collaboration-followup',group:2});await reload(true);const c=data.progress.teams[2].adaptive.changes.find(c=>c.pattern==='reason-check');adaptiveReview(2,c.id);demoFill(document,'#adaptiveReviewNote','I checked the counterfactual explanation and Taylor’s reply to Ren. They distinguish the counted subset from total residents.');},'.adaptive-review-work'),
 D('finish-rules','回看三组的变化','教师记录检查结果，Dashboard 保留后续证据。当前演示完成：检测问题 → 预览 → 应用 → 复查。',async()=>{demoClick('#adaptiveReviewSave');await demoHostUntil(d=>d.progress.teams[2].adaptive.changes.find(c=>c.pattern==='reason-check').reviewed,'reviewed reasoning');teamModal();},'.progress-team-grid'),
 D('cosign-evidence','规则库的提醒出现在教室上方','载入明确标注的示例：第一组的共同评论由 Maya 一人保存，其他组员还没有读过。未处理的提醒排在教室地图上方。',async()=>{await api('/api/host/tutorial-examples',{kind:'rule-library-evidence'});await reload(true);progressPreview=false;monitorView='progress';teamModal();await demoWait(()=>$('[data-rh-alert="0|co-sign"]'),'second sign-off alert');},'.rh-alerts'),
 D('cosign-alert','提醒说明违反了哪条规则','左边是预期，右边是实际记录和现在提醒的原因。系统只记录谁保存、谁确认，不判断评论质量。',()=>teamDetail(0,'co-sign'),'#frameworkRuleObserved'),
 D('cosign-student','学生端：读完再确认','打开 Eli 的界面。他没有保存这一版，可以选择同意或想修改，并写一条理由。',async()=>{const doc=await demoStudentFor(0,1);await demoWait(()=>doc.querySelector('[data-ci-form="signoff"]'),'sign-off control');demoFill(doc,'input[name="ciAgree"]','no');demoFill(doc,'[data-ci-input="signoff"]','The first frame is not land area. The legend says one square is one million people, so each frame counts a smaller group of people.');doc.querySelector('[data-ci="signoff"]').scrollIntoView({block:'center'});},'frame:[data-ci="signoff"]'),
 D('cosign-review','教师读到不同意见','Eli 提交后，提醒变为待阅读的证据：他指出评论把面积读成了土地。教师读完，记录自己做了什么。',async()=>{const doc=$('.demo-student-frame')?.contentDocument||await demoStudentFor(0,1);if(demoSignal(data,0,'co-sign').status==='attention'){await demoWait(()=>doc.querySelector('[data-ci-form="signoff"] button[type="submit"]'),'sign-off control');if(!doc.querySelector('[data-ci-input="signoff"]').value){demoFill(doc,'input[name="ciAgree"]','no');demoFill(doc,'[data-ci-input="signoff"]','The first frame is not land area. The legend says one square is one million people, so each frame counts a smaller group of people.');}demoClick('[data-ci-form="signoff"] button[type="submit"]',doc);await demoHostUntil(d=>demoSignal(d,0,'co-sign').status!=='attention','saved sign-off');}progressPreview=false;teamDetail(0,'co-sign');demoFill(document,'#rhHandleNote','Read Eli’s objection with the team. Maya revised the first sentence to say the squares count people.');},'#frameworkRuleObserved'),
 D('cosign-handled','记录处理，再写下次怎么改','标记为已处理；证据变化时提醒会重新出现。再写一条下次活动的设计决定，本次课堂不变。',async()=>{if(!demoSignal(data,0,'co-sign').handled){demoClick('#rhHandle');await demoHostUntil(d=>Boolean(demoSignal(d,0,'co-sign').handled),'handled alert');}teamDetail(0,'co-sign');await demoWait(()=>$('#rhNextNote')||$('.rh-next-inline.saved'),'next time note');if($('#rhNextNote'))demoFill(document,'#rhNextNote','Turn on the second sign-off from the start, and ask the First-time Reader to sign off first.');},'.rh-next-inline'),
 D('next-time','带到下一次活动','保存后，这条决定进入 Next time。下次新建活动时，规则会按这条决定预先打开。',async()=>{if(!data.progress.library.carry.some(c=>c.ruleId==='co-sign'&&c.fromRun===data.progress.library.runId)){demoClick('#rhNextSave');await demoHostUntil(d=>d.progress.library.carry.some(c=>c.ruleId==='co-sign'),'saved decision');}progressPreview=false;teamModal();monitorView='next';drawMonitor();},'.rh-next'),
 D('knowledge-overview','整理学生的知识状态','从 Dashboard 打开 Knowledge，按学生和具体任务整理证据。先看 Eli 在哪些任务上已有表现，哪些仍需检查。',async()=>{demoClick('#knowledgeReportButton');await demoWait(()=>$('#knowledgeStudent'),'knowledge report');const eli=activePeople().find(p=>p.group===0&&p.slot===1);demoClick('[data-knowledge-person="'+eli.id+'"]');},'#knowledgeStudent'),
 D('knowledge-evidence','查看任务背后的证据','打开独立读图检查：保存具体选项和理由。这里表示这道题上的表现，不直接代表对整门课知识的掌握。',()=>{if(!$('[data-knowledge-task="population-filter"]').open)demoClick('[data-knowledge-task="population-filter"] summary')},'[data-knowledge-task="population-filter"]'),
 D('knowledge-review','给任务留下教师判断','查看 Eli 对人口筛选的独立解释，并记录：这次任务已展示理解，下一步换一个例子独立检查。',async()=>{const eli=activePeople().find(p=>p.group===0&&p.slot===1);await openKnowledgeReport(eli.id);const task=knowledgeData.learners.find(p=>p.person===eli.id).tasks.find(t=>t.id.startsWith('support-')&&t.id.endsWith('-interpretation'));demoClick('[data-knowledge-task="'+task.id+'"] summary');demoClick('[data-knowledge-review="'+task.id+'"]');demoFill(document,'#knowledgeJudgment','demonstrated');demoFill(document,'#knowledgeNote','I checked Eli’s explanation after smaller-step support. It distinguishes a smaller counted population from a change in total residents.');demoFill(document,'#knowledgeNextCheck','Interpret a new frame sequence independently, without the smaller-step prompts.');},'.knowledge-review-layout'),
 D('knowledge-judgment','保存任务层面的记录','保存教师判断和下一次检查建议。初答、后续作品和判断依据仍然保留。',async()=>{demoClick('#knowledgeReviewSave');await demoWait(()=>$('#knowledgeTasks'),'saved knowledge judgment');await demoWait(()=>knowledgeData.learners.find(p=>p.person===knowledgePerson).tasks.some(t=>t.review),'persisted judgment');},'#knowledgeTasks'),
 D('knowledge-gap','保留还没有解决的知识困难','切换到 Maya。她仍把面积读成土地面积；报告保留这项困难，不会因为小组已完成就覆盖个人记录。',()=>{demoClick('[data-knowledge-person="'+demoOwner().id+'"]');if(!$('[data-knowledge-task="population-filter"]').open)demoClick('[data-knowledge-task="population-filter"] summary');},'[data-knowledge-task="population-filter"]'),
 D('knowledge-save','保存知识状态报告','保存整班快照。之后可回看或下载报告；教师的新判断不会覆盖这份历史记录。',async()=>{demoClick('#knowledgeSave');await demoWait(()=>$('#knowledgeSaved')&&knowledgeData.readOnly,'saved report snapshot');},'.knowledge-map-tools')
];
const demoSteps=fullActivityTour?activityDemoSteps:frameworkSteps;
if(fullActivityTour)document.body.classList.add('full-activity-tour');

function demoDock(){
 let dock=$('#demoDock');if(!dock){document.body.insertAdjacentHTML('beforeend','<section id="demoDock" aria-label="中文教程"></section>');dock=$('#demoDock')}
 const step=demoSteps[demoIndex],last=demoIndex===demoSteps.length-1;
 dock.innerHTML='<div class="demo-counter"><span>逐步演示 · 只需下一步</span><strong>'+String(demoIndex).padStart(2,'0')+' <small>/ '+(demoSteps.length-1)+'</small></strong></div><div class="demo-copy"><h2>'+step.title+'</h2><p>'+step.text+'</p><span id="demoStatus" role="status">'+(demoError?'这一步未完成：'+esc(demoError):demoBusy?'正在替你操作，请稍等…':'示例输入与按钮操作均由教程完成。')+'</span></div><div class="demo-controls"><button id="demoNext" class="primary" '+(demoBusy?'disabled':'')+'>'+(demoBusy?'正在演示…':demoError?'重试这一步':last?'完成演示':'下一步 →')+'</button><div><button id="demoRestart" '+(demoBusy?'disabled':'')+'>从空画布重来</button><button id="demoPause" '+(demoBusy?'disabled':'')+'>暂停</button><button id="demoExit">返回正式活动</button></div></div>';
 dock.hidden=!demoActive;document.body.classList.toggle('guided-active',demoActive);document.body.dataset.demoStep=step.id;document.body.dataset.demoFocus=step.focus||'';
 document.body.style.setProperty('--demo-height',Math.ceil(dock.getBoundingClientRect().height)+'px');
 $('#demoNext').onclick=()=>last&&!demoError?demoFinish():demoAdvance(demoError?demoIndex:demoIndex+1);
 $('#demoRestart').onclick=demoFresh;$('#demoExit').onclick=()=>location.assign(data.tutorialReturn||'/');$('#demoPause').onclick=()=>{demoActive=false;demoPersist();demoDock();document.body.classList.remove('guided-active')};
}
async function demoAdvance(index){
 if(demoBusy)return;$('#toast').classList.remove('show');demoIndex=index;demoBusy=true;demoError='';demoDock();
 try{await demoSteps[index].run();await queue;demoReady=true;demoPersist();demoFocus();}catch(e){demoError=e.message;demoReady=false;}finally{demoBusy=false;demoDock();if(!demoError)requestAnimationFrame(demoFocus);}
}
function demoFocus(){
 const selector=demoSteps[demoIndex].focus;if(!selector)return;
 const doc=selector.startsWith('frame:')?$('#overlay iframe')?.contentDocument:document;
 const el=doc?.querySelector(selector.replace(/^frame:/,''));
 if(el&&el.closest('.modal,.inspector,.window-body,.editorial-page'))el.scrollIntoView({block:'nearest',behavior:'instant'});
}
function demoFinish(){closeModal();setInspector(false);render();fit();demoDock();$('#demoStatus').textContent='演示完成。你可以在英文界面中自由试用，或从空画布重新开始。';$('#demoNext').textContent='再从空画布演示';$('#demoNext').onclick=demoFresh;}

async function frameworkRestore(id){
 if(id==='empty'){resetPlannerWidget();render();return}
 if(['planner','upload','visual','brief','method','class-count','group-size','timing','generate-review'].includes(id)){demoSetPlanner(demoPart||'source');return}
 if(id==='inspect'){await demoRole(0);return}
 if(id==='edit'){await activityStep('edit').run();return}
 if(id==='preview'){await activityStep('edit').run();await previewTeachingEdit();return}
 if(id==='storyboard'){await demoStoryboard();return}
 if(id==='rules'){await frameworkSteps.find(s=>s.id==='rules').run();return}
 if(['rule-peer','rule-reason','rule-library','rule-students-see'].includes(id)){progressRulesModal();demoRuleSet(id.startsWith('rule-library')||id==='rule-students-see');ruleSelected={'rule-peer':'peer-use','rule-reason':'answer-pattern'}[id]||'co-sign';drawRulePlanner();if(id==='rule-students-see')await demoRulePreview('co-sign','[data-ci="signoff"]');return}
 if(id==='cosign-evidence'){progressPreview=false;monitorView='progress';teamModal();return}
 if(['cosign-alert','cosign-review','cosign-handled'].includes(id)){progressPreview=false;teamDetail(0,'co-sign');return}
 if(id==='cosign-student'){await demoStudentFor(0,1);return}
 if(id==='next-time'){progressPreview=false;teamModal();monitorView='next';drawMonitor();return}
 if(id==='rule-concerns'){progressRulesModal();ruleSelected='role-clarity';drawRulePlanner();return}
 if(id==='rule-preview'){progressRulesModal();showRuleStudentPreview(ruleDraft.find(r=>r.id==='reading-check'));return}
 if(['test-open','test','test-result'].includes(id)){activityTestModal();return}
 if(id==='deploy-review'){deploymentModal();return}
 if(id==='deploy'){shareModal();return}
 if(id==='join'){await demoSteps.find(s=>s.id==='join').run();return}
 if(id==='claim'){await demoStudent();return}
 if(id==='monitor'){teamModal();return}
 if(['rule-alert','intervene-apply','review'].includes(id)){progressPreview=false;teamDetail(0,'role-work');return}
 if(id.startsWith('peer-')){teamDetail(1,'peer-use');return}
 if(id.startsWith('reason-')){teamDetail(2,'answer-pattern');return}
 if(id==='finish-rules'){teamModal();return}
 if(id==='knowledge-review'){await frameworkSteps.find(s=>s.id===id).run();return}
 if(id.startsWith('knowledge-')){const eli=activePeople().find(p=>p.group===0&&p.slot===1);if(id==='knowledge-save'){await openKnowledgeReport(demoOwner().id);const latest=knowledgeData.snapshots.at(-1);if(latest)await openKnowledgeReport(demoOwner().id,latest.id);}else await openKnowledgeReport(id==='knowledge-gap'?demoOwner().id:eli.id);return}
 if(['preview-action','peer-preview-action','reason-preview-action'].includes(id)){teamDetail(id==='preview-action'?0:id==='peer-preview-action'?1:2,id==='preview-action'?'role-work':id==='peer-preview-action'?'peer-use':'answer-pattern');return}
 if(['intervene-preview','compare-before','compare-after','compare-review'].includes(id)){progressPreview=false;await adaptivePreview(0,'scaffold');if(id==='compare-before')openSupportComparison('before');if(id==='compare-after')openSupportComparison('after');return}
 if(id==='updated-ui'){frameworkInspect(0,demoTeam().adaptive.changes.find(c=>c.pattern==='scaffold').targets[0]);await demoFrame();return}
 if(id==='next-activity'){const draft=data.progress.drafts.find(d=>d.kind==='next-activity');if(draft){await showProgressDraft(draft);return}}
 closeModal();setInspector(false);render();fit();
}

async function demoRestore(){
 const id=demoSteps[demoIndex].id;
 if(!fullActivityTour)return frameworkRestore(id);
 if(demoIndex<=7){if(demoIndex===0){resetPlannerWidget();render()}else demoSetPlanner(demoPart||'source');return}
 if(['author','reader','checker','editor','task-setting','group-setting','roles-setting','interaction-setting','time-setting','rules','adaptive-rules','edit','join'].includes(id)){await demoSteps[demoIndex].run();return}
 if(id==='preview'){editStudioRegion(demoOwner().id,'author-build','the opening activity');demoFillSet(document,'edit');await previewTeachingEdit();return}
 if(id==='adaptive-rule-preview'){progressRulesModal();showRuleStudentPreview(ruleDraft.find(r=>r.id==='support-request'));return}
 if(id==='rule-preview'){progressRulesModal();showRuleStudentPreview(ruleDraft.find(r=>r.id==='reading-check'));return}
 if(id==='test'){activityTestModal();return}
 if(id==='deploy-review'){deploymentModal();return}
 if(id==='deploy'){shareModal();return}
 if(['claim','opening','role-work','share-role','shared-critique','support'].includes(id)){
  const doc=await demoStudent();const prepared={opening:'opening','role-work':'rolework','shared-critique':'critique',support:'followup'}[id];
  if(prepared)demoFillSet(doc,prepared);return;
 }
 if(['evidence','follow-up','review'].includes(id)){progressPreview=false;teamDetail(0);return}
 if(id==='support-preview'){progressPreview=false;supportPreview(0);return}
 if(['difficulty-review','agreement-save','agreement-review'].includes(id)){progressPreview=false;teamDetail(id==='difficulty-review'?2:1);return}
 if(id==='adaptive-evidence'){teamModal();return}
 if(['scaffold-preview','writing-preview','agreement-preview'].includes(id)){await demoAdaptivePreview(id==='scaffold-preview'?2:1,{'scaffold-preview':'scaffold','writing-preview':'written-exchange','agreement-preview':'reason-check'}[id]);return}
 if(['difficulty-request','scaffold-apply','scaffold-handoff','writing-request','writing-share','writing-reply'].includes(id)){await demoStudentFor(id.startsWith('writing')?1:2,id==='scaffold-handoff'?3:id==='writing-reply'?0:1);return}
 if(['scaffold-recheck','writing-recheck'].includes(id)){const group=id==='scaffold-recheck'?2:1;adaptiveReview(group,data.progress.teams[group].adaptive.changes.find(c=>c.pattern===(group===2?'scaffold':'written-exchange')).id);return}
 if(id==='agreement-keep'){adaptiveKeep(1);return}
 if(['next-activity','next-run'].includes(id)){const draft=data.progress.drafts.find(d=>d.kind===id);if(draft){await showProgressDraft(draft);return}}
 closeModal();setInspector(false);render();fit();
}
async function demoBoot(){
 if(!data||demoStartup)return;demoStartup=true;
 if(!data.tutorialSession)return;
 let saved;try{saved=JSON.parse(localStorage.getItem(demoKey())||'null')}catch{}
 if(!saved&&data.plan.planned){await demoFresh();return;}
 const savedStep=saved?.step==='private-check'?'generate-review':saved?.step;
 const byId=savedStep?demoSteps.findIndex(s=>s.id===savedStep):-1;
 const legacyIndex=saved?.version===1&&!fullActivityTour&&saved.index>9?saved.index-1:saved?.index||0;
 demoIndex=Math.max(0,Math.min(byId>=0?byId:legacyIndex,demoSteps.length-1));demoPart=saved?.part==='private-check'?'generate':saved?.part||'';plannerDraft=saved?.planner||null;demoActive=saved?.active!==false;
 document.body.classList.add('practice-classroom');
 if(demoActive){demoDock();if(demoIndex===0)await demoAdvance(0);else{demoBusy=true;demoDock();try{await demoRestore();demoFocus()}catch(e){demoError=e.message}finally{demoBusy=false;demoDock()}}}
}
$('#openGuide').textContent='Tutorial';$('#openGuide').onclick=()=>{if(data?.tutorialSession&&demoStartup){demoActive=true;demoDock();return}demoFresh()};
tutorialBoot=demoBoot;setInterval(()=>{if(data&&!demoStartup)demoBoot()},150);
window.addEventListener('resize',()=>{if(demoActive){demoDock();demoPresentPlanner()}});
