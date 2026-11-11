"""One activity model drives the host workspace and every learner view."""
from copy import deepcopy
from pathlib import Path
import json

ROLEPLAY=json.loads((Path(__file__).parent/'roleplay.json').read_text())

MATERIALS = [
    dict(id='83', slide='83', title='Changing middle-class jobs', author='Gregor Aisch & Robert Gebeloff · The New York Times', image='/assets/jobs.png', source='https://driven-by-data.net/2015/02/23/middle-class/', context='Each line connects 1980 and 2012. Height shows jobs per 1,000 middle-class jobs. Color shows the gender composition of an occupation.'),
    dict(id='81', slide='81', title='Who gets a vote?', author='Keith Collins & Greg Giroux · Bloomberg', image='/assets/voters-1.jpg', images=['/assets/voters-%s.jpg'%i for i in range(1,8)], frameLabels=['Population','Voting-age population','Voters','States with Senate races','Competitive states','Combined voters','Comparison with Florida'], source='https://www.bloomberg.com/politics/graphics/2014-who-votes-in-midterms/', context='A seven-part story narrows the US population to voters in competitive Senate states. The voting data refer to 2010; the story concerns the 2014 election.'),
    dict(id='82', slide='82', title='Reading climate time', author='Randall Munroe · xkcd · CC BY-NC 2.5', image='/assets/climate.png', source='https://xkcd.com/1732/', context='This long timeline places recent warming beside 22,000 years of temperature change. Read its historical annotations and future scenarios.'),
    dict(id='84', slide='84', title='How outbreaks spread', author='The Guardian · source simulation capture', image='/assets/outbreaks.png', source='https://www.theguardian.com/society/ng-interactive/2015/feb/05/-sp-watch-how-measles-outbreak-spreads-when-kids-get-vaccinated', context='Each panel shows a community at a different vaccination rate. The image is one recorded outcome of the source simulation, not a live model.'),
    dict(id='85', slide='85', title='Evolution on a plate', author='Baym Lab · Harvard Medical School · CC BY', image='/assets/bacteria.png', video='/assets/bacteria.mp4', source='https://vimeo.com/180908160', context='Bacteria spread across a plate with increasing antibiotic concentrations. The time-lapse records growth, pauses, and the advance of resistant populations.'),
]

QUESTIONS = {
 '83': [('Color', 'What does line color encode? Does red mean that an occupation grew?'), ('Position', 'What does a downward line mean? Use the unit on the vertical axis.'), ('Story', 'Why are job groups ordered from left to right? What change does this order emphasize?')],
 '81': [('Area', 'What does area represent? How does this differ from a geographic map?'), ('Sequence', 'Compare the first and last frames. Which steps change who is included?'), ('Story', 'How do the outlines and final comparison support the political argument?')],
 '82': [('Scale', 'Compare equal time intervals near the start and end. What does the spacing reveal?'), ('Attention', 'How do the annotations and long scroll affect your reading of recent warming?'), ('Story', 'Where does the timeline shift from past observations to future scenarios? Why does that distinction matter?')],
 '84': [('Encoding', 'Use the legend. What do the dot colors show, and what does one panel represent?'), ('Comparison', 'Compare two vaccination rates. What pattern is visible in this recorded outcome?'), ('Limits', 'What can one recorded simulation show? What would need repeated runs?')],
 '85': [('Sequence', 'Find a moment when growth stops and then resumes. What changes on the plate?'), ('Attention', 'How do the time-lapse and concentration labels direct your attention?'), ('Evidence', 'Which visible change supports an account of resistance? What cannot be concluded from the video alone?')],
}

def tasks_for(material_id='83', structure='Analytic Teams', size=3):
    if structure == 'Role Play':
        order=ROLEPLAY['roleOrder'][str(size)]
        prompts=ROLEPLAY['prompts'].get(material_id, ['Explain the intended message.','Explain one difficult reading.','Test a claim against the material.','Check the facts or units.','Prepare a question that connects two interpretations.'])
        return [dict(id='task-'+str(slot+1),title=ROLEPLAY['roles'][i]['title'],prompt=prompts[i],responseType='text',options=[],assignees=[slot],materialId=material_id,roleId=ROLEPLAY['roles'][i]['id'],handoff=ROLEPLAY['roles'][i]['exchange']) for slot,i in enumerate(order)]
    qs=QUESTIONS.get(material_id, QUESTIONS['83'])
    if structure == 'Think–Pair–Share':
        qs=[('Your reading', 'Explain one visual choice that shapes the message. Refer to a specific part of the visual.')]
    elif structure == 'Peer Editing':
        qs=[('Draft a critique', 'Write a short critique: what does this design communicate well, and which reading could it make difficult?')]
    return [dict(id='task-'+str(i+1), title=t, prompt=q, responseType='text', options=['Yes','No','Not sure'], assignees=list(range(size)) if len(qs)==1 else [slot for slot in range(size) if slot % len(qs)==i] or [i%size], materialId=material_id) for i,(t,q) in enumerate(qs)]

def default_plan():
    return dict(planned=False,title='Untitled activity', intent='', materialId='83', structure='Analytic Teams', budget=15, groupSize=3, groupCount=1,
        tasks=tasks_for(), phases=[
         dict(id='read',title='Read',kind='individual',minutes=4,instruction='Read the visual. Answer your assigned question.',deliverable='Your interpretation'),
         dict(id='discuss',title='Discuss',kind='discussion',minutes=7,instruction='Compare your readings. Resolve one difference using the visual. Keep any question you cannot resolve.',deliverable='One group explanation'),
         dict(id='revise',title='Revise',kind='revision',minutes=4,instruction='What would you change in your first reading after the discussion? Explain what led you to change it, or why you kept it.',deliverable='Your revised explanation')],
        interaction=dict(mode='sync',channel='talk',visibility='after_own',regroup='home',feedback='teacher',reference='Color shows gender composition. Vertical position shows jobs per 1,000 middle-class jobs. A red line can slope downward: these cues encode different variables.'),
        positions={}, live=dict(started=False,paused=False,phaseId='read',startedAt=None,remaining=None,reveal=False))

def validate_plan(raw):
    p=deepcopy(raw)
    if not isinstance(p,dict): raise ValueError('Invalid activity.')
    p['title']=str(p.get('title','Activity'))[:160]
    p['intent']=str(p.get('intent',''))[:3000]
    p['groupSize']=int(p.get('groupSize',3)); p['groupCount']=int(p.get('groupCount',1)); p['budget']=int(p.get('budget',15))
    if not 2<=p['groupSize']<=5 or not 1<=p['groupCount']<=6 or not 1<=p['budget']<=240: raise ValueError('Use 2–5 learners per group, 1–6 groups, and a 1–240 minute budget.')
    if not 1<=len(p.get('phases',[]))<=8 or not 1<=len(p.get('tasks',[]))<=12: raise ValueError('Keep 1–8 stages and 1–12 tasks.')
    ids=[]
    for x in p['phases']:
        x['id']=str(x['id'])[:60]; ids.append(x['id']); x['title']=str(x['title'])[:80]
        x['minutes']=int(x['minutes'])
        if not 1<=x['minutes']<=120 or x['kind'] not in ['individual','discussion','revision','check']: raise ValueError('Invalid stage.')
        for k in ['instruction','deliverable']: x[k]=str(x.get(k,''))[:2000]
    if len(ids)!=len(set(ids)): raise ValueError('Stage identifiers must be unique.')
    tids=[]
    for t in p['tasks']:
        t['id']=str(t['id'])[:60]; tids.append(t['id']); t['title']=str(t['title'])[:100]; t['prompt']=str(t['prompt'])[:3000]
        if t['responseType'] not in ['text','choice']: raise ValueError('Invalid response type.')
        t['assignees']=sorted(set(int(a) for a in t.get('assignees',[]) if 0<=int(a)<p['groupSize']))
        t['options']=[str(o)[:120] for o in t.get('options',[])][:6]
        if 'roleId' in t:t['roleId']=str(t['roleId'])[:60]
        if 'handoff' in t:t['handoff']=str(t['handoff'])[:1500]
    if len(tids)!=len(set(tids)): raise ValueError('Task identifiers must be unique.')
    allowed={'mode':['sync','async'],'channel':['talk','write'],'visibility':['after_own','after_group','always'],'regroup':['home','cross'],'feedback':['teacher','after_group','request']}
    for k,values in allowed.items():
        if p['interaction'].get(k) not in values: raise ValueError('Invalid interaction setting.')
    p['interaction']['reference']=str(p['interaction'].get('reference',''))[:5000]
    from progress_rules import validate_rules
    validate_rules(p)
    return p
