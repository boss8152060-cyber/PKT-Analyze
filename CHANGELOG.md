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
- เวอร์ชันถัดไป: งานต่อเรื่องเดิม = `1.33.3`; เรื่องใหม่ = `1.34.0` (เลขเรียงตามหัวข้อ ไม่ใช่เวลาเสมอไป — หัวข้อ 1.25 ทำหลังหัวข้อ 1.26–1.28 ของเซสชัน cloud)


## 0.1.z — เอกสารโปรเจ็คและกติกา git (ก่อนชุด v27)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 0.1.0** | `e5551a1` | Docs: ProjectOverview_Plan_GitRules_Gitignore | เอกสารภาพรวมโปรเจ็ค, แผนงาน, กติกา git, .gitignore |
| **PKT 0.1.1** | `3454454` | Docs: PlanUpdate_RemoteOriginPushed | อัปเดตแผน: ตั้ง remote origin และ push แล้ว |

## 0.2.z — แก้ย่อยชุด v27

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 0.2.0** | `c34a553` | Run3 v27(1): ZoneSummary_ExitTimeFix | แก้เวลาออกของ Zone Summary |
| **PKT 0.2.1** | `1d9e14a` | Run3 v27(2): ZoneFlicker_SummaryCleanup | ล้างการแกว่งเข้าออกขอบโซนใน Summary |
| **PKT 0.2.2** | `a151434` | Run3 v27(3): Preflight_ZoneNotDefinedWarning | เตือนก่อนรันเมื่อยังไม่มีโซน |
| **PKT 0.2.3** | `96d8326` | Run3 v27(4): Preflight_GapMappingWarning | เตือนก่อนรันเมื่อ Gap ไม่มี Line mapping |
| **PKT 0.2.4** | `69a307b` | Docs: PlanAdd_LineEditor_GapCrossingDedupe | เอกสาร: เพิ่มแผนหน้าต่างวาด Line และการตัดซ้ำของ Gap |

## 0.3.z — เอกสารสเปกตัวชี้วัดชุดใหม่ (v28)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 0.3.0** | `4d1fa07` | Docs: SpecV28_NewIndicators_PlanPhaseV | เขียน SPEC v28 และแผนระยะที่ 5 |
| **PKT 0.3.1** | `7b97302` | Docs: SpecV28_AnswersRecorded | บันทึกคำตอบของผู้ใช้ลงสเปก |

## 1.1.z — ตัวชี้วัดชุดใหม่ + Movement (LDP, Lateral Clearance, PET, TTC, Gap, Speed)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.1.0** | `2e7bf5a` | Run3 v28(1): MovementSequence_LaneWidthInputs | Movement จากลำดับโซน + ช่องกรอกความกว้างเลน |
| **PKT 1.1.1** | `2ce0a15` | Docs: SpecV28_NewIndicatorCodes_Y1toY6 | เอกสาร: ตั้งรหัสตัวชี้วัด (ภายหลังเลิกใช้) |
| **PKT 1.1.2** | `cd313e2` | Run3 v28(2): Y6Speed_ZoneAndMovement | Speed ต่อโซนและต่อ Movement |
| **PKT 1.1.3** | `fe2e0d3` | Run3 v28(3): Y1LDP_ChordReference | LDP แบบเส้นอ้างอิงจุดเข้า-ออกโซน |
| **PKT 1.1.4** | `f17581d` | Run3 v28(4): Y2LateralClearance_HeadingPerpendicular | Lateral Clearance ตั้งฉากกับทิศวิ่ง + กรอบซ้อนกัน |
| **PKT 1.1.5** | `f0839ad` | Run3 v28(5): Y5PET_Y4TTC_Zones3and6_SideCollision | PET และ TTC ในโซน 3, 6 + ชนด้านข้าง |
| **PKT 1.1.6** | `4ea06f5` | Run3 v28(6): Y3Gap_FirstCrossingOnly_V28Finalize | Gap Acceptance ข้ามเส้นครั้งแรกเท่านั้น |
| **PKT 1.1.7** | `b73c9aa` | Run3 v28(7): IndicatorNamesInsteadOfYCodes | เรียกตัวชี้วัดด้วยชื่อ ไม่ใช้รหัส Y1–Y6 |
| **PKT 1.1.8** | `b00032b` | Run3 v28(8): UserAnswers_GapTable_LDPAllClasses_TTCSideAdjustable_LCAllPairs | ตามคำตอบผู้ใช้: ตาราง Gap, LDP ทุกชนิดรถ, TTC ด้านข้างปรับได้, LC ทุกคู่ |
| **PKT 1.1.9** | `ef74ab3` | Run3 v28(9): LDP_DivideByHalfWidth | LDP หารด้วยครึ่งความกว้างเลน |

## 1.2.z — Line และ Reference Line Mapping

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.2.0** | `0501549` | Run3 v28(10): LineEditor_DrawReferenceLines | หน้าต่างวาด Line อ้างอิง |
| **PKT 1.2.1** | `9ec71a2` | Run3 v28(11): ReferenceLineMapping_PrefilledSite8 | Reference Line Mapping ตั้งไว้ให้ Site 8 |

## 1.3.z — ไฟล์โซนและการรันด้วย GPU (CUDA)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.3.0** | `ae12f21` | Docs: ZoneFileDJI0426_VideoFacts | เอกสาร: ข้อเท็จจริงของวิดีโอที่ใช้กับไฟล์โซน DJI_0426 |
| **PKT 1.3.1** | `105b30a` | Run3 v28(12): CUDA_PythonFallback_LauncherBat | ถอยไปใช้ Python ที่มี CUDA อัตโนมัติ + ไฟล์ .bat เปิดโปรแกรม |
| **PKT 1.3.2** | `68755a1` | Docs: CUDA_Python312_Launcher | เอกสาร: ตั้ง Python 3.12 + CUDA |

## 1.4.z — กรองข้อมูลและบอกสาเหตุผลว่าง

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.4.0** | `2dcbeda` | Run3 v28(13): DuplicateTrackFilter | ตัดแทร็กซ้ำ (รถคันเดียวสองไอดี) |
| **PKT 1.4.1** | `758745a` | Run3 v28(14): ExplainEmptyOutputs_ZoneVideoMismatchWarning | อธิบายสาเหตุที่ผลลัพธ์ว่าง + เตือนโซนไม่ตรงวิดีโอ |
| **PKT 1.4.2** | `26adf50` | Run3 v28(15): MovementFirstVisitFallback | Movement: ถอยไปใช้การเข้าโซนครั้งแรกเมื่อลำดับไม่ครบ |

## 1.5.z — Gap Acceptance แบบ PASS (สองขั้น)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.5.0** | `cb6010c` | Docs: GapAcceptance_PASSDesign_WaitZones1356 | เอกสาร: ออกแบบ Gap แบบ PASS โซนรอ 1, 3, 5, 6 |
| **PKT 1.5.1** | `b8e3be2` | Run3 v28(16): GapAcceptance_TwoStagePASS_LineOptional | Gap สองขั้น (เข้า/ออก) ตรรกะ PASS, Line เป็นตัวเลือก |
| **PKT 1.5.2** | `1f4991c` | Run3 v28(17): ZoneRemap_OldZoneFileWorksWithNewMovements | แปลงไฟล์โซนเก่าให้ใช้กับ Movement ใหม่ (ภายหลังถูกถอย) |
| **PKT 1.5.3** | `1413947` | Run3 v28(18): RevertToV28_13 | ย้อนไป v28(13) |
| **PKT 1.5.4** | `ac75723` | Run3 v28(19): RestoreV28_16_WithoutZoneRemap | คืน v28(16) โดยไม่มีการแปลงโซน |

## 1.6.z — ความถูกต้องของ CSV และพื้นฐาน UI

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.6.0** | `72064e9` | Run3 v28(20): ExcelSafeMovementArrows | เขียน Movement เป็นลูกศร กัน Excel แปลงเป็นวันที่ |
| **PKT 1.6.1** | `091330e` | Run3 v28(21): FP16KeyByVersion_TimestampStartsAtZero | คีย์ FP16 ตามเวอร์ชัน + เวลาเริ่มที่ 0 |
| **PKT 1.6.2** | `5539a3f` | Run3 v28(22): SpeedOutlierFlag_LC_PET_Stats_UntrackedCount | ธง Speed ผิดปกติ, สถิติ LC/PET, นับรถที่ไม่ได้ติดตาม |
| **PKT 1.6.3** | `f03b069` | Run3 v28(23): MergeClips_SensitivityTool_ParametersDoc | เครื่องมือรวมคลิป, วิเคราะห์ความไว, เอกสารค่าพารามิเตอร์ |
| **PKT 1.6.4** | `24c33bf` | Docs: Phase3_UserDeferredRiskRuleSensitivityTracking | เอกสาร: ระยะที่ 3 เรื่องที่ผู้ใช้เลื่อนไว้ |
| **PKT 1.6.5** | `6b6ff1a` | Run3 v28(24): UiQueue_RelativeDefaultPaths_NoAutoDelete_Logging | คิวเธรดของ UI, พาธเริ่มต้นแบบสัมพัทธ์, ไม่ลบไฟล์เอง, log |
| **PKT 1.6.6** | `978e62e` | Docs: PlanCleanup_RemoveUserPendingItems | เอกสาร: จัดแผนใหม่ เอารายการรอผู้ใช้ออก |
| **PKT 1.6.7** | `6c67780` | Docs: RemovePlan_4.4_4.5 | เอกสาร: ตัดหัวข้อ 4.4–4.5 ออกจากแผน |
| **PKT 1.6.8** | `b2039f2` | Docs: PlanFix_4.2_Note | เอกสาร: แก้หมายเหตุข้อ 4.2 |

## 1.7.z — รันหลายคลิป ช่วงเวลา และเครื่องเล่นวิดีโอ

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.7.0** | `9b5e656` | Run3 v28(25): BatchRun_TrackerSweepTool | เครื่องมือ batch ไล่ค่า tracker |
| **PKT 1.7.1** | `243cdfa` | Run3 v28(26): BatchRun_FolderMirrorOutput_CombinedPerLevel | ผลลัพธ์ batch เป็นโครงสร้างโฟลเดอร์เดียวกับต้นทาง + รวมต่อระดับ |
| **PKT 1.7.2** | `0c2d783` | Run3 v28(27): AnalysisTimeWindow_RecordWindow_Core | ช่วงเวลาวิเคราะห์และช่วงบันทึกวิดีโอ (แกนหลัก) |
| **PKT 1.7.3** | `c52fdac` | Run3 v28(28): VideoPlayerDialog_SetTimeRangeInApp | หน้าต่างเครื่องเล่น: กำหนดช่วงเวลาในโปรแกรม |
| **PKT 1.7.4** | `c1e613f` | Run3 v28(29): BatchWindow_PerClipTimeRangeAndRecording_PlanFile | หน้าต่าง batch: ช่วงเวลาและการบันทึกต่อคลิป + ไฟล์แผน |
| **PKT 1.7.5** | `3443851` | Run3 v28(30): PerClipCsvOnly_AddToExistingPlace_DayFolder | บันทึก CSV อย่างเดียวต่อคลิป, เพิ่มเข้าโฟลเดอร์วันเดิม |
| **PKT 1.7.6** | `3d83a3f` | Run3 v28(31): MirrorAnyFolderStructure_FolderPerClip | ทำโครงสร้างโฟลเดอร์ใดก็ได้ที่นำเข้า, โฟลเดอร์ต่อคลิป |

## 1.8.z — จัด UI ใหม่เป็น 4 ขั้น

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.8.0** | `de7d676` | Run3 v28(32): UiRedesign_FourSteps_UnifiedClipList_RunBar | UI 4 ขั้น: รายการคลิปรวม + แถบรัน |
| **PKT 1.8.1** | `12a49aa` | Run3 v28(33): PlayerDialog_FitScreen_VisibleSaveButton | เครื่องเล่น: พอดีหน้าจอ ปุ่มบันทึกมองเห็น |
| **PKT 1.8.2** | `9665e3b` | Run3 v28(34): RemoveRedundantRecordCheckbox_SkipDoneWording | ตัดช่องติ๊กบันทึกที่ซ้ำ, แก้คำว่า ข้ามคลิปที่เสร็จแล้ว |
| **PKT 1.8.3** | `5e800fd` | Run3 v28(35): CalibrationDialog_FixOverlappingFields_LayoutTest | แก้ช่องซ้อนกันในหน้าปรับเทียบ + ทดสอบเลย์เอาต์ |

## 1.9.z — การปรับเทียบ: จุดที่บันทึก, จุดตัดสินโซน, ต่อโซน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.9.0** | `0551086` | Run3 v28(36): CalibrationShowsSavedPoints_PreviewFix_EmptyReasonsInBatchReport_TrajectoryWarning | หน้าปรับเทียบแสดงจุดที่บันทึก, แก้ตัวอย่าง, รายงานผลว่างใน batch |
| **PKT 1.9.1** | `89383f3` | Run3 v28(37): ShowZoneDecisionPoint_CalibrationMeasureTool | แสดงจุดตัดสินโซน + เครื่องมือวัดในหน้าปรับเทียบ |
| **PKT 1.9.2** | `c92e76e` | Run3 v28(38): PerZoneCalibration_OwnReferenceQuadPerZone | ปรับเทียบต่อโซน (ชุดจุดอ้างอิงของโซนเอง) |

## 1.10.z — ชื่อไฟล์ผลลัพธ์และการต่อคลิปต่อเนื่อง

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.10.0** | `42798d7` | Run3 v28(39): FileNamesWithClipName_CombinedCsvAllClips | ชื่อไฟล์มีชื่อคลิป + CSV รวมทุกคลิป |
| **PKT 1.10.1** | `5ab05df` | Run3 v28(40): CombinedCsv_UniqueIdKeys_ClipStart | CSV รวม: คีย์ ID ไม่ซ้ำ + เวลาเริ่มคลิป |
| **PKT 1.10.2** | `2088758` | Run3 v28(41): ChainConsecutiveClips_IdsContinueAcrossClips | ต่อคลิปต่อเนื่อง: ID ต่อกันข้ามคลิป |
| **PKT 1.10.3** | `55b1893` | Run3 v28(42): ChainUsesWholeClips_IgnoresTimeRangeAndRecordRange | การต่อใช้ทั้งคลิป ไม่สนช่วงเวลา |
| **PKT 1.10.4** | `c82ce10` | Run3 v28(43): PlainResultFileNames_NoClipNameInFiles | ชื่อไฟล์ผลลัพธ์แบบเรียบ ไม่มีชื่อคลิป |
| **PKT 1.10.5** | `aeccb09` | Run3 v28(44): ContinueMeansTrackerCarriesOn_RangeAndRecordingStayPerClip | ต่อต่อเนื่อง = tracker ไปต่อ, ช่วงเวลา/บันทึกยังต่อคลิป |
| **PKT 1.10.6** | `00f3887` | Docs: ContinueGapExplanation_R6Review | เอกสาร: ช่องว่างของการต่อคลิป (ทบทวน R6) |

## 1.11.z — ความเร็วในการรัน และตัดแทร็กสั้นซ้ำ

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.11.0** | `ed20e8e` | Run3 v28(45): BackgroundDecodeAndEncode_AutoPrecisionFP32OnGTX16 | ถอดรหัส/เข้ารหัสวิดีโอเบื้องหลัง + เลือกความแม่นยำอัตโนมัติ (GTX16) |
| **PKT 1.11.1** | `62b55c0` | Run3 v28(46): ShortDuplicateTracks_RemovedFromAnalysis | ตัดแทร็กสั้นที่ซ้ำออกจากการวิเคราะห์ |

## 1.12.z — Lateral Clearance: ระยะข้างสูงสุดและช่วงเคียงข้าง

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.12.0** | `69eb163` | Run3 v28(47): LateralClearance_SidewaysLimit_AlongWindow_ClosestPerPair | LC: จำกัดระยะข้าง, หน้าต่างตามแนวยาว, ค่าใกล้สุดต่อคู่ |
| **PKT 1.12.1** | `da9edba` | Run3 v28(48): BottomDefault_OffsetWarning_ZoneFlickerMergeSetting | จุดล่างเป็นค่าเริ่มต้น + เตือน offset (ถูกถอยทันที) |
| **PKT 1.12.2** | `2f97af3` | Run3 v28(49): RevertTo_v28(46)_UndoLateralClearanceLimits_And_BottomDefault | ย้อนไป v28(46) |
| **PKT 1.12.3** | `5b5bb9a` | Run3 v28(50): LateralClearance_AlongWindow_And_MaxSidewaysOptions | LC: ตัวเลือกช่วงเคียงข้างและระยะข้างสูงสุด |

## 1.13.z — Topview รอบแรก และแผนที่อ้างอิงจากภาพโดรน (ภายหลังถอยออก)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.13.0** | `68994ca` | Run3 v28(51): TopviewRecords_And_TopviewVideo_FromMetricPoints | ไฟล์พิกัด Topview + วิดีโอ Topview จากจุดเมตร |
| **PKT 1.13.1** | `6720fdb` | Run3 v28(52): TopviewVideo_PlaysAtRealSpeed | วิดีโอ Topview เล่นด้วยความเร็วจริง |
| **PKT 1.13.2** | `a63ad21` | Run3 v28(53): ReferenceMap_DroneTopviewAsMap_CalibrationDialog | แผนที่อ้างอิง: ใช้ภาพโดรนเป็นแผนที่ในหน้าปรับเทียบ |
| **PKT 1.13.3** | `c6d4c48` | Run3 v28(54): ReferenceMap_AcceptsVideoFrame_ThaiPaths | แผนที่อ้างอิงรับเฟรมวิดีโอ + พาธภาษาไทย |
| **PKT 1.13.4** | `e8101ba` | Run3 v28(55): ReferenceMapDialog_ZoomAtPointer_Pan_ResetView_FrameSlider | หน้าแผนที่: ซูมที่เมาส์ แพน รีเซ็ต แถบเลื่อนเฟรม |
| **PKT 1.13.5** | `3a1c825` | Run3 v28(56): ReferenceMap_ZonesOverlay_PerPointError_DeletePoint_PoorCalibrationWarning | แผนที่: ซ้อนโซน, ความคลาดต่อจุด, ลบจุด, เตือนปรับเทียบไม่ดี |
| **PKT 1.13.6** | `ce8ff29` | Run3 v28(57): AdjustZonesOnMap_DragCorners_WriteMapfitZoneFile | ปรับโซนบนแผนที่ด้วยการลากมุม (ถูก revert) |
| **PKT 1.13.7** | `74d5c69` | Revert "Run3 v28(57): AdjustZonesOnMap_DragCorners_WriteMapfitZoneFile" | ย้อน: ปรับโซนบนแผนที่ |
| **PKT 1.13.8** | `2d6350d` | Run3 v28(58): ReferenceMap_UseZoneCornersAsCameraPoints_DragOnMap | ใช้มุมโซนเป็นจุดกล้อง ลากบนแผนที่ |
| **PKT 1.13.9** | `0f1c6f2` | Run3 v28(59): ZonesAppearOnMap_LayoutFollowsCorners_RealDistancesBetweenCorners | โซนแสดงบนแผนที่ ระยะจริงระหว่างมุม |
| **PKT 1.13.10** | `b29a300` | Run3 v28(60): ReferenceMap_AutoAlign_ECC_EdgeImages_BeforeAfterPreview | จัดแนวแผนที่อัตโนมัติ (ECC) + ดูก่อนหลัง |
| **PKT 1.13.11** | `67db8b7` | Run3 v28(61): SnapZonesToRoadSurface_Automatic_MapfitZoneFile | ปรับโซนให้ชิดผิวถนนอัตโนมัติ |
| **PKT 1.13.12** | `e5843c5` | Run3 v28(62): ReferenceMap_FreeCornersStayStill_SmallStepsBefore4Pairs_ClickVsDrag | มุมอิสระอยู่นิ่ง, ขยับทีละน้อยก่อนมี 4 คู่, คลิป vs ลาก |
| **PKT 1.13.13** | `640d2b4` | Run3 v28(63): SnappedZones_CleanOutlines_OptionalCornerDragOnMap | โซนที่ปรับแล้วเส้นสะอาด, ลากมุมบนแผนที่ได้ |
| **PKT 1.13.14** | `7f8485f` | Run3 v28(64): LensDistortion_EstimatedFromPairs_LeaveOneOutGuard_UsedInEveryMetricPoint | ประมาณความบิดของเลนส์จากคู่จุด + กัน leave-one-out |

## 1.14.z — Topview รอบสอง: ปรับเทียบแบบวางราบ เส้นถนน เลนส์ (ถอยออกทั้งหมด)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.14.0** | `aec9071` | Run3 v28(65): RevertTo_v28(50)_BeforeTopview | ย้อนไป v28(50) ก่อน Topview |
| **PKT 1.14.1** | `61facb8` | Revert "Run3 v28(65): RevertTo_v28(50)_BeforeTopview" | ย้อน: การย้อนไป v28(50) |
| **PKT 1.14.2** | `c81a960` | Run3 v28(66): LeanGroundCalibration_Fig2Style_LensKeypointsReprojectionROI | ปรับเทียบพื้นแบบเอียง (Fig.2) + เลนส์ + ROI |
| **PKT 1.14.3** | `b470bd4` | Docs: PlanLog_v28(66)_LeanGroundCalibration | เอกสาร: บันทึกแผน v28(66) |
| **PKT 1.14.4** | `14ecfb8` | Run3 v28(67): RevertTo_a6f6f54_TopviewWithoutDrone | ย้อนไป a6f6f54 (Topview ไม่มีโดรน) |
| **PKT 1.14.5** | `6b0b3ae` | Revert "Run3 v28(67): RevertTo_a6f6f54_TopviewWithoutDrone" | ย้อน: การย้อนไป a6f6f54 |
| **PKT 1.14.6** | `7dc3def` | Run3 v28(68): TopviewLooksLikeAMap_FullBrightnessMap_FaintGrid_TranslucentVehicles | Topview หน้าตาเหมือนแผนที่ |
| **PKT 1.14.7** | `e7aa59a` | Docs: PlanLog_v28(67)_v28(68)_TopviewLooksLikeAMap | เอกสาร: บันทึกแผน v28(67)–(68) |
| **PKT 1.14.8** | `c26e776` | Run3 v28(69): TopviewVideo_IsTheCameraVideoLensCorrectedAndLaidFlat | วิดีโอ Topview คือวิดีโอกล้องที่แก้เลนส์และวางราบ |
| **PKT 1.14.9** | `81e3f94` | Run3 v28(70): RemoveDroneMapFeatures_BackToNoDroneTopview | เอาฟีเจอร์แผนที่โดรนออก |
| **PKT 1.14.10** | `612ee81` | Run3 v28(71): LensFisheyeFromStraightLines_EmptyRoadTopviewLaidFlat | หาเลนส์ fisheye จากเส้นตรง, Topview วางราบจากถนนว่าง |
| **PKT 1.14.11** | `406c1d6` | Run3 v28(72): LensDialog_PopupWhenNoResult | หน้าต่างเลนส์เด้งเมื่อไม่มีผล |
| **PKT 1.14.12** | `78c8e6c` | Run3 v28(73): TopviewBlankAboveGroundFarField_RoadOnly | Topview ว่างส่วนเหนือพื้น/ไกล เหลือเฉพาะถนน |
| **PKT 1.14.13** | `7f77056` | Run3 v28(74): TopviewSameShapeAsVideo_VehiclePicturesOnFootprints | Topview รูปทรงเดียวกับวิดีโอ, รูปรถบนฐานรถ |
| **PKT 1.14.14** | `1a0de51` | Run3 v28(75): TopviewFollowsDisplaySettings_ReferencePointOnly_NoDarkMask | Topview ตามค่าการแสดงผล, จุดอ้างอิงอย่างเดียว |
| **PKT 1.14.15** | `e6bf24a` | Run3 v28(76): MapStyleTopview_RoadLinesClickedOnCameraFrame | Topview แบบแผนที่, เส้นถนนคลิปบนเฟรมกล้อง |
| **PKT 1.14.16** | `877c7f0` | Run3 v28(77): TopviewNoVehiclePictures_ReferencePointOnly | Topview ไม่มีรูปรถ |
| **PKT 1.14.17** | `f10117a` | Run3 v28(78): RoadLineTypes_WhiteYellowKerbBlueMotorcycleLane | ชนิดเส้นถนน: ขาว เหลือง ขอบทาง เลนมอเตอร์ไซค์ |
| **PKT 1.14.18** | `3cb4f0c` | Run3 v28(79): KerbWhiteYellow_InsteadOfYellowBlack | ขอบทางขาว-เหลือง |
| **PKT 1.14.19** | `2970dae` | Run3 v28(80): KerbStripeLength_0_5m | ความยาวลายขอบทาง 0.5 ม. |
| **PKT 1.14.20** | `758936b` | Run3 v28(81): OneToolForLensAndRoadLines | เครื่องมือเดียวสำหรับเลนส์และเส้นถนน |
| **PKT 1.14.21** | `4301ef8` | Run3 v28(82): StraightMarkedRoadLinesSnapToBestLine | เส้นถนนตรงเกาะเส้นที่ดีที่สุด |
| **PKT 1.14.22** | `99fa35d` | Run3 v28(83): OneCalibrationWindow_LensGroundPointsRoadLines | หน้าต่างปรับเทียบเดียว: เลนส์ จุดพื้น เส้นถนน |
| **PKT 1.14.23** | `45250b3` | Run3 v28(84): GroundFromParallelPerpendicularLines_ManyPointsLeastSquares | พื้นจากเส้นขนาน/ตั้งฉากหลายจุด กำลังสองน้อยสุด |
| **PKT 1.14.24** | `57dd46c` | Run3 v28(85): ZoneCornersAsGroundPoints_TypeEdgeLengths | มุมโซนเป็นจุดบนพื้น พิมพ์ความยาวขอบ |

## 1.15.z — ปรับเทียบจากมุมโซน (ถอยออกทั้งชุด)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.15.0** | `13fd162` | Run3 v28(86): RevertTo_v28(50)_RemoveWholeTopviewSystem | ย้อนไป v28(50) เอาระบบ Topview ทั้งชุดออก |
| **PKT 1.15.1** | `5fe3908` | Run3 v28(87): PerspectiveFromZones_EdgeLengths_QualityCheck | Perspective จากโซน: ความยาวขอบ + ตรวจคุณภาพ |
| **PKT 1.15.2** | `aec67ca` | Run3 v28(88): CalibrationMethodChoice_ShowOnlyChosenBlock | เลือกวิธีปรับเทียบ แสดงเฉพาะกรอบที่เลือก |
| **PKT 1.15.3** | `f6797a5` | Run3 v28(89): PerZoneCalibration_ZoneCornersAppearAsP1toP4 | ปรับเทียบต่อโซน: มุมโซนปรากฏเป็น P1–P4 |
| **PKT 1.15.4** | `22ae162` | Run3 v28(90): PerZoneOwnTransform_AnyNumberOfCorners_OneSummaryLine | การแปลงต่อโซน: จำนวนมุมเท่าไรก็ได้ สรุปบรรทัดเดียว |
| **PKT 1.15.5** | `e48b934` | Run3 v28(91): CalibrationWindow_ZoneOutlinesAlwaysVisible_ChosenZoneYellow | หน้าปรับเทียบ: เส้นโซนมองเห็นเสมอ โซนที่เลือกสีเหลือง |
| **PKT 1.15.6** | `147517d` | Run3 v28(91): FourCornerWindowDoesNotCutDownZonesWithMoreCorners | หน้าต่าง 4 มุมไม่ตัดโซนที่มีมุมมากกว่านี้ |
| **PKT 1.15.7** | `6e553ca` | Run3 v28(92): RadialLensTrend_FromZoneLengths_UsedForEveryPoint | แนวโน้มเลนส์แบบรัศมีจากความยาวโซน |
| **PKT 1.15.8** | `a3cf06f` | Run3 v28(93): RevertTo_v28(50)_RemoveCalibrationLayers | ย้อนไป v28(50) เอาชั้นปรับเทียบออก |

## 1.16.z — ผัง X–Y เมตร (พื้นฐานที่ใช้อยู่)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.16.0** | `976f3c6` | Run3 v28(51): TopviewRecords_And_TopviewVideo_FromMetricPoints | ไฟล์พิกัด Topview + วิดีโอ Topview (นำกลับ) |
| **PKT 1.16.1** | `0dace8d` | Run3 v28(52): TopviewVideo_PlaysAtRealSpeed | วิดีโอ Topview เล่นด้วยความเร็วจริง (นำกลับ) |
| **PKT 1.16.2** | `4da03f7` | Run3 v28(94): PlainXYPlane_TrajectoryPng_And_Video_ReferencePointLabelsPerDisplaySettings | ผัง X–Y เปล่า: ภาพเส้นทาง PNG + วิดีโอ จุดอ้างอิงและป้ายตามการแสดงผล |
| **PKT 1.16.3** | `79f0eb7` | Run3 v28(95): OutsideZoneVehicles_ShowDotOrHide_NormalVideoAndXY | รถนอกโซน: แสดงเป็นจุดหรือซ่อน (วิดีโอปกติและ X–Y) |
| **PKT 1.16.4** | `b05a678` | Docs: PlanStatus_v28(95)_TagV28_95_OpenItems | เอกสาร: สถานะ v28(95) + tag + รายการค้าง |

## 1.17.z — จัดแนววิดีโอกับภาพโดรน (Align)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.17.0** | `6c76dc7` | Run3 v28(96): AlignVideoToDronePlane_KindsLikeQgisGeoreferencer_LeaveOneOut | Align วิดีโอกับระนาบโดรน หลายชนิดการแปลง + leave-one-out |
| **PKT 1.17.1** | `a3075b4` | Run3 v28(97): AlignTable_WorstPairsFirst_RedMark_DeleteWorst | ตาราง Align: คู่แย่สุดก่อน ทำสีแดง ลบคู่แย่ |
| **PKT 1.17.2** | `7d44244` | Run3 v28(98): AlignReferenceLines_NPointsInVideo_HeadTailInDrone_XYAxes | Align จากเส้นอ้างอิง (ถูกถอย) |
| **PKT 1.17.3** | `b43096f` | Run3 v28(97): AlignTable_SortedByHonestError_WorstPairs_MeasureTest | ตาราง Align เรียงตามความคลาดที่ซื่อสัตย์ + เครื่องมือวัด |
| **PKT 1.17.4** | `48a2c78` | Run3 v28(98): AlignZoneMode_PinsFromVideo_PlaceOnDrone_NewZoneFile | Align โหมดโซน: หมุดจากวิดีโอ วางบนโดรน (ถูกถอย) |
| **PKT 1.17.5** | `e9e7d00` | Run3 v28(99): RevertTo_v28(97)_RemoveAlignV28_98 | ย้อนไป v28(97) เอา Align v28(98) ออก |
| **PKT 1.17.6** | `6182219` | Run3 v28(100): AlignZonePins_VideoSideFromZoneFile_SkipUnsure | หมุดมุมโซนจากไฟล์โซน ข้ามได้ถ้าไม่แน่ใจ |

## 1.18.z — ผัง X–Y ตรงกลาง + ตัวแก้รูปโซน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.18.0** | `4f72042` | Run3 v28(101): XYPictureCentredOnZones | ภาพ X–Y อยู่กลางโซน |
| **PKT 1.18.1** | `9ba7156` | Run3 v28(102): PreviewXYPlaneBeforeRun_ZonesInMetres_EdgeLengths | ดูตัวอย่างผัง X–Y ก่อนรัน + ความยาวขอบโซน |
| **PKT 1.18.2** | `d1e5168` | Run3 v28(103): ZoneEditorOnVideoDroneXYViews_PerpendicularShiftSnapNewZoneFile | ตัวแก้รูปโซน 3 มุมมอง (วิดีโอ/โดรน/X–Y) ทำให้ตั้งฉาก บันทึกไฟล์โซนใหม่ |
| **PKT 1.18.3** | `3276845` | Run3 v28(104): ZoneEditor_UseForAnalysisButton | ปุ่มใช้โซนที่แก้ในการวิเคราะห์ทันที |
| **PKT 1.18.4** | `63a6098` | Run3 v28(105): RemoveXYPreviewButton | เอาปุ่มตัวอย่างผัง X–Y ออก |

## 1.19.z — กรอบฐานรถ Footprint (ทดลอง แล้วถอยออก)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.19.0** | `8957187` | Run3 v28(106): VehicleFootprint_OnRoadPlane_XYAndRoadsideVideo | กรอบฐานรถบนระนาบถนน แสดงใน X–Y และวิดีโอข้างทาง |
| **PKT 1.19.1** | `f62ee58` | Run3 v28(107): RevertFootprint_BackToV28_105 | ย้อน Footprint กลับไปที่ v28(105) |

## 1.20.z — ออกแบบ TTC แบบเวกเตอร์ (เอกสาร)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.20.0** | `2b690b2` | Docs: TTC_VectorFormulation_Draft_InSpec | เขียนสูตร TTC เวกเตอร์ฉบับร่างลงสเปก |
| **PKT 1.20.1** | `0d77781` | Docs: TTC_Draft_RemoveDGate | ฉบับร่าง: ตัดเกณฑ์ระยะพลาดกัน D ออกก่อน |
| **PKT 1.20.2** | `a71592e` | Docs: TTC_Draft_FixDMention | ฉบับร่าง: แก้ข้อความที่พูดถึง D |
| **PKT 1.20.3** | `87c4017` | Docs: TTC_ConflictType_ByAngle_SameAsPaper | ฉบับร่าง: ชนิดความขัดแย้งตามมุมเหมือนเปเปอร์ |
| **PKT 1.20.4** | `260c545` | Docs: TTC_Draft_PairSelection_NoCrossingFilter | ฉบับร่าง: เลือกคู่รถ ไม่กรองด้วยจุดตัด trajectory |

## 1.21.z — TTC เวกเตอร์ + เกณฑ์ความเสี่ยง + สี่เหลี่ยมรถ + ตารางการแสดงผล

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.21.0** | `e891838` | Run3 v28(108): VectorTTC_ConflictAngleType_NoMissGate | TTC เวกเตอร์ + ชนิดความขัดแย้งตามมุม (30°/85°) |
| **PKT 1.21.1** | `b52c5d4` | Run3 v28(109): RiskLevels_SeminarTables_SingleSpeedScale_OverallLevel_EditableLimits | เกณฑ์ความเสี่ยงตามสไลด์สัมมนา, ความเร็วชุดเดียว, ระดับรวม, กรอกเกณฑ์เองได้ |
| **PKT 1.21.2** | `3d1de8e` | Run3 v28(110): TTC_MissGateRestored_SlowVehicleSkip_TTCFramesCSV | คืนเกณฑ์ระยะพลาดกัน + ข้ามรถช้า + ไฟล์ TTC_Frames.csv |
| **PKT 1.21.3** | `0f2b827` | Docs: SpecAndPlan_TTCMissGate_v28_110 | เอกสาร: สเปกและแผนเรื่องเกณฑ์ระยะพลาดกัน |
| **PKT 1.21.4** | `ecb77fa` | Run3 v28(111): TTC_CrossingPathsArrivalGap_OtherPairsVector_BlankCutoffAll | TTC สองวิธี: เส้นทางตัดกัน (ส่วนต่างเวลาถึง) / ไม่ตัด (เวกเตอร์); เว้นว่าง = บันทึกทั้งหมด |
| **PKT 1.21.5** | `73876df` | Run3 v28(112): TTC_VehicleRectangles_TimeUntilBoxesTouch | TTC: รถเป็นสี่เหลี่ยม ยาว×กว้าง เวลาที่กรอบแตะกัน |
| **PKT 1.21.6** | `31b2cdc` | Run3 v28(113): TTCRectangles_ShowInXYAndRoadsideVideo_Switches | แสดงสี่เหลี่ยมรถของ TTC ใน X–Y และวิดีโอข้างทาง (สวิตช์) |
| **PKT 1.21.7** | `06aec44` | Run3 v28(114): TTCRectangles_OnNormalVideoNotThirdVideo_OptionsInTab1 | สี่เหลี่ยมวาดลงวิดีโอปกติ ไม่สร้างวิดีโอที่สาม + ตัวเลือกไปหน้า ① |
| **PKT 1.21.8** | `7d83150` | Run3 v28(115): DisplayTable_TwoColumns_EverySwitchPerVideo_VideoSwitchesOnOnePage | ตารางการแสดงผลสองคอลัมน์: เปิด/ปิดแยกต่อวิดีโอ + สร้างวิดีโอหน้าเดียวกัน |
| **PKT 1.21.9** | `62e5eaf` | Run3 v28(116): TTC_PointMethodDefault_ExpectedCollisionPointStoredAndDrawn | TTC จุดเดียวเป็นค่าตั้งต้น + เก็บและวาดจุดที่คาดว่าจะชน |
| **PKT 1.21.10** | `c51d531` | Run3 v28(117): ExpectedCollisionPoint_IsPathIntersection_NotMidpoint | จุดที่คาดว่าจะชน = จุดตัดของเส้นทางตรงสองคัน (ไม่ใช่จุดกึ่งกลาง) |
| **PKT 1.21.11** | `de21e39` | Run3 v28(118): TTC_MeetingPointMustBeInsideZone_EdgeMargin | จุดพบกันของ TTC ต้องอยู่ในโซน (ขอบเผื่อ) — เซสชันคู่ขนาน |
| **PKT 1.21.12** | `79f0962` | Run3 v28(118): TTC_ZoneFiltersCollisionPoint_NotTracking | โซนของ TTC เป็นตัวกรองจุดชน ไม่ใช่ตัวกำหนดการ track |
| **PKT 1.21.13** | `83b9a58` | Run3 v28(119): TTC_CollisionZoneMustBeOnPathOfBothVehicles_ZoneSequence | จุดชนต้องอยู่ในโซนที่รถทั้งสองอยู่/จะเข้า (Zone Sequence) |

## 1.22.z — PET แบบพื้นที่ขัดแย้ง + LDP โซน 1

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.22.0** | `6e94ff6` | Run3 v28(120): PET_AllZones_Selectable | PET เลือกโซนได้ทุกโซน |
| **PKT 1.22.1** | `5d7bcb2` | Run3 v28(121): LDP_Zone1_LockedWithNote | LDP: ล็อกโซน 1 พร้อมหมายเหตุ |
| **PKT 1.22.2** | `6b1d2b9` | Run3 v28(122): PET_SameMovement_CountedIfTrajectoriesCross | PET: Movement เดียวกันนับถ้า trajectory ตัดกัน |
| **PKT 1.22.3** | `be542e8` | Run3 v28(123): PET_RequireRealTrajectoryCrossing_NoClosestApproachFallback | PET: ต้องตัดกันจริง ไม่ใช้จุดใกล้สุดแทน |
| **PKT 1.22.4** | `6855e89` | Run3 v28(124): PET_OptionalMinVehicleSpeed | PET: ความเร็วรถขั้นต่ำ (ตัวเลือก) |
| **PKT 1.22.5** | `c663ae9` | Run3 v28(125): PET_MinSpeed_UsesSpeedAtCrossingPoint | PET: ความเร็วขั้นต่ำใช้ความเร็ว ณ จุดตัด |
| **PKT 1.22.6** | `767745a` | Run3 v28(126): PET_SpeedColumns_AtCrossingPoint | PET: คอลัมน์ความเร็ว ณ จุดตัด |
| **PKT 1.22.7** | `0098e38` | Run3 v28(127): PET_CrossingPointOnly_ShowCrossingInVideo | PET: นับเฉพาะจุดตัด + แสดงจุดตัดในวิดีโอ |
| **PKT 1.22.8** | `aa3a0aa` | Docs: SPEC_PET_TypoFix | เอกสาร: แก้คำผิดในสเปก PET |
| **PKT 1.22.9** | `02b7d83` | Run3 v28(128): PET_ConflictAreaRadius_WaPlusWbHalf_Toggle | PET: รัศมีพื้นที่ขัดแย้ง = (Wa+Wb)/2 สลับได้ |

## 1.23.z — จัด CSV ใหม่ (ชื่อคอลัมน์ ไฟล์ล้ม ความเร็วต่อเฟรม)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.23.0** | `aa423b6` | Run3 v28(129): CSV_ErrorFileSeparate_GapColumnsRenamed | ตัวชี้วัดที่ล้มเขียนไฟล์ _ERROR.csv แยก + เปลี่ยนชื่อคอลัมน์ Gap |
| **PKT 1.23.1** | `8f56886` | Run3 v28(130): CSV_ConsistentColumnNames_TTCDetail_FrameSpeed_MovementCalibration | ชื่อคอลัมน์ CSV สม่ำเสมอ, TTC แบบละเอียด, ความเร็วต่อเฟรม, การปรับเทียบของ Movement |
| **PKT 1.23.2** | `9581308` | Run3 v28(131): CSV_Cleanup_SpeedPerFrame_DropRedundantColumns_DetailFilesSwitch | ล้าง CSV: Speed ต่อเฟรม ตัดคอลัมน์ซ้ำ สวิตช์ไฟล์รายละเอียด |

## 1.24.z — PET: ชนิดความขัดแย้งตามกติกา TTC

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.24.0** | `39627f5` | Run3 v28(132): PET_ConflictType_ByTtcAngleRule | PET กำหนด Conflict_Type ด้วยมุมระหว่างความเร็วสองคัน ณ จุดตัด (เหมือน TTC) |
| **PKT 1.24.1** | `a20f50d` | Chore: e2e_run3 follows v28(131) (speed per frame in Speed.csv, no Speed rows in Indicator_Summary) | แก้เทสต์ e2e ให้ตรง v28(131) (ความเร็วต่อเฟรมใน Speed.csv) |

## 1.25.z — เลขเวอร์ชัน PKT และ CHANGELOG

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.25.0** | (commit นี้) | PKT 1.25.0: Changelog_PKT_VersionNumbers_Tags | ตั้งกติกาเลขเวอร์ชัน PKT x.y.z, ทำตารางนี้, ติด tag `PKT-x.y.z` ให้ทุก commit ในตาราง |
| **PKT 1.25.1** | (ตัวรวม main ถูกเอาออกแล้ว tag ชี้ที่ 1.29.2) | PKT 1.25.1: Changelog_IncludesCloudSessionCommits_MergeMain | รวมงานของเซสชัน cloud (หัวข้อ 1.26–1.28) เข้าตาราง, ผู้ใช้ยืนยันใช้ PKT ตามของตน ทับการยกเลิก `PKT 1.78.0` |

| **PKT 1.29.2** | `f6e0451` | PKT 1.29.2: Changelog_HashesUpdatedAfterRename | เปลี่ยนชื่อ commit เก่าทั้งหมดเป็น `PKT x.y.z: ...` (เขียนประวัติ main ใหม่เฉพาะข้อความ เนื้อไฟล์เท่าเดิมทุกไบต์) และแก้ hash ในตารางให้ตรงของใหม่; ประวัติเดิมสำรองไว้ใน `_git_backup/` |

## 1.26.z — ลองตั้งชื่อ PKT 1.x.y ในเซสชัน cloud (ยกเลิกแล้ว — เลข 1.78.0 ไม่ใช้)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.26.0** | `37223fd` | PKT 1.78.0: VersionNaming_PKT_HistoryMap | ตาราง VERSION_HISTORY.md เลขแบบ 1.x.y (ถูกยกเลิก) |
| **PKT 1.26.1** | `d9003d2` | Docs: RevertPKTNaming_BackToRun3Names | ย้อนการตั้งชื่อ PKT ของเซสชัน cloud กลับเป็นชื่อ Run3 |

## 1.27.z — เอกสารที่มาของเกณฑ์ความเสี่ยง (สไลด์สัมมนา)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.27.0** | `19ee2ce` | Docs: LdpRiskTableSource_CROW2009_SeminarSlide42 | เอกสาร: ที่มาตารางเกณฑ์ LDP (CROW 2009 สไลด์ 42) |
| **PKT 1.27.1** | `2c4751b` | Docs: SeminarSlides_TTC_PET_LDP_SourcesVerified | เอกสาร: ตรวจที่มาเกณฑ์ TTC/PET/LDP จากสไลด์สัมมนาแล้ว |

## 1.28.z — Gap Acceptance แบบแยกขั้นตามโซนกลาง + สรุปวิธี TTC ปัจจุบัน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.28.0** | `9d0c306` | Run3 v28(133): GapAcceptance_StagedPerMiddleZone | Gap Acceptance: ตัดสินแยกขั้นต่อโซนกลาง |
| **PKT 1.28.1** | `c93fc5d` | Docs: SpecTTC_CurrentMethodSummary_CleanOutdated | เอกสาร: สรุปวิธี TTC ปัจจุบัน ล้างข้อความที่ล้าสมัย |
| **PKT 1.28.2** | `aae79fa` | Docs_PlanStatusUpdate_AfterPR4Merge | เอกสาร: อัปเดตสถานะใน plan.md หลังรวม PR #4 (งานค้าง: รอผลเทสต์จากเครื่องผู้ใช้) |
| **PKT 1.28.3** | `b84d0a6` | Run3 v28(134): GapCsv_ReadablePrecision_CriticalGapQC | Gap CSV: เวลา/ช่องว่างทศนิยม 3 ตำแหน่ง; Critical_Gap เพิ่มจำนวนคนขับที่ถูกตัดออกและ QC_Flag |
| **PKT 1.28.4** | `5f1993e` | Run3 v28(135): GapCsv_LeadLagNames_SpeedColumnTimeFix | Gap CSV: ชื่อคอลัมน์ Lead/Lag และแก้ชื่อความเร็วที่บอกเวลาผิด; Decision_Zone → Subject_Zone_At_Decision |

## 1.29.z — เรียงคอลัมน์ CSV ให้ผลหลักอยู่หน้า

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.29.0** | `eec9e97` | Run3 v28(136): CsvColumnOrder_ResultsFirst | TTC/PET/LDP: ตัวระบุ → ผลหลักและระดับความเสี่ยง → รายละเอียด → QC_Flag (ชื่อคอลัมน์ไม่เปลี่ยน) |
| **PKT 1.29.1** | (commit นี้) | PKT 1.29.1: Changelog_CloudCommits134to136 | เพิ่มงานเซสชัน cloud (v28(134)–(136)) เข้าตาราง ตั้งชื่อ commit แบบ PKT ต่อจากนี้ |

## 1.30.z — PET เลือกนับตามชนิดความขัดแย้ง + ไฟล์ Headway

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.30.0** | `781393a` | PKT 1.30.0: PetExcludeRearEnd_HeadwayCsv | PET ตัดคู่ชนิด Rear-end (สวิตช์ `pet_exclude_rear_end`); ไฟล์ใหม่ `Headway.csv` (Time Headway, Time Gap ต่อ Movement); แยกฟังก์ชันหาเวลาข้ามเส้นของกระแสใช้ร่วมกับ Gap Acceptance |
| **PKT 1.30.1** | `6be0b0d` | PKT 1.30.1: HeadwayFromPetRearEnd_DropConsecutivePairs | **ยกเลิกใน 1.30.2** — เคยเปลี่ยน Headway.csv เป็นแถว PET ชนิด Rear-end |
| **PKT 1.30.2** | `1a60530` | PKT 1.30.2: HeadwayBackToLineGaps_PetConflictTypeSwitches | Headway.csv กลับเป็นแบบเส้น Line/โซนต้นทางของแต่ละ Movement (เหมือน 1.30.0); PET มีสวิตช์เลือกนับต่อชนิด Rear-end / Lane change / Crossing (มุมเดียวกับ TTC) แทน `pet_exclude_rear_end` |
| **PKT 1.30.3** | (commit นี้) | PKT 1.30.3: TtcConflictTypeSwitches | TTC มีสวิตช์เลือกนับต่อชนิด TTC_Type (Rear-end / Lane change / Crossing, ค่าตั้งต้นเปิดทั้งสาม) เหมือน PET; ชนิดที่ปิดไม่ออกแถวและไม่วาดในวิดีโอ |
| **PKT 1.30.4** | (commit นี้) | PKT 1.30.4: Changelog_LinearHistory_MergeCommitsRemoved | เอา Merge pull request (#1–#6) ออกจากประวัติ main ให้เป็นเส้นตรง (งานจริงทุก commit อยู่ครบ เนื้อไฟล์ล่าสุดเท่าเดิม) แก้ hash ในตารางและ tag ให้ตรงของใหม่; ประวัติก่อนแก้สำรองไว้ใน `_git_backup/` |
| **PKT 1.30.5** | (commit นี้) | PKT 1.30.5: Changelog_Renumber_1.25.2_to_1.29.2 | เปลี่ยนเลข 1.25.2 เป็น 1.29.2 ให้เรียงตามลำดับ commit (แก้ชื่อ commit + tag, แก้ hash ในตาราง) |
| **PKT 1.30.6** | `b018af8` | PKT 1.30.6: HeadwayOwnBox_FollowersOnly_LinePerMovement | Headway มีกรอบ/สวิตช์ของตัวเองในแท็บ ③; เลือก Movement และ Line ต่อ Movement ได้; จับเฉพาะรถที่ตามกัน (อยู่ในแนวทางวิ่งของคันหน้า ข้ามรถขนาน); Headway สูงสุดตั้งได้; คอลัมน์ `Lateral_To_Lead_Path_m` |

## 1.31.z — เส้นอ้างอิงจากขอบโซน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.31.0** | `b7514ab` | PKT 1.31.0: ReferenceLineFromSharedZoneEdge | เส้นอ้างอิงของ Gap Acceptance และ Headway = เส้นเชื่อมโหนดร่วมของสองโซนที่ติดกัน (1-3-4/1-3-6-7 = 1\|3, 2-3-1/2-3-4 = 2\|3, 5-6-7 = 5\|6, 5-6-3-1 = 3\|6) ไม่ต้องวาด; เลือก `ขอบโซน`/`Line ที่วาดไว้` ได้; เขียน `Edge a-b` ในช่อง Line ได้ |

## 1.32.z — Critical Gap แยกกลุ่มตามชนิดรถ

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.32.0** | `a4029aa` | PKT 1.32.0: CriticalGapByVehicleClass_LowSampleFlag | Critical Gap แยกตามชนิดรถของคนที่รอ (เปิด/ปิด) และชนิดรถของคันหลังที่กำลังมา (เปิด/ปิด); คอลัมน์ `Lag_Vehicle_Class`; ธง `Few_Drivers_Below_N` เมื่อตัวอย่างน้อย (ตั้งค่า N ได้) |
| **PKT 1.32.1** | (commit นี้) | PKT 1.32.1: TrackingVideo_NoLeftoverTmpFile | วิดีโอ Tracking_Result ที่วาดกรอบ TTC/PET: ถ้าไฟล์ถูกเปิดค้างในเครื่องเล่น ลองแทนที่ซ้ำหลายครั้งก่อน, ลบไฟล์ชั่วคราว `Tracking_Result._ttc_tmp.mp4` ทิ้งเสมอ (รวมกรณีวาดผิดพลาด), บอกผลใน Summary.json (`ttc_boxes_video`) |

## 1.33.z — ความเร็วในการรัน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.33.0** | `a3aee2d` | PKT 1.33.0: SpeedUps_PreviewOff_ScaledVideo_HwDecode_TensorRT_FastPairs | พรีวิวปิดเป็นค่าตั้งต้น; วิดีโอผลลัพธ์ย่อไม่เกิน 1920 px; ตัวเลือกถอดรหัสด้วยการ์ดจอและ TensorRT (ถอยกลับเอง); TTC/PET กรองคู่เร็วขึ้นโดยผลเหมือนเดิม |
| **PKT 1.33.1** | `a3aee2d` | PKT 1.33.1: TensorRT_AutoInstallPackages | เปิด TensorRT แล้วไม่มีแพ็กเกจ `tensorrt` / `onnx` → ติดตั้งให้เองด้วย pip (Python ที่รันโปรแกรม) ก่อนสร้าง engine |
| **PKT 1.33.2** | (commit นี้) | PKT 1.33.2: PetMark_ShowAfterSecondVehicle_1s | กากบาท PET ในวิดีโอขึ้นเมื่อคันที่ 2 ถึงจุดตัด (ผลเกิดแล้ว) แสดง 1 วินาทีแล้วหาย (เดิมขึ้นตั้งแต่ 1 วินาทีก่อนคันแรกถึง อยู่ยาวจนรก) |
