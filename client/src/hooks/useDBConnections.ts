import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiService, type ConnectionListSimpleResponse, type ConnectionCreateRequest, type ConnectionRead, type FileType, type DatasetUploadResponse, type DatasourceListResponse } from '../services/api'
import { showToast } from '../utils/toast'

// Query key factory
export const dbConnectionsKeys = {
  all: ['dbConnections'] as const,
  lists: () => [...dbConnectionsKeys.all, 'list'] as const,
  list: (filters: string) => [...dbConnectionsKeys.lists(), { filters }] as const,
  details: () => [...dbConnectionsKeys.all, 'detail'] as const,
  detail: (id: string) => [...dbConnectionsKeys.details(), id] as const,
}

// Hook to get all database connections
export function useDBConnections() {
  return useQuery({
    queryKey: dbConnectionsKeys.lists(),
    queryFn: async (): Promise<ConnectionListSimpleResponse> => {
      return ApiService.listAllConnections()
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000,  // 10 minutes
  })
}

// Hook to create a database connection
export function useCreateDBConnection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (connectionData: ConnectionCreateRequest): Promise<ConnectionRead> => {
      return ApiService.createConnection(connectionData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dbConnectionsKeys.lists() })
      queryClient.invalidateQueries({ queryKey: ['all-connections'] }) // Sync with notebook creation
      queryClient.invalidateQueries({ queryKey: ['datasources'] }) // Sync unified datasources
      showToast.success('Database connection created successfully')
    },
    onError: (error: Error) => {
      showToast.error(`Failed to create connection: ${error.message}`)
    },
  })
}

// Hook to delete a database connection
export function useDeleteDBConnection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (connectionId: string): Promise<void> => {
      return ApiService.deleteConnection(connectionId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dbConnectionsKeys.lists() })
      queryClient.invalidateQueries({ queryKey: ['all-connections'] }) // Sync with notebook creation
      queryClient.invalidateQueries({ queryKey: ['datasources'] }) // Sync unified datasources
      showToast.success('Database connection deleted successfully')
    },
    onError: (error: Error) => {
      showToast.error(`Failed to delete connection: ${error.message}`)
    },
  })
}

// Hook to update a database connection
export function useUpdateDBConnection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ConnectionCreateRequest }) => {
      return ApiService.updateConnection(id, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dbConnectionsKeys.lists() })
      queryClient.invalidateQueries({ queryKey: ['all-connections'] }) // Sync with notebook creation
      queryClient.invalidateQueries({ queryKey: ['datasources'] }) // Sync unified datasources
      showToast.success('Database connection updated successfully')
    },
    onError: (error: Error) => {
      showToast.error(`Failed to update connection: ${error.message}`)
    },
  })
}

// Hook to get connection details
export function useGetConnectionDetails(connectionId: string | null) {
  return useQuery({
    queryKey: dbConnectionsKeys.detail(connectionId || ''),
    queryFn: async () => {
      if (!connectionId) return null
      return ApiService.getConnectionDetails(connectionId)
    },
    enabled: !!connectionId,
    staleTime: 0, // Always fetch fresh data when editing
  })
}

// Hook to upload multiple files (CSV/Excel/Parquet/JSON - handles both single and multiple)
// Now uploads to datasets instead of connections
export function useUploadMultipleFiles() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      files,
      name,
      fileType,
      notebookId,
      aliases
    }: {
      files: File[]
      name: string
      fileType: FileType
      notebookId?: string
      aliases?: Record<string, string>
    }): Promise<DatasetUploadResponse> => {
      return ApiService.uploadMultipleFiles(files, name, fileType, notebookId, aliases)
    },
    onSuccess: (data, variables) => {
      // Invalidate datasets for the notebook if provided
      if (variables.notebookId) {
        queryClient.invalidateQueries({ queryKey: ['datasets', variables.notebookId] })
      }
      // Invalidate unified datasources list
      queryClient.invalidateQueries({ queryKey: ['datasources'] })
      // Still invalidate connections for backward compatibility
      queryClient.invalidateQueries({ queryKey: dbConnectionsKeys.lists() })
      queryClient.invalidateQueries({ queryKey: ['all-connections'] })

      const fileTypeLabel = data.file_type?.toUpperCase() || 'file'
      const fileWord = data.files_count === 1 ? 'file' : 'files'
      showToast.success(`Successfully uploaded ${data.files_count} ${fileTypeLabel} ${fileWord}`)
    },
    onError: (error: Error) => {
      showToast.error(`Failed to upload files: ${error.message}`)
    },
  })
}

// Hook to upload files from URLs
export function useUploadFromURL() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      urls,
      name,
      fileType,
      notebookId,
      signal,
    }: {
      urls: string[]
      name: string
      fileType?: FileType
      notebookId?: string
      signal?: AbortSignal
    }): Promise<DatasetUploadResponse> => {
      return ApiService.uploadFromURL(urls, name, fileType, notebookId, signal)
    },
    onSuccess: (data, variables) => {
      // Invalidate datasets for the notebook if provided
      if (variables.notebookId) {
        queryClient.invalidateQueries({ queryKey: ['datasets', variables.notebookId] })
      }
      // Invalidate unified datasources list
      queryClient.invalidateQueries({ queryKey: ['datasources'] })
      // Still invalidate connections for backward compatibility
      queryClient.invalidateQueries({ queryKey: dbConnectionsKeys.lists() })
      queryClient.invalidateQueries({ queryKey: ['all-connections'] })

      const fileTypeLabel = data.file_type?.toUpperCase() || 'file'
      const fileWord = data.files_count === 1 ? 'file' : 'files'
      showToast.success(`Successfully downloaded ${data.files_count} ${fileTypeLabel} ${fileWord} from URL`)
    },
    onError: (error: Error) => {
      showToast.error(`Failed to upload from URL: ${error.message}`)
    },
  })
}

// Hook to get all datasources (connections + datasets)
export function useDatasources() {
  return useQuery({
    queryKey: ['datasources'],
    queryFn: async (): Promise<DatasourceListResponse> => {
      return ApiService.listAllDatasources()
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000,  // 10 minutes
  })
}