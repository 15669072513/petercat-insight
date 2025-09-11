import axios from 'axios';
import { promises as fs } from 'fs';
import { join } from 'path';
import {ActiveData, TimeData} from "@/app/hooks/util";

// 定义类型
interface ActivityData {
    user: string;
    value: number;
}

// 获取活动数据
export async function getActivityData(repoName: string): Promise<ActivityData[]> {
    const url = `https://oss.open-digger.cn/github/${repoName}/activity_details.json`;

    try {
        const response = await axios.get(url);
        const data = response.data;

        if (!data) return [];

        // 过滤出月度数据
        const monthlyData: { [key: string]: Array<[string, number]> } = {};
        for (const [key, value] of Object.entries(data)) {
            if (key.includes('-')) {
                monthlyData[key] = value as Array<[string, number]>;
            }
        }

        // 获取最近的月份
        const keys = Object.keys(monthlyData);
        if (keys.length === 0) return [];

        // 提取年份和月份
        const months = keys.map(key => {
            const [year, month] = key.split('-').map(Number);
            return { year, month };
        });

        // 找到最新的月份（按年份和月份排序）
        months.sort((a, b) => {
            if (a.year !== b.year) return b.year - a.year;
            return b.month - a.month;
        });

        const mostRecentMonthKey = `${months[0].year}-${String(months[0].month).padStart(2, '0')}`;
        const result = monthlyData[mostRecentMonthKey].map(([user, value]) => ({
            user,
            value,
        }));

        return result;
    } catch (err) {
        console.error('Failed to fetch activity data:', err);
        return [];
    }
}

// 获取活跃时间数据
export async function getActiveDatesAndTimes(repoName: string): Promise<ActiveData> {
    const url = `https://oss.open-digger.cn/github/${repoName}/active_dates_and_times.json`;

    try {
        const response = await axios.get(url);
        const data = response.data;

        const patternYear = /^\d{4}$/;
        const patternQuarter = /^\d{4}Q[1-4]$/;
        const patternMonth = /^\d{4}-\d{2}$/;

        const years: string[] = [];
        const quarters: string[] = [];
        const months: string[] = [];

        for (const key in data) {
            if (patternYear.test(key)) years.push(key);
            else if (patternQuarter.test(key)) quarters.push(key);
            else if (patternMonth.test(key)) months.push(key);
        }

        // 获取最新时间
        const safeGetLatest = (arr: string[]) => (arr.length > 0 ? arr.sort().pop() : null);
        const latestYearKey = safeGetLatest(years);
        const latestQuarterKey = safeGetLatest(quarters);
        const latestMonthKey = safeGetLatest(months);

        // 转换168小时数据
        const convert168ToDayHourValue = (arr168: number[]): TimeData[] => {
            if (!arr168 || arr168.length === 0) return [];

            const dayMap = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
            return arr168.map((value, index) => {
                const dayIndex = Math.floor(index / 24);
                const hour = index % 24;
                return { day: dayMap[dayIndex], hour, value };
            });
        };

        const yearData = latestYearKey ? convert168ToDayHourValue(data[latestYearKey]) : [];
        const quarterData = latestQuarterKey ? convert168ToDayHourValue(data[latestQuarterKey]) : [];
        const monthData = latestMonthKey ? convert168ToDayHourValue(data[latestMonthKey]) : [];

        return { year: yearData, quarter: quarterData, month: monthData };
    } catch (err) {
        console.error('Failed to fetch active dates and times:', err);
        return { year: [], quarter: [], month: [] };
    }
}

// 主函数
// async function main() {
//     const repoName = 'your-repo-name'; // 替换为实际仓库名
//
//     try {
//         const activityData = await getActivityData(repoName);
//         const activeData = await getActiveDatesAndTimes(repoName);
//
//         console.log('Activity Data:');
//         console.log(JSON.stringify(activityData, null, 2));
//
//         console.log('\nActive Dates and Times:');
//         console.log(JSON.stringify(activeData, null, 2));
//     } catch (err) {
//         console.error('Error in main:', err);
//     }
// }
//
// main();
