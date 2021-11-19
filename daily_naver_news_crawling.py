from bs4 import BeautifulSoup
from urllib.request import urlopen
import pandas as pd
import time
import datetime
from datetime import timedelta
import pickle

def request_url(url):
    sleep_time=5
    num=5
    for _ in range(num):
        try:
            html=urlopen(url)
            code = html.status  
            time.sleep(sleep_time)
            if code==200: 
                bs=BeautifulSoup(html,'lxml')
                return bs
                break
            
        except Exception as e:
            print("url_page",e)
            time.sleep(30)
    return -1
    
def list_page(date,page):
    url="https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=001&date={}&page={}".format(date,page)
    bs=request_url(url.format(date,page))
    return bs

def news_page(url):
    news={}
    news['url']=url
#     print('url',url)
    body_pro=True
    for _ in range(3):
        bs=request_url(url)
        if bs!=-1:
            try:
                head=bs.select_one("div.article_info")

                news['title']=head.select_one("h3#articleTitle").text
                news['day']=head.select_one("span.t11").text
                body=bs.select_one("div#articleBodyContents").text
                body=body.replace("\n","").replace("\xa0","").replace("\t",'')
                news['body']=body.replace("// flash 오류를 우회하기 위한 함수 추가function _flash_removeCallback() {}","")
                sections=bs.select("em.guide_categorization_item")
                news['sections']=[section.text for section in sections]
            except Exception as e:
                print("뉴스 바디", e)
            else:
                body_pro=False
                break
    if not body_pro:    
        try:   #부가적
            company=bs.select_one("div.article_header a[href]")
            news['company_url']=company['href']
            news["company"]=company.select_one("img[title]")['title']
        except Exception as e:
            print("부가적 문제1",e)
            print(url)
            fail_log.append([3,url])
            
        try:   #부가적
            news['reporter']=bs.select_one("p.b_text").text.strip()
        except Exception as e:
            print("부가적 문제2",e)
            print(url)
            fail_log.append([4,url])
    else:
        fail_log.append([2,url])

    return news

    
fail_log=[]
today=datetime.datetime.today()
yesterday=today - timedelta(days=1)
y_day=yesterday.strftime('%Y%m%d')
print('day : ',y_day)
with open('fail_log_{}.pkl'.format(y_day),'wb') as f:
    pickle.dump(fail_log,f)

try:

    keep=False
    for _ in range(3):
        bs=list_page(y_day,10000)
        if bs!=-1:
            try:
                max_page_num=bs.select_one('div.paging strong').text
                print(max_page_num)
            except Exception as e:
                print("max_num",e)
                time.sleep(30)
            else:
                keep=True
                break
        else:
            time.sleep(15)

    if keep:
        news_pd=pd.DataFrame([])
        for i in range(1,int(max_page_num)):
            if i%100==0:
                print(i,"/",max_page_num)
            lis=True
            for _ in range(2):
                bs=list_page(y_day,i)
                if bs!=-1:
                    news_list=bs.select('div.list_body.newsflash_body li')
                    if len(news_list)!=0:
                        for new in news_list:

                            url=new.select_one('a[href]')
                            if url!=None:
                                dic=news_page(url['href'])
                                if dic!={}:
                                    news_pd=news_pd.append(dic,ignore_index=True)
                        news_pd.to_csv("news_pd_{}.csv".format(y_day),index=False)
                        lis=False
                        break
            if lis:
                fail_log.append([1,y_day,i])
    else:
        fail_log.append([0,y_day])
except KeyboardInterrupt as e:
    print("key")
finally:
    with open('fail_log_{}.pkl'.format(y_day),'wb') as f:
        pickle.dump(fail_log,f)