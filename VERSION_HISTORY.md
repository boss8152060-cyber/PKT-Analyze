# VERSION_HISTORY — ชื่อเวอร์ชัน PKT ของทุก commit

> **สถานะ (2026-10-07):** ชื่อ `PKT 1.x.y` ในตารางนี้คือชื่อที่กำหนดให้ commit เดิมแต่ละอัน **ประวัติใน git ยังใช้ชื่อเดิม (`Run3 v28(NNN)` ฯลฯ)** เพราะการแก้ชื่อ commit ที่ push แล้วต้อง force push ทับ `main` และ tag ซึ่งเครื่อง cloud ของ Claude ทำไม่ได้ (ระบบปฏิเสธการ push tag/แก้ `main`, HTTP 403) — ใช้ตารางนี้ค้นหาว่า commit เดิมคือเวอร์ชันไหน; commit ใหม่ตั้งแต่ `PKT 1.78.0` เป็นต้นไปใช้ชื่อแบบใหม่แล้ว

**กติกาเลข `PKT 1.<หัวข้อ>.<ครั้งที่แก้>`:** เลขกลาง = หัวข้องาน (งานใหม่/คนละเรื่อง → +1 และครั้งที่แก้กลับเป็น 0, เช่น `1.1.0` → `1.2.0`); เลขท้าย = การแก้ต่อเนื่องในหัวข้อเดียวกัน (`1.1.0` → `1.1.1`); เลขแรก `1` = ชุดโปรเจ็คนี้

**หมายเหตุ:** คำอธิบายสั้น ๆ เขียนจากชื่อ commit เดิมและบันทึกงาน (`plan.md`) ไม่ได้อ่านโค้ดของแต่ละ commit ใหม่ทีละอัน; รหัสสั้น (hash) คือรหัสของ commit เดิม ค้นได้ด้วย `git show <รหัส>`


## 1.1.x — นับและสรุปการตรวจจับ (Run0)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.1.0` | Detection_Counting_Summary | โปรแกรมแรก: ตรวจจับและนับรถ พร้อมไฟล์สรุป | `2e09d95` Run0: Detection_Counting_Summary |

## 1.2.x — หน้าต่างตรวจจับ + ติดตาม (Run1)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.2.0` | GUI_Detection_Tracking | เพิ่มหน้าต่างโปรแกรม ตรวจจับรถและติดตาม ID | `42c4cb2` Run1: GUI_Detection_Tracking |

## 1.3.x — โซน (Run2 v2-v6)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.3.0` | Zones | เริ่มวาดโซนบนวิดีโอ | `221f713` Run2 v2: Zones |
| `1.3.1` | ZoneAssignment | กำหนดว่ารถอยู่โซนไหน | `6ed68a1` Run2 v3: ZoneAssignment |
| `1.3.2` | SimpleZone | ทำโซนให้ใช้ง่ายขึ้น | `9152b6f` Run2 v4: SimpleZone |
| `1.3.3` | CleanZoneUI | จัดหน้าจอโซนให้สะอาด | `c822938` Run2 v5: CleanZoneUI |
| `1.3.4` | FileZoneSettings | บันทึก/โหลดการตั้งค่าโซนเป็นไฟล์ | `1e92c2f` Run2 v6: FileZoneSettings |

## 1.4.x — จุดตำแหน่งรถ (Run2 v7-v10)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.4.0` | TrajectoryPosition | เลือกจุดตำแหน่งรถ (trajectory position) | `71ab06a` Run2 v7: TrajectoryPosition |
| `1.4.1` | TrajectoryPosition_CleanUI | จัดหน้าจอจุดตำแหน่งให้สะอาด | `d76f525` Run2 v8: TrajectoryPosition_CleanUI |
| `1.4.2` | SingleLabel | ใช้ป้ายกำกับเดียวต่อรถ | `48305bb` Run2 v9: SingleLabel |
| `1.4.3` | TrajectoryPointOnly | ใช้เฉพาะจุดตำแหน่งรถเป็นตัวกำหนดโซน | `ee1ffdc` Run2 v10: TrajectoryPointOnly |

## 1.5.x — การตั้งค่า/หน้าจอประมวลผล (Run2 v11-v12)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.5.0` | SettingsFixed | แก้การบันทึก/โหลดการตั้งค่า | `8620368` Run2 v11: SettingsFixed |
| `1.5.1` | RestoreProcessingUI | คืนหน้าจอระหว่างประมวลผล | `7169bd1` Run2 v12: RestoreProcessingUI |

## 1.6.x — CSV สามไฟล์ + แสดงโซน (Run2 v14-v17)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.6.0` | ThreeCSV | ผลลัพธ์เป็น CSV สามไฟล์ | `3d1ed51` Run2 v14: ThreeCSV |
| `1.6.1` | ZoneDisplay | ปรับการแสดงโซนในวิดีโอ | `be84313` Run2 v15: ZoneDisplay |
| `1.6.2` | ThreeCSV_Only | เขียนเฉพาะ CSV สามไฟล์ | `f89c499` Run2 v16: ThreeCSV_Only |
| `1.6.3` | NoPreset | เลิกใช้ค่าตั้งต้นสำเร็จรูป (preset) | `d8cb85c` Run2 v17: NoPreset |

## 1.7.x — รวมโปรแกรมวิเคราะห์ตัวชี้วัด (Run3 v1-v26)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.7.0` | Integrated | รวมการวิเคราะห์ตัวชี้วัด (Run 3) เข้าในโปรแกรม | `c6b3f79` Run3: Integrated |
| `1.7.1` | Defaults | ใส่ค่าตั้งต้นของ Run 3 | `e96f69d` Run3: Defaults |
| `1.7.2` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v2) | `7cc17cf` Run3 v2: Integrated_Defaults |
| `1.7.3` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v3) | `beda398` Run3 v3: Integrated_Defaults |
| `1.7.4` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v4) | `096a023` Run3 v4: Integrated_Defaults |
| `1.7.5` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v5) | `9dbd02f` Run3 v5: Integrated_Defaults |
| `1.7.6` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v6) | `7a06b18` Run3 v6: Integrated_Defaults |
| `1.7.7` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v7) | `d281065` Run3 v7: Integrated_Defaults |
| `1.7.8` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v8) | `ae7af22` Run3 v8: Integrated_Defaults |
| `1.7.9` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v9) | `a26b995` Run3 v9: Integrated_Defaults |
| `1.7.10` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v13) | `7dad670` Run3 v13: Integrated_Defaults |
| `1.7.11` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v14) | `b818ae8` Run3 v14: Integrated_Defaults |
| `1.7.12` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v16) | `339ec21` Run3 v16: Integrated_Defaults |
| `1.7.13` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v17) | `f6928ea` Run3 v17: Integrated_Defaults |
| `1.7.14` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v18) | `3c82dea` Run3 v18: Integrated_Defaults |
| `1.7.15` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v19) | `b489212` Run3 v19: Integrated_Defaults |
| `1.7.16` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v21) | `b83df5a` Run3 v21: Integrated_Defaults |
| `1.7.17` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v22) | `d1992c7` Run3 v22: Integrated_Defaults |
| `1.7.18` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v23) | `e7e5c4a` Run3 v23: Integrated_Defaults |
| `1.7.19` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v25) | `6f03c0c` Run3 v25: Integrated_Defaults |
| `1.7.20` | Integrated_Defaults | รวมเวอร์ชันและค่าตั้งต้น (v26) | `520da23` Run3 v26: Integrated_Defaults |

## 1.8.x — Gap Acceptance แก้ไข + มุมมองการปรับเทียบ (v26 5.x)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.8.0` | GapFixed | แก้ Gap Acceptance | `c5b6b97` Run3 v26(5): GapFixed |
| `1.8.1` | GapFixed | แก้ Gap Acceptance ต่อ | `cee301e` Run3 v26(5.1): GapFixed |
| `1.8.2` | GapFixed_CalibrationView | แก้ Gap และเพิ่มมุมมองตรวจการปรับเทียบ | `8c7d1f9` Run3 v26(5.2): GapFixed_CalibrationView |
| `1.8.3` | GapFixed_CalibrationView | ปรับมุมมองตรวจการปรับเทียบ | `bf362eb` Run3 v26(5.3): GapFixed_CalibrationView |
| `1.8.4` | GapFixed_CalibrationView_TableOrganized | จัดตารางในมุมมองตรวจการปรับเทียบให้เป็นระเบียบ | `faa1b6f` Run3 v26(5.4): GapFixed_CalibrationView_TableOrganized |

## 1.9.x — Gap Acceptance แยกตามรถที่รอ/โซนตัดสินใจ (v26 5.5-5.10)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.9.0` | GapAcceptance_SubjectSpecific | Gap Acceptance แยกตามรถที่รอแต่ละแบบ | `8611735` Run3 v26(5.5): GapAcceptance_SubjectSpecific |
| `1.9.1` | GapAcceptance_Zone6StopState | เพิ่มสถานะรถหยุดที่โซน 6 | `81a6b88` Run3 v26(5.6): GapAcceptance_Zone6StopState |
| `1.9.2` | GapAcceptance_DecisionZones_1_4_6 | กำหนดโซนตัดสินใจ 1, 4, 6 | `b7820cc` Run3 v26(5.8): GapAcceptance_DecisionZones_1_4_6 |
| `1.9.3` | GapAcceptance_DecisionZoneWindow | ใช้ช่วงเวลาของโซนตัดสินใจ | `6ef502d` Run3 v26(5.10): GapAcceptance_DecisionZoneWindow |

## 1.10.x — ตารางเหตุการณ์รถร่วม (v26 5.11)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.10.0` | CommonVehicleEventMap | สร้างตารางเหตุการณ์ของรถร่วมกันทุกตัวชี้วัด | `ebe9ac2` Run3 v26(5.11): CommonVehicleEventMap |
| `1.10.1` | CommonVehicleEventMap_GapErrorFix (PASS) | แก้ข้อผิดพลาดของ Gap ในตารางเหตุการณ์ (ผู้ใช้ยืนยันผ่าน) | `9e51e20` Run3 v26(5.11.1): CommonVehicleEventMap_GapErrorFix (PASS) |

## 1.11.x — CSV แบบเรียบง่าย (v26 5.12-5.13.1)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.11.0` | CSV_Simplified | ทำ CSV ให้เรียบง่ายขึ้น | `4dd21af` Run3 v26(5.12): CSV_Simplified |
| `1.11.1` | CSV_SchemaFix | แก้โครงคอลัมน์ CSV | `1b0f3fd` Run3 v26(5.13.1): CSV_SchemaFix |

## 1.12.x — ความเร็วโซน 1-6 (v26 5.13.2)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.12.0` | SpeedZones1_6 | คิดความเร็วในโซน 1 ถึง 6 | `c6ef6ab` Run3 v26(5.13.2): SpeedZones1_6 |

## 1.13.x — จัดหน้าจอวิจัย (v26 5.14.1)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.13.0` | UI_Research_Organized (PASS) | จัดหน้าจอตัวชี้วัดให้เป็นระเบียบ (ผู้ใช้ยืนยันผ่าน) | `b8c8236` Run3 v26(5.14.1): UI_Research_Organized (PASS) |

## 1.14.x — Gap Acceptance ผลแบบไบนารี สองขั้น (v26 5.14.5-5.14.8)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.14.0` | GapAcceptance_BinaryOnly_CleanDiagnostics | Gap ให้ผลแบบยอมรับ/ปฏิเสธอย่างเดียว และข้อมูลวินิจฉัยสะอาด | `dd25c1b` Run3 v26(5.14.5): GapAcceptance_BinaryOnly_CleanDiagnostics |
| `1.14.1` | GapAcceptance_BinaryProgress | แสดงความคืบหน้าของ Gap แบบไบนารี | `25c3ea6` Run3 v26(5.14.6): GapAcceptance_BinaryProgress |
| `1.14.2` | GapAcceptance_BinaryProgress_Fix | แก้ความคืบหน้า Gap แบบไบนารี | `b04ae8b` Run3 v26(5.14.7): GapAcceptance_BinaryProgress_Fix |
| `1.14.3` | GapAcceptance_TwoStage (PASS) | Gap สองขั้น Access/Exit (ผู้ใช้ยืนยันผ่าน) | `3ed30b1` Run3 v26(5.14.8): GapAcceptance_TwoStage (PASS) |

## 1.15.x — ความเร็วตามเหตุการณ์ PET/Gap/LC (v26 5.14.9-5.14.10)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.15.0` | EventSpeed_PET_Gap_LC | ใส่ความเร็วตามเวลาเหตุการณ์ใน PET, Gap, Lateral Clearance | `db2b5c2` Run3 v26(5.14.9): EventSpeed_PET_Gap_LC |
| `1.15.1` | EventSpeed_PET_Gap_LC_Fix | แก้ความเร็วตามเหตุการณ์ | `dd85eef` Run3 v26(5.14.10): EventSpeed_PET_Gap_LC_Fix |

## 1.16.x — แก้ตารางเหตุการณ์ Gap (v26 5.14.11)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.16.0` | GapVehicleEventMap_Fix (PASS) | แก้ตารางเหตุการณ์รถร่วมของ Gap (ผู้ใช้ยืนยันผ่าน) | `1006a76` Run3 v26(5.14.11): GapVehicleEventMap_Fix (PASS) |

## 1.17.x — ฐานเวอร์ชัน v27

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.17.0` | Integrated_Defaults | รวมค่าตั้งต้นเป็น v27 (tag v27) | `a0de48d` Run3 v27: Integrated_Defaults |

## 1.18.x — เอกสารโปรเจ็คและกฎ git

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.18.0` | Docs_ProjectOverview_Plan_GitRules_Gitignore | เขียนภาพรวมโปรเจ็ค แผนงาน กฎ git และ .gitignore | `9a397dc` Docs: ProjectOverview_Plan_GitRules_Gitignore |
| `1.18.1` | Docs_PlanUpdate_RemoteOriginPushed | บันทึกว่า push ขึ้น remote แล้ว | `bb975a5` Docs: PlanUpdate_RemoteOriginPushed |

## 1.19.x — สรุปโซนและโซนกะพริบ (v27 1-2)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.19.0` | ZoneSummary_ExitTimeFix | แก้เวลาออกโซนในสรุปโซน | `88a603f` Run3 v27(1): ZoneSummary_ExitTimeFix |
| `1.19.1` | ZoneFlicker_SummaryCleanup | ล้างการกะพริบของโซนและทำสรุปให้สะอาด | `39247ce` Run3 v27(2): ZoneFlicker_SummaryCleanup |

## 1.20.x — คำเตือนก่อนรัน (v27 3-4)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.20.0` | Preflight_ZoneNotDefinedWarning | เตือนเมื่อโซนที่เลือกยังไม่ได้กำหนด | `2b78199` Run3 v27(3): Preflight_ZoneNotDefinedWarning |
| `1.20.1` | Preflight_GapMappingWarning | เตือนเมื่อ mapping ของเส้น Gap ไม่ครบ | `35fc982` Run3 v27(4): Preflight_GapMappingWarning |

## 1.21.x — แผนและข้อกำหนด v28

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.21.0` | Docs_PlanAdd_LineEditor_GapCrossingDedupe | เพิ่มแผนตัววาดเส้นและการตัดข้อมูลซ้ำของ Gap | `4fd32c9` Docs: PlanAdd_LineEditor_GapCrossingDedupe |
| `1.21.1` | Docs_SpecV28_NewIndicators_PlanPhaseV | เขียนข้อกำหนดตัวชี้วัดชุด v28 และแผนเฟส | `567bd69` Docs: SpecV28_NewIndicators_PlanPhaseV |
| `1.21.2` | Docs_SpecV28_AnswersRecorded | บันทึกคำตอบของผู้ใช้ลงข้อกำหนด | `f684c2f` Docs: SpecV28_AnswersRecorded |

## 1.22.x — Movement ใหม่ + ความกว้างเลน (v28 1)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.22.0` | MovementSequence_LaneWidthInputs | Movement 6 แบบจากลำดับโซน และช่องกรอกความกว้างเลน | `35838bc` Run3 v28(1): MovementSequence_LaneWidthInputs |
| `1.22.1` | Docs_SpecV28_NewIndicatorCodes_Y1toY6 | เขียนข้อกำหนดตัวชี้วัดพร้อมรหัสเดิม | `3c7d463` Docs: SpecV28_NewIndicatorCodes_Y1toY6 |

## 1.23.x — Speed ต่อโซนและ Movement (v28 2)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.23.0` | Y6Speed_ZoneAndMovement | คิดความเร็วต่อโซนและต่อ Movement | `2569b3e` Run3 v28(2): Y6Speed_ZoneAndMovement |

## 1.24.x — LDP เส้นอ้างอิงจุดเข้า-ออก (v28 3)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.24.0` | Y1LDP_ChordReference | LDP แบบใหม่ วัดจากเส้นจุดเข้า-ออกโซน | `7c4df56` Run3 v28(3): Y1LDP_ChordReference |

## 1.25.x — Lateral Clearance ตามทิศรถ (v28 4)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.25.0` | Y2LateralClearance_HeadingPerpendicular | ระยะห่างด้านข้างตั้งฉากกับทิศที่รถเคลื่อนที่ | `f7eb841` Run3 v28(4): Y2LateralClearance_HeadingPerpendicular |

## 1.26.x — PET + TTC โซน 3, 6 (v28 5)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.26.0` | Y5PET_Y4TTC_Zones3and6_SideCollision | PET และ TTC ในโซน 3, 6 รวมการชนด้านข้าง | `35c4e1d` Run3 v28(5): Y5PET_Y4TTC_Zones3and6_SideCollision |

## 1.27.x — Gap ข้ามเส้นครั้งแรก (v28 6)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.27.0` | Y3Gap_FirstCrossingOnly_V28Finalize | Gap นับการข้ามเส้นครั้งแรกครั้งเดียว และสรุป v28 | `3fb63ca` Run3 v28(6): Y3Gap_FirstCrossingOnly_V28Finalize |

## 1.28.x — เลิกรหัส Y (v28 7)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.28.0` | IndicatorNamesInsteadOfYCodes | เรียกตัวชี้วัดด้วยชื่อแทนรหัส Y | `1e5dc90` Run3 v28(7): IndicatorNamesInsteadOfYCodes |

## 1.29.x — นำคำตอบผู้ใช้มาใช้ (v28 8-9)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.29.0` | UserAnswers_GapTable_LDPAllClasses_TTCSideAdjustable_LCAllPairs | ตารางใครให้ทางใคร, LDP ทุกชนิดรถ, TTC ปรับได้, LC ทุกคู่ | `1d70004` Run3 v28(8): UserAnswers_GapTable_LDPAllClasses_TTCSideAdjustable_LCAllPairs |
| `1.29.1` | LDP_DivideByHalfWidth | LDP หารด้วยครึ่งความกว้าง (W/2) | `a9b02f9` Run3 v28(9): LDP_DivideByHalfWidth |

## 1.30.x — ตัววาดเส้นอ้างอิง (v28 10-11)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.30.0` | LineEditor_DrawReferenceLines | หน้าต่างวาดเส้นอ้างอิงของ Gap | `218b893` Run3 v28(10): LineEditor_DrawReferenceLines |
| `1.30.1` | ReferenceLineMapping_PrefilledSite8 | ใส่ Reference Line Mapping ของ Site 8 ไว้ล่วงหน้า | `162ce39` Run3 v28(11): ReferenceLineMapping_PrefilledSite8 |

## 1.31.x — ไฟล์โซนของโดรน

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.31.0` | Docs_ZoneFileDJI0426_VideoFacts | บันทึกข้อมูลไฟล์โซนและวิดีโอโดรน DJI_0426 | `5e4c27f` Docs: ZoneFileDJI0426_VideoFacts |

## 1.32.x — ใช้ CUDA/Python 3.12 (v28 12)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.32.0` | CUDA_PythonFallback_LauncherBat | สลับไปใช้ Python ที่มี CUDA อัตโนมัติ พร้อมไฟล์ .bat | `fad5c1d` Run3 v28(12): CUDA_PythonFallback_LauncherBat |
| `1.32.1` | Docs_CUDA_Python312_Launcher | บันทึกวิธีเปิดด้วย Python 3.12 | `357b024` Docs: CUDA_Python312_Launcher |

## 1.33.x — กรองแทร็กซ้ำ (v28 13)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.33.0` | DuplicateTrackFilter | กรองรถคันเดียวที่ได้สองไอดี | `346aced` Run3 v28(13): DuplicateTrackFilter |

## 1.34.x — อธิบายผลว่าง (v28 14)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.34.0` | ExplainEmptyOutputs_ZoneVideoMismatchWarning | บอกเหตุผลเมื่อผลว่าง และเตือนโซนไม่ตรงวิดีโอ | `025cc2d` Run3 v28(14): ExplainEmptyOutputs_ZoneVideoMismatchWarning |

## 1.35.x — Movement จากการเห็นครั้งแรก (v28 15)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.35.0` | MovementFirstVisitFallback | จับ Movement ด้วยลำดับการเห็นครั้งแรกเมื่อไม่ชัด | `1dfbde7` Run3 v28(15): MovementFirstVisitFallback |

## 1.36.x — Gap Acceptance แบบสองขั้น PASS (v28 16)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.36.0` | Docs_GapAcceptance_PASSDesign_WaitZones1356 | เขียนแบบ Gap ที่ผ่านแล้ว โซนรอ 1, 3, 5, 6 | `3f9ed34` Docs: GapAcceptance_PASSDesign_WaitZones1356 |
| `1.36.1` | GapAcceptance_TwoStagePASS_LineOptional | Gap สองขั้นแบบ PASS เส้น Line เป็นตัวเลือก | `0313954` Run3 v28(16): GapAcceptance_TwoStagePASS_LineOptional |

## 1.37.x — แปลงเลขโซนไฟล์เก่า (v28 17-19)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.37.0` | ZoneRemap_OldZoneFileWorksWithNewMovements | แปลงเลขโซนของไฟล์เก่าให้ใช้กับ Movement ใหม่ | `aff23ea` Run3 v28(17): ZoneRemap_OldZoneFileWorksWithNewMovements |
| `1.37.1` | RevertToV28_13 | ถอยกลับไป v28(13) | `68dbf52` Run3 v28(18): RevertToV28_13 |
| `1.37.2` | RestoreV28_16_WithoutZoneRemap | คืน v28(16) โดยไม่มีตัวแปลงโซน | `f3d33ac` Run3 v28(19): RestoreV28_16_WithoutZoneRemap |

## 1.38.x — ลูกศร Movement ใน Excel (v28 20)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.38.0` | ExcelSafeMovementArrows | เขียน Movement ด้วยลูกศรกันเอ็กเซลแปลงเป็นวันที่ | `4f25a81` Run3 v28(20): ExcelSafeMovementArrows |

## 1.39.x — FP16 และเวลาเริ่ม 0 (v28 21)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.39.0` | FP16KeyByVersion_TimestampStartsAtZero | เลือก FP16 ตามเวอร์ชันและเริ่มเวลาที่ 0 | `2f164d0` Run3 v28(21): FP16KeyByVersion_TimestampStartsAtZero |

## 1.40.x — ธงความเร็วผิดปกติ (v28 22)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.40.0` | SpeedOutlierFlag_LC_PET_Stats_UntrackedCount | ธงความเร็วสูงผิดปกติ สถิติ LC/PET และนับแทร็กไม่มีไอดี | `fecb62c` Run3 v28(22): SpeedOutlierFlag_LC_PET_Stats_UntrackedCount |

## 1.41.x — รวมคลิป + ทดสอบความไว (v28 23)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.41.0` | MergeClips_SensitivityTool_ParametersDoc | เครื่องมือรวมคลิป, ทดสอบความไวของค่า, เอกสารพารามิเตอร์ | `14114da` Run3 v28(23): MergeClips_SensitivityTool_ParametersDoc |
| `1.41.1` | Docs_Phase3_UserDeferredRiskRuleSensitivityTracking | บันทึกงานเฟส 3 ที่ผู้ใช้เลื่อนไว้ | `c713dde` Docs: Phase3_UserDeferredRiskRuleSensitivityTracking |

## 1.42.x — คิวหน้าจอ เส้นทางสัมพัทธ์ และ log (v28 24)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.42.0` | UiQueue_RelativeDefaultPaths_NoAutoDelete_Logging | คิวอัปเดตหน้าจอ, path สัมพัทธ์, ไม่ลบไฟล์เอง, ใช้ logging | `120dd41` Run3 v28(24): UiQueue_RelativeDefaultPaths_NoAutoDelete_Logging |
| `1.42.1` | Docs_PlanCleanup_RemoveUserPendingItems | ล้างรายการแผนที่ผู้ใช้ค้างอยู่ | `c1f1016` Docs: PlanCleanup_RemoveUserPendingItems |
| `1.42.2` | Docs_RemovePlan_4.4_4.5 | ตัดข้อ 4.4, 4.5 ออกจากแผน | `79863d7` Docs: RemovePlan_4.4_4.5 |
| `1.42.3` | Docs_PlanFix_4.2_Note | แก้หมายเหตุข้อ 4.2 ในแผน | `5e90c24` Docs: PlanFix_4.2_Note |

## 1.43.x — รันหลายวิดีโอ (v28 25-26)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.43.0` | BatchRun_TrackerSweepTool | เครื่องมือรันหลายวิดีโอและลองค่า tracker | `2a6ee5c` Run3 v28(25): BatchRun_TrackerSweepTool |
| `1.43.1` | BatchRun_FolderMirrorOutput_CombinedPerLevel | เลือกเป็นโฟลเดอร์ ผลลัพธ์แยกตามต้นฉบับ | `1609290` Run3 v28(26): BatchRun_FolderMirrorOutput_CombinedPerLevel |

## 1.44.x — ช่วงเวลาวิเคราะห์ (v28 27-29)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.44.0` | AnalysisTimeWindow_RecordWindow_Core | แกนกำหนดช่วงเวลาวิเคราะห์และช่วงบันทึกวิดีโอ | `4ed3b01` Run3 v28(27): AnalysisTimeWindow_RecordWindow_Core |
| `1.44.1` | VideoPlayerDialog_SetTimeRangeInApp | หน้าต่างเครื่องเล่นวิดีโอกำหนดช่วงเวลา | `2f4dd0e` Run3 v28(28): VideoPlayerDialog_SetTimeRangeInApp |
| `1.44.2` | BatchWindow_PerClipTimeRangeAndRecording_PlanFile | หน้าต่างรันหลายคลิปกำหนดช่วงเวลาต่อคลิปและไฟล์แผน | `a1fffcd` Run3 v28(29): BatchWindow_PerClipTimeRangeAndRecording_PlanFile |

## 1.45.x — ผลลัพธ์ต่อคลิป (v28 30-31)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.45.0` | PerClipCsvOnly_AddToExistingPlace_DayFolder | CSV เฉพาะต่อคลิป เพิ่มเข้าที่เดิมได้ | `21472ea` Run3 v28(30): PerClipCsvOnly_AddToExistingPlace_DayFolder |
| `1.45.1` | MirrorAnyFolderStructure_FolderPerClip | สร้างโครงสร้างโฟลเดอร์ตามที่นำเข้า โฟลเดอร์ต่อคลิป | `9583738` Run3 v28(31): MirrorAnyFolderStructure_FolderPerClip |

## 1.46.x — ออกแบบหน้าจอใหม่ 4 ขั้น (v28 32-36)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.46.0` | UiRedesign_FourSteps_UnifiedClipList_RunBar | หน้าจอ 4 แท็บ รายการคลิปรวม แถบ START | `c5d9787` Run3 v28(32): UiRedesign_FourSteps_UnifiedClipList_RunBar |
| `1.46.1` | PlayerDialog_FitScreen_VisibleSaveButton | หน้าต่างเครื่องเล่นพอดีจอ มีปุ่มบันทึกเห็นชัด | `4af6470` Run3 v28(33): PlayerDialog_FitScreen_VisibleSaveButton |
| `1.46.2` | RemoveRedundantRecordCheckbox_SkipDoneWording | เอาช่องบันทึกวิดีโอที่ซ้ำออก | `ab48eb5` Run3 v28(34): RemoveRedundantRecordCheckbox_SkipDoneWording |
| `1.46.3` | CalibrationDialog_FixOverlappingFields_LayoutTest | แก้ช่องซ้อนกันในหน้าต่างปรับเทียบ พร้อมเทสต์เลย์เอาต์ | `8b7a743` Run3 v28(35): CalibrationDialog_FixOverlappingFields_LayoutTest |
| `1.46.4` | CalibrationShowsSavedPoints_PreviewFix_EmptyReasonsInBatchReport_TrajectoryWarning | หน้าต่างปรับเทียบแสดงจุดที่บันทึก แก้ภาพตัวอย่าง และเตือน trajectory | `99e11c2` Run3 v28(36): CalibrationShowsSavedPoints_PreviewFix_EmptyReasonsInBatchReport_TrajectoryWarning |

## 1.47.x — จุดตัดสินใจโซนและปรับเทียบรายโซน (v28 37-38)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.47.0` | ShowZoneDecisionPoint_CalibrationMeasureTool | แสดงจุดที่ใช้ตัดสินโซน และเครื่องมือวัดในการปรับเทียบ | `522e375` Run3 v28(37): ShowZoneDecisionPoint_CalibrationMeasureTool |
| `1.47.1` | PerZoneCalibration_OwnReferenceQuadPerZone | ปรับเทียบรายโซน แต่ละโซนมีกรอบอ้างอิงของตัวเอง | `d118ad6` Run3 v28(38): PerZoneCalibration_OwnReferenceQuadPerZone |

## 1.48.x — CSV รวมทุกคลิป (v28 39-40)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.48.0` | FileNamesWithClipName_CombinedCsvAllClips | ชื่อไฟล์มีชื่อคลิป และ CSV รวมทุกคลิป | `c8b16bc` Run3 v28(39): FileNamesWithClipName_CombinedCsvAllClips |
| `1.48.1` | CombinedCsv_UniqueIdKeys_ClipStart | CSV รวมมีคีย์ไอดีไม่ซ้ำและเวลาเริ่มคลิป | `8e62588` Run3 v28(40): CombinedCsv_UniqueIdKeys_ClipStart |

## 1.49.x — ต่อไอดีข้ามคลิป (v28 41-44)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.49.0` | ChainConsecutiveClips_IdsContinueAcrossClips | ต่อคลิปที่ติดกันให้ไอดีรถต่อเนื่อง | `6103d4d` Run3 v28(41): ChainConsecutiveClips_IdsContinueAcrossClips |
| `1.49.1` | ChainUsesWholeClips_IgnoresTimeRangeAndRecordRange | การต่อใช้คลิปทั้งคลิป ไม่สนช่วงเวลา | `5dea4be` Run3 v28(42): ChainUsesWholeClips_IgnoresTimeRangeAndRecordRange |
| `1.49.2` | PlainResultFileNames_NoClipNameInFiles | ชื่อไฟล์ผลลัพธ์แบบธรรมดา ไม่มีชื่อคลิปในไฟล์ | `9a50f3e` Run3 v28(43): PlainResultFileNames_NoClipNameInFiles |
| `1.49.3` | ContinueMeansTrackerCarriesOn_RangeAndRecordingStayPerClip | การต่อคือ tracker ทำต่อ ช่วงเวลาและการบันทึกยังเป็นต่อคลิป | `fc91f6c` Run3 v28(44): ContinueMeansTrackerCarriesOn_RangeAndRecordingStayPerClip |
| `1.49.4` | Docs_ContinueGapExplanation_R6Review | อธิบายช่องว่างของการต่อคลิปตามผลทบทวน | `0950e52` Docs: ContinueGapExplanation_R6Review |

## 1.50.x — ถอดรหัส/เข้ารหัสวิดีโอเบื้องหลัง (v28 45)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.50.0` | BackgroundDecodeAndEncode_AutoPrecisionFP32OnGTX16 | ถอดและเข้ารหัสวิดีโอเบื้องหลัง เลือกความแม่นอัตโนมัติ | `0e5f2e5` Run3 v28(45): BackgroundDecodeAndEncode_AutoPrecisionFP32OnGTX16 |

## 1.51.x — ตัดแทร็กซ้ำสั้น ๆ (v28 46)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.51.0` | ShortDuplicateTracks_RemovedFromAnalysis | ตัดแทร็กซ้ำช่วงสั้นออกจากการวิเคราะห์ | `991525c` Run3 v28(46): ShortDuplicateTracks_RemovedFromAnalysis |

## 1.52.x — ขีดจำกัดของ Lateral Clearance (v28 47-50)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.52.0` | LateralClearance_SidewaysLimit_AlongWindow_ClosestPerPair | จำกัดระยะด้านข้างและช่วงเคียงข้าง เลือกค่าใกล้สุดต่อคู่ | `0b8be69` Run3 v28(47): LateralClearance_SidewaysLimit_AlongWindow_ClosestPerPair |
| `1.52.1` | BottomDefault_OffsetWarning_ZoneFlickerMergeSetting | ค่าตั้งต้นจุดล่าง เตือนค่าชดเชย รวมโซนกะพริบ | `7eb98c3` Run3 v28(48): BottomDefault_OffsetWarning_ZoneFlickerMergeSetting |
| `1.52.2` | RevertTo_v28(46)_UndoLateralClearanceLimits_And_BottomDefault | ถอยกลับ v28(46) ยกเลิกขีดจำกัดและค่าตั้งต้นจุดล่าง | `a4c3f9a` Run3 v28(49): RevertTo_v28(46)_UndoLateralClearanceLimits_And_BottomDefault |
| `1.52.3` | LateralClearance_AlongWindow_And_MaxSidewaysOptions | คืนตัวเลือกช่วงเคียงข้างและระยะด้านข้างสูงสุด | `794561b` Run3 v28(50): LateralClearance_AlongWindow_And_MaxSidewaysOptions |

## 1.53.x — Topview รุ่นแรก (v28 51-52)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.53.0` | TopviewRecords_And_TopviewVideo_FromMetricPoints | ตารางพิกัดเมตรและวิดีโอมุมบน (Topview) | `a6f6f54` Run3 v28(51): TopviewRecords_And_TopviewVideo_FromMetricPoints |
| `1.53.1` | TopviewVideo_PlaysAtRealSpeed | วิดีโอ Topview เล่นเร็วเท่าจริง | `3f98895` Run3 v28(52): TopviewVideo_PlaysAtRealSpeed |

## 1.54.x — แผนที่อ้างอิงจากโดรน (v28 53-64)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.54.0` | ReferenceMap_DroneTopviewAsMap_CalibrationDialog | ใช้ภาพโดรนเป็นแผนที่อ้างอิงในหน้าต่างปรับเทียบ | `3de86c1` Run3 v28(53): ReferenceMap_DroneTopviewAsMap_CalibrationDialog |
| `1.54.1` | ReferenceMap_AcceptsVideoFrame_ThaiPaths | แผนที่รับเฟรมวิดีโอและพาธภาษาไทย | `5d8e7a0` Run3 v28(54): ReferenceMap_AcceptsVideoFrame_ThaiPaths |
| `1.54.2` | ReferenceMapDialog_ZoomAtPointer_Pan_ResetView_FrameSlider | ซูมที่เมาส์ เลื่อน รีเซ็ตมุมมอง สไลเดอร์เฟรม | `cfdb485` Run3 v28(55): ReferenceMapDialog_ZoomAtPointer_Pan_ResetView_FrameSlider |
| `1.54.3` | ReferenceMap_ZonesOverlay_PerPointError_DeletePoint_PoorCalibrationWarning | ซ้อนโซน แสดงความคลาดต่อจุด ลบจุด เตือนการปรับเทียบไม่ดี | `70e5128` Run3 v28(56): ReferenceMap_ZonesOverlay_PerPointError_DeletePoint_PoorCalibrationWarning |
| `1.54.4` | AdjustZonesOnMap_DragCorners_WriteMapfitZoneFile | ปรับโซนบนแผนที่ลากมุม เขียนไฟล์โซนใหม่ | `0045329` Run3 v28(57): AdjustZonesOnMap_DragCorners_WriteMapfitZoneFile |
| `1.54.5` | Revert_AdjustZonesOnMap_DragCorners_WriteMapfitZoneFile | ยกเลิกการปรับโซนบนแผนที่ (revert v28(57)) | `1b9a6cf` Revert "Run3 v28(57): AdjustZonesOnMap_DragCorners_WriteMapfitZoneFile" |
| `1.54.6` | ReferenceMap_UseZoneCornersAsCameraPoints_DragOnMap | ใช้มุมโซนเป็นจุดกล้อง ลากบนแผนที่ | `a6ef7e4` Run3 v28(58): ReferenceMap_UseZoneCornersAsCameraPoints_DragOnMap |
| `1.54.7` | ZonesAppearOnMap_LayoutFollowsCorners_RealDistancesBetweenCorners | โซนปรากฏบนแผนที่ ผังตามมุม ระยะจริงระหว่างมุม | `405d1d0` Run3 v28(59): ZonesAppearOnMap_LayoutFollowsCorners_RealDistancesBetweenCorners |
| `1.54.8` | ReferenceMap_AutoAlign_ECC_EdgeImages_BeforeAfterPreview | จัดแนวแผนที่อัตโนมัติด้วย ECC เทียบก่อน/หลัง | `4ec2787` Run3 v28(60): ReferenceMap_AutoAlign_ECC_EdgeImages_BeforeAfterPreview |
| `1.54.9` | SnapZonesToRoadSurface_Automatic_MapfitZoneFile | ดึงโซนไปชิดผิวถนนอัตโนมัติ เขียนไฟล์โซน | `78461b3` Run3 v28(61): SnapZonesToRoadSurface_Automatic_MapfitZoneFile |
| `1.54.10` | ReferenceMap_FreeCornersStayStill_SmallStepsBefore4Pairs_ClickVsDrag | มุมที่ยังว่างอยู่นิ่ง ขยับทีละน้อยก่อนครบ 4 คู่ แยกคลิก/ลาก | `1f45ed7` Run3 v28(62): ReferenceMap_FreeCornersStayStill_SmallStepsBefore4Pairs_ClickVsDrag |
| `1.54.11` | SnappedZones_CleanOutlines_OptionalCornerDragOnMap | โซนที่ดึงแล้วเส้นขอบสะอาด ลากมุมบนแผนที่เป็นตัวเลือก | `51bad6b` Run3 v28(63): SnappedZones_CleanOutlines_OptionalCornerDragOnMap |
| `1.54.12` | LensDistortion_EstimatedFromPairs_LeaveOneOutGuard_UsedInEveryMetricPoint | ประมาณความโค้งเลนส์จากคู่จุด ใช้กับทุกจุดเมตร | `e3bc2b3` Run3 v28(64): LensDistortion_EstimatedFromPairs_LeaveOneOutGuard_UsedInEveryMetricPoint |

## 1.55.x — ถอยกลับและปรับเทียบแบบเบา (v28 65-67)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.55.0` | RevertTo_v28(50)_BeforeTopview | ถอยกลับไป v28(50) ก่อนมี Topview | `0ddee4f` Run3 v28(65): RevertTo_v28(50)_BeforeTopview |
| `1.55.1` | Revert_RevertTo_v28(50)_BeforeTopview | ยกเลิกการถอยกลับ v28(65) | `f054e47` Revert "Run3 v28(65): RevertTo_v28(50)_BeforeTopview" |
| `1.55.2` | LeanGroundCalibration_Fig2Style_LensKeypointsReprojectionROI | ปรับเทียบพื้นถนนแบบเบา จุดเลนส์ ฉายซ้ำ ROI | `b492af8` Run3 v28(66): LeanGroundCalibration_Fig2Style_LensKeypointsReprojectionROI |
| `1.55.3` | Docs_PlanLog_v28(66)_LeanGroundCalibration | บันทึกแผนของ v28(66) | `e925060` Docs: PlanLog_v28(66)_LeanGroundCalibration |
| `1.55.4` | RevertTo_a6f6f54_TopviewWithoutDrone | ถอยกลับไป a6f6f54 Topview ไม่ใช้โดรน | `4278868` Run3 v28(67): RevertTo_a6f6f54_TopviewWithoutDrone |
| `1.55.5` | Revert_RevertTo_a6f6f54_TopviewWithoutDrone | ยกเลิกการถอยกลับ v28(67) | `62b72a3` Revert "Run3 v28(67): RevertTo_a6f6f54_TopviewWithoutDrone" |

## 1.56.x — Topview ให้เหมือนแผนที่ (v28 68-77)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.56.0` | TopviewLooksLikeAMap_FullBrightnessMap_FaintGrid_TranslucentVehicles | Topview ดูเหมือนแผนที่ สว่างเต็ม เส้นตารางจาง รถโปร่งใส | `c721de0` Run3 v28(68): TopviewLooksLikeAMap_FullBrightnessMap_FaintGrid_TranslucentVehicles |
| `1.56.1` | Docs_PlanLog_v28(67)_v28(68)_TopviewLooksLikeAMap | บันทึกแผน v28(67)-(68) | `dee0f5e` Docs: PlanLog_v28(67)_v28(68)_TopviewLooksLikeAMap |
| `1.56.2` | TopviewVideo_IsTheCameraVideoLensCorrectedAndLaidFlat | วิดีโอ Topview คือวิดีโอกล้องที่แก้เลนส์และวางราบ | `dd472c8` Run3 v28(69): TopviewVideo_IsTheCameraVideoLensCorrectedAndLaidFlat |
| `1.56.3` | RemoveDroneMapFeatures_BackToNoDroneTopview | เอาฟีเจอร์แผนที่โดรนออก กลับไป Topview แบบไม่มีโดรน | `5330d2c` Run3 v28(70): RemoveDroneMapFeatures_BackToNoDroneTopview |
| `1.56.4` | LensFisheyeFromStraightLines_EmptyRoadTopviewLaidFlat | ประมาณเลนส์ฟิชอายจากเส้นตรง Topview ถนนว่างวางราบ | `680cba7` Run3 v28(71): LensFisheyeFromStraightLines_EmptyRoadTopviewLaidFlat |
| `1.56.5` | LensDialog_PopupWhenNoResult | หน้าต่างเลนส์เด้งเมื่อไม่มีผล | `a7abdfb` Run3 v28(72): LensDialog_PopupWhenNoResult |
| `1.56.6` | TopviewBlankAboveGroundFarField_RoadOnly | Topview เว้นว่างเหนือพื้นถนน เหลือเฉพาะถนน | `ee03e65` Run3 v28(73): TopviewBlankAboveGroundFarField_RoadOnly |
| `1.56.7` | TopviewSameShapeAsVideo_VehiclePicturesOnFootprints | Topview รูปทรงเดียวกับวิดีโอ รูปรถบนรอยเท้า | `85d86a3` Run3 v28(74): TopviewSameShapeAsVideo_VehiclePicturesOnFootprints |
| `1.56.8` | TopviewFollowsDisplaySettings_ReferencePointOnly_NoDarkMask | Topview ตามค่าการแสดงผล แสดงเฉพาะจุดอ้างอิง ไม่มีหน้ากากมืด | `b1f5ed6` Run3 v28(75): TopviewFollowsDisplaySettings_ReferencePointOnly_NoDarkMask |
| `1.56.9` | MapStyleTopview_RoadLinesClickedOnCameraFrame | Topview แบบแผนที่ ตีเส้นถนนบนเฟรมกล้อง | `8f88b8d` Run3 v28(76): MapStyleTopview_RoadLinesClickedOnCameraFrame |
| `1.56.10` | TopviewNoVehiclePictures_ReferencePointOnly | Topview ไม่มีรูปรถ เหลือเฉพาะจุดอ้างอิง | `03417e9` Run3 v28(77): TopviewNoVehiclePictures_ReferencePointOnly |

## 1.57.x — ชนิดเส้นถนน (v28 78-80)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.57.0` | RoadLineTypes_WhiteYellowKerbBlueMotorcycleLane | ชนิดเส้นถนน ขาว เหลือง ขอบทาง น้ำเงินเลนมอเตอร์ไซค์ | `4fc88d3` Run3 v28(78): RoadLineTypes_WhiteYellowKerbBlueMotorcycleLane |
| `1.57.1` | KerbWhiteYellow_InsteadOfYellowBlack | ขอบทางลายขาว-เหลืองแทนเหลือง-ดำ | `36b3f93` Run3 v28(79): KerbWhiteYellow_InsteadOfYellowBlack |
| `1.57.2` | KerbStripeLength_0_5m | ความยาวลายขอบทาง 0.5 m | `07a5d59` Run3 v28(80): KerbStripeLength_0_5m |

## 1.58.x — เครื่องมือปรับเทียบรวม (v28 81-85)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.58.0` | OneToolForLensAndRoadLines | เครื่องมือเดียวสำหรับเลนส์และเส้นถนน | `e0b0f26` Run3 v28(81): OneToolForLensAndRoadLines |
| `1.58.1` | StraightMarkedRoadLinesSnapToBestLine | เส้นถนนที่ตีตรงเลื่อนเข้าหาเส้นที่ดีที่สุด | `6f557b8` Run3 v28(82): StraightMarkedRoadLinesSnapToBestLine |
| `1.58.2` | OneCalibrationWindow_LensGroundPointsRoadLines | หน้าต่างปรับเทียบเดียว จุดพื้น เลนส์ เส้นถนน | `d96c571` Run3 v28(83): OneCalibrationWindow_LensGroundPointsRoadLines |
| `1.58.3` | GroundFromParallelPerpendicularLines_ManyPointsLeastSquares | จุดพื้นจากเส้นขนาน/ตั้งฉากหลายจุดแบบกำลังสองน้อยสุด | `abb05f2` Run3 v28(84): GroundFromParallelPerpendicularLines_ManyPointsLeastSquares |
| `1.58.4` | ZoneCornersAsGroundPoints_TypeEdgeLengths | ใช้มุมโซนเป็นจุดพื้น กรอกความยาวขอบ | `58bf613` Run3 v28(85): ZoneCornersAsGroundPoints_TypeEdgeLengths |

## 1.59.x — ปรับเทียบด้วยมุมมองจากโซน (v28 86-93)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.59.0` | RevertTo_v28(50)_RemoveWholeTopviewSystem | ถอยกลับไป v28(50) เอาระบบ Topview ทั้งหมดออก | `9c90056` Run3 v28(86): RevertTo_v28(50)_RemoveWholeTopviewSystem |
| `1.59.1` | PerspectiveFromZones_EdgeLengths_QualityCheck | Perspective จากความยาวขอบโซน ตรวจคุณภาพ | `7390cfd` Run3 v28(87): PerspectiveFromZones_EdgeLengths_QualityCheck |
| `1.59.2` | CalibrationMethodChoice_ShowOnlyChosenBlock | เลือกวิธีปรับเทียบ แสดงเฉพาะกลุ่มที่เลือก | `ac9c4c0` Run3 v28(88): CalibrationMethodChoice_ShowOnlyChosenBlock |
| `1.59.3` | PerZoneCalibration_ZoneCornersAppearAsP1toP4 | ปรับเทียบรายโซน มุมโซนเป็นจุด P1-P4 | `0367fbc` Run3 v28(89): PerZoneCalibration_ZoneCornersAppearAsP1toP4 |
| `1.59.4` | PerZoneOwnTransform_AnyNumberOfCorners_OneSummaryLine | แต่ละโซนมีการแปลงของตัวเอง กี่มุมก็ได้ สรุปบรรทัดเดียว | `05fe553` Run3 v28(90): PerZoneOwnTransform_AnyNumberOfCorners_OneSummaryLine |
| `1.59.5` | CalibrationWindow_ZoneOutlinesAlwaysVisible_ChosenZoneYellow | หน้าต่างปรับเทียบแสดงเส้นโซนเสมอ โซนที่เลือกสีเหลือง | `a224dfe` Run3 v28(91): CalibrationWindow_ZoneOutlinesAlwaysVisible_ChosenZoneYellow |
| `1.59.6` | FourCornerWindowDoesNotCutDownZonesWithMoreCorners | หน้าต่าง 4 มุมไม่ตัดโซนที่มีมุมมากกว่า | `0b98f3a` Run3 v28(91): FourCornerWindowDoesNotCutDownZonesWithMoreCorners |
| `1.59.7` | RadialLensTrend_FromZoneLengths_UsedForEveryPoint | แนวโน้มรัศมีเลนส์จากความยาวโซน ใช้กับทุกจุด | `b86a3c0` Run3 v28(92): RadialLensTrend_FromZoneLengths_UsedForEveryPoint |
| `1.59.8` | RevertTo_v28(50)_RemoveCalibrationLayers | ถอยกลับไป v28(50) เอาชั้นการปรับเทียบออก | `9af983f` Run3 v28(93): RevertTo_v28(50)_RemoveCalibrationLayers |

## 1.60.x — ระนาบ X-Y (v28 51-52, 94-95)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.60.0` | TopviewRecords_And_TopviewVideo_FromMetricPoints | คืนตารางพิกัดเมตรและวิดีโอมุมบน | `7d2c854` Run3 v28(51): TopviewRecords_And_TopviewVideo_FromMetricPoints |
| `1.60.1` | TopviewVideo_PlaysAtRealSpeed | คืนให้วิดีโอ Topview เล่นเร็วเท่าจริง | `deaba91` Run3 v28(52): TopviewVideo_PlaysAtRealSpeed |
| `1.60.2` | PlainXYPlane_TrajectoryPng_And_Video_ReferencePointLabelsPerDisplaySettings | ระนาบ X-Y เรียบ ภาพเส้นทาง PNG และวิดีโอ ป้ายตามค่าการแสดงผล | `c85f3d2` Run3 v28(94): PlainXYPlane_TrajectoryPng_And_Video_ReferencePointLabelsPerDisplaySettings |
| `1.60.3` | OutsideZoneVehicles_ShowDotOrHide_NormalVideoAndXY | รถนอกโซน แสดงจุดหรือซ่อน ทั้งวิดีโอปกติและ X-Y (tag v28-95) | `6cc4225` Run3 v28(95): OutsideZoneVehicles_ShowDotOrHide_NormalVideoAndXY |
| `1.60.4` | Docs_PlanStatus_v28(95)_TagV28_95_OpenItems | บันทึกสถานะ v28(95) tag และรายการค้าง | `9c8be42` Docs: PlanStatus_v28(95)_TagV28_95_OpenItems |

## 1.61.x — จัดแนววิดีโอกับโดรน (v28 96-100)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.61.0` | AlignVideoToDronePlane_KindsLikeQgisGeoreferencer_LeaveOneOut | จัดแนววิดีโอเข้าระนาบโดรนแบบ QGIS leave-one-out | `4c91a9e` Run3 v28(96): AlignVideoToDronePlane_KindsLikeQgisGeoreferencer_LeaveOneOut |
| `1.61.1` | AlignTable_WorstPairsFirst_RedMark_DeleteWorst | ตารางจัดแนวเรียงคู่ที่แย่ก่อน มาร์กแดง ลบคู่ที่แย่สุด | `9511458` Run3 v28(97): AlignTable_WorstPairsFirst_RedMark_DeleteWorst |
| `1.61.2` | AlignReferenceLines_NPointsInVideo_HeadTailInDrone_XYAxes | จัดแนวด้วยเส้นอ้างอิงหลายจุด หัวท้ายในโดรน แกน X-Y | `b39eb3f` Run3 v28(98): AlignReferenceLines_NPointsInVideo_HeadTailInDrone_XYAxes |
| `1.61.3` | AlignTable_SortedByHonestError_WorstPairs_MeasureTest | ตารางจัดแนวเรียงตามความคลาดจริง วัดทดสอบ | `34fcc3c` Run3 v28(97): AlignTable_SortedByHonestError_WorstPairs_MeasureTest |
| `1.61.4` | AlignZoneMode_PinsFromVideo_PlaceOnDrone_NewZoneFile | โหมดจัดแนวโซน ปักหมุดจากวิดีโอ วางบนโดรน ไฟล์โซนใหม่ | `1a9b954` Run3 v28(98): AlignZoneMode_PinsFromVideo_PlaceOnDrone_NewZoneFile |
| `1.61.5` | RevertTo_v28(97)_RemoveAlignV28_98 | ถอยกลับไป v28(97) เอา v28(98) ออก | `46a51ec` Run3 v28(99): RevertTo_v28(97)_RemoveAlignV28_98 |
| `1.61.6` | AlignZonePins_VideoSideFromZoneFile_SkipUnsure | ปักหมุดโซนฝั่งวิดีโอจากไฟล์โซน ข้ามที่ไม่แน่ใจ | `c9c8aa2` Run3 v28(100): AlignZonePins_VideoSideFromZoneFile_SkipUnsure |

## 1.62.x — ตัวแก้ไขโซนและภาพ X-Y (v28 101-105)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.62.0` | XYPictureCentredOnZones | ภาพ X-Y อยู่กึ่งกลางโซน | `fad9372` Run3 v28(101): XYPictureCentredOnZones |
| `1.62.1` | PreviewXYPlaneBeforeRun_ZonesInMetres_EdgeLengths | ดูตัวอย่างระนาบ X-Y ก่อนรัน โซนเป็นเมตร ความยาวขอบ | `7a8396e` Run3 v28(102): PreviewXYPlaneBeforeRun_ZonesInMetres_EdgeLengths |
| `1.62.2` | ZoneEditorOnVideoDroneXYViews_PerpendicularShiftSnapNewZoneFile | ตัวแก้โซนบนวิดีโอ/โดรน/X-Y เลื่อนตั้งฉาก snap ไฟล์โซนใหม่ | `3d46ca9` Run3 v28(103): ZoneEditorOnVideoDroneXYViews_PerpendicularShiftSnapNewZoneFile |
| `1.62.3` | ZoneEditor_UseForAnalysisButton | ปุ่มใช้ไฟล์โซนนี้วิเคราะห์ | `793fe49` Run3 v28(104): ZoneEditor_UseForAnalysisButton |
| `1.62.4` | RemoveXYPreviewButton | เอาปุ่มดูตัวอย่าง X-Y ออก | `aaeae07` Run3 v28(105): RemoveXYPreviewButton |

## 1.63.x — รอยเท้ารถบนพื้นถนน (v28 106-107)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.63.0` | VehicleFootprint_OnRoadPlane_XYAndRoadsideVideo | วาดรอยเท้ารถบนระนาบถนน ใน X-Y และวิดีโอ | `61a4b31` Run3 v28(106): VehicleFootprint_OnRoadPlane_XYAndRoadsideVideo |
| `1.63.1` | RevertFootprint_BackToV28_105 | ถอยกลับรอยเท้ารถ ไป v28(105) | `66527d7` Run3 v28(107): RevertFootprint_BackToV28_105 |

## 1.64.x — TTC แบบเวกเตอร์ (ร่างและเขียน v28 108)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.64.0` | Docs_TTC_VectorFormulation_Draft_InSpec | ร่างสูตร TTC แบบเวกเตอร์ในข้อกำหนด | `18fa76d` Docs: TTC_VectorFormulation_Draft_InSpec |
| `1.64.1` | Docs_TTC_Draft_RemoveDGate | ตัดเกณฑ์ D ออกจากร่าง TTC | `3ec2285` Docs: TTC_Draft_RemoveDGate |
| `1.64.2` | Docs_TTC_Draft_FixDMention | แก้ที่กล่าวถึง D ในร่าง TTC | `8e3cbbb` Docs: TTC_Draft_FixDMention |
| `1.64.3` | Docs_TTC_ConflictType_ByAngle_SameAsPaper | ชนิดความขัดแย้งของ TTC ตามมุมเหมือนงานอ้างอิง | `9be2cfa` Docs: TTC_ConflictType_ByAngle_SameAsPaper |
| `1.64.4` | Docs_TTC_Draft_PairSelection_NoCrossingFilter | การเลือกคู่ของ TTC ไม่กรองด้วยจุดตัด | `246e5e9` Docs: TTC_Draft_PairSelection_NoCrossingFilter |
| `1.64.5` | VectorTTC_ConflictAngleType_NoMissGate | เขียน TTC เวกเตอร์ ชนิดตามมุม ไม่มีเกณฑ์พลาดกัน | `2f07b08` Run3 v28(108): VectorTTC_ConflictAngleType_NoMissGate |

## 1.65.x — ระดับความเสี่ยง (v28 109)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.65.0` | RiskLevels_SeminarTables_SingleSpeedScale_OverallLevel_EditableLimits | ระดับความเสี่ยงตามตารางสัมมนา สเกลความเร็วเดียว ระดับรวม ปรับเกณฑ์ได้ | `d1ae2fd` Run3 v28(109): RiskLevels_SeminarTables_SingleSpeedScale_OverallLevel_EditableLimits |

## 1.66.x — เกณฑ์ระยะพลาดกันของ TTC (v28 110-111)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.66.0` | TTC_MissGateRestored_SlowVehicleSkip_TTCFramesCSV | คืนเกณฑ์ระยะพลาดกัน ข้ามรถช้า ไฟล์ TTC_Frames.csv | `867d5ce` Run3 v28(110): TTC_MissGateRestored_SlowVehicleSkip_TTCFramesCSV |
| `1.66.1` | Docs_SpecAndPlan_TTCMissGate_v28_110 | บันทึกข้อกำหนดและแผนของเกณฑ์ v28(110) | `6dca929` Docs: SpecAndPlan_TTCMissGate_v28_110 |
| `1.66.2` | TTC_CrossingPathsArrivalGap_OtherPairsVector_BlankCutoffAll | TTC สำหรับทางตัดกันใช้ช่องห่างเวลาถึงจุดตัด คู่อื่นใช้เวกเตอร์ | `b8d68b3` Run3 v28(111): TTC_CrossingPathsArrivalGap_OtherPairsVector_BlankCutoffAll |

## 1.67.x — TTC สี่เหลี่ยมรถ (v28 112-115)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.67.0` | TTC_VehicleRectangles_TimeUntilBoxesTouch | TTC จากสี่เหลี่ยมรถ เวลาที่กล่องแตะกัน | `ae117c7` Run3 v28(112): TTC_VehicleRectangles_TimeUntilBoxesTouch |
| `1.67.1` | TTCRectangles_ShowInXYAndRoadsideVideo_Switches | แสดงสี่เหลี่ยม TTC ใน X-Y และวิดีโอข้างถนนด้วยสวิตช์ | `6aac019` Run3 v28(113): TTCRectangles_ShowInXYAndRoadsideVideo_Switches |
| `1.67.2` | TTCRectangles_OnNormalVideoNotThirdVideo_OptionsInTab1 | วาดสี่เหลี่ยม TTC ในวิดีโอปกติ ไม่สร้างวิดีโอที่สาม | `6a57886` Run3 v28(114): TTCRectangles_OnNormalVideoNotThirdVideo_OptionsInTab1 |
| `1.67.3` | DisplayTable_TwoColumns_EverySwitchPerVideo_VideoSwitchesOnOnePage | ตารางการแสดงผลสองคอลัมน์ ทุกสวิตช์ต่อวิดีโอ | `0ea949e` Run3 v28(115): DisplayTable_TwoColumns_EverySwitchPerVideo_VideoSwitchesOnOnePage |

## 1.68.x — TTC จุดชนที่คาดการณ์ (v28 116-119)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.68.0` | TTC_PointMethodDefault_ExpectedCollisionPointStoredAndDrawn | TTC ค่าตั้งต้นแบบจุดเดียวต่อรถ เก็บและวาดจุดชนที่คาดการณ์ | `034724b` Run3 v28(116): TTC_PointMethodDefault_ExpectedCollisionPointStoredAndDrawn |
| `1.68.1` | ExpectedCollisionPoint_IsPathIntersection_NotMidpoint | จุดชนคือจุดตัดของเส้นทาง ไม่ใช่จุดกึ่งกลาง | `809caa7` Run3 v28(117): ExpectedCollisionPoint_IsPathIntersection_NotMidpoint |
| `1.68.2` | TTC_MeetingPointMustBeInsideZone_EdgeMargin | จุดพบกันต้องอยู่ในโซน มีระยะเผื่อขอบ | `7314418` Run3 v28(118): TTC_MeetingPointMustBeInsideZone_EdgeMargin |
| `1.68.3` | TTC_ZoneFiltersCollisionPoint_NotTracking | โซนใช้กรองจุดชน ไม่ใช่กำหนดการแทร็ก | `e7f619f` Run3 v28(118): TTC_ZoneFiltersCollisionPoint_NotTracking |
| `1.68.4` | TTC_CollisionZoneMustBeOnPathOfBothVehicles_ZoneSequence | โซนจุดชนต้องอยู่ในเส้นทางของรถทั้งสองคัน ตามลำดับโซน | `a377274` Run3 v28(119): TTC_CollisionZoneMustBeOnPathOfBothVehicles_ZoneSequence |

## 1.69.x — PET ติ๊กโซนได้ทุกโซน (v28 120)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.69.0` | PET_AllZones_Selectable | PET เลือกได้ทุกโซน 1-7 | `c805795` Run3 v28(120): PET_AllZones_Selectable |

## 1.70.x — LDP ล็อกโซน 1 (v28 121)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.70.0` | LDP_Zone1_LockedWithNote | ช่อง Zone 1 ของ LDP กดไม่ได้ พร้อมหมายเหตุ | `3c55264` Run3 v28(121): LDP_Zone1_LockedWithNote |
| `1.70.1` | Merge_PR1_into_main | รวม PR #1 เข้า main | `3651c4a` Merge pull request #1 from boss8152060-cyber/claude/zen-davinci-wdlq4j |

## 1.71.x — PET ต้องมีจุดตัดจริง (v28 122-123)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.71.0` | PET_SameMovement_CountedIfTrajectoriesCross | PET นับรถ Movement เดียวกันได้ถ้าเส้นทางตัดกัน | `64de196` Run3 v28(122): PET_SameMovement_CountedIfTrajectoriesCross |
| `1.71.1` | PET_RequireRealTrajectoryCrossing_NoClosestApproachFallback | PET ทุกคู่ต้องมีจุดตัดจริง เลิกวิธีจุดใกล้สุด | `2f6a7cf` Run3 v28(123): PET_RequireRealTrajectoryCrossing_NoClosestApproachFallback |

## 1.72.x — PET ความเร็วขั้นต่ำ (v28 124-126)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.72.0` | PET_OptionalMinVehicleSpeed | ตัวกรองความเร็วขั้นต่ำของ PET ว่าง = ไม่จำกัด | `d48f8c5` Run3 v28(124): PET_OptionalMinVehicleSpeed |
| `1.72.1` | PET_MinSpeed_UsesSpeedAtCrossingPoint | ความเร็วของตัวกรองใช้ความเร็วตอนผ่านจุดตัด | `a370adb` Run3 v28(125): PET_MinSpeed_UsesSpeedAtCrossingPoint |
| `1.72.2` | PET_SpeedColumns_AtCrossingPoint | คอลัมน์ความเร็วของ PET เป็นความเร็วตอนผ่านจุดตัด | `5c00411` Run3 v28(126): PET_SpeedColumns_AtCrossingPoint |

## 1.73.x — PET จุดตัดและแสดงในวิดีโอ (v28 127)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.73.0` | PET_CrossingPointOnly_ShowCrossingInVideo | PET ใช้เวลาที่รถอยู่ที่จุดตัด เลิกรัศมี และแสดงจุดตัดในวิดีโอ | `a552bc9` Run3 v28(127): PET_CrossingPointOnly_ShowCrossingInVideo |
| `1.73.1` | Docs_SPEC_PET_TypoFix | แก้คำผิดในข้อกำหนด PET | `5b2401a` Docs: SPEC_PET_TypoFix |

## 1.74.x — PET พื้นที่ขัดแย้ง (v28 128)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.74.0` | PET_ConflictAreaRadius_WaPlusWbHalf_Toggle | พื้นที่ขัดแย้งรัศมี (W_A+W_B)/2 พร้อมสวิตช์เปิด/ปิด | `ecf95d4` Run3 v28(128): PET_ConflictAreaRadius_WaPlusWbHalf_Toggle |
| `1.74.1` | Merge_main_into_work_branch | รวม main เข้า branch งาน (PR #1 merge ไปแล้ว) | `9dbad9d` Merge main (PR #1 already merged) into claude/zen-davinci-wdlq4j |
| `1.74.2` | Merge_PR2_into_main | รวม PR #2 เข้า main | `ca64d56` Merge pull request #2 from boss8152060-cyber/claude/zen-davinci-wdlq4j |

## 1.75.x — จัดระเบียบ CSV (v28 129-131)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.75.0` | CSV_ErrorFileSeparate_GapColumnsRenamed | ไฟล์ Error แยกชื่อ และเปลี่ยนชื่อคอลัมน์ Gap Acceptance | `cc86417` Run3 v28(129): CSV_ErrorFileSeparate_GapColumnsRenamed |
| `1.75.1` | CSV_ConsistentColumnNames_TTCDetail_FrameSpeed_MovementCalibration | ชื่อคอลัมน์สม่ำเสมอ แยก TTC_Detail เพิ่ม Movement ใน LC | `0da0c82` Run3 v28(130): CSV_ConsistentColumnNames_TTCDetail_FrameSpeed_MovementCalibration |
| `1.75.2` | CSV_Cleanup_SpeedPerFrame_DropRedundantColumns_DetailFilesSwitch | ตัดข้อมูลซ้ำ Speed ต่อเฟรม สวิตช์ไฟล์ตรวจสอบ | `28d824e` Run3 v28(131): CSV_Cleanup_SpeedPerFrame_DropRedundantColumns_DetailFilesSwitch |

## 1.76.x — PET ชนิดความขัดแย้งแบบ TTC (v28 132)

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.76.0` | PET_ConflictType_ByTtcAngleRule | PET กำหนดชนิดความขัดแย้งจากมุมเหมือน TTC | `be2689d` Run3 v28(132): PET_ConflictType_ByTtcAngleRule |
| `1.76.1` | Merge_PR3_into_main | รวม PR #3 เข้า main | `0162a8d` Merge pull request #3 from boss8152060-cyber/claude/zen-davinci-wdlq4j |

## 1.77.x — เทสต์ e2e ตามการเปลี่ยน Speed

| เวอร์ชัน | ชื่อใหม่ | ทำอะไร | commit เดิม |
|---|---|---|---|
| `1.77.0` | Chore_E2eFollowsSpeedPerFrame | ปรับ e2e ให้ตรงกับ Speed ต่อเฟรมและไม่มีแถว Speed ใน Indicator_Summary | `5d896b5` Chore: e2e_run3 follows v28(131) (speed per frame in Speed.csv, no Speed rows in Indicator_Summary) |
