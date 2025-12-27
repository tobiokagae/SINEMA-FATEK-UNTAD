<?php

namespace App\Filament\Resources\ActivityFieldResource\Pages;

use App\Filament\Resources\ActivityFieldResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditActivityField extends EditRecord
{
    protected static string $resource = ActivityFieldResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }
}
