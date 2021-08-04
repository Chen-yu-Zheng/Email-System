"""
文件名：databaseClass.py
作者：孙策
描述：数据库
创建时间：2021/7/8
修改人：孙策
修改时间：2021/7/9
修改内容：更新_init_，判断是否存在库文件，若无则建表
"""
import os
import sqlite3

class databaseLink():
    # 打开数据库
    def __init__(self):
        dbname = "userinfor.db"
        #print(1000)
        flag = os.path.exists(dbname)
        
        self.con =sqlite3.connect(dbname)  #链接数据库
        self.curs = self.con.cursor()
        
        if not flag:
            self.create_tables()

    # 关闭数据库
    def __del__(self):
        #self.curs.close()
        self.con.close()
    
    def create_tables(self):
        self.curs.execute('''create table user (
                                uID varchar(128) primary key not null, 
                                password varchar(128) not null);''')
        self.curs.execute('''create table userANDhistory (
                                hisID varchar(128) primary key not null, 
                                uID varchar(128) not null);''')
        self.curs.execute('''create table history (
                                hisID varchar(128) primary key not null, 
                                time time not null,
                                rawpicture verchar(255) not null,
                                getobject verchar(255) not null,
                                restpicture verchar(255) not null);''')
        self.con.commit()

    def db_query(self,querystr):
        usrs_info = self.curs.execute(querystr).fetchone()
        return usrs_info
    
        
    def db_insert(self,querystr):
        self.curs.execute(querystr)
        #print(1000)
        self.con.commit()

