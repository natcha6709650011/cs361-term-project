# Booking No-show Lambda (V4)

## Purpose
Marks approved bookings as `no_show` when they have not checked in within 30 minutes after `start_time`.

## AWS setup
1. Create a Lambda function named `cstu-booking-no-show`.
2. Runtime: Python 3.12 (or the same supported runtime used by the project).
3. Upload `lambda_function.py` and attach the existing PyMySQL Lambda Layer.
4. Set `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME=cstu_room_db`, and `DB_PORT=3306`.
5. Give the Lambda network access to the RDS instance.
6. Create an EventBridge Scheduler/Rule with `rate(1 minute)` targeting this Lambda.
7. Grant EventBridge permission to invoke the Lambda.

The Lambda only updates `bookings.status` from `approved` to `no_show`. Existing room-availability logic excludes every status except `pending` and `approved`, so the room becomes available again after the No-show transaction commits.

## Safety
- The database query uses row locks and a conditional update.
- Repeated invocations are idempotent.
- A booking already checked in is not changed to No-show.
- The API independently enforces the 30-minute cutoff, so a late check-in is rejected even if the scheduled job has not run yet.
