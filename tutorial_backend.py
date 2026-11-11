"""A separate practice classroom for the hands-on instructor tutorial."""
from pathlib import Path
from copy import deepcopy
import json,os,secrets,signal,socket,subprocess,sys,time,urllib.request

def stop_practice(info):
 """Stop a practice classroom this launcher started earlier, so restarts do not use up the local ports. Its saved file stays."""
 pid=info.get('pid')
 if not pid or pid==os.getpid():return False
 try:
  request=urllib.request.Request(f"http://127.0.0.1:{info['port']}/api/host",headers={'X-Admin-Token':info['admin']})
  with urllib.request.urlopen(request,timeout=.6) as r:
   if not json.load(r).get('tutorialSession'):return False
  os.kill(pid,signal.SIGTERM);return True
 except (OSError,ValueError,KeyError):return False

def launch_tutorial(root,return_url,reset=False,spawn=True):
 root=Path(root);runtime=root/'runtime';runtime.mkdir(exist_ok=True)
 launch=runtime/'tutorial-launch.json';old=json.loads(launch.read_text()) if launch.exists() else None
 if old and not reset:
  try:
   request=urllib.request.Request(old['url'].split('/?')[0]+'/api/host',headers={'X-Admin-Token':old['admin']})
   with urllib.request.urlopen(request,timeout=.6) as r:found=json.load(r)
   from build_info import BUILD
   if found.get('tutorialSession') and found.get('build')==BUILD:return {'url':old['url'],'reused':True}
  except (OSError,ValueError,KeyError):pass
 # New sessions get new storage and identities. Previous practice runs stay recoverable.
 name='tutorial-'+secrets.token_hex(4);path=runtime/(name+'.json')
 from model import default_plan
 state=dict(admin=secrets.token_urlsafe(24),code=secrets.token_hex(3),plan=default_plan(),people=[],responses={},previewResponses={},posts={},previewPosts={},groupAnswers={},previewGroupAnswers={},feedback={},requests=[],rev=1,planRev=1,customMaterials=[],deployment=dict(active=False,deployedAt=None),tutorialSession=True,tutorialReturn=return_url)
 state['plan']['groupSize']=4;state['plan']['groupCount']=3;state['plan']['budget']=18
 # server.reconcile creates places without touching any existing classroom.
 for group in range(3):
  for slot in range(4):state['people'].append(dict(id=secrets.token_hex(5),token=secrets.token_urlsafe(18),name='',group=group,slot=slot,active=True,claimed=False))
 path.write_text(json.dumps(state,ensure_ascii=False),encoding='utf8')
 if os.environ.get('COLLABCANVAS_PUBLIC','').lower() in ('1','true','yes'):
  # One public process cannot open extra ports. Prepare a new state file; the running server reloads it.
  url=(os.environ.get('PUBLIC_BASE') or os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('COLLABCANVAS_BASE') or '').rstrip('/')
  if not url:url='http://127.0.0.1:'+str(int(os.environ.get('PORT',8931)))
  url=url+'/?admin='+state['admin']+'&view=flow&tutorial=1'
  info=dict(url=url,admin=state['admin'],state=str(path),port=int(os.environ.get('PORT',8931)),inplace=True)
  launch.write_text(json.dumps(info));return {'url':url,'reused':False,'state':str(path),'retire':False,'inplace':True}
 for port in range(8944,8990):
  sock=socket.socket()
  try:sock.bind(('127.0.0.1',port))
  except OSError:sock.close();continue
  sock.close();break
 else:raise ValueError('No local tutorial port is available.')
 url=f'http://127.0.0.1:{port}/?admin='+state['admin']+'&view=flow&tutorial=1'
 info=dict(url=url,admin=state['admin'],state=str(path),port=port);launch.write_text(json.dumps(info));retire=False
 if spawn:
  log=(runtime/(name+'.log')).open('ab')
  child=subprocess.Popen([sys.executable,str(root/'server.py'),'--port',str(port),'--state',str(path)],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close()
  info['pid']=child.pid;launch.write_text(json.dumps(info))
  for attempt in range(60):
   try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=.3) as response:
     if json.load(response).get('ok'):break
   except (OSError,ValueError):time.sleep(.05)
  else:raise ValueError('The practice classroom could not start. Check the tutorial log in runtime.')
  # The practice classroom being replaced is stopped. When it is this process, the server retires itself after it answers.
  if old and old.get('pid')==os.getpid():retire=True
  elif old:stop_practice(old)
 return {'url':url,'reused':False,'state':str(path),'retire':retire}

def practice_action(state,body):
 if not state.get('tutorialSession'):raise ValueError('Example classmates can only be added in the separate tutorial classroom.')
 from studio_backend import seed_rehearsal
 from progress_backend import save_answer,records
 group=0;people=sorted([p for p in state['people'] if p['active'] and p['group']==group],key=lambda p:p['slot'])
 owner=next((p for p in people if p.get('claimed') and p.get('slot')==0),None)
 if not owner:raise ValueError('Claim the Story Author task in Group 1 first.')
 if state['plan']['materialId']!='81' or state['plan']['structure']!='Role Play':raise ValueError('This tutorial uses the voting-story Role Play activity.')
 kind=body.get('kind')
 if kind=='collaboration-evidence':
  if state.get('tutorialCollaborationEvidence'):return {'ok':True}
  if any(state.get(key) for key in ['artifacts','responses']) or records(state)['answers']:raise ValueError('Use a fresh demo for these examples.')
  clone=deepcopy(state);seed_rehearsal(clone)
  phase=next(p['id'] for p in state['plan']['phases'] if p['kind']=='individual')
  names=[['Maya','Eli','Noor','Leo'],['Iris','Sam','Alex','Jules'],['Ren','Taylor','Ari','Robin']]
  for p in [p for p in state['people'] if p['active']]:
   g,slot=p['group'],p['slot'];p.update(name=names[g][slot]+' (example)',claimed=True)
   state.setdefault('studioGroups',{}).setdefault(str(g),{})['opening']={'text':'The frames narrow the population counted.','version':1}
   a=deepcopy(clone['previewArtifacts'][p['id']]);a['submitted']={phase:not(g==0 and slot==1)}
   if g!=1:a.pop('question',None);a.pop('questionSent',None)
   if g==0 and slot==1:a={'version':1,'submitted':{phase:False}}
   if g==1 and slot==1:a.update(question='Does the Florida comparison show equal political power, or only equal numbers of people?',questionSent=True)
   state.setdefault('artifacts',{})[p['id']]=a
   state.setdefault('responses',{})[p['id']]={phase+':submitted':not(g==0 and slot==1)}
   answer='filter' if g==2 or slot else 'land'
   save_answer(state,p,dict(kind='initial',answer=answer,reason='Example: '+('The legend counts people and the frame labels narrow the group.' if answer=='filter' else 'I read the state shapes as geographic land areas.'),phaseId=phase))
  reader=next(p for p in state['people'] if p['group']==0 and p['slot']==1)
  state.setdefault('requests',[]).append(dict(person=reader['id'],group=0,requestKind='difficulty',text='I am not sure where to start. Could I work through this in smaller steps?',preview=False,time=time.time(),resolved=False))
  state['plan']['live'].update(started=True,phaseId=phase,paused=True,remaining=120,startedAt=time.time())
  state['tutorialCollaborationEvidence']=True
 elif kind=='collaboration-followup':
  if not state.get('tutorialCollaborationEvidence'):raise ValueError('Load the collaboration example first.')
  from adaptive_backend import save_response
  g=int(body.get('group',0));pattern=['scaffold','written-exchange','reason-check'][g]
  change=next((c for c in state.get('adaptive',{}).get('teams',{}).get(str(g),{}).get('changes',[]) if c['pattern']==pattern),None)
  if not change:raise ValueError('Apply the matching interface change first.')
  if change.get('responses'):return {'ok':True}
  ps=sorted([p for p in state['people'] if p['active'] and p['group']==g],key=lambda p:p['slot'])
  if g==0:
   p=ps[1];save_response(state,p,dict(id=change['id'],version=0,values={'unit':'One square counts one million people.','population':'The first frame includes residents; later frames retain smaller voter groups.','interpretation':'Each label changes who is counted.'},shared=True))
   phase=next(p['id'] for p in state['plan']['phases'] if p['kind']=='individual')
   state['responses'][p['id']][phase+':submitted']=True;state['artifacts'][p['id']].update(reflection='The unit counts people. Each filter keeps a smaller population group.',submitted={phase:True},version=2)
  elif g==1:
   save_response(state,ps[2],dict(id=change['id'],version=0,values={'idea':'It compares population size, not equal political power. The map does not measure influence.','evidence':'The legend is one square per million people; the final label compares the remaining voters with Florida.'},shared=True))
  else:
   save_response(state,ps[0],dict(id=change['id'],version=0,values={'idea':'The state could shrink even with the same resident count, because later frames keep only a subset.','evidence':'The titles change from residents to eligible or remaining voters.'},shared=True))
   save_response(state,ps[1],dict(id=change['id'],version=0,values={'idea':'I agree with the counterfactual explanation: the counted subset can change without a population decline.','evidence':'The unit stays people; the included group changes.'},shared=True,replyTo=ps[0]['id'],reply='Your explanation separates a smaller counted subset from a decrease in total residents.'))
 elif kind=='rule-library-evidence':
  # One member wrote the whole shared critique and nobody else has read it: the case the second sign-off rule watches.
  if not state.get('tutorialCollaborationEvidence'):raise ValueError('Load the collaboration example first.')
  if state.get('tutorialRuleLibraryEvidence'):return {'ok':True}
  from collab_workflow import roles_ready
  if not roles_ready(state,0):raise ValueError('Finish the role work example for Team 1 first.')
  saved=time.time()-200;writer=people[0]['id']
  state.setdefault('studioGroups',{}).setdefault('0',{})['critique']={'message':'The seven frames shrink each state from its land area down to its voters.','misreading':'A reader may miss that the last frame is about the 2014 Senate election.','change':'Add the election year to every frame title.','version':1,'updated':saved,'person':writer}
  state.setdefault('signals',{}).setdefault('authors',{}).setdefault('0',{})['critique']=[dict(person=writer,time=saved,fields=['message','misreading','change'],version=1)]
  state['signals'].setdefault('shared',{})['0']=saved
  state['tutorialRuleLibraryEvidence']=True
 elif kind=='framework-evidence':
  if state.get('tutorialFrameworkEvidence'):return {'ok':True}
  if any(state.get(key) for key in ['artifacts','responses']) or records(state)['answers']:
   raise ValueError('Use a fresh framework demo to load example evidence.')
  clone=deepcopy(state);seed_rehearsal(clone)
  phase=next(p['id'] for p in state['plan']['phases'] if p['kind']=='individual')
  state.setdefault('studioGroups',{})['0']={'opening':{'text':'Each frame counts a narrower population group.','version':1}}
  for p in people:
   p.update(name=['Maya (example)','Eli (example)','Noor (example)','Leo (example)'][p['slot']],claimed=True)
   state.setdefault('artifacts',{})[p['id']]=deepcopy(clone['previewArtifacts'][p['id']])
   state['artifacts'][p['id']]['submitted']={phase:True}
   state['responses'].setdefault(p['id'],{})[phase+':submitted']=True
   save_answer(state,p,dict(kind='initial',answer='time' if p['slot']<2 else 'filter',reason='Example: '+('The smaller maps looked like population falling over time.' if p['slot']<2 else 'The labels identify narrower groups of people.'),phaseId=phase))
  state['tutorialFrameworkEvidence']=True
 elif kind=='framework-followups':
  if not state.get('tutorialFrameworkEvidence'):raise ValueError('Load the framework example first.')
  support=records(state)['teams'].get('0',{}).get('support')
  if not support:raise ValueError('Apply the team support first.')
  for p in people:
   if p['id'] in support['targets'] and not records(state)['answers'].get(p['id'],{}).get('followup'):
    save_answer(state,p,dict(kind='followup',answer='yes',reason='Example: the later frame retains a narrower population group, not a later year.',phaseId=state['plan']['live']['phaseId']))
 elif kind=='peers':
  if not state.get('studioGroups',{}).get('0',{}).get('opening',{}).get('text'):raise ValueError('Save the group’s starting reading first.')
  clone=deepcopy(state);seed_rehearsal(clone)
  phase=next(p['id'] for p in state['plan']['phases'] if p['kind']=='individual')
  for p in people:
   if p['id']==owner['id']:continue
   p.update(name=['Maya','Eli (example)','Noor (example)','Leo (example)','Host (example)'][p['slot']],claimed=True)
   state.setdefault('artifacts',{})[p['id']]=deepcopy(clone['previewArtifacts'][p['id']]);state['artifacts'][p['id']]['submitted']={phase:True}
   task=next(t for t in state['plan']['tasks'] if p['slot'] in t['assignees'])
   state['responses'].setdefault(p['id'],{}).update({phase+':submitted':True,phase+':'+task['id']:'Tutorial example: '+task['title']+' finding.'})
   if not records(state)['answers'].get(p['id'],{}).get('initial'):save_answer(state,p,dict(kind='initial',answer='time' if p['slot']==1 else 'filter',reason='Tutorial example: '+('I read the shrinking maps as a change over time.' if p['slot']==1 else 'The labels retain narrower population groups.'),phaseId=phase))
  state['tutorialPeerExamples']=True
 elif kind=='adaptive-teams':
  if state.get('tutorialAdaptiveExamples'):return {'ok':True}
  clone=deepcopy(state);seed_rehearsal(clone)
  phase=next(p['id'] for p in state['plan']['phases'] if p['kind']=='individual')
  for p in [p for p in state['people'] if p['active'] and p['group'] in [1,2]]:
   p.update(name=(['Iris','Sam','Alex','Jules'] if p['group']==1 else ['Ren','Taylor','Ari','Robin'])[p['slot']]+' (example)',claimed=True)
   state.setdefault('studioGroups',{}).setdefault(str(p['group']),{})['opening']={'text':'The sequence filters who is counted. It does not show a change in years.','version':1}
   state.setdefault('artifacts',{})[p['id']]=deepcopy(clone['previewArtifacts'][p['id']])
   if p['group']==1:
    state['artifacts'][p['id']]['submitted']={phase:True}
    state['responses'].setdefault(p['id'],{})[phase+':submitted']=True
    if not records(state)['answers'].get(p['id'],{}).get('initial'):
     reasons=['The legend counts people, not land.','The labels keep smaller population groups.','The frame titles describe filters rather than later years.','The story narrows the electorate, not the number of residents.']
     save_answer(state,p,dict(kind='initial',answer='filter',reason='Tutorial example: '+reasons[p['slot']],phaseId=phase))
  state['tutorialAdaptiveExamples']=True
 elif kind=='followups':
  support=records(state)['teams'].get('0',{}).get('support')
  if not support:raise ValueError('Add the team comparison task first.')
  for p in people:
   if p['id']==owner['id'] or p['id'] not in support['targets']:continue
   if not records(state)['answers'].get(p['id'],{}).get('followup'):save_answer(state,p,dict(kind='followup',answer='yes',reason='Tutorial example: a later frame counts a narrower group, even if total population stays constant.',phaseId=state['plan']['live']['phaseId']))
  state['tutorialFollowupExamples']=True
 else:raise ValueError('Choose an available tutorial example.')
 return {'ok':True}
