"""Scheduled V4 booking lifecycle job.

Configure an EventBridge schedule (rate(1 minute)) to invoke this Lambda.
- APPROVED bookings without Check-in become NO_SHOW after the 30-minute grace period.
- CHECKED_IN bookings become COMPLETED automatically when end_time is reached.
No user-operated Check-out endpoint or timestamp is used.
"""

import json
import os
from datetime import datetime

import pymysql


def connect_database():
    connection = pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "cstu_room_db"),
        port=int(os.environ.get("DB_PORT", "3306")),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
    )

    # Booking DATETIME values are stored in Thailand local time.
    with connection.cursor() as cursor:
        cursor.execute("SET time_zone = '+07:00'")

    return connection


def lambda_handler(event, context):
    connection = connect_database()

    try:
        with connection.cursor() as cursor:
            # Find approved bookings that passed the 30-minute
            # Check-in grace period without being checked in.
            cursor.execute(
                """
                SELECT booking_id
                FROM bookings
                WHERE status = 'approved'
                  AND attendance_status = 'NOT_CHECKED_IN'
                  AND start_time <= DATE_SUB(NOW(), INTERVAL 30 MINUTE)
                ORDER BY start_time
                LIMIT 200
                FOR UPDATE
                """
            )

            booking_ids = [
                row["booking_id"]
                for row in cursor.fetchall()
            ]

            if booking_ids:
                placeholders = ",".join(
                    ["%s"] * len(booking_ids)
                )

                cursor.execute(
                    f"""
                    UPDATE bookings
                    SET status = 'no_show',
                        attendance_status = 'NO_SHOW',
                        no_show_at = NOW()
                    WHERE booking_id IN ({placeholders})
                      AND status = 'approved'
                      AND attendance_status = 'NOT_CHECKED_IN'
                    """,
                    booking_ids,
                )

                marked_no_show = cursor.rowcount
            else:
                marked_no_show = 0

            # Automatically complete bookings that were checked in
            # and have reached their reservation end time.
            # No manual Check-out is required.
            cursor.execute(
                """
                UPDATE bookings
                SET attendance_status = 'COMPLETED'
                WHERE status = 'approved'
                  AND attendance_status = 'CHECKED_IN'
                  AND end_time <= NOW()
                """
            )

            marked_completed = cursor.rowcount

        connection.commit()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Booking lifecycle scan completed",
                "marked_no_show": marked_no_show,
                "marked_completed": marked_completed,
                "checked_at": datetime.now().isoformat(
                    timespec="seconds"
                ),
            }),
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()