<?php

namespace App\Filament\Resources\TranscriptRequestResource\Pages;

use App\Filament\Resources\TranscriptRequestResource;
use Filament\Actions;
use Filament\Resources\Components\Tab;
use Filament\Resources\Pages\ListRecords;
use Illuminate\Database\Eloquent\Builder;

class ListTranscriptRequests extends ListRecords
{
    protected static string $resource = TranscriptRequestResource::class;

    // Admin tidak bisa membuat permohonan
    protected function getHeaderActions(): array
    {
        return [];
    }

    public function getTabs(): array
    {
        return [
            'all' => Tab::make('Semua')
                ->badgeColor('info')
                ->badge(static::getResource()::getModel()::count()),
            'pending' => Tab::make('Menunggu Persetujuan')
                ->badge(static::getResource()::getModel()::where('status', 'pending')->count())
                ->badgeColor('warning')
                ->modifyQueryUsing(fn(Builder $query) => $query->where('status', 'pending')),
            'approved' => Tab::make('Disetujui')
                ->badge(static::getResource()::getModel()::where('status', 'approved')->count())
                ->badgeColor('success')
                ->modifyQueryUsing(fn(Builder $query) => $query->where('status', 'approved')),
            'rejected' => Tab::make('Ditolak')
                ->badge(static::getResource()::getModel()::where('status', 'rejected')->count())
                ->badgeColor('danger')
                ->modifyQueryUsing(fn(Builder $query) => $query->where('status', 'rejected')),
        ];
    }

    public function getDefaultActiveTab(): string|int|null
    {
        return 'pending';
    }
}
