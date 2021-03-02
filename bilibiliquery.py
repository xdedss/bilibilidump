
import requests
import math, time
import json, re



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

def rank(tid=1):
    url = 'http://api.bilibili.com/x/web-interface/ranking/region?rid=%s&day=3' % (tid, )
    j = raw(url)
    if j['code'] == 0:
        videos = j['data']
        return [v['aid'] for v in videos]
    else:
        print(j)
        return []

