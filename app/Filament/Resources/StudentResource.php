<?php

namespace App\Filament\Resources;

use App\Filament\Resources\StudentResource\Pages;
use App\Models\Faculty;
use App\Models\Student;
use App\Models\StudyProgram;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Forms\Get;
use Filament\Notifications\Notification;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Actions\Action;
use Filament\Tables\Filters\Filter;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\HtmlString;

class StudentResource extends Resource
{
    protected static ?string $model = Student::class;
    protected static ?string $navigationIcon = 'heroicon-o-academic-cap';
    protected static ?string $navigationLabel = 'Mahasiswa';
    protected static ?string $modelLabel = 'Mahasiswa';
    protected static ?string $pluralLabel = 'Mahasiswa';

    public static function canViewAny(): bool
    {
        return Auth::user()->role === 'Admin';
    }

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Informasi Akun')
                    ->schema([
                        // PERBAIKAN: Gunakan nama field sederhana
                        Forms\Components\TextInput::make('name')
                            ->label('Nama Mahasiswa')
                            ->required(),
                        Forms\Components\TextInput::make('email')
                            ->label('Email')
                            ->email()
                            ->required()
                            // Validasi unik sekarang perlu query kustom
                            ->unique(
                                table: 'users',
                                column: 'email',
                                ignoreRecord: true,
                                modifyRuleUsing: function ($rule, Get $get) {
                                    // Dapatkan ID user dari record student yang sedang diedit
                                    $studentId = $get('id');
                                    if ($studentId && $student = Student::find($studentId)) {
                                        return $rule->ignore($student->user_id);
                                    }
                                    return $rule;
                                }
                            ),
                    ])->columns(2),

                Forms\Components\Section::make('Informasi Akademik')
                    ->schema([
                        Forms\Components\TextInput::make('nim')
                            ->label('NIM')
                            ->unique(table: 'students', column: 'nim', ignoreRecord: true)
                            ->maxLength(9)
                            ->required(),
                        Forms\Components\Select::make('faculty_id')
                            ->label('Fakultas')
                            ->options(Faculty::all()->pluck('name', 'id'))
                            ->live()
                            ->searchable()
                            ->required(),
                        Forms\Components\Select::make('study_program_id')
                            ->label('Program Studi')
                            ->options(function (Get $get) {
                                $facultyId = $get('faculty_id');
                                if (!$facultyId) return [];
                                return StudyProgram::where('faculty_id', $facultyId)->pluck('name', 'id');
                            })
                            ->searchable()
                            ->required(),
                    ])->columns(3),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('nim')->label('NIM')->searchable(),
                Tables\Columns\TextColumn::make('user.name')->label('Nama Mahasiswa')->searchable()->sortable(),
                Tables\Columns\TextColumn::make('faculty.name')->label('Fakultas')->searchable(),
                Tables\Columns\TextColumn::make('studyProgram.name')->label('Program Studi')->searchable(),

                Tables\Columns\TextColumn::make('total_score')
                    ->label('Poin')
                    ->numeric()
                    ->state(function (Student $record): int {
                        return $record->submissions
                            ->where('status', 'Verified')
                            ->sum('activityType.score');
                    })
                    ->sortable(query: function (Builder $query, string $direction): Builder {
                        return $query
                            ->select('students.*') // Hindari ambiguitas kolom
                            ->selectSub(function ($subQuery) {
                                $subQuery->from('submissions')
                                    ->join('activity_types', 'submissions.activity_type_id', '=', 'activity_types.id')
                                    ->whereColumn('submissions.student_id', 'students.id')
                                    ->where('submissions.status', 'Verified')
                                    ->selectRaw('SUM(activity_types.score)');
                            }, 'total_score_for_sort')
                            ->orderBy('total_score_for_sort', $direction);
                    }),

                Tables\Columns\TextColumn::make('nilai_mutu')
                    ->label('Nilai')
                    ->badge()
                    ->state(function (Student $record): string {
                        $totalScore = $record->submissions
                            ->where('status', 'Verified')
                            ->sum('activityType.score');

                        return match (true) {
                            $totalScore > 3000 => 'A',
                            $totalScore >= 2501 => 'A-',
                            $totalScore >= 2001 => 'B+',
                            $totalScore >= 1500 => 'B',
                            default => '-',
                        };
                    })
                    ->color(fn(string $state): string => match ($state) {
                        'A', 'A-' => 'success',
                        'B+', 'B' => 'warning',
                        default => 'danger',
                    })
                    ->sortable(query: function (Builder $query, string $direction): Builder {
                        return $query
                            ->select('students.*')
                            ->selectSub(function ($subQuery) {
                                $subQuery->from('submissions')
                                    ->join('activity_types', 'submissions.activity_type_id', '=', 'activity_types.id')
                                    ->whereColumn('submissions.student_id', 'students.id')
                                    ->where('submissions.status', 'Verified')
                                    ->selectRaw('SUM(activity_types.score)');
                            }, 'total_score_for_sort')
                            ->orderByRaw("CASE
                                WHEN total_score_for_sort > 3000 THEN 5
                                WHEN total_score_for_sort >= 2501 THEN 4
                                WHEN total_score_for_sort >= 2001 THEN 3
                                WHEN total_score_for_sort >= 1500 THEN 2
                                ELSE 1
                            END {$direction}");
                    }),
            ])
            ->filters([
                Filter::make('academic_info')
                    ->form([
                        Forms\Components\Select::make('faculty_id')
                            ->label('Fakultas')
                            ->options(Faculty::all()->pluck('name', 'id'))
                            ->live()
                            ->searchable(),
                        Forms\Components\Select::make('study_program_id')
                            ->label('Program Studi')
                            ->options(function (Get $get): array {
                                $facultyId = $get('faculty_id');
                                if (!$facultyId) {
                                    return StudyProgram::all()->pluck('name', 'id')->toArray();
                                }
                                return StudyProgram::where('faculty_id', $facultyId)->pluck('name', 'id')->toArray();
                            })
                            ->searchable(),
                    ])
                    ->query(function (Builder $query, array $data): Builder {
                        return $query
                            ->when(
                                $data['faculty_id'],
                                fn(Builder $query, $facultyId): Builder => $query->where('faculty_id', $facultyId)
                            )
                            ->when(
                                $data['study_program_id'],
                                fn(Builder $query, $studyProgramId): Builder => $query->where('study_program_id', $studyProgramId)
                            );
                    })
            ])
            ->actions([
                // 
            ])
            ->recordAction('view');
    }

    public static function getEloquentQuery(): Builder
    {
        return parent::getEloquentQuery()->with(['submissions.activityType', 'user', 'faculty', 'studyProgram']);
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
            'index' => Pages\ListStudents::route('/'),
            // 'create' => Pages\CreateStudent::route('/create'),
            'edit' => Pages\EditStudent::route('/{record}/edit'),
            'view' => Pages\ViewStudent::route('/{record}'),
        ];
    }

    public static function canCreate(): bool
    {
        return false;
    }
}
