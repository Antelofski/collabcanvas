/* The catalogue lists each distinct control, rather than repeating every learner instance. */
const tutorialBrief='Students review the seven-frame voting story as a story author, first-time reader, and critical editor. Each prepares an account, questions a peer in a roundtable, then revises their own explanation. Use 2 groups of 3 learners for 15 minutes.';
const ctl=(title,target,text,context='canvas',extra={})=>({title,target,text,context,...extra});
const tutorialChapters=[
 ['入口与计划',[
  ctl('Planner','#planButton','点画布下方按钮，展开可移动的配置 widget。它不会立即修改现有计划。'),
  ctl('Activity title','#activityTitle','修改活动名称；离开输入框后自动保存。'),
  ctl('Undo','#undo','撤销最近一次计划编辑，不会撤销学生答案、消息或课堂启动。'),
  ctl('Tutorial','#openGuide','回到教程目录；已读控件和实操进度会保留。'),
  ctl('Students','#studentsButton','查看每个人的独立页面、预览、HTML 和二维码。'),
  ctl('Deploy','#shareButton','班级入口让每个学生扫码后领取不同位置。'),
  ctl('Activity description','#planningBrief','写学生先做什么、如何交流、最后留下什么。','plan'),
  ctl('Use InfoVis example','#usePlanningExample','按当前选择的方法填入示例描述，填后仍可改。','plan'),
  ctl('Material','#planningMaterial','选择课件材料；起始问题会对应这份材料。','plan'),
  ctl('Starting arrangement','#planningMethod','本地演示支持四种起始安排，尚未连接生成模型。','plan'),
  ctl('Groups / Learners / Minutes','.planning-numbers','设小组数量、每组人数和总分钟数，之后仍可改。','plan'),
  ctl('Generation prompt','.prompt-note a','打开完整生成 prompt，它不是实时生成按钮。','plan'),
  ctl('Generate UI','#planningForm button[type=submit]','把表单落实成阶段、任务和个人页面。导览无需点击，实操时再建。','plan',{effect:'会修改计划'}),
  ctl('Close / Escape','[data-close-planner]','收起画布上的 Planner，暂存描述和配置；重新打开仍可继续编辑。','plan')
 ]],
 ['材料与预览',[
  ctl('Materials','#materialsButton','打开五个 InfoVis 例子，或加入自己的图片 / PDF。'),
  ctl('Choose a material','.material-choice','切换材料和起始问题，原学生答案保留。','materials',{effect:'会修改计划'}),
  ctl('Reference window','#toggleReference','把额外材料窗口放到画布，或收起来。','materials'),
  ctl('Upload','#upload','加入 PNG、JPG 或 PDF，再从材料库选它；不会自动解读上传内容。','materials'),
  ctl('Course slides','#sourceButton','在新标签页打开原课件 PDF。'),
  ctl('Preview stage','#phaseBar','切换所有个人页面的预览阶段，同时打开 Time；不会推进真实课堂。'),
  ctl('Preview group','#groupPreview','切换检查的小组。各组复用计划，但各自保存答案。')
 ]],
 ['自由画布',[
  ctl('Annotations','#notationToggle','显示或隐藏学生实际页面上的手绘标注和同伴交流箭头；不切换界面。'),
  ctl('CoLT mechanism','#methodHelp','查看当前方法的流程、同伴交接和改编说明。'),
  ctl('Meta planner','.meta-planner','深色模块是教师专用的活动配置，控制所有学生页面；五行设置分别打开对应的 attribute。'),
  ctl('Peer handoffs','#connections .notation-connection','手绘箭头表示谁向谁提问或反馈；每名学生的完整页面始终留在画布。','role-exchange'),

  ctl('Select / V','#selectTool','拖动卡片移动；单击打开设置。拖动只改变画布位置。'),
  ctl('Hand / H','#handTool','拖动画布平移；按住空格也可临时平移。'),
  ctl('Zoom −','#zoomOut','缩小画布，不改变学生实际页面的字号。'),
  ctl('Zoom +','#zoomIn','放大画布；也可用 Command / Ctrl 加滚轮。'),
  ctl('Percentage / Fit','#zoomValue','点击百分比，让所有卡片回到可见范围。'),
  ctl('Fit all','#fit','展开图标与点击百分比的适配功能相同。'),
  ctl('Arrange windows','#layoutButton','恢复默认卡片排列，任务和答案不变。','canvas',{effect:'会重排画布'}),
  ctl('Plan card / Edit brief','[data-plan-query]','左侧 Meta planner 控制所有学生页面；Edit brief 重开活动描述表单。'),
  ctl('Material thumbnail','.plan-source,.teacher-material','展开原材料，检查完整视觉内容和背景。'),
  ctl('Preview stages','#phaseBar','用上方阶段按钮切换所有个人页面的预览。','canvas'),
  ctl('Group workspace','[data-focus="shared-group"]','打开本组共同产物，个人回答依然独立保存。','role-exchange'),
  ctl('Edit a learner','[data-inspect^="student-"]','标题栏列表图标打开这名学生的任务设置。'),
  ctl('Open a learner','[data-focus^="student-"]','打开可操作的大页面，每个人都有自己的版本。'),
  ctl('Drag / Resize / Enter','.web-window','拖标题移动，选中后拖右下角缩放。双击使用内嵌页面，或点击 Open 打开大页面。'),
  ctl('Change this activity','#commandInput','支持 discussion to 6、3 learners per group、hide peers；其他文字只存备注。','command'),
  ctl('Apply command','#applyCommand','执行支持的本地规则；这不是自由对话的 AI。','command',{effect:'会修改计划'})
 ]],
 ['Task：任务',[
  ctl('Edit activity / Close inspector','#inspectorToggle','左侧列表图标显示或隐藏设置；面板右上角 × 也能关闭。'),
  ctl('Five attribute tabs','#attributeTabs','Task 改问题，Group 改组队，Roles 改分配，Interaction 改交流，Time 改时长。','task'),
  ctl('Collaboration method','#structure','切换方法会更新起始任务，请重查问题和交接。','task',{effect:'会修改计划'}),
  ctl('View as','#selectedPerson','选择另一名学生，查看分给这个位置的题。','task'),
  ctl('Task title / Question','[data-task-field="prompt"]','改题目和提问，离开字段后保存；同角色的所有组一起更新。','task'),
  ctl('Peer action','[data-task-field="handoff"]','说明向谁提问、请谁检查。保留 {peer}，页面会填入目标同伴。','task',{fallback:'.task-row'}),
  ctl('Response / Options','[data-task-field="responseType"]','可选简答或选择加解释；选后者会出现逐行填写选项的字段。','task'),
  ctl('Task source','[data-task-field="materialId"]','为这道题选材料；不同角色可以收到不同材料。','task'),
  ctl('Add a question','#addTask','给当前角色加题，再用 Roles 调整分配。','task',{effect:'会增加任务'}),
  ctl('Activity note','#intent','展开备注再编辑；备注本身不会重写其他字段。','task',{expand:'details'})
 ]],
 ['阶段与交接',[
  ctl('Edit stages & handoffs','#editStages','查看前一步产物怎样进入下一步。','task'),
  ctl('Stage title / Work type','[data-stage][data-key="title"]','改名称和类型，类型决定个人准备、讨论或修订页面。','stages'),
  ctl('Instruction / Output','[data-stage][data-key="instruction"]','写本阶段做什么、留下什么，输出要能被下一步使用。','stages'),
  ctl('Move stage ↑ / ↓','[data-up]','前移或后移阶段，答案仍按阶段 ID 保存。','stages',{effect:'会调整阶段'}),
  ctl('Remove stage ×','[data-delete]','移除阶段但后台保留答案；可用 Undo 撤回计划修改。','stages',{effect:'会移除阶段'}),
  ctl('Add a check stage','#addStage','增加核对环节，再设问题、产物和分钟数。','stages',{effect:'会增加阶段'})
 ]],
 ['Group 与 Roles',[
  ctl('Groups / Places','#groupCount','设组数和人数；人数变化会调整角色，已有身份和答案保留。','group'),
  ctl('Discussion groups','#regroup','保持原组，或让不同组的同角色交流；跨组至少需要两个组。','group'),
  ctl('Swap membership','#swapA','选择两个位置，个人答案跟作者走，共同产物留在原讨论组。','group'),
  ctl('Swap learners','#swap','交换所选两人的组和位置，导览中无需执行。','group',{effect:'会交换成员'}),
  ctl('Assign A / B / C','[data-assign]','点亮哪个字母，谁就收到这道题。','distribution'),
  ctl('Source per role','[data-source]','为该任务选材料，个人页面会更新。','distribution'),
  ctl('Give everyone all questions','#sameTasks','每人收到所有题，个人回答依然分开保存。','distribution',{effect:'会修改分配'}),
  ctl('Split questions across roles','#splitTasks','按角色轮流分题，再检查任务覆盖和同伴依赖。','distribution',{effect:'会修改分配'})
 ]],
 ['Interaction：交流与反馈',[
  ctl('Pace','#mode','Teacher-led 由教师切阶段；Self-paced 由学生自己选择阶段。','interaction'),
  ctl('Discussion channel','#channel','面对面说完记下来，或写给同伴的回复。系统不录音。','interaction'),
  ctl('Show peers’ interpretations','#visibility','自己提交后、全组提交后，或从开始显示同伴解释。','interaction'),
  ctl('Show the reference','#feedback','设参考解释何时开放：教师放行、组产物保存后或学生请求时。','interaction'),
  ctl('Teacher reference','#reference','填写可核对的参考说明，这不是自动判分。','interaction'),
  ctl('Release / Hide reference','#releaseReference','对真实学生放行或隐藏参考，教程不会自动点击。','interaction',{effect:'影响真实学生'}),
  ctl('Message to group','#feedbackText','选组号并写提示，例如提醒核对标签或解释分歧。','interaction'),
  ctl('Send to this group','#sendFeedback','发送提示。系统只知道保存的回答和明确求助，不知道现场谈话内容。','interaction',{effect:'会发送组消息'})
 ]],
 ['Time：时间与课堂',[
  ctl('Time budget','#budget','总预算和阶段用时分开设，超时会显示差额。','timing'),
  ctl('Stage minutes','[data-minutes]','调整阶段分钟数，计时与计划总时长一起更新。','timing'),
  ctl('Live stage','#liveStage','推进真实课堂阶段，与上方 Preview stage 不同。','timing',{effect:'影响真实学生'}),
  ctl('Start / Pause / Resume','#startPause','开始、暂停或继续计时，不会自动推进下一阶段。','timing',{effect:'影响真实学生'}),
  ctl('End live session','#stopClass','结束课堂计时，保留所有已保存的回答。','timing',{effect:'影响真实学生'}),
  ctl('Changes','#historyButton','查看本次打开页面以来的计划修改记录，Undo 在顶部。','timing')
 ]],
 ['每名学生的页面',[
  ctl('Version group / stage','.version-filters','在 Students 中切组和阶段，A/B/C 始终各有个人页面。','versions'),
  ctl('Preview','[data-open-student]','打开可试填的个人预览，预览与真实学生数据分开。','versions'),
  ctl('Open student ↗','.version-actions a[target]','打开这个位置的真实学生入口，请给不同学生不同位置。','versions'),
  ctl('HTML ↓','.version-actions a[href^="/api/export"]','下载个人 HTML。离线答案只在自己的设备，不同步讨论。','versions'),
  ctl('Personal QR','[data-version-qr]','为一个学生位置生成二维码，不要让全组共用这个位置。','versions'),
  ctl('Expand source',{frame:'[data-open-media]'},'把源图放大，连续查看完整的七帧故事。','learner-read'),
  ctl('First / Previous / Next / Last',{frame:'.frame-nav'},'逐帧查看人口筛选；首尾按钮直接跳到第一帧和最后一帧。','learner-read'),
  ctl('Submit / Update interpretation',{frame:'#responseForm button[type=submit]'},'输入解释再提交，可继续修改。分享规则会检查是否提交。','learner-read',{effect:'只保存预览'}),
  ctl('Save my note',{frame:'#responseForm button[type=submit]'},'讨论后保存自己的核对或改变，不覆盖同伴笔记。','learner-discuss'),
  ctl('Shared decision / Save group',{frame:'.shared-output'},'展开并保存共同决定；组内共享，但个人笔记依然独立。','learner-shared'),
  ctl('Send reply（书面模式）',{frame:'#postReply'},'在 Interaction → Discussion 选书面模式后出现，回复给页面注明的同伴。','learner-discuss',{optional:true}),
  ctl('Save explanation',{frame:'#responseForm button[type=submit]'},'修订最终解释，说明交流后改变了什么和为什么。','learner-revise'),
  ctl('Ask the teacher to join',{frame:'#help'},'提交明确的求助，不录制或分析声音。','learner-read',{effect:'只提交预览求助'}),
  ctl('Show the reference（按需）',{frame:'#requestReference'},'只有规则设为学生请求时出现，可见性由后台控制。','learner-read',{optional:true}),
  ctl('Close source / Escape',{frame:'#closeMedia'},'放大源图后点 Close 返回，Escape 也能关闭。','learner-source')
 ]],
 ['分享与样例',[
  ctl('Example answers','#sampleButton','加载或清除材料对应的预览样例，不是学生真实作答。'),
  ctl('Class QR / Share link','.qr-layout>div:first-child','班级二维码领取不同位置，设备需能通过同一 Wi-Fi 访问这台 Mac。','share'),
  ctl('Copy this link','#copyShare','复制当前班级或个人链接，不会替你发送。','share'),
  ctl('QR / Open per person','[data-person-qr]','列表指向具体位置，班级入口与个人入口用途不同。','share'),
  ctl('Finish button tour','#openGuide','控件已走完，接下来亲自完成计划、学生演练、分享与课堂控制。')
 ]]
];
const tutorialControls=tutorialChapters.flatMap(([chapter,items],ci)=>items.map((item,ii)=>({...item,chapter,ci,ii,id:'c'+ci+'-'+ii})));
const flow=(title,text,context,target,extra={})=>({title,text,context,target,...extra});
const tutorialFlow=[
 flow('1 · 输入活动描述','点画布下方的 Planner，在 widget 中描述学生怎么学。可填入下面示例：作者、读者、编辑先各自准备，再互问，最后各自修订。','plan','#planningBrief',{sample:tutorialBrief,fill:'brief',check:()=>($('#planningBrief')?.value.trim().length||0)>50,label:'活动描述已填好'}),
 flow('2 · 选择材料和规模','选择 Slide 81、Role Play、2 groups、3 learners、15 minutes。围绕同一份投票地图开展活动。','plan','.planning-numbers',{check:()=>$('#planningMaterial')?.value==='81'&&$('#planningMethod')?.value==='Role Play'&&+$('#planningGroups')?.value===2&&+$('#planningSize')?.value===3&&+$('#planningBudget')?.value===15,label:'81 / Role Play / 2 × 3 / 15 min'}),
 flow('3 · 建立计划','点击 Generate UI。画布应出现计划摘要和 A/B/C 三个独立页面；另一个组复用安排，不重复铺满画布。','plan','#planningForm button[type=submit]',{check:()=>Boolean(tutorialFacts.built),label:'计划已建立'}),
 flow('4 · 设定组队','检查两个三人组，Discussion groups 保持 home groups。这里决定谁与谁一起。','group','#regroup',{check:()=>data.plan.groupCount===2&&data.plan.groupSize===3&&data.plan.interaction.regroup==='home',label:'两组三人，保留原组'}),
 flow('5 · 分配任务','确认作者、读者、编辑分别给 A/B/C。点字母可改负责人，同一分配用于两个组。','distribution','.assignment-chips',{check:()=>['author','reader','editor'].every((r,i)=>data.plan.tasks.some(t=>t.roleId===r&&t.assignees.includes(i))),label:'三个角色都有负责人'}),
 flow('6 · 调整作者的问题','检查 A 的 Question 和 Peer action。可改一句，或确认保留：作者解释视觉论证，并向读者核对是否读懂。','task','[data-task-field="prompt"]',{ack:'问题与同伴动作已检查',label:'任务已检查'}),
 flow('7 · 设置公开规则','把同伴解释设为 After everyone in my group submits；Pace 选 Teacher-led，Discussion 选 Talk。先保留个人判断，再交流。','interaction','#visibility',{check:()=>data.plan.interaction.visibility==='after_group'&&data.plan.interaction.mode==='sync'&&data.plan.interaction.channel==='talk',label:'全组提交后公开；教师带节奏'}),
 flow('8 · 调整时间','Prepare 改为 5 分钟，Roundtable 改为 6 分钟，Revise 保持 4 分钟。检查总计 15 / 15 min。','timing','[data-minutes]',{check:()=>data.plan.budget===15&&['individual','discussion','revision'].every((k,i)=>data.plan.phases.find(p=>p.kind===k)?.minutes===[5,6,4][i]),label:'5 + 6 + 4 = 15 分钟'}),
 flow('9 · 检查阶段交接','核对 Instruction 和 Output：准备留下个人解释，讨论检查同伴观点，修订说明改变。需要时直接改。','stages','[data-stage][data-key="deliverable"]',{ack:'交接关系已检查',label:'三阶段交接已检查'}),
 flow('10 · 打开 A / B / C','逐个 Preview 三个人，读各自的问题。确认作者、读者、编辑不是同一道题换名字。下方按钮方便切换。','versions','.version-list',{people:true,check:()=>[0,1,2].every(s=>(tutorialFacts.openedSlots||[]).includes(s)),label:'三个个人页面都已打开'}),
 flow('11 · 试交 A 的准备','你现在是作者 A。用 Next / Last 看完整个故事，写一两句，再 Submit interpretation。只保存为预览。','learner-read',{frame:'#responseForm'},{sample:'The shrinking area shows how the population narrows to a small electorate. The final comparison makes the size easier to judge.',fill:'answer',check:()=>Boolean(tutorialFacts.prepared),label:'A 的准备已提交'}),
 flow('12 · 准备讨论样例','点击“加载讨论样例”补齐同伴贡献。样例会替换预览数据，不影响真实学生，下一步进入 Roundtable。','canvas','#sampleButton',{action:'sample',actionLabel:'加载讨论样例',check:()=>Boolean(tutorialFacts.examples),label:'讨论样例已加载'}),
 flow('13 · 以 A 的身份交流','看 B 的阅读困难和 C 的质疑，按 Peer action 核对。在 Your exchange note 记下检查或改变了什么，点 Save my note。','learner-discuss',{frame:'#responseForm'},{sample:'I will name each population group before defending the final comparison. Area shows group size, not equal political influence.',fill:'answer',check:()=>Boolean(tutorialFacts.exchanged),label:'A 的交流笔记已保存'}),
 flow('14 · 留下共同产物','展开 Open the shared editorial decision，写一条保留的信息、一条要澄清的表达，再 Save group response。','learner-shared',{frame:'#groupText'},{sample:'Keep: the electorate narrows through successive filters. Clarify: label each population group and explain the Florida comparison.',fill:'group',check:()=>Boolean(tutorialFacts.shared),label:'共同决定已保存'}),
 flow('15 · 完成个人修订','Revise 应带入 A 的准备、交流笔记与组决定。写最终解释，说明改了什么，再 Save explanation。','learner-revise',{frame:'#responseForm'},{sample:'The story narrows the population through labeled filters. I now distinguish electorate size from political influence and would clarify each transition.',fill:'answer',check:()=>Boolean(tutorialFacts.revised),label:'A 的个人修订已保存'}),
 flow('16 · 部署活动','点击 Deploy activity 开放学生入口，再检查班级二维码。学生领取不同位置；HTML 是离线快照。部署不启动计时器。','share','#confirmDeploy,#copyShare',{check:()=>Boolean(data.deployment?.active),label:'活动已部署，学生入口已开放'}),
 flow('17 · 开始课堂与干预','Start class 启动；Live stage 推进；Pause / Resume 控制计时。Interaction 可向某组发提示。可只完成备课，也可亲自试启课堂。','timing','#startPause',{live:true,check:()=>Boolean(tutorialFacts.started),label:'课堂已由你启动'}),
 flow('18 · 推进与结束','先将 Live stage 切到 Roundtable，再切 Revise，最后 End live session。真实课上等学生完成后再推进，回答始终保留。','timing','#liveStage',{check:()=>Boolean(tutorialFacts.liveDiscussion&&tutorialFacts.liveRevision&&tutorialFacts.ended),label:'已推进讨论、修订，并结束课堂'})
];
