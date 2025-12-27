<?php

namespace App\Filament\Resources\ActivityTypeResource\Pages;

use App\Filament\Resources\ActivityTypeResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListActivityTypes extends ListRecords
{
    protected static string $resource = ActivityTypeResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\CreateAction::make()
                ->label('Rubrik Kegiatan')
                ->icon('heroicon-o-plus')
                ->modalHeading('Tambah Rubrik Kegiatan')
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
