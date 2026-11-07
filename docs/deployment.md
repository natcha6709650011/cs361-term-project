# คู่มือการตรวจสอบและ Deploy ระบบ V5

## 1. วัตถุประสงค์

เอกสารนี้อธิบายขั้นตอนการตรวจสอบและเตรียม Deploy Infrastructure ของระบบ CS361 V5 ด้วย AWS SAM

## 2. เครื่องมือที่ต้องใช้

- AWS SAM CLI
- AWS CLI
- Python
- Git

## 3. การตรวจสอบ Template

เปิด Terminal ที่ Root Directory ของ Repository แล้วรัน

```bash
sam validate --lint -t infrastructure/template.yaml
```

ใช้ตรวจสอบความถูกต้องของ AWS SAM Template ก่อน Build

## 4. การ Build

รันคำสั่ง

```bash
sam build -t infrastructure/template.yaml
```

ใช้เตรียม Lambda และ Dependencies สำหรับการ Deploy

## 5. การ Deploy

การ Deploy ดำเนินการโดยผู้รับผิดชอบ AWS ของทีม หลังจากสมาชิกตรวจสอบ Template และผ่านการ Review แล้ว

ก่อน Deploy ต้องตรวจสอบ

- AWS Account และ Region
- CloudFormation Stack ที่จะใช้งาน
- การเปลี่ยนแปลง AWS Resources
- Environment Variables และ Secrets
- IAM Permissions
- การเชื่อมต่อกับ RDS และ S3

## 6. ข้อควรระวัง

- ห้ามนำ Password หรือ AWS Credentials ใส่ใน Repository
- ห้าม Deploy ทับระบบเดิมโดยไม่ตรวจสอบ Change Set
- ห้ามลบหรือเปลี่ยนแปลง Resource ที่ระบบเดิมใช้งานโดยไม่ได้รับอนุญาต
- ต้องทดสอบระบบหลัง Deploy ทุกครั้ง

## 7. การรายงานผล

สมาชิกแต่ละคนต้องแจ้งผลการตรวจสอบและ Build ของ Resource ที่ตนเองรับผิดชอบ เพื่อให้ผู้ดูแล Deployment ตรวจสอบก่อนรวมระบบ