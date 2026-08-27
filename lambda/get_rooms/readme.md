# Get Rooms Lambda

## Description

Lambda function สำหรับดึงข้อมูลห้องที่ใช้ในระบบจองห้อง

## API

**Method:** `GET`

**Endpoint:**

`/v1/rooms`

**API URL:**

https://aisw93f81a.execute-api.us-east-1.amazonaws.com/v1/rooms

## Current Status

ปัจจุบันใช้ **Mock Data** สำหรับทดสอบ API โดยมีข้อมูลห้องตัวอย่าง 3 ห้อง

ข้อมูลที่แสดงประกอบด้วย:

* Room ID
* Room Name
* Room Type
* Capacity
* Facilities
* Available Time

## AWS Services

* AWS Lambda — ประมวลผลและส่งข้อมูลห้อง
* Amazon API Gateway — เปิด API สำหรับให้ Frontend เรียกใช้งาน
* Amazon RDS MySQL — จะเชื่อมต่อภายหลังเพื่อใช้ข้อมูลจริง

## Future Update

เมื่อ Database ใน RDS พร้อม จะเปลี่ยนจาก Mock Data เป็นการดึงข้อมูลห้องจริงจาก RDS MySQL
