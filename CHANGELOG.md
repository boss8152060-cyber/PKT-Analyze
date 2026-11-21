# CHANGELOG — เลขเวอร์ชัน PKT x.y.z

ประวัติการเปลี่ยนแปลงของโปรแกรม PK Studio เรียงตามเวลา แต่ละบรรทัดมีเลขเวอร์ชัน PKT, รหัส commit (hash), ชื่อเดิม และคำอธิบายสั้น ๆ ว่าทำอะไร
ชื่อ commit ทั้งหมดถูกเปลี่ยนเป็น `PKT x.y.z: ...` แล้ว (PKT 1.29.2); คอลัมน์ "ชื่อเดิม" คือชื่อก่อนเปลี่ยน; hash ในตารางเป็นของประวัติใหม่ (61 commit แรกก่อน v27(1) hash ไม่เปลี่ยน)

## กติกาเลขเวอร์ชัน

| ตำแหน่ง | ความหมาย | ตัวอย่าง |
|---|---|---|
| `x` | ระยะใหญ่ | 0 = ก่อนชุด v28 (v27 และเอกสาร), 1 = งานตัวชี้วัดชุด v28 |
| `y` | หัวข้องานใหม่ (ตัวชี้วัดใหม่ / ระบบใหม่) | PET แบบพื้นที่ขัดแย้ง = `1.22.z` |
| `z` | งานเรื่องเดียวกันที่แก้ต่อ (แก้บั๊ก ปรับค่า ปรับเอกสาร) | `1.22.0` → `1.22.1`; เรื่องใหม่ → `1.23.0` |

- commit ใหม่ตั้งชื่อ `PKT x.y.z: คำอธิบายสั้น ๆ` (ต่อ `(PASS)` เมื่อผู้ใช้ยืนยัน) และติด tag `PKT-x.y.z` ที่ commit นั้น
- `Merge pull request ...` ที่ GitHub สร้างให้ไม่ให้เลขเวอร์ชัน (ไม่ใช่งาน)
- เวอร์ชันถัดไป: งานต่อเรื่องเดิม = `1.46.4` (เรื่อง 1.45 = `1.45.2`) (TTC ต่อ = `1.43.2`, วิดีโอผลลัพธ์ = `1.44.2`); เรื่องใหม่ = `1.47.0` (เลขเรียงตามหัวข้อ ไม่ใช่เวลาเสมอไป — หัวข้อ 1.25 ทำหลังหัวข้อ 1.26–1.28 ของเซสชัน cloud)


## 0.0.z — ประวัติเดิมที่นำเข้าจากไฟล์เวอร์ชันเก่า (Run0 → Run3 v27)

commit เหล่านี้มีชื่อเดิมแบบ `Run3 v26(...)` ฯลฯ ถูกเปลี่ยนเป็น `PKT-Analyze 0.0.N: <ชื่อเดิม>` เมื่อ 2026-10-10 (เรียงตามเวลา)

| PKT-Analyze | commit | ชื่อเดิม |
|---|---|---|
| **PKT-Analyze 0.0.0** | `2fd2c7c` | Run0: Detection_Counting_Summary |
| **PKT-Analyze 0.0.1** | `8f1276b` | Run1: GUI_Detection_Tracking |
| **PKT-Analyze 0.0.2** | `7f1c6fa` | Run2 v2: Zones |
| **PKT-Analyze 0.0.3** | `6490d92` | Run2 v3: ZoneAssignment |
| **PKT-Analyze 0.0.4** | `08d4f28` | Run2 v4: SimpleZone |
| **PKT-Analyze 0.0.5** | `ede3317` | Run2 v5: CleanZoneUI |
| **PKT-Analyze 0.0.6** | `2029467` | Run2 v6: FileZoneSettings |
| **PKT-Analyze 0.0.7** | `df3f7d2` | Run2 v7: TrajectoryPosition |
| **PKT-Analyze 0.0.8** | `246a63e` | Run2 v8: TrajectoryPosition_CleanUI |
| **PKT-Analyze 0.0.9** | `4b75ed2` | Run2 v9: SingleLabel |
| **PKT-Analyze 0.0.10** | `a33f211` | Run2 v10: TrajectoryPointOnly |
| **PKT-Analyze 0.0.11** | `d493fce` | Run2 v11: SettingsFixed |
| **PKT-Analyze 0.0.12** | `0ff107f` | Run2 v12: RestoreProcessingUI |
| **PKT-Analyze 0.0.13** | `0ef9310` | Run2 v14: ThreeCSV |
| **PKT-Analyze 0.0.14** | `8108b5a` | Run2 v15: ZoneDisplay |
| **PKT-Analyze 0.0.15** | `d38c0c6` | Run2 v16: ThreeCSV_Only |
| **PKT-Analyze 0.0.16** | `988f3fb` | Run2 v17: NoPreset |
| **PKT-Analyze 0.0.17** | `3ebfe31` | Run3: Integrated |
| **PKT-Analyze 0.0.18** | `916434c` | Run3: Defaults |
| **PKT-Analyze 0.0.19** | `d71b23e` | Run3 v2: Integrated_Defaults |
| **PKT-Analyze 0.0.20** | `21d428b` | Run3 v3: Integrated_Defaults |
| **PKT-Analyze 0.0.21** | `8033a94` | Run3 v4: Integrated_Defaults |
| **PKT-Analyze 0.0.22** | `847d8ba` | Run3 v5: Integrated_Defaults |
| **PKT-Analyze 0.0.23** | `d25ded9` | Run3 v6: Integrated_Defaults |
| **PKT-Analyze 0.0.24** | `cf6b18e` | Run3 v7: Integrated_Defaults |
| **PKT-Analyze 0.0.25** | `bfaa540` | Run3 v8: Integrated_Defaults |
| **PKT-Analyze 0.0.26** | `ba9df51` | Run3 v9: Integrated_Defaults |
| **PKT-Analyze 0.0.27** | `075cd0f` | Run3 v13: Integrated_Defaults |
| **PKT-Analyze 0.0.28** | `9996d78` | Run3 v14: Integrated_Defaults |
| **PKT-Analyze 0.0.29** | `d51ba1c` | Run3 v16: Integrated_Defaults |
| **PKT-Analyze 0.0.30** | `726803f` | Run3 v17: Integrated_Defaults |
| **PKT-Analyze 0.0.31** | `dd0a130` | Run3 v18: Integrated_Defaults |
| **PKT-Analyze 0.0.32** | `123fb5f` | Run3 v19: Integrated_Defaults |
| **PKT-Analyze 0.0.33** | `5cbeeea` | Run3 v21: Integrated_Defaults |
| **PKT-Analyze 0.0.34** | `0c09099` | Run3 v22: Integrated_Defaults |
| **PKT-Analyze 0.0.35** | `02d19a9` | Run3 v23: Integrated_Defaults |
| **PKT-Analyze 0.0.36** | `2559f17` | Run3 v25: Integrated_Defaults |
| **PKT-Analyze 0.0.37** | `71f5c92` | Run3 v26: Integrated_Defaults |
| **PKT-Analyze 0.0.38** | `d1b72a5` | Run3 v26(5): GapFixed |
| **PKT-Analyze 0.0.39** | `d7c67ba` | Run3 v26(5.1): GapFixed |
| **PKT-Analyze 0.0.40** | `2b51820` | Run3 v26(5.2): GapFixed_CalibrationView |
| **PKT-Analyze 0.0.41** | `d248c59` | Run3 v26(5.3): GapFixed_CalibrationView |
| **PKT-Analyze 0.0.42** | `006d082` | Run3 v26(5.4): GapFixed_CalibrationView_TableOrganized |
| **PKT-Analyze 0.0.43** | `c11f535` | Run3 v26(5.5): GapAcceptance_SubjectSpecific |
| **PKT-Analyze 0.0.44** | `4acb681` | Run3 v26(5.6): GapAcceptance_Zone6StopState |
| **PKT-Analyze 0.0.45** | `ddf1941` | Run3 v26(5.8): GapAcceptance_DecisionZones_1_4_6 |
| **PKT-Analyze 0.0.46** | `4812069` | Run3 v26(5.10): GapAcceptance_DecisionZoneWindow |
| **PKT-Analyze 0.0.47** | `e1ee50d` | Run3 v26(5.11): CommonVehicleEventMap |
| **PKT-Analyze 0.0.48** | `a130703` | Run3 v26(5.11.1): CommonVehicleEventMap_GapErrorFix (PASS) |
| **PKT-Analyze 0.0.49** | `574ebaf` | Run3 v26(5.12): CSV_Simplified |
| **PKT-Analyze 0.0.50** | `c310f7c` | Run3 v26(5.13.1): CSV_SchemaFix |
| **PKT-Analyze 0.0.51** | `1312588` | Run3 v26(5.13.2): SpeedZones1_6 |
| **PKT-Analyze 0.0.52** | `662ceb3` | Run3 v26(5.14.1): UI_Research_Organized (PASS) |
| **PKT-Analyze 0.0.53** | `a7ccb8c` | Run3 v26(5.14.5): GapAcceptance_BinaryOnly_CleanDiagnostics |
| **PKT-Analyze 0.0.54** | `1e24951` | Run3 v26(5.14.6): GapAcceptance_BinaryProgress |
| **PKT-Analyze 0.0.55** | `a8202e1` | Run3 v26(5.14.7): GapAcceptance_BinaryProgress_Fix |
| **PKT-Analyze 0.0.56** | `2679c6d` | Run3 v26(5.14.8): GapAcceptance_TwoStage (PASS) |
| **PKT-Analyze 0.0.57** | `8fc494b` | Run3 v26(5.14.9): EventSpeed_PET_Gap_LC |
| **PKT-Analyze 0.0.58** | `3859b2c` | Run3 v26(5.14.10): EventSpeed_PET_Gap_LC_Fix |
| **PKT-Analyze 0.0.59** | `e59fbcb` | Run3 v26(5.14.11): GapVehicleEventMap_Fix (PASS) |
| **PKT-Analyze 0.0.60** | `97e3cb8` | Run3 v27: Integrated_Defaults |

## 0.1.z — เอกสารโปรเจ็คและกติกา git (ก่อนชุด v27)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 0.1.0** | `9e6d3f3` | Docs: ProjectOverview_Plan_GitRules_Gitignore | เอกสารภาพรวมโปรเจ็ค, แผนงาน, กติกา git, .gitignore |
| **PKT 0.1.1** | `b7b3c06` | Docs: PlanUpdate_RemoteOriginPushed | อัปเดตแผน: ตั้ง remote origin และ push แล้ว |

## 0.2.z — แก้ย่อยชุด v27

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 0.2.0** | `35c0403` | Run3 v27(1): ZoneSummary_ExitTimeFix | แก้เวลาออกของ Zone Summary |
| **PKT 0.2.1** | `bac2c29` | Run3 v27(2): ZoneFlicker_SummaryCleanup | ล้างการแกว่งเข้าออกขอบโซนใน Summary |
| **PKT 0.2.2** | `dee065b` | Run3 v27(3): Preflight_ZoneNotDefinedWarning | เตือนก่อนรันเมื่อยังไม่มีโซน |
| **PKT 0.2.3** | `108ee40` | Run3 v27(4): Preflight_GapMappingWarning | เตือนก่อนรันเมื่อ Gap ไม่มี Line mapping |
| **PKT 0.2.4** | `5500476` | Docs: PlanAdd_LineEditor_GapCrossingDedupe | เอกสาร: เพิ่มแผนหน้าต่างวาด Line และการตัดซ้ำของ Gap |

## 0.3.z — เอกสารสเปกตัวชี้วัดชุดใหม่ (v28)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 0.3.0** | `32069eb` | Docs: SpecV28_NewIndicators_PlanPhaseV | เขียน SPEC v28 และแผนระยะที่ 5 |
| **PKT 0.3.1** | `6c5cdee` | Docs: SpecV28_AnswersRecorded | บันทึกคำตอบของผู้ใช้ลงสเปก |

## 1.1.z — ตัวชี้วัดชุดใหม่ + Movement (LDP, Lateral Clearance, PET, TTC, Gap, Speed)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.1.0** | `c8feae0` | Run3 v28(1): MovementSequence_LaneWidthInputs | Movement จากลำดับโซน + ช่องกรอกความกว้างเลน |
| **PKT 1.1.1** | `d25d0b9` | Docs: SpecV28_NewIndicatorCodes_Y1toY6 | เอกสาร: ตั้งรหัสตัวชี้วัด (ภายหลังเลิกใช้) |
| **PKT 1.1.2** | `80fdf03` | Run3 v28(2): Y6Speed_ZoneAndMovement | Speed ต่อโซนและต่อ Movement |
| **PKT 1.1.3** | `02ab95b` | Run3 v28(3): Y1LDP_ChordReference | LDP แบบเส้นอ้างอิงจุดเข้า-ออกโซน |
| **PKT 1.1.4** | `7e8dbb9` | Run3 v28(4): Y2LateralClearance_HeadingPerpendicular | Lateral Clearance ตั้งฉากกับทิศวิ่ง + กรอบซ้อนกัน |
| **PKT 1.1.5** | `f07b007` | Run3 v28(5): Y5PET_Y4TTC_Zones3and6_SideCollision | PET และ TTC ในโซน 3, 6 + ชนด้านข้าง |
| **PKT 1.1.6** | `c1bbe9f` | Run3 v28(6): Y3Gap_FirstCrossingOnly_V28Finalize | Gap Acceptance ข้ามเส้นครั้งแรกเท่านั้น |
| **PKT 1.1.7** | `78f4385` | Run3 v28(7): IndicatorNamesInsteadOfYCodes | เรียกตัวชี้วัดด้วยชื่อ ไม่ใช้รหัส Y1–Y6 |
| **PKT 1.1.8** | `c005c29` | Run3 v28(8): UserAnswers_GapTable_LDPAllClasses_TTCSideAdjustable_LCAllPairs | ตามคำตอบผู้ใช้: ตาราง Gap, LDP ทุกชนิดรถ, TTC ด้านข้างปรับได้, LC ทุกคู่ |
| **PKT 1.1.9** | `fea90d8` | Run3 v28(9): LDP_DivideByHalfWidth | LDP หารด้วยครึ่งความกว้างเลน |

## 1.2.z — Line และ Reference Line Mapping

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.2.0** | `6b88069` | Run3 v28(10): LineEditor_DrawReferenceLines | หน้าต่างวาด Line อ้างอิง |
| **PKT 1.2.1** | `d713d8b` | Run3 v28(11): ReferenceLineMapping_PrefilledSite8 | Reference Line Mapping ตั้งไว้ให้ Site 8 |

## 1.3.z — ไฟล์โซนและการรันด้วย GPU (CUDA)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.3.0** | `1e6a357` | Docs: ZoneFileDJI0426_VideoFacts | เอกสาร: ข้อเท็จจริงของวิดีโอที่ใช้กับไฟล์โซน DJI_0426 |
| **PKT 1.3.1** | `7e4f51f` | Run3 v28(12): CUDA_PythonFallback_LauncherBat | ถอยไปใช้ Python ที่มี CUDA อัตโนมัติ + ไฟล์ .bat เปิดโปรแกรม |
| **PKT 1.3.2** | `d318ef1` | Docs: CUDA_Python312_Launcher | เอกสาร: ตั้ง Python 3.12 + CUDA |

## 1.4.z — กรองข้อมูลและบอกสาเหตุผลว่าง

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.4.0** | `1f5262c` | Run3 v28(13): DuplicateTrackFilter | ตัดแทร็กซ้ำ (รถคันเดียวสองไอดี) |
| **PKT 1.4.1** | `ad40f8a` | Run3 v28(14): ExplainEmptyOutputs_ZoneVideoMismatchWarning | อธิบายสาเหตุที่ผลลัพธ์ว่าง + เตือนโซนไม่ตรงวิดีโอ |
| **PKT 1.4.2** | `c9c446e` | Run3 v28(15): MovementFirstVisitFallback | Movement: ถอยไปใช้การเข้าโซนครั้งแรกเมื่อลำดับไม่ครบ |

## 1.5.z — Gap Acceptance แบบ PASS (สองขั้น)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.5.0** | `8957937` | Docs: GapAcceptance_PASSDesign_WaitZones1356 | เอกสาร: ออกแบบ Gap แบบ PASS โซนรอ 1, 3, 5, 6 |
| **PKT 1.5.1** | `8b27f57` | Run3 v28(16): GapAcceptance_TwoStagePASS_LineOptional | Gap สองขั้น (เข้า/ออก) ตรรกะ PASS, Line เป็นตัวเลือก |
| **PKT 1.5.2** | `b8a396d` | Run3 v28(17): ZoneRemap_OldZoneFileWorksWithNewMovements | แปลงไฟล์โซนเก่าให้ใช้กับ Movement ใหม่ (ภายหลังถูกถอย) |
| **PKT 1.5.3** | `0c7ac56` | Run3 v28(18): RevertToV28_13 | ย้อนไป v28(13) |
| **PKT 1.5.4** | `4320d51` | Run3 v28(19): RestoreV28_16_WithoutZoneRemap | คืน v28(16) โดยไม่มีการแปลงโซน |

## 1.6.z — ความถูกต้องของ CSV และพื้นฐาน UI

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.6.0** | `2028699` | Run3 v28(20): ExcelSafeMovementArrows | เขียน Movement เป็นลูกศร กัน Excel แปลงเป็นวันที่ |
| **PKT 1.6.1** | `092d318` | Run3 v28(21): FP16KeyByVersion_TimestampStartsAtZero | คีย์ FP16 ตามเวอร์ชัน + เวลาเริ่มที่ 0 |
| **PKT 1.6.2** | `d091aa4` | Run3 v28(22): SpeedOutlierFlag_LC_PET_Stats_UntrackedCount | ธง Speed ผิดปกติ, สถิติ LC/PET, นับรถที่ไม่ได้ติดตาม |
| **PKT 1.6.3** | `063136d` | Run3 v28(23): MergeClips_SensitivityTool_ParametersDoc | เครื่องมือรวมคลิป, วิเคราะห์ความไว, เอกสารค่าพารามิเตอร์ |
| **PKT 1.6.4** | `9d5411f` | Docs: Phase3_UserDeferredRiskRuleSensitivityTracking | เอกสาร: ระยะที่ 3 เรื่องที่ผู้ใช้เลื่อนไว้ |
| **PKT 1.6.5** | `6ea5f76` | Run3 v28(24): UiQueue_RelativeDefaultPaths_NoAutoDelete_Logging | คิวเธรดของ UI, พาธเริ่มต้นแบบสัมพัทธ์, ไม่ลบไฟล์เอง, log |
| **PKT 1.6.6** | `8798957` | Docs: PlanCleanup_RemoveUserPendingItems | เอกสาร: จัดแผนใหม่ เอารายการรอผู้ใช้ออก |
| **PKT 1.6.7** | `c47423d` | Docs: RemovePlan_4.4_4.5 | เอกสาร: ตัดหัวข้อ 4.4–4.5 ออกจากแผน |
| **PKT 1.6.8** | `30c7239` | Docs: PlanFix_4.2_Note | เอกสาร: แก้หมายเหตุข้อ 4.2 |

## 1.7.z — รันหลายคลิป ช่วงเวลา และเครื่องเล่นวิดีโอ

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.7.0** | `90676ae` | Run3 v28(25): BatchRun_TrackerSweepTool | เครื่องมือ batch ไล่ค่า tracker |
| **PKT 1.7.1** | `3ca9dfc` | Run3 v28(26): BatchRun_FolderMirrorOutput_CombinedPerLevel | ผลลัพธ์ batch เป็นโครงสร้างโฟลเดอร์เดียวกับต้นทาง + รวมต่อระดับ |
| **PKT 1.7.2** | `4cdd94f` | Run3 v28(27): AnalysisTimeWindow_RecordWindow_Core | ช่วงเวลาวิเคราะห์และช่วงบันทึกวิดีโอ (แกนหลัก) |
| **PKT 1.7.3** | `48e2f70` | Run3 v28(28): VideoPlayerDialog_SetTimeRangeInApp | หน้าต่างเครื่องเล่น: กำหนดช่วงเวลาในโปรแกรม |
| **PKT 1.7.4** | `a6a056d` | Run3 v28(29): BatchWindow_PerClipTimeRangeAndRecording_PlanFile | หน้าต่าง batch: ช่วงเวลาและการบันทึกต่อคลิป + ไฟล์แผน |
| **PKT 1.7.5** | `74b3e9a` | Run3 v28(30): PerClipCsvOnly_AddToExistingPlace_DayFolder | บันทึก CSV อย่างเดียวต่อคลิป, เพิ่มเข้าโฟลเดอร์วันเดิม |
| **PKT 1.7.6** | `44b2bf0` | Run3 v28(31): MirrorAnyFolderStructure_FolderPerClip | ทำโครงสร้างโฟลเดอร์ใดก็ได้ที่นำเข้า, โฟลเดอร์ต่อคลิป |

## 1.8.z — จัด UI ใหม่เป็น 4 ขั้น

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.8.0** | `6d5395c` | Run3 v28(32): UiRedesign_FourSteps_UnifiedClipList_RunBar | UI 4 ขั้น: รายการคลิปรวม + แถบรัน |
| **PKT 1.8.1** | `1b94664` | Run3 v28(33): PlayerDialog_FitScreen_VisibleSaveButton | เครื่องเล่น: พอดีหน้าจอ ปุ่มบันทึกมองเห็น |
| **PKT 1.8.2** | `c296e8c` | Run3 v28(34): RemoveRedundantRecordCheckbox_SkipDoneWording | ตัดช่องติ๊กบันทึกที่ซ้ำ, แก้คำว่า ข้ามคลิปที่เสร็จแล้ว |
| **PKT 1.8.3** | `3775a01` | Run3 v28(35): CalibrationDialog_FixOverlappingFields_LayoutTest | แก้ช่องซ้อนกันในหน้าปรับเทียบ + ทดสอบเลย์เอาต์ |

## 1.9.z — การปรับเทียบ: จุดที่บันทึก, จุดตัดสินโซน, ต่อโซน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.9.0** | `204be22` | Run3 v28(36): CalibrationShowsSavedPoints_PreviewFix_EmptyReasonsInBatchReport_TrajectoryWarning | หน้าปรับเทียบแสดงจุดที่บันทึก, แก้ตัวอย่าง, รายงานผลว่างใน batch |
| **PKT 1.9.1** | `f036895` | Run3 v28(37): ShowZoneDecisionPoint_CalibrationMeasureTool | แสดงจุดตัดสินโซน + เครื่องมือวัดในหน้าปรับเทียบ |
| **PKT 1.9.2** | `06b938b` | Run3 v28(38): PerZoneCalibration_OwnReferenceQuadPerZone | ปรับเทียบต่อโซน (ชุดจุดอ้างอิงของโซนเอง) |

## 1.10.z — ชื่อไฟล์ผลลัพธ์และการต่อคลิปต่อเนื่อง

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.10.0** | `2e00695` | Run3 v28(39): FileNamesWithClipName_CombinedCsvAllClips | ชื่อไฟล์มีชื่อคลิป + CSV รวมทุกคลิป |
| **PKT 1.10.1** | `8ac8c25` | Run3 v28(40): CombinedCsv_UniqueIdKeys_ClipStart | CSV รวม: คีย์ ID ไม่ซ้ำ + เวลาเริ่มคลิป |
| **PKT 1.10.2** | `f6def19` | Run3 v28(41): ChainConsecutiveClips_IdsContinueAcrossClips | ต่อคลิปต่อเนื่อง: ID ต่อกันข้ามคลิป |
| **PKT 1.10.3** | `952876b` | Run3 v28(42): ChainUsesWholeClips_IgnoresTimeRangeAndRecordRange | การต่อใช้ทั้งคลิป ไม่สนช่วงเวลา |
| **PKT 1.10.4** | `feaffd0` | Run3 v28(43): PlainResultFileNames_NoClipNameInFiles | ชื่อไฟล์ผลลัพธ์แบบเรียบ ไม่มีชื่อคลิป |
| **PKT 1.10.5** | `bd36f43` | Run3 v28(44): ContinueMeansTrackerCarriesOn_RangeAndRecordingStayPerClip | ต่อต่อเนื่อง = tracker ไปต่อ, ช่วงเวลา/บันทึกยังต่อคลิป |
| **PKT 1.10.6** | `49c6453` | Docs: ContinueGapExplanation_R6Review | เอกสาร: ช่องว่างของการต่อคลิป (ทบทวน R6) |

## 1.11.z — ความเร็วในการรัน และตัดแทร็กสั้นซ้ำ

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.11.0** | `62698f1` | Run3 v28(45): BackgroundDecodeAndEncode_AutoPrecisionFP32OnGTX16 | ถอดรหัส/เข้ารหัสวิดีโอเบื้องหลัง + เลือกความแม่นยำอัตโนมัติ (GTX16) |
| **PKT 1.11.1** | `57e4bb9` | Run3 v28(46): ShortDuplicateTracks_RemovedFromAnalysis | ตัดแทร็กสั้นที่ซ้ำออกจากการวิเคราะห์ |

## 1.12.z — Lateral Clearance: ระยะข้างสูงสุดและช่วงเคียงข้าง

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.12.0** | `9d94784` | Run3 v28(47): LateralClearance_SidewaysLimit_AlongWindow_ClosestPerPair | LC: จำกัดระยะข้าง, หน้าต่างตามแนวยาว, ค่าใกล้สุดต่อคู่ |
| **PKT 1.12.1** | `09301cd` | Run3 v28(48): BottomDefault_OffsetWarning_ZoneFlickerMergeSetting | จุดล่างเป็นค่าเริ่มต้น + เตือน offset (ถูกถอยทันที) |
| **PKT 1.12.2** | `9471108` | Run3 v28(49): RevertTo_v28(46)_UndoLateralClearanceLimits_And_BottomDefault | ย้อนไป v28(46) |
| **PKT 1.12.3** | `a223221` | Run3 v28(50): LateralClearance_AlongWindow_And_MaxSidewaysOptions | LC: ตัวเลือกช่วงเคียงข้างและระยะข้างสูงสุด |

## 1.13.z — Topview รอบแรก และแผนที่อ้างอิงจากภาพโดรน (ภายหลังถอยออก)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.13.0** | `63f5fa1` | Run3 v28(51): TopviewRecords_And_TopviewVideo_FromMetricPoints | ไฟล์พิกัด Topview + วิดีโอ Topview จากจุดเมตร |
| **PKT 1.13.1** | `21348e6` | Run3 v28(52): TopviewVideo_PlaysAtRealSpeed | วิดีโอ Topview เล่นด้วยความเร็วจริง |
| **PKT 1.13.2** | `c5e1bac` | Run3 v28(53): ReferenceMap_DroneTopviewAsMap_CalibrationDialog | แผนที่อ้างอิง: ใช้ภาพโดรนเป็นแผนที่ในหน้าปรับเทียบ |
| **PKT 1.13.3** | `1750840` | Run3 v28(54): ReferenceMap_AcceptsVideoFrame_ThaiPaths | แผนที่อ้างอิงรับเฟรมวิดีโอ + พาธภาษาไทย |
| **PKT 1.13.4** | `05c5505` | Run3 v28(55): ReferenceMapDialog_ZoomAtPointer_Pan_ResetView_FrameSlider | หน้าแผนที่: ซูมที่เมาส์ แพน รีเซ็ต แถบเลื่อนเฟรม |
| **PKT 1.13.5** | `0edef4b` | Run3 v28(56): ReferenceMap_ZonesOverlay_PerPointError_DeletePoint_PoorCalibrationWarning | แผนที่: ซ้อนโซน, ความคลาดต่อจุด, ลบจุด, เตือนปรับเทียบไม่ดี |
| **PKT 1.13.6** | `22192b9` | Run3 v28(57): AdjustZonesOnMap_DragCorners_WriteMapfitZoneFile | ปรับโซนบนแผนที่ด้วยการลากมุม (ถูก revert) |
| **PKT 1.13.7** | `dec858f` | Revert "Run3 v28(57): AdjustZonesOnMap_DragCorners_WriteMapfitZoneFile" | ย้อน: ปรับโซนบนแผนที่ |
| **PKT 1.13.8** | `2427ba3` | Run3 v28(58): ReferenceMap_UseZoneCornersAsCameraPoints_DragOnMap | ใช้มุมโซนเป็นจุดกล้อง ลากบนแผนที่ |
| **PKT 1.13.9** | `dfc4875` | Run3 v28(59): ZonesAppearOnMap_LayoutFollowsCorners_RealDistancesBetweenCorners | โซนแสดงบนแผนที่ ระยะจริงระหว่างมุม |
| **PKT 1.13.10** | `12cee67` | Run3 v28(60): ReferenceMap_AutoAlign_ECC_EdgeImages_BeforeAfterPreview | จัดแนวแผนที่อัตโนมัติ (ECC) + ดูก่อนหลัง |
| **PKT 1.13.11** | `af19011` | Run3 v28(61): SnapZonesToRoadSurface_Automatic_MapfitZoneFile | ปรับโซนให้ชิดผิวถนนอัตโนมัติ |
| **PKT 1.13.12** | `7a217e8` | Run3 v28(62): ReferenceMap_FreeCornersStayStill_SmallStepsBefore4Pairs_ClickVsDrag | มุมอิสระอยู่นิ่ง, ขยับทีละน้อยก่อนมี 4 คู่, คลิป vs ลาก |
| **PKT 1.13.13** | `eef6140` | Run3 v28(63): SnappedZones_CleanOutlines_OptionalCornerDragOnMap | โซนที่ปรับแล้วเส้นสะอาด, ลากมุมบนแผนที่ได้ |
| **PKT 1.13.14** | `633c269` | Run3 v28(64): LensDistortion_EstimatedFromPairs_LeaveOneOutGuard_UsedInEveryMetricPoint | ประมาณความบิดของเลนส์จากคู่จุด + กัน leave-one-out |

## 1.14.z — Topview รอบสอง: ปรับเทียบแบบวางราบ เส้นถนน เลนส์ (ถอยออกทั้งหมด)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.14.0** | `9c9bb6c` | Run3 v28(65): RevertTo_v28(50)_BeforeTopview | ย้อนไป v28(50) ก่อน Topview |
| **PKT 1.14.1** | `48fe227` | Revert "Run3 v28(65): RevertTo_v28(50)_BeforeTopview" | ย้อน: การย้อนไป v28(50) |
| **PKT 1.14.2** | `ca56d1e` | Run3 v28(66): LeanGroundCalibration_Fig2Style_LensKeypointsReprojectionROI | ปรับเทียบพื้นแบบเอียง (Fig.2) + เลนส์ + ROI |
| **PKT 1.14.3** | `ef9a3c8` | Docs: PlanLog_v28(66)_LeanGroundCalibration | เอกสาร: บันทึกแผน v28(66) |
| **PKT 1.14.4** | `325b92c` | Run3 v28(67): RevertTo_a6f6f54_TopviewWithoutDrone | ย้อนไป a6f6f54 (Topview ไม่มีโดรน) |
| **PKT 1.14.5** | `baf7349` | Revert "Run3 v28(67): RevertTo_a6f6f54_TopviewWithoutDrone" | ย้อน: การย้อนไป a6f6f54 |
| **PKT 1.14.6** | `b3e323b` | Run3 v28(68): TopviewLooksLikeAMap_FullBrightnessMap_FaintGrid_TranslucentVehicles | Topview หน้าตาเหมือนแผนที่ |
| **PKT 1.14.7** | `0e5c6e9` | Docs: PlanLog_v28(67)_v28(68)_TopviewLooksLikeAMap | เอกสาร: บันทึกแผน v28(67)–(68) |
| **PKT 1.14.8** | `118cea8` | Run3 v28(69): TopviewVideo_IsTheCameraVideoLensCorrectedAndLaidFlat | วิดีโอ Topview คือวิดีโอกล้องที่แก้เลนส์และวางราบ |
| **PKT 1.14.9** | `4736202` | Run3 v28(70): RemoveDroneMapFeatures_BackToNoDroneTopview | เอาฟีเจอร์แผนที่โดรนออก |
| **PKT 1.14.10** | `83aec56` | Run3 v28(71): LensFisheyeFromStraightLines_EmptyRoadTopviewLaidFlat | หาเลนส์ fisheye จากเส้นตรง, Topview วางราบจากถนนว่าง |
| **PKT 1.14.11** | `62c4d80` | Run3 v28(72): LensDialog_PopupWhenNoResult | หน้าต่างเลนส์เด้งเมื่อไม่มีผล |
| **PKT 1.14.12** | `f874a35` | Run3 v28(73): TopviewBlankAboveGroundFarField_RoadOnly | Topview ว่างส่วนเหนือพื้น/ไกล เหลือเฉพาะถนน |
| **PKT 1.14.13** | `f8b4925` | Run3 v28(74): TopviewSameShapeAsVideo_VehiclePicturesOnFootprints | Topview รูปทรงเดียวกับวิดีโอ, รูปรถบนฐานรถ |
| **PKT 1.14.14** | `ccdba1d` | Run3 v28(75): TopviewFollowsDisplaySettings_ReferencePointOnly_NoDarkMask | Topview ตามค่าการแสดงผล, จุดอ้างอิงอย่างเดียว |
| **PKT 1.14.15** | `4acbaff` | Run3 v28(76): MapStyleTopview_RoadLinesClickedOnCameraFrame | Topview แบบแผนที่, เส้นถนนคลิปบนเฟรมกล้อง |
| **PKT 1.14.16** | `1510543` | Run3 v28(77): TopviewNoVehiclePictures_ReferencePointOnly | Topview ไม่มีรูปรถ |
| **PKT 1.14.17** | `9956ce3` | Run3 v28(78): RoadLineTypes_WhiteYellowKerbBlueMotorcycleLane | ชนิดเส้นถนน: ขาว เหลือง ขอบทาง เลนมอเตอร์ไซค์ |
| **PKT 1.14.18** | `bf93c9f` | Run3 v28(79): KerbWhiteYellow_InsteadOfYellowBlack | ขอบทางขาว-เหลือง |
| **PKT 1.14.19** | `25c0c72` | Run3 v28(80): KerbStripeLength_0_5m | ความยาวลายขอบทาง 0.5 ม. |
| **PKT 1.14.20** | `bce3f57` | Run3 v28(81): OneToolForLensAndRoadLines | เครื่องมือเดียวสำหรับเลนส์และเส้นถนน |
| **PKT 1.14.21** | `135a190` | Run3 v28(82): StraightMarkedRoadLinesSnapToBestLine | เส้นถนนตรงเกาะเส้นที่ดีที่สุด |
| **PKT 1.14.22** | `9c4ea46` | Run3 v28(83): OneCalibrationWindow_LensGroundPointsRoadLines | หน้าต่างปรับเทียบเดียว: เลนส์ จุดพื้น เส้นถนน |
| **PKT 1.14.23** | `0eae322` | Run3 v28(84): GroundFromParallelPerpendicularLines_ManyPointsLeastSquares | พื้นจากเส้นขนาน/ตั้งฉากหลายจุด กำลังสองน้อยสุด |
| **PKT 1.14.24** | `48786b3` | Run3 v28(85): ZoneCornersAsGroundPoints_TypeEdgeLengths | มุมโซนเป็นจุดบนพื้น พิมพ์ความยาวขอบ |

## 1.15.z — ปรับเทียบจากมุมโซน (ถอยออกทั้งชุด)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.15.0** | `fe8f2a0` | Run3 v28(86): RevertTo_v28(50)_RemoveWholeTopviewSystem | ย้อนไป v28(50) เอาระบบ Topview ทั้งชุดออก |
| **PKT 1.15.1** | `37d8745` | Run3 v28(87): PerspectiveFromZones_EdgeLengths_QualityCheck | Perspective จากโซน: ความยาวขอบ + ตรวจคุณภาพ |
| **PKT 1.15.2** | `0e5db0d` | Run3 v28(88): CalibrationMethodChoice_ShowOnlyChosenBlock | เลือกวิธีปรับเทียบ แสดงเฉพาะกรอบที่เลือก |
| **PKT 1.15.3** | `3670a1f` | Run3 v28(89): PerZoneCalibration_ZoneCornersAppearAsP1toP4 | ปรับเทียบต่อโซน: มุมโซนปรากฏเป็น P1–P4 |
| **PKT 1.15.4** | `ae89392` | Run3 v28(90): PerZoneOwnTransform_AnyNumberOfCorners_OneSummaryLine | การแปลงต่อโซน: จำนวนมุมเท่าไรก็ได้ สรุปบรรทัดเดียว |
| **PKT 1.15.5** | `9de3702` | Run3 v28(91): CalibrationWindow_ZoneOutlinesAlwaysVisible_ChosenZoneYellow | หน้าปรับเทียบ: เส้นโซนมองเห็นเสมอ โซนที่เลือกสีเหลือง |
| **PKT 1.15.6** | `05ef8ef` | Run3 v28(91): FourCornerWindowDoesNotCutDownZonesWithMoreCorners | หน้าต่าง 4 มุมไม่ตัดโซนที่มีมุมมากกว่านี้ |
| **PKT 1.15.7** | `c91d69f` | Run3 v28(92): RadialLensTrend_FromZoneLengths_UsedForEveryPoint | แนวโน้มเลนส์แบบรัศมีจากความยาวโซน |
| **PKT 1.15.8** | `dc0fe06` | Run3 v28(93): RevertTo_v28(50)_RemoveCalibrationLayers | ย้อนไป v28(50) เอาชั้นปรับเทียบออก |

## 1.16.z — ผัง X–Y เมตร (พื้นฐานที่ใช้อยู่)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.16.0** | `939cde9` | Run3 v28(51): TopviewRecords_And_TopviewVideo_FromMetricPoints | ไฟล์พิกัด Topview + วิดีโอ Topview (นำกลับ) |
| **PKT 1.16.1** | `c5edba7` | Run3 v28(52): TopviewVideo_PlaysAtRealSpeed | วิดีโอ Topview เล่นด้วยความเร็วจริง (นำกลับ) |
| **PKT 1.16.2** | `6dd9af7` | Run3 v28(94): PlainXYPlane_TrajectoryPng_And_Video_ReferencePointLabelsPerDisplaySettings | ผัง X–Y เปล่า: ภาพเส้นทาง PNG + วิดีโอ จุดอ้างอิงและป้ายตามการแสดงผล |
| **PKT 1.16.3** | `aa5f4cf` | Run3 v28(95): OutsideZoneVehicles_ShowDotOrHide_NormalVideoAndXY | รถนอกโซน: แสดงเป็นจุดหรือซ่อน (วิดีโอปกติและ X–Y) |
| **PKT 1.16.4** | `2ef2153` | Docs: PlanStatus_v28(95)_TagV28_95_OpenItems | เอกสาร: สถานะ v28(95) + tag + รายการค้าง |

## 1.17.z — จัดแนววิดีโอกับภาพโดรน (Align)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.17.0** | `a04e36c` | Run3 v28(96): AlignVideoToDronePlane_KindsLikeQgisGeoreferencer_LeaveOneOut | Align วิดีโอกับระนาบโดรน หลายชนิดการแปลง + leave-one-out |
| **PKT 1.17.1** | `2de2753` | Run3 v28(97): AlignTable_WorstPairsFirst_RedMark_DeleteWorst | ตาราง Align: คู่แย่สุดก่อน ทำสีแดง ลบคู่แย่ |
| **PKT 1.17.2** | `b0fd795` | Run3 v28(98): AlignReferenceLines_NPointsInVideo_HeadTailInDrone_XYAxes | Align จากเส้นอ้างอิง (ถูกถอย) |
| **PKT 1.17.3** | `64666c5` | Run3 v28(97): AlignTable_SortedByHonestError_WorstPairs_MeasureTest | ตาราง Align เรียงตามความคลาดที่ซื่อสัตย์ + เครื่องมือวัด |
| **PKT 1.17.4** | `50f03b0` | Run3 v28(98): AlignZoneMode_PinsFromVideo_PlaceOnDrone_NewZoneFile | Align โหมดโซน: หมุดจากวิดีโอ วางบนโดรน (ถูกถอย) |
| **PKT 1.17.5** | `43c7d12` | Run3 v28(99): RevertTo_v28(97)_RemoveAlignV28_98 | ย้อนไป v28(97) เอา Align v28(98) ออก |
| **PKT 1.17.6** | `826ac03` | Run3 v28(100): AlignZonePins_VideoSideFromZoneFile_SkipUnsure | หมุดมุมโซนจากไฟล์โซน ข้ามได้ถ้าไม่แน่ใจ |

## 1.18.z — ผัง X–Y ตรงกลาง + ตัวแก้รูปโซน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.18.0** | `b4f6c5c` | Run3 v28(101): XYPictureCentredOnZones | ภาพ X–Y อยู่กลางโซน |
| **PKT 1.18.1** | `efe2c62` | Run3 v28(102): PreviewXYPlaneBeforeRun_ZonesInMetres_EdgeLengths | ดูตัวอย่างผัง X–Y ก่อนรัน + ความยาวขอบโซน |
| **PKT 1.18.2** | `0026f11` | Run3 v28(103): ZoneEditorOnVideoDroneXYViews_PerpendicularShiftSnapNewZoneFile | ตัวแก้รูปโซน 3 มุมมอง (วิดีโอ/โดรน/X–Y) ทำให้ตั้งฉาก บันทึกไฟล์โซนใหม่ |
| **PKT 1.18.3** | `1b41d1f` | Run3 v28(104): ZoneEditor_UseForAnalysisButton | ปุ่มใช้โซนที่แก้ในการวิเคราะห์ทันที |
| **PKT 1.18.4** | `4da2164` | Run3 v28(105): RemoveXYPreviewButton | เอาปุ่มตัวอย่างผัง X–Y ออก |

## 1.19.z — กรอบฐานรถ Footprint (ทดลอง แล้วถอยออก)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.19.0** | `355557e` | Run3 v28(106): VehicleFootprint_OnRoadPlane_XYAndRoadsideVideo | กรอบฐานรถบนระนาบถนน แสดงใน X–Y และวิดีโอข้างทาง |
| **PKT 1.19.1** | `b4ef0d4` | Run3 v28(107): RevertFootprint_BackToV28_105 | ย้อน Footprint กลับไปที่ v28(105) |

## 1.20.z — ออกแบบ TTC แบบเวกเตอร์ (เอกสาร)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.20.0** | `976b680` | Docs: TTC_VectorFormulation_Draft_InSpec | เขียนสูตร TTC เวกเตอร์ฉบับร่างลงสเปก |
| **PKT 1.20.1** | `70ea2d8` | Docs: TTC_Draft_RemoveDGate | ฉบับร่าง: ตัดเกณฑ์ระยะพลาดกัน D ออกก่อน |
| **PKT 1.20.2** | `c90ebac` | Docs: TTC_Draft_FixDMention | ฉบับร่าง: แก้ข้อความที่พูดถึง D |
| **PKT 1.20.3** | `5d3565a` | Docs: TTC_ConflictType_ByAngle_SameAsPaper | ฉบับร่าง: ชนิดความขัดแย้งตามมุมเหมือนเปเปอร์ |
| **PKT 1.20.4** | `a3f1d1b` | Docs: TTC_Draft_PairSelection_NoCrossingFilter | ฉบับร่าง: เลือกคู่รถ ไม่กรองด้วยจุดตัด trajectory |

## 1.21.z — TTC เวกเตอร์ + เกณฑ์ความเสี่ยง + สี่เหลี่ยมรถ + ตารางการแสดงผล

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.21.0** | `85d7f49` | Run3 v28(108): VectorTTC_ConflictAngleType_NoMissGate | TTC เวกเตอร์ + ชนิดความขัดแย้งตามมุม (30°/85°) |
| **PKT 1.21.1** | `5cd6696` | Run3 v28(109): RiskLevels_SeminarTables_SingleSpeedScale_OverallLevel_EditableLimits | เกณฑ์ความเสี่ยงตามสไลด์สัมมนา, ความเร็วชุดเดียว, ระดับรวม, กรอกเกณฑ์เองได้ |
| **PKT 1.21.2** | `2e81907` | Run3 v28(110): TTC_MissGateRestored_SlowVehicleSkip_TTCFramesCSV | คืนเกณฑ์ระยะพลาดกัน + ข้ามรถช้า + ไฟล์ TTC_Frames.csv |
| **PKT 1.21.3** | `8ab6486` | Docs: SpecAndPlan_TTCMissGate_v28_110 | เอกสาร: สเปกและแผนเรื่องเกณฑ์ระยะพลาดกัน |
| **PKT 1.21.4** | `5e0dd84` | Run3 v28(111): TTC_CrossingPathsArrivalGap_OtherPairsVector_BlankCutoffAll | TTC สองวิธี: เส้นทางตัดกัน (ส่วนต่างเวลาถึง) / ไม่ตัด (เวกเตอร์); เว้นว่าง = บันทึกทั้งหมด |
| **PKT 1.21.5** | `1cac3a4` | Run3 v28(112): TTC_VehicleRectangles_TimeUntilBoxesTouch | TTC: รถเป็นสี่เหลี่ยม ยาว×กว้าง เวลาที่กรอบแตะกัน |
| **PKT 1.21.6** | `62bedbd` | Run3 v28(113): TTCRectangles_ShowInXYAndRoadsideVideo_Switches | แสดงสี่เหลี่ยมรถของ TTC ใน X–Y และวิดีโอข้างทาง (สวิตช์) |
| **PKT 1.21.7** | `f1a75a3` | Run3 v28(114): TTCRectangles_OnNormalVideoNotThirdVideo_OptionsInTab1 | สี่เหลี่ยมวาดลงวิดีโอปกติ ไม่สร้างวิดีโอที่สาม + ตัวเลือกไปหน้า ① |
| **PKT 1.21.8** | `dadaed6` | Run3 v28(115): DisplayTable_TwoColumns_EverySwitchPerVideo_VideoSwitchesOnOnePage | ตารางการแสดงผลสองคอลัมน์: เปิด/ปิดแยกต่อวิดีโอ + สร้างวิดีโอหน้าเดียวกัน |
| **PKT 1.21.9** | `bd5720a` | Run3 v28(116): TTC_PointMethodDefault_ExpectedCollisionPointStoredAndDrawn | TTC จุดเดียวเป็นค่าตั้งต้น + เก็บและวาดจุดที่คาดว่าจะชน |
| **PKT 1.21.10** | `d0b6b57` | Run3 v28(117): ExpectedCollisionPoint_IsPathIntersection_NotMidpoint | จุดที่คาดว่าจะชน = จุดตัดของเส้นทางตรงสองคัน (ไม่ใช่จุดกึ่งกลาง) |
| **PKT 1.21.11** | `cd4a588` | Run3 v28(118): TTC_MeetingPointMustBeInsideZone_EdgeMargin | จุดพบกันของ TTC ต้องอยู่ในโซน (ขอบเผื่อ) — เซสชันคู่ขนาน |
| **PKT 1.21.12** | `10105e7` | Run3 v28(118): TTC_ZoneFiltersCollisionPoint_NotTracking | โซนของ TTC เป็นตัวกรองจุดชน ไม่ใช่ตัวกำหนดการ track |
| **PKT 1.21.13** | `baf1b16` | Run3 v28(119): TTC_CollisionZoneMustBeOnPathOfBothVehicles_ZoneSequence | จุดชนต้องอยู่ในโซนที่รถทั้งสองอยู่/จะเข้า (Zone Sequence) |

## 1.22.z — PET แบบพื้นที่ขัดแย้ง + LDP โซน 1

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.22.0** | `e15006a` | Run3 v28(120): PET_AllZones_Selectable | PET เลือกโซนได้ทุกโซน |
| **PKT 1.22.1** | `7cb39e8` | Run3 v28(121): LDP_Zone1_LockedWithNote | LDP: ล็อกโซน 1 พร้อมหมายเหตุ |
| **PKT 1.22.2** | `b33f7cc` | Run3 v28(122): PET_SameMovement_CountedIfTrajectoriesCross | PET: Movement เดียวกันนับถ้า trajectory ตัดกัน |
| **PKT 1.22.3** | `03371a6` | Run3 v28(123): PET_RequireRealTrajectoryCrossing_NoClosestApproachFallback | PET: ต้องตัดกันจริง ไม่ใช้จุดใกล้สุดแทน |
| **PKT 1.22.4** | `a43c6ab` | Run3 v28(124): PET_OptionalMinVehicleSpeed | PET: ความเร็วรถขั้นต่ำ (ตัวเลือก) |
| **PKT 1.22.5** | `41b9e90` | Run3 v28(125): PET_MinSpeed_UsesSpeedAtCrossingPoint | PET: ความเร็วขั้นต่ำใช้ความเร็ว ณ จุดตัด |
| **PKT 1.22.6** | `626e667` | Run3 v28(126): PET_SpeedColumns_AtCrossingPoint | PET: คอลัมน์ความเร็ว ณ จุดตัด |
| **PKT 1.22.7** | `8559a84` | Run3 v28(127): PET_CrossingPointOnly_ShowCrossingInVideo | PET: นับเฉพาะจุดตัด + แสดงจุดตัดในวิดีโอ |
| **PKT 1.22.8** | `71934da` | Docs: SPEC_PET_TypoFix | เอกสาร: แก้คำผิดในสเปก PET |
| **PKT 1.22.9** | `d50aafd` | Run3 v28(128): PET_ConflictAreaRadius_WaPlusWbHalf_Toggle | PET: รัศมีพื้นที่ขัดแย้ง = (Wa+Wb)/2 สลับได้ |

## 1.23.z — จัด CSV ใหม่ (ชื่อคอลัมน์ ไฟล์ล้ม ความเร็วต่อเฟรม)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.23.0** | `0d3c3bb` | Run3 v28(129): CSV_ErrorFileSeparate_GapColumnsRenamed | ตัวชี้วัดที่ล้มเขียนไฟล์ _ERROR.csv แยก + เปลี่ยนชื่อคอลัมน์ Gap |
| **PKT 1.23.1** | `ba09341` | Run3 v28(130): CSV_ConsistentColumnNames_TTCDetail_FrameSpeed_MovementCalibration | ชื่อคอลัมน์ CSV สม่ำเสมอ, TTC แบบละเอียด, ความเร็วต่อเฟรม, การปรับเทียบของ Movement |
| **PKT 1.23.2** | `8398f23` | Run3 v28(131): CSV_Cleanup_SpeedPerFrame_DropRedundantColumns_DetailFilesSwitch | ล้าง CSV: Speed ต่อเฟรม ตัดคอลัมน์ซ้ำ สวิตช์ไฟล์รายละเอียด |

## 1.24.z — PET: ชนิดความขัดแย้งตามกติกา TTC

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.24.0** | `2b1bcda` | Run3 v28(132): PET_ConflictType_ByTtcAngleRule | PET กำหนด Conflict_Type ด้วยมุมระหว่างความเร็วสองคัน ณ จุดตัด (เหมือน TTC) |
| **PKT 1.24.1** | `7cc87e3` | Chore: e2e_run3 follows v28(131) (speed per frame in Speed.csv, no Speed rows in Indicator_Summary) | แก้เทสต์ e2e ให้ตรง v28(131) (ความเร็วต่อเฟรมใน Speed.csv) |

## 1.25.z — เลขเวอร์ชัน PKT และ CHANGELOG

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.25.0** | `425cd6a` | PKT 1.25.0: Changelog_PKT_VersionNumbers_Tags | ตั้งกติกาเลขเวอร์ชัน PKT x.y.z, ทำตารางนี้, ติด tag `PKT-x.y.z` ให้ทุก commit ในตาราง |
| **PKT 1.25.1** | (ตัวรวม main ถูกเอาออกแล้ว tag ชี้ที่ 1.29.2) | PKT 1.25.1: Changelog_IncludesCloudSessionCommits_MergeMain | รวมงานของเซสชัน cloud (หัวข้อ 1.26–1.28) เข้าตาราง, ผู้ใช้ยืนยันใช้ PKT ตามของตน ทับการยกเลิก `PKT 1.78.0` |

| **PKT 1.29.2** | `e27a87f` | PKT 1.29.2: Changelog_HashesUpdatedAfterRename | เปลี่ยนชื่อ commit เก่าทั้งหมดเป็น `PKT x.y.z: ...` (เขียนประวัติ main ใหม่เฉพาะข้อความ เนื้อไฟล์เท่าเดิมทุกไบต์) และแก้ hash ในตารางให้ตรงของใหม่; ประวัติเดิมสำรองไว้ใน `_git_backup/` |

## 1.26.z — ลองตั้งชื่อ PKT 1.x.y ในเซสชัน cloud (ยกเลิกแล้ว — เลข 1.78.0 ไม่ใช้)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.26.0** | `52868d0` | PKT 1.78.0: VersionNaming_PKT_HistoryMap | ตาราง VERSION_HISTORY.md เลขแบบ 1.x.y (ถูกยกเลิก) |
| **PKT 1.26.1** | `b77d92b` | Docs: RevertPKTNaming_BackToRun3Names | ย้อนการตั้งชื่อ PKT ของเซสชัน cloud กลับเป็นชื่อ Run3 |

## 1.27.z — เอกสารที่มาของเกณฑ์ความเสี่ยง (สไลด์สัมมนา)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.27.0** | `855b4ac` | Docs: LdpRiskTableSource_CROW2009_SeminarSlide42 | เอกสาร: ที่มาตารางเกณฑ์ LDP (CROW 2009 สไลด์ 42) |
| **PKT 1.27.1** | `fb76b64` | Docs: SeminarSlides_TTC_PET_LDP_SourcesVerified | เอกสาร: ตรวจที่มาเกณฑ์ TTC/PET/LDP จากสไลด์สัมมนาแล้ว |

## 1.28.z — Gap Acceptance แบบแยกขั้นตามโซนกลาง + สรุปวิธี TTC ปัจจุบัน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.28.0** | `110ea1c` | Run3 v28(133): GapAcceptance_StagedPerMiddleZone | Gap Acceptance: ตัดสินแยกขั้นต่อโซนกลาง |
| **PKT 1.28.1** | `45771c4` | Docs: SpecTTC_CurrentMethodSummary_CleanOutdated | เอกสาร: สรุปวิธี TTC ปัจจุบัน ล้างข้อความที่ล้าสมัย |
| **PKT 1.28.2** | `c853e24` | Docs_PlanStatusUpdate_AfterPR4Merge | เอกสาร: อัปเดตสถานะใน plan.md หลังรวม PR #4 (งานค้าง: รอผลเทสต์จากเครื่องผู้ใช้) |
| **PKT 1.28.3** | `637ef3e` | Run3 v28(134): GapCsv_ReadablePrecision_CriticalGapQC | Gap CSV: เวลา/ช่องว่างทศนิยม 3 ตำแหน่ง; Critical_Gap เพิ่มจำนวนคนขับที่ถูกตัดออกและ QC_Flag |
| **PKT 1.28.4** | `90ecaf7` | Run3 v28(135): GapCsv_LeadLagNames_SpeedColumnTimeFix | Gap CSV: ชื่อคอลัมน์ Lead/Lag และแก้ชื่อความเร็วที่บอกเวลาผิด; Decision_Zone → Subject_Zone_At_Decision |

## 1.29.z — เรียงคอลัมน์ CSV ให้ผลหลักอยู่หน้า

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.29.0** | `fa78d31` | Run3 v28(136): CsvColumnOrder_ResultsFirst | TTC/PET/LDP: ตัวระบุ → ผลหลักและระดับความเสี่ยง → รายละเอียด → QC_Flag (ชื่อคอลัมน์ไม่เปลี่ยน) |
| **PKT 1.29.1** | `690a046` | PKT 1.29.1: Changelog_CloudCommits134to136 | เพิ่มงานเซสชัน cloud (v28(134)–(136)) เข้าตาราง ตั้งชื่อ commit แบบ PKT ต่อจากนี้ |

## 1.30.z — PET เลือกนับตามชนิดความขัดแย้ง + ไฟล์ Headway

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.30.0** | `d86d6d3` | PKT 1.30.0: PetExcludeRearEnd_HeadwayCsv | PET ตัดคู่ชนิด Rear-end (สวิตช์ `pet_exclude_rear_end`); ไฟล์ใหม่ `Headway.csv` (Time Headway, Time Gap ต่อ Movement); แยกฟังก์ชันหาเวลาข้ามเส้นของกระแสใช้ร่วมกับ Gap Acceptance |
| **PKT 1.30.1** | `d0cf56e` | PKT 1.30.1: HeadwayFromPetRearEnd_DropConsecutivePairs | **ยกเลิกใน 1.30.2** — เคยเปลี่ยน Headway.csv เป็นแถว PET ชนิด Rear-end |
| **PKT 1.30.2** | `a3783b4` | PKT 1.30.2: HeadwayBackToLineGaps_PetConflictTypeSwitches | Headway.csv กลับเป็นแบบเส้น Line/โซนต้นทางของแต่ละ Movement (เหมือน 1.30.0); PET มีสวิตช์เลือกนับต่อชนิด Rear-end / Lane change / Crossing (มุมเดียวกับ TTC) แทน `pet_exclude_rear_end` |
| **PKT 1.30.3** | `fcc0645` | PKT 1.30.3: TtcConflictTypeSwitches | TTC มีสวิตช์เลือกนับต่อชนิด TTC_Type (Rear-end / Lane change / Crossing, ค่าตั้งต้นเปิดทั้งสาม) เหมือน PET; ชนิดที่ปิดไม่ออกแถวและไม่วาดในวิดีโอ |
| **PKT 1.30.4** | `4abf2cb` | PKT 1.30.4: Changelog_LinearHistory_MergeCommitsRemoved | เอา Merge pull request (#1–#6) ออกจากประวัติ main ให้เป็นเส้นตรง (งานจริงทุก commit อยู่ครบ เนื้อไฟล์ล่าสุดเท่าเดิม) แก้ hash ในตารางและ tag ให้ตรงของใหม่; ประวัติก่อนแก้สำรองไว้ใน `_git_backup/` |
| **PKT 1.30.5** | `b352554` | PKT 1.30.5: Changelog_Renumber_1.25.2_to_1.29.2 | เปลี่ยนเลข 1.25.2 เป็น 1.29.2 ให้เรียงตามลำดับ commit (แก้ชื่อ commit + tag, แก้ hash ในตาราง) |
| **PKT 1.30.6** | `e92bdc1` | PKT 1.30.6: HeadwayOwnBox_FollowersOnly_LinePerMovement | Headway มีกรอบ/สวิตช์ของตัวเองในแท็บ ③; เลือก Movement และ Line ต่อ Movement ได้; จับเฉพาะรถที่ตามกัน (อยู่ในแนวทางวิ่งของคันหน้า ข้ามรถขนาน); Headway สูงสุดตั้งได้; คอลัมน์ `Lateral_To_Lead_Path_m` |

## 1.31.z — เส้นอ้างอิงจากขอบโซน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.31.0** | `43a49cc` | PKT 1.31.0: ReferenceLineFromSharedZoneEdge | เส้นอ้างอิงของ Gap Acceptance และ Headway = เส้นเชื่อมโหนดร่วมของสองโซนที่ติดกัน (1-3-4/1-3-6-7 = 1\|3, 2-3-1/2-3-4 = 2\|3, 5-6-7 = 5\|6, 5-6-3-1 = 3\|6) ไม่ต้องวาด; เลือก `ขอบโซน`/`Line ที่วาดไว้` ได้; เขียน `Edge a-b` ในช่อง Line ได้ |

## 1.32.z — Critical Gap แยกกลุ่มตามชนิดรถ

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.32.0** | `34b055c` | PKT 1.32.0: CriticalGapByVehicleClass_LowSampleFlag | Critical Gap แยกตามชนิดรถของคนที่รอ (เปิด/ปิด) และชนิดรถของคันหลังที่กำลังมา (เปิด/ปิด); คอลัมน์ `Lag_Vehicle_Class`; ธง `Few_Drivers_Below_N` เมื่อตัวอย่างน้อย (ตั้งค่า N ได้) |
| **PKT 1.32.1** | `f6acd99` | PKT 1.32.1: TrackingVideo_NoLeftoverTmpFile | วิดีโอ Tracking_Result ที่วาดกรอบ TTC/PET: ถ้าไฟล์ถูกเปิดค้างในเครื่องเล่น ลองแทนที่ซ้ำหลายครั้งก่อน, ลบไฟล์ชั่วคราว `Tracking_Result._ttc_tmp.mp4` ทิ้งเสมอ (รวมกรณีวาดผิดพลาด), บอกผลใน Summary.json (`ttc_boxes_video`) |

## 1.33.z — ความเร็วในการรัน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.33.0** | `030e123` | PKT 1.33.0: SpeedUps_PreviewOff_ScaledVideo_HwDecode_TensorRT_FastPairs | พรีวิวปิดเป็นค่าตั้งต้น; วิดีโอผลลัพธ์ย่อไม่เกิน 1920 px; ตัวเลือกถอดรหัสด้วยการ์ดจอและ TensorRT (ถอยกลับเอง); TTC/PET กรองคู่เร็วขึ้นโดยผลเหมือนเดิม |
| **PKT 1.33.1** | `030e123` | PKT 1.33.1: TensorRT_AutoInstallPackages | เปิด TensorRT แล้วไม่มีแพ็กเกจ `tensorrt` / `onnx` → ติดตั้งให้เองด้วย pip (Python ที่รันโปรแกรม) ก่อนสร้าง engine |
| **PKT 1.33.2** | `4249188` | PKT 1.33.2: PetMark_ShowAfterSecondVehicle_1s | กากบาท PET ในวิดีโอขึ้นเมื่อคันที่ 2 ถึงจุดตัด (ผลเกิดแล้ว) แสดง 1 วินาทีแล้วหาย (เดิมขึ้นตั้งแต่ 1 วินาทีก่อนคันแรกถึง อยู่ยาวจนรก) |

## 1.34.z — เส้นอ้างอิงและการแสดงผล (ชุดแก้ 10 ข้อ ของผู้ใช้ 2026-10-08)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.34.0** | `274f942` | PKT 1.34.0: RefLines_ShowSwitch_PerStreamEdgeOrDrawn | สวิตช์แสดง/ซ่อนเส้นอ้างอิงในวิดีโอปกติและ X–Y (แยกกัน, แสดงเฉพาะเส้นที่ใช้จริง) และหน้า "วาด Line…" เลือกทีละกระแสว่าใช้ขอบโซนหรือวาดเอง |

## 1.35.z — วิดีโอ X–Y บนภาพโดรน และเลือกบันทึกอิสระ 3 วิดีโอ

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.35.0** | `92ba536` | PKT 1.35.0: DroneBackgroundTopviewVideo_ThreeVideosChosenPerClip | วิดีโอที่ 3 `Tracking_Topview_Drone.mp4` (X–Y วางบนภาพโดรนของ Align) พร้อมสวิตช์แสดงผลของตัวเอง และเลือกบันทึกวิดีโอปกติ/X–Y/X–Y บนภาพโดรนแยกกันต่อคลิป |

## 1.36.z — สี่เหลี่ยมรถวางตามจุดอ้างอิง และ PET แบบสี่เหลี่ยม

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.36.0** | `1077e6d` | PKT 1.36.0: VehicleRectAtReferencePoint_PetAreaByRectangles | สี่เหลี่ยมรถของ TTC วางตามตำแหน่ง Trajectory Position (Bottom + Offset ฯลฯ) และ PET ใช้พื้นที่ขัดแย้งเป็นสี่เหลี่ยมรถแบบ TTC (เลือกวงกลมเดิมได้) |

## 1.37.z — ทำให้เส้นทางนิ่ง

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.37.0** | `83e9618` | PKT 1.37.0: TrajectorySmoothing_BoxDisplayEma_ZoneConfirmFrames | ทำให้ตำแหน่งรถนิ่งขึ้นก่อนคำนวณทุกตัวชี้วัด (ค่ากลาง 0.3 s), กรอบ/เส้นทางในวิดีโอนิ่งขึ้น (แสดงผลเท่านั้น), ตัวเลือกยืนยันโซนกี่เฟรม |

## 1.38.z — เลือกไฟล์ CSV ที่บันทึก

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.38.0** | `877bad7` | PKT 1.38.0: ChooseWhichResultCsvFilesToWrite | ติ๊กเลือกไฟล์ CSV ผลลัพธ์ของ Run 3 ทีละไฟล์ (สีเทาเมื่อตัวชี้วัดนั้นปิดอยู่) |

## 1.39.z — โปรเจกต์ (บันทึกทุกอย่าง)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.39.0** | `14b96b6` | PKT 1.39.0: ProjectSave_SettingsZonesAndClipList | บันทึก/เปิดโปรเจกต์: การตั้งค่าทั้งหมด + โซน/Line + รายการคลิป (วิดีโอ ช่วงเวลา ตัวเลือกบันทึก 3 วิดีโอ) |

## 1.40.z — จัดหน้าตาโปรแกรมใหม่

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.40.0** | `0a926b9` | PKT 1.40.0: UiRedesign_FiveTabs_IndicatorPages_FoldableGroups | 5 แท็บ, หน้าย่อยต่อตัวชี้วัด (● เปิด / ○ ปิด), กลุ่มย่อ/ขยายได้, ตารางวาดภาพ 3 วิดีโอพอดีจอ |
| **PKT 1.40.1** | `3a5d784` | PKT 1.40.1: TensorRt_CudaMatchingPackage_EngineBuiltInSeparateProcess | แก้ TensorRT เด้ง: ลงแพ็กเกจ tensorrt ให้ตรง CUDA ของ PyTorch (cu12 → 10.x), สร้าง engine ในโปรเซสแยก, .bat ไม่เปิดซ้ำเมื่อดับ |

## 1.41.z — เร่ง YOLO และการ์ดจอหลายค่าย

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.41.0** | `d547702` | PKT 1.41.0: TensorRtFp16_PerGpuEngineName_DirectMlBackendAnyGpu | TensorRT เป็น FP16 (เร็วขึ้นจริง 15.7→19.6 fps), engine แยกตามรุ่นการ์ด, ตัวเลือก GPU DirectML สำหรับ AMD/Intel/NVIDIA |
| **PKT 1.41.1** | `adb74b0` | PKT 1.41.1: ZoneEditor_EdgeLengthsInMetresOnPictures | เขียนความยาวขอบโซน (เมตร) บนภาพในหน้าต่างแก้รูปโซน (เปิด/ปิดได้) |

## 1.42.z — TTC และ PET ใช้จุดอย่างเดียว

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.42.0** | `d72942d` | PKT 1.42.0: TtcAndPet_PointOnly_AreaMethodsRemoved | ตัดวิธีสี่เหลี่ยมรถของ TTC และพื้นที่ขัดแย้งของ PET ออก เหลือจุดอย่างเดียว |
| **PKT 1.42.1** | `64941a9` | PKT 1.42.1: VehicleSizeDefaults_VanCommuter | ตรวจขนาดรถตั้งต้นกับข้อมูลรถในไทย แก้ Van เป็น 5.90 × 1.95 m |

## 1.43.z — TTC เลือกคู่ที่นับตามชนิดความขัดแย้ง

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.43.0** | `69c53a9` | PKT 1.43.0: TtcPairDecisionByConflictType_CrossingTimeAndRearEndException | TTC นับคู่ตามชนิดความขัดแย้ง (เส้นตัดกัน + ถึงจุดตัดใกล้กัน; ท้ายชนท้ายใช้ระยะด้านข้าง) เลือกแบบเดิม/ไม่มีเกณฑ์ได้ |
| **PKT 1.43.1** | `1062383` | PKT 1.43.1: TtcMinRecordValue_DropFramesBelow | เพิ่มค่าต่ำสุดของ TTC (`ttc_min_record_s`): เฟรมที่ TTC ต่ำกว่านี้ไม่นับ (สถานะ `Below_TTC_Min`) ตัดค่าที่ลงไปใกล้ 0 เพราะรถแค่ผ่านกัน คู่กับค่าสูงสุดเดิม |

## 1.44.z — วิดีโอผลลัพธ์ทำพร้อมกัน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.44.0** | `21d8b41` | PKT 1.44.0: PostRunVideosInParallel_BackgroundDecodeEncode | วิดีโอหลังรันตัวชี้วัด (Topview, Topview บนภาพโดรน, วาดเครื่องหมายทับ Tracking_Result) ทำพร้อมกันหลายเธรด + ถอดรหัส/เข้ารหัสในเธรดหลัง; R4: 140 s → 82 s |
| **PKT 1.44.1** | `b7b2607` | PKT 1.44.1: ResultVideoFpsAndSizeOptions | วิดีโอผลลัพธ์ปรับ fps ได้ (`video_fps`, `topview_fps`) และขนาดวิดีโอ X-Y/โดรนได้ (`topview_max_px`); ขนาดวิดีโอปกติเดิม `video_max_width` |

## 1.45.z — เลือกวิดีโอข้างทางในหน้าต่างวาด/จัดแนว

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.45.0** | `002fa27` | PKT 1.45.0: EditorWindowsChooseOtherVideo | หน้าต่างจัดแนวกับภาพโดรน (Align), แก้รูปโซน และวาด Line เปลี่ยนวิดีโอข้างทางที่ใช้เป็นภาพพื้นหลังได้ (เลือกจากรายการคลิปหรือไฟล์อื่น) |
| **PKT 1.45.1** | `cb22deb` | PKT 1.45.1: Docs_FolderMove_To_PK_Transport_Layout | ย้ายโฟลเดอร์ในเครื่องเป็น `PK-Transport\PKT-Analyze` (Run/Input/Output อยู่ข้างกันเหมือนเดิม), remote = PKT-Analyze; แก้ path ในเอกสารและคอมเมนต์ (ไม่เปลี่ยนพฤติกรรมโปรแกรม) |

## 1.46.z — เชื่อมกับ PK Transport

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.46.0** | `185d780` | PKT 1.46.0: DefaultModelFromPktModelPath | โมเดลตั้งต้นของโปรแกรมอ่านจากตัวแปรแวดล้อม `PKT_MODEL_PATH` (ตั้งโดยแอป PK Transport เมื่อผู้ใช้เลือกโมเดลที่เทรนแล้ว) ถ้าไฟล์มีอยู่; ไม่ตั้ง = `Input/Model/best.pt` เหมือนเดิม |
| **PKT 1.46.1** | `e9dc9fa` | PKT-Analyze 1.46.1: Docs_CommitMessageFormat | รูปแบบชื่อ commit เป็น `PKT-Analyze x.y.z: ...` (ชื่อ repo นำหน้า เหมือนทุก repo ของ PK Transport; tag ยังเป็น `PKT-x.y.z`) |
| **PKT-Analyze 1.46.2** | `c0d82eb` | PKT-Analyze 1.46.2: Docs_CommitNamesRenamed_HashesUpdated | ชื่อ commit ทั้งประวัติเปลี่ยนเป็น `PKT-Analyze x.y.z: ...` (61 commit เก่าที่นำเข้าจากไฟล์เวอร์ชันเก่า = `0.0.0`–`0.0.60` ชื่อเดิมอยู่ในหัวข้อ 0.0.z); เลข hash ทั้งหมดในเอกสารถูกแก้ตามประวัติใหม่ (tag ยังเป็น `PKT-x.y.z` เหมือนเดิม) |
| **PKT-Analyze 1.46.3** | `1b3492c` | PKT-Analyze 1.46.3: Docs_FixCountOfOldCommits | แก้เอกสาร: commit เก่าที่นำเข้าจากไฟล์เวอร์ชันเก่ามี 61 อัน (`0.0.0`–`0.0.60`) ไม่ใช่ 62 |
| **PKT-Analyze 1.47.0** | `abffe93` | PKT-Analyze 1.47.0: PKTransportModule | PKT Analyze เป็นโมดูลของ PK Transport: `pkt_module.json` + `pkt_plugin.py` (หน้าต่างหลัก `Run1App` ถูกสร้างในเฟรมของหน้าต่าง PK Transport, โหลดใน thread, ไม่ให้ PKStudio.py รีสตาร์ทด้วย Python อื่น, ส่งโมเดลจากแอปหลักเข้าช่อง Model, ถามก่อนปิดระหว่างวิเคราะห์) + `pkt_analyze_lang.py` (คำแปลอังกฤษของทุกข้อความ ใช้กับปุ่มสลับภาษา) + `requirements.txt`; โฟลเดอร์ Input/Output ตั้งต้นตามตัวแปร `PKT_USER_DATA` (นอกโฟลเดอร์โมดูล) ถ้าแอปหลักตั้งให้ — รันเดี่ยว ๆ ได้เหมือนเดิม (`python PKStudio.py`) |
| **PKT-Analyze 1.48.0** | `575544a` | PKT-Analyze 1.48.0: FasterRun1_LetterboxBesideGpu_DetectOnCleanFrame | Run 1 เร็วขึ้น: การย่อภาพเฟรม 1080p ให้เป็นขนาดของโมเดล (letterbox ของ Ultralytics ~4 ms ต่อเฟรม) ทำในเธรดที่อ่านวิดีโอ ขนานกับ GPU แทนที่จะรอในลูปหลัก (ภาพที่ส่งเข้าโมเดลเหมือนเดิมทุกบิต — Ultralytics สร้างเองด้วยฟังก์ชันเดิม); วัดจริงคลิป 1080p60 3600 เฟรม TensorRT FP16 บน GTX 1650: 131.9 → 123.4 วินาที (27.3 → 29.2 fps) ผล CSV ทุกไฟล์เหมือนเดิมทุกบรรทัด; แก้ด้วย: ชั้นโซนจาง ๆ ของวิดีโอผลลัพธ์วาดหลังจากโมเดลอ่านเฟรมแล้ว (เดิมวาดก่อน ทำให้ตอนบันทึกวิดีโอ YOLO เห็นเส้นโซนได้) |
| **PKT-Analyze 1.49.0** | `a06daa8` | PKT-Analyze 1.49.0: CombinedResultsPerDayFolder_ClipTable_CombineButton | ผลรวมหลายคลิปครบทุกชั้นโฟลเดอร์: นอกจาก `All_Clips` ในโฟลเดอร์ชั้นบนสุดที่นำเข้า ตอนนี้ทุกโฟลเดอร์ย่อยที่มีตั้งแต่ 2 คลิป (เช่นโฟลเดอร์ของแต่ละวัน) ได้ `All_Clips` ของตัวเองด้วย (ข้ามชั้นที่มีคลิปชุดเดียวกับชั้นบน); รวม `Indicator_Summary` และ `Zone_Summary` ของทุกคลิปด้วย; `All_Clips.csv` เป็นตารางรายคลิป (สถานะ เฟรม ความยาว จำนวนรถ จำนวนแถวของแต่ละตัวชี้วัด); ปุ่ม "รวมผลลัพธ์หลายคลิป…" ในแท็บ ① รวมผลที่วิเคราะห์ไว้แล้วโดยไม่ต้องรันใหม่; ผลรายคลิปเหมือนเดิม |
| **PKT-Analyze 1.50.0** | `1809a88` | PKT-Analyze 1.50.0: ResultFolderLayout_Numbered_Raw_Summary_SpeedPerZone | จัดไฟล์ผลลัพธ์ใหม่ตามที่ผู้ใช้เลือก: ผลวิเคราะห์ใส่เลข `1_ID_Zone` `2_Speed` `3_LDP` `4_Lateral_Clearance` `5_Gap_Acceptance`/`5_Critical_Gap` `6_Headway` `7_TTC` `8_PET`, ข้อมูลดิบ/ไฟล์ตรวจสอบใน `0_Raw/` (Detection_Records, Topview, Speed_Frames, LC samples, TTC detail/frames, Duplicate_Tracks), สรุป/ตั้งค่าใน `9_Summary/`; ระหว่างรันยังเขียนชื่อเดิมแล้ว `arrange_clip_folder` ย้ายเข้าที่เมื่อคลิปจบ (แก้พาธใน JSON ตาม) และ `result_file` หาเจอทั้งแบบใหม่และเก่า (ข้ามคลิปที่เสร็จแล้ว/รวมผล/ID ต่อเนื่องใช้ได้กับผลเก่า); **Speed รายคันรายโซน** ใหม่ `2_Speed.csv` (`speed_zone_summary`: Zone_Path, เวลาเข้า/ออก, Mean/Median/P85/Min/Max, ความเร็วตอนเข้า/ออก; เฟรมเกินค่าสูงสุดไม่นับ) + แถว Speed เฉลี่ยต่อโซนใน Indicator_Summary และสถิติรวม; `All_Clips` ใช้โครงสร้างเดียวกัน (`9_Summary/Clip_List.csv`, `9_Summary/Statistics.csv`) แทนไฟล์ `All_*.csv` เดิม |
| **PKT-Analyze 1.50.1** | `e325fe7` | PKT-Analyze 1.50.1: SpeedPerZone_LeavesOutStandingFrames | `2_Speed.csv` ไม่นำเฟรมที่รถจอด/หยุดรอ (ช้ากว่า 5 km/h — ค่าเดียวกับ "หยุด" ของ Gap Acceptance และความเร็วขั้นต่ำของ TTC) มาคิดความเร็ว เพราะกรอบของรถที่จอดกระพริบทำให้ความเร็วแกว่ง; เพิ่มคอลัมน์ `Moving_Frames`, `Stopped_Frames`, `Stopped_Time_s`; ช่วงที่จอดตลอด = ความเร็วว่าง + `QC_Flag` Stopped; ตั้งค่าได้ที่แท็บ Speed (`speed_stop_kmh`, 0 = ปิด); ผล R6: Zone 1 10.3→12.2, Zone 3 26.5→30.0, Zone 6 18.4→26.0 km/h (ค่าเฉลี่ยของค่าเฉลี่ยรายคัน) |
| **PKT-Analyze 1.51.0** | `ea5e543` | PKT-Analyze 1.51.0: UpgradeOlderResults_ToNewLayout_WithSpeedPerZone | ปุ่ม "รวมผลลัพธ์หลายคลิป…" จัดผลที่วิเคราะห์ด้วยเวอร์ชันก่อน 1.50.0 เป็นรูปแบบใหม่ก่อนรวม (`ClipListPanel.upgrade_results`): สร้าง `2_Speed.csv` จากความเร็วรายเฟรม (ตัดเฟรมรถจอดตามค่าที่ตั้ง) แล้วย้ายเข้า 1_…8_ / 0_Raw / 9_Summary โดยไม่วิเคราะห์ใหม่; `arrange_clip_folder` ย้ายไฟล์ชื่อแบบเก่า (`<คลิป>_LDP.csv`, `Run_3_LDP.csv`) ได้ด้วย; ใช้จัดผล R1–R6 ของผู้ใช้แล้ว |
| **PKT-Analyze 1.52.0** | `92e0cc8` | PKT-Analyze 1.52.0: BatchProgressWindow_ClipByClip | ตอนรันหลายคลิปมีหน้าต่าง "ความคืบหน้าการวิเคราะห์" ขึ้นเอง (`BatchProgressWindow`): บอกว่ากำลังทำคลิปที่เท่าไรจากทั้งหมด ชื่อคลิป กำลังทำขั้นตอนไหน (บรรทัดสถานะ) เฟรม/ความเร็ว/เวลาที่เหลือ เวลารวม แถบความคืบหน้า สรุป เสร็จ/ข้าม/ผิดพลาด/เหลือ และตารางหนึ่งแถวต่อคลิป (รอ / กำลังวิเคราะห์ / เสร็จ / ข้าม / ผิดพลาด / หยุด + เวลาที่ใช้ + หมายเหตุตัวชี้วัดว่าง); ปิดหน้าต่างได้ งานยังรันต่อ เปิดซ้ำด้วยปุ่ม "ดูความคืบหน้าทีละคลิป" ที่แถบล่าง; ข้อความสลับไทย/อังกฤษตามภาษาของ PK Transport (`tr_text`) |
| **PKT-Analyze 1.52.1** | `24b4034` | PKT-Analyze 1.52.1: TensorRTEngineName_AfterInstall_NoSecondBuild | แก้บั๊ก: ครั้งแรกที่ใช้ TensorRT โปรแกรมคิดชื่อไฟล์ `.engine` ก่อนติดตั้ง TensorRT จึงไม่มีเลขรุ่น (`..._trtx.engine`) แล้วรอบถัดไปคิดเป็น `..._trt10.engine` หาไฟล์ไม่เจอ และสร้างใหม่อีกรอบ (~10 นาที); ตอนนี้คิดชื่อใหม่หลังติดตั้งเสร็จ (`installed_tensorrt_version`) ได้ชื่อ `trt10` ตั้งแต่รอบแรก |
| **PKT-Analyze 1.52.2** | `e8fc63d` | PKT-Analyze 1.52.2: ETA_CountsFrameSkip_ProgressButtonVisible | แก้บั๊ก 2 ข้อ: (1) เมื่อใช้ Frame Skip (ข้ามเฟรม) เวลาที่เหลือ (ETA) แสดงนานเกินจริง N เท่า เพราะนำเฟรมที่เหลือทั้งหมดไปหารด้วยจำนวนเฟรมที่ตรวจจับต่อวินาที; ตอนนี้หารด้วยจำนวนเฟรมที่ข้ามด้วย (`eta_seconds`) — ตัวอย่าง: ข้ามเว้นเฟรมที่ 29.28 fps เหลือ 68,987 เฟรม เดิมแสดง 39:16 จริงราว 19:38; (2) ปุ่ม "ดูความคืบหน้าทีละคลิป" ถูกตัดหายไปนอกจอ (ต่อท้ายข้อความการ์ดจอที่ยาว) จึงเปิดหน้าต่างความคืบหน้ากลับมาหลังกดปิดไม่ได้ — ย้ายมาไว้หน้าข้อความการ์ดจอ |
| **PKT-Analyze 1.53.0** | `16d05b9` | PKT-Analyze 1.53.0: OneButton_AlignAndZoneEditor | หน้า ② เหลือปุ่มเดียว "🧭 จัดแนวและแก้โซน…" แทน "จัดแนว…" + "แก้รูปโซนบนภาพโดรน…" (`open_align_and_zones`): ถ้ายังไม่เคยจัดแนวเปิดหน้าจัดแนวก่อน — มีปุ่มใหม่ "ใช้ค่านี้ แล้วแก้โซน ▶" ต่อเข้าตัวแก้โซนทันที; ถ้ามีผลจัดแนวแล้วเปิดตัวแก้โซนเลย และมีปุ่ม "◀ แก้คู่จุดจัดแนว…" กลับไปหน้าจัดแนว (ถามก่อนถ้ามีมุมโซนที่ลากไว้แต่ยังไม่บันทึก); **วิธีคำนวณเมตรไม่เปลี่ยน** ผลวิเคราะห์เหมือนเดิมทุกค่า (ขั้น 1 ของการรวม; ขั้น 2 = ระยะจริงระหว่างโหนดแทน PPM/Perspective ยังไม่ทำ) |
| **PKT-Analyze 1.54.0** | `d7ccb57` | PKT-Analyze 1.54.0: RealEdgeLengths_FitAlignScale | ตัวแก้โซนมีตาราง "ระยะจริงของขอบ (ใส่เฉพาะที่รู้)": ทุกขอบของโซน (ขอบที่โซนข้างเคียงใช้ร่วมกันนับเป็นขอบเดียว) แสดงความยาวที่วัดได้จากผลจัดแนว; ดับเบิลคลิกแถวเพื่อใส่ระยะจริง (เมตร) — เว้นว่าง/ไม่รู้ได้; ตารางบอกส่วนต่างเป็น % และปุ่ม "ปรับสเกลตามระยะจริง" ปรับสเกลภาพโดรนตามค่าที่พอดีที่สุด (กำลังสองน้อยสุด `edge_scale_factor`) — **ถามก่อนทุกครั้ง** เพราะระยะ/ความเร็ว/ตัวชี้วัดทุกตัวเปลี่ยนตาม; ระยะจริงเก็บใน Align ที่บันทึก (`edge_lengths`) และไม่หายเมื่อบันทึก Align ใหม่; ไม่ใส่ = ผลเหมือนเดิมทุกค่า; PPM/Perspective แบบเดิมยังอยู่ (สำรองเมื่อไม่ใช้ผลจัดแนว) |
| **PKT-Analyze 1.55.0** | `b3d2b51` | PKT-Analyze 1.55.0: DrawZonesAndLines_InAnalyze | สร้างโซนและเส้นในโปรแกรม Analyze ได้เลย ไม่ต้องไปทำไฟล์โซนใน PKT Data ก่อน: หน้าต่างใหม่ "วาดโซนและเส้น" (`ZoneLineEditor`, ปุ่ม "✏️ วาดโซนและเส้น…" ในหน้า ② และปุ่มเดียว "จัดแนวและแก้โซน…" เมื่อยังไม่มีโซน) — เลือก Zone 1–7 ในรายการแล้วคลิกมุมทีละมุมบนเฟรมของวิดีโอ (เลือกเฟรมได้) มุมที่ใกล้มุม/ขอบของโซนอื่นดูดติด โซนข้างเคียงจึงใช้มุมร่วมกัน (ลากมุมร่วมแล้วขยับทุกโซนพร้อมกัน), ปิดโซนด้วย Enter หรือคลิกมุมแรกซ้ำ, ลบมุม, ย้อน/ทำซ้ำ; วาดเส้น Line 1–6 (คลิก 2 จุด ลากปลายได้); เปิดไฟล์โซนเดิม (จาก PKT Data) มาดู/แก้ได้; "ใช้โซนและเส้นนี้" เขียนไฟล์โซนรูปแบบเดียวกับ PKT Data ลงโฟลเดอร์ข้อมูลของโปรแกรม (`user_data/PKT-Analyze/Zones/<ชื่อวิดีโอ>_zones.json`) แล้วโหลดเป็นไฟล์โซนทันที — **ไม่เขียนลงโฟลเดอร์วิดีโอ** และไม่ทับไฟล์ที่ทำจากที่อื่น (สร้างไฟล์ใหม่ เก็บส่วนอื่น สี ป้ายของไฟล์เดิมไว้); ปุ่ม "ใช้โซนและเส้นนี้ แล้วจัดแนวต่อ ▶" ต่อเข้าหน้าจัดแนว (มุมโซนเป็นหมุด) |
| **PKT-Analyze 1.55.1** | `12cbbdd` | PKT-Analyze 1.55.1: PpmPerspective_FoldedAsFallback | หน้า ② กลุ่ม "แปลงพิกัดภาพเป็นเมตร" เหลือ Site_ID + ปุ่มจัดแนว (หลัก); ช่อง PPM, Road direction angle และ Perspective (P1–P4 กับระยะจริง 4 ด้าน) ย้ายไปกลุ่ม "สำรอง: PPM / Perspective" ที่พับไว้ตั้งแต่เริ่ม ใช้เมื่อไม่มีภาพโดรนหรือไม่ได้ติ๊กใช้ผลจัดแนว — **ไม่ลบโค้ด/ค่าเดิม** ผลวิเคราะห์เหมือนเดิมทุกค่า โปรเจกต์เก่ายังโหลดค่าเดิมได้ |
| **PKT-Analyze 1.56.0** | `994eaab` | PKT-Analyze 1.56.0: AlignInsideZoneWindow_NoSeparateAlign | **ไม่มีหน้าต่างจัดแนวแยกแล้ว** — จัดแนวกับภาพโดรนทำในหน้าต่าง "จัดแนวและแก้โซน" (วิดีโอ | โดรน | ผัง X–Y) หน้าต่างเดียว: โหมด "จัดแนว" ไล่มุมโซน (โหนดร่วมของโซนข้างเคียงนับเป็นมุมเดียว) ทีละมุมให้คลิกตำแหน่งเดียวกันบนภาพโดรน ข้ามมุมที่ไม่ชัดได้ (◀ ▶ เลือกมุม, คลิกมุมที่ใส่แล้วเพื่อวางใหม่), คลิกจุดว่างบนวิดีโอ = เพิ่มจุดเสริม, เลือกชนิดการแปลง, ลบคู่ล่าสุด/ลบคู่ที่แย่สุด (เลือกคู่ที่ตัดแล้วผลจัดแนวดีขึ้นที่สุด), เลือกภาพ/วิดีโอโดรนในหน้าต่างเอง; พอได้คู่พอ ภาพโดรนและผัง X–Y ขึ้นเอง; **สเกลมาจากระยะจริงของขอบที่รู้** (ใส่ขอบเดียวก็พอ แล้วกด ปรับสเกลตามระยะจริง ตั้งสเกลให้เลย ไม่ถามเพราะยังไม่มีค่าเดิม) หรือพิมพ์สเกลเอง; บันทึกในผลจัดแนวเดิม (รูปแบบเดียวกับหน้าจัดแนวเดิม เปิดต่อกันได้) และบอกให้การวิเคราะห์ใช้เมื่อพอดีและตั้งสเกลแล้ว; ปุ่ม "จัดแนวและแก้โซน…" และ "ใช้โซนและเส้นนี้ แล้วจัดแนวต่อ ▶" เปิดหน้าต่างนี้ (ไม่มีโซน → วาดโซนก่อน); คลาส `AlignDialog` ยังอยู่ในโค้ด แต่เมนูไม่เปิดแล้ว; ตอนยังไม่จัดแนวไม่แสดงความยาวขอบเป็นเมตร |
| **PKT-Analyze 1.57.0** | `464165d` | PKT-Analyze 1.57.0: SiteStudio_OneWindow_PinsLockVideoAndDrone | **หน้าต่างเดียว "ตั้งค่าทางแยก"** (`SiteStudio`) แทนเครื่องมือที่กระจายอยู่ (วาดโซนและเส้น / วาด Line Gap / จัดแนว / แก้โซน): หน้า ② เหลือปุ่มเดียว; **มุมโซนเป็นหมุดที่ล็อกคู่ วิดีโอ↔โดรน** — ลากบนวิดีโอย้ายเฉพาะฝั่งวิดีโอ ลากบนโดรนย้ายเฉพาะฝั่งโดรน (ผลจัดแนวคำนวณใหม่จากหมุดทุกครั้ง) ไม่ต้องจัดซ้ำสองรอบ; วาดโซน Zone 1–7 บนวิดีโอ (ดูดติดมุม/ขอบ มุมร่วมของโซนข้างเคียงเป็นหมุดเดียว) แล้วคลิกตำแหน่งเดียวกันบนโดรนเพื่อวางหมุด (ข้าม/ยกหมุดออก/ลบหมุดที่แย่สุด); ย้ายมุมในผัง X–Y และ "ทำให้ตั้งฉาก" = ย้ายมุมบนพื้นจริง ทั้งสองฝั่งของหมุดขยับตามและผลจัดแนวไม่เปลี่ยน; แท็บ "เส้น Gap": แต่ละกระแสใช้ขอบที่โซนติดกัน (ไม่ต้องวาด) หรือวาด Line เองบนวิดีโอ แล้วเติม Reference Line Mapping ให้; แท็บ "จัดแนวและระยะจริง": ชนิดการแปลง สเกลจากระยะจริงของขอบที่รู้ ความคลาด; "ใช้ในการวิเคราะห์" เขียนไฟล์โซนลงโฟลเดอร์ข้อมูลของโปรแกรม (ไม่เขียนลงโฟลเดอร์วิดีโอ) + บันทึกผลจัดแนว + เติมเส้น; อ่านผลจัดแนวรูปแบบเดิมได้; คลาสเดิม (`ZoneLineEditor`, `ZoneAlignEditor`, `AlignDialog`, `LineEditorDialog`) ยังอยู่ในโค้ดแต่ไม่มีทางเปิดจากเมนูแล้ว |
| **PKT-Analyze 1.57.1** | `46e4c0f` | PKT-Analyze 1.57.1: SiteStudio_TwoPictures_GhostCorners_NoExtraPins | แก้หน้าต่าง "ตั้งค่าทางแยก" ตามที่ผู้ใช้เห็นกับข้อมูลจริง: (1) **ไม่มีจุดเสริม P17/P21…** — คู่จุดที่ไม่ใช่มุมโซนในผลจัดแนวเก่าไม่ถูกนำเข้าแล้ว ใช้เฉพาะหมุดมุมโซน; (2) **โซนในภาพโดรนไม่หาย** — มุมที่ยังไม่วางหมุดแสดงที่ตำแหน่งที่ผลจัดแนวคาด (วงกลมเหลือง) โซนครบรูป และลากมุมนั้นไปวางเพื่อล็อกหมุดได้; ลากมุมที่ยังไม่วางหมุดบนวิดีโอ ตำแหน่งบนโดรนตามไปด้วย; (3) **อ่านผลจัดแนวเก่าได้ถูกต้อง** — มุมโซนที่ถูกแก้หลังจัดแนวใช้การแปลงเดิมหาตำแหน่งใหม่บนโดรน (เดิมคลาด 463 ซม. เพราะเอาตำแหน่งใหม่ไปคู่กับตำแหน่งโดรนเก่า); (4) **แสดงเฉพาะวิดีโอกับโดรน** ใหญ่ เลื่อน/ซูมได้ ส่วนผัง X–Y ติ๊ก "แสดง" เปิดได้ (ติ๊กปิด/เปิดแต่ละภาพได้ อย่างน้อยเหลือหนึ่งภาพ); ล้างโซน/ลบมุม = หมุดของมุมนั้นหายด้วย |
| **PKT-Analyze 1.57.2** | `dde5778` | PKT-Analyze 1.57.2: SiteStudio_ZonesShownFromFirstPin_RealLengthsKept | แก้ "ตั้งค่าทางแยก" ตามที่ผู้ใช้ลองกับข้อมูลจริง: (1) **โซนขึ้นบนภาพโดรนและผัง X–Y ตั้งแต่ยังไม่มีหมุด** — การจัดแนวโตตามจำนวนหมุด (0 หมุด = เกลี่ยโซนไว้กลางภาพโดรน, 1 = เลื่อนไปตามหมุด, 2 = ย้าย+หมุน+ย่อขยาย, 3 = ยืดเอียง, 4 = แก้มุมกล้อง, ครบตามชนิดที่เลือก = ชนิดนั้น) จึงเห็นรูปโซนทั้งสองภาพเสมอ แม่นขึ้นทุกครั้งที่วางหมุด และลากมุมในโดรนเพื่อวางหมุดได้ตลอด (ข้อความบอกว่าเป็นค่าประมาณจนกว่าหมุดจะพอ); (2) **ระยะจริงของขอบไม่หาย** — เดิมปุ่มย้อนย้อนระยะจริงไปด้วย และระยะที่ใส่ก่อนมีหมุดไม่ถูกบันทึก: ตอนนี้ระยะจริงไม่อยู่ในประวัติย้อน/ทำซ้ำ และบันทึกในโปรเจกต์ทันทีแม้ยังไม่มีหมุด (เปิดใหม่ยังอยู่); (3) ผัง X–Y ก่อนตั้งสเกลมีขอบเผื่อตามขนาด (ไม่ตัดมุมที่ขอบ) |
| **PKT-Analyze 1.58.0** | `3c6ba13` | PKT-Analyze 1.58.0: DiskLostDetected_WaitAndContinue | **ฮาร์ดดิสก์หลุดระหว่างวิเคราะห์**: (1) โปรแกรมแยกได้ว่าคลิปจบแบบไหน — `completed` (อ่านวิดีโอถึงท้าย), `stopped` (ผู้ใช้กด STOP), `interrupted` (วิดีโออ่านต่อไม่ได้ก่อนถึงท้าย เช่นดิสก์หลุด; เทียบเฟรมที่อ่านได้กับเฟรมที่ควรมี ≥97%) บันทึกใน `Run_Summary.json` (`status`, `stop_reason`, `input`); (2) ตอนอ่านวิดีโอค้าง (เกิน 10 วินาที) จะตรวจว่าไฟล์ยังเข้าถึงได้ไหม ไม่ค้างตลอดไป; (3) โหมดหลายคลิป: ถ้าดิสก์หลุด โปรแกรม **รอจนวิดีโอและโฟลเดอร์ผลลัพธ์กลับมา แล้วทำคลิปนั้นใหม่เองตั้งแต่ต้น** (กด STOP เพื่อเลิกรอ) หน้าต่างความคืบหน้าขึ้น "ฮาร์ดดิสก์หลุด"; (4) คลิปที่ถูกหยุดหรือถูกตัดกลางคันไม่ถูกนับว่าเสร็จ — ครั้งหน้าที่ติ๊ก "ข้ามคลิปที่เสร็จแล้ว" จะทำเฉพาะคลิปที่ยังไม่เสร็จ; (5) คลิปที่ถูกตัดไม่ทำ Run 3 บนข้อมูลบางส่วน. ข้อจำกัด: ทำต่อระดับคลิป (คลิปที่หลุดเริ่มใหม่จากต้นคลิป) |
| **PKT-Analyze 1.58.1** | (commit นี้) | PKT-Analyze 1.58.1: DiskLost_AutoPauseAndResumeSameFrame | ตามแนวคิดของผู้ใช้: **ดิสก์หลุดแล้วโปรแกรม PAUSE เอง** (ปุ่มเป็น ▶ RESUME, สถานะบอกเฟรมที่หยุดและเวลารอ) เมื่อวิดีโอกลับมา (นิ่งแล้ว) หรือกด RESUME ก็เปิดวิดีโอใหม่ที่เฟรมเดิมแล้ววิเคราะห์ต่อ **จากเฟรมที่หลุด ไม่ต้องเริ่มคลิปใหม่** (กด STOP = หยุดจริง). ใช้เมื่อโฟลเดอร์ผลลัพธ์ยังอยู่ (เช่นผลลัพธ์อยู่คนละดิสก์กับวิดีโอ); ถ้าผลลัพธ์หลุดด้วย (ไฟล์ที่เปิดเขียนอยู่ใช้ต่อไม่ได้) ยังใช้วิธีเดิมของ 1.58.0 คือรอแล้วทำคลิปนั้นใหม่ตั้งแต่ต้น. `Run_Summary.json` → `input.disk_pauses` = จำนวนครั้งที่หยุดรอดิสก์ |
| **PKT-Analyze 1.58.2** | `f28d910` | PKT-Analyze 1.58.2: DiskLost_PauseAndWaitForResume | ตามที่ผู้ใช้เสนอ: ดิสก์หลุดแล้วโปรแกรม **PAUSE ค้างไว้ ผู้ใช้เป็นคนกด RESUME เอง** (ไม่ทำต่อเองอัตโนมัติอีก) เมื่อต่อดิสก์ใหม่แล้วสถานะบอก "ฮาร์ดดิสก์กลับมาแล้ว — กด RESUME"; กด RESUME ตอนดิสก์ยังไม่กลับมา = ยังหยุดค้างต่อ; ถ้าวิดีโอกลับมา ทำต่อจากเฟรมเดิม. กรณีผลลัพธ์หลุดด้วย (อยู่ดิสก์เดียวกัน) ก็หยุดค้างแบบเดียวกัน แต่หลังกด RESUME ต้องทำคลิปนั้นใหม่ตั้งแต่ต้น |
| **PKT-Analyze 1.58.3** | `4889a1e` | PKT-Analyze 1.58.3: SiteStudio_ScaleFromEdgeLengths | ตามที่ผู้ใช้ขอ: **สเกลภาพโดรนคำนวณเองจากระยะจริงของขอบโซน** — ใส่ระยะจริงของขอบที่รู้ในตาราง (ดับเบิลคลิกแถว) สเกลเปลี่ยนทันทีและเติมลงช่องให้เอง ไม่ต้องกดปุ่ม "ปรับสเกลตามระยะจริง" (เอาปุ่มออก); ใส่หลายขอบ = ค่าที่พอดีที่สุดโดยเฉลี่ย; แก้ระยะ/เลื่อนหมุด สเกลตามใหม่; ล้างระยะจริงจนไม่เหลือ สเกลคงค่าที่คำนวณไว้; ช่องสเกลยังพิมพ์เองได้เมื่อไม่ได้ใส่ระยะขอบ |
| **PKT-Analyze 1.58.4** | `67e7d1b` | PKT-Analyze 1.58.4: SiteStudio_PickedEdgeHighlighted | คลิกแถวในตารางระยะจริงของขอบ → ขอบนั้นถูกไฮไลต์บนภาพวิดีโอ ภาพโดรน และผัง X–Y (แถบขาวแกนแดง วงแหวนที่มุมสองข้าง ป้ายชื่อขอบ + ความยาว) จะได้รู้ว่าแถวนั้นคือเส้นไหน; แถวที่เลือกอยู่คงเดิมแม้ตารางสร้างใหม่; ยกเลิกเลือก = ไฮไลต์หาย |
| **PKT-Analyze 1.58.5** | `0b78d0a` | PKT-Analyze 1.58.5: SiteStudio_HighlightClearsOnOutsideClick | ไฮไลต์ขอบที่เลือกในตาราง: (1) คลิกที่ใดก็ได้นอกตาราง (ภาพ แท็บอื่น ปุ่ม) → ไฮไลต์และแถวที่เลือกหายไป; (2) คลิกแถวที่เลือกค้างอยู่แล้ว → ไฮไลต์ขึ้นอีก (เดิมแถวเลือกอยู่แต่ไม่มีไฮไลต์ เพราะการคลิกแถวเดิมไม่ส่งเหตุการณ์เลือก) |
| **PKT-Analyze 1.59.0** | (commit นี้) | PKT-Analyze 1.59.0: SiteTypes_FourLegJunction_Zone8 | **ประเภทหน้างาน + สี่แยก (Zone 8)**: (1) เลือกประเภทหน้างานได้ในหน้าตั้งค่าทางแยก (แท็บ โซนและหมุด) และในตั้งค่า ② ทางแยก — สามแยกเล็ก (Zone 1–4), สามแยกเต็ม (Zone 1–7, ค่าเริ่มต้น = ผลเดิมทุกอย่าง), สี่แยก (Zone 1–8) และช่องติ๊ก "มีเกาะกลาง" (คิดเป็นสามแยก 2 แห่ง Zone 1–4 และ 5–8); (2) Zone 8 = ซอยฝั่งตรงข้าม Zone 1 (สะท้อน 1↔8, 2↔5, 3↔6, 4↔7) เส้นทางใหม่ 5 แบบ 8-6-7, 5-6-8, 8-6-3-4, 1-3-6-8, 8-6-3-1; (3) Gap Acceptance ของ Zone 8 รอช่องว่างตามที่ผู้ใช้ยืนยัน (8-6-7 รอ 5-6-7; 8-6-3-4 รอ 5-6-7, 2-3-4, 2-3-1; 1-3-6-8 และ 8-6-3-1 รอ 2-3-4, 5-6-7 และกระแสตรงข้ามกัน); (4) มีเกาะกลาง = ไม่คิดเส้นทางที่ข้ามเกาะ (1-3-6-7, 1-3-6-8, 8-6-3-4, 8-6-3-1, 5-6-3-1): คิดเฉพาะ 2-3-4, 2-3-1, 1-3-4 และ 5-6-7, 5-6-8, 8-6-7 (แยกที่ 2 เป็นภาพสะท้อนของแยกที่ 1); (5) การจัดประเภทเส้นทาง (classify_movement) ดูเฉพาะเส้นทางของประเภทหน้างานนั้น — สามแยกจึงไม่รู้จัก Zone 8 และผลเดิมไม่เปลี่ยน; (6) แท็บ เส้น Gap แสดงกระแสที่ต้องมีเส้นตามประเภท (เปลี่ยนประเภท กล่องเปลี่ยนตาม, Line 1–8); (7) ค่าบันทึกในโปรเจกต์ (site_type) โปรเจกต์เก่าเปิดเป็นสามแยกเต็ม; Zone 8 ติ๊กความเร็ว/Lateral Clearance เริ่มต้น และ LDP ล็อก Zone 8 เหมือน Zone 1; Summary.json บอก site_type |
