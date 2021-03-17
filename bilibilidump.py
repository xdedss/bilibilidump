

import jieba
import jieba.analyse
import jieba.posseg as pseg

import json, re
import argparse
import time, datetime, math, codecs, sys, os, requests, sqlite3, random
from urllib.parse import quote, unquote

import bilibiliquery as bq
from simpleDB import SimpleDB

commentsCache = {}

# 能爬的主分区id
# tids = [1, 13, 167, 3, 129, 4, 36, 188, 160, 211, 217, 119, 155, 5, 181, 177, 23, 11]
valid_tids = [1, 3, 129, 4, 36, 188, 160, 211, 217, 119, 155, 5, 181]


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

# 从数据库导出文本分词
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

# 导出专栏文本分词
def dump_articles_db(fname):
    db = SimpleDB('bili_articles.db')
    articles = db.iterate("SELECT content FROM Articles")
    article_count = 0
    with open(fname,'bw') as f:
        for article in articles:
            article_count += 1
            if (article_count % 10 == 0):
                print('%s articles dumped           ' % article_count, end='\r')
            f.write((unquote(article[0]) + '\n').encode('utf-8'))
        print('%s articles dumped           ' % article_count)
    db.close()

# 关键字分割（用于处理表情包）
def keyword_sep(s, kws=[]):
    for kw in kws:
        idx = s.find(kw)
        if (idx != -1):
            stop2 = idx+len(kw)
            return (keyword_sep(s[:idx], kws) + ' ' + s[idx:stop2] + ' ' + keyword_sep(s[stop2:], kws))
    return ' '.join([w.strip() for w in jieba.cut(s) if len(w.strip()) > 0])

# 单句分词
def cut_words(sentence):
    #print sentence
    tree = keyword_tree(sentence, kws)
    return ' '.join([w.strip() for w in jieba.cut(sentence) if len(w.strip()) > 0])

# 整个文件分词
def process_dump(fname):
    print('word separation...')
    dic_f = open('bilidict.txt', 'r', encoding='utf8')
    kws = [w for w in dic_f.read().split('\n') if len(w.strip()) > 0]
    dic_f.close()
    target_fname = '%s-seg.txt' % ('.'.join(fname.split('.')[:-1]))
    f = codecs.open(fname, 'r', encoding="utf8")
    target = codecs.open(target_fname, 'w', encoding="utf8")
    line_num = 1
    line = f.readline()
    while line:
        if (line_num % 100 == 0):
            print('%s lines processed            ' % line_num, end='\r')
        target.writelines(keyword_sep(line, kws) + '\n')
        line_num += 1
        line = f.readline()
    print('%s lines processed            ' % (line_num-1))
    f.close()
    target.close()
    os.remove(fname)
    os.rename(target_fname, fname)

# 循环爬取热门视频评论 interval分钟间隔
# 加大量sleep是防ban，完整爬一遍所有分区大概要一下午吧
def scrap_start(tids, interval=10):
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

# 循环爬取推荐专栏
# 专栏推荐可以无限刷，但是刷来刷去也就那120个专栏来回重复 最好隔一段时间再刷一次
# 隔一天也没有太多新专栏
def scrap_article_start():
    db = SimpleDB('bili_articles.db')
    db.execute("CREATE TABLE IF NOT EXISTS Articles (id INT PRIMARY KEY, content TEXT)")
    while True:
        articles = bq.article_suggestions()
        print(articles)
        time.sleep(2)
        for article in articles:
            print('cv%s' % (article, ))
            if (len(db.query("SELECT id FROM Articles WHERE id = %s " % (article, ))) == 0):
                content = bq.article_text(article)
                if (content == ''):
                    continue
                print('(new article)')
                db.execute("INSERT INTO Articles VALUES (%s, '%s')" % (article, quote(content)))
                time.sleep(2 + random.random() * 2)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', metavar='action', help='fetch=爬取热门视频评论区 fetcharticles=爬取推荐专栏文本  dump=输出评论到文件 dumparticles=输出专栏')
    parser.add_argument('-t', '--time', dest='time', default=0, type=int, help='自定义评论获取循环间隔时间（分钟），默认为0表示不循环')
    parser.add_argument('-f', '--file', dest='fname', default='dump.txt', help='将结果写入文件时的文件名，默认dump.txt')
    parser.add_argument('-c', '--category', dest='tid', default=0, type=int, help='要爬取或者导出的分区id，默认为0表示所有')
    args = parser.parse_args()
    
    fetch = args.action != 'dump'
    
    if (args.action == 'fetch'):
        fetch_interval = args.time
        if (args.tid != 0):
            if (not args.tid in valid_tids):
                print('invalid tid')
                print('choose from %s' % (valid_tids, ))
                exit()
            tids = [args.tid]
        else:
            tids = valid_tids
        scrap_start(tids, fetch_interval)
    elif (args.action == 'dump'):
        fname = args.fname
        tid = args.tid
        dump_db(fname, tid)
        process_dump(fname)
    elif (args.action == 'fetcharticles'):
        scrap_article_start()
    elif (args.action == 'dumparticles'):
        fname = args.fname
        dump_articles_db(fname)
        process_dump(fname)
    else:
        print('invalid action')

