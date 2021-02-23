#pythonUseMysql2.ipynbで使用
#DB（Mysql）を使用する理由
#利点：データの集計、検索はSQL文が非常に楽で便利、条件Whereを追加すれば細かく範囲を出力できる
#テーブル同士をリレーショナルに管理できる
#・エクセルでマクロを使ってデータを使用するのはどうか？マクロは苦手
#マクロを使ってセルを集計するのにマクロを組む手間がかかる。行が増えたり列が増減すると都度マクロの修正が必要
#シート同士でリレーショナルに集計できる方法がわからない。

import MySQLdb#古い更新されないライブラリらしいのでmysql-connector-pythonに今後切り替え
import mysql.connector#mysql-connector-python
import os
import re
import sys
import time
import datetime
import glob#ファイル一覧
import shutil#move
from selenium import webdriver
import pandas as pd

#
#株探の先物オプション記事について、特定文字列について空白をカンマに置換処理するためのメソッド
#def latterHalf(text):数字を後ろから探す
#def outMojiMKIII(text):空白をカンマに置換処理
#def csvToMysql(difile,dtablename,doptionDate,dmonth):
#def checkFile(filename):fileが存在するかチェック。パスは固定
#def fileMove(file,path):file移動
#def selectMysql(tablename):select 

#ADD　2021/02/18　
#yahooFinanceJapanから出来高率のデータを取得してMysqlのテーブルに登録する
#URL　https://info.finance.yahoo.co.jp/ranking/
#kd= ランキング種別項目koumoku 、mk= 市場market
#kd=33 出来高、kd=50 一株当期利益EPS 
#mk=3 東証一部、 mk=4東証二部
#株式ランキング、出来高率、東証一部
#https://info.finance.yahoo.co.jp/ranking/?kd=33&mk=3&tm=d&vl=a
#https://info.finance.yahoo.co.jp/ranking/?kd=33&tm=d&vl=a&mk=3&p=1
#https://info.finance.yahoo.co.jp/ranking/?kd=33&tm=d&vl=a&mk=3&p=2

#株式ランキング、出来高率、東証二部
#https://info.finance.yahoo.co.jp/ranking/?kd=33&mk=4&tm=d&vl=a

#一株当期利益　東証一部
#https://info.finance.yahoo.co.jp/ranking/?kd=50&mk=3&tm=d&vl=a
#一株当期利益東証二部
#https://info.finance.yahoo.co.jp/ranking/?kd=50&mk=4&tm=d&vl=a
class tableColum():
    def __init__(self,num,code,market,name,time,price,value,preValue,percent):
        self.num=num#たぶん使わないけど先頭なのでいれておく
        self.code=code
        self.market=market
        self.name=name
        self.time=time
        self.price=price
        self.value=value
        self.preValue=preValue
        self.percent=percent
        
        
    def columCapsul(self):
        print('def columCapsul')

class epsTableColum():
    def __init__(self,num,code,market,name,time,price,eps,kessanDate):
        #使用しない変数num,timeがあるのは、ループするときに挿入する順番を間違えないようにするためとコードを見やすくするため
        #使用するときは変数名を指定するので、不使用でも問題はない。
        self.num=num#たぶん使わないけど先頭なのでいれておく
        self.code=code
        self.market=market
        self.name=name
        self.time=time#使用せず、単に配列の要素数を合わせるために使っている
        self.price=price
        self.eps=eps
        self.kessanDate=kessanDate
        self.kessanSyubetsu=''#連結（連）、単体（単）を格納するための変数

    def changeEpsKessanSyubetsuWord(self):
        #「(連)」が含まれたら削除したい もしかすると「(単)」もあるので単、連結のテーブルカラムを用意するかな
        self.kessanSyubetsu=''
        tmpStr=''
        tmpStr=self.eps#一旦文字列を移してから文字列置換をする.replaceは元のデータは書き換えられない。

        if tmpStr.find('(連)')>=0:
            self.kessanSyubetsu='(連)'
            self.eps=tmpStr.replace('(連)','')
        elif tmpStr.find('(単)')>=0:
            self.kessanSyubetsu='(単)'
            self.eps=tmpStr.replace('(単)','')
    
    def changeKessanDate(self):
        #kessanDateの日付は年月2021/3とかのようになっていて日がないので日をダミーで付記する。
        #2021/3を2021/3/01みたいに日を付ける
        #なので、4桁2桁2桁か/を基準にして数を数えて日が足りていないことを判別する
        #splitで配列にしてその数で判別したほうが早いかもしれない。
        tmpArray=self.kessanDate.split('/')
        if len(tmpArray)==2:#yyyy,mmのときは2つしかないので、dayがないので付記する
            self.kessanDate+='/01'

#ヤフーファイナンスのランキングから出来高率を開く,EPS1株利益クラスで継承してる
#今後、出来高以外の条件のデータを取得することもあるので汎用性を考慮する
#市場ごとに必要なページ数を取得する。
#ループが2個　URLの引数を調整
#市場を番号で管理する
#注意　ページ数がいくつまであるかのチェックは行っていない。１０Pくらいはいつでも存在する前提。ページ数が１０を越えるとそのページが存在しないこともあり得る。
#東証一部で約5ページを取得
#東証二部で約5ページを取得
#一旦CSVに出力する（テスト、動作確認のため）
#CSVを読み込みMYｓｑｌの所定のテーブルに追加する
#SELECT文で必要な情報を出力する、TEXTかCSV
class yahooFinanceDekidaka():
    def __init__(self):
        #print()
        pass

    def checkFileExist(self,filename,path):
        #他にもimport os　os.listdir(path) というのもある
        if path[-1]=='/':#文字列の最後の1文字がスラッシュならなにもしない。
            pass
        else:
            path+='/'
        files=glob.glob(path+'*.csv')
        count=0
        for file in files:
            print(file)
            if filename in file:#ファイル名を含んでいればTRUE
                print('ファイルは存在します')
                count+=1
                return True#見つかれがすぐに抜ける
        #ループで探し終わってから判断もいれる     
        if count>0:
            return True
        else:
            print('ファイルはありません')
            return False
    #end def
    
    #MYSQL
    def selectDekidakaMysql(self):
        # コネクションの作成
        conn = mysql.connector.connect(
            host='localhost',
            port='3306',
            user='maseda',
            password='Test1030',
            database='YahooFinance'
        )
        #今日の日付か、CSVのファイル名から取得した日付または、直近のテーブルの日付
        sql="SELECT * FROM Table_Dekidaka;"
        df_dekidaka = pd.read_sql(sql,conn)
        print(df_dekidaka.head())#出力
        print("pd, head出力したけど表示されているかい＞されていないなら修正して")
        conn.close()
    
    #test確認用のコード
    def getDekidakaTest(self,koumokuCode,marketCode,pageNum):
        #print()
        #URL 項目koumokuと市場marketの引数をそれぞれ分解しておく
        #
        # 仮想ブラウザ起動、URL先のサイトにアクセス
        driver = webdriver.Chrome('/usr/local/bin/chromedriver')#ここでエラーになったらパスが違うかchromedriverをインストールする
        #他のエラーで、「unexpectedly exited. Status code was：-9」だったら、Macの場合はシステム環境設定　→　セキュリティとプライバシー　で許可すればよい
        url='https://info.finance.yahoo.co.jp/ranking/?kd='#株式ランキング
        if koumokuCode=='' or marketCode=='':
            print('ランキング種別か市場の引数が設定されていません')
            sys.exit()
        if pageNum=='' or pageNum==0:#ページ番号の指定がないときは強制的に1にしておく
            pageNum=1
        #注意　ページ数がいくつまであるかのチェックは行っていない。１０Pくらいはいつでも存在する前提。ページ数が１０を越えるとそのページが存在しないこともあり得る。  
        driver.get(url+str(koumokuCode)+'&mk='+str(marketCode)+'&tm=d&vl=a'+'&p='+str(pageNum))#&p=1,&p=2みたいにページ番号を追記する。
        time.sleep(1)
        
        contentsBodyBottom = driver.find_element_by_id("contents-body-bottom")
        rankdata = contentsBodyBottom.find_element_by_class_name("rankdata")
        rankingTableWrapper=rankdata.find_element_by_class_name("rankingTableWrapper")
        tableTag=rankingTableWrapper.find_element_by_tag_name("table")
        #thead tr
        thead=tableTag.find_element_by_tag_name("thead")
        trtag=thead.find_element_by_tag_name("tr")#１個しかないので単数
        tdsThead=trtag.find_elements_by_tag_name("td")#複数
        for m in range(0,len(tdsThead)):
            tdsThead[m].text
            print(tdsThead[m].text)
        
        #array
        outputArray=[]
        
        #tbody trs
        tbody=tableTag.find_element_by_tag_name("tbody")
        trs=tbody.find_elements_by_tag_name("tr")#"複数"
        for i in range(0,len(trs)):#tr
            tds=trs[i].find_elements_by_tag_name("td")
            #a link に挟まれたのが企業コード
            #倍を削除する
            obj=tableColum(tds[0].text,tds[1].find_element_by_tag_name("a").text,tds[2].text,tds[3].text,tds[4].text,tds[5].text,\
                          tds[6].text,tds[7].text,tds[8].text.replace('倍',''))
            outputArray.append(obj)
        driver.close()#起動したウィンドウを閉じる    
        output=outputArray
        return output
        
    def outputCSVForTableColum(self,columArray,filename,path):
        #TableColumクラス専用のCSV出力、通常の配列は使用できない。
        #path='/Users/toshiromaseda/Documents/2021年/2021年株/yahoofinance_data/'
        if filename.find('.csv')==-1:#拡張子.csvがないときは付記する
            filename+='.csv'
        os.chdir(path)#ディレクトリ変更
        print(os.getcwd())#ディレクトリ確認
        try:
            ofile=open(filename,'tw') 
        except FileNotFoundError as e: # FileNotFoundErrorは例外クラス名
           print("ファイルが見つかりません", e)
           sys._exit()#ファイルがなければ終了#tryのときは_exit()が良いらしい
        except Exception as e: # Exceptionは、それ以外の例外が発生した場合
           print(e)
        
        for i in columArray:#tableColumクラスのメンバ変数code,market,name,time,price,value,preValue,percent
            ofile.write(i.code+','+i.market+','+i.name+','+i.price.replace(',','')+','+i.value.replace(',','')+','+\
                        i.preValue.replace(',','')+','+i.percent.replace(',','')+'\n')
        ofile.close()  

    def mysqlInsertFuncDekidaka(self,inputStr,cursor):
        #MySQLdbを使用　#古い更新されないライブラリらしいのでmysql-connector-pythonに今後切り替え
        #mysqlの接続はすでに行われた前提
        tablename='Table_Dekidaka'
        rowname="(Code,Market,Name,Price,Volume,PreviousVolume,VolumePer,StockDate,CreateDate,Yobi)"
        tmp=[]
        tmp=inputStr.strip().split(",")
        
        dt_now=datetime.datetime.now()
        StockDate=dt_now.strftime('%Y/%m/%d')#
        createDate=dt_now.strftime('%Y/%m/%d %H:%M:%S')#今日の日付時刻を入れて、取り込み実行の日付で良い。後で削除操作するときの目安くらいだから厳密ではない
        yobi=''
        try:
             #%dにするとエラーになるのでINT型は%sにしておくとエラーにならない。なのでINTなのに%sとして記述してある。
            cursor.execute("INSERT INTO " + tablename + " " + rowname + " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",\
                            (tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5],tmp[6],StockDate,createDate,yobi))
        except MySQLdb.Error as e:
            print('MySQLdb.Error: ', e)
            

            
    def mysqlConnectorInsertFuncDekidaka(self,inputStr,cursor):
        #MysqlConnector版　今後はこちらで作業
        #MySQLdb#古い更新されないライブラリらしいのでmysql-connector-pythonに今後切り替え
        #mysqlの接続はすでに行われた前提
        tablename='Table_Dekidaka'
        rowname="(Code,Market,Name,Price,Volume,PreviousVolume,VolumePer,StockDate,CreateDate,Yobi)"
        tmp=[]
        tmp=inputStr.strip().split(",")
        #print(tablename)

        dt_now=datetime.datetime.now()
        StockDate=dt_now.strftime('%Y/%m/%d')#
        createDate=dt_now.strftime('%Y/%m/%d %H:%M:%S')#今日の日付時刻を入れて、取り込み実行の日付で良い。後で削除操作するときの目安くらいだから厳密ではない
        yobi=''
        #try:
             #%dにするとエラーになるのでINT型は%sにしておくとエラーにならない。なのでINTなのに%sとして記述してある。
        cursor.execute("INSERT INTO " + tablename + " " + rowname + " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",\
                        (tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5],tmp[6],StockDate,createDate,yobi))
        #except MySQLdb.Error as e:
            #print('MySQLdb.Error: ', e)
            
    def mysqlConnectorInsertFuncDekidakaTest(self,inputStr,cursor):
        #接続確認用メソッド
        #MysqlConnector版　今後はこちらで作業
        #MySQLdb#古い更新されないライブラリらしいのでmysql-connector-pythonに今後切り替え
        #mysqlの接続はすでに行われた前提
        tablename='Table_Dekidaka'
        rowname="(Code,Market,Name,Price,Volume,PreviousVolume,VolumePer,StockDate,CreateDate,Yobi)"
        tmp=[]
        if inputStr!='':
            tmp=inputStr.strip().split(",")
        
        dt_now=datetime.datetime.now()
        StockDate=dt_now.strftime('%Y/%m/%d')#
        createDate=dt_now.strftime('%Y/%m/%d %H:%M:%S')#今日の日付時刻を入れて、取り込み実行の日付で良い。後で削除操作するときの目安くらいだから厳密ではない
        yobi=''
        try:
             #%dにするとエラーになるのでINT型は%sにしておくとエラーにならない。なのでINTなのに%sとして記述してある。
            cursor.execute("SELECT * FROM " + tablename)
            rows = cursor.fetchall()
            print("SELECT処理")
            for row in rows:
                print(row)
        except MySQLdb.Error as e:
            print('MySQLdb.Error: ', e)        
   
    def CSVtoMysqlConnectorTest(self,filename,path):
        #Test
        #MysqlConnector版　今後はこちらで作業
        # コネクションの作成
        conn = mysql.connector.connect(
            host='localhost',
            port='3306',
            user='maseda',
            password='Test1030',
            database='YahooFinance'
        )
        cursor=conn.cursor()
        try:        
            #test
            iline=""
            self.mysqlConnectorInsertFuncDekidakaTest(iline,cursor)

        except MySQLdb.Error as e:
            print('MySQLdb.Error: ', e)
            conn.rollback()#失敗したらもとに戻す。これだと途中で成功してもコミットされるので、1回でもエラーのときはBREAKのほうがいいかも。
            print("強制終了MYSQL")
            conn.close()
            return
        conn.commit()
        cursor.close()
        conn.close()   
        
    def CSVtoMysqlConnector(self,filename,path):
        #MysqlConnector版　今後はこちらで作業
        # コネクションの作成
        conn = mysql.connector.connect(
            host='localhost',
            port='3306',
            user='maseda',
            password='Test1030',
            database='YahooFinance'
        )
        cursor=conn.cursor()
        
        print("Trueなら接続OK")
        print(conn.is_connected())#True,False
        os.chdir(path)#ディレクトリ変更
        print(os.getcwd())#ディレクトリ確認
        try:#ファイルが存在しないときのエラー処理try
            with open(filename,'tr') as fin:
                for iline in fin:
                    #try:        
                    
                    self.mysqlConnectorInsertFuncDekidaka(iline,cursor)

                    #except MySQLdb.Error as e:
                    #    print('MySQLdb.Error: ', e)
                    #    conn.rollback()#失敗したらもとに戻す。これだと途中で成功してもコミットされるので、1回でもエラーのときはBREAKのほうがいいかも。
                     #   print("強制終了MYSQL")
                     #   cursor.close()
                     #   conn.close()  
                    #    return  

        except FileNotFoundError as e: # FileNotFoundErrorは例外クラス名
            print("ファイルが見つかりません。パス、ファイル名を確認してください", e)
            print("強制終了")
            sys._exit()#ファイルがなければ終了 #tryのときは_exit()が良いらしい
        except Exception as e: # Exceptionは、それ以外の例外が発生した場合
            print(e)
            
        conn.commit()
        #テストロールバック
        #conn.rollback()
        #print('現在テスト中なのでrollbackしてます')
        print('commit')
        cursor.close()
        conn.close()
        print('DB 処理終了。。。')
        
     
    #古いコネクターを使っているのでこのメソッドは使わない    
    def CSVtoMysql(self,filename,path):##MySQLdb#古い
        #MySQLdb#古い更新されないライブラリらしいのでmysql-connector-pythonに今後切り替え
        #mysql接続
        #Mysqlに接続メソッドを入れる
        # データベースへの接続とカーソルの生成
        #DBはすでに作成済みとする。mysql-connector-pythonに今後切り替え
        connection = MySQLdb.connect(
            host='localhost',
            user='maseda',
            passwd='Test1030',#知られても問題ないパスワード
            db='YahooFinance')
        cursor = connection.cursor() 
        
        os.chdir(path)#ディレクトリ変更
        print(os.getcwd())#ディレクトリ確認
        try:#ファイルが存在しないときのエラー処理try
            with open(filename,'tr') as fin:
                for iline in fin:
                    try:
                        #カンマ区切りなのでSplitする
                        self.mysqlInsertFuncDekidaka(iline,cursor)
                    except MySQLdb.Error as e:
                        print('MySQLdb.Error: ', e)
                        connection.rollback()#失敗したらもとに戻す。これだと途中で成功してもコミットされるので、1回でもエラーのときはBREAKのほうがいいかも。
                        print("強制終了MYSQL")
                        connection.close()
                        return
            connection.commit()
        except FileNotFoundError as e: # FileNotFoundErrorは例外クラス名
            print("ファイルが見つかりません。パス、ファイル名を確認してください", e)
            print("強制終了")
            sys._exit()#ファイルがなければ終了 #tryのときは_exit()が良いらしい
        except Exception as e: # Exceptionは、それ以外の例外が発生した場合
            print(e)
        
#ヤフーファイナンスランキングの１株あたり利益クラス。　Dekidakaクラスを継承する。といってもそれほど継承するメソッドはない
class yahooFinanceEps(yahooFinanceDekidaka):
    def __init__(self):
        pass
        #print()
    #テーブルが存在するという前提Table_eps
    #override
    def selectDekidakaMysql(self):
        # コネクションの作成
        conn = mysql.connector.connect(
            host='localhost',
            port='3306',
            user='maseda',
            password='Test1030',
            database='YahooFinance'
        )
        #今日の日付か、CSVのファイル名から取得した日付または、直近のテーブルの日付
        sql="SELECT * FROM Table_Eps;"
        df_dekidaka = pd.read_sql(sql,conn)
        print(df_dekidaka.head())#出力
        print("pd, head出力したけど表示されているかい＞されていないなら修正して")
        conn.close()

    #オーバーライド
    def mysqlConnectorInsertFuncDekidaka(self,inputStr,cursor):
        #MysqlConnector版　今後はこちらで作業
        #MySQLdb#古い更新されないライブラリらしいのでmysql-connector-pythonに今後切り替え
        #mysqlの接続はすでに行われた前提
        tablename='Table_Eps'
        rowname="(Code,Market,Name,Price,KessanSyubetsu,Eps,KessanDate,StockDate,CreateDate,Yobi)"
        tmp=[]
        tmp=inputStr.strip().split(",")
        
        dt_now=datetime.datetime.now()
        StockDate=dt_now.strftime('%Y/%m/%d')#
        createDate=dt_now.strftime('%Y/%m/%d %H:%M:%S')#今日の日付時刻を入れて、取り込み実行の日付で良い。後で削除操作するときの目安くらいだから厳密ではない
        yobi=''
        #try:
             #%dにするとエラーになるのでINT型は%sにしておくとエラーにならない。なのでINTなのに%sとして記述してある。
        cursor.execute("INSERT INTO " + tablename + " " + rowname + " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",\
                        (tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5],tmp[6],StockDate,createDate,yobi))
        #except MySQLdb.Error as e:
            #print('MySQLdb.Error: ', e)  

    #override
    def outputCSVForTableColum(self,columArray,filename,path):
        #TableColumクラス専用のCSV出力、通常の配列は使用できない。
        #path='/Users/toshiromaseda/Documents/2021年/2021年株/yahoofinance_data/'
        if filename.find('.csv')==-1:#拡張子.csvがないときは付記する
            filename+='.csv'
        os.chdir(path)#ディレクトリ変更
        print(os.getcwd())#ディレクトリ確認
        try:
            ofile=open(filename,'tw') 
        except FileNotFoundError as e: # FileNotFoundErrorは例外クラス名
           print("ファイルが見つかりません", e)
           sys._exit()#ファイルがなければ終了#tryのときは_exit()が良いらしい
        except Exception as e: # Exceptionは、それ以外の例外が発生した場合
           print(e)
        
        for i in columArray:#tableColumクラスのメンバ変数code,market,name,time,price,value,preValue,percent
            ofile.write(i.code+','+i.market+','+i.name+','+i.price.replace(',','')+','+i.kessanSyubetsu+','+\
                        i.eps.replace(',','')+','+i.kessanDate+'\n')
        ofile.close()         

    #add    
    def getEps(self,koumokuCode,marketCode,pageNum):
        # 仮想ブラウザ起動、URL先のサイトにアクセス
        driver = webdriver.Chrome('/usr/local/bin/chromedriver')#ここでエラーになったらパスが違うかchromedriverをインストールする
        #他のエラーで、「unexpectedly exited. Status code was：-9」だったら、Macの場合はシステム環境設定　→　セキュリティとプライバシー　で許可すればよい
        url='https://info.finance.yahoo.co.jp/ranking/?kd='#株式ランキング
        if koumokuCode=='' or marketCode=='':
            print('ランキング種別か市場の引数が設定されていません')
            sys.exit()
        if pageNum=='' or pageNum==0:#ページ番号の指定がないときは強制的に1にしておく
            pageNum=1
        #注意　ページ数がいくつまであるかのチェックは行っていない。１０Pくらいはいつでも存在する前提。ページ数が１０を越えるとそのページが存在しないこともあり得る。  
        #Eps1株利益用に修正するkd=50になるので、「50」が異なるだけで他の書式は同じだ
        driver.get(url+str(koumokuCode)+'&mk='+str(marketCode)+'&tm=d&vl=a'+'&p='+str(pageNum))#&p=1,&p=2みたいにページ番号を追記する。
        time.sleep(1)
        #URLはほぼ同じだけど、CSSのクラスやIDが異なるので、EPS用に個別に変更が必要となる
        contentsBodyBottom = driver.find_element_by_id("contents-body-bottom")
        rankdata = contentsBodyBottom.find_element_by_class_name("rankdata")
        rankingTableWrapper=rankdata.find_element_by_class_name("rankingTableWrapper")
        tableTag=rankingTableWrapper.find_element_by_tag_name("table")
        #thead tr
        thead=tableTag.find_element_by_tag_name("thead")
        trtag=thead.find_element_by_tag_name("tr")#１個しかないので単数
        tdsThead=trtag.find_elements_by_tag_name("th")#複数
        for m in range(0,len(tdsThead)):
            tdsThead[m].text
            #print(tdsThead[m].text)
        
        #array
        outputArray=[]
        
        #tbody trs
        tbody=tableTag.find_element_by_tag_name("tbody")
        trs=tbody.find_elements_by_tag_name("tr")#"複数"
        for i in range(0,len(trs)):#tr
            tds=trs[i].find_elements_by_tag_name("td")
            #a link に挟まれたのが企業コード
            #num,code,market,name,price,eps,kessan
            #epsに「(連)3,358」「(連)」が含まれたら削除したい
            obj=epsTableColum(tds[0].text,tds[1].find_element_by_tag_name("a").text,tds[2].text,tds[3].text,tds[4].text,tds[5].text,\
                          tds[6].text,tds[7].text)
            obj.changeEpsKessanSyubetsuWord()#連、単の文字を調整する
            obj.changeKessanDate()#決算の日付を調整
            outputArray.append(obj)

        driver.close()#起動したウィンドウを閉じる    
        output=outputArray
        return output
##################################################################################################
##################################################################################################
##################################################################################################
#以下はクラスにしていない。クラスにしなかった理由は特にない    
#メソッドを別ファイルにした。
#文字列の後ろ側の数字を後ろから探し、抜けていた場合0を埋める
def latterHalf(text):
    textout=text
    pattern=re.compile('[0-9]+')#findで正規表現ができない
    i=0
    checkArray=[]#タプルを入れる配列
    while i>=0:#数字を探す
      m=pattern.search(textout, i)
      if m:
        #print(m.start())
        #print(m.end())
        #これをタプル配列に入れて、N,N-1で差が大きいときに0を入れる
        #print(m.span())
        checkArray.append(m.span())
        i = m.end()#m.start() + 1#m.end()
      else:
        break
    n=len(checkArray)
    if n>=2:#nは最低2こ必要 最後と最後の1こ前の
        #print("[n-1][0]",checkArray[n-1][0])#0番目の1個目 [0](0,1)
        #print("[n-2][1]",checkArray[n-2][1])#0番目の2個目
        #個数はNだけど配列の指定はそれより1小さいのでN-1となる
        if (checkArray[n-1][0]-checkArray[n-2][1])>=6:
            print("put抜けている")
            #checkArray[n-1][1]の後ろに挿入する
            texttmp=textout[:checkArray[n-2][1]+2]+ '0' + textout[checkArray[n-2][1]+2:]
            textout=texttmp
    output=textout
    return output
#end def

def outMojiMKIII(text):
    #空白を削除する前に、空白の個数を数える
    #株探の仕様が変わったらここを変える。2020/12/16
    kuro=re.compile('[ 　]+')#半角と全角の空白置換 半角全角が[半角全角]として入っている
    
    if text.count('　',0,15)>=13:
           #空白13個はプット
            opt='put'
            textout=text.strip()#先頭、末尾の空白、改行を削除する
    else:
            #コールの場合、2種類あるのでそれをチェックする
            textout=text.strip()#先頭、末尾の空白を削除する
            check=kuro.sub(',',textout)#半角全角の空白を置換
            count=check.split(",")
            #print ('len count:',len(count))
            if len(count)>=5:#配列が5個以上なら、call,putが含まれる       
                opt='callandput'
            else:
                opt='onlycall'
    pattern=re.compile('[0-9]+')#findで正規表現ができない
    if opt=='onlycall' or opt=='callandput':
        #次に、「call,putあり」OR「Callのみ」かをチェックする。
        #optSub='callandput' 'onlycall'
        #callのみを先に処理して、put側を調べる
        matchobj=re.search('[0-9]+',textout)#最初の数字を探す
        if matchobj:
            #print('マッチした文字列：'+matchobj.group())
            #print('マッチした文字列グループ：',matchobj.groups())
            #print( '開始位置'+str(matchobj.start()) )#先頭位置は0番として数える　3番目（4文字目）に見つかった
            #print( '終了位置'+str(matchobj.end()) )#終了位置は次の番目を含んでいるので実際は１を引いた数が終了位置
            #print(matchobj.span())#'マッチした文字列の (開始位置, 終了位置) のタプル'+
            #2番めの数字を探す
            secondMatch=pattern.search(textout,matchobj.end())#compileを使用してpatternで再度位置を指定して探す
            if secondMatch:
                #print( '開始位置2：'+str(secondMatch.start()) )#先頭から数えて10番目に次の数字が見つかった
                #1番目と2番めの文字数が5以上空いていたら数字が抜けている事がわかる。
                #ここに0を埋める処理を入れる
                if secondMatch.start()-matchobj.end() >=5:
                    print('値が抜けてる')
                    # hash = "355879ACB6"
                    # hash = hash[:4] + '-' + hash[4:]
                    #文字列の挿入。#1番目の文字の3文字目くらいに0を追加する。
                    texttmp=textout[:matchobj.end()+2]+ '0' + textout[matchobj.end()+2:]
                    textout=texttmp
        #put側のチェック。再度optでチェックする
        if opt=='onlycall':
            #置換して終わる
            output=kuro.sub(',',textout)+',,,'
        elif opt=='callandput':
            #print('callandputの処理')
            tmp=latterHalf(textout)#後半PUTの処理をして文字を返す
       
            #置換して終わる
            output=kuro.sub(',',tmp)
    elif opt=='put':
    #putのみの場合
        #3つのカンマを付ける
        tmp=latterHalf(textout)#後半PUTの処理をして文字を返す
        output=',,,'+kuro.sub(',',tmp)#＞＞,,,26250,285,-10,189
    #end if
 
    return output
### end def

def csvToMysql(difile,dtablename,doptionDate,dmonth):
#ここからSTART
#Mysqlに接続メソッドを入れる
# データベースへの接続とカーソルの生成
    connection = MySQLdb.connect(
        host='localhost',
        user='maseda',
        passwd='Test1030',#知られても問題ないパスワード
        db='Stock')
    cursor = connection.cursor()

    #csvファイル名
    ifile=difile
    
    #table
    tablename=dtablename#"Test_Table_StockOption"#テスト用テーブルを使用する

    #カラム名
    rowname="(Volume1,Change1,Price1,ExercisePrice,Price2,Change2,Volume2,Month,OptionDate,CreateDate,YOBI)"
    #VALUES (%d,%d,%d,%d,%d,%d,%d,%d,%s,%s,%s)＞＞%dは%sにしないとエラーになった。

    #カラム変数
    month=dmonth#1#月限
    optionDate=doptionDate#"2020/12/22"#データ取得の日付、たいていCSVに記載の日付になる。
    
    dt_now=datetime.datetime.now()
    createDate=dt_now.strftime('%Y-%m-%d %H:%M:%S')#今日の日付時刻を入れて、取り込み実行の日付で良い。後で削除操作するときの目安くらいだから厳密ではない

    yobi=""#コメントがあればいれる。
    
    count=0
    #テーブルにデータを挿入する部分から書いていく
    #CSVを1行ごとに読み取り、列ごとにカラムに入れていく
    try:#ファイルが存在しないときのエラー処理try
        with open(ifile,'tr') as fin:
            for iline in fin:
                try:
                    #Mysqlに直接インサートするバージョンを作業する
                    # ここに実行したいコードを入力します

                    #cursor.execute("INSERT INTO Test_Table_StockOption (カラム,) VALUES(値,,,)")
                    #cursor.execute("INSERT INTO " + tablename + " " + rowname + " VALUES (%s,%s)", ("test1","test2"))
                    #count=count+1
                    tmp=iline.strip().split(",")#stripしてからsplit()だと理解している。　iline.split(",")のままだと改行が入ってくるのでstripで前後の空白と改行を削除する
                    #CSVのデータが空の場合は、値0を入れる
                    if tmp[0]=='':
                        tmp[0]=0
                    if tmp[1]=='':
                        tmp[1]=0
                    if tmp[2]=='':
                        tmp[2]=0
                    if tmp[3]=='':
                        tmp[3]=0
                    if tmp[4]=='':
                        tmp[4]=0 
                    if tmp[5]=='':
                        tmp[5]=0
                    if tmp[6]=='':
                        tmp[6]=0    
                    #テストテーブルにインサートする前に、確認する前に、Splitを確認する。
                    #print(count,tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5],tmp[6])
                    #%dにするとエラーになるのでINT型は%sにしておくとエラーにならない。なのでINTなのに%sとして記述してある。
                    cursor.execute("INSERT INTO " + tablename + " " + rowname + " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",\
                                   (tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5],tmp[6],month,optionDate,createDate,yobi))

                    #こっちだと、%dに値がないよとエラーになる。正しい記述のはずがパイソンではエラーになるようだ。
                    #cursor.execute("INSERT INTO " + tablename + " " + rowname + " VALUES (%d,%d,%d,%d,%d,%d,%d,%d,%s,%s,%s)",\
                    #               (tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5],tmp[6],month,optionDate,createDate,yobi))

                except MySQLdb.Error as e:
                    print('MySQLdb.Error: ', e)
                    connection.rollback()#失敗したらもとに戻す。これだと途中で成功してもコミットされるので、1回でもエラーのときはBREAKのほうがいいかも。
                    print("強制終了MYSQL")
                    connection.close()
                    return
            #ofile.close()
        connection.commit()

    except FileNotFoundError as e: # FileNotFoundErrorは例外クラス名
        print("ファイルが見つかりません。パス、ファイル名を確認してください", e)
        ofile.close()
        sys._exit()#ファイルがなければ終了
    except Exception as e: # Exceptionは、それ以外の例外が発生した場合
       print(e)

    # 接続を閉じる
    connection.close()  

    print("Mysql書き込み終了")
#defここまで

#check file
def checkFile(filename):
    #他にもimport os　os.listdir(path) というのもある
    files=glob.glob('./option_python_execute/*.txt')
    for file in files:
        #print(file)
        if filename in file:#ファイル名を含んでいればTRUE
            print('すでに取り込み済みのファイルです。')
            sys.exit()
#end def

def fileMove(file,path):
    shutil.move(file, path)#('./new.txt', './sample')
    print('file move',file)
#end def

def selectMysql(tablename):#Month=1が指定なので、ここは引数にしたほうがよさそう
# データベースへの接続とカーソルの生成
    connection = MySQLdb.connect(
        host='localhost',
        user='maseda',
        passwd='Test1030',#知られても問題ないパスワード
        db='Stock')
    cursor = connection.cursor()  
    try: 
        # ここに実行したいコードを入力します
        cursor.execute("SELECT SUM(Volume1) as callVolume1, ExercisePrice, SUM(Volume2) as putVolume2 FROM "+ tablename +\
                        " WHERE Month=1 GROUP BY ExercisePrice ORDER BY ExercisePrice Desc")

        #カラム名を取得
        #cursor.execute("show columns from Table_StockOption")

        # fetchall()で全件取り出し
        rows = cursor.fetchall()
        searchArray=[]#タプルで登録
        for row in rows:
          print(row[0],row[1],row[2])
          searchArray.append(row)  
            # print(row[Volume1]) ERROR

        #print(searchArray[0])#IDの情報：('ID', 'int', 'NO', 'PRI', None, 'auto_increment')
        #for srow in searchArray:
        #    print(srow)#
    
    except MySQLdb.Error as e:
        print('MySQLdb.Error: ', e)
    
    #表示
    connection.commit()
    connection.close()  
#end def    