import { useQuery } from '@tanstack/react-query';
import { getApiUrl } from '../config';
import type { RefereeListResponse, RefereeProfile } from '../types/referee';

async function fetchRefereeList(sort: string, minGames: number): Promise<RefereeListResponse> {
  const res = await fetch(getApiUrl(`f5/referees?sort=${sort}&min_games=${minGames}`));
  if (!res.ok) throw new Error(`Failed to load referee list: ${res.status}`);
  return res.json();
}

async function fetchRefereeProfile(name: string): Promise<RefereeProfile> {
  const encoded = encodeURIComponent(name);
  const res = await fetch(getApiUrl(`f5/referees/${encoded}`));
  if (!res.ok) throw new Error(`No data for referee: ${name}`);
  return res.json();
}

export function useRefereeList(sort: string, minGames: number) {
  return useQuery<RefereeListResponse, Error>({
    queryKey: ['referees', sort, minGames],
    queryFn: () => fetchRefereeList(sort, minGames),
    staleTime: 5 * 60 * 1000,
  });
}

export function useRefereeProfile(name: string | null) {
  return useQuery<RefereeProfile, Error>({
    queryKey: ['referee', name],
    queryFn: () => fetchRefereeProfile(name!),
    enabled: name !== null && name.length > 0,
    staleTime: 5 * 60 * 1000,
  });
}
