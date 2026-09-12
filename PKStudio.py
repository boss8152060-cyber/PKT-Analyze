import cv2
import csv
from ultralytics import YOLO

# 1. ตั้งค่าไฟล์ต้นทาง ปลายทาง และไฟล์ตารางสรุปผล
model_path = r"F:\motorcycle group project\PSU Transport Project 2026\Test\best.pt"          
video_path = r"F:\motorcycle group project\PSU Transport Project 2026\Test\Input\20260907_073251A_.mp4"  
output_path = r"F:\motorcycle group project\PSU Transport Project 2026\Test\Output\20260907_073251A_.mp4"
csv_output_path = r"F:\motorcycle group project\PSU Transport Project 2026\Test\Output\20260907_073251A_Summary.csv"

# 2. โหลดโมเดล
model = YOLO(model_path) 

# 3. เปิดวิดีโอและเตรียมการบันทึก
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

# 4. ตัวแปรสำหรับเก็บสถิติ
counted_ids = set()
vehicle_summary = {}
frame_count = 0

print("กำลังประมวลผลวิดีโอแบบเบื้องหลัง (ซ่อนหน้าต่างพรีวิวเพื่อความรวดเร็ว)...")
print("หากต้องการหยุดทำงานกลางคัน ให้กดคลิกที่หน้าต่าง Terminal ด้านล่าง แล้วกดปุ่ม 'Ctrl + C'")
print("--------------------------------------------------")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
        
    frame_count += 1

    # 5. ใช้ bytetrack.yaml ติดตามวัตถุ (ลดขนาดภาพเป็น 480 เพื่อให้รันไวขึ้นโดยไม่เสียความแม่นยำมาก)
    results = model.track(frame, persist=True, tracker="bytetrack.yaml", imgsz=480, verbose=False)

    # 6. ดึงข้อมูล ID และ Class ออกมาเพื่อนับ
    if results[0].boxes.id is not None:
        track_ids = results[0].boxes.id.int().cpu().tolist()
        class_ids = results[0].boxes.cls.int().cpu().tolist()
        
        for track_id, class_id in zip(track_ids, class_ids):
            class_name = model.names[class_id]
            
            # ถ้ารถ ID นี้เพิ่งโผล่มาเป็นครั้งแรก ให้บวกเลขเพิ่มในตารางสรุป
            if track_id not in counted_ids:
                counted_ids.add(track_id)
                vehicle_summary[class_name] = vehicle_summary.get(class_name, 0) + 1

    # 7. วาดกรอบและ ID ลงบนภาพ แล้วบันทึกไฟล์
    annotated_frame = results[0].plot()
    out.write(annotated_frame)
    
    # พิมพ์แจ้งความคืบหน้าทุกๆ 50 เฟรม
    if frame_count % 50 == 0:
        print(f"ประมวลผลไปแล้ว {frame_count} / {total_frames} เฟรม...")

cap.release()
out.release()
# ไม่ต้องใช้คำสั่ง cv2.destroyAllWindows() แล้วเพราะเราไม่ได้เปิดหน้าต่างพรีวิว

# 8. สรุปผลลัพธ์และเซฟไฟล์ CSV
print("\n==================================")
print("สรุปปริมาณยานพาหนะที่วิ่งผ่านกล้อง:")
print("==================================")

total_vehicles = 0
# เขียนไฟล์ CSV
with open(csv_output_path, mode='w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['Vehicle Type', 'Count']) # สร้างหัวตาราง
    
    for cls, count in vehicle_summary.items():
        print(f"- {cls}: {count} คัน")
        writer.writerow([cls, count]) # เขียนข้อมูลแต่ละประเภทลง CSV
        total_vehicles += count
    
    writer.writerow(['Total', total_vehicles]) # บรรทัดสรุปรวมด้านล่างสุด

print(f"รวมทั้งสิ้น: {total_vehicles} คัน")
print("==================================")
print(f"บันทึกวิดีโอผลลัพธ์ไว้ที่: {output_path}")
print(f"บันทึกไฟล์ตารางสรุปไว้ที่: {csv_output_path}")