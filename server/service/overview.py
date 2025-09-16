import os
from typing import Optional
from github import Github
# 使用环境变量存储 token
TOKEN = os.getenv("GITHUB_TOKEN")  # 设置环境变量: export GITHUB_TOKEN=ghp_xxx...
g = Github(TOKEN) if TOKEN else Github()  # 有 token 就用，没有就匿名（不推荐生产使用）


def get_overview(repo_name: Optional[str] = None):
    if not repo_name:
        return None

    try:
        repo = g.get_repo(repo_name)

        # 注意：.totalCount 在 PyGithub 中可能不会立即生效（尤其是大仓库），可用 len(list()) 替代（但更慢）
        # 所以这里我们只取最新一页来估算或精确获取（如果 commit 不多）
        commits = repo.get_commits()
        # 如果只想快速获取数量而不在乎完全准确，可以用 totalCount（基于 API 返回头）
        commit_count = commits.totalCount  # 这个值是准确的，不需要遍历所有页

        info = {
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "commits": commit_count,
        }

        return info

    except Exception as e:
        print(f"An error occurred while fetching {repo_name}: {e}")
        return None

    finally:
        # 好习惯：及时关闭连接
        g.close()
