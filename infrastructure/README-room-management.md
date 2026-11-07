# เอกสารโครงสร้างพื้นฐานระบบจัดการห้อง (Room Management Infrastructure V5)

## 1. ภาพรวม

เอกสารนี้อธิบายโครงสร้างพื้นฐานของระบบจัดการห้อง สำหรับโครงการ CSTU Room Booking V5 ซึ่งพัฒนาโดยสมาชิก Person 4

ระบบส่วนนี้รองรับการจัดการข้อมูลห้อง การตั้งค่าห้อง และการอัปโหลดรูปภาพห้อง โดยใช้ AWS Serverless Application Model (AWS SAM) และ AWS CloudFormation ในการกำหนดและจัดการโครงสร้างพื้นฐาน

## 2. ขอบเขตความรับผิดชอบของ Person 4

Person 4 รับผิดชอบการพัฒนาส่วนต่าง ๆ ดังนี้

- Manage Room Lambda
- Room Configuration Lambda
- Room Image Upload Lambda
- กำหนด IAM Permissions สำหรับ Lambda
- กำหนด Environment Variables สำหรับ Database และ S3
- กำหนด VPC Configuration สำหรับ Lambda ที่เชื่อมต่อ Database
- จัดการ Infrastructure Deployment และเตรียมความพร้อมสำหรับ Integration

## 3. โครงสร้างไฟล์ของโปรเจกต์

```text
infrastructure/
├── modules/
│   └── room-management.yaml
├── samconfig.toml
└── README-room-management.md

lambda/
├── manage_room/
│   ├── lambda_function.py
│   └── requirements.txt
├── room_configuration/
│   ├── lambda_function.py
│   └── requirements.txt
└── room_image_upload/
    └── lambda_function.py

scripts/
├── build-room-management.sh
└── validate-room-management.sh

tests/
└── test_room_management_template.py
```

## 4. Lambda Functions

ใน Module นี้ประกอบด้วย AWS Lambda ทั้งหมด 3 ตัว

| Lambda Function | หน้าที่ |
|---|---|
| ManageRoomFunction | จัดการข้อมูลห้อง |
| RoomConfigurationFunction | จัดการการตั้งค่าห้อง |
| RoomImageUploadFunction | จัดการการอัปโหลดรูปภาพห้องไปยัง Amazon S3 |

การตั้งค่าพื้นฐานของ Lambda ทั้ง 3 ตัว

- Runtime: Python 3.13
- Architecture: x86_64
- Handler: `lambda_function.lambda_handler`

### 4.1 Dependencies

| Lambda | Dependencies |
|---|---|
| manage_room | PyMySQL 1.2.3 |
| room_configuration | PyMySQL 1.2.3 |
| room_image_upload | ไม่มี requirements.txt เพิ่มเติม |

## 5. การกำหนดค่า AWS Infrastructure

### 5.1 Amazon RDS

Manage Room และ Room Configuration เชื่อมต่อกับฐานข้อมูล Amazon RDS MySQL ที่มีอยู่แล้ว

ค่าที่ใช้ในการเชื่อมต่อฐานข้อมูล ได้แก่

| Environment Variable | ค่า |
|---|---|
| DB_HOST | Endpoint ของ CSTU RDS |
| DB_NAME | cstu_room_db |
| DB_PORT | 3306 |
| DB_USER | admin |
| DB_PASSWORD | กำหนดระหว่าง Deployment |

รหัสผ่านฐานข้อมูลกำหนดเป็น CloudFormation Parameter โดยใช้ `NoEcho: true` เพื่อไม่ให้แสดงค่า Parameter ในผลลัพธ์บางส่วนของ CloudFormation

ห้ามบันทึกรหัสผ่านลงใน Source Code หรือ Commit ลง Git Repository

### 5.2 Amazon VPC

Lambda ที่เชื่อมต่อฐานข้อมูลจะถูกกำหนดให้อยู่ภายใน VPC ได้แก่

- ManageRoomFunction
- RoomConfigurationFunction

ใช้ Security Group และ Subnets ที่กำหนดไว้สำหรับการเชื่อมต่อกับฐานข้อมูล

ส่วน RoomImageUploadFunction ไม่จำเป็นต้องกำหนด VPC Configuration

### 5.3 Amazon S3

RoomImageUploadFunction ใช้ Amazon S3 Bucket ที่มีอยู่แล้ว

ชื่อ Bucket:

`cstu-room-images1`

กำหนด Environment Variable ดังนี้

`IMAGE_BUCKET`

Lambda ได้รับสิทธิ์ IAM สำหรับการอัปโหลดไฟล์ด้วย Action:

- `s3:PutObject`

โดยจำกัด Resource ให้อยู่ภายใน Bucket ที่กำหนดเท่านั้น

### 5.4 IAM Permissions

กำหนดสิทธิ์ให้ Lambda แต่ละตัวตามหน้าที่การทำงาน

| Lambda Function | IAM Permissions |
|---|---|
| ManageRoomFunction | AWSLambdaBasicExecutionRole และ AWSLambdaVPCAccessExecutionRole |
| RoomConfigurationFunction | AWSLambdaBasicExecutionRole และ AWSLambdaVPCAccessExecutionRole |
| RoomImageUploadFunction | AWSLambdaBasicExecutionRole และ S3 PutObject Permission |

สิทธิ์เหล่านี้รองรับการบันทึก Log ผ่าน CloudWatch การจัดการ Network Interface สำหรับ Lambda ที่อยู่ใน VPC และการอัปโหลดรูปภาพไปยัง S3

## 6. การตั้งค่า Deployment

ไฟล์ตั้งค่าการ Deploy ของ AWS SAM อยู่ที่

`infrastructure/samconfig.toml`

ค่าที่กำหนดไว้ ได้แก่

| รายการ | ค่า |
|---|---|
| Stack Name | cstu-room-booking-v5-dev |
| AWS Region | us-east-1 |
| Environment | dev |
| Database Name | cstu_room_db |
| Image Bucket | cstu-room-images1 |

รหัสผ่านฐานข้อมูลต้องกำหนดอย่างปลอดภัยในขั้นตอน Deployment และห้ามเพิ่มลงใน `samconfig.toml` หรือ Git Repository

## 7. การตรวจสอบและ Build

ให้รันคำสั่งจาก Root Directory ของโปรเจกต์

### 7.1 ตรวจสอบ SAM Template

```bash
sam validate --lint \
  --template-file infrastructure/modules/room-management.yaml
```

### 7.2 Build Lambda Functions

```bash
sam build \
  --template-file infrastructure/modules/room-management.yaml
```

### 7.3 รัน Unit Tests

```bash
python -m pip install -r tests/requirements-test.txt

python -m unittest discover \
  -s tests \
  -p "test_room_management_template.py" \
  -v
```

หรือใช้ Script ที่เตรียมไว้

```bash
bash scripts/validate-room-management.sh
```

```bash
bash scripts/build-room-management.sh
```

## 8. สถานะการ Deployment

Module Room Management ได้รับการ Deploy สำเร็จแล้ว

CloudFormation Stack:

`cstu-room-booking-v5-dev`

Lambda Functions ที่ถูก Deploy ได้แก่

1. `cstu-v5-manage-room-dev`
2. `cstu-v5-room-configuration-dev`
3. `cstu-v5-room-image-upload-dev`

ตรวจสอบแล้วว่า Lambda ทั้ง 3 ตัวอยู่ในสถานะ Active

## 9. สถานะการ Integration

ในระหว่างที่สมาชิกคนอื่นกำลังพัฒนา Infrastructure ในส่วนที่รับผิดชอบ Person 4 ได้พัฒนาและ Deploy Room Management Module แยกไว้ก่อน เพื่อเตรียมพร้อมสำหรับการรวมระบบในภายหลัง

งานที่เหลือในขั้นตอน Integration ได้แก่

- รวม Resource ของสมาชิกทุกคนเข้าใน `infrastructure/template.yaml`
- เชื่อมต่อ API Gateway Routes เข้ากับ V5 Lambda Functions
- ตรวจสอบการทำงานร่วมกับ Component ของสมาชิกคนอื่น
- ทดสอบการทำงานแบบ End-to-End

ก่อนแก้ไข API Gateway ต้องตรวจสอบ Routes และ Authorizers ที่มีอยู่เดิม เพื่อหลีกเลี่ยงการสร้าง Authorizer ซ้ำหรือกระทบ Resource ที่ใช้งานอยู่ โดยต้องได้รับการยืนยันจากทีมก่อนดำเนินการ

## 10. ข้อควรระวังด้านความปลอดภัย

- ห้าม Commit รหัสผ่านฐานข้อมูล AWS Credentials หรือข้อมูลลับอื่น ๆ ลง Git Repository
- กำหนด IAM Permissions ตามหลัก Least Privilege
- จำกัดสิทธิ์ S3 ให้เฉพาะ Bucket และ Resource ที่จำเป็น
- ตรวจสอบผลกระทบก่อนแก้ไข AWS Resources ที่มีอยู่
- ห้ามจัดเก็บรหัสผ่านฐานข้อมูลไว้ใน Source Code หรือไฟล์ Configuration ที่ Commit ลง Repository