# Student Survival Security

ระบบเพิ่มชั้นป้องกันพื้นฐานสำหรับเว็บแอป Flask ได้แก่:

- CSRF token สำหรับคำขอ POST
- Session cookie แบบ HttpOnly และ SameSite=Lax
- Secret key สุ่มและเก็บแยกจาก source code ตามระบบของ skeleton
- Rate limit สำหรับการสมัคร/เข้าสู่ระบบ
- Password hashing แบบ PBKDF2-HMAC-SHA256
- Security headers: CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy และ Permissions-Policy
- จำกัดขนาด request และปิด Flask debug mode

> หมายเหตุ: `app.py` เป็นไฟล์ GIVEN ของ assignment จึงคงชื่อ environment variable และกลไก session เดิมไว้ เพื่อไม่ให้กระทบคะแนนตรวจโครงสร้าง
