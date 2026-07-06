import time
import hashlib
from typing import Dict, Any, Optional
import clickhouse_connect
import os

# 全局缓存变量
_global_cache: Dict[str, Dict[str, Any]] = {}
_global_cache_expiry = 30 * 60  # 30分钟（秒）

class ClickHouseClient:
    def __init__(self, host='localhost', port=8123, username=None, password=None, database='default'):
        """
        初始化 ClickHouse 客户端
        :param host: ClickHouse 服务器地址
        :param port: 端口（默认 HTTP 8123）
        :param username: 用户名
        :param password: 密码
        :param database: 数据库名
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.client = None
        self._create_client()

    def _create_client(self):
        """创建客户端连接"""
        try:
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database
            )
            print("✅ 成功连接到 ClickHouse")
        except Exception as e:
            raise ConnectionError(f"❌ 连接 ClickHouse 失败: {e}")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in _global_cache:
            return False
        
        cache_data = _global_cache[cache_key]
        current_time = time.time()
        
        # 检查是否过期
        if current_time - cache_data['timestamp'] > _global_cache_expiry:
            # 过期，删除缓存
            del _global_cache[cache_key]
            return False
        
        return True

    def _get_from_cache(self, cache_key: str) -> Optional[list]:
        """从缓存获取数据"""
        if self._is_cache_valid(cache_key):
            print(f"🎯 缓存命中: {cache_key}")
            return _global_cache[cache_key]['data']
        return None

    def _set_cache(self, cache_key: str, data: list):
        """设置缓存"""
        _global_cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        print(f"💾 缓存设置: {cache_key}")

    def clear_cache(self):
        """清空缓存"""
        _global_cache.clear()
        print("🗑️ 缓存已清空")

    @classmethod
    def clear_global_cache(cls):
        """清空全局缓存"""
        _global_cache.clear()
        print("🗑️ 全局缓存已清空")

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        total_cached = len(_global_cache)
        current_time = time.time()
        
        # 计算即将过期的缓存数量（5分钟内）
        expiring_soon = 0
        for cache_data in _global_cache.values():
            time_left = _global_cache_expiry - (current_time - cache_data['timestamp'])
            if time_left < 5 * 60:  # 5分钟内过期
                expiring_soon += 1
        
        return {
            'total_cached_queries': total_cached,
            'cache_expiry_minutes': _global_cache_expiry / 60,
            'expiring_soon_count': expiring_soon,
            'cache_keys': list(_global_cache.keys())[:10]  # 只显示前10个缓存键
        }

    def query(self, sql, reqType):
        """
        执行 SQL 查询，返回 list of dict
        :param reqType: 如果为 'None' 则不走缓存，直接查询
        :param sql: 要执行的 SQL 语句
        :return: list[dict] 每一行作为一个字典
        """
        if not self.client:
            raise RuntimeError("❌ ClickHouse 客户端未初始化")

        # 如果 reqType 为 'None'，使用 SQL 哈希作为缓存键
        if reqType == 'None':
            cache_key = hashlib.md5(sql.encode('utf-8')).hexdigest()
        else:
            cache_key = reqType

        # 尝试从缓存获取
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        try:
            print(f"🔍 执行 SQL:{cache_key}")
            result = self.client.query(sql)
            rows = []
            # 获取列名
            columns = result.column_names
            # 遍历数据行
            for row in result.result_set:
                row_dict = dict(zip(columns, row))
                rows.append(row_dict)

            # 设置缓存
            self._set_cache(cache_key, rows)
            return rows
        except Exception as e:
            raise RuntimeError(f"❌ SQL 执行失败: {e}")

    def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()
            self.client = None
            print("🔌 ClickHouse 连接已关闭")


# 示例调用
if __name__ == '__main__':
    client = ClickHouseClient(
        host='clickhouse.open-digger.cn',
        port=int(os.getenv('CLICKHOUSE_PORT', 8123)),
        username='antgroup',
        password='G7f$K9@qL1x!',
        database='opensource'
    )

    sql = "SELECT name, value FROM system.settings WHERE name LIKE 'max_%' LIMIT 5"
    
    print("=== 第一次查询（将访问数据库并缓存结果）===")
    try:
        start_time = time.time()
        data = client.query(sql, "a———aa")
        query_time = time.time() - start_time
        print(f"⏱️  查询耗时: {query_time:.3f}秒")
        print(f"📊 返回结果: {len(data)} 条记录")
        for row in data:
            print(row)
    except Exception as e:
        print(e)
    
    print("\n=== 第二次查询（将使用缓存）===")
    try:
        start_time = time.time()
        data = client.query(sql, "aa_bb")
        query_time = time.time() - start_time
        print(f"⏱️  查询耗时: {query_time:.3f}秒")
        print(f"📊 返回结果: {len(data)} 条记录")
        print("✅ 这次应该更快，因为是缓存命中！")
    except Exception as e:
        print(e)
    
    print("\n=== 缓存统计信息 ===")
    stats = client.get_cache_stats()
    print(f"📈 总缓存查询数: {stats['total_cached_queries']}")
    print(f"⏰ 缓存过期时间: {stats['cache_expiry_minutes']} 分钟")
    print(f"⚠️  即将过期缓存: {stats['expiring_soon_count']} 个")
    
    client.close()
