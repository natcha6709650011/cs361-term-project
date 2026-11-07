# คู่มือการทำงาน Infrastructure V5

## 1. วัตถุประสงค์

โฟลเดอร์นี้ใช้จัดเก็บไฟล์ Infrastructure as Code (IaC) สำหรับโปรเจกต์ CS361 V5

เป้าหมายคือทำให้สามารถสร้างและปรับใช้ Infrastructure ของระบบได้ซ้ำด้วย Automation ลดการตั้งค่าด้วยตนเอง และลดความผิดพลาดจากการตั้งค่าไม่ตรงกัน

## 2. ไฟล์หลักสำหรับกำหนด Infrastructure

ไฟล์หลักที่สมาชิกทุกคนใช้ร่วมกันคือ

`infrastructure/template.yaml`

สมาชิกแต่ละคนต้องเพิ่ม AWS Resources ในไฟล์หลักนี้ตามส่วนที่ตนเองรับผิดชอบ

ไม่สร้างไฟล์ YAML แยกเป็นส่วนย่อยโดยตรง เว้นแต่ทีมจะตกลงใช้วิธีเชื่อม Template ที่ CloudFormation รองรับ

## 3. การแบ่งหน้าที่สมาชิก

| สมาชิก | หน้าที่รับผิดชอบ | Lambda |
|---|---|---|
| คนที่ 1 | ข้อมูลห้องและการค้นหาห้อง | get_rooms, get_detail, get_room_schedule, search_available_rooms |
| คนที่ 2 | การจองและการจัดการสถานะการจอง | booking, booking_facility_management, booking_no_show |
| คนที่ 3 | การเข้าสู่ระบบและการรักษาความปลอดภัย | cstu-user-auth, cstu-jwt-authorizer, cstu-room-permission |
| คนที่ 4 | การจัดการห้องและการรวมระบบ Deployment | manage_room, room_configuration, room_image_upload |

## 4. กติกาการทำงาน

1. สมาชิกแต่ละคนรับผิดชอบ AWS Resources ตามงานที่ได้รับมอบหมาย
2. ใช้ Lambda Source Code ที่มีอยู่ใน Repository ไม่สร้าง Lambda ซ้ำโดยไม่จำเป็น
3. ตรวจสอบ Handler, Runtime, Environment Variables และ Dependencies ก่อนกำหนดค่าใน Template
4. ห้ามใส่ Password, Token หรือ AWS Credentials ลงใน Git
5. กำหนด IAM Permissions เท่าที่จำเป็นต่อการทำงาน
6. ห้าม Deploy หรือแก้ไข Resource เดิมที่ใช้งานจริงโดยไม่ได้รับการตรวจสอบจากทีม
7. สมาชิกต้องตรวจสอบและทดสอบงานของตนเองก่อนส่ง Pull Request
8. หากต้องแก้ไข Resource ที่สมาชิกคนอื่นรับผิดชอบ ต้องแจ้งและตกลงกันก่อน

## 5. การตรวจสอบ Template

ตรวจสอบความถูกต้องของ Template ด้วยคำสั่ง

`sam validate --lint -t infrastructure/template.yaml`

Build โปรเจกต์ด้วยคำสั่ง

`sam build -t infrastructure/template.yaml`

## 6. การ Deploy

คนที่ 4 เป็นผู้ดูแลการรวม Template และดำเนินการ Deploy หลังจากตรวจสอบงานของสมาชิกและได้รับการยืนยันจากทีมแล้ว

ก่อน Deploy ต้องตรวจสอบผลกระทบต่อ AWS Resources เดิมทุกครั้ง