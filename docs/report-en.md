# BeforeStep — rehearse the side you cannot see

**What.** A wheel-leg robot uses real RGB-D, Aholo Lux3D geometry candidates, frozen observation checks and complete physics rehearsals before acting in an independent simulation.

**Why.** Solar darkness removes reliable depth; rocks also hide space from view. Changing viewpoint changes visibility, not sunlight. A plausible backside can still be wrong.

**How.** Generate multiple hypotheses → register and check them → construct occupancy → rehearse every admitted world with the same controller → execute independently → review and intervene on rejected candidates. Original R1/R2: 180 unique tasks, 166 successful GLBs, 64 admissions and 102 rejections.

**Results.** The original corridor Lux run arrived, but the preregistered suite contains two real imagination collisions, F1_020 and F3_004. The strict method is a **post-result revision**: known-scene retests, 12 completed / 3 arrived / 9 stopped / 0 collisions; designated holdouts, 5 completed / 0 arrived / 5 stopped / 0 collisions. Only the holdouts support out-of-sample conclusions. Early oldv2 collided in F1_003; the final v3 statistics do not cover every revision attempt. The revision did not replace missing shadow depth in all scenarios that the depth-enabled control could traverse.

**Evidence.** [Report and failures](../site/report.html), [machine-readable results](../evidence/reviews/beforestep_r3/summary.json), [real asset iterations](../site/award-assets.html), [complete video source index](../evidence/video/index.json). This is simulation evidence; universal navigation and hardware success are unproven.

**Links.** [Public source](https://github.com/codezzzsleep/next-zenith-beforestep) · [Playable Demo](https://codezzzsleep.github.io/next-zenith-beforestep/levels.html) · [Historical video](https://codezzzsleep.github.io/next-zenith-beforestep/media/demo.mp4). The project lead prepares the new video from the supplied real run data.
