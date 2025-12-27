<?php

namespace App\Filament\Resources\SubmissionResource\Pages;

use App\Filament\Resources\SubmissionResource;
use Filament\Actions;
use Filament\Resources\Components\Tab;
use Illuminate\Database\Eloquent\Builder;
use Filament\Resources\Pages\ListRecords;
use Filament\Support\Colors\Color;
use Illuminate\Support\Facades\Auth;

class ListSubmissions extends ListRecords
{
    protected static string $resource = SubmissionResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\CreateAction::make()
                ->label('Pengajuan')
                ->icon('heroicon-o-plus')
                ->modalHeading('Tambah Pengajuan')
                ->modalSubmitActionLabel('Simpan')
                ->modalCancelActionLabel('Batal')
                ->createAnother(false)
        ];
    }

    public function getBreadcrumb(): string
    {
        return 'Daftar';
    }

    public function getTabs(): array
    {
        // Kueri dasar yang akan digunakan oleh semua tab
        $baseQuery = SubmissionResource::getEloquentQuery();

        // Khusus untuk mahasiswa, pastikan kueri sudah terfilter
        if (Auth::user()->role === 'Student') {
            $baseQuery->where('student_id', Auth::user()->student->id);
        }

        return [
            'all' => Tab::make('Semua')
                // ->icon('heroicon-o-list-bullet')
                ->badgeColor('info')
                ->badge($baseQuery->clone()->count()),

            'submitted' => Tab::make('Menunggu Persetujuan')
                // ->icon('heroicon-o-clock')
                ->badge($baseQuery->clone()->where('status', 'Submitted')->count())
                ->badgeColor('warning')
                ->modifyQueryUsing(fn(Builder $query) => $query->where('status', 'Submitted')),

            'verified' => Tab::make('Disetujui')
                // ->icon('heroicon-o-check-circle')
                ->badge($baseQuery->clone()->where('status', 'Verified')->count())
                ->badgeColor('success')
                ->modifyQueryUsing(fn(Builder $query) => $query->where('status', 'Verified')),

            'rejected' => Tab::make('Ditolak')
                // ->icon('heroicon-o-x-circle')
                ->badge($baseQuery->clone()->where('status', 'Rejected')->count())
                ->badgeColor('danger')
                ->modifyQueryUsing(fn(Builder $query) => $query->where('status', 'Rejected')),
        ];
    }

    public function getDefaultActiveTab(): string|int|null
    {
        // contoh: kalau Student buka langsung ke "submitted",
        // kalau Admin/Verifier buka default ke "all"
        return Auth::user()->role === 'Admin' ? 'submitted' : 'all';
    }
}
