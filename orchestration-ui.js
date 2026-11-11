/* Actual learner pages and their library-backed annotations share one activity model. */
function plannedPhases(p){
 const budget=p.budget,first=Math.max(1,Math.round(budget*.27)),last=Math.max(1,Math.round(budget*.27)),name=p.structure;
 const spec={
  'Role Play':[
   ['Prepare','You are at an editorial meeting about this visual. Prepare your assigned position.','Your role account'],
   ['Roundtable','Present your position. Ask a peer to explain one reading. Use the source to decide what to keep and what to clarify.','An exchange note and a shared editorial decision'],
   ['Revise','After the debrief, revise your own account. What changed when you heard the other roles?','Your revised account']
  ],
  'Analytic Teams':[
   ['Inspect','Read the shared visual through your assigned analytic lens. Prepare one finding to explain.','Your analytic finding'],
   ['Integrate','Explain your finding. Use a peer’s finding to extend or qualify the group’s interpretation.','An integrated group interpretation'],
   ['Report & revise','After the group report, revise your interpretation. Explain how a peer’s contribution changed or supported it.','Your revised interpretation']
  ],
  'Think–Pair–Share':[
   ['Think','Read the visual independently. Prepare your interpretation before seeing your partner’s.','Your independent interpretation'],
   ['Pair exchange','Each partner explains and listens. Compare one visual choice and clarify why your readings differ.','Your exchange note; a pair takeaway is optional'],
   ['Share & revise','Share one pair finding when the teacher invites reports. Then revise your own explanation using the exchange.','Your revised explanation']
  ],
  'Peer Editing':[
   ['Draft','Write your own short critique of the visual. State a claim, a source detail, and a judgment.','Your critique draft'],
   ['Peer review','Read your assigned peer’s draft. Check the claim, source detail, and clarity. Suggest one specific revision.','Written feedback to the draft’s author'],
   ['Revise','Revise your critique using the feedback. Explain which suggestion you accepted or declined and why.','Your revised critique']
  ]
 }[name];
 return ['individual','discussion','revision'].map((kind,i)=>({id:['read','discuss','revise'][i],kind,title:spec[i][0],minutes:[first,Math.max(1,budget-first-last),last][i],instruction:spec[i][1],deliverable:spec[i][2]}));
}
function taskHandoff(method,title){
 if(method==='Peer Editing')return 'Review {peer}’s draft. Check the claim, source detail, and clarity. Suggest one specific revision.';
 if(method==='Think–Pair–Share')return 'Explain your reading to {peer}. Listen to theirs, then clarify one difference using the visual.';
 return 'Explain your '+title.toLowerCase()+' finding to {peer}. Ask how their finding changes or qualifies your reading.';
}


function guideState(){return ActivityGuide.derive(data.plan,data.people,data.roleplay,previewGroup)}
function guidePhaseIndex(){return phase().kind==='individual'?0:phase().kind==='discussion'?1:2}
function renderGuideToolbar(){
 const g=guideState();$('#canvasViewBar').innerHTML='<button id="notationToggle" class="notation-toggle" aria-pressed="'+guidanceVisible+'" title="Show or hide teaching annotations">'+icon('arrow')+'Annotations</button><button id="methodHelp" class="method-help">'+esc(g.method.label)+' <span>CoLT '+g.method.number+'</span>'+icon('expand')+'</button><span class="distribution-caption">'+esc(g.cross?'Across groups · same-role exchange':g.method.distribution)+'</span>';
 $('#notationToggle').onclick=()=>{guidanceVisible=!guidanceVisible;try{localStorage.setItem('activity-canvas-guidance',guidanceVisible?'on':'off')}catch{}renderGuideToolbar();$$('iframe').forEach(f=>f.contentWindow?.postMessage({type:'preview-annotations',show:guidanceVisible},location.origin));drawConnections();fit()};$('#methodHelp').onclick=methodGuideModal;
}
function plannerShell(){
 return '<article id="window-plan" class="web-window meta-planner" data-window="plan" tabindex="0" aria-label="Meta planner, instructor only"><div class="window-bar planner-handle"><span class="planner-symbol">'+icon('roles')+'</span><strong>Planner</strong><span class="planner-grip" aria-hidden="true">⠿</span><button class="planner-close" data-close-planner aria-label="Close Planner" hidden>'+icon('close')+'</button></div><div class="window-body"></div><div class="window-resizer" aria-hidden="true"></div></article>';
}
function legacyTeacherPlanHTML(){
 const p=data.plan,m=material(p.materialId),g=guideState(),i=guidePhaseIndex(),total=p.phases.reduce((n,s)=>n+s.minutes,0),split=p.tasks.some(t=>t.assignees.length!==p.groupSize);
 const rows=[
  ['task','Tasks',p.tasks.length+' question'+(p.tasks.length===1?'':'s')],
  ['group','Groups',p.groupCount+' × '+p.groupSize+' learners'],
  ['distribution','Distribution',split?'Different responsibilities':'Same task for everyone'],
  ['interaction','Interaction',(p.interaction.channel==='write'?'Written':'Spoken')+' · '+(p.interaction.visibility==='after_group'?'after group submits':p.interaction.visibility==='after_own'?'after own submission':'always visible')],
  ['timing','Time',total+' min · '+p.phases.length+' stages']
 ];
 return '<div class="meta-plan"><div class="meta-plan-heading"><span class="meta-kicker">INSTRUCTOR ONLY</span><h2>'+esc(g.method.label)+'</h2><p class="meta-scope">Applies to all '+p.groupCount*p.groupSize+' student pages</p></div><button class="teacher-material meta-material" data-focus="material">'+icon('file')+'<span><small>SLIDE '+esc(m.slide)+'</small><strong>'+esc(m.title)+'</strong></span>'+icon('arrow')+'</button><div class="meta-attributes" aria-label="Activity configuration">'+rows.map(([attr,label,value])=>'<button data-guide-attribute="'+attr+'" aria-label="Configure '+label+'"><span>'+label+'</span><strong>'+esc(value)+'</strong><span class="meta-chevron" aria-hidden="true">›</span></button>').join('')+'</div><div class="teacher-stage-duty meta-facilitation"><span>FACILITATION · '+esc(phase().title.toUpperCase())+'</span><p>'+esc(g.method.teachers[i])+'</p></div><div class="meta-plan-footer"><button class="meta-edit-brief" data-plan-query>Edit brief '+icon('arrow')+'</button>'+(phase().kind==='discussion'&&g.collective?'<button class="teacher-shared" data-focus="shared-group">Preview group output '+icon('expand')+'</button>':'')+'</div></div>';
}

function bindGuideCards(){
 $$('[data-guide-attribute]').forEach(b=>b.onclick=e=>{e.stopPropagation();tab=b.dataset.guideAttribute;render();setInspector(true)});
}
function methodGuideModal(){
 const g=guideState(),m=g.method,p=data.plan;
 showModal(modalHead(m.label+' · CoLT '+m.number,m.mechanism)+'<div class="method-overview-flow">'+m.steps.map((x,i)=>'<div><span>'+String(i+1).padStart(2,'0')+'</span><strong>'+esc(x)+'</strong></div>').join('')+'</div><div class="method-role-list">'+g.actors.map(a=>'<div><span class="role-letter">'+String.fromCharCode(65+a.person.slot)+'</span><div><strong>'+esc(a.role)+'</strong><p>'+esc(a.handoff)+'</p></div></div>').join('')+'</div><p class="method-adaptation">'+esc(m.adaptation)+'</p><p class="method-source">Procedure grounding: <a href="'+m.source+'" target="_blank" rel="noreferrer">Barkley, Major & Cross (2014) ↗</a> · <a href="/Method_Procedures.txt" target="_blank">Procedure records ↗</a></p>');
}
function planningMethodPreview(){
 const el=$('#planningMechanism');if(!el)return;const name=$('#planningMethod').value,m=ActivityGuide.methods[name],size=+$('#planningSize').value;
 el.innerHTML='<div class="planning-mechanism-head"><span>ACTIVITY FLOW</span><strong>'+esc(m.label)+' · CoLT '+m.number+'</strong></div><div class="planning-mini-flow">'+m.steps.map((x,i)=>'<div><span>'+String(i+1)+'</span><strong>'+esc(x)+'</strong></div>').join('')+'</div><p>'+esc(m.mechanism)+'</p>'+((name==='Think–Pair–Share'||name==='Peer Editing')&&size!==2?'<p class="planning-adaptation">'+(name==='Peer Editing'?'Review ring: each author reviews a peer and receives feedback from another.':size+' learners: a small-group adaptation with turns to explain and listen.')+'</p>':name==='Analytic Teams'&&size<4?'<p class="planning-adaptation">Condensed team: fewer analytic responsibilities than the book’s 4–5-person arrangement.</p>':'');
}

let teacherInk=[],teacherInkFrame=0;
function scheduleTeacherAnnotations(){cancelAnimationFrame(teacherInkFrame);teacherInkFrame=requestAnimationFrame(drawTeacherAnnotations)}
function drawTeacherAnnotations(){
 teacherInk.forEach(a=>a.remove());teacherInk=[];const layer=$('#annotationLayer');if(!layer)return;layer.replaceChildren();if(!guidanceVisible||!window.RoughNotation)return;
 const target=$('.teacher-stage-duty'),area=$('#canvasArea').getBoundingClientRect();if(!target)return;const r=target.getBoundingClientRect();if(r.width<2)return;
 const anchor=document.createElement('span');anchor.className='notation-anchor';Object.assign(anchor.style,{left:(r.left-area.left)+'px',top:(r.top-area.top)+'px',width:r.width+'px',height:r.height+'px'});layer.append(anchor);
 const ink=RoughNotation.annotate(anchor,{type:'bracket',brackets:['left'],color:'#66aaff',padding:4,strokeWidth:1.6,iterations:2,animate:false});ink.show();teacherInk.push(ink);
}
function drawGuideConnections(){
 const svg=$('#connections');svg.replaceChildren();if(!guidanceVisible||!window.rough)return;const g=guideState(),p=$('#window-plan');if(!p)return;
 const rc=rough.svg(svg),ns='http://www.w3.org/2000/svg',ink='#397fc5',rect=w=>({x:parseFloat(w.style.left),y:parseFloat(w.style.top),w:parseFloat(w.style.width),h:parseFloat(w.style.height)}),pos=new Map(g.actors.map(a=>[a.person.id,rect($('#window-student-'+a.person.id))]));
 function path(d,seed){const line=rc.path(d,{stroke:ink,strokeWidth:1.7,roughness:.85,bowing:.6,seed,disableMultiStroke:true});line.classList.add('notation-connection');svg.append(line)}
 function arrow(x,y,angle,seed){const len=10,spread=.48;[[angle+Math.PI-spread,seed],[angle+Math.PI+spread,seed+1]].forEach(([a,s])=>svg.append(rc.line(x,y,x+len*Math.cos(a),y+len*Math.sin(a),{stroke:ink,strokeWidth:1.7,roughness:.6,seed:s,disableMultiStroke:true})))}
 function note(x,y,text){const e=document.createElementNS(ns,'text');e.classList.add('notation-note');e.setAttribute('x',x);e.setAttribute('y',y);e.setAttribute('text-anchor','middle');e.textContent=text;svg.append(e)}
 if(phase().kind==='discussion'){
  const top=Math.min(...[...pos.values()].map(q=>q.y)),edges=[...g.edges].sort((a,b)=>{const ap=pos.get(a.from),at=pos.get(a.to),bp=pos.get(b.from),bt=pos.get(b.to);return Math.abs((ap?.x||0)-(at?.x||0))-Math.abs((bp?.x||0)-(bt?.x||0))});
  edges.forEach((edge,i)=>{const a=pos.get(edge.from),b=pos.get(edge.to);if(!a)return;if(!b){note(a.x+a.w/2,a.y-30,'→ '+edge.actor.targetLabel);return}const lift=58+i*50,y=top-lift,ax=a.x+a.w/2-15,bx=b.x+b.w/2+15;path('M '+ax+' '+(a.y-4)+' C '+ax+' '+y+' '+bx+' '+y+' '+bx+' '+(b.y-8),13+i*5);arrow(bx,b.y-8,Math.PI/2,42+i*5);note((ax+bx)/2,top-lift*.75-11,String.fromCharCode(65+edge.actor.person.slot)+' → '+String.fromCharCode(65+edge.actor.target.slot)+' · '+edge.label.toLowerCase())});
 }else{
  const t=rect(p),top=Math.min(...[...pos.values()].map(q=>q.y)),y=top-45,spine=t.x+t.w+26;
  path('M '+(t.x+t.w)+' '+(t.y+150)+' H '+spine+' V '+y+' H '+Math.max(...[...pos.values()].map(q=>q.x+q.w/2)),7);
  g.actors.forEach((a,i)=>{const q=pos.get(a.person.id),x=q.x+q.w/2;path('M '+x+' '+y+' V '+(q.y-8),31+i*4);arrow(x,q.y-8,Math.PI/2,51+i*4)});
  note((spine+Math.max(...[...pos.values()].map(q=>q.x+q.w/2)))/2,y-13,phase().kind==='individual'?(g.sameSource?'Same source · assigned questions':'Materials follow each assignment'):'Debrief → each learner revises');
 }
}
