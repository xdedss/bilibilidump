
import requests
import math, time
import json, re

from pyquery import PyQuery as pq


def pick(dic, keys):
    res = {}
    for k in keys:
        if k in dic:
            res[k] = dic[k]
    return res

def raw(url):
    r = requests.get(url)
    r.encoding = 'utf-8'
    res = json.loads(r.text)
    return res

# mode=0热度 2时间 1混合
def comments(aid, page=0, mode=2):
    url = 'http://api.bilibili.com/x/v2/reply/main?pn=1&type=1&mode=%s&oid=%s&next=%s' % (mode, aid, page+1)
    j = raw(url)
    if j['code'] != 0:
        print(j)
        return []
    replies = j['data']['replies']
    if replies == None:
        return []
    # recursive
    _ = lambda reply:{'id' : reply['rpid'], 'username' : reply['member']['uname'], 'content' : reply['content']['message'], 
        'time' : reply['ctime'], 'floor' : reply['floor'], 'userid' : reply['mid'],
        'parent' : reply['parent'], 'replies' : [] if reply['replies'] == None else [_(r) for r in reply['replies']]}
    return [_(reply) for reply in replies]

def vid_info(aid=None, bvid=None):
    if aid != None:
        url = 'http://api.bilibili.com/x/web-interface/view?aid=%s' % aid
    elif bvid != None:
        url = 'http://api.bilibili.com/x/web-interface/view?bvid=%s' % bvid
    else:
        return None
    j = raw(url)
    if j['code'] == 0:
        data = j['data']
        return {'title' : data['title'], 'description' : data['desc'], 'time' : data['ctime'], 'bvid' : data['bvid'], 'aid' : data['aid'], 
            'stat' : pick(data['stat'], ['view', 'danmaku', 'reply', 'favorite', 'coin', 'share', 'like', 'now_rank', 'his_rank'])}
    else:
        print(j)
        return None

# 视频推荐
# day只能3天或7天
def rank(tid=1, day=3):
    #url = 'http://api.bilibili.com/x/web-interface/ranking/region?rid=%s&day=%s' % (tid, day)
#    j = raw(url)
#    if j['code'] == 0:
#        videos = j['data']
#        return [v['aid'] for v in videos]
#    else:
#        print(j)
#        return []

    url = 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=%s&type=all' % (tid, )
    j = raw(url)
    if j['code'] == 0:
        videos = j['data']['list']
        return [v['aid'] for v in videos]
    else:
        print(j)
        return []

# 专栏推荐
def article_suggestions(cid = 0, ps = 20):
    url = 'https://api.bilibili.com/x/article/recommends?cid=%s&pn=0&ps=%s' % (cid, ps)
    j = raw(url)
    if j['code'] == 0:
        articles = j['data']
        return [a['id'] for a in articles]
    else:
        print(j)
        return []

# 专栏内容（纯文本）
def article_text(cv):
    html = pq('https://www.bilibili.com/read/cv%s' % (str(cv).replace('cv', '')))
    return html('.article-holder').text()

