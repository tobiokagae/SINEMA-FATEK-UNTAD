<?php

namespace App\Filament\Resources\StudentResource\Pages;

use App\Filament\Resources\StudentResource;
use Filament\Actions;
use Filament\Infolists\Components\Section;
use Filament\Infolists\Components\TextEntry;
use Filament\Infolists\Infolist;
use Filament\Resources\Pages\ViewRecord;

class ViewStudent extends ViewRecord
{
    protected static string $resource = StudentResource::class;

    // Definisikan apa yang akan ditampilkan di halaman View
    public function infolist(Infolist $infolist): Infolist
    {
        return $infolist
            ->schema([
                Section::make('Informasi Akun')
                    ->schema([
                        TextEntry::make('user.name')->label('Nama Mahasiswa'),
                        TextEntry::make('user.email')->label('Email'),
                    ])->columns(2),

                Section::make('Informasi Akademik')
                    ->schema([
                        TextEntry::make('nim')->label('NIM'),
                        TextEntry::make('faculty.name')->label('Fakultas'),
                        TextEntry::make('studyProgram.name')->label('Program Studi'),
                    ])->columns(3),
            ]);
    }

    // Tambahkan tombol Edit di header halaman View
    protected function getHeaderActions(): array
    {
        return [
            Actions\EditAction::make(),
            Actions\Action::make('downloadTranscript')
                ->label('Cek Draft Transkrip')
                ->icon('heroicon-o-arrow-down-tray')
                ->color('success')
                ->url(fn() => route('transcript.generate', ['student' => $this->record]))
                ->openUrlInNewTab(),
        ];
    }
}
