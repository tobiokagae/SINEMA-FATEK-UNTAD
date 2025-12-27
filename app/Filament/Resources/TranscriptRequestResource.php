<?php

namespace App\Filament\Resources;

use App\Filament\Resources\TranscriptRequestResource\Pages;
use App\Models\TranscriptRequest;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Notifications\Notification;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Actions\Action;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;

class TranscriptRequestResource extends Resource
{
    protected static ?string $model = TranscriptRequest::class;

    protected static ?string $navigationIcon = 'heroicon-o-inbox-stack';
    protected static ?string $navigationLabel = 'Permohonan Transkrip';
    protected static ?string $pluralModelLabel = 'Permohonan Transkrip';
    protected static ?int $navigationSort = 4;

    // Admin tidak bisa membuat atau mengedit permohonan, hanya memproses
    public static function form(Form $form): Form
    {
        return $form->schema([]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('created_at')
                    ->label('Tanggal Permohonan')
                    ->date()
                    ->sortable(),
                Tables\Columns\TextColumn::make('student.user.name')
                    ->label('Mahasiswa')
                    ->searchable(),
                Tables\Columns\TextColumn::make('student.nim')
                    ->label('NIM')
                    ->searchable(),
                Tables\Columns\TextColumn::make('status')
                    ->badge()
                    ->color(fn(string $state): string => match ($state) {
                        'pending' => 'warning',
                        'approved' => 'success',
                        'rejected' => 'danger',
                    }),
                // Tables\Columns\TextColumn::make('processedBy.name')
                //     ->label('Diproses oleh')
                //     ->default('-'),
            ])
            ->defaultSort('created_at', 'desc')
            ->actions([
                // Aksi untuk menyetujui permohonan
                Action::make('approve')
                    ->label('Setuju')
                    ->icon('heroicon-o-check-circle')
                    ->color('success')
                    ->visible(fn(TranscriptRequest $record): bool => $record->status === 'pending')
                    ->modalContent(fn($record) => view('filament.previews.transcript-modal', ['record' => $record]))
                    ->modalWidth('4xl') // Buat modal lebih lebar
                    // ->extraModalAttributes(['class' => 'max-h-[90vh]'])
                    ->form([
                        Forms\Components\TextInput::make('document_number')
                            ->label('Nomor Surat')
                            ->required(),
                        Forms\Components\DatePicker::make('document_date')
                            ->label('Tanggal Surat')
                            ->default(now())
                            ->required(),
                    ])
                    ->modalSubmitActionLabel('Proses Transkrip')
                    ->action(function (array $data, TranscriptRequest $record) {
                        // 1. Simpan nomor & tanggal surat
                        $record->update([
                            'status' => 'approved',
                            'processed_by' => Auth::id(),
                            'processed_at' => now(),
                            'document_number' => $data['document_number'],
                            'document_date' => $data['document_date'],
                        ]);

                        Notification::make()->title('Permohonan disetujui & transkrip telah diarsipkan.')->success()->send();

                        // 2. Buka PDF final di tab baru
                        $url = route('transcript.generate', ['student' => $record->student, 'transcriptRequest' => $record]);
                        return redirect()->to($url);
                    }),

                // Aksi untuk menolak permohonan
                Action::make('reject')
                    ->label('Tolak')
                    ->icon('heroicon-o-x-circle')
                    ->color('danger')
                    ->visible(fn(TranscriptRequest $record): bool => $record->status === 'pending')
                    ->requiresConfirmation()
                    ->form([
                        Forms\Components\Textarea::make('admin_notes')
                            ->label('Alasan Penolakan')
                            ->required(),
                    ])
                    ->action(function (array $data, TranscriptRequest $record) {
                        $record->update([
                            'status' => 'rejected',
                            'admin_notes' => $data['admin_notes'],
                            'processed_by' => Auth::id(),
                            'processed_at' => now(),
                        ]);
                        Notification::make()->title('Permohonan ditolak')->success()->send();
                    }),

                // Aksi untuk mengunduh ulang transkrip yang sudah disetujui
                Action::make('download')
                    ->label('Download Transkrip')
                    ->icon('heroicon-o-arrow-down-tray')
                    ->color('primary')
                    ->visible(fn(TranscriptRequest $record): bool => $record->status === 'approved' && !empty($record->file_path))
                    ->url(fn(TranscriptRequest $record): string => Storage::url($record->file_path))
                    ->openUrlInNewTab(),
            ]);
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListTranscriptRequests::route('/'),
        ];
    }

    // Sembunyikan menu ini dari Mahasiswa
    public static function canViewAny(): bool
    {
        return Auth::user()->role === 'Admin';
    }

    // Tampilkan badge notifikasi untuk permohonan yang pending
    public static function getNavigationBadge(): ?string
    {
        return static::getModel()::where('status', 'pending')->count();
    }
}
