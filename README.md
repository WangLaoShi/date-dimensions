# date-dimensions

将时间戳或日期时间展开为分析字段，支持 Excel 友好的返回值。需要 Python 3.10+，基础功能无需 pandas 或其他第三方包。

## 安装

```sh
pip install date-dimensions
pip install "date-dimensions[cn]"  # 可选，中国大陆节假日和调休
pip install "date-dimensions[lunar]"  # 可选，农历、生肖和四柱
pip install "date-dimensions[tz]"  # 可选，供缺少系统时区数据的环境使用
```

## 解析时间和提取字段

```python
from datetime import datetime

from date_dimensions import time_features

seconds = time_features(1700000000, unit="s")
millis = time_features(1700000000123, unit="ms")
utc = time_features("2023-11-14T22:13:20.123Z")
local = time_features(datetime(2023, 11, 15, 6, 13, 20, 123000))

assert millis == utc == local
assert seconds["dt"].microsecond == 0

fields = ("year", "month", "day", "hour", "minute", "second")
print(*(millis[field] for field in fields))  # 2023 11 15 6 13 20
```

数字时间戳须指定 `unit="s"` 或 `unit="ms"`。带时区的输入转换为上海时间，无时区的字符串和 `datetime` 按上海本地时间解释。

## 批量提取与周报分组

```python
from collections import Counter

from date_dimensions import time_features

events = ["2020-12-31 23:50:00", "2021-01-01 14:35:20", "2021-01-04 08:00:00"]
rows = [time_features(event) for event in events]

counts = Counter((row["iso_year"], row["weekofyear"]) for row in rows)
assert counts == {(2020, 53): 2, (2021, 1): 1}

row = rows[1]
print(row["hour_floor"])    # 2021-01-01 14:00:00+08:00
print(row["15min_floor"])   # 2021-01-01 14:30:00+08:00
print(row["ten_day_period"])  # 上旬
```

## 查询节假日与补班

先安装 `date-dimensions[cn]`，再开启日历查询。

```python
from date_dimensions import time_features_excel

holiday = time_features_excel("2024-02-12", include_cn_calendar=True)
makeup = time_features_excel("2024-02-18", include_cn_calendar=True)

assert holiday["is_holiday"] == "是"
assert holiday["is_workday"] == "否"
assert makeup["is_weekend"] == "是"
assert makeup["is_workday"] == "是"
assert makeup["is_makeup_workday"] == "是"
```

## 农历、生肖和四柱

安装 `date-dimensions[lunar]` 后，给任一函数传入 `include_lunar=True`。底层使用 [cnlunar](https://github.com/OPN48/cnlunar)，无需额外数据库。农历和四柱均按上海本地时间计算，支持公历 1901-02-19 至 2099-12-31。

```python
from date_dimensions import time_features_excel

row = time_features_excel("2024-02-10 14:35:20", include_lunar=True)
print("公历", row["date_only"])
print("农历", f'{row["lunar_year"]}年{row["lunar_month_name"]}{row["lunar_day_name"]}')
print("属相", row["zodiac"])
print("八字", *(row[field] for field in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar")))

assert (row["lunar_year"], row["lunar_month"], row["lunar_day"]) == (2024, 1, 1)
assert row["zodiac"] == "龙"
assert row["is_lunar_leap_month"] == "否"
```

开启后增加 11 个字段。农历年月日保留整数，闰月在普通版中为 `1` 或 `0`，在 Excel 版中为「是」或「否」。如果同时需要大陆放假和补班，安装 `date-dimensions[cn,lunar]` 并同时开启两个参数。

## 写入 Excel

如需直接生成 `.xlsx`，可额外安装 `openpyxl`（`pip install openpyxl`）。只获取字典时直接调用 `time_features_excel()` 即可。

```python
from openpyxl import Workbook

from date_dimensions import time_features_excel

rows = [
    time_features_excel("2024-02-12 14:35:20"),
    time_features_excel("2024-02-18 09:05:00"),
]
columns = list(rows[0])
workbook = Workbook()
sheet = workbook.active
sheet.title = "日期维度"
sheet.append(columns)
for row in rows:
    sheet.append([row[column] for column in columns])

for field in ("day_progress", "week_progress", "month_progress"):
    column_index = columns.index(field) + 1
    for row_index in range(2, sheet.max_row + 1):
        sheet.cell(row=row_index, column=column_index).number_format = "0.00%"

sheet.auto_filter.ref = sheet.dimensions
workbook.save("date_dimensions.xlsx")
```

## 返回字段

两个函数默认均返回以下 35 个字段。普通版的标记为 `1` 或 `0`，Excel 版为「是」或「否」。

| 类别 | 字段 |
| --- | --- |
| 基础 | `dt`、`year`、`month`、`day`、`hour`、`minute`、`second` |
| 日历 | `quarter`、`dayofweek`、`day_name`、`is_weekend`、`iso_year`、`weekofyear`、`dayofyear` |
| 分桶与进度 | `date_only`、`hour_floor`、`15min_floor`、`week_start`、`month_start`、`seconds_of_day`、`minutes_of_day`、`day_progress`、`week_progress` |
| 月内位置 | `is_month_start`、`is_month_end`、`days_in_month`、`days_to_month_end`、`month_progress`、`is_payday_zone`、`ten_day_period` |
| 中国大陆日历 | `is_holiday`、`is_workday`、`is_in_lieu`、`is_makeup_workday`、`holiday_name` |

- `dayofweek` 从周一的 0 到周日的 6。按周分组时使用 `week_start`，或使用 `iso_year` 和 `weekofyear`。
- `month_progress` 为当月第几天除以当月总天数。发薪日标记命中每月 10、15、25 日。
- `include_cn_calendar=True` 启用节假日查询。`is_holiday` 包含普通周末休息日，`is_in_lieu` 表示调休放假，`is_makeup_workday` 表示周末补班。日历查询超出依赖包覆盖年份时会报错。未开启时，这组字段为 `None`。
- `time_features_excel` 将标记转成「是」或「否」，保留空值、数字和日期类型。时间值仍是上海本地时间，去掉时区标记后可写入 Excel。
