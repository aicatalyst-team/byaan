import type { StateCreator } from 'zustand'
import type { StoreState } from '../useStore'
import type { ConnectedRepo } from '../../services/github'

export interface GitHubSlice {
  githubConnected: boolean
  githubUsername: string | null
  connectedRepos: ConnectedRepo[]
  selectedRepo: ConnectedRepo | null

  setGitHubConnected: (connected: boolean, username?: string | null) => void
  setConnectedRepos: (repos: ConnectedRepo[]) => void
  addConnectedRepo: (repo: ConnectedRepo) => void
  updateRepoStatus: (repoId: string, status: string, error?: string | null) => void
  removeConnectedRepo: (repoId: string) => void
  setSelectedRepo: (repo: ConnectedRepo | null) => void
}

export const createGitHubSlice: StateCreator<
  StoreState,
  [],
  [],
  GitHubSlice
> = (set) => ({
  githubConnected: false,
  githubUsername: null,
  connectedRepos: [],
  selectedRepo: null,

  setGitHubConnected: (connected, username = null) =>
    set(() => ({
      githubConnected: connected,
      githubUsername: username,
    })),

  setConnectedRepos: (repos) =>
    set(() => ({
      connectedRepos: repos,
    })),

  addConnectedRepo: (repo) =>
    set((state) => ({
      connectedRepos: [...state.connectedRepos, repo],
    })),

  updateRepoStatus: (repoId, status, error = null) =>
    set((state) => ({
      connectedRepos: state.connectedRepos.map((r) =>
        r.id === repoId ? { ...r, analysis_status: status, analysis_error: error } : r
      ),
    })),

  removeConnectedRepo: (repoId) =>
    set((state) => ({
      connectedRepos: state.connectedRepos.filter((r) => r.id !== repoId),
      selectedRepo: state.selectedRepo?.id === repoId ? null : state.selectedRepo,
    })),

  setSelectedRepo: (repo) =>
    set(() => ({
      selectedRepo: repo,
    })),
})
