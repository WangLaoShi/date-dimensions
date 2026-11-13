# date-dimensions

将时间戳或日期时间展开为分析字段，支持 Excel 友好的返回值。需要 Python 3.10+，基础功能无需 pandas 或其他第三方包。

## 安装

```sh
pip install date-dimensions
pip install "date-dimensions[cn]"  # 可选，中国大陆节假日和调休
pip install "date-dimensions[tz]"  # 可选，供缺少系统时区数据的环境使用
```

## 使用

```python
from date_dimensions import time_features, time_features_excel

row = time_features(1700000000123, unit="ms")
print(row["year"], row["month"], row["day"])  # 2023 11 15

row = time_features_excel("2024-02-12 14:35:20", include_cn_calendar=True)
print(row["is_holiday"])   # 是
print(row["is_workday"])   # 否
print(row["15min_floor"])  # 2024-02-12 14:30:00
```

两个函数均返回相同字段。接受数字时间戳（需指定 `unit="s"` 或 `unit="ms"`）、ISO 日期时间字符串或 `datetime`。带时区的输入转换为上海时间，无时区输入按上海本地时间解释。

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
