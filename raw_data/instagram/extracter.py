import csv
import re

input_file = "廖允杰3.txt"    # 你的txt檔名
output_file = "廖允杰3.csv"   # 輸出的csv名稱

# 判斷是否為時間（如：6週, 3週, 1週, 2天）
def is_time_line(line):
    return bool(re.match(r"^\d+\s*(週|天|小時|分鐘)$", line.strip()))

# 判斷是否為 "username的大頭貼照"
def is_profile_pic_line(line):
    return "的大頭貼照" in line

rows = []
current_time = None
current_comment_lines = []
current_user = None

with open(input_file, "r", encoding="utf-8") as f:
    lines = [line.rstrip("\n") for line in f]

i = 0
while i < len(lines):
    line = lines[i].strip()

    # 1️⃣ 找到時間（每條留言都從時間開始）
    if is_time_line(line):
        # 若上一組資料完整，先存起來
        if current_time and current_user and current_comment_lines:
            rows.append({
                "time": current_time,
                "comments": "\n".join(current_comment_lines),
                "username": current_user
            })

        # 開始新的留言
        current_time = line
        current_comment_lines = []
        current_user = None
        i += 1
        continue

    # 2️⃣ 找到「xxx的大頭貼照」=留言結束
    if is_profile_pic_line(line):
        # 下一行就是 username
        if i + 1 < len(lines):
            current_user = lines[i + 1].strip()
            i += 2
            continue

    # 3️⃣ 其他都視為留言內容（可能多行）
    if line.strip() != "":
        current_comment_lines.append(line)

    i += 1

# 4️⃣ 處理最後一筆（因為沒有下一筆時間觸發 append）
if current_time and current_user and current_comment_lines:
    rows.append({
        "time": current_time,
        "comments": "\n".join(current_comment_lines),
        "username": current_user
    })

# 5️⃣ 輸出 CSV
with open(output_file, "w", encoding="utf-8", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["username", "comments", "time"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print(f"已成功輸出 CSV：{output_file}")
