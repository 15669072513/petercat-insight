import { get_data } from './util'; // 导入 insight.ts 中的 get_data 函数
import axios from 'axios';

// 定义类型
interface MetricsMapping {
    [key: string]: string;
}

interface DataEntry {
    type: string;
    date: string;
    value: number;
}

interface Result {
    year: DataEntry[];
    quarter: DataEntry[];
    month: DataEntry[];
}

interface IssueResolutionDurationResult {
    year: Array<{ date: string; value: number[] }>;
    quarter: Array<{ date: string; value: number[] }>;
    month: Array<{ date: string; value: number[] }>;
}

// 获取问题数据
export async function getIssueData(repoName: string): Promise<Result> {
    const metricsMapping: MetricsMapping = {
        "issues_new": "open",
        "issues_closed": "close",
        "issue_comments": "comment",
    };

    const issueData = await get_data(repoName, metricsMapping);
    return issueData;
}

// 获取问题解决时长数据
export async function getIssueResolutionDuration(repoName: string): Promise<IssueResolutionDurationResult> {
    const url = `https://oss.open-digger.cn/github/${repoName}/issue_resolution_duration.json`;

    try {
        const response = await axios.get(url);
        const data: Record<string, Record<string, number>> = response.data;

        const quantileKeys = ["quantile_0", "quantile_1", "quantile_2", "quantile_3", "quantile_4"];
        const quantileData: Record<string, Record<string, number>> = {};

        for (const key of quantileKeys) {
            if (key in data) {
                quantileData[key] = data[key];
            }
        }

        const allTimeKeys = new Set<string>();
        for (const qk of Object.keys(quantileData)) {
            for (const key of Object.keys(quantileData[qk])) {
                allTimeKeys.add(key);
            }
        }

        const yearPattern = /^\d{4}$/;
        const quarterPattern = /^\d{4}Q[1-4]$/;
        const monthPattern = /^\d{4}-\d{2}$/;

        const result: IssueResolutionDurationResult = {
            year: [],
            quarter: [],
            month: [],
        };

        for (const key of allTimeKeys) {
            const values: number[] = [];
            for (const qk of quantileKeys) {
                values.push(quantileData[qk]?.[key] || 0);
            }

            if (yearPattern.test(key)) {
                result.year.push({ date: key, value: values });
            } else if (quarterPattern.test(key)) {
                result.quarter.push({ date: key, value: values });
            } else if (monthPattern.test(key)) {
                result.month.push({ date: key, value: values });
            }
        }

        // 排序
        result.year.sort((a, b) => parseInt(a.date) - parseInt(b.date));
        result.quarter.sort((a, b) => {
            const aYear = parseInt(a.date.slice(0, 4));
            const aQuarter = parseInt(a.date.slice(-1));
            const bYear = parseInt(b.date.slice(0, 4));
            const bQuarter = parseInt(b.date.slice(-1));
            return aYear !== bYear ? aYear - bYear : aQuarter - bQuarter;
        });
        result.month.sort((a, b) => {
            const [aYear, aMonth] = a.date.split('-').map(Number);
            const [bYear, bMonth] = b.date.split('-').map(Number);
            return aYear !== bYear ? aYear - bYear : aMonth - bMonth;
        });

        return result;
    } catch (error) {
        console.error('Error fetching issue resolution duration data:', error);
        return { year: [], quarter: [], month: [] };
    }
}

// 主函数
// async function main() {
//     const repoName = 'your-repo-name'; // 替换为实际仓库名
//
//     try {
//         const issueData = await getIssueData(repoName);
//         console.log('Issue Data:', JSON.stringify(issueData, null, 2));
//
//         const resolutionData = await getIssueResolutionDuration(repoName);
//         console.log('Issue Resolution Duration Data:', JSON.stringify(resolutionData, null, 2));
//     } catch (err) {
//         console.error('Error in main:', err);
//     }
// }
//
// main();
