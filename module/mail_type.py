"""
 文件名：mail_type.py
 作者：孙策
 介绍：使用POP3从邮件服务器下载邮件，使用email对邮件解析
 创建时间：2021/7/30
"""

class mail_type:
    def __init__(self, from_str, to_list, cc_list, bcc_list, subject_str, body_str, attach_list, mail_id):
        self.from_str=from_str      # 发件人
        self.to_list=to_list        # 收件人
        self.cc_list=cc_list        # 收件人（抄送）
        self.bcc_list=bcc_list        # 收件人（密送）
        self.subject_str=subject_str    # 邮件标题
        self.body_str=body_str      # 正文（文本）
        self.attach_list=attach_list    # 附件地址（已保存在本地）
        self.mail_id=mail_id        # 邮件id
