# CollabCanvas · Plan, test, deploy and adapt

A working InfoVis prototype for planning, previewing and adapting connected student interfaces. This pilot uses the seven-frame voting story on SI649 slide 81 and an editorial Role Play with Author, Reader, Evidence Checker and Editor.

## Public demo

One-click host (free web service): [Deploy to Render](https://render.com/deploy?repo=https://github.com/Antelofski/collabcanvas).

Or with Fly.io after `fly auth login`: `fly launch --copy-config --yes && fly deploy`.

Deploy from the Docker/`render.yaml` files in this repository (Render free web service works). Set `COLLABCANVAS_PUBLIC=1`. The first boot loads `runtime/public-seed.json`.

- Instructor: `https://YOUR_HOST/?admin=collabcanvas-public-demo&view=flow`
- Join code for learners: `public1`
- Override with `COLLABCANVAS_DEMO_ADMIN` / `COLLABCANVAS_DEMO_CODE` / `PUBLIC_BASE` if needed.

Progress rules are a full library (19 seeds in 9 families, plus teacher-written rules). Automatic detectors cover contribution, reading checks, support requests, answer patterns, co-authoring, random explainers, sign-off, quiet teams, stalled learners, class blockers, workload balance, shared misconceptions, closing pulse, and paste notices. Teachers review peer-use, participation and similar signals themselves. The Chinese **下一步** walkthrough has 64 framework stops (0–63); `?tour=activity` has 58 stops (0–57).

## Open

- **Open Activity Canvas.command** opens the instructor's saved activity.
- **Open Tutorial.command** starts a new, separate classroom from an empty canvas.
- **Watch_Walkthrough.html** plays the current 2:50 framework-focused English-captioned demo.
- `python3 open_tutorial.py --resume` explicitly resumes the last practice classroom.

The product UI is English. The tutorial dock is Chinese. Its 64 stops (0–63) perform the real actions when **下一步** is clicked; no separate product clicks or typing are required. Pause to explore the product. Restart creates another practice classroom and preserves previous sessions and the formal class.

The default tutorial focuses on the system framework. It shows each Planner input separately, interface inspection and editing, progress-rule setup, functional UI testing, class entry, and one evidence-to-intervention loop. `?tour=activity` retains the longer activity walkthrough for optional exploration.

## Plan and inspect

1. Open Planner on the empty canvas. Upload the slides, select the voting story, describe the activity, and configure groups, learners and time.
2. Generate the prepared pilot. Open each learner card on the freely movable canvas to inspect its dedicated tools.
3. Select a region and use Edit or Try alternatives. Preview connected changes before applying them. The prepared group-first edit links shared discussion, role work and a shared critique.
4. Inspect Task, Group, Roles, Interaction and Time when precise configuration is useful. These describe the underlying arrangement.

## Plan progress rules

After inspecting the interfaces, open **Progress rules**, before testing and deployment. Ten suggested checks cover the following concerns:

- Role submissions at a configurable reminder time.
- Private reading checks with an answer and reason.
- Use of peer contributions, reviewed by the instructor.
- Opportunity to contribute, based on instructor observation.
- Explicit student requests for smaller steps or a written participation route.
- A unanimous answer pattern, prompting inspection of reasons rather than diagnosing a problem.
- Role clarity, workload fit, responding to disagreement and concrete peer feedback. These are optional teacher-review checks derived from the instructor feedback and collaboration concerns, not automatic diagnoses.

The activity collects role work, individual answers and help requests by default. Rule selection controls reminders and review expectations; disabling the individual-answer rule does not hide its question, stop collection or delete answers. Each prepared rule distinguishes the evidence, a possible teacher response and a subsequent check. Edit details or add a custom teacher-reviewed rule. Free text does not create an automatic detector. Preview how instrumentation changes the learner interface, then save.

## Test and deploy

**Test activity** runs scripted browser journeys through actual controls against isolated state. The four-role discussion-first journey has 25 checks: source controls, saving and reloading each role's work, private-check separation, peer visibility, group boundaries and shared-stage handoffs. Failures are reported and tests can be rerun. The report shows concise check names with expandable details. Guided playback adds a short pause on interface loads to make execution visible; it runs the same checks. This is not an LLM assessing teaching quality.

Deploy creates one class QR. Students choose a group, select an available role and enter a name to claim their connected interface. The QR points to the local server; it is not cloud hosting. Students need a reachable server on the same network.

## Adapt while students work

Open **Teams** and inspect the saved evidence. The compact detail view puts the unmet rule, the exact rule ID, its expected answer, observed correct-answer count, named incorrect choices and a visible explanation of why those choices fail the check beside a system suggestion. Preview the proposed support, check its recipients, apply it and inspect the follow-up. More options and detailed controls remain in expandable sections. The teacher can ask a question, send a message, visit a group, keep the activity, or preview a change:

- **Frame comparison:** one team receives first/last frame comparison; only learners with incorrect initial checks receive a private follow-up. Initial answers remain immutable.
- **Smaller steps:** selected learners work through the unit, population groups and interpretation. Once explicitly shared, findings reach teammates and the Editor's critique.
- **A written way to contribute:** team members share a source-based contribution and reply to a specific peer. Drafts remain private until shared.
- **Test an agreed answer:** team members explain a counterfactual and inspect peers' reasons. Private initial answers are not revealed.

Preview read-only before/after snapshots of the same role-specific interface and saved work. Use **Open before** and **Open after** to inspect each full interface, choose the learner, return to the comparison and confirm scope. Only **Apply** modifies the live team. Snapshot inspection cannot save or overwrite learner data. Check recipients and rationale, then apply to that group. Existing tools, role work and private checks remain intact. Other groups are unchanged. Inspect the changed interfaces read-only and review subsequent work. A saved contribution does not automatically close a request: the instructor records what was verified. **Keep the activity** records a no-change decision after reviewing agreement.

Inactivity alone does not establish disengagement, spoken participation or a disability. Speaking is not recorded. Social and rubric-based checks require instructor evidence. Correct choices or completed tasks do not establish learning gains.

**Adapt next activity / Improve next run** save separate evidence-linked drafts. The prepared drafts move the private check before discussion or clarify role briefs. Starting a draft requires ending the live session, archives the current run, and requires redeployment.

## Current capability boundary

Generation, semantic edits, rule suggestions and interface adaptations use prepared local logic. There is no live model API or arbitrary interface-generation agent. The video uses actual prototype actions and simulated students, with English captions and control cues; no voice-over. The research hypothesis is that teacher-controlled, evidence-linked changes across interdependent student interfaces reduce orchestration effort and errors. Superiority to a general coding agent has not been established.

## Verification and storage

`python3 -m unittest discover -q` runs 116 backend checks, including adaptation scope, private drafts, linked replies, stale-preview rejection, original-work preservation, read-only inspection and tutorial isolation. All 39 framework tutorial stops and the 25 browser checks were walked through in the local browser.

State is saved in `runtime/state.json`. New archives the current activity; Restore recovers it from an empty canvas. Keep the host URL private. The sharing ZIP excludes runtime files and credentials.

## Sources

- SI649 Communicative Visualization, slide 81; Bloomberg, Keith Collins and Greg Giroux: https://www.bloomberg.com/politics/graphics/2014-who-votes-in-midterms/
- Dillenbourg, *Over-scripting CSCL* (2002), §3: task, group, distribution, interaction and timing.
- Barkley, Major and Cross, *Collaborative Learning Techniques*, Role Play.
- Orca, Jiang and Xia, CHI 2026: https://arxiv.org/html/2505.22831v2


### Collaboration progress demo (November 1)
The current demo uses three selected checks: R1, saved role contributions by a checkpoint or an explicit help request; R2, a shared Reader question without a linked response at shared writing; R3, matching initial choices without a recorded contrast-and-reply exchange. R1 offers smaller steps to the selected learner. R2 brings the original question into a direct written response. R3 adds a counterfactual and peer check. These are recorded process checks, not diagnoses of engagement or automatic judgments of learning. Teachers preview the same work before/after, apply a scoped addition, inspect later contributions, and record a review.

Generation and adaptations are prepared local logic. The classroom walkthrough uses labelled simulated responses. UI testing runs real scripted browser journeys in isolated state. English interface and captions; Chinese Next-only tutorial.


### Task-level knowledge records
Teams → Knowledge state opens an instructor-only report of each learner’s individual task evidence. Keyed checks show demonstrated performance or a need for support on that item. Saved text remains ungraded until reviewed; group completion and help requests do not establish knowledge. Instructors can save a task judgment, evidence note and next check. Later evidence invalidates the previous judgment’s fingerprint and marks it for rechecking. Save report creates an immutable class snapshot; Download report exports a standalone HTML document with a Print / Save PDF button. Historical reports remain accessible in the report-version selector.

The tutorial and video now include a pre-click highlight for each Preview change button, and finish with task-level evidence, a teacher judgment, an unresolved individual difficulty and a saved report.


### Classroom dashboard and populated report

The Dashboard groups progress evidence, proposed interface changes, subsequent student work, and knowledge reports. Design previews show one representative set of roles; team-specific records are inspected during classroom use.

Open `Knowledge_State_Example.html` for a self-contained report with twelve simulated learners. Eli, Maya and Noor illustrate success after support, an unresolved interpretation, and conflicting MCQ/text evidence. All original evidence and task-specific teacher judgments are included.


The current classroom overview uses one frame per team and one selectable dot per learner. Select a learner for a flat evidence panel, or select a team for its progress rules. The downloadable knowledge report uses the same visual layout.
