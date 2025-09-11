import { defineStore } from 'pinia'
import axios from 'axios'

const api = axios.create({
  baseURL: '/api'
})

export const useRagStore = defineStore('rag', {
  state: () => ({
    documents: [],
    queryHistory: [],
    currentQuery: '',
    currentResponse: '',
    currentSources: [],
    loading: false,
    uploading: false
  }),
  
  actions: {
    async uploadDocument(file) {
      this.uploading = true
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        const response = await api.post('/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        await this.fetchDocuments()
        return response.data
      } catch (error) {
        console.error('Upload failed:', error)
        throw error
      } finally {
        this.uploading = false
      }
    },
    
    async fetchDocuments() {
      try {
        const response = await api.get('/documents')
        this.documents = response.data
      } catch (error) {
        console.error('Failed to fetch documents:', error)
      }
    },
    
    async queryDocuments(query) {
      this.loading = true
      this.currentQuery = query
      try {
        const response = await api.post('/query', { query })
        this.currentResponse = response.data.response
        this.currentSources = response.data.sources
        
        await this.fetchQueryHistory()
        return response.data
      } catch (error) {
        console.error('Query failed:', error)
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async fetchQueryHistory() {
      try {
        const response = await api.get('/history')
        this.queryHistory = response.data
      } catch (error) {
        console.error('Failed to fetch query history:', error)
      }
    }
  }
})