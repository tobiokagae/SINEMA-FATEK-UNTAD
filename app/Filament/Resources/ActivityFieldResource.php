<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ActivityFieldResource\Pages;
use App\Filament\Resources\ActivityFieldResource\RelationManagers;
use App\Models\ActivityField;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\SoftDeletingScope;
use Illuminate\Support\Facades\Auth;

class ActivityFieldResource extends Resource
{
    protected static ?string $model = ActivityField::class;
    protected static ?string $navigationIcon = 'heroicon-o-squares-2x2';
    protected static ?string $navigationGroup = 'Pengaturan';
    protected static ?string $navigationLabel = 'Kegiatan';
    protected static ?string $modelLabel = 'Bidang Kegiatan';
    protected static ?string $pluralLabel = 'Bidang Kegiatan';

    public static function canViewAny(): bool
    {
        return Auth::user()->role === 'Admin';
    }

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\TextInput::make('name')
                    ->label('Nama Bidang')
                    ->required()
                    ->maxLength(255),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->label('Nama Bidang')
                    ->searchable(),
                Tables\Columns\TextColumn::make('activity_types_count')
                    ->counts('activityTypes') // 'activityTypes' adalah nama relasi di model Faculty
                    ->label('Rubrik')
                    ->sortable(),
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
            RelationManagers\ActivityTypesRelationManager::class,
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListActivityFields::route('/'),
            // 'create' => Pages\CreateActivityField::route('/create'),x
            'edit' => Pages\EditActivityField::route('/{record}/edit'),
        ];
    }
}
