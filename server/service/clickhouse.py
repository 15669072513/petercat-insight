import logging

import clickhouse_connect
import os

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
        logging.log(f"🔧 ClickHouse 客户端初始化完成: {self.host}:{self.port} {self.database} {self.username} {self.password}")

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

    def query(self, sql):
        """
        执行 SQL 查询，返回 list of dict
        :param sql: 要执行的 SQL 语句
        :return: list[dict] 每一行作为一个字典
        """
        if not self.client:
            raise RuntimeError("❌ ClickHouse 客户端未初始化")

        try:
            result = self.client.query(sql)
            rows = []
            # 获取列名
            columns = result.column_names
            # 遍历数据行
            for row in result.result_set:
                row_dict = dict(zip(columns, row))
                rows.append(row_dict)
            return rows
        except Exception as e:
            raise RuntimeError(f"❌ SQL 执行失败: {e}")

    def close(self):
        """关闭连接（可选，适用于长连接管理）"""
        if self.client:
            self.client.close()


# 示例调用
if __name__ == '__main__':
    client = ClickHouseClient(
        host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
        port=int(os.getenv('CLICKHOUSE_PORT', 8123)),
        username=os.getenv('CLICKHOUSE_USER'),
        password=os.getenv('CLICKHOUSE_PASSWORD'),
        database=os.getenv('CLICKHOUSE_DB', 'default')
    )

    sql = "SELECT name, value FROM system.settings WHERE name LIKE 'max_%' LIMIT 5"
    try:
        data = client.query(sql)
        for row in data:
            print(row)
    except Exception as e:
        print(e)
    finally:
        client.close()
