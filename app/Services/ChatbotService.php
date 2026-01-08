<?php

namespace App\Services;

use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;

class ChatbotService
{
    protected string $baseUrl;
    
    public function __construct()
    {
        $this->baseUrl = config('services.chatbot.url', 'http://127.0.0.1:5000');
    }
    
    public function getDocuments(): array
    {
        try {
            $response = Http::get("{$this->baseUrl}/api/documents");
            if ($response->successful()) {
                return $response->json()['documents'] ?? [];
            }
        } catch (\Exception $e) {
            \Log::error('ChatbotService::getDocuments error: ' . $e->getMessage());
        }
        return [];
    }
    
    public function getCategories(): array
    {
        try {
            $response = Http::get("{$this->baseUrl}/api/categories");
            if ($response->successful()) {
                return $response->json()['categories'] ?? [];
            }
        } catch (\Exception $e) {
            \Log::error('ChatbotService::getCategories error: ' . $e->getMessage());
        }
        return [];
    }
    
    public function getStats(): array
    {
        try {
            $response = Http::get("{$this->baseUrl}/api/admin/stats");
            if ($response->successful()) {
                return $response->json() ?? [];
            }
        } catch (\Exception $e) {
            \Log::error('ChatbotService::getStats error: ' . $e->getMessage());
        }
        return [];
    }
    
    public function uploadDocument(UploadedFile $file, string $category = 'general'): array
    {
        try {
            $response = Http::attach(
                'file',
                file_get_contents($file->getRealPath()),
                $file->getClientOriginalName()
            )->post("{$this->baseUrl}/api/upload", [
                'category' => $category,
            ]);
            
            return $response->json() ?? ['error' => 'Empty response'];
        } catch (\Exception $e) {
            \Log::error('ChatbotService::uploadDocument error: ' . $e->getMessage());
            return ['error' => $e->getMessage()];
        }
    }
    
    public function deleteDocument(string $filename): array
    {
        try {
            // 1. Delete from Laravel storage (backup files) using native PHP
            $baseName = pathinfo($filename, PATHINFO_FILENAME);
            $normalizedName = strtolower(str_replace(['_', ' '], '', $baseName));
            
            $storagePath = storage_path('app/private/chatbot-uploads');
            
            // Scan all files in storage directory and delete matching ones
            if (is_dir($storagePath)) {
                $files = glob($storagePath . '/*');
                foreach ($files as $file) {
                    if (is_file($file)) {
                        $fileBaseName = pathinfo($file, PATHINFO_FILENAME);
                        $fileNormalized = strtolower(str_replace(['_', ' '], '', $fileBaseName));
                        
                        if ($fileNormalized === $normalizedName) {
                            if (unlink($file)) {
                                \Log::info("Deleted from Laravel storage: {$file}");
                            } else {
                                \Log::warning("Failed to delete: {$file}");
                            }
                        }
                    }
                }
            }
            
            // 2. Call Flask API to delete from chatbot folder, database, and refresh index
            $response = Http::timeout(120)->delete("{$this->baseUrl}/api/documents/{$filename}");
            return $response->json() ?? ['error' => 'Empty response'];
        } catch (\Exception $e) {
            \Log::error('ChatbotService::deleteDocument error: ' . $e->getMessage());
            return ['error' => $e->getMessage()];
        }
    }
    
    public function refreshIndex(): array
    {
        try {
            $response = Http::timeout(300)->post("{$this->baseUrl}/api/refresh");
            return $response->json() ?? ['error' => 'Empty response'];
        } catch (\Exception $e) {
            \Log::error('ChatbotService::refreshIndex error: ' . $e->getMessage());
            return ['error' => $e->getMessage()];
        }
    }
    
    public function createCategory(string $name, string $displayName, string $icon = '📁'): array
    {
        try {
            $response = Http::post("{$this->baseUrl}/api/categories", [
                'name' => $name,
                'display_name' => $displayName,
                'icon' => $icon,
            ]);
            return $response->json() ?? ['error' => 'Empty response'];
        } catch (\Exception $e) {
            \Log::error('ChatbotService::createCategory error: ' . $e->getMessage());
            return ['error' => $e->getMessage()];
        }
    }
    
    public function clearCache(): array
    {
        try {
            $response = Http::post("{$this->baseUrl}/api/cache/clear");
            if ($response->successful()) {
                return $response->json() ?? ['deleted_count' => 0];
            }
            return ['error' => 'Failed to clear cache'];
        } catch (\Exception $e) {
            \Log::error('ChatbotService::clearCache error: ' . $e->getMessage());
            throw $e;
        }
    }
}
