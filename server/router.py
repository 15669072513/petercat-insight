import json
import subprocess
import os
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
def getData(sql: str):
    client = ClickHouseClient(
        host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
        port=int(os.getenv('CLICKHOUSE_PORT', 8123)),
        username=os.getenv('CLICKHOUSE_USER'),
        password=os.getenv('CLICKHOUSE_PASSWORD'),
        database=os.getenv('CLICKHOUSE_DB', 'default')
    )
    try:

        data = client.query(sql)
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        return json.dumps({"success": False, "message": str(e)})
    finally:
        client.close()



@router.get("/clomonitor/lint")
def get_clomonitor_lint(gitUrl: str):
    try:
        # 配置参数
        LINTER_EXECUTABLE = "/root/clomonitor/clomonitor-linter-nightly-musl"
        MODE = "mix"
        CHECK_SET = "ant-incubator"
        CLONE_BASE_DIR = "/root/clomonitor_tmp"
        GIT_TIMEOUT = 300  # 5分钟git clone超时
        LINTER_TIMEOUT = 300  # 5分钟linter超时

        # 从URL中提取仓库名称
        try:
            # 处理https://github.com/owner/repo格式
            gitUrl = gitUrl.replace('.git', '')
            path_parts = gitUrl.replace('https://github.com/', '').replace('.git', '').split('/')
            if len(path_parts) >= 2:
                repo = path_parts[1]
                # 去掉可能的查询参数或片段标识符
                repo = repo.split('?')[0].split('#')[0]
                repo_name = repo
            else:
                raise ValueError("无效的GitHub URL格式")
        except Exception as e:
            raise ValueError(f"URL解析失败: {str(e)}")

        # 创建目标路径
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
            gitUrl,
            target_path
        ]

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

        # 构造clomonitor命令
        linter_cmd = [
            LINTER_EXECUTABLE,
            "--mode", MODE,
            "--url", gitUrl,
            "--path", target_path,
            "--check-set", CHECK_SET,
            "--format", "json"
        ]

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
                    "return_code": linter_result.returncode,
                    "cloned_path": target_path
                }
            }
        else:
            return {
                "success": False,
                "message": f"clomonitor命令执行失败，返回码: {linter_result.returncode}",
                "data": {
                    "stdout": linter_result.stdout,
                    "stderr": linter_result.stderr,
                    "return_code": linter_result.returncode,
                    "cloned_path": target_path
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
