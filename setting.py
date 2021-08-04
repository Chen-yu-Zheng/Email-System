"""
 文件名：setting.py
 作者：孙策
 创建时间：2021/7/20
 描述：tornado设置
"""

#设置
appsetting = {
    'template_path': 'template',
    'static_path': 'static',
    
    'pycket': {
        'engine': 'redis',
        'storage': {
            'host': '127.0.0.1',
            'port': 8080,
            'db_sessions': 10,
            'max_connections': 2 ** 31,
        },
        'cookies': {
            # 设置过期时间
            'expires_days': None,
            #'expires':None, #秒
        },
    }
    
}

appsecret="7114172b82354589ba988291e5f74e15"
