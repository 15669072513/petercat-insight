// pr.ts
import { get_data } from './util';
import { DataEntry } from './util'; // 确保从 util.ts 导入 DataEntry 接口

export async function getPRData(repoName: string) {
    const metricsMapping = {
        "change_requests": "open",
        "change_requests_accepted": "merge",
        "change_requests_reviews": "reviews",
    };
    return await get_data(repoName, metricsMapping);
}

export async function getCodeFrequency(repoName: string) {
    const metricsMapping = {
        "code_change_lines_add": "add",
        "code_change_lines_remove": "remove",
    };
    const data = await get_data(repoName, metricsMapping);

    // 显式声明 entries 的类型为 DataEntry[]
    const processEntries = (entries: DataEntry[]) => {
        return entries.map(entry => {
            if (entry.type === "remove") {
                return { ...entry, value: -entry.value };
            }
            return entry;
        });
    };

    return {
        year: processEntries(data.year),
        quarter: processEntries(data.quarter),
        month: processEntries(data.month),
    };
}
