<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Http\UploadedFile;

class ChatbotService
{
    protected string $baseUrl;
    
    public function __construct()
    {
        // Chatbot API URL (Python Flask)
        $this->baseUrl = config('services.chatbot.url', 'http://127.0.0.1:5000');
    }
    
    /**
     * Get health status of chatbot API
     */
    public function health(): array
    {
        try {
            $response = Http::timeout(5)->get("{$this->baseUrl}/api/health");
            return $response->json() ?? ['status' => 'error'];
        } catch (\Exception $e) {
            return ['status' => 'offline', 'error' => $e->getMessage()];
        }
    }
    
    /**
     * Get all document categories
     */
    public function getCategories(): array
    {
        try {
            $response = Http::get("{$this->baseUrl}/api/categories");
            return $response->json()['categories'] ?? [];
        } catch (\Exception $e) {
            return [];
        }
    }
    
    /**
     * Get all documents
     */
    public function getDocuments(): array
    {
        try {
            $response = Http::get("{$this->baseUrl}/api/documents");
            return $response->json()['documents'] ?? [];
        } catch (\Exception $e) {
            return [];
        }
    }
    
    /**
     * Upload and process a document
     */
    public function uploadDocument(UploadedFile $file, string $category = 'general'): array
    {
        try {
            $response = Http::timeout(120)
                ->attach('file', file_get_contents($file->getRealPath()), $file->getClientOriginalName())
                ->post("{$this->baseUrl}/api/upload", [
                    'category' => $category
                ]);
            
            return $response->json() ?? ['error' => 'Invalid response'];
        } catch (\Exception $e) {
            return ['error' => $e->getMessage()];
        }
    }
    
    /**
     * Delete a document
     */
    public function deleteDocument(string $filename): array
    {
        try {
            $response = Http::delete("{$this->baseUrl}/api/documents/{$filename}");
            return $response->json() ?? ['error' => 'Invalid response'];
        } catch (\Exception $e) {
            return ['error' => $e->getMessage()];
        }
    }
    
    /**
     * Refresh the document index
     */
    public function refreshIndex(): array
    {
        try {
            $response = Http::timeout(60)->post("{$this->baseUrl}/api/refresh");
            return $response->json() ?? ['error' => 'Invalid response'];
        } catch (\Exception $e) {
            return ['error' => $e->getMessage()];
        }
    }
    
    /**
     * Get admin statistics
     */
    public function getStats(): array
    {
        try {
            $response = Http::get("{$this->baseUrl}/api/admin/stats");
            return $response->json() ?? [];
        } catch (\Exception $e) {
            return [];
        }
    }
    
    /**
     * Sync documents from filesystem to database
     */
    public function syncDocuments(): array
    {
        try {
            $response = Http::timeout(30)->post("{$this->baseUrl}/api/sync");
            return $response->json() ?? ['error' => 'Invalid response'];
        } catch (\Exception $e) {
            return ['error' => $e->getMessage()];
        }
    }
}
