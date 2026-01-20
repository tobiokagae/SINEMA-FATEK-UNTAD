<?php

namespace App\Filament\Pages;

use App\Services\ChatbotService;
use Filament\Actions\Action;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Forms\Components\FileUpload;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Concerns\InteractsWithForms;
use Filament\Forms\Contracts\HasForms;
use Filament\Forms\Form;
use Filament\Notifications\Notification;
use Filament\Pages\Page;
use Illuminate\Support\Facades\Log;

class ChatbotDocuments extends Page implements HasForms, HasActions
{
    use InteractsWithForms;
    use InteractsWithActions;
    
    protected static ?string $navigationIcon = 'heroicon-o-document-text';
    protected static ?string $navigationLabel = 'Dokumen Chatbot';
    protected static ?string $navigationGroup = 'Chatbot';
    protected static ?int $navigationSort = -5;
    protected static string $view = 'filament.pages.chatbot-documents';
    
    public ?array $data = [];
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
        $this->form->fill();
    }
    
    protected function loadData(): void
    {
        $this->chatbotService = app(ChatbotService::class);
        $this->documents = $this->chatbotService->getDocuments();
        $this->categories = $this->chatbotService->getCategories();
        $this->stats = $this->chatbotService->getStats();
        
        \Log::info('ChatbotDocuments loadData: ' . count($this->documents) . ' documents loaded');
    }
    
    public function form(Form $form): Form
    {
        if (empty($this->categories)) {
            $this->categories = app(ChatbotService::class)->getCategories();
        }
        
        $categoryOptions = collect($this->categories)->pluck('display_name', 'name')->toArray();
        
        return $form
            ->schema([
                FileUpload::make('file')
                    ->label('Pilih Dokumen')
                    ->disk('local')
                    ->directory('chatbot-uploads')
                    ->visibility('private')
                    ->preserveFilenames()
                    ->acceptedFileTypes([
                        '.pdf', '.doc', '.docx', '.txt', '.md',
                        'application/pdf',
                        'application/msword',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'text/plain', 'text/markdown', 'text/x-markdown',
                    ])
                    ->maxSize(10240)
                    ->required()
                    ->live()
                    ->validationMessages([
                        'required' => 'File dokumen harus diupload',
                    ]),
                    
                Select::make('category')
                    ->label('Kategori')
                    ->placeholder('-- Pilih Kategori --')
                    ->options($categoryOptions ?: ['general' => 'Umum'])
                    ->required()
                    ->live()
                    ->searchable()
                    ->createOptionForm([
                        TextInput::make('display_name')
                            ->label('Nama Kategori Baru')
                            ->placeholder('Contoh: Panduan Akademik')
                            ->required()
                            ->maxLength(100),
                    ])
                    ->createOptionUsing(function (array $data) {
                        $displayName = $data['display_name'];
                        $name = \Str::slug($displayName, '_');
                        
                        $result = app(ChatbotService::class)->createCategory($name, $displayName, '📁');
                        
                        if (isset($result['error'])) {
                            Notification::make()
                                ->title('Gagal menambah kategori')
                                ->body($result['error'])
                                ->danger()
                                ->send();
                            return null;
                        }
                        
                        $this->categories = app(ChatbotService::class)->getCategories();
                        
                        Notification::make()
                            ->title('Kategori berhasil ditambahkan!')
                            ->success()
                            ->send();
                            
                        return $name;
                    })
                    ->validationMessages([
                        'required' => 'Kategori harus dipilih',
                    ]),
            ])
            ->statePath('data');
    }
    
    public function uploadAction(): Action
    {
        return Action::make('upload')
            ->label('Upload & Proses')
            ->icon('heroicon-o-cloud-arrow-up')
            ->color('warning')
            ->size('lg')
            ->extraAttributes(['class' => 'w-full justify-center'])
            ->disabled(fn () => empty($this->data['file']) || empty($this->data['category']))
            ->action(function () {
                $this->processUpload();
            });
    }
    
    public function clearCacheAction(): Action
    {
        return Action::make('clearCache')
            ->label('Clear Cache')
            ->icon('heroicon-o-trash')
            ->color('gray')
            ->requiresConfirmation()
            ->modalHeading('Hapus Semua Cache?')
            ->modalDescription('Ini akan menghapus semua cache respons chatbot. Pertanyaan berikutnya akan diproses ulang dari awal.')
            ->modalSubmitActionLabel('Ya, Hapus Cache')
            ->action(function () {
                $this->clearCache();
            });
    }
    
    public function clearCache(): void
    {
        try {
            $response = $this->chatbotService->clearCache();
            
            Notification::make()
                ->title('Cache berhasil dihapus')
                ->body("Deleted: {$response['deleted_count']} entries")
                ->success()
                ->send();
                
        } catch (\Exception $e) {
            Notification::make()
                ->title('Gagal menghapus cache')
                ->body($e->getMessage())
                ->danger()
                ->send();
        }
    }
    
    public function processUpload(): void
    {
        Log::info('=== processUpload called ===');
        
        $data = $this->form->getState();
        
        Log::info('Form data: ' . json_encode($data));
        
        if (empty($data['file'])) {
            Notification::make()
                ->title('Pilih file terlebih dahulu')
                ->warning()
                ->send();
            return;
        }
        
        // FileUpload with disk('local') stores in private/ folder
        $filePath = storage_path('app/private/' . $data['file']);
        
        Log::info('File path: ' . $filePath);
        
        if (!file_exists($filePath)) {
            Notification::make()
                ->title('File tidak ditemukan')
                ->body($filePath)
                ->danger()
                ->send();
            return;
        }
        
        $filename = basename($filePath);
        
        Notification::make()
            ->title('Memproses dokumen...')
            ->info()
            ->send();
        
        $file = new \Illuminate\Http\UploadedFile(
            $filePath,
            $filename,
            null,
            null,
            true
        );
        
        $category = $data['category'] ?? 'general';
        $result = $this->chatbotService->uploadDocument($file, $category);
        
        Log::info('API result: ' . json_encode($result));
        
        if (isset($result['error'])) {
            Notification::make()
                ->title('Gagal upload ke chatbot')
                ->body($result['error'])
                ->danger()
                ->send();
        } else {
            Notification::make()
                ->title('Dokumen berhasil diproses!')
                ->body("File: {$filename} | Chunks: " . ($result['chunks'] ?? 0))
                ->success()
                ->send();
            
            $this->form->fill();
            $this->loadData();
        }
    }
    
    public function deleteDocument(string $filename): void
    {
        $result = $this->chatbotService->deleteDocument($filename);
        
        if (isset($result['error'])) {
            Notification::make()
                ->title('Gagal menghapus')
                ->body($result['error'])
                ->danger()
                ->send();
        } else {
            Notification::make()
                ->title('Dokumen dihapus')
                ->body('Semua file dan data terkait telah dihapus.')
                ->success()
                ->send();
        }
        
        // Reload data to refresh the list immediately
        $this->documents = [];
        $this->stats = [];
        $this->loadData();
    }
    
    public function getDocumentUrl(string $filename): string
    {
        // Try PDF first, then DOCX, then DOC (replace .md extension)
        $baseName = preg_replace('/\\.md$/', '', $filename);
        $chatbotUrl = config('services.chatbot.url', 'http://127.0.0.1:5000');
        // Default to PDF - Flask will handle if file doesn't exist
        return $chatbotUrl . '/api/documents/' . urlencode($baseName . '.pdf') . '/download';
    }
    
    public function getPreviewUrl(string $filename): string
    {
        // Preview MD file (readable text)
        $chatbotUrl = config('services.chatbot.url', 'http://127.0.0.1:5000');
        return $chatbotUrl . '/api/documents/' . urlencode($filename) . '/preview';
    }
    
    public function getMdDownloadUrl(string $filename): string
    {
        // Download MD file with proper headers
        $chatbotUrl = config('services.chatbot.url', 'http://127.0.0.1:5000');
        return $chatbotUrl . '/api/documents/' . urlencode($filename) . '/download';
    }
    
    public function getOriginalUrl(string $filename): string
    {
        // Get original file URL (check for PDF, DOCX, DOC, TXT)
        $baseName = preg_replace('/\\.md$/', '', $filename);
        $chatbotUrl = config('services.chatbot.url', 'http://127.0.0.1:5000');
        return $chatbotUrl . '/api/documents/' . urlencode($baseName) . '/original';
    }
    
    public function getPdfPreviewUrl(string $filename): string
    {
        // Preview original file (PDF or DOCX)
        $baseName = preg_replace('/\\.md$/', '', $filename);
        $chatbotUrl = config('services.chatbot.url', 'http://127.0.0.1:5000');
        return $chatbotUrl . '/api/documents/' . urlencode($baseName . '.pdf') . '/preview';
    }
    
    public function refreshIndex(): void
    {
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
            Action::make('clearCache')
                ->label('Clear Cache')
                ->icon('heroicon-o-trash')
                ->color('gray')
                ->requiresConfirmation()
                ->modalHeading('Hapus Semua Cache?')
                ->modalDescription('Ini akan menghapus semua cache respons chatbot.')
                ->modalSubmitActionLabel('Ya, Hapus Cache')
                ->closeModalByClickingAway(false)
                ->action(function () {
                    try {
                        $result = $this->chatbotService->clearCache();
                        $this->loadData(); // Refresh stats immediately
                        Notification::make()
                            ->title('Cache berhasil dihapus')
                            ->success()
                            ->send();
                    } catch (\Exception $e) {
                        Notification::make()
                            ->title('Gagal menghapus cache')
                            ->body($e->getMessage())
                            ->danger()
                            ->send();
                    }
                }),
            Action::make('refresh')
                ->label('Refresh Index')
                ->icon('heroicon-o-arrow-path')
                ->color('warning')
                ->requiresConfirmation()
                ->modalHeading('Refresh Index Dokumen?')
                ->modalDescription('Ini akan memproses ulang semua dokumen dan membangun kembali vector store. Proses ini bisa memakan waktu beberapa menit.')
                ->modalSubmitActionLabel('Ya, Refresh Index')
                ->closeModalByClickingAway(false)
                ->action(function () {
                    $this->refreshIndex();
                }),
        ];
    }
}
