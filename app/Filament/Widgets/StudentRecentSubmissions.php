<?php

namespace App\Filament\Widgets;

use App\Filament\Resources\SubmissionResource;
use App\Models\Submission;
use Filament\Tables;
use Filament\Tables\Table;
use Filament\Widgets\TableWidget as BaseWidget;
use Illuminate\Support\Facades\Auth;

class StudentRecentSubmissions extends BaseWidget
{
    protected static ?int $sort = 2;
    protected int | string | array $columnSpan = 'full';

    public static function canView(): bool
    {
        return Auth::user()->role === 'Student';
    }

    public function table(Table $table): Table
    {
        return $table
            ->query(
                // Ambil 5 pengajuan terbaru HANYA milik mahasiswa yang sedang login
                Submission::query()
                    ->where('student_id', Auth::user()->student->id)
                    ->latest()
                    ->limit(5)
            )
            ->heading('5 Pengajuan Terakhir Anda')
            ->columns([
                Tables\Columns\TextColumn::make('activityType.name')
                    ->label('Nama Kegiatan')
                    ->limit(100)
                    ->wrap(),
                Tables\Columns\TextColumn::make('activityType.score')
                    ->label('Poin'),
                Tables\Columns\TextColumn::make('status')
                    ->badge()
                    ->color(fn(string $state): string => match ($state) {
                        'Submitted' => 'warning',
                        'Verified' => 'success',
                        'Rejected' => 'danger',
                    }),
                Tables\Columns\TextColumn::make('created_at')
                    ->label('Tanggal Diajukan')
                    ->since(),
            ])
            ->actions([
                // Tables\Actions\Action::make('Lihat')
                //     ->url(fn(Submission $record): string => SubmissionResource::getUrl('edit', ['record' => $record])),
            ])
            ->emptyStateHeading('Anda belum memiliki pengajuan')
            ->emptyStateDescription('Ayo buat pengajuan kegiatan pertama Anda!');
    }
}
