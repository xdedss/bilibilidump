

import requests

import sqlite3

import json, re
import argparse
import sys
import time, datetime, math
from urllib.parse import quote, unquote

import bilibiliquery as bq
from simpleDB import SimpleDB

commentsCache = {}

# 能爬的主分区id
tids = [1, 13, 167, 3, 129, 4, 36, 188, 160, 211, 217, 119, 155, 5, 181, 177, 23, 11]


# 获取单个视频的前5页热评及其回复(id, content)
def dump_comment(aid=None, bvid=None, mode=0, maxp=5):
    res = []
    vid_info = bq.vid_info(aid, bvid)
    num_reply = vid_info['stat']['reply']
    num_page = math.ceil(num_reply / 20)
    for page in range(min(num_page, maxp)):
        comments = bq.comments(vid_info['aid'], page=page, mode=mode)
        for comment in comments:
            res.append((comment['id'], comment['content']))
            for reply in comment['replies']:
                res.append((reply['id'], reply['content']))
    return res

# 从数据库导出文本
def dump_db(tid=1):
    db = SimpleDB('bili_comments.db')
    comments = db.query("SELECT content FROM Comments WHERE tid = %s " % (tid, ))
    return '\n'.join([unquote(comment[0]) for comment in comments])

# 循环爬取 interval分钟间隔
def scrap_start(interval=10):
    db = SimpleDB('bili_comments.db')
    db.execute("CREATE TABLE IF NOT EXISTS Comments (id INT PRIMARY KEY, tid INT, content TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS Videos (id INT PRIMARY KEY, tid INT)")
    while True:
        # main loop
        for tid in tids:
            print('----------checking tid %s-----------' % tid)
            aids = bq.rank(tid) # 热门视频
            print(aids)
            for aid in aids:
                print('----aid=%s----' % aid)
                if (len(db.query("SELECT id FROM Videos WHERE id = %s " % (aid, )))==0):
                    db.execute("INSERT INTO Videos VALUES (%s, %s)" % (aid, tid))
                comments = dump_comment(aid=aid, mode=0) # 热门评论
                print('%s comments found' % len(comments))
                comment_count = 0
                for rpid, comment in comments:
                    old = db.query("SELECT id FROM Comments WHERE id = %s " % (rpid, ))
                    if (len(old) == 0): # 去重
                        comment_count += 1
                        print('%s new comments           ' % comment_count, end = '\r')
                        #print('[comment]' + comment)
                        db.execute("INSERT INTO Comments VALUES (%s, %s, '%s')" % (rpid, tid, quote(comment)))
                print()
                time.sleep(3)
        for i in range(int(interval)):
            print('wait %s/%s min...' % (i + 1, interval))
            time.sleep(60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', metavar='action', help='fetch=爬取  dump=输出到文件')
    parser.add_argument('-t', '--time', dest='time', default=1, type=float, help='自定义评论获取间隔时间（分钟）（仅fetch）')
    parser.add_argument('-f', '--file', dest='fname', default='dump.txt', help='将结果写入文件（仅dump）')
    parser.add_argument('-c', '--category', dest='tid', default='0', type=int, help='分区id（仅dump）')
    args = parser.parse_args()
    
    fetch = args.action != 'dump'
    
    if (fetch):
        fetch_interval = args.time
        scrap_start(fetch_interval)
    else:
        fname = args.fname
        tid = args.tid
        with open(fname,'bw') as f:
            if (tid == 0):
                for tid in tids:
                    f.write(dump_db(tid).encode('utf-8'))
            else:
                f.write(dump_db(tid).encode('utf-8'))
    


