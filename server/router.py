import json
import subprocess
import os
import time
import requests
from fastapi import APIRouter
from service.activity import get_active_dates_and_times, get_activity_data
from service.clickhouse import ClickHouseClient
from service.contributor import get_contributor_data
from service.issue import get_issue_data, get_issue_resolution_duration
from service.overview import get_overview
from service.pr import get_code_frequency, get_pr_data

# ref: https://open-digger.cn/en/docs/user_docs/metrics/metrics_usage_guide
router = APIRouter(
    prefix="/api/insight",
    tags=["insight"],
    responses={404: {"description": "Not found"}},
)

# GitHub API 缓存：{url: {"data": data, "expire_time": expire_time}}
# 过期时间3天 = 3 * 24 * 60 * 60 = 259200 秒
GITHUB_API_CACHE_TTL = 3 * 24 * 60 * 60
github_api_cache = {}


@router.get("/issue/statistics")
def get_issue_insight(repo_name: str):
    try:
        result = get_issue_data(repo_name)
        return {
            "success": True,
            "data": result,
        }

    except Exception as e:
        return json.dumps({"success": False, "message": str(e)})


@router.get("/issue/resolution_duration")
def get_issue_resolution_duration_insight(repo_name: str):
    try:
        result = get_issue_resolution_duration(repo_name)
        return {
            "success": True,
            "data": result,
        }

    except Exception as e:
        return json.dumps({"success": False, "message": str(e)})


@router.get("/pr/statistics")
def get_pr_insight(repo_name: str):
    try:
        result = get_pr_data(repo_name)
        return {
            "success": True,
            "data": result,
        }

    except Exception as e:
        return json.dumps({"success": False, "message": str(e)})


@router.get("/contributor/statistics")
def get_contributor_insight(repo_name: str):
    try:
        result = get_contributor_data(repo_name)
        return {
            "success": True,
            "data": result,
        }

    except Exception as e:
        return json.dumps({"success": False, "message": str(e)})


@router.get("/pr/code_frequency")
def get_code_frequency_insight(repo_name: str):
    try:
        result = get_code_frequency(repo_name)
        return {
            "success": True,
            "data": result,
        }

    except Exception as e:
        return json.dumps({"success": False, "message": str(e)})


@router.get("/activity/statistics")
def get_activity_insight(repo_name: str):
    try:
        result = get_activity_data(repo_name)
        return {
            "success": True,
            "data": result,
        }

    except Exception as e:
        return json.dumps({"success": False, "message": str(e)})


@router.get("/activity/dates_and_times")
def get_active_dates_and_times_insight(repo_name: str):
    try:
        result = get_active_dates_and_times(repo_name)
        return {
            "success": True,
            "data": result,
        }

    except Exception as e:
        return json.dumps({"success": False, "message": str(e)})


@router.get("/overview")
def get_overview_data(repo_name: str):
    try:
        result = get_overview(repo_name)
        return {
            "success": True,
            "data": result,
        }

    except Exception as e:
        return json.dumps({"success": False, "message": str(e)})


@router.get("/ck/getData")
def getData(sql: str,reqType: str):
    # 创建 ClickHouseClient 实例
    client = ClickHouseClient(
        host='clickhouse.open-digger.cn',
        port=int(os.getenv('CLICKHOUSE_PORT', 8123)),
        username='antgroup',
        password='G7f$K9@qL1x!',
        database='opensource'
    )
    try:
        data = client.query(sql, reqType)
        print(f"reqType: {reqType}")
        print(f"data: {data[0] if len(data) > 0 else '空数据'}")
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        return json.dumps({"success": False, "message": str(e)})
    finally:
        # 关闭连接
        client.close()


@router.get("/clomonitor/lint")
def get_clomonitor_lint(gitUrl: str):
    try:
        # 配置参数
        LINTER_EXECUTABLE = "/root/clomonitor/clomonitor-linter-nightly-musl"
        GIT_TOKEN = os.getenv("GITHUB_TOKEN", "")
        if not GIT_TOKEN:
            return {
                "success": False,
                "message": "未配置GITHUB_TOKEN环境变量"
            }
        MODE = "mix"
        CHECK_SET = "ant-incubator"
        CLONE_BASE_DIR = "/root/clomonitor_tmp"
        GIT_TIMEOUT = 300  # 5分钟git clone超时
        LINTER_TIMEOUT = 300  # 5分钟linter超时
        gitTokenUrl = gitUrl.replace('.git', '').replace('https://', 'https://'+GIT_TOKEN+'@')
        # 从URL中提取仓库名称
        try:
            # 去掉 .git 后缀和 query 参数、fragment
            clean_url = gitUrl.replace('.git', '').split('?')[0].split('#')[0]

            # 解析出 owner/repo
            # 处理 https://github.com/owner/repo 格式
            path_parts = clean_url.replace('https://github.com/', '').split('/')
            if len(path_parts) >= 2:
                repo_name = path_parts[0] + '/' + path_parts[1]
            else:
                raise ValueError("无效的GitHub URL格式")
        except Exception as e:
            raise ValueError(f"URL解析失败: {str(e)}")

        # 创建目标路径
        print(f"仓库名称: {repo_name}")
        target_path = os.path.join(CLONE_BASE_DIR, repo_name)

        # 确保基础目录存在
        os.makedirs(CLONE_BASE_DIR, exist_ok=True)

        # 如果目录已存在，先删除
        if os.path.exists(target_path):
            import shutil
            shutil.rmtree(target_path)

        # git clone命令
        git_cmd = [
            "git",
            "clone",
            gitTokenUrl,
            target_path
        ]
        print(f"执行git clone命令: {' '.join(git_cmd)}")

        # 执行git clone
        git_result = subprocess.run(
            git_cmd,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT
        )

        if git_result.returncode != 0:
            return {
                "success": False,
                "message": f"Git clone失败，返回码: {git_result.returncode}",
                "data": {
                    "stdout": git_result.stdout,
                    "stderr": git_result.stderr,
                    "return_code": git_result.returncode
                }
            }

        # 检查clone的目标路径是否存在
        if not os.path.exists(target_path):
            return {
                "success": False,
                "message": "Git clone失败：目标目录不存在",
                "data": {
                    "stdout": git_result.stdout,
                    "stderr": git_result.stderr,
                    "return_code": git_result.returncode,
                    "target_path": target_path
                }
            }

        # 检查目标目录是否为空（可能clone了但没有文件）
        if not os.listdir(target_path):
            return {
                "success": False,
                "message": "Git clone失败：目标目录为空，仓库可能为空或clone不完整",
                "data": {
                    "stdout": git_result.stdout,
                    "stderr": git_result.stderr,
                    "return_code": git_result.returncode,
                    "target_path": target_path
                }
            }

        # 构造clomonitor命令
        linter_cmd = [
            LINTER_EXECUTABLE,
            "--mode", MODE,
            "--url", gitUrl,
            "--path", target_path,
            "--check-set", CHECK_SET,
            "--format", "json"
        ]
        print(f"执行clomonitor命令: {' '.join(linter_cmd)}")
        # 执行clomonitor命令
        linter_result = subprocess.run(
            linter_cmd,
            capture_output=True,
            text=True,
            timeout=LINTER_TIMEOUT
        )

        # 检查结果
        if linter_result.returncode == 0:
            return {
                "success": True,
                "data": {
                    "stdout": linter_result.stdout,
                    "stderr": linter_result.stderr,
                    "return_code": linter_result.returncode
                }
            }
        else:
            return {
                "success": False,
                "message": f"clomonitor命令执行失败，返回码: {linter_result.returncode}",
                "data": {
                    "stdout": linter_result.stdout,
                    "stderr": linter_result.stderr,
                    "return_code": linter_result.returncode
                }
            }

    except subprocess.TimeoutExpired as e:
        return {
            "success": False,
            "message": f"{'Git clone' if 'git' in str(e.cmd) else 'clomonitor'}超时（超过5分钟）"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


@router.get("/githubApiAdaptor")
def github_api_adaptor(url: str):
    """GitHub API 中转接口（带3天缓存）"""
    global github_api_cache

    # 检查缓存
    current_time = time.time()
    if url in github_api_cache:
        cache_entry = github_api_cache[url]
        if current_time < cache_entry["expire_time"]:
            print(f"[Cache] 命中缓存: {url}")
            return {
                "ok": True,
                "json": cache_entry["data"],
                "cached": True
            }
        else:
            # 缓存已过期，删除
            del github_api_cache[url]
            print(f"[Cache] 缓存已过期: {url}")

    try:
        # 获取 GitHub Token
        git_token = os.getenv("GITHUB_TOKEN", "")
        if not git_token:
            return {
                "success": False,
                "message": "未配置GITHUB_TOKEN环境变量"
            }

        # 设置请求头
        headers = {
            "Authorization": f"Bearer {git_token}",
            "Accept": "application/json"
        }

        # 发起请求
        response = requests.get(url, headers=headers, timeout=30)
        print(f"response: {response}")

        if response.ok:
            data = response.json()
            print(f"response.json(): {data}")

            # 存入缓存
            github_api_cache[url] = {
                "data": data,
                "expire_time": current_time + GITHUB_API_CACHE_TTL
            }
            print(f"[Cache] 已缓存: {url}, 过期时间: {GITHUB_API_CACHE_TTL}秒后")

            return {
                "ok": True,
                "json": data,
                "cached": False
            }
        else:
            return {
                "ok": False,
                "message": f"GitHub API请求失败，状态码: {response.status_code}",
                "json": {
                    "status_code": response.status_code,
                    "text": response.text
                }
            }

    except requests.RequestException as e:
        return {
            "ok": False,
            "message": f"请求异常: {str(e)}"
        }
    except Exception as e:
        return {
            "ok": False,
            "message": str(e)
        }
