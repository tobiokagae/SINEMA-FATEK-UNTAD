<?php

namespace App\Filament\Resources\StudentResource\Pages;

use App\Filament\Resources\StudentResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;
use Illuminate\Database\Eloquent\Model;

class EditStudent extends EditRecord
{
    protected static string $resource = StudentResource::class;

    protected function getHeaderActions(): array
    {
        return [
            // Actions\DeleteAction::make(),
        ];
    }

    /**
     * PERBAIKAN: Mengisi data form secara manual dari relasi.
     */
    protected function mutateFormDataBeforeFill(array $data): array
    {
        // Ambil data dari relasi 'user' dan masukkan ke form
        $data['name'] = $this->record->user?->name;
        $data['email'] = $this->record->user?->email;

        return $data;
    }

    protected function handleRecordUpdate(Model $record, array $data): Model
    {
        // 1. Ekstrak data untuk tabel 'users'
        $userData = [
            'name' => $data['name'],
            'email' => $data['email'],
        ];

        // 2. Hapus data 'user' dari array utama agar tidak error
        unset($data['name']);
        unset($data['email']);

        // 3. Update tabel 'users'
        $record->user->update($userData);

        // 4. Update tabel 'students' dengan sisa data
        $record->update($data);

        return $record;
    }
}
