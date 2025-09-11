
import {getIssueData} from './issue';
import {getIssueResolutionDuration} from './issue';
import {getContributorData} from './contributor';
import {getCodeFrequency, getPRData} from './pr';
import {getActivityData} from './activity';
import {getActiveDatesAndTimes} from './activity';
import {getOverview} from './overview';

import { useQuery } from '@tanstack/react-query';
export function useIssueStatistics(repoName: string) {
  return useQuery({
    queryKey: [`insight.issue.statistics`, repoName],
    queryFn: async () => getIssueData(repoName),
    enabled: !!repoName,
  });
}

export function useContributorStatistics(repoName: string) {
  return useQuery({
    queryKey: [`insight.contributor.statistics`, repoName],
    queryFn: async () => getContributorData(repoName),
    enabled: !!repoName,
  });
}

export function useIssueResolutionDuration(repoName: string) {
  return useQuery({
    queryKey: [`insight.issue.resolution_duration`, repoName],
    queryFn: async () => getIssueResolutionDuration(repoName),
    enabled: !!repoName,
  });
}

export function usePrStatistics(repoName: string) {
  return useQuery({
    queryKey: [`insight.pr.statistics`, repoName],
    queryFn: async () => getPRData(repoName),
    enabled: !!repoName,
  });
}

export function useCodeFrequency(repoName: string) {
  return useQuery({
    queryKey: [`insight.pr.code_frequency`, repoName],
    queryFn: async () => getCodeFrequency(repoName),
    enabled: !!repoName,
  });
}

export function useActivityStatistics(repoName: string) {
  return useQuery({
    queryKey: [`insight.activity.statistics`, repoName],
    queryFn: async () => getActivityData(repoName),
    enabled: !!repoName,
  });
}

export function useActivityDatesAndTimes(repoName: string) {
  return useQuery({
    queryKey: [`insight.activity.dates_and_times`, repoName],
    queryFn: async () => getActiveDatesAndTimes(repoName),
    enabled: !!repoName,
  });
}

export function useOverview(repoName: string) {
  return useQuery({
    queryKey: [`insight.overview`, repoName],
    queryFn: async () => getOverview(repoName),
    enabled: !!repoName,
    retry: false,
  });
}
