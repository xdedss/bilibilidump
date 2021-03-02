
爬取b站各分区热门视频的前100条热门评论，存入数据库，用来收集语料

[b站api](https://github.com/SocialSisterYi/bilibili-API-collect)

# 用法

1.爬取，每次间隔60分钟，爬取每一个主分区的热门视频，存入bili_comments.db
-t为间隔（分钟）
```
python bilibilidump.py fetch -t 60
```

2.从bili_comments.db导出纯文本到txt
-f为文件名，-c为[分区id](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/video/video_zone.md)，0表示所有分区
```
python bilibilidump.py dump -f dump.txt -c 0
```
