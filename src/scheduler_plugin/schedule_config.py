# schedule_config.py

# ===============================
# 全域開關
# ===============================

DRY_RUN = True

# ===============================
# Lane 定義
# ===============================

SOCIAL_LANE = "social"
ENT_LANE = "entertainment"
REPOST_LANE = "repost"
SPECIAL_LANE = "special"


# ===============================
# 工作日時間表
# ===============================

WORKDAY_SCHEDULE = [

    {"time": "00:15", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "00:30", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "00:45", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "01:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},

    {"time": "01:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野", "plastic"], "mode": "link_repost"},
    {"time": "02:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "02:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野", "plastic"], "mode": "link_repost"},
    {"time": "03:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "03:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野", "plastic"], "mode": "link_repost"},
    {"time": "04:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "04:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野", "plastic"], "mode": "link_repost"},
    {"time": "05:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "05:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野", "plastic"], "mode": "link_repost"},
    {"time": "06:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "06:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野", "plastic"], "mode": "link_repost"},

    {"time": "07:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "07:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "07:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "07:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "08:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "08:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},

    {"time": "09:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "09:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "09:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "10:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "10:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "10:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},

    {"time": "11:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},
    {"time": "11:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "11:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},
    {"time": "12:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "12:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},

    {"time": "13:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},
    {"time": "13:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "13:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},
    {"time": "14:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},
    {"time": "14:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "14:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},

    {"time": "15:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},
    {"time": "15:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "15:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},
    {"time": "16:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},
    {"time": "16:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "16:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},

    {"time": "17:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},
    {"time": "17:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "17:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},
    {"time": "18:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},
    {"time": "18:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "18:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "商業事"], "mode": "manual"},

    {"time": "19:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "消費", "商業事"], "mode": "manual"},
    {"time": "19:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "19:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "消費", "商業事"], "mode": "manual"},
    {"time": "20:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "消費", "商業事"], "mode": "manual"},
    {"time": "20:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "20:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "消費", "商業事"], "mode": "manual"},
    {"time": "21:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "消費", "商業事"], "mode": "manual"},
    {"time": "21:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "21:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "消費", "商業事"], "mode": "manual"},

    {"time": "22:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "消費", "商業事"], "mode": "manual"},
    {"time": "22:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "22:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "消費", "商業事"], "mode": "manual"},
    {"time": "23:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "消費", "商業事"], "mode": "manual"},

    {
        "time": "23:30",
        "lane": SPECIAL_LANE,
        "mode": "fixed_link_first_publish",
        "source": "entertainment_18_web"
    },
    {"time": "23:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "法庭事", "消費", "商業事"], "mode": "manual"},

]


# ===============================
# 周末 / 紅日時間表
# ===============================

WEEKEND_SCHEDULE = [

    {"time": "00:15", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "00:30", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "00:45", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "01:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},

    {"time": "01:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野","plastic"], "mode": "link_repost"},
    {"time": "02:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "02:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野","plastic"], "mode": "link_repost"},
    {"time": "03:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "03:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野","plastic"], "mode": "link_repost"},
    {"time": "04:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "04:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野","plastic"], "mode": "link_repost"},
    {"time": "05:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "05:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野","plastic"], "mode": "link_repost"},
    {"time": "06:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "06:30", "lane": REPOST_LANE, "categories": ["社會事", "兩岸", "大視野","plastic"], "mode": "link_repost"},

    {"time": "07:00", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "消費", "商業事"], "mode": "manual"},
    {"time": "07:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "07:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "07:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "08:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "08:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "08:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "09:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "09:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "09:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "10:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "10:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "10:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},

    {"time": "11:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "11:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "12:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "12:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "13:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "13:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "13:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "14:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "14:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "14:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "15:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "15:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "15:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "16:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "16:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "16:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "17:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "17:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "17:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "18:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "18:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "18:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "19:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "19:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "19:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "20:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "20:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "20:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "21:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "21:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "21:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "22:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "22:30", "lane": ENT_LANE, "categories": ["娛圈事", "心韓"], "mode": "auto"},
    {"time": "22:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},
    {"time": "23:15", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "manual"},

    {
        "time": "23:30",
        "lane": SPECIAL_LANE,
        "mode": "fixed_link_first_publish",
        "source": "entertainment_18_web",
        "optional": True
    },
    {"time": "23:45", "lane": SOCIAL_LANE, "categories": ["社會事", "兩岸", "大視野", "商業事"], "mode": "auto"},
]