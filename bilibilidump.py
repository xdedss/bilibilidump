

import jieba
import jieba.analyse
import jieba.posseg as pseg

import json, re
import argparse
import time, datetime, math, codecs, sys, requests, sqlite3
from urllib.parse import quote, unquote

import bilibiliquery as bq
from simpleDB import SimpleDB

commentsCache = {}

# 能爬的主分区id
# tids = [1, 13, 167, 3, 129, 4, 36, 188, 160, 211, 217, 119, 155, 5, 181, 177, 23, 11]
tids = [1, 3, 129, 4, 36, 188, 160, 211, 217, 119, 155, 5, 181]
# tids = [155, 5, 181]


# 获取单个视频的前5页热评及其回复(id, content)
def dump_comment(aid=None, bvid=None, mode=0, maxp=5):
    res = []
    vid_info = bq.vid_info(aid, bvid)
    if (vid_info == None):
        return res
    num_reply = vid_info['stat']['reply']
    num_page = math.ceil(num_reply / 20)
    for page in range(min(num_page, maxp)):
        comments = bq.comments(vid_info['aid'], page=page, mode=mode)
        time.sleep(0.3) # slow down
        for comment in comments:
            res.append((comment['id'], comment['content']))
            for reply in comment['replies']:
                res.append((reply['id'], reply['content']))
    return res

# 从数据库导出文本
def dump_db(fname, tid=1):
    db = SimpleDB('bili_comments.db')
    if (tid == 0):
        comments = db.iterate("SELECT content FROM Comments")
    else:
        comments = db.iterate("SELECT content FROM Comments WHERE tid = %s " % (tid, ))
    comment_count = 0
    with open(fname,'bw') as f:
        for comment in comments:
            comment_count += 1
            if (comment_count % 100 == 0):
                print('%s comments dumped           ' % comment_count, end='\r')
            f.write((unquote(comment[0]) + '\n').encode('utf-8'))
        print('%s comments dumped           ' % comment_count)
    
    db.close()

# 单句分词
def cut_words(sentence):
    #print sentence
    return ' '.join([w for w in jieba.cut(sentence) if len(w.strip()) > 0])

# 整个文件分词
def process_dump(fname):
    print('word separation...')
    f = codecs.open(fname, 'r', encoding="utf8")
    target = codecs.open('%s-seg.txt' % ('.'.join(fname.split('.')[:-1])), 'w', encoding="utf8")
    line_num = 1
    line = f.readline()
    while line:
        if (line_num % 100 == 0):
            print('%s lines processed            ' % line_num, end='\r')
        target.writelines(cut_words(line) + '\n')
        line_num += 1
        line = f.readline()
    print('%s lines processed            ' % (line_num-1))
    f.close()
    target.close()

# 循环爬取 interval分钟间隔
def scrap_start(interval=10):
    db = SimpleDB('bili_comments.db')
    db.execute("CREATE TABLE IF NOT EXISTS Comments (id INT PRIMARY KEY, tid INT, content TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS Videos (id INT PRIMARY KEY, tid INT)")
    while True:
        # main loop
        for tid in tids:
            print('----------checking tid %s-----------' % tid)
            aids = bq.rank(tid, day=3) # 热门视频
            time.sleep(1)
            print(aids)
            for aid in aids:
                print('----aid=%s----' % aid)
                if (len(db.query("SELECT id FROM Videos WHERE id = %s " % (aid, )))==0):
                    print('(new video)')
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
            time.sleep(5)
        if (int(interval) == 0):
            break
        for i in range(int(interval)):
            print('wait %s/%s min...' % (i + 1, interval))
            time.sleep(60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', metavar='action', help='fetch=爬取  dump=输出到文件')
    parser.add_argument('-t', '--time', dest='time', default=0, type=int, help='自定义评论获取间隔时间（分钟），0表示不循环')
    parser.add_argument('-f', '--file', dest='fname', default='dump.txt', help='将结果写入文件（仅dump）')
    parser.add_argument('-c', '--category', dest='tid', default=0, type=int, help='分区id（仅dump）')
    args = parser.parse_args()
    
    fetch = args.action != 'dump'
    
    if (fetch):
        fetch_interval = args.time
        scrap_start(fetch_interval)
    else:
        fname = args.fname
        tid = args.tid
        dump_db(fname, tid)
        process_dump(fname)


