
爬取b站各分区热门视频的前100条热门评论，存入数据库，用来收集语料

[b站api](https://github.com/SocialSisterYi/bilibili-API-collect)

# 用法

1.爬取每一个主分区的热门视频，存入bili_comments.db 

```
python bilibilidump.py fetch
```

2.从bili_comments.db导出纯文本到txt

-f为文件名，-c为[分区id](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/video/video_zone.md)，0表示所有分区

```
python bilibilidump.py dump -f dump.txt -c 0
```

3.生成词向量 d为维数

```
python word2vec.py dump.txt -d 300
```

4.生成词云（test.png）

```
python word2cloud.py
```

![test](wordcloud.png)
