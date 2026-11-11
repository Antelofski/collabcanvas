/* A resumable control tour followed by a checked, hands-on activity journey. */
'use strict';
let tutorialActive=false,tutorialStep=0,tutorialMode='welcome',tutorialContext='',tutorialMenu=false;
let tutorialSeen=new Set(),tutorialDone=new Set(),tutorialFacts={},tutorialLastHTML='';
const tutorialKey='activity-canvas-guide-v3';
function saveTutorial(){try{localStorage.setItem(tutorialKey,JSON.stringify({mode:tutorialMode,step:tutorialStep,seen:[...tutorialSeen],done:[...tutorialDone],facts:tutorialFacts,active:tutorialActive}))}catch{}}
function restoreTutorial(){try{const s=JSON.parse(localStorage.getItem(tutorialKey)||'null');if(s){tutorialMode=s.mode||'welcome';tutorialStep=s.step||0;tutorialSeen=new Set(s.seen||[]);tutorialDone=new Set(s.done||[]);tutorialFacts=s.facts||{};return s}}catch{}return null}
function currentTutorialStep(){return tutorialMode==='controls'?tutorialControls[tutorialStep]:tutorialFlow[tutorialStep]}
function tutorialPerson(slot=0){return activePeople().find(p=>p.group===previewGroup&&p.slot===slot)||activePeople()[0]}
function tutorialFrame(){return $('#overlay iframe[title="Full-size learner preview"]')}
function openTutorialAttribute(attribute){closeModal();const ph=data.plan.phases.find(p=>p.kind===(attribute==='interaction'?'discussion':'individual'));if(['task','interaction'].includes(attribute)&&ph&&phase().id!==ph.id)setPreviewStage(ph.id);if(attribute==='task'){selected=tutorialPerson().id;const v=sceneViews.find(v=>v.person.id===selected);if(v)focusedWindowId=v.id}tab=attribute;render();setInspector(true)}
function tutorialOpenPerson(slot=0,kind='individual'){closeModal();setInspector(false);previewGroup=0;const ph=data.plan.phases.find(p=>p.kind===kind);if(ph)setPreviewStage(ph.id);focusWindow(tutorialPerson(slot).id)}
function ensureTutorialContext(context,force=false){
 if(!data)return;
 if(context!=='plan'&&plannerWidgetOpen)closePlannerWidget();
 const same=tutorialContext===context;tutorialContext=context;
 document.body.classList.toggle('tour-command',context==='command');
 if(same&&!force&&(context==='plan'?Boolean($('#planningForm')):['materials','stages','versions','share'].includes(context)?!$('#overlay').hidden:['task','group','distribution','interaction','timing'].includes(context)?$('.inspector').classList.contains('open'):context.startsWith('learner-')?Boolean(tutorialFrame()):$('#overlay').hidden))return;
 closeModal();setInspector(false);
 if(context==='role-exchange'){const ph=data.plan.phases.find(p=>p.kind==='discussion');if(ph)setPreviewStage(ph.id)}else if(context==='plan')planModal();
 else if(context==='materials')materialsModal();
 else if(context==='stages')stageModal();
 else if(context==='versions'){const ph=data.plan.phases.find(p=>p.kind==='individual');if(ph)setPreviewStage(ph.id);studentVersionsModal()}
 else if(context==='share')shareModal();
 else if(['task','group','distribution','interaction','timing'].includes(context))openTutorialAttribute(context);
 else if(context.startsWith('learner-')){
  const kind=context==='learner-revise'?'revision':['learner-discuss','learner-shared'].includes(context)?'discussion':'individual';
  tutorialOpenPerson(0,kind);
  const f=tutorialFrame();f?.addEventListener('load',()=>{if(context==='learner-source')f.contentDocument?.querySelector('[data-open-media]')?.click();if(context==='learner-shared'){const d=f.contentDocument?.querySelector('.shared-output');if(d)d.open=true}positionTutorial(true)},{once:true});
 }else fit();
 setTimeout(()=>positionTutorial(true),100);
}
function tutorialTarget(step=currentTutorialStep()){
 const spec=step?.target;if(!spec)return null;
 if(typeof spec==='object'){const f=tutorialFrame();let el=f?.contentDocument?.querySelector(spec.frame);if(!el&&step.optional)return null;el=el||f?.contentDocument?.querySelector(step.fallbackFrame||'__none__');const details=el?.closest('details');if(details&&!details.open)el=details.querySelector('summary');return el?{el,frame:f}:f?{el:f,frame:null}:null}
 const el=$(spec)||$(step.fallback||'__none__');return el?{el,frame:null}:null;
}
function positionTutorial(scroll=false){
 const ring=$('#tutorialSpotlight');if(!ring)return;
 if(!tutorialActive||!['controls','flow'].includes(tutorialMode)||tutorialMenu){ring.hidden=true;return}
 const step=currentTutorialStep();if(step.context==='learner-source'){const f=tutorialFrame(),d=f?.contentDocument;if(d?.querySelector('[data-open-media]')&&!f.dataset.tourSource){f.dataset.tourSource='1';d.querySelector('[data-open-media]').click()}}const t=tutorialTarget(step);if(!t){ring.hidden=true;return}
 if(step.expand){const d=t.el.closest(step.expand);if(d)d.open=true}
 if(scroll&&(t.frame||t.el.closest('.inspector-body,.modal')))t.el.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'});
 let r=t.el.getBoundingClientRect();
 if(t.frame){const f=t.frame.getBoundingClientRect();r={left:f.left+r.left,top:f.top+r.top,width:r.width,height:r.height,right:f.left+r.right,bottom:f.top+r.bottom};if(r.top<f.top||r.bottom>f.bottom){if(!scroll)t.el.scrollIntoView({block:'center',behavior:'instant'});ring.hidden=true;return}}
 const dock=$('#tutorialDock').getBoundingClientRect();
 if(r.width<1||r.height<1||r.top>=dock.top||r.bottom<0){ring.hidden=true;return}
 const top=Math.max(3,r.top-5),left=Math.max(3,r.left-5),right=Math.min(innerWidth-3,r.right+5),bottom=Math.min(dock.top-5,r.bottom+5);
 ring.hidden=right<=left||bottom<=top;Object.assign(ring.style,{left:left+'px',top:top+'px',width:(right-left)+'px',height:(bottom-top)+'px'});
}
function tutorialIsReady(){if(tutorialMode!=='flow')return true;const s=currentTutorialStep();return tutorialDone.has(tutorialStep)||(s.check?Boolean(s.check()):false)}
function renderTutorial(){
 const dock=$('#tutorialDock');if(!dock)return;
 $('#openGuide').textContent='Tutorial';$('#openGuide').onclick=startWalkthrough;
 if(dock.parentElement!==document.body)document.body.append(dock);
 let ring=$('#tutorialSpotlight');if(!ring){ring=document.createElement('div');ring.id='tutorialSpotlight';ring.hidden=true;ring.setAttribute('aria-hidden','true');document.body.append(ring)}
 dock.hidden=!tutorialActive;document.body.classList.toggle('tour-open',tutorialActive);$('#canvasArea').classList.toggle('guided',tutorialActive);
 if(!tutorialActive){ring.hidden=true;return}
 let html='';
 const top='<div class="tour-top"><div class="tour-path"><span class="'+(tutorialMode==='controls'?'current':'')+'">01 按钮导览</span><i>→</i><span class="'+(tutorialMode==='flow'?'current':'')+'">02 规划实操</span></div><div class="tour-top-actions"><button id="tutorialContents">目录</button><button id="dismissTutorial" aria-label="暂停教程">暂停 ×</button></div></div>';
 if(['welcome','bridge','complete'].includes(tutorialMode)){
  const bridge=tutorialMode==='bridge',complete=tutorialMode==='complete';
  html=top+'<div class="tour-intro"><div><span class="tour-kicker">'+(complete?'WALKTHROUGH COMPLETE':bridge?'按钮导览完成':'ACTIVITY CANVAS · HANDS ON')+'</span><h2>'+(complete?'你已走完这个活动。':bridge?'现在亲自规划一场活动。':'先认识按钮，再从头做一次。')+'</h2><p>'+(complete?'可回放任何一步，或回到画布继续调整；已保存的计划和回答保留。':bridge?'Slide 81 · 作者、读者、编辑 · 两组三人 · 15 分钟。接下来会检查你的操作结果。':'蓝框指向当前控件。先逐个了解用途，再走完输入、分工、学生演练与分享。')+'</p></div><div class="tour-intro-actions">'+(complete?'<button id="tutorialReturn" class="primary">回到画布</button><button id="tutorialStartFlow">再走一次实操</button>':bridge?'<button id="tutorialStartFlow" class="primary">开始规划实操 →</button>':'<button id="tutorialStartControls" class="primary">开始按钮导览 →</button><button id="tutorialResume">继续上次进度</button>')+'</div></div>';
 }else{
  const s=currentTutorialStep(),controls=tutorialMode==='controls',ready=tutorialIsReady(),count=controls?tutorialControls.length:tutorialFlow.length;
  html=top+'<div class="tour-main"><div class="tour-step-index"><span>'+(controls?s.chapter:'INFOVIS · ROLE PLAY')+'</span><strong>'+String(tutorialStep+1).padStart(2,'0')+' <small>/ '+count+'</small></strong><select id="tutorialJump" aria-label="跳转教程步骤">'+(controls?tutorialControls:tutorialFlow).map((x,i)=>'<option value="'+i+'" '+(i===tutorialStep?'selected':'')+'>'+(controls?x.chapter+' · ':'')+x.title+'</option>').join('')+'</select></div><div class="tour-instruction" aria-live="polite"><div class="tour-heading"><h2>'+esc(s.title)+'</h2>'+(s.effect?'<span class="tour-effect">'+s.effect+'</span>':'')+'</div><p>'+esc(s.text)+'</p><div class="tour-inline-actions"><button id="tutorialLocate">定位控件 ↗</button>'+(s.sample?'<button id="tutorialFill">填入示例文字</button>':'')+(s.ack?'<button id="tutorialAcknowledge">'+(ready?'✓ '+s.label:s.ack)+'</button>':'')+(s.people?[0,1,2].map(i=>'<button data-tour-person="'+i+'">'+((tutorialFacts.openedSlots||[]).includes(i)?'✓ ':'')+'Preview '+String.fromCharCode(65+i)+'</button>').join(''):'')+(s.action?'<button id="tutorialAction">'+s.actionLabel+'</button>':'')+(s.live&&!data.plan.live.started?'<button id="tutorialPrepared">只完成备课</button>':'')+'</div>'+(controls?'':ready?'<div class="tour-completion">✓ '+esc(s.label||'已完成')+'</div>':'<div class="tour-wait">完成上面的操作后，下一步会解锁。</div>')+'</div><div class="tour-nav"><button id="tutorialBack" '+(tutorialStep===0?'disabled':'')+'>← 上一个</button><button id="tutorialNext" class="primary" '+(!ready?'disabled':'')+'>'+(controls?tutorialStep===count-1?'进入规划实操 →':'看过了，下一个 →':tutorialStep===count-1?'完成教程 ✓':'下一步 →')+'</button><span>'+(controls?tutorialSeen.size+' / '+count+' 个控件已读':'你的操作会保存；预演与真实课堂分开。')+'</span></div></div>';
 }
 if(tutorialMenu)html+='<div class="tour-contents"><h3>教程目录</h3><button data-tour-path="controls">01 按钮导览 · '+tutorialSeen.size+' / '+tutorialControls.length+' 已读</button>'+tutorialChapters.map(([name,items],ci)=>'<button data-tour-chapter="'+ci+'">'+name+'<span>'+items.filter((_,ii)=>tutorialSeen.has('c'+ci+'-'+ii)).length+' / '+items.length+'</span></button>').join('')+'<button data-tour-path="flow">02 规划实操 · '+tutorialDone.size+' / '+tutorialFlow.length+' 已完成</button></div>';
 if(html===tutorialLastHTML){positionTutorial();return}tutorialLastHTML=html;dock.innerHTML=html;
 $('#dismissTutorial').onclick=()=>{tutorialActive=false;tutorialMenu=false;saveTutorial();renderTutorial();fit()};
 $('#tutorialContents').onclick=()=>{tutorialMenu=!tutorialMenu;renderTutorial()};
 $('#tutorialStartControls')?.addEventListener('click',()=>{tutorialSeen.clear();tutorialDone.clear();tutorialFacts={};beginTutorial('controls',0)});
 $('#tutorialStartFlow')?.addEventListener('click',()=>{tutorialDone.clear();tutorialFacts={};beginTutorial('flow',0)});
 $('#tutorialReturn')?.addEventListener('click',()=>{tutorialActive=false;closeModal();setInspector(false);saveTutorial();renderTutorial();fit()});
 $('#tutorialResume')?.addEventListener('click',()=>{const s=restoreTutorial();beginTutorial(s?.mode==='flow'?'flow':'controls',s?.step||0)});
 $('#tutorialJump')?.addEventListener('change',e=>goTutorial(+e.target.value));
 $('#tutorialLocate')?.addEventListener('click',()=>{ensureTutorialContext(currentTutorialStep().context,true);positionTutorial(true)});
 $('#tutorialBack')?.addEventListener('click',()=>goTutorial(tutorialStep-1));
 $('#tutorialNext')?.addEventListener('click',()=>{if(!tutorialIsReady())return;if(tutorialMode==='controls'){tutorialSeen.add(currentTutorialStep().id);if(tutorialStep===tutorialControls.length-1){closeModal();setInspector(false);tutorialMode='bridge';saveTutorial();renderTutorial();fit();return}}else{tutorialDone.add(tutorialStep);if(tutorialStep===tutorialFlow.length-1){completeTutorial();return}}goTutorial(tutorialStep+1)});
 $('#tutorialFill')?.addEventListener('click',()=>{const s=currentTutorialStep();if(s.fill==='brief'){const el=$('#planningBrief');if(el){el.value=s.sample;el.dispatchEvent(new Event('input',{bubbles:true}))}}else{const d=tutorialFrame()?.contentDocument,el=d?.querySelector(s.fill==='group'?'#groupText':'[data-answer]');if(el){const details=el.closest('details');if(details)details.open=true;el.value=s.sample;el.dispatchEvent(new Event('input',{bubbles:true}));el.scrollIntoView({block:'center'});el.focus()}}renderTutorial()});
 $('#tutorialAcknowledge')?.addEventListener('click',()=>{tutorialDone.add(tutorialStep);saveTutorial();renderTutorial()});
 $$('[data-tour-person]').forEach(b=>b.onclick=()=>{tutorialOpenPerson(+b.dataset.tourPerson);tutorialContext='';});
 $('#tutorialAction')?.addEventListener('click',async()=>{await api('/api/host/sample',{});sample=true;$('#sampleButton').classList.add('active');refreshPreviewPages();tutorialFacts.examples=true;saveTutorial();renderTutorial();toast('Examples loaded in previews only. Real student work is unchanged.')});
 $('#tutorialPrepared')?.addEventListener('click',()=>{tutorialDone.add(tutorialStep);completeTutorial()});
 $$('[data-tour-chapter]').forEach(b=>b.onclick=()=>{const ci=+b.dataset.tourChapter;beginTutorial('controls',tutorialControls.findIndex(s=>s.ci===ci))});
 $$('[data-tour-path]').forEach(b=>b.onclick=()=>beginTutorial(b.dataset.tourPath,0));
 positionTutorial();
}
function beginTutorial(mode,step=0){tutorialActive=true;tutorialMode=mode;tutorialMenu=false;tutorialContext='';goTutorial(step)}
function goTutorial(step){const list=tutorialMode==='controls'?tutorialControls:tutorialFlow;tutorialStep=Math.max(0,Math.min(list.length-1,step));tutorialMenu=false;renderTutorial();ensureTutorialContext(currentTutorialStep().context);saveTutorial();fit();setTimeout(()=>positionTutorial(true),80)}
function startWalkthrough(){if(!data.plan.planned)return beginTutorial('flow',0);const active=tutorialActive;tutorialActive=true;tutorialMenu=false;if(active&&['controls','flow'].includes(tutorialMode)){tutorialMenu=true;renderTutorial();return}tutorialMode='welcome';tutorialLastHTML='';renderTutorial();fit()}
function completeTutorial(){tutorialMode='complete';tutorialContext='';closeModal();setInspector(false);saveTutorial();renderTutorial();fit()}
function planWalkthroughReady(){if(tutorialActive&&tutorialMode==='flow'){tutorialFacts.built=true;tutorialDone.add(0);tutorialDone.add(1);saveTutorial();renderTutorial()}tutorialContext=''}
function tutorialBoot(){const params=new URLSearchParams(location.search),s=restoreTutorial();if(!data.plan.planned&&params.get('walkthrough')!=='1'){tutorialActive=false;renderTutorial();return}if(params.get('view')==='flow'){tutorialActive=false;saveTutorial();renderTutorial();return}if(params.get('walkthrough')==='1'||!s){tutorialActive=true;tutorialMode='welcome';tutorialStep=0;renderTutorial();fit()}else if(s?.active&&['controls','flow'].includes(s.mode))beginTutorial(s.mode,s.step);}
function tutorialEvent(event,detail={}){
 if(!tutorialActive||tutorialMode!=='flow')return;
 if(event==='opened-person'){const slots=new Set(tutorialFacts.openedSlots||[]);slots.add(detail.slot);tutorialFacts.openedSlots=[...slots]}
 if(event==='response-saved'&&detail.submitted){if(detail.phase==='individual')tutorialFacts.prepared=true;if(detail.phase==='discussion')tutorialFacts.exchanged=true;if(detail.phase==='revision')tutorialFacts.revised=true}
 if(event==='group-saved')tutorialFacts.shared=true;
 if(event==='live-start')tutorialFacts.started=true;
 if(event==='live-stage'&&detail.kind==='discussion')tutorialFacts.liveDiscussion=true;
 if(event==='live-stage'&&detail.kind==='revision')tutorialFacts.liveRevision=true;
 if(event==='live-stop')tutorialFacts.ended=true;
 saveTutorial();renderTutorial();
}
window.addEventListener('message',e=>{if(e.origin!==location.origin||e.data?.type!=='tutorial-event')return;const f=tutorialFrame();if(f&&e.source===f.contentWindow)tutorialEvent(e.data.event,e.data)});
document.addEventListener('input',e=>{if(tutorialActive&&tutorialMode==='flow'&&e.target.closest('#planningForm'))renderTutorial()});
document.addEventListener('change',()=>{if(tutorialActive&&tutorialMode==='flow')setTimeout(renderTutorial,60)});
window.addEventListener('resize',()=>{positionTutorial();if(data)fit()});
document.addEventListener('scroll',()=>positionTutorial(),true);
setInterval(()=>{if(tutorialActive&&!document.hidden)renderTutorial()},450);
renderTutorial();

