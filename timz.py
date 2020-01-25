from datetime import timezone,datetime
dt = datetime.now()
timestamp = dt.replace(tzinfo=timezone.utc).timestamp()
print(int(timestamp))