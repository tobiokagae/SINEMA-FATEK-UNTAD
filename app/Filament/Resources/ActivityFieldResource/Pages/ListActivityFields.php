<?php

namespace App\Filament\Resources\ActivityFieldResource\Pages;

use App\Filament\Resources\ActivityFieldResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListActivityFields extends ListRecords
{
    protected static string $resource = ActivityFieldResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\CreateAction::make()
                ->label('Bidang Kegiatan')
                ->icon('heroicon-o-plus')
                ->modalHeading('Tambah Bidang Kegiatan')
                ->modalSubmitActionLabel('Simpan')
                ->modalCancelActionLabel('Batal')
                ->createAnother(false)
        ];
    }

    public function getBreadcrumb(): string
    {
        return 'Daftar';
    }
}
