# BeforeStep — rehearse the side you cannot see

**What.** Aholo Lux3D turns a robot's actual flat photograph into a complete 3D rock, including the unseen side. A wheel-leg robot checks and rehearses these geometry hypotheses before acting in an independent simulation.

**Why.** Solar darkness removes reliable depth; rocks also hide space from view. Changing viewpoint changes visibility, not sunlight. A plausible backside can still be wrong.

**How.** Generate multiple hypotheses → register and check them → construct occupancy → rehearse every admitted world with the same controller → execute independently → review and intervene on rejected candidates. Original R1/R2: 180 unique tasks, 166 successful GLBs, 64 admissions and 102 rejections.

**Results.** Original imagination, 8 preregistered decisive scenes: 3 arrived / 3 stopped / 2 collisions (F1_020, unseen C; F3_004, underestimated backside). In the 5 designated holdouts, original imagination: 1 arrived / 2 stopped / 2 collisions; final v3 **post-result revision**: 0 arrived / 5 stopped / 0 collisions. The revision removed both collisions and the holdout arrival benefit. Only holdouts support out-of-sample conclusions. Across all 12 known-scene retests, final v3: 3 arrived / 9 stopped / 0 collisions. Early oldv2 collided in F1_003 and remains separate. Imagination is useful, with a measured failure boundary.

**Evidence.** [Report and failures](../site/report.html), [machine-readable results](../evidence/reviews/beforestep_r3/summary.json), [real asset iterations](../site/award-assets.html), [complete video source index](../evidence/video/index.json). This is simulation evidence; universal navigation and hardware success are unproven.

**Links.** [Public source](https://github.com/codezzzsleep/next-zenith-beforestep) · [Playable Demo](https://codezzzsleep.github.io/next-zenith-beforestep/levels.html) · [Historical video](https://codezzzsleep.github.io/next-zenith-beforestep/media/demo.mp4). The project lead prepares the new video from the supplied real run data.
