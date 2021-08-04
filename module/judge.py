"""
*文件名:judge.py
*作者:孙策、叶尚察
*描述:登录、注册功能
*创建时间：2021/7/8
*修改人:孙策
*修改时间:2021/7/8
*修改内容:更新方法showdata,login_judge,register；增加了insertdata
*修改人:孙策
*修改时间:2021/7/9
*修改内容:修复了无限“欢迎”，无限“注册”的bug
*修改人:孙策
*修改时间:2021/7/21
*修改内容:修复了无法使用字符注册的bug
"""

from module.databaseClass import databaseLink

# 根据账号查询用户信息
def showdata(username):
    tempdatabaseLink = databaseLink()
    user_name="\'"+username+"\'"
    query_str = "select uID,password from user where user.uID = {} ".format(user_name)
    #print(query_str)
    #usrs_info = ['','']
    usrs_info = tempdatabaseLink.db_query(query_str)
    return usrs_info


def login_judge(account, password):

    if account=='' or password=='' :
        return 'the account number or password is empty', False
    
    usrs_info = showdata(account)
    #print(usrs_info)
    if usrs_info:
        if password==usrs_info[1]:
            return 'Welcome：', True
        else:
            return 'wrong password', False
    else:
        return "you haven't registered yet", False


def insertdata(username, password):
    tempdatabaseLink = databaseLink()
    user_name="\'"+username+"\'"
    pass_word="\'"+password+"\'"
    query_str = f"insert into user(uID, password) values({user_name},{pass_word})"
    #print(query_str)
    tempdatabaseLink.db_insert(query_str)
    #return usrs_info

def register(account, password, passwordf):
    usrs_info = showdata(account)
    # 检查账号存在、密码为空、密码前后不一致
    if password =='' or account=='':
        return 'the account number or password is empty', False
    elif usrs_info:
        return 'account number already exists', False
    elif password !=passwordf:
        return 'inconsistent password', False
    elif (len(password)<6 or len(password)>12):
        return 'format error', False
    else:
        insertdata(account, password)
        return 'login was successful', True
