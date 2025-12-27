<?php

namespace App\Filament\Resources\TranscriptRequestResource\Pages;

use App\Filament\Resources\TranscriptRequestResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditTranscriptRequest extends EditRecord
{
    protected static string $resource = TranscriptRequestResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }
}
