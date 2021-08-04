"""
 文件名：get_email.py
 作者：孙策
 介绍：使用POP3从邮件服务器下载邮件，使用email对邮件解析
 创建时间：2021/7/30
"""
"""
 入口函数：get_email(email, password, pop3_server)
 输入参数：
    email：邮箱地址
    password：邮箱授权码或密码（qq邮箱为授权码）
    pop3_server：邮箱服务器地址
 返回值：
    mailgets：list类型，列表中元素为mail_type类型
 使用说明：
    需先引用mail_type类，使用参考test.py
"""
import os
import poplib
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr
from module.mail_type import mail_type

MAIL_DIR = './tmp'

def guess_charset(msg):
    # 先从msg对象获取编码
    charset = msg.get_charset()
    if charset is None:
        # 如果获取不到，再从Content-Type字段获取
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            # 去掉尾部不代表编码的字段
            charset = content_type[pos + 8:].strip('; format=flowed; delsp=yes')
    return charset

def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value

def get_root(msg):
    header=['From', 'To', 'Cc', 'Bcc', 'Subject']
        
    # 邮件的From
    value = msg.get(header[0], '')
    if value:
        hdr, addr = parseaddr(value)
        name = decode_str(hdr)
        from_str = u'%s <%s>' % (name, addr)

    # 邮件的To
    to_list=[]
    value = msg.get(header[1], '')
    if value:
        values = value.split(',')
        for item in values:
            hdr, addr = parseaddr(item)
            name = decode_str(hdr)
            to_str = u'%s <%s>' % (name, addr)
            to_list.append(to_str)

    # 邮件的Cc
    cc_list=[]
    value = msg.get(header[2], '')
    if value:
        values = value.split(',')
        for item in values:
            hdr, addr = parseaddr(item)
            name = decode_str(hdr)
            cc_str = u'%s <%s>' % (name, addr)
            cc_list.append(cc_str)

    # 邮件的Bcc
    bcc_list=[]
    value = msg.get(header[3], '')
    if value:
        values = value.split(',')
        for item in values:
            hdr, addr = parseaddr(item)
            name = decode_str(hdr)
            cc_str = u'%s <%s>' % (name, addr)
            cc_list.append(cc_str)

    # 邮件的Subject
    value = msg.get(header[4], '')
    if value:
        subject_str = decode_str(value)
    
    return from_str, to_list, cc_list, bcc_list, subject_str


# 解析邮件内容
def get_body(msg):
    if msg.is_multipart():
        # 如果邮件对象是一个MIMEMultipart,
        # get_payload()返回list，包含所有的子对象
        return get_body(msg.get_payload(0))
    else:
        content = msg.get_payload(decode=True)
        # 要检测文本编码
        charset = guess_charset(msg)
        if charset:
            content = content.decode(charset)
        return content


def get_attach(msg):
    # 获取邮件附件
    attachfile = []
    for part in msg.walk():        
        fileName = part.get_filename()

        # 如果文件名为纯数字、字母时不需要解码，否则需要解码
        try:
            fileName = decode_header(fileName)[0][0].decode(decode_header(fileName)[0][1])
            #print(fileName)
        except:
            pass

        # 如果获取到了文件，则将文件保存在制定的目录下
        if fileName:
            dirPath = MAIL_DIR
            if not os.path.exists(dirPath):
                os.makedirs(dirPath)
            filePath = os.path.join(dirPath, fileName)
            fp = open(filePath, 'wb')
            fp.write(part.get_payload(decode=True))
            fp.close()
            attachfile.append(filePath)
            #print("tips：附件下载成功，文件名为：" + fileName)
    return attachfile


def get_info(msg, index):
    
    #mail=mail_type()
    from_str, to_list, cc_list, bcc_list, subject_str = get_root(msg)
    #header=['From', 'To', 'Cc', 'Bcc', 'Subject']
    #print('%s: %s' % (header[0], from_str))
    #print('%s: %s' % (header[1], to_list))
    #print('%s: %s' % (header[2], cc_list))
    #print('%s: %s' % (header[3], bcc_list))
    #print('%s: %s' % (header[4], subject_str))
    #mail.append(from_str)
    #mail.append(to_list)
    #mail.append(cc_list)
    #mail.append(bcc_list)
    #mail.append(subject_str)

    body_str = get_body(msg)
    #print('mail body: %s' % (body_str))
    #mail.append(subject_str)

    attach_list = get_attach(msg)
    #print('mail attach: %s' % (attach_list))
    #mail.append(subject_str)
    
    mail = mail_type(from_str, to_list, cc_list, bcc_list, subject_str, body_str, attach_list, index)
    return mail
    

def get_email(email, password, pop3_server='pop.qq.com'):
    # 连接到POP3服务器:
    server = poplib.POP3(pop3_server)
    
    # 身份认证
    server.user(email)
    server.pass_(password)
    
    # list()返回所有邮件的编号:
    resp, mails, octets = server.list()
    #print(mails)
    
    # 获取一封邮件, 注意索引号从1开始:
    mailgets=[]
    length = len(mails)
    for index in range(length, 0, -1):
        resp, lines, octets = server.retr(index)
        # lines存储了邮件的原始文本的每一行,
        # 可以获得整个邮件的原始文本:
        msg_content = b'\r\n'.join(lines).decode('utf-8')
        # 解析出邮件:
        msg = Parser().parsestr(msg_content)
        mailgets.append(get_info(msg, index))
        #print('\n')

    # 关闭连接:
    server.quit()
    return mailgets


if __name__ == "__main__":
    # 输入邮件地址, 口令和POP3服务器地址:
    email = '1447996712@qq.com'
    password = 'supfqhilvfshihei'
    mails=get_email(email, password)
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