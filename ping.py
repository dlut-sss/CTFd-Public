"""
用于检查数据库服务器是否可用的脚本。
本质上是一个跨平台、与数据库无关的 mysqladmin。
"""
import time

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url

from CTFd.config import Config

url = make_url(Config.DATABASE_URL)

# 忽略sqlite数据库
if url.drivername.startswith("sqlite"):
    exit(0)

# 清空数据库，以便 raw_connection 在数据库不存在时不会出错
# 如果数据库不存在，CTFd 将创建该数据库
url.database = None

# 等待数据库服务器可用
engine = create_engine(url)
print(f"[CTFd] 等待{url.host}就绪。。。", end="", flush=True)
while True:
    try:
        engine.raw_connection()
        break
    except Exception:
        print("。", end="", flush=True)
        time.sleep(3)

print(f"[CTFd] {url.host}已就绪！", flush=True)
time.sleep(1)
