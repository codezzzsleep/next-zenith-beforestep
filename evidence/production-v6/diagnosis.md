# 同路失败只读诊断

口径：与 ops/r3_back_error.py 相同，5cm XY 占地，沿该眼记录的车体朝向计算候选最远缘减关联真石联合最远缘。附加接触带结果单列；不把两种口径混用。未跑物理、未调用生成、未改规则。

## suite_r2_v4_F2_007

- A：collision，1 眼；来源 `outputs/crossing/route/suite_r2_v4_F2_007_gate/A/segment1/summary.json`。
  - look1：生成 12，准入 3。
    - T1：6 份 / 2 准入，证据 `outputs/crossing/route/suite_r2_v4_F2_007_gate/A/segment1/looks/look1/T1/decide/target_decision.json`。
      - A1 任务 7293064：背缘误差 +0.500244 m；接触带存在=True、带内误差=0.5；`outputs/crossing/route/suite_r2_v4_F2_007_gate/A/segment1/looks/look1/T1/decide/footprint_A1.npy`。
      - B1 任务 7293211：背缘误差 +0.350139 m；接触带存在=True、带内误差=0.25；`outputs/crossing/route/suite_r2_v4_F2_007_gate/A/segment1/looks/look1/T1/decide/footprint_B1.npy`。
    - T2：6 份 / 1 准入，证据 `outputs/crossing/route/suite_r2_v4_F2_007_gate/A/segment1/looks/look1/T2/decide/target_decision.json`。
      - A1 任务 7301931：背缘误差 -0.749825 m；接触带存在=False、带内误差=None；`outputs/crossing/route/suite_r2_v4_F2_007_gate/A/segment1/looks/look1/T2/decide/footprint_A1.npy`。
  - 第一眼上传图与原运行逐字节比较：{'T1': False, 'T2': False}；各输入 SHA 见 `diagnosis-data.json`。
- D：collision，1 眼；来源 `outputs/crossing/route/suite_r2_v4_F2_007_gate/D/segment1/summary.json`。
  - look1：生成 12，准入 3。
    - T1：6 份 / 2 准入，证据 `outputs/crossing/route/suite_r2_v4_F2_007_gate/D/segment1/looks/look1/T1/decide/target_decision.json`。
      - A1 任务 7293064：背缘误差 +0.500244 m；接触带存在=True、带内误差=0.5；`outputs/crossing/route/suite_r2_v4_F2_007_gate/D/segment1/looks/look1/T1/decide/footprint_A1.npy`。
      - B1 任务 7293211：背缘误差 +0.350139 m；接触带存在=True、带内误差=0.25；`outputs/crossing/route/suite_r2_v4_F2_007_gate/D/segment1/looks/look1/T1/decide/footprint_B1.npy`。
    - T2：6 份 / 1 准入，证据 `outputs/crossing/route/suite_r2_v4_F2_007_gate/D/segment1/looks/look1/T2/decide/target_decision.json`。
      - A1 任务 7301931：背缘误差 -0.749825 m；接触带存在=False、带内误差=None；`outputs/crossing/route/suite_r2_v4_F2_007_gate/D/segment1/looks/look1/T2/decide/footprint_A1.npy`。
  - 第一眼上传图与原运行逐字节比较：{'T1': False, 'T2': False}；各输入 SHA 见 `diagnosis-data.json`。
- original：arrived，2 眼；来源 `outputs/suite/real/suite_r2_v4_F2_007/imagination/summary.json`。
  - look1：生成 12，准入 5。
    - T1：6 份 / 5 准入，证据 `outputs/suite/real/suite_r2_v4_F2_007/imagination/looks/look1/T1/decide/target_decision.json`。
      - A1 任务 6349651：背缘误差 +0.100174 m；接触带存在=True、带内误差=0.10000000000000053；`outputs/suite/real/suite_r2_v4_F2_007/imagination/looks/look1/T1/decide/footprint_A1.npy`。
      - A2 任务 6349656：背缘误差 +0.100209 m；接触带存在=True、带内误差=0.10000000000000053；`outputs/suite/real/suite_r2_v4_F2_007/imagination/looks/look1/T1/decide/footprint_A2.npy`。
      - B1 任务 6349659：背缘误差 +0.350139 m；接触带存在=True、带内误差=0.25；`outputs/suite/real/suite_r2_v4_F2_007/imagination/looks/look1/T1/decide/footprint_B1.npy`。
      - B2 任务 6349662：背缘误差 +0.350139 m；接触带存在=True、带内误差=0.25；`outputs/suite/real/suite_r2_v4_F2_007/imagination/looks/look1/T1/decide/footprint_B2.npy`。
      - C2 任务 6349718：背缘误差 +0.100244 m；接触带存在=True、带内误差=0.0；`outputs/suite/real/suite_r2_v4_F2_007/imagination/looks/look1/T1/decide/footprint_C2.npy`。
    - T2：6 份 / 0 准入，证据 `outputs/suite/real/suite_r2_v4_F2_007/imagination/looks/look1/T2/decide/target_decision.json`。
  - look2：生成 6，准入 2。
    - T2：6 份 / 2 准入，证据 `outputs/suite/real/suite_r2_v4_F2_007/imagination/looks/look2/T2/decide/target_decision.json`。
      - B1 任务 6350945：背缘误差 -0.097479 m；接触带存在=True、带内误差=-0.1999999999999993；`outputs/suite/real/suite_r2_v4_F2_007/imagination/looks/look2/T2/decide/footprint_B1.npy`。
      - B2 任务 6350950：背缘误差 -0.097479 m；接触带存在=True、带内误差=-0.25；`outputs/suite/real/suite_r2_v4_F2_007/imagination/looks/look2/T2/decide/footprint_B2.npy`。
## stress_v8

- A：stuck，2 眼；来源 `outputs/crossing/route/stress_v8_gate/A/segment1/summary.json`。
  - look1：生成 12，准入 6。
    - T1：6 份 / 6 准入，证据 `outputs/crossing/route/stress_v8_gate/A/segment1/looks/look1/T1/decide/target_decision.json`。
      - A1 任务 7207374：背缘误差 +0.000402 m；接触带存在=True、带内误差=0.09999999999999964；`outputs/crossing/route/stress_v8_gate/A/segment1/looks/look1/T1/decide/footprint_A1.npy`。
      - A2 任务 7207760：背缘误差 +0.000373 m；接触带存在=True、带内误差=0.04999999999999982；`outputs/crossing/route/stress_v8_gate/A/segment1/looks/look1/T1/decide/footprint_A2.npy`。
      - B1 任务 7208183：背缘误差 +0.350287 m；接触带存在=True、带内误差=0.34999999999999964；`outputs/crossing/route/stress_v8_gate/A/segment1/looks/look1/T1/decide/footprint_B1.npy`。
      - B2 任务 7208576：背缘误差 +0.350287 m；接触带存在=True、带内误差=0.34999999999999964；`outputs/crossing/route/stress_v8_gate/A/segment1/looks/look1/T1/decide/footprint_B2.npy`。
      - C1 任务 7208971：背缘误差 +0.050344 m；接触带存在=True、带内误差=0.09999999999999964；`outputs/crossing/route/stress_v8_gate/A/segment1/looks/look1/T1/decide/footprint_C1.npy`。
      - C2 任务 7209396：背缘误差 +0.050344 m；接触带存在=True、带内误差=0.09999999999999964；`outputs/crossing/route/stress_v8_gate/A/segment1/looks/look1/T1/decide/footprint_C2.npy`。
    - T2：6 份 / 0 准入，证据 `outputs/crossing/route/stress_v8_gate/A/segment1/looks/look1/T2/decide/target_decision.json`。
  - look2：生成 12，准入 0。
    - T2：12 份 / 0 准入，证据 `outputs/crossing/route/stress_v8_gate/A/segment1/looks/look2/T2/decide/target_decision.json`。
  - 第一眼上传图与原运行逐字节比较：{'T1': False, 'T2': False}；各输入 SHA 见 `diagnosis-data.json`。
- D：stuck，2 眼；来源 `outputs/crossing/route/stress_v8_gate/D/segment1/summary.json`。
  - look1：生成 12，准入 6。
    - T1：6 份 / 6 准入，证据 `outputs/crossing/route/stress_v8_gate/D/segment1/looks/look1/T1/decide/target_decision.json`。
      - A1 任务 7207374：背缘误差 +0.000402 m；接触带存在=True、带内误差=0.09999999999999964；`outputs/crossing/route/stress_v8_gate/D/segment1/looks/look1/T1/decide/footprint_A1.npy`。
      - A2 任务 7207760：背缘误差 +0.000373 m；接触带存在=True、带内误差=0.04999999999999982；`outputs/crossing/route/stress_v8_gate/D/segment1/looks/look1/T1/decide/footprint_A2.npy`。
      - B1 任务 7208183：背缘误差 +0.350287 m；接触带存在=True、带内误差=0.34999999999999964；`outputs/crossing/route/stress_v8_gate/D/segment1/looks/look1/T1/decide/footprint_B1.npy`。
      - B2 任务 7208576：背缘误差 +0.350287 m；接触带存在=True、带内误差=0.34999999999999964；`outputs/crossing/route/stress_v8_gate/D/segment1/looks/look1/T1/decide/footprint_B2.npy`。
      - C1 任务 7208971：背缘误差 +0.050344 m；接触带存在=True、带内误差=0.09999999999999964；`outputs/crossing/route/stress_v8_gate/D/segment1/looks/look1/T1/decide/footprint_C1.npy`。
      - C2 任务 7209396：背缘误差 +0.050344 m；接触带存在=True、带内误差=0.09999999999999964；`outputs/crossing/route/stress_v8_gate/D/segment1/looks/look1/T1/decide/footprint_C2.npy`。
    - T2：6 份 / 0 准入，证据 `outputs/crossing/route/stress_v8_gate/D/segment1/looks/look1/T2/decide/target_decision.json`。
  - look2：生成 12，准入 0。
    - T2：12 份 / 0 准入，证据 `outputs/crossing/route/stress_v8_gate/D/segment1/looks/look2/T2/decide/target_decision.json`。
  - 第一眼上传图与原运行逐字节比较：{'T1': False, 'T2': False}；各输入 SHA 见 `diagnosis-data.json`。
- original：arrived，1 眼；来源 `evidence/reviews/beforestep_r1/lux/original_b/summary.json`。
  - look1：生成 12，准入 8。
    - T1：6 份 / 6 准入，证据 `evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T1/decide/target_decision.json`。
      - A1 任务 5958685：背缘误差 +0.000344 m；接触带存在=True、带内误差=0.04999999999999982；`evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T1/decide/footprint_A1.npy`。
      - A2 任务 5958690：背缘误差 +0.000344 m；接触带存在=True、带内误差=0.04999999999999982；`evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T1/decide/footprint_A2.npy`。
      - B1 任务 5958877：背缘误差 +0.350287 m；接触带存在=True、带内误差=0.2999999999999998；`evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T1/decide/footprint_B1.npy`。
      - B2 任务 5958911：背缘误差 +0.350287 m；接触带存在=True、带内误差=0.34999999999999964；`evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T1/decide/footprint_B2.npy`。
      - C1 任务 5958948：背缘误差 +0.100344 m；接触带存在=True、带内误差=0.15000000000000036；`evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T1/decide/footprint_C1.npy`。
      - C2 任务 5959025：背缘误差 +0.100344 m；接触带存在=True、带内误差=0.15000000000000036；`evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T1/decide/footprint_C2.npy`。
    - T2：6 份 / 2 准入，证据 `evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T2/decide/target_decision.json`。
      - A2 任务 5958654：背缘误差 -0.699856 m；接触带存在=False、带内误差=None；`evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T2/decide/footprint_A2.npy`。
      - C1 任务 5958934：背缘误差 -0.600000 m；接触带存在=False、带内误差=None；`evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T2/decide/footprint_C1.npy`。
- 1眼保存状态只读规划：{'production_with_zero_admitted_fallback': False, 'admitted_candidates_only': True, 'without_imagination_or_fallback': True, 'true_high_rock_occupancy': True}；候选联合占 435 格；`outputs/crossing/route/stress_v8_gate/A/segment1/decision/look1_state.npy`。
- 2眼保存状态只读规划：{'production_with_zero_admitted_fallback': False, 'admitted_candidates_only': True, 'without_imagination_or_fallback': True, 'true_high_rock_occupancy': True}；候选联合占 435 格；`outputs/crossing/route/stress_v8_gate/A/segment1/decision/look2_state.npy`。

## 结论与动作

F2_007 的 A/D 第一眼各12份、3准入：前石2份、后石1份；后石候选A1背面短约0.75m，接触点y=-0.365附近候选缺失。原R2首眼后石0准入，因此再看一眼，第二眼2份准入后到达。原监视器在高石轮触时停车，A/D未发生第二段。

stress_v8 首眼后石0准入，第二眼含重试12份仍0准入。冻结pipeline.py会把零准入目标周围1.5m的未知区按保守占地处理；只用已准入前石联合仍有路，加零准入后石fallback才无路。保存状态只读规划已复现两眼原停车条件。因此原因是后石没有准入候选触发保守封锁，不是已准入候选过大堵死窄道。

上传图字节不同本身不证明门遮挡了高石；没有能够支持移动门的因果证据。因此不调整方法参数，不为结果选门位置。F3_002 从 x9.0/22001 开始，只允许预检查不通过时按原规则整体后移。

数字修正：原F2_007实际2眼、sim_time_s=128.4，不能沿用未核实的1眼印象。所有逐字节上传对比与原始路径见diagnosis-data.json。
