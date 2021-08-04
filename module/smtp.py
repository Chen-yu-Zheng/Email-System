"""
 文件名：smtp.py
 作者：张钊为
 介绍：使用socket建立用户与smtp服务器之间的联系，并且根据SMTP协议构造相应方法，实现邮件的发送
 创建时间：2021/7/30
"""
import socket
import io
import re
import email.utils
import email.message
import email.generator
import base64
import hmac
import copy
import datetime
import sys
from email.base64mime import body_encode as encode_base64


SMTP_PORT = 25
CRLF = "\r\n"
bCRLF = b"\r\n"
_MAXLINE = 8192 

OLDSTYLE_AUTH = re.compile(r"auth=(.*)", re.I)

# 可能出现的异常类
class SMTPException(OSError):
    """
    异常基类
    """

class SMTPNotSupportedError(SMTPException):
    """
    SMTP服务器不支持该命令或选项
    """

class SMTPServerDisconnected(SMTPException):
    """
    未连接到任何SMTP服务器
    """

class SMTPResponseException(SMTPException):
    def __init__(self, code, msg):
        self.smtp_code = code
        self.smtp_error = msg
        self.args = (code, msg)

class SMTPSenderRefused(SMTPResponseException):
    """
    发件人地址被拒绝
    """

    def __init__(self, code, msg, sender):
        self.smtp_code = code
        self.smtp_error = msg
        self.sender = sender
        self.args = (code, msg, sender)

class SMTPRecipientsRefused(SMTPException):
    """
    所有收件人地址被拒绝
    """

    def __init__(self, recipients):
        self.recipients = recipients
        self.args = (recipients,)


class SMTPDataError(SMTPResponseException):
    """
    SMTP服务器没有收到数据
    """

class SMTPConnectError(SMTPResponseException):
    """
    在连接时出现错误
    """

class SMTPHeloError(SMTPResponseException):
    """
    服务器拒绝了 HELO 回复
    """

class SMTPAuthenticationError(SMTPResponseException):
    """
    权限错误
    """

def quoteaddr(addrstring):
    """
    引用RFC 821定义的电子邮件地址的子集
    """
    displayname, addr = email.utils.parseaddr(addrstring)
    if (displayname, addr) == ('', ''):
        # parseaddr 无法解析时，原封不动地使用
        if addrstring.strip().startswith('<'):
            return addrstring
        return "<%s>" % addrstring
    return "<%s>" % addr

def _addr_only(addrstring):
    displayname, addr = email.utils.parseaddr(addrstring)
    if (displayname, addr) == ('', ''):
        return addrstring
    return addr

# 保留旧方法以实现向后兼容性
def quotedata(data):
    
    return re.sub(r'(?m)^\.', '..',
        re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, data))

def _quote_periods(bindata):
    return re.sub(br'(?m)^\.', b'..', bindata)

def _fix_eols(data):
    return  re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, data)

try:
    import ssl
except ImportError:
    _have_ssl = False
else:
    _have_ssl = True


class SMTP:
    """
    此类管理到SMTP或ESMTP服务器的连接
    SMTP类有如下属性：
    helo_resp：这是服务器响应最近的HELO命令

    ehlo_resp：这是服务器响应最近的EHLO命令，通常是多行的

    does_esmtp：如果执行完EHLO后服务器支持ESMTP，则为True

    esmtp_features：这是一个字典，其包含：如果服务器支持ESMTP，在执行EHLO命令后，是否会包含此服务器支持的SMTP服务扩展及其参数（如有）。
        
    """
    debuglevel = 0
    file = None
    helo_resp = None
    ehlo_msg = "ehlo"
    ehlo_resp = None
    does_esmtp = 0
    default_port = SMTP_PORT

    def __init__(self, host='', port=0, local_hostname=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 source_address=None):
        """
        创建一个新实例
        如果指定，`host'是要访问的远程主机的名称连接如果指定，`port'指定要连接的端口。默认情况下，
        使用smtplib.SMTP_端口。如果指定了主机，则调用connect方法，如果它返回除成功代码引发SMTPConnectError。
        如有规定，`local_hostname`用作HELO/EHLO中本地主机的FQDN指挥部。否则，本地主机名将使用socket.getfqdn()
        'source_address'参数采用2元组（主机，端口）作为其源地址绑定到的套接字连接。如果主机为“”，端口为0，则操作系统默认行为将使用。
        """
        self._host = host
        self.timeout = timeout
        self.esmtp_features = {}
        self.command_encoding = 'ascii'
        self.source_address = source_address

        if host:
            (code, msg) = self.connect(host, port)
            if code != 220:
                self.close()
                raise SMTPConnectError(code, msg)
        if local_hostname is not None:
            self.local_hostname = local_hostname
        else:
            # RFC 2821说我们应该在EHLO/HELO动词中使用fqdn，如果无法计算，我们应该使用域文字（本质上是像[A.B.C.D]这样的编码IP地址）
            fqdn = socket.getfqdn()
            if '.' in fqdn:
                self.local_hostname = fqdn
            else:
                # 找不到fqdn主机名，所以使用域文字
                addr = '127.0.0.1'
                try:
                    addr = socket.gethostbyname(socket.gethostname())
                except socket.gaierror:
                    pass
                self.local_hostname = '[%s]' % addr

    def __enter__(self):
        return self

    def __exit__(self, *args):
        try:
            code, message = self.docmd("QUIT")
            if code != 221:
                raise SMTPResponseException(code, message)
        except SMTPServerDisconnected:
            pass
        finally:
            self.close()

    def set_debuglevel(self, debuglevel):
        """
        设置debug输出级别，非false值会导致连接的调试消息以及发送到服务器和从服务器接收的所有消息的调试消息
        """
        self.debuglevel = debuglevel

    def _print_debug(self, *args):
        if self.debuglevel > 1:
            print(datetime.datetime.now().time(), *args, file=sys.stderr)
        else:
            print(*args, file=sys.stderr)

    def _get_socket(self, host, port, timeout):
        # 这使得SMTP_SSL更容易使用SMTP连接代码，只需更改套接字连接位
        if self.debuglevel > 0:
            self._print_debug('connect: to', (host, port), self.source_address)
        return socket.create_connection((host, port), timeout,
                                        self.source_address)

    def connect(self, host='localhost', port=0, source_address=None):
        """
        通过socket建立连接到给定端口上的主机。

        如果主机名以冒号（`:'）结尾，后跟一个数字没有指定端口，该后缀将被剥离，而解释为要使用的端口号的数字。

        """

        if source_address:
            self.source_address = source_address

        if not port and (host.find(':') == host.rfind(':')):
            i = host.rfind(':')
            if i >= 0:
                host, port = host[:i], host[i + 1:]
                try:
                    port = int(port)
                except ValueError:
                    raise OSError("nonnumeric port")
        if not port:
            port = self.default_port
        if self.debuglevel > 0:
            self._print_debug('connect:', (host, port))
        self.sock = self._get_socket(host, port, self.timeout)
        self.file = None
        (code, msg) = self.getreply()
        if self.debuglevel > 0:
            self._print_debug('connect:', repr(msg))
        return (code, msg)

    def send(self, s):
        """
        把s的内容发送给服务器
        """
        if self.debuglevel > 0:
            self._print_debug('send:', repr(s))
        if hasattr(self, 'sock') and self.sock:
            if isinstance(s, str):
                # send由'data'命令使用，其中不应使用命令_编码，但无论如何'data'需要将字符串本身转换为二进制，因此这不是问题。
                s = s.encode(self.command_encoding)
            try:
                self.sock.sendall(s)
            except OSError:
                self.close()
                raise SMTPServerDisconnected('Server not connected')
        else:
            raise SMTPServerDisconnected('please run connect() first')

    def putcmd(self, cmd, args=""):
        """
        给服务器发送命令
        """
        if args == "":
            str = '%s%s' % (cmd, CRLF)
        else:
            str = '%s %s%s' % (cmd, args, CRLF)
        self.send(str)

    def getreply(self):
        """
        从服务器获得回复
        返回一个包括server response code与server response string corresponding to response code的元组
        """
        resp = []
        if self.file is None:
            self.file = self.sock.makefile('rb')
        while 1:
            try:
                line = self.file.readline(_MAXLINE + 1)
            except OSError as e:
                self.close()
                raise SMTPServerDisconnected("Connection unexpectedly closed: "
                                             + str(e))
            if not line:
                self.close()
                # 如果到达文件末尾，返回SMTPServerDisconnected
                raise SMTPServerDisconnected("Connection unexpectedly closed")
            if self.debuglevel > 0:
                self._print_debug('reply:', repr(line))
            if len(line) > _MAXLINE:
                self.close()
                raise SMTPResponseException(500, "Line too long.")
            resp.append(line[4:].strip(b' \t\r\n'))
            code = line[:3]
            # 检查错误代码的语法是否正确
            # 如果续行中断，不要尝试读取续行
            try:
                errcode = int(code)
            except ValueError:
                errcode = -1
                break
            # 检查是否有多行响应
            if line[3:4] != b"-":
                break

        errmsg = b"\n".join(resp)
        if self.debuglevel > 0:
            self._print_debug('reply: retcode (%s); Msg: %a' % (errcode, errmsg))
        return errcode, errmsg

    def docmd(self, cmd, args=""):
        """
        发送命令，并返回其响应代码
        """
        self.putcmd(cmd, args)
        return self.getreply()

    # 标准SMTP命令
    def helo(self, name=''):
        """
        SMTP的HELO命令，是SMTP的核心命令，要为此命令发送的主机名默认为本地主机的FQDN
        """
        self.putcmd("helo", name or self.local_hostname)
        (code, msg) = self.getreply()
        self.helo_resp = msg
        return (code, msg)

    def ehlo(self, name=''):
        """ 
        SMTP的EHLO命令，要为此命令发送的主机名默认为本地主机的FQDN
        """
        self.esmtp_features = {}
        self.putcmd(self.ehlo_msg, name or self.local_hostname)
        (code, msg) = self.getreply()
        # 根据RFC1869，一些（写得不好的）MTA将在ehlo上断开连接。如果发生这种情况，抛出一个异常 
        if code == -1 and len(msg) == 0:
            self.close()
            raise SMTPServerDisconnected("Server not connected")
        self.ehlo_resp = msg
        if code != 250:
            return (code, msg)
        self.does_esmtp = 1
        # 解析ehlo响应 -ddm
        assert isinstance(self.ehlo_resp, bytes), repr(self.ehlo_resp)
        resp = self.ehlo_resp.decode("latin-1").split('\n')
        del resp[0]
        for each in resp:
            """
            为了能够与尽可能多的SMTP服务器通信，我们必须考虑到老式的授权方式，因为：
                1）否则，我们的SMTP功能解析器会感到困惑
                2）有些服务器只宣传我们使用旧样式支持的身份验证方法
            """
            
            auth_match = OLDSTYLE_AUTH.match(each)
            if auth_match:
                # 这不会删除重复项，但这没有问题
                self.esmtp_features["auth"] = self.esmtp_features.get("auth", "") \
                        + " " + auth_match.groups(0)[0]
                continue

            # RFC1869要求ehlo关键字和参数之间有空格
            m = re.match(r'(?P<feature>[A-Za-z0-9][A-Za-z0-9\-]*) ?', each)
            if m:
                feature = m.group("feature").lower()
                params = m.string[m.end("feature"):].strip()
                if feature == "auth":
                    self.esmtp_features[feature] = self.esmtp_features.get(feature, "") \
                            + " " + params
                else:
                    self.esmtp_features[feature] = params
        return (code, msg)

    def has_extn(self, opt):
        """
        服务器是否支持给定的SMTP服务扩展
        """
        return opt.lower() in self.esmtp_features

    

    def rset(self):
        """
        SMTP中的REST指令，表示重启事务
        """
        self.command_encoding = 'ascii'
        return self.docmd("rset")

    def _rset(self):
        """
        忽略任何SMTPServerDisconnected错误的内部“rset”命令
        """
        try:
            self.rset()
        except SMTPServerDisconnected:
            pass

    def noop(self):
        """
        SMTP中的NOOP命令，表示不干任何事
        """
        return self.docmd("noop")

    def mail(self, sender, options=[]):
        """
        SMTP中的MAIL命令，用于初始化邮件的xfer部分.
        """
        optionlist = ''
        if options and self.does_esmtp:
            if any(x.lower()=='smtputf8' for x in options):
                if self.has_extn('smtputf8'):
                    self.command_encoding = 'utf-8'
                else:
                    # options参数包括“SMTPUTF8”，但服务器不支持SMTPUTF8扩展。
                    raise SMTPNotSupportedError(
                        'SMTPUTF8 not supported by server')
            optionlist = ' ' + ' '.join(options)
        self.putcmd("mail", "FROM:%s%s" % (quoteaddr(sender), optionlist))
        return self.getreply()

    def rcpt(self, recip, options=[]):
        """
        SMTP中的RCPT命令，用于指定该邮件的一个接收者
        """
        optionlist = ''
        if options and self.does_esmtp:
            optionlist = ' ' + ' '.join(options)
        self.putcmd("rcpt", "TO:%s%s" % (quoteaddr(recip), optionlist))
        return self.getreply()

    def data(self, msg):
        """
        SMTP中的DATA命令，用于把邮件中的数据发送到服务器
        根据rfc821，自动引用以句点开头的行。
        """
        self.putcmd("data")
        (code, repl) = self.getreply()
        if self.debuglevel > 0:
            self._print_debug('data:', (code, repl))
        if code != 354:
            # 如果对数据命令有异常答复，则引发SMTPDataError
            raise SMTPDataError(code, repl)
        else:
            if isinstance(msg, str):
                msg = _fix_eols(msg).encode('ascii')
            q = _quote_periods(msg)
            if q[-2:] != bCRLF:
                q = q + bCRLF
            q = q + b"." + bCRLF
            self.send(q)
            (code, msg) = self.getreply()
            if self.debuglevel > 0:
                self._print_debug('data:', (code, msg))
            return (code, msg)

    def verify(self, address):
        """
        SMTP 中的 'verify' 命令，用于检测地址的有效性
        """
        self.putcmd("vrfy", _addr_only(address))
        return self.getreply()

    vrfy = verify

    def ehlo_or_helo_if_needed(self):
        """
        如果需要，调用 self.ehlo() and/or self.helo()
        """
        if self.helo_resp is None and self.ehlo_resp is None:
            if not (200 <= self.ehlo()[0] <= 299):
                (code, resp) = self.helo()
                if not (200 <= code <= 299):
                    raise SMTPHeloError(code, resp)

    def auth(self, mechanism, authobject, *, initial_response_ok=True):
        """
        SMTP中的授权命令Authentication，需要回复进程
        """
        mechanism = mechanism.upper()
        initial_response = (authobject() if initial_response_ok else None)
        if initial_response is not None:
            response = encode_base64(initial_response.encode('ascii'), eol='')
            (code, resp) = self.docmd("AUTH", mechanism + " " + response)
        else:
            (code, resp) = self.docmd("AUTH", mechanism)
        # 根据错误码调节
        if code == 334:
            challenge = base64.decodebytes(resp)
            response = encode_base64(
                authobject(challenge).encode('ascii'), eol='')
            (code, resp) = self.docmd(response)
        if code in (235, 503):
            return (code, resp)
        raise SMTPAuthenticationError(code, resp)



    def auth_plain(self, challenge=None):
        """ 
        用于PLAIN身份验证的Authobject。需要self.user和要设置的self.password
        """
        return "\0%s\0%s" % (self.user, self.password)


    def login(self, user, password, *, initial_response_ok=True):
        """
        远程登录邮箱
        """

        self.ehlo_or_helo_if_needed()
        if not self.has_extn("auth"):
            raise SMTPNotSupportedError(
                "SMTP AUTH extension not supported by server.")

        # 服务器声称支持的身份验证方法
        advertised_authlist = self.esmtp_features["auth"].split()

        # 我们可以按首选顺序处理的身份验证方法：
        preferred_auths = ['CRAM-MD5', 'PLAIN', 'LOGIN']

        # 如果需要并且服务器支持它们，我们将按首选顺序尝试支持的身份验证
        authlist = [auth for auth in preferred_auths
                    if auth in advertised_authlist]
        if not authlist:
            raise SMTPException("No suitable authentication method found.")

        # 一些服务器并不真正支持的身份验证方法，所以如果身份验证失败，我们将继续，直到我们尝试了所有方法。
        self.user, self.password = user, password
        for authmethod in authlist:
            method_name = 'auth_' + authmethod.lower().replace('-', '_')
            try:
                (code, resp) = self.auth(
                    authmethod, getattr(self, method_name),
                    initial_response_ok=initial_response_ok)
                # 235 == 'Authentication successful'
                # 503 == 'Error: already authenticated'
                if code in (235, 503):
                    return (code, resp)
            except SMTPAuthenticationError as e:
                last_exception = e

        # 我们无法成功登录。返回上次尝试的结果
        raise last_exception

    def starttls(self, keyfile=None, certfile=None, context=None):
        """
        建立安全连接
        """
        self.ehlo_or_helo_if_needed()
        if not self.has_extn("starttls"):
            raise SMTPNotSupportedError(
                "STARTTLS extension not supported by server.")
        (resp, reply) = self.docmd("STARTTLS")
        if resp == 220:
            if not _have_ssl:
                raise RuntimeError("No SSL support included in this Python")
            if context is not None and keyfile is not None:
                raise ValueError("context and keyfile arguments are mutually "
                                 "exclusive")
            if context is not None and certfile is not None:
                raise ValueError("context and certfile arguments are mutually "
                                 "exclusive")
            if keyfile is not None or certfile is not None:
                import warnings
                warnings.warn("keyfile and certfile are deprecated, use a"
                              "custom context instead", DeprecationWarning, 2)
            if context is None:
                context = ssl._create_stdlib_context(certfile=certfile,
                                                     keyfile=keyfile)
            self.sock = context.wrap_socket(self.sock,
                                            server_hostname=self._host)
            self.file = None
            self.helo_resp = None
            self.ehlo_resp = None
            self.esmtp_features = {}
            self.does_esmtp = 0
        else:
            raise SMTPResponseException(resp, reply)
        return (resp, reply)

    def sendmail(self, from_addr, to_addrs, msg, mail_options=[], rcpt_options=[]):

        self.ehlo_or_helo_if_needed()
        esmtp_opts = []
        if isinstance(msg, str):
            msg = _fix_eols(msg).encode('ascii')
        if self.does_esmtp:
            if self.has_extn('size'):
                esmtp_opts.append("size=%d" % len(msg))
            for option in mail_options:
                esmtp_opts.append(option)
        (code, resp) = self.mail(from_addr, esmtp_opts)
        if code != 250:
            if code == 421:
                self.close()
            else:
                self._rset()
            raise SMTPSenderRefused(code, resp, from_addr)
        senderrs = {}
        if isinstance(to_addrs, str):
            to_addrs = [to_addrs]
        for each in to_addrs:
            (code, resp) = self.rcpt(each, rcpt_options)
            if (code != 250) and (code != 251):
                senderrs[each] = (code, resp)
            if code == 421:
                self.close()
                raise SMTPRecipientsRefused(senderrs)
        if len(senderrs) == len(to_addrs):
            # 服务器拒绝了所有的收件人
            self._rset()
            raise SMTPRecipientsRefused(senderrs)
        (code, resp) = self.data(msg)
        if code != 250:
            if code == 421:
                self.close()
            else:
                self._rset()
            raise SMTPDataError(code, resp)
        # 到了这一定会有收件人，返回收件人
        return senderrs


    def close(self):
        """
        关闭与SMTP服务器的连接
        """
        try:
            file = self.file
            self.file = None
            if file:
                file.close()
        finally:
            sock = self.sock
            self.sock = None
            if sock:
                sock.close()

    def quit(self):
        """
        终止SMTP会话
        """
        res = self.docmd("quit")
        # 重新连接connect（）后需要新的EHLO
        self.ehlo_resp = self.helo_resp = None
        self.esmtp_features = {}
        self.does_esmtp = False
        self.close()
        return res


