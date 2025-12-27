<?php

namespace App\Filament\Resources\SignatoryResource\Pages;

use App\Filament\Resources\SignatoryResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListSignatories extends ListRecords
{
    protected static string $resource = SignatoryResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\CreateAction::make()
                ->label('Penandatangan')
                ->icon('heroicon-o-plus')
                ->modalHeading('Tambah Penandatangan')
                ->modalSubmitActionLabel('Simpan')
                ->modalCancelActionLabel('Batal')
                ->createAnother(false)
        ];
    }
}
