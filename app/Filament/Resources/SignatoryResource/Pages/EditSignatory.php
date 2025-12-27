<?php

namespace App\Filament\Resources\SignatoryResource\Pages;

use App\Filament\Resources\SignatoryResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditSignatory extends EditRecord
{
    protected static string $resource = SignatoryResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }
}
