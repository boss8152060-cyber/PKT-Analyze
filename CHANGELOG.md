# CHANGELOG — เลขเวอร์ชัน PKT x.y.z

ประวัติการเปลี่ยนแปลงของโปรแกรม PK Studio เรียงตามเวลา แต่ละบรรทัดมีเลขเวอร์ชัน PKT, รหัส commit (hash), ชื่อเดิม และคำอธิบายสั้น ๆ ว่าทำอะไร
ชื่อเดิม (`Run3 v28(N)`) ยังอยู่ใน git เหมือนเดิม — ตารางนี้และ tag `PKT-x.y.z` เป็นชื่อใหม่ที่ใช้ค้นหา (ไม่มีการแก้ประวัติ ไม่มีการเปลี่ยน hash)

## กติกาเลขเวอร์ชัน

| ตำแหน่ง | ความหมาย | ตัวอย่าง |
|---|---|---|
| `x` | ระยะใหญ่ | 0 = ก่อนชุด v28 (v27 และเอกสาร), 1 = งานตัวชี้วัดชุด v28 |
| `y` | หัวข้องานใหม่ (ตัวชี้วัดใหม่ / ระบบใหม่) | PET แบบพื้นที่ขัดแย้ง = `1.22.z` |
| `z` | งานเรื่องเดียวกันที่แก้ต่อ (แก้บั๊ก ปรับค่า ปรับเอกสาร) | `1.22.0` → `1.22.1`; เรื่องใหม่ → `1.23.0` |

- commit ใหม่ตั้งชื่อ `PKT x.y.z: คำอธิบายสั้น ๆ` (ต่อ `(PASS)` เมื่อผู้ใช้ยืนยัน) และติด tag `PKT-x.y.z` ที่ commit นั้น
- `Merge pull request ...` ที่ GitHub สร้างให้ไม่ให้เลขเวอร์ชัน (ไม่ใช่งาน)
- เวอร์ชันถัดไป: งานต่อเรื่องเดิม = `1.29.2`; เรื่องใหม่ = `1.30.0` (เลขเรียงตามหัวข้อ ไม่ใช่เวลาเสมอไป — หัวข้อ 1.25 ทำหลังหัวข้อ 1.26–1.28 ของเซสชัน cloud)


## 0.1.z — เอกสารโปรเจ็คและกติกา git (ก่อนชุด v27)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 0.1.0** | `9a397dc` | Docs: ProjectOverview_Plan_GitRules_Gitignore | เอกสารภาพรวมโปรเจ็ค, แผนงาน, กติกา git, .gitignore |
| **PKT 0.1.1** | `bb975a5` | Docs: PlanUpdate_RemoteOriginPushed | อัปเดตแผน: ตั้ง remote origin และ push แล้ว |

## 0.2.z — แก้ย่อยชุด v27

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 0.2.0** | `88a603f` | Run3 v27(1): ZoneSummary_ExitTimeFix | แก้เวลาออกของ Zone Summary |
| **PKT 0.2.1** | `39247ce` | Run3 v27(2): ZoneFlicker_SummaryCleanup | ล้างการแกว่งเข้าออกขอบโซนใน Summary |
| **PKT 0.2.2** | `2b78199` | Run3 v27(3): Preflight_ZoneNotDefinedWarning | เตือนก่อนรันเมื่อยังไม่มีโซน |
| **PKT 0.2.3** | `35fc982` | Run3 v27(4): Preflight_GapMappingWarning | เตือนก่อนรันเมื่อ Gap ไม่มี Line mapping |
| **PKT 0.2.4** | `4fd32c9` | Docs: PlanAdd_LineEditor_GapCrossingDedupe | เอกสาร: เพิ่มแผนหน้าต่างวาด Line และการตัดซ้ำของ Gap |

## 0.3.z — เอกสารสเปกตัวชี้วัดชุดใหม่ (v28)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 0.3.0** | `567bd69` | Docs: SpecV28_NewIndicators_PlanPhaseV | เขียน SPEC v28 และแผนระยะที่ 5 |
| **PKT 0.3.1** | `f684c2f` | Docs: SpecV28_AnswersRecorded | บันทึกคำตอบของผู้ใช้ลงสเปก |

## 1.1.z — ตัวชี้วัดชุดใหม่ + Movement (LDP, Lateral Clearance, PET, TTC, Gap, Speed)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.1.0** | `35838bc` | Run3 v28(1): MovementSequence_LaneWidthInputs | Movement จากลำดับโซน + ช่องกรอกความกว้างเลน |
| **PKT 1.1.1** | `3c7d463` | Docs: SpecV28_NewIndicatorCodes_Y1toY6 | เอกสาร: ตั้งรหัสตัวชี้วัด (ภายหลังเลิกใช้) |
| **PKT 1.1.2** | `2569b3e` | Run3 v28(2): Y6Speed_ZoneAndMovement | Speed ต่อโซนและต่อ Movement |
| **PKT 1.1.3** | `7c4df56` | Run3 v28(3): Y1LDP_ChordReference | LDP แบบเส้นอ้างอิงจุดเข้า-ออกโซน |
| **PKT 1.1.4** | `f7eb841` | Run3 v28(4): Y2LateralClearance_HeadingPerpendicular | Lateral Clearance ตั้งฉากกับทิศวิ่ง + กรอบซ้อนกัน |
| **PKT 1.1.5** | `35c4e1d` | Run3 v28(5): Y5PET_Y4TTC_Zones3and6_SideCollision | PET และ TTC ในโซน 3, 6 + ชนด้านข้าง |
| **PKT 1.1.6** | `3fb63ca` | Run3 v28(6): Y3Gap_FirstCrossingOnly_V28Finalize | Gap Acceptance ข้ามเส้นครั้งแรกเท่านั้น |
| **PKT 1.1.7** | `1e5dc90` | Run3 v28(7): IndicatorNamesInsteadOfYCodes | เรียกตัวชี้วัดด้วยชื่อ ไม่ใช้รหัส Y1–Y6 |
| **PKT 1.1.8** | `1d70004` | Run3 v28(8): UserAnswers_GapTable_LDPAllClasses_TTCSideAdjustable_LCAllPairs | ตามคำตอบผู้ใช้: ตาราง Gap, LDP ทุกชนิดรถ, TTC ด้านข้างปรับได้, LC ทุกคู่ |
| **PKT 1.1.9** | `a9b02f9` | Run3 v28(9): LDP_DivideByHalfWidth | LDP หารด้วยครึ่งความกว้างเลน |

## 1.2.z — Line และ Reference Line Mapping

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.2.0** | `218b893` | Run3 v28(10): LineEditor_DrawReferenceLines | หน้าต่างวาด Line อ้างอิง |
| **PKT 1.2.1** | `162ce39` | Run3 v28(11): ReferenceLineMapping_PrefilledSite8 | Reference Line Mapping ตั้งไว้ให้ Site 8 |

## 1.3.z — ไฟล์โซนและการรันด้วย GPU (CUDA)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.3.0** | `5e4c27f` | Docs: ZoneFileDJI0426_VideoFacts | เอกสาร: ข้อเท็จจริงของวิดีโอที่ใช้กับไฟล์โซน DJI_0426 |
| **PKT 1.3.1** | `fad5c1d` | Run3 v28(12): CUDA_PythonFallback_LauncherBat | ถอยไปใช้ Python ที่มี CUDA อัตโนมัติ + ไฟล์ .bat เปิดโปรแกรม |
| **PKT 1.3.2** | `357b024` | Docs: CUDA_Python312_Launcher | เอกสาร: ตั้ง Python 3.12 + CUDA |

## 1.4.z — กรองข้อมูลและบอกสาเหตุผลว่าง

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.4.0** | `346aced` | Run3 v28(13): DuplicateTrackFilter | ตัดแทร็กซ้ำ (รถคันเดียวสองไอดี) |
| **PKT 1.4.1** | `025cc2d` | Run3 v28(14): ExplainEmptyOutputs_ZoneVideoMismatchWarning | อธิบายสาเหตุที่ผลลัพธ์ว่าง + เตือนโซนไม่ตรงวิดีโอ |
| **PKT 1.4.2** | `1dfbde7` | Run3 v28(15): MovementFirstVisitFallback | Movement: ถอยไปใช้การเข้าโซนครั้งแรกเมื่อลำดับไม่ครบ |

## 1.5.z — Gap Acceptance แบบ PASS (สองขั้น)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.5.0** | `3f9ed34` | Docs: GapAcceptance_PASSDesign_WaitZones1356 | เอกสาร: ออกแบบ Gap แบบ PASS โซนรอ 1, 3, 5, 6 |
| **PKT 1.5.1** | `0313954` | Run3 v28(16): GapAcceptance_TwoStagePASS_LineOptional | Gap สองขั้น (เข้า/ออก) ตรรกะ PASS, Line เป็นตัวเลือก |
| **PKT 1.5.2** | `aff23ea` | Run3 v28(17): ZoneRemap_OldZoneFileWorksWithNewMovements | แปลงไฟล์โซนเก่าให้ใช้กับ Movement ใหม่ (ภายหลังถูกถอย) |
| **PKT 1.5.3** | `68dbf52` | Run3 v28(18): RevertToV28_13 | ย้อนไป v28(13) |
| **PKT 1.5.4** | `f3d33ac` | Run3 v28(19): RestoreV28_16_WithoutZoneRemap | คืน v28(16) โดยไม่มีการแปลงโซน |

## 1.6.z — ความถูกต้องของ CSV และพื้นฐาน UI

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.6.0** | `4f25a81` | Run3 v28(20): ExcelSafeMovementArrows | เขียน Movement เป็นลูกศร กัน Excel แปลงเป็นวันที่ |
| **PKT 1.6.1** | `2f164d0` | Run3 v28(21): FP16KeyByVersion_TimestampStartsAtZero | คีย์ FP16 ตามเวอร์ชัน + เวลาเริ่มที่ 0 |
| **PKT 1.6.2** | `fecb62c` | Run3 v28(22): SpeedOutlierFlag_LC_PET_Stats_UntrackedCount | ธง Speed ผิดปกติ, สถิติ LC/PET, นับรถที่ไม่ได้ติดตาม |
| **PKT 1.6.3** | `14114da` | Run3 v28(23): MergeClips_SensitivityTool_ParametersDoc | เครื่องมือรวมคลิป, วิเคราะห์ความไว, เอกสารค่าพารามิเตอร์ |
| **PKT 1.6.4** | `c713dde` | Docs: Phase3_UserDeferredRiskRuleSensitivityTracking | เอกสาร: ระยะที่ 3 เรื่องที่ผู้ใช้เลื่อนไว้ |
| **PKT 1.6.5** | `120dd41` | Run3 v28(24): UiQueue_RelativeDefaultPaths_NoAutoDelete_Logging | คิวเธรดของ UI, พาธเริ่มต้นแบบสัมพัทธ์, ไม่ลบไฟล์เอง, log |
| **PKT 1.6.6** | `c1f1016` | Docs: PlanCleanup_RemoveUserPendingItems | เอกสาร: จัดแผนใหม่ เอารายการรอผู้ใช้ออก |
| **PKT 1.6.7** | `79863d7` | Docs: RemovePlan_4.4_4.5 | เอกสาร: ตัดหัวข้อ 4.4–4.5 ออกจากแผน |
| **PKT 1.6.8** | `5e90c24` | Docs: PlanFix_4.2_Note | เอกสาร: แก้หมายเหตุข้อ 4.2 |

## 1.7.z — รันหลายคลิป ช่วงเวลา และเครื่องเล่นวิดีโอ

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.7.0** | `2a6ee5c` | Run3 v28(25): BatchRun_TrackerSweepTool | เครื่องมือ batch ไล่ค่า tracker |
| **PKT 1.7.1** | `1609290` | Run3 v28(26): BatchRun_FolderMirrorOutput_CombinedPerLevel | ผลลัพธ์ batch เป็นโครงสร้างโฟลเดอร์เดียวกับต้นทาง + รวมต่อระดับ |
| **PKT 1.7.2** | `4ed3b01` | Run3 v28(27): AnalysisTimeWindow_RecordWindow_Core | ช่วงเวลาวิเคราะห์และช่วงบันทึกวิดีโอ (แกนหลัก) |
| **PKT 1.7.3** | `2f4dd0e` | Run3 v28(28): VideoPlayerDialog_SetTimeRangeInApp | หน้าต่างเครื่องเล่น: กำหนดช่วงเวลาในโปรแกรม |
| **PKT 1.7.4** | `a1fffcd` | Run3 v28(29): BatchWindow_PerClipTimeRangeAndRecording_PlanFile | หน้าต่าง batch: ช่วงเวลาและการบันทึกต่อคลิป + ไฟล์แผน |
| **PKT 1.7.5** | `21472ea` | Run3 v28(30): PerClipCsvOnly_AddToExistingPlace_DayFolder | บันทึก CSV อย่างเดียวต่อคลิป, เพิ่มเข้าโฟลเดอร์วันเดิม |
| **PKT 1.7.6** | `9583738` | Run3 v28(31): MirrorAnyFolderStructure_FolderPerClip | ทำโครงสร้างโฟลเดอร์ใดก็ได้ที่นำเข้า, โฟลเดอร์ต่อคลิป |

## 1.8.z — จัด UI ใหม่เป็น 4 ขั้น

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.8.0** | `c5d9787` | Run3 v28(32): UiRedesign_FourSteps_UnifiedClipList_RunBar | UI 4 ขั้น: รายการคลิปรวม + แถบรัน |
| **PKT 1.8.1** | `4af6470` | Run3 v28(33): PlayerDialog_FitScreen_VisibleSaveButton | เครื่องเล่น: พอดีหน้าจอ ปุ่มบันทึกมองเห็น |
| **PKT 1.8.2** | `ab48eb5` | Run3 v28(34): RemoveRedundantRecordCheckbox_SkipDoneWording | ตัดช่องติ๊กบันทึกที่ซ้ำ, แก้คำว่า ข้ามคลิปที่เสร็จแล้ว |
| **PKT 1.8.3** | `8b7a743` | Run3 v28(35): CalibrationDialog_FixOverlappingFields_LayoutTest | แก้ช่องซ้อนกันในหน้าปรับเทียบ + ทดสอบเลย์เอาต์ |

## 1.9.z — การปรับเทียบ: จุดที่บันทึก, จุดตัดสินโซน, ต่อโซน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.9.0** | `99e11c2` | Run3 v28(36): CalibrationShowsSavedPoints_PreviewFix_EmptyReasonsInBatchReport_TrajectoryWarning | หน้าปรับเทียบแสดงจุดที่บันทึก, แก้ตัวอย่าง, รายงานผลว่างใน batch |
| **PKT 1.9.1** | `522e375` | Run3 v28(37): ShowZoneDecisionPoint_CalibrationMeasureTool | แสดงจุดตัดสินโซน + เครื่องมือวัดในหน้าปรับเทียบ |
| **PKT 1.9.2** | `d118ad6` | Run3 v28(38): PerZoneCalibration_OwnReferenceQuadPerZone | ปรับเทียบต่อโซน (ชุดจุดอ้างอิงของโซนเอง) |

## 1.10.z — ชื่อไฟล์ผลลัพธ์และการต่อคลิปต่อเนื่อง

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.10.0** | `c8b16bc` | Run3 v28(39): FileNamesWithClipName_CombinedCsvAllClips | ชื่อไฟล์มีชื่อคลิป + CSV รวมทุกคลิป |
| **PKT 1.10.1** | `8e62588` | Run3 v28(40): CombinedCsv_UniqueIdKeys_ClipStart | CSV รวม: คีย์ ID ไม่ซ้ำ + เวลาเริ่มคลิป |
| **PKT 1.10.2** | `6103d4d` | Run3 v28(41): ChainConsecutiveClips_IdsContinueAcrossClips | ต่อคลิปต่อเนื่อง: ID ต่อกันข้ามคลิป |
| **PKT 1.10.3** | `5dea4be` | Run3 v28(42): ChainUsesWholeClips_IgnoresTimeRangeAndRecordRange | การต่อใช้ทั้งคลิป ไม่สนช่วงเวลา |
| **PKT 1.10.4** | `9a50f3e` | Run3 v28(43): PlainResultFileNames_NoClipNameInFiles | ชื่อไฟล์ผลลัพธ์แบบเรียบ ไม่มีชื่อคลิป |
| **PKT 1.10.5** | `fc91f6c` | Run3 v28(44): ContinueMeansTrackerCarriesOn_RangeAndRecordingStayPerClip | ต่อต่อเนื่อง = tracker ไปต่อ, ช่วงเวลา/บันทึกยังต่อคลิป |
| **PKT 1.10.6** | `0950e52` | Docs: ContinueGapExplanation_R6Review | เอกสาร: ช่องว่างของการต่อคลิป (ทบทวน R6) |

## 1.11.z — ความเร็วในการรัน และตัดแทร็กสั้นซ้ำ

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.11.0** | `0e5f2e5` | Run3 v28(45): BackgroundDecodeAndEncode_AutoPrecisionFP32OnGTX16 | ถอดรหัส/เข้ารหัสวิดีโอเบื้องหลัง + เลือกความแม่นยำอัตโนมัติ (GTX16) |
| **PKT 1.11.1** | `991525c` | Run3 v28(46): ShortDuplicateTracks_RemovedFromAnalysis | ตัดแทร็กสั้นที่ซ้ำออกจากการวิเคราะห์ |

## 1.12.z — Lateral Clearance: ระยะข้างสูงสุดและช่วงเคียงข้าง

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.12.0** | `0b8be69` | Run3 v28(47): LateralClearance_SidewaysLimit_AlongWindow_ClosestPerPair | LC: จำกัดระยะข้าง, หน้าต่างตามแนวยาว, ค่าใกล้สุดต่อคู่ |
| **PKT 1.12.1** | `7eb98c3` | Run3 v28(48): BottomDefault_OffsetWarning_ZoneFlickerMergeSetting | จุดล่างเป็นค่าเริ่มต้น + เตือน offset (ถูกถอยทันที) |
| **PKT 1.12.2** | `a4c3f9a` | Run3 v28(49): RevertTo_v28(46)_UndoLateralClearanceLimits_And_BottomDefault | ย้อนไป v28(46) |
| **PKT 1.12.3** | `794561b` | Run3 v28(50): LateralClearance_AlongWindow_And_MaxSidewaysOptions | LC: ตัวเลือกช่วงเคียงข้างและระยะข้างสูงสุด |

## 1.13.z — Topview รอบแรก และแผนที่อ้างอิงจากภาพโดรน (ภายหลังถอยออก)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.13.0** | `a6f6f54` | Run3 v28(51): TopviewRecords_And_TopviewVideo_FromMetricPoints | ไฟล์พิกัด Topview + วิดีโอ Topview จากจุดเมตร |
| **PKT 1.13.1** | `3f98895` | Run3 v28(52): TopviewVideo_PlaysAtRealSpeed | วิดีโอ Topview เล่นด้วยความเร็วจริง |
| **PKT 1.13.2** | `3de86c1` | Run3 v28(53): ReferenceMap_DroneTopviewAsMap_CalibrationDialog | แผนที่อ้างอิง: ใช้ภาพโดรนเป็นแผนที่ในหน้าปรับเทียบ |
| **PKT 1.13.3** | `5d8e7a0` | Run3 v28(54): ReferenceMap_AcceptsVideoFrame_ThaiPaths | แผนที่อ้างอิงรับเฟรมวิดีโอ + พาธภาษาไทย |
| **PKT 1.13.4** | `cfdb485` | Run3 v28(55): ReferenceMapDialog_ZoomAtPointer_Pan_ResetView_FrameSlider | หน้าแผนที่: ซูมที่เมาส์ แพน รีเซ็ต แถบเลื่อนเฟรม |
| **PKT 1.13.5** | `70e5128` | Run3 v28(56): ReferenceMap_ZonesOverlay_PerPointError_DeletePoint_PoorCalibrationWarning | แผนที่: ซ้อนโซน, ความคลาดต่อจุด, ลบจุด, เตือนปรับเทียบไม่ดี |
| **PKT 1.13.6** | `0045329` | Run3 v28(57): AdjustZonesOnMap_DragCorners_WriteMapfitZoneFile | ปรับโซนบนแผนที่ด้วยการลากมุม (ถูก revert) |
| **PKT 1.13.7** | `1b9a6cf` | Revert "Run3 v28(57): AdjustZonesOnMap_DragCorners_WriteMapfitZoneFile" | ย้อน: ปรับโซนบนแผนที่ |
| **PKT 1.13.8** | `a6ef7e4` | Run3 v28(58): ReferenceMap_UseZoneCornersAsCameraPoints_DragOnMap | ใช้มุมโซนเป็นจุดกล้อง ลากบนแผนที่ |
| **PKT 1.13.9** | `405d1d0` | Run3 v28(59): ZonesAppearOnMap_LayoutFollowsCorners_RealDistancesBetweenCorners | โซนแสดงบนแผนที่ ระยะจริงระหว่างมุม |
| **PKT 1.13.10** | `4ec2787` | Run3 v28(60): ReferenceMap_AutoAlign_ECC_EdgeImages_BeforeAfterPreview | จัดแนวแผนที่อัตโนมัติ (ECC) + ดูก่อนหลัง |
| **PKT 1.13.11** | `78461b3` | Run3 v28(61): SnapZonesToRoadSurface_Automatic_MapfitZoneFile | ปรับโซนให้ชิดผิวถนนอัตโนมัติ |
| **PKT 1.13.12** | `1f45ed7` | Run3 v28(62): ReferenceMap_FreeCornersStayStill_SmallStepsBefore4Pairs_ClickVsDrag | มุมอิสระอยู่นิ่ง, ขยับทีละน้อยก่อนมี 4 คู่, คลิป vs ลาก |
| **PKT 1.13.13** | `51bad6b` | Run3 v28(63): SnappedZones_CleanOutlines_OptionalCornerDragOnMap | โซนที่ปรับแล้วเส้นสะอาด, ลากมุมบนแผนที่ได้ |
| **PKT 1.13.14** | `e3bc2b3` | Run3 v28(64): LensDistortion_EstimatedFromPairs_LeaveOneOutGuard_UsedInEveryMetricPoint | ประมาณความบิดของเลนส์จากคู่จุด + กัน leave-one-out |

## 1.14.z — Topview รอบสอง: ปรับเทียบแบบวางราบ เส้นถนน เลนส์ (ถอยออกทั้งหมด)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.14.0** | `0ddee4f` | Run3 v28(65): RevertTo_v28(50)_BeforeTopview | ย้อนไป v28(50) ก่อน Topview |
| **PKT 1.14.1** | `f054e47` | Revert "Run3 v28(65): RevertTo_v28(50)_BeforeTopview" | ย้อน: การย้อนไป v28(50) |
| **PKT 1.14.2** | `b492af8` | Run3 v28(66): LeanGroundCalibration_Fig2Style_LensKeypointsReprojectionROI | ปรับเทียบพื้นแบบเอียง (Fig.2) + เลนส์ + ROI |
| **PKT 1.14.3** | `e925060` | Docs: PlanLog_v28(66)_LeanGroundCalibration | เอกสาร: บันทึกแผน v28(66) |
| **PKT 1.14.4** | `4278868` | Run3 v28(67): RevertTo_a6f6f54_TopviewWithoutDrone | ย้อนไป a6f6f54 (Topview ไม่มีโดรน) |
| **PKT 1.14.5** | `62b72a3` | Revert "Run3 v28(67): RevertTo_a6f6f54_TopviewWithoutDrone" | ย้อน: การย้อนไป a6f6f54 |
| **PKT 1.14.6** | `c721de0` | Run3 v28(68): TopviewLooksLikeAMap_FullBrightnessMap_FaintGrid_TranslucentVehicles | Topview หน้าตาเหมือนแผนที่ |
| **PKT 1.14.7** | `dee0f5e` | Docs: PlanLog_v28(67)_v28(68)_TopviewLooksLikeAMap | เอกสาร: บันทึกแผน v28(67)–(68) |
| **PKT 1.14.8** | `dd472c8` | Run3 v28(69): TopviewVideo_IsTheCameraVideoLensCorrectedAndLaidFlat | วิดีโอ Topview คือวิดีโอกล้องที่แก้เลนส์และวางราบ |
| **PKT 1.14.9** | `5330d2c` | Run3 v28(70): RemoveDroneMapFeatures_BackToNoDroneTopview | เอาฟีเจอร์แผนที่โดรนออก |
| **PKT 1.14.10** | `680cba7` | Run3 v28(71): LensFisheyeFromStraightLines_EmptyRoadTopviewLaidFlat | หาเลนส์ fisheye จากเส้นตรง, Topview วางราบจากถนนว่าง |
| **PKT 1.14.11** | `a7abdfb` | Run3 v28(72): LensDialog_PopupWhenNoResult | หน้าต่างเลนส์เด้งเมื่อไม่มีผล |
| **PKT 1.14.12** | `ee03e65` | Run3 v28(73): TopviewBlankAboveGroundFarField_RoadOnly | Topview ว่างส่วนเหนือพื้น/ไกล เหลือเฉพาะถนน |
| **PKT 1.14.13** | `85d86a3` | Run3 v28(74): TopviewSameShapeAsVideo_VehiclePicturesOnFootprints | Topview รูปทรงเดียวกับวิดีโอ, รูปรถบนฐานรถ |
| **PKT 1.14.14** | `b1f5ed6` | Run3 v28(75): TopviewFollowsDisplaySettings_ReferencePointOnly_NoDarkMask | Topview ตามค่าการแสดงผล, จุดอ้างอิงอย่างเดียว |
| **PKT 1.14.15** | `8f88b8d` | Run3 v28(76): MapStyleTopview_RoadLinesClickedOnCameraFrame | Topview แบบแผนที่, เส้นถนนคลิปบนเฟรมกล้อง |
| **PKT 1.14.16** | `03417e9` | Run3 v28(77): TopviewNoVehiclePictures_ReferencePointOnly | Topview ไม่มีรูปรถ |
| **PKT 1.14.17** | `4fc88d3` | Run3 v28(78): RoadLineTypes_WhiteYellowKerbBlueMotorcycleLane | ชนิดเส้นถนน: ขาว เหลือง ขอบทาง เลนมอเตอร์ไซค์ |
| **PKT 1.14.18** | `36b3f93` | Run3 v28(79): KerbWhiteYellow_InsteadOfYellowBlack | ขอบทางขาว-เหลือง |
| **PKT 1.14.19** | `07a5d59` | Run3 v28(80): KerbStripeLength_0_5m | ความยาวลายขอบทาง 0.5 ม. |
| **PKT 1.14.20** | `e0b0f26` | Run3 v28(81): OneToolForLensAndRoadLines | เครื่องมือเดียวสำหรับเลนส์และเส้นถนน |
| **PKT 1.14.21** | `6f557b8` | Run3 v28(82): StraightMarkedRoadLinesSnapToBestLine | เส้นถนนตรงเกาะเส้นที่ดีที่สุด |
| **PKT 1.14.22** | `d96c571` | Run3 v28(83): OneCalibrationWindow_LensGroundPointsRoadLines | หน้าต่างปรับเทียบเดียว: เลนส์ จุดพื้น เส้นถนน |
| **PKT 1.14.23** | `abb05f2` | Run3 v28(84): GroundFromParallelPerpendicularLines_ManyPointsLeastSquares | พื้นจากเส้นขนาน/ตั้งฉากหลายจุด กำลังสองน้อยสุด |
| **PKT 1.14.24** | `58bf613` | Run3 v28(85): ZoneCornersAsGroundPoints_TypeEdgeLengths | มุมโซนเป็นจุดบนพื้น พิมพ์ความยาวขอบ |

## 1.15.z — ปรับเทียบจากมุมโซน (ถอยออกทั้งชุด)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.15.0** | `9c90056` | Run3 v28(86): RevertTo_v28(50)_RemoveWholeTopviewSystem | ย้อนไป v28(50) เอาระบบ Topview ทั้งชุดออก |
| **PKT 1.15.1** | `7390cfd` | Run3 v28(87): PerspectiveFromZones_EdgeLengths_QualityCheck | Perspective จากโซน: ความยาวขอบ + ตรวจคุณภาพ |
| **PKT 1.15.2** | `ac9c4c0` | Run3 v28(88): CalibrationMethodChoice_ShowOnlyChosenBlock | เลือกวิธีปรับเทียบ แสดงเฉพาะกรอบที่เลือก |
| **PKT 1.15.3** | `0367fbc` | Run3 v28(89): PerZoneCalibration_ZoneCornersAppearAsP1toP4 | ปรับเทียบต่อโซน: มุมโซนปรากฏเป็น P1–P4 |
| **PKT 1.15.4** | `05fe553` | Run3 v28(90): PerZoneOwnTransform_AnyNumberOfCorners_OneSummaryLine | การแปลงต่อโซน: จำนวนมุมเท่าไรก็ได้ สรุปบรรทัดเดียว |
| **PKT 1.15.5** | `a224dfe` | Run3 v28(91): CalibrationWindow_ZoneOutlinesAlwaysVisible_ChosenZoneYellow | หน้าปรับเทียบ: เส้นโซนมองเห็นเสมอ โซนที่เลือกสีเหลือง |
| **PKT 1.15.6** | `0b98f3a` | Run3 v28(91): FourCornerWindowDoesNotCutDownZonesWithMoreCorners | หน้าต่าง 4 มุมไม่ตัดโซนที่มีมุมมากกว่านี้ |
| **PKT 1.15.7** | `b86a3c0` | Run3 v28(92): RadialLensTrend_FromZoneLengths_UsedForEveryPoint | แนวโน้มเลนส์แบบรัศมีจากความยาวโซน |
| **PKT 1.15.8** | `9af983f` | Run3 v28(93): RevertTo_v28(50)_RemoveCalibrationLayers | ย้อนไป v28(50) เอาชั้นปรับเทียบออก |

## 1.16.z — ผัง X–Y เมตร (พื้นฐานที่ใช้อยู่)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.16.0** | `7d2c854` | Run3 v28(51): TopviewRecords_And_TopviewVideo_FromMetricPoints | ไฟล์พิกัด Topview + วิดีโอ Topview (นำกลับ) |
| **PKT 1.16.1** | `deaba91` | Run3 v28(52): TopviewVideo_PlaysAtRealSpeed | วิดีโอ Topview เล่นด้วยความเร็วจริง (นำกลับ) |
| **PKT 1.16.2** | `c85f3d2` | Run3 v28(94): PlainXYPlane_TrajectoryPng_And_Video_ReferencePointLabelsPerDisplaySettings | ผัง X–Y เปล่า: ภาพเส้นทาง PNG + วิดีโอ จุดอ้างอิงและป้ายตามการแสดงผล |
| **PKT 1.16.3** | `6cc4225` | Run3 v28(95): OutsideZoneVehicles_ShowDotOrHide_NormalVideoAndXY | รถนอกโซน: แสดงเป็นจุดหรือซ่อน (วิดีโอปกติและ X–Y) |
| **PKT 1.16.4** | `9c8be42` | Docs: PlanStatus_v28(95)_TagV28_95_OpenItems | เอกสาร: สถานะ v28(95) + tag + รายการค้าง |

## 1.17.z — จัดแนววิดีโอกับภาพโดรน (Align)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.17.0** | `4c91a9e` | Run3 v28(96): AlignVideoToDronePlane_KindsLikeQgisGeoreferencer_LeaveOneOut | Align วิดีโอกับระนาบโดรน หลายชนิดการแปลง + leave-one-out |
| **PKT 1.17.1** | `9511458` | Run3 v28(97): AlignTable_WorstPairsFirst_RedMark_DeleteWorst | ตาราง Align: คู่แย่สุดก่อน ทำสีแดง ลบคู่แย่ |
| **PKT 1.17.2** | `b39eb3f` | Run3 v28(98): AlignReferenceLines_NPointsInVideo_HeadTailInDrone_XYAxes | Align จากเส้นอ้างอิง (ถูกถอย) |
| **PKT 1.17.3** | `34fcc3c` | Run3 v28(97): AlignTable_SortedByHonestError_WorstPairs_MeasureTest | ตาราง Align เรียงตามความคลาดที่ซื่อสัตย์ + เครื่องมือวัด |
| **PKT 1.17.4** | `1a9b954` | Run3 v28(98): AlignZoneMode_PinsFromVideo_PlaceOnDrone_NewZoneFile | Align โหมดโซน: หมุดจากวิดีโอ วางบนโดรน (ถูกถอย) |
| **PKT 1.17.5** | `46a51ec` | Run3 v28(99): RevertTo_v28(97)_RemoveAlignV28_98 | ย้อนไป v28(97) เอา Align v28(98) ออก |
| **PKT 1.17.6** | `c9c8aa2` | Run3 v28(100): AlignZonePins_VideoSideFromZoneFile_SkipUnsure | หมุดมุมโซนจากไฟล์โซน ข้ามได้ถ้าไม่แน่ใจ |

## 1.18.z — ผัง X–Y ตรงกลาง + ตัวแก้รูปโซน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.18.0** | `fad9372` | Run3 v28(101): XYPictureCentredOnZones | ภาพ X–Y อยู่กลางโซน |
| **PKT 1.18.1** | `7a8396e` | Run3 v28(102): PreviewXYPlaneBeforeRun_ZonesInMetres_EdgeLengths | ดูตัวอย่างผัง X–Y ก่อนรัน + ความยาวขอบโซน |
| **PKT 1.18.2** | `3d46ca9` | Run3 v28(103): ZoneEditorOnVideoDroneXYViews_PerpendicularShiftSnapNewZoneFile | ตัวแก้รูปโซน 3 มุมมอง (วิดีโอ/โดรน/X–Y) ทำให้ตั้งฉาก บันทึกไฟล์โซนใหม่ |
| **PKT 1.18.3** | `793fe49` | Run3 v28(104): ZoneEditor_UseForAnalysisButton | ปุ่มใช้โซนที่แก้ในการวิเคราะห์ทันที |
| **PKT 1.18.4** | `aaeae07` | Run3 v28(105): RemoveXYPreviewButton | เอาปุ่มตัวอย่างผัง X–Y ออก |

## 1.19.z — กรอบฐานรถ Footprint (ทดลอง แล้วถอยออก)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.19.0** | `61a4b31` | Run3 v28(106): VehicleFootprint_OnRoadPlane_XYAndRoadsideVideo | กรอบฐานรถบนระนาบถนน แสดงใน X–Y และวิดีโอข้างทาง |
| **PKT 1.19.1** | `66527d7` | Run3 v28(107): RevertFootprint_BackToV28_105 | ย้อน Footprint กลับไปที่ v28(105) |

## 1.20.z — ออกแบบ TTC แบบเวกเตอร์ (เอกสาร)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.20.0** | `18fa76d` | Docs: TTC_VectorFormulation_Draft_InSpec | เขียนสูตร TTC เวกเตอร์ฉบับร่างลงสเปก |
| **PKT 1.20.1** | `3ec2285` | Docs: TTC_Draft_RemoveDGate | ฉบับร่าง: ตัดเกณฑ์ระยะพลาดกัน D ออกก่อน |
| **PKT 1.20.2** | `8e3cbbb` | Docs: TTC_Draft_FixDMention | ฉบับร่าง: แก้ข้อความที่พูดถึง D |
| **PKT 1.20.3** | `9be2cfa` | Docs: TTC_ConflictType_ByAngle_SameAsPaper | ฉบับร่าง: ชนิดความขัดแย้งตามมุมเหมือนเปเปอร์ |
| **PKT 1.20.4** | `246e5e9` | Docs: TTC_Draft_PairSelection_NoCrossingFilter | ฉบับร่าง: เลือกคู่รถ ไม่กรองด้วยจุดตัด trajectory |

## 1.21.z — TTC เวกเตอร์ + เกณฑ์ความเสี่ยง + สี่เหลี่ยมรถ + ตารางการแสดงผล

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.21.0** | `2f07b08` | Run3 v28(108): VectorTTC_ConflictAngleType_NoMissGate | TTC เวกเตอร์ + ชนิดความขัดแย้งตามมุม (30°/85°) |
| **PKT 1.21.1** | `d1ae2fd` | Run3 v28(109): RiskLevels_SeminarTables_SingleSpeedScale_OverallLevel_EditableLimits | เกณฑ์ความเสี่ยงตามสไลด์สัมมนา, ความเร็วชุดเดียว, ระดับรวม, กรอกเกณฑ์เองได้ |
| **PKT 1.21.2** | `867d5ce` | Run3 v28(110): TTC_MissGateRestored_SlowVehicleSkip_TTCFramesCSV | คืนเกณฑ์ระยะพลาดกัน + ข้ามรถช้า + ไฟล์ TTC_Frames.csv |
| **PKT 1.21.3** | `6dca929` | Docs: SpecAndPlan_TTCMissGate_v28_110 | เอกสาร: สเปกและแผนเรื่องเกณฑ์ระยะพลาดกัน |
| **PKT 1.21.4** | `b8d68b3` | Run3 v28(111): TTC_CrossingPathsArrivalGap_OtherPairsVector_BlankCutoffAll | TTC สองวิธี: เส้นทางตัดกัน (ส่วนต่างเวลาถึง) / ไม่ตัด (เวกเตอร์); เว้นว่าง = บันทึกทั้งหมด |
| **PKT 1.21.5** | `ae117c7` | Run3 v28(112): TTC_VehicleRectangles_TimeUntilBoxesTouch | TTC: รถเป็นสี่เหลี่ยม ยาว×กว้าง เวลาที่กรอบแตะกัน |
| **PKT 1.21.6** | `6aac019` | Run3 v28(113): TTCRectangles_ShowInXYAndRoadsideVideo_Switches | แสดงสี่เหลี่ยมรถของ TTC ใน X–Y และวิดีโอข้างทาง (สวิตช์) |
| **PKT 1.21.7** | `6a57886` | Run3 v28(114): TTCRectangles_OnNormalVideoNotThirdVideo_OptionsInTab1 | สี่เหลี่ยมวาดลงวิดีโอปกติ ไม่สร้างวิดีโอที่สาม + ตัวเลือกไปหน้า ① |
| **PKT 1.21.8** | `0ea949e` | Run3 v28(115): DisplayTable_TwoColumns_EverySwitchPerVideo_VideoSwitchesOnOnePage | ตารางการแสดงผลสองคอลัมน์: เปิด/ปิดแยกต่อวิดีโอ + สร้างวิดีโอหน้าเดียวกัน |
| **PKT 1.21.9** | `034724b` | Run3 v28(116): TTC_PointMethodDefault_ExpectedCollisionPointStoredAndDrawn | TTC จุดเดียวเป็นค่าตั้งต้น + เก็บและวาดจุดที่คาดว่าจะชน |
| **PKT 1.21.10** | `809caa7` | Run3 v28(117): ExpectedCollisionPoint_IsPathIntersection_NotMidpoint | จุดที่คาดว่าจะชน = จุดตัดของเส้นทางตรงสองคัน (ไม่ใช่จุดกึ่งกลาง) |
| **PKT 1.21.11** | `7314418` | Run3 v28(118): TTC_MeetingPointMustBeInsideZone_EdgeMargin | จุดพบกันของ TTC ต้องอยู่ในโซน (ขอบเผื่อ) — เซสชันคู่ขนาน |
| **PKT 1.21.12** | `e7f619f` | Run3 v28(118): TTC_ZoneFiltersCollisionPoint_NotTracking | โซนของ TTC เป็นตัวกรองจุดชน ไม่ใช่ตัวกำหนดการ track |
| **PKT 1.21.13** | `a377274` | Run3 v28(119): TTC_CollisionZoneMustBeOnPathOfBothVehicles_ZoneSequence | จุดชนต้องอยู่ในโซนที่รถทั้งสองอยู่/จะเข้า (Zone Sequence) |

## 1.22.z — PET แบบพื้นที่ขัดแย้ง + LDP โซน 1

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.22.0** | `c805795` | Run3 v28(120): PET_AllZones_Selectable | PET เลือกโซนได้ทุกโซน |
| **PKT 1.22.1** | `3c55264` | Run3 v28(121): LDP_Zone1_LockedWithNote | LDP: ล็อกโซน 1 พร้อมหมายเหตุ |
| **PKT 1.22.2** | `64de196` | Run3 v28(122): PET_SameMovement_CountedIfTrajectoriesCross | PET: Movement เดียวกันนับถ้า trajectory ตัดกัน |
| **PKT 1.22.3** | `2f6a7cf` | Run3 v28(123): PET_RequireRealTrajectoryCrossing_NoClosestApproachFallback | PET: ต้องตัดกันจริง ไม่ใช้จุดใกล้สุดแทน |
| **PKT 1.22.4** | `d48f8c5` | Run3 v28(124): PET_OptionalMinVehicleSpeed | PET: ความเร็วรถขั้นต่ำ (ตัวเลือก) |
| **PKT 1.22.5** | `a370adb` | Run3 v28(125): PET_MinSpeed_UsesSpeedAtCrossingPoint | PET: ความเร็วขั้นต่ำใช้ความเร็ว ณ จุดตัด |
| **PKT 1.22.6** | `5c00411` | Run3 v28(126): PET_SpeedColumns_AtCrossingPoint | PET: คอลัมน์ความเร็ว ณ จุดตัด |
| **PKT 1.22.7** | `a552bc9` | Run3 v28(127): PET_CrossingPointOnly_ShowCrossingInVideo | PET: นับเฉพาะจุดตัด + แสดงจุดตัดในวิดีโอ |
| **PKT 1.22.8** | `5b2401a` | Docs: SPEC_PET_TypoFix | เอกสาร: แก้คำผิดในสเปก PET |
| **PKT 1.22.9** | `ecf95d4` | Run3 v28(128): PET_ConflictAreaRadius_WaPlusWbHalf_Toggle | PET: รัศมีพื้นที่ขัดแย้ง = (Wa+Wb)/2 สลับได้ |

## 1.23.z — จัด CSV ใหม่ (ชื่อคอลัมน์ ไฟล์ล้ม ความเร็วต่อเฟรม)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.23.0** | `cc86417` | Run3 v28(129): CSV_ErrorFileSeparate_GapColumnsRenamed | ตัวชี้วัดที่ล้มเขียนไฟล์ _ERROR.csv แยก + เปลี่ยนชื่อคอลัมน์ Gap |
| **PKT 1.23.1** | `0da0c82` | Run3 v28(130): CSV_ConsistentColumnNames_TTCDetail_FrameSpeed_MovementCalibration | ชื่อคอลัมน์ CSV สม่ำเสมอ, TTC แบบละเอียด, ความเร็วต่อเฟรม, การปรับเทียบของ Movement |
| **PKT 1.23.2** | `28d824e` | Run3 v28(131): CSV_Cleanup_SpeedPerFrame_DropRedundantColumns_DetailFilesSwitch | ล้าง CSV: Speed ต่อเฟรม ตัดคอลัมน์ซ้ำ สวิตช์ไฟล์รายละเอียด |

## 1.24.z — PET: ชนิดความขัดแย้งตามกติกา TTC

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.24.0** | `be2689d` | Run3 v28(132): PET_ConflictType_ByTtcAngleRule | PET กำหนด Conflict_Type ด้วยมุมระหว่างความเร็วสองคัน ณ จุดตัด (เหมือน TTC) |
| **PKT 1.24.1** | `5d896b5` | Chore: e2e_run3 follows v28(131) (speed per frame in Speed.csv, no Speed rows in Indicator_Summary) | แก้เทสต์ e2e ให้ตรง v28(131) (ความเร็วต่อเฟรมใน Speed.csv) |

## 1.25.z — เลขเวอร์ชัน PKT และ CHANGELOG

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.25.0** | (commit นี้) | PKT 1.25.0: Changelog_PKT_VersionNumbers_Tags | ตั้งกติกาเลขเวอร์ชัน PKT x.y.z, ทำตารางนี้, ติด tag `PKT-x.y.z` ให้ทุก commit ในตาราง |
| **PKT 1.25.1** | (commit รวม main) | PKT 1.25.1: Changelog_IncludesCloudSessionCommits_MergeMain | รวมงานของเซสชัน cloud (หัวข้อ 1.26–1.28) เข้าตาราง, ผู้ใช้ยืนยันใช้ PKT ตามของตน ทับการยกเลิก `PKT 1.78.0` |

## 1.26.z — ลองตั้งชื่อ PKT 1.x.y ในเซสชัน cloud (ยกเลิกแล้ว — เลข 1.78.0 ไม่ใช้)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.26.0** | `7fa078f` | PKT 1.78.0: VersionNaming_PKT_HistoryMap | ตาราง VERSION_HISTORY.md เลขแบบ 1.x.y (ถูกยกเลิก) |
| **PKT 1.26.1** | `a95aef6` | Docs: RevertPKTNaming_BackToRun3Names | ย้อนการตั้งชื่อ PKT ของเซสชัน cloud กลับเป็นชื่อ Run3 |

## 1.27.z — เอกสารที่มาของเกณฑ์ความเสี่ยง (สไลด์สัมมนา)

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.27.0** | `1e58849` | Docs: LdpRiskTableSource_CROW2009_SeminarSlide42 | เอกสาร: ที่มาตารางเกณฑ์ LDP (CROW 2009 สไลด์ 42) |
| **PKT 1.27.1** | `4c91601` | Docs: SeminarSlides_TTC_PET_LDP_SourcesVerified | เอกสาร: ตรวจที่มาเกณฑ์ TTC/PET/LDP จากสไลด์สัมมนาแล้ว |

## 1.28.z — Gap Acceptance แบบแยกขั้นตามโซนกลาง + สรุปวิธี TTC ปัจจุบัน

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.28.0** | `b4ab76c` | Run3 v28(133): GapAcceptance_StagedPerMiddleZone | Gap Acceptance: ตัดสินแยกขั้นต่อโซนกลาง |
| **PKT 1.28.1** | `5d2d33d` | Docs: SpecTTC_CurrentMethodSummary_CleanOutdated | เอกสาร: สรุปวิธี TTC ปัจจุบัน ล้างข้อความที่ล้าสมัย |
| **PKT 1.28.2** | `7239526` | Docs_PlanStatusUpdate_AfterPR4Merge | เอกสาร: อัปเดตสถานะใน plan.md หลังรวม PR #4 (งานค้าง: รอผลเทสต์จากเครื่องผู้ใช้) |
| **PKT 1.28.3** | `0545dd9` | Run3 v28(134): GapCsv_ReadablePrecision_CriticalGapQC | Gap CSV: เวลา/ช่องว่างทศนิยม 3 ตำแหน่ง; Critical_Gap เพิ่มจำนวนคนขับที่ถูกตัดออกและ QC_Flag |
| **PKT 1.28.4** | `5439551` | Run3 v28(135): GapCsv_LeadLagNames_SpeedColumnTimeFix | Gap CSV: ชื่อคอลัมน์ Lead/Lag และแก้ชื่อความเร็วที่บอกเวลาผิด; Decision_Zone → Subject_Zone_At_Decision |

## 1.29.z — เรียงคอลัมน์ CSV ให้ผลหลักอยู่หน้า

| PKT | commit | ชื่อเดิม | ทำอะไร |
|---|---|---|---|
| **PKT 1.29.0** | `792563f` | Run3 v28(136): CsvColumnOrder_ResultsFirst | TTC/PET/LDP: ตัวระบุ → ผลหลักและระดับความเสี่ยง → รายละเอียด → QC_Flag (ชื่อคอลัมน์ไม่เปลี่ยน) |
| **PKT 1.29.1** | (commit นี้) | PKT 1.29.1: Changelog_CloudCommits134to136 | เพิ่มงานเซสชัน cloud (v28(134)–(136)) เข้าตาราง ตั้งชื่อ commit แบบ PKT ต่อจากนี้ |
