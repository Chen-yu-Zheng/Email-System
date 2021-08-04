"""
 文件名：handler.py
 作者：孙策
 创建时间：2021/7/20
 描述：tornado handler类
 修改人：孙策
 修改时间：2021/7/22
 修改内容：去除userinfo临时信息保存，添加cookie作为userid临时信息保存
"""

import email
import tornado.web
from tornado.web import RequestHandler
import glob
from module.judge import login_judge, register
from module.send import send2others
from module.get_email import get_email

user_cookie='CoCoCookie'

#逻辑处理模块
#主界面
class IndexHandler(RequestHandler):
    def get(self):
        if not self.get_secure_cookie(user_cookie):
            userid=''
        else:
            userid=self.get_secure_cookie(user_cookie).decode()
            #print("index")
            #print(userid)
            #print(type(userid))
        self.render('index.html', user_id=userid)

    def post(self,*args,**kwargs):
        self.redirect('/login')


#登陆
class LoginHandler(RequestHandler):
    def get(self,*args,**kwargs):
        self.render('login.html')

    def post(self,*args,**kwargs):
        #验证登陆
        userid = self.get_argument('userid')
        password = self.get_argument('password')
        messagestr, flag = login_judge(userid, password)
        if flag:
            self.set_secure_cookie(user_cookie,str(userid),expires_days=None)
            self.redirect('/success')
        else:
            self.render('error.html', messagestrs=messagestr)


#注册
class RegisterHandler(RequestHandler):
    def get(self,*args,**kwargs):
        self.render('register.html')
        
    def post(self,*args,**kwargs):
        userid = self.get_argument('userid')
        password = self.get_argument('password')
        password2 = self.get_argument('password2')
        messagestr, flag = register(userid, password, password2)
        if flag:
            self.set_secure_cookie(user_cookie,str(userid),expires_days=None)
            self.redirect('/success')
        else:
            self.render('error2.html', messagestrs=messagestr)

#登出
class LoginOutHandler(RequestHandler):
    def get(self,*args,**kwargs):
        self.clear_cookie(user_cookie)
        self.redirect('/index')
        
    def post(self,*args,**kwargs):
        self.clear_cookie(user_cookie)
        self.redirect('/index')


#历史图片
class turnHistoryHandler(RequestHandler):
    def get(self):
        # glob 方法，获取指定路径下的所有符合要求的文件信息，返回所有图片路径
        #img_names = glob.glob('static/images/*.jpg')
        # 渲染页面，将参数传递给HTML页面
        
        if not self.get_secure_cookie(user_cookie):
            self.redirect('/login')
        else:
            userid=self.get_secure_cookie(user_cookie).decode()
            self.render('history.html', user_id=userid, from_list = [])

    def post(self):
        userid=self.get_secure_cookie(user_cookie).decode()
        email = self.get_argument('addr')
        password = self.get_argument('mypassword')

        mails=get_email(email, password)
        addr1 = []
        topic = []
        body = []
        
        for i in range(len(mails)):
            addr1.append(mails[i].from_str)
            topic.append(mails[i].subject_str)
            body.append(mails[i].body_str)
        self.render('history.html', user_id= userid, from_list = addr1, topic_list = topic, body_list = body)
        
        

#成功
class MailsHandler(RequestHandler):
    def get(self):
        # glob 方法，获取指定路径下的所有符合要求的文件信息，返回所有图片路径
        #img_names = glob.glob('static/images/*.jpg')
        # 渲染页面，将参数传递给HTML页面
        
        if not self.get_secure_cookie(user_cookie):
            self.redirect('/login')
        else:
            userid=self.get_secure_cookie(user_cookie).decode()
            self.render('mails.html', user_id=userid, from_list = [])

#成功
class SuccessHandler(RequestHandler):
    def get(self,*args,**kwargs):
        self.render('success.html')


#提交       
class SubmitHandler(RequestHandler):
    def get(self):
        # glob 方法，获取指定路径下的所有符合要求的文件信息，返回所有图片路径
        if not self.get_secure_cookie(user_cookie):
            self.redirect('/login')

        else:
            userid=self.get_secure_cookie(user_cookie).decode()
            self.render('submit.html', user_id=userid)


    def post(self):
        if not self.get_secure_cookie(user_cookie):
            self.redirect('/login')
        else:
            from_addr = self.get_argument('addr1')
            mypassword = self.get_argument('mypassword')
            to_addr = self.get_argument('addr2')
            message_topic = self.get_argument('topic')
            message = self.get_argument('message')
            send2others(from_addr, mypassword, to_addr, message_topic, message)
            userid=self.get_secure_cookie(user_cookie).decode()
            self.render('submit.html', user_id=userid)

