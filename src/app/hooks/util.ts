import axios from 'axios';

// 定义类型
interface MetricsMapping {
    [key: string]: string;
}

export interface AggregatedData {
    year: Record<string, Record<string, number>>;
    quarter: Record<string, Record<string, number>>;
    month: Record<string, Record<string, number>>;
}

export interface TimeData {
    day: string;
    hour: number;
    value: number;
}

export interface ActiveData {
    year: TimeData[];
    quarter: TimeData[];
    month: TimeData[];
}


export interface DataEntry {
    type: string;
    date: string;
    value: number;
}

export interface Result {
    year: DataEntry[];
    quarter: DataEntry[];
    month: DataEntry[];
}

// 导出 get_data 函数
export async function get_data(repoName: string, metricsMapping: MetricsMapping): Promise<Result> {
    const baseUrl = `https://oss.open-digger.cn/github/${repoName}/`;

    const aggregatedData: AggregatedData = {
        year: {},
        quarter: {},
        month: {},
    };

    for (const [metric, metricType] of Object.entries(metricsMapping)) {
        const url = `${baseUrl}${metric}.json`;
        try {
            const response = await axios.get(url);
            const data = response.data;

            for (const [date, value] of Object.entries(data)) {
                if (date.includes('-')) {
                    const [year, month] = date.split('-').map(Number);
                    const quarter = `${year}Q${Math.floor((month - 1) / 3) + 1}`;
                    const numericValue = Number(value);


                    // 初始化聚合数据
                    if (!aggregatedData.year[year]) {
                        aggregatedData.year[year] = {};
                    }
                    if (!aggregatedData.year[year][metricType]) {
                        aggregatedData.year[year][metricType] = 0;
                    }
                    aggregatedData.year[year][metricType] += numericValue;

                    if (!aggregatedData.quarter[quarter]) {
                        aggregatedData.quarter[quarter] = {};
                    }
                    if (!aggregatedData.quarter[quarter][metricType]) {
                        aggregatedData.quarter[quarter][metricType] = 0;
                    }
                    aggregatedData.quarter[quarter][metricType] += numericValue;

                    if (!aggregatedData.month[date]) {
                        aggregatedData.month[date] = {};
                    }
                    if (!aggregatedData.month[date][metricType]) {
                        aggregatedData.month[date][metricType] = 0;
                    }
                    aggregatedData.month[date][metricType] += numericValue;
                }
            }
        } catch (error) {
            console.error(`Error fetching data from ${url}:`, error);
            return {
                year: [],
                quarter: [],
                month: [],
            };
        }
    }

    // 格式化结果
    const formatResult = (data: Record<string, Record<string, number>>): DataEntry[] => {
        const result: DataEntry[] = [];
        for (const [date, counts] of Object.entries(data)) {
            for (const [type, value] of Object.entries(counts)) {
                result.push({ type, date, value });
            }
        }
        return result;
    };

    return {
        year: formatResult(aggregatedData.year),
        quarter: formatResult(aggregatedData.quarter),
        month: formatResult(aggregatedData.month),
    };
}
