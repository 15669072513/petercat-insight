import axios from 'axios';

// 定义类型
interface ContributorData {
    year: Array<{ date: string; value: number }>;
    quarter: Array<{ date: string; value: number }>;
    month: Array<{ date: string; value: number }>;
}

// 主函数
export async function getContributorData(repoName: string): Promise<ContributorData> {
    const url = `https://oss.open-digger.cn/github/${repoName}/contributors.json`;

    // 正则表达式匹配
    const patternYear = /^\d{4}$/;
    const patternQuarter = /^\d{4}Q\d$/;
    const patternMonth = /^\d{4}-\d{2}$/;

    try {
        const response = await axios.get(url);
        const data: Record<string, number> = response.data;

        if (!data) {
            return { year: [], quarter: [], month: [] };
        }

        // 初始化统计对象
        const yearData: Record<string, number> = {};
        const quarterData: Record<string, number> = {};
        const monthData: Record<string, number> = {};

        // 遍历数据并分类统计
        for (const [date, value] of Object.entries(data)) {
            if (patternYear.test(date)) {
                yearData[date] = (yearData[date] || 0) + value;
            } else if (patternQuarter.test(date)) {
                quarterData[date] = (quarterData[date] || 0) + value;
            } else if (patternMonth.test(date)) {
                monthData[date] = (monthData[date] || 0) + value;
            }
        }

        // 转换为数组并排序
        const yearResult = Object.entries(yearData).map(([date, value]) => ({
            date,
            value,
        })).sort((a, b) => a.date.localeCompare(b.date));

        const quarterResult = Object.entries(quarterData).map(([date, value]) => ({
            date,
            value,
        })).sort((a, b) => a.date.localeCompare(b.date));

        const monthResult = Object.entries(monthData).map(([date, value]) => ({
            date,
            value,
        })).sort((a, b) => a.date.localeCompare(b.date));

        return { year: yearResult, quarter: quarterResult, month: monthResult };
    } catch (error) {
        console.error('Error fetching contributor data:', error);
        return { year: [], quarter: [], month: [] };
    }
}

// 执行主函数
// async function main() {
//     const repoName = 'your-repo-name'; // 替换为实际仓库名
//
//     try {
//         const result = await getContributorData(repoName);
//         console.log('Contributor Data:', JSON.stringify(result, null, 2));
//     } catch (err) {
//         console.error('Error in main:', err);
//     }
// }
//
// main();
