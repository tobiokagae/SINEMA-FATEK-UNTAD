<?php

namespace App\Filament\Widgets;

use App\Filament\Resources\SubmissionResource;
use App\Models\Submission;
use Filament\Tables;
use Filament\Tables\Table;
use Filament\Widgets\TableWidget as BaseWidget;
use Illuminate\Support\Facades\Auth;

class LatestSubmissions extends BaseWidget
{
    protected static ?int $sort = 3; // Urutan widget di dashboard
    protected int | string | array $columnSpan = 'full';

    public static function canView(): bool
    {
        return Auth::user()->role === 'Admin';
    }

    public function table(Table $table): Table
    {
        return $table
            ->query(
                // Ambil 5 pengajuan terbaru yang perlu diverifikasi
                Submission::query()
                    ->where('status', 'Submitted')
                    ->latest()
                    ->limit(5)
            )
            ->heading('Pengajuan Terbaru yang Perlu Diverifikasi')
            ->columns([
                Tables\Columns\TextColumn::make('student.user.name')
                    ->label('Mahasiswa'),
                Tables\Columns\TextColumn::make('activityType.name')
                    ->label('Nama Kegiatan')
                    ->limit(50),
                Tables\Columns\TextColumn::make('created_at')
                    ->label('Tanggal Diajukan')
                    ->since(),
            ])
            ->actions([
                Tables\Actions\Action::make('Lihat')
                    ->url(fn(Submission $record): string => SubmissionResource::getUrl('edit', ['record' => $record])),
            ])
            ->emptyStateHeading('Belum ada pengajuan');
    }
}
