"""Compare the instructor's diagram against the actual student routing service."""
import json, shutil, subprocess, tempfile, unittest
from pathlib import Path
import server
from model import tasks_for

ROOT = Path(__file__).parent

@unittest.skipUnless(shutil.which('node'), 'Node is needed for diagram integration checks')
class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        server.initialize(Path(self.temp.name) / 'isolated-class.json')

    def tearDown(self):
        self.temp.cleanup()

    def diagram(self, cases):
        script = """
        const fs=require('fs'),guide=require('./orchestration.js');
        const cases=JSON.parse(fs.readFileSync(0,'utf8'));
        process.stdout.write(JSON.stringify(cases.map(c=>guide.derive(c.plan,c.people,c.roles,0).allActors.map(a=>({id:a.person.id,to:a.target.id,role:a.role,sources:a.sourceIds,tasks:a.tasks.map(t=>t.id)})))));
        """
        run = subprocess.run(['node', '-e', script], cwd=ROOT, input=json.dumps(cases), text=True, capture_output=True, check=True)
        return json.loads(run.stdout)

    def snapshot(self):
        return json.loads(json.dumps(dict(plan=server.STATE['plan'], people=server.STATE['people'], roles=server.ROLEPLAY)))

    def test_diagram_destinations_match_student_service_for_methods_sizes_and_regrouping(self):
        cases, expected = [], []
        for method in ['Role Play','Analytic Teams','Think–Pair–Share','Peer Editing']:
            for size in range(2, 6):
                for regroup in ['home', 'cross']:
                    p = server.STATE['plan']
                    p.update(structure=method, groupSize=size, groupCount=2, tasks=tasks_for('81', method, size))
                    p['interaction']['regroup'] = regroup
                    server.reconcile()
                    people = sorted((x for x in server.STATE['people'] if x['active']), key=lambda x:(x['group'], x['slot']))
                    cases.append(self.snapshot())
                    expected.append({x['id']:server.learner_view(x)['reviewTo'] for x in people})
        actual = self.diagram(cases)
        for case, result, wanted in zip(cases, actual, expected):
            with self.subTest(method=case['plan']['structure'],size=case['plan']['groupSize'],regroup=case['plan']['interaction']['regroup']):
                self.assertEqual({a['id']:a['to'] for a in result}, wanted)

    def test_reassigning_roles_and_leaving_a_role_unassigned_keeps_routes_truthful(self):
        cases, expected = [], []
        for assignments in [[[1],[0],[2]], [[0,1],[1],[2]], [[],[1],[2]]]:
            p = server.STATE['plan']
            p.update(structure='Role Play', tasks=tasks_for('81', 'Role Play', 3))
            for task, assignees in zip(p['tasks'], assignments): task['assignees'] = assignees
            cases.append(self.snapshot())
            expected.append({x['id']:server.learner_view(x)['reviewTo'] for x in server.STATE['people'] if x['active']})
        for result, wanted in zip(self.diagram(cases), expected):
            self.assertEqual({a['id']:a['to'] for a in result}, wanted)

    def test_source_assignments_and_common_tasks_remain_distinct_from_personas(self):
        p = server.STATE['plan']
        p.update(structure='Peer Editing', tasks=tasks_for('83','Peer Editing',3))
        common = self.snapshot()
        p.update(structure='Analytic Teams', tasks=tasks_for('83','Analytic Teams',3))
        p['tasks'][1]['materialId'] = '81'
        common_actors, split_actors = self.diagram([common,self.snapshot()])
        self.assertEqual(len({a['id'] for a in common_actors}), 3)
        self.assertEqual({a['role'] for a in common_actors}, {'Author & reviewer'})
        self.assertEqual({tuple(a['tasks']) for a in common_actors}, {('task-1',)})
        self.assertEqual([a['sources'] for a in split_actors], [['83'],['81'],['83']])

    def test_planning_keeps_method_specific_actions_and_time_budget(self):
        script = """
        const fs=require('fs'),vm=require('vm'),ctx={};vm.createContext(ctx);
        vm.runInContext(fs.readFileSync('orchestration-ui.js','utf8'),ctx);
        const names=['Role Play','Analytic Teams','Think–Pair–Share','Peer Editing'];
        process.stdout.write(JSON.stringify(names.map(structure=>({structure,phases:ctx.plannedPhases({structure,budget:15})}))));
        """
        r = subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True,check=True)
        plans = {x['structure']:x['phases'] for x in json.loads(r.stdout)}
        for phases in plans.values():
            self.assertEqual(sum(p['minutes'] for p in phases),15)
            self.assertEqual([p['kind'] for p in phases],['individual','discussion','revision'])
        self.assertIn('debrief',plans['Role Play'][2]['instruction'])
        self.assertIn('peer’s finding',plans['Analytic Teams'][1]['instruction'])
        self.assertIn('independently',plans['Think–Pair–Share'][0]['instruction'])
        self.assertIn('declined',plans['Peer Editing'][2]['instruction'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
