/* One spatial planner: configuration before generation, summary afterward. */
let plannerWidgetOpen=false,plannerDraft=null;
function getPlannerDraft(){
 if(!plannerDraft){const p=data.plan;plannerDraft={planned:true,intent:p.planned?p.intent:'',materialId:p.materialId,structure:p.structure,groupSize:p.groupSize,groupCount:p.groupCount,budget:p.budget}}
 return plannerDraft;
}
function rememberPlannerDraft(){
 if(!$('#planningForm'))return;
 plannerDraft={planned:true,intent:$('#planningBrief').value,materialId:$('#planningMaterial').value,structure:$('#planningMethod').value,groupSize:$('#planningSize').value,groupCount:$('#planningGroups').value,budget:$('#planningBudget').value};
 if(typeof renderPlannerArrangement==='function')renderPlannerArrangement();
}
function resetPlannerWidget(){plannerWidgetOpen=false;plannerDraft=null;document.body.dataset.planner='closed'}
function plannerWidgetPosition(){
 const saved=data.plan.positions['planner-config'];if(saved)return saved;
 const area=$('#canvasArea').getBoundingClientRect(),w=Math.max(320,Math.min(480,area.width-48)),h=Math.max(420,Math.min(680,area.height-110));
 const compact=data.plan.positions['meta-plan']||{x:35,y:220,w:310};
 return {x:data.plan.planned?compact.x+compact.w-w:28,y:data.plan.planned?compact.y:28,w,h};
}
function focusPlannerWidget(){
 const w=$('#window-plan');if(!w)return;
 const area=$('#canvasArea').getBoundingClientRect(),width=parseFloat(w.style.width),height=parseFloat(w.style.height);
 scale=Math.min(1,(area.width-48)/width,(area.height-110)/height);tx=(area.width-width*scale)/2-parseFloat(w.style.left)*scale;ty=26-parseFloat(w.style.top)*scale;transform();
}
function openPlannerWidget(){
 rememberPlannerDraft();plannerWidgetOpen=true;getPlannerDraft();closeModal();setInspector(false);setTool('select');render();focusPlannerWidget();$('#planningBrief')?.focus({preventScroll:true});
}
function closePlannerWidget(){
 rememberPlannerDraft();plannerWidgetOpen=false;render();if(data.plan.planned)fit();$('#planButton')?.focus({preventScroll:true});
}
function togglePlannerWidget(){if(plannerWidgetOpen)closePlannerWidget();else openPlannerWidget()}
function renderPlannerNode(w){
 w.classList.toggle('planner-widget',plannerWidgetOpen);w.classList.toggle('interacting',plannerWidgetOpen);
 const close=w.querySelector('[data-close-planner]');close.hidden=!plannerWidgetOpen;close.onclick=closePlannerWidget;
 if(plannerWidgetOpen){
  w.dataset.positionKey='planner-config';place(w,plannerWidgetPosition());
  if(!w.querySelector('#planningForm'))mountPlanningForm(w);
 }else{
  w.dataset.positionKey='meta-plan';place(w,data.plan.positions['meta-plan']||{x:35,y:220,w:310,h:590});
  w.querySelector('.window-body').innerHTML=teacherPlanHTML();
 }
}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&plannerWidgetOpen&&$('#overlay').hidden){e.preventDefault();e.stopImmediatePropagation();closePlannerWidget()}},true);
