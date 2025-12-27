<?php

namespace App\Filament\Resources;

use App\Filament\Resources\SubmissionResource\Pages;
use App\Filament\Resources\SubmissionResource\RelationManagers;
use App\Models\ActivityField;
use App\Models\ActivityType;
use App\Models\Student;
use App\Models\Submission;
use App\Rules\ValidClaimDate;
use Carbon\Carbon;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Forms\Get;
use Filament\Forms\Set;
use Filament\Infolists;
use Filament\Infolists\Components\Grid;
use Filament\Infolists\Components\ImageEntry;
use Filament\Infolists\Components\Section;
use Filament\Infolists\Components\TextEntry;
use Filament\Infolists\Infolist;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Actions\Action;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Support\Collection;
use Illuminate\Database\Eloquent\SoftDeletingScope;
use Illuminate\Support\Facades\Auth;

class SubmissionResource extends Resource
{
    protected static ?string $model = Submission::class;
    protected static ?string $navigationIcon = 'heroicon-o-document-arrow-up';
    protected static ?string $navigationLabel = 'Pengajuan Klaim';
    protected static ?string $modelLabel = 'Pengajuan Klaim';
    protected static ?string $pluralLabel = 'Pengajuan Klaim';
    protected static ?int $navigationSort = 2;

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                // LANGKAH 1: Pilih Bidang Kegiatan
                Forms\Components\Select::make('activity_field_id')
                    ->label('1. Pilih Bidang Kegiatan')
                    ->options(ActivityField::query()->pluck('name', 'id'))
                    ->live()
                    ->afterStateUpdated(fn(Set $set) => $set('activity_name', null)) // Reset langkah berikutnya
                    ->searchable()
                    ->required(),

                // LANGKAH 2: Pilih Nama Kegiatan
                Forms\Components\Select::make('activity_name')
                    ->label('2. Pilih Nama Kegiatan')
                    ->options(function (Get $get): Collection {
                        return ActivityType::query()
                            ->where('activity_field_id', $get('activity_field_id'))
                            ->distinct()->pluck('name', 'name');
                    })
                    ->live()
                    ->afterStateUpdated(function (Set $set, Get $get) {
                        // Reset langkah berikutnya
                        $set('activity_level', null);
                        $set('activity_type_id', null);

                        // Cek apakah langkah berikutnya (level) harus dilewati
                        $fieldName = $get('activity_name');
                        $fieldId = $get('activity_field_id');
                        if (!$fieldName) return;

                        // Jika semua kegiatan dengan nama ini tidak punya level, coba cari ID final
                        $hasNoLevels = !ActivityType::where('activity_field_id', $fieldId)->where('name', $fieldName)->whereNotNull('level')->exists();
                        if ($hasNoLevels) {
                            $activity = ActivityType::where('activity_field_id', $fieldId)->where('name', $fieldName)->first();
                            if ($activity) {
                                $set('activity_type_id', $activity->id); // Langsung pilih ID final
                            }
                        }
                    })
                    ->searchable()
                    ->required(fn(Get $get) => $get('activity_field_id')),

                // LANGKAH 3: Pilih Tingkat Kegiatan (Bisa disabled)
                Forms\Components\Select::make('activity_level')
                    ->label('3. Pilih Tingkat Kegiatan')
                    ->options(function (Get $get): Collection {
                        return ActivityType::query()
                            ->where('activity_field_id', $get('activity_field_id'))
                            ->where('name', $get('activity_name'))
                            ->whereNotNull('level') // Hanya tampilkan yang punya level
                            ->distinct()->pluck('level', 'level');
                    })
                    ->live()
                    ->afterStateUpdated(function (Set $set, Get $get) {
                        $set('activity_type_id', null); // Reset langkah akhir

                        // Cek apakah langkah berikutnya (achievement) harus dilewati
                        $fieldName = $get('activity_name');
                        $fieldId = $get('activity_field_id');
                        $level = $get('activity_level');
                        if (!$level) return;

                        $hasNoAchievements = !ActivityType::where('activity_field_id', $fieldId)->where('name', $fieldName)->where('level', $level)->whereNotNull('achievement')->exists();
                        if ($hasNoAchievements) {
                            $activity = ActivityType::where('activity_field_id', $fieldId)->where('name', $fieldName)->where('level', $level)->first();
                            if ($activity) {
                                $set('activity_type_id', $activity->id);
                            }
                        }
                    })
                    ->searchable()
                    // ** LOGIKA DISABLE UTAMA UNTUK LEVEL **
                    ->disabled(function (Get $get): bool {
                        $fieldName = $get('activity_name');
                        if (!$fieldName) return true; // Disable jika nama kegiatan belum dipilih
                        // Disable jika tidak ada satupun kegiatan dengan nama ini yang punya level
                        return !ActivityType::where('activity_field_id', $get('activity_field_id'))->where('name', $fieldName)->whereNotNull('level')->exists();
                    })
                    ->required(function (Get $get): bool {
                        // Wajib diisi hanya jika tidak di-disable
                        $fieldName = $get('activity_name');
                        if (!$fieldName) return false;
                        return ActivityType::where('activity_field_id', $get('activity_field_id'))->where('name', $fieldName)->whereNotNull('level')->exists();
                    }),

                // LANGKAH 4: Pilih Jabatan/Pencapaian (Bisa disabled)
                Forms\Components\Select::make('activity_type_id')
                    ->label('4. Pilih Peringkat / Jabatan')
                    ->relationship(
                        name: 'activityType',
                        titleAttribute: 'achievement',
                        modifyQueryUsing: fn(Builder $query, Get $get) => $query
                            ->where('activity_field_id', $get('activity_field_id'))
                            ->where('name', $get('activity_name'))
                            ->where('level', $get('activity_level'))
                    )
                    ->getOptionLabelFromRecordUsing(fn(ActivityType $record) => "{$record->achievement} ({$record->score} Poin)")
                    ->searchable()->preload()->live()
                    // ** LOGIKA DISABLE UTAMA UNTUK ACHIEVEMENT **
                    ->disabled(function (Get $get): bool {
                        $fieldName = $get('activity_name');
                        if (!$fieldName) return true;

                        // Cek apakah level di-disable, jika ya, achievement juga di-disable
                        $levelIsDisabled = !ActivityType::where('activity_field_id', $get('activity_field_id'))->where('name', $fieldName)->whereNotNull('level')->exists();
                        if ($levelIsDisabled) return true;

                        // Jika level tidak di-disable, cek apakah ada achievement untuk level yg dipilih
                        $level = $get('activity_level');
                        if (!$level) return true; // Disable jika level belum dipilih
                        return !ActivityType::where('activity_field_id', $get('activity_field_id'))->where('name', $fieldName)->where('level', $level)->whereNotNull('achievement')->exists();
                    }),

                // Detail Pengajuan
                Forms\Components\Section::make('Detail Pengajuan')->schema([
                    Forms\Components\Select::make('student_id')
                        ->label('Pilih Mahasiswa')
                        // Gunakan 'relationship' untuk efisiensi
                        ->relationship(
                            name: 'student',
                            // Atribut dasar, akan kita override
                            titleAttribute: 'nim',
                            // Eager load relasi untuk performa
                            modifyQueryUsing: fn(Builder $query) => $query->with(['user', 'faculty', 'studyProgram'])
                        )
                        // Atur format label yang ditampilkan
                        ->getOptionLabelFromRecordUsing(fn(Student $record) => sprintf(
                            '%s - %s - %s - %s',
                            $record->nim,
                            $record->user?->name,
                            $record->faculty?->name,
                            $record->studyProgram?->name
                        ))
                        // Atur kolom mana saja yang bisa dicari
                        ->searchable(['nim', 'user.name', 'faculty.name', 'studyProgram.name'])
                        ->preload()
                        ->required()
                        ->visible(fn(): bool => Auth::user()->role !== 'Student'),

                    Forms\Components\TextInput::make('organizer')->required()->label('Penyelenggara'),
                    Forms\Components\Grid::make(2)->schema([
                        Forms\Components\DatePicker::make('activity_start_date')->required()->label('Tanggal Mulai Kegiatan'),
                        Forms\Components\DatePicker::make('activity_end_date')->required()->label('Tanggal Selesai Kegiatan'),
                    ]),
                    Forms\Components\Grid::make(2)->schema([
                        Forms\Components\TextInput::make('certificate_number')->label('No. Sertifikat/SK'),
                        Forms\Components\DatePicker::make('certificate_date')->required()->label('Tanggal Sertifikat')
                            ->rules([new ValidClaimDate]),
                    ]),

                    Forms\Components\FileUpload::make('proof_document')
                        ->label('Upload Bukti')
                        ->directory('submission-proofs')
                        ->acceptedFileTypes([
                            'application/pdf',
                            'image/jpeg',
                            'image/png',
                        ])
                        ->previewable(true)
                        ->openable()
                        ->downloadable()
                        ->required(),
                ]),

                // Status Verifikasi (hanya untuk Admin/Verifier)
                Forms\Components\Section::make('Status Verifikasi')->schema([
                    Forms\Components\Select::make('status')->options(['Submitted' => 'Submitted', 'Verified' => 'Verified', 'Rejected' => 'Rejected'])->default('Submitted'),
                    Forms\Components\Textarea::make('notes')->label('Catatan Verifikator'),
                ])->visible(fn() => Auth::user()->role !== 'Student'),
            ]);
    }

    public static function infolist(Infolist $infolist): Infolist
    {
        return $infolist
            ->schema([
                Section::make('')->schema(
                    [
                        Grid::make(4)->schema([
                            TextEntry::make('student.user.name')->label('Nama Mahasiswa'),
                            TextEntry::make('student.nim')->label('NIM'),
                            TextEntry::make('student.studyProgram.name')->label('Program Studi'),
                            TextEntry::make('student.faculty.name')->label('Fakultas'),
                        ])
                    ]
                ),

                Section::make('Detail Kegiatan')
                    ->schema([
                        TextEntry::make('activityType.activityField.name')->label('Bidang Kegiatan'),
                        TextEntry::make('activityType.name')->label('Nama Kegiatan'),
                        TextEntry::make('activityType.achievement')->label('Peringkat/Jabatan'),
                        TextEntry::make('activityType.score')->label('Poin')->badge(),
                        TextEntry::make('organizer')->label('Penyelenggara'),
                        TextEntry::make('activityType.level')->label('Tingkat'),

                        TextEntry::make('activity_start_date')
                            ->label('Tanggal Kegiatan')
                            ->formatStateUsing(function ($record) {
                                $start = Carbon::parse($record->activity_start_date)->locale('id')->translatedFormat('d F Y');
                                $end   = Carbon::parse($record->activity_end_date)->locale('id')->translatedFormat('d F Y');
                                return $start === $end ? $start : "$start s/d $end";
                            }),

                        TextEntry::make('certificate_number')
                            ->label('No. Sertifikat/SK')
                            ->formatStateUsing(function ($record) {
                                return $record->certificate_number . ' - ' .
                                    Carbon::parse($record->certificate_date)->locale('id')->translatedFormat('d F Y');
                            }),


                    ])->columns(2),

                Section::make('')
                    ->schema([
                        TextEntry::make('proof_document')
                            ->label('Bukti Kegiatan')
                            ->url(fn($state) => $state ? asset('storage/' . $state) : null, shouldOpenInNewTab: true)
                            ->formatStateUsing(fn() => 'Klik untuk melihat dokumen.')
                            ->icon(fn($state) => match (strtolower(pathinfo($state, PATHINFO_EXTENSION) ?? '')) {
                                'pdf' => 'heroicon-o-document-text',  // ikon pdf
                                'jpg', 'jpeg', 'png' => 'heroicon-o-photo', // ikon image
                                default => 'heroicon-o-document', // default
                            })
                            ->color('primary'),
                    ]),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->recordUrl(null)
            ->columns([
                Tables\Columns\TextColumn::make('certificate_date')
                    ->label('Tanggal Sertifikat')
                    ->date('d F Y')
                    ->sortable(),
                Tables\Columns\TextColumn::make('student.nim')
                    ->label('NIM')
                    ->visible(fn(): bool => Auth::user()?->role === 'Admin')
                    ->searchable(),
                Tables\Columns\TextColumn::make('student.user.name')
                    ->label('Mahasiswa')
                    ->visible(fn(): bool => Auth::user()?->role === 'Admin')
                    ->searchable(),
                Tables\Columns\TextColumn::make('activityType.name')
                    ->label('Nama Kegiatan')
                    ->wrap()
                    ->description(
                        fn(Submission $record): ?string =>
                        $record->status === 'Rejected' ? 'Alasan: ' . $record->notes : null
                    ),
                Tables\Columns\TextColumn::make('activityType.score')
                    ->label('Poin')
                    ->numeric(),
                Tables\Columns\TextColumn::make('status')
                    ->badge()
                    ->color(fn(string $state): string => match ($state) {
                        'Submitted' => 'warning',
                        'Verified' => 'success',
                        'Rejected' => 'danger',
                    }),
            ])->defaultSort('created_at', 'desc')
            ->filters([
                //
            ])
            ->actions([
                Tables\Actions\EditAction::make()
                    ->visible(function (Submission $record): bool {
                        // Selalu tampil untuk Admin/Verifier
                        if (Auth::user()->role !== 'Student') {
                            return true;
                        }
                        // Hanya tampil untuk Student jika status 'Submitted'
                        return $record->status === 'Submitted';
                    }),

                // Tombol View (Lihat)
                Tables\Actions\ViewAction::make()
                    ->visible(function (Submission $record): bool {
                        // Hanya tampil untuk Student jika status BUKAN 'Submitted'
                        if (Auth::user()->role === 'Student') {
                            return $record->status !== 'Submitted';
                        }
                        // Tidak pernah tampil untuk Admin/Verifier
                        return false;
                    }),

                //     Action::make('Verify')
                //         ->action(function (Submission $record) {
                //             $record->status = 'Verified';
                //             $record->save();
                //         })
                //         ->color('success')
                //         ->icon('heroicon-o-check-circle')
                //         ->visible(fn(Submission $record) => $record->status === 'Submitted' && Auth::user()->role !== 'Student'),

                //     Action::make('Reject')
                //         ->action(function (array $data, Submission $record) {
                //             $record->update([
                //                 'status' => 'Rejected',
                //                 'notes' => $data['notes'],
                //             ]);
                //         })
                //         ->color('danger')
                //         ->icon('heroicon-o-x-circle')
                //         ->visible(fn(Submission $record) => $record->status === 'Submitted' && Auth::user()->role !== 'Student')
                //         ->requiresConfirmation() // Minta konfirmasi sebelum menolak
                //         ->form([ // Minta alasan penolakan
                //             Forms\Components\Textarea::make('notes')
                //                 ->label('Alasan Penolakan')
                //                 ->required(),
                //         ]),


            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ])
            ->emptyStateHeading('Belum ada pengajuan');
    }


    public static function getRelations(): array
    {
        return [
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListSubmissions::route('/'),
            'create' => Pages\CreateSubmission::route('/create'),
            'edit' => Pages\EditSubmission::route('/{record}/edit'),
        ];
    }

    public static function getEloquentQuery(): Builder
    {
        if (Auth::user()->role === 'Student') {
            return parent::getEloquentQuery()->where('student_id', Auth::user()->student->id);
        }
        return parent::getEloquentQuery();
    }

    // Tampilkan badge notifikasi untuk permohonan yang submitted
    public static function getNavigationBadge(): ?string
    {
        if (Auth::user()->role === 'Student') {
            return null; // Mahasiswa tidak perlu badge
        }
        return static::getModel()::where('status', 'submitted')->count();
    }
}
