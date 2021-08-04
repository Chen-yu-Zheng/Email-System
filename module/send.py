"""
 文件名：send.py
 作者：张钊为
 介绍：使用构建的SMTP模块实现邮件到SMTP服务器的发送
 创建时间：2021/7/30
"""
from module import smtp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def send2others(from_addr, password, to_addr, message_topic, message, send_file=False, smtp_server= 'smtp.qq.com'):
	if len(message) >= 6 and message[0:6] == '<html>':
		# 网页文件
		msg = MIMEMultipart('alternative')
		
		# # 正常发送msg对象...
		msg = MIMEText(message, 'html', 'utf-8')#'<html><body><h1>Hello</h1>' + '<p>send by <a href="http://www.python.org">Python</a>...</p>' + '</body></html>', 'html', 'utf-8')

	else:
		# 普通邮件
		msg = MIMEText(message, 'plain', 'utf-8')#'hello, send by Python...', 'plain', 'utf-8')



	if send_file is True:
		send_path = input('file path: ')
		# 附件
		# 邮件对象:
		msg = MIMEMultipart()

		# 邮件正文是MIMEText:
		msg.attach(MIMEText(message, 'plain', 'utf-8'))

		# 添加附件就是加上一个MIMEBase，从本地读取一个图片:
		with open(send_path, 'rb') as f:
			# 设置附件的MIME和文件名:
			mime = MIMEBase('image', 'png', filename=send_path.split('/')[-1])
			# 加上必要的头信息:
			mime.add_header('Content-Disposition', 'attachment', filename=send_path.split('/')[-1])
			mime.add_header('Content-ID', '<0>')
			mime.add_header('X-Attachment-Id', '0')
			# 把附件的内容读进来:
			mime.set_payload(f.read())
			# 用Base64编码:
			encoders.encode_base64(mime)
			# 添加到MIMEMultipart:
			msg.attach(mime)
		send_file = False

	# msg = MIMEText('hello, send by Python...', 'plain', 'utf-8')
	msg['From'] = _format_addr(from_addr)
	msg['To'] = _format_addr(to_addr)
	msg['Subject'] = Header(message_topic, 'utf-8').encode()  # 邮件主题


	server = smtp.SMTP(smtp_server, 25) # SMTP协议默认端口是25
	# 建立安全链接
	server.starttls()
	server.set_debuglevel(1)

	server.login(from_addr, password)
	server.sendmail(from_addr, [to_addr], msg.as_string())
	server.quit()

if __name__ == '__main__':
	# 输入Email地址和口令:
	from_addr = '1805515795@qq.com'
	# from_addr = input('From: ')
	password = 'bdblylopgjuzcddb'
	# password = input('Password: ')
	# 输入收件人地址:
	# to_addr = '1447996712@qq.com'
	to_addr = '1447996712@qq.com'
	# to_addr = input('To: ')
	# 输入SMTP服务器地址:
	smtp_server = 'smtp.qq.com'
	# smtp_server = input('SMTP server: ')

	# 输入邮件主题
	message_topic = input('Message topic: ')


	message = input('Message: ')

	# send_pic = False
	send_file = False
	send2others(from_addr, password, to_addr, message_topic, message)






