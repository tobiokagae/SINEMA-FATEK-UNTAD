<?php

namespace App\Filament\Resources\SubmissionResource\Pages;

use App\Filament\Resources\SubmissionResource;
use App\Models\ActivityType;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Auth;

class EditSubmission extends EditRecord
{
    protected static string $resource = SubmissionResource::class;

    /**
     * Metode ini berjalan saat halaman dimuat.
     * Kita akan menempatkan logika otorisasi di sini.
     */
    public function mount(int | string $record): void
    {
        // Jalankan proses mount bawaan Filament terlebih dahulu
        parent::mount($record);

        // PERBAIKAN UTAMA: Cek otorisasi di sini
        $canAccess = false;

        // Izinkan akses jika pengguna BUKAN mahasiswa (misal: Admin/Verifier)
        if (Auth::user()->role !== 'Student') {
            $canAccess = true;
        }
        // Jika pengguna adalah mahasiswa, izinkan akses HANYA jika statusnya 'Submitted'
        elseif ($this->record->status === 'Submitted') {
            $canAccess = true;
        }

        // Jika tidak diizinkan, hentikan proses dan tampilkan halaman 403 Forbidden
        if (!$canAccess) {
            abort(403);
        }
    }

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }

    protected function mutateFormDataBeforeFill(array $data): array
    {
        $activityType = ActivityType::find($data['activity_type_id']);

        if ($activityType) {
            $data['activity_field_id'] = $activityType->activity_field_id;
            $data['activity_name'] = $activityType->name;
            $data['activity_level'] = $activityType->level;
        }

        return $data;
    }

    protected function handleRecordUpdate(Model $record, array $data): Model
    {
        unset($data['activity_field_id']);
        unset($data['activity_name']);
        unset($data['activity_level']);

        $record->update($data);

        return $record;
    }
}
