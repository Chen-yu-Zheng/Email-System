
"""
 文件名：app.py
 作者：王存策
 创建时间：2021/7/12
 描述：tornado主程序
 修改人：孙策
 修改内容：tornado主程序过长，分割主程序
"""
import time
import tornado.web
import tornado.options
from tornado.options import define, options
from tornado.web import RequestHandler
import tornado.httpserver
import tornado.ioloop
import glob
from setting import appsetting, appsecret
from url import apphandler

define('port', default=8080, help='run port', type=int)

application = tornado.web.Application(handlers=apphandler,**appsetting,cookie_secret=appsecret)

#socket服务端
if __name__ == '__main__':
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port) #端口
    tornado.ioloop.IOLoop.instance().start()


