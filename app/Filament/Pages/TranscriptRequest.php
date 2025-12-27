<?php

namespace App\Filament\Pages;

use App\Models\ActivityType;
use App\Models\TranscriptRequest as TranscriptRequestModel;
use Filament\Actions\Action;
use Filament\Infolists\Components\TextEntry;
use Filament\Infolists\Concerns\InteractsWithInfolists;
use Filament\Infolists\Contracts\HasInfolists;
use Filament\Infolists\Infolist;
use Filament\Notifications\Notification;
use Filament\Pages\Page;
use Illuminate\Support\Facades\Auth;

class TranscriptRequest extends Page implements HasInfolists
{
    use InteractsWithInfolists;

    protected static ?string $navigationIcon = 'heroicon-o-document-check';
    protected static string $view = 'filament.pages.transcript-request';
    protected static ?string $title = 'Permohonan Transkrip';
    protected static ?string $navigationLabel = 'Permohonan Transkrip';
    protected static ?int $navigationSort = 3;

    // Properti untuk menyimpan status pemenuhan syarat
    public int $pkkmbCount = 0;
    public int $baktiLingkunganCount = 0;
    public bool $allRequirementsMet = false;
    public ?TranscriptRequestModel $latestRequest = null;

    // Sembunyikan menu ini dari Admin/Verifier
    public static function shouldRegisterNavigation(): bool
    {
        return Auth::user()->role === 'Student';
    }

    public function mount(): void
    {
        abort_if(Auth::user()->role !== 'Student', 403);
        $this->checkRequirements();
        $this->latestRequest = Auth::user()->student->transcriptRequests()->latest()->first();
    }

    /**
     * Memeriksa pemenuhan kegiatan wajib.
     */
    protected function checkRequirements(): void
    {
        $student = Auth::user()->student;

        // Hitung jumlah kegiatan PKKMB yang sudah diverifikasi
        $this->pkkmbCount = $student->submissions()
            ->where('status', 'Verified')
            ->whereHas('activityType', function ($query) {
                $query->where('required_category', ActivityType::REQUIRED_CATEGORY_PKKMB);
            })
            ->count();

        // Hitung jumlah kegiatan Bakti Lingkungan yang sudah diverifikasi
        $this->baktiLingkunganCount = $student->submissions()
            ->where('status', 'Verified')
            ->whereHas('activityType', function ($query) {
                $query->where('required_category', ActivityType::REQUIRED_CATEGORY_BAKTI_LINGKUNGAN);
            })
            ->count();

        // Cek apakah semua syarat terpenuhi
        $this->allRequirementsMet = ($this->pkkmbCount >= 1 && $this->baktiLingkunganCount >= 2);
    }

    public function requirementsInfolist(Infolist $infolist): Infolist
    {
        return $infolist
            ->state([]) // State kosong karena kita menggunakan properti dari kelas
            ->schema([
                TextEntry::make('pkkmb')
                    ->label('Mengikuti Kegiatan PKKMB')
                    ->hint("Status: {$this->pkkmbCount} dari 1 kegiatan terpenuhi.")
                    ->hintColor($this->pkkmbCount >= 1 ? 'success' : 'danger')
                    ->hintIcon($this->pkkmbCount >= 1 ? 'heroicon-s-check-circle' : 'heroicon-s-x-circle'),

                TextEntry::make('bakti_lingkungan')
                    ->label('Mengikuti Kegiatan Bakti Lingkungan')
                    ->hint("Status: {$this->baktiLingkunganCount} dari 2 kegiatan terpenuhi.")
                    ->hintColor($this->baktiLingkunganCount >= 2 ? 'success' : 'danger')
                    ->hintIcon($this->baktiLingkunganCount >= 2 ? 'heroicon-s-check-circle' : 'heroicon-s-x-circle'),
            ]);
    }

    /**
     * Mendefinisikan tombol aksi "Ajukan Permohonan".
     */
    protected function getHeaderActions(): array
    {
        $disabled = !$this->allRequirementsMet || ($this->latestRequest && $this->latestRequest->status === 'pending');
        return [
            Action::make('cancelRequest')
                ->label('Batalkan Permohonan')
                ->icon('heroicon-o-trash')
                ->color('danger')
                ->requiresConfirmation()
                ->modalHeading('Batalkan Permohonan')
                ->modalDescription('Apakah Anda yakin ingin membatalkan permohonan transkrip yang sedang diproses saat ini?')
                ->modalSubmitActionLabel('Ya, Batalkan')
                // Tombol ini hanya muncul jika ada permohonan dengan status 'pending'
                ->visible($this->latestRequest && $this->latestRequest->status === 'pending')
                ->action(function () {
                    $this->latestRequest->delete();
                    Notification::make()->title('Permohonan Dibatalkan')->success()->send();
                    $this->redirect(static::getUrl());
                }),
            Action::make('requestTranscript')
                ->label('Ajukan Permohonan Transkrip')
                ->icon('heroicon-o-paper-airplane')
                ->requiresConfirmation()
                ->modalHeading('Konfirmasi Permohonan')
                ->modalDescription('Anda akan mengajukan permohonan transkrip. Pastikan semua data kegiatan Anda sudah lengkap.')
                ->modalSubmitActionLabel('Ya, Ajukan')
                ->disabled($disabled)
                ->action(function () {
                    Auth::user()->student->transcriptRequests()->create(['status' => 'pending']);
                    Notification::make()
                        ->title('Permohonan Berhasil Diajukan')
                        ->body('Permohonan Anda akan segera diproses oleh admin.')
                        ->success()
                        ->send();
                    $this->redirect(static::getUrl());
                }),
        ];
    }

    /**
     * Logika yang berjalan saat tombol "Ajukan Permohonan" diklik.
     */
}
