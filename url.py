"""
 文件名：url.py
 作者：孙策
 创建时间：2021/7/20
 描述：tornado路由
"""
from handler import *

# 路由
apphandler = [
    (r"/",IndexHandler),
    (r"/index",IndexHandler),
    (r"/login",LoginHandler),
    (r"/register",RegisterHandler),
    (r"/log_out",LoginOutHandler),
    (r"/success",SuccessHandler),
    (r"/turnHistory",turnHistoryHandler),
    (r"/submit",SubmitHandler),
    (r"/mails",MailsHandler),
]