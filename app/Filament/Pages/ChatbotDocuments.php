<?php

namespace App\Filament\Pages;

use App\Services\ChatbotService;
use Filament\Actions\Action;
use Filament\Forms\Components\FileUpload;
use Filament\Forms\Components\Select;
use Filament\Forms\Concerns\InteractsWithForms;
use Filament\Forms\Contracts\HasForms;
use Filament\Forms\Form;
use Filament\Notifications\Notification;
use Filament\Pages\Page;
use Illuminate\Support\Facades\Log;

class ChatbotDocuments extends Page implements HasForms
{
    use InteractsWithForms;
    
    protected static ?string $navigationIcon = 'heroicon-o-document-text';
    protected static ?string $navigationLabel = 'Dokumen Chatbot';
    protected static ?string $navigationGroup = 'Chatbot';
    protected static ?int $navigationSort = -5;
    protected static string $view = 'filament.pages.chatbot-documents';
    
    public ?array $uploadData = [];
    public array $documents = [];
    public array $categories = [];
    public array $stats = [];
    
    protected ChatbotService $chatbotService;
    
    public function boot(ChatbotService $chatbotService): void
    {
        $this->chatbotService = $chatbotService;
    }
    
    public function mount(): void
    {
        $this->loadData();
    }
    
    protected function loadData(): void
    {
        $this->chatbotService = app(ChatbotService::class);
        $this->documents = $this->chatbotService->getDocuments();
        $this->categories = $this->chatbotService->getCategories();
        $this->stats = $this->chatbotService->getStats();
    }
    
    public function form(Form $form): Form
    {
        $categoryOptions = collect($this->categories)->pluck('display_name', 'name')->toArray();
        
        return $form
            ->schema([
                FileUpload::make('file')
                    ->label('Pilih Dokumen')
                    ->acceptedFileTypes([
                        'application/pdf',
                        'text/plain',
                        'text/markdown',
                        '.md',
                        'application/msword',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    ])
                    ->maxSize(10240)
                    ->required(),
                    
                Select::make('category')
                    ->label('Kategori')
                    ->options($categoryOptions ?: ['general' => 'Umum'])
                    ->default('general')
                    ->required(),
            ])
            ->statePath('uploadData');
    }
    
    public function upload(): void
    {
        $data = $this->form->getState();
        
        Log::info('Upload data: ' . json_encode($data));
        
        if (empty($data['file'])) {
            Notification::make()
                ->title('Pilih file terlebih dahulu')
                ->warning()
                ->send();
            return;
        }
        
        // The file value from Filament FileUpload
        $fileValue = $data['file'];
        Log::info('File value type: ' . gettype($fileValue));
        Log::info('File value: ' . (is_string($fileValue) ? $fileValue : json_encode($fileValue)));
        
        // Find the actual file path
        $tempPath = null;
        $originalName = null;
        
        // Check all possible locations
        $searchPaths = [
            storage_path('app/private/livewire-tmp'),
            storage_path('app/livewire-tmp'),
            storage_path('app/public'),
        ];
        
        foreach ($searchPaths as $searchDir) {
            if (!is_dir($searchDir)) continue;
            
            $files = glob($searchDir . '/*');
            foreach ($files as $file) {
                $basename = basename($file);
                // Match if fileValue is contained in basename or vice versa
                if (strpos($basename, $fileValue) !== false || strpos($fileValue, $basename) !== false || $basename === $fileValue) {
                    $tempPath = $file;
                    break 2;
                }
            }
        }
        
        // If still not found, try direct path
        if (!$tempPath) {
            $directPaths = [
                storage_path('app/private/livewire-tmp/' . $fileValue),
                storage_path('app/livewire-tmp/' . $fileValue),
                storage_path('app/' . $fileValue),
            ];
            
            foreach ($directPaths as $path) {
                if (file_exists($path)) {
                    $tempPath = $path;
                    break;
                }
            }
        }
        
        Log::info('Temp path found: ' . ($tempPath ?? 'NOT FOUND'));
        
        if (!$tempPath || !file_exists($tempPath)) {
            Notification::make()
                ->title('File tidak ditemukan')
                ->body('File: ' . $fileValue)
                ->danger()
                ->send();
            return;
        }
        
        // Extract original name from Livewire metadata in filename
        $basename = basename($tempPath);
        if (preg_match('/-meta(.+)-\./', $basename, $matches)) {
            $decoded = base64_decode($matches[1]);
            if ($decoded) {
                $originalName = $decoded;
            }
        }
        
        if (!$originalName) {
            $originalName = $basename;
        }
        
        Log::info('Original name: ' . $originalName);
        
        // Create safe filename
        $extension = pathinfo($originalName, PATHINFO_EXTENSION);
        $safeName = preg_replace('/[^a-zA-Z0-9_.-]/', '_', pathinfo($originalName, PATHINFO_FILENAME));
        $finalName = $safeName . '.' . $extension;
        
        // Ensure storage directory exists
        $storageDir = storage_path('app/chatbot-documents');
        if (!is_dir($storageDir)) {
            mkdir($storageDir, 0755, true);
        }
        
        $storagePath = $storageDir . '/' . $finalName;
        
        // Copy file
        if (!copy($tempPath, $storagePath)) {
            Notification::make()
                ->title('Gagal menyimpan file')
                ->danger()
                ->send();
            return;
        }
        
        Log::info('File saved to: ' . $storagePath);
        
        Notification::make()
            ->title('File tersimpan, mengirim ke chatbot API...')
            ->info()
            ->send();
        
        // Send to chatbot API
        $file = new \Illuminate\Http\UploadedFile(
            $storagePath,
            $finalName,
            null,
            null,
            true
        );
        
        $category = $data['category'] ?? 'general';
        $result = $this->chatbotService->uploadDocument($file, $category);
        
        Log::info('API result: ' . json_encode($result));
        
        if (isset($result['error'])) {
            Notification::make()
                ->title('Gagal mengupload ke chatbot API')
                ->body($result['error'])
                ->danger()
                ->send();
        } else {
            Notification::make()
                ->title('Dokumen berhasil diproses!')
                ->body("File: {$finalName} | Chunks: " . ($result['chunks'] ?? 0))
                ->success()
                ->send();
            
            $this->reset('uploadData');
            $this->loadData();
        }
    }
    
    public function deleteDocument(string $filename): void
    {
        $result = $this->chatbotService->deleteDocument($filename);
        
        $localPath = storage_path('app/chatbot-documents/' . $filename);
        if (file_exists($localPath)) {
            unlink($localPath);
        }
        
        if (isset($result['error'])) {
            Notification::make()
                ->title('Gagal menghapus')
                ->body($result['error'])
                ->danger()
                ->send();
        } else {
            Notification::make()
                ->title('Dokumen dihapus')
                ->success()
                ->send();
            
            $this->loadData();
        }
    }
    
    public function refreshIndex(): void
    {
        Notification::make()
            ->title('Memperbarui index...')
            ->info()
            ->send();
        
        $result = $this->chatbotService->refreshIndex();
        
        if (isset($result['error'])) {
            Notification::make()
                ->title('Gagal refresh')
                ->body($result['error'])
                ->danger()
                ->send();
        } else {
            Notification::make()
                ->title('Index berhasil diperbarui!')
                ->success()
                ->send();
            
            $this->loadData();
        }
    }
    
    protected function getHeaderActions(): array
    {
        return [
            Action::make('refresh')
                ->label('Refresh Index')
                ->icon('heroicon-o-arrow-path')
                ->action('refreshIndex')
                ->color('warning'),
        ];
    }
}
