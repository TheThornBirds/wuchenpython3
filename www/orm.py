#创建一个全局的连接池，每个http请求都可以从连接池直接获取数据库连接，
#连接池由全局变量__pool存储，缺省情况下将编码设置为utf-8，自动提交事务：
import asyncio, logging, aiomysql

def log(sql, args=()):
    logging.info('SQL: %s' %sql)

@asyncio.coroutine
def create_pool(loop, **kw):
    logging.info('create dateabase connection poll...')
    global  __pool
    __pool = yield from aiomysql.create_pool(
        host = kw.get('host', 'localho,st'),
        port = kw.get('port', 3306),
        user = kw.get('user'),
        password = kw.get('password'),
        db = kw['db'],
        charset = kw.get('charset', 'utf-8'),
        autocommit = kw.get('autocommit', True),
        maxsize = kw.get('maxsize', 10),
        minsize = kw.get('minsize', 1),
        loop = loop
    )

#select,要执行select语句，我们要用select函数执行，需要传入sql语句和sql参数:
@asyncio.coroutine
def select(sql, args, size=None):
    logging.log(sql, args)
    global __pool
    with (yield from __pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.excute(sql.replace('?', '%s'), args or ())
        if size:
            rs = yield from cur.fetchall()
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
        logging.info('rows returned: %s' % len(rs))
        return rs

#insert,update,delete
@asyncio.coroutine
def execute(sql, args):
    log(sql)
    with (yield from __pool) as conn:
        try:
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        return affected

#ORM
from orm import Model, StringField, IntergerField
class User(Model):
    __table__ = 'users'
    id = IntergerField(primary_key=True)
    name = StingField()

#创建实例:
user = User(id=123, name='wuchen')
#存入数据库
user.insert()
#查询所有的User对象
users = user.findAll()

#定义model,定义所有orm映射的基类，Model:
class Model(dict, metaclass=ModelMetaclass):

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" %key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self,key,None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' %(key, str(value)))
                setattr(self, key, value)
        return value

print(user['id'])

