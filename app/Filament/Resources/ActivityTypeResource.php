<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ActivityTypeResource\Pages;
use App\Filament\Resources\ActivityTypeResource\RelationManagers;
use App\Models\ActivityType;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\SoftDeletingScope;
use Illuminate\Support\Facades\Auth;

class ActivityTypeResource extends Resource
{
    protected static ?string $model = ActivityType::class;
    protected static ?string $navigationIcon = 'heroicon-o-list-bullet';
    protected static ?string $navigationGroup = 'Pengaturan';
    protected static ?string $navigationLabel = 'Rubrik Kegiatan';
    protected static ?string $modelLabel = 'Rubrik Kegiatan';
    protected static ?string $pluralLabel = 'Rubrik Kegiatan';
    protected static bool $shouldRegisterNavigation = false;

    public static function canViewAny(): bool
    {
        return Auth::user()->role === 'Admin';
    }

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Select::make('activity_field_id')
                    ->label('Bidang Kegiatan')
                    ->relationship('activityField', 'name')
                    ->required(),
                Forms\Components\TextInput::make('level')
                    ->label('Tingkat')
                    ->maxLength(255),
                Forms\Components\Textarea::make('name')
                    ->label('Nama Kegiatan')
                    ->required()
                    ->columnSpanFull(),
                Forms\Components\TextInput::make('achievement')
                    ->label('Peringkat')
                    ->maxLength(255),
                Forms\Components\TextInput::make('score')
                    ->label('Poin')
                    ->required()
                    ->numeric(),
                Forms\Components\Select::make('required_category')
                    ->label('Kategori Wajib')
                    ->options([
                        ActivityType::REQUIRED_CATEGORY_PKKMB => 'PKKMB (Wajib)',
                        ActivityType::REQUIRED_CATEGORY_BAKTI_LINGKUNGAN => 'Bakti Lingkungan (Wajib)',
                    ])
                    ->helperText('Pilih kategori ini hanya jika kegiatan tersebut adalah syarat wajib untuk permohonan transkrip.')
                    ->columnSpanFull(),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('activityField.name')
                    ->label('Bidang Kegiatan')
                    ->numeric()
                    ->sortable(),
                Tables\Columns\TextColumn::make('level')
                    ->label('Tingkat')
                    ->searchable(),
                Tables\Columns\TextColumn::make('achievement')
                    ->label('Peringkat')
                    ->searchable(),
                Tables\Columns\TextColumn::make('score')
                    ->label('Poin')
                    ->numeric()
                    ->sortable(),
                Tables\Columns\TextColumn::make('required_category')
                    ->label('Kategori')
                    ->badge()
                    ->color(fn(?string $state): string => match ($state) {
                        ActivityType::REQUIRED_CATEGORY_PKKMB => 'success',
                        ActivityType::REQUIRED_CATEGORY_BAKTI_LINGKUNGAN => 'info',
                        default => 'gray',
                    })
                    ->formatStateUsing(fn(?string $state): string => match ($state) {
                        ActivityType::REQUIRED_CATEGORY_PKKMB => 'PKKMB',
                        ActivityType::REQUIRED_CATEGORY_BAKTI_LINGKUNGAN => 'Bakti Lingkungan',
                        default => '-',
                    })->searchable(),
                // Tables\Columns\TextColumn::make('created_at')
                //     ->dateTime()
                //     ->sortable()
                //     ->toggleable(isToggledHiddenByDefault: true),
                // Tables\Columns\TextColumn::make('updated_at')
                //     ->dateTime()
                //     ->sortable()
                //     ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                //
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
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
            'index' => Pages\ListActivityTypes::route('/'),
            // 'create' => Pages\CreateActivityType::route('/create'),
            'edit' => Pages\EditActivityType::route('/{record}/edit'),
        ];
    }
}
