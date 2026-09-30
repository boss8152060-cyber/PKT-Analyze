# plan.md — แผนงานและสถานะ

> อัปเดตไฟล์นี้ทุกครั้งที่งานเปลี่ยนสถานะ (กฎอยู่ใน `CLAUDE.md`)
> รายละเอียดของแต่ละข้อ (เลขข้อ #) ดูใน `PROJECT_OVERVIEW.md` หัวข้อ 2
> สถานะ: `[ ]` รอทำ · `[~]` กำลังทำ · `[x]` เสร็จ (ระบุเวอร์ชัน/วันที่)

## ▶ ทำต่อจากตรงนี้

- **สถานะปัจจุบัน:** ข้อ 1.1–1.4 แก้โค้ดแล้ว (v27(1)–v27(4)) — รอผู้ใช้รันจริงยืนยันก่อนใส่ `(PASS)`/tag
- **ขั้นถัดไป:** ข้อ 1.5 (เตือนเมื่อไฟล์ Zone มาจากวิดีโอคนละไฟล์/ความละเอียดต่างกัน — เพิ่มต่อใน `collect_run3_warnings()`) — commit ถัดไปใช้ `Run3 v27(5): ...`; ผู้ใช้รันโปรแกรมกับวิดีโอสั้นเพื่อยืนยัน 1.1–1.4 และควรวาด Line 1–6 + กรอก Reference Line Mapping เพื่อให้ Y3 ได้ข้อมูล
- **ไฟล์โค้ดปัจจุบัน:** `PKStudio.py` (ในโฟลเดอร์ repo `PK STUDIO/Run`; เท่ากับ v27 ล้วน ๆ ที่ tag `v27`)
- **ตั้งค่า git แล้ว:** ประวัติ 61 commits (Run0 → Run3 v27) นำเข้าแล้ว; รูปแบบ commit message ดู `CLAUDE.md`; ไฟล์เวอร์ชันเก่าสำรองที่ `PK STUDIO/_Run_backup_before_git/`
- **Remote (push):** `origin` = https://github.com/boss8152060-cyber/PKT-Project.git (push แล้ว: main + tag v27)

## เฟส 0 — เตรียมงาน

- [x] 0.1 ตั้งค่า git (ชื่อ, อีเมล) — ทำแล้ว (2026-09-29)
- [x] 0.2 `.gitignore` + `git init` ที่ `PK STUDIO/Run` (2026-09-29)
- [x] 0.3 นำเข้าไฟล์เวอร์ชันเก่า 61 ไฟล์เป็น 61 commits ของ `PKStudio.py` (ตรวจ hash ตรงทุก commit) และย้ายไฟล์เก่าไป `_Run_backup_before_git/` (2026-09-29)
- [x] 0.4 ตั้ง remote GitHub และ push ครั้งแรก + tag `v27` (2026-09-29)

## เฟส 1 — แก้บั๊กที่กระทบผลลัพธ์ (โค้ด v28)

- [x] 1.1 (#1) `last_exit_time` ไม่ถูกกำหนด → `Zone_Summary`/`total_zone_time` ผิด — แก้แล้วใน commit `Run3 v27(1)` (2026-09-30) **รอผู้ใช้รันจริงเพื่อยืนยัน** (ดูบันทึกด้านล่าง)
- [x] 1.2 (#9) Zone flicker — แก้แล้วใน `Run3 v27(2)` (2026-09-30) แบบ "ทำความสะอาดตอนสรุปผล" (`ZONE_FLICKER_MERGE_S = 0.10` s) ไม่แตะค่า zone ดิบใน Detection_Records; **รอผู้ใช้รันจริงยืนยัน**
- [x] 1.3 (#4) ตรวจว่าโซนที่เลือกมี polygon จริง (Zone 7) แล้วเตือนก่อนรัน — `Run3 v27(3)` (2026-09-30) เพิ่ม `collect_run3_warnings()` + กล่องยืนยัน "Continue anyway?" ตอนกด START; **รอผู้ใช้กด START ดูกล่องจริง**
- [x] 1.4 (#5) เตือนก่อนรันถ้า Y3 ไม่มี Line/Reference Mapping — `Run3 v27(4)` (2026-09-30) เพิ่มใน `collect_run3_warnings()`; **รอผู้ใช้กด START ดูกล่องจริง** (ตัว Y3 ยังไม่มีข้อมูลจนกว่าผู้ใช้วาด Line 1–6 และกรอก mapping เอง)
- [ ] 1.5 (#6) เตือนเมื่อไฟล์ Zone มาจากวิดีโอคนละไฟล์/ความละเอียดต่างกัน
- [ ] 1.6 (#7) เปลี่ยน FP16 จาก `quantize=16` เป็น `half=True` และทดสอบ
- [ ] 1.7 (#11) ทบทวน timestamp เริ่มที่ 1/fps

## เฟส 2 — คุณภาพข้อมูลและตัวชี้วัด

- [ ] 2.1 (#3) smoothing ตำแหน่ง + ตัด outlier ความเร็ว (Y6/Y7)
- [ ] 2.2 (#2) ทบทวน Y2 LDP (reference line ต่อโซน, ความกว้างเลน, สถิติ)
- [ ] 2.3 (#8) ปรับ tracker (track_buffer, match_threshold) / ลอง BoT-SORT / track stitching
- [ ] 2.4 (#15, #16) แยกสถิติ Y1 ติดลบ และ PET แบบ Crossing vs Merging/Diverging
- [ ] 2.5 (#10) นับ detection ที่ track_id = -1 ใน summary

## เฟส 3 — วิธีวิจัย/ตัวอย่าง

- [ ] 3.1 (#12) Batch mode หลายวิดีโอ + สรุปรวมข้ามคลิป
- [ ] 3.2 (#13) เอกสารที่มาของค่า starter + sensitivity analysis
- [ ] 3.3 (#14) กำหนดกฎ risk level รวม (ตัดสินใจกับอาจารย์/วิทยานิพนธ์)
- [ ] 3.4 (#8) ประเมิน tracking กับ ground truth (HOTA/IDF1) 1–2 คลิป

## เฟส 4 — โครงสร้างโค้ด

- [ ] 4.1 (#19) unit test ให้ฟังก์ชันคำนวณ Y1–Y7 (pytest)
- [ ] 4.2 (#20, #21) ลบโค้ดตาย, แก้ path ตั้งต้นเป็นแบบสัมพัทธ์
- [ ] 4.3 (#22, #23) queue แทน `root.after` จาก thread, ใช้ logging, เลิก `except: pass`
- [ ] 4.4 (#17) แยกโมดูล (`pkstudio/…`)
- [ ] 4.5 (#24, #25) จัดโฟลเดอร์ output ต่อรัน, ปรับประสิทธิภาพ

## บันทึกความคืบหน้า (ใหม่สุดอยู่บน)

| วันที่ | สิ่งที่ทำ | ไฟล์ที่เกี่ยวข้อง | ค้างอยู่ |
|---|---|---|---|
| 2026-09-30 | ข้อ 1.4: เพิ่มคำเตือน Y3 ใน `collect_run3_warnings()` — mapping ไม่ถูกต้อง / ไม่มีแถวของ Site_ID / ขาด mapping ของ movement ที่ขัดแย้ง / Line ที่ map ยังไม่ได้วาด; ย้าย `conflict_map` เป็นค่าคงที่ `RUN3_GAP_CONFLICT_MAP` ใช้ร่วมกับ `_run3_gap` (พฤติกรรมเดิม). ตรวจ: py_compile + mock 5 กรณี (template, ครบ, ขาดบางตัว, Line ไม่ได้วาด, รูปแบบผิด) ได้ผลตามคาด | `PKStudio.py` | ยังไม่ได้เปิด GUI จริง; ผู้ใช้ต้องวาด Line และกรอก mapping เองเพื่อให้ Y3 มีข้อมูล |
| 2026-09-30 | ข้อ 1.3: เพิ่ม `collect_run3_warnings()` (เตือนเมื่อโซนที่เลือกของ Y1/Y2/Y4/Y5/Y6-7 ไม่มี polygon, หรือเปิด Run 3 แต่ไม่ได้โหลด Zone เลย); `start_run` แสดง askokcancel ให้เลือกต่อ/ยกเลิก; เก็บใน `summary.diagnostics.preflight_warnings`. ตรวจ: py_compile + ทดสอบด้วย mock (Zone 1–6 → เตือน Zone 7 ของ 4 ตัวชี้วัด; ไม่มีโซน → เตือน; ครบ → ไม่เตือน) | `PKStudio.py` | ยังไม่ได้เปิด GUI จริง; ข้อ 1.4/1.5 จะเพิ่มคำเตือนในฟังก์ชันเดียวกัน |
| 2026-09-30 | ข้อ 1.2: เพิ่ม `collect_zone_visits`/`clean_zone_visits` — ตัดการกะพริบ A→B→A (B ≤ 0.10 s) และรวมการหลุดโซนสั้น ๆ (≤ 0.10 s); `ID_Zone_Summary` (zone_sequence, transitions, total time) และ `Zone_Summary` ใช้ visit ที่ทำความสะอาดแล้ว; ลบ `id_zone_history`; บันทึก `summary_flicker_merge_s` ใน JSON. ตรวจ: unit case 5 แบบผ่าน + จำลองจากข้อมูลจริง visits 159 → 139 (เช่น ID 49 จาก 4↔3 สลับ 8 รอบ เหลือ 2 รอบ; 1→6→5 ไม่ถูกแตะ) | `PKStudio.py` | ยังไม่ได้รันโปรแกรมจริง; Run 3 ยังใช้ zone ดิบรายเฟรม (ไม่กระทบ); ID 49 ยังสลับ 4↔3 เหลือ 2 รอบ (ช่วงนานกว่า 0.1 s) |
| 2026-09-30 | ข้อ 1.1: เก็บ `visits` (start,end) ต่อโซนต่อ ID + `last_inside_time`; Zone_Summary นับทุกการเข้าโซน (รวมที่ยังอยู่ตอนจบ), `total_zone_time_seconds` = ผลรวมทุก visit; เวลาออก = ตัวอย่างสุดท้ายที่อยู่ในโซน. ตรวจ: py_compile ผ่าน + จำลองซ้ำจาก `Output/Run3/Run_3_Detection_Records.csv` ได้ Zone 2 = 26 IDs (เดิม 1), Zone 6 = 41 IDs (เดิม 6), ID 1 ใช้เวลาในโซน 15.4 s (เดิม 0) | `PKStudio.py` | ยังไม่ได้รันโปรแกรมจริง; entries มากกว่า IDs เพราะ zone flicker (ข้อ 1.2) |
| 2026-09-29 | ตรวจ v27, เขียน overview, CLAUDE.md, plan.md, GIT_GUIDE.md; git init + import 61 commits (`Run0` … `Run3 v27`) + .gitignore + tag v27 | `PROJECT_OVERVIEW.md`, `CLAUDE.md`, `plan.md`, `GIT_GUIDE.md` | ยังไม่แก้โค้ด, push ขึ้น GitHub แล้ว |
