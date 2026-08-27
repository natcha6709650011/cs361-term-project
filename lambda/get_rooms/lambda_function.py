import json
#mock data รอdatabase

def lambda_handler(event, context):
    rooms = [
        {
            "room_id": "R001",
            "room_name": "ห้องเรียน 1",
            "room_type": "Classroom",
            "capacity": 40,
            "facilities": ["Projector", "Air Conditioner"],
            "available_time": "08:00-18:00"
        },
        {
            "room_id": "R002",
            "room_name": "ห้องปฏิบัติการคอมพิวเตอร์",
            "room_type": "Computer Laboratory",
            "capacity": 50,
            "facilities": ["Computer", "Projector", "Air Conditioner"],
            "available_time": "08:00-18:00"
        },
        {
            "room_id": "R003",
            "room_name": "ห้องประชุม 1",
            "room_type": "Meeting Room",
            "capacity": 20,
            "facilities": ["Projector", "Air Conditioner"],
            "available_time": "08:00-18:00"
        }
    ]

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(rooms, ensure_ascii=False)
    }