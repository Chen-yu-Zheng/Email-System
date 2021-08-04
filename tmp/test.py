"""
 文件名：test.py
 作者：孙策
 介绍：对get_email进行测试
 创建时间：2021/7/27
"""

from get_email import get_email
from mail_type import mail_type
from cut_email import cut_email

def test_get():
    # 输入邮件地址, 口令和POP3服务器地址:
    email = '1805515795@qq.com'
    password = 'dlcdkwbfdendcddj'
    pop3_server = 'pop.qq.com'
    mails=get_email(email, password, pop3_server)
    for i in range(len(mails)):
        header=['From', 'To', 'Cc', 'Bcc', 'Subject']
        print('%s: %s' % (header[0], mails[i].from_str))
        print('%s: %s' % (header[1], mails[i].to_list))
        print('%s: %s' % (header[2], mails[i].cc_list))
        print('%s: %s' % (header[3], mails[i].bcc_list))
        print('%s: %s' % (header[4], mails[i].subject_str))
        print('mail body: %s' % (mails[i].body_str))
        print('mail attach: %s' % (mails[i].attach_list))
        print('\n')
    print("there are {} emails".format(len(mails)))

def test_cut():
    # 输入邮件地址, 口令和POP3服务器地址:
    email = '1805515795@qq.com'
    password = 'dlcdkwbfdendcddj'
    pop3_server = 'pop.qq.com'
    cut_email(email, password, pop3_server, 1)

if __name__ == "__main__":
    test_get()
    #test_cut()
    #test_get()