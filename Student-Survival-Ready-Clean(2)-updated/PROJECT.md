# Student Survival · Computer Programming Project

เว็บแอปสำหรับนักศึกษาวิศวกรรมศาสตร์ที่เปลี่ยนข้อมูลรายรับ–รายจ่ายให้เป็น “แผนเอาตัวรอด” รายวัน

## จุดเด่น
- Dashboard แบบกราฟ: ค่าใช้จ่าย 7 วันล่าสุด + หมวดที่ใช้มากที่สุด
- Budget Guard: เปรียบเทียบการใช้วันนี้กับงบที่ควรใช้ต่อวัน
- Runway: ประมาณจำนวนวันที่เงินคงเหลือจะรองรับจากค่าใช้จ่ายเฉลี่ย 7 วัน
- What-if Simulator: ทดลองใช้เงินต่อวันและจำนวนวันก่อนตัดสินใจ
- Allocation Lab: ทดลองแบ่งเงินเป็น อาหาร / เดินทาง / การเรียน / เงินสำรอง
- Emergency Reserve: ติดตามเป้าหมายเงินสำรอง
- บันทึกและลบรายการได้จากหน้าเดียว

## โครงสร้าง
ยึดโครงสร้าง assignment เดิม: `app.py`, `storage.py`, `check_project.py`, `pages/`, `templates/`, `models.py`, `data.json` และ `team.json`

`app.py`, `storage.py`, `templates/base.html`, `templates/_not_built.html`, `check_project.py` และ `test_pages.py` เป็นไฟล์ GIVEN ของ skeleton จึงคงไว้ตามข้อกำหนดของงาน

## หน้าเว็บ
- `/` หน้าแรก Student Survival
- `/page1` เข้าสู่ระบบ / สมัครสมาชิก
- `/page2` ศูนย์ควบคุม + กราฟ
- `/page3` ห้องวางแผน + Simulator + Allocation + เป้าหมาย + จัดการรายการ
- `/team` สมาชิกกลุ่ม

## ตรวจงาน
- `python -m pytest -q` → 4 passed
- `python check_project.py` → automated score 60/60
