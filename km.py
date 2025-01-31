from collections import Counter
import re
from datetime import datetime, timedelta

def parse_log_line(line):
    # Extract timestamp and event details from the log line
    match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{3})-*\d*\s+(.+)', line)
    if match:
        timestamp_str, event_details = match.groups()
        timestamp = datetime.strptime(timestamp_str, "%H:%M:%S.%f")
        return timestamp, event_details.split(",")
    return None, None

file_path = "km_test_2hours.txt"#".\WoWCombatLog-090224_211250.txt"
event_names = ["SPELL_AURA_APPLIED", "SPELL_AURA_REFRESH", "SPELL_AURA_APPLIED_DOSE"]

with open(file_path, "r", encoding="utf8") as file:
  lines = file.readlines()

crit_auto_counter = 0
km_events = []
unmatched_km_event = False

for line in lines:
  timestamp, event_details = parse_log_line(line)

  if "Khazak" not in event_details[2]:
     continue

  if timestamp and event_details[0] in event_names and event_details[9] == '51124':
    km_events.append({'time': timestamp})
    unmatched_km_event = True

  if timestamp and event_details[0] == "SWING_DAMAGE" and event_details[-3] == '1':

    crit_auto_counter += 1


    if unmatched_km_event:
      last_km_event = km_events[-1]
      # handles edge case when MH and OH both proc 
      # event order is [proc proc swing swing]
      if len(km_events) > 1 and "attempts" not in km_events[-2]:
        last_km_event = km_events[-2]

      time_diff = timestamp - last_km_event.get('time')
      if timedelta(milliseconds=0) <= time_diff <= timedelta(milliseconds=200):
        last_km_event.update({"attempts": crit_auto_counter})
        crit_auto_counter = 0
        unmatched_km_event = "attempts" not in km_events[-1]
      else:
        print(f"WARNING - KM AND MELEE EVENTS OUT OF ORDER at {timestamp.time()}")

# pop last event so we don't have to worry if the log broke off
km_events.pop()
attempt_counts = Counter([entry['attempts'] for entry in km_events])
sorted_attempt_counts = dict(sorted(attempt_counts.items()))

print("Attempts to proc | count")
for key, value in sorted_attempt_counts.items():
   print(f"        {key}        |  {value}")