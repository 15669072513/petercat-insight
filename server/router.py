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




@router.get("/clomonitor")
def get_clomonitor(gitUrl: str, checkSet: str):
    try:
        # 配置参数
        LINTER_EXECUTABLE = os.path.join(os.path.dirname(__file__), "utils", "clomonitor-linter-centos7-musl")
        CHECK_SET = checkSet

        # 执行clomonitor命令
        linter_cmd = [
            LINTER_EXECUTABLE,
            "--url", gitUrl,
            "--mode", "mix",
            "--check-set", CHECK_SET,
            "--format", "json",
            "--path", "/tmp/"
        ]

        # 执行命令，设置超时
        result = subprocess.run(
            linter_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )

        if result.returncode == 0:
            return {
                "success": True,
                "data": {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                }
            }
        else:
            return {
                "success": False,
                "message": f"clomonitor命令执行失败，返回码: {result.returncode}",
                "data": {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                }
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "clomonitor执行超时（超过5分钟）"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


@router.get("/clomonitor/lint")
def get_clomonitor_lint(gitUrl: str):
    try:
        # 配置参数
        LINTER_EXECUTABLE = "/root/clomonitor/clomonitor-linter-nightly-musl"
        MODE = "mix"
        CHECK_SET = "ant-incubator"
        LINTER_TIMEOUT = 300  # 5分钟linter超时

        # 从URL中提取仓库名称
        try:
            # 处理https://github.com/owner/repo格式
            gitUrl = gitUrl.replace('.git', '')
        except Exception as e:
            raise ValueError(f"URL解析失败: {str(e)}")

        # 构造clomonitor命令
        linter_cmd = [
            LINTER_EXECUTABLE,
            "--mode", MODE,
            "--url", gitUrl,
            "--path", "/tmp/",
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
