import { Octokit } from '@octokit/rest';
import * as dotenv from 'dotenv';

// 加载环境变量
dotenv.config();

// 定义类型
interface RepoInfo {
    stars: number;
    forks: number;
    commits: number;
}

// 初始化 GitHub 客户端
const octokit = new Octokit({
    auth: process.env.GITHUB_TOKEN,
});

// 获取仓库信息
export async function getOverview(repoName: string): Promise<RepoInfo | null> {
    if (!repoName) {
        console.error('Repository name is required');
        return null;
    }

    try {
        // 分割仓库名（格式：owner/repo）
        const [owner, repo] = repoName.split('/');
        if (!owner || !repo) {
            console.error('Invalid repository name format. Expected "owner/repo"');
            return null;
        }

        // 获取仓库基本信息
        const { data: repoData } = await octokit.rest.repos.get({ owner, repo });

        // 获取提交总数
        const commitCount = await getCommitCount(owner, repo);

        const info: RepoInfo = {
            stars: repoData.stargazers_count,
            forks: repoData.forks_count,
            commits: commitCount,
        };

        return info;
    } catch (error) {
        console.error(`An error occurred: ${error}`);
        return null;
    }
}


async function getCommitCount(owner: string, repo: string): Promise<number> {
    let totalCommits = 0;
    let page = 1;

    try {
        while (true) {
            // 等待 100ms，防止被 GitHub 限流
            // await new Promise(resolve => setTimeout(resolve, 10));

            const { data: commits, headers } = await octokit.rest.repos.listCommits({
                owner,
                repo,
                per_page: 500,
                page,
            });

            if (commits.length === 0) break;

            totalCommits += commits.length;

            const linkHeader = headers.link;
            if (!linkHeader || !linkHeader.includes('rel="next"')) break;

            page++;
        }
    } catch (error) {
        console.error(`Failed to fetch commit count for ${owner}/${repo}:`, error);
        return 0;
    }

    return totalCommits;
}

