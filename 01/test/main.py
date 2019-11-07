import requests as re
import hashlib as h
import random, configparser, pandas, json, pandas as pd, time, datetime
from lib.excel import Excel
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from datetime import date, timedelta

PATHLABEL = None
DOMAINNAME = "https://mp.weixin.qq.com"

URL = {
    "login" : "/cgi-bin/bizlogin?action=startlogin",
    "login_referer" : "/cgi-bin/loginpage?t=wxm2-login&lang=zh_CN",
    "source" : "/wxopen/sourceanalysis",
    "user" : "/wxopen/userportrait",
    "datacount" : "/wxopen/appdatacount",
    "visit" : "/wxopen/visitanalysis"
}

def formatIniToDict(label):
    l = {}
    for e in label :
        l[e[0]] = e[1]
    return l

def getUrl(name : str) :
    return DOMAINNAME + URL[name]

def login(username : str, password : str) :
    m = h.md5()
    m.update(password.encode("utf-8"))
    md5ps = m.hexdigest() 

    data = {"username" : username, "pwd" : md5ps, "imgcode" : "", "f" : "json", "userlang" : "zh_CN", "redirect_url" : "", 
            "token" : "", "lang" : "zh_CN", "ajax" : "1"}

    headers = {"Referer" : getUrl("login_referer")}

    s = re.Session()
    r = s.post(url=getUrl("login"), data=data, headers = headers)
    return s


def simulateLogin(cookiesText) :
    s = re.Session()
    cookies = s.cookies

    for x in cookiesText.split(";") :
        cookies.set(x[:x.index("=")] , x[x.index("=") + 1:])

    return s 

def queryPara(p : map) :
    l = []
    for k,v in p.items() :
        l.append("%s=%s" % (k,v))
    return '&'.join(l)

def getQuery(token : str, action : str) :
    p = {
        "token" : token,
        "lang" : "zh_CN",
        "f" : "json",
        "ajax" : "1",
        "random" : str(random.random()),
        "action" : action
    }
    return p

def getHttp(session, urlname, p, name) :
    r = session.get(getUrl(urlname) + "?" + queryPara(p))
    res = r.json()

    if res["base_resp"]["ret"] != 0 :
        print("调用失败:" + res["base_resp"]["err_msg"])
        return None 
    return json.loads(res[name]) 

def writeUser(excel, sheet, point, row, col, categories, values, title, isRatio, isTotal, isPie, e) :
    d = title
    total = 0

    for e1 in e["line_list"] :
        key = None
        value = None
        ratio = None

        for e2 in e1["data_list"] :
            if e2["key"] == "key" :
                key = e2["value"]
            elif e2["key"] == "value" :
                value = int(e2["value"])
            elif e2["key"] == "ratio" :
                ratio = '{:.2%}'.format(float(e2["value"]))

        if isRatio :
            d.append([(0,0,key,0),(0,0,value,0),(0,0,ratio,0)])
        else :
            d.append([(0,0,key,0),(0,0,value,0)])
        total = total + value

    if isTotal :
        d.append([(0,0,"总人数",0),(0,0,total,0)])

    #写数据
    excel.write(sheet, point, d, {})

    if isPie :
        excel.insertPie(sheet, "",  row, col, "用户画像", categories, values) 
    else :
        excel.insertColumn(sheet, "",  row, col, "用户画像", categories, values)

def analyzeUser(session, timeScope : int, token : str, excel) :
    sheet = excel.addSheet("用户画像")

    p = getQuery(token, "get_user_gender_and_age")
    p["time_scope"] = timeScope

    data = getHttp(session, "user", p, "data_info")
    if data is not None :
        for e in data["result_list"] :
            if e["id"] == "2" :
                #性别分布
                writeUser(excel, sheet, (1,1), 19, 4, "$B$3:$B$5", "$C$3:$C$5", [[(1,0,"性别分布",0),None]], False, False, True, e)
            elif e["id"] == "5" :
                #年龄分布
                t = [[(0,0,"年龄分布",0),(0,0,"人数",0),(0,0,"比重",0)]]
                writeUser(excel, sheet, (0,19), 1, 4, "$A$21:$A$27", "$B$21:$B$27", t, True, True, True, e)

    p = getQuery(token, "get_province_distribution")
    p["time_scope"] = timeScope

    data = getHttp(session, "user", p, "data_info")
    if data is not None :
        for e in data["result_list"] :
            if e["id"] == "6" :
                #区域分布
                writeUser(excel, sheet, (20,1), 1, 12, "$U$3:$U$38", "$V$3:$V$38", [[(0,0,"省份",0),(0,0,"活跃用户",0)]], False, False, False, e)

    p = getQuery(token, "get_platform_and_device")
    p["time_scope"] = timeScope

    data = getHttp(session, "user", p, "data_info")
    if data is not None :
        for e in data["result_list"] :
            if e["id"] == "3" :
                #机型分布
                writeUser(excel, sheet, (12,17), 22, 12, "$M$19:$M$21", "$N$19:$N$21", [[(1,0,"手机系统分布图",0),None]], False, False, True, e)

    p = getQuery(token, "get_city_distribution")
    p["index"] = "1"
    p["time_scope"] = timeScope
    data = getHttp(session, "user", p, "data_info")
    if data is not None :
        for e in data["result_list"] :
            if e["id"] == "1" :
                #城市分布
                writeUser(excel, sheet, (0,36), 36, 3, "$A$38:$A$57", "$B$38:$B$57", [[(0,0,"城市",0),(0,0,"活跃用户",0)]], False, False, False, e)

def writeSource(excel, sheet, layout, name, point, row, col, categories, values, l, data) :
    r1 = [(0,0,"来源",1)]
    r2 = [(0,0,"",1)]
    r3 = [(0,0,name,1)]
    s1d = []
    s1i = []
    d = [r1, r2, r3]
    total = 0
    for e in data["list"] :
        r1.append((0,0, l[e["source_id"]], 1))
        r2.append((0,0, e["value"], 0))
        s1i.append(l[e["source_id"]])
        s1d.append(e["value"])
        total = total + e["value"]
    for i in range(1, len(r2)) :
        r3.append((0,0, '{:.2%}'.format(r2[i][2] / total), 0))

    #写数据
    excel.write(sheet, point, d, layout)
    #写入占比饼图
    excel.insertPie(sheet, name, row, col, "来源分析", categories, values)
    #写入占比柱形图
    excel.insertColumn(sheet, name, row, col + 10, "来源分析", categories, values)
    

def analyzeSource(session, startTime : int, endTime : int, token : str, label, excel) :
    l = {}
    for e in label :
        l[int(e[0])] = e[1]

    sheet = excel.addSheet("来源分析")

    layout = {
        1 : {"bg_color":"#66B3FF"}
    }

    p = getQuery(token, "get_distribution")
    p["index_id"] = "1"
    p["begin_timestamp"] = str(startTime)
    p["end_timestamp"] = str(endTime)

    data = getHttp(session, "source", p, "data_info")
    if data is not None :
	    writeSource(excel, sheet, layout, "打开次数", (0,0), 5, 0, "$B$1:$V$1", "$B$2:$V$2", l, data)

    p["index_id"] = "2"

    data = getHttp(session, "source", p, "data_info")
    if data is not None :
        writeSource(excel, sheet, layout, "访问人数", (0,22), 27, 0, "$B$23:$V$23", "$B$24:$V$24", l, data)
    
def writeDataCount(session, p, d, id, dtype, source, zb, layoutId, ltime, daynum) :
    p["id"] = id
    data = getHttp(session, "datacount", p, "default_time_data")
    if data is not None :
        r = [dtype,(0,0,source,layoutId),(0,0,zb,layoutId)]
        
        di = 0
        total = 0
        for t in ltime :
            if di >= len(data["list"]) :
                break
            if(t == data["list"][di]["ref_date"]) :
                num = int(data["list"][di]["value"])
                r.append((0,0, num, layoutId))
                total = total + num
                di = di + 1
            else :
                r.append((0,0,0,layoutId))            
        r.append((0,0,total,layoutId))            
        r.append((0,0,total / daynum,layoutId))            
        d.append(r)
    
def analyzeBase(session, startTime, endTime, token, excel) :
    sheet = excel.addSheet("基础数据")

    layout = {
        1 : {"bg_color":"#8FAADC"},
        2 : {"bg_color":"#BDD7EE"}
    }
    
    r1 = [(0,0,"数据类别",1),(0,0,"数据来源",1),(0,0,"数据指标",1)]
    d = [r1]

    timeArray = time.localtime(startTime)
    stime = time.strftime("%Y%m%d", timeArray)
    stime = datetime.datetime.strptime(stime, "%Y%m%d")

    timeArray = time.localtime(endTime)
    etime = time.strftime("%Y%m%d", timeArray)
    etime = datetime.datetime.strptime(etime, "%Y%m%d")

    offset = timedelta(days=1)

    ltime = []
    daynum = 0
    while str(stime) != str(etime) :
        r1.append((0,0,str(stime)[5:7] + "月" + str(stime)[8:10] + "日",1))
        ltime.append(str(stime)[0:4] + str(stime)[5:7] + str(stime)[8:10])
        stime = stime + offset
        daynum = daynum + 1
    r1.append((0,0,"合计",1))
    r1.append((0,0,"平均数",1))
        
    p = getQuery(token, "overview_compare")
    p["default_start_time"] = str(startTime)
    p["default_end_time"] = str(endTime)
    
    writeDataCount(session, p, d, "4", (0,7,"概况数据",2), "微信MP后台", "累计访问用户数", 2, ltime, daynum)
    writeDataCount(session, p, d, "6", None, "微信MP后台", "当日访问次数(PV)", 0, ltime, daynum)
    writeDataCount(session, p, d, "7", None, "微信MP后台", "访问人数(UV)", 2, ltime, daynum)
    writeDataCount(session, p, d, "8", None, "微信MP后台", "新访问人数", 0, ltime, daynum)
    writeDataCount(session, p, d, "9", None, "微信MP后台", "分享次数", 2, ltime, daynum)
    writeDataCount(session, p, d, "10", None, "微信MP后台", "分享人数", 0, ltime, daynum)
    writeDataCount(session, p, d, "11", None, "微信MP后台", "人均停留时长", 2, ltime, daynum)

    excel.write(sheet, (0,0), d, layout)

def analyzeShare(session, startTime, endTime, token, excel):
    p = getQuery(token, "get_visit_page_top")
    p["table_start_time"] = str(startTime)
    p["table_end_time"] = str(endTime)
    p["sort_key"] = "visit_pv"
    p["sort_type"] = "2"
    p["offset"] = 0
    p["count"] = 1000

    d = getHttp(session, "visit", p, "data_info")
    if d is None :
        return

    sheet = excel.addSheet('访问页面')
    sheet.set_column(0, 0, 30)
    sheet.set_column(1, 1, 60)

    layout = {
        1 : {"bg_color":"#8FAADC"},
        2 : {"bg_color":"#BDD7EE"}
    }

    arr = [
        [ 
        (0,0,'页面名称',1),
        (0,0,'页面路径',1),
        (0,0,'访问次数',1),
        (0,0,'访问人数',1),
        (0,0,'次均时长(s)',1),
        (0,0,'入口页次数',1),
        (0,0,'退出页次数',1),
        (0,0,'退出率',1),
        (0,0,'分享次数',1),
        (0,0,'分享人数',1)]
    ];

    total = []; 
    lid = 2
    for line in d['list'] :
        tmpele = [];
        for i in range(0,len(line['list'])) : 
            ele = line['list'][i]
            if i != 0 :
                tmpele.append((0,0,float(ele['value']),lid));
                if i-1 >= len(total):
                    total.append(float(ele['value']));
                else :
                    total[i-1] = total[i-1] + float(ele['value'])
            else :
                if ele['value'].lower() in PATHLABEL:
                  tmpele.append((0,0,PATHLABEL[ele['value'].lower()],lid));
                else :
                  tmpele.append((0,0,'',lid));
                tmpele.append((0,0,ele['value'],lid));
        arr.append(tmpele);
        lid = 0 if lid == 2 else 2

    last = [(1,0,'合计',lid),None];
    for num in total:
        last.append((0,0,num,lid));
    arr.append(last);

    excel.write(sheet, (0,0), arr, layout)

def createShareToDayData(data, lmap, length) :
    if data is not None :
        for line in data['list'] :
            pagepath = line["list"][0]["value"]

            for m in lmap :
                index = m[0]
                dmap = m[1]

                if pagepath in dmap :
                    l = dmap[pagepath]
                    si = len(l)
                else :
                    l = []
                    si = 0
                    dmap[pagepath] = l

                for i in range(si,length) :
                    l.append(0)
                l.append(int(line["list"][index]["value"]))

def writeShareToDay(lmap, head, excel, length) :
    y = 0
    lid = 2

    sheet = excel.addSheet('访问页面按天统计')
    sheet.set_column(0, 0, 30)
    sheet.set_column(1, 1, 60)
    
    layout = {
        1 : {"bg_color":"#8FAADC"},
        2 : {"bg_color":"#BDD7EE"}
    }

    dtable = None
    for m in lmap :
        dtable = [[(0,0,m[2],0)],head]
        for k, v in m[1].items() :
            l = []
            if k.lower() in PATHLABEL :
                l.append((0,0,PATHLABEL[k.lower()],lid))
            else :
                l.append((0,0,'noname',lid))
            l.append((0,0,k,lid))
            
            lv = len(v)
            while lv != length :
                v.append(0)
                lv = lv + 1
            
            for e in v : 
                l.append((0,0,e,lid))
            dtable.append(l)
            lid = 0 if lid == 2 else 2

        excel.write(sheet, (0,y), dtable, layout)
        y = y + len(dtable) + 4
    
         
def analyzeShareToDay(session, startTime, endTime, token, excel):
    daystamp = 86400
	
    p = getQuery(token, "get_visit_page_top")
    p["sort_key"] = "visit_pv"
    p["sort_type"] = "2"
    p["offset"] = 0
    p["count"] = 1000
    
    st = startTime
    head = [ (0,0,'页面名称',1),(0,0,'页面路径',1)]
    lmap = [(7,{}, "分享次数"),(8,{}, "分享人数"),(1,{}, "访问次数"),(2,{}, "访问人数")]
    length = 0
    while st != endTime :
        timeArray = time.localtime(st)
        ptime = time.strftime("%m月%d日", timeArray)
        head.append((0,0,ptime,1))
    
        p["table_start_time"] = str(st)
        p["table_end_time"] = str(st + daystamp - 1)

        d = getHttp(session, "visit", p, "data_info")
        st = st + daystamp

        createShareToDayData(d, lmap, length)
        length = length + 1

    writeShareToDay(lmap, head, excel, length)
    
def analyzeAccess(session, token, startTime, endTime, depthDict, timeDict, excel) :
    p = getQuery(token, "get_visit_distribution")
    p["start_time"] = str(startTime)
    p["end_time"] = str(endTime)

    data = getHttp(session, "visit", p, "data_info")
    if data is None :
        return

    sheet = excel.addSheet('访问分析')

    d = [[(0,0,"访问时长(秒)",0),(0,0,"打开次数",0)]]
    for e in data["access_time_info_list"] :
        d.append([(0,0,timeDict[str(e["source_id"])],0),(0,0,int(e["value"]),0)])
    excel.write(sheet, (0,0), d, {})
    excel.insertTable('bar', sheet, "访问时长", 0, 4, "访问分析", "$A$9:$A$2", "$B$9:$B$2")

    d = [[(0,0,"访问深度",0),(0,0,"打开次数",0)]]
    for e in data["access_depth_info_list"] :
        d.append([(0,0,depthDict[str(e["source_id"])],0),(0,0,int(e["value"]),0)])
    excel.write(sheet, (0,17), d, {})
    excel.insertTable('bar', sheet, "访问深度", 17, 4, "访问分析", "$A$25:$A$19", "$B$25:$B$19")


    p = getQuery(token, "get_qr_visit_data")
    p["start_time"] = str(startTime)
    p["end_time"] = str(endTime)
    p["qr_type"] = "2"
    p["offset"] = "0"
    p["count"] = "30"
    data = getHttp(session, "visit", p, "data_info")
    if data is None :
        return

    layout = {
        1 : {"bg_color":"#8FAADC"},
        2 : {"bg_color":"#BDD7EE"}
    }

    d = [[(9,0,"带参数的二维码",1),None,None,None,None,None,None,None,None,None,(0,0,"打开次数",1),(0,0,"占比",1)]]
    lid = 0
    for line in data["list"] :
        r = []
        r.append((9,0,line["item"][0]["value"],lid))
        for i in range(0, 9) :
            r.append(None)
        r.append((0,0,line["item"][1]["value"],lid))
        r.append((0,0,line["item"][2]["value"],lid))

        d.append(r)
        lid = 0 if lid == 2 else 2

    excel.write(sheet, (0,34), d, layout)
    
    ln = writeRetain(excel, sheet, session, token, startTime, endTime, 0, 0, 0)
    ln = writeRetain(excel, sheet, session, token, startTime, endTime, 0, 1, int(ln))
    ln = writeRetain(excel, sheet, session, token, startTime, endTime, 0, 2, int(ln))
    ln = writeRetain(excel, sheet, session, token, startTime, endTime, 1, 0, int(ln))
    ln = writeRetain(excel, sheet, session, token, startTime, endTime, 1, 1, int(ln))
    ln = writeRetain(excel, sheet, session, token, startTime, endTime, 1, 2, int(ln))
    
def writeRetain(excel, sheet, session, token, startTime, endTime, tp, size, curry): #tp 新增orh活跃  size 日周月 curry当前开始行
    #retain_type 0  新增留存 1活跃
    # 0日，1周，2月
    p = getQuery(token, "get_visit_retain")
    p["begin_timestamp"] = str(startTime)
    p["end_timestamp"] = str(endTime)
    p["offset"] = 0;
    p["count"] = 1000;
    p['retain_type']=tp;
    p['grain_size']=size; #grain_size 0,1,2

    strname = '新增'
    strsize = '天'
    if tp == 1 :
      strname = '活跃'
    if size == 1 :
      strsize = '周'
    if size == 2 :
      strsize = '月'

    data = getHttp(session, "visit", p, "data_info")
    if data is None :
      excel.write(sheet, (14,int(curry)), [[(7,0,strname+'留存-'+strsize,0)]], {})
      return 6+int(curry);

    res = formatRetain(data, strname, strsize);
    res.insert(0, [(len(res[0]),0,strname+'留存-'+strsize, 0 )]);

    excel.write(sheet, (14,int(curry)), res, {})
    return len(res)+int(curry)+5; #空5行
    
def formatRetain(data, tp, size):
    arr = [];
    date = [None];
    user = [(0,0,tp+'用户数',0)];
    maxlen = 0;
    data['list'].reverse()
    for day in data['list']:
      date.append((0,0,day['refdate'],0));
      user.append((0,0,day['assign_user'],0));
      if len(day['item']) > maxlen :
        maxlen = len(day['item'])
    arr.append(date);
    arr.append(user);

    inx = 0;
    for day in data['list']:
      inx = inx + 1;
      for i in range(0, maxlen):
        if i <= (len(arr)-2) and inx == 1 : 
          arr.append([(0,0,str(i+1)+size,0)]);
        if i < len(day['item']) :
          tmp = day['item'][i]
          arr[i+2].append((0,0,float(int(tmp['percentage'])/int(day['assign_user'])),0));
        else :
          arr[i+2].append((0,0,None,0));
    return arr;

if __name__ == '__main__' : 
    #读取系统配置文件
    config = configparser.ConfigParser()

    config.read("./config/sys.ini",encoding='utf-8')
    sourceLabel = config.items("source")
    PATHLABEL = formatIniToDict(config.items("path"))
    depthDict = formatIniToDict(config.items("access_depth"))
    timeDict = formatIniToDict(config.items("access_time"))

    config.read("./config/para.ini")
    cookies = config.get("login","cookies")
    token = config.get("login","token")

    startTime = config.get("para","startTime")
    timeArray = time.strptime(startTime + " 00:00:00", "%Y%m%d %H:%M:%S")
    startTimeStamp = int(time.mktime(timeArray))

    endTime = config.get("para","endTime")
    timeArray = time.strptime(endTime + " 00:00:00", "%Y%m%d %H:%M:%S")
    endTimeStamp = int(time.mktime(timeArray))

    filename = config.get("para","filename")
    timeScope = config.get("para","timeScope")

    #账号密码登录 暂不可用
    #username = "guowuyuanxcx@163.com"
    #password = "guowuyuan1224"
    #session = login(username, password)

    #模拟登录
    s = simulateLogin(cookies)

    e = Excel("./", filename, "xls")

    analyzeBase(s, startTimeStamp, endTimeStamp, token, e)
    analyzeAccess(s, token, startTimeStamp, endTimeStamp, depthDict, timeDict, e)
    analyzeShare(s, startTimeStamp, endTimeStamp, token, e)
    analyzeShareToDay(s, startTimeStamp, endTimeStamp, token, e)
    analyzeSource(s, startTimeStamp, endTimeStamp, token, sourceLabel, e)
    analyzeUser(s, timeScope, token, e)
    
    e.close()
