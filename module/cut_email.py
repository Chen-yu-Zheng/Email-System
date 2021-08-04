"""
 文件名：get_email.py
 作者：孙策
 介绍：使用POP3从邮件服务器删除邮件
 创建时间：2021/7/31
"""
"""
 入口函数：cut_email(email, password, pop3_server, index)
 输入参数：
    email：邮箱地址
    password：邮箱授权码或密码（qq邮箱为授权码）
    pop3_server：邮箱服务器地址
    index：邮件ID
 无返回值
"""
from pop3 import POP3

def cut_email(email, password, pop3_server, index):
    # 连接到POP3服务器:
    server = POP3(pop3_server)
    
    # 身份认证
    server.user(email)
    server.pass_(password)
    
    # 可以根据邮件索引号直接从服务器删除邮件:
    server.dele(index)

    # 关闭连接:
    server.quit()